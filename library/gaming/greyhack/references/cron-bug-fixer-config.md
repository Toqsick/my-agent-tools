# Cron Bug-Fixer Configuration — Truncation Prevention

## Critical Issue

Scans 244+ .src files. Without limits → truncation.

## Required Prompt Constraints

1. **Batch limit**: Max 10 files per run
2. **State tracking**: `~/greyhack-tools/bug-reports/last-scan-index.txt`
3. **Filter**: `grep -v '/backups/'` — **CRITICAL: Build the filtered list FIRST, then index into it.**

## Correct Pipeline

```bash
find ~/greyhack-tools/ -name "*.src" | sort | grep -v '/backups/' > /tmp/active-files.txt
# Then index into /tmp/active-files.txt, NOT the full find output
```