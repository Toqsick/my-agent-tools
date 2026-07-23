# Disk Analysis — Detailed Reference

Deep-dive on disk inspection workflows, large-file scanning, and duplicate detection.
Loaded on demand from the slim `SKILL.md`.

## Manual System Inspection Workflow

When the user asks for "systempflege" or general health check, follow this
step-by-step manual inspection before any automated cleanup. Always gather
hard data first, then propose actions.

### 1. Quick Health Check

```bash
# Disk usage (root + home)
df -h / /home

# RAM + Swap
free -h && swapon --show

# CPU temperature
sensors | head -20

# System load + uptime
uptime
```

### 2. Package & Kernel Audit

```bash
# Available updates
apt list --upgradable 2>/dev/null | head -30

# ALL kernels (installed=ii + orphaned configs=rc)
dpkg -l | grep -E 'linux-(image|headers|modules)'

# Orphaned config packages
dpkg -l | grep '^rc' | wc -l

# Detailed rc list
dpkg -l | grep '^rc' | awk '{print $2, $3}'
```

For the actual kernel + rc purge commands, see `cleanup-procedures.md` §"Kernel
Cleanup Rule" and §"rc Package Purge".

### 3. Inspection Commands Used (full session example)

A complete inspection session also walks through:

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

# Mail client detection (see cleanup-procedures.md §"Mail Client Detection")

# Big directories
du -sh ~/*/ 2>/dev/null | sort -rh | head -15
```

## Duplicate Finder

Hash-based duplicate detection using two-phase filtering:
1. Group files by size (fast, no disk reads)
2. Hash only groups with >1 file (parallel with ThreadPoolExecutor)

```python
class DuplicateFinder(BaseScanner):
    def scan(self) -> dict:
        files_by_size = defaultdict(list)
        # Phase 1: group by size
        for root, _, files in os.walk(path):
            for f in files:
                size = os.path.getsize(f)
                if size >= self.min_size:
                    files_by_size[size].append(f)

        # Phase 2: hash groups with duplicates
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = executor.map(self._hash_file, file_list)
```

## Large Files Scanner

Top-N finder with depth-limit to avoid crawling infinitely deep trees:

```python
class LargeFilesScanner(BaseScanner):
    def _scan_path_fast(self, path: Path, depth: int) -> list:
        if depth > self.max_depth:
            return []
        for entry in path.iterdir():
            if entry.is_file() and entry.stat().st_size >= self.min_size:
                results.append((entry, entry.stat().st_size))
            elif entry.is_dir() and entry.name not in ("node_modules", "__pycache__", "proc", "sys"):
                results.extend(self._scan_path_fast(entry, depth + 1))
```

Key optimization: skip known-huge directories (`node_modules`, `.git`, `proc`, `sys`, `dev`).

## Real Scan Data (Session 2026-06-03)

For a worked example of inspection → cleanup → documentation on a Zorin OS 18.1
gaming desktop (RTX 5060 Laptop, i7-13620H, 15 GB RAM, 607 GB disk at 81%),
see `references/system-inspection-2026-06-03.md`. Key numbers:

- **Total reclaimed:** ~30.4 GB (81% → 72%)
- **Largest single wins:** npm cache 1.16 GB, journal 678 MB, thumbnails 217 MB,
  rc packages ~30 MB, APT cache 139 MB
- **Surprise:** user said "Thunderbird" but actually used Evolution/Gmail IMAP,
  no local mail to clean