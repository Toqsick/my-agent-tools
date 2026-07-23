# NVIDIA Prime Wayland Debugging — Optimus Laptops with Flatpak Steam

**Date:** 2026-06-28
**Context:** Acer-P1, Zorin OS (Wayland/Gnome), RTX 5060 Laptop, nvidia-driver-595-open, Flatpak Steam (com.valvesoftware.Steam), GE-Proton10-34

## Problem Class

Optimus laptop where:
- GPU driver loads fine (`nvidia-smi` works, `glxinfo` shows NVIDIA)
- `prime-run` exists and routes correctly
- But games still render on iGPU (terrible FPS) or crash on launch

## Root Causes Discovered

### 1. Session-global `__NV_PRIME_RENDER_OFFLOAD=1` + `__GLX_VENDOR_LIBRARY_NAME=nvidia`

**Symptom:** `env | grep -E '__NV_|__GLX_'` shows both vars set to `nvidia`/`1`.

**Source:** On Zorin/Wayland, `gnome-session-binary` (PID ~15579) sets these and inherits them to ALL child processes including the compositor, browsers, and Flatpak apps. NOT in `/etc/environment`, NOT in `pam_env.conf`, NOT in user dotfiles — injected by the session binary itself.

**Detection:**
```bash
# Find the source (oldest PID carrying the vars):
for p in $(ls /proc | grep -E '^[0-9]+$' | sort -n); do
  if grep -q "__NV_PRIME_RENDER_OFFLOAD" /proc/$p/environ 2>/dev/null; then
    echo "PID=$p CMD=$(tr '\0' ' ' < /proc/$p/cmdline | head -c 80)"
  fi
done | head -10
```

**Impact:** Everything renders on NVIDIA → EC power cap (25W on this laptop) → thermal throttle → games stutter even though "GPU is working".

**Fix:** `sudo prime-select on-demand` + reboot. This makes the session use iGPU by default, and only `prime-run <game>` switches to NVIDIA.

### 2. Flatpak Steam ignores host `prime-run`

**Symptom:** `prime-run steam steam://rungameid/1091500` → "Der Befehl 'steam' wurde nicht gefunden"

**Cause:** Steam is installed as Flatpak (`com.valvesoftware.Steam`). The binary lives inside the Flatpak sandbox at `/app/bin/steam`, not in host PATH. `prime-run` from host cannot see it.

**Solutions (in order of reliability):**

| Method | Command | Reliability |
|--------|---------|-------------|
| Steam Launch Options | `DXVK_FILTER_DEVICE_NAME="NVIDIA GeForce RTX 5060 Laptop GPU" %command%` | Best |
| Flatpak env passthrough | `flatpak run --env=__NV_PRIME_RENDER_OFFLOAD=1 --env=__GLX_VENDOR_LIBRARY_NAME=nvidia com.valvesoftware.Steam steam://rungameid/1091500` | May not propagate to Proton |
| Host prime-run + flatpak | `prime-run flatpak run com.valvesoftware.Steam ...` | Sandbox blocks host NVIDIA access |

### 3. Proton sees both GPUs but picks wrong one

**Symptom:** Proton log shows both Intel and NVIDIA devices, then crashes at OpenXR/Vulkan device extension query.

**Cause:** DXVK device enumeration fails when multiple Vulkan devices present and the right one isn't selected.

**Fix — Steam Launch Options (recommended):**
```
DXVK_FILTER_DEVICE_NAME="NVIDIA GeForce RTX 5060 Laptop GPU" %command%
```

**Fix — Direct Proton test:**
```bash
export DXVK_FILTER_DEVICE_NAME="NVIDIA GeForce RTX 5060 Laptop GPU"
export PROTON_LOG=1
/path/to/GE-ProtonXX/proton run /path/to/game.exe
```

**Note:** `DXVK_FILTER_DEVICE_NAME` filters at the DXVK layer (works for DX9/10/11 games via DXVK). For native Vulkan games, use `__NV_PRIME_RENDER_OFFLOAD=1` which works at the loader level.

### 4. Game appears "installed" but folder is empty (staging state)

**Symptom:** Steam shows game as installed, logs show `AppID 1091500 state changed : Fully Installed`, but game crashes immediately on launch. `steamapps/common/<GameName>/` doesn't exist or is empty.

**Cause:** Steam's staging system downloads to `steamapps/<title>/` (staging) before moving to `steamapps/common/`. If interrupted, the staging folder is empty but the manifest still says "Fully Installed".

**Detection:**
```bash
# Check if game folder exists in common:
ls /mnt/DATA/Programme/Steam/steamapps/common/ | grep -i <game>
# Check if staging folder is empty:
du -sh /mnt/DATA/Programme/Steam/steamapps/<Game Title>/
```

**Fix:** Reinstall the game through Steam (delete from library → reinstall).

## Diagnostic Workflow

When "games used to work, now they don't" on an Optimus laptop:

```
1. nvidia-smi                    → driver OK?
2. lsmod | grep nvidia            → module loaded?
3. env | grep __NV_/__GLX_        → Prime env poisoning?
4. which prime-run                → wrapper exists?
5. prime-run glxinfo | grep renderer → routes to NVIDIA?
6. glxinfo | grep renderer           → routes to iGPU? (should be iGPU on on-demand)
7. For Flatpak Steam:
   - Check Steam Launch Options for DXVK_FILTER_DEVICE_NAME
   - Check libraryfolders.vdf for staging vs common paths
8. For Proton crashes:
   - PROTON_LOG=1 → which device does it pick?
   - DXVK_FILTER_DEVICE_NAME="NVIDIA ..." in launch options
9. Check for empty staging folders
```

## Key Environment Variables

| Variable | Effect | When to use |
|----------|--------|-------------|
| `__NV_PRIME_RENDER_OFFLOAD=1` | Forces NVIDIA for OpenGL/Vulkan (host-level) | Non-Flatpak apps |
| `__GLX_VENDOR_LIBRARY_NAME=nvidia` | Forces NVIDIA GLX vendor | Same |
| `DXVK_FILTER_DEVICE_NAME="NVIDIA ..."` | Filters DXVK device enumeration | DX9/10/11 games via Proton |
| `DRI_PRIME=0` | Force iGPU | Debugging |
| `PROTON_LOG=1` | Proton debug log to `steam-*.log` | Any Proton crash |
| `PROTON_DISABLE_OPENXR=1` | Disable OpenXR in Proton | OpenXR crashes |

## Self-Service Fix Script Pattern

See `scripts/nvidia-prime-perf-fix.sh` in the user's home for a working example that:
1. Diagnoses (read-only snapshot)
2. Reinstalls `nvidia-driver-595-open` to restore `prime-run`
3. Sets `prime-select on-demand`
4. Sets `powerprofilesctl performance`
5. Adds userland `prime-run()` and `intel()` shell functions to `~/.bashrc`

## Pitfalls

1. **sudo from non-TTY:** Scripts using `sudo` fail in Hermes TUI (no PTY). Always instruct user to run in a real terminal (Ctrl+Alt+T) or use `--askpass` flag.

2. **`apt purge nvidia-driver-XXX` cascades to `nvidia-prime`:** The `nvidia-prime` package provides `prime-run`. Purging the driver removes it. Always reinstall `nvidia-driver-XXX-open` (not just `nvidia-driver-XXX`) to restore the prime wrapper.

3. **`nvidia-smi -pl` rejected on laptops:** EC controls power limit, `nvidia-smi -pl` returns `[N/A]`. This is by design on many laptop BIOSes, not a bug.

4. **`vulkaninfo` may not be installed:** Don't block diagnosis — check `/usr/share/vulkan/icd.d/nvidia_icd.json` directly.

5. **Steam ShaderCache GPU hash mismatch:** After GPU switching, Steam may show stale shader cache. It auto-rebuilds on next game launch.
