---
name: nvidia-suspend-resume
title: NVIDIA Suspend/Resume Debugging (Linux Optimus Laptops)
description: |
  Use when you need to use the nvidia-suspend-resume workflow and its documented procedures.
  NOT for unrelated tasks outside the nvidia-suspend-resume workflow.
  Provides focused guidance for nvidia-suspend-resume.
triggers:
- dmesg shows 'RmInitAdapter failed' or 'rm_init_adapter failed' after resume
- NVIDIA GPU crashes after suspend/resume on Linux laptop
- nvidia-smi fails after wakeup but works after reboot
- User reports 'GPU verschwindet nach Sleep' or 'Resume crasht GPU'
- External monitor wakeup triggers GPU error (PEG1/PXSX enabled)
- S0ix power management conflicts with NVIDIA open kernel modules
- DynamicPowerManagement=2 causes resume failure on Optimus laptops
- User mentions 'wakeup fix', 'suspend crash', 'GPU resume', 'treiber wakeup'
version: 1.0.0
author: Hermes Agent
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - nvidia
    - suspend
    - resume
    - wakeup
    - optimus
    - s0ix
    - rminitadapter
    - power-management
    related_skills:
    - nvidia-laptop-gaming-tuning
    - linux-system
lane: worker-heavy
reasoning_effort: xhigh
trigger_keywords: ['nvidia', 'suspend', 'resume', 'workflow', 'need']
keywords: ['nvidia', 'suspend', 'resume', 'workflow', 'need']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['voice-clone', 'github-workflow', 'multi-agent-pitfalls-cheatsheet']
---



# NVIDIA Suspend/Resume Debugging

## Diagnostic Flow (always read-only first)

### 1. Identify the Error Pattern

```bash

set -euo pipefail
# The key error — GPU fails to reinitialize after resume
journalctl -k -b 0 --grep="RmInitAdapter|rm_init_adapter|NVRM" --no-pager

# Check if it's boot-related or resume-related
journalctl -k -b 0 --grep="PM: suspend|PM: resume|suspend_enter|syscore" --no-pager

# Check current suspend mode
cat /sys/power/mem_sleep  # [s2idle] deep → currently active is s2idle
```

### 2. Check GPU Power State & Driver Configuration

```bash

set -euo pipefail
# NVIDIA power management params
cat /proc/driver/nvidia/params | grep -iE "S0ix|DynamicPower|PreserveVideo|UseKernelSuspend"

# GPU runtime PM state
cat /sys/bus/pci/devices/0000:01:00.0/power/runtime_status  # active/suspended
cat /sys/bus/pci/devices/0000:01:00.0/power/control       # auto/on

# NVIDIA services
systemctl status nvidia-suspend.service nvidia-resume.service nvidia-hibernate.service
```

### 3. Check Wakeup Sources (common trigger)

```bash

set -euo pipefail
# ACPI wakeup devices
cat /proc/acpi/wakeup | grep -E '\*enabled'

# PCI wakeup
for dev in /sys/bus/pci/devices/*/power/wakeup; do
  val=$(cat "$dev" 2>/dev/null)
  [ "$val" = "enabled" ] && echo "ENABLED: $(basename $(dirname $dev))"
done

# USB wakeup
for dev in /sys/bus/usb/devices/*/power/wakeup; do
  val=$(cat "$dev" 2>/dev/null)
  [ "$val" = "enabled" ] && echo "ENABLED: $(cat $(dirname "$dev")/product 2>/dev/null)"
done
```

### 4. Check Optimus Configuration

```bash

set -euo pipefail
# Which GPU is primary?
lspci | grep -E "VGA|3D|Display"

# DRM devices (card1 = iGPU/intel, card2 = nvidia)
ls -la /sys/class/drm/

# External monitor connected to which GPU?
for f in /sys/class/drm/*/status; do echo "$(basename $(dirname $f)): $(cat $f)"; done

# NVIDIA sleep hook
cat /lib/systemd/system-sleep/nvidia 2>/dev/null
```

## Common Root Causes & Fixes

### Cause 1: S0ix Disabled + DynamicPowerManagement=2 Conflict

**Symptom:** `RmInitAdapter failed! (0x22:0x56:1017)` after resume, GPU needs full reboot.
**Why:** `EnableS0ixPowerManagement=0` + `DynamicPowerManagement=2` creates inconsistent power state during resume. The GPU enters S0ix but the driver doesn't handle it correctly.

**Fix:**
```bash

set -euo pipefail
# Add to /etc/modprobe.d/nvidia-graphics-drivers-kms.conf (or create new file)
options nvidia NVreg_EnableS0ixPowerManagement=1
options nvidia NVreg_DynamicPowerManagement=0x00
```
Then: `sudo update-initramfs -u` + reboot.

**Alternative (if S0ix causes other issues):**
```bash

set -euo pipefail
options nvidia NVreg_DynamicPowerManagement=0x01  # GPU stays awake, no S0ix
```

### Cause 2: External Monitor Wakeup via PEG1/PXSX

**Symptom:** GPU error only when external monitor is connected during sleep.
**Why:** External monitor is wired to iGPU (card1 = Intel/AMD), but wakeup triggers PCIe event through PEG1 (NVIDIA). The NVIDIA GPU wakes via S3 but fails to reinitialize because the display output routes through the iGPU.

**Fix — disable wakeup on NVIDIA-related PCIe ports:**
```bash

set -euo pipefail
# Disable wakeup on NVIDIA GPU and its bridges
echo disabled | sudo tee /sys/bus/pci/devices/0000:01:00.0/power/wakeup
echo disabled | sudo tee /sys/bus/pci/devices/0000:00:01.0/power/wakeup
echo disabled | sudo tee /sys/bus/pci/devices/0000:00:06.0/power/wakeup
```

**Or switch suspend mode:**
```bash

set -euo pipefail
# If s2idle causes issues, try deep (requires BIOS support)
echo deep | sudo tee /sys/power/mem_sleep
# Note: deep may not work on all laptops, test with: sudo systemctl suspend
```

### Cause 3: PreserveVideoMemoryAllocations + s2idle Incompatibility

**Symptom:** Resume works with `deep` but fails with `s2idle`.
**Why:** `PreserveVideoMemoryAllocations=1` reserves VRAM across sleep, but s2idle doesn't fully power-cycle the GPU, causing stale memory state on resume.

**Fix options:**
```bash

set -euo pipefail
# Option A: Disable video memory preservation (uses more power, but more reliable)
options nvidia NVreg_PreserveVideoMemoryAllocations=0

# Option B: Use deep suspend instead of s2idle
echo deep | sudo tee /sys/power/mem_sleep
```

### Cause 4: nvidia-sleep.sh Hook Missing/Incorrect

**Symptom:** NVIDIA services exist but don't properly signal the driver about suspend/resume.
**Why:** The systemd sleep hook (`/lib/systemd/system-sleep/nvidia`) must call `nvidia-sleep.sh` to tell the driver to save/restore state.

**Verify:**
```bash

set -euo pipefail
cat /proc/driver/nvidia/suspend  # Should show: suspend hibernate resume
cat /lib/systemd/system-sleep/nvidia  # Should exist and call nvidia-sleep.sh
```

**Fix if missing:**
```bash

set -euo pipefail
# Reinstall the driver's sleep hook
sudo apt install --reinstall nvidia-kernel-common-595
```

### Cause 5: GNOME Inhibitors Blocking Proper Suspend

**Symptom:** Suspend appears to work but GPU state is corrupted on resume.
**Why:** GNOME inhibitors (gsd-power with lid-switch, gnome-session) can block the suspend sequence, causing partial GPU shutdown.

**Check:**
```bash

set -euo pipefail
systemd-inhibit --list | grep -E "block|sleep"
```

**Fix:** If `gsd-power handle-lid-switch` is blocking, it means lid switch events are interfering. Disable lid-switch handling:
```bash

set -euo pipefail
# GNOME: ignore lid switch
gsettings set org.gnome.settings-daemon.plugins.power lid-close-ac-action 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power lid-close-battery-action 'nothing'
```

## RTX 50xx (Blackwell) Specific Quirks

1. **Open Kernel Module Required:** RTX 50xx needs `nvidia-open` kernel module. The error `"requires use of the NVIDIA open kernel modules"` is **normal** and not the cause of resume failures.

2. **GSP Firmware:** Blackwell uses GSP (GPU System Processor) for power management. Ensure firmware is loaded:
   ```bash

set -euo pipefail
   dmesg | grep -i "gsp\|firmware" | grep -i nvidia
   ```

3. **Error Code 0x22:0x56:1017:** This is `NV_ERROR_INVALID_GPU_STATE` — the GPU is in an invalid power state during resume. Fix is almost always S0ix or DynamicPowerManagement configuration.

## Pitfalls

1. **Don't confuse `RmInitAdapter failed` with driver not loaded.** The error happens AFTER the driver loads — it's a runtime initialization failure, not a module loading failure.

2. **`nvidia-smi` working ≠ GPU fully functional.** The kernel module may load but display output may be broken. Always check `dmesg | grep -i nvidia` for the full picture.

3. **External monitor topology matters.** On Optimus laptops, external ports (DP/HDMI) may be wired to the iGPU, not the NVIDIA GPU. Wakeup events on these ports trigger PEG1/PXSX wakeup, which can confuse the NVIDIA driver.

4. **`s2idle` vs `deep` is hardware-dependent.** Not all laptops support `deep` (S3) suspend. Test with `sudo systemctl suspend` before committing.

5. **NVReg changes require `update-initramfs -u`.** The initramfs loads these parameters at boot. Skipping this step means changes don't take effect.

6. **Multiple modprobe.d files can conflict.** Check all files in `/etc/modprobe.d/` and `/usr/lib/modprobe.d/` for duplicate `options nvidia` lines.

7. **nvidia-sleep.sh must be executable.** If permissions are wrong, the suspend/resume hook silently fails.

## References

- `references/rm-init-adapter-wakeup-fix-2026-06-27.md` — Full session transcript: RTX 5060 + driver 595 + external DP monitor → RmInitAdapter failed after resume, S0ix/DynamicPowerManagement conflict analysis, 3 fix options with trade-offs.
