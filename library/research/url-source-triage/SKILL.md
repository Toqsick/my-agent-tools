---
name: url-source-triage
description: "Use when a task hands you a known list of URLs (10+ items) to verify, audit, or inventory across heterogeneous sources — typically as Phase 1 reconnaissance before a measurement, comparison, or migration. NOT for verifying a single specific claim (use tech-fact-check) and NOT for open-ended research (use research-tools). Output is a URL-by-URL status table with a stable [VERIFIED]/[UNVERIFIED — bot-blocked]/[PHANTOM 404]/[PHANTOM] taxonomy, plus content summaries for the verified tier."
author: Hermes Agent (agent-created)
version: 1.0.0
license: MIT
lane: worker-flash
reasoning_effort: high
agent: Researcher
metadata:
  hermes:
    tags:
    - research
    - url-verification
    - reconnaissance
    - source-triage
    - cloudflare-fallback
trigger_keywords: ['not', 'verified', 'phantom', 'url-source-triage', 'you']
keywords: ['research', 'verified', 'phantom', 'task', 'hands']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

# URL Source Triage

Verify a known list of URLs at scale, with a stable per-URL verdict and content summaries for the verified ones. Used as **Phase 1 reconnaissance** before a measurement, comparison, or migration task — a phase-1 pass produces a source map, not answers.

## When to load

- Task starts with "ALLGEMEINE RECHERCHE für …", "Phase 1 — KEINE Zielsystem-Daten", "inventory these URLs", "verify these sources", "triage these links", or similar.
- More than ~5 URLs to check, drawn from heterogeneous sources (vendor docs, GitHub, web stores, forums, marketing sites).
- Output is for downstream code (collector script, migration plan, comparison report) rather than a human narrative.
- The hard rule is "no claim about target X based on these URLs" — research is strictly *about the sources themselves*.

**Not** for:

- One tech claim → `tech-fact-check`
- Open-ended "research X" → `research-tools`
- One URL needs deep extraction → `web_extract` directly

## The 4-tier URL-status taxonomy

Apply this taxonomy consistently. A future agent reading the table must be able to act on each row without re-checking:

| Tag | HTTP | Content | What it means |
|---|---|---|---|
| `[VERIFIED]` | 2xx | Extracted | Real URL, content read or summarized. **Only this tier counts as evidence.** |
| `[UNVERIFIED — bot-blocked]` | 401/403/429, or 200 with `cf-mitigated: challenge` / `cf-ray` header | Not extracted | Page is real but Cloudflare/CDN blocks unauthenticated bot access. Tag with the exact HTTP code and add a search-snippet fallback in the row. |
| `[PHANTOM 404]` | 404, no redirect | n/a | Path genuinely does not exist. State what the canonical alternative is (e.g. "Brave per-tag URLs in lieu of a CHANGELOG.md"). |
| `[PHANTOM]` | 3xx redirect to generic root | n/a | URL silently resolves to a landing page instead of the article. **Functionally a 404, but the HTTP layer lies about it.** Always check `final=` URL. |

A sweep that hits 8/15 `[VERIFIED]` is **acceptable for a Phase 1 hand-off** — do not soften the distinction by tagging bot-blocked pages `[VERIFIED]` just because a search snippet exists. The snippet goes in the row, the tag stays honest.

## Quick-start template (copy + adapt)

```bash
# 1. Status sweep — ALL URLs in one parallel batch
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
for url in "${URLS[@]}"; do
  printf "%s -> " "$url"
  curl -kIL -s -o /dev/null \
       -w "HTTP %{http_code} | final=%{url_effective} | redir=%{num_redirects}\n" \
       --max-time 15 "$url"
done

# 2. Content extraction for [VERIFIED] — try web_extract first, fall back to curl+UA
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
curl -sL --max-time 25 -A "$UA" "$url" \
  | sed 's/<[^>]*>/ /g' | tr -s ' \n\t' ' ' | head -c 1500

# 3. For GitHub repos, prefer REST API over HTML scraping
curl -s -H 'Accept: application/vnd.github+json' \
  "https://api.github.com/repos/brave/brave-browser/releases?per_page=10"

# 4. For [UNVERIFIED — bot-blocked] rows, do NOT reload firecrawl-web — use search snippets
web_search "<site or domain> <key concept>"  # informational only, not evidence
```

## Pitfalls

### Don't confuse 302-redirect-to-root with 401/403

Article URLs that pretend to exist via 302 to a generic Help-Center root (pattern seen on `comet-help.perplexity.ai`) fool a casual `-I` check — the status is `HTTP/2 403` on the article path but `num_redirects=1` lands you on `/help-center/comet/`. Mark `[PHANTOM]`, not `[UNVERIFIED — bot-blocked]`. The redirect chain tells you the article path is dead.

```bash
# Always log both immediate status and final URL
curl -kIL -s -o /dev/null \
     -w "HTTP %{http_code} | final=%{url_effective} | redir=%{num_redirects}\n" "$url"
```

### Don't assume URL path casing

`/devtools-protocol/tot/runtime/` → 404; `/devtools-protocol/tot/Runtime/` → 200. GitHub-Pages-hosted docs use **CamelCase** for domain names. Same on Flathub manifests: `com.brave.Browser.yaml` exists, `com.brave.Browser.json` does not. Probe 2–3 variants before extracting.

### Don't `web_extract` reload when FIRECRAWL_API_KEY is missing

If `firecrawl-web` is unconfigured, the tool returns a config error. Do not retry it mid-sweep; fall back to `curl` with `Mozilla/5.0` user-agent and HTML-stripping. Reserve `firecrawl-web` for batches ≥10 *with* the key set.

### Don't mistake "search snippet confirms page exists" for "page verified"

A `web_search` snippet proves the URL existed at index time. It does NOT prove the current response, headers, or content. For `[UNVERIFIED — bot-blocked]` rows, the snippet is a fallback note, not evidence.

### Don't claim anything about the target system

The whole point of a Phase 1 sweep is **what is published about the world**, not **what the target system has**. Any phrasing like "Brave stable 1.93 is installed on the host" violates the phase-1 contract. Phrase facts as "Brave stable v1.93.126 was published 2026-07-22 per github.com/brave/brave-browser/releases" — let the collector prove target state later.

### Don't scope-creep into tech-fact-check

If a single URL turns out to host a controversial claim ("fake Perplexity extension tracked searches") and the user wants the *truth* of that claim → stop, hand off to `tech-fact-check`. URL triage verifies that the URL is what it claims to be; it does not adjudicate the claim.

## Output template

For each URL, produce one row:

```
| URL | Status tag | Brief content summary (1 sentence) | Date if visible |
```

Plus a per-category breakdown (A, B, C…) showing the verification ratio, the real URLs, the phantoms, and the bot-blocked rows with their snippet context. Close with a "Cross-cutting findings" section listing only facts *established by sources*, never about a target system.

## Related skills

- `tech-fact-check` — for verifying a single headline/claim (not bulk URL triage).
- `research-tools` — for open-ended research; URL triage is the input-handshake phase that often *precedes* a `research-tools` call.
- `firecrawl-web` — for batches where the key is configured; pair with the curl fallback in this skill when it isn't.
