# WLAN Activation Trace — 2026-07-04

Platform: Ubuntu 24.04, Intel Raptor Lake PCH CNVi WiFi (8086:51f1)
Interface: wlp0s20f3, `iwlwifi` driver
State: RFKill soft-blocked, NM radio off, previously connected to FRITZ!Box 5590 XC

## Initial State

```
rfkill list:
  0: hci0: Bluetooth — Soft blocked: yes, Hard blocked: no
  1: phy0: Wireless LAN — Soft blocked: yes, Hard blocked: no

nmcli radio:
  WIFI-HW: aktiviert, WIFI: deaktiviert

ip link show wlp0s20f3:
  DOWN
```

## Fix (3 commands, 0 sudo)

```bash
rfkill unblock wifi        # → Soft blocked: no, ohne sudo
nmcli radio wifi on        # → WIFI: aktiviert, ohne sudo
nmcli connection up "FRITZ!Box 5590 XC"   # → 192.168.178.91/24
```

## Result

```
wlp0s20f3        UP             192.168.178.91/24
nmcli general:   verbunden · vollständig
Ping 8.8.8.8:    9.6 ms
```

## Dual-Stack Config

Both LAN (`enp3s0`, 192.168.178.92, metric 100) and WLAN (192.168.178.91, metric 600) active.
LAN is the default route (lower metric) — WLAN acts as backup.

## Key Observations

1. **`rfkill unblock wifi` works without sudo** — PolicyKit grants `CAP_NET_ADMIN` to local user for rfkill operations. No PAM/TTY needed.
2. **`nmcli radio wifi on` works without sudo** — D-Bus interface at `/org/freedesktop/NetworkManager` allows user-session process to enable radios.
3. **`nmcli connection up` works without sudo** — user-owned connections in NM's `settings/plugins/keyfile` are accessible via user's D-Bus session. No root needed.
4. **Password was pre-saved** — the FRITZ!Box connection had `802-11-wireless-security.psk` already set from prior setup. No interactive prompt needed.
5. **bluetooth soft-blocked was NOT cleared** — user may not want BT; `rfkill unblock wifi` only affects `phy0`, not `hci0`.

## FRITZ!Box 5590 XC Connection Details

- UUID: `1bcfd4a2-1ae4-45a5-bcfa-ee66a658c256`
- Saved: yes (autoconnect: ja, priority: 0)
- Type: 802-11-wireless
- Interface: wlp0s20f3
- 5 GHz visible: channels 52 (40%), 100 (44%), 116 (49%), 132 (51%), 140 (30%)
- 2.4 GHz visible: channel 11 (51%)
