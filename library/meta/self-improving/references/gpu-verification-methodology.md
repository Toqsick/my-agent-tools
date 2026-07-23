# GPU Verification Methodology — Avoid False Negatives from Default Tools

**Erstellt:** 2026-07-16
**Kategorie:** hardware-diagnostic
**Context:** Ornith-9B iGPU-Split Versuch auf Bastis MEDION ERAZER (RTX 5060 8GB + Intel RPL-P UHD iGPU)

## Die Lesson in einem Satz

> Default-Tools auf Dual-GPU-Laptops zeigen **nur den primären Display-GPU** — nicht was wirklich existiert. "Nicht gefunden" ≠ "nicht vorhanden".

## Der konkrete Vorfall (was schiefging)

**Symptom:** `vulkaninfo` zeigte nur `NVIDIA GeForce RTX 5060 Laptop GPU`. `xrandr --listproviders` zeigte `Providers: number: 0`. Daraus zog ich den Schluss "iGPU-Split nicht realisierbar — PRIME blockt Intel Vulkan-Compute-Route."

**Warum das falsch war:**
- Wayland hat keine PRIME-Provider-API wie X11. `xrandr --listproviders: 0` ist **normal** unter Wayland und sagt nichts über Compute-Fähigkeit aus.
- Der Vulkan-Loader priorisiert standardmäßig den primären Display-GPU-ICD. Intel-Vulkan ist installiert, aber wird beim default `vulkaninfo`-Aufruf nicht gelistet.
- Die iGPU ist als Compute-Device voll funktional — nur der Display-Pfad wird umgangen, weil NVIDIA per PRIME den Bildschirm treibt.

**Korrektur:** Mit `VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/intel_icd.json vulkaninfo` tauchte Intel als vollwertiges Vulkan-Compute-Device auf:
```
deviceType = INTEGRATED_GPU
deviceName = Intel(R) Graphics (RPL-P)
driverName = Intel open-source Mesa driver
apiVersion = 1.4.318
maxComputeWorkGroupInvocations = 1024
subgroupSize = 32
```

## Die 4-Routen-Regel (Copy-Paste Command Sequence)

### Route 1: User-Space-API (Default)

```bash
# Vulkan: was der Loader standardmäßig zeigt
vulkaninfo --summary 2>/dev/null | grep -E "deviceName|deviceType|driverName|apiVersion"

# CUDA: NVIDIA-Toolkit
nvidia-smi -q 2>/dev/null | grep "Product Name"

# OpenCL (falls installiert)
clinfo 2>/dev/null | grep "Device Name"
```

### Route 2: Explicit ICD/Driver Override

```bash
# ICD-Pfade auf dem System finden
ls /usr/share/vulkan/icd.d/

# Intel Mesa-Vulkan forcieren
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/intel_icd.json vulkaninfo --summary 2>/dev/null | grep -E "deviceName|deviceType|driverName"

# Intel Haswell-Vulkan forcieren (ältere Architekturen, legacy)
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/intel_hasvk_icd.json vulkaninfo --summary 2>/dev/null | grep deviceName

# NVIDIA-Vulkan forcieren
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json vulkaninfo --summary 2>/dev/null | grep deviceName

# Alle ICDs gleichzeitig vergleichen
for icd in /usr/share/vulkan/icd.d/*.json; do
  echo "=== $(basename $icd) ==="
  VK_ICD_FILENAMES="$icd" vulkaninfo --summary 2>/dev/null | grep deviceName
done
```

### Route 3: Sysfs / Kernel Device Tree (unabhängig von Userspace-Treibern)

```bash
# PCI-Treiberbindung prüfen (wer treibt welche Karte?)
ls -la /sys/class/drm/card*/device/driver

# Hersteller- und Device-IDs
for card in /sys/class/drm/card*; do
  [ -f "$card/device/vendor" ] || continue
  ven=$(cat "$card/device/vendor" 2>/dev/null)
  dev=$(cat "$card/device/device" 2>/dev/null)
  echo "$(basename $card): vendor=$ven device=$dev"
done

# Render-Knoten-Treiber
ls -la /sys/class/drm/renderD*/device/driver

# Vollständige PCI-Topologie
lspci -nn | grep -iE "vga|3d controller|display"

# AMD-specific (falls vorhanden)
ls /sys/class/drm/card*/device/vendor 2>/dev/null | xargs cat
# Intel: 0x8086, NVIDIA: 0x10de, AMD: 0x1002
```

### Route 4: Prozess-/Kernel-Topologie

```bash
# DRM-Geräte
ls /dev/dri/

# PCI-Speicher
cat /proc/bus/pci/devices 2>/dev/null | grep -E "10de|8086|1002"

# NUMA-Topologie (welche GPU auf welcher CPU?)
cat /sys/class/drm/card*/device/numa_node

# GPU-Memory-Info
cat /sys/class/drm/card*/device/mem_info_used 2>/dev/null
cat /sys/class/drm/card*/device/mem_info_free 2>/dev/null
```

## Wayland vs X11 — Worauf man achten muss

### Wayland (Bastis Session: `zorin-wayland`)

| Tool | Verhalten | Bedeutung |
|---|---|---|
| `xrandr --listproviders` | `Providers: number: 0` | **Normal.** Wayland hat keine X11-RandR-Provider. Kein PRIME-Indikator. |
| `vulkaninfo` (default) | Zeigt nur primären GPU-ICD | Loader-priorisiert. Nicht vollständig. |
| `glxinfo` | Zeigt nur NVIDIA | GLX ist X11-only unter Wayland keine sinnvolle GPU-Diagnose |
| `DISPLAY=:0.0` | NVIDIA ist primary | Steht nicht im Widerspruch zu iGPU-Compute |

### X11 (`zorin-xorg`)

| Tool | Verhalten | Bedeutung |
|---|---|---|
| `xrandr --listproviders` | Zeigt NVIDIA + Intel | Zeigt PRIME-Konfiguration |
| `xrandr --setprovideroutputsource` | Kann Intel als Output setzen | Nur unter X11 möglich |

## Bastis MEDION ERAZER — Verified Topologie (2026-07-16)

```
/sys/class/drm/
├── card1/   → vendor=0x8086 (Intel), device=0xa7a8 (RPL-P UHD)
└── card2/   → vendor=0x10de (NVIDIA), device=0x2d19 (RTX 5060)

/sys/class/drm/renderD128/device/driver → /sys/bus/pci/drivers/i915    ← Intel
/sys/class/drm/renderD129/device/driver → /sys/bus/pci/drivers/nvidia  ← NVIDIA

ICD-Dateien:
/usr/share/vulkan/icd.d/
├── intel_icd.json       → Intel Mesa Vulkan (active)
├── intel_hasvk_icd.json → Intel legacy Vulkan (present)
└── nvidia_icd.json      → NVIDIA Vulkan (active)

Compute-Capability Intel:
- maxComputeWorkGroupInvocations: 1024
- subgroupSize: 32
- Vulkan API 1.4.318 (Mesa 25.x)
- Kein OpenCL / Level-Zero / SYCL installiert
```

## Was tun wenn llama.cpp mit `--tensor-split` den Intel-Teil ignoriert?

```bash
# 1. Prüfen ob Vulkan-Backend im Build aktiv ist
~/tmp/llama.cpp/build/bin/llama-cli --help 2>&1 | grep -i vulkan
# → MUSS "--vulkan-device" zeigen, sonst ohne Vulkan-Backend gebaut

# 2. Explizit Intel als Vulkan-Device setzen
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/intel_icd.json \
  ~/tmp/llama.cpp/build/bin/llama-cli \
  -m ~/models/ornith-gguf/ornith-1.0-9b-Q8_0.gguf \
  --vulkan-device 1 \
  -ngl 99

# 3. Wenn --tensor-split nicht funktioniert: NVIDIA über CUDA,
# Intel über separaten llama-Server (Network-Distributed)
```

## Verwandte Lessons

- Self-Improving: "Diagnostic Methodology — Avoiding False Negatives" (SKILL.md Section)
- Memory: `mnemosyne_recall(query="iGPU Split realisierbar false negative vulkaninfo")`
