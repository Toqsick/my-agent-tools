# Connection Forensic Trace — Reference Data

Geo-Data für bekannte Provider-IPs aus Basti's Workstation (ermittelt 2026-07-14).

## Bekannte API-Endpoint-IPs

| Domain | IPs | AS / Owner |
|--------|-----|------------|
| `api.minimax.io` | `47.252.72.253`, `47.89.128.168` | AS45102 Alibaba (US) Technology |
| `api.nousresearch.com` | diverse Anycast-IPs | Nous Research / Cloudflare |
| `api.anthropic.com` | `2607:6bc0::/32` (via IPv6) | AS399358 Anthropic, PBC |

## Provider-Geo-Datenbank (Session-kalibriert)

| IP | Provider | Land | Bewertung |
|----|----------|------|-----------|
| `47.89.128.168` | MiniMax (Alibaba US) | 🇺🇸 Virginia | ✅ erwartbar |
| `47.252.72.253` | MiniMax (Alibaba US) | 🇺🇸 | ✅ erwartbar |
| `49.12.193.137` | Hetzner | 🇩🇪 Nürnberg | ⚠️ Browser-Tab / GNOME-Telemetry — nur bei gleichzeitiger Firefox-Chromium-Nutzung |
| `155.133.229.4:27019` | Valve | 🇩🇪 Frankfurt | ✅ Steamworks |
| `2a04:4e42:6f::347` | Fastly (CDN) | 🇩🇪 München | ✅ GNOME Software / Flathub |
| `2607:6bc0::10` | Anthropic | 🇺🇸 San Francisco | ✅ Claude Desktop |
| `2600:1901:0:179c::` | Google LLC | 🇺🇸 Kansas City | ✅ Claude Desktop Telemetrie |
| `2606:b740:1:20::103` | Amazon AWS | 🇺🇸 Reston | ⚠️ Claude / Browser Helper |
| `2606:b740:49::107` | Amazon AWS | 🇩🇪 Frankfurt | ⚠️ Claude / Browser Helper |

## Entscheidungslogik

```
Ist die IP in der DNS-Response eines erwartbaren API-Hosts?
  └── JA → ✅ Kein Finding
  └── NEIN → 
       Ist der Owner ein bekannter CDN / Cloud-Provider?
         └── Fastly, Cloudflare, Akamai, AWS CloudFront → ⚠️ Kein Finding (Flathub, Browser-CDN)
         └── Hetzner, OVH, DigitalOcean → ⚠️ Browser-Tab, kein Owner in ss? Kein Finding
         └── Unbekannter Owner, ungewöhnlicher Port, kein PID → 🔴 User fragen
```

## ipinfo.io CLI One-Liner

```bash
# Einzel-IP (schnell):
curl -s -m 8 "https://ipinfo.io/47.89.128.168/json"

# Batch (mehrere):
for ip in 47.89.128.168 155.133.229.4 49.12.193.137; do
  printf '--- %s ---\n' "$ip"
  curl -s -m 8 "https://ipinfo.io/$ip/json"
  echo
done

# IPv6:
curl -s -m 8 "https://ipinfo.io/2607:6bc0::10/json"
```

## Known-False-Positive Patterns

- **Hetzner IPs (`49.12.x.x`, `5.75.x.x`, `116.202.x.x`):** GNOME-Software-Updates, 
  Browser-Tabs mit deutschen Websites, ProtonMail, Mailcow. Ohne PID-Owner → ⚠️.
- **AWS IPs (`2606:b740::/32`):** Claude-Desktop-NetworkService, Hermes-Desktop 
  Chromium-Infra, Browser-CDN-Load. Ohne PID-Owner → ⚠️.
- **Kein PID in `ss -tupn`:** Firefox/Chrome Helper-Prozesse, snap-Desktop-Integration.
  Kernel verweigert PID-Abfrage aus CONFIG_NET_NS-Gründen.
- **`gnome-software` auf Port 443:** Flathub-Update-Check (Fastly CDN). Erwartbar.
- **Port 27019:** Valve-GameCoordinator (Steamworks). Wenn Steam läuft, erwartbar.