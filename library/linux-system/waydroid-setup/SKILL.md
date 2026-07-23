---
name: waydroid-setup
title: Waydroid Setup & Repair (Android Container on Linux)
description: "Use when user asks for Waydroid Android container setup on Linux, Waydroid install/repair lifecycle, Android-in-Linux container. NOT for full Android emulation, Genymotion, or non-Linux Android. Full lifecycle for Waydroid Android containers on Linux desktops."
triggers:
- User asks about Waydroid, Android on Linux, or containerized Android
- 'Waydroid shows ''Session: STOPPED'' or ''Container: STOPPED'''
- binder devices (/dev/binder*) missing on Wayland+NVIDIA
- cgroup2 v2 migration issues with LXC containers
- Android apps have no network inside Waydroid
version: 1.0.0
author: Yuno
license: MIT
lane: worker-flash
reasoning_effort: xhigh
trigger_keywords: ['android', 'linux', 'waydroid', 'container', 'lifecycle']
keywords: ['android', 'linux', 'waydroid', 'container', 'lifecycle']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['imessage']
---

# Waydroid Setup & Repair

## Overview

Waydroid runs a full Android system in an LXC container on Linux using kernel binder/IPC namespaces. It works on Wayland and X11, but **proprietary NVIDIA GPUs on Wayland** introduce specific quirks.

## Architecture

```
Host Linux
  ├── Wayland compositor (GNOME/KDE/Sway) ← wayland-0 socket
  ├── LXC container 'waydroid' (systemd-free, cgroup2)
  │   ├── Android init (zygote64 + zygote)
  │   ├── servicemanager / hwservicemanager / vndservicemanager
  │   ├── surfaceflinger (Android display compositor)
  │   └── Android apps (via APEX/APK)
  ├── waydroid0 bridge (192.168.240.1/24)
  │   └── dnsmasq DHCP (192.168.240.2-254)
  └── binder_linux kernel module
      └── /dev/anbox-binder, /dev/anbox-vndbinder, /dev/anbox-hwbinder
```

## Prerequisites

- Linux kernel with `CONFIG_ANDROID_BINDER_IPC` (all major distros since 5.x)
- LXC installed (`lxc-info --version`)
- Waydroid package installed (`waydroid --version`)
- Android system/vendor images in `/etc/waydroid-extra/images/`

## Installation

```bash
# Ubuntu/Debian
sudo apt install waydroid lxc python3-gbinder

# Download Android images (if not bundled)
sudo waydroid init -s GAPPS   # with Google Play
# or
sudo waydroid init -s VANILLA # without Google Play
```

## Session Lifecycle

| State | Meaning | Common Fix |
|-------|---------|-----------|
| Session: RUNNING | Waydroid session daemon alive | OK |
| Session: STOPPED | Daemon not running | `waydroid session start` or `sudo systemctl restart waydroid-container.service` |
| Container: RUNNING | LXC guest booted | OK |
| Container: STOPPED | LXC guest not booted | Start session or check binder/cgroup |
| IP address: UNKNOWN | Network not configured inside container | Check dnsmasq, waydroid0 bridge |

Check status: `waydroid status`

## Critical Pitfalls

### 1. binder Devices Missing (NVIDIA Wayland)

The most common reason Waydroid won't start on NVIDIA Wayland:

```bash
# Check if module is available
find /lib/modules/$(uname -r) -name 'binder_linux*'
ls /dev/binder* /dev/anbox* 2>&1
lsmod | grep binder

# Load module
sudo modprobe binder_linux
ls -la /dev/binder* /dev/anbox*
```

Expected after successful modprobe:
```
/dev/anbox-binder    (crw-rw----)
/dev/anbox-vndbinder (crw-rw----)
/dev/anbox-hwbinder  (crw-rw----)
```

If devices appear but Waydroid still can't find them, the Waydroid LXC config needs explicit `lxc.mount.entry` lines (see reference file).

### 2. cgroup2 v2 Mount

Modern distros (Ubuntu 24.04+) use cgroup v2. LXC containers often need:

```bash
# Check current cgroup version
stat -fc %T /sys/fs/cgroup/  # cgroup2fs = v2

# If Waydroid container fails with cgroup errors, add to kernel cmdline:
# systemd.unified_cgroup_hierarchy=1 cgroup_no_v1="all"
# (Usually already set; check /etc/default/grub)
```

On NVIDIA Wayland, `/sys/fs/cgroup` may need proper delegation for the LXC container. The LXC config in `/var/lib/waydroid/lxc/waydroid/config` should NOT be modified manually — use waydroid's config mechanism instead.

### 3. Host Permissions XML (Wayland Socket)

Waydroid needs access to the Wayland display socket. This is handled by `waydroid session start` but can fail if the `host-permissions` XML was not created:

```bash
ls -la /var/lib/waydroid/host-permissions/
```

Expected file: `1000.xml` or `1000-wayland.xml` containing `wayland-0` socket access. If missing, Waydroid's Android services can't register, and `servicemanager`, `hwservicemanager` show as DOWN.

### 4. GPU Acceleration (NVIDIA)

NVIDIA GPUs on Wayland:
- **No Vulkan support inside Waydroid** (NVIDIA doesn't expose virtio-gpu or venus to LXC guests)
- **Software rendering** is the default (mesa/swrast inside Android)
- `waydroid prop set persist.waydroid.multi_windows true` enables multi-window mode (apps as separate Wayland toplevels)
- Multi-window works without GPU acceleration — each app gets its own XDG surface
- 3D/gaming inside Android will NOT work on NVIDIA Wayland — use software rendering for app testing

### 5. Sudo-Only Operations

In a non-interactive agent environment (Hermes TUI), these **must be copy-pasted by the user**:

```bash
sudo -v  # once to cache credentials
bash /path/to/waydroid-reboot-script.sh  # then run
```

Commands that require root:
- `systemctl restart waydroid-container.service`
- `modprobe binder_linux`
- `lxc-attach` (for container shell access)
- Editing `/etc/modules-load.d/` for persistent module loading
- Editing LXC config in `/var/lib/waydroid/lxc/`

## Complete Repair Sequence

When Waydroid shows `Session: STOPPED` or `Container: STOPPED`, follow this order:

### Phase 1 — Kernel Module

```bash
# Persistent binder_linux
echo "binder_linux" | sudo tee /etc/modules-load.d/binder_linux.conf
sudo modprobe binder_linux
ls /dev/anbox-*
```

### Phase 2 — LXC Mount Entries

If binder devices exist on host but container doesn't see them, add to `/var/lib/waydroid/lxc/waydroid/config`:

```
lxc.mount.entry = /dev/anbox-binder dev/anbox-binder none bind,create=file 0 0
lxc.mount.entry = /dev/anbox-vndbinder dev/anbox-vndbinder none bind,create=file 0 0
lxc.mount.entry = /dev/anbox-hwbinder dev/anbox-hwbinder none bind,create=file 0 0
```

Then restart: `sudo systemctl restart waydroid-container.service`

### Phase 3 — Service Restart

```bash
sudo systemctl restart waydroid-container.service
sleep 4
waydroid status  # should show RUNNING/RUNNING
```

If it fails, check: `journalctl -u waydroid-container.service --no-pager -n 50`

### Phase 4 — Network Verification

```bash
# Host side
ip -br addr show waydroid0
# Should show: 192.168.240.1/24

# Inside container
sudo lxc-attach -P /var/lib/waydroid/lxc -n waydroid -- ip route show
sudo lxc-attach -P /var/lib/waydroid/lxc -n waydroid -- timeout 6 ping -c 2 8.8.8.8

# DNS
sudo lxc-attach -P /var/lib/waydroid/lxc -n waydroid -- getprop net.dns1
```

### Phase 5 — UI Launch

```bash
WAYLAND_DISPLAY=wayland-0 XDG_SESSION_TYPE=wayland waydroid show-full-ui &
```

## Network Architecture

| Component | Value |
|-----------|-------|
| Bridge IP | `192.168.240.1/24` |
| DHCP range | `192.168.240.2 - 254` |
| dnsmasq PID | `/run/waydroid-lxc/dnsmasq.pid` |
| DHCP leases | `/var/lib/misc/dnsmasq.waydroid0.leases` |
| Container gets | `192.168.240.x` via DHCP, internet via host NAT |

## Verification Checklist

- [ ] `waydroid status` shows `Session: RUNNING, Container: RUNNING`
- [ ] `/dev/anbox-binder` exists
- [ ] `waydroid0` is UP with `192.168.240.1/24`
- [ ] Container can ping `192.168.240.1` (host bridge)
- [ ] Container can ping `8.8.8.8` (internet via NAT)
- [ ] `waydroid show-full-ui` opens Android window
- [ ] Apps with `multi_windows=true` appear as separate Wayland surfaces
