# Cross-Reference Repair After Entity Merge/Delete

> Pattern: after deleting or merging a wiki entity page, systematically repair
> all inbound wikilinks across the entire wiki. Discovered 2026-07-17 during
> a 12-page orchestration-ingest pass where `langgraph.md` was collapsed into
> the existing framework-comparison page.

## When This Applies

- You deleted a stub entity page and merged its content into an umbrella
- You renamed a page (new slug != old slug)
- You replaced a monolithic page with several focused ones
- A lint pass flagged broken wikilinks pointing to a page that no longer exists

## Repair Pass Procedure

### Phase 1 — Find all affected inbound links

```bash
cd ~/wiki
# Find every wikilink matching the deleted entity's slug or title
grep -rn '\[\[langgraph' --include='*.md' . | grep -v 'raw/'
```

### Phase 2 — Classify each link

| Link type | Example | Action |
|-----------|---------|--------|
| Direct link to deleted page | `[[langgraph]]` | Replace with `[[target-page|Display Text]]` |
| Link with alias | `[[langgraph\|LangGraph State Graph]]` | Update target to umbrella page |
| Self-reference in deleted page | — | No action (page is gone) |

### Phase 3 — Apply patches

Do NOT patch one file at a time if there are 5+ files. Read all affected files,
plan the canonical mapping, then batch the patches:

```python
# Mapping: old_link -> (new_target, new_display)
REMAP = {
    "langgraph":         ("autogen-vs-crewai-vs-langgraph", "AutoGen vs. CrewAI vs. LangGraph"),
    "langgraph|LangGraph": ("autogen-vs-crewai-vs-langgraph", "AutoGen vs. CrewAI vs. LangGraph"),
}
```

For each affected file, apply targeted `patch` replacements. Prefer `patch`
mode (find+replace) over full-file rewrites — preserves existing prose and
provenance markers.

### Phase 4 — Verify

Run the verification script:

```bash
python3 scripts/verify-ingest.py
```

Expect **zero** broken-link errors from the deleted entity. If any remain,
they're either:
- In a file you missed (re-run `grep`)
- In a raw/ article (not expected to have wiki-internal links — these are
  source copies, not content pages)

### Phase 5 — Log and document

Record the merge in log.md with clear rationale:

```markdown
- **Entity merged**: `entities/langgraph.md` → collapsed into
  `comparisons/multi-agent-frameworks-2026.md` and
  `entities/orchestration-framework-landscape.md`. Rationale: stub with
  single-source content that belongs under the framework-comparison umbrella.
  Cross-references patched: 9 files, 15 links.
```

## Pitfalls

- **Partial grep matches** — `[[langgraph]]` and `[[langgraph|LangGraph]]`
  need separate patterns. Use `\[\[langgraph` (no closing bracket) to catch both.
- **Self-link in the page being deleted** — `grep` will find the page itself.
  Skip it; it's being deleted.
- **Raw articles that reference wiki entities** — raw/ files are source copies,
  not wiki content. They may contain `[[langgraph]]` from the original material.
  Do NOT patch these — the source copy should stay pristine.
- **Case sensitivity** — wikilinks are case-sensitive. `[[LangGraph]]` and
  `[[langgraph]]` are different targets. If the page was created with one case
  but linked with another, the link was already broken — decide whether to fix
  it during the repair pass.
- **Multiple pages linking from the same file** — patch `replace_all=true` if
  the same old_string appears multiple times in one file and all instances
  should be remapped the same way.
