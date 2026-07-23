---

name: wine-electron-apps
description: |
  Use when installing or troubleshooting Electron desktop applications under Wine or Bottles on Linux, including prefixes, launch flags, and rendering issues.
  NOT for native Linux Electron applications, general Windows game compatibility, or bypassing application licensing and security controls.
  Provides a repeatable setup and diagnosis workflow for Electron runtimes operating through Wine-compatible environments.
trigger: Benutzer will eine Electron-App (app.asar, Chromium-Renderer) unter Wine
  installieren ODER OAuth/SSO-Login einer Wine-Electron-App debuggen
version: 1.0
author: Hermes Agent
license: MIT
trigger_keywords: ['electron', 'applications', 'wine', 'linux', 'installing']
keywords: ['electron', 'applications', 'wine', 'linux', 'installing']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---
# wine-electron-apps — Electron unter Wine

## Wann dieser Skill greift

Sobald eine Desktop-App ein **Electron-Bundle** ist (`.asar` im `resources/`,
Chromium-Renderer, Webbasierte UI) und unter Linux via Wine/Bottles laufen soll.
Besonders relevant wenn:

- **NSIS-Installer** (`*.exe`, Nullsoft Scriptable Install System) hängt beim Silent-Install
- **OAuth/SSO-Login** mit Custom-Protocol-Callback (`appname://auth-callback?code=...`)
- **Login-Flow-Debugging** nötig wird (Token-Extraktion, Cookie-Storage, Electron-Logs)

## Voraussetzungen

- Wine 9+ (Kron4ek empfohlen) oder Bottles
- `p7zip-full` (für NSIS-Manual-Extraktion)
- `xdg-utils` + `update-desktop-database` (für Custom-Protocol-Registrierung)
- Python 3 (für URL-Handler-Wrapper)
- `sqlite3` (für Cookie-Storage-Inspektion)

## Pattern 1: NSIS-Electron-Manual-Extraktion

Wenn `wine installer.exe /S` (silent NSIS) hängt — oft wegen Electron-
`createWritableStdioStream EBADF` unter Wine:

1. Extrahiere die NSIS-Hülle (schnell, 7z kann NSIS):
   ```bash
   7z x "$INSTALLER_NAME" -o"$TMPDIR"
   ```
2. Finde das komprimierte Electron-Bundle:
   ```bash
   ls "$TMPDIR/\$PLUGINSDIR/"
   # → app-64.7z  (213 MB, x64)
   # → app-arm64.7z  (213 MB, arm — für Wine irrelevant)
   ```
3. Extrahiere das x64-Bundle:
   ```bash
   7z x -t7z "$TMPDIR/\$PLUGINSDIR/app-64.7z" -o"$TMPDIR/app"
   ```
   Das entpackt die komplette Electron-Struktur (`resources/app.asar`, `*.exe`, DLLs etc.).
4. Kopiere in den Wine-Prefix:
   ```bash
   cp -r "$TMPDIR/app" "$WINEPREFIX/drive_c/APP-NAME/"
   ```
5. Aufräumen:
   ```bash
   rm -rf "$TMPDIR"
   ```

**Vorteile:** Kein Wine-Installer-Bug mehr, volle Kontrolle über Bundle-Inhalt, 5-10x schneller.
**Nachteil:** Kein Windows-Registry-Setup durch den Installer — ggf. manuelle Registry-Keys.

## Pattern 2: Custom-Protocol-Handler-Bridge (Linux → Wine)

Viele Electron-Apps registrieren ein **Custom Protocol** (z.B. `appname://auth-callback?code=...`)
für OAuth-Redirects vom Browser zurück zur App. Unter Wine funktioniert das nicht,
weil der Linux-Desktop den `appname://`-Link nicht kennt.

**Lösung:** xdg-mime-Handler in Linux, der den Deeklink an die laufende Wine-App weiterleitet.
Die App selbst hat den Handler bereits in der Wine-Registry (customer.reg) registriert,
braucht aber einen xdg-Brückenkopf.

### Schritt 1: Desktop-File

`~/.local/share/applications/appname-url-handler.desktop`:

```ini
[Desktop Entry]
Name=AppName URL Handler
Exec=/pfad/zu/appname-url-handler %u
Type=Application
MimeType=x-scheme-handler/appname;
NoDisplay=true
```

### Schritt 2: Python-Wrapper

`appname-url-handler` (legt in `~/50-System/bin/` und `~/.local/bin/`):

```python
#!/usr/bin/env python3
import os, subprocess, sys
from pathlib import Path

RUNNER = Path.home() / ".var/app/com.usebottles.bottles/data/bottles/runners/kron4ek-wine-XX-YY-amd64"
BOTTLE = Path.home() / ".var/app/.../bottles/MiniMax-Hub"
APP_EXE = BOTTLE / "drive_c/APP-NAME/APP.exe"
WINE = RUNNER / "bin/wine"
URL = sys.argv[1]

def laeuft_app():
    return "APP.exe" in subprocess.run(
        ["pgrep", "-af", "APP\\.exe"], capture_output=True, text=True
    ).stdout

if laeuft_app():
    subprocess.run(["xdg-open", URL])  # Wine leitet an laufende Instanz weiter
else:
    env = os.environ.copy()
    env.update(WINEPREFIX=str(BOTTLE), WINEESYNC="1", WINEFSYNC="1", WINEDEBUG="-all")
    subprocess.Popen([str(WINE), str(APP_EXE), "--no-sandbox", URL], env=env,
                     cwd=str(APP_EXE.parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
```

### Schritt 3: Registrierung

```bash
chmod +x /pfad/zu/appname-url-handler
update-desktop-database ~/.local/share/applications/
xdg-mime default appname-url-handler.desktop x-scheme-handler/appname
xdg-mime query default x-scheme-handler/appname   # → appname-url-handler.desktop
```

**Verify:** Nach Registrierung sollte der Wine-Browser bei `appname://`-Redirect
den Handler aufrufen und die URL an die laufende App weiterreichen.

## Pattern 3: Login-Flow-Debugging

### Electron-Logs finden

Unter Wine liegen die Logs in:
```
$WINEPREFIX/drive_c/users/$USER/AppData/Roaming/APP-NAME/logs/
  main-YYYY-MM-DD.log       # Hauptprozess-Logs
  renderer-YYYY-MM-DD.log   # Renderer-Logs
```

**Wichtige Marker:**

| Log-Eintrag | Bedeutung |
|---|---|
| `[WindowManager] Registered window: type=onboarding, id=1` | Onboarding-Screen aktiv |
| `[WindowManager] Registered window: type=login, id=2` | Login-Screen geöffnet |
| `[Auth] navigateToLogin triggered, source: onboarding:not_logged_in` | Auto-Redirect zum Login |
| `[WindowManager] Unregistered window: type=onboarding, id=1` | Onboarding geschlossen (nach Skip oder Token) |
| `[WindowManager] Registered window: type=main, id=3` | Haupt-UI geladen! |
| `Heartbeat` | Alle 6-10s → App lebt |

### Cookie-Storage prüfen

Wine-Browser (Chromium) speichert Cookies im Chromium-SQLite-Format:
```bash
sqlite3 "$WINEPREFIX/drive_c/users/$USER/AppData/Roaming/APP-NAME/Network/Cookies" \
  "SELECT host_key, name, length(value), expires_utc FROM cookies;"
```

⚠️ **Chromium v10 Encryption:** `value` = '' bei encrypted, `encrypted_value` = Binär.
Plain-Text nur bei Nicht-Auth-Cookies (Akamai, Tracking). Nützlich für Bot-Detection-Check.

### Config-Injection

Viele Electron-Apps haben eine persistente Config:
```
$WINEPREFIX/drive_c/users/$USER/AppData/Roaming/APP-NAME/app-config.json
```

Oft mit `tokens`-Feld + localStorageConfig:
```json
{
  "tokens": {"accessToken": "...", "refreshToken": "..."},
  "localStorageConfig": {"isOnboardingCompleted": false, ...}
}
```

Token setzen → `isOnboardingCompleted = true` → `tokens.accessToken` setzen → App-Start
überspringt Onboarding + Login.

#### Token-Quellen (priorisiert)

1. **Brave/Chrome DevTools:** F12 → Network-Tab → Auth-Response suchen
   (Cookie/Auth-Header aus Request extrahieren)
2. **Brave DevTools Console:** `document.cookie` (httpOnly-Cookies unsichtbar —
   besser Network-Tab)
3. **Wine-Browser DevTools:** App mit `--remote-debugging-port=9222` starten,
   via Chrome DevTools Protocol auf `localhost:9222` zugreifen
4. **OAuth-Flow wiederholen:** Nach Custom-Protocol-Registrierung (Pattern 2)
   Login in der App nochmal durchführen — Token sollte jetzt ankommen

## Pattern 4: Shared-Prefix-Strategie

Mehrere Apps vom gleichen Hersteller (MiniMax Hub + Code etc.) teilen sich
ein Wine-Prefix:

- Spart **1-3 GB Disk** pro App (Runner + System-DLLs + Fonts nur einmal)
- Voraussetzung: gleiche Wine-Version, keine DLL-Konflikte
- Getrennte `drive_c/APP-NAME/`-Verzeichnisse pro App
- Eigene Desktop-Files + PATH-Wrapper pro App
- Eigene `app_name` im Wine-Title (via Registry oder `--name=APP`)

### Disk-Nutzung (Erfahrungswerte pro App)

| Komponente | Größe |
|---|---|
| Electron-Bundle (`app-64.7z` extrahiert) | ~800-900 MB |
| Wine-Prefix-Basis (geteilt) | ~2.5 GB |
| Pro zusätzliche App (Bundle only) | +800-900 MB |

## Pattern 5: Main-Window bleibt 1x1 — Helper-Windows-Resize + Virtual-Desktop Workaround

**Symptom:** Eine Wine-App startet, alle 5 X11-Child-Windows sind registriert, aber das Main-Window ist nur 1x1 Pixel groß. `xdotool search --class` findet das Window, aber `wmctrl` und `xdotool windowsize` haben keinen Effekt. Die App selbst rendert nichts Sichtbares.

**Ursache (zwei Varianten):**

1. **WS_POPUP | WS_VISIBLE mit internem Resize-Loop:** App nutzt `CreateWindow(WS_POPUP | WS_VISIBLE, "Title", CW_USEDEFAULT, 0, 1, 1, ...)` und hat einen internen `WM_SIZE`-Handler der jede externe Größenänderung sofort auf 1x1 zurücksetzt. Tritt bei nativem MFC/Win32-Code auf (z.B. Reckhorn DSP-6, viele USB-Device-Configuration-Tools).

2. **Hardware-Detection blockiert Main-Window:** App wartet auf USB-Hardware und öffnet das Main-Window erst wenn das Device erkannt wird. Ohne Device bleibt das Main-Window im "Connect device"-Splash (1x1). Tritt bei Audio-DSP-Tools, USB-Konfiguratoren, etc. auf.

**Diagnose:**

```bash
# Wie viele Windows hat die App?
DISPLAY=:1 xdotool search --class "<app-class>"  # z.B. "reckhorn dsp-6.exe"

# Welche davon sind Main vs Helper?
DISPLAY=:1 xwininfo -root -children 2>&1 | grep -E "<app-class>" | head
# Main-Window = Map State: IsViewable
# Helper-Windows = Map State: IsUnMapped

# DLL-Liste (für Hardware-Detection-Diagnose)
cat /proc/<pid>/maps | grep -iE "dll|exe" | grep -oE "/[^ ]+\.(dll|exe)" | sort -u | head -30
# Suche nach Treiber-DLLs (SiUSBXp.dll, FTDI-DLLs, etc.) — wenn geladen, wartet die App
```

**Workaround-Lösung in 3 Schritten:**

### Schritt 1: Wine-Virtual-Desktop aktivieren

```bash
WINEPREFIX=/path/to/bottle wine reg add 'HKCU\Software\Wine\Explorer\Desktops' /v Name /d Default /f
WINEPREFIX=/path/to/bottle wine reg add 'HKCU\Software\Wine\Explorer\Desktops' /v Width /d 1280 /f
WINEPREFIX=/path/to/bottle wine reg add 'HKCU\Software\Wine\Explorer\Desktops' /v Height /d 800 /f
# Verify
WINEPREFIX=/path/to/bottle wine reg query 'HKCU\Software\Wine\Explorer\Desktops'
```

→ Setzt einen Container-Bereich. **Wichtig:** Das Main-Window wird dadurch NICHT automatisch resized, aber Helper-Windows orientieren sich daran.

### Schritt 2: Helper-Windows resized automatisch, Main-Window bleibt klein

Wrapper-Pattern für den Launcher (in Python):

```python
import threading
import subprocess
import time

def fix_window_geometry():
    """Resize alle Helper-Windows auf 1024x768.
    Helper-Windows folgen externen Resize-Befehlen, Main-Windows mit WS_POPUP nicht.
    """
    display = os.environ.get("DISPLAY", ":1")
    w, h, x, y = 1024, 768, 200, 150

    for _ in range(30):  # 30s warten
        r = subprocess.run(
            ["xdotool", "search", "--class", "<app-class>"],
            env={**os.environ, "DISPLAY": display},
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            for wid in r.stdout.strip().split("\n"):
                # wmctrl -l -G zeigt PID, X, Y, W, H
                wm = subprocess.run(
                    ["wmctrl", "-l", "-G"], env={**os.environ, "DISPLAY": display},
                    capture_output=True, text=True, timeout=5,
                )
                for line in wm.stdout.splitlines():
                    if wid in line:
                        parts = line.split()
                        if len(parts) >= 7:
                            try:
                                cur_w, cur_h = int(parts[5]), int(parts[6])
                                if cur_w < 200 or cur_h < 200:
                                    # Helper-Window ist klein → resizen
                                    subprocess.run(
                                        ["wmctrl", "-i", "-r", wid, "-e", f"0,{x},{y},{w},{h}"],
                                        env={**os.environ, "DISPLAY": display},
                                        capture_output=True, timeout=5,
                                    )
                                    subprocess.run(
                                        ["xdotool", "windowraise", wid],
                                        env={**os.environ, "DISPLAY": display},
                                        capture_output=True, timeout=5,
                                    )
                            except (ValueError, IndexError):
                                pass
        time.sleep(1)

# Im Launcher-Thread starten
threading.Thread(target=fix_window_geometry, daemon=True).start()
```

### Schritt 3: Main-Window braucht entweder Hardware ODER Diagnostic-Screenshot via xwd

Falls die App auf USB-Hardware wartet, ist das Main-Window 1x1 bis das Device erkannt wird. Bei nativem MFC mit internem Resize-Loop hilft nur ein direkter Eingriff in den Code (nicht möglich).

**Visuelle Verifikation wenn alle Stricke reissen:**

```bash
# xwd statt scrot (Wayland-Screenshot-Blocker umgehen)
DISPLAY=:1 xwd -id 0x03e00003 -out /tmp/screen.xwd
convert /tmp/screen.xwd /tmp/screen.png
# → liefert 1-Bit-PNG, aber wenn das Window NICHT 1x1 ist, sieht man den Inhalt
file /tmp/screen.png
# Bei 1x1-PNG ist das Main-Window noch im Hardware-Wait-Modus
```

**Lessons Learned (Reckhorn DSP-6 Session 2026-07-09):**

- **Helper-Windows folgen externen Resize, Main-Windows mit `WS_POPUP` nicht** — das ist asymmetrisch und kann Stunden verschlingen bis man es versteht
- **Virtual-Desktop setzt nur den Container, nicht die Window-Geometrie** — keine Wunderwaffe
- **USB-Detection-Block ist App-Behavior, kein Bug** — die App wartet auf `SI_GetNumDevices()` und öffnet das Main-Window erst wenn das Device antwortet
- **xwd-Screenshot funktioniert auch wenn Wayland-Scrot/import blockt** — ist die letzte Option für visuelle Verifikation

## Pitfalls

- ❌ **NSIS-Silent-Install hängt** → Pattern 1 (manuelle Extraktion über 7z)
- ❌ **Custom-Protocol fehlt** → OAuth-Token kommt nie in der App an → Pattern 2
- ❌ **App beendet sich nach Onboarding-Skip** → Token fehlt → Pattern 3 injizieren
- ❌ **Wayland-Screenshots von Wine-Fenstern** → `scrot` nimmt den ganzen Screen,
  `import -window` liefert leeres Bild (Wayland-Bug). Workaround: `xdotool` + `scrot`
  ODER `xwd -id <win-id> -out screen.xwd` + `convert` für Window-spezifische Screenshots
  die auch in 1-Bit funktionieren wenn das Window sichtbar ist.
- ❌ **Wine-Browser öffnet externen Browser statt App** → Custom-Protocol fehlt,
  siehe Pattern 2.
- ❌ **Login erfolgreich auf Server-Seite, App bleibt leer** → OAuth-Token wurde nirgends
  gespeichert (Custom-Protocol-Problem) — nicht das Electron-Log suchen, sondern
  den Network-Tab im Browser prüfen.
- ❌ **pgrep false-positives durch Agent-Prozesse** → Im Wrapper `pgrep -af "APP\\.exe"`
  statt `pgrep -af "APP"` verwenden, sonst matchen auch Agent-Subprozesse mit
  ähnlichem Namen.
- ❌ **Main-Window bleibt 1x1 trotz xdotool** → Siehe Pattern 5. Ursache ist meist
  `WS_POPUP | WS_VISIBLE` mit internem Resize-Loop, oder USB-Hardware-Detection-Block.
  Virtual-Desktop hilft nur teilweise. Helper-Windows (IME, Tooltips) kann man
  resized bekommen, das Main-Window nicht.

## Skills-Linked-Files

- `references/minimax-code-login-2026-07-08.md` — Session-spezifische Detailnotizen
  (Endpoints, Login-Typen, Config-Pfade, Heartbeat, bek. Probleme)
- `templates/custom-protocol-handler.py` — Template für den Python-Wrapper
  eines Custom-Protocol-Handlers (Platzhalter ersetzen, fertig)

## Siehe auch

- `~/docs/system/minimax-code-bottles-2026-07-08.md` (detaillierte Session-Doku)
- `system-documentation` skill (für Doku-Ablage im `~/docs/system/`-Schema)
- `linux-system` skill (Disk-Management, Wine-Installation)