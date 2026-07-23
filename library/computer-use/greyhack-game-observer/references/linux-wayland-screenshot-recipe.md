# Linux Wayland + GreyHack Observer: Screenshot-Rezept

## Problem

Auf Bastis Zorin-/GNOME-Wayland-Desktop funktioniert der naive `from hermes_tools import computer_use`-Pfad **NICHT**. `hermes_tools` enthält das `computer_use`-Symbol in der Subprocess-Sandbox nicht (verifiziert 2026-07-06: `ImportError: cannot import name 'computer_use' from 'hermes_tools'`). Der falsche Pfad lässt sich leicht aus dem `computer-use`-Skill-Text kopieren, der den `computer_use(action=...)`-Aufruf direkt zeigt — aber dieses Tool wird **nur** über die Hermes-Desktop-/TUI-Laufzeitumgebung bereitgestellt, NICHT in Hermes-Subprocess-Code.

## Diagnose-Befehle

```bash
# Schritt 1: cua-driver installiert?
hermes computer-use status
# → cua-driver: installed at /home/bratan/.local/bin/cua-driver (cua-driver 0.7.0)

# Schritt 2: Welche Display-Probleme gibt es?
hermes computer-use doctor
# → zeigt u.U. [warn] display server: neither DISPLAY nor WAYLAND_DISPLAY set

# Schritt 3: Welche Xwayland-Instanz läuft?
ps -eo pid,cmd | grep -E 'Xwayland|mutter-Xwaylandauth'
# → /usr/bin/Xwayland :1 -rootless -auth /run/user/1000/.mutter-Xwaylandauth.L8U0R3 ...

# Schritt 4: Auth-File existent?
ls /run/user/1000/.mutter-Xwaylandauth.* 2>/dev/null
# → /run/user/1000/.mutter-Xwaylandauth.L8U0R3
```

## Funktionierender Screenshot-Pfad

```python
import subprocess
import os
import json
import base64
from pathlib import Path

# 1) Display-Env INJEKTIEREN — cua-driver erbt sonst keine
env = os.environ.copy()
env["DISPLAY"] = ":1"
env["XAUTHORITY"] = "/run/user/1000/.mutter-Xwaylandauth.L8U0R3"

# 2) PID der Ziel-App finden (z.B. Steam / Grey Hack)
pgrep_result = subprocess.run(
    ["pgrep", "-f", "steam"],
    capture_output=True, text=True, timeout=5, env=env
)
pids = [p for p in pgrep_result.stdout.strip().split("\n") if p.isdigit()]
if not pids:
    raise RuntimeError("Kein Steam-/Grey-Hack-Prozess gefunden")

# 3) cua-driver: Screenshot via get_window_state
cua_result = subprocess.run(
    ["cua-driver", "call", "get_window_state", json.dumps({"pid": int(pids[0])})],
    capture_output=True, text=True, env=env, timeout=20
)
if cua_result.returncode != 0:
    raise RuntimeError(f"cua-driver get_window_state fehlgeschlagen: {cua_result.stderr}")

# 4) Antwort parsen — Screenshot ist base64-encoded in structuredContent
data = json.loads(cua_result.stdout)
screenshot_b64 = data.get("screenshot_base64") or data.get("screenshot")
if not screenshot_b64:
    raise RuntimeError("cua-driver hat keinen Screenshot geliefert")
screenshot_bytes = base64.b64decode(screenshot_b64)
```

## 3-Tier-Fallback (in `greyhack_capture.py` implementiert)

Wenn `cua-driver` fehlschlägt, probiere diese Fallbacks der Reihe nach:

```python
# Fallback 1: scrot mit Display-Env
tmp_path = Path("/tmp/greyhack_observer_fallback.png")
subprocess.run(["scrot", str(tmp_path)], check=True, timeout=5, env=env)
if tmp_path.exists():
    return tmp_path.read_bytes()

# Fallback 2: gnome-screenshot
subprocess.run(["gnome-screenshot", "-f", str(tmp_path)], check=True, timeout=5, env=env)
if tmp_path.exists():
    return tmp_path.read_bytes()

# Fallback 3: grim (Wayland nativ)
subprocess.run(["grim", str(tmp_path)], check=True, timeout=5, env=env)
if tmp_path.exists():
    return tmp_path.read_bytes()

raise RuntimeError("Kein Screenshot-Tool verfügbar — Installiere eines!")
```

## Validation-Test

Vor dem ersten echten Run validieren:

```python
import subprocess, os, json

env = os.environ.copy()
env["DISPLAY"] = ":1"
env["XAUTHORITY"] = "/run/user/1000/.mutter-Xwaylandauth.L8U0R3"

# Test 1: cua-driver doctor
result = subprocess.run(
    ["cua-driver", "doctor"], capture_output=True, text=True, env=env
)
assert "X11 connection: connected" in result.stdout, "X11 nicht verbunden!"
print("✅ cua-driver doctor OK")

# Test 2: list_windows findet etwas
result = subprocess.run(
    ["cua-driver", "call", "list_windows", json.dumps({"on_screen_only": True})],
    capture_output=True, text=True, env=env
)
data = json.loads(result.stdout)
windows = data.get("windows", [])
assert len(windows) > 0, "Keine Fenster gefunden!"
print(f"✅ list_windows OK ({len(windows)} Fenster)")

# Test 3: get_window_state liefert Screenshot
if windows:
    pid = windows[0].get("pid")
    if pid:
        result = subprocess.run(
            ["cua-driver", "call", "get_window_state", json.dumps({"pid": pid})],
            capture_output=True, text=True, env=env, timeout=20
        )
        assert result.returncode == 0
        print("✅ get_window_state OK")
```

## Edge-Case: Apps nicht sichtbar

Wenn `list_windows` 0 Fenster findet, obwohl die App läuft:

1. **App im Hintergrund / minimiert**: cua-driver erfasst nur sichtbare Fenster per Default. Bei `on_screen_only=true` werden minimierte Fenster gefiltert. Lösung: ohne `on_screen_only` listen.
2. **App crasht beim Start**: pidof zeigt PID, aber kein Fenster. Dann existiert kein Screenshot. Lösung: App im Vordergrund starten, dann nochmal versuchen.
3. **WAYLAND_DISPLAY statt DISPLAY**: Auf reinen Wayland-Setups (z.B. Sway ohne Xwayland) muss `WAYLAND_DISPLAY=wayland-0` gesetzt sein statt `DISPLAY`. cua-driver bevorzugt in dieser Reihenfolge: Wayland → X11 → sonst.

## Gotchas für Background-Runs (Cron / nohup)

Wenn der Observer als Daemon oder Cron läuft, sind die Display-Variablen typischerweise NICHT in der Umgebung:

```python
# IMMER explizit setzen, nicht von env erben
import glob

env = os.environ.copy()
env["DISPLAY"] = ":1"

# Auth-File zur Laufzeit ermitteln (ändert sich pro Login!)
auth = glob.glob("/run/user/*/.mutter-Xwaylandauth.*")
if auth:
    env["XAUTHORITY"] = auth[0]
else:
    raise RuntimeError("Kein Xwayland-Auth-File gefunden — Desktop läuft?")
```

## Reference

- Skill: `skill-tool-computer-use-routing/references/linux-xwayland-display.md` — generisches Linux-Wayland-cua-driver-Rezept
- Skill: `computer-use` (gebündelt) — die zugrundeliegende Tool-Vokabular-Schicht
- cua-driver upstream: https://github.com/trycua/cua
- Working script: `~/.hermes/skills/computer-use/greyhack-game-observer/scripts/greyhack_capture.py`