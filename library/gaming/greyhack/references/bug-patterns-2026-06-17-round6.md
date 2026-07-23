# Bug Patterns — Scan #8 (2026-06-17, Index 121–130)

**Scanned:** Files 121–130 (all backup copies)

## New Pattern

### NP-48: Infinite Parent Traversal Loop
**Pattern:** `while file.name != "/"` with `file = file.parent` — if parent returns self at root, loops forever.
**Fix:** Add `next_file = file.parent; if next_file == file then break; file = next_file`

## Lesson: Backup Files Drift Index
When the scan index advances past active files (104), remaining indices point to backups.
**Fix:** Filter backups BEFORE indexing: `find ... | grep -v '/backups/' | sort`
Track index in filtered list only. Reset to 0 when exhausted.
