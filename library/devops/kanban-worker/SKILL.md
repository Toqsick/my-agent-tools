---
name: kanban-worker
description: "Use when user asks for Kanban worker pitfalls, worker examples, tenant isolation patterns, card claiming rules. NOT for Kanban system health or board policy (use kanban-system-health). Pitfalls, examples, and edge cases for Hermes Kanban workers."
version: 2.2.0
changelog:
- 2026-07-09 - Added done_hook / side-effect extension pattern with subprocess fire-and-forget
  contract, hook DB path resolution, and schema migration guide for hook columns.
  Added references/mnemosyne-done-hook-2026-07-09.md.
platforms:
- linux
- macos
- windows
environments:
- kanban
metadata:
  hermes:
    tags:
    - kanban
    - multi-agent
    - collaboration
    - workflow
    - pitfalls
    related_skills:
    - kanban-orchestrator
author: Hermes Agent
license: MIT
lane: worker-heavy
reasoning_effort: xhigh
trigger_keywords: ['kanban', 'worker', 'pitfalls', 'examples', 'system']
keywords: ['kanban', 'worker', 'pitfalls', 'examples', 'system']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['board-policy', 'multi-agent-pitfalls-cheatsheet', 'kanban-codex-lane']
---


# Kanban Worker — Pitfalls and Examples

> You're seeing this skill because the Hermes Kanban dispatcher spawned you as a worker with `--skills kanban-worker` — it's loaded automatically for every dispatched worker. The **lifecycle** (6 steps: orient → work → heartbeat → block/complete) also lives in the `KANBAN_GUIDANCE` block that's auto-injected into your system prompt. This skill is the deeper detail: good handoff shapes, retry diagnostics, edge cases.

## Workspace handling

Your workspace kind determines how you should behave inside `$HERMES_KANBAN_WORKSPACE`:

| Kind | What it is | How to work |
|---|---|---|
| `scratch` | Fresh tmp dir, yours alone | Read/write freely; it gets GC'd when the task is archived. |
| `dir:<path>` | Shared persistent directory | Other runs will read what you write. Treat it like long-lived state. Path is guaranteed absolute (the kernel rejects relative paths). |
| `worktree` | Git worktree at the resolved path | If `.git` doesn't exist, run `git worktree add <path> ${HERMES_KANBAN_BRANCH:-wt/$HERMES_KANBAN_TASK}` from the main repo first, then cd and work normally. Commit work here. |

## Tenant isolation

If `$HERMES_TENANT` is set, the task belongs to a tenant namespace. When reading or writing persistent memory, prefix memory entries with the tenant so context doesn't leak across tenants:

- Good: `business-a: Acme is our biggest customer`
- Bad (leaks): `Acme is our biggest customer`

## Good summary + metadata shapes

The `kanban_complete(summary=..., metadata=...)` handoff is how downstream workers read what you did. Patterns that work:

**Coding task:**
```python
kanban_complete(
    summary="shipped rate limiter — token bucket, keys on user_id with IP fallback, 14 tests pass",
    metadata={
        "changed_files": ["rate_limiter.py", "tests/test_rate_limiter.py"],
        "tests_run": 14,
        "tests_passed": 14,
        "decisions": ["user_id primary, IP fallback for unauthenticated requests"],
    },
)
```

**Coding task that needs human review (review-required):**

For most code-changing tasks, the work isn't truly *done* until a human reviewer has eyes on it. Block instead of complete, with `reason` prefixed `review-required: ` so the dashboard surfaces the row as needing review. Drop the structured metadata (changed files, test counts, diff/PR url) into a comment first, since `kanban_block` only carries the human-readable reason — comments are the durable annotation channel. Reviewer either approves and runs `hermes kanban unblock <id>` (which re-spawns you with the comment thread for any follow-ups) or asks for changes via another comment.

```python
import json

kanban_comment(
    body="review-required handoff:\n" + json.dumps({
        "changed_files": ["rate_limiter.py", "tests/test_rate_limiter.py"],
        "tests_run": 14,
        "tests_passed": 14,
        "diff_path": "/path/to/worktree",  # or PR url if pushed
        "decisions": ["user_id primary, IP fallback for unauthenticated requests"],
    }, indent=2),
)
kanban_block(
    reason="review-required: rate limiter shipped, 14/14 tests pass — needs eyes on the user_id/IP fallback choice before merging",
)
```

Use `kanban_complete` only when the task is genuinely terminal — e.g. a one-line typo fix, a docs change with no functional consequences, or a research task where the artifact IS the writeup itself.

**Research task:**
```python
kanban_complete(
    summary="3 competing libraries reviewed; vLLM wins on throughput, SGLang on latency, Tensorrt-LLM on memory efficiency",
    metadata={
        "sources_read": 12,
        "recommendation": "vLLM",
        "benchmarks": {"vllm": 1.0, "sglang": 0.87, "trtllm": 0.72},
    },
)
```

**Review task:**
```python
kanban_complete(
    summary="reviewed PR #123; 2 blocking issues found (SQL injection in /search, missing CSRF on /settings)",
    metadata={
        "pr_number": 123,
        "findings": [
            {"severity": "critical", "file": "api/search.py", "line": 42, "issue": "raw SQL concat"},
            {"severity": "high", "file": "api/settings.py", "issue": "missing CSRF middleware"},
        ],
        "approved": False,
    },
)
```

Shape `metadata` so downstream parsers (reviewers, aggregators, schedulers) can use it without re-reading your prose.

## Claiming cards you actually created

If your run produced new kanban tasks (via `kanban_create`), pass the ids in `created_cards` on `kanban_complete`. The kernel verifies each id exists and was created by your profile; any phantom id blocks the completion with an error listing what went wrong, and the rejected attempt is permanently recorded on the task's event log. **Only list ids you captured from a successful `kanban_create` return value — never invent ids from prose, never paste ids from earlier runs, never claim cards another worker created.**

```python
# GOOD — capture return values, then claim them.
c1 = kanban_create(title="remediate SQL injection", assignee="security-worker")
c2 = kanban_create(title="fix CSRF middleware", assignee="web-worker")

kanban_complete(
    summary="Review done; spawned remediations for both findings.",
    metadata={"pr_number": 123, "approved": False},
    created_cards=[c1["task_id"], c2["task_id"]],
)
```

```python
# BAD — claiming ids you don't have captured return values for.
kanban_complete(
    summary="Created remediation cards t_a1b2c3d4, t_deadbeef",  # hallucinated
    created_cards=["t_a1b2c3d4", "t_deadbeef"],                   # → gate rejects
)
```

If a `kanban_create` call fails (exception, tool_error), the card was NOT created — do not include a phantom id for it. Retry the create, or omit the id and mention the failure in your summary. The prose-scan pass also catches `t_<hex>` references in your free-form summary that don't resolve; these don't block the completion but show up as advisory warnings on the task in the dashboard.

## Block reasons that get answered fast

Bad: `"stuck"` — the human has no context.

Good: one sentence naming the specific decision you need. Leave longer context as a comment instead.

```python
kanban_comment(
    task_id=os.environ["HERMES_KANBAN_TASK"],
    body="Full context: I have user IPs from Cloudflare headers but some users are behind NATs with thousands of peers. Keying on IP alone causes false positives.",
)
kanban_block(reason="Rate limit key choice: IP (simple, NAT-unsafe) or user_id (requires auth, skips anonymous endpoints)?")
```

The block message is what appears in the dashboard / gateway notifier. The comment is the deeper context a human reads when they open the task.

## Heartbeats worth sending

Good heartbeats name progress: `"epoch 12/50, loss 0.31"`, `"scanned 1.2M/2.4M rows"`, `"uploaded 47/120 videos"`.

Bad heartbeats: `"still working"`, empty notes, sub-second intervals. Every few minutes max; skip entirely for tasks under ~2 minutes.

## Retry scenarios

If you open the task and `kanban_show` returns `runs: [...]` with one or more closed runs, you're a retry. The prior runs' `outcome` / `summary` / `error` tell you what didn't work. Don't repeat that path. Typical retry diagnostics:

- `outcome: "timed_out"` — the previous attempt hit `max_runtime_seconds`. You may need to chunk the work or shorten it.
- `outcome: "crashed"` — OOM or segfault. Reduce memory footprint.
- `outcome: "spawn_failed"` + `error: "..."` — usually a profile config issue (missing credential, bad PATH). Ask the human via `kanban_block` instead of retrying blindly.
- `outcome: "reclaimed"` + `summary: "task archived..."` — operator archived the task out from under the previous run; you probably shouldn't be running at all, check status carefully.
- `outcome: "blocked"` — a previous attempt blocked; the unblock comment should be in the thread by now.

## Notification routing

You can configure the gateway to receive cross-profile Kanban task notifications by adding `notification_sources` to `~/.hermes/config.yaml`.
- `notification_sources: ['*']` accepts subscriptions from all profiles.
- `notification_sources: ['default', 'zilor-ppt']` or `"default,zilor-ppt"` restricts subscriptions to specified profiles.
- Omitting the key keeps the default behavior (profile isolation).

## Do NOT

- Call `delegate_task` as a substitute for `kanban_create`. `delegate_task` is for short reasoning subtasks inside YOUR run; `kanban_create` is for cross-agent handoffs that outlive one API loop.
- Call `clarify` to ask the human a question. You are running headless — there is no live user to answer. The call will time out (default ~120s) and the task will sit silently in `running` with no signal that it needs input. Use `kanban_comment` (context) + `kanban_block(reason=...)` (decision needed) instead — the task surfaces on the board as blocked, the operator sees it, unblocks with their answer in a comment, and you respawn with the thread.
- Modify files outside `$HERMES_KANBAN_WORKSPACE` unless the task body says to.
- Create follow-up tasks assigned to yourself — assign to the right specialist.
- Complete a task you didn't actually finish. Block it instead.

## Pitfalls

**Task state can change between dispatch and your startup.** Between when the dispatcher claimed and when your process actually booted, the task may have been blocked, reassigned, or archived. Always `kanban_show` first. If it reports `blocked` or `archived`, stop — you shouldn't be running.

**Workspace may have stale artifacts.** Especially `dir:` and `worktree` workspaces can have files from previous runs. Read the comment thread — it usually explains why you're running again and what state the workspace is in.

**Don't rely on the CLI when the guidance is available.** The `kanban_*` tools work across all terminal backends (Docker, Modal, SSH). `hermes kanban <verb>` from your terminal tool will fail in containerized backends because the CLI isn't installed there. When in doubt, use the tool.

**Exiting cleanly (rc=0) without calling `kanban_complete` or `kanban_block` is treated as a crash.** The kernel reaps your process, increments `consecutive_failures`, and may auto-block the task via the circuit breaker (`failure_limit: 2`). The diagnostic will read `worker exited cleanly (rc=0) without calling kanban_complete or kanban_block — protocol violation`. The fix is discipline: at the end of every run, decide explicitly whether the work is **done** (call `kanban_complete`), **needs human input** (call `kanban_block` with `kind=needs_input`), **needs another tool/profile** (call `kanban_block` with `kind=capability`), or **has dependency on unfinished work** (call `kanban_block` with `kind=dependency`). Never just let the process exit — the dispatcher assumes crash-and-retry semantics on un-annotated exits.

**Iterations budget (default 80) is per-task, not per-session.** Tasks that run long Agentic loops — e.g. an autonomous refactor with file reads, edits, test runs, repeated verification — will burn through the 80-iteration budget and exit with `Iteration budget exhausted (80/80) — task could not complete within the allowed iterations`. The circuit breaker then auto-blocks on the next attempt. The fix is one of: (a) chunk the work into sub-tasks via `kanban_create` so each card has a smaller iteration budget, (b) use Goal-Mode (`--goal --goal-max-turns N`) so the Judge re-evaluates instead of the iteration budget, or (c) raise `agent.max_turns` in `~/.hermes/config.yaml` for tasks that genuinely need >80 iterations. Don't try to "push harder" — the budget is a hard cap for runaway-task protection.

## Done hook / side-effect extension pattern

When you need to fire a side-effect (memory capture, logging, WebHook, notification, analytics) from `complete_task()`, use the **subprocess fire-and-forget** pattern — never inline code that could roll back the completion transaction.

### Hook integration point in `kanban_db.py`

The hook fires **after** confirming the task update succeeded (`if cur.rowcount != 1: return False`), **before** the event-logic (`_end_run`, timeline events):

```python
# In kanban_db.py's complete_task():
try:
    import base64 as _b64
    import os as _os
    import subprocess as _sp
    _hook = _os.environ.get(
        "KANBAN_DONE_HOOK",
        "/home/bratan/50-System/bin/kanban-done-hook.py",
    )
    if _os.path.isfile(_hook):
        _row = conn.execute(
            "SELECT title, body, assignee FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        _title = _row[0] if _row else ""
        _body = (_row[1] if _row and _row[1] else "") or ""
        _assignee = (_row[2] if _row and _row[2] else "") or ""
        _args = [
            _os.environ.get("HERMES_VENV_PYTHON",
                "/home/bratan/.hermes/hermes-agent/venv/bin/python3"),
            _hook, task_id, _title,
            _b64.b64encode(_body.encode("utf-8", "replace")).decode("ascii"),
            _b64.b64encode((result or "").encode("utf-8", "replace")).decode("ascii"),
            _assignee,
        ]
        _sp.Popen(_args, stdin=_sp.DEVNULL, stdout=_sp.DEVNULL,
                  stderr=_sp.DEVNULL, start_new_session=True)
except Exception:
    pass  # Must never roll back the completion
```

**Why subprocess + Popen + DEVNULL + start_new_session:**
- The hook can take 1-3s (first-time model load, network call) — must not block the completion transaction.
- Dispatcher writes in `IMMEDIATE` transaction semantics — any hook exception would roll back `complete_task()` itself.
- `start_new_session=True` orphans the subprocess from the dispatcher's process group so a dispatcher kill doesn't kill the hook mid-flight.
- `DEVNULL` keeps hook stderr from polluting the dispatcher's stderr stream.
- The `try/except` is a hard fence: hook code never, ever touches the original connection.

### Hook contract

The hook script receives **6 positional args**: `(task_id, title, body_b64, result_b64, assignee)`.

- `body_b64` and `result_b64` are base64-encoded (task body and result fields can contain newlines, quotes, unicode).
- The hook must decode them first, then perform its side-effect.
- Optionally write back to the kanban DB (e.g. store a reference ID in a new column).
- Exit code 0 = success, non-zero = failure (silently logged, no rollback).

### Hook DB path resolution

If the hook writes back to the kanban DB, resolve the path in this order:

1. `KANBAN_DB_PATH` env var (manual override for testing).
2. `from hermes_cli import kanban_db as _kdb; db_path = str(_kdb.kanban_db_path())` — canonical path `kanban/boards/<slug>/kanban.db`.
3. Fallback: `<HERMES_HOME>/state/kanban.db` (legacy, often wrong on active boards).

**Pitfall:** The active DB is `kanban/boards/<board>/kanban.db`, NOT `state/kanban.db`. Resolving via `kanban_db.kanban_db_path()` is the only reliable way. Hardcoding `state/kanban.db` works for basic setups but misses board-scoped DBs.

### Schema extension for hook columns

If your hook writes back to the `tasks` table, extend the schema following the **additive migration pattern** (no Alembic — kanban_db uses a simpler approach):

1. **`SCHEMA_SQL`** (the `CREATE TABLE tasks (...)` string): add your new column here so fresh DBs get it automatically.
2. **`init_db()` body**: add a `_add_column_if_missing(conn, "tasks", "your_col_name", "TEXT")` call for existing DBs.
3. **Index**: add `conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_your_col ON tasks(your_col)")` in `init_db()`.

The helper `_add_column_if_missing` exists in `kanban_db.py` — it wraps `ALTER TABLE ... ADD COLUMN` in a try/except for idempotency (no-op if column already exists).

**Verification:** After migration, run `sqlite3 <kanban.db> 'PRAGMA table_info(tasks)'` and check the new column appears.

### Pitfalls specific to done hooks

**`complete_task()` parameter signature — title/body NOT included.** The function accepts `(conn, task_id, *, result, summary, metadata, created_cards, expected_run_id)`. Everything except `conn` and `task_id` is optional keyword-only. To access task metadata inside a hook, issue a fresh `SELECT title, body, assignee FROM tasks WHERE id = ?` in the hook script — do not expect these as function arguments. A Pyright lint pass (`undefined-variable`) catches this at edit time.

**`init_db()` takes `db_path` (str), not `conn`.** Calling `init_db(conn_object)` does not error (sqlite3.connect accepts a conn as first arg, opening that conn's database file path) but **does not run any schema SQL**. Pass the path string. Verify schema migrations by running `sqlite3 <path> 'PRAGMA table_info(tasks)'` against the actual DB file.

**Hook script path must be resolved at runtime, not hardcoded.** Use `KANBAN_DONE_HOOK` env var with the full path as the default. In containerized backends (Docker, Modal), host paths don't exist — the worker must either bundle the hook or skip gracefully.

---

## CLI fallback (for scripting)

Every tool has a CLI equivalent for human operators and scripts:
- `kanban_show` ↔ `hermes kanban show <id> --json`
- `kanban_complete` ↔ `hermes kanban complete <id> --summary "..." --metadata '{...}'`
- `kanban_block` ↔ `hermes kanban block <id> "reason"`
- `kanban_create` ↔ `hermes kanban create "title" --assignee <profile> [--parent <id>]`
- etc.

Use the tools from inside an agent; the CLI exists for the human at the terminal.
