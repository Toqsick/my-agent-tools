# Companion-App APK Delivery via Tailscale Serve

> **Wann lesen:** Wenn du eine Hermes-Companion-App (z.B. `rusty4444/hermes-android`) auf ein Handy/Tablet bringen willst, OHNE Google Play Store, OHNE Cloud-Upload, OHNE USB-Debugging. Funktioniert nur wenn das Handy im selben Tailscale-Tailnet ist wie die Workstation.

> **Vorbedingung:** Tailscale läuft auf Workstation UND Handy. APK ist heruntergeladen und liegt lokal. Hermes-API + Dashboard laufen (siehe `references/api-server-external-clients.md`).

---

## Warum dieser separate Pattern

Companion-Apps werden oft **nicht im Play Store** angeboten (Self-Hosted-Tooling, Beta-Releases, Sicherheitsbedenken). Die üblichen Lieferwege sind:

| Weg | Vorteil | Nachteil |
|---|---|---|
| **Google Play Store** | Auto-Update, einfach | Account + Dev-Console nötig ($25 einmalig), Review-Zeit |
| **Sideload via USB** | Offline-tauglich | `adb` muss auf Workstation installiert sein, USB-Kabel, USB-Debugging auf Handy |
| **E-Mail-Anhang** | Funktioniert ohne Tools | Gmail-Anhang-Limit 25 MB, APK oft > 15 MB |
| **Cloud-Drive (Dropbox etc.)** | Funktioniert | Account-Login auf Handy, Sync-Delay |
| **Tailscale Serve + Mini-Server** ✅ | Tailnet-only, Tailscale-Cert, kein Login, sofortiger Download, kein Storage-Account | Nur für Tailscale-Nodes erreichbar (kein Always-On für externe User) |

Für die typische Basti-Situation (Workstation + Handy im selben Tailnet) ist **Tailscale Serve + Mini-Python-Server** die direkteste Lösung.

---

## Schritt-für-Schritt

### 1. APK in den Hermes-Workspace (NICHT `~/Downloads`!)

Wichtig: Workspace-Regel. Yunos Staging-Ordner für sowas:

```bash
mkdir -p ~/.hermes/apk-staging
mv ~/Downloads/hermes-android-vX.Y.Z-arm64.apk ~/.hermes/apk-staging/
```

**Pitfall:** Die Versuchung, die APK in `~/Downloads/` zu lassen, ist groß (User hat sie ja da "gedownloadet"). Aber für Yunos operative Workflows gilt `~/.hermes/` als Workspace — `~/Downloads/` ist User-Browser-Downloads. Wenn Yuno später `~/.hermes/` für Backups oder System-Audits scannt, will sie nicht versehentlich 19-MB-APKs in einen Backup einschließen oder mit einem Cleanup-Script wegräumen.

### 2. Mini-Python-Server schreiben

Statt einen vollwertigen Static-File-Server (nginx, darkhttpd, python -m http.server) zu benutzen, der Path-Traversal-Risiken mitbringt: minimaler Handler, der **nur die exakte APK ausliefert**, alles andere 404.

```python
#!/usr/bin/env python3
"""Minimaler Static-File-Server NUR für die Hermes-Android APK.
Liefert NUR Dateien aus ~/.hermes/apk-staging/ aus.
Kein Directory-Listing, kein Path-Traversal.
"""
import http.server
import socketserver
import os
import sys

PORT = 8445
ROOT = "/home/bratan/.hermes/apk-staging"
ALLOWED_FILES = {"hermes-android-v1.0.9-arm64.apk"}   # exakte Whitelist

class APKHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        filename = self.path.lstrip("/")
        if filename in ALLOWED_FILES:
            filepath = os.path.join(ROOT, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.android.package-archive")
                self.send_header("Content-Length", str(size))
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                with open(filepath, "rb") as f:
                    while chunk := f.read(64 * 1024):
                        try:
                            self.wfile.write(chunk)
                        except (BrokenPipeError, ConnectionResetError):
                            return
                return
        # 404 für alles andere (kein Listing, kein Traversal)
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"404 - only hermes-android-vX.Y.Z-arm64.apk is served here\n")

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[apk-serve] {fmt % args}\n")

if __name__ == "__main__":
    os.chdir(ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), APKHandler) as httpd:
        sys.stderr.write(f"[apk-serve] serving on 127.0.0.1:{PORT} from {ROOT}\n")
        httpd.serve_forever()
```

**Pitfall — `bytes`-Literals mit UTF-8:** Wenn im 404-Text ein em-dash (`—`) oder ein Umlaut landet, wirft Python `SyntaxError: bytes can only contain ASCII literal characters` beim Parsen. **Immer ASCII-Strings in `b"..."`-Literals** (siehe `python-stdlib-pitfalls` §6).

### 3. Server im Hintergrund starten

```bash
python3 /home/bratan/50-System/bin/hermes-apk-server.py
```

**Pitfall — `nohup`/`disown`/`setsid` im foreground-terminal:** Wird vom Hermes-Approval-System auto-rejected. Stattdessen `terminal(background=true)` benutzen oder den Server dauerhaft als systemd-unit registrieren (siehe Schritt 6).

### 4. Via Tailscale Serve exposen

```bash
tailscale serve --bg --https=8446 http://127.0.0.1:8445
```

MagicDNS-URL: `https://<workstation>.tailXXXX.ts.net:8446/hermes-android-vX.Y.Z-arm64.apk`

### 5. APK auf dem Handy herunterladen

Im Handy-Browser die MagicDNS-URL öffnen → Download startet (Tailscale-Cert ist trusted) → APK installieren (Android fragt nach "Unbekannte Quellen erlauben").

### 6. Optional — Persistente systemd-Unit

Damit der Server nach Reboot/Logout weiterläuft:

```ini
# ~/.config/systemd/user/hermes-apk-server.service
[Unit]
Description=Hermes APK-Delivery Server (nur die erlaubte APK, Port 8445)
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/bratan/50-System/bin/hermes-apk-server.py
WorkingDirectory=/home/bratan/.hermes/apk-staging
Restart=always
RestartSec=5
KillMode=mixed

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now hermes-apk-server.service
```

---

## Verwechslungs-Falle: APK-Download-URL vs. Hermes-API-URL

**Häufige Verwechslung:** User trägt die APK-Download-URL (`https://...:8446/hermes-android-...apk`) als **Connection-Host** in der Hermes-Companion-App ein. Das schlägt fehl weil die APK-URL eine **Datei** liefert (Content-Type: `application/vnd.android.package-archive`), nicht die Hermes-API.

**Die zwei URLs sind komplett verschieden:**

| Zweck | URL | Was passiert |
|---|---|---|
| **APK herunterladen** | `https://<host>.tailXXXX.ts.net:8446/hermes-android-vX.Y.Z-arm64.apk` | Liefert 19 MB APK-Datei (einmalig) |
| **Hermes connecten** | `https://<host>.tailXXXX.ts.net:8444/api/...` (Dashboard) bzw. `https://<host>.tailXXXX.ts.net/v1/...` (API, default Port 443) | Liefert JSON, Bearer-Auth, SSE-Stream |

**In der Companion-App-Connection eintragen:**
- **Host**: `https://<host>.tailXXXX.ts.net` (MagicDNS-Name, kein Pfad)
- **Port**: `443`
- **API Key**: der `API_SERVER_KEY` aus `~/.hermes/.env`
- **Dashboard Port**: `8444` (der exposed Port, NICHT 9119!)
- **Dashboard behind proxy**: ✅ AN (Tailscale injiziert Cert)

**Wie man Usern die Verwechslung erspart:**
1. APK-Download-URL **NIE als MagicDNS-Host-Field** in der App nennen
2. Stattdessen klar trennen: "Download-URL (einmalig)" vs. "Connection-URL (App-Config)"
3. Schritt-für-Schritt-Listen mit beiden URLs separat auflisten

---

## Reversibility

```bash
# Server stoppen
pkill -TERM -f "hermes-apk-server.py"

# Tailscale Serve für diese URL abschalten
tailscale serve --https=8446 off

# Optional: systemd-unit entfernen
systemctl --user disable --now hermes-apk-server.service
rm ~/.config/systemd/user/hermes-apk-server.service
systemctl --user daemon-reload

# Optional: APK löschen
rm ~/.hermes/apk-staging/hermes-android-vX.Y.Z-arm64.apk
```

---

## Sicherheit

**Was dieses Pattern NICHT schützt:**
- APK-Download ist **tailnet-only** (Tailscale-Nodes können connecten) — keine externen User
- Auth erfolgt via Tailscale-Membership, nicht per Token
- Wenn jemand dein Tailscale-Tailnet kompromittiert, kann er auch die APK ziehen (aber er hat eh Zugriff auf alles andere)
- **Kein HTTPS-Cert-Pinning**: jeder mit Tailscale-Zugang kann die APK über ihren Tailscale-MagicDNS-Namen ziehen, egal von welchem Gerät

**Was es schützt:**
- Externe Internet-Scanner sehen die APK nicht (kein öffentlicher Port)
- `~/.hermes/apk-staging/` ist durch 700-Permissions auf das Home-Dir geschützt
- Mini-Server hat **explizite Whitelist** (`ALLOWED_FILES`) — kein Path-Traversal-Risiko wie bei `python -m http.server`
- Tailscale-Cert ist selbst-signiert via Tailscale-CA (nicht über öffentliche CA verifizierbar — schützt vor externer MITM, nicht vor Tailnet-interner MITM)

---

## Sources / Context

- Tailscale Serve Doku: <https://tailscale.com/kb/1247/funnel-serve-use-cases>
- Hermes-Android Companion-App: <https://github.com/rusty4444/hermes-android>
- Validated: 2026-07-10 auf bratan-17-P1, Hermes v0.18.2, Tailscale 1.98.8, Galaxy S8-Handy
- Pattern: Mini-Server (~30 Zeilen Python) + 1 systemd-unit + 1 Tailscale-Serve-Aufruf
- Companion-Skill: `hermes-maintenance/references/api-server-external-clients.md` (API-Server freischalten)
- Verwandt: `hermes-maintenance/references/tailscale-serve-caddy-replacement.md` (Tailscale-Serve-Grundlagen)