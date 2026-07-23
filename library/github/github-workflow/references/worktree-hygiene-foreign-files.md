# Worktree Hygiene — Foreign Untracked Files Before Push

**Validated 2026-07-13** with `feat/idempotency-key-patch` in
`/home/bratan/30-Library/hermes-v7/`. The feature branch had exactly the
intended commit (`src/core/types.ts`, +52 lines, additive idempotency fields)
plus **three unrelated untracked files** left in the worktree by other agents /
sessions:

- `.hermes/phase1-tech-inspector-report.md` (Phase-1 Tech-Inspector output)
- `src/storage/memory-provider.ts` (memory-provider source for an unrelated
  feature)
- `src/storage/__tests__/memory-provider.test.ts` (matching test file)

The push had to happen, but the foreign files could not be:
1. Committed with the patch (would pollute the PR diff and break code review).
2. Deleted (they belonged to other workflows that would silently break).
3. Left as-is with `git add .` (same as #1).

## The Pattern: Stash Foreign Untracked Files with a Traceable Message

```bash
set -euo pipefail
BRANCH=$(git branch --show-current)

# 1. Inventory: see every untracked file and confirm none belong to YOUR patch
git status --short --branch
git ls-files --others --exclude-standard

# 2. Read every file mentally (or open it) — verify it's foreign
#    Cross-check filenames and contents against your patch's intent.
#    A 30-second eyeball saves a corrupted commit.

# 3. Stash with a descriptive, dated, attributed message
git stash push --include-untracked -m \
  "A1 cleanup: preserve foreign untracked files before push (2026-07-13)"

# 4. Verify clean worktree
test -z "$(git status --porcelain)" && echo "CLEAN"
git status --short --branch
# Should show only `## branch-name` and no `??` lines.

# 5. Verify your intended commit is intact
git show --stat HEAD
git diff --check HEAD^

# 6. Run repo-level safety checks the patch needs (typecheck, tests)
npx tsc --noEmit
npx jest --runInBand <scope>

# 7. Push
git push -u origin "$BRANCH"

# 8. Verify remote == local SHA
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git ls-remote origin "refs/heads/$BRANCH" | cut -f1)
test "$LOCAL" = "$REMOTE" && echo "REMOTE_MATCH"

# 9. Document the stash ref in your handoff so a future session can restore
echo "stash@{0} = unrelated scratch — restore with: git stash pop"
```

## Pitfalls

### `git stash` without `--include-untracked` hides nothing

Untracked files are not moved by a plain `git stash`. They sit in the
worktree, and your `git push` may succeed but the next `git status` on the
remote branch (or a fresh clone) shows them missing. Always use
`--include-untracked` (or `--all` to also touch ignored files, but that's
rarely what you want).

### Stashing without a message

Future-you finds `stash@{0}` with no context. `git stash show` returns a
diff of the changes — useful for tracked files, useless for untracked.
The **message is the only audit trail**. Always include:

- Date (YYYY-MM-DD)
- Agent / worker-bee ID
- Reason ("before push", "before rebase", "before merge")
- Optional: where the stash should eventually return ("→ restore when X
  workflow resumes")

### Forgetting to verify HEAD after stashing

`--include-untracked` will refuse to stash tracked changes by default, but
edge cases exist (e.g. you have an intent-to-add file via `git add -N`).
Always re-run `git show --stat HEAD` after the stash to confirm the
intended commit is intact.

### `git stash pop` immediately after push

Don't. The foreign files belong to another workflow. Pop only when that
workflow asks, or hand the stash ref to the user. A popped stash is gone
forever (you can recover with `git fsck` but it's painful).

### `git clean -fd` instead of stash

`git clean -fd` **deletes** the untracked files. Use only if you've
independently verified they're truly transient (build artifacts, editor
scratch that you own). For files another agent might own, never.

### Adding ignored files to the stash by accident

`!!`-prefixed files in `git status --short --ignored` are already
`.gitignore`'d — they don't need stashing. Don't reach for `--all` unless
you specifically need to capture them.

## When This Pattern Does NOT Apply

| Situation | Right Move |
|-----------|-----------|
| Untracked files ARE part of your patch | `git add` them normally |
| Untracked files are build artifacts you own | `git clean -fd` after preview with `git clean -nd` |
| Branch is brand-new with no commit yet | `git clean -fd` (or move aside + start fresh) |
| Foreign tracked modifications + foreign untracked files | `git stash --include-untracked` (same pattern, plus tracked changes) |
| Multiple agents parallel-write to same worktree | Single-Writer lock (`single-writer-inbox` pattern) before any git operation |

## Handoff Template

When handing off the stash to another agent / session:

```text
Branch `feat/<name>` was pushed to origin as <sha>.
Three unrelated untracked files are preserved in stash@{0} on that branch:

- `.hermes/phase1-tech-inspector-report.md` — Phase-1 Tech-Inspector output
- `src/storage/memory-provider.ts` — memory-provider source (Mnemosyne)
- `src/storage/__tests__/memory-provider.test.ts` — matching test file

To restore: `git checkout feat/<name> && git stash pop`
They belong to the memory-provider feature work and must NOT be committed
on the idempotency-key-patch branch.
```

## Verification Checklist (after push, before declaring done)

- [ ] `git status` shows clean worktree
- [ ] `git show --stat HEAD` matches intended commit (same files, same diff)
- [ ] `git rev-parse HEAD` matches `git ls-remote origin <branch>` SHA
- [ ] `git push -u origin HEAD` reports the upstream tracking set
- [ ] Stash ref documented in handoff / queue file / session note
- [ ] Repo-level safety checks (typecheck, lint, tests) all green for the pushed commit

## See Also

- `references/github-pr-workflow.md` — the broader PR lifecycle
- `single-writer-inbox` (collaboration/) — when the foreign files are
  Obsidian-vault writes, the lock protocol applies before git operations
- `orchestration/deployment-landing-zone` — where multi-agent deliverables
  land (branch vs live system)