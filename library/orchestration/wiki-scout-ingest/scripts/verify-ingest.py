#!/usr/bin/env python3
"""
verify-ingest.py — Reusable wiki-ingest quality gate.

Usage:
    python3 scripts/verify-ingest.py [--root /path/to/wiki]

Checks:
  1. Frontmatter completeness on all content pages (title, created, updated, type, domain, tags, sources)
  2. Domain consistency
  3. Wikilink resolution with three-way fallback (stem, slugified-stem, title, slugified-title)
  4. Source-hash integrity (body-SHA256 match for raw/ articles)
  5. Index inclusion for every content page
  6. Log inclusion for every content page
  7. Page size ≤200 lines (flag only, no hard fail)

Returns exit code 0 on pass, 1 on failure, with per-page diagnostics.
"""

from __future__ import annotations

import hashlib
import re
import sys
import unicodedata
from pathlib import Path


def slugify(value: str) -> str:
    """ASCII-slugify a string for wikilink resolution.

    Preserves alphanumerics, collapses runs of non-alnum to single '-'.
    Handles Unicode normalization (ä→ae not done, stripped instead).
    """
    # Expand common special characters
    value = value.replace("&", " und ")
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value


def build_resolvable_index(wiki_root: Path) -> set[str]:
    """Build a set of all resolvable wikilink targets.

    Three-way resolution per page:
      1. filename stem (e.g. 'qwen-3-5-9b-alibaba-qwen-team')
      2. slugified filename stem (may differ if stem already has hyphens)
      3. raw title from frontmatter
      4. slugified title

    This catches mismatches between what an agent writes as [[qwen-3.5-9b]]
    and what the filesystem slug created (qwen-3-5-9b-alibaba-qwen-team).
    """
    resolvable: set[str] = set()
    for p in wiki_root.rglob("*.md"):
        resolvable.add(p.stem)
        resolvable.add(slugify(p.stem))
        try:
            first = p.read_text(encoding="utf-8")[:2000]
        except UnicodeDecodeError:
            continue
        m = re.search(r"(?m)^title:\s*(.+?)\s*$", first)
        if m:
            title = m.group(1).strip("\"'")
            resolvable.add(title)
            resolvable.add(slugify(title))
    return resolvable


def check_raw_integrity(wiki_root: Path) -> list[str]:
    """Verify body-SHA256 matches declared sha256 in frontmatter."""
    errors: list[str] = []
    for path in sorted(wiki_root.rglob("raw/articles/*.md")):
        data = path.read_bytes()
        marker = b"---\n"
        if not data.startswith(marker):
            errors.append(f"raw missing frontmatter: {path}")
            continue
        end = data.find(marker, len(marker))
        if end < 0:
            errors.append(f"raw bad delimiter: {path}")
            continue
        fm = data[len(marker):end].decode("utf-8")
        body = data[end + len(marker):]
        declared = re.search(r"(?m)^sha256:\s*([0-9a-f]{64})$", fm)
        if not declared:
            errors.append(f"raw no sha256: {path}")
            continue
        actual = hashlib.sha256(body).hexdigest()
        if actual != declared.group(1):
            errors.append(f"raw hash mismatch: {path}")
    return errors


def main() -> int:
    root = Path("/home/bratan/wiki")
    # Allow override via --root
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--root" and i < len(sys.argv):
            root = Path(sys.argv[i + 1])

    if not root.exists():
        print(f"FATAL: wiki root {root} not found")
        return 1

    # Read config files
    index_text = (root / "index.md").read_text(encoding="utf-8")
    log_text = (root / "log.md").read_text(encoding="utf-8")

    # Build resolvable index (all pages in wiki)
    resolvable = build_resolvable_index(root)

    # Content pages = non-raw, non-config
    content_pages: list[Path] = []
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root)
        if str(rel).startswith("raw/"):
            continue
        if p.name in ("index.md", "log.md", "SCHEMA.md"):
            continue
        content_pages.append(p)

    required_fm = ["title", "created", "updated", "type", "domain", "tags", "sources"]
    valid_types = {"entity", "concept", "comparison", "query", "summary"}
    errors: list[str] = []

    for path in content_pages:
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8")

        # 1. Frontmatter
        if not text.startswith("---\n"):
            errors.append(f"no frontmatter: {rel}")
            continue
        parts = text.split("---\n", 2)
        if len(parts) != 3:
            errors.append(f"bad frontmatter delimiters: {rel}")
            continue
        fm, body = parts[1], parts[2]

        for key in required_fm:
            if not re.search(rf"(?m)^{re.escape(key)}:", fm):
                errors.append(f"missing {key}: {rel}")

        # 2. Type validity
        typ = re.search(r"(?m)^type:\s*(\S+)", fm)
        if typ and typ.group(1) not in valid_types:
            errors.append(f"invalid type '{typ.group(1)}': {rel}")

        # 3. Wikilink resolution
        links = re.findall(r"\[\[([^\]|#]+)", body)
        if len(links) < 2:
            errors.append(f"too few outbound links ({len(links)}): {rel}")
        for link in links:
            if link not in resolvable and slugify(link) not in resolvable:
                errors.append(f"broken link {link!r}: {rel}")

        # 4. Page size
        line_count = text.count("\n") + 1
        if line_count > 200:
            errors.append(f"oversized ({line_count} lines): {rel}")

        # 5. Indexed?
        title = re.search(r"(?m)^title:\s*(.+)$", fm)
        title_text = title.group(1).strip("\"'") if title else path.stem
        if (
            path.stem not in index_text
            and title_text not in index_text
            and slugify(title_text) not in index_text
        ):
            errors.append(f"not indexed: {rel}")

        # 6. Logged?
        if (
            str(rel) not in log_text
            and path.name not in log_text
        ):
            errors.append(f"not in log: {rel}")

        status = "\u26a0\ufe0f" if errors and errors[-1].startswith(f"broken link") else "\u2705"
        print(f"{status} {rel}  lines={line_count} links={len(links)}")

    # 7. Raw integrity
    raw_errors = check_raw_integrity(root)
    errors.extend(raw_errors)

    # Summary
    if errors:
        print(f"\n\ud83d\uded1 FAILURES ({len(errors)}):")
        for e in errors:
            print(f"  \u2022 {e}")
        return 1
    else:
        print(f"\n\ud83d\udfe2 ALL CHECKS PASSED: {len(content_pages)} content pages, {len(list(root.rglob('raw/articles/*.md')))} raw sources")
        return 0


if __name__ == "__main__":
    sys.exit(main())
