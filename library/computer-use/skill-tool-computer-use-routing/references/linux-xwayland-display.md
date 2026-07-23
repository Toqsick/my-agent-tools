# Linux Wayland + cua-driver: Xwayland-Auth-File-Rezept

## Symptom

`hermes computer-use doctor` meldet:

```
[warn] display server: neither DISPLAY nor WAYLAND_DISPLAY set
       — window-driving tools will fail
[warn] X11 connection: no top-level windows returned
       (possible disconnected or inaccessible X11 display)
[ok  ] AT-SPI: org.a11y.Bus reachable via session bus
```

Auf einem reinen Wayland-Desktop (Zorin/GNOME mit Xwayland-Backend) erbt der cua-driver-Subprocess keine Display-Umgebungsvariablen vom Hermes-Shell. Ohne sie sieht der Driver **keine Fenster** und liefert:

```
$ cua-driver call list_windows '{"on_screen_only": true}'
{"windows": []}

$ cua-driver call get_window_state '{"pid": 56658}'
Missing required integer field: pid   # weil window_id fehlt
```

## Root Cause

GNOME/Wayland-Sessions starten Xwayland als `rootless`-X-Server mit `XAUTHORITY` auf einer **zufällig generierten Datei** im `XDG_RUNTIME_DIR`:

```
/usr/bin/Xwayland :1 -rootless -noreset -accessx -core \
  -auth /run/user/1000/.mutter-Xwaylandauth.L8U0R3 \
  -listenfd 4 -listenfd 5 -displayfd 6 -initfd 7
```

Diese `XAUTHORITY` muss beim cua-driver-Call mitgegeben werden, sonst verweigert Xwayland die Verbindung.

## Recipe

### Schritt 1: Xwayland-Auth-File finden

```bash
# Methode 1: ps
ps -eo pid,cmd | grep -E 'Xwayland|mutter-Xwaylandauth'
# → /run/user/1000/.mutter-Xwaylandauth.L8U0R3

# Methode 2: ls im XDG_RUNTIME_DIR
ls /run/user/1000/ | grep -i xwayland
# → .mutter-Xwaylandauth.L8U0R3

# DISPLAY-Nummer herausfinden (meist :1)
echo $DISPLAY    # aktuelle Shell-Session
ps -eo cmd | grep Xwayland | head -1
```

### Schritt 2: Vor-fix verifizieren

```bash
cua-driver doctor
# → [warn] display server: neither DISPLAY nor WAYLAND_DISPLAY set
```

### Schritt 3: Mit Env-Injection re-verifizieren

```bash
DISPLAY=:1 \
XAUTHORITY=/run/user/1000/.mutter-Xwaylandauth.L8U0R3 \
cua-driver doctor
```

Erwartetes Resultat:

```
[ok  ] display server: X11 (DISPLAY=:1)
[ok  ] X11 connection: connected, 2 visible top-level windows
[ok  ] AT-SPI: org.a11y.Bus reachable via session bus
```

### Schritt 4: In Python-Skripten übernehmen

```python
import subprocess
import os

# Display-Env-Vars IMMER setzen, bevor du cua-driver aufrufst
env = os.environ.copy()
env["DISPLAY"] = ":1"
env["XAUTHORITY"] = "/run/user/1000/.mutter-Xwaylandauth.L8U0R3"

result = subprocess.run(
    ["cua-driver", "call", "get_window_state", json.dumps({"pid": <pid>})],
    capture_output=True, text=True, env=env, timeout=20
)
```

Wenn das Xwayland-Auth-File bei jedem Login neu generiert wird (was es tut), kannst du es zur Laufzeit ermitteln:

```python
import glob
auth_files = glob.glob("/run/user/*/.mutter-Xwaylandauth.*")
if auth_files:
    env["XAUTHORITY"] = auth_files[0]
```

### Schritt 5: Wayland-Backend (alternativ)

Wenn du statt Xwayland das experimentelle **native Wayland-Backend** von cua-driver nutzen willst:

```bash
CUA_DRIVER_RS_ENABLE_WAYLAND=1 cua-driver doctor
# → [warn] wayland_backend: Wayland session detected, but the experimental
#         backend is opt-in. Set CUA_DRIVER_RS_ENABLE_WAYLAND=1 to enable
```

Setze die Env-Var auch im Python-Subprocess:

```python
env["CUA_DRIVER_RS_ENABLE_WAYLAND"] = "1"
```

⚠️ **Achtung**: Der native Wayland-Backend ist als **experimentell** markiert. Auf Zorin/GNOME mit Xwayland ist der Xwayland-Approach (Schritte 1–4) der robustere und offiziell unterstützte Pfad.

## Validation-Checklist

- [ ] `cua-driver doctor` zeigt `✅ X11 connection: connected` (statt `[warn]`)
- [ ] `cua-driver call list_windows '{"on_screen_only": true}'` gibt nicht-leeres `{"windows": [...]}` zurück
- [ ] `pgrep -af Xwayland` zeigt die laufende Xwayland-Instanz
- [ ] `ls /run/user/1000/.mutter-Xwaylandauth.*` zeigt mindestens eine Auth-Datei
- [ ] In Python: `subprocess.run(..., env=env)` (statt ohne env) wird verwendet

## Pitfalls

- **`$DISPLAY` nicht gesetzt in der Shell** — wenn der User via SSH oder in einem Cron-Job ohne Display arbeitet, funktioniert NICHTS. Erst mit Display testen.
- **Falsche DISPLAY-Nummer** — wenn mehrere Xwayland-Instanzen laufen, muss man die richtige `:N`-Nummer aus `ps` nehmen.
- **Vergessene `XAUTHORITY`** — die häufigste Ursache für "connected, aber keine Fenster"-Symptome. Ohne XAUTHORITY erlaubt Xwayland keine Verbindungen.
- **Auth-File-Pfad ändert sich bei Login** — bei Xwayland wird pro Login ein neuer zufälliger Suffix generiert. Hartkodierte Pfade gehen nach Reboot kaputt. **Immer zur Laufzeit ermitteln** mit `glob.glob`.
- **Wayland-Only-Desktops (kein Xwayland)** — auf reinen Wayland-Sessions (z.B. Sway ohne Xwayland) muss man entweder `CUA_DRIVER_RS_ENABLE_WAYLAND=1` setzen oder Xwayland installieren.
- **Token-Cost-Spirale vermeiden** — Computer-Use ist teuer (Latenz 5-15s, hohe Token-Costs). Wenn eine Aufgabe auch über Terminal/CLI lösbar ist, immer **Stufe 1–2 bevorzugen** (siehe skill-tool-computer-use-routing Stufen-Modell).

## Gotchas für Multi-Process-Setups

Wenn du cua-driver aus einem **Hintergrund-Daemon** oder einem **Cron-Job** aufrufst, sind die Display-Variablen typischerweise NICHT in der Umgebung:

```python
# In einem Cron-Job / Daemon: IMMER selbst setzen
import subprocess
import os

env = os.environ.copy()
env["DISPLAY"] = ":1"
env["XAUTHORITY"] = "/run/user/1000/.mutter-Xwaylandauth.L8U0R3"

result = subprocess.run(
    ["cua-driver", "doctor"],
    env=env, capture_output=True, text=True
)
```

Wenn der Daemon als root oder anderer User läuft, hat er evtl. keinen Zugriff auf `/run/user/1000/` (User-spezifisches Runtime-Dir). Lösung: Daemon als derselbe User wie die Desktop-Session laufen lassen.

## Related

- `cua-driver` upstream: https://github.com/trycua/cua
- `computer-use` skill (gebündelt) — die zugrundeliegende Tool-Vokabular-Schicht
- `~/.hermes/skills/computer-use/greyhack-game-observer/scripts/greyhack_capture.py` — funktionierende Implementierung dieses Patterns für GreyHack-Screenshots