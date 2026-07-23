---
title: Wayland + 595-open + RTX 50xx — NV-CONTROL-Tools sind IMMER falsch
datum: 2026-07-05
hardware: MEDION ERAZER 17 P1 · RTX 5060 · i7-13620H · Zorin 18.1
treiber: 595-open
session-beleg: perf-tuning-plan Chat 2026-07-05
---

# Symptom

Nach GPU-Tuning-Versuch (egal ob via `nvidia-settings`, Coolbits, GreenWithEnvy / GWE, oder `xorg.conf.d/10-nvidia-coolbits.conf`):

1. nvidia-settings friert bei "Querying Tree..." ein, muss per SIGKILL beendet werden.
2. GWE crasht mit `Cannot connect to X server` ODER zeigt NV-CONTROL-Felder leer.
3. Co dbits-OC-Versuch endet in Hard-Lock + Reboot-Schleife.
4. `nvidia-settings -q GpuPowerMizerMode` zeigt nichts/leer statt 0/1.

# Ursache

**NV-CONTROL ist eine X11-Extension** (libXnvctrl mit `libXNVCtrl.so` und DBUS-Bridge). Wayland hat keine X11-Extensions. Versuche, NV-CONTROL von einer Wayland-Session aus zu nutzen:

- Resultieren in **stillem Hang** oder **Hard-Lock** der Compositor-Komponente, die den X11-Wrapper hält.
- Kein freundlicher Error — Wayland-Compositor crashed ohne Log-Eintrag (manchmal ist `journalctl --user -b | grep -i "gnome-shell\|mutter"` aufschlussreich).
- Co dbits in `xorg.conf.d/` ist **tot** unter Wayland, weil Mutter / KWin mit modesetting/EGL rendert, nicht via NV-CONTROL.

# Werkzeug-Hierarchie für RTX 50xx + Wayland + 595-open

| Werkzeug | Funktioniert? | Bemerkung |
|---|---|---|
| 🥇 `nvidia_oc` (Dreaming-Codes) | ✅ Ja | NVML-basiert, Wayland-sicher |
| 🥈 `nvoc` (martinstark) | ✅ Ja | Dedizierter Blackwell-Support, mehr Optionen |
| 🥉 `nvidia-smi` direkt | ⚠️ Nur Read | Set-Capabilities via `-pl` / `-lgc` (Hardware-Range beachten) |
| ❌ `nvidia-settings` | ❌ Nein | Braucht NV-CONTROL → X11-Extension → Wayland crasht |
| ❌ `Coolbits` in `xorg.conf.d/` | ❌ Nein | Wirkt nur bei X11-Sessions via NV-CONTROL |
| ❌ GreenWithEnvy | ❌ Nein | Setzt auf NV-CONTROL auf |
| ❌ `nvidia-prime` für OC | ❌ Nein | Macht PRIME-Routing, nicht OC |

**Einzige "offizielle" NVML-Route für direkte OC-Controls:**

```
nvidia-smi -pl <power_limit_mW>      # Power-Limit (Hardware-Range beachten, RTX 5060 Laptop = 5-115W)
nvidia-smi -lgc <freq_mhz>           # GPU-Clock-Lock (invasiv, kann andere Karten stören)
nvidia-smi -lmc <freq_mhz>           # Memory-Clock-Lock
```

Aber für OC-Offsets (Core +X MHz / Memory +Y MHz) ist `nvidia_oc`/`nvoc` der gangbare Weg.

# Wenn der User hartnäckig X11-Tools will

Manche User wollen GWE's Drag-and-Drop Fan-Curve-Editor. Dann:

```bash
# GDM auf X11 umstellen
sudo sed -i 's/#WaylandEnable=false/WaylandEnable=false/' /etc/gdm3/custom.conf
# Logout, beim Login-Screen "Zorin (Xorg)" wählen
```

**Was verloren geht:**
- Vari-Bind (Multi-Monitor-Tiling)
- Screen-Capture via PipeWire in voller Qualität
- Fraktional-HiDPI-Scaling

**Was gewonnen wird:**
- NV-CONTROL-Funktionen (nvidia-settings, GWE voller Funktionsumfang)
- Co dbits-OC ohne Umweg

Für Basti (wayland-Vari-Bind-Fan, Multi-Monitor, Screen-Capture) **nicht** empfehlenswert. Dokumentiere es als Fallback in 03 Projekte/Perf-Tuning RTX5060/Plan Stufe 6.2.

# Verwandte Themen

- Pitfall #23 — Kernel-Lockdown blockiert NVML (oft Doppelursache bei Basti)
- `references/kernel-lockdown-nvml-blocks-tuning-2026-07-05.md`
- Pitfall #25 — GameMode [gpu]-Block muss in `/etc/gamemode.ini`
- `references/prime-offload-env-vars-2026-06-28.md` — PRIME-Setup
