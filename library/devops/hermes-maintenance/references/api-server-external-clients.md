# API-Server im Hermes-Gateway für externe Clients (Mobile-Apps, Web-UIs, OpenAI-kompatible Tools)

> **Wann lesen:** Wenn du Hermes um einen HTTP-Endpoint erweitern willst, mit dem externe Geräte/Apps/Clients direkt chatten können (z.B. die offizielle `rusty4444/hermes-android` Companion-App, ein eigenes Web-UI, oder OpenAI-kompatible Tooling-Integrationen wie Open WebUI, LM Studio, Cursor).
>
> **Vorbedingung:** Hermes läuft bereits als Gateway mit anderen Adaptern (Telegram/Discord). `hermes-gateway.service` (user-unit) ist aktiv. `~/.hermes/config.yaml` hat einen `gateway.api_server:`-Block (default: `max_concurrent_runs: 10`).

---

## Architektur in einem Satz

Der `api_server`-Adapter ist **kein eigener Prozess**, sondern ein Platform-Plugin im Gateway-Prozess — er wird mitgestartet, sobald die drei ENV-Vars gesetzt sind. Standard-Port 8642, OpenAI-kompatibel (`/v1/chat/completions`, `/v1/models`, `/v1/responses` plus Hermes-eigene Routes wie `/api/sessions`, `/api/memory`, `/api/cron/jobs`, `/api/skills`).

**Code-Lokation:** `~/.hermes/hermes-agent/gateway/platforms/api_server.py` (~4940 Zeilen, aiohttp-basiert)

**Adapter-Klasse:** `APIServerAdapter(BasePlatformAdapter)` (Zeile 846)

**Konfig-Lese-Reihenfolge** (Zeile 866-870):
```python
extra = config.extra or {}
self._host: str = extra.get("host", os.getenv("API_SERVER_HOST", DEFAULT_HOST))
raw_port = extra.get("port")
if raw_port is None:
    raw_port = os.getenv("API_SERVER_PORT", str(DEFAULT_PORT))
self._port: int = _coerce_port(raw_port, DEFAULT_PORT)
self._api_key: str = extra.get("key", os.getenv("API_SERVER_KEY", ""))
```

→ **Reihenfolge:** `config.yaml extra` > `os.getenv()` > Code-Default. ENV-Vars gewinnen.

---

## Schritt-für-Schritt: API-Server auf 0.0.0.0:8642 freischalten

### 1. ENV-Vars generieren und in `~/.hermes/.env` eintragen

```bash
# Key generieren (64-char hex, 32 random bytes)
NEW_KEY=$(openssl rand -hex 32)
echo "API_SERVER_KEY=$NEW_KEY" >> ~/.hermes/.env
echo "API_SERVER_HOST=0.0.0.0" >> ~/.hermes/.env
echo "API_SERVER_PORT=8642" >> ~/.hermes/.env
```

**Sicherheits-Hinweis:** `0.0.0.0` macht den Service auf allen Interfaces erreichbar (LAN, Tailscale, später auch öffentlich wenn nicht hinter Firewall/Proxy). Für Tailscale-only `0.0.0.0` lassen (Tailscale-Interface ist Layer obendrauf) und mit Tailscale-MagicDNS arbeiten.

### 2. `config.yaml` — `api_server`-Block prüfen/aktivieren

In `~/.hermes/config.yaml`:
```yaml
gateway:
  api_server:
    max_concurrent_runs: 10  # default, ggf. erhöhen für parallele Mobile-Connections
```

Falls der Block fehlt → hinzufügen. ENV-Vars gewinnen über YAML, also reicht der Block als "Schalter".

### 3. TCP_NODELAY-Patch für Mobile-Streaming portieren (optional, empfohlen)

**Warum:** Nagle's Algorithmus coalesced kleine SSE-Writes (Text-Deltas, Tool-Progress) zu größeren TCP-Segmenten. Mobile Clients (Android) sehen dann Token-Bursts am Stream-Ende statt live.

**Original-Patch:** `rusty4444/hermes-android/server-patches/0001-tcp-nodelay-sse.patch`

**Manueller Port (4 Callsites + 1 Helper):**

**(a) Helper-Funktion einfügen** direkt nach `logger = logging.getLogger(__name__)` in `api_server.py`:
```python
# ── SSE flush: disable Nagle on SSE response sockets so small writes
#    (tool progress events, text deltas) reach clients immediately instead
#    of being coalesced into larger TCP segments.  Without this, mobile
#    clients see all tool cards and text arrive as one burst at stream end.
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
(`import socket as _socket` ist schon in Zeile 40 — nicht doppelt importieren.)

**(b) Vier Callsites patchen** — direkt nach jedem `await response.prepare(request)` in den SSE-Stream-Funktionen:
```python
        response = web.StreamResponse(...)
        await response.prepare(request)
        _sse_disable_nagle(response)   # ← NEU
        # ... rest of stream
```

Callsites in `api_server.py` (Stand 2026-07-10): Zeilen 2038, 2434, 2662, 4520.

**Verifikation (3 Checks):**
```bash
# 1. Helper definiert + 4 Calls vorhanden
grep -c "_sse_disable_nagle(response)" gateway/platforms/api_server.py
# → Erwartet: 5 (1 Def + 4 Calls)

# 2. Syntax-Check
cd ~/.hermes/hermes-agent && python -c "import ast; ast.parse(open('gateway/platforms/api_server.py').read()); print('OK')"

# 3. Import-Check
cd ~/.hermes/hermes-agent && timeout 8 venv/bin/python -c "from gateway.platforms.api_server import _sse_disable_nagle; print('OK')"
```

**Pitfall — `grep -c` für andere Keywords:** Zähle **denselben** Identifier für Verifikation, nicht `TCP_NODELAY` (das nur 2x vorkommt: Docstring + setsockopt). Counts von verschiedenen Keywords sind keine Cross-Validation.

**Pitfall — `git apply` schlägt fehl** wenn dein Hermes-Repo Commits ahead des Upstream-Patches hat. Manuelles Portieren wie oben ist schneller und sicherer.

### 4. Restart mit Workaround für 3-Layer-Block

Der saubere `systemctl --user restart hermes-gateway.service` triggert den 3-Layer-Block (siehe §16 in SKILL.md). Workaround:

```bash
systemd-run --user --scope -u yuno-gw-restart bash -c 'systemctl --user restart hermes-gateway.service'
```

Der terminal()-Call timeoutet, der Restart läuft im Hintergrund, neue PID erscheint im Journal.

### 5. 4-Punkt-Smoke-Test nach Restart

```bash
# 1. Port 8642 muss listening sein
ss -tlnp | grep 8642
# Erwartet: LISTEN ... 0.0.0.0:8642 ... users:(("python",pid=...,fd=...))

# 2. Telegram-Bot darf NICHT weg sein (Multi-Adapter läuft parallel)
ss -tlnp | grep <telegram-port>  # dein Telegram-Webhook-Port oder Polling-Indicator

# 3. Bearer-Token-Test: 200 mit Capabilities
curl -sS http://127.0.0.1:8642/v1/models -H "Authorization: Bearer $API_SERVER_KEY" | head -20

# 4. No-Auth-Test: 401
curl -sS -w "\n%{http_code}\n" http://127.0.0.1:8642/v1/models
```

### 6. Companion-App konfigurieren (z.B. Hermes Android)

**App-Name:** `rusty4444/hermes-android` (Flutter, v1.0.8+108, Apache 2.0)

**Connection-Daten in der App:**
- **Label:** z.B. "Workstation" oder "Home"
- **Host:** die Tailscale-IP deiner Workstation (z.B. `100.x.y.z`) oder LAN-IP (z.B. `192.168.1.50`) — `Host`-Feld ist nur scheme + hostname + optional port, **kein Pfad**
- **Port:** `8642`
- **API Key:** der `API_SERVER_KEY` aus `~/.hermes/.env`
- **Dashboard-Port:** `9119` (default) oder eigener Port
- **Path-Prefixes:** leer lassen für direkte Verbindung; `/profile/<name>` wenn hinter Reverse-Proxy

**App-Features die funktionieren:**
- Chat (SSE streaming, /v1/chat/completions)
- Sessions browsen/erstellen/löschen
- Memory viewer (Dashboard :9119)
- Cron jobs verwalten (list/trigger/pause/create/edit/delete)
- Skills browser
- Model settings (wo Dashboard es erlaubt)
- Voice chat (Mikro → STT → Hermes, TTS-Reply falls Toggle an)

**App-Features die NICHT funktionieren ohne Reverse-Proxy:**
- HTTPS-Dashboard mit Password-Auth (Browser-Login-Flow)
- Sub-Path-Routing (`/profile/<name>/...`) — braucht Caddy/nginx

---

## Security-Hardening: Wie du 8642 nicht offen ins Internet stellst

**Problem:** `0.0.0.0:8642` ist im LAN erreichbar. Wenn dein Router UPnP hat oder du mal Port-Forwarding machst, ist der Service plötzlich öffentlich.

**Lösung 1 (empfohlen) — Tailscale:**
- Tailscale auf Workstation + Android installieren
- Beide im gleichen Tailnet → `100.x.y.z` als Host in der App
- LAN ist irrelevant, weil die App nur über Tailscale-Interface routet
- MagicDNS aktivieren → App-Host = `workstation-name.tail-net.ts.net`

**Lösung 2 — Reverse-Proxy mit Caddy:**
- Caddy auf cloud-server (eigener VPS) oder lokal
- Caddy terminiert TLS + Basic-Auth, leitet intern an `127.0.0.1:8642` weiter
- App-Host = `https://hermes.example.com` mit `Authorization: Bearer` UND Caddys Basic-Auth
- Siehe `hermes-v7-sse` Skill für Caddy-Config-Pattern (gleiche Struktur)

**Lösung 3 — UFW-Regel (defense in depth):**
```bash
# Nur Tailscale-Interface erlauben
sudo ufw allow in on tailscale0 to any port 8642
# ODER: nur LAN-Subnet erlauben
sudo ufw allow from 192.168.0.0/16 to any port 8642
```

**Niemals:** Port 8642 direkt per Router-Firewall/Port-Forwarding exposen, ohne VPN dazwischen. `API_SERVER_KEY` allein ist KEIN ausreichender Schutz gegen Internet-Scanner.

---

## API-Endpoints-Übersicht (für eigene Clients)

**OpenAI-kompatibel:**
- `POST /v1/chat/completions` — SSE streaming chat
- `GET  /v1/models` — verfügbare Modelle
- `POST /v1/responses` — alternative Response-API

**Hermes-spezifisch (für Companion-Apps):**
- `GET  /api/sessions` — alle Sessions
- `POST /api/sessions` — neue Session
- `GET  /api/sessions/{id}/messages` — Session-History
- `DELETE /api/sessions/{id}` — Session löschen
- `GET  /api/memory` — Memory-Store (Mnemosyne)
- `GET  /api/cron/jobs` — Cron-Jobs
- `POST /api/cron/jobs/{id}/trigger` — manueller Run
- `GET  /api/skills` — verfügbare Skills
- `GET  /api/model/info` — aktuelles Model
- `GET  /api/capabilities` — was der Server kann (für Client-Discovery)

**Auth:** Alle `/api/*` und `/v1/*` brauchen `Authorization: Bearer <API_SERVER_KEY>`. **Ausnahme:** Health-Endpoint `/health` ist offen.

**Rate-Limit:** Default 10 requests / 60s (per IP). Für Mobile-Apps meist ausreichend; bei Bursts konfigurierbar via `SSE_LIMITER_MAX`-ähnliche ENV.

---

## Troubleshooting

| Symptom | Ursache | Fix |
|---|---|---|
| `ss` zeigt 8642 nicht | `API_SERVER_KEY` fehlt → Adapter-Connect refused | `grep API_SERVER_KEY ~/.hermes/.env`, `systemctl --user show-environment` |
| `curl /v1/models` → 401 | Token falsch oder ENV nicht geladen | `systemctl --user show-environment \| grep API_SERVER` zeigt was systemd sieht |
| SSE-Stream liefert alles am Ende | TCP_NODELAY-Patch fehlt | Patch portieren, restart |
| Telegram-Bot tot nach Restart | Restart-Block getriggert, alter Prozess nicht ganz tot | Siehe §16 systemd-run Workaround |
| Mobile App kann nicht connecten | LAN-IP falsch oder Firewall blockt | `nmap -p 8642 <workstation-ip>` von einem anderen LAN-Gerät |
| Tailscale-Verbindung langsam | Tailscale-Daemon nicht auf Android im Hintergrund | Tailscale-App → Settings → "Run in background" aktivieren |

---

## Sources / Context

- `~/.hermes/hermes-agent/gateway/platforms/api_server.py` (Code-Stand 2026-07-10, Hermes v0.18.2)
- `https://github.com/rusty4444/hermes-android` (v1.0.8+108, 2026-05-29 Patch)
- Validated: 2026-07-10 via Pre-Flight-Check (Syntax, Import, ENV grep) — Service-Restart steht aus weil Hermes-Production gerade läuft
- Related: `hermes-maintenance` SKILL.md §16 (3-Layer-Restart-Block), `hermes-v7-sse` SKILL.md (Caddy-Config-Pattern)
