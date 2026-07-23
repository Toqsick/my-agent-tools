# MiroFish Operational Experience — Session 2026-07-13/14

> Collection of crash patterns, workarounds, and techniques discovered during Sim09 + Sim10 (skill-chaining bias-reproducibility study, ~10h continuous runtime).

## Crash Patterns

### `npm run dev` → `concurrently --kill-others` cascade kill

**Symptom:** Backend dies, Frontend dies, all DB writes stop mid-run. `ps auxf` shows no OASIS worker. Happened **~6×** in one session.

**Root cause:** `npm run dev` uses `concurrently --kill-others`. When ONE process exits (backend from BertSdpaSelfAttention warning), the flag kills ALL processes — including the OASIS worker and frontend.

**Fix:** Start backend + frontend SEPARATELY:

```bash
# Terminal 1
cd ~/10-Projekte/20-experimental/MiroFish/backend && python3 app.py &
# Terminal 2
cd ~/10-Projekte/20-experimental/MiroFish/frontend && npx serve -s build -l 3000 &
```

**Never use `npm run dev` for simulation runs.**

**Verification:** With separate PIDs, backend survives worker crashes. Worker auto-respawns via internal Watchdog.

### Zep Rate-Limit 429 on parallel Graph-Builds

**Symptom:** Graph-Build fails at 15–20% with `"Rate limit exceeded for FREE plan"`. Response: `x-ratelimit-remaining: 0`.

**Root cause:** Zep FREE plan ~5 req/min. Parallel `/ontology/generate` calls exceed quota.

**Fix:** Sequential builds with retry:

```bash
# Gen 0
curl -s -X POST http://localhost:5001/api/ontology/generate ... # wait for graph_completed
# Gen 1 — only after Gen 0 is done
curl -s -X POST http://localhost:5001/api/ontology/generate ... # if 429, retry 10s
# Gen 2 — same pattern
```

One retry after 10s always works. Structure as `graph_build → wait(2min) → graph_build_followup` loop.

### Backend Watchdog respawn confusion

**Symptom:** Worker PID changes mid-run. Observer detects "Worker X TOT" but simulation continues because backend auto-respawned.

**Root cause:** MiroFish Backend has an internal `WatchdogTimer` that restarts the OASIS worker on crash. The new worker gets a different PID.

**Fix:** Check `run_state.json` for truth, not `pgrep`:

```bash
curl -s http://localhost:5001/api/simulation/<sim_id> | python3 -c "
import json,sys; d=json.load(sys.stdin)['data']
print('runner:', d.get('runner_status'))
print('round:', d.get('current_round'))
print('actions:', d.get('total_actions_count'))
"
```

If `runner_status: running` and `current_round` advances, worker is fine regardless of PID.

## Monitoring Pitfalls

### Prepare percentage is approximate

**Symptom (observed 3×):** Prepare stuck at 76% for 2-5 min. User + agent both nearly panic-kill.

**Reality:** 76% is the "LLM config generation" step. MiniMax-M3 takes 60-120s per entity (8-11 entities = 8-18 min total). Percentage is a heuristic from the frontend, not a real progress counter.

**Fix:** Trust system health over progress bar:
1. Check `htop` — Python process consuming CPU? → working
2. Check `simulation.log` — timestamps advancing? → working  
3. Check Backend `/health` endpoint → 200? → working
4. Check DB writes — file sizes growing? → working

If ALL FOUR say working: **wait**. Do NOT restart.

### Worker PID gone after session close

**Symptom:** After Hermes session ends (context compaction, model change), simulation continues but no PID is visible.

**Fix:** Simulation persists independent of agent session. On reconnecting: check DB directly (`sqlite3 twitter_simulation.db "SELECT COUNT(*) FROM post"`). Never assume death from a cold restart.

## Techniques

### Skill Injection via ontology/generate multipart

MiroFish has NO separate skill-upload endpoint. Skills are injected as additional `files[]` in the `/ontology/generate` call:

```bash
curl -X POST http://localhost:5001/api/ontology/generate \
  -F "files=@seed.md" \
  -F "files=@skill.md" \
  -F "project_name=Sim10-Gen2"
```

Both files land in `document_texts[]`. The LLM receives both during config generation — seed for topic, skill for structure/inheritance.

**Verification:** Check project after upload:
```bash
curl -s http://localhost:5001/api/project/<project_id> | python3 -c "
import json,sys; d=json.load(sys.stdin)['data']
for i, doc in enumerate(d.get('documents',[])):
    print(f'Doc {i}: {doc.get(\"document_title\",\"?\")} ({len(doc.get(\"document_text\",\"\"))} chars)')
"
```

### Cross-Run Synthesis Pattern (Skill-Chaining Bias Study)

For bias-inheritance experiments across N generations (Sim10 design):

1. **Baseline:** Run Gen 0 (Fresh, no skill) — 60 rounds complete, extract all posts to JSON
2. **Hypothesis phase:** Predict CDI (Concept Drift Index), INS (Insight Novelty Score), Cluster-Saturation BEFORE running Gen N
3. **Sequential setup:** Gen 0 → Gen 2 (1× inheritance) → Gen 4 (3× inheritance). Each uses same seed + different skill version
4. **Metric extraction:** 5-dimensional quantitative analysis (Persona-Workload, Insight-Diversity, Discourse-Function, Word-Cloud Drift, Cross-Run Overlap)
5. **Verification:** Compare actual drift against predictions — the gap IS the finding

See `simulation-brainstorm-learning` skill for the 5-dimensional framework with Sim09 baselines.

## RAM Budget (RTX 5060 laptop, 16 GB total)

| Component | RAM | Notes |
|---|---|---|
| MiroFish Backend (Python) | ~200 MB | Stable |
| OASIS Worker | ~1.3-1.7 GB | Spikes during LLM calls |
| Frontend (serve) | ~50 MB | Negligible |
| Hermes Desktop | ~900 MB-1.2 GB | Desktop GUI |
| Hermes CLI server | ~800-900 MB | Background daemon |
| **Free for OS + other** | **~3-4 GB** | With all running |
| **Critical threshold** | <1 GB | Swap activates, Backend OOM |

**Rule:** Kill stale OASIS workers before starting a new run. One OASIS worker at a time. Check `free -m` before launch — need ≥3 GB available for a clean run.