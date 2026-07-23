---
name: simulation-brainstorm-learning
description: |
  Use when extracting architectural lessons from completed persona-driven simulation reports, interviewing the report through fixed questions, or verifying proposed edits against source data.
  NOT for running simulations, authoring personas, or drawing conclusions when the original posts and completed report are unavailable.
  Produces a source-verified IST-to-SOLL workshop with gaps, concrete edits, and archival outputs for the vault and Mnemosyne.
version: 0.3.0
author: Hermes
metadata:
  hermes:
    tags:
    - Simulation
    - Brainstorm
    - Workshop
    - Multi-Agent
    - Verification
license: MIT
trigger_keywords: ['completed', 'report', 'edits', 'source', 'extracting']
keywords: ['completed', 'report', 'edits', 'source', 'extracting']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

# Simulation Brainstorm Learning

Extract architectural learnings from multi-persona simulation reports (MiroFish, OASIS, similar) by running a 5-question Report-Agent interview, then verifying every answer against the original source data. The skill delivers a 4-phase workshop artifact (IST→SOLL→Gap→Edits) ready for vault + Mnemosyne archival.

This skill does **not** cover: running the simulation itself, persona authoring, or Hermes-V7-specific topic modeling. It assumes the simulation is already `completed` and the source data is readable.

## When to Use

- "Lass uns das mal mit Personas durchsimulieren" + post-run review
- "Was hat die Sim eigentlich ergeben?" (after a completed brainstorms run)
- "Bevor wir X bauen, lass uns das im Schwarm diskutieren"
- "Verifizier mal was der Report-Agent behauptet"
- Any post-mortem of a completed multi-persona simulation
- **"Werte mir die ergebnisse aus"** / "sub-analyse" / "detaillierte sub-analyse" — triggers the 5-dimensional quantitative analysis (see §Quantitative Sub-Analysis below)

## Prerequisites

- Completed simulation with `status=completed` (read-only mode after that)
- Source data accessible: Twitter/Reddit SQLite DB + profiles CSV + report markdown
- Report-Agent chat endpoint reachable (browser or `report/chat` API)
- Mnemosyne CLI for archival: `~/.hermes/hermes-agent/venv/bin/mnemosyne`
- Obsidian vault at `~/Dokumente/Obsidian Vault/` (or equivalent)

## How to Run

1. Confirm simulation is `completed` (Hermes rule: read-only after that).
2. Invoke `read_file` / `search_files` to load all source posts and the report MD.
3. Formulate **5 questions** across perspectives (see Procedure §3).
4. Send questions to Report-Agent one at a time via browser or `report/chat` API.
5. For each answer: invoke `terminal` to cross-check claims against source posts (Pitfall #5).
6. Document in 4-phase format using `write_file`.
7. Archive to vault (`02 Inbox/`) + Mnemosyne (`mnemosyne store`).

## Quick Reference

| Action | Tool |
|---|---|
| Check simulation status | `read_file` on `run_state.json` |
| List all posts | `terminal` + `sqlite3 twitter_simulation.db` |
| Save report MD | `write_file` to `~/path/MiroFish/<report_id>.md` |
| Verify answer claim | `search_files` for claim substring in posts |
| Archive to vault | `write_file` to `02 Inbox/YYYY-MM-DD - <Title>.md` |
| Store to memory | `mnemosyne store "<content>" <source> <importance>` |
| Verify recall | `mnemosyne recall "<query>" 3` |

## Procedure

### 1. Verify simulation is complete

```bash
# Via terminal — read run_state.json
cat /path/to/sim/run_state.json | jq '{status, current_round, total_actions_count}'
```

If `status != completed`, **wait** until it is. Mnemosyne-Context lesson: reading during active run wastes DB queries.

### 2. Load source data

```bash
# List personas + their first 400-char descriptions
sqlite3 twitter_simulation.db ".schema post"
sqlite3 twitter_simulation.db "SELECT user_id, COUNT(*) FROM post GROUP BY user_id;"

# Save report markdown
curl -s http://localhost:5001/api/report/<report_id> | jq -r '.data.markdown_content' \
  > /path/to/MiroFish/<report_id>.md
```

### 3. Formulate 5 questions across perspectives

| # | Angle | Example |
|---|---|---|
| 1 | **Take-Aways (broad)** | "Was sind eure drei wichtigsten Take-Aways?" |
| 2 | **Controversy trigger** | "Persona A vs. Persona B: wer hat bei Konflikt X das letzte Wort?" |
| 3 | **Prioritization** | "Ranke Items nach TTI/RIS/CTM" |
| 4 | **Reality check** | "Welche Vendor-Claims sind nicht belegbar?" |
| 5 | **Meta-question** | "Wenn nur EINE Regel — welche?" |

### 4. Send to Report-Agent

Browser path: open `<frontend>/report/<report_id>` and type questions.
API path:
```bash
curl -X POST http://localhost:5001/api/report/chat \
  -H "Content-Type: application/json" \
  -d '{"simulation_id":"<sim_id>","report_id":"<report_id>","message":"<question>"}'
```

Mnemosyne-Lesson: endpoint expects field `message` (not `question`). Hermes-CLI auto-skips `hermes send` when session-target matches delivery target — content goes via final response.

### 5. Verify each answer (Pitfall #5)

For every claim in every answer, search the original posts:

```bash
grep -i "<claim-substring>" /tmp/posts_dump.txt
```

Cross-check between answers: does Answer N contradict Answer N±1? In this session, Answer 5 contained 2 contradictions against Answers 2+3 (verified mechanically, not asserted).

### 6. Document in 4-phase workshop format

Use `write_file` to create `~/docs/system/<topic>-workshop.md`:

1. **Phase 1 IST** — 5 answers extracted with original quotes
2. **Phase 2 Verification** — contradictions + corrections (Pitfall #5 log)
3. **Phase 3 SOLL** — items grouped by Layer (Atom/Molekül/Organism)
4. **Phase 4 Edits** — 7+ prioritized actions (P0/P1/P2) with code snippets

### 7. Archive to vault + Mnemosyne

```bash
# Inbox entry (compact, points to workshop doc)
write_file → ~/Dokumente/Obsidian Vault/02 Inbox/YYYY-MM-DD - <Title>.md

# Mnemosyne (4 items max — 1 per category)
mnemosyne store "<P0-findings summary>" fact 0.70
mnemosyne store "<methodology lesson>" self-improving 0.65
mnemosyne store "<tool/pattern lessons>" insight 0.55
```

Verify with `mnemosyne recall "<query>" 3` — each stored item should appear with score > 0.30.

## Alternative Track: Quantitative Sub-Analysis (5-Dimensional)

For multi-run comparisons (2+ simulations on same topic with different skill types), skip the Report-Agent interview and use this quantitative analysis instead. Trigger: "werte mir die ergebnisse aus", "mach ne detaillierte sub-analyse", "detailing".

Load `skill_view(name='simulation-brainstorm-learning', file_path='references/cross-run-diff-methodology.md')` for the full cross-run comparison framework with Sim09/Sim10 baselines and Diff-Methodik (two triads with same setup, different research question).

### The 5 Dimensions

| # | Dimension | Measures | Method |
|---|---|---|---|
| 1 | **Persona-Workload** | Who speaks, how often, per run | SQL `GROUP BY user_id` |
| 2 | **Insight-Diversity** | Meta vs Cluster-Rep vs Fresh ratio | Concept-cluster substring matching |
| 3 | **Discourse-Function** | Position / Challenge / Resolution ratio | Keyword triage |
| 4 | **Word-Cloud Drift** | Topic shift via N-gram frequency | `collections.Counter` on 2-grams |
| 5 | **Hashtag Tracking** | Skill-emergent topic markers | grep frequency |

### Sim09 Baselines (reference thresholds)

| Metric | Fresh | Template | Derived |
|---|---|---|---|
| Persona-Dominance | Dispersed | Zep-Ops ~50% | Skill-Self ~60% |
| Cluster-Repetition | 0% | 0% | 23% |
| Fresh Insights | 10% | 37% | -7% |
| Challenge-Rate | 10% | 6% | 14% |
| Common 2-Grams across | 4 total | 4 total | 4 total |

### Pitfall: Quantitative ≠ Report-Agent

Report-Agent interview = qualitative depth (explains WHY). Quantitative = structural fingerprints (measures WHAT). Use quantitative first (detect patterns) then Report-Agent (explain them).

---

## Pitfalls

When the user asks for detailed cross-run comparison (e.g. "werte mir die ergebnisse aus", "sub-analyse", "detaillierte analyse"), the interview-based approach is too shallow. Use **direct SQLite analysis** across 5 quantitative dimensions instead.

**When to choose this path over the interview path:**
- Two+ completed simulations on the same topic (A/B/C runs)
- User asks for bias-inheritance quantification
- User wants word-cloud drift, discourse function, or persona-workload data
- The interview path feels thin / "the agent just agrees"

### Prerequisites

- All simulations are `completed` (data extraction only after run is done)
- SQLite DBs accessible (`twitter_simulation.db`, `reddit_simulation.db`)
- Posts dumped to JSON or queried directly from DB
- Optionally: the report markdown saved to disk

### How to Run

1. Confirm ALL simulations are `completed` (`run_state.json` status check)
2. Extract all posts from each simulation's SQLite DBs to JSON
3. For each dimension, run the analysis across all runs
4. Write a structured Markdown report with cross-run comparison tables
5. Save to `~/MiroFish/<run-name>-sub-analysis.md`

### The 5 Dimensions

#### D1: Persona Workload Distribution

Count posts per user across runs. Reveals which skill-type shifts discourse dominance.

```sql
SELECT user_id, COUNT(*) as cnt FROM post GROUP BY user_id ORDER BY cnt DESC;
```

**Calibration (from Sim09):** Fresh = dispers (all personae contribute); Template = Ops-fokussiert (50%+); Derived = Skill-Selbst (60%+).

#### D2: Insight Diversity (Meta vs Repeat vs Fresh)

Classify each post heuristically:
- **Meta-Reflection**: Contains simulation/bias/consensus/finding keywords — the agent reflects on the simulation itself
- **Cluster-Repetition**: Contains verbatim 3+ word clusters from earlier runs' source material
- **Fresh-Insight**: Neither — genuinely novel content

```python
def classify(content, known_clusters):
    if any(p in content.lower() for p in known_clusters):
        return "repeat"
    if any(w in content.lower() for w in ["simulation","bias","consensus","finding"]):
        return "meta"
    return "fresh"
```

**Calibration (Sim09):** Run B Template had 37% fresh-0% repeat (sweet spot); Run C Derived had 23% repeat (bias confirmed).

#### D3: Discourse Function (Position vs Challenge vs Resolution)

Tag each post. Low effort: search for disagreement markers ("but", "however", "actually,", "wrong", "contradict") vs agreement markers ("agreed", "makes sense", "valid point").

**Calibration (Sim09):** Derived runs trigger most Challenges (14%); Fresh runs have zero Resolutions.

#### D4: Word Cloud Drift

```python
import re
from collections import Counter
text = " ".join(p["content"] for p in all_posts)
clean = re.sub(r'[^\w\s]', ' ', text.lower())
words = [w for w in clean.split() if len(w) > 4]
c = Counter(words).most_common(15)
```

Compare top words across runs. **Calibration (Sim09):** Fresh→`drift/jaccard`, Template→`schema/layer/boundary`, Derived→`compliance/provenance/signed`.

#### D5: Hashtag / Cross-Run Phrasal Overlap

```python
import re
from collections import Counter
hashtags = re.findall(r'#\w+', " ".join(p["content"] for p in all_posts))
c = Counter(hashtags).most_common(10)
```

When a hashtag appears in only one run, it's a skill-inherited bias signal.

### Tooling

Use `python3` with standard lib only (json, sqlite3, re, collections.Counter). Run as a single terminal command per analysis:

```bash
python3 << 'PYEOF'
import json, re, sqlite3
from collections import Counter
# ... analysis code ...
PYEOF
```

Save results to `~/MiroFish/<run-name>-sub-analysis.md`. Include calibration tables from Sim09 (see `references/cross-run-diff-methodology.md` in this skill).

### Pitfalls

- ❌ Don't read from DB while simulation is still running — wait for `completed` status
- ❌ Don't run all 5 analyses in separate tool calls — batch into one Python script
- ❌ Don't declare bias without evidence — use the calibration thresholds above
### Pitfalls

- **OOM risk:** OASIS Worker alone needs ~1.3 GiB. RAM-cleanup (kill old Brave-tabs) before run.
- **Watcher timeout:** Hermes terminates `notify_on_complete=true` background watchers after ~10–15 min. Use log-file watchers without `notify` or a cron wrapper.
- **`max_tokens`:** Seed size × 0.7 = expected output, +50% buffer. 8192 was enough for V1/V2, V3 needed 16384.
- **Report-Agent field name:** Endpoint takes `message`, not `question`. Wrong field returns silent error.
- **Hermes-CLI auto-skip:** `hermes send --to telegram:<id>` skips when session-target matches. Content reaches user via final response, no manual send needed.
- **Hallucination in answers:** Even plausible-sounding Subagent output may contradict source. **Always grep source for claim substrings**, not "the answer sounds right".
- **Mnemosyne sleep cycles:** Memory consolidation runs 02:30, LLM summarization often fails (`llm_available=False`), AAAK compression is fallback. Don't rely on real-time LLM summary.

## Verification

### Sim10 Hypothesis-Driven Prediction Pattern

For bias-inheritance studies (comparing N generations of the same simulation with different skill-inheritance depths), add this **prediction-verification loop** before the quantitative analysis:

1. **Predict first:** Before running Gen N, state explicit predictions for:
   - **CDI (Concept Drift Index):** % of Gen N posts that directly reference Gen 0 concepts
   - **INS (Insight Novelty Score):** % of Gen N posts that are genuinely new (not cluster-repetition)
   - **Cluster-Saturation:** % of Gen N posts that repeat verbatim clusters from Gen N-1
   - **Dominant Cluster:** Which MiroFish cluster (Auditability/Cost/Layering/etc.) will dominate

2. **Run Gen N** (60 rounds), extract all posts to JSON

3. **Measure actual values** using the 5-dimensional framework

4. **The gap between prediction and reality IS the finding.** Example from Sim10 Gen 0:
   - Predicted Auditability 40-50% → Actual 25% (skill-independent cluster distribution is broader)
   - Predicted Recovery 1-2% → Actual 1% (confirmed: Recovery is structurally under-discussed)

### Example: Sim10 Gen 0 Baseline Findings

From the session 2026-07-14 (167 posts, 60 rounds, no skill):

| Cluster | Gen 0 Hit Rate | Sim09 Run A (41 posts) | Δ |
|---|---|---|---|
| Auditability | 25% | 63% | Broader distribution without skill |
| Cost | 25% | 41% | Skill compresses to fewer clusters |
| Layering | 14% | 24% | Similar ratio |
| Reviewer_Model | 10% | 22% | Less dominance |
| EU_Compliance | 3% | 24% | Drastically less |
| Recovery | 1% | 22% | Nearly absent |

**Key insight:** Fresh (no-skill) runs produce BROADER cluster distribution, not just different values. The skill's effect is CONCENTRATION, not DIRECTION.

**Cross-run metric extraction commands (batch):**

```python
# Combined cluster hit extraction (Python std lib)
import json, re
CLUSTER_MARKERS = {
    'Layering': ['layering','layer','sandbox','sub-layer'],
    'Cost': ['cost','routing','three-tier','c0-c4'],
    'Auditability': ['audit','byte-identical','replay','gate-decision'],
    'Recovery': ['recovery','retry','reassign','checkpoint','heartbeat','idempotency'],
    'Reviewer_Model': ['reviewer','factchecker','review-process'],
    'EU_Compliance': ['eu ai act','compliance','data-residency','self-host']
}
text = ' '.join(p.get('content','') for p in all_posts).lower()
for cluster, kws in CLUSTER_MARKERS.items():
    hits = sum(text.count(kw) for kw in kws)
    print(f'{cluster}: {hits}')
```

A workshop is valid when:

```bash
# 1. All 5 answers cross-checked
for n in 1 2 3 4 5; do grep -c "Answer $n\|Antwort $n" <workshop>.md; done  # ≥5 matches

# 2. ≥1 contradiction logged per 5 answers
grep -c "Widerspruch\|contradiction" <workshop>.md  # ≥1

# 3. ≥7 prioritized edits
grep -cE "^### (Edit|Prio)" <workshop>.md  # ≥7

# 4. Vault entry exists
ls ~/Dokumente/Obsidian\ Vault/02\ Inbox/ | grep "$(date +%Y-%m-%d)"  # ≥1

# 5. Mnemosyne recall works
mnemosyne recall "<topic keywords>" 3 | grep -c "Score:"  # ≥1
```

If any check fails, the workshop is incomplete — re-run the missing step.