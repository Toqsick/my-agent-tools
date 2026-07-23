---
name: todo-kanban-promotion
description: >-
  Use when user asks for promoting durable session todos to Kanban, preserving work that must survive a chat session, assigning ownership and dependencies to deferred tasks, or moving follow-up work into a persistent queue. NOT for short-lived conversational checklists or executing an existing Kanban task. Provides a promotion threshold and worker convention so only durable, actionable, scoped work becomes persistent board state.
version: 1.0.0
author: Hermes Agent (hermes-v2 plan, H-24, 2026-07-20)
license: MIT
platforms:
  - linux
  - macos
  - windows
metadata:
  hermes:
    tags: ['todo', 'kanban', 'promotion', 'session-handoff', 'hermes-v2']
    related_skills:
      - kanban-system-health
      - writing-plans
      - plan
      - coding-pipeline-orchestrator
lane: koenigin
reasoning_effort: xhigh
agent: Orchestrator
routing_hint: |
  **Agent-Scope:** Promoting session-todos to Kanban tasks. Off-scope: in-session todo management, plan authoring.
trigger_keywords: ['work', 'durable', 'session', 'kanban', 'persistent']
keywords: ['work', 'durable', 'session', 'kanban', 'persistent']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['hermes-memory', 'daily-briefing', 'session-handoff']
---

---

# todo → Kanban Promotion (hermes-v2)

Convention for the moment when a session's todo list outlives the
session — the worker crashed, the context overflowed, the operator
closed the session mid-task, or the worker simply hit a hard
checkpoint and stopped. In all these cases, the todos are
**durable intent** that should not be lost.

The convention: at the end of every turn that ends with non-empty
todos, the worker evaluates whether any TODO should be promoted to a
Kanban task on the active board.

## When to Use

Promote a session todo to a Kanban task when **any** of the
following is true:

1. **The worker is about to exit.** Closing the session without
   promotion loses the todo. Always check the native `todo` tool at
   session close.
2. **The worker hit a hard checkpoint** (rate-limit, model failure,
   context overflow). Resume may be hours away.
3. **The TODO has a clear single-owner** (a known profile or lane).
   Todos that are pure context notes (e.g. "remember to update the
   plan file later") stay as todos; only actionable work gets
   promoted.
4. **The TODO has a verify command** (per `step-execution`, H-52).
   A TODO without a verify is too vague to track as a Kanban task
   — keep refining first.

If none of the above hold, leave the todo as a session-internal
reminder. In-session todo management and pure planning are out of
scope; use the native `todo` tool or `writing-plans` respectively.

## Quick Start

Read the title, body, owner, and verify command from the session's
native `todo` tool, then create the durable task on the active board:

```bash
hermes kanban create "<todo title>" \
    --body "<todo body and verify command>" \
    --assignee <owner-profile> \
    --priority 5 \
    --idempotency-key "todo-<todo_id>-<session_id>"
```

`todo` is a native session tool, not a `hermes` CLI subcommand. After
creation succeeds, record the returned Kanban id in the session and
resolve the source item through `todo`; do not invoke `hermes todo`.

For an explicit board, the global option must precede the subcommand:

```bash
hermes kanban --board <board-slug> create "<todo title>" \
    --body "<todo body and verify command>" \
    --assignee <owner-profile> \
    --priority 5 \
    --idempotency-key "todo-<todo_id>-<session_id>"
```

## Promotion Workflow

For each TODO that meets the rule:

1. Inspect the current session state through the native `todo` tool.
2. Preserve the original title and body verbatim, including its
   verify command.
3. Read the todo's `owner:` field, then fall back to the lane that
   produced it (`worker-heavy` for code TODOs, `gate` for review
   TODOs, etc.).
4. Run the `hermes kanban create` command from Quick Start and capture
   the returned task id. The session-qualified idempotency key makes a
   crash retry return the existing task instead of creating a duplicate.
5. Record that Kanban id in the session context, then resolve the
   source item with the native `todo` tool.
6. If there is parent context, link the new task:

   ```bash
   hermes kanban link <parent_kanban_id> <new_kanban_id>
   ```

### Worker-side convention

This is a worker/orchestrator convention rather than a shell hook. At
each relevant session boundary, inspect active todos, apply the
promotion rule, create each durable task, and only then resolve its
session todo. Owner inference follows the todo's `owner:` field and
then its producing lane.

### Why this matters

Without promotion:
- A worker crash mid-task loses the todo list silently.
- The operator doesn't see actionable TODOs on the kanban board.
- Session state is the only place the intent lives.

With promotion:
- The kanban board is the single source of truth for "what's next".
- The next worker session picks up where the crashed one stopped.
- Operators can review remaining work via `hermes kanban list
  --assignee <lane>` even without a live session.

## Verification / Acceptance

A promotion is correct only if:
1. The promoted task contains the original todo's body verbatim and
   its verify command.
2. The promoted task has an explicit `assignee`.
3. The returned Kanban id is recorded in the session before the
   original todo is resolved through the native `todo` tool.
4. `hermes kanban list --assignee <owner>` shows the new task.

## Anti-Patterns

| Anti-pattern | Why it's rejected |
|---|---|
| Promoting every todo unconditionally | Bloats the kanban board; loses the "is this worth tracking" filter |
| Promoting without an assignee | Re-creates the H-00 dispatcher risk; tasks sit unowned |
| Promoting with empty body | Loses context; the kanban task is meaningless without the original detail |
| Using the todo id as the idempotency key | TODO ids are session-scoped; two sessions could collide |
| Re-promoting after success | Without idempotency, creates duplicates; with it, no-op |
| Calling `hermes todo show` or `hermes todo complete` | `todo` is a native session tool, not a Hermes CLI command |

## Failure Recovery / Troubleshooting

If `kanban create` fails (for example, because no board is selected),
the todo stays as-is; it does not silently disappear. Log the failure
and leave the todo open so the next session boundary can retry with the
same idempotency key. To select a board explicitly, use the complete
explicit-board command shown in Quick Start. Only resolve the session
todo after creation returns a Kanban id.

## Related Skills / References

- **`coding-pipeline-orchestrator`** (H-31): when a worker in the
  pipeline exits with TODOs, the convention kicks in and they
  become root-level kanban tasks (or children of the relevant
  pipeline step).
- **`writing-plans`** (H-20): if the work is larger than a single
  Kanban task, prefer promoting to a plan (then `/plan approve`)
  rather than individual todos.
- **`step-execution`** (H-52): promoted TODOs from a worker should
  carry the verify-command from the original todo as their
  `verify:` segment.
