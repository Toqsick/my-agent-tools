---
name: swarm-workspace-isolation
description: >-
  Use when user asks for isolating filesystem state for parallel workers, preventing workers from overwriting shared files, creating per-worker scratch and output directories, or making re-queued work reproducible. NOT for single-worker tasks or coding tasks already isolated by dedicated worktrees. Defines read-only inputs, per-worker scratch space, artifact contracts, cross-worker sharing rules, cleanup, and acceptance checks.
version: 1.0.0
author: Hermes Agent (hermes-v2 plan, H-43, 2026-07-20)
license: MIT
platforms:
  - linux
  - macos
metadata:
  hermes:
    tags: ['swarm', 'workspace', 'isolation', 'orchestration', 'hermes-v2']
    related_skills:
      - swarm-router
      - coding-pipeline-orchestrator
      - queen-bee-schwarm-dispatch
      - multi-agent-work
      - worker-failure-discipline
      - kanban-system-health
lane: koenigin
reasoning_effort: xhigh
agent: Orchestrator
routing_hint: |
  **Agent-Scope:** Per-worker workspace conventions. Off-scope: single-worker tasks, worktrees (H-31 has its own).
trigger_keywords: ['worker', 'workers', 'scratch', 'tasks', 'user']
keywords: ['worker', 'workers', 'scratch', 'tasks', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

---

# Swarm Workspace Isolation (hermes-v2, H-43)

When N workers run in parallel — kanban swarm, parallel-reads,
MoA-consensus — they each need **independent filesystem state**.
Without isolation, worker A overwrites worker B's output, two
workers race on the same cache file, or one worker's `pip install`
pollutes another's import path.

This skill defines the conventions for workspace layout, input
guards, and cleanup.

## When to Use

Use this skill when:

- Dispatching N workers that need **independent filesystem state**
  (kanban swarm, parallel-reads, MoA-consensus).
- Two or more workers in the same run could otherwise stomp on each
  other's outputs, caches, scratch files, or `pip install` paths.
- You need an explicit workspace contract so a re-queued worker
  re-creates the same layout from the input MD5 reference.

Off-scope:

- **Single-worker tasks** — no isolation needed; run inline.
- **Plan mode** — the read-fence already isolates the working set.
- **Coding-pipeline worktrees (H-31)** — the `wt/<task-id>` branch
  *is* the workspace; there is no separate `output/` layout.

## Quick Start

> **Scope:** worker / orchestrator **convention**, not Hermes
> bootstrap. The lifecycle assigns the workspace path and
> creates the workspace directory; subdirectory layout, MD5
> guards, chmod, and `result.json` semantics are responsibilities
> the worker / orchestrator implements. Do not expect the
> dispatcher to mkdir `input/output/cache/logs` for you.

1. Workers are dispatched via
   `hermes kanban claim <task_id>` (or via `hermes kanban --board <slug>
   claim <task_id>` to pin a board). The `claim` command prints the
   resolved workspace path
   (`<board_root>/workspaces/<task_id>/` for scratch, or the
   worktree / dir path the task was created with).
2. The **worker** materialises `input/`, `output/`, `cache/`, `logs/`
   under that workspace; the orchestrator writes any input MD5 guards
   before dispatch. The lifecycle does not create these subdirs.
3. The worker `cd`s into the workspace, verifies every MD5-guarded
   input, and writes all artifacts (transient + final) there.
4. On completion, the worker reports via
   `hermes kanban complete <task_id> --result <text> --summary <text>`
   (no `--cleanup` flag exists on `complete`; cleanup of stale
   scratch workspaces is handled by `_cleanup_workspace` on
   `complete_task` — see Cleanup policy).
5. The orchestrator / verifier reads `output/result.json` to decide
   success/failure (H-42 worker-failure-discipline).

## Workspace layout

```
<board_root>/workspaces/<task_id>/
├── input/          # shared inputs (read-only for the worker)
│   └── critical.md # MD5-guarded shared files
├── output/         # the worker's deliverables
├── cache/          # scratch space (pip caches, downloaded data)
└── logs/           # per-worker stdout/stderr
```

Where:
- `<board_root>` is `~/.hermes/kanban/boards/<slug>/` (set per-board).
- `<task_id>` is the kanban task id (e.g. `t_a621a924`). One
  workspace per task — even if the task spawns multiple internal
  sub-tasks, they all live under the same parent workspace.

For `workspace_kind=scratch`, the workspace directory is materialised
by the lifecycle at claim time under `workspaces_root(slug) /
task_id`. For `workspace_kind=worktree` and `workspace_kind=dir`,
the path the task was created with is reused — there is no separate
`input/output/cache/logs` layout (the worktree or dir IS the workspace;
see `coding-pipeline-orchestrator` H-31).

The lifecycle creates the **root** directory only; `input/`, `output/`,
`cache/`, `logs/` are worker-managed subdirectories.

## Read-only input mount (worker / orchestrator convention)

Files that all workers need access to (a spec, a dataset, a config
template) live in `input/`. Workers treat them as **read-only** by
convention — the worker (or orchestrator during briefing) is
expected to `chmod -R a-w input/` once the input set is final.
The lifecycle does NOT chmod for you. If a worker needs to mutate
an input, it must copy the file into its own `output/` first.

The MD5 guard is a worker-side discipline; the lifecycle does not
generate it:

```bash
# Orchestrator / queen runs this before spawning workers:
md5sum input/critical.md > input/critical.md.md5

# Each worker, before reading, verifies:
md5sum -c input/critical.md.md5
```

If the check fails, the worker aborts with a clear error rather
than silently using stale or corrupted input. The MD5 file is
generated once at workspace-materialisation time and never changes
during the run.

## Per-worker scratch

Workers MUST write all transient artifacts (intermediate
computations, downloaded blobs, temp files) to `cache/`, not to
`/tmp` or to the project tree. Reasons:

- `/tmp` is shared across workers; collisions are silent.
- The project tree is the worker's deliverable target, not scratch.
- `cache/` is cleaned up at task completion (see below).

## Output contract

Workers write their final deliverables to `output/`. The shape:

```
output/
├── result.json     # machine-parseable: {"status": "ok"|"failed", "summary": "...", "artifacts": [...]}
├── artifacts/      # files the worker produced (code, docs, data)
└── log.txt         # last 4 KB of stdout/stderr
```

The Queen / orchestrator reads `output/result.json` to decide
success/failure (H-42 worker-failure-discipline). If `result.json`
is missing or malformed, the worker is treated as **failed** —
never as "nothing to do" (the H-42 trap).

## Cleanup policy

Retention depends on `workspace_kind`:

- **`scratch` workspaces are ephemeral.** The lifecycle calls
  `_cleanup_workspace(conn, task_id)` from `complete_task` after the
  DB transaction commits. Only `workspace_kind='scratch'` dirs are
  removed; the path is verified against
  `_managed_scratch_path_info` so a misconfigured scratch dir cannot
  ever wipe a user-controlled directory. **`worktree` and `dir`
  workspaces are intentionally preserved** — `_cleanup_workspace`
  short-circuits when `kind != 'scratch'`. There is **no
  `--cleanup` flag** on `hermes kanban complete`; that flag does
  not exist on the real CLI.
- **`hermes kanban archive <task_id>`** archives the **task rows**
  (status flips to `archived`); it does NOT move the workspace
  directory anywhere. Pass `--rm <task_id>` to permanently delete
  the (already-archived) task records, but the workspace on disk
  is not touched by either path. Use it for task-level bookkeeping,
  not for workspace removal.
- **`hermes kanban gc`** is **not** a workspace retention
  mechanism. Its flags prune:
  - `--event-retention-days` (default 30) — older `task_events`
    rows for terminal tasks.
  - `--log-retention-days` (default 30) — older worker log files
    under `<kanban-root>/kanban/logs/`.

  So if you want a workspace preserved indefinitely for audit,
  create the task with `--workspace worktree:...` or
  `--workspace dir:/abs/path` instead of `scratch`.

## Cross-worker file sharing

Sometimes two workers in a swarm need to share intermediate state
(e.g. worker A produces data worker B consumes). Patterns:

1. **Blackboard via kanban comments** — Worker A posts a comment
   with the data inline; worker B reads via
   `hermes kanban show <task_id>`. (`show` displays comments by
   default; there is no `--comments` flag to add.) This is the
   default — keeps state in the durable record.
2. **Shared `output/` mount** — Anti-pattern: workers race on
   the same file. Use only when (a) data is read-only after
   producer finishes, (b) workers have a clear phase ordering.
3. **External artifact store** (S3, blob store) — For
   >100 MB outputs. Out of scope for v1.

## Worker-side startup

The **worker itself** owns the following steps at startup; the
dispatcher does not perform them:

1. `cd` into the workspace.
2. Verify input MD5.
3. Set `cwd` to the workspace for all subsequent tool calls.
4. Bind log file to `logs/worker.log`.
5. Write `result.json` on completion (success OR failure).

If step 1-5 fails for any reason, the worker is treated as failed
and the task is re-queued (per H-42 discipline).

## Interaction with coding-pipeline-orchestrator (H-31)

When the pipeline runs in kanban-swarm mode, each pipeline step
uses this isolation scheme. The pipeline-spawn script
(`scripts/spawn_pipeline.py`) creates the root task workspace;
child-task workspaces are auto-created by `kanban create`.

When the pipeline uses worktrees (H-31's `wt/<task-id>` branches),
the worktree IS the workspace — there is no separate
`output/` layout. Workers in a worktree-mode pipeline commit
directly to the branch; the dispatcher reads commits to confirm
progress.

## Verification / Acceptance

A workspace is "correct" iff:

1. For `workspace_kind=scratch`, the directory exists at
   `<board_root>/workspaces/<task_id>/`. For `worktree`/`dir`, the
   path the task was created with is reused.
2. `input/` is read-only (worker `chmod a-w` after input finalisation).
3. MD5 guards exist for any file the worker needs to read
   consistently.
4. Worker writes `output/result.json` regardless of outcome.
5. `scratch` workspaces are removed by `_cleanup_workspace` on
   `complete_task`; `worktree`/`dir` workspaces are preserved across
   re-spawns by design.
6. Completion is reported via
   `hermes kanban complete <task_id> --result <text> --summary <text>`
   (no `--cleanup` flag on `complete`; that flag does not exist).
7. `hermes kanban show <task_id>` prints comments by default
   (no `--comments` flag; do not invent one).
8. `hermes kanban archive <task_id>` does not touch the workspace
   directory; `hermes kanban gc` is event/log retention, not
   workspace retention.

## Anti-patterns

| Anti-pattern | Why it's rejected |
|---|---|
| Writing to `/tmp/<task_id>/` | Collision risk; cleanup-orphans |
| Sharing `output/` across workers | Race conditions |
| Worker writes to project tree | Worker's deliverable target becomes unreliable (other tasks may overwrite) |
| Worker reads from sibling's `output/` directly | Order-of-execution dependency breaks if worker re-spawns |
| No `result.json` | H-42 "empty result = nothing to do" trap; orchestrator can't distinguish success from failure |
| Passing `kanban complete --cleanup` | The flag does not exist; scratch-workspace cleanup is `_cleanup_workspace` on `complete_task`, never a completion flag |
| Expecting `hermes kanban archive <task_id>` to remove the workspace dir | `archive` only flips task rows to `archived`; workspace dir is untouched unless it was a scratch dir already cleaned by `_cleanup_workspace` on completion |
| Treating `hermes kanban gc` as a 30-day workspace retention | `gc` prunes `task_events` rows and worker log files; it does **not** touch workspace directories |
| Treating `input/`, `output/`, `cache/`, `logs/` as lifecycle-created | The lifecycle creates only the root workspace dir; subdirs and the MD5/chmod discipline are worker / orchestrator responsibilities |

## Failure recovery

If a worker's workspace becomes corrupted mid-run:

1. **Stop the worker** (the dispatcher's stale-timeout fires after
   `claim.stale_timeout_seconds`).
2. **Mark the task `archived`** via
   `hermes kanban archive <task_id>`. The workspace dir is not
   moved by `archive`; for a scratch workspace it may already have
   been removed by `_cleanup_workspace` if the worker ever reached
   `complete_task`; for `worktree`/`dir`, the dir stays where it is.
3. **Re-queue the task** — a fresh worker will materialise a new
   workspace (scratch) or reuse the existing one (worktree/dir) and
   re-validate against the input MD5 reference.
4. **Surface in diagnostics** — `hermes kanban diagnostics` should
   flag the corruption so the operator can investigate input
   drift.
5. **Run `hermes kanban gc`** only to apply the configured
   `task_events` / worker-log retention windows; it does **not**
   reclaim workspace disk space.

## Related skills

- `swarm-router` — picks between parallel-reads, kanban-swarm,
  MoA-consensus, persona-pipeline.
- `coding-pipeline-orchestrator` (H-31) — pipeline mode uses
  worktrees instead of this layout; see
  `## Interaction with coding-pipeline-orchestrator (H-31)` above.
- `worker-failure-discipline` (H-42) — defines when a worker
  counts as failed (no `result.json` = failure, not "nothing to do").
- `queen-bee-schwarm-dispatch` — the dispatcher that actually
  spawns workers into these workspaces.
- `multi-agent-work` — broader patterns around running multiple
  agents on a shared problem.
- `kanban-system-health` — operational health checks for boards,
  workspaces, and retention.
