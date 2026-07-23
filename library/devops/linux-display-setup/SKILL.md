---
name: linux-display-setup
title: Linux Display Setup
description: |
  Use when a Linux monitor has the wrong resolution or refresh rate, appears as unknown, has broken EDID data, or needs X11, Wayland, NVIDIA, or modeline diagnosis.
  NOT for general GPU performance tuning, remote headless servers, or applying persistent display changes before live detection and driver state are verified.
  Provides a diagnostic-first workflow for display detection, EDID repair, custom modes, GPU drivers, and multi-monitor configuration.
triggers:
- User says monitor is "unknown display" / not detected
- User wants custom resolution or refresh rate (e.g. 144Hz)
- EDID-related display issues (0mm x 0mm in xrandr)
- Multi-monitor layout configuration
- GPU driver check (NVIDIA, AMD, Intel)
- G-Sync / VRR setup
- Second monitor detected at wrong resolution
version: 1.0.0
author: Hermes Agent
license: MIT
lane: worker-heavy
reasoning_effort: xhigh
trigger_keywords: ['monitor', 'edid', 'display', 'detection', 'linux']
keywords: ['monitor', 'edid', 'display', 'detection', 'linux']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---


# Linux Display Setup

## Diagnostic Workflow

When a monitor shows wrong resolution or is detected as "unknown display",
work through this checklist before proposing fixes:

1. **Identify GPU and current driver**
   ```bash

set -euo pipefail
   lspci | grep -E "VGA|3D|Display"
   nvidia-smi 2>/dev/null || echo "No NVIDIA GPU detected"
   ```

2. **List all displays and current modes**
   ```bash

set -euo pipefail
   xrandr --query
   ```
   - `*` = currently active mode
   - `+` = preferred mode (from EDID)
   - Look for monitors reporting `0mm x 0mm` — **hallmark of broken EDID**

3. **Get detailed monitor info** (especially for "unknown display")
   ```bash

set -euo pipefail
   xrandr --verbose | grep -A30 "^<PORT>"
   ```
   Check: `vrr_capable`, `max bpc`, connection type (`subconnector: Native`)

4. **Calculate correct modeline**
   ```bash

set -euo pipefail
   cvt 1920 1080 144            # Standard CVT timing
   # Output: Modeline "1920x1080_144.00"  452.50  1920 2088 2296 2672  1080 1083 1088 1177 -hsync +vsync
   ```
   - `cvt <width> <height> <refresh>` for standard timing
   - `cvt -r <width> <height> <refresh>` for reduced blanking (some monitors prefer this)
   - If both fail, try known-working GTF timings from monitor forums

## EDID Repair — Custom Modeline

When EDID is broken, the monitor reports no physical size (`0mm x 0mm`) and only
shows basic resolutions like 1024x768 or 640x480. The fix is to manually add a
custom modeline.

**Step 1: Create the new mode**
```bash

set -euo pipefail
xrandr --newmode "1920x1080_cvt144"  452.50  1920 2088 2296 2672  1080 1083 1088 1177 -hsync +vsync
```
The name (e.g. `1920x1080_cvt144`) is free-form — use something descriptive.

**Step 2: Add mode to the correct output port**
```bash

set -euo pipefail
xrandr --addmode DP-1-1 "1920x1080_cvt144"
```
Find the port from `xrandr --query`: look for `connected` entries (DP-0, HDMI-0, DP-1-1, etc.).

**Step 3: Activate the mode**
```bash

set -euo pipefail
xrandr --output DP-1-1 --mode "1920x1080_cvt144" --rate 144 --right-of eDP-1-1
```
Position options: `--right-of`, `--left-of`, `--above`, `--below`, or `--same-as`.

**Step 4: Verify**
```bash

set -euo pipefail
xrandr --query | grep -A5 "DP-1-1"
```
Look for the new mode with `*` (active marker). Example output:
```

set -euo pipefail
DP-1-1 connected 1920x1080+1920+0
   1920x1080_cvt144 143.88*       # ← 144Hz aktiv!
```

### Important: xrandr vs NVIDIA MetaMode

Modes added via `xrandr --newmode` + `--addmode` are NOT managed by
`nvidia-settings`. Attempting to set `CurrentMetaMode` with
`ForceCompositionPipeline` or `AllowGSYNCCompatible` via nvidia-settings
on an xrandr-created mode will fail with `Attribute not available`.

To get G-Sync working on custom modelines, use xrandr to set `vrr_capable`:
```bash

set -euo pipefail
xrandr --output DP-1-1 --set "vrr_capable" 1
```

But note: G-Sync via nvidia-settings requires modes to be set through
NVIDIA's own MetaMode system (via nvidia-xconfig or nvidia-settings GUI),
not through raw xrandr.

## Persistence (Autostart)

Custom modelines **do not survive a reboot** because the EDID is still broken.
Three persistence strategies:

### A. xrandr Autostart Script (Recommended, simple)
1. Create a script in `~/bin/`:
   ```bash

set -euo pipefail
   mkdir -p ~/bin
   cat > ~/bin/monitor-setup.sh << 'SCRIPT'
   #!/bin/bash
   xrandr --newmode "1920x1080_cvt144"  452.50  1920 2088 2296 2672  1080 1083 1088 1177 -hsync +vsync 2>/dev/null
   xrandr --addmode DP-1-1 "1920x1080_cvt144" 2>/dev/null
   xrandr --output DP-1-1 --mode "1920x1080_cvt144" --rate 144 --right-of eDP-1-1
   SCRIPT
   chmod +x ~/bin/monitor-setup.sh
   ```
2. Add to Gnome/KDE autostart:
   ```bash

set -euo pipefail
   mkdir -p ~/.config/autostart
   cat > ~/.config/autostart/monitor-setup.desktop << 'EOF'
   [Desktop Entry]
   Type=Application
   Name=Monitor Setup
   Exec=/home/bratan/bin/monitor-setup.sh
   X-GNOME-Autostart-enabled=true
   NoDisplay=true
   EOF
   ```

### B. xorg.conf (Advanced, NVIDIA only)
Add to /etc/X11/xorg.conf:
```

set -euo pipefail
Section "Monitor"
    Identifier  "DP-1-1"
    Modeline    "1920x1080_144" 452.50 1920 2088 2296 2672 1080 1083 1088 1177 -hsync +vsync
    Option      "PreferredMode" "1920x1080_144"
EndSection
```

### C. Kernel boot parameter (EDID override)
Add `video=DP-1-1:1920x1080@144` to GRUB_CMDLINE_LINUX_DEFAULT in `/etc/default/grub`.
This works for simple resolutions but not for custom timings.

## G-Sync / VRR on Custom Modes

G-Sync with custom xrandr modelines is limited:

1. **Check if VRR is supported on the port:**
   ```bash

set -euo pipefail
   xrandr --props | grep -A5 "DP-1-1" | grep vrr_capable
   ```
   `vrr_capable: 0` means disabled.

2. **Enable VRR via xrandr (partial):**
   ```bash

set -euo pipefail
   xrandr --output DP-1-1 --set "vrr_capable" 1
   ```
   This may enable variable refresh at the driver level.

3. **Full G-Sync with nvidia-settings** requires the mode to be set through
   NVIDIA's MetaMode system, not xrandr. Steps:
   - Generate xorg.conf: `sudo nvidia-xconfig`
   - Add custom modeline to xorg.conf
   - Set `AllowGSYNCCompatible=On` in the Display Device section
   - Reboot

## Multi-Monitor Layout Quick Reference

| Command | Effect |
|---------|--------|
| `--right-of eDP-1-1` | External right of laptop |
| `--left-of eDP-1-1` | External left of laptop |
| `--above eDP-1-1` | External above laptop |
| `--same-as eDP-1-1` | Mirror (clone) mode |
| `--primary` | Set as primary display |

## Pitfalls

1. **`cvt` pixel clock may exceed DisplayPort bandwidth.**
   DP 1.2 max: 540 MHz. CVT 1920x1080@144 = 452.50 MHz — fine.
   CVT 2560x1440@144 = 596.50 MHz — exceeds DP 1.2 limit! Use `cvt -r` for reduced blanking.

2. **Custom modes vanish on display sleep/wake.** The autostart script
   may not re-run. Workaround: create a udev rule or use `xrandr` in
   a systemd user service that watches for `DP-1-1` reconnect.

3. **`xrandr --newmode` fails if mode name already exists.** Always
   use unique names (e.g. include refresh rate in the name) and
   redirect stderr: `2>/dev/null`.

4. **`nvidia-settings --assign CurrentMetaMode` fails on xrandr-created modes.**
   The error is `Attribute not available` — NVIDIA's MetaMode system
   only recognizes modes configured through nvidia-settings or xorg.conf.

5. **EDID works fine on Windows but not Linux.** This is common with
   certain monitor firmware/GPU combinations. The fix is always the same
   5. **EDID works fine on Windows but not Linux.** This is common with certain monitor firmware/GPU combinations. The fix is always the same (xrandr custom modeline), regardless of the root cause.

   6. **NVIDIA driver loaded but nvidia-smi shows "No devices found"** — Not a display issue! This is a kernel module problem. Check: `lsmod | grep nvidia` (module loaded?), `modinfo -F filename nvidia` (proprietary vs open kernel path), `dmesg | grep "open kernel modules"` (RTX 50xx mismatch). See `nvidia-laptop-gaming-tuning` skill for full diagnosis.

- `references/edid-modeline-recipes.md` — Known-working modelines for specific monitors
