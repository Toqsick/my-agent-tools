---
name: tech-fact-check
description: "Use when user asks to verify a technology claim such as a data leak, security incident, model release, outage, ban, or policy change. NOT for opinion writing or repeating an unverified headline as fact. Applies a primary-source waterfall, claim decomposition, evidence levels, confidence matrix, precise restatement, and practical consequence check."
author: Hermes Agent
version: 1.0.0
license: MIT
trigger_keywords: ['claim', 'tech-fact-check', 'verify', 'technology', 'such']
keywords: ['claim', 'user', 'asks', 'verify', 'technology']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---


# Tech Fact-Check

Verify a tech claim end-to-end against primary and reputable sources, then
return a precise restatement with an explicit confidence matrix. Designed for
the "viral headline → what actually happened" pattern that recurs in security
news, model releases, and platform policy changes.

## When to load

- User asks to verify a specific tech story (security incident, data leak,
  model release, outage, ban, policy change).
- User quotes a headline and wants ground-truth.
- User forwards an HN / X / Reddit / news link and wants a verdict.

**Not** for: pure opinion disputes, personal claims about identifiable
people, financial advice, legal advice. Those cross into other domains —
return to Yuno.

## The 5-phase workflow

### Phase 1 — Reframe

The headline is almost always misstated in the popular retelling. Restate the
**literal claim** in your own words before fetching anything.

Three common reframings to look for:

| Popular framing | Actual pattern |
|---|---|
| "Model X leaks data to Company Y" | Often: a *tool built on* Model X, not the model itself, leaks |
| "GitHub repo exfiltrated to X" | Often: a *local clone* sent over the air, GitHub was not involved |
| "Open-source tool spies on users" | Often: telemetry default-ON, well-documented but not opt-out |
| "X bans Y" | Often: a *specific tier* (EU, free, mobile) banned, not globally |

Reframe in 1–2 sentences. This is the user's primary deliverable even if all
later phases fail. Skip the reframe only if the headline was already precise.

### Phase 2 — Source waterfall (in order)

Stop at the first tier that yields a verifiable claim; don't over-fetch.

1. **Primary source** — the vendor / researcher / official post that first
   disclosed the incident. Look for SHA-256 hashes, wire captures, repro
   repos, commit IDs, CVEs.
2. **Reputable secondaries** — specialized security press (BleepingComputer,
   The Record, Krebs, SecurityWeek, The Hacker News, vendor security blogs).
3. **Community discussion** — HN, Lobsters, relevant Discords, vendor issues.
4. **Provider-side artifacts** — repo code search, commit history, binary
   strings (`strings <binary> | grep`), network captures (`mitmproxy`,
   Wireshark), CVE databases (NVD, GHSA, OSV).

If the primary source is a GitHub gist / repo / issue, use the GitHub MCP
tools or `curl` fallbacks documented in `references/source-fetch-recipes.md`.

If web fetch is completely unavailable, try MseeP (mcp.memory) for the user's
personal notes, then raw `curl` against APIs that don't require auth.

### Phase 3 — Verify, don't trust

For each claim the original headline makes, demand:

- **Wire-level or binary-level evidence** (sha256, hex, raw bytes), not "I
  tested this and saw X."
- **A reproduction path** that another party can run independently.
- **Explicit scope statements** — what was tested, what was not, what version,
  what account tier, what region.
- **Failure mode honesty** — what the original researcher could NOT prove
  ("training" claims, "all users" claims, "across versions" claims).

Subtract confidence for each missing item. A claim with no primary source,
no reproduction path, and no scope limitation is **opinion, not evidence**.

### Phase 4 — Precise restatement

Restate the claim in exactly one paragraph, distinguishing:

- **What is established** (wire-captured, reproduced, multi-source)
- **What is asserted but not proven** (e.g., training use, scale, intent)
- **What is unknown / not tested** (other product variants, account tiers,
  regions, versions)
- **What is contradicted by primary source** (vendor flags, settings,
  CVE entries)

State the actual mechanism in technical detail. Name endpoints, file paths,
binary strings, CVE IDs, version numbers. Trade gossip for specs.

### Phase 5 — Confidence matrix + verdict

Render a table at the end, one row per sub-claim made by the headline:

| Sub-claim | Confidence | Why |
|---|---|---| |

Then a one-line verdict (true / partially true / misframed / unverified /
false) and primary URLs with their publication date.

## Output template

```
# Faktencheck: <headline or claim>

## Kurzantwort
<one paragraph, ~5 lines, with the precise verdict>

## 1. Was genau behauptet wird
<primary source link + date + author + literal claim restatement>

## 2. Was belegt ist (mit Evidenz-Level)
<table>

## 3. Vendor / offizielle Reaktion
<none / commit / advisory / blog post / CVE / server-side flag change>

## 4. Bewertung pro Sub-Claim
<table>

## 5. Praktische Konsequenz
<credential rotation / mitigating config / sandbox pattern>

## 6. Konfidenz pro Aussage
<table>

## 7. Primärquellen
<numbered URLs with dates>
```

Return language matches the user language (default English; mirror German if
the user wrote in German).

## PITFALLS

### Don't parrot the headline

If you write "*[Vendor] leaked data to [cloud]*" without first identifying
*what* in *[vendor]* leaked, you have failed Phase 1. The whole rest of the
fact-check rests on getting the actor + mechanism precise.

### Don't cite secondary sources as primary

A Medium re-write of a BleepingComputer article is not primary. Trace every
claim back to the original disclosure (gist ID, repo SHA, post URL, advisory
ID). Cross-reference at least one reputable independent secondary only when
the primary is sparse.

### Don't confuse "code observed" with "data uploaded"

For telemetry / privacy findings, distinguish three things explicitly:
1. **Local staging** (file written to `~/.cache/...`) — not a leak
2. **Wire transmission** (POST request over the network) — a leak candidate
3. **Server acceptance** (HTTP 200 from `/v1/storage`) — a confirmed upload
4. **Use for training** — policy question, often *not* technically proven

A complete fact-check walks all four steps and says where the evidence
chain breaks. The popular press usually conflates 3 and 4.

### Don't ignore vendor silent fixes

Server-side flag flips (`disable_codebase_upload: true`, `trace_upload_enabled: false`)
count as evidence of acknowledgement even when no blog post is published.
Look at the same endpoint a day/week later and compare.

### Don't load firecrawl-web just to fetch one page

If only one URL needs fetching, `curl` is faster than spinning up a skill.
If many URLs need parsing, *then* load firecrawl-web. Match the tool to the
task.

## Quick-start template (copy + adapt)

```
Phase 1 — reframe the literal claim in 1–2 sentences
Phase 2 — fetch primary source → secondary → community; stop at first tier
          with verifiable evidence
Phase 3 — check: wire-level evidence? reproduction? scope? honesty about unknowns?
Phase 4 — write the precise mechanism paragraph (endpoints, paths, hashes)
Phase 5 — confidence matrix per sub-claim; one-line verdict; primary URLs

Return: 7-section template above, in user's language.
```

## Related skills

- `firecrawl-web` — primary fetch tool; this skill's curl/MCP fallback
  recipes live there.
- `mcp/native-mcp` — for registering custom MCP servers if more discovery
  channels are needed.
- `research-tools` — for general research beyond fact-checking
  (academic arxiv search, polymarket, web archive).
