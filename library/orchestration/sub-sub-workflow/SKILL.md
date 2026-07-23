---
name: sub-sub-workflow
description: |
  Use when dispatching parent agents that need to spawn verifiable sub-subagents, structuring a 3-level agent hierarchy, or running a sub-sub workflow with self-verify gates.
  NOT for flat 2-level dispatch (parent → child), single-agent runs, or agent chains without verification — too shallow for this skill.
  Dispatch parent agents that spawn verifiable sub-subagents.
version: 0.3.0
author: Hermes + Yuno
metadata:
  hermes:
    tags:
    - Orchestration
    - Subagents
    - Verification
    - Multi-Agent
    related_skills:
    - multi-agent-master-workflow
    - multi-agent-pitfalls-cheatsheet
    - agent-orchestration-patterns-2026
license: MIT
trigger_keywords: ['parent', 'agent', 'agents', 'spawn', 'verifiable']
keywords: ['parent', 'agent', 'agents', 'spawn', 'verifiable']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

# Sub-Sub Workflow

Dispatches parent subagents that each spawn a verifiable sub-subagent.
Use when a task splits cleanly into a parent deliverable plus an
independently verifiable subtask that benefits from an isolated context.
The workflow relies on `delegate_task` with `role='orchestrator'` and
hard side-effect files as proof of the spawn.

## When to Use

- "Spawn N parent subagents where each delegates a sub-task."
- "Use a Sub-Sub-Workflow with verifiable outputs."
- "Test subagent-of-subagent delegation."
- "Run sub-sub fan-out with sha256sum/file-size proof."

## Prerequisites

- `delegation.max_spawn_depth` >= 2 in `~/.hermes/config.yaml`.
  Raise via `hermes config set delegation.max_spawn_depth 2`.
- `delegation.orchestrator_enabled: true` in same config.
- `delegation.max_concurrent_children` aware: a fan-out of N parents
  plus N subs consumes `2N` of the configured child budget.
- Working directory `/tmp/<test-prefix>/` for side-effect files;
  `terminal` and `file` toolsets on every agent.
- **Model resolution (matters when Queen != default M3)**:
  The `model` argument of `delegate_task` is IGNORED at
  `tools/delegate_tool.py:1161` — children inherit from config.
  Effective priority: `delegation.provider+model` (pinned) →
  `model.provider+model` (main) → `parent_agent.model`.
  Pin in `~/.hermes/config.yaml` to keep a sub-fleet on a
  cheap model while the Queen runs Claude or GLM 5.2. If
  unpinned, switching the Queen switches the sub-fleet too,
  which can blow budget silently.

## How to Run

Invoke through the `delegate_task` tool with `tasks=[...]` array.
Each item MUST set `role='orchestrator'` (not the default `leaf`)
so the child keeps `delegate_task` in its toolset. Each parent
briefing names two side-effect files: a parent deliverable path
that always exists, and a sub-sub deliverable path that proves
the spawn. Self-Report must include `sub_call_count`.

## Quick Reference

- Tool: `delegate_task`
- Required role: `'orchestrator'`
- Config key: `delegation.max_spawn_depth` (>= 2)
- Side-effect file pattern: `/tmp/<prefix>/<ts>.{json,md,txt}`
- Sub-sub side-effect file: `/tmp/<prefix>/<ts>-sub.{ext}`
- Verification: `ls -la /tmp/<prefix>/<ts>*`
- Cross-check: `sha256sum` parent-recompute vs sub-file content
- Memory refs: 3d8dac1c8769ad7e (positive validation),
  fe6db9a5cc653773 (briefing pattern),
  1347071a1a693e4c (failure root cause)

## Procedure

1. Pick a fan-out scale `N`. Confirm `2N <= max_concurrent_children`
   before dispatch. For 3 parents + 3 subs, the default budget of 6
   is exactly at the limit.
2. Run `hermes config set delegation.max_spawn_depth 2` if not
   already raised. Verify with `grep max_spawn_depth ~/.hermes/config.yaml`.
3. Create the side-effect directory:
   ```bash
   mkdir -p /tmp/<prefix>/ && date +%s
   ```
   Use the timestamp `TS` as a deterministic suffix shared by all
   parent and sub-sub files in this run.
4. Author one parent task per item in `tasks=[...]`. Each task
   sets `role='orchestrator'` and includes in `goal`:
   - Parent deliverable path: `/tmp/<prefix>/<TS>.<ext>`
   - Sub-sub deliverable path: `/tmp/<prefix>/<TS>-sub.<ext>`
   - Explicit sentence: "If the sub-file is missing after your work,
     you did not delegate. Retry with `delegate_task(..., toolsets=['terminal','file'])`.
   - Self-Report requirement: `sub_call_count`, both file sizes,
     both file paths, a Lohnt-sich-Bewertung line.
5. Call `delegate_task(tasks=[...], role='orchestrator')`.
6. When the batch callback arrives, verify with the `terminal` tool:
   ```bash
   ls -la /tmp/<prefix>/<TS>*
   ```
   All `2N` files must exist. A missing `-sub` file means the parent
   did not delegate, even if its parent file looks plausible.
7. For sha256-style side effects, run parent-recompute:
   ```bash
   while read h f; do
     [ "$h" = "$(sha256sum "$f" | awk '{print $1}')" ] \
       && echo "MATCH: $f" || echo "MISMATCH: $f"
   done < /tmp/<prefix>/<TS>-sub.txt
   ```
   Every line must print `MATCH`. A mismatch means the sub-sub
   fabricated its output rather than reading the live filesystem.
8. Persist findings via `mnemosyne_remember` with `importance >= 0.85`
   and `veracity='tool'`. Use the pattern `importance: 0.95` for
   validated-positive events, `0.85` for the briefing pattern.

## Pitfalls

- `role='leaf'` (the default) strips `delegate_task` from the
  child toolset at `tools/delegate_tool.py:705`. Parents will run,
  finish cleanly, and silently never spawn subs. The Self-Report
  will look correct; only the missing sub-side-effect file reveals
  the failure. Always verify with `ls`, never trust the report.
- `max_spawn_depth=1` blocks nested delegation regardless of role.
  Raising it without setting role='orchestrator' does nothing
  visible; both conditions must hold.
- `max_concurrent_children` is a hard concurrency cap, not a queue.
  A fan-out of `2N` parents plus subs must fit `max_concurrent_children`
  at the moment of dispatch; otherwise the surplus gets rejected.
- Sub-subs are NOT free. Boot time, prompt-token overhead, and the
  tool round-trip add 30-90 seconds of wall time. Sub-Sub pays off
  when the subtask carries non-mechanical reasoning (diagnosis,
  classification) or produces enough output volume to relieve the
  parent context. For pure IO (`sha256sum`, `cp`, `ls`) inline work
  is faster and cheaper.
- Side-effect files in `/tmp` survive reboots only if `/tmp` is
  not tmpfs-backed. On most Linux desktops `/tmp` is RAM-backed and
  vanishes on poweroff. Copy artifacts you want to keep into the
  Obsidian vault or `~/.hermes/docus/` before the system reboots.
- Sub-subs cannot chain further unless `max_spawn_depth >= 3`.
  The default 2 caps the tree at parent -> sub. Sub-sub-sub needs
  an additional config raise.
- Sub-side-effect files inherit the parent's filesystem but NOT
  the parent's terminal session or working directory. Each sub
  starts in the home directory with its own ephemeral shell.
- **Cross-model spawn works but inherits silently**: when the Queen
  is GLM 5.2 (free) and `delegation.model` is unpinned, every sub
  also runs GLM 5.2. When the Queen is Claude, every sub runs
  Claude (paid). Sub-Sub fans out 2x the spawn count, so an
  unpinned expensive Queen burns budget quickly. Pin in config
  before any Queen swap.

## Verification

A single command proves the workflow succeeded:

```bash
ls /tmp/<prefix>/<TS>* | wc -l
```

The count must equal `2 * N`. For `N=3`, the answer is `6`. A
count of `3` or less means parents ran but did not delegate.
A count of `0` means dispatch never reached the filesystem.
Pair with a parent-recompute of any sha256-side-effect file
to rule out fabricated outputs from the sub.

## Related Skills

- `orchestration/multi-agent-pitfalls-cheatsheet` (Hub) — generic pre-spawn trap-detector. Load **before** drafting sub-sub briefs to catch Pitfall #28 (model-inheritance), #5 (phantom-fixes), and run the 5-question Pre-Spawn Checklist. This skill inlines the sub-sub-specific model resolution caveats; the cheatsheet covers the generic cross-agent failure modes.
- `orchestration/multi-agent-orchestration` — the 3-expert / 5-phase pattern for structured parallel research. The sub-sub workflow extends that pattern by adding nested delegation with hard-verification proof. Combine when each expert's research phase needs its own isolated verification subagent.

## Reference Files

- `references/sub-sub-briefing-template.md` — copy-paste template
  for parent task briefings with the two side-effect paths,
  Self-Report requirements, and the explicit "if the sub-file is
  missing you did not delegate" sentence.
- `references/sub-sub-fullscan-template.md` — fullscan /
  deep-intel template for comprehensive directory/application
  scanning with parallel non-overlap bees. Covers pre-flight,
  scope division, bee briefing structure, non-overlap checklist,
  verification commands, and anti-patterns. Use when the user
  says "vollscan", "deep intel", "alles zu Y rausfinden".
- `scripts/verify-sub-sub.sh` — bash helper that takes a prefix
  and a timestamp, runs `ls` + parent-recompute sha256sum, and
  prints a green/red summary suitable for piping into the parent
  Self-Report.

## Lohnt-sich-Decision-Tree (validiert aus 4 Schwärmen)

Bevor du Sub-Sub dispatchst, bewerte den Sub-Task:

```
Ist der Sub-Task mechanisch (sha256sum, ls, cp, grep)?
├── JA → NICHT per Sub-Sub. Inline ist 10-100x schneller.
│        (Cicada-Test: 5 Hashes inline = 100ms vs Sub-Sub = 90s)
│
└── NEIN → Enthält der Sub-Task Reasoning/Diagnose?
    ├── JA → Sub-Sub LOHNT SICH. Sub-Biene findet Bonus-Erkenntnisse.
    │        (Alpaca: Alias-vs-Hyphen-Bug entdeckt, Beta: 10 weitere
    │         stale Werte in anderer Datei gefunden, Gamma: 38 Links
    │         mit Backup+Verify gepatcht)
    │
    └── NEIN, aber hohes Output-Volumen → Sub-Sub LOHNT SICH
        wenn Output den Parent-Context überlasten würde.
        (Bumble: 13.4KB JSON-Cross-Map = zu groß für Parent-Inline)
```

Faustregel: Sub-Sub kostet 30-90s Wall-Time + Token-Overhead pro
Spawn. Lohnt sich nur wenn der Sub entweder **Erkenntniswert**
oder **Output-Volumen-Entlastung** liefert.

## Erfahrungswerte (4 Schwärme, 13 Bienen, 6 Sub-Subs)

| Schwarm | Bienen | Sub-Subs | Wall | API | Lohnt? | Warum |
|---|---|---|---|---|---|---|
| 1 (Vault-Vervollständigung) | 4 leaf | 0 | 318s | 136 | n/a | leaf, kein Sub-Sub möglich |
| 2 (Sub-Sub v1 FAIL) | 3 leaf | 0 | 210s | 55 | nein | role='leaf' = kein delegate_task |
| 2b (Sub-Sub v2 PASS) | 3 orch | 3 | 285s | 24+41 | gemischt | Cicada=overhead, Alpaca=Bonus-Fund |
| 3 (Cross-Model Vault-Patch) | 3 orch | 3 | 369s | 39+sub | ja! | Alle 3 Subs fanden echte Bonus-Befunde |

**Bonus-Fund-Rate:** 3 von 6 Sub-Subs (50%) fanden Erkenntnisse
die der Parent verpasst hätte. Das ist der eigentliche Wert.

## Cross-Model-Validation (validiert 2026-07-14)

Queen = GLM 5.2 (zai, free), Bienen = M3 (minimax, pinned).
Config-Pinning via `delegation.provider+model` greift zuverlässig.
Sub-Sub-Dispatch funktioniert cross-model ohne Anpassungen.
Wichtig: Pinning VOR dem Queen-Wechsel setzen, nicht danach.