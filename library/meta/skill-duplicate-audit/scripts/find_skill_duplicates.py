#!/usr/bin/env python3
"""find_skill_duplicates.py — Detect duplicate scripts across skill directories.

Walks ~/.hermes/skills/ and finds scripts with identical content (by md5 hash).
Reports them as candidates for de-duplication. Exit code 0 always (advisory only).

Usage: python find_skill_duplicates.py
"""

import hashlib
import sys
from pathlib import Path

SKILLS_ROOT = Path.home() / ".hermes" / "skills"


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def main():
    if not SKILLS_ROOT.exists():
        print(f"ERROR: {SKILLS_ROOT} does not exist", file=sys.stderr)
        sys.exit(1)

    # Collect all scripts
    hash_to_paths: dict[str, list[Path]] = {}
    for path in SKILLS_ROOT.rglob("scripts/*.py"):
        h = md5(path)
        hash_to_paths.setdefault(h, []).append(path)

    # Find duplicates
    duplicates = {h: paths for h, paths in hash_to_paths.items() if len(paths) > 1}

    if not duplicates:
        print("=== No skill-script duplicates found ===")
        print(f"Scanned: {len(hash_to_paths)} unique scripts in {SKILLS_ROOT}")
        return

    print(f"=== Found {len(duplicates)} duplicate script group(s) ===\n")
    for h, paths in duplicates.items():
        print(f"MD5: {h}")
        for p in paths:
            skill = p.relative_to(SKILLS_ROOT).parts[0]
            print(f"  - {skill}/scripts/{p.name}")
        print()


if __name__ == "__main__":
    main()