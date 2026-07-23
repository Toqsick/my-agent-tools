# VPN-DNS-Block vs. Brave/Chrome — Trennung der Schichten

> Symptom: Eine Web-Seite lädt nicht — weder im normalen Tab, noch im
> Inkognito, noch mit Shields aus. Curl vom Terminal aus gegen dieselbe
> URL antwortet mit `000` (Timeout) bzw. `nslookup` mit `NXDOMAIN`,
> obwohl die Domain öffentlich erreichbar ist.

Diese Fallstricke ist eine **Schicht-verwechselung zwischen Brave/Chrome-Blocking
(URL-Level) und System-DNS-Blocking (Hostname-Auflösung)**. Beide können
unabhängig voneinander zuschlagen.

## Schnell-Diagnose: Welche Schicht blockt?

```bash
# 1. Testet Brave/Extension-Block? Schalte Shields aus und teste in Inkognito
#    → Wenn es dann lädt: Brave-Schicht blockt
#
# 2. Testet System-DNS? Curl/nslookup vom Terminal:
nslookup <blocked-domain>
# Server: 127.0.0.53
# ** server can't find <blocked-domain>: NXDOMAIN  ← System-DNS blockt
#
# 3. Vergleich mit einem bekannten DNS-Provider:
nslookup <blocked-domain> 1.1.1.1
# Non-authoritative answer: ...                   ← Domain existiert, anderer DNS kommt durch

# 4. Welcher Upstream hat NXDOMAIN geliefert?
systemd-resolve --status | grep -A2 "DNS Servers"
# Oder:
cat /run/systemd/resolve/resolv.conf | grep nameserver
# nameserver 10.x.y.z  ← das ist der blockende Resolver
```

Wenn der System-Default-Resolver `NXDOMAIN` zurückgibt aber `1.1.1.1`/`8.8.8.8`
die Domain kennen: **System-DNS-Block**, nicht Brave.

## Häufigste Ursache: VPN-Client mit aktivem Werbe-/Tracker-Block

Viele VPN-Clients (ProtonVPN, Mullvad, AdGuard-VPN, Windscribe, etc.) bieten
"NetShield", "Tracker-Block", "AdBlock" oder ähnliche Features. Diese laufen
auf zwei Ebenen:

| Ebene | Was es blockt | Wie es sich zeigt |
|-------|--------------|-------------------|
| **DNS-Ebene** | `*.tracking.com`, `googletagmanager.com`, `facebook.com/tr`, etc. | `nslookup` zeigt NXDOMAIN, Apps können Domain nicht auflösen |
| **HTTP-Ebene** | Tracking-Pixel, Beacons, XHR-Requests | Brave-Shields + Filter-Extensions blocken die HTTP-Response |

**Anti-Tracking-DNS-Listen** (z.B. ProtonVPNs NetShield, AdGuard DNS, NextDNS)
enthalten viele Tracking-Domains die legitime SaaS-Apps für ihre SPA-Rendering
brauchen. Beispielhafte Domain-Listen die **kaputt gehen**:

- `googletagmanager.com` (Google Tag Manager — fast jede Next.js-Site)
- `*.facebook.com/tr` und `connect.facebook.net` (Facebook-Pixel)
- `*.redditstatic.com/ads/` (Reddit-Pixel)
- `*.twitter.com/i/adsct` (X-Pixel)
- `bat.bing.net/bat.js` (Microsoft UET / Clarity)
- `*.doubleclick.net` (Google Ad-Serving)

Viele SPAs verlinken diese Tracker-Skripte **synchron** im `<head>`.
Bleibt eines hängen, kippt das gesamte Client-Side-Rendering.

## Test-Workflow: Welcher VPN-Client hat den Blocker an?

```bash
# 1. Welche VPN-Interfaces laufen?
ip link show | grep -E "proton|nord|mullvad|tun|tap|wg"
# 10: proton0: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 1420 ...
#   ↑ WireGuard-Tunnel aktiv

# 2. Welcher DNS-Server ist im systemd-resolved eingetragen?
cat /run/systemd/resolve/resolv.conf | grep nameserver
# nameserver 10.2.0.1  ← ProtonVPN-Tunnel-DNS

# 3. Welcher Upstream blockt?
nslookup googletagmanager.com 10.2.0.1
# → Wenn NXDOMAIN vom VPN-DNS kommt, ist NetShield/dgl. aktiv

# 4. Welche VPN-Tools sind installiert?
which proton-cli tailscale wireguard mullvad
# /usr/bin/protonvpn-app-flatpak  ← ProtonVPN Flatpak
```

## Lösungen (von schnell nach permanent)

### 1. VPN-eigenen Werbe-/Tracker-Block ausschalten (30 Sek)

**ProtonVPN:**
- ProtonVPN-App öffnen → "NetShield" → `Off` (oder `Standard` statt `Aggressive`)

**Andere VPN-Clients:**
- Mullvad: Settings → `Block ads/trackers` → off
- Windscribe: Preferences → `R.O.B.E.R.T.` → Custom rules ausschalten
- AdGuard VPN: Settings → `Ad blocking` → off

### 2. Brave DNS-over-HTTPS aktivieren (1 Min, kein VPN-Disconnect)

Brave DoH läuft **außerhalb** des systemd-DNS-Stacks — wenn DoH an ist, fragt
Brave direkt bei Cloudflare/Google/Quad9 nach und umgeht VPN-DNS-Block.

**Per GUI:** `brave://settings/security` → "Use secure DNS" → an → "Cloudflare (1.1.1.1)"

**Per Preferences-File (CLI-fähig):**
```bash
python3 << 'PYEOF'
import json
from pathlib import Path
prefs_path = Path.home() / ".config/BraveSoftware/Brave-Browser/Default/Preferences"
data = json.loads(prefs_path.read_text())
data['dns_over_https'] = {'mode': 'secure', 'templates': 'cloudflare'}
prefs_path.write_text(json.dumps(data, indent=2))
print("✓ DoH auf 'secure' + Cloudflare gesetzt")
PYEOF
```

**Wichtig:** DoH greift erst nach Browser-Restart (`Ctrl+Shift+Q` → neu öffnen).
Inkognito erbt die Settings nicht — neuer Inkognito-Tab reicht nicht, wenn
man auf einer DoH-blockenden Seite ist.

### 3. System-weit via systemd-resolved überschreiben (permanent, sudo nötig)

```bash
# /etc/systemd/resolved.conf.d/override.conf anlegen
sudo mkdir -p /etc/systemd/resolved.conf.d
sudo tee /etc/systemd/resolved.conf.d/override.conf <<'EOF'
[Resolve]
DNS=1.1.1.1 1.0.0.1
FallbackDNS=8.8.8.8
EOF
sudo systemctl restart systemd-resolved
# Test:
nslookup googletagmanager.com
# → sollte jetzt 1.1.1.1 fragen, nicht 10.2.0.1
```

**Risiko:** VPN-Tunnel funktioniert dann für Apps die NICHT VPN-eigenes DNS
benutzen. Wenn du VPN für Geoblocking brauchst, ist das hier vermutlich
nicht der richtige Fix.

### 4. VPN komplett trennen (schnellster Weg, kein Settings-Editing)

```bash
# WireGuard-Tunnel manuell stoppen
sudo wg-quick down proton0

# App-Login in normalem Tab
# Danach: VPN wieder hoch
sudo wg-quick up proton0
# Oder über die VPN-App
```

## Pitfalls

1. **VPN-DNS wirkt SYSTEM-WEIT** — auch Apps die gar nicht der Login-Trigger
   waren (Terminal, curl, andere Browser-Sessions) sehen den NXDOMAIN. Deshalb
   ist der `nslookup`-Test vom Terminal aus der schnellste Diagnose.
2. **DoH umgeht nur Browser** — wenn ein Terminal-Tool (curl, git, gh) die
   Domain auch braucht, muss man es via `--dns-servers 1.1.1.1` Override machen
   oder oben die `1.1.1.1` als System-DNS setzen.
3. **Brave-Cache vergisst DNS schnell** — DoH greift erst nach Browser-Restart,
   NICHT nach Tab-Reload (DNS-Cache überlebt Tab-Refresh).
4. **VPN-DNS-Upstream kann schwanken** — manche VPN-Clients fragen ihre
   eigene Tracker-Liste ab, andere laufen über Quad9 oder Cloudflare. Nicht
   jeder NXDOMAIN ist garantiert Werbe-Block — auch Manipulation oder Server-
   Fehler möglich.
5. **"VPN-DNS aus" wirkt sich auf alle VPN-Connections aus** — wenn du mit
   WireGuard `wg-quick` arbeitest, geht nur der WireGuard-Tunnel down, der
   VPN-Client fällt nicht automatisch auf seine zweite Konfiguration zurück.

## Diagnose-Matrix

| Test | Ergebnis | Schicht | Lösung |
|------|----------|--------|--------|
| `nslookup <domain>` (system-DNS) | NXDOMAIN, aber `1.1.1.1` kennt die Domain | System-DNS-Block | Methode 1-4 oben |
| `nslookup <domain>` (system-DNS) | NXDOMAIN, `1.1.1.1` auch | Domain ist wirklich weg / Down | Provider fragen |
| `nslookup` OK, aber Brave zeigt nichts | DNS funktioniert, Browser blockt | Brave/Extension-Block | Inkognito + Filter-Whitelist |
| Inkognito + Shields aus → lädt | Brave-Schicht blockte | Extension-Block | Filter-Whitelist, dediziertes Profil |
| Inkognito lädt immer noch nicht → nslookup NXDOMAIN | System-DNS-Block | System-DNS | VPN-Werbeblocker aus / DoH an |

## Quellen

- ProtonVPN NetShield documentation
- systemd-resolved: `man systemd-resolved`
- Chromium DNS-over-HTTPS: https://blog.chromium.org/2018/05/announcing-dns-over-https.html
- Session 2026-07-03: MiniMax Hub Login-Flow, identifiziert via
  `nslookup googletagmanager.com 10.2.0.1` → NXDOMAIN, `1.1.1.1` → OK
  (ProtonVPN NetShield war der Verursacher, gelöst via Brave DoH)
