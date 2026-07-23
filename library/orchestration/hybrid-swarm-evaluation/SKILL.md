---
name: hybrid-swarm-evaluation
description: >-
  Use when user asks for deciding whether a plan should use a swarm, designing a Queen-Bee plus scout workflow, estimating wall-time savings from parallelism, or reviewing a plan before multi-agent dispatch. NOT for executing a single-worker task or dispatching without first classifying the work. Scores task structure, dependencies, risk, and cost, then recommends an inline, scout-led, hybrid, or fully parallel operating model.
version: 0.1.0
author: Hermes
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - Orchestration
    - Swarm
    - Evaluation
    - Decision-Matrix
    - Hybrid
    related_skills:
    - queen-bee-schwarm-dispatch
    - orchestration/multi-agent-orchestration
    - orchestration/multi-agent-pitfalls-cheatsheet
license: MIT
trigger_keywords: ['plan', 'hybrid-swarm-evaluation', 'deciding', 'whether', 'should']
keywords: ['plan', 'scout', 'task', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['swarm-router', 'plan', 'subagent-driven-development']
---

# Hybrid Swarm Evaluation — Designing Queen+Bee Workflows

Decide whether a task batch needs a Schwarm (parallel Bienen) or is better
handled Parent-Direct (inline), then design the right hybrid mix. Built on the
validated Queen-Pre-Execute pattern: Queen works inline while Scout-Bienen
run orthogonal read-only audits in the background. This is the evaluation and
design layer; for briefing templates and pitfall defense, load
`queen-bee-schwarm-dispatch`.

## When to Use

- You have a multi-task plan and need to decide: inline or Schwarm?
- User says "mit Bienen orchestrieren" or "Schwarm-Arbeit" or "evaluieren"
- Plan has >5 tasks and you want wall-time optimization
- Before dispatching `delegate_task` with 3+ subagents
- After writing a plan, before execution handoff

## Prerequisites

- `delegate_task` tool available (Hermes built-in)
- `queen-bee-schwarm-dispatch` skill loaded for briefing templates
- `orchestration/multi-agent-pitfalls-cheatsheet` loaded for trap defense

## How to Run

Invoke through `execute_code` or inline reasoning. The evaluation is a
4-step decision process that runs BEFORE any `delegate_task` call.

## Quick Reference

```
Step 1: Classify each task (mechanik/code/identity vs research/audit/content)
Step 2: Count swarm-suitable vs parent-direct tasks
Step 3: Design orthogonal scout scopes (if any swarm-suitable)
Step 4: Project wall-time + dispatch
```

## Procedure

### Step 1: Task-Classification Matrix

For each task in the plan, classify into one of two categories:

**Parent-Direct (do NOT delegate):**

| Task Type | Why Not Delegate |
|---|---|
| Mechanik (backup, tar, cp, audit-scan) | Pitfall #34: Parent pre-scan beats subagent |
| Single-file code edit | Subagent context-burn exceeds inline effort |
| Config mutation (.env, config.yaml, SOUL.md) | Identity and config work is Queen-Pflicht |
| Cron creation (`cronjob action=create`) | Parent-Direct, no reasoning needed |
| Deterministic Python script execution | Parent does in seconds, subagent needs minutes |
| Sequential dependencies (B needs A output) | One bee with sub-tasks, not parallel |

**Schwarm-Suitable (delegate to Bienen):**

| Task Type | Why Delegate |
|---|---|
| Read-only audit across many files | Bees excel at broad scans with Content |
| Cross-check / drift-matrix creation | Bees provide judgment, Queen measures |
| Content generation with format constraints | Bees are strong with PFLICHT briefings |
| Stub-healing / vault-note filling | Independent per-file judgment |
| Research / multi-source synthesis | Parallel discovery beats sequential |

### Discovery-Led Bee Dispatch (NEU 2026-07-16 — validiert Security-Audit)

**Problem:** Steps 1-4 dispatch bees BEFORE the Queen knows what concrete Findings to investigate. For RECURRING or TARGETED work (audits with existing baseline, system health checks), the Queen benefits from characterizing first and dispatching TARGETED deep-dive bees.

**Lösung:** Queen characterisiert inline (recon snapshot in ~2 min), identifiziert P0/P1 Findings aus dem Diff zur letzten Baseline, dispatcht Targeted Deep-Dive Bees auf konkrete Findings.

**5-Phasen-Struktur:**

```
Phase 1 — Queen Recon (inline, ~2 Min)
  ├── System-Snapshot (df, ps, ss, systemctl --failed)
  ├── Log-Health (du -sh /var/log/syslog /var/log/journal)
  ├── Service-Health (Boot-Zeit vs. Start-Zeit, Prozess-Tree)
  └── Diff zur letzten Baseline (Besser / Unverändert / Neu)

Phase 2 — Queen P0/P1 Triage
  └── Findings priorisieren (max 2 P0, max 1 P1)
  └── Entscheiden: dispatch notwendig? (P0 vorhanden = ja)

Phase 3 — Targeted Deep-Dive Bees (parallel, background)
  ├── Biene 1: P0 Scope A (z.B. Port 8642 Service-Audit)
  ├── Biene 2: P0 Scope B (z.B. Syslog-Wachstum RCA)
  └── Biene 3: P1 Scope C (z.B. Health-Check, supporting)

Phase 4 — Queen arbeitet parallel (Queen-Pre-Execute)
  ├── Report schreiben (Findings-Tabelle, Drift-Sektion, A/B/C/D-Optionen)
  └── NUR Mechanik/IO-Tasks — kein Reasoning das Bee-Outputs braucht

Phase 5 — Bees landen → Queen integriert
  └── Report patchen + Cross-Check Bee-Findings vs Queen-Triage
```

**Wann Discovery-Led statt Standard-Dispatch:**

| Situation | Pattern | Begründung |
|-----------|---------|-----------|
| Unbekanntes System, breiter Check | Standard (Step 1-4) | Scouts geben Überblick |
| Recurring Audit, Baseline vorhanden | Discovery-Led | Queen nutzt Diff, Bees targeted |
| User sagt "schnell checken" | Discovery-Led (Mini) | 1-2 Bees statt 3-5 Scouts |
| User sagt "tiefes Eintauchen" | Discovery-Led + Welle 2 | Queen identifiziert Tiefen-Bereiche |

**Vorteile gegenüber Standard:**
- Weniger Bee-Warmup-Kosten (Bees targeted statt generisch)
- Queen hat Report bereits fertig wenn Bees landen (keine Serialisierung)
- Diff zur Baseline eliminiert Scout-Neustart-Kosten
- Niedrigere False-Positive-Rate (Queen triagiert Findings vor Bee-Dispatch)

**Bee-Scope-Design-Heuristik (validiert 3 Bees):**
```
Biene 1: P0 — externer Service / Gateway / Expositions-Prüfung
         → Layer-4 Service Audit (Route Probing, Auth, Network Exposure, Config Tracing, Lifecycle)
Biene 2: P0 — System-Integrität / Logs / Disk-Wachstum
         → Log-Trend, Rotations-Status, Haupt-Verursacher
Biene 3: P1 — Health-Check / Cron / Prozess-Leakage (Supporting)
         → Container-Count, Prozess-Watchdog, Cron-Coverage
```

**Weniger als 3 Bees:** Wenn Queen nur 1 P0 findet → 2 Bees (P0 Deep-Dive + P1 Health).
Wenn 0 P0 → kein Schwarm nötig (Queen macht alles inline).

**Referenz:** `system-security-audit` → Post-Run Learnings (2026-07-16) für das vollständige Audit-Beispiel mit Briefing-Templates, Baseline-Comparison-Format und 3-Bee-Report-Integration.

### Step 2: Hybrid Model Design

If >0 tasks are swarm-suitable, design orthogonal scout scopes.

Orthogonal means: Bienen finden was Queen uebersieht. Not the same work
parallelized, but ADDITIONAL coverage.

```
QUEEN (arbeitet sequenziell)     BIENEN (parallel, read-only)
Task A: Mechanik                 ─
Task B: Code edit            ←→  S1: Audit Domain A
Task C: Identity             ←→  S2: Audit Domain B
                                  S3: Audit Domain C
Task D: Verify               ←→  [Bienen landen]
Synthesis: Cross-Check       ←   Bienen vs Queen
```

Rules:
- Max 3-4 Scout-Bienen per wave (more = context-bloat + verify overhead)
- Each Biene gets a UNIQUE output domain (file-affinity check before dispatch)
- Bienen sind Insurance/Oversight, nicht Gate. Queen wartet nicht auf sie.
- Bienen machen NICHT die Mutation. Sie finden was Queen uebersieht.

### Step 3: Wall-Time Projection

```
inline_only  = sum(all task durations) sequential
hybrid       = queen_sequential + verify_overhead
              (bienen laufen parallel zur queen, kein warten)

speedup_pct  = (inline_only - hybrid) / inline_only * 100
```

Typical: 20-35% wall-time reduction with higher audit quality.

### Step 4: Dispatch via Queen-Pre-Execute

1. Dispatch Scout-Bienen via `delegate_task(tasks=[...])` (background mode)
2. Queen arbeitet sofort weiter inline, wartet NICHT auf Bienen
3. Bienen landen automatisch (results re-enter conversation)
4. Queen macht Tier-3 Reality-Check bei Synthesis

## Scout-Briefing Template (PFLICHT Constraints)

```text
Du bist Biene S(N) (<Role>) in Yunos Schwarm.

KONTEXT: [2-3 sentences what Queen is doing]

DEINE TASKS (ALLE READ-ONLY):
1. [specific task with paths]
2. [specific task with paths]

TOOLSET: terminal (read-only), read_file. KEIN write_file, KEIN sudo.

OUTPUT-CONSTRAINTS (PFLICHT - NICHT VERHANDELBAR):
- Output: REIN TEXT in deiner Antwort (kein File-Write)
- Sprache: Deutsch
- Max 800 Woerter
- 0 em-dashes, Kommas statt Gedankenstrichen
- 0 mid-sentence boldface
- Pro Finding: Pfad + konkrete Zahlen
- SELF-REPORT am Ende: N tool-calls, M findings

MAX 10-12 tool-calls. Nach Limit Synthese mit was du hast.
Self-Verify: Nichts erfinden.
```

Critical (validated 2026-07-14): PFLICHT wording produces 0 violations.
Bevorzugen wording produces 17+. Wortwahl ist der groesste Einzelfaktor.

## Pitfalls

- Dispatching Bienen for mechanik tasks wastes tokens. Deterministic tasks
  (tar, cp, grep, wc) are done by Queen in seconds. Pitfall #34.
- Waiting for Bienen before continuing. Queen-Pre-Execute means Queen works
  while Bienen scout. Only wait at synthesis time.
- Bienen doing the same work as Queen is redundancy not insurance. Orthogonal
  means ADDITIONAL coverage, not parallelized duplication.
- Self-Report trust. Bienen-Self-Reports are unreliable. Always run Tier-3
  Reality-Check with the real filesystem.
- More than 4 Bienen per wave causes context-bloat. Verify-overhead exceeds
  gains.
- No file-affinity check. Two Bienen writing the same file causes lost writes.
  Check unique output paths BEFORE dispatch.

## Verification

After Bienen land, run the 3-Tier Queen-Verify.

Tier 1 Datei-Existenz, check if claimed output files exist.
Invoke through the `terminal` tool:
```bash
ls -la <OUTPUT_PATH> && wc -l <OUTPUT_PATH>
```

Tier 2 Content-Validierung, check structure.
```bash
grep -c "^## " <file>
grep -cE "[0-9]+" <file>
```

Tier 3 Realitaets-Check, CRITICAL for Pitfall #5 defense. Re-derive the key
claim independently rather than trusting the Biene report:
```bash
find ~/.hermes/skills -name SKILL.md | wc -l
crontab -l | grep -v '^#' | grep -v '^$' | wc -l
```

Write the consolidated Schwarm-Verifikations-Matrix in the final report.
If any Tier fails, mark findings as PARTIAL UNVERIFIED in the synthesis.
