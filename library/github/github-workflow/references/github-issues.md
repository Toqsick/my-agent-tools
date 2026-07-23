# GitHub Issues

Issue management patterns and pitfalls.

## Full Issue Management

```bash
set -euo pipefail
# Create
gh issue create --title "Bug: X" --body "..." --label "bug" --assignee "@me"

# List
gh issue list --state open --label "bug"
gh issue list --assignee @me

# Manage
gh issue edit 42 --add-label "priority:high"
gh issue edit 42 --add-assignee username
gh issue comment 42 --body "Investigated — working on fix"
gh issue close 42
gh issue reopen 42
```

## Pitfalls

- **`gh issue view <N> --json ...` does NOT include `number`** (it also strips `repository`). The output gives title/body/labels/comments/state, but every field you'd reasonably expect from `gh issue list --json number,title,...` is *missing*. Python parsers that do `d['number']` get `KeyError`. Workarounds: (a) pair each `gh view` with the number you already know — `[{"number": <N>, **d}]`; (b) read numbers from `gh issue list --json number,title` separately and join. Verified 2026-07-07 on Toqsick/greyscripts triage — every per-issue read needed this fix.

- **Read-only vs mutating triage — ask before assuming.** When the user says "kategorisieren", "priorisieren", "review", "audit", default to **read-only** (categorize, write report, but do NOT add labels / comments / close anything). Explicitly note "read-only" in the report footer so the user knows. Only mutate when the user explicitly says "label them", "close the empty ones", etc. Many reviewer/external/audit profiles do not have mutation rights.

- **Cross-check the user's numerical assumptions.** If the user names a count ("alle 54 offenen Issues") or describes scope, verify against actual API state before diving in. The discrepancy is load-bearing context — the user may be working from a stale mental model, the repo was recently groomed, or they're testing whether you'll blindly trust framing. Surface the gap clearly at the top of the report; don't silently adjust and proceed. Verified 2026-07-07: user said "54", repo had 7 (other 47 closed) → flagging this upfront saved the session.

- **Triage-report shape — what the user actually wants.** A categorized, prioritized Markdown report, not just a list. Default deliverable: per-issue row with number/title/category/labels/priority/recommendation; activity check (`age_days` + `stale_days`, flag stale beyond threshold); empty-body issue detection (CI-badge-only or "[BUG]" placeholder → recommend `state_reason=not_planned`); recommended execution order based on dependency graph; summary table by category. Skip any of these only when the user signals a different deliverable.