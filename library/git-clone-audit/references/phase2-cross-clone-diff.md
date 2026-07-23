# Phase 2 — Cross-Clone Diff Commands

```bash
# Alle non-empty Diffs (Working-Tree vs Working-Tree)
GIT_DIFF_URI=$(cd /pfad/zu/klonB && pwd)
cd /pfad/zu/klonA
git diff --no-index --ignore-cr-at-eol \
  -- . "$GIT_DIFF_URI" \
  2>/dev/null | grep "^diff --git" | wc -l

# Nur .src-Files mit non-empty Diff
git diff --no-index --ignore-cr-at-eol \
  -- . "$GIT_DIFF_URI" \
  2>/dev/null | grep "^diff --git" | sed 's|diff --git a/||; s| b/.*||' \
  | sort -u | grep '\.src$'
```

**Output:** Tabelle: **Relativer Pfad | Klon A LOC | Klon B LOC | Änderung**.