# Scout-Swarm Ingest Walkthrough

> Real session recipe: tri-domain wiki ingest from Obsidian vault MOCs +
> research files + Hermes Architecture Review.
> Session date: 2026-07-17 | Domains: ai-ml, orchestration, personal
> Sources: ~15 Obsidian notes + 27 KB research doc + 2 meta docs
> Result: ~25 wiki pages created across 4 + 5 domains

## Context

Basti had a fresh tri-domain wiki under `~/wiki` and wanted to feed it
from his Obsidian vault (`~/Dokumente/Obsidian Vault/`) and research files
(`~/30-Library/`, `~/00-Meta/`).

The vault uses Julian-Ivanov-schema (01 Kontext, 02 Inbox, ... 08 Anhaenge)
with MOCs per folder. Key MOCs identified during Recon:

| Domain | Key MOCs / Sources |
|---|---|
| ai-ml | MOC - KI-Architektur, Hermes-Architecture-Review |
| orchestration | MOC - Lernen & Orchestration, multi-agent-frameworks-research.md (27KB) |
| personal | MOC - Home, MOC - Content-Creation, MOC - Daily Notes, MOC - Voice-Pipeline, Yuno-Status-Dashboard |

## Phase 1: Recon

**Commands:**
```bash
cat ~/wiki/SCHEMA.md
cat ~/wiki/index.md
find ~/Dokumente/Obsidian\ Vault/ -name "MOC*" -type f | sort
wc -l ~/30-Library/multi-agent-frameworks-research.md  # 27KB!
ls ~/00-Meta/*.md | head -20
```

**Output:** 4 potential domains identified → merged to 3 (AI/ML, Orchestration,
Personal). Estimated 20-30 pages.

## Phase 2: Dispatch

Three parallel `delegate_task` calls. Each scout got:
- Wiki path + SCHEMA rules in context
- Sources to read (specific file paths)
- Domain tag to use
- "Antworte auf Deutsch"

Key context passed:
```
"Basti hat ein frisches tri-domain Wiki unter ~/wiki. 
Wiki-Konventionen aus SCHEMA.md — lies es VOR dem Schreiben.
WICHTIG: Quality > Quantity. 5-7 substanzielle Pages > 20 Stubs.
Jede Page MUSS Frontmatter haben + min 2 outbound [[wikilinks]].
Source-Pfade: [paths]"
```

## Phase 3: Queen Synthesis (concurrent)

While scouts worked, the queen:

1. **Created skeleton pages** (5 total):
   - `_meta/llm-wiki-pattern.md` — Karpathy architecture + mapping
   - `_meta/lint-checklist.md` — quality gates with 3 severity tiers
   - `_meta/agent-readme.md` — session onboarding for next agent
   - `comparisons/llm-wiki-vs-rag.md` — compile-once vs retrieve-each
   - `concepts/compounding-knowledge.md` — network-effect curve
   - (queen-bee-pattern skeleton stub for scout to fill)

2. **Updated index.md** — added cross-domain + meta sections
3. **Updated log.md** — initial batch ingest entry

Skeleton format:
```yaml
---
title: LLM Wiki Pattern
created: 2026-07-17
updated: 2026-07-17
type: concept
domain: cross-domain
tags: [concept, pattern, meta]
sources: []
confidence: medium
---
# Page Title
> Stub — populated by [domain] scout from [source name].
[[wikilink-1]] · [[wikilink-2]]
```

## Phase 4: Merge

Post-dispatch:
1. `find ~/wiki -type f -name "*.md" | wc -l` — 8→25+ pages
2. Checked for duplicates (none found — domain separation worked)
3. Updated index.md page count
4. Single log entry per scout payload

## Key Lessons from the Session

1. **Skeletons before scouts** — wikilinks need to exist before they're referenced
2. **Domain-separated scouts** reduce duplicates naturally
3. **Queen writes index/log** — avoids race conditions
4. **cross-domain pages** are the bridge that makes a multi-domain wiki work
5. **Scout instructions must be explicit** — "write wiki pages to filesystem,
   not descriptions of what you'd write"
