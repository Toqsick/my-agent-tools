---
name: mirofish-pitfalls
title: "MiroFish Pitfalls — 35+ Lessons Learned"
description: "Use when a MiroFish simulation misbehaves, hangs, crashes, or returns unexpected state — covers all 35 known pitfalls (Zep rate limits, run_state staleness, OASIS worker survival, watcher pid discovery, prepare stalls, MiniMax-M3 truncation, etc). NOT for first-time pipeline setup (use mirofish-pipeline). Index of failure modes + recovery recipes."
category: software-development
version: '2.7'
created: '2026-07-23'
author: Yuno (split from mirofish v2.6)
lane: software-development
agent: universal
trigger_keywords: ['mirofish', 'pitfall', 'stuck', 'stall', 'crash', 'oom', 'watcher', 'rate limit', 'stale state', 'zep']
keywords: ['mirofish', 'pitfall', 'stuck', 'crash', 'watcher', 'rate-limit', 'stale', 'recovery', 'diagnostic']
related_skills: ['mirofish-pipeline', 'mirofish-runbook', 'systematic-debugging']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from mirofish 2026-07-23)'

license: MIT
---

# MiroFish Pitfalls — 35+ Lessons Learned

MiroFish Pitfalls — 35+ Lessons Learned


#### 5 Analysis Dimensions


| # | Dimension | Method | What it reveals |
|---|---|---|---|
| 1 | **Persona Workload** | Count posts per user across runs | Which persona dominates per skill-type |
| 2 | **Insight Diversity** | Classify: Meta / Repeat / Fresh | Bias-inheritance rate (quantified) |
| 3 | **Discourse Function** | Tag: Position / Challenge / Resolution | Debate depth per skill-type |
| 4 | **Word Cloud Drift** | Top-15 words per run → compare overlap | Topic emergence per skill-layer |
| 5 | **Hashtag Overlap** | Unique hashtags per run → intersection | Operational bias-monitor |

#### Dimension 2 Calibration (from Sim09)


| Run | Meta | Repeat | Fresh |
|---|---|---|---|
| A (Fresh) | 90% | 0% | 10% |
| B (Template) | 63% | 0% | **37%** ⭐ Sweet Spot |
| C (Derived) | 84% | **23%** ⚠️ | bias confirmed |

**The 23% cluster-repetition in Derived runs** is the quantitative confirmation of the bias-inheritance hypothesis.

#### Dimension 3 Calibration


| Function | Run A | Run B | Run C |
|---|---|---|---|
| Position | 90% | 92% | 85% |
| Challenge | 10% | 6% | **14%** ⚠️ |
| Resolution | 0% | 2% | 1% |

Derived runs trigger most Challenges (skill-content inherited → attacked). Fresh runs have zero Resolutions.

#### Dimension 4 Calibration


| Run | Top-3 words | Topic signature |
|---|---|---|
| A (Fresh) | skill, drift, jaccard | Drift-fokussiert |
| B (Template) | schema, layer, boundary | Schema-Mechanik |
| C (Derived) | skill, audit, compliance | Compliance / Provenance |

**Only 4 two-grams common across all 3 runs:** `audit trail`, `cluster skeleton`, `derived skill`, `runa fresh`.

#### Dimension 5 Calibration


| Hashtag | Run A | Run B | Run C | Signal |
|---|---|---|---|---|
| `#SkillChaining` | 10x | – | 30x | C-driven |
| `#HygieneBoundary` | – | 14x | – | B-only |
| `#provenance_chain` | – | – | 10x | C-only |
| `#NeurIPS2025` | 5x | – | – | A-only |

When a hashtag appears in only one run, it's a skill-inherited bias signal. Pattern shift = bias-drift.

#### Skill-Type Recommendation (from Sim09 Validation)


| Question-Type | Recommended Skill-Type | Why |
|---|---|---|
| Discovery / Neue Insights | Fresh | Maximale Überraschung, keine Repetition |
| Reproduzierbare Methodik | Template | 37% Fresh, keine Bias-Vererbung |
| Compliance / Provenance-Audit | Derived | Reproduzierbar, Bias-Disclosure erzwingbar |

**Sub-Analysis Tooling:** Use `python3` with standard lib (json, sqlite3, re, collections.Counter). Run as single terminal command. Save to `~/MiroFish/<run-name>-sub-analysis.md`.

---

## Step 3: Runbook Documentation


After every non-trivial run, create a runbook at:
`~/10-Projekte/20-experimental/MiroFish/RUN-<topic>.md`

Structure:
```markdown
### 15. Duplicate Report on Multiple Watcher Triggers


**Symptom:** Two reports exist for one simulation — the first with status `planning` (actually progressing) and a second with status `pending` (stale). The user sees duplicate report IDs.

**Root cause:** If the simulation completion notification fires twice (e.g. two watcher processes both detect `completed`), the `/api/report/generate` endpoint creates a new report each time. The first report progresses to `completed`; the second stays at `pending` because the first one already consumed the simulation data.

**Resolution at run end:**
1. Check ALL reports: `curl -s http://localhost:5001/api/report/list | python3 -m json.tool`
2. Only use the `completed` report (status=completed, markdown_content > 1000 chars)
3. Delete the stale `pending` report: `curl -X DELETE http://localhost:5001/api/report/{stale_report_id}` (implement DELETE or leave for cleanup)
4. Or simply save the completed one and ignore the duplicate

**Prevention:** Only ONE watcher should call `/api/report/generate`. The watcher should set a semaphore/lock file before triggering the report to prevent double-trigger.

---

### 16. Long Sessions Exceed Tool-Call Limits


**Symptom:** After 30+ tool calls monitoring a simulation, Hermes hits the max tool-call iterations limit and forces a final-response summary while the simulation is still running.

**Root cause:** Long MiroFish sessions (1-6h) require many tool calls for polling, status checks, log reading, and API calls. Each poll cycle is 2-4 tool calls (poll → check → read run_state.json → write status). Over 60 rounds × 30s intervals = ~40 tool calls just for monitoring.

**Mitigation strategies:**
1. **Background watcher + periodic check** — launch a Python-based watcher that writes progress to a log file, then only check the log every 10 cycles (not every 30s)
2. **Write intermediate findings as you go** — after every ~20 tool calls, write a `RUN-<topic>-phase.md` checkpoint so the session ending doesn't lose work
3. **Use the robust watcher template** (`templates/robust-watcher.py` in skill dir) — it handles all polling in a single background process
4. **For 2+ hour simulations, offer to write a handoff doc** and continue in a new session

---

### 17. User Says "hab gestartet" — They Restarted from the UI


**Symptom:** After an OOM crash or process kill, the user says "hab gestartet" ["have started"]. The agent is unsure what was started and tries to inspect too much.

**Pattern:** The user opened Brave browser, navigated to the MiroFish landing page, entered parameters, and clicked "Start". This:
1. Creates a new OASIS worker (new PID, new worker process)
2. The simulation shows as `running R0/60` in the API
3. Initial output appears in `simulation.log` as `[Twitter] 已发布 3 条初始帖子` ("3 initial posts published")
4. The Twitter DB starts growing (typically 100-200 KB within 1-2 min)

**Recognition signals:**
- User message is short ("hab gestartet", "hab's nochmal gestartet", "started")
- Simulation status changes from `preparing` or `graph_completed` to `running` without an agent-triggered API call
- A new OASIS worker PID appears (not the old one)
- The pre-existing V3 project/graph (from the agent's failed attempt) is being reused

**Response:** Acknowledge briefly, verify with ONE lightweight check (PID exists + sim status + DB growth optional), then report the key findings. Do NOT start a new watcher unless the user asks. The user is watching it live in the browser.

**PITFALL — Don't start a new watcher unasked:** When the user has started the simulation themselves from the UI, they don't need a watcher. Starting one wastes resources and creates confusion. Only offer if the user asks for auto-report-trigger at the end.

**PITFALL — Don't inspect the DB or logs excessively:** One quick check ("PID lives? Sim running?") is enough. More inspection violates Mnemosyne's "nicht mehr Daten erzeugen" guidance.

---

### 18. User-Requested "link!" / "den kompletten link" — Respond With ALL Relevant URLs


**Symptom:** User says "link!", "URL!", "schick den kompletten link", or similar. The agent responds with a single URL or explanation text. The user wants ALL relevant URLs — no intro, no friendly wrapper.

**Fix:** When the user asks for a link, respond with ONLY the URL(s) formatted as a clean markdown list or table. No explanation, no context, no friendly intro. "Den kompletten link" means ALL relevant URLs in one response:

```markdown
| Was | URL |
|---|---|
| 🚀 Live-Sim-Visualisierung | http://localhost:3000/simulation/sim_xxx/start |
| 📋 Sim-Detail-Panel | http://localhost:3000/simulation/sim_xxx |
```

**What "alle relevanten URLs" includes:**
- The **live simulation dashboard** (`/simulation/{id}/start`)
- The **simulation detail panel** (`/simulation/{id}`)
- The **frontend landing page** (`http://localhost:3000/`)
- The **API health** endpoint only if asked specifically

**Examples:**
- ✅ `http://localhost:3000/simulation/sim_xxx/start`
- ✅ A markdown table with all 2-3 relevant URLs as the FIRST response element
- ❌ "Hier ist der Link zu deiner Simulation: http://..."
- ❌ Any explanation text before the URL(s)
- ❌ Only a single URL when the user said "kompletten link"

---

### 19. Completed Simulation = Full Data Reading Allowed


**Symptom:** After a simulation completes, the agent hesitates to read simulation data (DBs, posts, profiles, logs) because of Mnemosyne's "Don't inspect the DB or logs excessively" guidance.

**Permission pattern:** The user explicitly allows full data reading when the simulation is no longer running. Signal phrase: "wenn die sim nicht mehr läuft darfst du lesen" (when the sim is no longer running, you may read).

**What becomes readable after completion:**
| Source | Path | What it contains |
|---|---|---|
| Twitter DB | `simulations/{id}/twitter_simulation.db` | All posts (content, likes, shares), user profiles |
| `run_state.json` | `simulations/{id}/run_state.json` | Full run metrics (rounds, actions, timing) |
| `simulation.log` | `simulations/{id}/simulation.log` | LLM call log, error traces |
| Twitter profiles CSV | `simulations/{id}/twitter_profiles.csv` | All persona profiles and descriptions |
| Report markdown | `report_{id}.md` (in MiroFish root) | Full report content (if saved from API) |

**Reading methodology for completed sims:**
1. Start with `run_state.json` to get the overview (rounds, actions, status)
2. Read the report markdown for synthesized findings
3. Query the Twitter DB for post content — group by user_id to see each persona's posts
4. Read the profiles CSV for persona descriptions

**PITFALL — run_state.json vs DB content may diverge:** The state file tracks "actions" (includes replies, likes) while the DB tracks "posts" (original content). A sim may show 73 actions but only 46 posts in the DB — the difference is non-post actions (replies, comments).

**PITFALL — Post content may be duplicated across users:** When the LLM generates the same content for multiple personas (a known MiroFish quirk), you'll see identical posts attributed to different user_ids. Filter by unique content or user_id to get the real signal.

---

### 20. Report Agent Chat Expects `message` Field, Not `question`


**Symptom:** The report agent chat returns `{"error":"请提供 message","success":false}` despite sending what seems like a valid question payload.

**Root cause:** The `/api/report/chat` endpoint expects the field name **`message`**, not `question`, `query`, `prompt`, or `text`. This is hard-coded in the MiroFish backend.

**Fix — always use `message` as the field name:**
```json
{
    "simulation_id": "sim_xxx",
    "report_id": "report_xxx",
    "message": "Your actual question here",
    "interview_agents": true,
    "max_agents": 4
}
```

**Testing pattern (isolated):**
```bash
### 21. Zep Cloud API `run-status` Endpoint Returns Stale/Empty Data


**Symptom:** `curl http://localhost:5001/api/simulation/{id}` returns `runner_status: running` but **all other fields are `None`** — `current_round`, `total_actions_count`, `progress_percent`, `twitter_status`, `reddit_status` — even though the simulation is actively producing posts.

**Root cause:** With the Zep Cloud backend deployment, the GET simulation endpoint reads from a database that is **NOT updated in real-time** by the OASIS worker. The worker writes progress to disk (`simulation.log`, `oasis.env.log`, `twitter_simulation.db`) but the API's DB query returns empty/None for all non-`runner_status` fields.

**Real-time truth sources (in priority order):**
| Source | Path | Update frequency | What it shows |
|---|---|---|---|
| `simulation.log` | `simulations/{id}/simulation.log` | Real-time (per LLM call) | `[Day 1, HH:MM] Round N/60 (X%)` |
| `oasis.env.log` | `simulations/{id}/log/oasis.env.log` | Per action | `performed all actions` count |
| `twitter_simulation.db` | `simulations/{id}/twitter_simulation.db` | Per post write | DB file size grows (= alive worker) |

**Workaround — never rely on the API endpoint for progress. Only use it for alive/dead detection:**

```bash
### 22. Zep Cloud Free Tier Rate Limiting (300 req/day)


**Symptom:** Graph build pauses mid-way. API returns HTTP 429 with:
```
x-ratelimit-limit: 300
x-ratelimit-remaining: 0
Rate limit exceeded for FREE plan
Rate limit windows: Reset 438 seconds
```

**Root cause:** Zep Cloud Free Tier is limited to 300 API requests per rolling day. The graph build's parallel chunk processing (119 chunks in typical runs) can exhaust this quota in a single build run.

**Behavior during rate limit:**
1. Build tasks show `progress: 70%` and freeze
2. Watcher sees no progress for 3-5 minutes
3. Zep resets quota after ~440 seconds (7+ minutes)
4. Build automatically resumes and completes
5. Total build time with rate limiting: ~26 min (vs 5-8 min without)

**Mitigation strategies:**
1. **Wait for reset**: If stuck at ~70%, wait 7-8 minutes. The build resumes automatically once quota refreshes.
2. **Reduce chunk count**: Use smaller seed (6-10k chars) or adjust `chunk_size` to 400-500 to reduce total chunks from 119 to ~56
3. **Run simulations back-to-back, not parallel**: Each graph build consumes ~119 requests. Two parallel runs exceed 300 before the first build finishes.
4. **Monitor quota proactively**: Before starting a graph build, check remaining quota:
   ```bash
   curl -s -X POST http://localhost:5001/api/graph/build \
     -H "Content-Type: application/json" \
     -d '{"project_id": "proj_xxx", "dry_run": true}' | head -3
   # (if dry_run not supported, just let it run and handle 429 gracefully)
   ```

**Watcher design with rate limiting awareness:**
```bash
### 23. `force=true` Parameter on Graph Build Is Destructive


**Symptom:** A diagnostic or debugging call to the graph build endpoint with `force=true` overwrites the existing project's graph with a new one. The original graph (with its accumulated chunks, nodes, and edges) is gone. If the simulation was already referencing the original graph, it becomes orphaned.

**Root cause:** The `force=true` parameter on `POST /api/graph/build` tells Zep to **destroy and recreate** the graph from scratch for the same project. Unlike `reset=true` (which rebuilds in-place with the same ontology), `force=true` creates an entirely new `graph_id` and detaches the old graph.

**What `force=true` does:**
- Creates a new `graph_id` (e.g. `mirofish_6f14c7f130e8` → different from original)
- The original graph's data is still in Zep but the new simulation points to the new graph
- If a simulation was created against the original graph, it becomes orphaned — the simulation still references the old graph_id but the project now points to the new one
- Can waste Zep Cloud quota (rebuilding 119 chunks = ~119 API calls = ~35-40% of daily Free Tier quota)

**Correct usage:**
| Parameter | Use case | Effect |
|---|---|---|
| `reset=true` | Graph build failed mid-way; retry from same project | Rebuilds with same project_id, same graph_id |
| **No parameter** | First-time build or normal rerun | Default: creates new graph on first build, returns existing on subsequent calls |
| ❌ `force=true` | **Only** when you explicitly want to replace a production graph with a new ontology | Destructive: new graph_id, old orphaned |

**Rule:** NEVER use `force=true` in diagnostic or reconnaissance API calls. A simple `GET /api/task/{task_id}` or `POST /api/graph/build` with no parameters is sufficient for state checking. When you need to diagnose a build issue, use read-only endpoints only.

---

### 24. Watcher Script Via Heredoc Fails (Exit 127 / IOCTL Error)


**Symptom:** A watcher script created via shell heredoc piping in a terminal command fails immediately with:
```
bash: Kann die Prozessgruppe des Terminals nicht setzen (-1).: Unpassender IOCTL (I/O-Control) für das Gerät
bash: Keine Jobsteuerung in dieser Shell
bash: /tmp/run-A-real-watcher.sh: Datei oder Verzeichnis nicht gefunden
```
Exit code 127.

**Root cause:** When Hermes executes a heredoc-based script via `terminal()`, the inline heredoc content is piped through a shell snapshot mechanism that may not properly write to `/tmp`. The `chmod` sets executable permissions, but the file content never actually landed on disk — the bash process sees an empty/non-existent file.

**Fix — Use `write_file` tool for script creation, then `terminal()` for execution:**

```python
### 1. MiniMax-M3 max_tokens Truncation


**Symptom:** Ontology generation returns empty/truncated JSON. JSON parse error at a specific character position — typically an `"Unterminated string"` error mid-document. The response may look empty or truncated to a few hundred chars when it should be 6000+.

**Root cause:** MiniMax-M3 produces reasoning tags (````) before the JSON output and wraps JSON in markdown codeblocks (` ```json\n...\n``` `), inflating raw completion characters to 6000-8000. Default `max_tokens=4096` in `chat_json()` truncates the response mid-JSON. Additionally, if the JSON-stripping regex expects clean JSON but encounters codeblock wrappers, the content may appear empty after strip.

**Fix:** TWO places must be patched:
1. `backend/app/services/ontology_generator.py` — call to `self.llm_client.chat_json()`: pass `max_tokens=8192`
2. `backend/app/services/llm_client.py` — `chat_json()` signature: raise default from 4096 to 8192

The `chat_json()` method MUST strip both markdown codeblocks (```json...```) AND `...` reasoning tags from the response before attempting JSON parsing. This is not optional — MiniMax-M3 ALWAYS wraps JSON output in these wrappers, so without this stripping the parsed JSON will be empty or malformed:
```python
json_str = raw_response.strip()
if json_str.startswith("```"):
    json_str = re.sub(r'^```(?:json)?\s*', '', json_str)
    json_str = re.sub(r'\s*```$', '', json_str)
```

**Verification:**
```python
llm.llm_client.chat_json(
    messages=[{"role": "user", "content": "Generate 10 entity types for a multi-agent architecture discussion..."}],
    temperature=0.3, max_tokens=8192
)
```
Expected: clean JSON parse, 7500+ completion tokens, `finish_reason=stop`.

**Testing pattern (isolated, no backend):**
```bash
unset PYTHONPATH PYTHONHOME
cd ~/10-Projekte/20-experimental/MiroFish
backend/.venv/bin/python3 -c "
import sys; sys.path.insert(0, 'backend')
from app.services.llm_client import LLMClient
import os
client = LLMClient(
    api_key=os.getenv('OPENAI_API_KEY'),
    base_url='https://api.minimax.io/v1',
    model='MiniMax-M3',
)
result = client.chat_json(messages=[{'role':'user','content':'Generate JSON with keys: name, version, entities'}])
print('SUCCESS' if result else 'FAIL')
print(type(result))
" 2>&1 | tail -10
```

### 2. Backend Restart After Patch


The backend runs via npm → concurrently → python3 run.py in **Flask debug mode**. Flask debug mode spawns **two** `run.py` processes: a parent (reloader watcher) and a child (actual Flask app). Killing just the child leaves the parent to restart it; killing the parent via `pkill -f "backend/run.py"` kills both.

**Correct procedure:**
1. Patch the file(s)
2. Identify exact PIDs: `pgrep -af "backend/run.py"`
3. Kill all: `pkill -f "backend/run.py"` (or specific PIDs)
4. If port stays bound: `fuser -k 5001/tcp`
5. Restart manually:
   ```bash
   cd ~/10-Projekte/20-experimental/MiroFish
   unset PYTHONPATH PYTHONHOME
   exec backend/.venv/bin/python backend/run.py
   ```
6. Verify: `curl localhost:5001/health`

**PITFALL — Multiple backends on same port:** When you restart manually while the old npm-managed Flask reloader still holds the socket, both run.py instances listen on port 5001 via SO_REUSEADDR. The old parent is the Flask reloader, the old child is the real app. `pkill -9 -f "backend/run.py"` kills ALL run.py processes including the child that spawned the OASIS worker.

**Safer approach:** Identify exact PIDs before killing:
```bash
pgrep -af "run.py"   # shows all instances with PIDs
kill PID             # kill specific PID, not pkill -9
```

### 3. `run_state.json` vs API Endpoint Staleness (Three Levels)


There are **three distinct levels** of staleness, depending on seed size, simulation phase, and OASIS version:

#### Level 1: API Endpoint Only (standard seeds, ≤12k chars)


**Symptom:** `curl http://localhost:5001/api/simulation/{id}` returns `runner_status: running` but **all other fields are `None`** — `current_round`, `total_actions_count`, `progress_percent`, `twitter_status`, `reddit_status` — even though the simulation is actively progressing. `run_state.json` on disk shows real data.

**Root cause:** The GET simulation endpoint reads from the database (SQLite), which is NOT updated in real-time by the OASIS worker. The worker writes progress to `run_state.json` on disk instead.

**Workaround — read `run_state.json` directly:**
```bash
cat backend/uploads/simulations/{sim_id}/run_state.json | python3 -m json.tool
```

**Real data fields** (from `run_state.json`):
```json
{
  "simulation_id": "sim_...",
  "runner_status": "running",
  "current_round": 34,
  "total_rounds": 60,
  "progress_percent": 56.7,
  "twitter_current_round": 34,
  "reddit_current_round": 21,
  "twitter_status": "running",
  "reddit_status": "running",
  "twitter_actions_count": 47,
  "reddit_actions_count": 48,
  "total_actions_count": 95,
  "started_at": "2026-07-12T01:48:53"
}
```

Only the `runner_status` field from the API endpoint is authoritative for alive/dead detection. All other numeric fields should be read from `run_state.json` for accurate live data.

#### Level 2: Deep Staleness (dense seeds, >12k chars)


**Symptom:** `run_state.json` itself stays at `current_round: 0, total_actions: 0` with the `updated_at` timestamp identical to `started_at` for **10+ minutes**, even though the OASIS worker shows 99% CPU with 10+ min of accumulated CPU time. The watcher falsely reports "stuck" state.

**Root cause:** With dense seeds (>12k chars), the OASIS worker's first few LLM round calls take abnormally long (>2 min per persona per round). Since `run_state.json` is only written after **each complete round**, the state file stays frozen until the first round finishes. This can take >10 min for 3-4 profiles × dense system prompts.

**Three truth sources for dense seeds, in priority order:**
| Source | File Pattern | Updates | Best for |
|---|---|---|---|
| `simulation.log` (golden) | `simulations/{id}/simulation.log` | Real-time (per LLM call) | Live status, error diagnosis |
| Twitter DB | `simulations/{id}/twitter_simulation.db` | Per-post write | Action count, content sampling — file size grows as posts are written |
| `run_state.json` | `simulations/{id}/run_state.json` | Per-round write (10+ min lag with dense seeds) | Round counter (only when updated) |

**Workaround — DB file size as health indicator (most reliable for deep staleness):**
```bash
#### Level 3: Completely Frozen `run_state.json` (OASIS version-dependent, any seed)


**Symptom:** `run_state.json` is **never updated** — `updated_at` stays at the `started_at` timestamp forever, `current_round` stays at 0, `total_actions_count` stays at 0. **But** the simulation is clearly progressing: `simulation.log` shows Round 20+/60, the Twitter DB is growing, the worker PID shows `State: R (running)` with open file descriptors writing to logs. The `run-status` endpoint also returns frozen start-snapshot values.

**Root cause:** In some OASIS versions (observed in the version used for Skill-Chaining Sim09), the `run_state.json` writer in the OASIS worker is either absent, broken, or the state is written via a codepath that errors silently. Unlike the "deep staleness" pattern where the first round eventually completes and un-freezes state, this is a **complete absence of state updates** — the file is written once at simulation start and then never touched again.

**Distinguishing Level 2 vs Level 3 (critical for correct response):**

| Signal | Level 2 (Deep) | Level 3 (Frozen) |
|---|---|---|
| `simulation.log` round count | Rounds eventually appear after 10+ min | Rounds appear in normal cadence (1-3 min) |
| `run_state.json.updated_at` | Stays at start_time for 10+ min, then jumps to current | Stays at start_time **forever** |
| DB file growth after 3 min | 0-100 KB (first round still processing) | 300+ KB (multiple rounds done) |
| Worker PID state (from `/proc/PID/status`) | `State: R (running)`, 99% CPU | `State: R (running)`, normal CPU, fd shows open DB |
| Best response | Wait 10+ min for first round | **Immediately** switch to simulation.log monitoring |

**Diagnostic procedure for Level 3:**
```bash
### 4. Background OASIS Worker Survival After Backend Kill


**Behaviour:** If you kill the backend while a simulation is running (e.g. `pkill -9 -f "backend/run.py"`), the OASIS simulation worker **survives** because:
- It was spawned via `subprocess.Popen` with `start_new_session=True` (separate process group)
- It's a standalone Python process, not a thread or child of Flask
- Killing the parent only orphans it; it keeps running independently

**Consequence:** The simulation keeps producing posts, writing to `run_state.json` and SQLite databases. When you restart the backend, the new Flask process discovers the existing OASIS worker through the simulation data on disk and picks it up.

**Critical — Check for stale workers BEFORE starting a new run:** Lingering OASIS workers from previous runs consume 1.3+ GB RAM silently. Multiple OOM crashes in a single session are often caused by not checking for these. Always run before starting a new simulation:

```bash
ps -ef | grep -E "run_parallel_simulation|run_twitter_simulation" | grep -v grep
```

If you find one, kill it before starting a new simulation. After killing, RAM can free up 1.5-2.0 GiB instantly — this alone can turn a "stuck at 1.5 GiB free" situation into "3.3 GiB free, safe to proceed".

**Clean shutdown of everything:**
```bash
### 5. First Ontology Call Is Slow


Takes 60-90s on MiniMax-M3 (second call ~30-40s). Do NOT timeout at 30s.

### 6. Zep API Limits


Max 10 entity types, max 10 edge types. Generator must not request more.

### 7. File Attachment Failure


After project creation, verify `files_count > 0`. If 0, retry with explicit `-F "files=@..."`.

### 8. User-Started Parallel Simulations


**Symptom:** You're monitoring a simulation running via the API pipeline, but the user reports seeing a different simulation (or an empty/landing page). Two simulation IDs exist — one created by the agent's pipeline, one started by the user from the MiroFish landing page UI.

**Root cause:** The MiroFish landing page (`http://localhost:3000/`) has a Create flow where the user can independently start a new simulation by entering parameters and clicking "Start". This creates a second simulation with a different ID that the agent doesn't know about. The user may also pass query parameters like `?maxRounds=60` directly in the URL.

**Prevention — Before creating a new simulation, check for ALL existing ones:**
```bash
curl -s http://localhost:5001/api/simulation/list | python3 -c "
import json, sys
d = json.load(sys.stdin)
sims = d.get('data', [])
print(f'Found {len(sims)} existing simulations:')
for s in sims:
    sid = s.get('simulation_id', '?')
    status = s.get('status', '?')
    name = s.get('name', s.get('project_name', '?'))
    print(f'  {sid} | {status} | {name}')
"
```

**Resolution when user has a different simulation ID:**
1. Ask the user which simulation they're looking at (the URL in their address bar shows the simulation ID)
2. Check both simulations: `curl -s http://localhost:5001/api/simulation/{sim_id_a}` and `{sim_id_b}`
3. Read `run_state.json` for both to determine real progress vs stuck API data
4. Generate reports for the completed one(s) and offer the view URLs

**Note:** The user's simulation (started from UI) may have different parameters (maxRounds, platform) than the agent-created one. Both run concurrently as independent OASIS worker processes.

### 9. Zep `source_targets` Edge-Type Limit (Max 10 Pairs)


**Symptom:** Graph build returns error: `source_targets cannot contain more than 10 items (max)`. The project was created with a seed that references many entity combinations.

**Root cause:** Zep Cloud's ontology schema limits each edge type to max 10 `source_targets` pairs (the LLM-generated ontology may produce 11-12 pairs when the seed is rich in entity relationships).

**Fix:** Patch the ontology generator to truncate edge `source_targets` to max 10 before sending to Zep. In `backend/app/services/ontology_generator.py`, wrap the Zep API calls with:
```python
for edge in result["edge_types"]:
    if "source_targets" in edge and len(edge["source_targets"]) > 10:
        edge["source_targets"] = edge["source_targets"][:10]
```

**Verification:** Before calling the graph build, check the generated ontology:
```bash
curl -s http://localhost:5001/api/project/<proj_id> | python3 -c "
import json, sys
d = json.load(sys.stdin)['data']
print(f'Entity types: {d.get(\"entity_types_count\")}')
print(f'Edge types: {d.get(\"edge_types_count\")}')
"
```

### 10. RAM Budget Planning


**Symptom:** MiroFish simulation gets killed (OOM-killer) or the system becomes unresponsive during graph build or simulation run.

**Root cause:** The OASIS simulation worker consumes ~1.3 GB RSS. Combined with Hermes CLI server (~870 MB), Hermes Desktop (~1.1 GB), Brave browser (~700 MB+ per window), and system services, total usage can exceed 15 GB physical RAM.

**Memory budget checklist (for 15 GB total):**
| Component | Typical RSS | Notes |
|---|---|---|
| OASIS Worker | ~1.3 GB | MiroFish sim process |
| Hermes CLI server | ~870 MB | Python -m hermes_cli |
| Hermes Desktop | ~1.1 GB | Electron app |
| Brave Browser | ~700 MB+ per window | Each renderer ~250-350 MB |
| GNOME Shell | ~420 MB | |
| Other system | ~2 GB | Everything else |
| **Minimum needed** | **~7 GB free** | To avoid OOM during LLM calls |

**RAM-saving strategies:**
1. Close unused Brave tabs (each tab costs 250-350 MB)
2. Avoid running MiroFish + another large LLM process (e.g. Ollama, vLLM) simultaneously
3. Monitor RAM before each heavy step: `free -h`
4. If the simulation's prepare step fails silently (stuck in "preparing"), check for OOM traces in `dmesg | tail -20`
5. zram provides ~8 GB swap cushion but shouldn't be relied on for steady-state

### 11. Mnemosyne Sleep Cron Kills Long-Running Simulations


**Symptom:** After ~02:30, MiroFish backend and/or OASIS worker disappear. The simulation stops mid-run and can't be resumed.

**Root cause:** The `mnemosyne sleep` cron (02:30 daily) kills processes including MiroFish's backend when freeing memory. This is a durable fact — Mnemosyne's nightly cleanup is designed to reclaim resources and doesn't discriminate between processes.

**Prevention:** Before starting a long simulation (>1h expected), warn the user and suggest:
1. Pause/skip Mnemosyne sleep for tonight: `hermes cron list && hermes cron pause <id>`
2. Or start the simulation early enough (>3h before 02:30) that it completes before the cron fires
3. Long-run simulations should start before 23:00 max

**Recovery after Mnemosyne kill:**
1. Check if backend survived: `curl -s http://localhost:5001/health`
2. Check if OASIS worker survived: `ps aux | grep run_parallel_simulation`
3. Both processes are typically dead. The graph is persistent (in Zep Cloud); the simulation's `run_state.json` will show the round it died on, but OASIS workers don't resume. Start a new simulation from the same project.

### 12. Vue SPA Doesn't Refresh (Landing Page Stuck)


**Symptom:** User enters a simulation URL (`http://localhost:3000/simulation/sim_xxx/start`) but sees only the landing page. The Vue frontend doesn't detect the route change.

**Root cause:** The MiroFish frontend is a Vue SPA that loads all pages from the same `index.html`. If the Vue Router cache is stale or the initial route was `/`, the router may not pick up URL changes made in the address bar.

**Fix:** Hard refresh: `Ctrl+Shift+R` (clears Vue SPA cache). In Brave/Chrome, you can also open DevTools (F12) → Network → "Disable cache" checkbox, then reload.

**Verification:** After hard refresh, check the browser URL matches `http://localhost:3000/simulation/sim_xxx/start`. The Vue Router should now pick it up.

### 13. Two Concurrent Simulations = Triangulation (Not a Bug)


**Symptom:** Two simulations are running simultaneously on the same topic — one created by the agent's API pipeline, one started by the user from the landing page UI. Both have different simulation IDs and different parameters.

**Root cause:** This is a deliberate feature, not a bug. The MiroFish landing page Create flow is independent of the API pipeline. When the user starts a simulation from the UI while the agent is also running one, the two simulations run concurrently as independent OASIS worker processes.

**Value:** Two simulations on the same topic with different seeds (or slightly different configurations) reveal consensus vs divergence far better than either simulation alone. They typically produce different report output shapes (Future Prediction vs Structured Analysis — see Step 3a).

**Resolution:** 
1. Monitor BOTH simulations via `curl -s http://localhost:5001/api/simulation/list`
2. When both complete, generate both reports
3. Do a cross-comparison (see Step 3b: Multi-Run Comparison)
4. Write a synthesis document

**PITFALL — Direct URL delivery:** When the user asks for a link or URL to a simulation, deliver only the URL, no explanation. The user knows what they want. Example: `http://localhost:3000/simulation/sim_xxx/start`

### 14. User-Initiated Crash Recovery (RAM / OOM)


**Symptom:** The user reports the system is overloaded or the simulation dies mid-run.

**Recovery procedure when MiroFish is completely down:**
1. Clean kill all MiroFish processes: `pkill -f "run.py"; pkill -f "run_parallel_simulation"; pkill -f "vite"`
2. Verify ports free: `ss -tlnp | grep -E "5001|3000"`
3. Check RAM: `free -h` — need at least 4 GB free before restart
4. Start backend: `cd MiroFish && unset PYTHONPATH PYTHONHOME && backend/.venv/bin/python backend/run.py &`
5. Verify: `curl localhost:5001/health`
6. Start frontend: `cd frontend && npm run dev`
7. Verify: `curl localhost:3000`

**PITFALL — Scope reduction after crash:** When the user says to reduce scope after an OOM crash, reduce the simulation scope (fewer personas, smaller seed, fewer rounds) rather than trying to run the same heavy simulation again. This is the user's preferred recovery strategy.

for current RAM state.

---

#### Three Skill Types


| Skill-Type | What it provides | Bias-Inheritance | Setup-Time | Best for |
|---|---|---|---|---|
| **Fresh** (no skill) | Nothing — Zep generates everything from seed | None | 5-7 min | Baseline, max surprise |
| **Template-Skill** | Persona-skeleton (7 functional slots) + empty 6-cluster findings architecture + tone-constraint | None (form-only) | 3-5 min | Format-consistency test, bias-free speed |
| **Derived-Skill** | Deterministic 10-persona-set + filled 6-cluster-architecture (with inherited priorities) + mandatory bias-disclosure-header | **High** (inherits source priorities) | 2-4 min | Reproducibility test, max bias-inheritance measurement |

#### Seed Structure for Skill-Chaining Runs


```
Section A — Topic Introduction with Skill-Type taxonomy
Section B — Persona-Beschreibungen (10 x voll ausformuliert, Englisch)
Section C — Research Question (DE + EN)
Section D — Drei-Run-Schema mit Skill-Diffs
Section E — Konfliktlinien (mind. 3, zeitlich gestaffelt)
Section F — Metriken-Definition
Section G — Stop-Words / Out-of-Scope (hard scope-limit)
Section H — Closing Brief Template
```

#### Template-Skill Blueprint


YAML-frontmatter with `type: template`. Content:
- **7 functional slots** (Architecture-Synthesist, Cost-Optimizer, Quality-Gate-Owner, Operator/SRE, Vendor-A managed, Vendor-B open-weight, Academic-Ethics-Critic) — handles left to Zep
- **6 empty cluster skeleton** (Layering/Cost/Auditability/Recovery/Reviewer-Model/EU-Compliance)
- **Tone-constraint** (DE/EN bilingual, technical-analytical, conflict-oriented)
- **Bias-Selbstauskunft** declared as `inherited_from: none` (form-only, no bias)
- **Anti-Patterns section** (what Zep MUST NOT derive from this skill)

#### Derived-Skill Blueprint


YAML-frontmatter with `type: derived` and `derived_from: [report_id_a, report_id_b, ...]`. Content:
- **Source-Disclosure** table (report-id, bytes, style, primary-focus, source-path)
- **Bias-Inheritance-Selbstauskunft** — explicit statement of which Findings-Schwerpunkte are inherited
- **Deterministic 10-persona-set** with `@`-handles, 1-sentence-role, and a **Zep-Override-Forbidden** flag on both handles and roles
- **6-cluster architecture** with:
  - Fixed cluster names
  - Inherited priority levels (HIGH / MEDIUM / LOW)
  - Must-cover topics per cluster
  - Expected-quotes-examples (paraphrased, not verbatim from source)
  - Bias-risk warnings per cluster
- **Trade-off Profile** table vs Fresh vs Template
- **Königin validation checks** (10@-handles appear, 6 clusters match, bias-disclosure surfaced)

#### Cross-Run Comparison Methodology


After all 3 runs complete, produce a **Cross-Run-Empfehlungs-Memo**. For a deeper quantitative breakdown, use the **5-dimensional sub-analysis framework** (see `references/sim09-sub-analysis-framework.md`):

1. **Persona-Workload** — which persona dominated which run
2. **Insight-Diversity** — meta vs cluster-repetition vs fresh-insights ratio
3. **Discourse-Function** — position vs challenge vs resolution per run
4. **Word-Cloud Drift** — topic shift via 2-gram frequency
5. **Hashtag/Handle Tracking** — skill-emergent topic markers

Sim09 baseline: 23% cluster-repetition for Derived (0% for Template), only 4 shared 2-grams across all 3 runs.

```markdown
| Skill-Type | Konsens-Punkte | Risiken |
|---|---|---|
| Fresh (Run A) | (was universally agreed) | (what went unaddressed) |
| Template (Run B) | (was universally agreed) | (where empty template constrained useful conflict) |
| Derived (Run C) | (was universally agreed) | (which blind spots were inherited) |
```

End with **ONE explicit recommendation** in the form:
> *"For Q3/Q4-2026 multi-agent simulation campaigns, recommend Skill-Type `X` for question-type `Y`, because `Z`. Skill-Type `W` is contra-indicated because `V`."*

#### Validation Checks (Königin, pre-launch)


Before launching a Derived-Skill Run C:

1. All 10 persona @-handles appear in Zep-output → expected: true
2. All 10 persona 1-sentence-roles match (semantically-or-verbatim) → expected: true
3. 6 cluster-names match exactly → expected: true
4. 6 cluster-priorities match inherited schema (HIGH/HIGH/HIGH/MEDIUM/MEDIUM/MEDIUM) → expected: true
5. Bias-disclosure-header surfaced in Zep-output → expected: true

If any validation fails → abort Run C, fix Zep-payload, re-run.

#### Conflict-Line Staffelung (Zeitliches Routing)


Empfohlene Staffelung über 60 Rounds:
- **Rounds 1-15**: Conflict 1 (Setup-Zeit vs Anpassungs-Aufwand) — `@cost_cfo` ↔ `@quality_gate`. Schnell zu klären, schafft Faktenbasis.
- **Rounds 20-45**: Conflict 2 (Konsistenz vs Bias-Vererbung) — `@basti_synth` ↔ `@academic_eth`. Braucht Findings-Material aus ersten Runden.
- **Rounds 40-60**: Conflict 3 (Self-Hosting vs API-Skill-Cloud) — `@mistral_vendor` ↔ `@openai_vendor`. Hängt von vorheriger Skill-Hosting-Entscheidung ab.

Diese Staffelung verhindert parallele Eskalation aller drei Konflikte und Fragmentierung der Diskussion.

#### Project-Isolation-Rule


Each run uses its OWN MiroFish project (separate Zep-graph, separate simulation). Naming convention:
- `Sim<XX>-SkillChaining-RunA-Fresh-<YYYY>`
- `Sim<XX>-SkillChaining-RunB-Template-<YYYY>`
- `Sim<XX>-SkillChaining-RunC-Derived-<YYYY>`

Cross-contamination of graph-state between runs invalidates all three.

See `references/skill-chaining-architecture.md` for the original skill-chaining blueprint with concrete examples from Sim09.

For multi-generation derived-skill-authoring (creating deterministic `derived-from-gen-N.md` files for bias-drift or reproducibility studies across Gen 0/2/4), see `references/derived-skill-authoring-pattern.md` — covers YAML-frontmatter conventions, persona-set cross-validation, drift-vector annotations, re-inheritance-risk analysis, and the Stale-State-Workaround.

---

---

## Skills-Version History


- v2.6 (2026-07-13): Added Step 3a-iv (Insight Diversity & Discourse Sub-Analysis) with 5 quantitative dimensions: Persona Workload, Insight Diversity (Meta/Repeat/Fresh), Discourse Function (Position/Challenge/Resolution), Word Cloud Drift, Hashtag Overlap. Integrated Sim09 calibration tables (23% bias inheritance for Derived, 37% fresh for Template, 4 common 2-grams across all 3 runs). Added Skill-Type recommendation table (Discovery→Fresh, Methodology→Template, Compliance→Derived).

- v2.4 (2026-07-13): Report timing scales with post count (30-90s for ~41 posts, 6+ min for 169 posts). Updated evidence file with Run B completion data (169 posts, 60/60 rounds, 274 actions) and Run C start (Derived, 24 initial posts). Documented report generation timeline for large runs.

- v2.3 (2026-07-13): Added Pitfalls 34-35. Updated Pitfall 18 for "den kompletten link" pattern (all URLs in one response, no explanation). Learned from Sim09 Skill-Chaining Run A/B: npm run dev --kill-others cascade kills discovered as root cause of recurring backend+worker death; inline worker pattern (pgrep fails) discovered during dynamic PID troubleshooting.
- v2.0 (2026-07-13): Added Pitfall 3 Level 3 (Completely Frozen run_state.json). New diagnosis pattern for OASIS versions that never write run_state.json. Added references/liveness-diagnosis.md with ready-to-run diagnosis script. Patched robust-watcher.py → v4 with primary simulation.log monitoring.
- v1.9 (2026-07-13): Added Step 5f (Skill-Chaining Simulation Archetype). Documented 3-skill-type spectrum (Fresh/Template/Derived), bias-disclosure format for derived skills, deterministic persona-sets with Zep-override-forbidden flag, cross-run comparison schema with closing-brief template, and Königin validation checks. Added references/skill-chaining-architecture.md.
- v1.8 (2026-07-13): Added Step 5 (Max-Kampagne Deck). Documented 10-card pattern, one-pager workflow, subagent-based seed+skill creation for A/B/C multi-run, seed structure, and two seed styles. Added references/max-kampagne-deck.md.
- v1.7 (2026-07-12): Added Step 3c (Post-Run Interactive Agent Chat).
- v1.5 (2026-07-12): Expanded pitfall 3 to cover two levels of staleness (API-only deep staleness with dense seeds). Added DB file size as liveness signal and simulation.log as golden truth source. Removed duplicate pitfall 18 (merged into pitfall 3). Updated `templates/robust-watcher.py` to detect deep staleness via DB file growth.
- v1.4 (2026-07-12): Added seed-density correlation insight (more seed ≠ more output, determines output TYPE). Added simulation speed estimation table (3 personas = 7x faster than 7). Added pitfalls 13-14: concurrent-sim triangulation, Hermes watcher termination, OOM recovery with scope reduction. Added `references/seed-density-correlation.md` and `templates/robust-watcher.py`. Added Basti's brainstorming seed preferences (performance/reliability focus, code snippets, quantitative arguments).
- v1.3 (2026-07-12): Added chunk_size/overlap graph density params, prepare/status endpoint, `--reset` rebuild flag. Added pitfalls 9-12: Zep edge pair limit, RAM budget, Mnemosyne cron conflict, Vue SPA hard refresh fix.
- v1.0 (2026-07-12): Initial creation. Pipeline + MiniMax-M3 pitfall + runbook pattern.