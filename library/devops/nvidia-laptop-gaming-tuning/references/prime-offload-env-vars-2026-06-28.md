# PRIME Render Offload + Wayland→X11 Fix (2026-06-28)

**System:** Acer Laptop, RTX 5060 Laptop GPU, Optimus (Intel iGPU + NVIDIA dGPU)
**Treiber:** 595.71.05
**Ausgangslage:** Games liefen auf Intel iGPU, nvidia-smi zeigte nur gnome-shell

## Diagnose

```
$ glxinfo | grep "OpenGL renderer"
OpenGL renderer string: Mesa Intel(R) Graphics (RPL-P)   ← PROBLEM

$ __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia glxinfo | grep "OpenGL renderer"  
OpenGL renderer string: NVIDIA GeForce RTX 5060 Laptop GPU/PCIe/SSE2   ← OK

$ prime-select query
on-demand   ← korrekt, aber Env-Vars fehlen

$ nvidia-smi pmon -s um -c 1
# nur gnome-shell, keine Games
```

**Root Cause:** PRIME Offload erfordert Environment-Variables. `prime-select on-demand` allein reicht nicht — Anwendungen starten standardmäßig auf iGPU.

## Fix 1: PRIME Offload Env-Vars

### Für Login-Shells (`/etc/profile.d/nvidia-prime-offload.sh`)
```bash
__NV_PRIME_RENDER_OFFLOAD=1
__NV_PRIME_RENDER_OFFLOAD_PROVIDER=NVIDIA-G0
__GLX_VENDOR_LIBRARY_NAME=nvidia
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json
export __NV_PRIME_RENDER_OFFLOAD __NV_PRIME_RENDER_OFFLOAD_PROVIDER __GLX_VENDOR_LIBRARY_NAME VK_ICD_FILENAMES
```

### Für systemd user sessions (`~/.config/environment.d/nvidia-prime-offload.conf`)
```
__NV_PRIME_RENDER_OFFLOAD=1
__NV_PRIME_RENDER_OFFLOAD_PROVIDER=NVIDIA-G0
__GLX_VENDOR_LIBRARY_NAME=nvidia
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json
```

**Wichtig:** Steam/Games via `.desktop` starten im systemd user session context. `/etc/profile.d/` wird NICHT geladen ohne Login-Shell. Deshalb beide Orte setzen!

## Fix 2: Wayland → X11 (für NV-CONTROL)

`/etc/gdm3/custom.conf` → `WaylandEnable=false` unter `[daemon]`

**Auswirkungen:**
- nvidia-settings zeigt vollständige NV-CONTROL-Optionen
- GWE (GreenWithEnvy) funktioniert
- Coolbits OC verfügbar
- glxinfo zeigt NVIDIA als Standard-Renderer
- Power Draw nicht mehr am EC-Limit gebremst (X11 + PerfMode erhöht Power Budget)

## Verifikation nach Reboot

```bash
# Session-Typ
echo $XDG_SESSION_TYPE   # sollte "x11" zeigen

# OpenGL Renderer
glxinfo | grep "OpenGL renderer"   # NVIDIA GeForce RTX 5060

# PRIME Offload testen
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia glxinfo | grep "OpenGL renderer"   # NVIDIA

# Power Draw (sollte unter Load >25W sein)
nvidia-smi --query-gpu=power.draw --format=csv,noheader

# nvidia-settings
nvidia-settings -q GpuPowerMizerMode   # sollte Attribute zeigen
```

## Pitfalls
- `VK_LAYER_NV_optimus=NVIDIA_only` kann bei manchen Vulkan-Spielen crashen → besser weglassen, `VK_ICD_FILENAMES` reicht
- `prime-select nvidia` (Full-NVIDIA-Modus) ist Alternative, aber kostet Battery und erzeugt Wärme — `on-demand` + Env-Vars ist besser für Laptops
- Environment-Vars in `~/.bashrc` setzen wirkt nur für neue Terminals, nicht für bereits laufende GUI-Apps → immer systemweit via profile.d + environment.d
