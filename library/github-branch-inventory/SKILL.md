---
name: github-branch-inventory
description: "Use when user asks for multi-repo branch staleness scan, branch inventory, cleanup of stale GitHub branches. NOT for single-repo branch ops (use github-pr-workflow). Multi-repo branch staleness scans, branch inventory with cleanup."
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
    - Branches
    - Cleanup
    - Repository-Management
    - Audit
    - Hygiene
    related_skills:
    - github-repo-management
    - github-auth
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['branch', 'repo', 'multi', 'staleness', 'inventory']
keywords: ['branch', 'repo', 'multi', 'staleness', 'inventory']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['github-pr-workflow', 'pr-ship-pattern']
---


# GitHub Branch Inventory & Cleanup

Read-only inventory of every branch across multiple repos, classified by staleness, with auto-delete heuristics and bulk-cleanup patterns. Companion to `github-repo-management` (which covers clone/create/fork — does **not** cover branch sweeps).

## When to use this skill

- "Branch-Cleanup-Scan", "scan all repos for stale branches"
- "Welche Branches sind alt", "aufräumen alle Repos", "branch hygiene"
- "Welche feature-Branches sind outdated?"
- Any task that needs **last-commit date per branch** (per-repo or multi-repo)
- Any task that needs to **classify** branches by name pattern (e.g. `backup/*`, `copilot/*`, `import/*`)

## Auth fallback chain (CRITICAL — try in order)

When listing branches across multiple repos:

| Tier | Tool | When to use |
|---|---|---|
| 1 | `gh api` CLI | **Default.** Always available when `gh auth status` returns OK; uses your own PAT from keyring |
| 2 | `curl` + `GITHUB_TOKEN` | Headless/script-only environments without `gh` |
| 3 | `mcp__github__list_branches` etc. | Last resort — sometimes the MCP GitHub server has a stale token returning **401 Bad Credentials** or **"server is unreachable after 3 consecutive failures"**. If that happens, **stop, don't loop, switch to tier 1 or 2** |

> **Pitfall (encountered 2026-07-07):** the MCP GitHub server in a Hermes session can fail with 401 + then "unreachable", seemingly permanently, even though `gh auth status` shows the user authenticated. Don't burn 3+ retries on `mcp__github__list_branches` — fall back to `gh api` immediately and note the MCP failure in the report's "Issues encountered" section.

Pre-flight check (run this once per session):

```bash
gh --version && gh auth status 2>&1 | head -3
```

If `gh` is missing, fall through to tier 2.

## The /branches API gotcha

`GET /repos/{owner}/{repo}/branches` returns only `name` and `commit.sha` (a URL) **per branch**. It does **not** include the commit date or message.

```json
{
  "name": "develop",
  "commit": {"sha": "abc123...", "url": "https://api.github.com/repos/.../commits/abc123..."},
  "protected": false
}
```

Naive reads of `.commit.committer.date` from this response return `null`. **Do not waste time debugging a "no date" issue — that's by design.**

The correct path: one extra request per branch against the commits endpoint, keyed by the SHA from the previous response:

```bash
gh api repos/$OWNER/$repo/commits/$sha \
  --jq '.commit.committer.date // .commit.author.date // ""'
```

Alternative form **does not work** well: `GET /commits?sha=$branch&per_page=1` — when `$sha` is already a hash, `?sha=` filters further off that commit (parent or below) and usually returns empty. Stick to the direct ref endpoint.

## Staleness classification

Compute `age_days = floor((reference_epoch - commit_epoch) / 86400)` and bucket:

| Age (days) | Status | Meaning |
|---|---|---|
| ≤ 14 | ACTIVE | Routine active-work branch, leave alone |
| 15-30 | WARN | Worth a quick human check — backups, imports, single-shot fixes |
| > 30 | STALE | Candidate for deletion unless protected |

Reference date is whatever "today" is at scan time. For multi-day scripted sweeps, pass `REFERENCE_DATE=YYYY-MM-DD` to make the run deterministic.

## Multi-repo scan script

A reusable scan script lives at `scripts/branch_cleanup_scan.sh` in this skill. It takes `OWNER` and a space-separated `REPOS` list, fetches every branch's last-commit date, and emits a TSV you can pipe into Markdown-report generators.

```bash
OWNER=Toqsick \
REPOS="greyscripts hermes-v7 MaxClaw hermes-v7-sse-dashboard multi-agent-workflows" \
REFERENCE_DATE=2026-07-07 \
THRESHOLD_DAYS=30 \
OUTPUT_PREFIX=/tmp/branch_cleanup \
./scripts/branch_cleanup_scan.sh
```

Output: `branch_cleanup.tsv` with columns `repo, branch, sha, date, age_days, status`. Top of stderr shows counts (`STALE`, `WARN`, `ACTIVE`).

## Auto-delete-candidate heuristics

Branch-name patterns that signal ephemeral-by-design. Flag for delete **as soon as** they cross 30 days, **regardless of commit activity**:

| Pattern | Why ephemeral |
|---|---|
| `backup/*` | One-off snapshots; never long-lived |
| `copilot/task-<id>-<uuid>-*` | Auto-generated by Copilot Coding Agent; safe after PR merge |
| `copilot/<sha>` | Branch-name IS a commit hash; ephemeral |
| `copilot/actions-run-<id>` | Tied to a specific Actions run |
| `master` alongside `main` (in same repo) | Default-branch conflict; pick one (usually rename `master` → `main`) |
| `translation/<lang>-N` with N ≥ 2 | Superseded snapshots |
| `import/*` with 1-2 commits | Importer branches terminate after merge |
| `ci/<name>` and `docs/<name>` | Config/doc tweaks, usually merged within days |

## Protect-before-delete checklist

Before deleting any branch, cross-check carve-outs:

- [ ] Not the repo's default branch (`gh repo view $OWNER/$REPO --json defaultBranchRef`)
- [ ] No open PR (`gh pr list --state open --head $BRANCH --json number,title`)
- [ ] Not protected (`gh api repos/$OWNER/$REPO/branches/$BRANCH/protection` — 404 means unprotected)
- [ ] Tip commit not unreachable from default (`git log --not default...branch`)

> **Never delete the default branch.** GitHub's API will reject it, but automation can race past the check.

## Delete branches (after approval)

**With gh:**

```bash
gh api -X DELETE repos/$OWNER/$REPO/git/refs/heads/$BRANCH
# or, with push access:
git push origin --delete $BRANCH
```

**With curl:**

```bash
curl -s -X DELETE \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$OWNER/$REPO/git/refs/heads/$BRANCH
```

## Report output shape

A useful scan report contains (in this order):

1. **Summary table** — repos scanned, total branches, STALE/WARN/ACTIVE counts, deletion-safe-now count
2. **Full table per repo** — every branch with date, age, status, recommendation
3. **Pattern-based recommendations** — branches flagged by heuristics
4. **Issues encountered** — auth failures, API gotchas, MCP fallbacks
5. **Repro block** — exact command(s) used, so the next sweep (7 days later) is one copy-paste

A Markdown output template lives at `templates/branch_cleanup_report.md` — fill in the placeholders, group branches per repo, done.

## Quick reference

| Action | Command |
|---|---|
| List branches (gh) | `gh api repos/$OWNER/$REPO/branches --paginate --jq '.[] | "\(.name)\t\(.commit.sha)"'` |
| Last-commit date (gh) | `gh api repos/$OWNER/$REPO/commits/$sha --jq '.commit.committer.date // .commit.author.date'` |
| Open PRs on branch | `gh pr list --state open --head $BRANCH` |
| Branch protection | `gh api repos/$OWNER/$REPO/branches/$BRANCH/protection` |
| Default branch | `gh repo view $OWNER/$REPO --json defaultBranchRef` |
| Delete branch (gh) | `gh api -X DELETE repos/$OWNER/$REPO/git/refs/heads/$BRANCH` |

## Reproducibility checklist

Before declaring the scan done, capture in the report:

- `OWNER` and full `REPOS` list used
- `REFERENCE_DATE` (so re-runs 7 days later compare apples-to-apples)
- `THRESHOLD_DAYS`
- Exact one-liner command for re-runs
- Any auth fallbacks triggered (MCP failures, etc.)
