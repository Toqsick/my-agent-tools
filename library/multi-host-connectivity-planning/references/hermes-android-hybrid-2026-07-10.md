# Hermes-Android Hybrid-Hosting (Workstation + cloud-server)

**Stand:** 2026-07-10 · **Status:** Architektur validiert, Setup noch nicht ausgeführt (User-Phasen-Approval pending) · **Recon-Quelle:** `rusty4444/hermes-android` v1.0.8 von GitHub geclont, Stack analysiert, Server-Patch identifiziert.

## Pattern-Übersicht

Hermes bleibt auf der Workstation (alle Memory, Cron, Skills, Sessions lokal — kein Cloud-Sync nötig). Ein **schlanker Reverse-Proxy** (Caddy) auf `cloud-server` terminiert TLS, macht Auth, und tunnelt per **WireGuard/Tailscale** zum Heimnetz durch. Kein offener Port am Heimnetz, keine Cloud-Migration der Hermes-Daten.

```
┌──────────────────────┐         WireGuard/Tailscale      ┌─────────────────────────┐         HTTPS
│  Android (Tailscale) │◄───────────────────────────────►│  cloud-server (Caddy)   │◄────────────┘
│  Hermes-App          │  private, 100.x.y.z:8642        │  TLS-Terminator + Auth  │  (dein Handy,
│  v1.0.8              │  100.x.y.z:9119                 │  → tunnel → Workstation │  von überall)
└──────────────────────┘                                  └─────────────────────────┘
                                                                 │
                                                                 │  Tailscale encrypted tunnel
                                                                 ▼
                                                       ┌─────────────────────────┐
                                                       │  Workstation (Zorin)    │
                                                       │  Hermes Agent läuft     │
                                                       │  api_server :8642       │
                                                       │  dashboard    :9119     │
                                                       └─────────────────────────┘
```

## Warum Hybrid statt Cloud-Migration

| Kriterium | Cloud-Migration (Hermes auf cloud-server) | Hybrid (Workstation + Tunnel) |
|---|---|---|
| Always-On | ✅ | ✅ (durch Cloud-Proxy) |
| Daten-Sync nötig | ❌ schwer (Memory, Cron, Skills, Sessions) | ✅ keine — bleiben lokal |
| Kosten | GCP n2d-standard-2 ~$25/Mon | ~$5-10/Mon für den schlanken Proxy |
| Backup-Disziplin | Sync-Engine nötig | Workstation-Backup reicht |
| Security-Posture | Cloud = mehr Angriffsfläche | Heimnetz bleibt hinter WireGuard |
| Performance | 1-Hop Cloud-Latenz | 1-Hop WireGuard (oft schneller) |
| Komplexität | Hoch (Sync, Volumes, Sticky-Sessions) | Mittel (Tunnel + Caddy) |

**Wann Cloud-Migration besser wäre:** Wenn du von 3+ Geräten gleichzeitig schreibst, die alle State brauchen (Multi-User-Setup), oder Bastis-Workstation oft aus ist.

## Architektur-Komponenten im Detail

### Workstation-Seite (was schon läuft)
- **Hermes Messenger-Gateway** auf `127.0.0.1:35395` (random, user-services `hermes-gateway.service` + `hermes-gateway-yuno.service` in `~/.config/systemd/user/`)
- **Hermes API-Server** muss noch gestartet werden: `hermes api-server --host 0.0.0.0 --port 8642` — **noch NICHT ausgeführt** (Phase 1 wartet auf User-Freigabe)
- **Hermes Dashboard** muss auf `0.0.0.0:9119` exposed werden: `hermes dashboard --insecure --host 0.0.0.0 --tui --port 9119`
- **`API_SERVER_KEY`** fehlt komplett in `~/.hermes/.env` — muss generiert werden via `openssl rand -hex 32`

### cloud-server-Seite (was fehlt)
- **Caddy** mit TLS (Let's Encrypt via `dns-cloudflare` oder HTTP-Challenge), Basic-Auth vor Hermes-Endpoints
- **Tailscale** installiert + im gleichen Tailnet wie Workstation
- **Reverse-Proxy-Config** mit Path-Prefixes (Gateway vs. Dashboard) — siehe `messaging-gateway-setup/references/api-server-quirks.md` für die App-Erwartungen
- **Optional: Cloudflare-Tunnel** als zusätzlicher Fallback (kann auch ohne Tailscale laufen, aber dann ist Public-IP sichtbar)

### Android-Seite (was die App mitbringt)
- **Tailscale für Android** (kostenlos, ~30 MB, aus dem Play Store) — Voraussetzung für privates Netzwerk
- **Hermes-Android v1.0.8** — Flutter-Cross-Platform-App, hat Voice-Chat, Cron-Management, Memory-Viewer, Skills-Browser out-of-the-box
- **API-Key = `API_SERVER_KEY`** aus Workstation-`~/.hermes/.env`

## Phasen-Plan (vom Skill-Besitzer abgenickt)

### Phase 1 — Hermes lokal vorbereiten (PENDING)
- API-Server starten auf `0.0.0.0:8642` via `systemctl --user` (saubereres Restart-Model als `pkill` — beide User-Units `hermes-gateway.service` + `hermes-gateway-yuno.service` existieren bereits als Vorbild)
- Dashboard auf `0.0.0.0:9119` exposed
- `API_SERVER_KEY` generieren + eintragen
- TCP_NODELAY-Patch aus `rusty4444/hermes-android/server-patches/0001-tcp-nodelay-sse.patch` anwenden (4 SSE-Endpoints, ~22 Zeilen)
- Verifikation: `ss -tlnp | grep -E ':(8642|9119)'` zeigt beide auf 0.0.0.0, `curl /health` antwortet 200

### Phase 2 — Tailscale installieren + Key-Exchange
- Workstation: `curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up`
- cloud-server: gleich, aber via SSH vom Workstation-Terminal
- Beide im gleichen Tailnet, MagicDNS-Namen vergeben (z.B. `bratan-home.tail-xxxx.ts.net`, `cloud-bastion.tail-xxxx.ts.net`)

### Phase 3 — Caddy auf cloud-server
- `apt install caddy` (oder `docker run caddy`)
- Caddyfile: TLS via Let's Encrypt DNS-Challenge, Basic-Auth, Path-Routing (Gateway auf `/api/*` und `/v1/*`, Dashboard auf `/dashboard/*` → Workstation)
- Firewall: nur :443 von außen, Workstation-IPs whitelisten für :8642 und :9119 (WireGuard-Interface only)

### Phase 4 — APK auf Handy + Smoke-Test
- Tailscale-App installieren, einloggen
- Hermes-Android aus `rusty4444/hermes-android/releases/latest` (arm64 für die meisten Handys)
- Connection-Dialog: `Host: https://hermes.example.com`, `Port: 443`, `API Key: <API_SERVER_KEY>`
- Dashboard-Config: Username/Password für Caddy's Basic-Auth
- **Happy-Path-Test-Matrix:**
  1. Session-Liste lädt
  2. Neue Session erstellen
  3. Message senden → SSE-Stream zeigt Token-Deltas (nicht Burst → TCP_NODELAY verifizieren)
  4. Cron-Liste lädt
  5. Voice-Chat testen (Mic → STT → Hermes → TTS)
  6. Memory-Tab öffnet ohne Fehler

## Failure-Modi (vor dem ersten Production-Use durchdenken)

| Szenario | Detection | Workaround |
|---|---|---|
| Workstation aus | Caddy bekommt 502 von Workstation | Mobile zeigt "Connection failed" — erinnert User daran dass Workstation an sein muss |
| Tailscale-Key abgelaufen | Curl von cloud-server zu Workstation timeout | Pre-Auth-Key mit `--expiry=90d` setzen, Kalender-Reminder |
| Caddy-Config-Syntax kaputt | `caddy validate` in CI | Vor jedem Push `caddy adapt --validate` |
| API_SERVER_KEY rotiert | Mobile zeigt 401 | User muss in App neuen Key eintragen (Connection bearbeiten) |
| cloud-server-Platte voll | Caddy-Logs zeigen ENOSPC | Yuno-Cleaner-Cron auf cloud-server (analog Workstation) |

## Performance-Benchmarks (geschätzt, vor Live-Messung)

- **Latenz Workstation → cloud-server (WireGuard):** 5-15 ms p50, 20-50 ms p99
- **Latenz cloud-server → Android (Tailscale, gutes WLAN/Mobilfunk):** 20-80 ms p50
- **End-to-End Hermes-Chat-Latenz:** 100-500 ms für erste Token-Antwort (je nach Modell)
- **SSE-Token-Delta-Rate:** Mit TCP_NODELAY ~50-200ms pro Token, ohne Patch sichtbare Bursts alle 1-3 Sek

## Referenzen (Cross-Skill)

- `messaging-gateway-setup/references/api-server-quirks.md` — API-Server-Setup-Details, Endpoints, `API_SERVER_KEY`-Generierung, TCP_NODELAY-Patch
- `messaging-gateway-setup` SKILL.md "ZWEI verschiedene Gateway-Begriffe"-Warnbox — Verwechslung Messenger-Gateway vs. API-Server
- `github-workflow` SKILL.md "ALLE drei GH-Tools tot"-Pitfall — wie `git clone --depth 1` HTTPS als Read-Only-Fallback funktioniert
