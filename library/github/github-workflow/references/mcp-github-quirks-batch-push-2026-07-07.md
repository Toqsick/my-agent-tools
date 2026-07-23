# MCP GitHub Quirks - Session 2026-07-07

MCP-Tool-Antwort-Fallen beim Batch-Push von `CONTRIBUTING.md` über 4 Repos.

## Tools Involved

- `mcp__github__create_or_update_file`
- `mcp__github__get_file_contents`

## Pitfall 1: "File already exists" Lie

**Symptom:**
```
MCP: {"error": "File already exists. Provide SHA."}
curl: 404 Not Found
```

**Reality:** File genuinely did NOT exist (curl 404). MCP lied but server-side write still succeeded.

**Fix:** Treat MCP write errors as soft signals, not ground truth. After any error, curl-verify:
```bash
curl -s -o /dev/null -w "%{http_code}" https://raw.githubusercontent.com/OWNER/REPO/BRANCH/PATH
```

## Pitfall 2: Sentinel Success SHA

**Symptom:**
```
MCP: {"sha":"777035533703e3b24b90916e17598aeb2f8fb17a", "content":"..."}
curl: 404 Not Found
```

**Reality:** This sentinel SHA appears for non-existent files.

**Fix:** Never trust MCP existence checks. Always curl-confirm:
```bash
curl https://api.github.com/repos/OWNER/REPO/contents/PATH?ref=BRANCH
```

## Pitfall 3: "unreachable after 3 failures" Cooldown

**Symptom:**
```
MCP server 'github' is unreachable after 3 consecutive failures. Auto-retry available in ~32s.
```

**Fix:** Do NOT keep hammering it. Switch to `gh api -X PUT` or curl with `gh auth token`:
```bash
TOKEN=$(gh auth token)
curl -H "Authorization: token $TOKEN" -X PUT \
  "https://api.github.com/repos/OWNER/REPO/contents/PATH"
```

## Fallback Pattern for 4-Repo Batch Push

```bash
TOKEN=$(gh auth token)
CONTENT_B64=$(base64 -w0 /tmp/file.md)
BODY=$(jq -n --arg m "docs: add file" --arg c "$CONTENT_B64" \
  '{message:$m, content:$c, branch:"main"}')

for repo in repo-a repo-b repo-c repo-d; do
  curl -s -H "Authorization: token $TOKEN" \
    -H "Accept: application/vnd.github+json" \
    -X PUT "https://api.github.com/repos/Toqsick/$repo/contents/FILE.md" \
    -d "$BODY" | jq -r '.commit.sha // .message'
done
```

## Key Takeaway

When MCP and curl disagree on a file's existence, **curl wins**. MCP's success metadata is not authoritative for filesystem-shape questions.