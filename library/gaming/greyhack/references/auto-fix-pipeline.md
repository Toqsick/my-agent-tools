# GreyHack Multi-Agent Auto-Fix Pipeline

> Gebaut 2026-06-23 — Transfer von TheMorpheus407's the-dmz/auto-develop.sh  
> **Modell-Update 2026-06-23**: `deepseek/deepseek-v4-flash:free` existiert NICHT auf OpenRouter.  
> Alle Worker-Rollen nutzen `openrouter/owl-alpha` (gratis, 1M Kontext).

## Sub-Agent Specs (6 Stück)

In `~/greyhack-tools/.claude/agents/`:

| Spec | Rolle | Domain |
|------|-------|--------|
| `greyhack-syntax.md` | Syntax-Review | Build, char(), if/else-Regeln |
| `greyhack-mission.md` | Game-Logik | Missionen, Reraldi, Deployment |
| `greyhack-tools.md` | Tool-Architektur | lib_core, Cross-Tool-Kompatibilität |
| `greyhack-reviewer.md` | Code-Review | 12-Punkt-Checkliste (DMZ-Pattern) |
| `greyhack-tester.md` | Smoke-Tests | In-Game-Tests, Coverage |
| `greyhack-deploy.md` | Deployment | Fileserver :8765, 4-Phase-Deploy |

## Pipeline

```
greyhack-auto-fix.sh --bug <N>
     │
     ├─ RESEARCH  (owl-alpha) → logs/issues/{N}/research.md
     ├─ IMPLEMENT (owl-alpha) → Code-Fix
     ├─ [greybel build]       → Build-Check VOR AI-Review
     ├─ REVIEW A  (owl-alpha) → Syntax-Check (ACCEPTED/DENIED)
     │  REVIEW B  (owl-alpha) → Game-Logik + Bug-Abdeckung (ACCEPTED/DENIED)
     ├─ GATE: ACCEPTED+ACCEPTED → Finalize
     │        DENIED → Loop (max 3x) mit Delta-Feedback
     └─ FINALIZE (owl-alpha) → derive_commit_message() → git commit
```

## Modell-Kosten

| Rolle | Modell | Kosten | Kontext |
|-------|--------|--------|---------|
| Research | `openrouter/owl-alpha` | 0€ | 1M |
| Implement | `openrouter/owl-alpha` | 0€ | 1M |
| Reviewer A/B | `openrouter/owl-alpha` | 0€ | 1M |
| Finalizer | `openrouter/owl-alpha` | 0€ | 1M |
| Queen (Parent) | `deepseek/deepseek-v4-flash` | paid | 1M |

`hermes config set delegation.model openrouter/owl-alpha` — alle Subagenten gratis.