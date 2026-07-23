# Entity Consolidation — Merge & Re-link

Merge content from one wiki/entity/concept page into another, then rewrite every
inbound wikilink across the documentation tree so no dead links remain.

## When to use

- Two entity pages cover the same ground and one should absorb the other.
- An entity was split out prematurely — its content is better hosted by a parent.
- A concept page grew abstract and its real value is in the page that operationalizes it.
- A refactoring produces a "thin" page that can be merged back into a broader page.

## Workflow

### Phase 1: Decide what happens to each page

| Role | What happens |
|------|-------------|
| **Absorber** (surviving page) | Gains relevant content from the absorbed page. Its slug stays. |
| **Absorbed** (page to delete) | Content migrated to absorber, then deleted. Its slug must never appear in a wikilink again. |

### Phase 2: Absorb content into the survivor

Read both pages. Move substantive content (definitions, examples, rules) from the
absorbed page into the right section of the survivor. Do NOT copy verbatim —
reframe in the survivor's voice. Keep the original raw source citation:

```markdown
Diese Regeln sind ... ^[raw/articles/personal-working-agreement-yuno-basti.md]
```

### Phase 3: Rewrite all wikilinks (the critical step)

Use a **multi-file V4A patch** (`patch(mode='patch')`) to replace every
`[[absorbed-slug]]` and `[[absorbed-slug|label]]` across all documentation pages:

1. **Find every file** that links to the absorbed slug:
   ```
   search_files(target='content', pattern='absorbed-slug', path='~/wiki/')
   ```

2. **Build one V4A patch** with a block per file. Each block is:
   ```
   *** Update File: path/to/page-1.md
   @@
   -[[absorbed-slug|old label]]
   +[[survivor-slug|new context label]]
   @@
   -[[absorbed-slug]]
   +[[survivor-slug]]
   ```

3. **Run the patch**. Verify `success: true` for every file.

4. **Verify no residual links:**
   ```
   search_files(target='content', pattern='absorbed-slug', path='~/wiki/')
   ```
   — must return zero hits. If any remain, they're in a file the patch missed.
   Add another `*** Update File` block and re-apply.

### Phase 4: Remove index & log references

- Delete the absorbed page's entry from `index.md` (if index exists).
- Delete the absorbed file: `rm entities/absorbed-slug.md` (and any duplicate
  variant in `lessons/` or elsewhere from a prior refactor).
- Update the log entry for this session: strike the deleted file's name.

### Phase 5: Validate

| Check | Method |
|-------|--------|
| No broken wikilinks to old slug | `search_files(pattern='absorbed-slug')` — must be 0 |
| All surviving pages still have ≥2 outbound links | `grep -oE '\[\[[^]]+\]\]'` per page |
| Frontmatter intact on all touched pages | `grep '^---$'` — delimiters present |
| Absorbed page file deleted | `ls entities/absorbed-slug.md` should error |
| Index no longer lists absorbed page | `grep 'absorbed' index.md` should be empty |

## Anti-Patterns

- ❌ **Don't skip the link-rewrite search.** A single missed `[[absorbed-slug]]`
  creates a broken link. Run the grep post-patch.
- ❌ **Don't delete the file before patching links.** Patch first, delete second.
- ❌ **Don't rename the absorbed file as a redirect.** Most markdown wiki engines
  don't follow rename-redirects. Full relinking + deletion is the only safe path.
- ❌ **Don't use `replace_all=true` on a V4A patch block with ambiguous context.**
  Use `replace_all` only per-operation inside the patch body — not on the block
  itself — or you risk patching the wrong occurrence across unrelated files.
- ❌ **Don't forget to update the log.** Future sessions reading `log.md` will
  see the absorbed page listed as created but not notice it's gone. Strike it
  from the creation entry or add a consolidation log entry.

## Worked example (2026-07-17)

**Context:** Wiki ingestion from Obsidian Vault produced `entities/working-agreement-yuno-basti.md`
as a separate entity. After review, its content (operational rules, risk classes, secret policy)
was a natural subsection of `entities/yuno.md`.

**Execution:**
1. Absorbed content from `working-agreement-yuno-basti.md` into `yuno.md` as new section
2. Crafted V4A multi-file patch: 7 files, ~14 link replacements
3. Deleted `entities/working-agreement-yuno-basti.md` and stale `lessons/` variant
4. Removed from `index.md` + updated `log.md`
5. Final grep confirmed zero residual references
