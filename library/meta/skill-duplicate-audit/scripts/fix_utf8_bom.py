#!/usr/bin/env python3
"""fix_utf8_bom.py — Migrate utf-8 → utf-8-sig in skill scripts (read-mode only).

Strategy: Only change `encoding="utf-8"` to `encoding="utf-8-sig"` for read-mode
operations (read_text, open with "r" mode). Leave write operations alone (utf-8
is correct for write — we don't want to inject BOMs into output).

Usage: python3 fix_utf8_bom.py [--dry-run]
"""

import re
import sys
from pathlib import Path

SKILLS_ROOT = Path.home() / ".hermes" / "skills"

# Match read-mode patterns:
#   1. .read_text(encoding="utf-8-sig")        → .read_text(encoding="utf-8-sig")
#   2. open(..., "r", encoding="utf-8-sig")   → open(..., "r", encoding="utf-8-sig")
#   3. open(..., "rt", encoding="utf-8-sig")  → open(..., "rt", encoding="utf-8-sig")
#   4. open(..., encoding="utf-8", "r")   → open(..., encoding="utf-8-sig", "r")
PATTERNS = [
    # read_text
    (re.compile(r'(\.read_text\(\s*encoding=)"utf-8"'), r'\1"utf-8-sig"'),
    # open with explicit "r" or "rt" mode
    (re.compile(r'(open\([^)]*?)("r"|"rt"|mode="r"|mode="rt")([^)]*?encoding=)"utf-8"'),
     r'\1\2\3"utf-8-sig"'),
]


def fix_file(path: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """Returns (change_count, list_of_changes)."""
    text = path.read_text(encoding="utf-8-sig")
    changes = []
    for pattern, replacement in PATTERNS:
        new_text, count = pattern.subn(replacement, text)
        if count > 0:
            changes.append(f"  {count}x: {pattern.pattern[:60]}...")
            text = new_text

    if changes and not dry_run:
        path.write_text(text, encoding="utf-8")

    return len(changes), changes


def main():
    dry_run = "--dry-run" in sys.argv

    files_changed = 0
    total_changes = 0

    for py_file in sorted(SKILLS_ROOT.rglob("scripts/*.py")):
        if ".archive" in py_file.parts:
            continue
        count, changes = fix_file(py_file, dry_run=dry_run)
        if count > 0:
            files_changed += 1
            total_changes += count
            print(f"{'[DRY-RUN] ' if dry_run else ''}{py_file.relative_to(SKILLS_ROOT)}")
            for change in changes:
                print(change)
            print()

    print(f"=== {'[DRY-RUN] ' if dry_run else ''}Summary ===")
    print(f"Files changed: {files_changed}")
    print(f"Total replacements: {total_changes}")


if __name__ == "__main__":
    main()