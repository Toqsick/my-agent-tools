# Slug Resolution Playbook — Worked Example from Basti's Wiki

> Concrete transcript of a real slug-resolution pass on a wiki with
> 330+ wikilinks and ~15% broken. Use as a template for your own
> resolution passes.

## Starting State

- 100 files (50 content pages + 47 raw articles + index/log/SCHEMA)
- 330 wikilinks total
- ~48 broken (14.5%) due to slug mismatches

## Root Cause

Multiple subagents wrote pages concurrently using different naming
conventions:

| Agent | Naming | Example |
|---|---|---|
| Scout A (AI/ML) | Raw title-slug | `qwen-3.5-9b` → slug `-3-5-9b-` (dot becomes dash) |
| Scout B (Orchestration) | Frontmatter-based | Title `Qwen3.5-9B (Alibaba)` → slug `qwen3-5-9b-alibaba-qwen-team` |
| Filesystem | `p.stem` | `qwen3-5-9b-alibaba-qwen-team.md` |

Result: Scout A's `[[qwen-3.5-9b]]` links point to nowhere.

## Resolution Protocol (Applied)

### Phase 1: Count + Classify

```bash
cd ~/wiki
python3 << 'PYEOF'
import re
from pathlib import Path
wiki = Path(".")

# Build slug set from filesystem (MULTI-FORM: stem + slugified stem + title slug)
slugs = set()
for p in wiki.rglob("*.md"):
    if "raw/" in p.parts: continue
    slugs.add(p.stem)                                                       # raw stem: "qwen-3.5-9b"
    slugs.add(re.sub(r"[^\w]+", "-", p.stem.lower()).strip("-"))            # slugified: "qwen-3-5-9b"

# Build title→slug map from frontmatter
title_slugs = {}
for p in wiki.rglob("*.md"):
    if "raw/" in p.parts: continue
    text = p.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"^title:\s*(.+)", text, re.M)
    if m:
        ts = re.sub(r"[^\w]+", "-", m.group(1).strip().lower()).strip("-")
        title_slugs[ts] = p.stem

# Scan all files for broken links
broken = {}
for p in wiki.rglob("*.md"):
    if "raw/" in p.parts: continue
    text = p.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r"\[\[([^\]\|]+?)(?:\|[^\]]+)?\]\]", text):
        link = m.group(1).strip()
        if link.startswith("#") or link.startswith("http"): continue
        target = re.sub(r"[^\w]+", "-", link.lower()).strip("-")
        if target not in slugs:
            if target not in broken: broken[target] = []
            broken[target].append((str(p.relative_to(wiki)), m.group(0)))

# Show unique broken slugs + their canonical targets
for b, hits in sorted(broken.items()):
    # Look up in title_slugs
    canonical = title_slugs.get(b, "???")
    print(f"  {b:50s} → {canonical:40s}  ({len(hits)} hits)")
PYEOF
```

### Phase 2: Fix by category (shrink-before-expand)

```bash
# Fix dots → dashes slug mismatches (bulk replace across ALL files)
# Each file gets scanned; broken link is replaced with real slug
for f in $(find . -name "*.md" ! -path "*/raw/*" ! -name "SCHEMA.md"); do
    sed -i 's/\[\[qwen-3\.5-9b\]\]/[[qwen3-5-9b-alibaba-qwen-team]]/g' "$f"
    sed -i 's/\[\[ornith-1\.0-9b\]\]/[[ornith-1-0-9b-deepreinforce-ai]]/g' "$f"
    # ... repeat for each slug mismatch
done
```

### Phase 3: Create stubs for truly missing entities

For links that pointed to concepts that genuinely had no page:

```markdown
---
title: <Concept Name>
created: 2026-07-17
updated: 2026-07-17
type: concept
tags: [meta, wiki]
sources: []
---
# <Concept Name>

Stub page created during automated lint repair.
<!-- Referenced by [[existing-pages]] that need this entity -->
```

### Phase 4: Handle SCHEMA.md

`SCHEMA.md` has no frontmatter — it's a config file, not a wiki page.
But pages reference it as `[[schema]]`. Fix:

1. Add frontmatter to SCHEMA.md (`title: Wiki Schema`, `type: meta`)
2. Now `[[schema]]` → slug `wiki-schema` → file SCHEMA.md stem = schema? No.
   `SCHEMA.md` stem is `SCHEMA`. Fix links to `[[SCHEMA|Wiki Schema]]`.

```bash
# Fix SCHEMA reference: replace [[schema]] with [[SCHEMA|Wiki Schema]]
sed -i 's/\[\[schema\]\]/[[SCHEMA|Wiki Schema]]/g' $(find . -name "*.md" ! -path "*/raw/*")
```

### Phase 5: Inline-code escapes

Wikilinks inside inline code or bullet-point convention examples
were flagged as broken despite being documentation, not links:

- `` [[slug|Display]] `` → change to `[slug|Display]` (remove wikilink brackets)
- `[[wikilinks]]` in prose → wrap in backticks
- `[[schema]]` in SCHEMA.md → leave or escape

## Lessons for Future Passes

1. **Plan for slug mismatch.** Add a dedicated slug-resolution phase
   to EVERY ingest pipeline. It's not a bug — it's the cost of concurrent
   distributed writing.

2. **Classify broken links first.** Don't fix one at a time. A single pass
   that identifies all categories and fixes by bulk-replace is 50x faster.

3. **The 5 categories always appear:** slug mismatch, missing stub, inline
   code, SCHEMA.md convention, legacy name. Memorize them.

4. **Test with code-fence-aware lint** before declaring victory. Without
   stripping ``` blocks, inline examples inflate the broken-count by 3-5x.

5. **Git commit after resolution** — `git add -A && git commit -m "wiki: resolve N broken wikilinks"`.
   This creates a clean recovery point and documents the scale of the issue.

## Stats from This Pass

| Metric | Before | After |
|---|---|---|
| Total files | 100 | 106 |
| Wikilinks | 330 | 463 |
| Broken | ~48 | 0 |
| Git commits | 1 | 2 |
| Time | — | ~30 min (including classification) |
