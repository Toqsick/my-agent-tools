# Phase 0 — Clone-Inventar Commands

Für jeden Klon ausführen:

```bash
# Branch, Remote, Working-Tree
cd /pfad/zu/klon
git status --short -b
git remote -v
git log --oneline -5

# Tracked Files, Branches, Untracked
git ls-files | wc -l
git branch -a | wc -l
git status --porcelain | grep '^??' | wc -l   # untracked count

# Relation zu origin/develop
git fetch origin develop   # einmal reicht für alle Klone
git rev-list --left-right --count origin/develop...HEAD
git log --oneline origin/develop..HEAD     # ahead
git log --oneline HEAD..origin/develop     # behind
```

**Wichtig:** `git fetch origin develop` nur **einmal** ausführen und für alle
Klone denselben Referenzstand nutzen (fetch ist read-only, idempotent).