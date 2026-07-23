---
name: coding-pipeline-orchestrator
description: "Use when user asks to create or operate a reviewed coding pipeline in Hermes Kanban, assign implementation and review steps, promote gated tasks, or recover a blocked pipeline. NOT for a one-off quick fix or unreviewed direct coding. Creates the root-plus-steps workflow and coordinates worker, reviewer, verdict, and acceptance gates."
version: 1.0.0
author: Hermes Agent (hermes-v2 plan, H-31, 2026-07-20)
license: MIT
platforms:
  - linux
  - macos
metadata:
  hermes:
    tags: ['orchestration', 'coding-pipeline', 'kanban', 'review-loop', 'hermes-v2']
    related_skills:
      - subagent-driven-development
      - requesting-code-review
      - critic-gate
      - test-driven-development
      - writing-plans
      - simplify-code
      - verify-before-fix
      - coding-specialist
lane: koenigin
reasoning_effort: xhigh
agent: Orchestrator
routing_hint: |
  **Agent-Scope:** Spawn + supervise a kanban coding pipeline for ONE
  feature/fix. Hands off individual tasks to worker / gate lanes.
  Off-scope: small edits, docs, one-off scripts (do those directly).
trigger_keywords: ['and', 'coding', 'pipeline', 'coding-pipeline-orchestrator', 'create']
keywords: ['coding', 'pipeline', 'steps', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['code-review-checklist', 'multi-agent-work', 'coding-agents']
---

---

# Coding Pipeline Orchestrator (hermes-v2)

This skill creates a **kanban-driven coding pipeline** — a root task
and five step tasks that guide a single code change from "write" to
"merge-ready" with explicit review gates. It is the v1 implementation
of the hermes-v2 plan's H-31 task for non-trivial changes.

The pipeline is **convention, not engine**. `spawn_pipeline.py` creates
only the blocked task scaffold with `workflow_template_id='coding-pipeline'`
and `current_step_key` metadata. The orchestrator assigns and promotes
each step in sequence, reads review comments, and reacts to review
verdicts. H-53 is intended to automate that sequencing later; there is
no functioning automated end-to-end review loop today.

## When to Use

Use this skill when:
- The change is non-trivial (multi-file, has design tradeoffs, or
  will be reviewed by someone other than the author).
- You want **explicit review gates** between "code is written" and
  "code is mergeable".
- You want **recoverable state** — if a worker dies mid-step, the
  pipeline can resume from the last completed step.

Do NOT use this skill when:
- The change is a one-line fix or a single-file edit.
- The change is documentation-only (use `writing-plans` + a single
  `hermes kanban create` task instead).
- You want to do the change yourself, not delegate. Use the
  `writing-plans` skill to plan, then execute manually.

## Quick Start

```bash
~/.hermes/hermes-agent/venv/bin/python3 \
    ~/.hermes/skills/software-development/coding-pipeline-orchestrator/scripts/spawn_pipeline.py \
    --title "Add idempotency-key to webhook handler" \
    --body "..." --board hermes-v2 --priority 5
hermes kanban --board hermes-v2 list \
    --workflow-template-id coding-pipeline
```

This creates only the blocked task scaffold. The orchestrator must
assign and promote the steps in the order below and handle each review
verdict; the helper does not run an automated review loop.

## Workflow

### Pipeline Shape

Five step tasks sit under one root. The script force-loads the listed
skills; the orchestrator supplies the sequence and review reaction.

| Step | `current_step_key` | Force-load skills | Lane | Completion contract |
|---|---|---|---|---|
| 1. implement | `implement` | `test-driven-development`, `coding-specialist`, `verify-before-fix` | `worker-heavy` (glm-5 or M3) | Code compiles and new/updated tests pass; no review verdict. |
| 2. spec-review | `spec-review` | `writing-plans`, `test-driven-development`, `requesting-code-review`, `critic-gate` | `gate` (glm-5) | Gate: `spec-review`; `VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES`. |
| 3. quality-review | `quality-review` | `simplify-code`, `critic-gate`, `output-validator` | `gate` (glm-5) | Gate: `quality-review`; `VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES`. |
| 4. fix | `fix` | `verify-before-fix`, `test-driven-development`, `simplify-code` | `worker-heavy` (glm-5) | Address root-task review comments and rerun verification; no review verdict. |
| 5. re-review | `re-review` | `requesting-code-review`, `critic-gate` | `gate` (glm-5) | Gate: `re-review`; `VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES`. |

The orchestrator promotes `implement`, then `spec-review`. Approval
advances to `quality-review`; requested changes route through `fix` and
`re-review`. A re-review request can start another fix/re-review cycle
or pause for a human. H-53 will automate this convention later.

**Modell-Fit der Lanes (2026-07-21 / G-3).** Die Lane-Spalte oben nennt Modelle nur illustrativ — welches Modell eine Lane real fährt, steht in `skill_lanes` (Source of Truth; live: `worker-heavy`=glm-5, `gate`=glm-5, `worker-vision`=MiniMax-M3). Praktisch:
- **`worker-heavy`/`gate` = GLM:** briefe implement/fix/review-Schritte mit expliziter Tool-Disziplin und **flachen Argument-/`result.json`-Shapes** (GLM emittiert sonst Repr-Listen, die `coerce_tool_args` reparieren muss). GLMs Reasoning ist nicht persistent → verträgt lange Review-Kontexte gut (stark im Planen/Prüfen).
- **implement/fix auf MiniMax-M3** (wenn auf `worker-vision`/M3-Profil geroutet): starker nativer Caller mit erhaltenem Reasoning → knapp briefen, es denkt selbst; lange Prosa nur wo nötig (M3 füllt Kontext mit Denken).
- Der Kind-System-Prompt hängt die passende Modell-Notiz seit G-2 automatisch an — briefe nach **Rolle/Lane**, nicht nach Modell-ID.

### Spawning Details

Use the included helper script `scripts/spawn_pipeline.py` (or
construct the same calls via the kanban CLI). Both forms:

#### Helper script (preferred — sets workflow metadata via Python API)

```bash
~/.hermes/hermes-agent/venv/bin/python3 \
    ~/.hermes/skills/software-development/coding-pipeline-orchestrator/scripts/spawn_pipeline.py \
    --title "Add idempotency-key to webhook handler" \
    --body "..." \
    --board hermes-v2 \
    --priority 5
```

The script:
1. Creates the root task (`workflow_template_id='coding-pipeline'`,
   `current_step_key='root'`, priority from `--priority`).
2. Creates five blocked child tasks (`current_step_key=implement|spec-review|
   quality-review|fix|re-review`), each linked under the root via
   `task_links`, each with `skills=` set to the force-load list above.
3. Stores the plan/spec in the root body and, when `--plan-file` is
   used, attaches that file to the root.
4. Prints the task-id tree so the orchestrator can run `hermes kanban
   --board hermes-v2 list --workflow-template-id coding-pipeline`.

It does not assign workers, promote steps, parse reviews, or execute an
end-to-end loop; the orchestrator performs those actions by convention.

#### CLI form (no metadata — fine for manual one-offs)

```bash
ROOT=$(hermes kanban --board hermes-v2 create \
    "Add idempotency-key to webhook handler" \
    --body "..." --priority 5 --json | jq -r .id)
hermes kanban --board hermes-v2 create "implement" --parent "$ROOT" \
    --skill test-driven-development --skill coding-specialist --skill verify-before-fix
hermes kanban --board hermes-v2 create "spec-review" --parent "$ROOT" \
    --skill writing-plans --skill test-driven-development \
    --skill requesting-code-review --skill critic-gate
hermes kanban --board hermes-v2 create "quality-review" --parent "$ROOT" \
    --skill simplify-code --skill critic-gate --skill output-validator
hermes kanban --board hermes-v2 create "fix" --parent "$ROOT" \
    --skill verify-before-fix --skill test-driven-development --skill simplify-code
hermes kanban --board hermes-v2 create "re-review" --parent "$ROOT" \
    --skill requesting-code-review --skill critic-gate
```

The CLI form omits `workflow_template_id` / `current_step_key`
metadata, so `hermes kanban --board hermes-v2 list
--workflow-template-id coding-pipeline` will not see CLI-spawned tasks.
Prefer the helper script when those filters matter.

### Verdict Protocol

Each reviewer leaves exactly one machine-readable verdict line in its
task comment. The gate is named separately in text or metadata:

```
Gate: spec-review
VERDICT: APPROVE
Notes: Matches the plan and acceptance criteria.
```

```
Gate: quality-review
VERDICT: REQUEST_CHANGES
Notes: Missing error handling on the 5xx path; see lines 42–48.
```

Only `VERDICT: APPROVE` and `VERDICT: REQUEST_CHANGES` are valid.
The orchestrator reads them as follows:
- `VERDICT: APPROVE` → complete that review gate and promote the next
  conventional step.
- `VERDICT: REQUEST_CHANGES` → preserve the notes on the root
  blackboard and route work through `fix` and `re-review`.
- Missing, duplicate, or any other verdict → stop for human review.

H-53 is planned to automate this parsing and routing; until then, the
orchestrator performs it explicitly.

### Worker Assignment

The helper script creates all five tasks as
`assignee=None` + `initial_status="blocked"` (the dispatcher-safe
state per H-22). The operator assigns workers as they become
available:

```bash
hermes kanban --board hermes-v2 assign "$IMPLEMENT_TASK_ID" yuno-coder
hermes kanban --board hermes-v2 promote "$IMPLEMENT_TASK_ID"
```

**Lane mapping** (defined in `~/.hermes/config.yaml:skill_lanes`):

| Step | Lane | Profile | Provider | Why |
|---|---|---|---|---|
| implement | `worker-heavy` | `yuno-coder` | `zai` (glm-5) | Heavy reasoning, code generation |
| spec-review | `gate` | `yuno-coder` | `zai` (glm-5) | xhigh reasoning, quality review |
| quality-review | `gate` | `yuno-coder` | `zai` (glm-5) | xhigh reasoning, quality review |
| fix | `worker-heavy` | `yuno-coder` | `zai` (glm-5) | Heavy reasoning, refactor |
| re-review | `gate` | `yuno-coder` | `zai` (glm-5) | xhigh reasoning, final approval |

For higher-stakes work, override the per-step `assignee` to a profile
that maps to M3 (e.g. `yuno-vision` for visual reviews, or a custom
profile pointing at the `minimax` provider). The lane is the
default; the per-task `assignee` is the override.

### Reviewer Blackboard (H-50)

The fix step's job is to **address reviewer feedback**. Every review
comment is copied to the pipeline root, with the gate named separately.
The fix worker reads those comments with `show`, which includes comments
without an extra flag:

```bash
hermes kanban --board hermes-v2 comment "$ROOT_TASK_ID" \
    $'Gate: spec-review\nVERDICT: REQUEST_CHANGES\nNotes: Missing 5xx handling.'
hermes kanban --board hermes-v2 show "$ROOT_TASK_ID"
```

The fix task body includes the original root plan. The current review
feedback comes from the root comments above. The `verify-before-fix`
skill (force-loaded on the fix step) requires every reviewer comment to
be addressed in code or explicitly marked out of scope in a reply — no
silent drops.

The `comment` command appends an auditable row to `task_comments`.
Operators can reconstruct the decision history with `hermes kanban
--board hermes-v2 show "$ROOT_TASK_ID"` without reading worker logs.

### Why Kanban, Not a Subagent Loop?

The hermes-v2 plan explored a "fresh subagent per task" approach via
`delegate_task`. We chose kanban because:
- **Crash recovery**: a subagent loop in the orchestrator's memory
  dies if the orchestrator dies. Kanban state persists.
- **Human-in-the-loop**: any operator with webui access can pause,
  reassign, or insert feedback mid-pipeline.
- **Reviewable trail**: every verdict + comment is a row in
  `task_comments`, auditable from `hermes kanban show $TASK_ID`.
- **Existing infrastructure**: Kanban persistence plus claim,
  heartbeat, and retry support keep each task recoverable; the
  orchestrator still controls step ordering and review reactions.

## Verification and Acceptance

A scaffold and its orchestrated run are correct when:
1. `hermes kanban --board hermes-v2 list --workflow-template-id
   coding-pipeline` shows the root and all five steps.
2. Each step title starts with its `current_step_key`.
3. Each step's `skills` field matches the force-load table above.
4. The root body contains the plan/spec; when `--plan-file` is used,
   that file is also attached.
5. Every review comment contains exactly one canonical verdict line,
   with the gate named separately.
6. The orchestrator explicitly drives `implement → spec-review →
   quality-review`, routing requested changes through `fix → re-review`.
   The helper alone is not expected to complete this sequence.

Run the existing tests with the repository environment:

```bash
/home/bratan/.hermes/hermes-agent/venv/bin/python -m pytest \
    tests/test_spawn_pipeline.py
```

### Manual v1 Start (sticky root + parent-gate)

In v1 there is **no** functioning automated sequencer. The
pipeline scaffold is dropped into a deliberately sticky state
and stays there until the operator walks it forward step-by-step.

**Why the scaffold is sticky.** `spawn_pipeline.py` creates the
root with `initial_status='blocked'` and every child the same way.
The lifecycle's parent-gate refuses to auto-promote a child whose
parent is not yet `done`/`archived`, and `recompute_ready` is
defensively tuned to leave a parentless / blocked root sitting at
`blocked` (H-22 dispatcher guard). After a spawn call you can
verify the scaffold state with:

```bash
hermes kanban --board <SLUG> list --workflow-template-id coding-pipeline
# All six rows: root + 5 children, every status='blocked'.
```

The root stays as the park / blackboard task for the whole run —
operator comments, plan attachments, and review verdicts all live
on the root — and is **not** meant to be promoted.

**Normal promotion of a child fails because of the parent-gate.**
`hermes kanban --board <SLUG> promote <STEP_ID>` checks `task_links`
for unsatisfied parents; the root is `blocked`, not `done`, so the
command refuses:

```
hermes kanban --board hermes-v2 promote t_<implement>
→ (refused) unsatisfied parent dependencies: t_<root> (use --force to override)
```

**Manual v1 start sequence.** Promote and activate exactly one step
at a time. Wait for the gated step to finish and `complete` before
moving to the next. The first activation deliberately uses `--force`
because the root is parked by design, not because it is actually a
dependency the implement step is waiting on:

```bash
ROOT=$(hermes kanban --board hermes-v2 list \
    --workflow-template-id coding-pipeline --json | jq -r '.[0].id')

IMPLEMENT=$(hermes kanban --board hermes-v2 list \
    --workflow-template-id coding-pipeline --json \
    | jq -r '.[] | select(.current_step_key=="implement") | .id')

# 1. Park + blackboard: do NOT promote the root.
# 2. Force-activate implement — the root is parked by design.
hermes kanban --board hermes-v2 assign "$IMPLEMENT" yuno-coder
hermes kanban --board hermes-v2 promote "$IMPLEMENT" --force

# 3. Wait for implement to complete (hermes kanban show / webui),
#    route its review comments to the root, then start the next step:
hermes kanban --board hermes-v2 complete "$IMPLEMENT" \
    --result "..." --summary "..."
# Now the next child has its satisfied parent — but the *root* is
# still blocked, so subsequent promotes also need --force for the
# same reason. This is why the v1 sequence is operator-driven.
```

**`--force` here is a deliberate operator override**, not a default.
It records `forced: true` on the `promoted_manual` task_event row
so the override is auditable. Do **not** script it into routine
promotion; treat each `--force` as an explicit "I have looked at
the root and the prior step is ready to be unblocked" decision.

## Anti-Patterns

- Treating `spawn_pipeline.py` as a workflow engine or claiming it runs
  an automated end-to-end review loop.
- Passing comma-separated skills instead of repeating `--skill`.
- Placing `--board` after the Kanban subcommand or assuming `show`
  needs a separate flag to include comments.
- Encoding the gate name inside a third verdict token instead of using
  one of the two canonical verdict lines.
- Promoting every blocked step at once rather than following the
  orchestrator-controlled sequence.

## Failure Recovery

| Symptom | Likely cause | Fix |
|---|---|---|
| All five children remain `blocked` | This is the expected scaffold state; no step was assigned and promoted | Run `hermes kanban --board hermes-v2 assign "$TASK_ID" <profile>`, then `hermes kanban --board hermes-v2 promote "$TASK_ID"` for the next step only |
| A review finishes but the next step does not start | H-53 automation is not implemented | Read the root with `hermes kanban --board hermes-v2 show "$ROOT_TASK_ID"`, apply the verdict convention, then promote the appropriate step |
| A verdict is not recognized | The comment has no canonical line, more than one, or another token | Edit/repost the review with exactly `VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES`; keep the gate separate |
| The scaffold appears on the wrong board | Board context was implicit or the global flag was misplaced | Pass `--board` to the helper, or use `hermes kanban --board <slug> <subcommand> ...` |

## Related Skills

- `subagent-driven-development` — same shape but with inline subagents
  instead of Kanban tasks. Use this for a one-shot run without
  persistence.
- `writing-plans` — produces the implement step's source of truth.
- `requesting-code-review` — loaded by review workers.
- `critic-gate` — enforces the canonical review verdict format.
- `verify-before-fix` — loaded by implement and fix workers so
  regressions surface before any human-approved commit.
