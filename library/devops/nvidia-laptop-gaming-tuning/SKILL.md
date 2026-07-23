---
name: nvidia-laptop-gaming-tuning
title: NVIDIA Laptop Gaming Performance Tuning (Linux)
description: |
  Use when tuning gaming performance on a Linux laptop with NVIDIA Optimus, diagnosing hybrid-GPU bottlenecks, or validating power and graphics settings.
  NOT for desktop systems without hybrid graphics, Windows-only tuning, or unsafe overclocking and thermal-limit bypasses.
  Provides an evidence-first workflow for GPU selection, power profiles, driver settings, and repeatable game performance validation.
triggers:
- User wants better gaming/GPU performance on an NVIDIA laptop (Linux)
- nvidia-powerd fails to start / "not allowed to own service nvidia.powerd.server"
- nvidia-powerd failed on Wayland (GPU not visible as DRM device, service crashes
  — expected behavior on Optimus+Wayland)
- GameMode "Verifying CPU governor setting: Failed"
- Dynamic Boost not active on a laptop that supports it
- CPU governor stuck on powersave on intel_pstate systems
- nvidia-smi reports "No devices were found" despite driver loaded
- dmesg shows "requires use of the NVIDIA open kernel modules" (RTX 50xx)
- User says games run on integrated GPU / NVIDIA not utilized in games
- glxinfo shows "Mesa Intel" instead of NVIDIA
- nvidia-smi shows only desktop processes, no games
- Desktop "blinkt" (GDM restart loops) without boot-loop — check NVReg configs
- GPU in D3cold causing nvidia-smi communication failure
- User says driver does not recognize GPU - always check D3cold first, not Device-ID!
- nvidia_drv.so missing despite xserver-xorg-video-nvidia-595 being installed
- Boot-Loop via xorg.conf + missing nvidia_drv.so + rc-Zombie packages
- User wants update path info BEFORE changes (no blind apt-install)
- Desktop "blinkt" / GDM restart loops without boot-loop — check NVReg configs first
- User boots into wrong kernel (e.g. lowlatency instead of generic) — nvidia.ko not
  built for this kernel, nvidia-smi fails
- Native Linux game (non-Proton, e.g. CS2) runs on iGPU despite prime-select on-demand
- Flatpak Steam game doesn't respond to prime-run or profile.d env vars (pressure-vessel
  strips them)
- RTX 50xx + Wayland + nvidia-settings/Coolbits crashes/freezes → use NVML-only tools
  instead
- GPU OC tuning crashes / driver lockup on Wayland → check Kernel-Lockdown status
  FIRST
- GameMode GPU optimizations silently disabled → check [gpu]-block is in /etc/gamemode.ini
  not user config
- nvmlDeviceGetCount returns 0 with no obvious cause on Lockdown=integrity + Secure
  Boot systems
version: 1.5.0
author: Hermes Agent
changelog:
- 2026-07-05 - Basti RTX 5060 Wayland session - Lockdown-pitfall
license: MIT
lane: worker-heavy
reasoning_effort: xhigh
trigger_keywords: ['tuning', 'performance', 'hybrid', 'power', 'graphics']
keywords: ['tuning', 'performance', 'hybrid', 'power', 'graphics']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['claude-gaming-optimizer']
---


# NVIDIA Laptop Gaming Performance Tuning

## Diagnostic First (always)

```bash

set -euo pipefail
nvidia-smi --query-gpu=name,driver_version,clocks.max.graphics --format=csv
prime-select query                                    # 'nvidia' for max FPS, 'on-demand' for PRIME render offload
cat /proc/driver/nvidia/gpus/*/power | grep -i "Dynamic Boost"   # Supported?
systemctl is-active nvidia-powerd                     # Dynamic Boost daemon
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_driver   # intel_pstate?
cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference
powerprofilesctl get
```

## Diagnostic Layer 0: Quick 5-Second Scan (BEFORE any other action)

Immer als erstes — identifiziert die häufigsten Probleme ohne Änderungen:

```bash

set -euo pipefail
# Ist nvidia-smi generell erreichbar?
nvidia-smi >/dev/null 2>&1 && echo "nvidia-smi OK" || echo "nvidia-smi FAIL"

# Xorg-Treiber vorhanden? (wichtig für X11, nicht für nvidia-smi!)
ls /usr/lib/xorg/modules/drivers/nvidia* 2>/dev/null || echo "nvidia_drv.so MISSING"

# xorg.conf von nvidia-xconfig? (BOOT-LOOP-RISIKO!)
ls /etc/X11/xorg.conf 2>/dev/null && echo "xorg.conf EXISTS (risky)" || echo "no xorg.conf"

# Zombie-Pakete?
dpkg -l | grep nvidia | grep ^rc || echo "no zombie packages"

# DKMS-Build?
dkms status | grep nvidia

# GPU Power State (D3cold = unerreichbar für nvidia-smi!)
cat /sys/bus/pci/devices/*/power_state 2>/dev/null || echo "cannot read power_state"

# "requires open kernel modules" Warning? (RTX 50xx specific)
sudo dmesg | grep -i "open kernel modules" >/dev/null && echo "WARNING: proprietary nvidia module loaded, open kernel module expected"

# PRIME Offload Provider count
xrandr --listproviders 2>/dev/null | head -1

# NVML Device Count (alternative to nvidia-smi when it fails)
python3 -c "
import ctypes
try:
    lib = ctypes.CDLL('libnvidia-ml.so.1')
    lib.nvmlInit()
    count = ctypes.c_uint()
    lib.nvmlDeviceGetCount(ctypes.byref(count))
    print(f'NVML Devices: {count.value}')
except: print('NVML not available')
" 2>&1

**VOR JEDEM USER-INPUT PRÜFEN (Zero-Actions-Check):**
```bash
# Nur read-only, keine Änderungen - User will wissen was updatable ist
dpkg -l | grep nvidia | grep ^rc                              # Muss leer sein!
apt-cache policy nvidia-driver-595 | grep Candidate            # Neueste verfügbar?
apt-cache policy libxnvctrl0 | grep Candidate                  # Mismatch prüfen
ls /usr/lib/xorg/modules/drivers/nvidia_drv.so                # Existiert?
dpkg -L xserver-xorg-video-nvidia-595 | grep "\.so"           # ODER Paket leer?
```

set -euo pipefail
Wenn der User "Treiber-Update" will, sag ihm:
- Welche Version aktuell läuft
- Welche Version verfügbar ist (Candidate)
- Ob libxnvctrl0 mismatch besteht (nie updated für >535 Treiber)
- Dass nvidia_drv.so ggf. durch Reinstall kommt (nicht durch Update!)

DANN erst fixen nach Freigabe. NICHT blind `apt install` ohne User wissen!

## CRITICAL: nvidia-smi != Xorg Driver

Häufiger Irrtum: `nvidia-smi` funktioniert OHNE `nvidia_drv.so`. Sie nutzt
`/dev/nvidia0` direkt via kernel interface. Wenn nvidia-smi failt liegt das
NICHT an fehlendem Xorg-Treiber. Wenn Xorg failt (X11-Session) KANN es am
fehlenden `nvidia_drv.so` liegen.

Umgekehrt: `nvidia_drv.so` fehlt + `/etc/X11/xorg.conf` fordert `nvidia` Driver =
Xorg crasht ("Failed to load module nvidia"). Auf Wayland nicht relevant (Mutter
nutzt modesetting/EGL).

Hierarchie:
1. nvidia-smi failt → prüfe D3cold / Power Management / Device Nodes
2. Xorg failt (X11) → prüfe nvidia_drv.so / xorg.conf / Zombie-Pakete
3. Beides failt → prüfe DKMS / Zombie-Pakete

## CRITICAL: intel_pstate uses EPP, NOT the classic governor

On modern Intel laptops `scaling_driver` is `intel_pstate` in **active mode**.
Here the `scaling_governor` string (`powersave`/`performance`) is NOT the real
lever — the actual knob is **EPP (Energy Performance Preference)**.

- `powersave` governor + EPP `performance` == effectively **full boost**.
- Blindly forcing the governor to `performance` does **nothing** useful.
- The real lever: set `power-profiles-daemon` profile to `performance`, which
  pulls EPP to `performance` on all cores. This needs **no sudo**:
  ```bash
  powerprofilesctl set performance   # EPP -> performance (max boost)
  powerprofilesctl set balanced      # EPP -> balance_performance (quiet)
  ```

set -euo pipefail
- This is also why Feral GameMode's built-in governor switch FAILS on these
  systems ("Verifying CPU governor setting: Failed", pkexec "Not authorized").
  Don't fight it — use GameMode custom hooks calling powerprofilesctl instead.

## Fix: nvidia-powerd (Dynamic Boost) won't start

Symptom in `journalctl -u nvidia-powerd`:
```
Error requesting D-Bus name (Connection ... is not allowed to own the
service "nvidia.powerd.server" due to security policies ...)
```

set -euo pipefail
Some driver packages (e.g. 595) ship the `/usr/bin/nvidia-powerd` binary but
NOT the systemd service and NOT the DBus policy. Three things needed:

**1. Service file** — use the one the driver ships as docs (Type=simple!):
```bash
sudo cp /usr/share/doc/nvidia-kernel-common-*/nvidia-powerd.service \
        /etc/systemd/system/nvidia-powerd.service
sudo systemctl daemon-reload
```

set -euo pipefail
Do NOT hand-write a `Type=dbus` unit — it hangs in `activating` waiting for a
bus name. The official unit is `Type=simple`.

**2. DBus system policy** — `/etc/dbus-1/system.d/nvidia-powerd.conf`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <policy user="root">
    <allow own="nvidia.powerd.server"/>
    <allow send_destination="nvidia.powerd.server"/>
    <allow receive_sender="nvidia.powerd.server"/>
  </policy>
  <policy context="default">
    <allow send_destination="nvidia.powerd.server"/>
    <allow receive_sender="nvidia.powerd.server"/>
  </policy>
</busconfig>
```

set -euo pipefail
**3. PERMISSIONS PITFALL** — the DBus daemon runs as user `messagebus`/`message+`
and cannot read a `-rw-------` file. The policy MUST be world-readable:
```bash
sudo chmod 644 /etc/dbus-1/system.d/nvidia-powerd.conf
sudo pkill -HUP dbus-daemon        # reload policy
sudo systemctl enable --now nvidia-powerd
journalctl -u nvidia-powerd --since "30 seconds ago"   # want: "DBus Connection is established"
```

set -euo pipefail
Note: a harmless `ERROR! Error(1f) in setting the short timescale limit` may
appear — that's an optional register some laptops don't expose; Dynamic Boost
still works.

## Feral GameMode setup (auto perf on game launch)

```bash
sudo apt install -y gamemode
systemctl --user enable --now gamemoded
```

set -euo pipefail
`/etc/gamemode.ini` (chmod 644!):
```ini
[general]
renice=10
ioprio=0
softrealtime=auto
[gpu]
apply_gpu_optimisations=accept-responsibility
gpu_device=0
nv_powermizer_mode=1
[custom]
start=/home/USER/bin/gamemode-start.sh
end=/home/USER/bin/gamemode-end.sh
```

set -euo pipefail
Hooks (chmod +x), because the governor path is dead on intel_pstate:
```bash
# gamemode-start.sh
powerprofilesctl set performance
# gamemode-end.sh
powerprofilesctl set balanced
```

set -euo pipefail
Test end-to-end:
```bash
gamemoderun bash -c 'cat /sys/devices/system/cpu/cpu0/cpufreq/energy_performance_preference'
# should print: performance
```

set -euo pipefail
**Steam:** per-game launch option `gamemoderun %command%` (also for Proton games).

## Boot-Loop Recovery

**PRINZIP: Erst gründlich Research NEU — dann fixen!**
- Read-Only Diagnose: Logs, Paket-Status, Kernel-Module checken OHNE Änderungen
- 3-Expert Research parallel (Boot-Loop, Treiber-State, Web)
- Synthese + Safe-Fix-Plan → User-Freigabe → Fix
- NIEMALS blind `apt install/remove` oder `nvidia-xconfig` ohne Diagnose

**Symptom:** `nvidia-smi` fails, Boot-Loop nach GPU-Tweak/Treiberwechsel.
**Top 3 Ursachen:**
1. 🔴 Zombie-Pakete (rc) von Treiberwechseln — `dpkg -l | grep nvidia | grep ^rc`
2. 🔴 Fehlendes `xserver-xorg-video-nvidia-595` (kein `nvidia_drv.so`)
3. 🔴 DKMS-Build fehlt — `dkms status | grep nvidia`

**Vollständige Recovery in** `references/boot-loop-recovery.md`.

**Key rule:** NEVER run `nvidia-xconfig` on Optimus laptops. Use `xorg.conf.d` snippets instead. Always create Timeshift snapshot before GPU tweaks.

## Fix: PRIME Render Offload — Games nutzen iGPU statt NVIDIA

**Symptom:** `glxinfo` zeigt "Mesa Intel", `nvidia-smi` zeigt nur gnome-shell, Games laufen auf iGPU.
**Root Cause:** PRIME Offload ist `on-demand` aber die Environment-Variables fehlen → Anwendungen routen nicht auf die NVIDIA GPU.

**Diagnose:**
```bash
glxinfo | grep "OpenGL renderer"          # Intel = Problem
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia glxinfo | grep "OpenGL renderer"
# NVIDIA = Offload funktioniert, nur Env-Vars fehlen
```

set -euo pipefail
**Fix — Env-Vars systemweit setzen:**

1. **Für Login-Shells** (`/etc/profile.d/nvidia-prime-offload.sh`):
```bash
__NV_PRIME_RENDER_OFFLOAD=1
__NV_PRIME_RENDER_OFFLOAD_PROVIDER=NVIDIA-G0
__GLX_VENDOR_LIBRARY_NAME=nvidia
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json
export __NV_PRIME_RENDER_OFFLOAD __NV_PRIME_RENDER_OFFLOAD_PROVIDER __GLX_VENDOR_LIBRARY_NAME VK_ICD_FILENAMES
```

set -euo pipefail
2. **Für systemd user sessions** (`~/.config/environment.d/nvidia-prime-offload.conf`):
Wichtig für Steam/Games die via `.desktop` gestartet werden — die sehen profile.d nicht!
```
__NV_PRIME_RENDER_OFFLOAD=1
__NV_PRIME_RENDER_OFFLOAD_PROVIDER=NVIDIA-G0
__GLX_VENDOR_LIBRARY_NAME=nvidia
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json
```

set -euo pipefail
3. **Sofort testen** (ohne Logout):
```bash
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia glxinfo | grep "OpenGL renderer"
# Erwartet: "NVIDIA GeForce RTX ..."
```

set -euo pipefail
**Hinweis:** `VK_LAYER_NV_optimus=NVIDIA_only` ist optional und kann bei manchen Spielen Probleme machen — besser nur `VK_ICD_FILENAMES` setzen.

## Fix: Wayland → X11 für NV-CONTROL (nvidia-settings, GWE)

**Symptom:** `nvidia-settings` zeigt keine NV-CONTROL-Optionen, GWE crasht, GPU Power Draw niedrig.
**Ursache:** Wayland + Optimus → NV-CONTROL X11 extension nicht verfügbar.

**Fix:**
```bash
# GDM auf X11 umstellen
sudo sed -i 's/#WaylandEnable=false/WaylandEnable=false/' /etc/gdm3/custom.conf
# Danach: Logout → X11 Session
```

**Nach X11-Wechsel:**
- `nvidia-settings -q GpuPowerMizerMode` funktioniert
- GWE (GreenWithEnvy) funktioniert
- Coolbits OC ist verfügbar
- `glxinfo` zeigt NVIDIA als Standard-Renderer (nicht mehr Intel)

**Kombination (empfohlen für Gaming-Laptops):**
1. Wayland→X11 (für NV-CONTROL)
2. PRIME Offload Env-Vars (für Games die nur NVIDIA rendern sollen)
3. Coolbits 28 OutputClass (für OC)

## Pitfalls
1. intel_pstate EPP quirk (see above) — biggest gotcha. Governor name lies.
2. DBus policy file MUST be chmod 644, not 600. messagebus can't read 600.
3. Use the driver's shipped Type=simple service, never a hand-rolled Type=dbus.
4. GameMode governor verification fails on intel_pstate — expected, use hooks.
5. powerprofilesctl needs no sudo for profile changes (local active session).
6. **Boot-Loop Recovery:** If `nvidia-smi` fails after tweaks → check `/etc/X11/xorg.conf` first, remove it, reload modules. Auch `prime-select query` checken! Nach DKMS-Rebuild kann PRIME noch auf `intel` stehen → `sudo modprobe nvidia` + `sudo prime-select nvidia`, dann abmelden (nicht rebooten). See `references/boot-loop-recovery.md`.
7. **GPU in D3cold = nvidia-smi "No devices found"** — Häufigste Ursache bei Laptops mit Wayland. Runtime PM schaltet GPU ab. Fix: `echo on | sudo tee /sys/bus/pci/devices/0000:01:00.0/power/control`. Siehe `references/nvidia-smi-failure-chain-2026-06-27.md`.
8. **nvidia_drv.so fehlt nach Treiber-Wechsel** (open↔proprietär): Selten nur "Zombie" oder "DKMS kaputt" — in 20% der Fälle ist es Packaging-Bug. Fix: `apt install xserver-xorg-video-nvidia-595` (matching Version). Siehe `references/boot-loop-recovery.md` Layer 2.
9. **`nvidia-smi` meldet "No devices", aber `lsmod | grep nvidia` zeigt geladenes Modul**: Nicht paniken! Meist D3cold oder fehlendes `/dev/nvidia0`. Erst `dmesg | grep -i nvidia` checken, dann `echo on > power/control`, dann neu versuchen. Siehe `references/nvidia-smi-failure-chain-2026-06-27.md`.
18. **NVReg-Configs gelöscht → Desktop "blinkt" ohne Boot-Loop**: Wenn `lspci` GPU zeigt, Module geladen, Power State D0, aber `nvidia-smi` "No devices" UND Desktop blinkt (GDM restart loops) → prüfe `/etc/modprobe.d/nvidia-pm-fix.conf`, `nvreg_fix.conf`, `10-nvidia-coolbits.conf`. Fehlen diese → wiederherstellen + `update-initramfs -u` + Reboot. Siehe `references/nvreg-config-loss-2026-06-27.md`.
19. **sudo tee in execute_code funktioniert nicht**: Der Agent läuft oft in TTY-Session ohne PTY. `sudo` braucht Passwort und kann nicht durch `execute_code` / `terminal()` aufgerufen werden. Lösung: Befehl als Copy-Paste an User geben, User führt in seinem Wayland-Terminal aus. Siehe `references/nvreg-config-loss-2026-07-03.md` Pitfall "sudo in execute_code".
20. **nvidia-powerd failed auf Wayland + Optimus** — Service existiert, crashed aber, weil die GPU als DRM-Device nicht sichtbar ist (schläft in D3cold). `nvidia-powerd` sucht `/sys/class/drm/card0/device/vendor`, findet es nicht, bricht ab. Ist **erwartetes Verhalten** unter Wayland. Gaming funktioniert trotzdem via gamemode + PRIME-Offload. Empfehlung: Service ignorieren/deaktivieren. Siehe `references/nvidia-powerd-wayland-sleeping-gpu-2026-06-27.md`.
21. **RTX 50xx requires open kernel modules + nvidia-smi No devices** — dmesg zeigt dass der Treiber Open Kernel Modules erwartet, aber das proprietäre nvidia-Modul ist geladen. NVML init OK aber DeviceGetCount=0. GPU in D3cold, glxinfo zeigt nur Intel iGPU, xrandr --listproviders zeigt nur 1 Provider. Lösung: Proprietäre Module entladen → Open Kernel Module laden. Siehe references/rtx50xx-open-kernel-module-mismatch-2026-06-27.md.
22. **PRIME Offload Env-Vars fehlen → Games nutzen iGPU** — `prime-select query` zeigt `on-demand`, aber `__NV_PRIME_RENDER_OFFLOAD` und `__GLX_VENDOR_LIBRARY_NAME` sind nicht gesetzt. Fix: Env-Vars in `/etc/profile.d/` UND `~/.config/environment.d/` setzen (systemd user sessions sehen profile.d nicht!). **Flatpak Steam Sonderfall:** pressure-vessel/bwrap-Container stripst die meisten Host-Env-Vars. Weder profile.d noch environment.d erreichen das Spiel. Fix: Steam Launch Options mit `__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia %command%` — ABER ACHTUNG: Auch das funktioniert nicht bei allen Spielen (z.B. CS2 Native Linux), weil der pressure-vessel Entry-Point manche Env-Vars filtert. Siehe `references/prime-offload-env-vars-2026-06-28.md`.

23. **🔴 Kernel-Lockdown=integrity blockiert NVML-Hardware-Writes (Standard Secure-Boot-Setup)** — Die **Hauptursache** für "GPU-OC crasht"-Symptome bei Zorin/Ubuntu mit aktivem Secure Boot (Zorin-Default). Symptom: NVML-basierte OC-Tools wie `nvidia_oc` (Dreaming-Codes), `nvoc` (martinstark) schlagen silent fehl ODER erzeugen Hard-Lock. Diagnose: `cat /sys/kernel/security/lockdown` zeigt `[ Integrity ]`. Kernel-Lockdown=integrity blockt NVML-Hardware-Offset-Schreibzugriffe (Clock/Power/Mem-Register). **Lösung:** GRUB `lockdown=none` in `/etc/default/grub` → `GRUB_CMDLINE_LINUX_DEFAULT="quiet splash lockdown=none"` → `sudo update-grub && sudo reboot`. Verify: `cat /sys/kernel/security/lockdown` zeigt `[ none ]` oder leer. **Sicherheits-Trade-off EXPLIZIT kommunizieren** und User-Freigabe einholen: Secure Boot bleibt aktiv, Modul-Signaturen werden weiter erzwungen — nur Lockdown-Schutz (gegen Live-Patching von unsigned Code) wird aufgehoben. Bei produktiven Maschinen wo Lockdown=integrity bleiben muss: auf OC verzichten (kein Workaround). **Rollback:** gleiche Zeile auf `lockdown=integrity` zurücksetzen, `sudo update-grub && reboot`. Siehe `references/kernel-lockdown-nvml-blocks-tuning-2026-07-05.md`.

24. **🔴 Wayland + 595-open + RTX 50xx: NV-CONTROL-Tools IMMER vermeiden** — Andere Hauptursache der "Tuning-Crash"-Symptome. Symptom: `nvidia-settings` friert ein, GreenWithEnvy crasht, Coolbits-OC-Versuch endet in Hard-Lock. Ursache: NV-CONTROL-API ist eine reine X11-Extension (libXnvctrl) und unter Wayland nicht verfügbar. Aufrufe resultieren in Hang/Lock, **NICHT** in graceful error. **EINZIG sauberer Tuning-Pfad unter RTX 50xx + Wayland:** NVML-only Tools (`nvidia_oc`, `nvoc`). Diese funktionieren nativ unter Wayland UND X11. COOLBITS-Section (`Option     "Coolbits" "28"`) in `xorg.conf.d/` ebenfalls tot unter Wayland. **Wenn User explizit X11-Tools nutzen will** (Maus-Drag-Fan-Curve): GDM auf X11 umstellen (`WaylandEnable=false` in `/etc/gdm3/custom.conf`, dann re-Login wählt X11) — aber Wayland-Vorteile gehen verloren (Vari-Bind, Screen-Sharing, etc.). Siehe `references/wayland-nvcontrol-rtx50xx-2026-07-05.md`.

25. **🟧 GameMode [gpu]-Block MUSS in `/etc/gamemode.ini` (NICHT user-Config)** — GameMode liest drei Dateien in fester Reihenfolge, **gemerged**: (1) `/etc/gamemode.ini` (systemweit, akzeptiert [gpu]-Block), (2) `~/.config/gamemode.ini` (user, [gpu] als "unsafe" ignoriert), (3) `./gamemode.ini` (verzeichnislokal). Konsequenz: `gamemoded -s` zeigt "GPU optimizations: off" obwohl Config korrekt aussieht — weil der Block in der User-Config steht. Diagnose: `gamemoded -t && grep -A6 '\[gpu\]' /etc/gamemode.ini ~/.config/gamemode.ini`. Fix: Block nach `/etc/gamemode.ini` verschieben. Workaround wenn Treiber-Konstellation den Block nicht anwendet (Wayland+595-open RTX 50xx Setup-Problem): GPU-Block leer lassen, OC komplett via `nvidia_oc` Service. ACHTUNG bei mehreren GPUs: `gpu_device=0` muss manuell gegen `nvidia-smi -L` (NVIDIA-Index) UND `ls /dev/dri` (DRM-Nummer) abgeglichen werden — GameMode verwechselt sie intern.

## Fix: Wrong Kernel Flavour (lowlatency → generic) — RECURRING BUG

**Symptom:** `nvidia-smi` fails "couldn't communicate with the NVIDIA driver",  
`lsmod | grep nvidia` empty, `find /lib/modules/$(uname -r) -name 'nvidia*.ko*'` returns only `nvidiafb.ko.zst`/`nvidia-wmi-ec-backlight.ko.zst`.  
`uname -r` shows `...-lowlatency`, but NVIDIA modules are installed for `...-generic`.

**Root cause (Ubuntu Studio / Zorin):**  
`/etc/default/grub.d/ubuntustudio.cfg` sets `GRUB_FLAVOUR_ORDER="lowlatency $GRUB_FLAVOUR_ORDER"`  
→ GRUB boots lowlatency flavour. **The lowlatency kernel has no nvidia.ko — NVIDIA modules only ship for generic HWE.**

**DO NOT reinstall `nvidia-driver-*` — the packages are intact.** The fix is purely GRUB/reboot.

**Fix (full details in `references/kernel-flavour-mismatch-2026-07-14.md`):**

```bash
# 1) Override flavour order so generic wins
sudo tee /etc/default/grub.d/zz-yuno-flavour-generic.cfg >/dev/null <<'EOF'
GRUB_FLAVOUR_ORDER="generic lowlatency"
EOF

# 2) Find exact generic menuentry title, set default
awk -F\\\' '/menuentry / {print i++ " : " $2}' /boot/grub/grub.cfg
sudo grub-set-default "Advanced options for Ubuntu>Ubuntu, with Linux 6.17.0-35-generic"
sudo update-grub

# 3) Reboot → verify
# uname -r → *-generic
# nvidia-smi -L → RTX 5060
```

**Recurrence guard:** `sudo apt-mark hold nvidia-driver-595-open nvidia-utils-595 nvidia-prime`  
(prevents apt from removing driver in a way that forces lowlatency module rebuild; the GRUB override file persists across updates.)

## Wayland-Tuning-Strategie für RTX 50xx (Konsolidierung)

Kombiniere: vorher NVCONTROL-Tools JEDES Mal vermeiden. RTX 50xx + 595-open + Wayland ist die häufigste Crash-Kombination — auch wenn andere Tools in der Vergangenheit funktionierten, hier ist der Pfad:

1. **Lockdown** prüfen + ggf. lösen (Pitfall #23) — sonst kann `nvidia_oc` nie schreiben
2. **`nvidia_oc` (oder `nvoc`) installieren** — NVML-only, Wayland-sicher
3. **`/etc/gamemode.ini` [gpu] korrekt anlegen** (Pitfall #25) — oder leer lassen wenn OC parallel läuft
4. **OC iterativ in kleinen Schritten** — +25 MHz Core / +50 MHz Mem pro Iteration, 15-30 Min. Last + Xid-Check
5. **Erst nach Stabilitätsnachweis** (mind. 5 erfolgreiche Boots) systemd-Service für Persistenz aktivieren

**Werkzeug-Hierarchie für RTX 50xx + Wayland:**
- 🥇 `nvidia_oc` — NVML-basiert, Dreaming-Codes. Erste Wahl.
- 🥈 `nvoc` — martinstark. Dedizierter Blackwell-Support, manchmal mehr Optionen.
- 🚫 `nvidia-settings` / Coolbits / `GreenWithEnvy` — ZWINGEND X11-Session, crasht sonst.

## Related References

- `references/prime-offload-env-vars-2026-06-28.md` — PRIME Render Offload Env-Vars + Wayland→X11 Fix + Flatpak Steam pressure-vessel Pitfall
- `references/rtx5060-kernel-recovery-and-gaming-2026-07-02.md` — Kernel selection recovery, CS2 native Linux, Flatpak Steam external library, EC-cap confirmation on correct kernel
- `references/sysdoctor-cli-notes.md` — sysdoctor.py CLI usage (daily-briefing integration)
- `references/kernel-lockdown-nvml-blocks-tuning-2026-07-05.md` — **NEU 2026-07-05:** Kernel-Lockdown=integrity blockt NVML-Hardware-Writes, GRUB `lockdown=none` als Lösung, Security-Trade-off, Rollback (Pitfall #23)
- `references/wayland-nvcontrol-rtx50xx-2026-07-05.md` — **NEU 2026-07-05:** NV-CONTROL-Tools sind auf RTX 50xx + Wayland + 595-open IMMER falsch, NVML-Pfad als einzige saubere Alternative, Werkzeug-Hierarchie (Pitfall #24)
