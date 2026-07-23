---
title: Hermes Kanban Implementation Source-Audit (Source/Tests/Doku Drift)
date: 2026-07-13
status: live findings
workspace-head: ac705b52c
version: 0.18.2
---

# Kanban Implementation Source-Code Audit (2026-07-13)

**Zweck:** Diese Reference-Datei dokumentiert das vollständige Rezept + Live-Resultate für
einen read-only Source/Tests/Doku-Drift-Audit der Kanban-Implementierung. Sie validiert
die §14 Source-Code Implementation Audit Recipe Patterns in SKILL.md.

**Validierungs-Anlass:** User-Auftrag "Führe einen unabhängigen read-only Source-, Test- und
Doku-Drift-Audit der Hermes-Kanban-Implementierung durch" mit Referenz auf
`v0.18.2 (2026.7.7.2), bd740f20`.

---

## Audit-Kontext

- **Workspace-Pfad:** `/home/bratan/.hermes/hermes-agent`
- **Lokaler HEAD:** `ac705b52c90e114342370c3637e49c8d78b5afe6` ("fix(sessions): validate imported session payloads", main...origin/main [hinterher 4])
- **Version (pyproject):** `0.18.2` ✓ matcht User-Referenz
- **Vom User genannter Upstream-SHA:** `bd740f20` — **NICHT im Repo**. Verifiziert via:
  ```bash
  git log --oneline | grep bd740f20 || echo "SHA not in repo — drift confirmed"
  ```
  Audit wurde gegen den tatsächlich vorhandenen HEAD `ac705b52c` durchgeführt.

## Audit-Methodik

Read-only Inventur in 8 Audit-Achsen, jede mit Source:Line-Belegen. Pytest-Selector mit
11 Test-Files, 227 Tests. Kein Write, kein Commit, keine Mutation.

---

## Modul-Inventur (8 Source-Module)

```bash
$ wc -l hermes_cli/kanban.py hermes_cli/kanban_db.py hermes_cli/kanban_diagnostics.py \
        hermes_cli/kanban_swarm.py hermes_cli/kanban_decompose.py hermes_cli/kanban_specify.py \
        tools/kanban_tools.py gateway/kanban_watchers.py
 2845 hermes_cli/kanban.py
 8981 hermes_cli/kanban_db.py
 1133 hermes_cli/kanban_diagnostics.py
  278 hermes_cli/kanban_swarm.py
  477 hermes_cli/kanban_decompose.py
  273 hermes_cli/kanban_specify.py
 1681 tools/kanban_tools.py
 1286 gateway/kanban_watchers.py
16954 total
```

Doku-Files:
```
940 website/docs/user-guide/features/kanban.md
113 website/docs/user-guide/features/kanban-worker-lanes.md
310 website/docs/user-guide/features/kanban-tutorial.md
```

---

## Audit-Achse 1: State-Machine Invariants — robust

### Claim Atomicity (`hermes_cli/kanban_db.py:3373-3492`)

`claim_task` enforced **3 harte Server-Side Invariants**:

1. **Parent-Gate (Z. 3397-3413):** Vor dem CAS wird geprüft ob alle Parents `done` sind.
   Bei Treffer: demote zurück zu `todo` + emit `claim_rejected{reason: "parents_not_done"}`.
   Comment verweist auf RCA: `kanban/boards/cookai/workspaces/t_a6acd07d/root-cause.md`.

2. **Stale-Recovery (Z. 3418-3433):** Wenn ein phantom-hafter `current_run_id` aus einem
   vorherigen Run hängenbleibt, wird er als `reclaimed` geschlossen.

3. **CAS (Z. 3434-3448):** `UPDATE tasks SET status='running' WHERE id=? AND status='ready' AND claim_lock IS NULL`.
   Bei `rowcount != 1`: kein Mutate, return None.

### Complete Atomicity (`hermes_cli/kanban_db.py:4053-4090`)

Haupt-CAS: `WHERE status IN ('running', 'ready', 'blocked')`. Cleared im selben Statement:
`claim_lock`, `claim_expires`, `worker_pid`, `block_kind`, `block_recurrences` — keine
Observation-Inkonsistenzen.

### Block Routing nach Kind (`hermes_cli/kanban_db.py:4765-4965`)

3 Routen:
- `dependency` → `todo` (kein Cron-Re-Block möglich)
- `needs_input | None | capability` → `blocked`, **Loop-Breaker**: bei `recurrences >= BLOCK_RECURRENCE_LIMIT` → `triage`
- `transient` → wie generic block

---

## Audit-Achse 2: Atomic Claim/Lock — robust

### Single-DB-Writer Discipline (`hermes_cli/kanban_db.py:7174-7237`)

`dispatch_once` ist Wrapper um `_dispatch_once_locked` mit **`_dispatch_tick_lock(db_path)`**.
Verliert den Lock → `DispatchResult(skipped_locked=True)`. Lock-Doku verweist auf issue #35240.

### Write-Retry-Pattern (`hermes_cli/kanban_db.py`, Commit `204a67f0c`)

Transient `SQLITE_BUSY` wird in `write_txn` retried. Test-Dekorator
`tests/hermes_cli/test_kanban_write_txn_busy_retry.py` passed (8 Tests).

---

## Audit-Achse 3: Gateway Embedded-Dispatcher Lifecycle — sauber

### Integration (`gateway/run.py`)

- `gateway/run.py:1758` importiert `GatewayKanbanWatchersMixin`
- `GatewayRunner` erbt davon (`gateway/run.py:2775`)
- `asyncio.create_task(self._kanban_dispatcher_watcher())` (`gateway/run.py:7353`)

### Singleton-Lock (`gateway/kanban_watchers.py:60-110, 794-817`)

- `_dispatcher.lock` ist **machine-global** (`_kb.kanban_home() / "kanban" / ".dispatcher.lock"`)
- `held` → Process hält Lock für Lifetime
- `contended` → anderer Gateway hat Lock, **dispatcht nicht** (Z. 803-809)
- `unavailable` → kein flock (z.B. nicht-POSIX FS), fällt auf Config-Control zurück

### Shutdown (`gateway/kanban_watchers.py:1272-1286`)

`finally`-Pfade rufen `_release_singleton_lock` auf jeden Fall:
```python
_release_singleton_lock(self._kanban_dispatcher_lock_handle)
self._kanban_dispatcher_lock_handle = None
```

### Per-Board-Tick (`gateway/kanban_watchers.py:976-1078`)

`_tick_once_for_board(slug)` mit `board=slug` Argument. Corrupt-DB-Quarantäne via
`disabled_corrupt_boards` dict, periodic retry. Tests
`test_gateway_dispatcher_*` (in `test_kanban_watchers_mixin.py`) passed.

### Offenes TODO (`gateway/kanban_watchers.py:137`)

```python
# Gate: only the dispatch-owning gateway opens kanban DBs for notifier polling.
# TODO: gate per-board when per-board dispatcher_owner tracking lands.
```

Risiko: aktueller Singleton-Lock ist process-global, nicht per-Board. Bei Multi-Gateway-
Setup (z.B. docker-compose mit mehreren gateway-Containern) theoretisch doppeltes
Dispatch möglich, wenn beide auf demselben Host lock-frei sind. Status: nur Marker,
kein Bugfix nötig — Doku-Design-Linie "One dispatcher sweeps all boards per tick"
(`website/docs/user-guide/features/kanban.md` Z. 69) ist konsistent.

---

## Audit-Achse 4: Failure-Circuit-Breaker — robust

### Schema (`hermes_cli/kanban_db.py:1124`)

`consecutive_failures INTEGER NOT NULL DEFAULT 0` mit Spalten-Migration von Legacy
`spawn_failures` (Z. 1894-1903).

### Auto-Block-Pfad (`hermes_cli/kanban_db.py:7309`)

`result.promoted = recompute_ready(conn, failure_limit=failure_limit)`. Nach
`failure_limit` (default 2, `DEFAULT_FAILURE_LIMIT`) consecutive failures → task wird
auto-blocked. Comment Z. 7266-7271: "prevents thrashing on tasks whose profile doesn't exist".

### Success-Path Reset (`hermes_cli/kanban_db.py:4172-4176`)

```python
_clear_failure_counter(conn, task_id)
```

Der Counter ist für "aktuelle Pathologie", nicht Audit-History.

### Test-Coverage

`test_repeated_timeouts_trip_the_circuit_breaker` (in `test_kanban_core_functionality.py`)
passed.

---

## Audit-Achse 5: Board-Scoping — konsistent

### Flag existiert (`hermes_cli/kanban.py:214-224`)

```python
kanban_parser.add_argument("--board", ...)
```

### Pre-Check (`hermes_cli/kanban.py:894-921`)

- `boards`-Aktionen ignorieren `--board` explizit (gewollt, Z. 894)
- Andere Subcommands reichen es via `kb.scoped_current_board(normed)` als env-Pin durch (Z. 922)
- Pre-Check: `if normed != kb.DEFAULT_BOARD and not kb.board_exists(normed):` (Z. 915)
  → typo'd Slugs geben **expliziten Fehler** statt silent create

### Resolution-Chain (`hermes_cli/kanban_db.py:415-460`)

Priorität: `HERMES_KANBAN_BOARD` env (Worker-Pin) > pointer-file > `DEFAULT_BOARD`.

### Doku-Match

`website/docs/user-guide/features/kanban.md` Z. 105-129 dokumentiert exakt diese Reihenfolge.

---

## Audit-Achse 6: JSON-Contracts & Toolset-Liste — vollständig

### 9 Tools registriert (`tools/kanban_tools.py:1603-1681`)

```
kanban_show, kanban_list, kanban_complete, kanban_block,
kanban_heartbeat, kanban_comment, kanban_create, kanban_unblock, kanban_link
```

Exakt was die Doku (`kanban.md` Z. 27-28) bewirbt. **Vollständig konsistent.**

### Tool-Gates

- `kanban_list, kanban_unblock` → `check_fn=_check_kanban_orchestrator_mode`
- Rest → `check_fn=_check_kanban_mode`

### Worker-Task-Ownership (`tools/kanban_tools.py:135-165`)

`_enforce_worker_task_ownership(tid)` wirft, wenn `tid != HERMES_KANBAN_TASK`.

---

## Audit-Achse 7: Default-Assignee / Profile-Resolution

### Drei-Stufen-Lookup (`hermes_cli/kanban_db.py:7369-7397`)

```python
_default_assignee = (default_assignee or "").strip() or None
_default_assignee_resolved = False
if _default_assignee:
    try:
        from hermes_cli.profiles import profile_exists as _pe
        _default_assignee_resolved = bool(_pe(_default_assignee))
    except Exception:
        _default_assignee_resolved = True
```

Operator-Config `kanban.default_assignee` (gateway-side Z. 889-901 in
`kanban_watchers.py`) wird gepinnt als Fallback für unassigned ready tasks.

### Hardening

`_default_assignee_resolved = bool(_pe(_default_assignee))` — wird nur gesetzt, wenn
`profiles.profile_exists` wirklich true zurückgibt. Bei Test-Stub (Profile-Modul nicht
importierbar) wird `True` angenommen und downstream Profil-Check entscheidet.

---

## Audit-Achse 8: Retries / Heartbeats / Runtime

### Claim TTL (`hermes_cli/kanban_db.py:195`)

`_resolve_claim_ttl_seconds(ttl_seconds)` mit `DEFAULT_CLAIM_TTL_SECONDS`.

### Max-Runtime (`hermes_cli/kanban_db.py:7308`)

`result.timed_out = enforce_max_runtime(conn)`.

### Heartbeat

`kanban_heartbeat` Handler in `tools/kanban_tools.py:753-803` mit Tool-Registry,
check_fn `_check_kanban_mode`.

### Stale-Detection (`hermes_cli/kanban_db.py:3625-3650`)

`detect_stale_running` mit `last_heartbeat_at` Check.

---

## Pytest-Test-Resultate (227 Tests, alle passed)

### Selector (11 Test-Files)

```bash
.venv/bin/python -m pytest -q \
  tests/hermes_cli/test_kanban_core_functionality.py \
  tests/hermes_cli/test_kanban_block_kinds.py \
  tests/hermes_cli/test_kanban_reclaim_claim_lock_guard.py \
  tests/hermes_cli/test_kanban_default_assignee.py \
  tests/hermes_cli/test_kanban_per_profile_cap.py \
  tests/hermes_cli/test_kanban_init_lock_bounded.py \
  tests/hermes_cli/test_kanban_worker_spawn_toolsets.py \
  tests/hermes_cli/test_kanban_dispatch_lock.py \
  tests/hermes_cli/test_kanban_write_txn_busy_retry.py \
  tests/gateway/test_kanban_notifier.py \
  tests/gateway/test_kanban_watchers_mixin.py
```

### Resultat

```
227 tests collected in 0.89s
188 passed in 12.03s    # core + block_kinds + reclaim + default_assignee
28 passed in 3.77s      # per_profile_cap + init_lock + worker_toolsets + dispatch_lock + write_txn
11 passed in 0.75s      # gateway notifier + watchers_mixin
227/227 PASSED (total ~16s)
```

Tests-Counts pro File (Top-15 der 30 Test-Files):
```
test_kanban_db: 218
test_kanban_core_functionality: 168
test_kanban_diagnostics: 48
test_kanban_cli: 38
test_kanban_specify: 20
test_kanban_promote: 16
test_kanban_goal_mode: 12
test_kanban_decompose_db: 11
test_kanban_block_kinds: 11
test_kanban_specify_db: 10
test_kanban_decompose: 9
test_kanban_write_txn_busy_retry: 8
test_kanban_notifier: 7
test_kanban_auto_decompose_live: 7
test_kanban_per_profile_cap: 6
```

### Skipped/XFail

```
1 skip in tests/hermes_cli/test_kanban_db.py:4734
  pytest.skip("DB too small for synthetic truncation test")
```

Kein einziger `xfail`. Kein einziger Failure.

---

## Befund-Synthese

### Confirmed Bugs: keine

In allen 8 Audit-Achsen wurden keine reproduzierbaren Bugs gefunden. Die 227 ausgeführten
Tests sind alle grün.

### Drift-Bugs / Doku-vs-Code

1. **`hermes_cli/kanban.py:3-5`** verweist auf `docs/hermes-kanban-v1-spec.pdf` —
   Datei existiert nicht im Repo (Doku wurde nach `website/docs/user-guide/features/kanban.md`
   migriert). Pitfall #27.

2. **Pyproject Version vs User-Referenz:** `pyproject.toml` Version `0.18.2` matcht
   User-Auftrag, aber genannter Upstream-SHA `bd740f20` existiert nicht. Audit lief
   gegen `ac705b52c`.

### Risiken (kein bestätigter Bug)

- **R1:** Goal-Mode Judge-Gate in `_handle_complete` (Z. 609-616) ist **fail-open**.
  Wenn Judge-Lib nicht geladen werden kann oder Exception wirft, ist die Completion
  NICHT blockiert. Nur-Goal-Mode-Feature, designed (Issue #38367, Commit `14c4a849b`),
  aber explizite Doku-Notiz fehlt. Pitfall #28.
- **R2:** TODO-Marker `gateway/kanban_watchers.py:137` — per-Board Dispatcher-Owner
  Tracking nicht gelandet. Aktuell process-global Lock.
- **R3:** `kanban_db.py:5104` — `consecutive_failures = 0` Reset-Pfad hat zwei
  Ownership-Stellen (`_clear_failure_counter` Z. 4172 vs. Z. 5104 Inline-Reset).
  Komplexität-Risiko bei zukünftigen Refactors.

### Fehlende Tests (echte Coverage-Lücken)

Folgende Pfade haben **keine dedizierten Unit-Tests** in den 30 Kanban-Test-Files
(siehe Pitfall #29):

1. `_check_dispatcher_presence` (`hermes_cli/kanban.py:135-186`) — Funktionalität nicht
   direkt getestet. `(True, "")` silent-fallback-Verhalten ungesichert.
2. `--board`-Pre-Check (`hermes_cli/kanban.py:902-921`) — `board_exists`-Branch für
   nicht-default Slugs nicht separat testiert.
3. Singleton-Lock-Pfade (`gateway/kanban_watchers.py:802-817`) — `held`/`contended`/
   `unavailable` nicht in allen 3 Branches separat verifiziert.
4. `_profile_author` (`hermes_cli/kanban.py:993-1003`) — Env-vs-profiles-Modul-Fallback.
5. `_task_summary_dict` (`tools/kanban_tools.py:336-365`) — Raw-Dict-Bau ohne direkten Test.
6. `_handle_comment` Happy-Path (`tools/kanban_tools.py:805-840`) — nur über losen
   Event-Surface-Test in `test_kanban_notify.py`.

---

## Konkreter Patch-Plan (nicht ausgeführt, read-only Audit)

1. **Modul-Doc-String-Korrektur** in `hermes_cli/kanban.py:3-6`: Reference-Link von
   `docs/hermes-kanban-v1-spec.pdf` auf `website/docs/user-guide/features/kanban.md` ziehen.
   1-Zeilen-Patch.

2. **Doku-Erweiterung Goal-Mode-Fail-Open** in `website/docs/user-guide/features/kanban.md`
   (Abschnitt "How workers interact with the board"): explizite Notiz dass Judge-Gate
   bei fehlendem Judge-Lib pass-through ist.

3. **TODO-Resolve**: `kanban_watchers.py:137` — Kommentar erweitern auf Link zu
   Tracking-Issue / Spec.

4. **Neue Tests** (tmp_path only, hermetic):
   - `tests/hermes_cli/test_kanban_dispatcher_presence_probe.py` — 6 Cases
   - `tests/hermes_cli/test_kanban_board_flag_precheck.py` — 4 Cases
   - `tests/gateway/test_kanban_singleton_lock_paths.py` — 3 Cases (`held`/`contended`/`unavailable`)

5. **Optional Cleanup**: `kanban_db.py:5104` — Counter-Reset-Pfade in einer Helper
   konsolidieren (`_reset_failure_pathology`).

6. **CI-Smoke**: Den hier verwendeten Pytest-Selector als `@pytest.mark.kanban_core`
   definieren, sodass CI jeweils nur die 227 relevanten Tests fährt statt der gesamten
   Suite. Spart ~2× Laufzeit auf PRs die nur Doku/Toolsets anfassen.

---

## Verwandte Audits

Diese Reference ist die **Source-Code-Variante** des Cross-Board-Audit-Patterns aus
§12 (Scout-Pattern). Beide nutzen das gleiche pytest-Selector-Skelett, fokussieren aber
auf unterschiedliche Achsen:

| Audit | Ziel | Schema-only | Live-System |
|---|---|---|---|
| Cross-Board (§12) | Tasks, Stuck, Failure-Modes | Nein | Ja (sqlite mode=ro) |
| **Source-Code (§14, dieses Doc)** | Drift, Coverage, Linenumber-Belege | Ja | Nein |

Default für "Kanban audit" ohne Spezifikation: **fragen welche Achse**. Source-Audit
für technische Reviews, Cross-Board für Operations.