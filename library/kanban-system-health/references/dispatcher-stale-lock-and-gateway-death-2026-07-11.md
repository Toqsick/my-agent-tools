# Dispatcher Stale Lock + Gateway Death — Live Findings 2026-07-11

**Gefunden im:** Scout C (Multi-Angle Cron + Dispatcher + Skill Health Check)
**Ausgangsfrage:** "Scout C: Cron + Dispatcher + Skill-Library Health"

## Befund

- **Gateway-Status:** `hermes-gateway.service` = `inactive (dead)`
- **Dispatcher-Lockdatei:** `~/.hermes/kanban/.dispatcher.lock` = 0 Bytes, mtime = 2026-06-19. **Korrektur 2026-07-13:** Größe und mtime sind bei einem Advisory-Lock nicht aussagekräftig. Entscheidend ist ein non-blocking `flock`-Probe; im Re-Audit war der Lock frei.
- **Kein laufender Daemon:** `pgrep -af "kanban.*daemon"` = leer
- **Keine laufenden Workers:** `pgrep -af "dispatch"` = leer
- **Cron-Ticker:** `~/.hermes/cron/ticker_heartbeat` mtime = jetzt (frisch, alle 60s)
- **Kanban-DBs:** Alle 7 Boards haben eine `kanban.db` unter `~/.hermes/kanban/boards/*/kanban.db`, alle intakt

## Kern-Erkenntnis

Der Cron-Ticker läuft **unabhängig vom Gateway**. Er heartbeatet, fired LLM-Jobs, und gibt den Anschein "alles läuft". Der Kanban-Dispatcher ist aber **embedded im Gateway** — wenn das Gateway tot ist, ist auch der Dispatcher tot, und ready-Tasks akkumulieren sich ungesehen.

**Dreifach-Bestätigung des Musters:**
1. Gateway inactive → dispatcher nicht verfügbar (embedded-Architektur seit 2026-07-02)
2. Lock-File seit 3 Wochen stale → kein Dispatcher hat in der Zeit den Lock gehalten
3. Kein `kanban daemon` Prozess → auch keine Standalone-Variante

## Recovery-Sequenz

```bash
# Schritt 1: Gateway starten (bringt Dispatcher embedded mit)
systemctl --user start hermes-gateway.service
sleep 3

# Schritt 2: Gateway läuft?
systemctl --user is-active hermes-gateway.service  # muss "active"

# Schritt 3: Hält ein Dispatcher den Singleton-Lock?
python3 - <<'PY'
import fcntl
p = '/home/bratan/.hermes/kanban/.dispatcher.lock'
f = open(p, 'a+')
try:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    print('LOCK_CONTENDED')
else:
    print('LOCK_FREE')
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
finally:
    f.close()
PY

# Schritt 4: Dispatcher-Ticks im Log
journalctl --user -u hermes-gateway --since "5 minutes ago" | grep -i dispatch

# Schritt 5: Kanban lebt?
hermes kanban diagnostics  # sollte "stranded_in_ready" zeigen
```

## Lessons Learned

1. **Cron-Ticker ≠ Dispatcher.** Der Ticker ist eine separate Loop in Hermes-Desktop/Cron-Subsystem und heartbeatet unabhängig vom Gateway. Ein "alles läuft"-Eindruck vom Ticker bedeutet NICHT, dass Kanban aktiv ist.
2. **Lockdatei-Attribute sind kein Health-Signal.** Der Dispatcher hält einen OS-Advisory-Lock auf einer persistenten Datei. Prüfe Lock-Contention per non-blocking `flock`; korreliere danach mit Gateway-PID und Dispatcher-Logs.
3. **Board-DBs intakt ≠ System aktiv.** Die SQLite-DBs werden bei jedem `hermes kanban list`/`show`/`diagnostics` gelesen, aber der Dispatcher schreibt nur, wenn er läuft. DB-Freshness kann von Read-Operations kommen.
4. **Stale Locks werden NIEMALS automatisch aufgeräumt.** Der Lock überlebt Gateway-Crashs, Reboots, und Profile-Wechsel. Der einzige Cleanup-Pfad ist manuell: `rm -f ~/.hermes/kanban/.dispatcher.lock`.