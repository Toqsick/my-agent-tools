# RTX 5060 Open Kernel Device Recognition — Discovery 2026-06-27

**Session:** RTX 5060 Laptop (Device 2d19, Blackwell GB206), Driver 595.71.05, Open Kernel

## Symptom

- `nvidia-smi` → "No devices found" trotz geladenem nvidia Kernel-Modul
- `/proc/driver/nvidia/gpus/*/information` zeigt aber "RTX 5060 Laptop GPU"
- User meldet "erkennt RTX 5060 nicht"

## Root Cause (ENTSPANNEND)

**Der Treiber KENNT die RTX 5060!** 
- Die Device 2d19 ist GB206-Architektur (Blackwell)
- Der Kernel-Source enthält `uvm_blackwell.c` und `NV2080_CTRL_MC_ARCH_INFO_IMPLEMENTATION_GB206`
- Die PCI-Device-Table ist `PCI_ANY_ID` (generischer Match-All)
- Die Erkennung erfolgt über User-Space OpenRM, nicht über PCI-IDs

## Warum nvidia-smi failt obwohl erkannt

1. GPU ist im D3cold Power State (Runtime PM)
2. `power/control = auto` schaltet GPU ab
3. `nvidia-powerd` ist failed → kein Waker
4. Erst `echo on > power/control` weckt die GPU

## Diagnose

```bash
# Kernel kennt die Architektur?
grep -r "GB206\|gb206" /usr/src/nvidia-595.71.05/ 2>/dev/null | head -5

# GPU-ID可见 in /proc?
cat /proc/driver/nvidia/gpus/*/information | grep "Model"

# Power State check
cat /sys/bus/pci/devices/*/power_state

# Kernel Module implementation symbol check
grep "GB206\|uvm_blackwell\|0x2d19" /usr/src/nvidia-595.71.05/nvidia-uvm/ 2>/dev/null | head -3
```

## Lösung

```bash
# GPU wecken
echo on | sudo tee /sys/bus/pci/devices/*/power/control
nvidia-smi

# Falls immer noch "No devices", prüfe dmesg
dmesg | grep -iE "nvidia.*error|nvidia.*fail|nvidia.*init"
```

## Botschaft für andere Sessions

Wenn jemand sagt "erkennt RTX 5060 nicht", aber `/proc/driver/nvidia/gpus/*/information`
zeigt den korrekten Namen: **Es ist ein POWER-MANAGEMENT-Problem, kein
Device-ID-Problem.** Der Treiber kennt die GPU, sie ist nur schlafen. Fix: PM
auf "on" setzen. Das Device `2d19` ist neu (Blackwell) und braucht keinen
neueren Treiber — ist in 595.71.05 bereits enthalten.
