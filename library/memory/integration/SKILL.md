---
name: hermes-memory
description: >-
  Use when user asks for recalling durable lessons from prior work, querying Yuno persistent memory, finding reusable context in the memory index, or storing a long-lived operational lesson. NOT for tracking temporary session todos or checking live external facts. Provides the bridge and index conventions for durable Hermes memory rather than short-lived conversational state.
version: 1.0.0
changelog:
- '1.0.0 (2026-07-03): Initial conversion from MiniMax Hub'
author: Toqsick + Yuno (Hub→Hermes conversion)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    source: minimax-hub
    hub_skill_id: hermes-memory
    category: integration
    domain: memory
    converted_at: '2026-07-03T23:19:32.981327'
  tags:
  - hub
  - conversion
  - workflow
triggers:
- memory
- hermes
- context
- yuno
- remember
- recall
trigger_keywords: ['memory', 'durable', 'index', 'lived', 'user']
keywords: ['memory', 'durable', 'index', 'lived', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['todo-kanban-promotion', 'mnemosyne-memory-provider', 'session-handoff']
---



> **Hub Origin:** Convexed from MiniMax Hub skill `hermes-memory` (version 1.0.0). Original Hub-SKILL.md is preserved at `scripts-originals/SKILL.md.hub`, original meta.yaml at `scripts-originals/meta.yaml.hub`. All Hub-specific paths (e.g. `~/.hub-global/skills/hermes-memory/`) translated to Hermes-equivalent references in `references/`.
# Hermes Memory Bridge

This skill contains **HERMES' persistent memory** — all the things Yuno (the Hermes agent)
has remembered across previous sessions, now available to MiniMax Hub's agent.

## How to use

1. **Read this when user asks context-dependent questions**, like:
   - "What did we set up for X?"
   - "How was Y configured?"
   - "Remember that bug from last week?"
2. **Each Memory-Note is in references/** as a markdown file
3. **Tags/importance rating** in meta.yaml per-note

## Memory-Index

The list below is the index of what Yuno remembers. To look up a specific topic,
search for matching subject or read all notes in references/.

- **** (importance 0.90): Surface meta: GreyHack Tool-Pipeline (Stand 17.06.2026): greybel-js installiert,...
- **** (importance 0.50): ...
- **** (importance 0.50): ...
- **** (importance 0.50): ...
- **** (importance 0.50): ...
- **** (importance 0.50): ...
- **** (importance 0.50): Surface meta: GreyHack Tool-Pipeline (Stand 17.06.2026): greybel-js installiert,...
- **** (importance 0.50): ...
- **** (importance 0.50): ...
- **** (importance 0.50): ...
- **** (importance 0.50): ...
- **** (importance 0.50): ...
- **** (importance 0.50): ...
- **** (importance 0.50): ...
- **** (importance 0.70): ...
- **** (importance 0.70): ...
- **** (importance 0.50): ...
- **** (importance 0.50): ...
- **** (importance 0.50): ...
- **** (importance 0.50): ...
- **** (importance 0.50): ...
- **** (importance 0.50): ...

_All memories also available in references/ with full content._