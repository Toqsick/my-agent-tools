---
name: better-plan-strategy
description: "Use when user asks to improve an LLM implementation plan, reality-check assumptions, define atomic tasks, estimate effort, map risks, or choose a safe subagent wave strategy. NOT for executing the plan or handling a trivial one-line task. Applies verified path checks, single-source-of-truth tables, explicit done criteria, and preflight planning discipline."
version: 0.2.0
author: Hermes
platforms:
- linux
- macos
metadata:
  hermes:
    tags:
    - planning
    - plan-quality
    - queen-verify
    - pre-plan-check
license: MIT
trigger_keywords: ['plan', 'better-plan-strategy', 'improve', 'llm', 'implementation']
keywords: ['plan', 'user', 'asks', 'improve', 'implementation']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['plan', 'plan-review-and-orchestrate', 'hermes-plan-mode-recovery']
---

# Better Plan Strategy

A practitioner's guide to writing LLM-driven implementation plans that survive
real-world execution. The core lesson: **a plan is only as good as its verified
assumptions**. This skill distills the patterns GLM 5.2 and Yuno learned the
hard way across dozens of plan-and-execute cycles — most painfully the 2026-07-16
fall where a queen-agent wrote 6 audit-driven plan items and 3 of them turned
out to be obsolete or built on false filesystem assumptions.

> **Planer-Modell:** GLM-5.2 ist das bevorzugte Planer-Modell (Basti-Preference „GLM ist besser im Planen") und wird per `plan-glm`-Subprozess geroutet — unabhängig davon, ob die Session-Königin gerade auf M3 (Live-Default) oder GLM läuft. Diese S1–S7-Checkliste ist bewusst **modell-agnostisch**: sie greift für jeden Planer. Auf GLM-5.2 löst `reasoning_effort` zu `max` auf (nur 2 Stufen) — Details in `plan-glm`.

## When to Use

- A plan is about to be written by GLM 5.2, MiniMax M3, or any LLM planner.
- A plan already exists but has gaps the executor keeps hitting (re-work loops).
- Auditing an existing plan before subagent dispatch.
- Trigger phrases: "besserer plan", "plan strategie", "plan verbessern",
  "plan-quality", "plan pre-verify", "plan hat lücken", "plan soll queen-verify passen".

## Prerequisites

- The plan workflow (`software-development/plan` or `software-development/plan-glm`)
  loaded in the planning session.
- `~/.hermes/plans/` exists and is writable (default location).
- `terminal`, `read_file`, `search_files`, `write_file`, `patch`, `delegate_task`,
  `memory` tools all available in the queen session.
- The plan target context (project path, relevant file inventory, user
  constraints) collected before drafting.

## How to Run

```text
skill_view(name='software-development/better-plan-strategy')
```

Apply the 7 strategies below as a checklist when writing OR reviewing any plan.

## Quick Reference

- **S1 Pre-Plan Reality-Check:** `ls -la` / `find` / `read_file` on every path
  the plan will touch. Write results into a "Realitäts-Status" table BEFORE
  drafting tasks.
- **S2 Single-Source-of-Truth tables:** one table per audit point that maps
  claim vs. verified status. Stale rows must be striken with ✅ / ❌ markers.
- **S3 Estimated effort per task:** `X Min` not `small / medium / large`.
  Subagent dispatch ordering depends on these.
- **S4 Atomic-write policy:** any task that touches a single file with
  Frontmatter+Body must use ONE `write_file` call, not 2 `patch` calls.
- **S5 Risk section (R1-Rn):** numbered checklist, each item a one-line
  shell probe. Queen runs the whole list before subagent dispatch.
- **S6 Subagent wave plan:** AB-Standard Rolling-Waves — 3 parallel bees
  per wave, queen-verify between waves. Independent tasks per wave.
- **S7 Done-Kriterium:** checkbox list of objectively checkable outcomes.
  Includes Mnemosyne-anchor recall verification, not just file-existence.

## Procedure

### Strategy 1: Pre-Plan Reality-Check (Pitfall PLANNING-1)

Before the plan is written, verify every path and assumption that will
appear in it. The cost is 1-3 minutes; the cost of skipping it is 30-60
minutes of re-work per wrong assumption (proven 2026-07-17).

```bash
# For each path the plan will reference:
test -f <path> && echo "✅ exists" || echo "❌ MISSING"
find <vault-root> -iname "<glob>"  # check for duplicates
```

Document results in a "Realitäts-Status" table near the top of the plan,
BEFORE the tasks section. Every row gets ✅ / ❌ / 🆕 marker so the queen
can scan it during verification.

### Strategy 2: Single-Source-of-Truth (SSOT) Audit Tables

For any plan derived from an audit, refactor, or improvement backlog,
build one table where each row is: `Audit-Punkt | Geplanter Status |
Tatsächlicher Status | Plan-Aktion`. This single table:

- Forces the planner to confront reality, not just transcribe backlog.
- Makes obsolet findings easy to strikethrough (no work, just checkmark).
- Gives the queen one place to verify vs. filesystem.

### Strategy 3: Concrete Effort Estimates

Replace "small/medium/large" with **concrete minutes** (e.g. `25 Min`,
`45 Min`, `15 Min`). Use these rules:

- 5-15 Min: a single `write_file` + verification grep
- 15-30 Min: a small script + dry-run test
- 30-60 Min: cross-file refactor with multiple verify steps
- 60+ Min: should probably be split into sub-tasks

Without minute-estimates the queen cannot batch waves correctly.

### Strategy 4: Atomic-Write Policy

Tasks that modify one file (e.g. Working Agreement YAML-Frontmatter + Body)
MUST be specified as ONE `write_file` call, not two `patch` calls.
Pitfall #41-class races (user edits between patch-1 and patch-2) cost hours
to debug. State this in the task explicitly:

> Step 2+3: write_file with full file content (frontmatter + body + changelog),
> NOT two separate patches.

### Strategy 5: Numbered Risk Section (R1-Rn)

Before subagent dispatch, the queen runs a numbered risk-probe list. Each
risk is one shell one-liner. Example from GLM 5.2's 2026-07-17 plan:

```bash
# R1: Pfad-Existenz aller Touch-Points
test -f ~/.hermes/skills/software-development/plan-glm/SKILL.md
test -f ~/.hermes/skills/meta/self-improving/SKILL.md
# R2: crontab-Backup vor Task N
crontab -l > /tmp/crontab.backup.$(date +%s).bak
```

Pattern: each risk maps to ONE probe, expected output ✅. Any ❌ = pause
plan, clarify with user.

### Strategy 6: Subagent Wave Strategy (AB-Standard Rolling-Waves)

For plans with 4+ tasks, group them into 2-3 waves of 2-3 parallel bees:

```
Welle 1 (parallel):     [Task 0] [Task 1] [Task 5]
                              ↓
                  Queen-Verify Welle 1 (15 Min)
                              ↓
Welle 2 (parallel):     [Task 2] [Task 3] [Task 4]
                              ↓
                  Queen-Verify Welle 2 (15 Min)
```

Rules:

- Tasks in one wave MUST be independent (no shared file-write targets).
- One "smallest" task per wave validates the dispatch pipeline.
- One "documentation-only" task per wave keeps a learning record even on
  partial failure.
- Queen-verify between waves: `mnemosyne_recall` for each task's anchor +
  `ls -la` for each modified file. Mismatch = stop, clarify.

### Strategy 7: Done-Kriterium Checkbox List

End every plan with a checkbox list of objectively verifiable outcomes:

```markdown
## Done-Kriterium

- [ ] Welle 1 abgeschlossen + Queen-Verify ok
- [ ] Welle 2 abgeschlossen + Queen-Verify ok
- [ ] Alle N Mnemosyne-Anker erzeugt + recall-verified
- [ ] Audit-Recovery-Report finalisiert
- [ ] Crontab-Eintrag persistiert + first run bestätigt
- [ ] Mnemosyne-Budget < 50% (sonst consolidate-Cron triggern)
```

Pitfall-Prevention: include **Mnemosyne-recall-verification** not just
file-existence. Subagents can write files that say "verified" without
verification.

## Pitfalls

- **No estimated minutes = impossible wave-planning.** Always include.
- **Two-patch tasks race with concurrent user edits.** Atomic-write only.
- **Plan-derived "verification" without live shell probe = theatre.** Every
  verify step must be `grep`/`ls`/`mnemosyne_recall`/script, not "looks good".
- **Mnemosyne-anchor `importance < 0.5` = recall-clutter.** Audit-anchors
  should be ≥ 0.7, CRITICAL findings ≥ 0.85.
- **No Done-Kriterium = "done" is whatever the subagent claims.** Force
  checkbox list with objectively-verifiable items.
- **Re-using a plan across sessions without re-verifying paths.** Filesystem
  drift is real — pre-verify EVERY time.
- **Plan assumes subagent will remember to verify Mnemosyne anchors = plan failure (proven 2026-07-17).** The Done-Kriterium MUST include a Queen-side verification step for each task's Mnemosyne anchor — but use the **Dual-Verification Workflow** (`mnemosyne_recall` with query on content + SQLite cross-check), NOT `mnemosyne_get` (which has a known tool-bug — see self-improving Pitfall #44: liefert `not_found` für ALLE IDs, auch selbst-gesetzte). Subagents may claim anchors they haven't persisted — the plan that trusts subagent self-reporting without Queen verification will silently lose audit records. Mitigation: S6 wave strategy MUST include "Queen verifies ALL Mnemosyne anchors via `mnemosyne_recall(query=...)` before marking wave complete" as a hard gate.
- **Skilled existieren, aber werden nicht als Prerequisites geladen (proven 2026-07-17 Mass-Audit).** `better-plan-strategy` existiert seit 2026-07-17, wurde aber in historisch 0/21 vorherigen Plänen geladen. Nach Erstellung nur 2 von 2 Plänen (100%, weil explizit via Skill-Naming geladen). Die Existenz eines Quality-Skills bedeutet NICHT dass er in der Plan-Pipeline angewendet wird. Jeder Skill der Pläne erzeugt (`plan-glm`, `plan`, `workflow-template`) MUSS `better-plan-strategy` als Prerequisite laden — idealerweise per `skill_view` im "How to Run" Schritt. Ohne diese Verdrahtung ist der Skill ein reines Doku-Artefakt ohne Wirkung auf 83% der Pläne.
- **Standalone `python -c ...` verification breaks when pyproject.toml uses `pythonpath = ["src"]`.** Proven 2026-07-17 on qwen-dsv4-q5 clone: the plan said `python -c "from module import ...; print('ok')"` which got `ModuleNotFoundError` because `[tool.pytest.ini_options] pythonpath = ["src"]` only applies to pytest, not standalone python. Fix: prefix with `PYTHONPATH=src` or use `python -m pytest` instead. **Any plan with a "verify via python -c" step MUST check whether the project's pyproject.toml has a `pythonpath` setting.** If yes, the verify command needs explicit `PYTHONPATH=src` prefix, or switch to a pytest-based invocation that picks up the config automatically.

## Verification

Run this checklist on any existing plan before subagent-dispatch:

```bash
PLAN="$HOME/.hermes/plans/<plan-file>.md"
echo "=== Has Pre-Plan Reality-Check table? ==="
grep -c "Realitäts-Status\|Reality-Check\|Pre-Plan" "$PLAN"
echo "=== Has effort-estimates? ==="
grep -cE "[0-9]+ Min" "$PLAN"
echo "=== Has R1-Rn risk section? ==="
grep -cE "^### R[0-9]" "$PLAN"
echo "=== Has wave strategy? ==="
grep -cE "Welle|Wave" "$PLAN"
echo "=== Has Done-Kriterium checkboxes? ==="
grep -cE "^- \[ \]" "$PLAN"
```

Expected: 1+ for each. Any 0 = plan needs the missing strategy added before
queen-dispatch.

## Plan Health Dashboard (Mass-Audit)

When you need to evaluate plan quality **across ALL plans** (not one at a time),
run the mass-audit reference script. It scans every plan in `~/.hermes/plans/`,
scores them against the 6 quality gates (S1, S2, S3, S5, S6, S7), groups them
by creation date, and shows the quality trend over time.

```bash
bash ~/.hermes/skills/software-development/better-plan-strategy/scripts/plan-mass-audit.sh
bash ~/.hermes/skills/software-development/better-plan-strategy/scripts/plan-mass-audit.sh

**Quick Gate Check (single plan):** For checking ONE plan before subagent dispatch
(not a full mass-audit), run the compact S1-S7 gate script:

```bash
bash ~/.hermes/skills/software-development/better-plan-strategy/scripts/verify-plan-quality-gates.sh ~/.hermes/plans/my-plan.md
```

Exit codes: `0` = all gates green (ready for dispatch), `1` = gates failed (plan needs rework), `2` = plan file not found.

**Expected output shape:**
```
=== Trend by Date ===
  2026-06-17 | avg=0.5/6 max=1/6 | ██
  2026-07-17 | avg=3.3/6 max=6/6 | ██████████████████  ← after skill was loaded
=== Overall Stats ===
  Total plans: 23
  Average score: 1.2/6
  Plans with score >= 4/6: 2 (8%)
  Plans with score 0-1/6: 19 (83%)
```

Use this before:
- Prioritizing which plans to retro-fit with quality gates
- Deciding if the plan-pipeline is actually improving over time
- Demonstrating the gap between skill-ownership and skill-application
- Starting a new planning-heavy session (run once to calibrate)

The scripts live at `scripts/plan-mass-audit.sh` (cross-plan trend) and
`scripts/verify-plan-quality-gates.sh` (single-plan gate check). Both require
Python 3 and the bash shell. No dependencies beyond stdlib.