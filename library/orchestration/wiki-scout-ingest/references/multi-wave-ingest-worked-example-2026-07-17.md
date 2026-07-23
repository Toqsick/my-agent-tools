# Multi-Wave Wiki Ingest — Worked Example (2026-07-17)

> Session date: 2026-07-17 | Model: deepseek/deepseek-v4-flash
> Source: Obsidian vault + Perplexity research exports (~155 files triaged)
> Result: 100 files, 50 content pages, 47 raw articles, 330 wikilinks, 98.8% lint

## Overview

Biggest multi-wave wiki ingest to date. 4 sequenced waves produced a
production-ready tri-domain wiki (ai-ml, orchestration, personal) in a
single session.

## Wave Strategy

| Wave | Scouts | Focus | Pages Created |
|------|--------|-------|:------------:|
| W1 — Core tri-domain | 3 | Obsidian MOCs (KI-Architektur, Lernen&Orchestration, Personal) | 8 content + 6 raw |
| W2 — Perplexity Gold | 3 | Multi-Agent-Systems, Local-9B-MoE, Hermes-V7 | 7 entities + 10 concepts + 9 raw |
| W3 — Personal Scout | 1 | Julian-Ivanov-Framework, system-doku | 1 cross-domain + 1 entity |
| W4 — Lint + consolidation | Queen self | Slug normalization, missing stubs, index/log sync | 50 → 50 (124 wikilinks fixed) |

**Why 4 waves and not one-shot:** Wave 1 revealed two critical issues:
1. Slug normalization (titles with dots `.` produce mismatched filenames)
2. Missing entities (scouts linked to pages that didn't exist yet)
These were fixed before Wave 2 started → Wave 2 output was cleaner as a result.

## Concrete Numbers

| Metric | After W1 | After W2 | After W3 | After W4 (final) |
|--------|:-------:|:-------:|:-------:|:----------------:|
| Total files | 8 | 47 | 52 | 100 |
| Content pages | 7 | 34 | 44 | 50 |
| Raw articles | 6 | 22 | 44 | 47 |
| Broken wikilinks | 0 (queen skeletoned) | 132 | 64 | 4 |
| Lint rate | 100% | ~60% | ~80% | 98.8% |

## Key Learnings

### 1. Slug normalization cost is real
124 wikilinks needed fixing across 3 automated passes. The pattern:
- Scout writes `[[qwen-3.5-9b]]` (from title in source)
- Filename slug is `qwen-3-5-9b-alibaba-qwen-team.md` (dots → hyphens, parentheses stripped)
- Fix in three rounds: (1) bulk grep-replace on pattern, (2) single-file patches for remaining, (3) stub creation for truly missing entities

### 2. Lint coverage improved per wave
```
W1: 0 broken → all wikilinks pointed to queen's pre-seeded skeletons
W2: 132 broken → scouts linked to each other's pages but also to non-existent ones
W3: 64 broken → half fixed by now-existing Wave-2 pages
W4: 4 broken → all in SCHEMA.md and log.md (inline [[wikilinks]] as prose examples, not real pages)
```

### 3. Domain distribution proved balanced
```
ai-ml: 25 content pages (models, quantization, MoE, local inference)
orchestration: 6 content pages + cross-domain bridges
personal: 9 content pages (documentation system, daily notes, vision)
cross-domain: 4 pages + 1 in _meta/cross-domain/
```

### 4. Sibling-agent race on index.md
The `patch` tool warned about modification by sibling subagent. The correct
response: re-read the file (sibling may have already indexed your pages),
re-evaluate if write is still needed, only then re-patch.

### 5. "98% is good enough"
The last 4 broken wikilinks were all in meta/convention files (SCHEMA.md
uses `[[wikilinks]]` as syntax examples, log.md describes the wiki format).
These are NOT missing pages — they're inline code references. Chasing 100%
at scale wastes effort. Consider them as "documented non-pages" and stop
at 98-99%.

## Source Material Used

| Source Type | Path | Volume |
|-------------|------|--------|
| Obsidian vault MOCs | `~/Dokumente/Obsidian Vault/` | ~10 notes, ~2KB each |
| Research doc | `~/30-Library/multi-agent-frameworks-research.md` | 27KB single file |
| Perplexity export | `~/Dokumente/Perplexity/` | ~155 .md files, ~15-20KB total viable |
| Hermes Architecture | `~/docs/system/` + memory recall | ~5 system docs |
| Mnemosyne memory | `mnemosyne_recall` | ~2KB patterns |

## Commands to Reproduce

```bash
# Recon
cat ~/wiki/SCHEMA.md
cat ~/wiki/index.md
find ~/Dokumente/Obsidian\ Vault/ -name "MOC*" | sort
# Triage: Perplexity has 155 files, filter to relevant ones
find ~/Dokumente/Perplexity/ -name "*.md" | wc -l

# After dispatch: verify scout output
find ~/wiki -type f -name "*.md" | wc -l
find ~/wiki/entities/ ~/wiki/concepts/ -name "*.md" | wc -l
wc -l ~/wiki/index.md

# Lint pass (slug normalization)
python3 -c "import re; ..."  # scan for broken [[wikilinks]]

# Domain distribution
grep -r "^domain:" ~/wiki/entities/ ~/wiki/concepts/ | sort | uniq -c

# Final count
find ~/wiki -type f -name "*.md" | wc -l
```
