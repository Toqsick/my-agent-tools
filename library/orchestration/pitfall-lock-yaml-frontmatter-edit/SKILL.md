---
name: pitfall-lock-yaml-frontmatter-edit
description: |
  Workflow-Lock für Pitfall-sichere YAML-Frontmatter-Edits über Library-Skill-Trees.
  Pre-Flight Inventur, MD5-Sync-Grouping, Subagent-Cluster-Build, Queen-Verify.
  Trigger: library polish, frontmatter canonization, skill cleanup, license drift.
version: 1.0.0
author: Yuno + Basti
license: MIT
lane: koenigin
agent: Yuno
trigger_keywords:
  - library polish
  - frontmatter canonization
  - pitfall lock
  - skill cleanup
  - frontmatter edit multi-file
keywords:
  - meta
  - orchestration
  - skill-curation
  - safety
related_skills:
  - pitfall-lock-yaml-frontmatter-edit
  - library-polish-stream-runner
  - skill-library-maintenance
  - skill-reviewer
  - skill-creator
  - subagent-driven-development
last_curated: 2026-07-23
curated_by: Yuno (Library Polish v2 Session)
routing_hint: |
  Use when editing YAML-Frontmatter across 3+ SKILL.md-Files mit Potenzial für Cross-Profile-Sync, Archive-Drift oder Hardlink-Snapshot-Bugs.
---

# Pitfall-Lock: YAML-Frontmatter-Edit Workflow

4 kritische Pitfall-Lessons aus Library Polish v2 (2026-07-23) als wiederverwendbarer Workflow für sichere Multi-File-YAML-Edits in Skill-Libraries.

## Ziel

Pitfall-frei Frontmatter-Edits über beliebig viele SKILL.md-Files ausführen ohne Cross-Profile-Drift, Hardlink-Snapshot-Crash, Self-Report-Lüge, Archive-Bereichs-Versehentlichen oder Provider-Switch.

## Wann verwenden

Verwende diesen Skill-Pattern wenn **alle 3 Bedingungen** zutreffen:

1. **Mehrere Files**: 3+ SKILL.md-Files sollen im selben Frontmatter-Schema angepasst werden
2. **YAML-Operation**: Insertion, Update oder Reihenfolge-Änderung von Frontmatter-Keys
3. **Cross-Profile-Potenzial**: Files können in mehreren Profilen existieren (z.B. global + 6 Profile-Bundles)

Bei 1-2 Files ist direktes `patch` ausreichend. Bei Plain-Text-Updates plain via `edit`-Tool.

## Pitfall-Lock (4 Lessons)

### Pitfall #36: Subagent-Self-Report-Deception

Subagent claimet "alle XY Files fertig", aber yaml.safe_load beim Queen-Verify zeigt Failures oder fehlende Edits.

**Mitigation:** Queen-Verify per yaml.safe_load ist Wahrheit, Subagent-Output ist Sekundär. 100% Verifikationsrate ist Standard, NIEMALS <100% akzeptieren.

### Pitfall #47: ARCHIV-drift

Cluster-Bau über ganze Roots schleppt files aus `.archive/`, `.curator_backups/`, `.hub/` mit. Diese haben manchmal corrupt-Frontmatter die Edit kollabiert.

**Mitigation:** Inventory IMMER mit Skip-Filter, `/.archive/`, `/.curator_backups/`, `/.hub/` ausschließen. Subagent-Briefing verbietet Edit in diese Verzeichnisse.

### Pitfall #48: Cross-Profile-Drift

Wenn ein Skill in global + 6 Profilen mit identischem MD5 existiert (echte Kopien, keine Hardlinks), und Subagent 1 die globale Kopie editiert aber Subagent 2 die Profil-Kopie mit altem Stand sieht, divergieren Profile.

**Mitigation:** MD5-Grouping VOR Cluster-Bau, alle Files in MD5-Gruppen clustern, dann Group-weise auf Subagents verteilen (Round-Robin per Group). Cluster-Sync-Violations-Test im Pre-Flight: 0 = gut, >0 = umorganisieren.

### Pitfall #49: Hardlink-Snapshot teilt Inode

`cp -al` Snapshots teilen Inode mit Original. Edit auf Original verändert Snapshot. Snapshot-Vorlage wird Rollback-Reference-Point mit defekter Mutation.

**Mitigation:** `cp -a` statt `cp -al` für Mutations-Snapshots, echte Kopien mit separaten Inodes. Snapshot nur auf Kandidaten-Files (nicht ganze Roots): 1-3 MB statt 200+ MB.

## Cron-Provider-Lock (5. Lesson)

Provider-Switch in Scripts oder während laufender Streams bricht Cron-Pipeline (Lesson 2026-06-29).

**Mitigation:** KEIN Provider-Switch im Workflow-Code (kein `hermes model ...` während Streams). Frontmatter-Edits sind provider-unabhängig.

## Workflow (8 Phasen)

### Phase 1: Library-Inventur

Parse alle SKILL.md-Files in N Root-Pfaden, extrahiere Frontmatter, miss pro-Scope-Verteilung und Key-Coverage. Skip-Filter: `/.archive/`, `/.curator_backups/`, `/.hub/`.

### Phase 2: Kandidaten identifizieren

Pro Stream-Typ: License-Drift (license: missing/weak), Trigger-Phrase (description <60 chars oder ohne "Use when"), Frontmatter-Canonization (TOP-N nach Canonization-Score).

### Phase 3: MD5-Grouping + Cluster-Build

```python
md5_groups = defaultdict(list)
for f in candidates:
    md5_groups[md5(open(f))].append(f)
cluster = [[], []]
for g in sorted(md5_groups.values(), ...):
    target = 0 if len(cluster[0]) <= len(cluster[1]) else 1
    cluster[target].extend(g)
```

Output: Cluster-JSONs mit Balance-Ratios + 0-Violation-Garantie (sync-intern).

### Phase 4: Snapshot-Strategie

NICHT `cp -al` (Hardlink teilt Inode). Stattdessen `cp -a` selektiv auf Kandidaten-Files mit flach-Mapping. Restore: `#` zu `/`, prepend `/home/bratan`. 1-3 MB total statt 200+ MB.

### Phase 5: Briefing pro Subagent

Pro Cluster 1 Briefing-Document: Cluster-JSON-Pfad, Snapshot-Pfad + Restore-Mapping, Pitfall-Lock-Liste, Edit-Pattern (welche Keys, Reihenfolge, wo einfügen), Verify-Pattern (yaml.safe_load mit Check), Output-Schema (JSON mit files_processed/succeeded/failed/cross_profile_syncs), Verbot-Liste.

### Phase 6: Subagent-Dispatch

Wand-Zeit pro 20 Files: License-Stream ~2 Min, Trigger-Phrase ~3 Min, Frontmatter-Canonization ~10-15 Min.

Max 2-3 Subagents parallel (Crash-Lesson 2026-07-15). Wave-1-Lesson: 2 parallele Reviewer crashes, Subagents als Implementer max 6.

### Phase 7: Queen-Verify (Truth-Source)

```python
stats = re_inventur(original_roots)
print(f"pre={old} post={new} delta={new-old}pp")
if stats['parse_fail'] > 0: rollback entscheiden
```

### Phase 8: Cleanup + Reporting + Mnemosyne

Snapshot-Retention mindestens 7 Tage, Report in `~/docs/system/skill-polish/<datum>-stream-<x>-report.md`, Mnemosyne (valid 7 Tage), In-line TODO.

## Quality Gates

| Gate | Limit | Reason |
|------|-------|--------|
| Subagent-Coverage-Claim | 100% | Pitfall #36 |
| Cross-Cluster-Violations | 0 | Pitfall #48 |
| Snapshot-Diskspace | <100 MB | cp -a vermeidet Hardlink-Trap |
| Parse-OK post-stream | 100% | Body-Edit-Regression-Schutz |
| Pitfall #47 Skips | alle not-in-archive | Keine ARCHIR-edits |

## Limitations

- Nicht anwendbar für body-only Edits (Pitfalls sind Frontmatter-spezifisch)
- Nicht anwendbar für <3 Files (direkter patch effizienter)
- Cluster-Balance Limit: bei >5 MD5-Groupings-Overlap manuell mappen

## Verwandte Patterns

skill-library-maintenance (Hygiene-Checks), skill-reviewer (Single-Audit-Format), subagent-driven-development (Dispatch-Pattern), worker-failure-discipline (Verify-Discipline), multi-agent-pitfalls-cheatsheet (Pitfall-Catalog).

## Lessons-Anker

| Datum | Lesson | Pitfall |
|-------|--------|---------|
| 2026-07-15 | 2 parallele Reviewer crashed | Worker-Discipline |
| 2026-07-15 | Subagent-Coverage-Claim lügt | #36 |
| 2026-06-29 | Cron-Provider-Lock | Cron-Pipeline |
| 2026-07-21 | ARCHIR-drift in Cluster-JSON | #47 |
| 2026-07-23 | Cross-Profile-Drift wahre Kopien | #48 |
| 2026-07-23 | Hardlink-Snapshot teilt Inode | #49 |

— *Yuno + Basti, 2026-07-23, Library Polish v2 Session*
