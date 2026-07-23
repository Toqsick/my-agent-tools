---
name: plan
description: "Use when user wants an actionable, machine-readable implementation plan instead of execution, including phased tasks, bite-sized work items, acceptance criteria, or a saved plan file. NOT for implementing code or answering a trivial request that needs no plan. Enforces Plan Mode, structured YAML and task contracts, dependency awareness, and verification-oriented writing."
version: 3.0.0
author: Hermes Agent (writing-craft adapted from obra/superpowers)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - planning
    - plan-mode
    - implementation
    - workflow
    - design
    - documentation
    - hermes-v2
    related_skills:
    - subagent-driven-development
    - test-driven-development
    - requesting-code-review
    - writing-plans
    - hermes-kanban
lane: koenigin
reasoning_effort: xhigh
agent: Engineer
routing_hint: '**Agent-Scope:** Code-Tasks (build / fix / refactor / debug / review).
  Off-scope: visual design, long-form copy, data modeling — say ''this is Designer/Writer/Analyst''s
  territory'' and return to Yuno.


  Routing-Spec: `yuno-team-routing`.

  '
trigger_keywords: ['plan', 'user', 'wants', 'actionable', 'machine']
keywords: ['plan', 'user', 'wants', 'actionable', 'machine']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['hermes-plan-mode-recovery', 'writing-plans', 'plan-review-and-orchestrate']
---

---

# Plan Mode

Use this skill when the user wants a plan instead of execution.

## Core behavior

For this turn, you are planning only.

- Do not implement code.
- Do not edit project files except the plan markdown file.
- Do not run mutating terminal commands, commit, push, or perform external actions.
- You may inspect the repo or other context with read-only commands/tools when needed.
- Your deliverable is a markdown plan saved inside the active workspace under `.hermes/plans/`.

## Output requirements

Write a markdown plan that is concrete and actionable.

Include, when relevant:
- Goal
- Current context / assumptions
- Proposed approach
- Step-by-step plan
- Files likely to change
- Tests / validation
- Risks, tradeoffs, and open questions

If the task is code-related, include exact file paths, likely test targets, and verification steps.

## Plan File v2 Contract (hermes-v2, machine-parseable)

When the user wants the plan to be **approvable via `/plan approve`** — meaning the kimi-mode plugin will parse it and seed a Kanban board (H-22) — write the plan in the v2 contract below. v2 plans are an additive superset of the free-form format: every section that follows is required for approval, and the heading/checkbox conventions are exact so a parser can round-trip them.

### Required YAML frontmatter

The plan MUST start with a YAML frontmatter block. All keys are required.

```markdown
---
slug: starman-booster-gold-red-star   # URL-safe identifier; idempotency key
title: Hermes v2 Verbesserungsplan     # Human-readable title
goal: |
  Bring Hermes/Yuno to Claude Code / Kimi Code workflow level.
  In one sentence.
scope_tiers:                          # A=Muss, B=Soll, C=Kür
  A: [H-01, H-10, H-11, H-22]
  B: [H-12, H-13, H-20, H-50]
  C: [H-08, H-15, H-64]
risks:
  - Core-Patches kollidieren mit Upstream → git revert + Branch hermes-v2-work
  - state.db-VACUUM braucht 2× Disk → Freien Platz prüfen
verification:
  - ./scripts/run_tests.sh tests/run_agent/ -k 'minimax or thinking_budget' grün
  - Live-Session mit 3 Tool-Runden zeigt Thinking-Blöcke im Replay
created_by: yuno
created_at: 2026-07-20
model: MiniMax-M3
provider: minimax
---
```

Field semantics:
- `model` / `provider` — **optionale Routing-Hinweise, keine Pflichtfelder.** Der Wert im Beispiel oben (`MiniMax-M3`/`minimax`) ist illustrativ; lässt du beide weg, erbt der Task das aktive Session-/Lane-Modell. Hartcodiere sie nur, wenn ein Task *zwingend* auf einem bestimmten Modell laufen muss — die Single Source of Truth fürs Routing ist `skill_lanes`, nicht dieses Beispiel. **Live-Realität (2026-07-21):** Session-Default/Königin = **MiniMax-M3**; das bevorzugte Planer-Modell ist **GLM-5.2**, das per `plan-glm`-Subprozess geroutet wird (nicht durch ein `model:`-Feld hier). Siehe LANE-TRUTH / `plan-glm`.
- `slug` — lower-kebab-case identifier. Used as the idempotency-key prefix when the plan is approved and seeded to Kanban; re-approval reuses task IDs while refreshing the stored plan attachment.
- `scope_tiers` — explicit A/B/C categorisation. Parsers seed higher tiers first.
- `risks` — bullet list rendered in the root task body by H-22.
- `verification` — bullet list of runnable commands rendered in the root task body.

### Required machine-readable task block

After the frontmatter and the human-readable sections, add a single fenced block:

````markdown
```tasks
- [ ] T1: H-04 Secrets-Migration | skill: hermes-v2-helper | paths: [.env] | verify: bash -n .env
- [ ] T2: H-05 state.db-Diät | skill: hermes-v2-helper | paths: [state.db] | verify: sqlite3 .backup /tmp/x.db && du -sh state.db
- [ ] T3: H-10 MiniMax-Interleaved-Thinking | skill: hermes-core-patch | paths: [run_agent/, tests/run_agent/test_minimax_tool_reasoning.py] | verify: ./scripts/run_tests.sh tests/run_agent/test_minimax_tool_reasoning.py
```
````

Line format: `- [ ] T<n>: <Title> | skill: <skill-slug> | paths: [<path>, ...] | verify: <command>`

- `T<n>` — stable task ID within the plan. Used for parent/child linking.
- `skill:` — comma-separated list of skill slugs to force-load when the worker picks up this task.
- `paths:` — canonical file-scope field; use a comma-separated value or bracketed list. The parser also accepts legacy `path:` and `files:` aliases, but new plans must emit `paths:`.
- `verify:` — shell command the worker must run before completing. H-22 stores it on the task and surfaces it in webui.

Children use `parent:` and `depends:` fields:

````markdown
```tasks
- [ ] T1: Phase 1 setup | skill: hermes-v2-helper | paths: [run_agent/, tests/run_agent/]
- [ ] T1.1: Apply H-10 patch | parent: T1 | skill: hermes-core-patch | paths: [run_agent/, tests/run_agent/test_minimax_tool_reasoning.py] | verify: ./scripts/run_tests.sh tests/run_agent/test_minimax_tool_reasoning.py
- [ ] T1.2: Apply H-11 patch | parent: T1 | depends: [T1.1] | skill: hermes-core-patch | paths: [run_agent/, tests/run_agent/test_thinking_budget_ultra.py] | verify: ./scripts/run_tests.sh tests/run_agent/test_thinking_budget_ultra.py
```
````

### Parser guarantees (contract for H-22)

A plan is **approvable** iff:
1. Frontmatter parses as YAML and contains all required keys.
2. At least one `- [ ]` line exists inside a single `` ```tasks `` fenced block.
3. Every `T<n>` ID is unique within the plan.
4. Every `verify:` value is a non-empty shell line.
5. The plan file lives under `.hermes/plans/` (resolved against the active workspace).

Free-form plans without frontmatter remain usable for human execution. Seeding creates one triage task instead of a structured tree; callers may explicitly request auxiliary decomposition.

### Worked example (hermes-v2 plan, abridged)

```markdown
---
slug: starman-booster-gold-red-star
title: Hermes v2 Verbesserungsplan
goal: Hermes/Yuno auf Claude Code / Kimi Code Workflow-Niveau heben.
scope_tiers:
  A: [H-01, H-10, H-11, H-22]
  B: [H-12, H-13, H-20, H-50]
  C: [H-08, H-15, H-64]
risks:
  - Core-Patches kollidieren mit Upstream → git revert
  - state.db-VACUUM braucht 2× Disk → Freien Platz prüfen
verification:
  - ./scripts/run_tests.sh tests/run_agent/ -k 'minimax or thinking_budget' grün
created_by: yuno
created_at: 2026-07-20
model: MiniMax-M3
provider: minimax
---

# Hermes v2 Verbesserungsplan

> Plan-file: this very document. Goals, risks, and verification above.
> Phase ordering and rationale in §Phases below.

## Phases

[free-form prose — phases 0..6 with H-task summaries]

## Tasks

```tasks
- [ ] T1: Phase 0 — Hygiene | parent: root | skill: hermes-v2-helper
- [ ] T1.1: H-01 Baseline-Snapshot | parent: T1 | skill: hermes-v2-helper | verify: ls ~/hermes-v2-baseline-*
- [ ] T1.2: H-04 Secrets-Migration | parent: T1 | depends: [T1.1] | skill: hermes-v2-helper | verify: grep -c DASHBOARD ~/.hermes/.env
- [ ] T2: Phase 1 — Tool-Calling + M3-Tuning | parent: root | skill: hermes-core-patch
- [ ] T2.1: H-10 MiniMax-Interleaved-Thinking | parent: T2 | skill: hermes-core-patch | verify: ./scripts/run_tests.sh tests/run_agent/test_minimax_tool_reasoning.py
- [ ] T2.2: H-11 ultra in THINKING_BUDGET | parent: T2 | depends: [T2.1] | skill: hermes-core-patch | verify: ./scripts/run_tests.sh tests/run_agent/test_thinking_budget_ultra.py
```
```

## Save location

Save the plan with `write_file` under:
- `.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md`

Treat that as relative to the active working directory / backend workspace. Hermes file tools are backend-aware, so using this relative path keeps the plan with the workspace on local, docker, ssh, modal, and daytona backends.

**Pitfall: verify the exact `.hermes/` spelling.** The directory is `.hermes/plans/`, not `.herme/plans/`. After `write_file`, immediately check the tool result's `resolved_path`. If it does not start with `.hermes/plans/`, write the plan again to the correct path with `write_file`; do not continue with a typo-path plan.

If the runtime provides a specific target path, use that exact path.
If not, create a sensible timestamped filename yourself under `.hermes/plans/`.

## Interaction style

- If the request is clear enough, write the plan directly.
- If no explicit instruction accompanies `/plan`, infer the task from the current conversation context.
- If it is genuinely underspecified, ask a brief clarifying question instead of guessing.
- After saving the plan, reply briefly with what you planned and the saved path.

## Trivial-task bypass (hermes-v2, H-23)

Plan mode is **opt-out for trivial work**. The default activation
rule is:

> **If a request is unambiguously trivial, skip `/plan` entirely and
> just do the work.**

A task is unambiguously trivial when ALL of these hold:

- One file edit, OR one shell command, OR one read+reply.
- No multi-step coordination (no subagents, no kanban, no
  pipelines).
- No design tradeoffs that benefit from being written down.
- Output fits in one short message.

Examples of trivial tasks (skip plan mode):

- "What's the exit code of grep when no match?" → read + reply.
- "Add a docstring to this function." → one file edit.
- "Restart the gateway service." → one shell command.
- "Convert this JSON to YAML." → one file edit.

Examples that MUST use plan mode (do not bypass):

- "Refactor the auth flow." → multi-file, design tradeoffs.
- "Add a new pipeline for X." → multi-step coordination.
- "Investigate why Y is slow." → requires discovery + plan.
- "Implement feature Z end-to-end." → multi-file, multi-step.

When auto-activation is enabled (via
`config.auto_activation.enabled` in `plugin.yaml`), the
heuristic-trigger classifier in `hermes_auto_detect.py` already
skips low-confidence cases. The trivial-task bypass here is the
explicit operator rule for manual `/plan` calls: when in doubt,
**err on the side of doing the work directly** for single-step
tasks rather than writing a plan file the work doesn't need.

The plan-mode write-fence (`hermes_plan_mode.py:policy_hook`) is
still active when plan mode IS on — no need to relax it for trivial
work, because plan mode isn't activated for trivial work in the
first place.

## Auto-activation tuning (hermes-v2, H-23)

When auto-activation is on, the `confidence_threshold` controls how
often the heuristic promotes ambiguous requests to plan mode.
Defaults from `plugin.yaml`:

```yaml
auto_activation:
  enabled: false                  # opt-in only; flip to true after testing
  confidence_threshold: 0.25     # lower = more eager activation
  plan_mode: true                 # which modes auto-activation can flip
  swarm_mode: true
```

After the 1-week soak period (per the hermes-v2 plan, Phase 2), tune:

- **Raise threshold to 0.4** if too many trivial requests are getting
  plan mode and forcing plan-write turns.
- **Lower threshold to 0.15** if multi-step requests are slipping
  through and ending up as inline TODOs without structure.
- **Disable entirely** (`enabled: false`) if the false-positive rate
  outweighs the false-negative cost.

The threshold tunes the **classifier's eagerness**; the trivial-task
bypass above tunes the **operator's manual-call behavior**. Both
levers exist because they target different decisions.

---

# Writing the Plan Well

The rest of this skill is the craft of authoring a *good* implementation plan — the content that goes inside the markdown file above.

## Overview

Write comprehensive implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume the implementer is a skilled developer but knows almost nothing about the toolset or problem domain. Assume they don't know good test design very well.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## When a Full Implementation Plan Helps

**Always use before:**
- Implementing multi-step features
- Breaking down complex requirements
- Delegating to subagents via subagent-driven-development

**Don't skip when:**
- Feature seems simple (assumptions cause bugs)
- You plan to implement it yourself (future you needs guidance)
- Working alone (documentation matters)

## Bite-Sized Task Granularity

**Each task = 2-5 minutes of focused work.**

Every step is one action:
- "Write the failing test" — step
- "Run it to make sure it fails" — step
- "Implement the minimal code to make the test pass" — step
- "Run the tests and make sure they pass" — step
- "Commit" — step

**Too big:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Right size:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Plan Document Structure

### Header (Required)

Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

### Task Structure

Each task follows this format:

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `./scripts/run_tests.sh tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `./scripts/run_tests.sh tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```

````

## Writing Process

### Step 1: Understand Requirements

Read and understand:
- Feature requirements
- Design documents or user description
- Acceptance criteria
- Constraints

### Step 2: Explore the Codebase

Use Hermes tools to understand the project:

```python
# Understand project structure
search_files("*.py", target="files", path="src/")

# Look at similar features
search_files("similar_pattern", path="src/", file_glob="*.py")

# Check existing tests
search_files("*.py", target="files", path="tests/")

# Read key files
read_file("src/app.py")
```

### Step 3: Design Approach

Decide:
- Architecture pattern
- File organization
- Dependencies needed
- Testing strategy

### Step 4: Write Tasks

Create tasks in order:
1. Setup/infrastructure
2. Core functionality (TDD for each)
3. Edge cases
4. Integration
5. Cleanup/documentation

### Step 5: Add Complete Details

For each task, include:
- **Exact file paths** (not "the config file" but `src/config/settings.py`)
- **Complete code examples** (not "add validation" but the actual code)
- **Exact commands** with expected output
- **Verification steps** that prove the task works

### Step 6: Review the Plan

Check:
- [ ] Tasks are sequential and logical
- [ ] Each task is bite-sized (2-5 min)
- [ ] File paths are exact
- [ ] Code examples are complete (copy-pasteable)
- [ ] Commands are exact with expected output
- [ ] No missing context
- [ ] DRY, YAGNI, TDD principles applied

## Principles

### DRY (Don't Repeat Yourself)

**Bad:** Copy-paste validation in 3 places
**Good:** Extract validation function, use everywhere

### YAGNI (You Aren't Gonna Need It)

**Bad:** Add "flexibility" for future requirements
**Good:** Implement only what's needed now

```python
# Bad — YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # Not needed yet!
        self.metadata = {}     # Not needed yet!

# Good — YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

### TDD (Test-Driven Development)

Every task that produces code should include the full TDD cycle:
1. Write failing test
2. Run to verify failure
3. Write minimal code
4. Run to verify pass

See `test-driven-development` skill for details.

### Frequent Commits

Commit after every task:
```bash
git add [files]
git commit -m "type: description"
```

## Common Mistakes

### Vague Tasks

**Bad:** "Add authentication"
**Good:** "Create User model with email and password_hash fields"

### Incomplete Code

**Bad:** "Step 1: Add validation function"
**Good:** "Step 1: Add validation function" followed by the complete function code

### Missing Verification

**Bad:** "Step 3: Test it works"
**Good:** "Step 3: Run `./scripts/run_tests.sh tests/test_auth.py -v`, expected: 3 passed"

### Missing File Paths

**Bad:** "Create the model file"
**Good:** "Create: `src/models/user.py`"

## Execution Handoff

After saving the plan, offer the execution approach:

**"Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?"**

When executing, use the `subagent-driven-development` skill:
- Fresh `delegate_task` per task with full context
- Spec compliance review after each task
- Code quality review after spec passes
- Proceed only when both reviews approve

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**A good plan makes implementation obvious.**
