# Documentation Health Audit

10-phase repo documentation audit for identifying outdated READMEs, broken links, and missing docs.

## Phases 1-7 (Discovery)

1. **Parse claims** - Extract all build/test/install commands from READMEs
2. **Count state** - Verify claimed files/folders actually exist
3. **Count support files** - Check if `bin/`, `scripts/`, etc. match README claims
4. **Verify standalone deps** - Ensure `standalone.md` dependencies are accurate
5. **Find thin sub-READMEs** - Identify READMEs < 500B (often placeholders)
6. **Cross-reference category listings** - Check tool lists against actual directory structure
7. **Verify CI badges** - Ensure workflow files exist and badges link correctly

## Phases 8-10 (Fix & Verify)

8. **Markdown verification** - Run markdown linters, check link validity
9. **Thin README expansion** - Expand placeholder READMEs to 600-1100B with real content
10. **Category table enrichment** - Update summary tables with current counts

## Common Pitfalls

- `find . -maxdepth 2` avoids counting nested build outputs and git-internal copies
- Always exclude `bin/`, `build/`, `src/`, `test/`, `tests/`, `includes/`, `scripts/` from tool counts
- Use `grep -l` + `xargs` to avoid false positives from backup dirs
- `standalone.md` is usually stable; main README drifts faster
- After updates, always run Phase 8 to catch new link/syntax errors

## Session Example

Audit of `Toqsick/greyscripts` on 2026-06-25:
- Found 3 thin READMEs (< 500B) that needed expansion
- Fixed 2 broken CI badge links
- Corrected 1 stale dependency list in standalone.md
- Updated tool counts after directory restructure