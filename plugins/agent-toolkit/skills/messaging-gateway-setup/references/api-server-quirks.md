# Hermes API-Server (`gateway/platforms/api_server.py`) — Domain-Wissen

Quellen: `~/.hermes/hermes-agent/gateway/platforms/api_server.py` (Stand 2026-07-10, Hermes v0.18.2, Commit `2b4ec0082`), plus Recon von `rusty4444/hermes-android` v1.0.8/1.0.9.

## Was der API-Server ist (und was nicht)

**Ist:** HTTP-API-Server mit OpenAI-kompatiblen Endpoints für externe Clients. Default `127.0.0.1:8642`. Bindet 0.0.0.0 wenn mit `--host 0.0.0.0` gestartet.

**Ist NICHT:** Der Messenger-Gateway. Nicht zu verwechseln mit `hermes_cli.main gateway run` (Port random, für Telegram/Discord/WhatsApp). Siehe `messaging-gateway-setup` SKILL.md "ZWEI verschiedene Gateway-Begriffe"-Warnbox.

## Endpoints die Mobile-Companion-Apps erwarten

| Endpoint | Auth | Zweck |
|---|---|---|
| `GET /api/sessions` | Bearer `API_SERVER_KEY` | Sessions listen |
| `GET /api/sessions/{id}/messages` | Bearer | Message-History |
| `POST /v1/chat/completions` | Bearer | **SSE Streaming** — Token-Deltas |
| `GET /v1/capabilities` | Bearer | Feature-Discovery für App |
| `GET /v1/models` | Bearer | Model-Liste |
| `GET /v1/skills` | Bearer | Skills-Liste (App "Skills"-Tab) |
| `GET /api/cron/jobs` | Bearer (über Dashboard) | Cron-Liste (App "Cron"-Tab) |
| `GET /api/memory` | Bearer (über Dashboard) | Memory-Viewer |
| `GET /health` | bypass | Liveness |
| `GET /health/detailed` | Bearer | Plattform-Status (telegram + api_server) |
| `POST /api/webhook/:channel` | `X-Webhook-Token` | External → SSE bridge |

OpenAI-kompatibles Format: `{"model": "...", "messages": [...], "stream": true}` — das ist warum die Hermes-Android-App (und jede OpenAI-SDK-App) direkt damit spricht.

## Pflicht-Setup für Mobile-Companion-Erreichbarkeit

### 1. `API_SERVER_KEY` in `~/.hermes/.env` setzen

Ohne den Key akzeptiert der Server **keinen Mobile-Client** (alle Bearer-Auth-Calls → 401). Generierung:

```bash
# 64-char hex (256-bit), manuell oder via hermes setup
echo "API_SERVER_KEY=$(openssl rand -hex 32)" >> ~/.hermes/.env
chmod 600 ~/.hermes/.env
```

**Wichtig:** `.env` ist für Secrets, nicht für behavioral config. Wenn der Key rotiert wird → alle Mobile-Clients müssen neu konfiguriert werden.

### 2. ENV-Vars gewinnen über YAML — kein separater Config-Block nötig

In Hermes v0.18+ liest `APIServerAdapter.__init__()` die Config in dieser Reihenfolge:
1. `extra.get("host", os.getenv("API_SERVER_HOST", "127.0.0.1"))`
2. `extra.get("port", os.getenv("API_SERVER_PORT", "8642"))`
3. `extra.get("key", os.getenv("API_SERVER_KEY", ""))`

→ **ENV-Vars in `~/.hermes/.env` reichen** — kein Edit von `config.yaml` nötig. Der `gateway.api_server.max_concurrent_runs: 10`-Block ist optional und schon default-mäßig da.

### 3. Server-Restart (mit Pitfalls — siehe unten)

```bash
systemctl --user restart hermes-gateway   # 5-10s Telegram-Downtime, unvermeidbar
sleep 10 && hermes gateway status         # beide Plattformen sollten "connected" sein
```

**Verifikation:**
```bash
ss -tlnp | grep ':8642'           # muss LISTEN auf 0.0.0.0 zeigen, nicht 127.0.0.1
curl -s http://127.0.0.1:8642/health/detailed | python3 -m json.tool
# → "platforms": {"telegram": {...}, "api_server": {...}} beide "connected"
```

### 4. (Optional, aber empfohlen) TCP_NODELAY-Patch für SSE-Streaming

**Symptom ohne Patch:** Mobile-Chat zeigt Text nicht Token-für-Token, sondern als einen Burst am Ende der Antwort. Fühlt sich kaputt an auf Handy/Tablet.

**Ursache:** Nagle's Algorithmus auf dem Server-Socket sammelt kleine SSE-Writes (Token-Deltas, Tool-Progress-Events) und schickt sie als großes TCP-Segment. Auf dem Handy sieht's aus wie ein einziger Klumpen.

**Fix:** `server-patches/0001-tcp-nodelay-sse.patch` aus `rusty4444/hermes-android` anwenden. Patch modifiziert 4 SSE-Endpoints in `gateway/platforms/api_server.py`:

```python
def _sse_disable_nagle(response):
    """Set TCP_NODELAY on the transport socket underlying an SSE response."""
    try:
        transport = getattr(response, '_req', None)
        if transport is not None:
            transport = getattr(transport, 'transport', None)
        if transport is not None:
            sock = transport.get_extra_info('socket')
            if sock is not None:
                sock.setsockopt(_socket.IPPROTO_TCP, _socket.TCP_NODELAY, 1)
    except Exception:
        pass
```

Aufruf direkt nach `await response.prepare(request)` an allen 4 SSE-Stellen (`_sse_disable_nagle(response)`).

**Patch-Drift-Pitfall (2026-07-10, wichtig):** `git apply` schlägt fehl wenn Hermes 20+ Commits neuer ist als der Patch-Stand (Patch-Quelle: `rusty4444/hermes-android`, Hunk-Offsets verschieben sich). Symptom: `error: Anwendung des Patches fehlgeschlagen: gateway/platforms/api_server.py:N` mit `Patch konnte nicht angewendet werden`. **Lösung: manuell portieren** in dieser Reihenfolge:
1. Helper-Funktion `_sse_disable_nagle(response)` direkt nach `logger = logging.getLogger(__name__)` einfügen — **Achtung:** Wenn der Patch-Helper schon existiert oder versehentlich doppelt eingefügt wurde, prüfen mit `grep -c "^def _sse_disable_nagle"` (muss 1 sein)
2. Mit `patch`-Tool + `replace_all=true` die 2 identischen Stellen mit `headers["X-Hermes-Session-Key"]` pattern patchen:
   ```
   old: response = web.StreamResponse(status=200, headers=headers)
        await response.prepare(request)
        last_write = time.monotonic()
   new: response = web.StreamResponse(status=200, headers=headers)
        await response.prepare(request)
        _sse_disable_nagle(response)
        last_write = time.monotonic()
   ```
3. Mit `replace_all=true` die 2 Stellen mit `sse_headers` patchen (gleiche Pattern-Form mit leerer Zeile davor statt `last_write`)
4. Verifizieren: `python -c "import ast; ast.parse(open('gateway/platforms/api_server.py').read())"` (syntax OK)
5. `grep -c "_sse_disable_nagle(response)" api_server.py` muss 4 ergeben, `grep -c "^def _sse_disable_nagle"` muss 1 ergeben
6. Module-Import testen: `cd ~/.hermes/hermes-agent && venv/bin/python -c "from gateway.platforms.api_server import _sse_disable_nagle; print('OK')"`

**Stand 2026-07-10:** Patch ist in Hermes v0.18.2 noch nicht gemerged (`grep -c "TCP_NODELAY" api_server.py` → 0). Wenn's bei dir drin ist, prüfen via `grep _sse_disable_nagle gateway/platforms/api_server.py`.

## API-Server ist KEIN separater Prozess — läuft IM Messenger-Gateway (korrigiert 2026-07-10)

Frühere Annahme: API-Server ist eigener Prozess via `hermes api-server`. **Falsch** (für Hermes ≥ v0.18).

**Realität**: Der API-Server-Adapter (`gateway/platforms/api_server.py`) wird **im selben Prozess** geladen wie der Messenger-Gateway-Adapter. Ein einziger `hermes_cli.main gateway run`-Prozess hostet beide Plattformen. Konfiguration erfolgt über `gateway.api_server.*` in `config.yaml` plus ENV-Vars (`API_SERVER_HOST`, `API_SERVER_PORT`, `API_SERVER_KEY`).

**Was das für die Praxis bedeutet:**
- **Restart = Restart vom Messenger-Gateway** (= 5-10s Telegram-Bot-Downtime, unvermeidbar)
- API-Server kann **nicht unabhängig** gestartet/gestoppt werden
- ENV-Vars in `~/.hermes/.env` greifen beim nächsten Gateway-Restart automatisch
- `hermes api-server --host 0.0.0.0 --port 8642` als Standalone-Command funktioniert in Hermes v0.18 nicht mehr (siehe Hinweis oben — `hermes api-server` ist veraltet)

**Verifikation, dass beide Plattformen in einem Prozess laufen:**
```bash
ss -tlnp | grep -E ':(8642|35395)'    # beide Ports vom SELBEN pid
# Beispiel-Output:
# LISTEN ... 127.0.0.1:35395  ... users:(("hermes",pid=61301,fd=24))
# LISTEN ... 0.0.0.0:8642     ... users:(("hermes",pid=61301,fd=27))
#                              ^^^^ gleicher pid → beide im selben Prozess

curl -s -H "Authorization: Bearer $KEY" http://127.0.0.1:8642/health/detailed
# Beide "platforms": {"telegram": {...}, "api_server": {...}} → state "connected"
```

## Reverse-Proxy-Strategien für Mobile-Erreichbarkeit (Stand 2026-07-10)

Drei Wege, die Hermes-Android-App von unterwegs erreichbar zu machen:

### Option A: LAN-only (einfachste)

- Hermes-API auf `0.0.0.0:8642` (siehe oben)
- Handy im gleichen WLAN
- App-Config: `Host: <workstation-LAN-IP>`, `Port: 8642`
- **Kein TLS**, aber privates WLAN ist ok
- **Limit**: nur Zuhause, nicht von unterwegs

### Option B: Tailscale (eleganteste Hybrid-Variante)

- Tailscale auf Workstation + Handy + (optional) Cloud-Server im selben Tailnet
- **`tailscale serve --bg <URL>`** exposed einen lokalen Port per Tailscale-HTTPS mit Auto-Cert
- **3 Befehle, kein Caddy, keine Domain, kein Cloud-Reboot**:
  ```bash
  tailscale serve --bg http://127.0.0.1:8642                  # Hermes API auf :443
  tailscale serve --bg --https=8443 http://127.0.0.1:8787    # Yuno WebUI auf :8443
  tailscale serve --bg --https=8444 http://127.0.0.1:9119    # Hermes Dashboard auf :8444
  ```
- App-Config: `Host: <machine-name>.tail<XXX>.ts.net`, `Port: 443`
- **Nur im Tailnet erreichbar** (`tailnet only`) — kein Public-Internet-Risiko

**Pitfalls:**
- `tailscale serve <URL>` **ersetzt** die komplette Serve-Config. Wenn man das WebUI behalten will und API hinzufügen, muss man die `--https=<PORT>` Multi-Service-Variante nutzen oder das WebUI neu hinzufügen. **Konkreter Vorfall 2026-07-10:** Erst `tailscale serve --bg http://127.0.0.1:8642/v1` → WebUI auf 8787 weg. Recovery: `tailscale serve reset` → alle Services neu mit `--https=<PORT>` starten.
- Hermes-Dashboard mit `--host 127.0.0.1` rejected Tailscale-Requests wegen FastAPI-Host-Header-Validierung (`Invalid Host header`). Fix: `--host 0.0.0.0`.
- Hermes-Dashboard sollte als systemd-user-unit laufen, nicht als nohup-Prozess oder `terminal(background=true)` — Letzteres stirbt beim Subshell-Cleanup mit exit 143 + Crashpad-Fehlermeldung. Saubere Variante: eigene `~/.config/systemd/user/hermes-dashboard.service` mit `--host 0.0.0.0`.
- MagicDNS-Suffix herausfinden: `tailscale dns status` → "MagicDNS: enabled tailnet-wide (suffix = tail<XXX>.ts.net)"
- Tailscale auf Handy prüfen: `tailscale status` auf der Workstation — Gerätename muss `online` sein, nicht `offline`/`am Start`.

### Option C: Caddy + eigene Domain

- Klassischer Reverse-Proxy mit Let's-Encrypt Auto-TLS
- Braucht eigene Domain (DNS-Record auf Cloud-Server-IP)
- Basic-Auth zusätzlich möglich (2-Layer-Security)
- **Aufwendigste Variante**, aber voll public-internet-fähig

**Empfehlung**: Option B (Tailscale) für 90% der Basti-Use-Cases — kein DNS-Setup, kein Zertifikats-Renewal, kein Cloud-Server-Reboot.

## systemd-units für die 3 Hermes-Plattformen (Stand 2026-07-10)

| Unit | Was | Port | ENV-Konfig |
|---|---|---|---|
| `hermes-gateway.service` | Messenger-Gateway (Telegram/Discord) **+ API-Server** | 35395 + 8642 | `API_SERVER_HOST/PORT/KEY` |
| `hermes-dashboard.service` | Hermes Web-Dashboard für Memory/Cron/Skills | 9119 | — |
| `hermes-webui.service` | Yuno WebUI (legacy nesquena/hermes-webui) | 8787 | — |

**Wichtige Properties** (alle 3):
- `Type=simple`, `Restart=always`, `RestartSec=5`
- `WorkingDirectory=/home/bratan/.hermes` (Default-Profile, nicht yuno)
- `Environment="HERMES_HOME=/home/bratan/.hermes"`
- `disabled` by default → bewusst kein Auto-Start nach Crash oder Reboot (Memory-Warnung aus dem Yuno-Betrieb: Hermes-Crashes können Endlosschleifen auslösen wenn `Restart=always` + Port-Konflikt)

**Persistent aktivieren** (nach erfolgreichem Stabilitätstest):
```bash
systemctl --user enable hermes-gateway hermes-dashboard hermes-webui
```

**Beispiel-unit** für Hermes-Dashboard (Pflicht-Pattern, 2026-07-10 angelegt):
```ini
[Unit]
Description=Hermes Dashboard (Web-UI auf 9119, für Hermes-Android Memory/Cron/Skills)
After=network-online.target hermes-gateway.service
Wants=network-online.target

[Service]
Type=simple
ExecStart=/home/bratan/.hermes/hermes-agent/venv/bin/hermes dashboard --port 9119 --host 0.0.0.0
WorkingDirectory=/home/bratan/.hermes
Environment="PATH=/home/bratan/.hermes/hermes-agent/venv/bin:/usr/bin:/bin"
Environment="VIRTUAL_ENV=/home/bratan/.hermes/hermes-agent/venv"
Environment="HERMES_HOME=/home/bratan/.hermes"
Restart=always
RestartSec=5
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

**Restart-Sequenz die Endlosschleifen verhindert (Pitfall 2026-07-10):**
```bash
# 1. Service disable VOR dem stop (verhindert Auto-Restart-Falle)
systemctl --user disable hermes-gateway
# 2. Graceful stop mit Timeout
systemctl --user stop hermes-gateway
# 3. Warten bis wirklich tot (manchmal bleiben mcp-stdio-watchdog-Children übrig)
sleep 3
# 4. Falls noch Hermes-Prozesse laufen: PID-basiert killen, NICHT pkill -f
PIDS=$(ps -eo pid,args | grep "hermes_cli.main" | grep -v grep | awk '{print $1}')
[ -n "$PIDS" ] && kill -TERM $PIDS && sleep 2
# 5. Neu starten
systemctl --user start hermes-gateway
# 6. Nach erfolgreichem Smoke-Test: enable zurück
systemctl --user enable hermes-gateway
```

## Hermes-Android-App Configuration (App-Config-Reference 2026-07-10)

Für `rusty4444/hermes-android` (v1.0.9 aktuell):

| App-Feld | Wert (Tailscale-Variante) | Wert (LAN-Variante) |
|---|---|---|
| **Label** | `Yuno Tailnet` | `Home LAN` |
| **Host** | `bratan-17-p1.tail94d785.ts.net` (oder eigener MagicDNS-Name) | `192.168.x.y` (Workstation-LAN-IP) |
| **Port** | `443` | `8642` |
| **API Key** | `API_SERVER_KEY` aus `~/.hermes/.env` | dito |
| **Gateway path prefix** | leer | leer |
| **Dashboard path prefix** | leer | leer |
| **Dashboard behind proxy** | **AN** (Tailscale injiziert Cert) | AUS |
| **Dashboard Port** | `8444` (Tailscale) | `9119` (LAN) |
| **Username / Password** | leer (Tailscale-only) | leer (open Dashboard) |

**APK-Download**: <https://github.com/rusty4444/hermes-android/releases/latest>
- `app-arm64-v8a-release.apk` für moderne Phones (Galaxy S8+, alle Pixel, OnePlus, etc.)
- `app-armeabi-v7a-release.apk` für alte 32-bit-Phones
- `app-x86_64-release.apk` für Emulator

**APK aufs Handy bringen** — wenn kein `adb` im Setup ist, Mini-Python-File-Server (siehe `scripts/apk-serve.py` Template):
- Erlaubt nur explizit gelistete Dateinamen (kein Path-Traversal, kein Directory-Listing)
- Läuft auf freiem Port (z. B. 8445)
- Via Tailscale Serve exposed: `tailscale serve --bg --https=8446 http://127.0.0.1:8445`
- Im Handy-Browser: `https://<machine-name>.tail<XXX>.ts.net:8446/<filename>`
- Achtung: ASCII-only Bytes in 404-Text (kein em-dash `—`), sonst `SyntaxError`

**Tailscale auf Handy aktiv?** `am Start` heißt nicht "online". Check via `tailscale status` auf der Workstation — `galaxy-s8` muss dort als `online` stehen, nicht `offline`.

## Hermes-CLI Befehle für API-Server-Setup (Stand 2026-07-10)

| Befehl | Was |
|---|---|
| `hermes gateway status` | Listet alle Plattformen mit Health-State |
| `hermes dashboard --port 9119 --host 0.0.0.0` | Startet Dashboard-Prozess im Vordergrund |
| `hermes dashboard --status` | Check ob Dashboard läuft |
| `hermes api-server ...` | **VERALTET** in v0.18+, der API-Server läuft im Gateway-Prozess |

**Smoke-Test-Sequenz** für die Mobile-Companion-Pflichtpfade:
```bash
KEY=$(awk -F= '/^API_SERVER_KEY=/{print $2}' ~/.hermes/.env)

# 1. API läuft, Bearer-Auth funktioniert
curl -s -H "Authorization: Bearer $KEY" http://127.0.0.1:8642/v1/models

# 2. Sessions-Endpoint für Mobile-App-Liste
curl -s -H "Authorization: Bearer $KEY" http://127.0.0.1:8642/api/sessions | head -c 300

# 3. Capabilities zeigt der App was alles geht
curl -s -H "Authorization: Bearer $KEY" http://127.0.0.1:8642/v1/capabilities | python3 -m json.tool

# 4. Detailed Health zeigt beide Plattformen "connected"
curl -s -H "Authorization: Bearer $KEY" http://127.0.0.1:8642/health/detailed | python3 -m json.tool

# 5. SSE-Stream-Test (3 Sek Sample)
timeout 3 curl -N -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"test","messages":[{"role":"user","content":"hi"}],"stream":true}' \
  http://127.0.0.1:8642/v1/chat/completions
```

## Known-Stolpersteine (konsolidiert 2026-07-10)

- **Default-Bind auf 127.0.0.1:** Frisch gestarteter API-Server ist nur Localhost erreichbar. Mobile-App im LAN/WAN kriegt Connection-Refused. Fix: `--host 0.0.0.0`.
- **`API_SERVER_KEY` fehlt in `.env`:** Mobile-App sendet Bearer-Token, Server lehnt ab mit 401. Symptom: App zeigt "Unauthorized".
- **TCP_NODELAY nicht aktiv:** Mobile-UX fühlt sich träge an, Burst-Stream-Problem auf Mobilfunk schlimmer als auf WiFi.
- **Port 8642 vs. Dashboard-Port 9119:** Zwei verschiedene Server, beide müssen laufen wenn die Mobile-App Drawer-Features nutzen soll.
- **`pkill -f "hermes_cli.main"` killt die eigene Terminal-Subshell:** Match zu breit, erwischt den Hermes-Terminal-Wrapper. Exit -15 (SIGTERM). Fix: PID-basiert (`ps -eo pid,args | grep ... | awk '{print $1}' | xargs kill -TERM`) oder über `systemctl --user stop`.
- **`systemctl Restart=always` + Port-Konflikt = Endlosschleife:** Service restartet sich endlos wenn alter Prozess noch Port hält. Fix: Testphase `disabled`, nach Smoke-Test `enable`.
- **TCP_NODELAY-Patch `git apply` schlägt fehl bei Hermes-Drift > ~20 Commits:** Patch-Hunk-Offsets stimmen nicht mehr. Fix: manuell portieren wie oben beschrieben.
- **`tailscale serve <URL>` ersetzt Config:** WebUI auf 8787 ist nach erstem Hermes-API-Serve weg. Fix: `--https=<PORT>` Multi-Service-Variante oder alle Services in einem Schritt.
- **Hermes-Dashboard Host-Header-Validierung:** Lehnt Tailscale-Requests ab mit "Invalid Host header" wenn `--host 127.0.0.1`. Fix: `--host 0.0.0.0`.
- **`hermes dashboard` als `terminal(background=true)`:** Stirbt beim Subshell-Cleanup mit exit 143 + Crashpad-Fehler. Fix: systemd-user-unit.
- **Python-Server Bytes-Literals:** Umlaute/em-dash in `b"..."` → `SyntaxError: bytes can only contain ASCII literal characters`. Nur ASCII in Bytes-Literals.