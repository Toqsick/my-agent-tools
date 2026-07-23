# GitHub Repository Management

Clone, create, fork, releases, secrets, actions.

## Full Repo Management

```bash
set -euo pipefail
# Clone/Create/Fork
gh repo clone owner/repo
gh repo create my-project --public --clone
gh repo fork owner/repo --clone

# Settings
gh repo edit --description "..." --visibility public
gh repo edit --enable-auto-merge

# Releases
gh release create v1.0.0 --title "v1.0.0" --generate-notes

# Secrets
gh secret set API_KEY --body "value"
gh secret list

# Actions
gh workflow list
gh run list --limit 10
```

## Documentation Health Audit

When the user asks to update READMEs, check what's outdated, or audit repo docs, use the pattern from `references/documentation-health-audit.md` (10 phases).

**Core phases (1–7):** Parse claims → Count state → Count support files → Verify standalone deps → Find thin sub-READMEs → Cross-reference category listings → Verify CI badges

**Post-update phases (8–10):** Markdown verification → Thin README expansion → Category table enrichment

**Common pitfalls:**
- `find . -maxdepth 2` avoids counting nested build outputs and git-internal copies
- Always exclude `bin/`, `build/`, `src/`, `test/`, `tests/`, `includes/`, `scripts/` from tool counts — these are support, not tools
- `grep -l` + `xargs` avoids false positives from backup dirs; use `find -path './de/*' -prune` to exclude import snapshots
- standalone.md is usually the most stable doc (deps don't change), main README is the most drift-prone (numbers get stale)
- After updating READMEs, always run Phase 8 (Markdown verification) — even text-only changes can break links or introduce syntax errors
- Thin READMEs (< 500B) are often template placeholders; expand with real build paths and feature descriptions (600–1100B target)

See `references/documentation-health-audit.md` for the full shell script patterns, execute_code alternatives, and a session example.