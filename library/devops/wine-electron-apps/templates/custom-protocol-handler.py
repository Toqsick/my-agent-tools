#!/usr/bin/env python3
"""
Template: Electron-App Custom-Protocol-Handler (Linux → Wine Bridge)

Kopiere und passe an für jede Wine-Electron-App die ein Custom-Protocol
für OAuth-Redirects braucht (z.B. appname://auth-callback?code=...).

Ersetze die Platzhalter:
  - APP_NAME: Name der App (z.B. "MiniMax Hub", "MiniMax Code")
  - APP_EXE_NAME: Exakt wie der Prozess in pgrep erscheint (z.B. "MiniMax Hub.exe")
  - WINEPREFIX: Pfad zum Bottle/Wine-Prefix
  - APP_PATH: Relativer Pfad zur EXE im Prefix (z.B. "drive_c/Program Files/App/AppName.exe")
  - WINE_RUNNER: Pfad zum Wine-Binary
  - PROTOCOL: Custom-Protocol-Name (z.B. "appname")
  - SCHEME: URL-Scheme (z.B. "appname://")

Usage:
  chmod +x appname-url-handler
  sudo desktop-file-install appname-url-handler.desktop  # oder manuell kopieren
  xdg-mime default appname-url-handler.desktop x-scheme-handler/appname
  update-desktop-database ~/.local/share/applications/
"""
import os
import subprocess
import sys
from pathlib import Path

# ═══════════════════════════════════════════════
# KONFIGURATION — Anpassen!
# ═══════════════════════════════════════════════
APP_NAME = "AppName"          # Anzeigename
APP_EXE_NAME = "AppName.exe"  # Exakter pgrep-Match (escaped für regex)
PROTOCOL = "appname"          # Custom-Protocol-Name
WINE_RUNNER = Path.home() / ".var/app/com.usebottles.bottles/data/bottles/runners/kron4ek-wine-11.11-amd64/bin/wine"
WINEPREFIX = Path.home() / ".var/app/com.usebottles.bottles/data/bottles/bottles/MiniMax-Hub"
APP_PATH = f"drive_c/{APP_NAME}/{APP_EXE_NAME}"
APP_EXE = WINEPREFIX / APP_PATH
# ═══════════════════════════════════════════════

URL = sys.argv[1] if len(sys.argv) > 1 else ""
if not URL.startswith(f"{PROTOCOL}://"):
    print(f"⚠️  Unerwartete URL: {URL}", file=sys.stderr)
    sys.exit(1)

def laeuft_app():
    result = subprocess.run(
        ["pgrep", "-af", APP_EXE_NAME.replace(".", "\\.")],
        capture_output=True, text=True,
    )
    return APP_EXE_NAME in result.stdout

if laeuft_app():
    # App läuft schon → xdg-open reicht, Wine leitet an Instanz weiter
    subprocess.run(["xdg-open", URL])
else:
    # App starten mit URL
    env = os.environ.copy()
    env["WINEPREFIX"] = str(WINEPREFIX)
    env["WINEESYNC"] = "1"
    env["WINEFSYNC"] = "1"
    env["WINEDEBUG"] = "-all"
    subprocess.Popen(
        [str(WINE_RUNNER), str(APP_EXE), "--no-sandbox", URL],
        env=env, cwd=str(APP_EXE.parent),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )