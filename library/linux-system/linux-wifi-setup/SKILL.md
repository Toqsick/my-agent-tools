---
name: linux-wifi-setup
title: Linux WLAN / WiFi Setup & Troubleshooting
description: "Use when user asks for activating/troubleshooting Linux WiFi, WLAN connection issues, rfkill/networkmanager diagnostics. NOT for non-WiFi networking or non-Linux WiFi setup. Activate, connect, and troubleshoot WLAN on Linux desktops."
triggers:
- User asks to enable or connect WiFi
- WLAN interface shows DOWN despite hardware being present
- rfkill shows soft-blocked WLAN
- User wants to switch from LAN to WLAN for connectivity
- nmcli shows WIFI deactivated or no access points visible
version: 1.0.0
author: Yuno
license: MIT
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['linux', 'wifi', 'wlan', 'linux-wifi-setup', 'activating']
keywords: ['linux', 'wifi', 'wlan', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

# Linux WLAN / WiFi Setup & Troubleshooting

## Quick Start (3 commands, no sudo needed)

```bash
rfkill unblock wifi        # Soft-Block aufheben (PolicyKit — kein sudo)
nmcli radio wifi on        # NetworkManager WLAN aktivieren (D-Bus — kein sudo)
nmcli connection up "SSID" # Gespeichertes Netz verbinden
```

Diese 3 Befehle lösen **90% der WLAN-Probleme** ohne root.

## Architecture

```
User Request
  ├── rfkill unblock wifi    → Kernel: remove soft-block flag
  │                            (PolicyKit automatically grants for local user)
  ├── nmcli radio wifi on    → NetworkManager: enable WiFi radio
  │                            (D-Bus, user session has permission)
  └── nmcli connection up    → NetworkManager: activate saved connection
                               (user's own connections always accessible)
```

## Diagnostic Flow

### Step 1 — RFKill Status

```bash
rfkill list
# Look for "Soft blocked: yes" on phy0 (WLAN)
```

Fix: `rfkill unblock wifi` (no sudo needed)

### Step 2 — NetworkManager Radio

```bash
nmcli radio
# Shows: WIFI-HW, WIFI, WWAN-HW, WWAN
# If WIFI is "deaktiviert" — nmcli radio wifi on
```

### Step 3 — Interface Status

```bash
ip -br link show
# Look for wlp* interface
# If DOWN — check rfkill + radio
# If UP,LOWER_UP — interface is ready
```

### Step 4 — Saved Networks

```bash
nmcli connection show                      # all connections
nmcli connection show --active             # only active ones
nmcli -t -f NAME,UUID,DEVICE,STATE connection show --active
```

### Step 5 — Scan Available Networks

```bash
nmcli device wifi
# Columns: SSID, FREQ, SIGNAL, SECURITY, BARS
```

### Step 6 — Connect

```bash
# To saved network:
nmcli connection up "FRITZ!Box 5590 XC"

# To new network (saves password):
nmcli device wifi connect "MyWiFi" password "secret123"
```

## Dual-Stack Routing (LAN + WLAN)

When both interfaces are UP:

```
default via 192.168.178.1 dev enp3s0  metric 100   — LAN (primary)
default via 192.168.178.1 dev wlp0s20f3 metric 600  — WLAN (backup)
```

- **Lower metric wins** for outbound traffic
- Use case: LAN as primary (stable), WLAN as fallback
- To switch: `nmcli connection modify <name> ipv4.route-metric <value>`

## Verification

```bash
# IP address
ip -br addr show wlp0s20f3

# Ping gateway
ping -c 2 -W 2 192.168.178.1

# Ping internet
ping -c 2 -W 2 8.8.8.8

# Connection state + connectivity
nmcli general
```

## Common Hardware Classes

| Hardware | Interface | Chipset Driver | Notes |
|----------|-----------|---------------|-------|
| Intel Raptor Lake PCH CNVi | `wlp0s20f3` | `iwlwifi` | ax201/ax211, excellent Linux support |
| Intel AX200/AX210 | `wlp0s20f3` | `iwlwifi` | CNVi not needed, works OOTB |
| Realtek RTL88xxx | `wlpxxxx` | `r8a88x` | May need firmware, check `dmesg` |
| Broadcom BCM43xx | varies | `b43`/`wl` | Problematic, may need proprietary driver |

## Pitfalls

1. **rfkill hard block** (`Hard blocked: yes`) — physical switch or Fn key. No software fix. Common on laptops with airplane mode toggle.
2. **nmcli connection up fails with "Secrets were required"** — password not stored. Use `nmcli connection modify <name> 802-11-wireless-security.psk <password>` first.
3. **Connected but no internet** — check DNS: `nmcli device show wlp0s20f3 | grep DNS`
4. **WLAN disconnects after suspend** — NetworkManager `wifi.powersave = 2` (disable power save). Fix: `nmcli connection modify <name> 802-11-wireless.powersave 2`
5. **Interface shows but can't scan** — firmware issue. Check `dmesg | grep iwl` or `journalctl -k | grep wifi`

## Sudo-Free vs Sudo

| Command | Needs Sudo? | Mechanism |
|---------|------------|-----------|
| `rfkill unblock wifi` | **No** | PolicyKit (local user) |
| `nmcli radio wifi on` | **No** | D-Bus session permissions |
| `nmcli connection up` | **No** | User owns saved connections |
| `nmcli device wifi connect` | **No** | Creates new connection as user |
| `systemctl restart NetworkManager` | **Yes** | System service management |
| `iw dev wlp0s20f3 scan` | **Yes** | Kernel-level scan trigger |
