---
name: step-execution
description: "Use when an implementer needs to execute a plan one TODO at a time with a failing test, minimal change, green verification, full-suite check, and checkpoint. NOT for planning, broad multi-task orchestration, or committing without approval. Enforces the small-step TDD micro-loop and marks each verified task complete before moving on."
version: 1.0.0
author: Hermes Agent (hermes-v2 plan, H-52, 2026-07-20)
license: MIT
platforms:
  - linux
  - macos
  - windows
metadata:
  hermes:
    tags: ['execution', 'tdd', 'incremental', 'verification', 'checkpoint-discipline', 'hermes-v2']
    related_skills:
      - test-driven-development
      - verify-before-fix
      - coding-pipeline-orchestrator
      - plan
      - writing-plans
lane: worker-heavy
reasoning_effort: xhigh
agent: Engineer
routing_hint: |
  **Agent-Scope:** Executing a single plan task in tiny verified steps.
  Off-scope: designing the plan (writing-plans), spawning pipelines
  (coding-pipeline-orchestrator), reviewing (code-review-checklist).
trigger_keywords: ['task', 'implementer', 'needs', 'execute', 'plan']
keywords: ['task', 'implementer', 'needs', 'execute', 'plan']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['subagent-driven-development', 'plan', 'writing-plans']
---

---

# Step Execution ("kleine Schritte")

This skill is the **micro-loop** that an `implement` worker runs
inside a coding-pipeline step (H-31), or a worker picking up a plan
task (H-20). It enforces the discipline of "one TODO at a time,
verify, surface a checkpoint, next":

```
while tasks_remaining:
    next_task = pick_smallest_unblocked_TODO
    write_failing_test_for(next_task)        # TDD step 1
    run_tests → MUST FAIL → "red"
    implement_minimal_change_for(next_task)  # TDD step 2
    run_tests → MUST PASS → "green"
    record_checkpoint(next_task)             # verified green, awaiting human commit
    mark_TODO_done_in_plan_file              # - [x]
```

The complement to `coding-pipeline-orchestrator` (H-31, which
manages the macro-level 5-step pipeline). That skill decides
*what* work happens; this skill decides *how* it happens at the
micro-level.

## When to use

Use this skill when you are the **implementer** in a coding-pipeline
step, or when picking up any plan task with more than one TODO. It
is the default for `worker-heavy` lane work.

Do NOT use this skill when:
- The work is a one-line edit (no checklist to iterate over).
- The work is documentation-only (no verify command).
- The plan has a single TODO (use `writing-plans` instead, or just
  do the work).

## Quick Start

Minimal cycle for one TODO, in five shell commands (read each
step in the workflow below before running them):

```bash
# 1. Pull the plan from the task body
hermes kanban show $TASK_ID

# 2. Run the new test alone — expect RED
pytest tests/test_<feature>.py::<test_name> -v

# 3. Implement, then re-run the same test — expect GREEN
pytest tests/test_<feature>.py::<test_name> -v

# 4. Run the full suite to catch regressions
pytest tests/ -x -q

# 5. Surface a checkpoint for the human (no auto-commit)
git status --short && git diff --stat
```

After the human approves the checkpoint, they run `git commit`
themselves. See the workflow below for the rationale and full
discipline.

## The micro-loop

### Step 1 — Pick the smallest TODO

Read the plan (from the task body, or attached as a file). Find the
smallest TODO that is not blocked by other TODOs:

```bash
hermes kanban show $TASK_ID
```

The body contains the plan's tasks block. Pick the first `- [ ]`
line that has all its `depends:` TODOs already `- [x]`.

### Step 2 — Write the failing test FIRST (TDD)

Before touching any production code, write the test that proves the
TODO is done. Run it. It MUST fail. If it passes, your test is
wrong — refine until it fails for the right reason.

```bash
# Write the test
$EDITOR tests/test_<feature>.py
# Run it; expect FAIL with a clear message
pytest tests/test_<feature>.py::<test_name> -v
```

A failing test that doesn't mention your new code means the test
isn't actually exercising what you think. Fix the test before
proceeding.

### Step 3 — Implement the minimal change

Write the smallest possible production code that makes the test
pass. Don't refactor adjacent code. Don't fix other bugs you spot.
Don't add features not in this TODO.

```bash
$EDITOR src/<feature>.py
pytest tests/test_<feature>.py::<test_name> -v
# Expect PASS
```

If you're tempted to "while I'm here, also fix X", stop. File a
follow-up TODO in the plan file (`- [ ] follow-up: ...`) and move
on.

### Step 4 — Run the FULL test suite

The single-test pass isn't enough. Run the full suite to catch
unintended regressions:

```bash
pytest tests/ -x -q
```

If anything other than the new test fails, you broke something.
Either revert or fix forward — but DO NOT commit a known-broken
state.

### Step 5 — Record a verified checkpoint

Hermes workers do **not** auto-commit. After a green verification,
record the checkpoint and surface it to the human for review:

```bash
# Confirm the working tree state for this TODO
git status --short
git diff --stat

# Note: only the human runs `git commit` after explicit approval.
# A suggested message (do NOT execute without approval):
#   git add <test files> <impl files>
#   git commit -m "implement: T<n>: <short description>
#
#   - <bullet from plan, if useful>
#   Refs: H-52 (step-execution), <plan slug>"
```

One TODO = one proposed commit. This keeps the per-step git
history reviewable without giving the worker authority to mutate
branches on its own.

### Step 6 — Mark the TODO done in the plan

Edit the plan file (in the task body or attached). Change `- [ ]`
to `- [x]`. The fix worker on later steps (H-50 blackboard convention)
will read these markings.

```bash
$EDITOR $PLAN_FILE_PATH   # - [ ] T1.1: ... → - [x] T1.1: ...
```

### Step 7 — Loop

Re-evaluate which TODOs are now unblocked (this TODO may have
un-blocked others via `depends:`). Repeat from Step 1 until no
unblocked TODOs remain.

## Verification discipline

Every step has a verify command:

- For TDD work: `pytest tests/test_<feature>.py::<test_name> -v`
- For shell-script work: `bash -n script.sh && bash script.sh`
- For config-only work: `python -c "import yaml; yaml.safe_load(open('config.yaml'))"`
- For documentation work: `grep -c "<expected section>" doc.md` (cheap structural check)

If you can't write a verify command in one line, your TODO is too
big — split it.

## Interaction with coding-pipeline-orchestrator

When this skill runs inside a `coding-pipeline-orchestrator` step:
- The plan = the pipeline root's body.
- The TODOs = the implement step's per-feature work (NOT the 5
  pipeline steps — those are macro-level, decided by the
  orchestrator).
- The review verdicts → posted to the pipeline root (H-50
  blackboard).

When this skill runs standalone (no pipeline):
- The plan = the task body or `--plan-file`.
- Each TODO = one micro-task.
- Verification still per-step.

## Time-boxing

If a single TODO is taking longer than ~5 minutes of focused work
(per the plan's "bite-sized tasks" principle in `writing-plans`),
the TODO is too big — split it. Don't bundle smaller TODOs to
"save time" — the per-step commit + verify cycle is fast enough.

## Acceptance

An execution is "correct" iff:

1. Every TODO has a corresponding test (when the work is testable).
2. Every proposed commit message references the TODO id.
3. Every checkpoint was recorded when `pytest` was green (the
   human runs `git commit` only after that gate).
4. The plan file shows `- [x]` for every TODO the worker claims to
   have finished.
5. No proposed commit contains a `TODO`, `FIXME`, or
   commented-out code.

The orchestrator (or reviewer) can verify these via:
- `git log --oneline <branch>` — should show one commit per TODO
  once the human has approved and committed.
- `grep -c '\[ \]' $PLAN_FILE` — should drop to zero for done TODOs.
- `pytest` — should be green at the worker's last recorded HEAD.

## Anti-patterns (rejected executions)

| Anti-pattern | Why it's rejected |
|---|---|
| Bundling 3 TODOs in one commit | Reviewer can't isolate which TODO introduced a regression; git bisect broken |
| Running tests only at the end of the bundle | Failures can't be attributed; you spend an hour debugging the wrong layer |
| "While I'm here, also fix X" | Scope creep; X deserves its own TODO, its own test, its own commit |
| Commit message just says "wip" | Future reviewer can't tell what the commit does; force a one-line summary |
| Marking TODO done without test | TDD broken; "did it work?" becomes unanswerable |
| Recording a checkpoint (or letting the human commit) when ANY test fails | The commit bisects as bad; never checkpoint red |

## Failure recovery / Troubleshooting

If a step fails mid-execution:
1. **Don't panic-commit.** `git status` to see what's uncommitted.
2. **Revert the partial implementation:** `git checkout -- <file>`.
3. **Re-run the test** to confirm you're back to the previous green
   state.
4. **Re-read the TODO** — maybe the test was right and the
   implementation was wrong; restart from Step 2.
5. **If stuck > 10 min:** post a `WONTFIX: ...` comment to the task
   body and move to the next TODO. Don't burn the whole pipeline on
   one hard problem.

Troubleshooting quick reference:
- *Test passes before the change?* Your test isn't exercising the
  TODO; rewrite it to fail for the right reason.
- *Full suite fails after the new test passes?* Re-run the suite
  with `-x` to surface the first regression, then `git checkout`
  to revert and re-think.
- *Plan body not visible in `hermes kanban show`?* Check for an
  attached plan file (`hermes kanban attachments $TASK_ID`) — the
  body and attachments are separate surfaces.

## Related skills

- `test-driven-development` — the red/green/refactor discipline
  referenced in Steps 2–4.
- `verify-before-fix` — verify each step *before* committing to a
  fix.
- `writing-plans` — produces the bite-sized TODOs this loop
  consumes; pair it when the plan is too coarse.
- `coding-pipeline-orchestrator` — the macro-loop that decides
  *which* TODO this skill should pick up next; the orchestrator
  owns the 5-step pipeline, this skill owns the per-TODO loop.
- `code-review-checklist` — the reviewer that reads the
  per-checkpoint diffs this skill produces.

See also the frontmatter `metadata.hermes.related_skills` for the
machine-readable list.
