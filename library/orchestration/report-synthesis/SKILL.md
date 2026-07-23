---
name: report-synthesis
description: >-
  Use when user asks for combining three or more subagent reports, writing a coherent master report, mapping overlaps and cross-references across findings, or building a consolidated resource index. NOT for summarizing only one or two reports or merging reports about unrelated topics. Preserves specialized source reports while adding structural synthesis, cross-report insights, navigation, and a concise executive view.
version: 1.0.0
author: Yuno
license: MIT
platforms:
  - linux
  - macos
  - windows
metadata:
  hermes:
    tags:
      - documentation
      - synthesis
      - consolidation
      - report
      - multi-agent
      - orchestration
    related_skills:
      - subagent-driven-development
      - multi-agent-master-workflow
      - plan-glm
      - multi-agent-orchestration
    lane: koenigin
    reasoning_effort: xhigh
trigger_keywords: ['reports', 'and', 'report-synthesis', 'combining', 'three']
keywords: ['reports', 'report', 'cross', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['dogfood', 'weekly-insights-synthesis']
---

# Report Synthesis — Multi-Report Documentation Consolidation

> **Kernprinzip:** Wenn 3+ Subagent-Reports zum gleichen Thema vorliegen,
> schreibe KEINEN vierten Report der dasselbe nochmal mined. Schreibe
> einen **Synthese-Layer** der die bestehenden Reports zueinander in
> Beziehung setzt, Lücken identifiziert und einen Navigator bietet.

## When to Use

- 3+ Subagent-Reports zu verwandten Themen liegen vor (z.B. Deep-Mining + Working-Agreement-Evolution + Fall-Study)
- Reports überlappen teilweise thematisch, decken aber unterschiedliche Aspekte ab
- Der Benutzer will den Gesamtüberblick ("Master-Bericht")
- Die Reports sind einzeln zu spezialisiert oder tief, um den Zusammenhang zu verstehen

**NICHT verwenden wenn:**
- Nur 1-2 Reports vorliegen (einfache Zusammenfassung reicht)
- Reports völlig unabhängige Themen abdecken (separate Handoffs, keine Synthese nötig)
- Der Benutzer explizit nach Rohdaten / unkonsolidierten Reports fragt

## The Process

### Phase 0: Inventory (was haben wir?)

Lies alle Reports und erstelle eine Ressourcen-Tabelle:

```markdown
| Report | Größe | Kernthema | 3 Hauptfindings |
|---|---|---|---|
| working-agreement-evolution.md | 35 KB / 4.007 W | WA-Chronologie + Yuno-Disziplin | (a) (b) (c) |
| subagent-self-test-deception.md | 54 KB / 6.623 W | Subagent-Fallstudie | (a) (b) (c) |
| daily-report-trigger-handoff.md | 7 KB / 1.012 W | Trigger-Handoff | (a) (b) (c) |
```

Dokumentiere **welches Modell** jeden Report geschrieben hat (Queen vs Subagent vs GLM 5.2) — das erklärt ggf. Stil- und Tiefenunterschiede.

### Phase 1: Structural Map

Lege die Master-Dokument-Struktur fest:

```
1. Executive Summary (TL;DR) — 1 Seite, was heute geliefert wurde
2. §1 — Sub-Report A Zusammenfassung
3. §2 — Sub-Report B Zusammenfassung
4. §3 — Sub-Report C Zusammenfassung
5. §4 — Synthese (übergreifende Insights QUER zu allen Reports)
6. Meta-Reflexion — was das Arbeiten selbst über das System verrät
```

**Regel:** Jede §-Section fasst den Sub-Report in 500-1000 Wörtern zusammen. Zitieren erlaubt, aber KEIN Volltext-Kopieren — das ist re-mining und bläht auf. Der Leser hat die Original-Reports referenziert.

### Phase 2: Cross-Reference Map

Identifiziere Themen, die in MEHREREN Reports vorkommen:

| Thema | Report A | Report B | Report C |
|---|---|---|---|
| 17 Pioneer-Patterns | §2 (3 Zeilen) | §3 (ausführlich) | — |
| Subagent-Deception | — | §4 (vollständig) | §3 (1 Absatz) |
| Queen-Audit-Pflicht | §5 (Implikation) | §4 (Empfehlung) | §3 (Pitfall-Eintrag) |

Diese Cross-Reference-Map ist der MEHRWERT der Synthese — sie zeigt Zusammenhänge die kein Einzelreport sehen kann.

### Phase 3: Meta-Reflexion schreiben

Die wertvollste Section der Synthese. Beantworte:

1. **Was hat der Workflow heute über das System verraten?**
   - Z.B. "Wir haben die 4-Phasen-Werkstatt-Methodik gelebt während wir sie auditierten"
2. **Welche Rolle hatte die Queen heute?**
   - Builder? Auditor? Integrator? Orchestrator?
3. **Wo liegen die noch offenen Fäden?**
4. **Was ist die wichtigste Lektion die NUR in der Synthese sichtbar wird?**

Die Meta-Reflexion sollte **nicht** in den Sub-Reports zitierbar sein — sie existiert nur im Synthese-Layer.

### Phase 4: Resource-Verzeichnis

Füge ein strukturiertes Verzeichnis aller Assets an:

```markdown
**Reports & Handoffs:**
- `~/.hermes/docus/reports/<report-A>.md` — was es ist
- `~/.hermes/docus/reports/<report-B>.md` — was es ist
- `~/.hermes/docus/handoffs/<handoff>.md` — was es ist

**Skills (neu/patch):**
- `~/.hermes/skills/<category>/<skill>/SKILL.md` — Version + Änderung

**Plan:**
- `~/.hermes/plans/<plan>.md` — N Tasks

**Mnemosyne:**
- ID `<id>` — Zweck (importance 0.85, scope: global)

**Vault:**
- `~/Dokumente/Obsidian Vault/path/to/note.md` — Status
```

Das Resource-Verzeichnis ist der **einzige Ort** der alle Assets in einem Dokument vereint — das ist der konkrete Nutzen der Synthese für den Benutzer.

## Composition Rules

### DOs

- ✅ Querverweise zu Sub-Reports: `(siehe §3 im Working-Agreement-Report)`
- ✅ Kurze, prägnante Zusammenfassungen (500-1000 Wörter pro §)
- ✅ Tabellen für Cross-Reference-Maps
- ✅ Executive Summary als ersten sichtbaren Block (der Benutzer entscheidet ob er weiterliest)
- ✅ Meta-Reflexion als Abschluss — sie ist der emotionale/konzeptionelle Clou
- ✅ Resource-Verzeichnis als praktischer Nutzen
- ✅ Modell- und Tool-Chain transparent dokumentieren

### DON'Ts

- ❌ Sub-Reports nicht neu ausminen (kein erneutes `grep`/`find` für Daten die bereits erforscht sind)
- ❌ Keine Redundanz schaffen — wenn etwas in Report A steht, zitieren, nicht wiederholen
- ❌ Kein "und das war's"-Abschluss — immer eine Meta-Reflexion liefern
- ❌ Sub-Reports nicht gegeneinander ausspielen (Report A ist besser/schlechter als B)
- ❌ Synthese nicht länger machen als der kürzeste Sub-Report — sie muss kompakter sein

### Die 80/20-Regel der Synthese

20% der Wörter liefern 80% des Werts. Die wertvollen 20% sind:
1. Executive Summary (TL;DR)
2. Cross-Reference Map (Phase 2)
3. Meta-Reflexion (Phase 3)
4. Resource-Verzeichnis (Phase 4)

Die restlichen 80% (§1-3) sind "notwendiges Übel" — sie machen die Synthese autark ohne die Original-Reports lesen zu müssen. Schreib sie so kompakt wie möglich.

## Proven Example

Session 2026-07-16, 3 Subagent-Reports:

| Report | Modell | Größe |
|---|---|---|
| Working-Agreement-Evolution | Subagent (MiniMax-M3) | 35 KB / 4.007 W |
| Subagent-Fall-Study | Subagent (MiniMax-M3) | 54 KB / 6.623 W |
| Trigger-Handoff | Queen | 7 KB / 1.012 W |
| **Master-Synthese** | **Queen (MiniMax-M3)** | **28 KB / 3.322 W** |

Die Master-Synthese war **kürzer als jeder Sub-Report** (28 KB vs 35+54 KB) und lieferte:
- Executive Summary: 7 Bulletpoints + Live-Test-Ergebnis
- 5 §-Sections die Sub-Reports zusammenfassen (je 300-500 Wörter)
- Synthese-Section mit 3 übergreifenden Trends + Prognose + Empfehlungen
- Meta-Reflexion: "Wir haben die 4-Phasen-Werkstatt-Methodik gelebt während wir sie auditierten"
- Resource-Verzeichnis mit 12+ Pfadangaben

Pfad: `~/.hermes/docus/reports/2026-07-16-master-synthesis.md` (28 KB)

## Cross-References

- `subagent-driven-development` SKILL.md — der Skill der die Subagent-Wellen orchestriert, deren Reports du konsolidierst
- `multi-agent-master-workflow` (orchestration/) — das übergeordnete Workflow-Pattern in dem Report-Synthesis die Abschlussphase ist
- `subagent-driven-development Step 5` (Real-World Cross-Check) — Phase die vor der Synthese läuft: Subagent-Output gegen Realität prüfen
- `subagent-driven-development references/heuristic-subagent-real-world-cross-check.md` — spezifischer Cross-Check für Heuristik-Subagents
