---
name: mirofish-runbook
title: "MiroFish Runbook — Templates & Max-Kampagne Deck"
description: "Use when user asks to write a MiroFish runbook, run a Max-Kampagne skill-chaining simulation, create seed templates, or define subagent-based multi-run patterns. NOT for live pipeline (use mirofish-pipeline) or post-run analysis (use mirofish-analysis). Covers Step 5 + runbook-documentation templates."
category: software-development
version: '2.7'
created: '2026-07-23'
author: Yuno (split from mirofish v2.6)
lane: software-development
agent: universal
trigger_keywords: ['mirofish', 'runbook', 'max-kampagne', 'skill-chaining', 'seed template', 'subagent multi-run', 'a/b/c']
keywords: ['mirofish', 'runbook', 'template', 'deck', 'subagent', 'multi-run', 'skill-chaining', 'validation']
related_skills: ['mirofish-pipeline', 'mirofish-pitfalls', 'multi-agent-work']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from mirofish 2026-07-23)'

license: MIT
---

# MiroFish Runbook — Templates & Max-Kampagne Deck

MiroFish Runbook — Templates & Max-Kampagne Deck


## Übersicht — table with Thema, Seed-Quelle, IDs, max_rounds, Plattformen


## Personas — table per profile: Username, Rolle, Beschreibung


## Konfiguration — LLM-generated config: Zielgruppe, Zeitzone, Aktivitätsmuster, Diskussionsachsen


## Bug-Fixes — table: Datei, Patch, Grund


## API-Endpoints — table: Endpoint, URL, Status


## Instructions — Watcher PID, nächste Schritte

```

---

## Step 5: Simulating from the Max-Kampagne Deck


Basti's `mirofish_max_kampagne_komplett.md` defines a complete **Max-Plan** with **10 simulation cards** (Orchestrator vs Mesh, Agentenzahl-Sweep, Skill-Chaining, etc.), a one-pager-per-card pattern, and a monthly 80-run capacity (800 Zep credits).

When the user says "neue Simulation aus dem Deck" or references one of the 10 cards:

### 5a) Pick the Right Card


Cards are numbered 01-10 in the deck (see `references/max-kampagne-deck.md`). Each has: a research question, hypothesis, variables, and metrics.

| Wenn der User sagt… | Treffer |
|---|---|
| "Recovery, Resilience, Timeouts" | 06 — Recovery & Resilience |
| "Skill-Chaining, Wiederverwendung" | 09 — Skill-Chaining |
| "Gate-Strenge, Quality Gate" | 04 — Gate-Strenge |
| "Orchestrator vs Mesh, Queen vs Swarm" | 01 — Orchestrator vs Mesh |
| "Human-in-the-loop, HITL" | 08 — Human-in-the-loop |

### 5b) One-Pager → Clarify → Proceed


Before building seed files, write a short **One-Pager** (template in `references/max-kampagne-deck.md`): research question, hypothesis, variables, task design, metrics, failure modes, gate criteria, artifacts. **Show to the user for confirmation** before proceeding.

**PITFALL — Don't start writing without user confirmation.** Use clarify() with 2-4 concrete choices, each with a single-sentence justification. Never ask "was möchtest du?" — always provide options.

### 5c) Subagent-Based Seed + Skill Creation (für A/B/C Multi-Run)


For cards requiring multiple runs with different skill configurations:

1. **Königin (du)** schreibt: One-Pager, Persona-Liste, Konfliktlinien, Run-Schema
2. **Biene (subagent)** baut:
   - `testdata/simXX-<name>-seed.md` — gemeinsamer Seed-Kern
   - `testdata/skills/template-<name>.md` — nur Form, keine Inhalte
   - `testdata/skills/derived-from-<name>.md` — deterministisch
3. **Königin** sichtet, startet Runs sequenziell: R-A → Report → R-B → Report → R-C → Report
4. **Synthese:** SYNTHESE.md mit Vergleichstabelle

Der Delegation-Prompt der Biene MUSS enthalten:
- Exakte Dateipfade + Projektroot
- Referenz-Dateien zum Einlesen (vorige Reports, Seed-Vorlagen)
- Komplette Persona-Tabelle (identisch in Seed + Derived-Skill)
- Validierungsschritte (wc -l, Markdown-Sanity, Cross-Check)
- Explizites Verbot von API-Calls oder Simulation-Starts

### 5d) Seed-Struktur für Multi-Run


Für A/B/C-Simulationen (identischer Seed-Kern, Diff = Skill-Datei):

```
Section A — Topic Introduction
Section B — Personas (10 x voll ausformuliert, Englisch)
Section C — Research Question (DE + EN)
Section D — Run Schema mit Skill-Diffs
Section E — Conflict Lines (mind. 3)
Section F — Metrics Definition
Section G — Stop-Words / Out-of-Scope
Section H — Closing Brief
```

### 5e) Seed-Stile


| Stil | Quelle | Best für |
|---|---|---|
| **Whitepaper** | Whitepaper-seed.md | Vorhersagen, Framework-Vergleiche, Cost-Modelle |
| **Brainstorming** | Siehe seed-structure-brainstorming.md | Engineering-Lessons, Crash-Szenarien, A2A-Patterns |

Basti's bevorzugter Stil: Brainstorming (10 Personas, Twitter-only, Code-Snippets, DE+EN, quantitative Argumente).

### 5f) Skill-Chaining Simulation Archetype


For Card 09 (Skill-Chaining) and any future run that compares **skill reuse vs fresh generation**, use this pattern. It defines a three-run A/B/C schema where the only variable is the skill file passed to Zep.

### 25. Backend + OASIS Worker Crash Pattern (8-9 Min Stability Window)


**Symptom:** The OASIS worker dies after 8-9 minutes of runtime, despite `simulation.log` showing active rounds. The backend Flask process also dies (port 5001 unreachable). A BertSdpaSelfAttention warning appears in the worker's stderr before the crash. After cleanup + restart, the worker state is lost but SQLite data persists.

**Root cause:** Multiple overlapping issues:
1. **BertSdpaSelfAttention**: The Transformer library emits `"BertSdpaSelfAttention is used but torch.nn.functional.scaled_dot_product_attention does not support non-absolute position_embedding_type..."` — this is a warning only, not the crash itself.
2. **RAM pressure**: The OASIS worker (~1.3 GB) + Hermes server (~870 MB) + Hermes Desktop (~1.1 GB) + Brave (~700 MB) pushes 15 GB systems toward OOM.
3. **Backend in-memory state loss**: Flask debug mode × OASIS subprocess × signal handling causes cascade.

**Recovery procedure (worker crashed, data intact):**

```bash
### 26. Prepare Step at 76% Stall Is Normal (LLM Config Generation)


**Symptom:** The prepare step's progress stays at 76% with message `[3/4] 生成模拟配置: 1/3` for 2-5 minutes. Nothing changes. The user says "ja es ist nur ein ungefär wert die %" (it's just an approximate value).

**Normal behavior:** The prepare step has 4 stages:
- `[1/4]` — Profile generation (fast, ~10-30s)
- `[2/4]` — Initial posts (fast, ~10-30s)
- `[3/4]` — Simulation config **← LLM generates the config** (takes 2-5 minutes)
- `[4/4]` — Finalize (fast, ~5s)

The 76% stall at `[3/4] 1/3` means the LLM (MiniMax-M3 or similar) is generating the simulation configuration. This is the longest phase because it calls the LLM with the full profile context + seed to produce the config JSON.

**Don't:**
- ❌ Re-trigger prepare (creates a race condition — two prepare tasks running)
- ❌ Kill and restart (wastes the profile generation already done)
- ❌ Panic after 60s (it's normal for 2-5 min)

**Do:**
- ✅ Wait 5 minutes before checking again
- ✅ Use `prepare/status` endpoint to check (returns `progress: 100` when done)
- ✅ If after 5+ minutes still at 76% with no change, check backend health — the LLM call may have timed out

**User preference:** Basti confirmed the percentage is approximate. Don't over-analyze mid-step progress. A single check after 3-5 minutes is sufficient.

---

### 27. `profiles` Endpoint Defaults to `reddit` (Frontend Shows Empty for Twitter-Only)


**Symptom:** The simulation dashboard at `/simulation/{id}/start` shows an error or empty profile list. Inspection shows the API returns `{"platform": "reddit", "profiles": []}` even though the simulation is Twitter-only.

**Root cause:** The MiroFish backend's GET `/api/simulation/{id}/profiles` endpoint defaults `platform` to `"reddit"` when no query parameter is provided. For Twitter-only simulations, this returns an empty array because no Reddit profiles exist.

**Fix:** Either:
1. **Enable both platforms (recommended):** Create the simulation with `"platform": "parallel"` and `"enable_twitter": true, "enable_reddit": true` — the frontend will find profiles on both.
2. **Pass platform=twitter explicitly:** If creating a Twitter-only simulation, the frontend needs to call `/api/simulation/{id}/profiles?platform=twitter`. This is a frontend bug; the workaround is creating the sim with both platforms enabled.

**When creating simulations for frontend viewing:** Always enable both platforms to avoid the empty-profile error in the dashboard.

---

### 28. Worker Crash ≠ Data Loss — SQLite Persists


**Symptom:** The OASIS simulation worker crashes (PID disappears, no new log entries). The system seems to have lost the simulation. But the SQLite databases contain all posts produced so far.

**Pattern confirmed across multiple runs (V1-V3, Skill-Chaining Sim09 Run A):**

| Event | What happens | Data status |
|---|---|---|
| Worker starts | Writes to twitter_simulation.db | ✅ Intact |
| Worker produces Round 1-15 | ~22 Twitter posts created | ✅ In DB |
| Worker crashes (PID gone) | Process dies, backend may also die | ✅ DB files persist |
| Backend restarted | Flask restarts, discovers old sim | ✅ API finds the simulation |
| SQLite read | All 22 Twitter posts readable | ✅ Full content available |

**Recovery after crash — data extraction:**

```bash
SIM_PATH="backend/uploads/simulations/$SIM_ID"
### 29. Parallel Mode (Twitter + Reddit) Produces ~3x More Data


**Symptom:** A parallel-mode simulation (twitter+reddit) produces substantially more posts than a Twitter-only simulation, even with the same personas and seed.

| Mode | Typical Posts (8 min) | DB Size Growth |
|---|---|---|
| Twitter-only | 8-12 posts | ~130-180 KB |
| Parallel (twitter+reddit) | **22-29 posts** | Twitter: ~300 KB + Reddit: ~1.2 MB |

**Why:** Reddit allows longer-form posts (no character limit within reason), so the OASIS worker generates more verbose content for Reddit agents. Additionally, the two platforms run as separate sub-processes with independent LLM call queues, doubling throughput.

**Trade-off:** More data means more comprehensive findings, but also:
- Higher RAM consumption (~1.5 GB vs ~1.0 GB for Twitter-only)
- Potentially more worker crashes (more LLM calls = more memory pressure)
- Reports take longer to generate (more content to synthesize)

**Recommendation:** For analytical runs where you need as much data as possible before the 8-9 min crash window, use parallel mode. For quick smoke tests or when RAM is tight, use Twitter-only.

**User preference:** Basti prefers to enable both platforms when the dashboard needs to display profiles correctly (avoids the `profiles` endpoint default bug).

---

### 30. Progress Percentage Is Approximate — Don't Over-Monitor


**Symptom:** The agent keeps checking progress percentages (71%, 72%, 73%, ...) every 15-30 seconds during graph build or prepare, driving up tool-call count without adding value.

**User preference (verbally confirmed):** "ja es ist nur ein ungefär wert die %" — the progress percentage is just an approximate value.

**Rule of thumb for monitoring frequency:**
| Phase | Check interval | Max checks before pause |
|---|---|---|
| Graph build (normal) | Every 2-3 min | 3 checks = 9 min, then wait 5 min |
| Graph build (rate-limited) | Every 3-5 min | After detecting 429, wait full reset (~7 min) |
| Prepare | **Single check** after 4 min | Don't poll — it's 2-5 min anyway |
| Simulation run | Every 5-8 min | Check PID alive + DB size growth, don't read logs every cycle |
| Report generation | Every 15-30s (this one is fast) | Expected to complete in 30-90s |

**For build progress specifically:** Three checks max (2 min apart → 6 min total), then pause for 5 min. The next check after the pause will show a much larger jump or completion.

---

### 31. Backend Restart Loses In-Memory Prepare Tasks


**Symptom:** After a backend crash + restart, the `prepare/status` endpoint returns `None` for the old task ID. The simulation shows `status: "preparing"` but never progresses. Trying to start the simulation returns `"模拟已在运行中"` (sim already running) even though no worker PID exists.

**Root cause:** The MiroFish backend's `TaskManager` is an **in-memory** data structure (Python dict, not persisted to SQLite). When the backend Flask process restarts:
1. All in-flight prepare tasks are gone — their `task_id`s no longer exist
2. The backend's `SimulationManager` remembers the sim's `status: "preparing"` from the last time it loaded the data, but the task that was doing the work is lost
3. The `POST /api/simulation/prepare` endpoint creates a new task_id, but the old task's progress is unrecoverable
4. The `POST /api/simulation/start` endpoint may return `"模拟已在运行中"` if the in-memory state believes the sim is still running, even though no worker process exists

**Diagnosis — three distinct cases after backend restart:**

```bash
### 32. Observer/Watcher Should Use Dynamic PID Discovery


**Symptom:** A watcher script hardcodes a worker PID at startup. When the backend crashes, the worker respawns with a new PID, and the watcher reports "worker dead" forever — even though the simulation is still actively producing data.

**Root cause:** OASIS workers can crash and be respawned with a new PID (observed: PID 17048 → PID 17527 in Sim09 Run A). A watcher that captures the PID once at startup will miss the respawn.

**Fix — dynamic PID discovery via `pgrep`:**

```python
import subprocess

def find_worker_pid():
    """Discover the current OASIS worker PID dynamically."""
    try:
        r = subprocess.run(
            ["pgrep", "-f", "run_parallel_simulation"],
            capture_output=True, text=True
        )
        pids = r.stdout.strip().splitlines()
        if pids:
            return int(pids[0])
    except Exception:
        pass
    return None

### 33. Observer Polling Frequency — Don't Over-Sample


**Symptom:** The agent writes a watcher/observer that polls every 30 seconds, accumulating 90+ log entries for a 45-minute simulation run. The observer's log file is mostly noise (same round numbers repeated).

**Rule of thumb for observer polling:**

| Simulation phase | Poll interval | Purpose |
|---|---|---|
| First 3 min | 60s | Detect initial startup (8 initial posts) |
| Steady state (Rounds 5-40) | 120-180s | Track real progress, don't react to every single round |
| Final phase (Rounds 40-60) | 60s | Detect completion for report trigger |
| After 3 consecutive no-change polls | 300s | Simulation may be stuck — don't burn CPU checking |

**Design pattern — log-based observer with summary output:**

```python
### 34. `npm run dev --kill-others` Is Crash Root Cause


**Symptom:** The OASIS worker dies after 8-9 min. OR: Backend and frontend die simultaneously despite enough free RAM (no OOM in dmesg). The MiroFish `npm run dev` command starts a `concurrently --kill-others` shell that kills ALL if ANY exits.

**Root cause:** MiroFish's `package.json` uses `concurrently --kill-others` to run backend + frontend together. This flag tells `concurrently` to kill ALL processes in the group if ANY ONE exits. When Flask's debug reloader briefly disconnects (a completely normal Flask hot-reload cycle), the `--kill-others` flag triggers a cascade termination: the Python backend is killed, which kills the Vite dev server, which kills the entire MiroFish stack. This is NOT an OOM crash — it's a `--kill-others` false positive.

**Detection — how to tell if --kill-others caused a crash:**
```bash
### 35. Inline OASIS Worker — `pgrep -f "run_parallel_simulation"` Can Miss It


**Symptom:** A simulation is running (DB growing, logs showing real rounds), but `pgrep -f "run_parallel_simulation"` or `ps -ef | grep run_parallel_simulation` returns nothing. The watcher reports "no worker found" even though the sim is actively producing.

**Root cause:** In some MiroFish/OASIS deployments, the simulation worker runs **inline** within the Flask backend process itself (as a thread or long-lived function call). It was NOT spawned as a separate `run_parallel_simulation.py` subprocess. Instead:
- The Flask process has `run.py` as its parent
- The inline worker is a function within the Flask app (e.g. in `app/services/`)
- There is no `run_parallel_simulation` binary or script running as a distinct OS process
- `pgrep` or `ps` pattern-matching on the subprocess name returns empty

**Alternative detection methods:**

```bash