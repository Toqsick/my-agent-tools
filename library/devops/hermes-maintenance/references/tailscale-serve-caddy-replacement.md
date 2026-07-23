# Tailscale Serve — Caddy-Alternative für tailnet-only Hermes-Exposure

> **Wann lesen:** Wenn du den Hermes-API-Server (oder andere Hermes-Services) **im Tailscale-Tailnet** für Mobile-Clients/Companion-Apps exposen willst, OHNE eigene Domain, OHNE Caddy/nginx, OHNE Cloud-Server-Konfiguration. Funktioniert auch wenn cloud-server noch nicht konfiguriert ist oder SSH-Keys fehlen.

> **Vorbedingung:** Tailscale ist auf Workstation UND allen gewünschten Clients (z.B. Android) installiert. Alle im selben Tailnet. MagicDNS läuft (Suffix sichtbar via `tailscale dns status`).

---

## Architektur in 3 Sätzen

Tailscale Serve bietet HTTPS mit automatischem Let's-Encrypt-ähnlichem Cert (Tailscale-intern, nicht öffentlich), auf einer MagicDNS-Subdomain wie `https://workstation-name.tailXXXXXX.ts.net`. Jeder Service auf einer Workstation bekommt einen Port (`:443`, `:8443`, `:8444` etc.) und wird via `tailscale serve --bg <URL>` registriert. **Wichtig:** Tailscale Serve ist **NICHT additiv** — jeder Aufruf ersetzt die komplette Config des jeweiligen Ports.

---

## Tailscale Serve vs. Caddy — Wann was?

| Kriterium | Tailscale Serve | Caddy auf cloud-server |
|---|---|---|
| **Setup-Aufwand** | 1-3 Befehle pro Service | Domain kaufen, DNS, Caddy installieren, Caddyfile schreiben |
| **Kosten** | 0 € (Tailscale-Free reicht) | ~$5-25/Monat VPS |
| **TLS** | Auto, Tailscale-CA | Auto, Let's Encrypt (echte öffentliche CA) |
| **Auth** | Bearer-Token via Backend (z.B. `API_SERVER_KEY`) | Basic-Auth + Bearer-Auth kombinierbar |
| **Tailnet-only** | ✅ by design (nur Tailscale-Nodes) | ❌ öffentlich erreichbar (Firewall nötig) |
| **Öffentlich erreichbar** | ❌ (außer via `tailscale funnel`) | ✅ |
| **Custom Domain** | ❌ (nur `<host>.tailXXXX.ts.net`) | ✅ |
| **Always-On** | nur wenn Workstation läuft | ✅ wenn cloud-server läuft |
| **Reverse-Proxy auf Workstation** | ❌ (läuft direkt auf Workstation) | ✅ (Tailscale- oder LAN-Tunnel) |
| **Path-basiertes Routing auf einem Port** | ❌ (jeder Service = eigener Port) | ✅ (Caddyfile-Snippet) |
| **CORS-Header anpassbar** | ❌ (nur passthrough) | ✅ |

→ **Tailscale Serve** ist die richtige Wahl wenn: nur Tailscale-Clients connecten, kein Always-On gebraucht, kein CORS-Customizing, keine path-basierten Routes nötig.

→ **Caddy/cloud-server** ist die richtige Wahl wenn: 24/7-Verfügbarkeit, öffentlicher Zugriff, komplexe Routing-Regeln, oder Basic-Auth vor Bearer-Auth.

---

## Step-by-Step: Hermes API + WebUI + Dashboard via Tailscale Serve

### 1. Aktuellen State checken

```bash
tailscale serve status
# Erwartet: "No serve config" ODER bestehende Config
tailscale status | head -10
# MagicDNS-Suffix aus dem Output ablesen
```

### 2. Hermes-API exposen (Port 443 = default HTTPS)

```bash
tailscale serve --bg http://127.0.0.1:8642
# → "Available within your tailnet: https://<host>.tailXXXX.ts.net/"
```

### 3. Zweiten Service auf anderem Port exposen (Port 8443)

Tailscale Serve unterstützt pro Port nur EINEN Service. Für Multi-Service:
```bash
tailscale serve --bg --https=8443 http://127.0.0.1:8787   # Yuno WebUI
tailscale serve --bg --https=8444 http://127.0.0.1:9119   # Hermes Dashboard
```

### 4. Status prüfen

```bash
tailscale serve status
# Erwartet:
# https://<host>.tailXXXX.ts.net (tailnet only)
# |-- / proxy http://127.0.0.1:8642
#
# https://<host>.tailXXXX.ts.net:8443 (tailnet only)
# |-- / proxy http://127.0.0.1:8787
```

### 5. Smoke-Tests

```bash
KEY=$(grep "^API_SERVER_KEY=" ~/.hermes/.env | cut -d= -f2)

# Hermes API
curl -sk --max-time 8 -w "HTTP %{http_code}\n" \
  -H "Authorization: Bearer $KEY" \
  "https://<host>.tailXXXX.ts.net/v1/models"
# → HTTP 200, JSON

# WebUI
curl -sk --max-time 8 -w "HTTP %{http_code}\n" \
  "https://<host>.tailXXXX.ts.net:8443/"
# → HTTP 302 (Login-Redirect) oder 200 (wenn schon eingeloggt)
```

### 6. In der Companion-App konfigurieren

- **Host**: `<host>.tailXXXX.ts.net` (voller MagicDNS-Name, kein Port im Host-Feld)
- **Port**: `443` (default für HTTPS)
- **API Key**: der `API_SERVER_KEY`-Wert
- **Dashboard Port**: `8444` (der exposed Port, NICHT 9119!)
- **Dashboard behind proxy**: ✅ (Tailscale injiziert bereits Auth via Cert)

---

## Pitfalls (eigene Erfahrungen 2026-07-10)

### Pitfall 1: `tailscale serve` ist NICHT additiv

Jeder `tailscale serve --bg <URL>`-Aufruf **ersetzt** die komplette Config für den jeweiligen `--https`-Port. Wenn du erst WebUI auf :443 exposen willst, dann Hermes-API dazu — das WebUI verschwindet.

**Fix:** Port-Trennung statt path-basiertem Routing. Jeder Service bekommt einen eigenen `--https=<port>`.

**Anti-Pattern-Versuch mit `tailscale serve set-config`:**
```bash
# Was ich versucht habe (funktioniert NICHT in Tailscale 1.98.8):
tailscale serve set-config /tmp/multi-route.yaml --service=svc:web
# → "must specify filename" oder "invalid service name"
# Workaround: set-config ist in der Version instabil, Port-Trennung nutzen
```

### Pitfall 2: WebUI redirectet zu Login wenn Catch-All-Route

Wenn du Tailscale Serve mit `tailscale serve --bg http://127.0.0.1:8787` exposen willst und der WebUI-Server auf Port 8787 ein catch-all `/` mit Login-Redirect hat, dann landen ALLE Requests dort — auch wenn du `/v1/models` aufrufst (Tailscale proxiet das ja eigentlich zu 8642, aber bei Reset-Confusion kann das passieren).

**Diagnose:**
```bash
curl -sk -w "%{http_code} %{url_effective}\n" "https://<host>.tailXXXX.ts.net/v1/models" | head -3
# Wenn das HTML zurückgibt statt JSON → falsche Config
```

**Fix:** `tailscale serve reset` und mit Port-Trennung neu aufbauen.

### Pitfall 3: 302 statt 200 bei HTTPS-Test

Wenn dein Hermes-API nur HTTP spricht (kein HTTPS-Server), aber Tailscale macht HTTPS draus — der Test kann 302 zurückgeben statt direkt die JSON.

**Diagnose:** Mit `-L` (follow redirects) testen, um den wahren Endpoint zu sehen.
```bash
curl -skL -w "\nFinal: %{url_effective}, HTTP %{http_code}\n" \
  -H "Authorization: Bearer $KEY" \
  "https://<host>.tailXXXX.ts.net/v1/models"
```

**Wenn Tailscale Serve richtig konfiguriert ist, kommt 200 mit JSON direkt.**

### Pitfall 4: Reset vergisst nicht nur WebUI sondern auch Hermes-API

Wenn du `tailscale serve reset` machst um eine kaputte Config zu clearen, ist BEIDES weg. Du musst ALLE Services neu registrieren:
```bash
tailscale serve --bg http://127.0.0.1:8642
tailscale serve --bg --https=8443 http://127.0.0.1:8787
tailscale serve --bg --https=8444 http://127.0.0.1:9119
```

### Pitfall 5: Android-Tailscale muss im Hintergrund laufen

Die Companion-App funktioniert nur wenn Tailscale auf dem Handy aktiv ist. Tailscale Free hat 1-Device-Limit, Tailscale Personal hat unbegrenzt.

**Check auf dem Handy:** Tailscale-App öffnen → Status muss "Connected" sein. "Run in background" in den Android-Tailscale-Settings aktivieren.

---

## Reversibility

```bash
# Komplett zurücksetzen
tailscale serve reset

# Einzelnen Service stoppen
tailscale serve --https=8443 off

# Wieder aktivieren
tailscale serve --bg --https=8443 http://127.0.0.1:8787
```

---

## Kombination mit Caddy (Hybrid-Setup)

Für die Basti-typische Hybrid-Architektur (Workstation = Daten, cloud-server = Proxy):

```
┌──────────────┐                    ┌───────────────┐                ┌──────────────┐
│ Android App  │──────HTTPS────────►│ cloud-server  │──Tailscale────►│ Workstation  │
│ (Galaxy S8)  │                    │ (Caddy)       │   WireGuard    │ (Hermes)     │
└──────────────┘                    │  Basic-Auth   │   100.x.y.z    │  :8642       │
                                    │  + TLS-Term   │                │  :9119       │
                                    │  :443 public  │                │  :8787       │
                                    └───────────────┘                └──────────────┘
```

**Vorteil:** Workstation kann aus sein wenn man nur Mobile-UI nutzen will, cloud-server ist 24/7 da.
**Nachteil:** Komplexer — cloud-server-Setup nötig, SSH-Keys, Caddyfile, DNS, etc.

→ Für die meisten Fälle (Workstation läuft eh beim Basti-Szenario) reicht **Tailscale Serve ohne cloud-server** wie oben beschrieben.

---

## Sources / Context

- Tailscale Serve Doku: <https://tailscale.com/kb/1242/funnel> und <https://tailscale.com/kb/1247/funnel-serve-use-cases>
- Validated: 2026-07-10 auf bratan-17-P1 (Ubuntu 24.04, Tailscale 1.98.8, MagicDNS-Suffix `tail94d785.ts.net`)
- Pattern: 3 Befehle ersetzen komplettes Caddy-Setup für Tailnet-only Use-Case
- Tailscale-DNS-Suffix rausfinden: `tailscale dns status | grep "MagicDNS"`
