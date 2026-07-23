# GreyScript Bug Patterns — 2026-06-19 Round 9

## Scan Details

**Index range:** 41–50
**Files scanned:** 10
**Source:** ALL from `backups/20260612_003843/` (backup copies)
**New bugs found:** 0 (all patterns already documented in previous rounds)

## Operational Issue: Backup File Index Drift

**This is the key finding of Round 9.**

The cron job used the unfiltered `find | sort` list for indexing. Files 41–50 were ALL from the backup directory. Every bug found was a duplicate of a pattern already documented from active files (NP-28, NP-30, NP-32, NP-33, NP-34, NP-35).

**Total file count:** 269 (including backups and nested backups)
**Active file count:** ~90 (excluding backups)
**Drift point:** After index ~40, the scan enters backup territory

### Required Fix

The cron prompt must:
1. Build a filtered, backup-excluded file list FIRST
2. Use THAT list for both scanning AND index tracking

```
# CORRECT pipeline:
find ~/greyhack-tools/ -name "*.src" | sort | grep -v '/backups/' > /tmp/active-files.txt
# Then index into /tmp/active-files.txt

# INCORRECT pipeline (produces backup drift):
FILES=$(find ~/greyhack-tools/ -name "*.src" | sort)  # includes backups!
```

## Duplicate Findings (already documented)

| File | Pattern | NP ID | First found in |
|------|---------|-------|----------------|
| minitest/manager.src:43 | Null-check on File | NP-32-like | Round 3 |
| minitest/manager.src:47-48 | Null crash on .build() result | NP-32 | Round 3 |
| parseExploitReqs.src:5 | Unvalidated split [1] | NP-30 | Round 3 |
| parseExploitReqs.src:13 | Unvalidated split [1] | NP-30 | Round 3 |
| parseExploitReqs.src:33 | Off-by-one range(N-1) | NP-28 | Round 3 |
| password_generator.src:77 | String concat in loop | NP-33 | Round 3 |
| password_generator.src:78 | Print in tight loop | NP-34 | Round 3 |

## Lessons

1. **This round produced zero new knowledge** — all findings were duplicates. This is wasted compute.
2. **Index 50 is past the active file boundary.** The next scan (51–60) will also be backups.
3. **After index ~90, the scan wraps around** and will re-scan active files from the beginning.
4. **The fix must be in the cron prompt** — it needs to filter before indexing.
