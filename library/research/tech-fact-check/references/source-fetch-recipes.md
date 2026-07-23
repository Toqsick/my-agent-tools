# Source-Fetch Recipes (fallback when web tools are dead)

When `web_extract`, `web_search`, and `firecrawl-web` all return
"Web tools are not configured. Set FIRECRAWL_API_KEY …", this is the
fetch ladder that actually works.

## Tier 0 — check what's loaded

```bash
# Quick probe: try one built-in first to avoid wasted calls
```

If `web_extract` returns the Firecrawl error message verbatim, both
the built-ins AND firecrawl-web are dead. Jump to Tier 1.

## Tier 1 — GitHub MCP (no auth needed for public content)

```python
# Discover repos / gists / code / issues / commits
mcp__github__search_repositories(query="grok-build-exfil-repro in:name")
mcp__github__search_issues(query="Grok Build privacy exfiltration")
mcp__github__search_code(query="grok-code-session-traces")
mcp__github__search_commits(query="author:cereblab grok-build-exfil-repo")

# Read specific files
mcp__github__get_file_contents(owner="cereblab", repo="grok-build-exfil-repro",
                                path="README.md", ref="main")

# Issue threads (incl. comments)
mcp__github__list_issues(owner="cereblab", repo="grok-build-exfil-repro")
mcp__github__issue_read(method="get_comments", owner=..., repo=..., issue_number=1)

# PR reviews / diffs
mcp__github__pull_request_read(method="get_diff", owner=..., repo=..., pullNumber=...)
```

These tools work with zero API rate limits beyond GitHub's public API
quotas because they use the GitHub MCP server's bundled auth.

## Tier 2 — raw curl on GitHub's open APIs

```bash
# Gist raw content (no auth, no rate limit beyond IP)
curl -sL -H "User-Agent: hermes-factcheck/1.0" \
  "https://gist.githubusercontent.com/<user>/<gist-id>/raw"

# Repo file content
curl -sL "https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path>"

# GitHub REST API (60 req/h unauthenticated, 5000 with $GITHUB_TOKEN)
curl -sL -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/<owner>/<repo>/contents/<path>"
curl -sL "https://api.github.com/repos/<owner>/<repo>/issues?state=all"

# HN thread (HTML, lightweight)
curl -sL "https://news.ycombinator.com/item?id=<NNN>"
```

**User-Agent is mandatory** for gist / HN / many CDNs — without it the
CDN may serve a generic interstitial. Use a real-looking UA.

## Tier 3 — Wayback Machine if the live page is gone

```bash
# Wayback Machine CDX API
curl -sL "https://web.archive.org/cdx/search/cdx?url=<url>&output=json&limit=5"
```

Pair with `web-archive-research` skill for batched historical lookups.

## Tier 4 — auth-gated APIs if user provides a token

```bash
# GitHub with token
curl -sL -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/repos/<owner>/<repo>/commits"

# HuggingFace, GitLab, etc. — same pattern, swap header
```

Only request a token if Tiers 1–3 cannot reach the necessary content.
Tokens belong in environment variables, never inline.

## Tier 5 — Tell the user honestly

If all of Tiers 1–4 cannot reach the primary source, say so explicitly:

> "Cannot reach primary source. The popular retelling is the only thing
> available, so I can only verify *internal consistency* of the claim,
> not *external correspondence* with vendor reality."

This is better than paraphrasing social media and presenting it as a
fact-check. Report what's reachable, flag what's not.

## Anti-patterns

- **Don't** spam the same search with slight variations. If a key term
  doesn't surface the primary, switch terms not the verb (`in:name` →
  `in:description` → `org:`).
- **Don't** trust GitHub `in:file` code search to find secrets/strings
  — it indexes at snapshot time, not live. Use `curl` on the raw file.
- **Don't** re-use a User-Agent that looks like a bot — Cloudflare
  serves an interstitial to `python-requests/x.y` and similar default UAs.
- **Don't** issue 50+ rapid curls to api.github.com without a token — the
  IP gets 60-req/h-throttled, then 403'd for a while.

## Verified 2026-07-13

Used to fact-check "Grok 4.5 exfiltrates GitHub repos" claim end-to-end:

| Source type | Tool used | Latency |
|---|---|---|
| Gist (26 KB Markdown) | `curl .../gist/<id>/raw` | 1.2 s |
| Repro repo README | `mcp__github__get_file_contents` | ~1 s |
| HN thread + 183 comments | `curl .../item?id=...` HTML | 0.8 s |
| Koreferat (Korean) | `curl raw.githubusercontent.com/...` | 0.5 s |
| Wire-log artefacts | `mcp__github__search_repositories` | ~2 s |

Total session: 17 tool calls, all sources reachable without Firecrawl.
The firecrawl dependency is a single point of failure for fact-checking
tasks; this ladder is the resilient path.
