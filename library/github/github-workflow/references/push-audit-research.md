# Push Audit Research - Session Reference

## "Was wurde kürzlich gepusht?" - Research Session

When user claims "du hast gestern gepusht" / "da wurde was committed" — the question is **"what does the remote say vs local?"**, not "what does my local log say?".

## Ground-Truth Verification Matrix

| Method | What it shows | Reliability | When to use |
|--------|---------------|-------------|-------------|
| `git ls-remote origin` | Remote SHA + Ref per branch | **Highest** | First choice for push verification |
| `git rev-parse origin/main` | Local cached remote HEAD | Medium | Compare with `git rev-parse HEAD` |
| `gh api repos/OWNER/REPO/commits` | Remote commit history | High | When MCP GitHub 401s |
| MCP GitHub | Depends on container config | Low | Fallback to `gh` or `ls-remote` |

## Verification Pattern

```bash
# 1. Check remote state (authoritative)
git ls-remote origin

# 2. Compare with local
if [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ]; then
  echo "No unpushed commits"
else
  echo "Diverged or unpushed"
fi

# 3. If MCP GitHub 401s, fall back to gh api
gh api "repos/OWNER/REPO/commits?since=$(date +%Y-%m-%d)T00:00:00Z&per_page=100" --jq 'length'
```

## Common Pitfalls

- **"Working tree clean ≠ nothing pushed"** - A clean working tree means no local changes, but commits may already be pushed.
- **"Pull says already up to date ≠ nothing pushed"** - Same as above; check remote SHA directly.
- **MCP GitHub 401 during read** - Don't retry MCP; use `gh api` or `git ls-remote` instead.
- **curl 404 on commits endpoint** - Repo is **private**, not deleted. This is useful diagnostic info.

## Private vs Public Repo Diagnostics

```bash
# Public repo (works)
curl https://api.github.com/repos/OWNER/REPO/commits
# Returns JSON with commit list

# Private repo (no auth)
curl https://api.github.com/repos/OWNER/REPO/commits
# Returns 404 {"message": "Not Found"}

# Private repo (with auth)
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/repos/OWNER/REPO/commits
# Returns JSON with commit list
```