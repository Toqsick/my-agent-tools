# Skill Conversion & Config-Sync Workflow

When user asks to 'push my skills to github', 'sync skills between devices', 'convert skills from <X> to <Y>' — these are common, distinct from PR work, and follow a non-obvious pattern. Apply this 7-step workflow:

## 7-Step Workflow

1. **Inventory target repo first.** `gh repo view <name> --json name,description,pushedAt,defaultBranchRef`. Discover if repo exists or whether `gh repo create` would fail silently.
2. **If repo exists and has unrelated code:** `gh repo clone <name> ~/worktree`. Don't `gh repo create` — it errors with `Name already exists`.
3. **If repo doesn't exist** and you already have a local working tree ready (e.g. `/tmp` stage dir), use the **atomic pattern**:
   ```bash
   cd /path/to/local-working-tree
   git init -q
   git config init.defaultBranch main   # ← PREVENT master-branch issue
   git add -A && git commit -q -m "Initial commit"
   gh repo create <name> --private --description "..." --source=. --push
   ```
   The `--source=. --push` flag creates the remote AND pushes in one command — no separate `git remote add` needed. **BUT:** `gh repo create` with `--source=. --push` pushes the **local** branch name as-is. If you forget `config init.defaultBranch main`, the remote gets `master`. Fix:
   ```bash
   git branch -m master main
   git push origin main
   gh repo edit --default-branch main  # update GH's default ref
   ```
   **Simpler: set `init.defaultBranch main` before git init** — then the remote gets `main` directly.

   Without `--source=. --push` (older pattern, still valid):
   ```bash
   gh repo create <name> --public --description '...'
   git remote add origin "https://github.com/USER/<name>.git"
   git push -u origin main
   ```
4. **Use HTTPS-with-token from `gh auth token`** for push, not SSH:
   ```
   TOKEN=$(gh auth token)
   git remote set-url origin "https://Toqsick:${TOKEN}@github.com/Toqsick/<repo>.git"
   git push -u origin main
   ```
   This avoids SSH-host-verification failures which turn into long debugging.
5. **Pick a flat-id namespace under one umbrella dir.** For skill conversion (Hub ↔ Hermes, etc.), never merge categories — use e.g. `skills/hub-imported/<hub-id>/`. See `software-development/skill-format-conversion` for the canonical workflow.
6. **Commit on a feature branch if the default branch is populated.** Use `git switch -c feat/skills-import-<date>`. Then `gh pr create` for review.
7. **Always include secrets-preflight** when converting skills: many skill-system source trees carry `~/.hermes/auth.json` references or hardcoded tokens. `grep -rE '(api[_-]?key|secret|password|bearer|token)[^[:space:]]{0,5}[:=]["'"'"']?[A-Za-z0-9_-]{16,}'` over the source before committing.

## Pitfall — pushing to a populated repo on `main`

```
$ git push -u origin main
To https://github.com/<owner>/<repo>.git
 ! [rejected]        main -> main (fetch first)
error: failed to push some refs
```

This means the repo has commits you don't have. Either:
1. `git fetch origin && git merge origin/main --allow-unrelated-histories` (if desired to add on top)
2. Branch instead: `git switch -c feat/skills-2026-07-03-import && git push -u origin feat/skills-2026-07-03-import && gh pr create`