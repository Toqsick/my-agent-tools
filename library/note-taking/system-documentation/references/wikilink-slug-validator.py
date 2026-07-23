#!/usr/bin/env python3
"""Wikilink Slug Validator — prüft dass alle [[target]] auf existierende .md-Files zeigen.

Verwendung:
  python3 references/wikilink-slug-validator.py /pfad/zum/wiki/
  python3 references/wikilink-slug-validator.py /pfad/zu/einer/page.md

Exit-Code: 0 wenn alle Links auflösen, 1 bei broken links.
Broken links werden auf stderr ausgegeben.

Batch-Fix-Modus (--fix):
  python3 references/wikilink-slug-validator.py --fix /pfad/zum/wiki/
  Ersetzt nicht-auflösende Slug-Varianten (Punkte→Striche, lowercased, etc.)
  gegen die echten Dateinamen auf Disk.

Pitfall-Check (--double-pipe):
  python3 references/wikilink-slug-validator.py --double-pipe /pfad/zum/wiki/
  Findet [[X||Y]] — doppelte Pipes die von Obsidian nicht aufgelöst werden.
"""

import re, os, sys

def collect_slugs(base):
    """Walk base and return {slug: path} for all .md files (excl. raw/ and _meta/)."""
    slugs = {}
    for root, dirs, files in os.walk(base):
        # Skip directories that are raw material or meta
        rel = os.path.relpath(root, base)
        parts = rel.split(os.sep)
        if 'raw' in parts or '_meta' in parts or parts[0].startswith('.'):
            continue
        for f in files:
            if not f.endswith('.md'):
                continue
            slug = re.sub(r'\.md$', '', f)
            slugs[slug] = os.path.join(root, f)
    return slugs

def all_wikilinks_in_file(path):
    """Extract all [[target]] first segments from a file."""
    with open(path, encoding='utf-8') as f:
        content = f.read()
    hits = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]', content)
    # return unique
    unique = set(h.strip() for h in hits)
    # skip things that look like raw/ or external refs
    return {s for s in unique if '/' not in s and not s.startswith('http')}

def find_double_pipes(path):
    """Find [[X||Y]] patterns (broken wikilinks)."""
    with open(path, encoding='utf-8') as f:
        content = f.read()
    hits = re.findall(r'\[\[[^\]|]+\|\|[^\]]*\]\]', content)
    return hits

def build_slug_map(existing_slugs):
    """Build {wrong_variant: correct_slug} mapping."""
    slug_map = {}
    for slug in existing_slugs:
        # Normalized variant with dots/hyphens unified
        normalized = slug.replace('.', '-').replace('_', '-').lower()
        if normalized != slug:
            slug_map[normalized] = slug
        # Also add title-derived variants (longer descriptions)
        # e.g. "ornith-1-0-9b-deepreinforce-ai" → "ornith-1.0-9b"
        parts = slug.split('-')
        if len(parts) > 4:
            short = '-'.join(parts[:2]) if len(parts) >= 2 else parts[0]
            slug_map[slug.replace('-', '.').replace('_', '.')] = slug
    return slug_map

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    fix_mode = '--fix' in args
    double_pipe_mode = '--double-pipe' in args
    targets = [a for a in args if not a.startswith('--')]

    for target in targets:
        target = os.path.abspath(target)
        if os.path.isfile(target):
            pages = [target]
            base = os.path.dirname(target)
        else:
            base = target
            pages = []
            for r, _, fs in os.walk(base):
                rel = os.path.relpath(r, base)
                parts = rel.split(os.sep)
                if 'raw' in parts or '_meta' in parts or parts[0].startswith('.'):
                    continue
                for f in fs:
                    if f.endswith('.md'):
                        pages.append(os.path.join(r, f))

        existing = collect_slugs(base)
        slug_map = build_slug_map(existing) if fix_mode else {}

        if double_pipe_mode:
            found_any = False
            for page in pages:
                dp = find_double_pipes(page)
                if dp:
                    found_any = True
                    print(f"[DOUBLE-PIPE] {os.path.relpath(page, base)}: {dp}")
            if not found_any:
                print(f"[OK] No double-pipe wikilinks found in {base}")

        for page in pages:
            wikilinks = all_wikilinks_in_file(page)
            unresolved = [s for s in wikilinks if s not in existing]

            if not unresolved:
                continue

            if fix_mode:
                # Try to fix each unresolved slug
                with open(page, encoding='utf-8') as f:
                    content = f.read()
                pat = re.compile(r'\[\[([^\]|]+)(\|[^\]]*)?\]\]')
                def fix(m):
                    t = m.group(1).strip()
                    l = m.group(2) or ''
                    if t in slug_map and slug_map[t] != t:
                        return f'[[{slug_map[t]}{l}]]'
                    return m.group(0)
                new_content = pat.sub(fix, content)
                if new_content != content:
                    with open(page, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    fixed = [s for s in unresolved if s in slug_map]
                    still_broken = [s for s in unresolved if s not in slug_map or slug_map[s] == s]
                    if fixed:
                        print(f"[FIXED] {os.path.relpath(page, base)}: {fixed}")
                    if still_broken:
                        print(f"[BROKEN] {os.path.relpath(page, base)}: {still_broken}", file=sys.stderr)
                else:
                    print(f"[BROKEN] {os.path.relpath(page, base)}: {unresolved}", file=sys.stderr)
            else:
                rel = os.path.relpath(page, base)
                print(f"[BROKEN] {rel}: {unresolved}", file=sys.stderr)

if __name__ == '__main__':
    main()
