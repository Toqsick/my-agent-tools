# Skill README — agent-orchestration-patterns-2026

**Version:** 1.0.0 (2026-07-16)
**Autor:** Yuno + Basti
**Lizenz:** MIT

## Was dieser Skill tut

Liefert 3 produktive Python-Skeletons für die häufigsten Multi-Agent-Orchestration-Patterns (Queen-Bee, 2-Level Tree, Critic-Loop) + Decision-Flowchart + Token-Budget-Tabelle + Integration-Guide + Verify-Script. Drop-in für jedes Hermes-Projekt.

## Struktur

```
agent-orchestration-patterns-2026/
├── SKILL.md                          ← Hauptdatei (vom Hermes-Skill-Loader geladen)
├── references/
│   ├── skeleton-a-master-worker.md   ← Deep-Dive Skeleton A (17 KB)
│   ├── skeleton-b-hierarchical-tree.md  ← Deep-Dive Skeleton B (19 KB)
│   ├── skeleton-c-critic-loop.md     ← Deep-Dive Skeleton C (21 KB)
│   ├── integration-guide.md          ← 5-Min-Setup + Anpassungs-Patterns
│   └── perplexity-research-summary.md  ← Quellen-Triage + 3-Stufen-Filter
├── templates/
│   ├── subdomain-templates.json      ← vorgefertigte Subdomain-Definitionen
│   └── rubric-templates.json         ← vorgefertigte Critic-Rubrics (5 Domains)
└── scripts/
    └── verify_skeletons.py           ← Health-Check (Syntax + Config + Tests)
```

**Quell-Repo mit Skeleton-Code:** `~/10-Projekte/10-active/agent-orchestration-patterns/`
(dort liegen `master_worker.py`, `hierarchical_tree.py`, `critic_loop.py`, `tests/`)

## Schnellstart (5 Min)

```bash
# 1. Skeleton-Code in dein Projekt kopieren
cp ~/10-Projekte/10-active/agent-orchestration-patterns/master_worker.py ~/mein-projekt/orchestration/
cp ~/10-Projekte/10-active/agent-orchestration-patterns/hierarchical_tree.py ~/mein-projekt/orchestration/
cp ~/10-Projekte/10-active/agent-orchestration-patterns/critic_loop.py ~/mein-projekt/orchestration/

# 2. Health-Check laufen lassen
python3 ~/.hermes/skills/orchestration/agent-orchestration-patterns-2026/scripts/verify_skeletons.py \
    --skeletons-dir ~/mein-projekt/orchestration/

# 3. Im Code verwenden
from orchestration.master_worker import QueenOrchestrator
queen = QueenOrchestrator()
result = await queen.run("Research goal")
```

## Verwandte Skills

- `multi-agent-pitfalls-cheatsheet` — Trigger-Watchlist (LADE VOR jedem Spawn)
- `multi-agent-cluster-patterns` — Theorie: 13 Patterns + 🅰️🅱️🅲️ Dispatch-Mode
- `sub-sub-workflow` — Pattern 12 (verifizierbare 2-Level-Delegation)
- `subagent-driven-development` — Generischer Subagent-Workflow
- `delegation-anti-patterns` — Hermes-spezifische Pitfalls
- `queen-bee-schwarm-dispatch` — Pattern-Worker-Cluster-Konzept

## Provenance

- **2026-07-15:** Perplexity Deep Research Report (Master-Prompt + 13 Folge-Prompts)
- **2026-07-15:** 3-Stufen-Evaluierung (Konsens / Quellen / Decision-Matrix)
- **2026-07-16:** 3 Skeletons produktiv geschrieben (108 KB, 1781 LOC, 27 Tests grün)
- **2026-07-16:** Skill-Wiederverwendbarkeit dokumentiert

## Maintainer

Basti + Yuno (2026-07-16)
Repo: `~/10-Projekte/10-active/agent-orchestration-patterns/`
Abschluss-Report: `~/.hermes/docus/reports/2026-07-16-agent-orchestration-skeletons-productive.md`