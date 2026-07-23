# RmInitAdapter Failed After Resume — Wakeup Fix Session 2026-06-27

## System Profile
- Laptop: CLEVO/KAPOK (Optimus)
- CPU: Intel (likely 12th+ gen, intel_pstate)
- GPU: NVIDIA GeForce RTX 5060 Laptop GPU (Blackwell, Device ID 10de:2d19)
- Driver: 595.71.05 (open kernel module)
- Kernel: 6.17.0-35-generic
- Display: eDP-1 (internal) + DP-1 (external) — both connected
- Suspend mode: s2idle (deep available but not default)

## Error Pattern

### Symptom
```
NVRM: GPU 0000:01:00.0: RmInitAdapter failed! (0x22:0x56:1017)
NVRM: GPU 0000:01:00.0: rm_init_adapter failed, device minor number 0
```
Error repeats 5-6 times during boot, then stabilizes. GPU works after full reboot but fails after suspend→resume cycle.

### Error Code Meaning
`0x22:0x56:1017` = `NV_ERROR_INVALID_GPU_STATE` — GPU is in an invalid power state during resume. The driver tries to initialize the GPU but it's in D3cold or S0ix state that wasn't properly restored.

## Root Cause Analysis

### Primary Cause: S0ix/DynamicPowerManagement Conflict
```
EnableS0ixPowerManagement: 0        ← S0ix disabled
DynamicPowerManagement: 2            ← Fine-grained power management active
```

The GPU enters a low-power state during s2idle suspend, but without S0ix management enabled, the resume path doesn't properly reinitialize the GPU's power state machines.

### Contributing Factor: External Monitor Wakeup Topology
```
ACPI Wakeup Sources (enabled):
  PEG0   S3  *enabled  pci:0000:00:06.0  ← PCIe bridge (NVIDIA-related)
  PEG1   S3  *enabled  pci:0000:00:01.0  ← PCIe bridge (also routes to NVIDIA)
  XHCI   S3  *enabled  pci:0000:00:14.0  ← USB controller
  RP07   S4  *enabled  pci:0000:00:1c.0  ← Root port
  PXSX   S0  *enabled  pci:0000:03:00.0  ← Realtek Ethernet (r8169)
  PWRB   S3  *enabled  platform:PNP0C0C:00  ← Power button
  SLPB   S3  *enabled  platform:PNP0C0E:00  ← Sleep button
  LID0   S3  *enabled  platform:PNP0C0D:00  ← Lid switch
```

External monitor is connected to DP-1, which routes through the iGPU (card1 = Intel). But PEG1 wakeup can trigger NVIDIA GPU wakeup unnecessarily, causing the RmInitAdapter failure.

### Additional Factor: GNOME Inhibitors
```
gsd-power    handle-lid-switch    block    ← Blocks lid switch handling
gsd-power    sleep                delay    ← Delays sleep for screen lock
gnome-session-b sleep             block    ← Session inhibits sleep
```

GNOME inhibitors can cause partial suspend sequences where the GPU driver's suspend hook runs but the GPU hardware isn't fully powered down.

## Fix Options

### Option A: Enable S0ix Power Management (Recommended)
**Trade-off:** Requires S0ix support in BIOS, may not work on all laptops.

```bash
# Edit /etc/modprobe.d/nvidia-graphics-drivers-kms.conf
# Add these lines:
options nvidia NVreg_EnableS0ixPowerManagement=1
options nvidia NVreg_DynamicPowerManagement=0x00

# Apply
sudo update-initramfs -u
sudo reboot
```

**Why it works:** S0ix power management gives the NVIDIA driver a proper resume path for S0ix-enabled GPUs. Setting DynamicPowerManagement to 0x00 (disabled) prevents the conflicting fine-grained power management from fighting with S0ix.

### Option B: Disable GPU Wakeup Sources (Safe)
**Trade-off:** GPU won't wake on PCIe events, only on explicit power button.

```bash
# Disable wakeup on NVIDIA GPU and related bridges
echo disabled | sudo tee /sys/bus/pci/devices/0000:01:00.0/power/wakeup
echo disabled | sudo tee /sys/bus/pci/devices/0000:00:01.0/power/wakeup
echo disabled | sudo tee /sys/bus/pci/devices/0000:00:06.0/power/wakeup

# Make persistent via udev rule or systemd service
```

**Why it works:** Prevents spurious wakeup events from triggering GPU reinitialization when the GPU isn't actually needed.

### Option C: Switch to Deep Suspend
**Trade-off:** Higher power consumption during sleep, slower resume.

```bash
echo deep | sudo tee /sys/power/mem_sleep
# Test: sudo systemctl suspend
```

**Why it works:** Deep (S3) suspend fully powers down the GPU, so resume is a clean reinitialization rather than trying to resume from a low-power state.

### Option D: Disable DynamicPowerManagement (Simple)
**Trade-off:** GPU always powered on, slightly higher idle power consumption.

```bash
options nvidia NVreg_DynamicPowerManagement=0x01
# 0x01 = coarse-grained (on/off), avoids the problematic fine-grained mode 2
```

## Key Diagnostic Commands

```bash
# Full NVIDIA power state snapshot
cat /proc/driver/nvidia/params | grep -iE "S0ix|Dynamic|Preserve|KernelSuspend"
cat /proc/driver/nvidia/gpus/0000:01:00.0/power 2>/dev/null

# Wakeup source audit
cat /proc/acpi/wakeup | grep enabled
for dev in /sys/bus/pci/devices/*/power/wakeup; do
  [ "$(cat $dev)" = "enabled" ] && echo "$(basename $(dirname $dev)): enabled"
done

# Suspend/resume cycle test
sudo systemctl suspend
# After resume:
dmesg | grep -iE "nvidia|NVRM|PM:" | tail -30
nvidia-smi  # Should show GPU without errors
```

## Session Notes

- The `RmInitAdapter failed` error is **not** a driver loading failure — the kernel module loads fine, but the GPU hardware fails to initialize during the resume path.
- The error code `0x22:0x56:1017` is specific to `NV_ERROR_INVALID_GPU_STATE`.
- RTX 50xx (Blackwell) with open kernel modules is particularly sensitive to S0ix configuration.
- External monitors connected to the iGPU's DP ports can trigger wakeup events on NVIDIA PCIe bridges (PEG1), causing unnecessary GPU wakeup attempts.
- The `nvidia-sleep.sh` hook and `PreserveVideoMemoryAllocations=1` are correct but insufficient without proper S0ix management.
