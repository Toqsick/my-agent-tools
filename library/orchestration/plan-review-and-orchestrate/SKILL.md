---
name: plan-review-and-orchestrate
description: |
  Use when a non-trivial plan needs pre-execution weakness review, dependency repair, subagent assignment, or Queen verification across multiple deliverables.
  NOT for simple one-step work, executing an unreviewed plan immediately, or trusting subagent self-reports without inspecting artifacts and evidence.
  Combines a structured plan critique with bounded dispatch, verification gates, recovery actions, and final synthesis.
version: 0.2.0
author: Hermes
license: MIT
platforms:
  - linux
  - macos
metadata:
  hermes:
    tags: ['Planning', 'Plan-Review', 'Subagent-Orchestration', 'Queen-Verify', 'Pitfall-36']
    related_skills: ['plan', 'subagent-driven-development', 'self-improving', 'multi-agent-pitfalls-cheatsheet']
lane: koenigin
reasoning_effort: xhigh
agent: Engineer
routing_hint: |
  Use when Basti asks for a plan + execution on a multi-step task (skill-curation, repo cleanup,
  bundle build). Two-phase: (1) review the plan for 5 weakness categories, (2) dispatch subagents
  per task with Queen-Verify after each. Pairs with `plan` (creates the plan) and
  `subagent-driven-development` (executes). Trigger words: "verfeinere", "refactor",
  "multi-step", "build plan", "orchestrate", "plane neu".

  LIGHTWEIGHT MODE: Explicit user invocation overrides the "Do NOT use" rule.
  For single-file/small-scope tasks, run Phase A (Plan-Review) standalone.
  Present the Schwächen-Tabelle as the deliverable; execute the plan inline
  instead of dispatching subagents. The Schwächen-Review format is useful
  even without Phase B.
trigger_keywords: ['plan', 'subagent', 'verification', 'trivial', 'needs']
keywords: ['plan', 'subagent', 'verification', 'trivial', 'needs']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['plan', 'hermes-plan-mode-recovery', 'subagent-driven-development']
---

# Plan-Review-and-Orchestrate

Two-phase workflow for non-trivial multi-step tasks: (1) review the plan for 6
weakness categories before any execution, (2) dispatch subagents per task with
Queen-Verify as the loop closure. Proven pattern from a 18-subagent skill-curation
run on 2026-07-15 where Pitfall #36 (subagent-self-test-deception) live-manifested
6 times in one session.

> **Mnemosyne-Anker:** Read `references/run-log-2026-07-15.md` for the canonical
> worked example — 9 phases, 18 subagent calls, 6 Pitfall-#36 manifestations.

## When to Use

- Basti asks for a multi-step change with explicit "verfeinere"/"refactor"/"build" trigger.
- The plan already exists (from `plan` skill) or you draft one inline.
- ≥3 tasks touch the same file or files in the same directory.
- Lessons-promotion is a goal (skill-curation, doc-restructuring).
- The output must survive without Basti in the loop (no clarifying questions allowed mid-run).

**Do NOT use when:**
- Single-file edit with clear scope.
- Research/analysis without deliverable file edits.
- Basti explicitly wants to be in the loop every step.

## Prerequisites

- Plan file at `~/.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md` (or draft inline).
- Mnemosyne IDs known OR `mnemosyne_recall` available for ID-resolution.
- Backup target directory for any file that will be edited (default: `<skill>/.archive/`).
- Hermes tools: `read_file`, `patch`, `write_file`, `terminal`, `delegate_task`,
  `mnemosyne_recall`, `mnemosyne_get`, `mnemosyne_remember`.

## How to Run

```text
Phase A: Plan-Review
  1. Read the plan file with `read_file`
  2. Classify weaknesses into 5 categories (Procedure below)
  3. Patch the plan inline before any subagent dispatch

Phase B: Subagent-Orchestrate
  4. Phase 0 — ID-Discovery (resolve Mnemosyne IDs Queen-verified)
  5. Phases 1-N — Implementer subagent + Queen-Verify (skip 2-Stage if crash rate >20%)
  6. Phase Final — Comprehensive Verifier
  7. Write Curation Report to `~/.hermes/docus/reports/`
```

## Quick Reference

| Action | Tool | When |
|---|---|---|
| Read plan | `read_file` plan-path | Phase A start |
| Resolve Mnemosyne ID | `mnemosyne_recall` + `mnemosyne_get` | Phase 0, before any update |
| Queen-Verify edit | `terminal` grep + diff vs backup | After every subagent edit |
| Dispatch subagent | `delegate_task` with full task text | Phase N implementer |
| Queen-Patch | `patch` (never `replace_all=true`) | When subagent drifts |
| Crash-Recovery | Queen-Verify fallback | When subagent returns "owner exited" |
| Write Report | `write_file` to `~/.hermes/docus/reports/` | End |

## Procedure

### Phase A: Plan-Review (5-Schwächen-Framework)

Read the plan with `read_file`, then scan for these 5 weakness categories:

1. **Mnemosyne-ID-Platzhalter:** Plans often write `<id-von-...>` placeholders.
   These fail silently at execute. **Patch:** add a `## Resolved Mnemosyne-IDs`
   table filled by Queen-verified recall.

2. **Section-Anker-Vagheit:** Plans say "insert AFTER X" without exact line
   numbers or unique-context strings. **Patch:** add a per-task Anker-Tabelle
   mapping task → anchor hash → position relative to existing section.

3. **Test-Cluster-am-Ende:** Tests at the end miss task-level failures early.
   **Patch:** inline-verify blocks per task (5-10 lines, runs after edit).

4. **Output-Bomb-Risiko:** Scripts/tools that produce huge output (hygiene
   scan over 281 skills, etc.) surprise Basti on first run. **Patch:** add
   `--brief` flag in plan for any tool emitting >10KB.

5. **"Biet-sized"-Violations:** Tasks >5 Min that aren't actually atomic.
   **Patch:** add a "Wo anfangen (Time-Budget-Cuts)" section with 5/15/45
   Min alternatives.

6. **Parameter-Feasibility:** Plans specify `num_predict`, `temperature`,
   `num_ctx`, `timeout`, `batch_size` without checking hardware compatibility.
   Five concrete sub-classes proven from the Qwythos-9B benchmark session:
   - **num_predict-Buffer für Thinking-Modelle:** qwythos-artige Modelle
     produzieren 300-1500 Tokens Thinking BEVOR die Antwort kommt. `num_predict`
     muss denken + antwort umfassen → 10-20× des erwarteten Outputs.
     _Symptom:_ Leere Antworten / Finish-Reason="length".
   - **VRAM-Budget für Vision/Cross-Modal:** CLIP-Projectoren (~500M params)
     passen auf 8GB nicht zusätzlich zum LM → CPU-Offload (`num_gpu=20`) nötig.
     _Symptom:_ CUDA OOM beim ersten Vision-Call.
   - **Timeout vs Task-Laufzeit:** Needle-in-Haystack + Context-Scaling mit
     64k+ Context brauchen >60s pro Call → SystemSampler Race-Condition.
     _Symptom:_ VRAM=0 in Rohdaten bei sonst erfolgreichen Calls.
   - **think=False für strukturierte Outputs bei Thinking-Modellen:** Mit
     `temperature=0.0` und kleinem `num_predict` (≤80) schreiben qwythos-artige
     Thinking-Modelle die komplette Antwort in den Thinking-Block — die `response`
     bleibt leer. Fix: `think=False` bei MC-Fragen, Code-Generierung und anderen
     kurzen strukturierten Outputs. Alternativ: `temperature≥0.3` damit das
     Modell nicht in der Reflexionsschleife hängenbleibt.
     _Symptom:_ 0% Accuracy bei Multiple Choice trotz großzügigem `num_predict`.
   - **Erwarte 2-3 Runs für LLM-Benchmarks:** Runner-Bugs sind bei
     LLM-Benchmark-Suites die Regel, nicht die Ausnahme. Der erste Run deckt
     typisch 3 Bugs auf (num_predict, think-Flag, Path-Parents). Der zweite
     Run deckt den tieferen Bug auf (z.B. think-Flag-Wechselwirkung mit q=0.0).
     Der dritte Run ist final. **Plane Zeit für 3 Iterationen ein und baue
     Runner von Anfang an auf Re-Run aus** (deterministische Seeds, JSON-Rohdaten,
     `--skip-raw` für teilweisen Re-Run).
     _Symptom:_ Plan hat nur einen Run eingeplant — nach Bug-Fix fehlt Zeitbudget.
   **Patch:** Per-Task Parameter-Validation-Block mit hardware-spezifischen
   Defaults (GPU-VRAM, Model-Bauform mit Vision, Quant-Stufe).

**Patch template (apply to plan file):**

```python
patch(mode='replace',
      old_string='<existing plan section>',
      new_string='<patched section>',
      replace_all=False)  # MANDATORY — see Pitfall #5
```

### Phase B: Subagent-Orchestrate

#### Phase 0: ID-Discovery (run first, always)

```python
# Subagent: read-only Mnemosyne lookup
delegate_task(
    goal="Resolve Mnemosyne IDs for N lessons, return ID-table",
    context="KNOWN IDs: <list>. LESSONS TO RESOLVE: <list>. USE mnemosyne_recall + mnemosyne_get.",
    toolsets=['terminal', 'file', 'mnemosyne']
)
```

**Queen-Verify Phase 0 — always run this BEFORE trusting the result:**

```bash
# Verify each returned ID actually exists in Mnemosyne
for id in <list>; do
    result=$(mnemosyne_get $id 2>&1 | head -1)
    [ "$result" != '{"status": "not_found", "memory_id": "'$id'"}' ] \
        && echo "✅ $id" \
        || echo "🚨 $id FABRICATED"
done
```

**If Queen-Verify finds fabricated IDs (Pitfall #36 variant a):**

- Don't re-dispatch (sunk-cost, but re-dispatch often fabricates again).
- Solve Queen-side via parallel `mnemosyne_recall` with different keywords.
- Store a Queen-verified ID-table back in plan file for downstream tasks.

#### Phases 1-N: Implementer + Queen-Verify

For each Edit-Task in the plan:

```python
delegate_task(
    goal=f"Implement Phase {N}: {task_name}",
    context=f"""
    TASK FROM PLAN: <paste full task text from plan file>
    EINGEPLANTER SUBAGENT: Implementer
    MNEMOSYNE-IDS: <Queen-verified list>

    TDD-REQUIREMENTS:
    1. Edit <file> (exact lines given in task)
    2. Run inline verify (test {a|b|c|d|e} from plan)
    3. Mnemosyne-Call with REAL id (not placeholder)
    4. Report: <files-modified> + <verify-output> + <lesson-ids-touched>

    NICHT ERLAUBT:
    - replace_all=true (Pitfall #5!)
    - write_file > 4KB ohne Chunk-Strategie (Pitfall write-file-truncation)
    - Mnemosyne-Update mit placeholder-IDs
    """,
    toolsets=['terminal', 'file', 'mnemosyne'],
)
```

**After each subagent returns — Queen-Verify (mandatory, even if subagent reports PASS):**

```bash
# 1. Diff body against pre-edit snapshot
diff <(sed -n 'N,Mp' <file>) <(sed -n 'N,Mp' <backup>) | wc -l
# Soll: 0 lines (or only the expected added lines)

# 2. Grep for new structure
grep -nE '^## |<new-field>:' <file>

# 3. Cross-check Mnemosyne IDs if subagent claims update
sqlite3 ~/.hermes/mnemosyne/data/mnemosyne.db \
    "SELECT id, importance FROM working_memory WHERE id IN (<ids>);"
```

**Reviewer-Mode decision:**

- **Crash rate <10%:** Full 2-Stage (Implementer + Spec-Reviewer + Quality-Reviewer)
- **Crash rate 10-20%:** Reduced 1-Stage (Implementer + Spec-Reviewer only, Queen handles quality)
- **Crash rate >20%:** No reviewer, just Implementer + Queen-Verify (subagent dispatch budget exceeded)

**Subagent-Crash recovery (Pitfall #36 variant c — "owner exited"):**

- Do NOT re-dispatch immediately (high re-crash probability).
- Queen-Verify the partial state (did the edit land before crash?).
- If edit landed: continue with the next phase.
- If edit did not land: re-dispatch with the same task brief but explicitly
  shorter new_string (Pitfall #5 truncation often precedes crash).

#### Phase Final: Comprehensive Verifier

Dispatch ONE final Implementer that runs all 7 audit checks against the
finished artifact:

```python
delegate_task(
    goal="Phase Final Verifier: 7-area audit of finished <skill-name>",
    context="Run all 7 checks against <file>. Report PASS/FAIL per check + FINAL VERDICT.",
    toolsets=['terminal', 'file', 'mnemosyne']
)
```

#### Curation-Report

After FINAL APPROVED, write a report to `~/.hermes/docus/reports/<name>-YYYY-MM-DD.md`:

```text
## What was changed (table)
## Pitfalls promoted (list with IDs)
## Mnemosyne audit (lessons created/updated)
## Side-effects (unexpected findings, e.g. hygiene scan found 781 drifts)
## Subagent stats (calls, crashes, recovery paths)
## Verification checklist
## Meta-lessons (what we learned about the orchestration itself)
## v1.2 follow-ups
```

## Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| **#36a Subagent fabricates data** | Subagent returns "all green" + IDs that don't exist | Queen-Verify with `mnemosyne_get` BEFORE trusting; don't re-dispatch |
| **#36b Subagent misreads spec** | Wrong tool, wrong table, wrong SQL query | Queen-Verify the actual side-effects, not just the report claims |
| **#36d Subagent stale template tests** | Cloned project passes tests but they still reference the source model name/URL/config | **Queen-Verify after every clone subagent** — grep for source-model string in `tests/` and `src/` before declaring success |
| **#36c Subagent process crash** | "owner exited before terminal result" | Queen-Verify partial state; re-dispatch with shorter new_string |
| **#5 write_file truncation** | `write_file` returns but content is incomplete | Split into 2 patches; verify with `wc -c` before/after |
| **#5 patch replace_all=true trippling** | Same content injected N times in N sections | Use `replace_all=False`; unique `old_string` ≥3 lines |
| **#5 Path.parents off-by-one** | `parents[2]` statt `parents[3]` bei Modulen in `src/project/subdir/` | Laufzeit-Prüfung: `parents[X]` zählt vom File-Dir, nicht Project-Root |
| **think=False vergessen** | Strukturierte Outputs (MC/Code) bleiben leer trotz ausreichend num_predict | Set `think=False` bei temp=0.0 + kurzen Outputs auf Thinking-Modellen |
| **Plan-Review gap** | Phase 1 fails on something a 5-Min plan-review would have caught | Always run Phase A before any dispatch |
| **Cross-session-context-loss** | Mid-orchestration, agent loses track of earlier subagent results | Todo-List updaten, Mnemosyne-IDs in Plan-File speichern |

## Verification

```bash
# 1. All Queen-Verify checks pass for every phase
for phase in 0 1 2 3a 3b 3c 3d 3e 3f 4 5a 5b; do
    echo "=== Phase $phase ==="
    grep "Queen-verified" /home/bratan/.hermes/plans/<plan>.md | grep -q "Phase $phase" \
        && echo "✅ Phase $phase Queen-verified" \
        || echo "🚨 Phase $phase missing Queen-Verify"
done

# 2. Subagent crash rate is documented
grep -c "owner exited" /home/bratan/.hermes/docus/reports/<this-report>.md

# 3. Mnemosyne-Lessons created during run are accessible
sqlite3 ~/.hermes/mnemosyne/data/mnemosyne.db \
    "SELECT COUNT(*) FROM working_memory WHERE timestamp LIKE '<YYYY-MM-DD>%';"
```

**Reference outputs:**

| Variante | Run-Log | Task-Typ | Geeignet für |
|---|---|---|---|
| **Subagent (default)** | `references/run-log-2026-07-15.md` | 18 unabhängige Skill-Edits (parallelisierbar) | Hohe Isolation, viele Sub-Tasks |
| **Inline (lightweight)** | `references/run-log-2026-07-17-inline-execution.md` | 15 Module, lineare Build-Abhängigkeiten | Build-Projekte, schnelle Fehler-Recovery |
| **Hybrid (Phase A inline + B subagent)** | `references/run-log-2026-07-17-yuxin-tau2.md` | 4-Phasen, 1 Subagent, Rest inline | Queen-Verify + Cloned-Project-Setup |

**Wahl-Heuristik** (validiert auf 2026-07-17 durch zwei unabhängige Runs mit
unterschiedlichen Modell-Architekturen — qwythos qwen35 und yuxin-tau2 gemma4):
- **Lineare Abhängigkeiten** (Phase N baut auf Phase N-1 auf) → **Inline-Execution**
- **Parallelisierbare Tasks** (mehrere unabhängige Read/Edit-Cycles) → **Subagent-Orchestrate**
- **Gemischte Workloads** → Phase A inline + Phase B hybrid (Subagenten nur für isolierte Tasks)

## See Also

- `plan` (writes the plan first)
- `subagent-driven-development` (executes plan via 3-stage review)
- `self-improving` (lesson-storage + curation cycle)
- `multi-agent-pitfalls-cheatsheet` (full Pitfall #36 catalog)
- `mnemosyne-id-resolution` (5-phase ID-discovery workflow)
- Run-log: `references/run-log-2026-07-17-yuxin-tau2.md` (Hybrid Inline + Subagent — second validated case)