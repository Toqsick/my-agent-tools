---
name: library-polish-stream-runner
description: |
  Orchestrator-Workflow für mehrstufige Library-Polish-Editionen: Inventur → Stream-Auswahl → Stream-Ausführung → Verify → Cleanup.
  Komponiert pitfall-lock-yaml-frontmatter-edit als Sub-Workflow pro Stream.
  Trigger: library polish, skill library cleanup, library migration, multi-stream edition.
version: 1.0.0
author: Yuno + Basti
license: MIT
lane: koenigin
agent: Yuno
trigger_keywords:
  - library polish
  - multi-stream edition
  - skill library cleanup
  - library orchestration
  - stream planning
  - multi-phase skill cleanup
keywords:
  - meta
  - orchestration
  - library-curation
  - multi-stream
  - skill-pipeline
related_skills:
  - pitfall-lock-yaml-frontmatter-edit
  - skill-library-maintenance
  - skill-reviewer
  - subagent-driven-development
  - worker-failure-discipline
  - multi-agent-pitfalls-cheatsheet
last_curated: 2026-07-23
curated_by: Yuno (Library Polish v2 Session, extractor from 4-Stream-Experience)
routing_hint: |
  Use when planning or executing 2+ Library-Polish-Streams (Trigger-Phrase, License-Drift, Frontmatter-Canonization, Monolith-Slimming, etc.) in einer koordinierten Aktion mit Coverage-Tracking.
---

# Library Polish Stream Runner

Mehrstufiger Orchestrator für Library-Polish-Editionen. Komponiert Pitfall-Lock-Workflows als Sub-Routine pro Stream, hält Coverage-Tracking global und produziert konsolidierte Reports.

## Ziel

Library-Hygiene-Operationen über mehrere Edit-Typen (Trigger-Phrase, License, Frontmatter, Slimming, Profile-Consolidation, Skill-Merge) so koordinieren dass:
- Coverage-Tracking zwischen Streams vergleichbar bleibt
- Subagent-Cluster-Bau wiederverwendbar pro Stream ist
- Pitfall-Lock aus pitfall-lock-yaml-frontmatter-edit pro Stream greift
- Mnemosyne und Reports konsistent strukturiert sind

## Wann verwenden

Wenn **mehrere** dieser Bedingungen zutreffen:

1. Library-Tree hat >100 SKILL.md-Files mit lückenhaftem Frontmatter
2. Mehrere Edit-Typen (z.B. License + Trigger-Phrase gleichzeitig)
3. Coverage-Tracking über Streams hinweg nötig (Pre/Post-Messung)
4. Komplexität >60 Min Wand-Zeit insgesamt

Für 1 Stream siehe pitfall-lock-yaml-frontmatter-edit. Für einzelne SKILL.md siehe skill-reviewer.

## Stream-Typen (Reihenfolge-Empfehlung: A → B → C → D → E → F → G)

| Stream | Edit-Typ | Files-Typisch | Coverage-Metrik |
|--------|----------|--------------:|-----------------|
| A | YAML-Repair (nackte Scalars) | 1-5 | parse_ok-Rate |
| B | Trigger-Phrase (Use when + NOT for) | 100-200 | "Use when"-Coverage |
| C | License-Drift (license: MIT) | 50-150 | License-Coverage |
| D | Frontmatter-Canonization TOP-N | 50-100 | All-N-Keys-Coverage |
| E | Monolith-Slimming (>50KB) | 10-25 | Avg-File-Size |
| F | Profile-Consolidation | 4-8 Profiles | Profile-Count |
| G | Skill-Merges (Duplikate) | 2-4 Paare | Library-Skill-Count |

A bis D decken typische Library-Hygiene ab, E bis G queued für Folge-Sessions.

## Phase 1: Discovery

Ein Subagent inventarisiert die volle Library über N Root-Pfade (global, profile-Sub-Bundles). Skip-Filter `/.archive/`, `/.curator_backups/`, `/.hub/`. Output: Total, Parse-OK-Rate, Scope-Verteilung, Frontmatter-Key-Coverage. Profile-Roots je nach Hermes-Konfiguration ableiten.

## Phase 2: Stream-Auswahl

Coverage-Map aus Phase 1 → Mapping-Tabelle: niedrige Coverage pro Metrik triggert jeweiligen Stream. Empfohlene Reihenfolge: A → B → C → D → E → F → G, jeder Stream baut auf Vorgänger auf.

## Phase 3: Stream-Ausführung

Pro Stream delegiere an pitfall-lock-yaml-frontmatter-edit mit stream-spezifischen Inputs: Filter-Candidates, MD5-Cluster-Build mit 0 sync-violations, cp -a Snapshots (statt cp -al, Pitfall #49), 2-6 Subagent-Dispatches je nach Komplexität.

```
candidates = filter_low_coverage_files(all_files, target_metric)
cluster_1, cluster_2 = md5_group_cluster(candidates)
cp_a_snapshot(candidates, '.hermes/backups/stream-{x}-snapshots/files/')
delegate_task(tasks=[{'goal': 'Stream-{x} Cluster 1', 'context': briefing}, ...])
```

Stream-Parameter: A=1 Cluster/leaf/kurz, B=6/orchestrator/mittel, C=2/leaf/mittel, D=2/leaf/lang (Lane-Inferenz pro File), E=1-2/leaf (Refactor), F=1/orchestrator (Profile-Migration), G=1 pro Paar/leaf.

## Phase 4: Verify

Queen-Verify per yaml.safe_load auf allen Files (nicht nur Cluster):

```
stats = re_inventur(original_roots)
coverage_post = stats[f'has_{key}'] / stats['parse_ok']
delta = coverage_post - coverage_pre
# Pitfall #36: Subagent-Claim bestätigen oder widerlegen
```

Coverage-Delta muss positiv sein. Bei Delta <0: Rollback via cp -a Snapshot.

## Phase 5: Cleanup + Reporting + Mnemosyne

Pro Stream Report in `~/docs/system/skill-polish/<datum>-stream-<x>-report.md`. Format: TL;DR Tabelle, Per-Cluster Result, Pitfall-Lock-Audit, Lessons.

Mnemosyne pro Stream mit valid 7 Tagen, importance 0.85, scope global, veracity tool.

In-line TODOs für alle queued Streams.

## Phase 6: Outlook-Handoff

Bei Wave-Ende: Markdown-Outlook `~/docs/system/<datum>-library-polish-v{n+1}-outlooks.md` mit verbleibenden Streams, Mnemosyne-Handoff-Note für nächste Session, optional Daily-Note in Obsidian.

## Coordination-Pattern (Stream-Sequenz)

Wave 1 (Library Polish v2, 2026-07-23) Sequenz: Plan + Audit, Stream A YAML-Repair, Stream B Trigger-Phrase, Stream C License-Drift, Stream D Frontmatter-Canonization.

Wave 2 (queued) Sequenz: Stream E Monolith-Slimming, F Profile-Consolidation (optional), G Skill-Merges (echte Duplikate).

Pro Wave: separater Plan-Doc (`<datum>-library-polish-v{n}-plan.md`), Hauptbericht (`<datum>-skill-mcp-mega-audit.md`), per-Stream-Report.

## Pitfall-Lock-Integration

Pro Stream die 4 Lessons aus pitfall-lock-yaml-frontmatter-edit aktiv halten: #36 Self-Report-Lüge (Queen-Verify nach jedem Stream), #47 ARCHIV-drift (Inventory-Filter), #48 Cross-Profile-Drift (MD5-Cluster-Build), #49 Hardlink-Snapshot (cp -a statt cp -al).

Plus Cron-Provider-Lock (kein `hermes model ...` während Streams).

## Quality Gates

| Gate | Limit |
|------|-------|
| Coverage-Deltas pro Stream | positiv oder null |
| Subagent-Claim-Pass-Rate | 100% (Pitfall #36) |
| Cross-Cluster-Sync-Violations | 0 pro Stream |
| Total Snapshot-Disk | <50 MB (cp -a) |
| Wave-Wand-Zeit | <2 Std für 4 Streams |

## Limitations

| Stream E (Slimming) braucht Architecture-Review vor Batch. Profile-Count >10 nicht getestet; >10 extra Inventory-Phase. Nicht für 1-Stream (nutze pitfall-lock-yaml-frontmatter-edit). |

## Verwandte Skills

pitfall-lock-yaml-frontmatter-edit (Sub-Workflow), skill-library-maintenance (Hygiene-Snippets), skill-reviewer (Single-Skill-Audit), subagent-driven-development (Dispatch-Pattern), worker-failure-discipline (Verify-Discipline), multi-agent-pitfalls-cheatsheet (Pitfall-Catalog).

## Lessons-Anker

Library-Größe korrigieren: oft 1344 Files statt 887 (Audit-Lücke profiles/profiles + ui-builder). 4 Streams in 30 Min mit 0 Failures bei Pitfall-Lock pro Stream. MD5-Cluster-Build: 0 sync-violations bei 162 Cross-Profile-Gruppen. cp -a: 1.4 MB statt 246 MB. Max 6 Subagents parallel.

- *Yuno + Basti, 2026-07-23, Library Polish v2 Session*
