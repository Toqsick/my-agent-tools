# Read-Only Cross-Board Audit Recipe — 2026-07-13

**Zweck:** Diese Reference-Datei dokumentiert die Live-Daten + Methodik eines 73-Task Cross-Board Audits vom 2026-07-13, der **ausschließlich** mit read-only Tools (`sqlite3 file:?mode=ro` + `hermes kanban <read-only>`) ausgeführt wurde. Sie validiert die §12-Patterns und ist die empirische Grundlage für die Pitfalls #24, #25 und #26.

**Source:** Unabhängiger Audit-Auftrag ("Führe einen unabhängigen read-only Cross-Board Daten-, Lifecycle- und State-Machine-Correctness-Audit des Hermes Kanban durch"), 2026-07-13 13:48 CEST.

---

## Audit-Kontext

- **Epoch (UTC):** 1783943306 ≈ 2026-07-13 11:48 UTC
- **Aktives Board zu Beginn:** `hermes` (per `cat ~/.hermes/kanban/current`)
- **CLI-Version:** `Hermes Agent v0.18.2 (2026.7.7.2)` — wichtig: `--board` globaler Flag erst ab v0.18.x
- **Shell:** bash (Linux 6.8.0-134-lowlatency)
- **Letzte Completion über alle Boards:** 2026-07-09 ~10:40 UTC (≈ 98h Standstill)

## Boards-Inventar (6 aktive + 1 leere = 7 Boards)

| Board | Slug | Total | Done | Blocked | Todo | Ready | Running | Archived | Last-Done |
|---|---|---|---|---|---|---|---|---|---|
| Hermes V7 + Orchestrierung | `hermes` | 21 | 12 | 5 | 4 | 0 | 0 | 0 | 09:52 UTC |
| Yuno Dashboard | `dashboard` | 4 | 1 | 3 | 0 | 0 | 0 | 0 | 08:58 UTC |
| GreyHack Tools | `greyhack` | 6 | 2 | 4 | 0 | 0 | 0 | 0 | 09:39 UTC |
| System Fixes & Maintenance | `system` | 4 | 3 | 1 | 0 | 0 | 0 | 0 | 09:18 UTC |
| Voice Bot Pipeline | `voice` | 3 | 2 | 1 | 0 | 0 | 0 | 0 | 09:12 UTC |
| 3-Lane Routing Swarms | `routing-lanes` | 35 | 30 | 0 | 0 | 0 | 0 | 5 | 10:40 UTC |
| Default | `default` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | – |

**Total:** 73 Tasks · 50 done (68,5%) · 14 blocked · 4 todo · 0 ready · 0 running · 5 archived.

## Run-Lifecycle (`task_runs` Aggregat)

| Board | Runs | done | completed | crashed | timed_out | spawn_failed | gave_up | running |
|---|---|---|---|---|---|---|---|---|
| hermes | 27 | 11 | 4 | 10 | 0 | 0 | 0 | 1 |
| routing-lanes | 42 | 23 | 7 | 8 | 0 | 2 | 2 | 0 |
| greyhack | 12 | 2 | 0 | 2 | 2 | 1 | 2 | 0 |
| dashboard | 7 | 1 | 0 | 3 | 1 | 0 | 1 | 0 |
| voice | 8 | 2 | 0 | 4 | 1 | 0 | 0 | 0 |
| system | 6 | 3 | 0 | 2 | 0 | 0 | 0 | 0 |
| **Σ** | **102** | **42** | **11** | **29** | **4** | **3** | **5** | **1** |

**Crash-Rate global:** 29/102 = **28,4%** · **Schema-Drift:** `done` UND `completed` parallel genutzt → Filter müssen beide matchen (Pitfall #26).

---

## Pitfall #24 — Zombie-Run ohne Task-Zeile (das wichtigste Finding)

### Symptom

`task_runs` und `task_events` referenzieren via `task_id` eine ID, die in `tasks` NICHT existiert.

### Detection-Query

```sql
SELECT te.task_id, te.kind, te.run_id, datetime(te.created_at,'unixepoch') AS event_time
FROM task_events te
WHERE NOT EXISTS (SELECT 1 FROM tasks t WHERE t.id=te.task_id);
```

### Live-Befund (hermes-board)

```
task_id      | kind      | run_id | event_time
-------------+-----------+--------+--------------------
t_69b64cc4   | created   | (null) | 2026-07-09 18:00:56
t_ff13b7c7   | created   | (null) | 2026-07-09 18:00:56
t_ff13b7c7   | claimed   |     27 | 2026-07-09 18:01:53
t_ff13b7c7   | spawned   |     27 | 2026-07-09 18:01:53
t_ff13b7c7   | heartbeat |     27 | 2026-07-09 18:01:55
```

### Run-Details

```
task_id:    t_ff13b7c7
status:     running
profile:    yuno
started:    2026-07-09 18:01:53 (= 1783620113)
heartbeat:  2026-07-09 18:01:55 (= 1783620115)
worker_pid: 116705        → NICHT MEHR ALIVE (ps -p 116705 → "not alive")
claim_lock: bratan-17-P1:103565
max_runtime_seconds: 5400 (90 min)
```

### Globale Verifikation

`SELECT id FROM tasks WHERE id='t_ff13b7c7'` in **allen 7 Board-DBs** (default, dashboard, greyhack, hermes, routing-lanes, system, voice) = **0 Treffer**.

### Process-State

```
ps -p 116705 → "(PID 116705 not alive — process dead)"
ps -ef | grep -iE 'kanban|hermes.*worker|yuno' | grep -v grep
  → Nur slash_worker-Prozesse (TUI-Gateway-Workers), KEIN Kanban-Worker
  → KEIN laufender `hermes kanban dispatcher` (embedded im Gateway)
```

### Hardline-Cleanup (NICHT ausgeführt — read-only Audit)

```sql
-- Run-Status korrigieren:
UPDATE task_runs
SET status = 'crashed', ended_at = strftime('%s','now'), outcome = 'orphan_zombie'
WHERE task_id = 't_ff13b7c7' AND status = 'running';

-- Optional orphan-Events löschen (kein FK erzwungen):
DELETE FROM task_events
WHERE task_id = 't_ff13b7c7' AND task_id NOT IN (SELECT id FROM tasks);
```

**Hypothese:** Race zwischen `create_task` (INSERT INTO tasks) und `claim_task` (INSERT INTO task_runs + task_events). Möglich auch manuelles DELETE einer Task ohne Cascade-Cleanup. Das DB-Schema hat **keine Foreign-Key-Constraints zwischen tasks/task_runs/task_events**, daher werden Anomalien nicht durch die Engine erkannt.

---

## Pitfall #25 — Timestamps sind Sekunden, nicht Millisekunden

### Live-Beleg

```sql
SELECT datetime(MIN(created_at), 'unixepoch') FROM tasks;
-- → 2026-06-30 23:29:35  ✓ (realistisches Datum, also SEKUNDEN)

SELECT MAX(created_at), datetime(MAX(created_at),'unixepoch') FROM tasks;
-- → 1783589857 = 2026-07-09 09:37:37  ✓
```

### Falsche Variante (mixed s + ms)

```sql
-- FALSCH — liefert Overflow:
SELECT strftime('%s','now')*1000 - last_heartbeat_at AS hb_age_ms
FROM task_runs WHERE status='running' AND last_heartbeat_at IS NOT NULL;

-- Ergebnis: 1782159694885  (= 56 Jahre → offensichtlich Müll)
```

### Korrekte Variante

```sql
-- Sekunden-Differenz (richtig):
SELECT strftime('%s','now') - last_heartbeat_at AS sec_since_hb
FROM task_runs WHERE status='running' AND last_heartbeat_at IS NOT NULL;

-- 30-Min-Schwelle:
WHERE strftime('%s','now') - last_heartbeat_at > 1800
```

### Verifizierungs-Rezept (IMMER als erste Query im Audit)

```sql
-- Wenn das hier NICHT 2026-XX-XX zurückgibt, stimmt die Einheit nicht:
SELECT datetime(MIN(created_at),'unixepoch') FROM tasks;

-- Wenn das hier 1970 oder 2096 zeigt, ist die DB in ms:
SELECT datetime(MIN(created_at)/1000,'unixepoch') FROM tasks;
```

---

## Pitfall #26 — `task_runs.status` Schema-Drift `done` vs `completed`

### Live-Beleg

```sql
-- hermes-Board:
SELECT status, COUNT(*) FROM task_runs GROUP BY status;
-- done=11, completed=4, crashed=10, blocked=1, running=1

-- routing-lanes-Board:
SELECT status, COUNT(*) FROM task_runs GROUP BY status;
-- done=23, completed=7, crashed=8, spawn_failed=2, gave_up=2
```

### Filter-Falle

```sql
-- Verloren die Hälfte aller Erfolge:
SELECT COUNT(*) FROM task_runs WHERE status='done';
-- → 42 (alle Boards)

-- Komplett:
SELECT COUNT(*) FROM task_runs WHERE status IN ('done','completed');
-- → 53 (alle Boards)

-- Wer nur "done" filtert, sieht 21% weniger Success-Rate.
```

### Cleanup-Vorschlag (NICHT ausgeführt — read-only)

```sql
-- Backup vor jedem Cleanup:
.mode list
.output /tmp/task_runs_dump.txt
SELECT * FROM task_runs;
.output stdout

-- Migration (in Wartungsfenster):
UPDATE task_runs SET status='done' WHERE status='completed';

-- ⚠️ Dashboard-Plugins die explizit "completed" matchen brechen — vorher suchen:
grep -rn "status.*completed" ~/.hermes/ | grep -v ".git"
```

---

## Reproduzierbare Read-Only Checks (für CI / Smoke-Tests)

```bash
# 1) Schema-Integrität aller Board-DBs:
for slug in dashboard greyhack hermes routing-lanes system voice; do
  sqlite3 "file:/home/bratan/.hermes/kanban/boards/$slug/kanban.db?mode=ro" "PRAGMA quick_check;"
done

# 2) Orphan-Events / Comments / Links:
sqlite3 "file:.../hermes/kanban.db?mode=ro" "
SELECT 'orphan_events', COUNT(*) FROM task_events te
 WHERE NOT EXISTS (SELECT 1 FROM tasks t WHERE t.id=te.task_id);
SELECT 'orphan_comments', COUNT(*) FROM task_comments tc
 WHERE NOT EXISTS (SELECT 1 FROM tasks t WHERE t.id=tc.task_id);
SELECT 'orphan_links', COUNT(*) FROM task_links tl
 WHERE NOT EXISTS (SELECT 1 FROM tasks t WHERE t.id=tl.parent_id)
    OR NOT EXISTS (SELECT 1 FROM tasks t WHERE t.id=tl.child_id);"

# 3) Zombie-Runs (laufend + nicht-existierende Task-Zeile):
sqlite3 "file:.../hermes/kanban.db?mode=ro" "
SELECT r.id, r.task_id, r.status FROM task_runs r
 WHERE r.status='running' AND NOT EXISTS (SELECT 1 FROM tasks t WHERE t.id=r.task_id);"

# 4) Done-Tasks ohne erfolgreichen Run:
sqlite3 "file:.../hermes/kanban.db?mode=ro" "
SELECT id FROM tasks WHERE status='done' AND NOT EXISTS
 (SELECT 1 FROM task_runs r WHERE r.task_id=tasks.id AND r.status IN ('done','completed'));"

# 5) Crash-Rate letzte 50 Runs (in Prozent):
sqlite3 "file:.../hermes/kanban.db?mode=ro" "
SELECT 100.0 * SUM(CASE WHEN status IN ('crashed','timed_out','spawn_failed') THEN 1 ELSE 0 END) / COUNT(*)
 FROM (SELECT status FROM task_runs ORDER BY id DESC LIMIT 50);"

# 6) Stale-Heartbeat Detection (Sekunden-Differenz!):
sqlite3 "file:.../hermes/kanban.db?mode=ro" "
SELECT id, task_id, strftime('%s','now') - last_heartbeat_at AS sec_since_hb
FROM task_runs WHERE status='running' AND last_heartbeat_at IS NOT NULL
 AND strftime('%s','now') - last_heartbeat_at > 1800;"
```

---

## Methodik-Notizen

### 6 Boards × 2 Aggregat-Levels

Pro Board wurden zwei SQL-Blöcke gefahren:
1. **Aggregat:** Status-Counts, Assignee-Validität, Block-Kinds, Recurrences, Runs-Status, Orphan-Counts.
2. **Detailed:** BLOCKED_NO_KIND, HIGH_CONSEC_FAILURES, CRASHED_RUNS_BY_TASK, STALE_CLAIMS, OLDEST_BLOCKED_AGE, WORKSPACE_PATH_MISSING, DONE_RUN_MISMATCH, RUNNING_WITHOUT_ACTIVE_RUN, HEARTBEAT_DEAD_RUNNING, CLAIM_LOCK_BUT_NOT_RUNNING, TENANT_USAGE, SESSION_IDS.

### Call-Budget

11/15 Calls — innerhalb des Limits. Jeder Call kombinierte mehrere `sqlite3`-Statements via HEREDOC.

### Was NICHT ausgeführt wurde

- **Keine** `UPDATE`/`DELETE` Operationen.
- **Keine** `hermes kanban reassign/block/unblock/edit` Schreib-Befehle.
- **Keine** Modifikation von `~/.hermes/kanban/current` (active board blieb `hermes`).
- **Keine** Spawn / Kill von Worker-Prozessen.

### Verifikationskette am Ende

```
hermes v0.18.2
+ 6 Board-DBs (alle PRAGMA quick_check = ok)
+ default-DB (0 Tasks, schema valid)
+ 73 Tasks total (alle vorhanden in tasks-Tabelle der jeweiligen Boards)
+ 1 Zombie-Run (t_ff13b7c7) ohne Task-Zeile
+ 5 orphan task_events in hermes (alle für t_ff13b7c7)
+ 3 orphan task_events in routing-lanes (für t_52ee599e)
+ 0 orphan task_links
+ 0 orphan task_comments
```

---

## Failure-Mode-Triage (für §12.4 Report-Template)

| Mode | Anzahl global | Boards | Diagnose-Hinweis |
|---|---|---|---|
| Crash (pid not alive) | ≥ 9 (Cluster 146383-85) | hermes | Worktree-Spawn-Race oder venv-Lock-Issue |
| Protocol violation (rc=0) | 1 (t_f52972de) | hermes | Worker-Hook fehlt: `kanban_complete/block` nicht gerufen |
| Timeout | 6 | dashboard, greyhack, voice | `max_runtime_seconds` zu klein oder Heartbeat-Schleife hängt |
| Spawn failed | 3 | greyhack, routing-lanes | Dispatcher-Lock oder venv-Pfad |
| Gave_up | 5 | dashboard, greyhack, routing-lanes | Circuit-Breaker (failure_limit=2) ausgelöst |
| Zombie-Run | 1 (t_ff13b7c7) | hermes | Run existiert, Task nicht — Schema-Anomalie |

## Coverage-Health

| Metrik | Wert |
|---|---|
| Skills referenced in hermes | 4 (`null`=16, `system-documentation`=3, `requesting-code-review`=1, `humanizer`=1) |
| `model_override` benutzt | 0/21 (alle nutzen Profil-Default) |
| `project_id` als Anker gesetzt | 0/73 (alle laufen im Default-Worktree) |
| `block_kind` gesetzt (außer greyhack t_5e94e7e6) | 1/14 (≈7%) |
| `goal_mode=1` benutzt | 1/21 (4,8%) |

## Cross-Skill-Lessons

- **`kanban-system-health` §12.1 (Board-Scoping):** Der globale `--board` Flag macht Cross-Board-Audits ohne `boards switch`-Side-Effect möglich. Beide Methoden haben Vor-/Nachteile — dokumentiert in §12.1.
- **`kanban-system-health` §12.4 (Report-Template):** Diese Live-Audit-Outputs sind die zweite empirische Validierung des Templates nach Scout-A 2026-07-11.
- **DB-Correctness vs Dispatcher-Correctness:** DBs sind integer (`quick_check=ok` überall), aber der Dispatcher ist seit 98h idle. **DB-Integrität ≠ System-Gesundheit.** Ein separates Skill-Sub-Chapter für "DB-Integrity vs Dispatcher-Heartbeat" wäre eine Überlegung wert — derzeit implizit in Pitfall #22/#23.