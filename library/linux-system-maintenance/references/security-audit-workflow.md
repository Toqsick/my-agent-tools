# Desktop Linux Security Audit Workflow

> Built 2026-06-03 during Basti's maintenance session (DeepSeek V4 Flash).
> System: Zorin OS 18.1 (GNOME/X11), Erazer 17 P1, RTX 5060.

## When to Run

- User asks for "sicherheitscheck", "security audit", "was ist offen"
- After discovering unknown services during system maintenance
- After installing/messy-uninstalling software that may have left services behind
- Before exposing the machine to a new network

## Audit Checklist

### Phase 1: Inventory — What's Running and Open

```bash
# 1. SSH — is there a server?
systemctl is-active sshd
ss -tlnp | grep :22

# 2. Firewall — is it actually blocking?
sudo ufw status verbose

# 3. All listening ports (focus on 0.0.0.0:* and :::*)
ss -tlnp | grep -E "0.0.0.0:|:::|:\*"

# 4. All SYSTEMD services running
systemctl list-units --type=service --state=running | head -40

# 5. User-level services (GNOME, Rygel, etc.)
systemctl --user list-units --type=service --state=running | head -20
```

**Critical filter:** Ports binding on `0.0.0.0` or `::` are reachable from the
entire network. Localhost-only (`127.0.0.1` or `::1`) is safe.

### Phase 2: File Permission Scan

```bash
# Config files with credentials
ls -la ~/.gmail-organizer.json   # Should be 600
ls -la ~/.greysync.json          # Should be 600
ls -la ~/.hermes/config.yaml     # Should be 600
ls -la ~/.ssh/                   # Should be 700, keys 600

# Any world-readable sensitive files in home
find ~ -maxdepth 3 -type f -perm -o+r ! -name "*.py" ! -name "*.md" \
  ! -name "*.txt" ! -name "*.desktop" ! -name "*.png" 2>/dev/null | head -20
```

### Phase 3: Users, Sudoers, and Password Policies

```bash
# All users with shell access
sudo cat /etc/passwd | grep -E "/bin/bash|/bin/zsh|/bin/sh"

# Empty passwords (dangerous!)
sudo awk -F: '($2==""){print $1}' /etc/shadow

# Sudo NOPASSWD entries (should be rare/none for normal users)
sudo cat /etc/sudoers | grep -i NOPASSWD
sudo cat /etc/sudoers.d/* | grep -i NOPASSWD

# Password hashing algorithm
grep pam_unix /etc/pam.d/common-password | head -1
# yescrypt = good, md5 = bad, sha512 = acceptable
```

### Phase 4: Network Service Audit

Common services that shouldn't listen on 0.0.0.0 without reason:

| Service | Port | Expected | Action if running unnecessarily |
|---------|------|----------|-------------------------------|
| **gnome-remote-desktop** | 3389 | Localhost only or disabled | `sudo ufw deny 3389/tcp && sudo ufw allow from 127.0.0.1 to any port 3389` |
| **Rygel (DLNA)** | dynamic | User-dependent | `systemctl --user stop rygel && systemctl --user disable rygel` |
| **ssh** | 22 | Disabled or firewalled | `sudo systemctl disable --now ssh` |
| **CUPS** | 631 | Localhost only | Usually fine on localhost |
| **Ollama** | 11434 | Localhost only | Check for crash-loop: `systemctl status ollama` |
| **Steam** | 27036 | Network (LAN games) | Expected for gaming |

### Phase 5: Service Health

```bash
# Find crash-looping services (auto-restart loops)
systemctl list-units --type=service --state=failed
systemctl list-units --type=service --state=activating

# Check for services that keep restarting
sudo journalctl -u <service-name> --since "1 hour ago" | grep -c "Started\\|Failed" | tail -5
```

## Localhost-Restriction via UFW (GNOME Remote Desktop Pattern)

When a service MUST bind on 0.0.0.0 (can't change its config) but should
only be reachable from localhost:

```bash
# 1. Deny from everywhere
sudo ufw deny 3389/tcp

# 2. Allow from localhost specifically
sudo ufw allow from 127.0.0.1 to any port 3389 proto tcp

# 3. Also add IPv6 deny
sudo ufw deny 3389/tcp  # also adds v6 rule

# 4. Verify
sudo ufw status numbered
# [1] 3389/tcp    DENY IN    Anywhere
# [2] 3389/tcp    ALLOW IN   127.0.0.1
# [3] 3389/tcp    DENY IN    Anywhere (v6)
```

**UFW applies rules in order:** the first match wins. Since DENY is rule 1
and ALLOW is rule 2, the DENY from Anywhere is checked first for any non-localhost
connection. Localhost connections match rule 2 (ALLOW) and skip rule 1.

## Disposal Decision Tree for Services

```
Service found running
├── Do I know what it is?
│   ├── Yes
│   │   ├── Do I use it?  → Keep
│   │   └── No             → Disable + ask user
│   └── No
│       ├── Research service
│       ├── Is it needed?  → Keep with localhost restriction
│       └── No             → Disable safely
│
└── ALWAYS ask the user before disabling:
    "Rygel (DLNA Media Sharing) läuft — brauchst du's?"
```

**Never disable a service without asking first.** The user may rely on it
even if they didn't explicitly mention it.

## Documentation After Security Audit

Write results to `~/docs/system/security.md` with:

- Audit date and tool/version used
- List of all findings (good and bad)
- Quick-wins table (action taken, result, verification method)
- UFW rules added (exact commands and verification)
- Services disabled/enabled (exact commands)
- Open questions / "ask user" items
- Before/after port exposure summary

## Common Findings on Gaming Desktops (Zorin OS / Ubuntu)

1. **gnome-remote-desktop** — enabled by default in GNOME Settings → Sharing.
   Listens on 0.0.0.0:3389. Most users don't know it's running.
   Fix: restrict via UFW (see above).

2. **Rygel** — GNOME's DLNA media server. Starts automatically. If user
   doesn't stream media to TV/console, stop and disable it.

3. **Ollama crash-loop** — If Ollama.service keeps restarting, it may be
   a version mismatch or corrupted model. Check: `journalctl -u ollama`.
   Fix: `sudo systemctl disable --now ollama`.

4. **Steam ports** — steam.exe opens several ports for LAN game discovery
   and Remote Play. Normal behavior. Ports on 0.0.0.0:27036 are expected.

5. **Flatpak with many runtimes** — Each runtime adds >100MB. Pinned
   Zorin theme runtimes can consume 1+ GB. Reclaim: remove unused themes
   or switch to a single theme.

## Pitfalls

1. **Don't disable without asking.** Services like gnome-remote-desktop
   might be used for remote support.
2. **UFW rules are order-dependent.** Always verify with `ufw status numbered`.
3. **systemctl --user vs systemctl.** Rygel and other GNOME services run
   under the USER systemd instance, not system-wide. Use `--user` flag.
4. **Symlinks in ~/.ssh** can look like keys but may point to mounted
   volumes. Check with `file ~/.ssh/*` to distinguish real keys.
5. **Ollama crash-loop may be transient.** A single Python process crash
   shouldn't trigger service disable. Check logs for frequency first.
6. **Chmod 600 on credential files** — this is correct but the USER's
   group can still read them if the user's home directory is 755 and
   group permissions are generous. Modern Ubuntu defaults are fine.
