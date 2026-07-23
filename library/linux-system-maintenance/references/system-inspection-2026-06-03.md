# System Inspection — 2026-06-03

**Host:** ERAZER 17 P1, Zorin OS 18.1  
**Kernel:** 6.17.0-35-generic  
**CPU:** i7-13620H  
**GPU:** RTX 5060 Laptop (NVIDIA 595, PRIME=nvidia)  
**RAM:** 15 GB  
**Session Model:** DeepSeek V4 Flash  
**User:** Basti

## Scan Results

| Bereich | Befund | Potenzial |
|---------|--------|-----------|
| Platte | 466G / 607G (81%) | ~100 GB reclaimable |
| RAM | 7G used / 8.3G available | healthy |
| CPU Temp | 43°C | cool |
| Swap | 7.7G zram, 1.7G used | OK |

## Cleanup Actions Taken (same session)

After the initial scan, the following were executed (user-approved):

| Action | Size Reclaimed | Method |
|--------|---------------|--------|
| npm cache | **1.16 GB** | `npm cache clean --force` |
| pip cache | ~420 KB | `pip cache purge` |
| Thumbnails | **217 MB** | `rm -rf ~/.cache/thumbnails/*` |
| Orion (Warhammer game) | **14 GB** | `rm -rf ~/Downloads/Orion/` |
| Google Takeout (old export) | **14 GB** | `rm -rf ~/Dokumente/Takeout/` |
| Old kernel images (rc) | ~100 MB | `sudo dpkg --purge` (4 kernel versions) |
| Old NVIDIA modules (570/580) | ~100 MB | `sudo dpkg --purge` (11 packages) |
| rc package configs | minimal | `sudo dpkg --purge` (44→0) |
| steam-installer config | minimal | `rm postrm && sudo dpkg --purge --force-all` |
| APT cache | **139 MB** | `sudo apt clean` |
| Journal logs | **678 MB** | `sudo journalctl --vacuum-size=100M` |
| Orphaned /lib/modules/ dirs | minimal | `sudo rm -rf` (4 stale dirs) |
| **TOTAL** | **~30.4 GB** | **81% → ~72% disk usage** |

## Notable Workarounds Discovered

### 1. steam-installer postrm blocks non-interactive purge
The postrm script spawned a debconf whiptail dialog that failed without a full TTY.
Fix: remove postrm/prerm scripts, then `dpkg --purge --force-all`. Steam data in
`~/.steam/` was unaffected.

### 2. apt autoremove --purge is NOT sufficient for rc packages
`apt autoremove --purge` only cleans auto-installed no-longer-needed packages.
For explicit rc-state configs (kernel images, NVIDIA modules, i386 libs),
`dpkg --purge` on each package is required.

### 3. Module directories survive kernel image purge
After `dpkg --purge linux-image-*`, stale directories under `/lib/modules/` can
remain if they contain NVIDIA .ko files. Manual `sudo rm -rf` cleanup needed.

### 4. Mail Client Discovery
User said "Thunderbird" but actually uses **Evolution** with Gmail IMAP.
All emails are server-side on Gmail. No local mail files to clean.
**Always check systematically:**
```bash
dpkg -l | grep -iE "thunderbird|evolution|kmail|geary|claws|mutt"
ls ~/.thunderbird/ 2>/dev/null
ls ~/.config/evolution/sources/*.source
```

## Documentation Established
- `~/docs/system/README.md` — master system overview with specs, cleanup history
- `~/docs/builds/` — for project documentation
- `~/docs/scripts/` — for script documentation

## Commands Used for Inspection

```bash
# Disk + System
df -h / /home
free -h
sensors
uptime
swapon --show

# Package audit
apt list --upgradable 2>/dev/null | head -30
dpkg -l | grep -E 'linux-(image|headers|modules)'
dpkg -l | grep '^rc' | wc -l
dpkg -l | grep '^rc' | awk '{print $2, $3}' | head -20

# Cache sizes
du -sh /var/cache/apt/
du -sh ~/.npm/
du -sh ~/.cache/evolution/
journalctl --disk-usage

# Snap + Flatpak
snap list --all | grep disabled
flatpak list
flatpak uninstall --unused

# Mail client detection
dpkg -l | grep -iE "thunderbird|evolution|kmail|geary|claws|mutt"
ls ~/.thunderbird/ 2>/dev/null || echo "Kein .thunderbird"
ls ~/.config/evolution/sources/*.source

# Big directories
du -sh ~/*/ 2>/dev/null | sort -rh | head -15
```

## Tools Built This Session

After cleanup, three CLI tools were built, refined to v2.1, documented:

### sysdoctor v2.1 — `~/projects/sysdoctor/` → `~/bin/sysdoctor`
System check + cache cleanup tool. Stdlib-only.
- `--json` output, `--top N` dir scanner, `--dry-run` flag
- Uses `find + du -sb` instead of `du --exclude` for directory scanning
- `err_msg()` helper for sudo-required error messages

### greysync v2.1 — `~/projects/greysync/` → `~/bin/greysync`
Greyhack .src script deployer via SCP/SSH.
- `config` command: shows config + SSH key status + connectivity test
- `check` command: compares local vs remote (file presence + line count)
- `list` command: shows all .src files with KB size + total line count

### gmail-organizer v2.1 — `~/projects/gmail-organizer/` → `~/bin/gmail-organizer`
Gmail IMAP email organizer. Stdlib-only (imaplib).
- **Renamed** from `gmail-cleaner` per user request (softer branding)
- `show` command: preview with sender + subject before deleting
- `--quick` mode: scan only 500 mails for fast checks
- 25+ no-reply sender patterns (GitHub, GitLab, newsletters, alerts)
- App Password auth via `~/.gmail-organizer.json` (chmod 600)
- Dry-run default with `--for-real` flag to enable deletion
