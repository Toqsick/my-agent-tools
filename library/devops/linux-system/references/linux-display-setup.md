# Linux Display Setup — Full Reference

Extracted from the `linux-display-setup` skill.

## Diagnostic Workflow
```bash
# 1. GPU and driver
lspci | grep -E "VGA|3D|Display"
nvidia-smi 2>/dev/null || echo "No NVIDIA GPU"

# 2. Displays and modes
xrandr --query
# * = active, + = preferred, 0mm x 0mm = broken EDID

# 3. Detailed info
xrandr --verbose | grep -A30 "^<PORT>"

# 4. Calculate modeline
cvt 1920 1080 144
# Output: Modeline "1920x1080_144.00" 452.50 ...
```

## EDID Repair — Custom Modeline
```bash
# Step 1: Create mode
xrandr --newmode "1920x1080_cvt144" 452.50 1920 2088 2296 2672 1080 1083 1088 1177 -hsync +vsync

# Step 2: Add to port
xrandr --addmode DP-1-1 "1920x1080_cvt144"

# Step 3: Activate
xrandr --output DP-1-1 --mode "1920x1080_cvt144" --rate 144 --right-of eDP-1-1

# Step 4: Verify
xrandr --query | grep -A5 "DP-1-1"
```

### ⚠️ When step 3 fails with `X Error: BadValue` / `Value 0x780`
The mode is created and added to the output, but the CRTC refuses to set a
resolution larger than the EDID-derived fallback. `0x780` is the rejected value
in hex (= 1920 in decimal). This is **not** a bandwidth problem — even lowering
to 120 Hz won't help, because the CRTC is hard-capped to whatever the driver
chose as the safe default (usually 1024x768) when EDID was missing.

**Root cause:** NVIDIA's proprietary driver (`nvidia.ko`) caps the CRTC to a
fallback resolution when the output has no valid EDID. Custom modelines added
via `xrandr --newmode`/`--addmode` are accepted by the RANDR protocol, but the
`RRSetCrtcConfig` call then fails because the requested mode is bigger than
the cap. The "missing EDID" check: `ls -la /sys/class/drm/card*/DP-1/edid` →
size 0 means no EDID was read.

**Verify it's the cap and not a real bandwidth problem:**
```bash
# A sub-fallback mode should succeed:
xrandr --newmode "test_low" 65.0 1024 1048 1184 1344 768 771 777 806 -hsync +vsync
xrandr --addmode DP-1  "test_low"
xrandr --output DP-1 --mode "test_low"   # works → cap is the issue
# Now try the real resolution — this is the one that fails
```

**Fixes (in order of preference):**

1. **Re-plug the cable to trigger an EDID re-read** (cheapest, fixes ~80% of cases)
   - Unplug DP cable from laptop, wait 5s, replug
   - Unplug from monitor too, wait 5s, replug
   - Wait 5–10s for hotplug, then `xrandr` — if a real `1920x1080` mode appears as preferred, run the modeline dance on that native mode instead of a `cvt` one.

2. **`Option "ModeValidation" "AllowNonEdidModes"` in xorg.conf.d** (lets xrandr push the modeline through)
   ```ini
   # /etc/X11/xorg.conf.d/99-custom-mode-DP-1.conf
   Section "Monitor"
       Identifier   "DP-1"
       Option       "ModeValidation" "AllowNonEdidModes"
   EndSection
   ```
   Requires an Xorg restart. **Do not** generate `/etc/X11/xorg.conf` via
   `nvidia-xconfig` — see NVIDIA troubleshooting ref for why.

3. **Provide a CustomEDID blob** (use when the monitor/EDID is genuinely bad, not just a hotplug glitch)
   - Dump the monitor's EDID from a working system with `get-edid` / `monitor-edid` / `nvidia-settings → Display → Save EDID...`
   - Place at e.g. `/etc/X11/edids/dp-1.bin` (chmod 444)
   - Add to xorg.conf.d:
     ```ini
     Section "Monitor"
         Identifier   "DP-1"
         Option       "CustomEDID" "DP-1:/etc/X11/edids/dp-1.bin"
     EndSection
     ```

**Diagnostic shortcuts:**
```bash
# Confirm EDID is the issue (size 0 = no EDID read)
ls -la /sys/class/drm/card*/DP-1/edid
# Or on NVIDIA's proprietary driver:
sudo cat /sys/class/drm/card1-DP-1/edid | xxd | head -3

# nvidia-smi display state is unreliable — "display_active: Disabled" can
# happen even when a display IS connected. Don't trust it as a diagnosis.

# Multi-GPU / Optimus: outputs may be on card1 / card2, not card0
ls /sys/class/drm/

# gtf at non-60Hz without -r produces a high-pixclk modeline (450+ MHz at
# 1920x1080@144) — even DP-1.2 (HBR2, 540 MHz/lane) can usually take it,
# but a 1024x768 EDID fallback has nothing to do with pixclk. Don't waste
# time lowering refresh rate to "fix" a 0x780.
```

## Persistence (Autostart)
```bash
# Create ~/bin/monitor-setup.sh with xrandr commands
mkdir -p ~/bin
cat > ~/bin/monitor-setup.sh << 'SCRIPT'
#!/bin/bash
xrandr --newmode "1920x1080_cvt144" 452.50 1920 2088 2296 2672 1080 1083 1088 1177 -hsync +vsync 2>/dev/null
xrandr --addmode DP-1-1 "1920x1080_cvt144" 2>/dev/null
xrandr --output DP-1-1 --mode "1920x1080_cvt144" --rate 144 --right-of eDP-1-1
SCRIPT
chmod +x ~/bin/monitor-setup.sh

# Add to autostart
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

## G-Sync / VRR
```bash
# Check VRR support
xrandr --props | grep -A5 "DP-1-1" | grep vrr_capable

# Enable VRR via xrandr
xrandr --output DP-1-1 --set "vrr_capable" 1

# Full G-Sync requires NVIDIA MetaMode (nvidia-settings or xorg.conf)
```

## Multi-Monitor Layout
| Command | Effect |
|---------|--------|
| `--right-of eDP-1-1` | External right of laptop |
| `--left-of eDP-1-1` | External left |
| `--above eDP-1-1` | External above |
| `--same-as eDP-1-1` | Mirror (clone) |
| `--primary` | Set as primary |

## Pitfalls
1. `cvt` pixel clock may exceed DP bandwidth — use `cvt -r` for reduced blanking
2. Custom modes vanish on display sleep/wake — use autostart script
3. `xrandr --newmode` fails if name exists — use unique names + `2>/dev/null`
4. `nvidia-settings --assign CurrentMetaMode` fails on xrandr-created modes
5. **NVIDIA caps CRTC to 1024x768 when EDID is missing.** A `cvt` modeline is
   accepted by `xrandr --newmode`/`--addmode` but `--output --mode` fails with
   `X Error BadValue 0x780` (0x780 = 1920 in decimal = the resolution).
   **This is NOT a bandwidth problem** — lowering refresh rate won't help. See
   the "When step 3 fails" section above for the three real fixes
   (re-plug → `ModeValidation AllowNonEdidModes` → `CustomEDID`).
6. **EDID that worked on Windows but not Linux is NOT always fixable with a
   custom modeline** on NVIDIA. The driver can refuse custom modes when there's
   no valid EDID; the cure is an EDID re-read or a CustomEDID blob, not more
   `cvt` arithmetic.
7. **`nvidia-smi --query-gpu=display_active` is unreliable** as a "is the
   display connected" probe. `display_active: Disabled` can occur even when a
   display IS connected (this session, Zorin/GNOME Wayland via XWayland).
   Trust `/sys/class/drm/card*-DP-1/edid` (size 0 = no EDID) and `xrandr --query` instead.
8. **Wayland blocks NV-CONTROL X extension** — nvidia-settings and GWE cannot
   communicate with the GPU under Wayland. Diagnose with `echo $XDG_SESSION_TYPE`.
   Fix: switch to X11 at GDM login, or use `nvidia-smi` CLI which goes through
   the kernel driver directly.
9. **PRIME Render Offload** — on Optimus laptops, GL apps default to the iGPU.
   Force NVIDIA GPU: `__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia <command>`.
   Without this, `nvidia-smi` shows 0% GPU utilization even under heavy GL load.
