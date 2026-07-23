# nvidia-powerd fails on Wayland — GPU sleeping (Optimus)

**Session:** 2026-06-27, Zorin OS 18.1, RTX 5060 Laptop, NVIDIA 595.71.05
**Symptom:** `nvidia-powerd.service` → `failed`, GPU not visible as DRM device

## Diagnosis Path

```bash
# 1. Service exists but fails
systemctl --user status nvidia-powerd
# → "failed" (not "not found" — unit exists, binary crashes)

# 2. GPU is NOT a DRM card under /sys/class/drm/
ls /sys/class/drm/card*/device/vendor
# → Only Intel (0x8086) shows. NVIDIA GPU has no DRM device entry.

# 3. nvidia-smi also fails (GPU in D3cold / not activated)
nvidia-smi
# → "No devices were found"

# 4. But the kernel module IS loaded
lsmod | grep nvidia
# → nvidia_drm, nvidia_modeset, nvidia_uvm, nvidia

# 5. GPU exists on PCI bus
lspci | grep -i vga
# → "01:00.0 VGA compatible controller: NVIDIA Corporation Device [10de:2d19]"

# 6. Prime mode
prime-select query
# → "on-demand" (correct for Optimus)

# 7. GPU power state
cat /sys/bus/pci/devices/0000:01:00.0/power_state
# → "D3" (deep sleep)

# 8. nvidia-powerd is an ELF binary (not a script)
file /usr/bin/nvidia-powerd
# → ELF 64-bit executable
```

## Root Cause

On **Wayland + Optimus** systems:
- The NVIDIA GPU is **not exposed as a DRM device** (`/sys/class/drm/card0/` doesn't exist for it)
- `nvidia-powerd` looks for `/sys/class/drm/card0/device/vendor` to identify the GPU
- Since the GPU is in D3cold (deep sleep) and not activated, no DRM node exists
- The service crashes with exit code because it cannot find the hardware

**This is EXPECTED behavior** on modern Optimus laptops under Wayland. The GPU only wakes when an application requests it via PRIME Render Offload.

## What Works Without Fixing nvidia-powerd

- `gamemoded` runs fine (it hooks into the process, not the DRM device)
- PRIME Render Offload works: `__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia <app>`
- Steam Proton games work via `prime-run` or `__NV_PRIME_RENDER_OFFLOAD=1`
- `nvidia-powerd` is only a **Dynamic Boost** helper — it's optional, not required

## Options (in order of preference)

### Option A: Ignore nvidia-powerd (recommended)
- Disable the service: `systemctl --user disable nvidia-powerd`
- Gaming works fine without it (gamemoded + PRIME handle performance)
- No risk of breaking anything

### Option B: Switch to X11 session for gaming
- Log out → GDM gear icon → "Ubuntu on Xorg"
- nvidia-powerd will find the GPU under X11 (nvidia_drv.so loads)
- Tradeoff: lose Wayland features (fractional scaling, security)

### Option C: Patch nvidia-powerd service
- Modify the service to target the correct GPU device path
- Complex, fragile across driver updates
- Not recommended unless you need Dynamic Boost specifically

### Option D: Custom GPU wake script
- Script that activates GPU before gaming, then lets nvidia-powerd manage it
- Over-engineered for most use cases

## Key Insight

`nvidia-powerd` failure ≠ GPU not working. It's a **service compatibility issue** between the daemon's DRM-based detection and Wayland's GPU sleeping behavior. The GPU itself is functional when activated by applications.

## Related
- `references/nvidia-smi-failure-chain-2026-06-27.md` — D3cold diagnosis
- `references/ec-power-capping-2026-06-18.md` — EC power limit issues
- SKILL.md Pitfall #7 (D3cold)
- SKILL.md Pitfall #10 (Coolbits only on X11)
