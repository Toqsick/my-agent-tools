---
name: web-archive-research
description: "Use when user asks to find historical web content, query Common Crawl CDXJ indexes, inspect captures, or fetch and parse WARC records. NOT for current-web search or scraping a live site. Provides SURT query syntax, index filtering, gzip/WARC handling, rate-limit guidance, and the bundled archive-query scripts."
version: 1.0.0
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - common-crawl
    - cdxj
    - warc
    - web-archive
    - research
    - data-mining
author: Hermes Agent
license: MIT
lane: worker-flash
reasoning_effort: high
agent: Researcher
routing_hint: '**Agent-Scope:** Deep-research, fact-checking, paper-search, knowledge-base.
  Off-scope: code-building, visual design, writing — return to Yuno.


  Routing-Spec: `yuno-team-routing`.

  '
trigger_keywords: ['query', 'and', 'warc', 'web-archive-research', 'find']
keywords: ['query', 'warc', 'user', 'asks', 'find']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

---
# Web Archive Research

Search and extract content from web archives like Common Crawl without downloading terabytes of data.

## Quick Start

Use the included script for CDXJ index queries and WARC fetching:

```bash

set -euo pipefail
python3 ~/.hermes/skills/web-archive-research/scripts/cc-search.py \
  --query "example.com/*" --limit 5 --fetch --clean
```

## How It Works

1. **Query the CDXJ Index** — finds URLs, WARC file names, offsets, lengths
2. **Byte-Range Fetch** — downloads only the relevant ~1-5 KB from S3
3. **Extract Content** — decompress gzip, parse WARC, strip HTML

## Common Crawl CDXJ Index

Base URL: `https://index.commoncrawl.org/{INDEX}-index`

| Parameter | Description | Example |
|-----------|-------------|---------|
| `url` | URL pattern (SURT format) | `example.com/*` |
| `matchType` | `exact`, `prefix`, `domain` | `domain` |
| `output` | `json` or `cdxj` | `json` |
| `limit` | Max results | `10` |
| `filter` | `status:200`, `mime:text/html` | `status:200` |
| `from` / `to` | Timestamp range | `20260508000000` |

### SURT Query Syntax

| Goal | Query |
|------|-------|
| All pages on domain | `example.com/*` |
| Subdomain | `sub.example.com/*` |
| Path prefix | `example.com/blog/*` |
| Keyword in path | `example.com/*keyword*` |

**Important:** `*.example.com/*` does NOT work. Use `example.com/*` (matches subdomains automatically via `matchType=domain`) or list the full subdomain.

## Pitfalls

### Many Sites Block Common Crawl

Sites with restrictive robots.txt appear empty:
- Reddit, HLTV, Steam Community, Medium (partial)
- **Works:** GitHub Pages, Wikipedia, open-source docs, personal blogs

### `404` means "No captures"

```json
{"message": "No Captures found for: example.com/path"}
```
Normal — page was never crawled or the crawler was blocked.

### WARC records are gzip-compressed

Always `gzip.decompress()` before parsing the HTTP response.

### Rate-limit your requests

Stay below ~2 req/s. No hard limits documented, but be polite to the free service.

## Scripts

- `scripts/cc-search.py` — Full CLI (see `--help`)
- Supports: index query, WARC fetch, HTML cleaning, JSON output

## References

- `references/cdxj-query-syntax.md` — Complete query parameter reference
