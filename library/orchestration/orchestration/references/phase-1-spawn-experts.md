# Phase 1: Spawn 3 Experts — Detailed Procedure

Full step-by-step procedure for spawning the 3 parallel expert subagents.
Loaded from `multi-agent-orchestration` SKILL.md §"Phase 1".

## Spawn Pattern

Use `delegate_task(tasks=[...])` with exactly **3 parallel tasks**.

If `delegate_task` is rejected by HermesUltraCode with `base_prompt is empty; nothing to dispatch`, provider-gate failures, or provider HTTP errors such as OpenRouter 404, do **not** keep retrying the same dispatch. Treat it as a dispatcher failure, not as a research result. Immediately switch to parent-direct fallback:

1. Run the same three expert scopes yourself with terminal/file/web measurements.
2. Write the three expert reports to explicit paths.
3. Synthesize them in `~/docs/system/`.
4. State in the final report that subagent dispatch was blocked and parent-direct fallback was used.

## Scope Assignment

| Expert | Typical Scope |
|--------|--------------|
| 1 | Auth, Security, Credentials |
| 2 | Tools, APIs, GPU/Compute |
| 3 | Infra, Messaging, Monitoring |

Adapt scopes to the actual system.

## Expert Context Template

Every expert MUST receive the following briefing structure (Pitfall #6 — explicit `OUTPUT` path prevents file chaos):

```
SYSTEM: [OS, hardware, user]
AKTUELLER STATE: [Status aller Komponenten]
NEU SEIT LETZTER SESSION: [Was sich geändert hat]
AUFGABE: [8-12 konkrete Fragen, nummeriert]
TRENNUNG: [Sofort umsetzbar vs Großprojekt]
OUTPUT: [Expliziter Pfad — z.B. ~/docs/system/NAME-YYYY-MM-DD.md]
```

Always include:
- `MAX 8 web-calls. After 8 -> synthesis with what you have` (prevents pagination loops, Pitfall #15)
- `OUTPUT-LIMITS: Bei Outputs >100 Zeilen head, wc -l, oder limit=` (prevents 874-line log timeout)
- Explicit source-code paths when relevant (Pitfall #10: source beats web)

## Toolset Assignment

| Expert Type | Required Toolsets |
|-------------|-------------------|
| System analysis | web, search, **terminal, file** |
| Web research | web, search |
| Code/Build | terminal, file, web |

**Critical:** Experts without `terminal` + `file` produce estimates, not measurements (Pitfall #3).

## Read-Only Briefing Default

When security/permission audits, use read-only briefings by default to avoid 90+90s Ollama approval timeouts (Pitfall #31). For tasks requiring one controlled write, see the "Controlled Write" pattern in `multi-agent-pitfalls-cheatsheet` §"Controlled Write in Read-Only Briefings".

If subagent has write commands (chmod/rm/systemctl) in briefing, set `auxiliary.approval.provider: nous` before batch to avoid Background-Review timeouts.

## Hybrid Pre-Scan Pattern (When Applicable)

For tasks where the parent can do a deterministic pre-scan:

```
Phase 0: PARENT runs Python via execute_code → deterministic pattern-scan
         → produces curated hit-list (10-30 files) → ~/docs/.../pre-scan-results.md

Phase 1: PARENT spawns Expert 3 with briefing that REFERENCES pre-scan-results.md
         → Subagent reads the hit-list, does NOT scan from scratch
         → Subagent verifies 3-5 random findings, produces bug report

Phase 2: PARENT cross-checks subagent's verifications against own scan
```

Why: subagent scope drops from "118 files × 12 patterns" to "verify 20 pre-filtered hits". API-call budget: ~8 calls vs. 50+.

Apply when: bug scans across many files, doc completeness checks, coverage audits, dependency audits. Don't apply when: source-code reasoning needed, single-file deep dives, scope unknown until explored.