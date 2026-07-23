---
name: mirofish
title: "MiroFish Simulation Setup & Run (Router)"
description: "Use when user asks to set up, run, monitor, or generate reports from a MiroFish simulation based on a whitepaper, research document, or report. NOT for generic multi-agent simulations or starting an unrequested watcher. ROUTER: delegates to 4 specialized sub-skills — mirofish-pipeline (seed+API+monitor), mirofish-analysis (post-run+multi-run+chat), mirofish-pitfalls (35+ failure recovery recipes), mirofish-runbook (templates+max-kampagne deck)."
category: software-development
version: '3.0'
created: '2026-07-12'
author: Hermes Agent
lane: software-development
agent: universal
trigger_keywords: ['mirofish', 'simulation', 'multi-agent', 'distill', 'monitor', 'ontology', 'report', 'oasis']
keywords: ['mirofish', 'oasis', 'simulation', 'persona', 'graph build', 'distillation', 'zep', 'multi-agent', 'pipeline']
related_skills: ['mirofish-pipeline', 'mirofish-analysis', 'mirofish-pitfalls', 'mirofish-runbook', 'multi-agent-cluster-patterns', 'multi-agent-research']
last_curated: '2026-07-23'
curated_by: 'Yuno (split into 4 sub-skills 2026-07-23)'

license: MIT
---


# MiroFish Simulation Setup & Run (Router)

Use this skill as the **entry point** for MiroFish simulation work. This skill is a **router** — it delegates to four specialized sub-skills. Pick the right one based on what the user wants.

## When to use which sub-skill

| User intent | Sub-skill |
|-------------|-----------|
| Set up a new simulation, seed distillate, API pipeline, live monitoring | **mirofish-pipeline** |
| Analyze a completed simulation, compare runs, interactive agent chat | **mirofish-analysis** |
| Simulation is stuck, crashed, or returning wrong state — need recovery recipe | **mirofish-pitfalls** |
| Write a runbook, Max-Kampagne deck, skill-chaining template, subagent multi-run | **mirofish-runbook** |

## Pipeline Phases (Quick Reference)

1. **Setup** → mirofish-pipeline (Step 1+2: seed distillate, project+ontology, graph build, prepare)
2. **Live monitoring** → mirofish-pipeline (Step 4: watcher patterns, progress polling)
3. **Post-run analysis** → mirofish-analysis (Step 3a+3b+3c)
4. **Failure recovery** → mirofish-pitfalls (35+ pitfall recipes indexed by symptom)
5. **Runbook templates** → mirofish-runbook (Step 5 + documentation patterns)

## Source Document

This router was extracted from mirofish v2.6 (1860 lines, 101KB) on 2026-07-23 by splitting into 4 specialized sub-skills. The full content lives in the sub-skills above; this router is the **only** entry point for the keyword "mirofish" and routes by user intent.

## Related Skills

- `mirofish-pipeline` — seed, API pipeline, live monitor
- `mirofish-analysis` — post-run, multi-run, agent chat
- `mirofish-pitfalls` — 35+ failure modes + recovery
- `mirofish-runbook` — runbook templates, Max-Kampagne deck
- `multi-agent-cluster-patterns` — general multi-agent orchestration
- `multi-agent-research` — research-driven multi-agent workflows