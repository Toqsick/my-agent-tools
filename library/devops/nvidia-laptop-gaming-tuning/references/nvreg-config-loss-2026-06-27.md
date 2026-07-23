# NVReg Config Loss — GPU "Invisible" After Config Deletion

**Session:** 2026-06-27, RTX 5060 Laptop, Driver 595.71.05, Wayland
**Symptom:** Desktop "blinkt" (GDM restart loops), nvidia-smi → "No devices found", but NO boot-loop, NO freeze

## Symptom-Muster

```
- GPU erkannt via lspci (Device 2d19, RTX 5060)
- nvidia kernel modules loaded (nvidia, nvidia_drm, nvidia_modeset, nvidia_uvm)
- /proc/driver/nvidia/version zeigt 595.71.05
- Power State = D0 (full power, NOT D3cold!)
- nvidia-persistenced: "device 0000:01:00.0 - failed to open"
- nvidia-smi: "No devices were found" (exit code 6)
- Desktop blinkt: GDM starts → crash → restart → crash...
- NO boot-loop (system boots fine)
- NO freeze (desktop partially works)
```

## Root Cause

Zwei modprobe.d-Configs wurden gelöscht:
1. `/etc/modprobe.d/nvidia-pm-fix.conf` — Power Management Fix
2. `/etc/modprobe.d/10-nvidia-coolbits.conf` — Coolbits für OC

Der `nvidia-pm-fix.conf` enthielt typischerweise:
```
options nvidia NVreg_PreserveVideoMemoryAllocations=1
```
oder ähnlich. Ohne diese Option kann der Treiber auf manchen Laptops
die GPU-Initialisierung nicht abschließen, auch wenn der Kernel-Modul
geladen ist.

## Diagnose-Folge

```bash
# 1. GPU sichtbar?
lspci -v -s 01:00.0 | grep -E "Kernel driver|Memory"

# 2. Module geladen?
lsmod | grep nvidia

# 3. Treiber-Version?
cat /proc/driver/nvidia/version

# 4. Power State (D0 = gut, D3cold = schlecht)
cat /sys/bus/pci/devices/0000:01:00.0/power_state

# 5. nvidia-persistenced erreichbar?
nvidia-smi --query-gpu=name --format=csv
# "No devices" + exit 6 = GPU existiert nicht für Nutzer-space

# 6. NVReg-Configs vorhanden?
cat /etc/modprobe.d/nvidia-pm-fix.conf 2>/dev/null || echo "MISSING"
cat /etc/modprobe.d/nvreg_fix.conf 2>/dev/null || echo "MISSING"
cat /etc/modprobe.d/10-nvidia-coolbits.conf 2>/dev/null || echo "MISSING"
```

## Fix-Optionen

### Option A: NVReg-Configs wiederherstellen (sicher)
```bash
# Prüfen was fehlt und wiederherstellen
# nvreg_fix.conf (enthält NVreg_OpenRmEnableUnsupportedGpus=1)
echo 'options nvidia NVreg_OpenRmEnableUnsupportedGpus=1' | sudo tee /etc/modprobe.d/nvreg_fix.conf

# nvidia-pm-fix.conf (falls PM-Optionen fehlen)
echo 'options nvidia NVreg_PreserveVideoMemoryAllocations=1' | sudo tee /etc/modprobe.d/nvidia-pm-fix.conf

# Coolbits (nur für X11, nicht Wayland)
echo 'options nvidia NVreg_RegistryDwords=PerfLevelSrc=0x2222' | sudo tee /etc/modprobe.d/10-nvidia-coolbits.conf

sudo update-initramfs -u
# Reboot erforderlich
```

### Option B: Treiber neu laden (sanft, kein Reboot)
```bash
sudo rmmod nvidia_uvm nvidia_drm nvidia_modeset nvidia
sudo modprobe nvidia
sudo modprobe nvidia_drm
sudo modprobe nvidia_modeset
sudo modprobe nvidia_uvm
nvidia-smi  # testen
```
Hilft nur wenn Module-Cache problematisch war, nicht bei fehlenden NVReg-Configs.

### Option C: NVIDIA Treiber neu installieren (radikal)
```bash
sudo apt install --reinstall nvidia-driver-595 nvidia-kernel-common-595
sudo update-initramfs -u
sudo reboot
```

## Pitfall: "Blinkendes" Desktop ohne Boot-Loop

Wenn das Desktop "blinkt" (GDM restartet periodisch) aber kein Boot-Loop:
- NICHT paniken — es ist recoverable
- Ursache: GDM startet X11/Wayland → GPU wird initialisiert → schlägt fehl → GDM crasht → GDM restartet
- Fix: NVReg-Configs wiederherstellen + Reboot
- Workaround bis Fix: Auf TTY wechseln (Ctrl+Alt+F2), GDM stoppen: `sudo systemctl stop gdm`

## Pitfall: nvidia-smi != GPU existiert

`nvidia-smi` sagt "No devices" bedeutet NICHT "GPU ist nicht da".
Es bedeutet: "Der Kernel-Treiber kann nicht mit der GPU kommunizieren."
Das ist ein Unterschied! Die GPU ist physisch da (lspci zeigt sie),
aber der Nutzer-space Teil des Treibers kann sie nicht ansprechen.
Das passiert wenn:
1. NVReg-Configs fehlen (Initialisierung unvollständig)
2. Power State ist D3cold (Runtime PM)
3. nvidia-persistenced kann Device nicht öffnen
4. EC Power Capping blockiert

## Pitfall: sudo in execute_code / Agent-Terminal

Wenn der Agent in einer TTY-Session läuft (kein DISPLAY, kein Wayland):
- `sudo tee /etc/modprobe.d/...` funktioniert NICHT — sudo braucht Passwort
- PTY-Mode hilft auch nicht — sudo fragt trotzdem ein Passwort
- **Lösung:** Den Befehl als Copy-Paste-Block an den User geben
- Der User führt ihn in seinem Wayland-Terminal aus (xterm, gnome-terminal, etc.)
- Alternativ: User gibt Passwort an (vertrauensbasiert, "-yolo"-Signal)

## User Profile: Basti

- Nutzt **xterm** als Terminal
- Nutzt **Wayland** (Ubuntu 24.04, GDM)
- Hat **sudo-Rechte** (Gruppe sudo) aber vergibt Passwort nicht gern
- "-yolo" = Signal, dass er dem Agent vertraut, aber Passwort muss trotzdem eingegeben werden
- Erwartet, dass der Agent **nicht blind sudo ausführt** ohne Wissen
