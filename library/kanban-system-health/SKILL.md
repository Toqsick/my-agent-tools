---
name: kanban-system-health
title: "Kanban System Health & Operations (Router)"
description: "Use when user asks for Kanban system health checks, dispatch playbook, swarm operations, auto-decompose, board auditing, or troubleshooting. NOT for single-worker pitfalls (use kanban-worker) or board policy definition (use board-policy). ROUTER: delegates to 4 specialized sub-skills — kanban-diagnostics (live-state + diagnose-baum), kanban-phases (Phase 0-5 + bienen-dispatch), kanban-pitfalls (14+ lessons + hermes-v2), kanban-audit (cross-board + source-code)."
category: kanban-system-health
version: '3.0'
created: '2026-07-09'
author: Yuno (Hermes)
lane: koenigin
agent: universal
trigger_keywords: ['kanban', 'health check', 'dispatch', 'swarm', 'auto-decompose', 'troubleshooting', 'multi-agent']
keywords: ['kanban', 'multi-agent', 'health-check', 'troubleshooting', 'dispatcher', 'activation', 'swarm', 'auto-decompose', 'audit']
related_skills: ['kanban-diagnostics', 'kanban-phases', 'kanban-pitfalls', 'kanban-audit', 'kanban-orchestrator', 'board-policy', 'multi-agent-kanban-audit']
last_curated: '2026-07-23'
curated_by: 'Yuno (split into 4 sub-skills 2026-07-23)'

license: MIT
---


# Kanban System Health & Operations (Router)

Use this skill as the **entry point** for Kanban work. This skill is a **router** — it delegates to four specialized sub-skills.

## Quick Start: Which sub-skill do I need?

| User intent | Sub-skill |
|-------------|-----------|
| "Why isn't the dispatcher spawning?" / "Gateway seems dead" / "Live-state check" | **kanban-diagnostics** |
| "Set up the Kanban" / "Phase 0 cleanup" / "Assign ready-tasks" / "Run swarm" | **kanban-phases** |
| "Hit a pitfall" / "CLI flag wrong" / "Config drift" / "Source-code mismatch" | **kanban-pitfalls** |
| "Audit all boards" / "Cross-board scout" / "Source-code implementation audit" | **kanban-audit** |

## Pipeline Phases

1. **Diagnose** → kanban-diagnostics (§1-2)
2. **Setup + Cleanup** → kanban-phases (§3: Phase 0+1)
3. **Mature Workers** → kanban-phases (§5: Worker-Maturity Flags)
4. **Advanced Patterns** → kanban-phases (§6: Swarm + Auto-Decomp + Notifications)
5. **Polish** → kanban-phases (§7-8: Attachments, Dashboard, Evolution)
6. **Recovery from Pitfall** → kanban-pitfalls (§10+15)
7. **Cross-Board Audit** → kanban-audit (§12+14)

## Source Document

This router was extracted from kanban-system-health v2.5 (~86KB) on 2026-07-23 by splitting into 4 specialized sub-skills. The full content lives in the sub-skills above.

## Related Skills

- `kanban-diagnostics` — Live-State-Check + Diagnose-Baum + Status-Report
- `kanban-phases` — Phase 0-5 + Bienen-Dispatch
- `kanban-pitfalls` — 14+ Lessons + Hermes-v2-Betrieb
- `kanban-audit` — Cross-Board Scout + Source-Code Audit Recipe
- `kanban-orchestrator` — orchestrator profile routing
- `board-policy` — per-board policy declaration
- `multi-agent-kanban-audit` — overarching audit methodology