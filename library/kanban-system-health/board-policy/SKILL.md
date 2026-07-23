---
name: board-policy
description: "Use when user asks for declarative per-board Kanban policy, policy schema, board policy audit. NOT for board health (use kanban-system-health) or worker pitfalls. Define and audit declarative per-board Kanban policy."
version: 1.0.0
author: Hermes Agent (hermes-v2 plan, H-32, 2026-07-20)
license: MIT
platforms:
  - linux
  - macos
metadata:
  hermes:
    tags: ['kanban', 'board', 'policy', 'governance', 'hermes-v2']
    related_skills:
      - kanban-system-health
      - coding-pipeline-orchestrator
      - todo-kanban-promotion
lane: koenigin
reasoning_effort: xhigh
agent: Orchestrator
routing_hint: |
  **Agent-Scope:** Per-board policy configuration. Off-scope: task-level settings, global config.
trigger_keywords: ['board', 'policy', 'kanban', 'declarative', 'audit']
keywords: ['board', 'policy', 'kanban', 'declarative', 'audit']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['kanban-worker', 'kanban-system-health', 'task-weight-routing']
---

---

# Board Policy (hermes-v2, H-32)

Convention for per-board policy. Each Kanban board lives at
`~/.hermes/kanban/boards/<slug>/` and may carry an optional
`BOARD.md` describing its defaults. This file is the
operator-facing source of truth for board-level settings that the
global `~/.hermes/config.yaml` doesn't cover (claim TTL, retry
budget, judge-loop wiring, failure-limit review policy).

A separate **pre-existing** `BOARD.md` markdown-tasklist format
exists in the codebase (used for V7-era manual boards). This skill
defines a **new YAML-frontmatter policy schema** that lives next to
(or replaces) the legacy file when a board is upgraded to v2
policy tracking. The two formats can coexist on different boards.

## When to Use

Use this convention when:

- **Creating a new kanban board** — write a fresh `BOARD.md` with
  defaults that match the board's purpose (coding, ops, research).
- **Auditing intended board policy** — read `BOARD.md` to understand the
  declared `max_retries`, `goal_mode`, and other operator defaults.
- **Debugging a board-level anomaly** — compare actual config
  against the declared policy.

Do NOT use this convention for:
- Task-level settings (use supported `hermes kanban create --help` flags).
- Global defaults (those live in `~/.hermes/config.yaml`).
- Cross-board coordination; this schema governs one board only.

## Quick Start

1. Place a `BOARD.md` in `~/.hermes/kanban/boards/<slug>/`.
2. Copy the schema below, replace `<slug>`, and review every default.
3. Treat the policy as documentation. Hermes does not currently load or
   apply this file automatically.
4. Pass supported policy values explicitly when creating a task, for example:

```bash
hermes kanban --board <slug> create "<title>" \
  --max-retries 2 --initial-status blocked
```

The global `--board` option must precede the `create` subcommand.

## Procedure

### Define the schema

```markdown
---
# [hermes-v2] BOARD.md policy schema (v1.0)
board: <slug>                  # required: matches directory name
schema_version: 1               # required: bump on breaking changes
defaults:
  max_retries: 2                # intended task-level retry budget
  initial_status: blocked       # blocked | running (we recommend blocked)
  priority: 5                   # A=10, B=5, C=1, default 0
  goal_mode: false              # intended goal-mode setting
judge_loop:
  enabled: false                # declares intended coding-pipeline review
  workflow_template_id: coding-pipeline  # see coding-pipeline-orchestrator
  human_gates_after: 2          # intended re-review escalation threshold
claim:
  ttl_seconds: 14400            # 4h default
  heartbeat_seconds: 600        # 10m
  stale_timeout_seconds: 14400  # 4h
failure:
  failure_limit: 2              # intended consecutive-failure limit
  review_on_trip: true          # declares whether trips require review
notifications:
  on_create: false
  on_complete: true
  on_failure: true
description: |
  Free-text description of the board's purpose. Optional but recommended.
tags: [coding, hermes-v2]       # optional tags for board discovery
created_by: basti
created_at: 2026-07-20
---

# Optional: prose

Any free-text below the frontmatter is human documentation.
```

The frontmatter fields are the **declarative contract** for operators; Hermes
currently does not parse them. The prose section is for human eyes only.

### Declared fallback values

These are convention defaults for manual interpretation when a field is
omitted. They do not become runtime configuration automatically.

| Field | Default |
|---|---|
| `defaults.max_retries` | 2 |
| `defaults.initial_status` | `blocked` |
| `defaults.priority` | 0 |
| `defaults.goal_mode` | false |
| `judge_loop.enabled` | false |
| `judge_loop.workflow_template_id` | (unset) |
| `judge_loop.human_gates_after` | 3 |
| `claim.ttl_seconds` | 14400 (4h) |
| `claim.heartbeat_seconds` | 600 (10m) |
| `claim.stale_timeout_seconds` | 14400 (4h) |
| `failure.failure_limit` | 2 |
| `failure.review_on_trip` | true |
| `notifications.on_create` | false |
| `notifications.on_complete` | true |
| `notifications.on_failure` | true |

### Resolve values

When an operator resolves a value to pass explicitly for a task:

1. **Task-level overrides** (for example, `--max-retries 5` on
   `hermes kanban create`) are the actual effective values.
2. **Board policy** (`BOARD.md` frontmatter in
   `~/.hermes/kanban/boards/<slug>/BOARD.md`) supplies operator guidance.
3. **Global config** (`~/.hermes/config.yaml`) provides the runtime fallback.
4. **Hardcoded defaults** are the last-resort runtime floor.

This is the intended manual cascade. The runtime does not insert the board
policy layer unless an operator transfers its values to supported task flags
or configuration.

### Apply supported values manually

**v1 status:** the `BOARD.md` frontmatter is **declarative only**. Operators
must transfer supported values when creating tasks: `max_retries` maps to
`--max-retries`, `priority` to `--priority`, `goal_mode: true` to `--goal`,
and `initial_status` maps only to the real CLI choices
`--initial-status blocked` or `--initial-status running`.

Future work may add policy parsing or linting. Until then, the file's value is:
- Operator documentation (what policy a board is intended to follow).
- Audit trail (when the declared policy changed).
- Migration path to future automatic application.

### Worked example: hermes-v2 board

```markdown
---
board: hermes-v2
schema_version: 1
defaults:
  max_retries: 2
  initial_status: blocked
  priority: 5
  goal_mode: false
judge_loop:
  enabled: true
  workflow_template_id: coding-pipeline
  human_gates_after: 2
claim:
  ttl_seconds: 14400
  heartbeat_seconds: 600
  stale_timeout_seconds: 14400
failure:
  failure_limit: 2
  review_on_trip: true
notifications:
  on_create: false
  on_complete: true
  on_failure: true
description: |
  The hermes-v2 plan board. Holds the 39 H-tasks driving the
  consolidation work. blocked + unassigned records the safe
  task-creation practice until Basti explicitly promotes. judge_loop
  records the intended review chain; BOARD.md does not route it.
tags: [hermes-v2, planning, code-review-pipeline]
created_by: basti
created_at: 2026-07-20
---
```

### Worked example: ops board

```markdown
---
board: system
schema_version: 1
defaults:
  max_retries: 5            # ops tasks may need more retries (rate limits)
  initial_status: blocked
  priority: 1
judge_loop:
  enabled: false            # declares that ops tasks skip review
notifications:
  on_failure: true
description: |
  System maintenance board. Holds cron-debug, auth-fix, log-rotate
  tasks. Higher retry budget because ops frequently hits transient
  failures (network, rate limits, missing temp files).
tags: [ops, maintenance]
created_by: basti
created_at: 2026-07-20
---
```

## Verification and Acceptance

A `BOARD.md` is "correct" iff:
1. It has a YAML frontmatter block delimited by `---`.
2. `board`, `schema_version`, and the `defaults` map are all present.
3. All field values are valid against the schema above (no negative
   TTLs, etc.).
4. The board slug matches the directory it's stored in.
5. The file is at `~/.hermes/kanban/boards/<slug>/BOARD.md`.
6. Operators can map every value they intend to apply now to a supported
   task flag or an existing runtime configuration setting.

Verification is currently manual. Treat the file as documentation with
forward-compatibility constraints, not as proof of applied runtime state.

## Anti-Patterns

| Anti-pattern | Why it's rejected |
|---|---|
| Putting tasks in `BOARD.md` instead of `hermes kanban create` | The board file is policy, not work; mixing them loses both signals |
| Setting `initial_status: ready` | `ready` is not a real `hermes kanban create --initial-status` choice; use `blocked` or `running` intentionally |
| Omitting `schema_version` | Future readers can't tell if they're looking at v1 or a newer format |
| Storing secrets in frontmatter | BOARD.md is in `~/.hermes/`; secrets belong in `~/.hermes/.env` or `~/.config/<service>.env` (see H-04) |
| Assuming BOARD.md is applied automatically | Hermes does not currently parse this policy file |
| Using BOARD.md as the single source of truth instead of layering with config | Loses the operator's ability to override per-task; reduces flexibility |

## Failure Recovery / Troubleshooting

- **Declared defaults have no effect:** this is expected in v1. Transfer
  supported values explicitly with the command pattern in Quick Start.
- **A task flag is rejected:** check `hermes kanban create --help`; schema
  fields without a supported flag remain operator guidance only.
- **`initial_status` is rejected:** the real `create` choices are only
  `blocked` and `running`; `ready` is not accepted.
- **Diagnostics do not flag an invalid `BOARD.md`:**
  `hermes kanban --board <slug> diagnostics` reports runtime diagnostics and
  does not lint this policy file.

## Verdict

`BOARD.md` is an operator-authored, declarative policy contract. It does not
change Hermes runtime state; supported values take effect only when an operator
passes them through real task flags or existing runtime configuration.

## Related Skills and References

- `kanban-system-health` — system-level board health and diagnostics.
- `coding-pipeline-orchestrator` — intended review workflow named by
  `judge_loop.workflow_template_id`.
- `todo-kanban-promotion` — durable promotion into Kanban tasks.
- CLI references: `hermes kanban --help` and
  `hermes kanban create --help`.
