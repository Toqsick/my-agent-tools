#!/usr/bin/env python3
"""Extract YAML frontmatter from a Hermes SKILL.md → MiniMax-compatible meta.yaml.

Usage:
    python3 extract-minimax-meta.py <src_skill.md> <name> <category> <src_dir> <dest_dir>

Handles:
- Block-scalar (| for literal, > for folded) multi-line description
- Single-line quoted description
- Trigger-words / triggers list from frontmatter
- Provenance tracking (original-category, original-skill-path, date)
- Display-name generation from kebab-case name

Exit code: 0 on success, 1 on parse failure (SKILL.md has no frontmatter block).
Still writes a minimal meta.yaml on failure so CI doesn't break.

Author: Yuno (2026-07-07) — part of Hermes Skill-Format-Conversion skill
"""

import re
import sys
from pathlib import Path


def extract_frontmatter(text: str) -> str:
    """Extract the raw YAML frontmatter block between --- markers."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    return m.group(1) if m else ""


def parse_description(fm_text: str) -> str:
    """Parse description field — handles single-line, | (literal), > (folded)."""
    # Single-line: description: "some text" or description: some text
    m = re.search(r"^description:\s*['\"]?(.*?)['\"]?\s*$", fm_text, re.MULTILINE)
    if m:
        return m.group(1).strip().strip("'\"")

    # Block-scalar: description: | or description: >
    m = re.search(r"^description:\s*[|>]\s*\n((?:  .*\n?)+)", fm_text, re.MULTILINE)
    if m:
        lines = []
        for line in m.group(1).splitlines():
            if line.startswith("  "):
                lines.append(line[2:])
            elif line.startswith("\t"):
                lines.append(line[1:])
        return "\n".join(lines).strip()

    return ""


def parse_triggers(fm_text: str) -> list[str]:
    """Parse triggers or trigger-words from frontmatter."""
    triggers = []

    # Hermes-style: triggers: ["foo", "bar"]
    m = re.search(r"^triggers:\s*\[(.*?)\]", fm_text, re.MULTILINE)
    if m:
        triggers = [t.strip().strip("'\"") for t in m.group(1).split(",") if t.strip()]

    # MiniMax-style: trigger-words: ["foo", "bar"]
    m = re.search(r"^trigger-words:\s*\[(.*?)\]", fm_text, re.MULTILINE)
    if m:
        triggers = [t.strip().strip("'\"") for t in m.group(1).split(",") if t.strip()]

    return triggers


def build_meta(name: str, display_name: str, description: str,
               triggers: list[str], src_cat: str, src_dir: str, dest_dir: str) -> str:
    """Build the meta.yaml content string."""
    # Truncate description to 600 chars for Hub display
    if len(description) > 600:
        description = description[:597] + "..."

    desc_indented = description.replace("\n", "\n  ")

    entry = f"""name: {name}
display-name: {display_name}
version: "1.0.0"
author: "Basti (Hermes-Skill conversion)"
license: MIT
source: "Hermes Skills Library ~/.hermes/skills/{src_cat}/{name}/"
description: |
  {desc_indented[:600]}
trigger-words:
"""

    for t in triggers[:8]:
        entry += f"  - {t}\n"

    entry += f"""provenance:
  original-category: {src_cat}
  original-skill-path: {src_dir}/SKILL.md
  converted-by: yuno-bundle-builder
  date: 2026-07-07
  hermes-skill-format: 'YAML frontmatter + Markdown body'
  minimax-skill-format: 'Same (Hub reads SKILL.md directly)'
"""
    return entry


def main() -> int:
    if len(sys.argv) != 6:
        print(f"Usage: {sys.argv[0]} <src_skill.md> <name> <category> <src_dir> <dest_dir>",
              file=sys.stderr)
        return 1

    src_path, name, src_cat, src_dir, dest_dir = sys.argv[1:6]
    src = Path(src_path)

    if not src.exists():
        print(f"ERROR: Source not found: {src_path}", file=sys.stderr)
        return 1

    fm_text = src.read_text()
    fm_short = extract_frontmatter(fm_text)

    display_name = name.replace("-", " ").title()
    description = parse_description(fm_short)
    triggers = parse_triggers(fm_short)

    meta = build_meta(name, display_name, description, triggers,
                      src_cat, src_dir, dest_dir)

    dest_path = Path(dest_dir) / "meta.yaml"
    dest_path.write_text(meta)

    # Print a one-line summary for the build log
    desc_preview = description[:80].replace("\n", " ")
    print(f"✓ meta.yaml written for {name}: {len(description)} chars desc, "
          f"{len(triggers)} triggers")
    print(f"  └→ {desc_preview}…")

    return 0


if __name__ == "__main__":
    sys.exit(main())
