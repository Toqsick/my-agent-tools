#!/usr/bin/env python3
"""
check-broken-wiki-links.py — Cross-Link Cleanup for Obsidian Vaults

Usage:
    python3 scripts/check-broken-wiki-links.py <vault-path>

Scans all .md files in the vault and reports:
  - Wiki-links pointing to non-existent files (optionally resolved via aliases)
  - Markdown-style links [text](path%20with%20spaces.md) to missing files
  - Distinguishes real broken links from intentional template placeholders.

Alias resolution: reads YAML frontmatter `aliases:` field from every note.
Placeholder exclusion: skips lines matching [[…]], [[<…>]], and similar template markers.
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict


def parse_frontmatter(text: str) -> dict:
    """Minimal YAML frontmatter parser (aliases only)."""
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    result = {}
    # Extract aliases
    am = re.search(r"^aliases:\s*\n((?:\s*-[^\n]*\n?)+)", block, re.MULTILINE)
    if am:
        aliases = []
        for line in am.group(1).splitlines():
            alias = re.sub(r"^\s*-\s*", "", line).strip().strip('"').strip("'")
            if alias:
                aliases.append(alias)
        if aliases:
            result["aliases"] = aliases
    return result


# Regex patterns for placeholder lines (template docs, syntax examples)
PLACEHOLDER_PATTERNS = re.compile(
    r"^\s*-\s*\[<"           # `- [<`
    r"|^\s*\[<\w"            # `[<Name>` at line start
    r"|<.+?>$"               # ends with `<something>`
    r"|^[\s\[]*…"            # starts with …
    r"|\[\[\.\.\.\]\]"       # [[…]]
    r"|\[\[<[^>]+>\]\]"      # [[<verlinkte Note>]]
    r"|\\(<--\\s*Platzhalter"  # (<-- Platzhalter, ...) inline comments
)


def scan_vault(vault_path: str, exclude_dirs: tuple = (".obsidian", ".trash", "_templates")):
    vault = Path(vault_path).resolve()
    if not vault.is_dir():
        print(f"❌ Not a directory: {vault}")
        sys.exit(1)

    # Phase 1: collect all filenames and aliases
    all_names: set[str] = set()
    aliases: dict[str, str] = {}  # alias -> canonical filename (stem)

    for md in sorted(vault.rglob("*.md")):
        rel = md.relative_to(vault)
        if any(part in rel.parts for part in exclude_dirs):
            continue
        stem = md.stem
        all_names.add(stem)
        try:
            text = md.read_text(encoding="utf-8-sig", errors="replace")
            fm = parse_frontmatter(text)
            for alias in fm.get("aliases", []):
                aliases[alias] = stem
        except Exception:
            pass

    all_targets = all_names | set(aliases.keys())
    print(f"📂 Vault: {vault}")
    print(f"📄 Notes: {len(all_names)}")
    print(f"🏷️  Aliases indexed: {len(aliases)}")

    # Phase 2: scan each file for broken links
    issues: list[tuple[str, int, str, str]] = []

    for md in sorted(vault.rglob("*.md")):
        rel = md.relative_to(vault)
        if any(part in rel.parts for part in exclude_dirs):
            continue
        try:
            text = md.read_text(encoding="utf-8-sig", errors="replace")
        except Exception as e:
            print(f"⚠️  Cannot read {rel}: {e}")
            continue

        for line_no, line in enumerate(text.split("\n"), start=1):
            # Skip template placeholder lines
            if PLACEHOLDER_PATTERNS.search(line):
                continue

            # Check wiki-links [[target]] or [[target|display]]
            for m in re.finditer(r"\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]", line):
                target = m.group(1).strip()
                # Strip heading anchor
                target = target.split("#")[0].strip()
                if not target:
                    continue
                if target not in all_targets:
                    issues.append((str(rel), line_no, m.group(0),
                                   f"✔  →  file not found (no alias match)"))

            # Check markdown-style links [text](path.md)
            for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", line):
                href = m.group(2)
                if href.startswith("http") or href.startswith("file://"):
                    continue
                if href.endswith(".md") or ".md#" in href:
                    # Resolve relative to parent dir of current file
                    candidate = (md.parent / href.split("#")[0]).resolve()
                    if not candidate.exists():
                        issues.append((str(rel), line_no, m.group(0),
                                       f"⚠️  →  .md link target missing: {href}"))

    # Phase 3: report
    by_file: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for f, line, text, reason in issues:
        by_file[f].append((line, text, reason))

    total_real = 0
    for f in sorted(by_file):
        real_in_file = [x for x in by_file[f]]
        if real_in_file:
            total_real += len(real_in_file)
            print(f"\n{'='*60}")
            print(f"  📄 {f}")
            print(f"{'='*60}")
            for line, text, reason in sorted(real_in_file):
                print(f"  L{line:>4}: {text}")
                print(f"         {reason}")

    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"  Total unresolved references: {len(issues)}")
    print(f"  (placeholders excluded)")
    print(f"\n💡 Fix strategies:")
    print(f"  1. Add `aliases:` frontmatter to the target file:")
    print(f"     ---")
    print(f"     aliases:")
    print(f"       - \"<alias-name>\"")
    print(f"     ---")
    print(f"  2. Convert markdown links to wiki-links: [text](path.md) → [[Note Name]]")
    print(f"  3. Create the missing file if the content was meant to exist")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        vault = os.environ.get("OBSIDIAN_VAULT")
        if not vault:
            print("Usage: python3 check-broken-wiki-links.py <vault-path>")
            print("       or set OBSIDIAN_VAULT environment variable")
            sys.exit(1)
    else:
        vault = sys.argv[1]
    scan_vault(vault)
