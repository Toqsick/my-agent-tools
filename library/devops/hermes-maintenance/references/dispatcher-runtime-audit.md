# Kanban Dispatcher Runtime-Correctness Audit — Playbook

**Source:** Unabhängiger read-only-Audit 2026-07-13: „Führe einen unabhängigen read-only Kanban Runtime-/Dispatcher-Correctness-Audit durch. Entscheide beweisbar, ob Tasks aktuell automatisch dispatcht werden könnten und welche Single Points of Failure/False-Health-Signale existieren."

**Ergebnis:** Tasks werden NICHT automatisch dispatcht. Dispatcher embedded im Gateway-Prozess, dieser seit 2026-07-13 03:19:54 tot (SIGTERM), keine externe Auto-Start-Mechanik. Drei voneinander unabhängige Falschzustands-Signale (`gateway_state.json`-Zombie-PID, leerer `.clean_shutdown`, 0-Byte-`.dispatcher.lock`).

**Zweck dieses Dokuments:** Die im Audit entdeckten Anti-Patterns und ihre Verifikations-Ladder sind NICHT kanban-spezifisch — sie gelten für jede Runtime-Korrektheits-Audit-Aufgabe (Watchers, Cron-Worker, Discord/Telegram-Bots, Mnemosyne-Sleep, etc.). Dies ist ein generalisierter Audit-Playbook mit Kanban als konkretem Beispiel.

## 1. Die 5 False-Health-Signal-Klassen

### 1.1 Persisted-state ≠ live-state (der häufigste Fehler)

**Symptom:** Eine JSON/SQLite-State-Datei behauptet `running=true pid=12345`, aber der PID existiert nicht. Ursache: Der Persist-Schritt passiert beim SIGTERM (nicht beim Cleanup), und niemand korrigiert die Datei beim Boot wenn der alte PID weg ist.

**Verifikation:**
```bash
# 1. State-Datei lesen und PID extrahieren
PID=$(python3 -c "import json; print(json.load(open('/home/bratan/.hermes/gateway_state.json'))['pid'])")
# 2. Live-Probe — kill -0 liefert 0 wenn PID lebt, 1 wenn tot
kill -0 $PID 2>/dev/null && echo "PID $PID lebt" || echo "PID $PID TOT — State-Datei lügt"
# 3. ps-Cross-Check
ps -p $PID -o pid,user,etime,cmd 2>/dev/null || echo "Kein solcher Prozess"
```

**Fix-Optionen:**
- **A — Boot-Time-Sweeper:** Im Gateway-Boot einen Hook, der alle PIDs in `gateway_state.json` validiert und auf `running: false` zurücksetzt wenn `kill -0` fehlschlägt.
- **B — Heartbeat-basierte Self-Korrektur:** State-Datei mit `last_tick_at` (Unix-Sekunden) erweitern. Bei jedem Dispatcher-Tick aktualisieren. Beim Lesen: wenn `now - last_tick_at > 5× interval` → Status auf `stale` setzen, egal was der `running`-Flag sagt.
- **C — PID-File statt State-File:** Statt JSON-State mit PID den PID via `PIDFile=` in systemd oder expliziter `path.pid` schreiben — systemd-`Type=simple` erkennt den Prozess-Tod selbst und respawnt.

**Hermes-spezifische Stelle:** `hermes_cli/main.py:1098` liest `gateway_state` und trifft davon abhängige Entscheidungen (`if gateway_state == "running": ...`) — wenn der State lügt, ist die Entscheidung falsch.

### 1.2 `.clean_shutdown` Marker ohne Write-Path

**Symptom:** `~/.hermes/.clean_shutdown` ist 0 Bytes (leer) aber Boot-Log sagt `Previous gateway exited cleanly — skipping session suspension`. Ursache: Zwei verschiedene Code-Pfade — der eine schreibt den Marker, der andere liest ihn und fällt bei leerer Datei auf "skip" zurück.

**Verifikation:**
```bash
# Marker existiert? Größe > 0?
stat -c '%s %y %n' /home/bratan/.hermes/.clean_shutdown
# Suche im Log nach der Behauptung
grep -E 'Previous gateway exited cleanly|skipping session' ~/.hermes/logs/gateway.log | tail -5
# Suche im Source nach den beiden Pfaden
grep -nE 'clean_shutdown|exited cleanly' ~/.hermes/hermes-agent/hermes_cli/main.py | head -10
```

**Fix-Optionen:**
- Boot-Logik muss `stat -c '%s' .clean_shutdown > 0` prüfen BEVOR sie "clean" annimmt.
- Marker muss IMMER geschrieben werden — auch im `except`-Pfad. Heute wird er vermutlich nur im Happy-Path geschrieben.

### 1.3 Advisory Lock-File vs. Lock-State-Verwechslung

**Symptom:** `~/.hermes/kanban/.dispatcher.lock` ist 0 Bytes mtime Monate alt. Naiver Check `test -s file` → „kein Lock" (false). Tatsächlich hält `fcntl.flock()` Locks am FD, nicht am File-Inhalt; die Datei DARF immer leer sein.

**Verifikation:**
```bash
# Falsch (false negative möglich):
test -s /home/bratan/.hermes/kanban/.dispatcher.lock && echo "lock held" || echo "lock free"
# Korrekt — Lock via fuser (PID der Inhaber):
fuser /home/bratan/.hermes/kanban/.dispatcher.lock 2>&1
# Oder: Python non-blocking acquire versuchen
python3 -c "
import fcntl, pathlib
h = pathlib.Path('/home/bratan/.hermes/kanban/.dispatcher.lock').open('a+b')
try:
    fcntl.flock(h.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    print('LOCK FREE — kein Inhaber')
    fcntl.flock(h.fileno(), fcntl.LOCK_UN)
except BlockingIOError:
    print('LOCK HELD — andere Instanz läuft')
"
```

**Faustregel:** Für jede Lock-Datei die Aussage „existiert" mit `LOCK_NB` non-blocking versuchen — Inhalt prüfen ist immer falsch.

**Hermes-Spezialfall:** In `gateway/kanban_watchers.py:802` hält der Inhaber `self._kanban_dispatcher_lock_handle` für Process-Lifetime (kein expliziter Unlock). Der Lock ist nach Prozess-Tod automatisch weg — genau DAS ist die richtige Semantik für advisory locks, nicht das Vorhandensein der Datei.

### 1.4 `except Exception: return (True, "")` als Anti-Pattern

**Symptom:** Eine `_check_<X>_presence()` Funktion meldet permanent `running=True`, selbst wenn alle Probes fehlschlagen. User-erwartetes Verhalten: Bei Fehler ehrlich "unbekannt" oder "nein, weil…" zurückgeben. Tatsächliches Verhalten: Silent-Pass-Through, was jeden Monitoring-Pfad sabotiert.

**Konkreter Befund:** `hermes_cli/kanban.py:135-186` `_check_dispatcher_presence()` schluckt JEDEN Import- und Probe-Fehler und gibt `(True, "")` zurück. `gateway.status.get_running_pid()` liest aus `gateway_state.json` und retourniert den dort persistierten PID — wenn der tot ist, ist die Probe erfolgreich (State lesen = success), aber das Result ist trotzdem ein zombie-PID.

**Verifikation:** Im Lab einen toten PID in `gateway_state.json` schreiben (oder warten bis ein SIGTERM den natürlichen Zombie erzeugt), dann `hermes kanban create "test"` aufrufen. Die Ausgabe darf KEIN `task will sit in 'ready' until you start the gateway`-Warning enthalten wenn der Gateway tot ist.

**Fix-Optionen:**
- `_check_dispatcher_presence` muss den PID zusätzlich validieren: `if pid and (os.kill(pid, 0) or True) and dispatch_on: return (True, ...)` — bei `kill -0` failure explizit `(False, f"PID {pid} tot")`.
- Import-Fehler sollen zu `(False, "probe unavailable")` führen, nicht `(True, "")`. Die Funktion darf NICHT lügen.
- Helper-Funktion `gateway_running_or_fail_unsafe()` mit `fail_unsafe=True`-Flag, die Probes nicht silent-ignored.

### 1.5 Config-Field-Trust vs. Process-Reality

**Symptom:** `config.yaml` zeigt `dispatch_in_gateway: true, dispatch_interval_seconds: 60` — sieht gesund aus. Aber der Prozess, der den Ticker hosten sollte, existiert nicht. Wer dem Config-Feld allein vertraut, hat null Aussage über den tatsächlichen Runtime-Zustand.

**Verifikation:**
```bash
# Was Config sagt:
grep -E '^  dispatch_in_gateway|^  dispatch_interval_seconds' ~/.hermes/config.yaml
# Was Prozessliste zeigt:
pgrep -af 'hermes.*gateway run' || echo "KEIN Gateway-Prozess — Config-Wert ist irrelevant"
```

**Faustregel:** Config ist **Intention** („so soll es sein"), nicht **Observation** („so ist es"). Runtime-Health-Audits müssen Prozess-Realität prüfen, nicht Config-Werte.

## 2. Die 4-Stufen-Verifikations-Ladder

Für jeden Runtime-Correctness-Audit, in dieser Reihenfolge:

| Stufe | Befehl | Was es prüft |
|-------|--------|--------------|
| **L1: Live-Prozess** | `pgrep -af '<pattern>'` | Existiert der Prozess überhaupt? |
| **L2: PID-Liveness** | `kill -0 <pid> 2>/dev/null`; echo $? | Lebt der aus State gelesene PID? |
| **L3: Heartbeat-Journal** | `journalctl --user -u <svc> --since '24h ago' \| grep '<expected-tick>' \| tail -3` | Wann hat der Prozess zuletzt signalisiert, dass er lebt? |
| **L4: Data-Drift** | `stat -c '%Y' <data-file>` und Vergleich zu `now` | Wann wurden die Daten zuletzt mutiert? Drift > 2× Heartbeat = Alarm |

**Wenn ALLE 4 Stufen passen → Runtime ist gesund.** Wenn eine Stufe versagt → diese Stufe reparieren, nicht die anderen überspringen. Die häufigste Audit-Fehlerquelle ist es, bei L1 zu stoppen wenn der Prozess läuft, ohne L2-L4 zu prüfen.

## 3. Kanban-spezifische Diagnose-Schritte

### 3.1 Schnell-Check (60 Sekunden)

```bash
# L1: Existiert der Gateway-Prozess?
pgrep -af 'hermes_cli.main gateway run' || echo "❌ kein gateway run"
# L2: PID aus gateway_state.json vs. Realität
PID=$(python3 -c "import json; print(json.load(open('/home/bratan/.hermes/gateway_state.json'))['pid'])")
kill -0 $PID 2>/dev/null && echo "PID $PID lebt" || echo "❌ PID $PID TOT"
# L3: Letzte Tick-Zeile im Log
grep -nE 'kanban dispatcher.*embedded in gateway' ~/.hermes/logs/gateway.log | tail -3
# L4: Letzte Mutation in Board-DB
ls -lt ~/.hermes/kanban/boards/*/kanban.db 2>/dev/null | head -3
```

### 3.2 Ausführlicher Audit (5 Minuten)

Siehe Phase-0-Pattern in `references/multi-angle-audit-pattern.md` (Phase 0 Sondierung). Die 10-Punkt-Liste dort ist genau die richtige Vorbereitung.

### 3.3 Single-Point-of-Failure-Checkliste für Kanban

| Frage | Wo zu prüfen | Akzeptanzkriterium |
|-------|-------------|--------------------|
| Läuft der Gateway-Prozess? | `pgrep -af hermes_cli.main` | Ja, PID stabil |
| Hält der Gateway den Dispatcher-Lock? | `gateway/kanban_watchers.py:768-817` | Log: `holding singleton dispatcher lock` |
| Ist `dispatch_in_gateway: true`? | `config.yaml:126` | `true` |
| Gibt es einen externen Watchdog? | `crontab -l`, `systemctl list-timers` | Heartbeat alle 60-120s ODER systemd-Restart |
| Wird der Dispatcher beim Boot gestartet? | `systemctl --user is-enabled hermes-gateway.service` | `enabled` (nicht `static`, nicht `not-found`) |
| Lockt der `dispatch_once` per-Tick? | `kanban_db.py:1415` `_dispatch_tick_lock` | Non-blocking, `_INIT_LOCK_TIMEOUT_SECONDS` bounded |
| Ist die SQLite-Busy-Timeout gesetzt? | `kanban_db.py:1287` `DEFAULT_BUSY_TIMEOUT_MS` | `120_000` (2 Min) |

**Heute (2026-07-13) sind die ersten 3 Fragen GRÜN, die letzten 4 ROT.** Genau diese Diskrepanz ist der Audit-Befund.

## 4. Konkrete Fix-Vorschläge (priorisiert)

### Fix A: `kill -0`-Probe in `_check_dispatcher_presence()` (P0)

```python
def _check_dispatcher_presence() -> tuple[bool, str]:
    try:
        from gateway.status import get_running_pid
    except Exception as exc:
        return (False, f"probe unavailable: {exc}")  # fail-closed statt silent
    try:
        pid = get_running_pid()
    except Exception as exc:
        return (False, f"pid lookup failed: {exc}")
    if pid and not _pid_alive(pid):  # neue Helper-Funktion
        return (False, f"persisted pid {pid} no longer alive — gateway_state stale")
    # ... rest wie bisher
```

**Verifikation:** Mit `kill -9 $(pgrep -f 'hermes_cli.main gateway run')` den Gateway killen, dann `hermes kanban create "x"` — muss die Warning „No gateway is running…" zeigen.

### Fix B: systemd `Restart=on-failure` für hermes-gateway (P0)

Unit-Datei `/etc/systemd/system/hermes-gateway.service` heute:
```ini
[Service]
Restart=no    # oder fehlend
```

Soll:
```ini
[Service]
Restart=on-failure
RestartSec=10
StartLimitIntervalSec=300
StartLimitBurst=5
```

**Verifikation:** Nach `kill -9` hebt systemd den Gateway automatisch. Nächster Dispatcher-Tick ≤ 60s nach Restart.

### Fix C: Heartbeat-Logging in `gateway_state.json` (P1)

```python
# Im _kanban_dispatcher_watcher Tick-Loop:
state_path = Path("/home/bratan/.hermes/gateway_state.json")
try:
    state = json.loads(state_path.read_text())
except Exception:
    state = {}
state["last_tick_at"] = time.time()
state["dispatcher_pid"] = os.getpid()
state_path.write_text(json.dumps(state, indent=2))
```

**Verifikation:** Nach 2 Ticks ist `last_tick_at` aktuell; nach Gateway-Tod bleibt es eingefroren → Audit-Check wird trivial.

### Fix D: `hermes kanban dispatcher-status` Befehl (P2)

Neuer CLI-Subcommand, der den Lock-Inhaber, den letzten Tick, die Board-Aktivität und ggf. konkurrierende Gateway-PID in einer Zeile zusammenfasst:

```bash
hermes kanban dispatcher-status
# → lock_held=true pid=12345 last_tick_at=2026-07-13T13:50:00Z board=hermes db_mtime=2026-07-13T13:49:30Z
```

**Verifikation:** Befehl existiert, antwortet konsistent mit den Rohdaten, läuft in < 100ms.

### Fix E: Multi-Gateway-Warning sichtbar (P1)

Statt `logger.info "another gateway already holds the dispatcher lock"` → SSE-Event in das Home-Channel und Eintrag in `~/.hermes/logs/warnings.jsonl`. Damit weiß der User beim nächsten Login, dass er im „passive dispatch"-Modus ist.

## 5. Lessons für die Skill-Library

Diese Audit-Findings gehören generalisiert (nicht kanban-spezifisch) in die Verifikations-Checkliste von `references/multi-angle-audit-pattern.md` (Phase 3 Verify subagent claims). Konkret:

- **Neue Verifikations-Zeile:** „Persistierte State-Dateien: `kill -0` jeden PID, nicht nur Existenz prüfen"
- **Neue Verifikations-Zeile:** „Lock-Dateien nie via `test -s` — immer `flock LOCK_NB` non-blocking versuchen oder `fuser`"
- **Neue Verifikations-Zeile:** „Bei `_check_*_presence()`-Funktionen: jede `except Exception: return (True)`-Zeile ist ein Audit-Risiko"

Diese Checkliste-Erweiterungen wurden im SKILL.md §11 als neuer Pitfall-Bullet zusammengefasst.

## 6. Bekannte Lücken in diesem Audit (für Nachfolge-Audits)

- Groß-Logs (`gateway.log` 4,9 MB; `gateway-exit-diag.log` 3,3 MB) wurden nur am Ende inspiziert. Mittlere Hot-Phasen könnten weitere SIGTERM-Restarts, OOM-Killer-Events oder WAL-Checkpoint-Probleme enthalten.
- SIGTERM-Ursache (03:19:54) bleibt unklar — `journalctl --user` zeigt nur Poweroff-Target um 03:20:00, kein `hermes-gateway.service`-Event (Unit war `not-found`). Mögliche Ursachen: OOM, user@.service idle-stop, manueller `systemctl stop`. Empfehlung: vor nächstem `hermes update` `dmesg -T | grep -iE 'killed|oom'` checken.
- Unit-Path-Drift: `/etc/systemd/system/hermes-gateway.service` existiert physisch, wird aber nicht im Index geführt. Vermutlich fehlt `daemon-reload` seit letzter Änderung.
- `@reboot`-Cron startet nur `hermes-gh-api-server.py`, NICHT den Gateway. Falls User einen Reboot-Recovery-Pfad will, muss er explizit eine Gateway-Start-Zeile ergänzen.