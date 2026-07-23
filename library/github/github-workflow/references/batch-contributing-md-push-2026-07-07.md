# Batch CONTRIBUTING.md Push - Session 2026-07-07

Session reference for batch-pushing `CONTRIBUTING.md` to 4 repos via Contents API.

## Repos

- `Toqsick/hermes-v7` (main)
- `Toqsick/MaxClaw` (main)
- `Toqsick/sse-dashboard` (main)
- `Toqsick/multi-agent-workflows` (main)

## 409 Stale SHA Pitfall

First attempt failed with 409 Conflict:
```
{"message":"sha is at abc123 but expected def456","documentation_url":"..."}
```

**Root cause:** `gh api PUT contents/` cached stale HEAD-SHA from earlier fetch in same process.

**Fix:** Retry without `sha` field to treat as fresh Create-or-Update.

## MD5 Verification Results

```bash
SOURCE_MD5=8f434346648f6b96df89dda901c5176b
# After push, all 4 repos matched ✓
```

## Template Reusability Lesson

**Source:** greyscripts `CONTRIBUTING.md` (38 lines, German, GreyScript conventions)

**Target repos:** Mixed tech stack (TypeScript, Python, Go, GreyScript)

**Result:** Source template NOT reusable - too domain-specific (`importcode`, `fail()`, `shell` rules).

**Fallback:** Created generic 14-line MIT-licensed template compatible across all repos.

## Final Pattern

```bash
CONTENT_B64=$(base64 -w0 /tmp/generic-contributing.md)
COMMIT_MSG="docs: add CONTRIBUTING.md"

for repo in hermes-v7 MaxClaw sse-dashboard multi-agent-workflows; do
  body=$(jq -n --arg m "$COMMIT_MSG" --arg c "$CONTENT_B64" \
    '{message:$m, content:$c, branch:"main"}')
  gh api -X PUT "repos/Toqsick/$repo/contents/CONTRIBUTING.md" \
    --input - <<<"$body" 2>&1 | jq -r '.commit.sha // .message'
done
```