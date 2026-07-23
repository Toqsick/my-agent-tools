# Deployment & Server Lifecycle — Hermes V7 SSE

Procedures for starting, supervising, and locating the `@hermes/sse` server. Companion to `hermes-v7-sse-server/SKILL.md`.

## Server Start (Localdev)

```bash
cd /home/bratan/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart/hermes-v7-repo-starter/packages/hermes-sse
npm run build    # tsc → dist/
CORS_ORIGINS="http://localhost:4321" \
HERMES_AUTH_TOKEN=super-secret \
HERMES_WEBHOOK_TOKEN=hook-secret \
PORT=4321 \
node dist/server/index.js
```

Stop with `pkill -f "node dist/server/index.js"`. The Hermes gateway does not supervise this process — it survives a gateway restart (see `hermes-admin` skill for the gateway-quirk pattern).

## Server-Restart-Pitfall: `terminal()` verbietet `nohup ... &` (2026-07-02)

**Symptom:** Du versuchst den Server mit klassischem Bash-Background-Wrapper zu starten:
```bash
nohup node dist/server/index.js > /tmp/hermes-sse.log 2>&1 &
```
→ Hermes rejected **mit Auto-Reject**: *"Foreground command uses shell-level background wrappers (nohup/disown/setsid). Use terminal(background=true) so Hermes can track the process, then run readiness checks and tests in separate commands."*

**Fix (zwingend):** `terminal(background=true, notify_on_complete=true)` benutzen, ENV inline als `VAR=value command` Prefix:
```python
terminal(
    background=True,
    notify_on_complete=True,
    command='cd <pkg-path> && CORS_ORIGINS="http://localhost:8787,http://127.0.0.1:8787" HERMES_AUTH_TOKEN=super-secret HERMES_WEBHOOK_TOKEN=hook-secret PORT=8787 node dist/server/index.js'
)
```

**Readiness-Probe in separatem `terminal()`-Call** (3-5s nach Start):
```bash
sleep 3
curl -s -o /dev/null -w "Dashboard: HTTP %{http_code}\n" http://127.0.0.1:<port>/dashboard/hermes-sse-dashboard.html
curl -s -H "X-Hermes-Token: super-secret" http://127.0.0.1:<port>/api/status | head -c 300
timeout 3 curl -s -N -H "Authorization: Bearer ***" http://127.0.0.1:<port>/api/events | head -5
```
Erwartet: Dashboard 200, Status JSON mit `stream.clients: 0` initial, SSE-Stream `retry: 2500\nid: 1\nevent: stream.open`.

## Auto-Restart fehlt — Server stirbt beim Reboot/Logout (2026-07-02)

**Symptom:** User meldet "WebUI geht nicht mehr". Du startest den Server, alles funktioniert. Beim nächsten Reboot oder Session-Logout: wieder Connection Refused. Es gibt **keine systemd-unit** für den SSE-Server — er muss manuell gestartet werden.

**Quick-Fix für Localdev (kein systemd-Setup nötig):** Server mit `terminal(background=true, notify_on_complete=false)` starten — der Prozess läuft in der Hermes-TUI-Session und wird vom Agent-Lifecycle mit-verwaltet. Trade-off: stirbt mit Hermes-TUI, nicht reboot-safe.

**Production-Pattern (systemd-user-unit, proven 2026-07-02 — echte Basti-Installation verifiziert):**

`~/.config/systemd/user/hermes-sse.service` (Unit-Name = `hermes-sse`, nicht `hermes-sse-dashboard` — siehe Lessons unten):
```ini
[Unit]
Description=Hermes V7 SSE Dashboard Server (Queen/Worker/Gate, port 8787)
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
WorkingDirectory=/home/bratan/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart/hermes-v7-repo-starter/packages/hermes-sse
ExecStart=/home/bratan/.nvm/versions/node/v20.20.2/bin/node dist/server/index.js
Environment="PATH=/home/bratan/.nvm/versions/node/v20.20.2/bin:/home/bratan/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PORT=8787"
Environment="CORS_ORIGINS=http://localhost:8787,http://127.0.0.1:8787"
Environment="HERMES_AUTH_TOKEN=super-secret"
Environment="HERMES_WEBHOOK_TOKEN=hook-secret"
Restart=always
RestartSec=5
RestartForceExitStatus=75
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=15
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

**Reihenfolge ist kritisch (Reihenfolge-Fehler → EADDRINUSE):**
```bash
# 1. Manuell gestarteten Server killen (falls vorhanden)
pkill -f "node dist/server/index.js" || true
sleep 2
ss -tln | grep :8787 || echo "(port 8787 frei)"

# 2. Daemon-Reload + enable + start
systemctl --user daemon-reload
systemctl --user enable hermes-sse.service
systemctl --user start hermes-sse.service
sleep 3

# 3. Status + Verifizierung
systemctl --user status hermes-sse.service
curl -s -o /dev/null -w "Dashboard: HTTP %{http_code} | %{size_download}B\n" \
  http://127.0.0.1:8787/dashboard/hermes-sse-dashboard.html
curl -s -H "X-Hermes-Token: super-secret" http://127.0.0.1:8787/api/status | head -c 200
timeout 4 curl -s -N -H "Authorization: Bearer ***" http://127.0.0.1:8787/api/events | head -5
journalctl --user -u hermes-sse.service -n 10 --no-pager | tail -10

# 4. Restart-Härtetest (simuliert Crash — neue PID muss kommen)
systemctl --user restart hermes-sse.service
sleep 2
curl -s -o /dev/null -w "Nach Restart: HTTP %{http_code}\n" \
  http://127.0.0.1:8787/dashboard/hermes-sse-dashboard.html
```

**Voraussetzungen-Check VORAB:**
- `loginctl show-user bratan | grep Linger=yes` — sonst stirbt die Unit beim Logout (nicht reboot-safe)
- Node-Binary-Pfad korrekt (nvm-Pfade ändern sich bei Node-Updates): `which node`
- `RestartForceExitStatus=75` matched den Temp-Fail-Exit-Code vom Cron-Kontext
- Unit-Name = `hermes-sse.service` (kurz, matches bestehendes hermes-gateway-Pattern)

**Lesson Unit-Name (2026-07-02):** Erster Entwurf war `hermes-sse-dashboard.service`, aber kürzer = besser, matches hermes-gateway-Schema, tippfreundlicher in `journalctl -u hermes-sse`. Wenn du schon eine Unit unter anderem Namen hast, gib beim `enable`/`status` einfach den Pfad an — beides funktioniert.

## Production-Sicherheits-Trade-off (Token in Klartext-Unit-File)

`HERMES_AUTH_TOKEN=super-secret` steht im Klartext in der Unit-Datei. Für Bastis Localdev akzeptabel, Production hat 3 Optionen:

1. **⭐⭐⭐ Best Practice — EnvironmentFile:** Token nach `~/.hermes/sse.env` (chmod 600) auslagern:
   ```ini
   [Service]
   EnvironmentFile=/home/bratan/.hermes/sse.env
   # (statt der Environment="..." Zeilen für Token)
   ```
   Inhalt `sse.env` (eine Variable pro Zeile, KEIN `export`):
   ```
   HERMES_AUTH_TOKEN=<dein-token>
   HERMES_WEBHOOK_TOKEN=<dein-token>
   ```
   Vorteil: Token änderbar ohne Unit-Edit + daemon-reload, Backup-Strategie für Secrets greift, `.gitignore` für Repo-fähig.

2. **⭐⭐ Mittel — chmod 600 auf Unit-File:** `chmod 600 ~/.config/systemd/user/hermes-sse.service` schützt vor Mitlesen durch andere User-Accounts. Reicht für Single-User-Desktop.

3. **⭐ Schnell — So lassen:** Localdev-OK, dokumentieren dass Token rotiert werden muss wenn jemand das System verlässt.

**Diagnose-Triage bei "Dashboard geht nicht" (proven 2026-07-02):**
1. `ss -tlnp sport = :<port>` → leer? Server down. `pgrep -af "node dist/server"` zeigt's.
2. `curl /dashboard/...` → HTTP 302 (redirect)? Server lebt, aber Static-Routing greift. Bei 200: läuft.
3. `curl /api/status` mit Token → JSON? Backend-Health OK.
4. `timeout 3 curl -N /api/events?token=...` → `stream.open`? SSE-Stream lebt.

Wenn alle 4 grün → Server ist fine, Bug ist im Browser (Cache, EventSource-Header-Workaround, TDZ, CORS — siehe 8-Layer-Tabelle im SKILL.md).

## Memory-Pfad kann outdated sein (2026-07-02)

**Symptom:** Mnemosyne-Memory sagt "Hermes-V7 lebt unter `~/hermes-v7/`". `ls ~/hermes-v7/` → *Datei oder Verzeichnis nicht gefunden*. Pfad ist umgezogen oder gelöscht.

**Realität (Stand 2026-07-02 für Basti):**
- ❌ `~/hermes-v7/` — existiert nicht mehr
- ✅ `/home/bratan/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart/hermes-v7-repo-starter/packages/hermes-sse/` — der **aktive** Server
- ✅ `/home/bratan/Dokumente/Perplexity/hermes-v7-repo-starter-with-sse/` — Starter-Variante (nur Scaffold, kein dist/)
- ⚠️ `/home/bratan/docs/queen-hermes-v7.1/` — Inventur/Multi-Agent-Research-Doku, **NICHT** der Server

**Pattern:** Wenn Memory-Pfad nicht mehr stimmt → `find /home/bratan -maxdepth 6 -name "package.json" | xargs grep -l '"name":.*hermes-v7\|sse-dashboard' 2>/dev/null` zur Wahrheit-Findung. Dann Memory mit `mnemosyne_remember` korrigieren (siehe `hermes-maintenance` Sektion 1).

**Mnemosyne-Pfad-Korrektur-Workflow (proven 2026-07-02):**

Nach erfolgreicher Pfad-Ermittlung den **echten, tool-verifizierten** Pfad speichern — NIE spekulierte:
```python
mnemosyne_remember(
    content="Hermes SSE Dashboard v0.2.0: ECHTER Pfad ist ~/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart/hermes-v7-repo-starter/packages/hermes-sse/ (NICHT ~/hermes-v7/, den gibts nicht). systemd-User-Unit ~/.config/systemd/user/hermes-sse.service seit 2026-07-02, Port 8787, Token super-secret. Befehle: systemctl --user {start,stop,restart,status} hermes-sse.service, journalctl --user -u hermes-sse.service -f.",
    importance=0.85,           # hoch — verhindert 5-Minuten-Pfad-Suche in Folgesessions
    source="fact",
    veracity="tool"            # KRITISCH: nur per Command verifizierte Pfade speichern
)
```
Alte Mnemosyne-Einträge mit `replace` oder `remove` Operations updaten, dann SKILL.md Memory-Pfad-Sektion patchen (wie hier). Anti-Pattern: alte + neue Einträge parallel — neue übersteuert per Importance-Score, aber Verwirrung bleibt.

## Hermes-Terminal: `nohup ... &` wird Auto-Rejected (2026-07-02)

**Symptom:** Du willst den SSE-Server (oder einen anderen lang laufenden Dev-Server) starten mit klassischem Bash-Background-Pattern:
```bash
nohup node dist/server/index.js > /tmp/server.log 2>&1 &
```
→ Hermes rejected **mit Approval-Prompt** (oder Auto-Reject): *"Foreground command uses shell-level background wrappers (nohup/disown/setsid). Use terminal(background=true) so Hermes can track the process, then run readiness checks and tests in separate commands."*

**Verbotene Wrapper im Foreground-Call:** `nohup`, `disown`, `setsid`, trailing `&` lösen den Reject aus.

**Fix (zwingend Hermes-konform):** `terminal(background=true, notify_on_complete=<bool>)` benutzen:
```python
terminal(
    background=True,
    notify_on_complete=True,   # bei endlichen Tasks (Server bleibt silent → notify_on_complete=False)
    command='cd <pkg> && ENV=val node dist/server/index.js'
)
```

**Wann `notify_on_complete=True` vs `False`:**
- `True` = "Benachrichtige mich wenn der Prozess endet" — für Builds, Tests, Migrations
- `False` = "Prozess läuft für immer, ich checke manuell" — für Dev-Server, Watcher, Daemons

**Readiness-Probe IMMER in separatem `terminal()`-Call** (3-5s nach Start):
```bash
sleep 3
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:<port>/health
```

**Lesson:** Diese Lektion erweitert das bash-IOCTL-Pitfall-Pattern in `hermes-maintenance` Sektion 11.4. Wer beim Server-Start hängt, sollte **erst** hier nachschauen (nohup-Auto-Reject), **dann** 11.4 (IOCTL-Fehler).
