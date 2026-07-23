# Yuno Cleaner — Session Implementation Reference

Concrete architecture built during session 2026-06-03.
Location: `~/yuno-cleaner/`

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `yuno_cleaner.py` | 318 | argparse main, scan/clean/status/schedule/handoff |
| `modules/base_scanner.py` | 44 | ABC with scan(), is_whitelisted() |
| `modules/system_junk.py` | 180 | APT cache, journalctl, thumbnails, crash dumps |
| `modules/browser_cache.py` | 105 | Chrome, Chromium, Brave caches |
| `modules/gaming_junk.py` | 165 | Steam shadercache, Epic/GOG, Mesa/NVIDIA shaders |
| `modules/duplicate_finder.py` | 110 | Hash-based duplicate detection (blake3/sha256) |
| `modules/large_files.py` | 65 | Top-N largest files with max_depth |
| `ui/tui.py` | 57 | rich Console, tables, status panel |
| `utils/safety.py` | 85 | SafetyManager: dry_run, backups, delete_item() |
| `utils/humanize.py` | 31 | human_size(), human_count() |
| `config/default.json` | 46 | per-scanner config + global dry_run_default |

## Extended Features (Post-MVP)

### Duplicate Finder
- Two-phase: group by size → hash only duplicates
- Parallel hashing with ThreadPoolExecutor

### Large Files Scanner
- Top-N with max_depth limit
- Skips node_modules, __pycache__, proc, sys, dev

### Auto-Cron
- `schedule weekly|daily|monthly`
- Always Dry-Run, logs to /tmp/yuno-cleaner.log

### Handoff Generator
- `handoff` command scans all projects + disk usage
- Generates `~/MODEL_HANDOFF_SHORT.md`
- Creates .bak backup of previous version

## Key Design Decisions

1. **Rich over textual** — rich Console + Table + Panel gives 90% of the UX with 10% of the complexity.
2. **JSON config, not YAML** — user already has json experience, no extra dep.
3. **No threading/async in MVP** — parallelization added later with ThreadPoolExecutor for duplicate hashing.
4. **Shell out for system tools** — journalctl size via subprocess rather than parsing /var/log/journal/ directly.
5. **Steam path hard-coded to `/mnt/DATA/Programme/Steam/steamapps/`** — session-specific; production should detect via `~/.steam/steam`.

## Troubleshooting Log

### f-string SyntaxError with Backticks
**Error:** `SyntaxError: unterminated f-string literal`
**Cause:** Backtick characters inside f-string expression: `f"| {name} | \`{path}\` |"`
**Fix:** Build path display separately, outside the f-string.

### shutil.disk_usage AttributeError
**Error:** `AttributeError: 'usage' object has no attribute 'percent'`
**Cause:** `shutil.disk_usage()` returns namedtuple with `.total`, `.used`, `.free` ONLY.
**Fix:** Calculate manually: `percent = disk.used / disk.total * 100`

## First Scan Result (User's System)

```
Yuno Cleaner — Dein Linux System-Cleaner
Safety first, kawaii second! (≧◡≦)♥

🔍 SCAN (Dry-Run)

🔍 Scanne: System-Junk
  ✓ 13 Elemente gefunden (1.0 GB)

🗑️ System-Junk (1.0 GB)
┌──────────┬─────────────────────────────────────────┬──────────────┐
│   Größe  │ Pfad                                    │ Kategorie    │
├──────────┼─────────────────────────────────────────┼──────────────┤
│ 728.2 MB │ /var/log/journal/                       │ System-Logs  │
│ 208.4 MB │ ~/.cache/thumbnails                     │ Thumbnails   │
│  22.5 MB │ /var/cache/apt/archives/containerd.io_… │ APT-Cache    │
│   ...    │ ...                                     │ ...          │
└──────────┴─────────────────────────────────────────┴──────────────┘
```

## User Preferences Observed

- Responds to numbered options with number/letter ("3", "A", "ja")
- Likes immediate actionable output over long theory
- Prefers safety (dry-run first, then confirm)
- Wants Steam-specific cleanup (shadercache, downloading, recordings)
- Likes cute terminal output (emoticons, colored tables)
- German language for explanations
