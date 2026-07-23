# Network Service Security Audit — Hermes Gateway (2026-07-16)

**Referenz-Dokument für Layer-4-Audit-Methodik (siehe `system-security-audit` → Layer 4).**
Dieses Dokument hält das vollständige Audit-Protokoll der Gateway-Inspektion vom 2026-07-16 — dient als konkrete Vorlage für zukünftige Network-Service-Audits.

---

## Kurzfassung

| Frage | Antwort |
|-------|---------|
| **Service** | Hermes-Gateway API-Server (Port 8642) |
| **Bindung** | `0.0.0.0:8642` — absichtlich für Hermes-Android-Hybrid-Hosting (Tailscale Serve) |
| **Auth** | Bearer-Token `API_SERVER_KEY` via `hmac.compare_digest` — aktiv enforced |
| **Ausnahmen** | `/health` und `/v1/health` ohne Auth (Liveness-Probes) |
| **Start** | Manuelle Reaktivierung 2h26min nach Boot (14:10:14 vs 11:43:58) |
| **Severity** | **P2** — kein P0, aber zwei P1-Empfehlungen |
| **Report** | Vollständig in `/tmp/gateway-audit-2026-07-16.md` |

---

## Phase 1: Live Route Probing

11 Endpoints auf `127.0.0.1:8642` ohne Auth-Header:

| Method | Path | Status | Body / Hinweis |
|--------|------|--------|----------------|
| GET | `/` | 404 | `404: Not Found` |
| GET | `/health` | **200** | `{"status":"ok","platform":"hermes-agent","version":"0.18.2"}` |
| GET | `/health/detailed` | **401** | Auth-geschützt (schützt PID/Uptime/Platform-States) |
| GET | `/v1/health` | 200 | identisch zu `/health` |
| GET | `/v1/models` | 401 | Auth-Pflicht |
| GET | `/v1/toolsets` | 401 | Auth-Pflicht |
| GET | `/v1/skills` | 401 | Auth-Pflicht |
| GET | `/v1/capabilities` | 401 | Auth-Pflicht |
| GET | `/api/sessions` | 401 | Auth-Pflicht |
| GET | `/api/` | 404 | — |
| GET | `/api` | 404 | — |

**Vollständige Route-Tabelle** (aus Source: `api_server.py:1320-1358`): ~38 Endpoints inkl. Discovery (`/v1/{models,capabilities,skills,toolsets}`), Sessions-CRUD (`/api/sessions/...`), Chat (`/v1/chat/completions`, `/v1/responses`), Jobs (`/api/jobs/...`), Runs (`/v1/runs/...`), Cron-Fire (`/api/cron/fire`), Multiplex-Mirror (`/p/{profile}/...`).

Server-Header: `Python/3.11 aiohttp/3.14.1` — aiohttp, nicht FastAPI.

---

## Phase 2: Configuration Source Tracing

**Konfigurations-Pfad:**
```
Env: API_SERVER_HOST=0.0.0.0   (aus ~/.hermes/.env)
Env: API_SERVER_PORT=8642       (aus ~/.hermes/.env)
Env: API_SERVER_KEY=<64-hex>    (aus ~/.hermes/.env)
Code-Default: host=127.0.0.1, port=8642, key="" (api_server.py:937-942)
Config.yaml: api_server: { max_concurrent_runs: 10 } — KEINE host/port/key-Override
Unit: ExecStart=/.../python -m hermes_cli.main gateway run (keine CLI-Args für host/port)
```
→ **Bindung folgt Env → `0.0.0.0` ist bewusst gesetzt für Hermes-Android-Companion (Tailscale-Serve)**

**Defaults wenn Env leer wären:** `127.0.0.1:8642` mit leerem Key → `connect()` refused to start (Fail-Closed).

**Referenzierte Doku:**
- `~/.hermes/skills/devops/hermes-maintenance/references/api-server-external-clients.md` — Setup-Details
- `~/.hermes/pending/memory/838383b3.json` — "API-Server auf 0.0.0.0:8642 für Hermes-Droid-App via Tailscale Serve"

---

## Phase 3: Auth Mechanism Verification

**Implementierung** (`api_server.py:1224-1248`):
```python
def _check_auth(self, request):
    if not self._api_key:         # Fail-Closed im Startup, nicht im Handler
        return None               # Existiert nur für Tests — connect() startet nicht ohne Key
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
        if hmac.compare_digest(token, self._api_key):
            return None
    return web.json_response({"error":{"message":"Invalid API key",...}}, status=401)
```

| Check | Befund |
|-------|--------|
| Typ | Bearer-Token |
| Vergleich | `hmac.compare_digest` — constant-time ✅ |
| Bypass bei leerem Key | `connect()` refused to start **vor** dem Adapter-Start (Fail-Closed) ✅ |
| Ausnahmen | `/health` + `/v1/health` absichtlich offen |
| Logging | Jeder Reject: `remote/peer_ip/method/path/user_agent` ✅ |
| `/health/detailed` | Explizit auth-geschützt (schützt PID, Uptime, Platform-States) |
| Cron-Fire | Sonder-Auth via NAS-minted JWT, nicht API_SERVER_KEY |

**Edge Cases:**
1. Wenn `API_SERVER_KEY` im Betrieb zurückgesetzt wird → Server läuft ohne Auth weiter (Key-Wechsel erfordert Restart)
2. Bei Direktstart des api_server-Adapters ohne Gateway (z.B. Test-Script) könnte der No-Auth-Pfad greifen wenn der Key leer ist

---

## Phase 4: Network Exposure Assessment

### Host-Interfaces
```
lo         127.0.0.1/8
enp3s0     192.168.178.92/24   ← LAN
tailscale0 100.96.90.61/32      ← Tailnet
docker0    172.17.0.1/16
br-*       172.18-20.0.1/16     ← Docker-Bridges
```

### Port-Bindung
`0.0.0.0:8642` → auf **allen** Interfaces hörbar:
- `192.168.178.92:8642` — **LAN-Zugriff** (per Router erreichbar)
- `100.96.90.61:8642` — **Tailnet-Zugriff** (SSH-Attacke)
- `172.17-20.0.1:8642` — **Docker-Container-Zugriff**

### Firewall
Keine UFW/nft-Regel die 8642 auf Tailscale beschränkt.

### Tailscale Exposure
`tailscale serve status` nicht im Audit aufgerufen (kein Zugriff — kann nachgeholt werden), aber gemäß Memory existieren Tailscale-Funnel-Routen.

### Bewertung
| Kanal | Erreichbarkeit | Auth | Risiko |
|-------|---------------|------|--------|
| LAN (192.168.xxx) | ✅ Erreichbar | ✅ Bearer-Token nötig | 🟡 P1 — Token ist einzige Schutzlinie |
| Tailnet (100.96.xxx) | ✅ Erreichbar | ✅ Bearer-Token nötig | 🟢 Gewollt (Android-App) |
| Docker (172.x) | ✅ Erreichbar | ✅ Bearer-Token nötig | 🟡 P1 — Container haben Token-Zugriff |
| Firewall-Schutz | ❌ Kein Fronting | — | ⚠️ P1 — Firewall fehlt |

---

## Phase 5: Process Lifecycle Tracking

```
Boot (PID 1 init):            2026-07-16 11:43:58 CEST
Systemd --user (PPID=1959):   seit Boot (ELAPSED 02:33)
Gateway PID 29969 START:      2026-07-16 14:10:14 CEST
Differenz Boot→Start:         2h 26min 16s

PPID-Kette:
  PID 29969 → PPID 1959 → systemd --user → PID 1 (init)
  Kein bash/terminal in der Kette → systemd-gesteuerter Start
```

**Befund:** Manuelle Reaktivierung. Service ist enabled (`WantedBy=default.target`), wurde aber nicht beim Boot gestartet. Log zeigt `Previous gateway exited cleanly — skipping session suspension` → kein Crash, sondern geplanter Start zwischen 13.07 und 16.07 per `hermes gateway start`. Grund: vermutlich `loginctl enable-linger` fehlt.

**Systemd-Unit:**
```
Unit: ~/.config/systemd/user/hermes-gateway.service
ExecStart: /home/bratan/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main gateway run
Restart: always
Environment geladen: HERMES_HOME, PATH, VIRTUAL_ENV
→ KEIN API_SERVER_HOST oder API_SERVER_PORT in der Unit → Werte aus .env
```

---

## Phase 6: Risk Classification

| # | Finding | Severity | Begründung | Empfehlung |
|---|---------|----------|------------|------------|
| 1 | `0.0.0.0` ohne IP-Firewall | **P1** | LAN + Docker können Port erreichen; Token ist einzige Schutzlinie. Code warnt selbst vor `hermes-0day`-Klasse | Firewall: 8642 nur auf `tailscale0` |
| 2 | Terminal-Backend=local | **P1** | Jeder gültige Token-Besitzer hat RCE auf Host-User via `/v1/chat/completions` | `terminal.backend: docker` in config.yaml |
| 3 | Auth enforced | ✅ OK | hmac.compare_digest für alle Data-Endpoints | Keine Aktion |
| 4 | Service nicht beim Boot | ✅ OK | Nachvollziehbar durch Laptop-Resume | `loginctl enable-linger` prüfen |
| 5 | Health-Version-Disclosure | **P3** | `/v1/health` gibt `version: 0.18.2` preis | Version aus Health entfernen |
| 6 | Token in `.env` ohne Vault | **P2** | 0600-Sicherung ok, aber Backup/Export kann Token leaken | In 1password Vault überführen |

### Empfehlungstabelle

| # | Aktion | Severity | Owner |
|---|--------|----------|-------|
| 1 | Firewall: 8642 auf `tailscale0` (100.96.90.61/32) beschränken, nicht auf `enp3s0` | **P1** | User |
| 2 | `terminal.backend: docker` setzen | P1 | User |
| 3 | `API_SERVER_KEY` in 1password Vault | P2 | User |
| 4 | Tailscale-Serve-Routen dokumentieren | P2 | Docs |
| 5 | Health-Version-Disclosure patchen | P3 | Ops |
| 6 | `loginctl enable-linger` prüfen für Auto-Start | Info | User |

---

## Lessons Learned (für zukünftige Layer-4-Audits)

### Was gut funktioniert hat

- **Parallel-Scan zu Beginn** (11 curl-Calls in einem `for`-Loop) — sofortiges Routing-Heatmap, keine serialisierten Roundtrips
- **Source-Code-Grep auf `_check_auth`** — findet den Auth-Handler unabhängig von Dokumentation. `grep -n 'def _check_auth\|return web.json_response.*401'` ist ausreichend für den ersten Auth-Check
- **`ss -tlnp` + `ip -o addr show`** — die Kombination zeigt sofort ob der Dienst auf mehr Interfaces hört als der Admin denkt. `ss` ohne diese zweite Info lässt ein `0.0.0.0` wie nur ein Interface aussehen
- **Boot-Zeit vs. Start-Zeit Differenz** — der größte Erkenntnisgewinn des Audits. Ein Service der enabled ist aber 2h nach Boot startet, läuft nicht automatisch. Ohne diese Messung wäre die Antwort "läuft seit Boot" gewesen (falsch)
- **Log-History auf `Previous gateway exited` prüfen** — unterscheidet "Crash-Restart" von "Manual Start" sofort
- **gateway.log Warnung parsen** — der live-logged-Hinweis `[Api_Server] API server is network-accessible (0.0.0.0)...` ist ein direkter Beweis, dass der Entwickler das Risiko kennt. Zitieren im Report verhindert "das haben wir nicht gewusst"-Diskussionen

### Was besser geht

- **`tailscale serve status` und `funnel status`** vergessen — nachdem Tailscale als Grund genannt wurde, hätte der Audit auch die aktuellen Funnel-Routen checken sollen. Für Layer-4-Audits auf Tailscale-Boxen immer als eigenen Schritt dokumentieren
- **`/health/detailed` ohne Auth überascht** — das ist dokumentiert (Doc-String), aber die Route-Definition und der Handler waren 1300 Zeilen auseinander im Code. Systematischer: Routes-Tabelle + Auth-Map generieren, nicht manuell aus Source lesen

### Quellen / Artefakte

- Ausführlicher Report: `/tmp/gateway-audit-2026-07-16.md` (~10.9 KB)
- Gateway-Logs: `/home/bratan/.hermes/logs/gateway.log`
- Service-Unit: `/home/bratan/.config/systemd/user/hermes-gateway.service`
- Source-Code: `/home/bratan/.hermes/hermes-agent/gateway/platforms/api_server.py`
- Config: `/home/bratan/.hermes/.env` (API_SERVER_HOST/PORT/KEY)
