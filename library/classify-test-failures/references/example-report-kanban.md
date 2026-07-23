# Example: 18 Kanban Test Failures Audit (2026-07-13)

Source artifact: `/home/bratan/.hermes/hermes-agent/docs/audits/kanban-test-leakage-audit-2026-07-13.md`

Full text reproduced here because the in-repo version may drift; this copy
serves as a worked example of the report structure produced by
`classify-test-failures`.

---

## 1. Reproducibility Proof (Phase 1)

Clean state: `main` branch, `git diff --quiet` returned 0 (the earlier
`captured_hooks` patch was reverted via `git show HEAD:… > FILE`).

```bash
cd /home/bratan/.hermes/hermes-agent
export TMPDIR=/tmp/hermes-kanban-audit-pytest2
export PYTHONDONTWRITEBYTECODE=1
PY=/home/bratan/.hermes/hermes-agent/venv/bin/python

# Cumulative run reproduced the original 18 failures exactly:
"$PY" -m pytest -p no:cacheprovider -q --tb=line \
  tests/hermes_cli/test_kanban_core_functionality.py \
  tests/hermes_cli/test_kanban_db.py \
  tests/hermes_cli/test_kanban_decompose.py \
  tests/hermes_cli/test_kanban_lifecycle_hooks.py \
  tests/plugins/test_kanban_worker_runs.py
# → 18 failed, 536 passed (RC=1)
```

## 2. Single-File Isolation (Phase 2)

All 5 suspect files passed individually:

| File | Result |
|---|---|
| `test_kanban_core_functionality.py` | 169 passed in 9.79s |
| `test_kanban_db.py` | 230 passed in 10.21s |
| `test_kanban_decompose.py` | 9 passed in 0.53s |
| `test_kanban_lifecycle_hooks.py` | 6 passed in 0.32s |
| `test_kanban_worker_runs.py` | 16 passed in 1.33s |

**Implication:** all 18 failures are cross-file leakage / ordering, NOT
in-file regressions.

## 3. Pairwise Ordering Matrix (Phase 3)

The minimal cascade for `test_claim_fires_hook` (the most fragile):

| Order | Result |
|---|---|
| `test_kanban_cli_dispatch_passthrough::test_cli_dispatch_passes_max_in_progress_from_config` then `test_kanban_lifecycle_hooks::test_claim_fires_hook` | **1 fail** |
| `test_kanban_lifecycle_hooks::test_claim_fires_hook` then the same dispatch test | 2 passed |
| Same with `test_kanban_default_assignee::test_unassigned_task_skipped_without_default_assignee` first | **1 fail** |
| Reversed | 2 passed |

Cumulative cascade (each row adds one file to the prefix):

| Prefix + | Additional Failures |
|---|---|
| `test_kanban_core_functionality.py` | 1 (`test_detect_crashed_workers_protocol_violation_auto_blocks`) |
| `test_kanban_db.py` | 8 |
| `test_kanban_decompose.py` | 5 |
| `test_kanban_lifecycle_hooks.py` | 3 |
| `test_kanban_worker_runs.py` | 1 |
| **Σ all 5** | **18 (= original)** |

## 4. Classification Table (Phase 5)

| # | Test ID | Class | Root Cause Code |
|---|---------|-------|-----------------|
| 1 | `test_kanban_lifecycle_hooks::test_claim_fires_hook` | FIXTURE_LEAK | `tests/hermes_cli/test_kanban_lifecycle_hooks.py:13-16` (stale `get_plugin_manager` ref) |
| 2 | `test_kanban_lifecycle_hooks::test_complete_fires_hook_with_summary` | FIXTURE_LEAK | same |
| 3 | `test_kanban_lifecycle_hooks::test_block_fires_hook_with_reason` | FIXTURE_LEAK | same |
| 4 | `test_kanban_core_functionality::test_detect_crashed_workers_protocol_violation_auto_blocks` | ENV_VAR_BLEED | `tests/conftest.py` `_hermetic_environment` doesn't unset `HERMES_KANBAN_CRASH_GRACE_SECONDS` |
| 5 | `test_kanban_db::test_stale_claim_with_live_pid_extends_instead_of_reclaiming` | TEST_ORDERING | `_kb._pid_alive` monkeypatch leak |
| 6 | `test_kanban_db::test_stale_claim_with_live_pid_uses_env_ttl_override` | TEST_ORDERING | same |
| 7 | `test_kanban_db::test_stale_claim_deferred_when_live_worker_survives_termination` | TEST_ORDERING | same |
| 8 | `test_kanban_db::test_rate_limit_exit_requeues_without_counting_failure` | TEST_ORDERING | `_kb.detect_crashed_workers._last_rate_limited` accumulates |
| 9 | `test_kanban_db::test_detect_stale_returns_running_task_with_no_heartbeat` | TEST_ORDERING | same as #5 |
| 10 | `test_kanban_db::test_detect_stale_returns_task_with_stale_heartbeat` | TEST_ORDERING | same |
| 11 | `test_kanban_db::test_detect_stale_does_not_tick_failure_counter` | TEST_ORDERING | same |
| 12 | `test_kanban_db::test_reap_worker_zombies_records_exit_status` | FIXTURE_LEAK | `os.waitpid` mock leak |
| 13 | `test_kanban_decompose::test_decompose_with_fanout_creates_children` | FIXTURE_LEAK | `_load_config` patch not stopped in finally |
| 14 | `test_kanban_decompose::test_decompose_fanout_false_assigns_default_when_unassigned` | FIXTURE_LEAK | same |
| 15 | `test_kanban_decompose::test_decompose_fanout_false_uses_valid_llm_assignee` | FIXTURE_LEAK | same |
| 16 | `test_kanban_decompose::test_decompose_fanout_false_invalid_llm_assignee_uses_default` | FIXTURE_LEAK | same |
| 17 | `test_kanban_decompose::test_decompose_unknown_assignee_falls_back_to_default` | FIXTURE_LEAK | same |
| 18 | `test_kanban_worker_runs::test_terminate_run_ok` | FIXTURE_LEAK | Patch targets `kb` import but router resolved differently |

**Summary: 0 / 18 real regressions, 18 / 18 fixture-leak / ordering.**

## 5. Mechanism Proof (Phase 6) — `test_claim_fires_hook`

Standalone repro (no pytest):

```python
import sys, importlib, tempfile, os
from pathlib import Path
sys.path.insert(0, '/home/bratan/.hermes/hermes-agent')

# Collection-time import
spec = importlib.util.spec_from_file_location(
    'lifecycle',
    '/home/bratan/.hermes/hermes-agent/tests/hermes_cli/test_kanban_lifecycle_hooks.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
mod_mgr = mod.get_plugin_manager()

# Simulate isolated_kanban_home sys.modules wipe
for k in list(sys.modules.keys()):
    if k.startswith('hermes_cli.'):
        del sys.modules[k]

# captured_hooks registers on mod_mgr (the OLD singleton)
events = []
mod_mgr._hooks.setdefault('kanban_task_claimed', []).append(lambda **kw: events.append(kw))

# Production code: kb._fire_kanban_lifecycle_hook lazy-imports the NEW plugins module
# Dispatch lands on the new singleton, NOT mod_mgr → events stays empty.
with tempfile.TemporaryDirectory() as td:
    home = Path(td) / '.hermes'; home.mkdir()
    Path.home = lambda: Path(td)
    mod.kb.init_db()
    conn = mod.kb.connect()
    tid = mod.kb.create_task(conn, title='t', assignee='worker')
    mod.kb.claim_task(conn, tid)
    conn.close()
print('events captured:', events)   # → []
```

This proves the classification: the failure is structural (stale
module-scope reference), not a production regression.

## 6. Recommendations (no auto-fix)

1. **Per-file subprocess isolation** (lowest risk): `scripts/run_tests_parallel.py`
   already does this; the audit's failures vanished when files were
   separated into independent processes.
2. **Captured-hooks refactor** (medium): replace module-scope
   `from hermes_cli.plugins import get_plugin_manager` with
   `_live_plugin_manager()` helper using `importlib.import_module` at
   call time.
3. **Decompose-test cleanup**: switch `_patch_list_profiles` to
   `enterContext` pattern; ensure `p.stop()` runs even on exception.
4. **Worker-runs patch target**: route monkeypatch through
   `plugins.kanban.dashboard.plugin_api.kanban_db` instead of `kb`.

## 7. Reproduction Commands (copy-pasteable)

See the audit file for the full set. The minimal cascade:

```bash
"$PY" -m pytest -p no:cacheprovider -q --tb=line \
  tests/hermes_cli/test_kanban_cli_dispatch_passthrough.py::test_cli_dispatch_passes_max_in_progress_from_config \
  tests/hermes_cli/test_kanban_lifecycle_hooks.py::test_claim_fires_hook
```

Reversed:

```bash
"$PY" -m pytest -p no:cacheprovider -q --tb=line \
  tests/hermes_cli/test_kanban_lifecycle_hooks.py::test_claim_fires_hook \
  tests/hermes_cli/test_kanban_cli_dispatch_passthrough.py::test_cli_dispatch_passes_max_in_progress_from_config
```

The first fails, the second passes — that's the ordering signal.