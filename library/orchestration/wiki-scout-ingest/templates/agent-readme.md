---
title: Agent Operating Manual — this wiki
created: __DATE__
updated: __DATE__
type: concept
domain: meta
tags: [meta, convention]
sources: []
---

# Agent Operating Manual — this wiki

> Read this FIRST in any new session that touches this wiki.
> Prevents duplicates and broken links.

## Every session, in this order

1. **Read SCHEMA** — conventions + tag taxonomy
2. **Read index** — what pages exist, where they live
3. **Scan log** — last 20-30 entries for recent activity context
4. Large wikis (100+): `search_files` for topic before creating new pages

## Don'ts

- ❌ Edit files in `raw/` — sources are immutable
- ❌ Create pages without ≥2 outbound `[[wikilinks]]`
- ❌ Use tags not in SCHEMA taxonomy
- ❌ Silently overwrite conflicting info — use `contradictions:` frontmatter
- ❌ Skip updating index.md and log.md

## Frontmatter is mandatory

```yaml
title: ...
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
domain: ai-ml | orchestration | personal | cross-domain
tags: [from SCHEMA taxonomy]
sources: [raw/articles/source.md]
```

## Quality signals

- `confidence: high` — multiple sources
- `confidence: medium` — single source, plausible
- `confidence: low` — opinion / fast-moving
- `contested: true` — set when contradictions unresolved
