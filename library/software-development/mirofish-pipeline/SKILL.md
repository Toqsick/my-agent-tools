---
name: mirofish-pipeline
title: "MiroFish Pipeline — Seed, API, Monitor"
description: "Use when user asks to set up the MiroFish pipeline: seed distillation, project/graph creation, simulation prepare/monitor, or live progress polling. NOT for post-run analysis (use mirofish-analysis), runbook templates (use mirofish-runbook), or known pitfall recovery (use mirofish-pitfalls). Covers Step 1+2+4 of the MiroFish lifecycle."
category: software-development
version: '2.7'
created: '2026-07-23'
author: Yuno (split from mirofish v2.6)
lane: software-development
agent: universal
trigger_keywords: ['mirofish', 'seed distillate', 'graph build', 'simulation prepare', 'monitor', 'poll progress', 'oasis worker', 'zep', 'ontology']
keywords: ['mirofish', 'pipeline', 'seed', 'graph', 'simulation', 'monitor', 'oasis', 'zep', 'ontology', 'distillation']
related_skills: ['mirofish-analysis', 'mirofish-pitfalls', 'mirofish-runbook', 'multi-agent-cluster-patterns']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from mirofish 2026-07-23)'

license: MIT
---

# MiroFish Pipeline — Seed, API, Monitor

MiroFish Pipeline — Seed, API, Monitor


## Trigger


- User asks to run a MiroFish simulation on a topic
- A source document (PDF, Markdown, research) needs to be turned into a multi-agent debate simulation
- Existing simulation needs monitoring or report generation

## Pipeline Overview


```
Source Doc → Distill Seed (~6-8k tokens) → Project Create → Ontology Generate → Graph Build → Simulation Create → Simulation Start → Monitor → Report Generate
```

Each step depends on the previous. Do NOT skip steps.

---

## Pre-Run Checklist


Before starting ANY simulation, run this checklist to prevent OOM crashes and stale-state issues:

### 1. Kill Stale OASIS Workers


Previous OASIS workers may survive backend restarts and consume 1.3+ GB RAM silently. Always check:

```bash
echo "=== Stale OASIS workers ==="
ps -ef | grep -E "run_parallel_simulation|run_twitter_simulation" | grep -v grep
### 2. Check RAM Budget


```bash
free -h
```

**Minimum requirements:**
| Scenario | Min Free RAM |
|---|---|
| Quick run (3-4 personas, 20 rounds) | 2 GiB |
| Full run (5-7 personas, 60 rounds) | 4 GiB |
| 10-persona run (Twitter only) | 3 GiB |
| Graph build (Zep processing) | 2 GiB |

If RAM is below minimum, close unused Brave tabs, kill stale workers, or defer the run.

### 3. Clean Up Old Simulations


Finished simulations accumulate on disk and in the API's in-memory state. Remove them to reduce DB clutter:

```bash
### 4. Check for Stale Watchers


```bash
ps -ef | grep -E "mirofish_watcher|watch_sim|robust-watcher" | grep -v grep
## Step 1: Seed Distillate


Create a dense Markdown file (~6-8k tokens / 800-1200 words) that captures the **substance** of the source, not the narrative:

Path: `~/10-Projekte/20-experimental/MiroFish/testdata/<topic>-seed.md`

Structure:
- **Executive Summary** (2-3 paragraphs)
- **Framework/Architecture Matrix** (key players, trade-offs)
- **Core Schemas** (data models, contracts)
- **Security Architecture** (threat model, defenses)
- **Cost Model** (tiers, routing, control)
- **Open Discussion Points** (polarizing questions → agent debate fuel)

See `references/seed-structure-brainstorming.md` for the full template.

**PITFALL — Seed density sweet spot:** ~1000 words (~7k tokens) is the sweet spot for general use. Much less and the ontology generator doesn't have enough entities to build. Much more (12k+ chars) and multiple issues emerge: (1) LLM context fills up, requiring max_tokens=16384, (2) the ontology generator produces fewer distinct profiles (e.g. 24k-char seed → only 4 profiles from 10 requested personas), and (3) the OASIS worker gets stuck in abnormally long LLM calls during initial rounds. **Counterintuitively, a larger seed does NOT produce more personas — it produces the same or fewer, but with deeper technical content.**

**PITFALL — More seed ≠ more output:** A denser seed (+66% tokens) actually produces **fewer** personas (3 vs 7) and fewer total actions (~90 vs ~150), but generates **more technical** output (code snippets, concrete configs) instead of narrative dialogue. Seed density determines output **type**, not output **volume**. See `references/seed-density-correlation.md` for the full V1 vs V2/V3 comparison data.

**PITFALL — Seed >12k chars requires max_tokens=16384:** When the seed exceeds 12k characters, the default 8192 max_tokens at the ontology generator and LLM client level is insufficient. Patch BOTH `ontology_generator.py` (`self.llm_client.chat_json(..., max_tokens=16384)`) AND `llm_client.py` default. Without this, the ontology JSON is silently truncated — the project appears clean but has 0 entities or 0 files. Symptom: successful ontology generation, but `curl /api/project/<id>` shows empty entity/edge lists.

---

## Step 2: MiroFish API Pipeline


All API calls go to `http://localhost:5001/api/`.

### 2a) Project + Ontology Generation


```bash
curl -X POST http://localhost:5001/api/graph/ontology/generate \
  -F "files=@testdata/<topic>-seed.md" \
  -F 'simulation_requirement=<JSON describing the simulation topic, audience, goal>'
```

Returns `{"data": {"project_id": "proj_..."}}`. Expect ~60-90s response.

**State verification:** Check the project has files attached:
```bash
curl -s http://localhost:5001/api/project/<proj_id> | python3 -c "import json,sys; d=json.load(sys.stdin)['data']; print(d.get('text_length'), d.get('files_count'))"
```

If `files_count: 0`, retry the upload — the file didn't attach.

### 2b) Graph Build


```bash
curl -X POST http://localhost:5001/api/graph/build \
  -H "Content-Type: application/json" \
  -d '{"project_id": "<proj_id>"}'

### 2c) Simulation Create + Prepare


```bash
### 2e) Monitor


Poll status:
```bash
curl -s "http://localhost:5001/api/simulation/$SIM_ID" | python3 -c "
import json, sys
d = json.load(sys.stdin)['data']
print(f'Runner: {d.get(\"runner_status\")}')
print(f'Round: {d.get(\"current_round\")}/{d.get(\"total_rounds\")}')
print(f'Actions: {d.get(\"total_actions_count\")} (T:{d.get(\"twitter_actions_count\")} R:{d.get(\"reddit_actions_count\")})')
print(f'Progress: {d.get(\"progress_percent\")}%')
print(f'Twitter: {d.get(\"twitter_status\")} | Reddit: {d.get(\"reddit_status\")}')
"
```

**⚠️ CRITICAL — `run-status` Endpoint is Stale for Zep Cloud Backend:** The API endpoint `/api/simulation/<id>` returns `runner_status: running` but **all other fields are often `None`** — `current_round`, `total_actions_count`, `progress_percent` — even when the simulation is actively producing posts. This is because the Zep Cloud backend writes progress to disk files, not the API database. **Only `runner_status` is authoritative for alive/dead detection.**

**Real-time progress MUST be read from `simulation.log` directly:**

```bash
### 2f) Report Generation


**⚠️ THIS IS ASYNC.** The endpoint returns immediately with a `report_id`, but the report stays in `planning` status before changing to `completed`. You MUST poll the GET endpoint to verify completion before reading content.

**⚠️ Timing scales with post count:**
| Simulation output | Typical "planning" duration |
|---|---|
| ~41 posts (small run, 8-9 min crash window) | 30-90s |
| ~100 posts (template-skill, partial) | 2-4 min |
| ~169 posts (template-skill, full 60 rounds) | **6+ minutes** |
| 200+ posts (derived-skill, full run) | Estimate: 10+ min |

The outline (4 sections, Chinese) appears immediately. The `markdown_content` generation is the slow part. **Don't declare failure if still "planning" after 2 minutes.**

```bash
### 2g) Save Report to Disk


Report content is served by the API but NOT persisted to disk by default. After confirming `status: completed`, save immediately:

```bash
curl -s "http://localhost:5001/api/report/$REPORT_ID" | \
  python3 -c "
import json, sys
d = json.load(sys.stdin)['data']
md = d.get('markdown_content', '')
path = '/home/bratan/10-Projekte/20-experimental/MiroFish/report_$REPORT_ID.md'
with open(path, 'w') as f:
    f.write(md)
print(f'Saved {len(md)} chars to {path}')
"
```

Saved path: `~/10-Projekte/20-experimental/MiroFish/report_{report_id}.md`

View in browser:
- Report view: `http://localhost:3000/report/{report_id}`
- Interactive agent chat: `http://localhost:3000/interaction/{report_id}`

**PITFALL:** The report may be generated in Chinese (the LLM's default language for this task type). The outline may show sections in Chinese. This is expected behaviour for MiroFish's default report generation — the LLM picks its primary language.

---

## Step 4: Watching the Simulation Live


The landing page (`http://localhost:3000/`) only shows the Create page. For live simulation views, navigate directly:

| What you want | URL |
|---|---|
| Simulation overview (profiles, entities, config) | `http://localhost:3000/simulation/{simId}` |
| 🔴 Live run dashboard (posts in real-time) | `http://localhost:3000/simulation/{simId}/start` |
| Report (after completion) | `http://localhost:3000/report/{reportId}` |
| Interactive agent chat | `http://localhost:3000/interaction/{reportId}` |

The `/start` dashboard shows: live Twitter/Reddit posts scrolling in, round counter, agent-stats (who posts most), graph visualization with 7 personae as nodes.

**PITFALL — Live content from disk:** The Vue frontend refreshes via API calls. If the GET endpoint returns stale `None` values but the simulation is clearly progressing, the dashboard may appear empty or stuck. In that case, check `run_state.json` on disk (see Pitfall 3 below).

**Practical usage — finding the right view:** Open your browser and type the exact URL into the address bar. The Vue SPA serves the same HTML shell for all routes — the URL path is what determines which view renders. If you see the landing page, you're on `http://localhost:3000/` — navigate to a simulation URL instead. If the page still shows the landing page after entering the URL, try a hard refresh (Ctrl+Shift+R) to clear any Vue SPA cache.

---
