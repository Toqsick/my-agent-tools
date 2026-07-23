---
name: rtx-5060-laptop-fix-2026-06-18
description: Session transcript reference for the nvidia-powerd + Coolbits recovery on a Lenovo P1 with RTX 5060 Laptop (device 2d19), driver 595.71.05, kernel 6.17.0-35. Use as a worked example; the skill SKILL.md is the distilled procedure.
---

# RTX 5060 Laptop (2d19) — Worked Example

## Hardware / driver context
- Lenovo ThinkPad P1 (17", build name `bratan-17-P1`)
- GPU: NVIDIA GeForce RTX 5060 **Laptop**, device ID `2d19`
- Driver: 595.71.05 (CUDA 13.2 reported)
- Kernel: 6.17.0-35-generic
- Module: `nvidia-open` flavour (`nvidia.ko` from `nvidia-kernel-open-595`)
- Optimus: Intel iGPU drives the internal panel, NVIDIA dGPU for compute/render

## What was broken before this session
Two compounding issues:

1. **nvidia-powerd service unit missing.** The `nvidia-kernel-common-595`
   package shipped `/usr/bin/nvidia-powerd` and a doc copy of the service
   file at `/usr/share/doc/nvidia-kernel-common-595/nvidia-powerd.service`,
   but **not** the unit at `/etc/systemd/system/nvidia-powerd.service`.
   Result: `systemctl status nvidia-powerd` showed `Unit not found`, so
   Dynamic Boost never engaged.

2. **Bad xorg.conf from a previous `nvidia-xconfig --cool-bits=12` call.**
   That command wrote a *full* `/etc/X11/xorg.conf` with a `Device` section
   binding `Driver "nvidia"` + BusID. On an Optimus laptop this disables
   the iGPU → black internal screen → forced a rescue-shell recovery in
   an earlier session. The file had been removed already, with the
   pre-incident copy preserved as `/etc/X11/xorg.conf.nvidia-xconfig-original`
   and the bad one as `/etc/X11/xorg.conf.disabled-by-yuno`.

## The fix sequence (what actually worked, in order)

### Step 1: Restore the powerd service
```bash
sudo cp /usr/share/doc/nvidia-kernel-common-595/nvidia-powerd.service \
        /etc/systemd/system/nvidia-powerd.service
sudo systemctl daemon-reload
sudo systemctl enable --now nvidia-powerd
systemctl status nvidia-powerd
# required output: Active: active (running)
```

Important: the shipped unit is `Type=simple`, **not** `Type=dbus`. A
hand-rolled `Type=dbus` version hangs in `activating` waiting for a bus
name that nobody is going to claim. Use the shipped one.

The DBus policy issue (chmod 644, `messagebus` user) called out in the
skill did **not** apply here — the DBus policy was already correct
(`/etc/dbus-1/system.d/nvidia-powerd.conf` was present and readable), so
the service started on first try. The skill's chmod fix matters for
fresh installs only.

### Step 2: Reboot
`sudo reboot`. After the reboot:
- `systemctl status nvidia-powerd` → active since boot
- `nvidia-smi` → lists RTX 5060 Laptop, no errors
- `nvidia-smi --query-gpu=power.draw,clocks.gr,clocks.mem --format=csv`
  populated normally (P8 idle, 3-4W, low clocks)

### Step 3: Confirm GWE sees the GPU
```bash
flatpak run com.leinardi.gwe --debug > /tmp/gwe.log 2>&1 &
sleep 12
grep -iE "supported|capab|power.*limit" /tmp/gwe.log
dbus-send --session --dest=org.freedesktop.DBus \
  --type=method_call --print-reply /org/freedesktop/DBus \
  org.freedesktop.DBus.ListNames | grep -i gwe
pkill -f com.leinardi.gwe
```

Observed:
- Debug log shows `Fetching new data took ~80 ms` repeating every 3s —
  NVML polling healthy.
- **Expected line:** `Function nvmlDeviceGetPowerManagementLimit not
  supported` — this is the *expected* state without Coolbits and is the
  green light to proceed to Step 4. Do not chase it as a bug.
- `com.leinardi.gwe` appears in the DBus name list — GUI subsystem is
  healthy.
- No "no supported GPU", no NVML ABI errors.

## What's still pending (next session)

Coolbits via a hand-written `/etc/X11/xorg.conf.d/99-coolbits.conf`
snippet containing only the Coolbits Option (no Driver / BusID section).
The user chose not to do this in the same session as the powerd fix
because the original `nvidia-xconfig`-induced black screen was still
fresh and they wanted to validate the baseline first. The right
sequence when the user comes back:

1. Write the minimal snippet (see SKILL.md "Coolbits without breaking
   Optimus boot" section).
2. Reboot.
3. Re-run the GWE debug log — `PowerManagementLimit not supported` line
   should be **gone**.
4. `nvidia-settings -q all | grep -i coolbits` should list the Coolbits
   attribute.

## Don't-touch list (state to preserve on next session)

- `/etc/modprobe.d/nvreg_fix.conf` with `NVreg_OpenRmEnableUnsupportedGpus=1`
  — **required** for the 5060 Laptop (device 2d19) to bind. Removing it
  makes the kernel module silently refuse the GPU.
- `/etc/dbus-1/system.d/nvidia-powerd.conf` — already correct, don't
  recreate.
- `/etc/systemd/system/nvidia-powerd.service` — the doc copy, not a
  hand-rolled unit.
- `/etc/X11/xorg.conf.nvidia-xconfig-original` — keep as the historical
  record of what broke boot. Do not move it back to `xorg.conf`.
