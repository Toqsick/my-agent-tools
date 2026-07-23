---
name: agent-orchestration-patterns-2026
description: |
  Use when selecting or implementing a production Python skeleton for sequential pipelines, parallel fan-out and synthesis, or reviewer-gated multi-agent workflows.
  NOT for a single trivial delegation, framework-agnostic brainstorming, or orchestration that cannot satisfy the included verification and token-budget assumptions.
  Supplies tested orchestration skeletons, a decision flowchart, retry and review gates, dry-run support, and token-budget guidance.
category: orchestration
platforms:
- linux
- macos
- windows
version: 1.0.0
author: Yuno + Basti (2026-07-16)
license: MIT
lane: koenigin
reasoning_effort: xhigh
metadata:
  hermes:
    tags:
    - multi-agent
    - orchestration
    - patterns
    - python-skeletons
    - hermes-bridge
    - production-ready
    - queen-bee
    - critic-loop
    - tree
    related_skills:
    - sub-sub-workflow
    - multi-agent-pitfalls-cheatsheet
    - multi-agent-cluster-patterns
    - subagent-driven-development
    - delegation-anti-patterns
    - queen-bee-schwarm-dispatch
triggers:
- subagent pattern
- queen bee pattern
- critic loop
- orchestration skeleton
- fan-out agents
- delegate_task pattern
- agent pipeline
- maker checker
- reflexion
- multi agent pattern
- parallel agents
- worker pool
- depth tree
- anti-pattern orchestration
- sycophancy guard
- idempotency agent
- agent orchestration
- spawn depth
- sub sub
- delegation chain
trigger_keywords: ['orchestration', 'token', 'budget', 'selecting', 'implementing']
keywords: ['orchestration', 'token', 'budget', 'selecting', 'implementing']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['fable-orchestration-pattern']
---


# Agent Orchestration Patterns 2026 — Production-Ready Skeletons

**Drei produktive Python-Skeletons + Decision-Flowchart + Token-Budget-Tabelle** für die häufigsten Multi-Agent-Orchestration-Patterns. Drop-in für jedes Hermes-Projekt, 27/27 Pytest-Tests grün, sofort einsatzbereit mit `--dry-run`.

## Wann diesen Skill laden

Trigger wenn du:
- Einen **Multi-Agent-Workflow** bauen willst (Queen-Bee, Tree, oder Critic-Loop)
- Zwischen den **3 Haupt-Patterns wählen** musst (Decision-Flowchart)
- Die **Token-Kosten** für verschiedene Pattern-Depth vergleichen willst
- Die **3-strategige Hermes-Bridge** (hermes_tools → subprocess → Mock) brauchst
- Bestehende Subagent-Workflows auf **produktives Python** heben willst
- **Sicherheitsschienen** einbauen willst (Depth-Guard, Token-Budget, Sycophancy-Guard)

**Nicht laden wenn:** Du nur ein einzelnes `delegate_task`-Call brauchst → direkt im Briefing, kein Pattern nötig.

## Die 3 Skeletons (TL;DR)

| Skeleton | Pattern | Wann nutzen | File |
|---|---|---|---|
| `master_worker.py` | Queen-Bee Fan-Out | Task in ≥2 unabhängige Subtasks zerlegbar, parallel | `references/skeleton-a-master-worker.md` |
| `hierarchical_tree.py` | 2-Level Tree mit Sub-Orchestrators | Multi-Domain-Tasks (research→implement→review), strukturiertes Routing | `references/skeleton-b-hierarchical-tree.md` |
| `critic_loop.py` | Maker-Checker / Reflexion | Korrektheit ist kritisch (Code-Generation, Security-Reviews) | `references/skeleton-c-critic-loop.md` |

**Vollständiger Source-Code:** `~/10-Projekte/10-active/agent-orchestration-patterns/` (108 KB, 1781 LOC, 27 Tests grün)

## Decision-Flowchart

```
Neuer Task kommt rein
      │
      ▼
Ist es ein einzelner Tool-Call oder triviales Format-Conversion?
  JA  → Tool direkt aufrufen / execute_code.  Keine Delegation.
  NEIN ↓
      │
Kann der Task in N ≥ 2 unabhängige Subtasks zerlegt werden (parallel)?
  JA  → master_worker.py (Skeleton A)
  NEIN ↓
      │
Spannt der Task mehrere Sub-Domains mit je eigenen Workern?
  JA  → hierarchical_tree.py (Skeleton B, depth=2)
  NEIN ↓
      │
Ist Korrektheit so wichtig, dass Verification-Overhead gerechtfertigt ist?
  JA  → critic_loop.py (Skeleton C, max_rounds=3)
  NEIN → master_worker.py ohne Critic (single Worker, no verification)
```

## Token-Budget-Referenz

| Skeleton | Typische Depth | Branching | Token-Multiplier vs. Chat | Wall-Clock (3 Worker) |
|---|---|---|---|---|
| A — Master/Worker | 1 | 4 | ~15× | ~100s parallel |
| B — Tree | 2 | 3×3 | ~45× | ~200s (L1 parallel, L2 parallel) |
| C — Critic-Loop | n/a | n/a | ~15×/Round × Rounds | ~100s × Rounds |

**Datenquellen:** Anthropic Engineering Post (Juni 2025), Hermes `delegate_task`-Doku, Tokenomics-Studien.

## 3-strategige Hermes-Bridge (Kern-Architektur)

Jedes Skeleton versucht **drei** Wege zum echten Agent-Call, in dieser Priorität:

1. **`from hermes_tools import delegate_task`** — direkte Library-Integration (bevorzugt, atomar, getrackt)
2. **`subprocess` auf `hermes -z PROMPT chat`** — Standalone-Python ohne Hermes-Kontext  
   ⚠️ **WICHTIG:** `-z` ist ein **Top-Level-Flag VOR dem Sub-Command**, also `hermes -z "prompt" chat`, NICHT `hermes chat -z "prompt"`!  
   Der Perplexity Deep Research Report vom 2026-07-15 hatte die falsche Form (`hermes chat -z PROMPT`) — wurde im Live-Test 2026-07-16 als Bug entlarvt und gefixt.  
   Siehe `references/hermes-cli-bridge-pitfalls.md` für die vollständige Bug-Analyse.
3. **Stub-Mock** — Dry-Run / Tests / CI

**Warum:** Kontext-unabhängig lauffähig. Funktionieren in einer Hermes-Session, als Cron-Job, oder als Standalone-Tool. **Drop-in für jedes Projekt.**

## Sicherheitsschienen (Anti-Pattern-Fixes)

| Rail | Datei | Verhindert |
|---|---|---|
| `MAX_SAFE_DEPTH = 2` | `hierarchical_tree.py` | Spawn-Storm (OpenCode-Incident erreichte depth 18) |
| `TokenBudget` | `hierarchical_tree.py` | Endloser Token-Verbrauch bei runaway recursion |
| `max_rounds` (Default 3) | `critic_loop.py` | Critic-Loop-Runaway (Agents debattieren ohne Ende) |
| `_is_unrecoverable()` | `critic_loop.py` | Endlos-Retry auf semantischen Fehlern |
| **Idempotency-Keys** | `master_worker.py` | Doppel-Ausführung auf Retry |
| `asyncio.wait_for()` | alle | Runaway-Workers ohne Wall-Clock-Limit |
| Semaphore | alle | API-Storm / Rate-Limit-Verletzungen |
| **Sycophancy-Guard** | `critic_loop.py` | `worker.rationale` NIEMALS an Critic (sonst mirrort Critic Selbst-Einschätzung) |
| **HandoffPacket ≤ 200 Token** | `hierarchical_tree.py` | Context-Explosion auf L2 |
| **`-z`-Flag-Position** | `master_worker.py` | **`-z` ist Top-Level-Flag VOR Sub-Command** — `hermes -z PROMPT chat`, NICHT `hermes chat -z PROMPT`. Perplexity-Report hatte falsche Syntax; gefunden im Live-Test 2026-07-16. |

## Use-Case-Mapping (welcher Task → welches Skeleton)

| Use-Case | Skeleton | Warum |
|---|---|---|
| GreyHack-Mission-Pipeline (research→implement→review) | **Skeleton B** (Tree) | Multi-Domain, klare Stufen |
| TikTok-Hook-Batch (4 Hooks parallel) | **Skeleton A** (Master/Worker) | Unabhängige Subtasks, parallel |
| Code-Gen mit Auto-Test-Critic | **Skeleton C** (Critic-Loop) | Korrektheit kritisch |
| Daily Research Digest (Cron-Job) | **Skeleton A** | Klein, schnell, reproduzierbar |
| Multi-Stage-Marketing-Pipeline | **Skeleton B** + **Skeleton C** pro Stage | Kombiniert Routing + Verification |
| 100-Papers-Daily-Research | **Skeleton A** mit Worker-Pool (N=10) | Map-Reduce-Pattern |
| Content-Multiplikation (30 Posts/Woche) | **Skeleton A** mit Template-Worker | Gleicher Pattern, verschiedene Topics |

## Quick-Start (5 Min zum ersten Run)

```bash
# 1. Repo klonen oder kopieren
cd ~/10-Projekte/10-active/agent-orchestration-patterns

# 2. Syntax + Tests verifizieren
python3 -m pytest tests/ -v   # → 27 passed

# 3. Dry-Run aller 3 Skeletons
python3 master_worker.py --dry-run "Test goal A"
python3 hierarchical_tree.py --dry-run
python3 critic_loop.py --dry-run "Test goal C"

# 4. In eigenem Projekt verwenden (Copy-Paste)
cp master_worker.py ~/mein-projekt/orchestration/
# → dann in deinem Code: from orchestration.master_worker import QueenOrchestrator
```

## Skeleton-Wahl-Matrix (vertieft)

| Kriterium | Skeleton A | Skeleton B | Skeleton C |
|---|---|---|---|
| **Parallelisierbar** | ✅ hoch | ⚠️ medium (Stufen) | ❌ sequentiell (Loop) |
| **Verifikation** | optional | optional | **PFLICHT** (Rubric) |
| **Sub-Domain-Routing** | nein | **JA** | nein |
| **Cost-Tiering** | Queen teuer / Worker günstig | L1 mittel / L2 günstig | Worker günstig / Critic teuer |
| **Termination** | Alle Worker fertig | Alle Subtrees fertig | PASS oder max_rounds |
| **Debug-Trace** | Audit-JSON | Trace-JSON mit correlation_id | History-Liste |
| **Failure-Cascade-Risk** | niedrig (Worker isoliert) | mittel (Subtree-Failure blockiert L2) | niedrig (Loop bricht ab) |

## Architektur-Entscheidungen (warum so)

| Entscheidung | Warum |
|---|---|
| 3-strategige Hermes-Bridge | Kontext-unabhängig lauffähig |
| HandoffPacket statt Raw-Context | Verhindert Context-Explosion auf L2 |
| Sycophancy-Guard via leere `rationale` | Critic mirrort sonst Worker-Selbst-Einschätzung |
| Idempotency-Cache (sha256) | Verhindert Doppel-Execution bei Retry |
| Cheap-Worker / Capable-Queen/Critic | 40-60% Cost-Reduction empirisch |
| MAX_SAFE_DEPTH=2 als Default | OpenCode-Incident erreichte depth 18 unkapiert |
| Audit-Trail als JSON | Vollständig replay-bar |
| Token-Budget als Hard-Cap | Verhindert Endlos-Token-Burn |

## Tests (alle grün)

```bash
cd ~/10-Projekte/10-active/agent-orchestration-patterns
python3 -m pytest tests/ -v
# → 27 passed in 16s

# Coverage-Matrix:
# - Idempotency-Cache (sha256-key, skip-logic)
# - Concurrency-Cap (Semaphore, peak-tracking)
# - Retry-Recovery (exponential backoff mit Jitter)
# - Audit-Trail (parseable JSON)
# - Depth-Guard (refused bei depth > MAX)
# - Token-Budget (raises bei Überschreitung)
# - Correlation-ID (unique pro Run, threaded durch alle Sub-Results)
# - Trace-JSON-Schema (alle Felder korrekt)
# - Termination-Logic (UNRECOVERABLE > PASS > max_rounds)
# - Sycophancy-Guard (Code-Inspection: rationale NICHT in Critic-Prompt)
# - JSON-Parser-Robustheit (Markdown-Fences tolerant)
```

## Reference Files (Deep-Dives)

| Datei | Inhalt | Wann lesen |
|---|---|---|
| `references/skeleton-a-master-worker.md` | Vollständiger Deep-Dive zu Skeleton A inkl. Code-Walkthrough | Wenn du A nutzen willst |
| `references/skeleton-b-hierarchical-tree.md` | Tree-Architektur, HandoffPacket-Protocol, Token-Budget-Guard | Wenn du B nutzen willst |
| `references/skeleton-c-critic-loop.md` | Maker-Checker-Mechanik, Sycophancy-Guard-Details, Rubric-Design | Wenn du C nutzen willst |
| `references/integration-guide.md` | Wie du die Skeletons in ein bestehendes Projekt integrierst | Beim ersten Setup |
| `references/perplexity-research-summary.md` | Original-Quellen + 3-Stufen-Evaluierung des Perplexity-Reports | Bei Quellen-Skeptikern |
| `references/hermes-cli-bridge-pitfalls.md` | Bug-Analyse (`-z`-Flag-Position), Live-Test-Metriken, QUEEN_LIVE_TEST-Workaround | Bei Subprocess-Bridge-Problemen |

## Pattern-Wahl-Empfehlung (deine Projekte)

Basierend auf den 2026-07-16 verifizierten Dry-Runs:

| Projekt | Empfehlung | Begründung |
|---|---|---|
| GreyHack-Mission-Pipeline | Skeleton B | Multi-Domain, klare Stufen, korrelationsgetrackt |
| TikTok-Content-Batch | Skeleton A | 4-8 Hooks parallel, unabhängig, günstig |
| Code-Gen + Tests | Skeleton C | Korrektheit kritisch, Rubric steuerbar |
| Daily-Research-Cron | Skeleton A mit N=3 | Schnell, idempotent, reproduzierbar |
| Marketing-Pipeline | Skeleton B outer + Skeleton C per Stage | Routing + Verification kombiniert |
| Discord-Voice-Bot-Diagnose | Skeleton A | 1 Domain, parallele Diagnose-Tasks |

## Related Skills (komplementär — nicht überschneidend)

- **`multi-agent-pitfalls-cheatsheet`** — Trigger-Watchlist (LADE VOR jedem Spawn)
- **`multi-agent-cluster-patterns`** — Theorie: 13 Patterns + 🅰️🅱️🅲️ Dispatch-Mode Selection (welcher Workflow-CHARAKTER passt)
- **`sub-sub-workflow`** — Pattern 12 Detail (verifizierbare 2-Level-Delegation)
- **`subagent-driven-development`** — Generischer Subagent-Workflow
- **`delegation-anti-patterns`** — Hermes-spezifische Pitfalls
- **`queen-bee-schwarm-dispatch`** — Pattern-Worker-Cluster-Konzept

**Workflow:** Pattern-Wahl (dieser Skill) → Cheatsheet (Pitfalls) → Cluster-Pattern (wenn Multi-Phase) → Spawn mit Briefing → Verify.

## Provenance & Live-Validierung

| Datum | Validierung | Ergebnis |
|---|---|---|
| 2026-07-15 | Perplexity Deep Research Report erhalten | ✅ 13/13 Deliverables, 4/6 Quellen solide |
| 2026-07-15 | 3-Stufen-Evaluierung (Konsens / Quellen / Decision) | ✅ Action-Items priorisiert |
| 2026-07-16 | 3 Skeletons produktiv geschrieben (108 KB, 1781 LOC) | ✅ alle syntax-OK |
| 2026-07-16 | 27 Pytest-Tests geschrieben + gefixt | ✅ 27/27 grün in 16s |
| 2026-07-16 | Dry-Run aller 3 Skeletons (reale Execution) | ✅ alle success, Audit-Trails geschrieben |
| 2026-07-16 | Skill angelegt + Memory-Notiz geschrieben | ✅ done |
| 2026-07-16 | **ECHTER Live-Test** via Subprocess-Bridge (MiniMax-M3) | ✅ **Bug-Fix:** `hermes chat -z` → `hermes -z chat` (Perplexity-Report hatte falsche Syntax). 2 Runs: 7.27s / 8.4s, echte LLM-Antworten, Audit-Trails valide. QUEEN_LIVE_TEST=1 Workaround etabliert. |

**Origin:** Basti-Auftrag "gib mir einen promt für perplexity deep research zu Agnet zu Subagent orchestration" → Perplexity-Report → 3-Stufen-Filter → produktive Skeletons → Skill-Wiederverwendbarkeit.

**Maintainer:** Basti + Yuno (2026-07-16)
**Lizenz:** MIT
**Quell-Repo:** `~/10-Projekte/10-active/agent-orchestration-patterns/`
**Quell-Skill:** dieser Skill
**Quell-Report:** `~/.hermes/docus/reports/2026-07-16-agent-orchestration-skeletons-productive.md`

---

_Final Note from Yuno:_
_Dieser Skill ist Pattern-Wahl + Code-Drop-In — du lädst ihn wenn du einen Multi-Agent-Workflow baust und die Wahl zwischen A/B/C treffen musst. Der Code liegt fertig im Repo, getestet, dokumentiert. Du kopierst was du brauchst in dein Projekt, integrierst die Hermes-Bridge, und bist live. ♛_