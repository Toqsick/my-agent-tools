---
name: queen-bee-schwarm-dispatch
title: "Queen-Bee Schwarm Dispatch (Router)"
description: "Use when orchestrating parallel subagents, dispatching a multi-agent swarm, or managing 2-wave dispatch patterns. ROUTER: delegates to queen-bee-dispatch-patterns (briefing/file-affinity/cross-wave), queen-bee-queen-verify (queen-verify/override/pre-execute), queen-bee-advanced (audit-biene/drift-marker/baseline). NOT for single-subagent execution without parallel/swarm context."
category: queen-bee-schwarm-dispatch
version: '2.0'
created: '2026-07-23'
author: Yuno (Hermes)
lane: koenigin
agent: universal
trigger_keywords: ['queen', 'bee', 'schwarm', 'dispatch', 'wave', 'subagent', 'parallel', 'multi-agent']
keywords: ['queen-bee', 'schwarm', 'dispatch', 'multi-agent', 'parallel', 'wave']
related_skills: ['queen-bee-dispatch-patterns', 'queen-bee-queen-verify', 'queen-bee-advanced', 'multi-agent-orchestration', 'multi-agent-cluster-patterns', 'delegation-anti-patterns']
last_curated: '2026-07-23'
curated_by: 'Yuno (split into sub-skills 2026-07-23)'

license: MIT
---

# Queen-Bee Schwarm Dispatch (Router)

This is a router skill. Choose the sub-skill based on your intent:

## Queen-Bee — Dispatch Patterns (Briefing, File-Affinity, Cross-Wave)

Use when setting up a queen-bee dispatch: briefing templates, file-affinity checks, cross-wave learning, or subagent limits. NOT for queen-verify patterns (use queen-bee-queen-verify).

## Queen-Bee — Queen-Verify, Override, Pre-Execute

Use when running queen-verify after a wave, applying queen-override patterns, or doing queen pre-execute while bees scout. NOT for dispatch setup (use queen-bee-dispatch-patterns).

## Queen-Bee — Advanced Patterns (Audit-Biene, Drift-Marker, Baseline)

Use when running advanced queen-bee patterns: audit-biene, drift-marker detection, queen pre-execute for audit cross-verification, queen baseline, orthogonal scout, hypothesis-falsification, skip-decision, nested delegation. NOT for basic dispatch (use queen-bee-dispatch-patterns).


## Related Skills

- `queen-bee-dispatch-patterns`
- `queen-bee-queen-verify`
- `queen-bee-advanced`
- `multi-agent-orchestration`
- `multi-agent-cluster-patterns`
- `delegation-anti-patterns`
