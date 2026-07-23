---
title: Hermes Kanban Worker Toolset Drift + JSON-Shape Drift
date: 2026-07-11
source: kanban-video-orchestrator v1.0.2 audit
status: live findings
---

# Kanban Worker Toolset Drift + JSON-Shape Drift

This reference captures **two distinct drift classes** that surfaced while auditing the
`kanban-video-orchestrator` v1.0.2 release against a live Hermes install (current
profile: `default`, current model: MiniMax-M3 via minimax-oauth, 2026-07-11). Both
findings reproduce against `yuno-coder` and `yuno` profiles and affect every worker
spawned via `hermes kanban create`.

## Drift 1 — Worker-Toolset-Resolution: `toolsets` vs `platform_toolsets.cli`

**Symptom:** Worker spawns, has a profile with `toolsets: [kanban, terminal, file]`
in `config.yaml`, but the dispatched subprocess inherits the **wrong / empty tool
surface** — Director cannot decompose, renderers cannot write files.

**Live evidence (2026-07-11, `kanban_db.py:7721-7752`):**
```python
def _resolve_worker_cli_toolsets(hermes_home: Optional[str]) -> Optional[list[str]]:
    """
    ... Resolve the assignee profile's CLI tool surface at dispatch time and
    pass it as an explicit --toolsets pin so worker startup cannot fall back
    to a stale root/active-profile config or a profile whose top-level
    ``toolsets`` entry is only the kanban orchestrator surface.
    """
```

The dispatcher resolves toolsets via `_get_platform_tools(cfg, "cli")` which
**reads `platform_toolsets.cli`**, not the profile's top-level `toolsets` key.
Writing only `cfg["toolsets"] = toolsets` in a setup script is therefore
**incomplete** — the workers will be spawned with the root profile's CLI
toolset (which may be empty for a freshly-cloned profile).

**Live verification on Basti's box:**

```bash
$ python3 -c "from hermes_cli.kanban_db import _resolve_worker_cli_toolsets; \
              print(_resolve_worker_cli_toolsets('/home/bratan/.hermes/profiles/yuno-coder'))"
['browser', 'clarify', 'code_execution', 'computer_use', 'cronjob',
 'delegation', 'file', 'image_gen', 'kanban', 'memory', 'session_search',
 'skills', 'terminal', 'todo', 'tts', 'vision', 'web']

$ python3 -c "from hermes_cli.kanban_db import _resolve_worker_cli_toolsets; \
              print(_resolve_worker_cli_toolsets('/home/bratan/.hermes/profiles/yuno'))"
['clarify', 'context_engine', 'file', 'memory', 'session_search',
 'skills', 'terminal', 'todo', 'vision']
```

The `yuno-coder` profile lists `toolsets: [hermes-cli, web]` at the top level but
the dispatcher resolves 17 distinct platform toolsets. **These are not the same
list** — `hermes-cli` is a composite that expands to many tools, and `web` is
explicitly added. Any generator / setup script that writes only `toolsets` is
silently overriding the resolved surface.

**Fix recipe (proposed in `kanban-video-orchestrator` v1.0.3 fork):**

```python
# In Python setup-script template (embedded yaml patch):
cfg["toolsets"] = toolsets
cfg.setdefault("skills", {})["always_load"] = skills
platform_toolsets = cfg.setdefault("platform_toolsets", {})
platform_toolsets["cli"] = toolsets
```

```bash
# Verify in generated setup.sh before write-back:
assert after.get("toolsets") == toolsets, f"toolsets mismatch for {profile}"
assert after.get("platform_toolsets", {}).get("cli") == toolsets, \
       f"platform_toolsets.cli mismatch for {profile}"
assert after.get("skills", {}).get("always_load") == skills, \
       f"skills.always_load mismatch for {profile}"
```

**Symptom checklist for live triage (2026-07-11):**

| Symptom | Likely cause |
|---|---|
| Worker says "no tool named `kanban_create`" or `delegate_task` | profile missing `platform_toolsets.cli` entry |
| Worker spawns with empty `enabled_toolsets` | root profile has no `platform_toolsets` and worker profile inherits empty list |
| Worker sees a different tool surface than the user's interactive chat | dispatcher resolved via root config, not profile config |
| Setup script claims success but workers fail immediately | `--workspace dir:` + missing toolset + missing description = silent death |

**Mitigation without a code change:** dispatch via `hermes kanban dispatch`
once after setup, watch the `runs` table for the `metadata.toolsets` field
(only present in newer Hermes versions) — if missing or empty, the profile
needs `platform_toolsets.cli` populated.

## Drift 2 — `kanban list --json` vs `kanban show --json` JSON-Shape Drift

**Symptom:** Any monitoring / observability script that enriches `kanban list
--json` output with `heartbeat_at`, `started_at`, `max_runtime_s`, `retries`
fields is silently getting `None` for everything that matters — STUCK /
OVERTIME / FLAPPING detection works only by accident.

**Live evidence (2026-07-11, `hermes_cli/kanban.py:60-83`):**
```python
def _task_to_dict(t: kb.Task) -> dict[str, Any]:
    return {
        "id": t.id, "title": t.title, "body": t.body, ...
        "started_at": t.started_at, "completed_at": t.completed_at,
        "result": t.result, "skills": list(t.skills) if t.skills else [],
        "max_retries": t.max_retries, ...
    }
```

`Task` has **no** `heartbeat_at`, `last_heartbeat_at`, `max_runtime_s`,
`max_runtime_seconds`, or `retries` fields. Those live on the `Run` dataclass
(`kanban_db.py:1004-1055`).

`kanban show <task-id> --json` returns a different shape:
```python
# kanban.py around show():
{
    "task": { ... Task fields ... },
    "latest_summary": "...",
    "parents": [...], "children": [...],
    "events": [...], "runs": [
        {"id": 9, "profile": "yuno-coder", "status": "crashed",
         "outcome": "crashed", "error": "worker exited cleanly (rc=0)
                     without calling kanban_complete or kanban_block —
                     protocol violation",
         "started_at": 1783587128, "ended_at": 1783587248,
         "max_runtime_seconds": null, "last_heartbeat_at": null, ...}
    ]
}
```

**The original `kanban-video-orchestrator/scripts/monitor.py` did:**

```python
def enrich(tasks: list[dict]) -> list[dict]:
    enriched = []
    for t in tasks:
        if all(k in t for k in ["heartbeat_at", "started_at",
                                "max_runtime_s", "retries"]):
            enriched.append(t)
            continue
        detail = kanban_show(t.get("id", "")) or {}
        merged = dict(t)
        for k in ["heartbeat_at", "started_at", "max_runtime_s",
                  "retries", "status", "assignee", "title"]:
            if k in detail and detail[k] is not None:
                merged[k] = detail[k]
        enriched.append(merged)
    return enriched
```

**Bug:** `detail["heartbeat_at"]` is **never set** — `kanban show` returns
`{task, runs, events, ...}` not a flat task dict. `heartbeat_at` was on
`runs[-1]`, not the task root. The `for k in ...: if k in detail ...` loop
**silently swallowed everything** that mattered.

**Fix recipe (in v1.0.3 fork):**

```python
def enrich(tasks: list[dict]) -> list[dict]:
    enriched = []
    for t in tasks:
        task_id = t.get("id", "")
        detail = kanban_show(task_id) or {}
        task_detail = detail.get("task") if isinstance(detail.get("task"), dict) else {}
        merged = dict(task_detail or t)
        merged.update({k: v for k, v in t.items() if v is not None})
        runs = detail.get("runs") if isinstance(detail.get("runs"), list) else []
        if runs:
            latest = runs[-1]
            merged["latest_run_status"] = latest.get("status")
            merged["latest_run_outcome"] = latest.get("outcome")
            merged["latest_run_error"] = latest.get("error")
            merged["retries"] = max(0, len(runs) - 1)
            for src_key, dst_key in [
                ("last_heartbeat_at", "heartbeat_at"),
                ("started_at", "started_at"),
                ("max_runtime_seconds", "max_runtime_s"),
            ]:
                if latest.get(src_key) is not None:
                    merged[dst_key] = latest.get(src_key)
        else:
            if merged.get("max_runtime_seconds") is not None:
                merged["max_runtime_s"] = merged.get("max_runtime_seconds")
            if merged.get("last_heartbeat_at") is not None:
                merged["heartbeat_at"] = merged.get("last_heartbeat_at")
            merged.setdefault("retries", 0)
        enriched.append(merged)
    return enriched
```

Plus a UTC-aware timestamp parser (epoch-or-ISO):

```python
def parse_ts(value) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    try:
        if text.isdigit():
            return datetime.fromtimestamp(float(text), tz=timezone.utc)
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError, OSError):
        return None
```

**Lesson:** `kanban list --json` is flat task-shaped (no run history). `kanban
show --json` is `{task, runs, events, ...}` aggregate. Any observability code
that tries to merge them by direct key copy **will silently fail**. Always
read run history from `runs[-1]` and the task body from `task`.

## Audit Recipe (re-runnable)

```bash
# Live JSON-shape check for any Hermes version:
hermes kanban list --json | python3 -c "import json, sys; \
  rows = json.load(sys.stdin); \
  print('list keys (first row):', sorted(rows[0].keys()) if rows else '<empty>')"

hermes kanban show t_<any_task_id> --json | python3 -c "import json, sys; \
  d = json.load(sys.stdin); \
  print('show top-level keys:', sorted(d.keys())); \
  print('runs[0] keys (if any):', sorted(d['runs'][0].keys()) if d.get('runs') else '<no runs>')"

# Toolset-resolution check for any profile:
python3 -c "from hermes_cli.kanban_db import _resolve_worker_cli_toolsets; \
  print(_resolve_worker_cli_toolsets('/home/bratan/.hermes/profiles/<name>'))"
```

If `list keys` lacks `heartbeat_at`/`max_runtime_s`/`retries` and `show` puts
those fields under `runs[-1]`, you're hitting both drifts.

## Related Drifts (sibling findings)

- `hermes kanban stats` is **board-scoped**, not tenant-scoped. There's no
  `--tenant` flag. README/SMOKE-RUNBOOK of `kanban-video-orchestrator`
  v1.0.2 incorrectly document `hermes kanban stats --tenant foo`. Use
  `kanban list --tenant foo --json` or a custom `monitor.py` for
  tenant-specific stats.
- `hermes kanban heartbeat <task-id> --note "..."` is the supported liveness
  signal. The dispatcher reads `last_heartbeat_at` from the `task_runs`
  table; emitting from the worker via this CLI command is the only
  reliable way.
- `--skills` and `-t/--toolsets` on `hermes kanban create` exist; the
  `skill_lanes.*.skills` lists in `config.yaml` are bundle composition hints
  for the interactive chat, **not** worker tool preloads.