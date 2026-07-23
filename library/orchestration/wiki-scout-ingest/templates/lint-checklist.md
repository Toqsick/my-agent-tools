# Wiki Lint Checklist

> Quality gates for every batch-ingest pass.
> 🔴 = fix immediately | 🟡 = review next session | 🟢 = nice-to-have

## Structural integrity
- [ ] Frontmatter present on every page (title, created, updated, type, domain, tags, sources)
- [ ] ≥2 outbound `[[wikilinks]]` per page (or 1 with comment explaining why terminal)
- [ ] Every page is listed in index.md under correct section

## Domain compliance
- [ ] `domain` in taxonomy: ai-ml, orchestration, personal, cross-domain
- [ ] Cross-domain pages live in `_meta/cross-domain/`, not duplicated
## Provenance

- [ ] Every claim traceable to a source file
- [ ] 3+ source pages have `^[raw/...]` provenance markers
- [ ] `sha256` (body-only, after stripping vault frontmatter) matches original source

## Conflicts
- [ ] `contested: true` pages have resolved contradictions or discussion
- [ ] `confidence` matches breadth of evidence

## Size
- [ ] No page > 200 lines (split candidate)
- [ ] No stub < 10 lines body (merge or expand)

## Drift
- [ ] Re-ingested sources: sha256 mismatch → flag and verify
- [ ] Pages not updated in 90 days while entities have new sources

## Logs
- [ ] log.md has entry for every ingest/update action
- [ ] log.md < 500 entries (rotate if exceeded)
