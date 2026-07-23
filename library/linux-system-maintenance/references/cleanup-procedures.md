# Cleanup Procedures — Detailed Reference

Concrete commands, orderings, and workarounds for Linux cleanup tasks. Loaded on demand
from the slim `SKILL.md` when the user asks for actual cleanup (not just scan).

## rc Package Purge — Critical Ordering

`apt autoremove --purge` does NOT clean rc-state packages (removed-but-config-lingers).
You MUST use explicit `dpkg --purge` for rc packages, in this specific order to avoid
NVIDIA module-dir blocks:

```bash
# Step 1: Identify ALL rc packages
dpkg -l | grep '^rc' | awk '{print $2}'

# Step 2: Purge old kernel images FIRST (their module dirs may block)
sudo dpkg --purge linux-image-6.14.0-37-generic linux-image-6.17.0-20-generic

# Step 3: Then purge kernel modules + extras
sudo dpkg --purge linux-modules-* linux-modules-extra-*

# Step 4: Then NVIDIA old-driver modules
sudo dpkg --purge $(dpkg -l | grep '^rc' | grep -E 'nvidia-(570|580)' | awk '{print $2}')

# Step 5: Clean up orphaned module directories under /lib/modules/
# (may contain NVIDIA module remnants that the purge left behind)
sudo rm -rf /lib/modules/6.14.0-37-generic /lib/modules/6.17.0-20-generic

# Step 6: Purge ALL remaining rc packages (non-kernel)
dpkg -l | grep '^rc' | awk '{print $2}' | xargs sudo dpkg --purge
```

This ordering avoids problems where a kernel module dir references a driver package
that was already in rc state but `dpkg --purge` on the kernel image couldn't rmdir
the module directory because of leftover NVIDIA `.ko` files.

## Kernel Cleanup Rule

Keep only the **current kernel** (from `uname -r`) plus **one backup**. Purge all
others including rc-state package configs:

```bash
# Remove installed old kernel (example: keep 6.17.0-35, remove 6.17.0-29)
sudo apt purge linux-image-6.17.0-29-generic linux-headers-6.17.0-29-generic

# Purge rc-state old kernels + NVIDIA modules
sudo dpkg --purge linux-image-6.14.0-37-generic linux-image-6.17.0-20-generic
sudo dpkg --purge linux-image-6.17.0-22-generic linux-image-6.17.0-23-generic
sudo dpkg --purge linux-modules-6.14.0-37-generic linux-modules-6.17.0-20-generic
sudo dpkg --purge linux-modules-6.17.0-22-generic linux-modules-6.17.0-23-generic
sudo dpkg --purge linux-modules-extra-6.14.0-37-generic linux-modules-extra-6.17.0-20-generic
sudo dpkg --purge linux-modules-extra-6.17.0-22-generic linux-modules-extra-6.17.0-23-generic

# Clean up old NVIDIA modules (570/580 after GPU driver update to 595)
for pkg in $(dpkg -l | grep '^rc' | grep -E 'nvidia-(570|580)' | awk '{print $2}'); do
  sudo dpkg --purge "$pkg"
done

# Purge all remaining rc-packages in one pass
dpkg -l | grep '^rc' | awk '{print $2}' | xargs sudo dpkg --purge

# Clean APT
sudo apt clean && sudo apt autoremove --purge
```

## steam-installer Purge Workaround

The `steam-installer` package's postrm script launches a debconf dialog that
requires a terminal (whiptail). When purging from a non-interactive context
(CLI without full TTY), this fails with error 255 and the package stays in `pc`
state.

**Fix: remove the postrm script, then force-purge:**

```bash
sudo rm -f /var/lib/dpkg/info/steam-installer.postrm
sudo rm -f /var/lib/dpkg/info/steam-installer.prerm
sudo dpkg --purge --force-all steam-installer
```

This does NOT affect Steam's actual data — that lives in `~/.steam/` and is
unaffected by package management. The user's games and configurations are safe.

## Log & Cache Audit

```bash
# Journal size
journalctl --disk-usage

# Reduce to 7 days
sudo journalctl --vacuum-time=7d

# APT cache size
du -sh /var/cache/apt/

# npm cache
du -sh ~/.npm/
# npm cache clean --force  # Reclaims 1+ GB

# Snap: find disabled revisions
snap list --all | grep disabled
# snap remove <name> --revision <n>  # for each disabled revision

# Flatpak: remove unused runtimes
flatpak uninstall --unused

# Evolution mail profile (Gmail IMAP → server-side, local cache minimal)
ls ~/.config/evolution/sources/*.source
du -sh ~/.cache/evolution/

# Home directories sorted by size
du -sh ~/*/ 2>/dev/null | sort -rh | head -15
```

**Key insight for Evolution/Gmail:** If Evolution is configured with an IMAP
account (e.g., Gmail), all messages live on the server. The local cache
(`~/.cache/evolution/`) is tiny and safe to delete. For actual email cleanup
(delete old no-reply mails, spam >5 years), build a Gmail IMAP cleanup tool
using `imaplib` (stdlib only). See `references/gmail-imap-cleanup.md` for
the full pattern: connection, search, categorize, no-reply patterns, delete
workflow, Evolution detection, and pitfalls.

## Mail Client Detection (common mixup)

Users often say "Thunderbird" when they actually use a different client.
Check systematically:

```bash
# 1. Is Thunderbird installed?
which thunderbird
# 2. Check Thunderbird profile dirs
ls ~/.thunderbird/
ls ~/snap/thunderbird/common/.thunderbird/
ls ~/.var/app/org.mozilla.thunderbird/
# 3. Check other mail clients
dpkg -l | grep -iE "thunderbird|evolution|kmail|geary|claws|mutt"
flatpak list | grep -iE "mail|thunder"
snap list | grep -iE "mail|thunder"
```

**Common findings:**
- **Evolution** (GNOME) with Gmail IMAP → mails on Gmail servers, not local
- **Thunderbird** can use local mbox or IMAP cache → check `Mail/` or `ImapMail/`

## Documentation After Cleanup

After every maintenance session, write results to `~/docs/system/README.md`:

- Date, action taken, size reclaimed
- Current disk usage (before → after)
- Any surprises or workarounds discovered
- Open items for next session

The user expects `~/docs/` as a living knowledge base for everything built or fixed.
Structure: `~/docs/system/` (maintenance), `~/docs/builds/` (projects), `~/docs/scripts/` (scripts).

## Presentation to User (after inspection)

Present findings in a structured table:

```
## Ergebnis
| Bereich        | Befund              | Potenzial    |
|----------------|---------------------|--------------|
| Platte         | 466G / 607G (81%)   | ~100 GB reclaimable |
| APT cache      | 139 MB              | run `apt clean` |
| ...            | ...                 | ...          |
```

Always include concrete actions ("run X to reclaim Y"), not just observations.

## Steam Cleanup Targets

| Target              | Path                          | Root? | Notes                                       |
|---------------------|-------------------------------|-------|---------------------------------------------|
| Steam Backups       | `steamapps/*.csd`, `*.csm`    | ❌    | Already compressed, do NOT re-pack          |
| Steam Installations | `steamapps/common/`           | ❌    | Can be removed if `.csd` backups exist      |
| Steam Downloads     | `steamapps/downloading/`      | ❌    | Incomplete downloads, safe to delete        |
| Steam Shader Cache  | `steamapps/shadercache/`      | ❌    | Regenerates, often 10-50 GB                 |
| Steam Recordings    | `steamapps/Recordings/`       | ❌    | `.m4s` fragments, archive then delete       |
| Steam Logs          | `~/.steam/steam/logs/`        | ❌    | Safe after closing Steam                    |

## Gaming Storage Toolkit Extension

For users with large Steam/Game libraries on external drives, a companion toolkit
helps manage backups, installations, and recordings separately from system cleanup.

**Architecture:**

```
steam_backup_toolkit/
├── steam_inventory.py      # Lists .csd/.csm backups + common/ installations
├── steam_archive.py        # Archives installations with zstd (optional)
└── data_cleanup.py         # Disk-wide analysis: Trash, Recordings, Backups
```

**Key patterns:**
- Mount external drives by UUID but symlink `/mnt/DATA` for user-friendly paths.
- Steam `.csd`/`.csm` files are already compressed — don't re-compress them.
- The `common/` directory contains unpacked installations that can be removed
  if `.csd` backups exist (Steam can restore them).
- Steam Recordings (`steamapps/Recordings/`) are often `.m4s` fragments that
  can be archived to `tar.zst` and then deleted to reclaim 5-10 GB.
- `.Trash-1000/` on external drives can hold **80+ GB** of deleted game files
  that the user forgot to empty.

**Workflow:**
1. `steam_inventory.py` → show what's backup vs installation
2. `data_cleanup.py --analyze` → find Trash, Recordings, duplicates
3. `data_cleanup.py --archive-recordings --method zstd_fast` → pack recordings
4. `data_cleanup.py --empty-trash` → reclaim massive space

## Firmware & Hardware Security Audits

When a user shares a `fwupdmgr security` report (or `Device Security Report.txt`),
interpret the HSI levels and propose concrete fixes. Load
`references/security-hardening.md` for the full playbook.

**Quick decision tree:**
1. `Linux Swap: Fail` → suggest ZRAM replacement (safer + faster)
2. `Suspend To RAM: Fail` → suggest s2idle (trade-off: battery life)
3. `Linux Kernel Verification: Fail (Verdorben)` → check taint code, usually harmless
4. `Encrypted RAM: Fail` → hardware limitation, not fixable

**Goal:** HSI:3 on consumer hardware is excellent. HSI:4 requires enterprise CPUs
with TME/SME.