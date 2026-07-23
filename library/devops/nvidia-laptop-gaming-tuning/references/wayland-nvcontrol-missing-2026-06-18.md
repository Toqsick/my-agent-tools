# Wayland Blocks NV-CONTROL X Extension — Discovery 2026-06-18

**Session:** GPU OC troubleshooting on RTX 5060 Laptop (Ubuntu Noble, GNOME)

## Discovery

User reported: nvidia-settings shows tiny menu, GWE crashes with "NV-CONTROL X not found".

Root cause found via `echo $XDG_SESSION_TYPE` → `wayland`. NV-CONTROL is a X11
extension that cannot exist under Wayland. This was NOT a package version issue
(despite libxnvctrl0 510 vs driver 595 mismatch being present too).

## Evidence

```
journalctl: com.leinardi.gwe.desktop[13091]: ERROR: NV-CONTROL missing!
xdpyinfo: (no NV-CONTROL in extension list, only GLX)
nvidia-settings: shows only basic info, no GPU-OC controls
XDG_SESSION_TYPE=wayland
```

## Key Insight

Two separate issues were layered:
1. **Wayland session** → NV-CONTROL X extension cannot exist → GUI OC broken
2. **libxnvctrl0 510 vs driver 595** → even under X11, nvidia-settings version
   mismatch would cause problems (but is secondary to the Wayland issue)

## Resolution Path

- Immediate: `sudo nvidia-smi -pl 115` for power limit (works under Wayland)
- GUI OC: Switch to X11 session at GDM login
- nvidia-settings + GWE: Work under X11 with Coolbits 28 OutputClass

## Hardware Context

- RTX 5060 Laptop (Device 2d19, Blackwell), driver 595.71.05
- Ubuntu Noble, GNOME + Mutter (Wayland default)
- nvidia-powerd as System-Unit (working)
- nvreg_fix.conf with OpenRmEnableUnsupportedGpus=1 (required, do NOT delete)
