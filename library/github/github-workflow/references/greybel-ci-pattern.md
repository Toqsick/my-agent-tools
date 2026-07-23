# GreyHack/Greybel CI Pattern

For GreyHack repos that build GreyScript with `greybel-js`, treat CI as a first-class issue/PR flow, not just a script edit.

## CI-First Pattern

```bash
set -euo pipefail
# 1. Create explicit CI issues before coding.
gh issue create --title '[CI] Add Greybel build verification to CI' --body-file /tmp/issue-ci-greybel-build.md --label ci,enhancement,roadmap --milestone v0.5.0
gh issue create --title '[CI] Make ci-build.sh scan active .src directories' --body-file /tmp/issue-ci-build-script.md --label ci,bug,enhancement --milestone v0.5.0

# 2. Branch from develop and implement both sides of the CI contract.
git checkout -b feat/p0-ci-greybel-build

# 3. Update the build script to scan active source dirs, not stale bin/ paths.
# 4. Add a workflow job that installs greybel-js, runs the script, and uploads outputs.
# 5. Commit, push, and open a PR with `Closes #<issue>` lines in the body.
```

## CI Shape

- `scripts/ci-build.sh` scans active `.src` directories such as `src/`, `tools/`, and `greyhack-tools/` if present.
- CI installs `greybel-js` with `npm install -g greybel-js`.
- CI runs `bash scripts/ci-build.sh --out-dir .ci-build`.
- CI uploads `.ci-build/` as an artifact.
- `.gitignore` ignores `.ci-build/`.
- Quote the workflow trigger key as `"on":` to avoid `yamllint` truthy warnings.

## Pitfalls

- Workflow TODOs may live in docs/plans instead of `.github/workflows/*.yml`; scan docs and plans too.
- `gh api repos/OWNER/REPO/milestones` defaults to POST; use `gh api -X GET 'repos/{owner}/{repo}/milestones?state=all'`.
- `gh milestone` may be unavailable in the installed gh CLI; use `gh api` for milestones.
- `gh issue create --label roadmap` fails if the label does not exist; create the label first or use existing labels.
- Use `--body-file` for `gh pr create` / `gh pr edit` when the body contains backticks/code fences; otherwise the shell may execute code inside backticks.