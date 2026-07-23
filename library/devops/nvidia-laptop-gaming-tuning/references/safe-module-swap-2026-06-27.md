# Safe Kernel Module Swap — Open Kernel Module ohne Reboot

**Session:** 2026-06-27, RTX 5060 Laptop, Zorin OS 18.1, Driver 595.71.05
**Ziel:** Proprietäres nvidia-Modul → Open Kernel nvidia-Modul wechseln OHNE Reboot, OHNE Boot-Freeze

## Problem

`modprobe -r nvidia` schlägt fehl: `FATAL: Module nvidia is in use.`
Man denkt "GDM hält die GPU" — **falsch!** In diesem Fall war es `gnome-remote-de` (PID 19130).

## Diagnose: Wer hält die GPU?

```bash
# Wer hat /dev/nvidiactl offen?
sudo fuser -v /dev/nvidia*

# Oder:
sudo lsof /dev/nvidia*
```

**Typische Ergebnisse:**
- `gnome-remote-de` → harmlos, kann gekillt werden
- `gdm`, `Xwayland`, `gnome-shell` → **NICHT killen** (Display-Manager)
- `nvidia-smi` → harmlos, kann gekillt werden

## Safe Swap Procedure

```bash
# 1. GPU Consumer identifizieren
sudo fuser -v /dev/nvidia*

# 2. Nur harmlose Prozesse killen (gnome-remote-de, nvidia-smi etc.)
#    NIEMALS gdm, gnome-shell, Xwayland killen!
kill <PID_von_gnome-remote-de>

# 3. Module entladen (sollte jetzt gehen)
sudo modprobe -r nvidia

# 4. Open Kernel Module laden (expliziter Pfad!)
sudo modprobe /lib/modules/$(uname -r)/kernel/nvidia-595-open/nvidia.ko

# 5. Erfolg prüfen
nvidia-smi -L
```

## Ergebnis (Session 2026-06-27)

```
GPU 0: NVIDIA GeForce RTX 5060 Laptop GPU (UUID: GPU-35e66359-bbef-20f1-ff19-507d27cba1a9)
```

**Ohne Reboot, ohne Boot-Freeze, ohne GDM-Neustart.**

## Nach dem Swap: Was ist anders?

| Vorher (proprietär) | Nachher (open kernel) |
|---------------------|----------------------|
| nvidia-smi → "No devices" | nvidia-smi → GPU erkannt ✅ |
| NVML DeviceGetCount=0 | NVML DeviceGetCount=1 ✅ |
| Power Limit: 20W (EC-gedrosselt) | Power Limit: 20W (gleiches EC-Bug) |
| Performance State: P4 | Performance State: P4 |
| dmesg: "requires open kernel modules" | dmesg: kein Warning ✅ |
| glxinfo: Intel Mesa | glxinfo: Intel Mesa (PRIME Offload nicht aktiv) |

## Pitfalls

1. **Niemals GDM/X11 killen** → schwarzer Bildschirm, Session-Ende
2. **`modprobe nvidia` (ohne Pfad) lädt das PROPRIETÄRE Modul** → muss explizit `/kernel/nvidia-595-open/nvidia.ko` angeben
3. **Nach dem Swap: nvidia-powerd bleibt failed** → erwartet, Service ist für Wayland+Optimus nicht nötig
4. **Power Limit Bug bleibt** → EC-Power-Limit ist unabhängig vom Kernel-Modul, braucht OC via nvidia-smi oder Coolbits
5. **Swap ist nicht persistent** → nach Reboot wird wieder das proprietäre geladen (braucht modules.dep oder modprobe.d Fix)

## Siehe auch

- `references/rtx50xx-open-kernel-module-mismatch-2026-06-27.md` — Vollständige Diagnose-Kette
- `references/ec-power-capping-2026-06-18.md` — Power Limit Bug
