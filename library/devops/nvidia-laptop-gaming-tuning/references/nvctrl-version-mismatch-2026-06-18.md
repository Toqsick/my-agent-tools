# NV-CONTROL X Extension Version Mismatch — RTX 5060 Laptop

**Date:** 2026-06-18
**Symptom:** GWE crashes with "NV-CONTROL X not found", nvidia-settings shows empty/minimal UI

## Root Cause

Ubuntu Noble packages `nvidia-settings` (510.47.03) and `libxnvctrl0` (510.47.03)
from the `nvidia-settings` source package, while the driver is `nvidia-driver-595-open`
(595.71.05). The NV-CONTROL X extension ABI is major-version-sensitive — 510's
libXNVCtrl.so cannot communicate with the 595 driver's X extension.

## Evidence

```
$ xdpyinfo | grep -i nv
(nothing — NV-CONTROL extension not loaded)

$ nvidia-settings --version
nvidia-settings: version 510.47.03

$ nvidia-smi --query-gpu=driver_version --format=csv,noheader
595.71.05

$ dpkg -l libxnvctrl0
ii  libxnvctrl0:amd64  510.47.03-0ubuntu4.24.04.1

$ dpkg -l nvidia-settings
ii  nvidia-settings  510.47.03-0ubuntu4.24.04.1
```

## Workaround: nvidia-smi Direct OC

Works immediately, no X extension needed:
```bash
# Check supported clocks:
nvidia-smi -q -d SUPPORTED_CLOCKS

# Set power limit to max:
sudo nvidia-smi -pl 115

# Set GPU + VRAM application clocks:
sudo nvidia-smi -ac 12001,3090

# Reset:
sudo nvidia-smi -rac
```

**⚠️ Driver 595 update:** `nvidia-smi -ac` returns "The requested functionality has been deprecated" on driver 595. The old Application Clocks API is deprecated in newer drivers. This means the only remaining CLI OC path is `nvidia-smi -pl` (power limit), which may also be blocked by laptop EC (see ec-power-capping reference). For full OC under driver 595, X11 + Coolbits + nvidia-settings GUI is the reliable path.

## Full Fix Options

1. **NVIDIA .run installer** — downloads matching nvidia-settings + libxnvctrl
   from NVIDIA directly. Most reliable but requires stopping X.
2. **Wait for Ubuntu update** — nvidia-settings 595 may land in noble-updates
   once NVIDIA releases it.
3. **Build from source** — nvidia-settings source tarball from NVIDIA,
   linked against the 595 driver's libXNVCtrl.

## Status

- Coolbits OutputClass (`/etc/X11/xorg.conf.d/10-nvidia-coolbits.conf`) was
  NOT applied — `sudo tee` failed on password rejection during previous session.
  User needs to run manually.
- Even with Coolbits applied, nvidia-settings 510 won't show OC sliders
  until libxnvctrl0 is upgraded to 595.
- nvidia-smi workaround is the only OC path that works right now.
