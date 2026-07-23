---
name: github-pr-merge-readiness
description: "Use when user asks for assessing PR merge-readiness, CI diagnostics, blocking-check identification for a PR. NOT for opening/merging PRs (use github-pr-workflow) or repo-wide audits. Assess one or more open PRs for merge-readiness — CI diagnostics, blocking checks."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - GitHub
    - Pull-Requests
    - Code-Review
    - CI/CD
    - Merge
    related_skills:
    - github-workflow
    - github-code-review
    - github-pr-workflow
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['merge', 'readiness', 'diagnostics', 'blocking', 'user']
keywords: ['merge', 'readiness', 'diagnostics', 'blocking', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['github-pr-workflow']
---


# GitHub PR Merge-Readiness Assessment

Distinct from **code review** (which asks "is the code right?"). Merge-readiness asks "is this PR safe and correctly sequenced to merge *right now*?". Use when the user wants a structured merge-decision report rather than a code-quality review.

## When to load this skill

Trigger phrases:
- "merge-readiness", "ready to merge", "can I merge this?"
- "is this PR safe?", "merge this PR"
- "review these PRs for merge", "PR #N and #M — which first?"
- "two PRs conflict?", "merge-order for these PRs"
- Any explicit "merge-decision" or "MERGE/NEEDS-WORK/CLOSE" verdict request

**Do NOT load** for pure code-quality reviews, single-PR "look at this PR" without merge framing, or local pre-push reviews (use `github-code-review` / `github-workflow` instead).

## Prerequisites

- `gh` CLI authenticated with `repo` scope (preferred path — see "MCP fallback" pitfall below)
- Read-only by default — never merge, close, or label without explicit user instruction

---

## 1. Capture One-Row-Per-PR Summary

Use `--json` to grab everything in one call:

```bash
gh pr view N --json title,state,isDraft,mergeable,mergeStateStatus,additions,deletions,changedFiles,headRefName,baseRefName,reviews,latestReviews,statusCheckRollup
```

Capture these fields (most important first):

| Field | What it tells you |
|---|---|
| `state` | OPEN / CLOSED / MERGED |
| `isDraft` | Draft PRs are never merge-ready, regardless of CI |
| `mergeable` | `MERGEABLE` / `CONFLICTING` / `UNKNOWN` |
| `mergeStateStatus` | `CLEAN` / `DIRTY` / `UNSTABLE` / `BLOCKED` — **the real merge-readiness signal** |
| `statusCheckRollup[]` | Per-check `conclusion` (FAILURE/SKIPPED/SUCCESS) and which files it owns |
| `additions` / `changedFiles` | Scope-hygiene indicator (see §4) |
| `reviews` | Coverage signal — 0 reviews on >1k LOC is a flag |
| `headRefName` / `baseRefName` | Detect same-base PRs for cross-PR analysis |

### JSON field-name pitfalls (verified via `gh` v2.93)

- `behindBy` / `aheadBy` **do not exist** — correct fields are `mergeStateStatus` and `mergeable`. Trying wrong names returns a "Unknown JSON field" error with the full available list.
- `statusCheckRollup` = `[]` (empty array) means **no CI workflows ran on this branch** — NOT "CI skipped". Different diagnosis. Triggers when the branch lacks the workflow trigger or has never been pushed to a path Actions watches.
- A `SKIPPED` check usually means a **prior check in the same job failed** (e.g. Typecheck FAIL → Tests SKIP). Diagnose the dependency, not the skipped check.

---

## 2. CI Failure Diagnosis — Where the Failure Actually Lives

`statusCheckRollup` can show FAILURE on a check that the PR didn't author. Two patterns:

1. **The failing check owns files outside the PR's scope** → the failure is pre-existing on `main`, exposed because the PR added new tooling (e.g. a new `tsconfig.json` strict-mode check that lights up old files). Report as: *"pre-existing in main, made visible by this PR's tooling — not the PR's fault to fix but blocks their CI"*.
2. **One check is SKIPPED because a prior check in the same job failed** → look at the dependency, not the skipped check.

### Get the failing-run logs

```bash
gh run list --branch <branch> --limit 5
gh run view <run-id> --log-failed
```

The log output mixes step labels with raw command lines — search for `##[error]` markers to surface failure messages quickly. `tail -120` is usually enough.

---

## 3. Draft-PR Handling

A draft PR's body checklist is *intent*, not *status*. Unchecked `[ ]` items in a draft are expected — **do not** conflate them with "this PR is broken".

Always read `isDraft` first. **Never recommend MERGE on a draft**, even if all checks are green. The default verdict for a draft is `WIP` / `WAIT` — explain what's blocking the flip-to-ready.

---

## 4. Scope-Hygiene Red Flags

A PR is unhealthy (regardless of CI green) if it includes any of:

| Signal | Why it's bad |
|---|---|
| `coverage/**`, `*.lcov`, `coverage-final.json`, generated HTML coverage | Generated artifacts, must be in `.gitignore` |
| `logs/*.jsonl`, runtime audit logs | Never source — indicates dirty working tree |
| `package-lock.json` with thousands of added lines alongside a small code change | Likely ran `npm install` with unrelated packages |
| `*.test.js` + `*.test.ts` mixed in the same PR | Two test strategies coexist — split signal |
| File-count >50 for a feature described in <200 words | Omnibus PR — recommend splitting |
| Files in diff that aren't mentioned in PR body | Hygiene risk; body claims scope X but diff contains Y |

**Report these first**, before any code-quality findings.

---

## 5. Cross-PR Conflict Detection

When the user asks about multiple PRs together ("can I merge these in order?", "do #7 and #8 conflict?"):

1. Get `headRefName` for each.
2. Extract their overlapping files: `gh pr diff N -- <path>` — **one path at a time** (see pitfall below).
3. Look for overlapping edits to the same file with different content, especially:
   - `package.json` (deps, scripts)
   - `tsconfig.json` / `babel.config.js` / `.eslintrc*` (build config)
   - `.github/workflows/*.yml` (CI definition)
   - Lockfiles
4. Read PR bodies for **undeclared scope**: many PRs carry fixes to files not mentioned in their description. Flag as "body says X but diff also contains Y" — that's a hygiene problem separate from conflicts.
5. Produce a recommended merge order, e.g.:
   > *"Merge #8 PR-B first (Babel-Setup), then rebase #7 against it. #7's `ts-jest` choice must yield to #8's `babel-jest`."*

---

## 6. Output Format

Do NOT use the standard "Critical/Warnings/Suggestions" template (that's for code review). Use a **per-PR table + verdict** instead:

```markdown
## PR #N — <title>
| Metric            | Value |
|-------------------|-------|
| Branch / Base     | `feat/x` → `main` |
| State / Mergeable | OPEN / MERGEABLE |
| Merge-State       | UNSTABLE (CI rot) |
| Additions / Files | +4.550 / 8 files |
| Reviews / Draft   | 0 / Nein |
| CI                | FAIL auf Typecheck, Tests SKIPPED |

### Verdict: NEEDS-WORK
1. <concrete blocking item>
2. <concrete blocking item>

### Cross-PR
- Konflikt mit PR #M in: babel.config.js, package.json
- Empfohlene Reihenfolge: #M zuerst, dann #N nach Rebase
```

Verdict vocabulary:
- **MERGE** — open, not draft, MERGEABLE, all checks SUCCESS, hygiene clean, has reviews
- **NEEDS-WORK** — mergeable but has CI failure, conflict, missing review, or undeclared scope
- **CLOSE** — wrong approach, duplicate, abandoned, or scope-creep beyond salvageable
- **WIP / WAIT** — draft, or depends on another PR merging first

---

## 7. Pitfalls

### `gh pr diff` path-filter limit

`gh pr diff N -- file1 file2` **fails** with `accepts at most 1 arg(s), received 2`. You can only filter by one path at a time. Workarounds:

- One-path filter: `gh pr diff N -- package.json` then `gh pr diff N -- tsconfig.json` (sequential calls).
- For large PRs (>20 files) where you want to inspect each separately, dump the full diff and split it:
  ```bash
  gh pr diff N > /tmp/prN.diff
  csplit -z -f /tmp/prN- -b '%03d.diff' /tmp/prN.diff '/^diff --git /' '{*}'
  # Then inspect /tmp/prN-001.diff, /tmp/prN-002.diff, etc.
  ```
- `awk '/^diff --git a\/<file>/,/^diff --git/' /tmp/prN.diff` is **flaky** because the last block has no terminating `diff --git` — prefer `csplit`.

### GitHub MCP unreachable

If `mcp__github__*` tools fail 3+ times with "MCP server is unreachable after 3 consecutive failures", **do not retry** — switch immediately to `gh` CLI. The bundled `github-workflow` skill has the full fallback recipe; quick checklist:

```bash
gh auth status   # verify scope
gh pr view N --json <fields>
gh pr diff N
gh run view <run-id> --log-failed
```

`repo` token scope is sufficient for all read-only operations.

### PR-Body is not the source-of-truth for scope

Always cross-check `gh pr diff --name-only` against the PR body. Items in the diff but missing from the body are *undeclared scope* — flag them as a hygiene issue. Verified pattern: PRs with WIP checklists often sneak in depp-fixes, log files, or unrelated tooling tweaks not in the description.

### `--log-failed` output is verbose

`gh run view <id> --log-failed` mixes step labels, raw commands, ANSI escapes (`^[[36;1m`), and actual error messages. Practical tips:
- Pipe to `tail -120` to skip the git-checkout boilerplate.
- Grep for `##[error]` to surface real failures: `gh run view <id> --log-failed 2>&1 | grep -E '##\[error\]'`
- `exit_code: 2` at the end is normal — the run failed, that's why you're reading the log.

### `coverage/` and `logs/` in diff = working-tree hygiene

If a PR's diff contains `coverage/lcov-report/*.html` or `logs/audit.jsonl`, the author has either:
- Never added `.gitignore` entries for these (most common)
- Run tests locally and `git add .`-ed the result

Before any other recommendation, flag this as the first action item — adding `.gitignore` entries and re-basing will eliminate ~50% of the PR's file count. The `.gitignore` snippet to recommend:

```gitignore
# Coverage artifacts
coverage/

# Local audit logs
logs/*.jsonl
!logs/.gitkeep
```

### User briefs can be wrong about file names and PR state

When the user hands you a brief that names specific files or claims specific PR states (e.g. "PR #8 is still WIP and conflicts with #7"), **verify against the actual repo before trusting**. Two fast checks:

```bash
# File name: list the directory the brief mentions
ls src/depp/   # or wherever the brief says the file lives

# PR state: re-pull fresh JSON, don't rely on cached knowledge
gh pr view N -R owner/repo --json state,isDraft,mergeable,mergeStateStatus
```

Patterns to watch for:
- **Wrong file names** — common when the brief was written from memory or from an earlier session; e.g. brief says `depp-truncation-detector.ts` but the actual file is `truncation-detector.ts` (no prefix).
- **Wrong PR state** — common when content was already merged via a different PR number; e.g. brief says "PR #8 is WIP and conflicts with #7" but #8's content is already in `main` via #9/#10.
- **Wrong conflict assumptions** — brief says "X and Y conflict" but Y is already in `main`, leaving only a stack-decision question.

Document any such corrections in your final report ("**Correction vs brief:** ...") so the user sees the verification chain.

### Bot-authored PRs need commit-message inspection

A PR from `app/copilot-swe-agent` (or similar auto-PR bots) can look legitimate at first glance — the diff is large, the body has a checklist, the commits have proper hashes. But the last commit may be a recovery-commit with a revealing message like `"Changes before error encountered"`. Always check the last 1-3 commits on the PR's head branch before recommending merge/split/close:

```bash
git fetch origin "refs/pull/N/head:prN"
git log --format='%H %an %s' prN | head -5
```

If the latest commit is an aborted bot run, the PR is **functionally obsolete** even if `state: OPEN` — recommend close with a superseded-by comment, not a merge or split.

### Duplicate files between directories cause "phantom" TS errors

When the same logical file lives at two paths (e.g. `src/depp/depp-orchestrator.ts` and `src/roles/depp-orchestrator.ts`, byte-identical), TS errors in one copy's imports won't show up in the other. Verify with `ls -la` + `cmp` before assuming a fix is needed in one place vs. the other:

```bash
ls -la src/depp/foo.ts src/roles/foo.ts
cmp src/depp/foo.ts src/roles/foo.ts   # exit 0 = identical
```

The `import { X } from './y.js'` style (Node ESM resolution) only works if the target is in the same directory. If the file is duplicated at `src/X/foo.ts` and `src/Y/foo.ts`, the one in `src/Y/` must import from `'../X/y.js'`. This is a common source of `TS2307: Cannot find module` errors during rebases onto branches that add new directory structure.

### `npx tsc --noEmit` is the fastest pre-existing-error reproducer

Don't wait for CI to confirm TS errors are pre-existing. Locally:

```bash
git checkout main && npm install && npx tsc --noEmit
```

Runs in 1-2 seconds once `node_modules/` exists. Same errors as CI will show up locally. This lets you confirm "yes, these are pre-existing in main, not caused by the PR" before writing the merge-readiness verdict.

### Branches with no common ancestor require pre-merge conflict-surface assessment

When merging branches that share **zero** common ancestors (e.g. `git merge-base <branch-a> <branch-b>` exits with 1), GitHub's `mergeable: MERGEABLE` status is **meaningless** — GitHub only checks fast-forward or clean-rebase scenarios. The real conflict surface only appears when you attempt the merge locally.

A pre-merge assessment plan that avoided a disaster in the real `Toqsick/hermes-v7` repo (see `references/session-2026-07-07-hermes-v7-issue5-integration.md`):

1. **Check ancestry first:** `git merge-base <branch-a> <branch-b>` — exit code 1 means no shared ancestor.
2. **Use `--allow-unrelated-histories` as a dry-run** to surface the conflict count:
   ```bash
   git merge --no-commit --no-ff --allow-unrelated-histories origin/<other-branch> 2>&1 | grep -c "KONFLIKT\|CONFLICT"
   git merge --abort  # always abort, even if 0 conflicts
   ```
3. **Categorize conflicts by layer** — not just "24 conflicts" but "24 conflicts across security (4), storage (2), config (3), core (3), deps (1), workflow (2), docs (2)".
4. **Make a go/no-go decision:**
   - **<5 conflicts, no security layer** → safe to resolve inline, document in merge commit.
   - **5-10 conflicts, non-critical layers** → attempt merge with file-by-file review, abort on surprises.
   - **>10 conflicts or ANY security-layer conflict** → **do not merge blind**. Abort, close the source issue with a detailed resolution comment, and create a follow-up integration tracking issue with conflict-by-conflict guidance.
5. **Document the decision** in a detailed resolution comment on the source issue (see reference file for the format), then create a follow-up issue with:
   - Per-file conflict table (layer | file | risk-level)
   - Security-risk callouts for specific files
   - Sub-task checklist (re-root branch → resolve low-risk files → resolve security files → integration test → CHANGELOG)
   - "Done when" criteria

**Why this pattern matters:** The alternative is a blind `--allow-unrelated-histories` merge that produces 24 add/add conflicts you can't resolve without understanding both branches' design intent. The conflict surface itself is the signal that the two branches need a human-guided integration, not a mechanical merge.

---

## See also

- `references/session-2026-07-07-hermes-v7-pr7-pr8.md` — Worked example: full merge-readiness review of two conflicting PRs on Toqsick/hermes-v7 (PR #7 SecurityKernel + PR #8 plugin-registry), with the actual CI failure transcript, scope-vs-body audit table, and the recommended merge-order resolution. Use as a template when you need to write up a multi-PR merge-readiness report.
- `references/session-2026-07-07-hermes-v7-issue5-integration.md` — Worked example: unrelated-histories merge assessment for Issue #5 (V7.1 Plugin-Registry) on Toqsick/hermes-v7. Documents the pre-merge ancestor check, conflict-surface quantification (24 add/add conflicts across 7 layers), go/no-go decision, issue-closure with detailed resolution comment, and follow-up integration tracking issue creation. Use as a template when branches have zero common ancestor and you need to decide whether to merge blind or create a tracking issue.
