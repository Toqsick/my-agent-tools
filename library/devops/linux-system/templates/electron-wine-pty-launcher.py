#!/usr/bin/env python3
"""
Electron-App-Starter für Bottles (Flatpak) + Wine — umgeht Node.js EBADF.

Hintergrund: Moderne Electron-Apps (Beispiel: MiniMax Hub 2026-07) prüfen
beim Start ob fd 0/1/2 echte TTYs sind. Bei Pipe-Redirect crashed der
Node-Bootstrap mit:
    Uncaught Exception:
    Error: open EBADF
        at createWritableStdioStream (node:internal/bootstrap/...)

Dieses Template allokiert ein Pseudo-Terminal bevor Wine gestartet wird,
und reicht zusätzlich optional einen Login-Token via Env-Var durch
(umgeht OAuth-Browser-Popup-Bug in Wine-X11).

ANPASSEN:
  - BOTTLE_PATH:    Pfad zur Bottles-Bottle
  - RUNNER:         Wine-Runner-Pfad (kron4ek-wine-11.11-amd64 empfohlen für Electron)
  - APP_EXE:        Pfad zur .exe IN der Bottle
  - EXE_FLAGS:      Electron-Flags (--no-sandbox für Electron-Apps in Wine)
  - TOKEN_VAR / TOKEN_FILE: Welche Env-Var/token-Datei-Pattern die App
    für Login nutzt (siehe references/windows-apps-on-linux.md → "Electron-Login
    Workaround: Token via Env-Var" für die Diagnose-Methode)

VERWENDUNG:
  1. cp dieses Script nach ~/bin/<app-name>
  2. chmod +x <app-name>
  3. Pfade oben anpassen
  4. Optional: Desktop-File in ~/.local/share/applications/<app-name>.desktop
  5. Token-Datei anlegen (für SaaS-Electron-Apps):
        echo '<TOKEN>' > ~/.config/<app-name>-token && chmod 600 ~/.config/<app-name>-token
  6. Starten via Terminal oder Anwendungsmenü
  7. NACH START: Stabilität via Heartbeat-Zählen prüfen:
        grep -c "Sent heartbeat" /pfad/zu/log
        → ≥10 in 3 Min = gesund (siehe references/windows-apps-on-linux.md)
"""
import argparse
import os
import pty
import re
import select
import signal
import subprocess
import sys
import time
from pathlib import Path

# ↓↓↓ ANPASSEN ↓↓↓
BOTTLE_PATH = Path.home() / ".var/app/com.usebottles.bottles/data/bottles/bottles/<BOTTLE_NAME>"
RUNNER      = Path.home() / ".var/app/com.usebottles.bottles/data/bottles/runners/<RUNNER_NAME>"
APP_EXE     = BOTTLE_PATH / "drive_c/<APP_DIR>/<APP_EXE_NAME>.exe"
WINE_BIN    = RUNNER / "bin/wine"
WINESERVER  = RUNNER / "bin/wineserver"
EXE_FLAGS   = ['--no-sandbox', '--disable-software-rasterizer']

# Login-Token-Support (siehe references/windows-apps-on-linux.md)
TOKEN_VAR   = '<PROVIDER>_USER_TOKEN'   # z.B. 'HILO_USER_TOKEN', 'GITHUB_TOKEN'
TOKEN_FILE  = Path.home() / ".config/<app-name>-token"

# PROCESS_PATTERN: Regex für pgrep/pkill zur Identifikation der App-Prozesse.
# ⚠️  NIEMALS nur den Herstellernamen (z.B. "MiniMax") verwenden — matcht dann
#      Hermes-Subagent-Prozesse die denselben Namen als Modellnamen tragen!
#      Stattdessen IMMER mit \\.exe suffix + wineserver + wine-preloader.
#      Beispiele:
#        r"(MiniMax Code\\.exe|wineserver|wine-preloader|wine64-preloader)"
#        r"(AppName\\.exe|wineserver|wine-preloader|wine64-preloader)"
PROCESS_PATTERN = r"(<APP_EXE_NAME>\\.exe|wineserver|wine-preloader|wine64-preloader)"
# ↑↑↑ ANPASSEN ↑↑↑


def check_setup() -> bool:
    issues = []
    if not BOTTLE_PATH.exists():
        issues.append(f"Bottle fehlt: {BOTTLE_PATH}")
    if not WINE_BIN.exists():
        issues.append(f"Wine-Binary fehlt: {WINE_BIN}")
    if not APP_EXE.exists():
        issues.append(f"App-EXE fehlt: {APP_EXE}")
    if issues:
        print("❌ Setup-Fehler:", file=sys.stderr)
        for i in issues:
            print(f"   {i}", file=sys.stderr)
        return False
    print("✅ Setup OK:")
    print(f"   Bottle: {BOTTLE_PATH}")
    print(f"   Runner: {RUNNER.name} (Wine {RUNNER.name.split('-')[-1]})")
    print(f"   App: {APP_EXE.parent.name}/{APP_EXE.name}")
    return True


def kill_prior() -> None:
    """Beende sauber alle Wine/App-Prozesse für diese Bottle."""
    print("🛑 Beende laufende Wine-Prozesse...")
    if WINESERVER.exists():
        try:
            subprocess.run([str(WINESERVER), "-k"], timeout=10)
        except subprocess.TimeoutExpired:
            print("⚠️  wineserver -k Timeout — pkill fallback")

    # Explizite pkill Patterns: nur \\.exe + wineserver + wine-preloader
    # ⚠️  NIEMALS `pkill -f "MiniMax"` oder APP_EXE.stem ohne .exe-Suffix!
    #      Das matcht Hermes-Subagent-Prozesse mit Modellname "MiniMax-M3".
    #      Sowas führte am 2026-07-08 zu false-positives → immer PROCESS_PATTERN verwenden.
    subprocess.run(["pkill", "-9", "-f", PROCESS_PATTERN], check=False)
    time.sleep(1)

    # Verifikation: pgrep mit dem SELBEN Pattern, eigenen Prozess rausfiltern
    procs = subprocess.run(
        ["pgrep", "-af", PROCESS_PATTERN],
        capture_output=True, text=True,
    )
    echte_prozesse = [
        line for line in procs.stdout.splitlines()
        if line and "pgrep" not in line
    ]
    if not echte_prozesse:
        print("✅ Alle Wine/App-Prozesse beendet")
    else:
        remaining = "\n".join(echte_prozesse)
        print(f"⚠️  Folgende Prozesse laufen noch:\n{remaining}")


def start_hub(log_path: str | None = None) -> int:
    if not check_setup():
        return 1

    # Sauberes Wine-Setup vor jedem Start
    if WINESERVER.exists():
        try:
            subprocess.run([str(WINESERVER), "-k"], timeout=5, check=False)
        except subprocess.TimeoutExpired:
            pass
        time.sleep(1)

    print(f"\n🚀 Starte {APP_EXE.name} via Wine + PTY")
    print(f"   Wine: {WINE_BIN}")
    print(f"   Prefix: {BOTTLE_PATH}")
    if log_path:
        print(f"   Log: {log_path}")
    print()

    # PTY allokieren — DAS ist der entscheidende Fix (Node EBADF workaround)
    master_fd, slave_fd = pty.openpty()

    env = os.environ.copy()
    env['WINEPREFIX'] = str(BOTTLE_PATH)
    env['WINEESYNC']  = '1'
    env['WINEFSYNC']  = '1'
    env['DISPLAY']    = os.environ.get('DISPLAY', ':1')
    env['WAYLAND_DISPLAY'] = os.environ.get('WAYLAND_DISPLAY', 'wayland-0')
    env['WINEDEBUG']  = '-all'
    env['ELECTRON_DISABLE_SECURITY_WARNINGS'] = '1'

    # Login-Token-Pattern: Env-Var ODER Token-Datei
    if TOKEN_VAR not in env:
        if TOKEN_FILE.exists():
            env[f'{TOKEN_VAR}_FILE'] = str(TOKEN_FILE)
            print(f"🔑 Lade Token aus: {TOKEN_FILE}")
        else:
            print("ℹ️  Kein Token — App-Login erforderlich (Klick in der App)")
            print(f"   Token anlegen: echo '<TOKEN>' > {TOKEN_FILE}")
            print(f"   Oder Env-Var: {TOKEN_VAR}='<TOKEN>' {Path(sys.argv[0]).name}")
    else:
        print(f"🔑 Token via Env-Var {TOKEN_VAR}")

    proc = subprocess.Popen(
        [str(WINE_BIN), str(APP_EXE), *EXE_FLAGS],
        stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
        env=env, preexec_fn=os.setsid,
        cwd=str(APP_EXE.parent),
    )
    print(f"   PID: {proc.pid}")
    print(f"   Strg+C beendet sauber.\n")

    def handle_signal(signum, frame):
        print("\n\n🛑 Beende …")
        kill_prior()
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    log_fp = None
    if log_path:
        log_fp = open(log_path, 'wb', buffering=0)

    try:
        while True:
            if proc.poll() is not None:
                print(f"\n⚠️  Prozess beendet (Exit {proc.returncode})")
                break
            rlist, _, _ = select.select([master_fd], [], [], 0.5)
            if rlist:
                try:
                    data = os.read(master_fd, 4096)
                    if not data:
                        break
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
                    if log_fp:
                        log_fp.write(data)
                except OSError:
                    break
    except KeyboardInterrupt:
        handle_signal(None, None)

    if log_fp:
        log_fp.close()
    kill_prior()
    return proc.returncode or 0


def main() -> int:
    parser = argparse.ArgumentParser(description='Electron-Wine-App-Starter')
    parser.add_argument('--check', action='store_true',
                        help='Nur Setup prüfen, nicht starten')
    parser.add_argument('--kill', action='store_true',
                        help='Wine/App-Prozesse beenden')
    parser.add_argument('--log', metavar='PATH', type=str,
                        help='PTY-Output in FILE loggen')
    args = parser.parse_args()

    if args.check:
        return 0 if check_setup() else 1
    if args.kill:
        kill_prior()
        return 0
    return start_hub(log_path=args.log)


if __name__ == '__main__':
    sys.exit(main())
