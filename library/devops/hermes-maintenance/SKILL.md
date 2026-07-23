---
name: hermes-maintenance
title: "Hermes Maintenance (Router)"
description: "Use when performing real-world maintenance on a Hermes Agent installation — config security, multi-agent patterns, SSE pipeline, pitfall recovery. ROUTER: delegates to hermes-maintenance-core (reality-check/config/SSE), hermes-maintenance-patterns (scout/canary/CDP/discovery), hermes-maintenance-pitfalls (port-conflict/memory/service-discovery)."
category: devops
version: '2.0'
created: '2026-07-23'
author: Yuno (Hermes)
lane: koenigin
agent: universal
trigger_keywords: ['hermes', 'maintenance', 'config', 'security', 'sse', 'canary', 'pitfall']
keywords: ['hermes', 'maintenance', 'config', 'security', 'sse', 'pitfall', 'devops']
related_skills: ['hermes-maintenance-core', 'hermes-maintenance-patterns', 'hermes-maintenance-pitfalls', 'hermes-agent', 'linux-system']
last_curated: '2026-07-23'
curated_by: 'Yuno (split into sub-skills 2026-07-23)'

license: MIT
---

# Hermes Maintenance (Router)

This is a router skill. Choose the sub-skill based on your intent:

## Hermes Maintenance — Core (Reality-Check, Config, SSE)

Use when doing core Hermes maintenance: reality-check before changes, Tirith verification, config.yaml security defaults, Perplexity-style analysis, SSE pipeline patterns, build documentation standards. NOT for pitfall recovery (use hermes-maintenance-pitfalls).

## Hermes Maintenance — Patterns (Scout, Canary, CDP, Discovery)

Use when applying advanced Hermes maintenance patterns: multi-agent scout, canary-token PoC, connection-drop resume, CDP cookie-bridge, or service discovery. NOT for core config (use hermes-maintenance-core).

## Hermes Maintenance — Pitfalls (Port-Conflict, Memory, Services)

Use when hitting a Hermes maintenance pitfall: port conflicts, memory hygiene, or critical don't-repeat errors. NOT for first-time setup (use hermes-maintenance-core).


## Related Skills

- `hermes-maintenance-core`
- `hermes-maintenance-patterns`
- `hermes-maintenance-pitfalls`
- `hermes-agent`
- `linux-system`
