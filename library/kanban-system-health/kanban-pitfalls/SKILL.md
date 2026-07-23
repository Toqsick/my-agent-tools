---
name: kanban-pitfalls
title: "Kanban Pitfalls — 14+ Lessons + Hermes-v2-Betrieb"
description: "Use when a Kanban operation hits a known pitfall: CLI flags wrong, config drift, profile-description missing, board-scoping issues, security findings, source-code implementation drifts, dispatcher lock contention. NOT for first-time setup (use kanban-phases) or live diagnosis (use kanban-diagnostics). Index of failure modes with fixes."
category: kanban-system-health
version: '3.0'
created: '2026-07-23'
author: Yuno (split from kanban-system-health v2.5)
lane: koenigin
agent: universal
trigger_keywords: ['kanban', 'pitfall', 'cli', 'config-drift', 'profile-description', 'board-scoping', 'security', 'source-code-drift', 'dispatcher-lock', 'hermes-v2']
keywords: ['kanban', 'pitfall', 'cli', 'config', 'profile', 'security', 'source-code', 'dispatcher', 'hermes-v2']
related_skills: ['kanban-diagnostics', 'kanban-phases', 'kanban-audit', 'delegation-anti-patterns']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from kanban-system-health 2026-07-23)'

license: MIT
---

# Kanban Pitfalls — 14+ Lessons + Hermes-v2-Betrieb

Kanban Pitfalls — 14+ Lessons + Hermes-v2-Betrieb

_Extracted from kanban-system-health v2.5 on 2026-07-23._

## 10. Pitfalls — 14 Lessons aus 2026-07-09 Sessions


### CLI-Pitfalls

1. **Stille Spawn-Skips:** Dispatcher silent skippt unbekannte Assignees → Karte bleibt in `ready`. Mitigation: `--assignee` IMMER setzen.
2. **Standalone-Daemon deprecated:** `hermes kanban daemon` läuft seit 2026-07-02 nicht mehr standalone — embedded im Gateway.
3. **`hermes kanban edit` nur für done-Tasks:** Für ready/blocked Tasks → `reassign` oder recreate (alle anderen Felder sind nicht editierbar).
4. **`hermes kanban block <id> <kind> <reason>`:** kind ist **POSITIONAL**, nicht `--kind` Flag!
5. **`hermes kanban archive` ohne `--reason`:** Grund muss vorher als Comment angelegt werden.

### Config-Pitfalls

**Pitfall #6:** Für `notification_sources: ['*']` MUSS direkt in `~/.hermes/config.yaml` editiert werden, sonst ist es `'["*"]'` (String, nicht Liste).

**Pitfall #17 — Worker-Toolset-Resolution-Drift [GELÖST 2026-07-20, H-07-Drift-Guard] (gefunden 2026-07-11, kvo-orchestrator Audit):** Profile-`config.yaml` hat zwei Schreiborte für Toolsets: top-level `toolsets` (historisch) und `platform_toolsets.cli` (was der Dispatcher via `_resolve_worker_cli_toolsets` → `_get_platform_tools(cfg, "cli")` seit den kanban_db-Änderungen tatsächlich liest). Generatoren / Setup-Scripts die NUR `cfg["toolsets"] = ...` setzen, spawnen Worker mit falscher oder leerer Tool-Liste. Pflicht-Setup für Kanban-Worker-Profile: **beide Keys** synchron setzen, plus Assertion beim Write-Back. Verifiziert 2026-07-11 auf `yuno-coder` (löst 17 Toolsets auf, obwohl Top-Level nur `[hermes-cli, web]` sagt) und `yuno` (9 Toolsets). Volle Live-Evidenz + Reproduktion: `references/kanban-worker-toolset-and-json-drift.md`.

> **✅ Gelöst (H-07, 2026-07-20):** Der Drift wird jetzt von `~/.hermes/scripts/check_toolset_drift.py`
> abgefangen. Das Skript lädt den **echten** Resolver (`hermes_cli.tools_config._get_platform_tools`)
> und prüft für die Haupt-Config **und jede Profil-Config**, was für die Plattform `cli` aufgelöst wird
> — also exakt das, was der Kanban-Dispatcher Workern gibt. **Exit 1** wenn eine Config **0** CLI-Toolsets
> auflöst (tool-loser Worker = der Vorfall). **Warnung/Exit 0** wenn ein Profil nur top-level `toolsets:`
> ohne `platform_toolsets:` definiert (funktioniert über den hermes-cli-Fallback, ist aber drift-anfällig).
> Läuft nächtlich als Teil der H-34-Diagnostics (`kanban-diagnostics-cron.sh`); letzter Lauf
> „0 Fehler, 3 Warnungen, 6 Configs". Manuell:
> `~/.hermes/hermes-agent/venv/bin/python3 ~/.hermes/scripts/check_toolset_drift.py`.
> Die Pflicht bleibt: bei neuen Worker-Profilen **beide** Keys synchron setzen — der Guard ist das
> Sicherheitsnetz, nicht die Ausrede.

**Pitfall #18 — `kanban list --json` vs `kanban show --json` Shape-Drift (gefunden 2026-07-11):** `list --json` liefert flache Task-Felder (`status, assignee, started_at, completed_at, ...`) — **keine** `heartbeat_at`, `max_runtime_s`, `retries`. `show <id> --json` liefert `{task, runs, events, latest_summary, parents, children}`. Jeder Monitor der `list` enriched, indem er aus `show` Keys direkt rüberkopiert, bekommt `None` für alles was STUCK / OVERTIME / FLAPPING-Detection braucht. Korrekt: Run-Felder aus `runs[-1]` ziehen (`last_heartbeat_at` → `heartbeat_at`, `max_runtime_seconds` → `max_runtime_s`, `len(runs)-1` → `retries`). Verifiziert gegen `t_e2d1fb50` (zwei Runs: `crashed` rc=0 protocol-violation, dann `completed`). Volle Schema-Tabelle + Fix-Pattern: `references/kanban-worker-toolset-and-json-drift.md`.

**Pitfall #19 — `hermes kanban stats` ist Board-scoped, NICHT Tenant-scoped (gefunden 2026-07-11):** Es gibt kein `--tenant`-Flag. README / SMOKE-RUNBOOK von Drittanbieter-Skills die das behaupten lügen. Tenant-spezifische Stats: `kanban list --tenant <slug> --json` plus eigener `monitor.py`, oder Board-weit via `kanban stats`.
7. **Plugin enabled ≠ config da:** `dashboard_auth/basic` muss in `plugins.enabled: [dashboard_auth/basic]` sein, sonst greift die Config nicht.
8. **`hermes config set` blocked security-sensitive:** `~/.hermes/config.yaml` ist security-protected → nicht direkt patch-bar, nur via `hermes config set` oder `hermes config edit`.

### Skill-Profile-Pitfalls

9. **Per-Profile Skill-Lookup:** Skills werden PRO PROFILE gesucht, nicht global. `yuno-coder` hat 17 Kategorien, `yuno` hat 129. Vor Assignierung: `find ~/.hermes/profiles/<ziel>/skills -name "*<skill>*"`.
10. **Profile-Status `stopped` ≠ Spawn-Blocker:** Indikator nur, kein Blocker. On-demand-Spawn funktioniert.
11. **Worktree-Board-Default-Workdir:** MUSS in Git-Repo sein. `~/10-Projekte/10-active` ist Multi-Repo-Ordner und funktioniert NICHT — spezifisches Repo wie `~/10-Projekte/10-active/greyhack-tools` angeben.
12. **default-Profile hat 0 Skills:** NIEMALS als Worker nutzen.

### Datenbank-Pitfalls

13. **Pro-Board DB:** `kanban.db` unter `~/.hermes/kanban.db` ist nur das default-Board. Andere Boards haben separate DBs unter `~/.hermes/kanban/boards/<slug>/kanban.db`. Globale SQL-Queries sehen nur das default-Board!
14. **`kanban_db.create_task(conn, ...)`, NICHT `create_task(db_path=...)`:** Nimmt sqlite3.Connection-Objekt. Attachment-Funktionen ähnlich: `attachments_root(board=...)` OHNE conn-Arg.
15. **`create_task` defaultet auf `ready`, nicht `todo`:** Bei `priority >= 1` setzt der Wrapper den Status auf `ready`. Für Test-Setup: `priority=0` oder `## Ready` im Test erwarten. (Verifiziert 2026-07-09 Sync-Engine-Roundtrip.)

### Security-Pitfalls (P0)

16. **Live-Tokens NIEMALS in config.yaml:** Nur in `.env` mit `chmod 600`. config.yaml wird gesichert, geteilt, committed — `.env` nicht.

### Board-Scoping-Pitfalls

20. **`hermes kanban show/list` ist Board-scoped mit optionalem `--board`-Flag:** Seit v0.18.2 existiert ein globaler `--board <slug>` Flag der `show`, `list`, `diagnostics`, `stats`, `runs`, `assignees` und `boards` akzeptiert — `hermes kanban --board hermes list` funktioniert ohne vorheriges `boards switch`. Allerdings hat `--board` KEINEN Effekt auf `boards list` selbst (zeigt immer alle Boards), und Task-IDs von anderen Boards geben `"no such task"` ohne Hinweis auf den korrekten Board. **Korrigiert** die ursprüngliche Scout-A-Aussage "KEIN `--board`-Flag" vom 2026-07-11. Cross-Board-Audit ist trotzdem sauberer via Loop + `boards switch`, weil `diagnostics --json` dann pro Board eigenständige Objekte liefert statt eine globale Liste.

21. **Drei Failure Modes für blocked Tasks, nicht ein Sammelgrund:** Jeder blocked Task in `hermes kanban diagnostics` sieht gleich aus (`repeated_failures`), aber die Ursache ist eine von drei komplett verschiedenen Klassen: (A) Spawn/Environment-Crash (pid not alive) — Profil defekt oder ulimit; (B) Protocol Violation (rc=0 ohne kanban_complete) — Worker-Disziplin; (C) Iteration Budget Exhausted (80/80) — Scope zu groß. Jede Klasse braucht einen anderen Fix. Verifiziert 2026-07-11: 5× A, 2× B, 3× C über alle Boards.

24. **Zombie-Run ohne Task-Zeile (Daten-Anomalie, gefunden 2026-07-13):** `task_runs` und `task_events` referenzieren via `task_id` eine ID, die in `tasks` NICHT existiert — möglich durch DELETE aus `tasks` ohne Cascade, oder Cross-Board-Spawn mit fehlendem Insert. Symptom: `task_runs.status='running'` mit `worker_pid` der nicht mehr lebt, aber `tasks`-Tabelle enthält die ID nicht. **Detection-Query:**
    ```sql
    SELECT te.task_id, te.kind, te.run_id FROM task_events te
    WHERE NOT EXISTS (SELECT 1 FROM tasks t WHERE t.id=te.task_id);
    ```
    **Hardline-Cleanup:** `UPDATE task_runs SET status='crashed', ended_at=strftime('%s','now'), outcome='orphan_zombie' WHERE task_id='t_xxx' AND status='running';` und analog für `task_events` (kein FK erzwungen, also manuell). Verifiziert 2026-07-13 gegen `t_ff13b7c7` im hermes-Board: 1 Zombie-Run + 4 orphan Events + PID 116705 nicht mehr alive (Started 2026-07-09 18:01, jetzt +4 Tage ohne Heartbeat).

25. **Kanban-Timestamps sind SEKUNDEN, NICHT Millisekunden (gefunden 2026-07-13):** Das Schema-Doku sagt nichts explizit, aber die Werte (z. B. `1783620113` = 2026-07-09 18:01:53 UTC) sind klassische Unix-Epoch-Sekunden. Wer SQL-Queries mit `strftime('%s','now')*1000 - last_heartbeat_at > 1800000` schreibt, bekommt IMMER negative Ergebnisse oder Overflows (Multi-Tages-Werte in "ms"). **Korrekt:**
    ```sql
    -- Sekunden-Differenz (richtig):
    strftime('%s','now') - last_heartbeat_at AS sec_since_hb
    -- 30-Min-Schwelle:
    WHERE strftime('%s','now') - last_heartbeat_at > 1800
    -- Human-readable:
    datetime(created_at, 'unixepoch') AS created_human
    ```
    Symptom der Verwechslung: `hb_age_ms = 1782159694885` ≈ 56 Jahre → das ist offensichtlich Müll und das ganze Audit-Ergebnis damit unglaubwürdig. **Verifizierung beim ersten Audit-Query:** `SELECT datetime(MIN(created_at),'unixepoch') FROM tasks` MUSS ein realistisches Datum (2026) liefern, nicht 1970 oder 2096.

26. **`task_runs.status` Schema-Drift: `done` vs `completed` (gefunden 2026-07-13):** In hermes/routing-lanes-Boards werden BEIDE Werte parallel geschrieben (`done` UND `completed` für erfolgreiche Runs). Filter-Querien wie `WHERE r.status IN ('done','completed')` müssen beide matchen — wer nur einen Wert filtert, halbiert seine Completion-Statistik. Andere Status-Werte (`crashed`, `timed_out`, `spawn_failed`, `gave_up`, `blocked`, `running`) sind konsistent. Wahrscheinlich historische Code-Pfade: älterer Kernel schreibt `done`, neuerer `completed` (oder umgekehrt). Cleanup wäre `UPDATE task_runs SET status='done' WHERE status='completed'` — aber **vorher dumpen** und nur in einem Wartungsfenster ausführen, weil Dashboard-Plugins brechen können, die explizit `status='completed'` matchen.

### Source-Code Implementation Drifts (Pitfalls #27-29, gefunden 2026-07-13 Source-Audit)

30. **`gateway_state.json` ist persistent-stale (gefunden 2026-07-13, Scout A):** Datei speichert `pid=61409 gateway_state=running`, aber PID ist seit Tagen tot. `_check_dispatcher_presence()` (kanban.py:135-186) liest den Wert und liefert Silent-OK → `hermes kanban create` warnt nicht, obwohl der Dispatcher in Wirklichkeit tot ist. Empfohlene Härtung (upstream): `kill -0 $pid 2>/dev/null` als zusätzlicher Gate. Workaround bis dahin: `jq '.pid=null | .gateway_state="stopped"' ~/.hermes/gateway_state.json > tmp && mv tmp ~/.hermes/gateway_state.json`.

31. **`~/.clean_shutdown` Marker-Bug (gefunden 2026-07-13, Scout A):** Boot-Logik behauptet „previous gateway exited cleanly", `~/.clean_shutdown` ist aber 0 Bytes → `container_boot` führt Cleanup-Code nicht aus. Round-Trip-Test fehlt. Symptom: Session-Resume wird nicht angeboten, obwohl der Marker sagt „clean".

32. **SQLite Foreign-Key-Constraints fehlen (gefunden 2026-07-13, Scout B):** Schema-Doku erwähnt FKs, Code (`kanban_db.py:5472-5501`) löscht manuell in Cascade-Reihenfolge. Edge-Case (Cross-Board-Spawn ohne Insert, oder DELETE ohne Cascade) produziert 8 orphan Rows (`task_runs`/`task_events` ohne Task-Zeile), verteilt auf hermes + routing-lanes. SQL-FK `task_id REFERENCES tasks(id) ON DELETE CASCADE` würde das strukturell verhindern. Verifiziert gegen `t_ff13b7c7` (Zombie-Run, 4 Tage alt), `t_52ee599e`, `t_69b64cc4` und 4 weitere.

28. **Goal-Mode Judge-Gate ist fail-open, kein hartes Protocol-Complete-Enforcement (gefunden 2026-07-13):** Source-Audit zeigt: Es gibt KEIN `protocol_complete` / `protocol_block` Token im Code (außer einem Kommentar in `detect_crashed_workers` Z. 7292). Der Goal-Mode-Judge in `_handle_complete` (`tools/kanban_tools.py:601-624`) und `_handle_block` (Z. 698-707, Issue #38696) **failt open** wenn Judge-Lib nicht ladbar oder Exception (Z. 609-616). Für nicht-Goal-Mode-Tasks ist `kanban_complete` **nicht** hart gegated — einziger harter Pre-Mutation-Barr in `complete_task` ist `HallucinatedCardsError` (Z. 4046), aber der greift nur wenn Worker `created_cards=...` deklariert. Wer in Audit-Outputs "protocol_complete enforced" behauptet, lügt. Realität: atomic CAS (`status IN (running, ready, blocked)`) + Hallucinated-Cards Gate + Reclaim/Timeout-Recovery sind die einzigen Hürden für Standard-Tasks.

29. **Test-Coverage-Lücken in `hermes_cli/kanban.py` und `gateway/kanban_watchers.py` (gefunden 2026-07-13):** Folgende Code-Pfade haben KEINE dedizierten Unit-Tests in den 30 Kanban-Test-Files: `_check_dispatcher_presence` (Z. 135-186), `--board`-Pre-Check-Branches (Z. 902-921 für `board_exists`-Failure-Pfad), Singleton-Lock-Branches `held`/`contended`/`unavailable` in `gateway/kanban_watchers.py:802-817` (nur happy-path via `test_kanban_watchers_mixin.py`), `_profile_author` (Z. 993-1003), `_task_summary_dict` (Z. 336-365), `_handle_comment` Happy-Path. Symptom: Refactors dieser Pfade brechen stillschweigend ohne Test-Signal. Mitigation: vor jedem PR der diese Funktionen anfässt, 6-Case-Test mit `tmp_path` und Stub-`gateway.status.get_running_pid` nachziehen (siehe `references/kanban-implementation-source-audit-2026-07-13.md` für konkretes Test-Skelett).

### Dispatcher & Lock-Pitfalls

22. **Advisory Dispatcher-Lock korrekt prüfen (korrigiert 2026-07-13):** `.dispatcher.lock` ist nur der persistente Inode für einen OS-Advisory-Lock (`fcntl`/`msvcrt`). **Dateigröße 0 und altes mtime sind normal und beweisen gar nichts**; beim Gateway-Stop wird der Lock freigegeben, die Datei aber absichtlich nicht gelöscht. Der frühere 2026-07-11-Befund „0 Byte + mtime >5 min = Dispatcher tot“ war ein False Positive. Korrekt ist ein non-blocking Lock-Probe:
    ```bash
    python3 - <<'PY'
    import fcntl
    p = '/home/bratan/.hermes/kanban/.dispatcher.lock'
    f = open(p, 'a+')
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('LOCK_CONTENDED: ein Dispatcher hält den Lock')
    else:
        print('LOCK_FREE: kein Dispatcher hält den Lock')
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    finally:
        f.close()
    PY
    ```
    `LOCK_CONTENDED` bestätigt nur einen Lock-Halter, nicht automatisch gesunde Ticks. Mit Gateway-Service/PID und Logs korrelieren. `LOCK_FREE` bei `dispatch_in_gateway: true` bestätigt, dass aktuell kein embedded Dispatcher den Singleton-Lock hält.

23. **Embedded-Dispatcher-Death (Gateway down = kein Dispatch):** Der Dispatcher ist seit 2026-07-02 im Gateway embedded. Das ist platzsparend, aber: **Gateway down = Dispatcher down = ready-Tasks akkumulieren sich ungesehen.** Der Cron-Ticker (separate Loop) heartbeatet weiter und täuscht „alles läuft“ vor. **Diagnose-Kette (verifiziert 2026-07-13, Scout A):**
    1. `systemctl --user status hermes-gateway.service --no-pager` (zeigt MainPID, NRestarts, ActiveEnterTimestamp)
    2. `systemctl --user list-unit-files hermes-gateway.service` (zeigt ob Unit im Index)
    3. `pgrep -af 'hermes_cli.main gateway run'`
    4. `python3` non-blocking `flock`-Probe (siehe Pitfall #22)
    5. `~/.hermes/gateway_state.json` (Achtung: stale möglich, immer `kill -0 $pid` mitprüfen)
    6. `journalctl --user -u hermes-gateway.service -n 50 | grep -i dispatch`

    **Neuer Befund 2026-07-13 (Scout A):** Die Unit-Datei `/etc/systemd/system/hermes-gateway.service` existiert physisch, ist aber `list-unit-files` als **not-found** gelistet — Ursache ist meist fehlender `daemon-reload` nach Unit-Änderung. Folge: `enable`/`start` greift erst nach `systemctl --user daemon-reload`. Kein Auto-Recovery-Mechanismus eingebaut.

    **Zweiter neuer Befund:** Boot-Log behauptet „previous gateway exited cleanly", `~/.clean_shutdown` ist aber leer → Logik-Bug im `container_boot`-Pfad. Cleanup-Code wird beim nächsten Start nicht ausgeführt. Round-Trip-Test (write marker → restart → check log → check marker) fehlt.

    **Recovery-Rezept:**
    ```bash
    systemctl --user daemon-reload
    systemctl --user enable --now hermes-gateway.service
    sleep 3
    # Verify:
    systemctl --user is-active hermes-gateway.service  # → active
    pgrep -af 'hermes_cli.main gateway run'             # PID sichtbar
    journalctl --user -u hermes-gateway -n 20 | grep -i "kanban dispatcher: holding singleton dispatcher lock"
    # Hardening für künftige Stops (optional in Unit-Datei ergänzen):
    #   Restart=on-failure RestartSec=10 StartLimitIntervalSec=300
    ```

30. **Test-Fixture-Leakage via Singleton + `sys.modules`-Reimport (gefunden 2026-07-13):** `PluginManager` ist ein Modul-Singleton (`hermes_cli.plugins.get_plugin_manager`). Tests, die `mgr._hooks` direkt patchen und via `mgr._hooks = saved` restaurieren, brechen wenn ein anderer Test dazwischen `discover_and_load(force=True)` aufruft — das macht `self._hooks.clear()`, und der gemerkte `saved`-Dict zeigt nicht mehr auf den aktiven Singleton-State. **Härtere Variante (gefunden 2026-07-13, `test_kanban_default_assignee.py`):** Die Fixture `isolated_kanban_home` löscht `hermes_cli.plugins` komplett aus `sys.modules` (`for mod in list(sys.modules): if mod.startswith("hermes_cli"): del sys.modules[mod]`), um einen frischen `HERMES_HOME` zu greifen. Das **orphant das alte `_plugin_manager`-Global komplett**, und Tests die oben im Modul `from hermes_cli.plugins import get_plugin_manager` machen, schreiben auf einen toten Dict. Folge: Capture-Hooks werden nie aufgerufen, Lifecycle-Hook-Tests scheitern selektiv im Full-Run, sind aber **allein grün**. **Symptom:** Tests grün isoliert, mehrere rot im Full-Run, alle nach demselben Muster „Hook wurde nicht gefeuert" / `assert 0 == 1`. **Reproduktion (binär):**
    ```bash
    # Identifiziere das verursachende File:
    pytest -q path/to/suspect.py tests/hermes_cli/test_kanban_lifecycle_hooks.py 2>&1 | tail -5
    pytest -q tests/hermes_cli/test_kanban_lifecycle_hooks.py path/to/suspect.py 2>&1 | tail -5
    # → nur eine Reihenfolge rot = Test-Ordering-Beweis
    ```
    **Fix-Pattern (3 Ebenen, kombiniert):**
    1. **Runtime-Resolver:** Statt `from hermes_cli.plugins import get_plugin_manager` (oben im Modul) → `def _live_plugin_manager(): return importlib.import_module("hermes_cli.plugins").get_plugin_manager()` und in der Fixture `_live_plugin_manager()` aufrufen. Damit greift jeder Test den **aktuellen** Singleton nach `sys.modules`-Reimport.
    2. **Defensive Restore:** Statt `mgr._hooks = saved` (Rebind orphaned) → `current = mgr._hooks; current.clear(); current.update(saved)`. Damit wird der LIVE-Singleton-State wiederhergestellt, nicht ein veralteter Snapshot.
    3. **Sys-Modules-Taboo:** Andere Fixtures (`isolated_kanban_home`) sollen `sys.modules` nicht wahllos löschen. Lieber `monkeypatch.setattr(...)` für targeted overrides.
    **Verifiziert 2026-07-13:** `test_kanban_lifecycle_hooks.py` nach Fix — 6 passed in 0.32s (allein), 12 passed in 0.68s (mit `test_kanban_default_assignee.py` Pair).

31. **„Standstill" ≠ Bug (Präzisierung 2026-07-13):** Ein System mit `running=0, ready=0, last_done>48h` kann **völlig gesund** sein, wenn `dispatch_in_gateway: true` + Gateway-Service inaktiv sind — dann ist „Standstill" der geplante Default-Zustand (Cron-only Modus), nicht der Hinweis auf einen kaputten Dispatcher. Frühere Standstill-Detection (§12.2 Step 5) hat das vermischt. **Korrigierte Heuristik:** „Standstill MIT ready-Tasks" (Hypothese 1 = Spawn-Skip) ist ein Bug. „Standstill OHNE ready-Tasks UND OHNE laufenden Dispatcher" ist normal, wenn Service disabled oder Cron-only gewollt. Vor jedem Re-Aktivierungs-Vorschlag: `hermes kanban list --status ready` pro Board prüfen UND `systemctl --user is-active hermes-gateway.service` — wenn ready=0 UND Service inactive, **ist nichts kaputt**. Wenn ready>0 UND Service inactive, ist's tatsächlich Pitfall #23 (Embedded-Dispatcher-Death). Wenn ready>0 UND Service active UND keine Worker-PIDs → Pitfall #1 (unassigned) oder Pitfall #2 (Skill-Lookup-Mismatch).

32. **`notify-subscribe`/`unsubscribe` Subcommands für Cross-Profile Notifications (Stand 2026-07-13):** Die CLI-Subcommands `notify-subscribe`, `notify-list`, `notify-unsubscribe` arbeiten **Board-scoped** wie die anderen `kanban`-Subcommands und akzeptieren keinen `--board`-Flag im Body; sie folgen dem aktiven Board (`HERMES_KANBAN_BOARD` oder `boards switch`). Wer pro-Board Notifications bulk managen will, braucht eine Loop mit `boards switch`. `notification_sources: ['*']` (Pitfall #6) muss weiterhin direkt in `~/.hermes/config.yaml` editiert werden, weil `hermes config set` Listen als String serialisiert — der `notify-subscribe`-Mechanismus ist **anders** (per-Task Subscriptions), nicht mit `notification_sources` zu verwechseln.

33. **`hermes-gateway.service` Unit-Datei existiert, aber systemd kennt sie nicht (gefunden 2026-07-13):** Die Unit-Datei `/etc/systemd/system/hermes-gateway.service` existiert physisch (z.B. nach `hermes setup` oder manuellem Edit), aber `systemctl --user list-unit-files hermes-gateway.service` listet sie als **`not-found`** (statt `disabled` oder `inactive`). Folge: `enable`/`start` greift erst nach `systemctl --user daemon-reload`. Symptom: User sagt „die Unit ist da, warum startet sie nicht?" und landet in einer Debug-Sackgasse weil `systemctl is-active` nichts zeigt. **Vollständige Diagnose-Kette (alle 4 Checks, nicht nur einen):**
    ```bash
    # 1. Unit-Datei physisch da?
    ls -la /etc/systemd/system/hermes-gateway.service
    # 2. Im systemd-Index?  (leer = not-found)
    systemctl --user list-unit-files hermes-gateway.service
    # 3. Service-Status (NOT-FOUND vs UNKNOWN vs INACTIVE)
    systemctl --user status hermes-gateway.service --no-pager
    # 4. MainPID + ActiveEnterTimestamp
    systemctl --user show hermes-gateway.service --property=MainPID,ActiveEnterTimestamp,SubState
    ```
    **Fix (3 Schritte, in dieser Reihenfolge):**
    ```bash
    systemctl --user daemon-reload                      # 1. zwingend zuerst
    systemctl --user enable --now hermes-gateway.service # 2. dann enable+start
    sleep 3
    systemctl --user is-active hermes-gateway.service   # 3. verify: → active
    pgrep -af 'hermes_cli.main gateway run'             # PID sichtbar?
    journalctl --user -u hermes-gateway -n 20 | grep -i "kanban dispatcher: holding singleton dispatcher lock"
    ```
    **Optional: Unit-Hardening** (in `/etc/systemd/system/hermes-gateway.service` ergänzen):
    ```ini
    [Service]
    Restart=on-failure
    RestartSec=10
    StartLimitIntervalSec=300
    ```
    Danach `daemon-reload && restart` — überlebt einzelnen SIGTERM automatisch statt komplett tot zu sein wie beim Vorfall 2026-07-13 03:19. **Verifiziert:** Diagnose-Kette reproduziert und Fix-Pfad in `kanban-correctness-audit-2026-07-13.md` §2.2 dokumentiert.

34. **`hermes`-CLI-Exitcodes sind IMMER 0 — NIE auf Returncodes verlassen (gefunden 2026-07-20, H-53, KRITISCH):** `hermes_cli/main.py:15290-15291` ruft `args.func(args)` auf und **verwirft den Rückgabewert**; die Subcommand-Funktionen returnen zwar sauber 0/1, aber `main()` fällt mit implizitem `return None` durch, und der Entrypoint ist ein **bloßer `main()`-Aufruf** (`main.py:15297`), kein `sys.exit(main())` → ein Subcommand, der Fehler per `return 1` (statt Exception) meldet, beendet den Prozess trotzdem mit Exitcode 0. **Konsequenz für jedes Skript/Cron:** kein `if hermes …; then`, kein `$?`-Check. Strukturierte Felder gibt es NUR bei `promote --json` / `promote --dry-run --json` (`hermes_cli/kanban.py:646-651`). Alle anderen Mutationen über **stdout-Textpräfixe** prüfen: `"Assigned…"` (`kanban.py:1685`), `"Comment added to…"` (`kanban.py:1910`), `"Completed…"` (`kanban.py:2045`). Separater Core-Fix-Task unterwegs (Chip `task_575d3b49`) — bis der upstream/hermes-v2-persistent ist, gilt die Regel unverändert (betrifft auch H-34/H-53/H-54).

35. **`source ~/.hermes/.env` ist seit H-04 kaputt — gezielte Zeilen-Extraktion pflicht (gefunden 2026-07-20):** Seit die Dashboard-Secrets externalisiert wurden, enthält `.env` `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH` mit einem **unquotierten bcrypt-Hash** (`$2b$…`). Ein `source`/`.` unter `set -u` interpretiert `$2b`/`$12` als Positionsparameter → **Abbruch**. Pflichtmuster für jedes Bash-Skript, das Credentials braucht (so machen es alle drei Cron-Wrapper): `grep -E "^KEY=" ~/.hermes/.env | tail -n1 | cut -d= -f2- || true` pro Key (`tail -n1` = letzte Definition gewinnt; `|| true` = kein Abbruch bei fehlendem Key). Nie `source`. **Nebenbefund:** `yuno-cleaner-cron.sh` nutzt noch das alte `source`-Muster und dürfte So 03:00 brechen (Chip `task_36e4e17f`). `TELEGRAM_CHAT_ID` existiert im `.env` nicht — nur `TELEGRAM_HOME_CHANNEL`.

36. **Board-Dispatch ist fail-closed — `dispatchable: false` ist kein Bug (P-71, 2026-07-20):** Seit dem Board-scoped Dispatch-Guard spawnt der Gateway-Dispatcher **nur** auf Boards mit Metadaten-Feld `dispatchable: true`; Default und jedes fehlende/malformte `board.json` → `false` (`kanban_db.board_is_dispatchable`, `hermes_cli/kanban_db.py:725`, Default `:660`). Ein Checklisten-/Planungs-Board wie `hermes-v2` mit `ready`-Tasks, die NICHT spawnen, ist damit **erwartetes, gesundes Verhalten** — nicht Pitfall #1 (unassigned) oder #23 (Dispatcher-Death). **Vor jedem „warum spawnt Board X nicht?"-Debug:** `hermes kanban boards list --json | grep -i dispatch` prüfen. Umschalten: `hermes kanban boards set-dispatch <slug> on|off` (`kanban.py:1247`). Nur reine Worker-/Coding-Boards je `on` (aktuell: `swarm-work`, `pr-review`). Gateway-Guards: `gateway/kanban_watchers.py:991/1039/1115/1179`. Vollständige Vorfall-Historie + Betrieb: siehe §15 und das OPS-RUNBOOK.

---

## 15. Hermes-v2-Betrieb (Konsolidierung 2026-07-20)


Ergänzt das Kern-Playbook um die hermes-v2-Änderungen. **Vollständiges Alltags-Runbook separat:**
`~/20-Workspace/results/h62-ops-runbook/OPS-RUNBOOK.md` (H-62). Alle `Datei:Zeile`-Angaben read-only
gegen den `hermes-v2-work`-Checkout verifiziert.

### 15.1 Update-Hazard — nach JEDEM `hermes update` (Standing Hazard)


`hermes update` setzt den Checkout **still von `hermes-v2-work` auf `main` zurück** und pullt Upstream —
damit verschwinden ALLE hermes-v2-Patches (Core-Patches H-10/H-11 **und der P-71-Dispatch-Guard**) aus
dem laufenden Gateway; ein ungeschützter Dispatcher kann wieder Worker-Stürme auslösen (§15.2, Vorfall 2).
Bleibt bestehen, bis die Patches upstream sind. **Pflicht nach jedem Update:**

```bash
git -C ~/.hermes/hermes-agent branch --show-current      # MUSS hermes-v2-work sein
### 15.2 P-71 Board-scoped Dispatch-Guard + die zwei Vorfälle


**Mechanik:** Per-Board-Feld `dispatchable` (Default **false**, fail-closed). Dispatcher spawnt nur auf
`true`-Boards, bevor `default_assignee`/`todo→ready`-Promotion greifen. Code: `board_is_dispatchable`
(`kanban_db.py:725`, Default `:660`), `write_board_metadata(dispatchable=)` (`:686/710`),
`dispatch_once(respect_dispatchable=)` (`:7551/7586`), 3 Gateway-Guards (`gateway/kanban_watchers.py:991/1039/1115/1179`),
CLI `hermes kanban boards set-dispatch <slug> on|off` (`kanban.py:306/1247`). Opt-in aktuell: `swarm-work`
(H-41) + `pr-review` (H-54); `hermes-v2` bleibt `false`.

**Vorfall 1 (2026-07-20 01:46–01:50):** Annahme „unassigned = kein Auto-Dispatch" war falsch —
`kanban.default_assignee: yuno` assigned ready-Tasks, der Dispatcher promotet `todo→ready` selbst → **22
Worker** auf dem Planungsboard gespawnt. Notbremse `dispatch_in_gateway: false`. Ein Worker „erledigte"
H-11 fälschlich (falscher Checkout) → delegation-anti-patterns #7.
**Vorfall 2 (2026-07-20 11:31–11:43, folgenlos):** `hermes update` → Checkout auf `main`, P-71-Guard weg,
Dispatcher spawnte 2×5 Worker. **Kein Schaden** (rein lesend; „crashed" = Kills durch die
systemd-Gateway-Neustarts des Updates). Recovery: Re-Rebase auf origin/main (0 Konflikte). → deshalb §15.1.

### 15.3 Cron-Trio H-34 / H-53 / H-54 (installiert + scharf, User-Crontab)


| Job | Kadenz | Wrapper (`~/50-System/bin/`) | Tut |
|---|---|---|---|
| H-34 Diagnostics | `15 3 * * *` | `kanban-diagnostics-cron.sh` | `kanban diagnostics --json` (aktives Board) + H-07-Drift-Guard → Telegram-Severity-Report |
| H-53 Review-Babysitter | `3,18,33,48 * * * *` | `review-babysitter-cron.sh` | treibt `coding-pipeline` durch `implement→spec/quality-review→fix→re-review`; Telegram nur bei Human-Gate/Fehler |
| H-54 PR-Watch | `7,37 * * * *` | `pr-review-watch-cron.sh` | pollt `Toqsick/{github-mcp-server,linux-assistant,greyscripts}` → Review-Task auf `pr-review` (`--skill code-review-checklist`) |

**Entwurfsentscheid User-Crontab (nicht Hermes-Cron):** ein Job, der Gateway-Probleme melden soll, darf
nicht am Gateway-Ticker hängen (Henne-Ei). Stärkstes Argument: H-53 (reine lokale SQLite-Ops). H-53-Boards
default `greyhack, routing-lanes, hermes-v2` (NICHT `swarm-work`). **Stoppen:** Crontab-Zeile raus;
Notfall `chmod -x <wrapper>`. Backups: `~/50-System/backups/crontab-backup-2026-07-20-pre-h3{4,53,54}.txt`.
**`.env`-Regel:** s. Pitfall #35. **Exitcode-Regel:** s. Pitfall #34.

### 15.4 Dispatcher-Instabilität (`pid not alive`)


Eigenständiger, ungeklärter Befund: Worker crashen beim Dispatch-Versuch mit `pid … not alive` (frischer
Beleg: `t_991a49c5` auf `hermes-v2`, Runs #142/#147). Häufigste harmlose Ursache: systemd-Gateway-Neustarts
killen laufende Worker (dann keine Code-Crashes). Klassifizieren via Failure-Modes A/B/C (Pitfall #21),
erst §15.1/§4.2 gegenprüfen (lebt Gateway/Dispatcher wirklich?). Watch-Item.

### 15.5 Kanban-UI: hermes-webui ist Single Source of Truth (H-30)


`hermes-webui` auf `127.0.0.1:8787` (user-systemd-Unit, aus `~/hermes-webui` →
`10-Projekte/40-archive/hermes-webui/`) ist die **einzige** Kanban-UI: `/api/kanban/*` + SSE, Backend des
Tailscale-Handy-Zugriffs. **Geparkt (nicht gelöscht, nicht weiterentwickelt):** das built-in
`web_dist`-Board-Dashboard und der Kanban-Teil von `yuno-dashboard`. **Archive-Cleanup-Verbot** für den
Archiv-Pfad, den Symlink und das Unit. Decision-Doc:
`~/.hermes/docus/reports/2026-07-20-kanban-ui-single-source.md`.

### 15.6 Coding-Pipeline (H-31)


Skill `coding-pipeline-orchestrator` (`~/.hermes/skills/software-development/coding-pipeline-orchestrator/`)
verkettet `implement→spec-review→quality-review→fix→re-review` mit Review-Gates. **Convention, kein
Engine:** `spawn_pipeline.py` legt nur das `blocked` Scaffold (Root + 5 Steps) mit Metadaten
`workflow_template_id='coding-pipeline'` + `current_step_key` an (`kanban_db.py:906-907`, Migration
`:1958-1963`); Verkettung via `--parent`/`--skill`. Das Durchtreiben übernimmt der H-53-Babysitter — es
gibt heute KEINE vollautomatische End-to-End-Loop. Reviewer-Verdikt via `hermes kanban comment` als genau
eine `VERDICT: APPROVE`/`VERDICT: REQUEST_CHANGES`-Zeile (Skill `code-review-checklist`, `--skill …`,
`kanban.py:348`).

### 15.7 Swarm v2 — Routing (H-41)


Version-controlled in `hermes_cli/swarm_routing.py`, aufgerufen vom Plugin-Shim `kimi-mode` **v0.3.0**.
Pfad: `decide_swarm_route` (`:166`, ab `worker_count ≥ swarm.kanban_backed_min_workers` Default 4 →
Kanban-Swarm statt v1-`delegate_task`-Fan-out) → `resolve_dispatch_board` (`:247`, P-71-safe) →
`route_and_materialize_swarm` (`:353`, Root→Worker→Verifier→Synthesizer auf `swarm-work`). Fail-safe:
fehlendes Modul/Exception → v1. Die **7 `swarm.*`-Keys** stehen als auskommentierter Block in
`~/.hermes/config.yaml` ab Z. 135 (Code-Defaults gelten ohne Eintrag):
`kanban_backed_min_workers` (4), `kanban_backed_min_runtime_seconds` (null), `kanban_board` (`swarm-work`),
`kanban_board_autocreate` (false), `kanban_verifier` (`reviewer`), `kanban_synthesizer` (`writer`),
`kanban_worker_profile` (`worker`).

---
