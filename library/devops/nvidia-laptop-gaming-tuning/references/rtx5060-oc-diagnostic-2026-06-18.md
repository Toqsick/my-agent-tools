# RTX 5060 Laptop OC Diagnostic — 2026-06-18

**Hardware:** Acer laptop, RTX 5060 Laptop GPU (Device 2d19, Blackwell), 8GB VRAM
**Driver:** 595.71.05 (nvidia-driver-595-open, Ubuntu Noble)
**Session type:** Wayland (GNOME + Mutter + mutter-x11-frames)

## Diagnostic Results

### Power Limit
- Default Power Limit: 80W, Max: 115W, Min: 5W
- EC had capped to 25W at some point (SW Power Cap: Active)
- `nvidia-smi -pl 115` → "Changing power management limit is not supported in current scope"
- EC power capping is confirmed — driver cannot override without Coolbits

### GPU Clocks Under Load
- Idle: 180 MHz GPU, 405 MHz VRAM, 3W, P8
- Under glxgears (PRIME render offload): 1012 MHz GPU, 810 MHz VRAM, 8.3W, P5
- Max supported: 3090 MHz GPU, 12001 MHz VRAM
- nvidia-smi -ac deprecated in driver 595

### OC Tool Status
- nvidia-settings 510.47.03 vs driver 595 = version mismatch
- libxnvctrl0 510 vs driver 595 = NV-CONTROL X extension broken
- BUT primary blocker is Wayland (no NV-CONTROL X extension at all under Wayland)
- GWE crashes with "NV-CONTROL missing!" under Wayland
- Coolbits 28 OutputClass not yet applied (sudo blocked by password prompt)

### Key Commands That Work
```bash
# Force NVIDIA GPU for GL apps (Optimus):
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia glxgears

# Check GPU under load:
nvidia-smi --query-gpu=clocks.gr,clocks.mem,power.draw,utilization.gpu --format=csv

# Check EC power cap status:
nvidia-smi -q -d POWER | grep -E "Current|SW Power|Cap"

# Check performance state:
nvidia-smi -q -d PERFORMANCE | grep "Performance State"
```

### Resolution Path (not yet completed)
1. User needs to manually: `sudo cp /tmp/nvidia-coolbits.conf /etc/X11/xorg.conf.d/10-nvidia-coolbits.conf`
2. Switch to X11 session (GDM → gear → "Ubuntu on X11")
3. Reboot
4. Test nvidia-settings PowerMizer page for OC sliders
5. If EC still blocks power limit, accept 80W default and optimize GPU/VRAM clocks only

### Files Involved
- `/etc/X11/xorg.conf.d/10-nvidia-coolbits.conf` — Coolbits 28 OutputClass (needs sudo to create)
- `/etc/modprobe.d/nvreg_fix.conf` — NVreg_OpenRmEnableUnsupportedGpus=1 (DO NOT remove)
- `/etc/systemd/system/nvidia-powerd.service` — System-Unit, active (running)
