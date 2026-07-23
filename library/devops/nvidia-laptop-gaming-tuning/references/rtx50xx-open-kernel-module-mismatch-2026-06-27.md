# RTX 5060 "Requires Open Kernel Modules" — Diagnosis & Fix

**Session:** 2026-06-27, RTX 5060 Laptop, Zorin OS 18.1, Driver 595.71.05
**Symptom:** `nvidia-smi` → "No devices were found", `nvidia-powerd` failed, GPU in D3cold

## Problem-Kette

1. **dmesg-Warning:** `NVRM: installed in this system requires use of the NVIDIA open kernel modules`
2. **Realität:** Das **proprietäre** `nvidia`-Modul ist geladen (`lsmod | grep nvidia` zeigt `nvidia 98902016`)
3. **Open Kernel Module** existiert (`linux-modules-nvidia-595-open`) aber wird **nicht geladen**
4. NVML init OK (`libnvidia-ml.so.1` geladen), aber `nvmlDeviceGetCount` → 0 Devices
5. `nvidia-smi` → "No devices were found"
6. `nvidia-powerd` (systemd) → failed (service exists but GPU nicht als DRM-Card erkannt)
7. GPU Power State: **D3cold** (Deep Sleep)
8. `glxinfo` zeigt **Intel Mesa** (iGPU), nicht NVIDIA
9. `xrandr --listproviders` → nur 1 Provider (Intel/modesetting), **NVIDIA nicht als Offload-Provider**
10. `gamemoded` läuft aber meldet: `ERROR: Couldn't open vendor file at /sys/class/drm/card0/device/vendor`

## Warum passiert das?

- RTX 50xx (GB203/Blackwell-Architektur) hat **propriäre und open kernel Module** im Paket
- Ubuntu/Zorin lädt automatisch das **proprietäre** Modul (älteres Verhalten)
- Der Treiber (595) **erwartet** aber die Open Kernel Modules für neuere GPUs
- Das proprietäre Modul kann die GPU nicht initialisieren → bleibt in D3cold
- NVML findet kein Device weil der Kernel-Treiber die GPU nicht aufweckt

## Diagnose-Befehle

```bash
# 1. Welches Modul ist geladen?
lsmod | grep "^nvidia "

# 2. Open Kernel Module verfügbar?
find /lib/modules/$(uname -r) -name "nvidia-open*" -o -name "nvidia-595-open*"

# 3. dmesg Warning checken
sudo dmesg | grep -i "open kernel modules"

# 4. NVML Device Count
python3 -c "
import ctypes
lib = ctypes.CDLL('libnvidia-ml.so.1')
lib.nvmlInit()
count = ctypes.c_uint()
lib.nvmlDeviceGetCount(ctypes.byref(count))
print(f'NVML Devices: {count.value}')
"

# 5. PRIME Offload Provider check
xrandr --listproviders

# 6. GPU Power State
cat /sys/bus/pci/devices/0000:01:00.0/power_state

# 7. DRM Devices
ls /sys/class/drm/card*/device/vendor
```

## Lösungen (Reihenfolge beachten!)

### Option A: Open Kernel Module laden (empfohlen)

```bash
# 1. Proprietäre Module entladen
sudo modprobe -r nvidia_uvm nvidia_drm nvidia_modeset nvidia

# 2. Open Kernel Module laden
sudo modprobe nvidia

# 3. Neues Modul prüfen
lsmod | grep "^nvidia "  # Sollte "nvidia" ohne "_uvm" etc. zuerst zeigen
```

**Achtung:** Nach `modprobe -r` schwarzt der Bildschirm kurz (GPU reset). Nicht paniken!

### Option B: PRIME Offload erzwingen (Testing, kein Fix)

```bash
# Testet ob GPU via PRIME aufwacht
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia glxinfo | grep "OpenGL renderer"
# Sollte zeigen: "NVIDIA GeForce RTX 5060"
```

### Option C: nvidia-powerd ignorieren (wenn A nicht klappt)

Der Service ist nur ein Power-Management-Helper. Wenn die GPU via PRIME/GameMode
funktioniert, braucht man ihn nicht:

```bash
sudo systemctl disable nvidia-powerd
```

## Pitfalls

1. **`echo on | sudo tee power/control` allein reicht nicht** — die GPU bleibt in D3cold wenn der Treiber sie nicht initialisiert
2. **NVML init OK ≠ GPU sichtbar** — NVML initialisiert sich selbst wenn die Library existiert, aber `DeviceGetCount=0` zeigt dass der Kernel-Treiber die GPU nicht findet
3. **Wayland vs X11 ist irrelevant für nvidia-smi** — das Problem ist der Kernel-Modul-Laufweg, nicht die Display-Session
4. **gamemoded Errors sind Kosmetik** — `vendor file at /sys/class/drm/card0` existiert nicht weil die NVIDIA-GPU kein DRM-Card ist (nur iGPU). Ignorieren.
5. **PRIME Offload Config vorhanden aber inaktiv** — `11-nvidia-offload.conf` mit `AllowNVIDIAGPUScreens` existiert, aber ohne geladenes nvidia-drm Modul wird kein Provider registriert
6. **Modul ist "in use"** — `modprobe -r` schlägt fehl mit "Module nvidia is in use" weil ein Prozess den Treiber nutzt. **NICHT immer GDM!** Häufig ist es `gnome-remote-de` (GNOME Remote Desktop) das `/dev/nvidiactl` hält. Diagnose: `sudo fuser -v /dev/nvidia*`. Safe Swap: Nur den halten Prozess killen (`kill <PID>` von fuser), NICHT GDM stoppen. Danach `sudo modprobe -r nvidia` → `sudo modprobe /lib/modules/$(uname -r)/kernel/nvidia-595-open/nvidia.ko` → `nvidia-smi` testen. **Kein Reboot nötig, kein Boot-Freeze-Risiko!** Siehe `references/safe-module-swap-2026-06-27.md`.
7. **Modul-Pfad prüfen** — `modinfo -F filename nvidia` zeigt `/kernel/nvidia-595/nvidia.ko` (proprietär) vs `/kernel/nvidia-595-open/nvidia.ko` (open). Der Pfad unterscheidet sich!
8. **Manuelles Laden via Pfad** — `sudo modprobe /lib/modules/$(uname -r)/kernel/nvidia-595-open/nvidia.ko` funktioniert auch wenn `modprobe nvidia` das proprietäre lädt
9. **X11 zeigt Intel iGPU** — `glxinfo` unter X11 zeigt Mesa/Intel wenn PRIME Offload nicht aktiviert ist. Das ist normal für on-demand Modus, aber nvidia-smi sollte trotzdem funktionieren (wenn das richtige Modul geladen ist)
10. **`nvidia-powerd.service` existiert als System-Unit, nicht als User-Unit** — `systemctl --user status nvidia-powerd` zeigt "not found" weil es unter `/etc/systemd/system/` liegt, nicht unter `~/.config/systemd/user/`. Mit `systemctl status nvidia-powerd` prüfen!

## Siehe auch

- `references/rtx5060-open-kernel-recognition-2026-06-27.md` — Device-ID/Matching
- `references/nvidia-smi-failure-chain-2026-06-27.md` — Allgemeine Diagnose
- `references/nvidia-powerd-wayland-sleeping-gpu-2026-06-27.md` — powerd + Wayland
