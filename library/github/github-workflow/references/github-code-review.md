# GitHub Code Review

Local and PR-level code review patterns.

## Local Changes (Pre-Push)

```bash
set -euo pipefail
git diff main...HEAD --stat      # scope
git diff main...HEAD             # full diff
git diff main...HEAD | grep -n "print\|console\.log\|TODO\|FIXME"  # debug statements
```

## PR Review on GitHub

```bash
set -euo pipefail
gh pr view 123
gh pr diff 123
git fetch origin pull/123/head:pr-123 && git checkout pr-123  # local checkout
gh pr review 123 --approve --body "LGTM"
gh pr review 123 --request-changes --body "See inline comments"
```

## Inline Comments (curl fallback)

```bash
set -euo pipefail
# Get HEAD SHA, then POST to /repos/{owner}/{repo}/pulls/{number}/reviews
```