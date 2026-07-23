# Cross-Repository PR Flow (Fork → Upstream)

Use when contributing a fix from your fork (`<your-account>/<repo>`) into an upstream repo (`<org>/<repo>`) where you don't have direct push rights. The `third-party-bundle-patch-release` skill follows this flow end-to-end.

## Detect your clone's origin state

```bash
set -euo pipefail
git remote get-url origin
# Two expected states:
#   https://github.com/<your-account>/<repo>.git  → you have the fork; add "upstream" if missing
#   https://github.com/<org>/<repo>.git            → you have the upstream; need to create the fork

UPSTREAM=$(git remote get-url upstream 2>/dev/null || echo "")
if [ -z "$UPSTREAM" ]; then
    git remote add upstream https://github.com/<org>/<repo>.git
    git fetch upstream main
fi
```

## Branch from `upstream/main`, not from `origin/main`

```bash
set -euo pipefail
git checkout -b my-fix-branch upstream/main
```

## PR creation sequence (cross-repo)

```bash
set -euo pipefail
# 1. Open on the fork first (always succeeds with your token)
gh pr create \
  --repo <your-account>/<repo> \
  --head my-fix-branch \
  --base main \
  --title "fix: description" \
  --body-file PR_BODY.md

# 2. Then create the cross-repo PR against upstream.
#    gh REQUIRES the owner-qualified head ref, NOT a bare branch name:
gh pr create \
  --repo <org>/<repo> \
  --head <your-account>:my-fix-branch \
  --base main \
  --title "fix: description" \
  --body-file PR_BODY.md
```

## Reviewer-Ping pitfall on cross-repo PRs

`gh pr create --reviewer <handle>` against a cross-repo PR fails with:

```
pull request update failed: GraphQL: <your-account> does not have the correct
permissions to execute `RequestReviewsByLogin`
```

The PR is created fine; only the reviewer-request mutation fails.

**Workaround:** drop `--reviewer` and add the reviewer through the GitHub UI ("Reviewers" sidebar on the PR page). The maintainer will also see the new cross-repo PR via their own "cross-repo PR opened against your repo" notification — it's not silent.

## Cleanup the fork-internal duplicate PR

After the cross-repo PR is open, the fork-internal PR is redundant. Close it with a pointer:

```bash
set -euo pipefail
gh pr close <n> --repo <your-account>/<repo> \
  --comment "Closing fork-internal PR — superseded by cross-repo PR <upstream-org-repo-url>"
```

## Cross-Repo PR Pitfalls

| # | Pitfall | Symptom | Fix |
|---|---------|---------|-----|
| 1 | **`git rm -r <skill-path>` then bulk-copy from external working-copy** | All upstream files under that path get staged as `D`, including `references/`, `CHANGELOG.md`, or sub-trees you meant to preserve. Final diff looks correct but you've already staged deletions that hit `git commit`. | Either `git rm <specific-files>` (not `-r`) OR copy upstream files back BEFORE commit: `git checkout upstream/main -- <path>/<sub-path>`. Verify with `git status --short -- <path>` before commit. |
| 2 | **Bare `--head` against upstream repo** | `gh pr create --repo <upstream-org>` fails with `Head sha can't be blank, Base sha can't be blank, No commits between main and <branch>, Head ref must be a branch`. The cross-repo call resolves the head against the upstream repo, not your fork. | Use `--head <your-account>:branch` (owner-qualified). |
| 3 | **`--reviewer <handle>` on cross-repo PR silently rejected** | See above. | Drop `--reviewer` and use the UI. |
| 4 | **Forgetting to fetch `upstream` after creating the fork** | `git checkout -b fix upstream/main` errors because upstream isn't a known remote. The branch tracks your own fork's stale `main`. | `git remote add upstream <url> && git fetch upstream main` immediately after fork creation. |
| 5 | **Restoring an upstream sub-tree after destructive cleanup** | After `git rm -r <skill-path>` you rebuild from a working-copy, but the working-copy didn't have everything the upstream had (e.g. `references/`). The commit "fixes" the missing files. | After every destructive cleanup, run `git checkout upstream/main -- <every-subtree-you-didn't-intend-to-touch>` and verify with `git diff --stat upstream/main -- <path>` before commit. |

## Real-world walkthrough (validated 2026-07-11)

End-to-end run that produced https://github.com/NousResearch/hermes-agent/pull/62526 from a v1.0.2 third-party skill ZIP:

1. ZIP inspection → 3 confirmed bugs → patches in working-copy under `20-Workspace/kanban-video-orchestrator-v1.0.3-yuno-fix/`
2. Smoke-test against fake-hermes shim with dummy assets → all 10 profiles created, all asset copies OK
3. VERSION/CHANGELOG/manifest bumped to v1.0.3, ZIP packaged, copied to `~/.hermes/kanban/`
4. Fork of `NousResearch/hermes-agent` already existed as `Toqsick/hermes-agent`
5. `gh repo fork --clone` skipped, just cloned local + added `upstream` remote
6. Branch `yuno/fix-orchestrator-v1.0.3` from `upstream/main`
7. Working-copy files copied into skill-path, then `git checkout upstream/main -- references/` to restore sub-trees the working-copy didn't have (Pitfall #1 + #5 caught immediately)
8. `git checkout upstream/main -- SKILL.md` + `sed -i 's/version: 1.0.0/version: 1.0.3/'` to keep upstream's metadata and only bump version
9. Commit + push to fork
10. `gh pr create --repo Toqsick/...` succeeded (#1), `gh pr create --repo NousResearch/... --head Toqsick:branch` succeeded (#62526)
11. `--reviewer alt-glitch` rejected (Pitfall #3) — reviewer left for manual UI ping
12. Closed fork-internal #1 with pointer to #62526

## Related

- `third-party-bundle-patch-release` — the upstream skill whose workflow this file documents
- `references/github-pr-workflow.md` — same-repo PR lifecycle (the foundation this file extends)
- `references/mcp-github-quirks.md` — when MCP auth is dead, use `gh` + `git clone https` as fallback