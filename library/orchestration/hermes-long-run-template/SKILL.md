---

name: hermes-long-run-template
description: |
  Use when you run a long-running Hermes Agent task (10–30 minutes), need a 7-phase template (kickoff → reconnaissance → planning → execution → verification → synthesis → handoff), and want a structured way to keep momentum and recovery checkpoints.
  NOT for short interactive turns (<5 min), single-tool tasks, or non-Hermes agents without phase-based scheduling.
  Long-run agent template: 7-phase pipeline with checkpoints, recovery hooks, momentum logging, sub-agent delegations, and a clean handoff artifact at the end.
version: 1.0.0
author: Yuno for Basti (Long-Run-Pattern aus Context-Engineering-Literatur + Hermes-v7
  Worker-Lanes + GLM-5.2-Template)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - long-run
    - agentic-run
    - multi-phase
    - worker-lanes
    - research
    - audit
    - release
    - queen-bee
    - gate-review
    - hard-stop
    related_skills:
    - hermes-react-pattern
    - hermes-context-budget
    - hermes-agentic-patterns
    - multi-agent-master-workflow
    - workflow-template
    - critic-gate
    - context-mode
    lane: koenigin
    reasoning_effort: high
    artifact_scope: run-scoped
trigger_keywords: ['agent', 'phase', 'long', 'hermes', 'template']
keywords: ['agent', 'phase', 'long', 'hermes', 'template']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['agent-config-refactoring']
---


# Hermes Long-Run Template

Für Tasks, die nicht in einem einzigen Prompt lösbar sind, sondern **mehrere Phasen, mehrere Worker-Lanes und explizites Gate** brauchen. Laufzeit-Ziel: **10–30 Minuten** stabil, artefakt-orientiert, nachvollziehbar.

Anders als `hermes-react-pattern` (das den Micro-Loop etikettiert) definiert dieser Skill den **Macro-Lifecycle** eines Long-Run-Tasks. Anders als `workflow-template` (das die Plan-Struktur liefert) liefert dieser Skill die **Ausführungs-Disziplin** mit harten Stop-Bedingungen.

## Trigger

Dieser Skill feuert, wenn **eines** der folgenden Signale vorliegt:

- Task wird explizit als "long" / "lange" / "10–30 Minuten" / "deep research" bezeichnet
- **>5 erwartete Tool-Calls** ODER **>3 logische Phasen** (z.B. Recherche → Build → Audit)
- Mehrere Quellenklassen involviert (GitHub + Drive + Akademisch, oder Code + Doku + Security)
- **Multi-Domain-Output** erwartet (mehrere Deliverables, mehrere Skills nötig)
- User sagt: "gründlich", "vollständig", "von A bis Z", "komplett durchziehen"
- Externer Provider (GLM-5.2, Perplexity, OpenRouter) wird für eine lange Aufgabe gebunden

## Wann NICHT

- Single-Step-Tasks (`echo`, `cat`, einfache `read_file`) → Overkill, bremst aus
- Time-Pressure / "schnell mal" → direkt ReAct, kein Macro-Overhead
- Bereits durch `workflow-template` abgedeckt UND unter 3 Phasen → kein zweiter Layer
- Rein konversationelle Tasks ohne Tool-Einsatz

## Die 7 Phasen

Jeder Long-Run folgt dieser Struktur. **Keine Phase überspringen**, **keine Reihenfolge umdrehen**, **kein Artefakt still überschreiben**.

```
┌─ Phase A: Scope & Erfolgskriterien        → task_card.md
├─ Phase B: Inventur & Kontextaufbau        → inventory.md
├─ Phase C: Arbeitsplan                     → plan.md
├─ Phase D: Worker-Lanes (parallel)         → lane_<N>_<topic>.md
├─ Phase E: Konsolidierung                  → consolidation.md
├─ Phase F: Gate (Reviewer A + B)           → gate_review.md
└─ Phase G: Abschluss-Artefakt              → [SPEC|AUDIT|RELEASE|DECISION].md
```

### Phase A — Scope & Erfolgskriterien

**Ziel**: Vor dem ersten Tool-Call exakt wissen, was rauskommen soll.

Erzeuge **vor** allem anderen:

```markdown
## Zieldefinition
[1–2 Sätze: was ist das fertige Ergebnis?]

## Nicht-Ziele
- [Was NICHT gemacht wird — Scope-Creep-Schutz]

## Done-Kriterien
- [ ] [Konkretes, prüfbares Kriterium 1]
- [ ] [Kriterium 2]

## Abbruchkriterien
- [Wann wird der Lauf abgebrochen statt schlecht abgeschlossen]

## Risikoannahmen
- [Was könnte schiefgehen, was ist akzeptiert]
```

**Output**: `task_card.md` im Run-Artefakt-Verzeichnis.

### Phase B — Inventur & Kontextaufbau

**Ziel**: Wissen, was vorhanden ist, bevor du anfängst zu suchen.

Sammle **nur**:
- Relevante Dateien / Ordner / Repos / Dokumente
- Abhängigkeiten und Schnittstellen
- Bekannte Constraints (Linux-only, keine Cloud, etc.)
- Offene Unklarheiten → explizit listen, nicht verschweigen

**Ergebnis-Format** (`inventory.md`):
```markdown
## Quellenlage
- GitHub: [Repos/Dateien mit Pfad]
- Drive: [Dokumente mit Link]
- Akademisch: [Papers/Methoden]
- Lokal: [Pfade]

## Constraints
- [Constraint-Liste]

## Offene Unklarheiten
- [Lücke 1: was fehlt, wer könnte klären]
```

**Just-in-Time-Retrieval**: Während Phase B noch keine Inhalte laden — nur referenzieren. Volle Inhalte erst in Worker-Lanes.

### Phase C — Arbeitsplan

**Ziel**: Ein **planbarer Graph**, kein Roman. Wer arbeitet woran in welcher Reihenfolge?

```markdown
## Phasen & Reihenfolge
1. [Phase X] → abhängig von [Voraussetzung]
2. [Phase Y] → parallel zu X möglich? ja/nein

## Worker-Lanes (parallele Stränge)
- Lane 1: [Thema] → Artefakt: [Datei]
- Lane 2: [Thema] → Artefakt: [Datei]
- Lane 3: [Thema] → Artefakt: [Datei]

## Gate-Punkte
- Nach [Phase X]: Reviewer A (technische Korrektheit)
- Vor Abschluss: Reviewer B (Vollständigkeit)

## Risiken im Plan
- [Lane-Abhängigkeit die scheitern könnte]
```

**Lane-Auswahl-Heuristik**: Wenn der Task mehrere Quellenklassen oder Domänen kombiniert, eine **Lane pro Klasse**. Faustregel:

| Quellenklasse | Default-Lane |
|---|---|
| GitHub / Code / Repo | Lane 1 |
| Drive / Doku / Betrieb | Lane 2 |
| Akademisch / Methode / Theorie | Lane 3 |
| Security / Risk / Failure Modes | Lane 4 |

Bei Tasks mit nur 1-2 Klassen: Lanes weglassen, stattdessen Phasen-linear arbeiten.

### Phase D — Worker-Lanes

**Ziel**: Parallele oder sequenzielle Vertiefung pro Lane. Jede Lane erzeugt **ein eigenes Artefakt**.

Pro Lane:

```markdown
## Lane [N]: [Thema]

### Ziel
[1 Satz]

### Inputs
- [Pfad/Link/Referenz]

### Methode
- [Wie wird gearbeitet — ReAct-Labels empfohlen]

### Artefakt
[lane_<N>_<topic>.md]

### Offene Unsicherheiten
- [Was konnte nicht geklärt werden]
```

**Hermes-Integration**: Lanes können via `delegate_task` als Subagenten dispatched werden (siehe `multi-agent-master-workflow`). Subagent-Briefing muss enthalten:
- Lane-Ziel + Inputs + Artefakt-Pfad
- ReAct-Pattern-Anweisung (siehe `hermes-react-pattern`)
- Hard-Stop-Regel: wenn Lane scheitert → DELTA notieren, nicht Lane-Output überspringen

**Append-only**: Lane-Artefakte werden **nie überschrieben**. Bei Bedarf `lane_<N>_<topic>_v2.md` mit Delta-Vermerk.

### Phase E — Konsolidierung

**Ziel**: Lane-Outputs zusammenführen **ohne Verwässerung**.

Trenne strikt:

```markdown
## Gesicherte Befunde
- [Fakt mit Quellenangabe]

## Widersprüche
- [Lane A sagt X, Lane B sagt Y — mögliche Erklärung]

## Ungelöste Fragen
- [Was offen bleibt]

## Umsetzbare Konsequenzen
- [Konkrete Aktion oder Entscheidung]
```

**Anti-Pattern**: Lane-Outputs nicht in Prosa "verschmelzen". Stattdessen **Quellen-Tagging** beibehalten, damit Reviewer später prüfen können.

### Phase F — Gate (Reviewer A + B)

**Ziel**: Bevor etwas "fertig" genannt wird, **müssen zwei simulierte Reviewer bestehen**.

**Reviewer A — Technische Korrektheit**:
- [ ] Logikfehler im Output?
- [ ] Technische Widersprüche zwischen Lanes?
- [ ] Fehlende Belege für Behauptungen?
- [ ] Riskante Annahmen ohne Quellen?
- [ ] Ungesicherte Ableitungen markiert?

**Reviewer B — Vollständigkeit**:
- [ ] Scope vollständig abgedeckt?
- [ ] Alle wichtigen Quellenklassen berücksichtigt?
- [ ] Deliverables vollständig?
- [ ] Randfälle erwähnt?
- [ ] Offene Punkte transparent gemacht?

**Gate-Output** (`gate_review.md`):
```markdown
## Reviewer A — Technische Korrektheit
- [✅|⚠|❌] [Befund]
- [Status]: PASS | FAIL | BLOCKED

## Reviewer B — Vollständigkeit
- [✅|⚠|❌] [Befund]
- [Status]: PASS | FAIL | BLOCKED

## Entscheidung
- [ ] PASS — Abschluss freigegeben
- [ ] FAIL — Delta-Plan erforderlich, kein Abschluss
- [ ] BLOCKED — externe Klärung nötig, Run pausiert
```

**Bei FAIL oder BLOCKED**: Zurück zu Phase D (Lane nachschärfen) oder Phase C (Plan anpassen). **Nie direkt zu Phase G springen.**

### Phase G — Abschluss-Artefakt

**Ziel**: Belastbares Ergebnisobjekt statt loses Fazit. Je nach Task-Typ:

| Task-Typ | Abschluss-Artefakt |
|---|---|
| Forschung / Recherche | `RESEARCH_REPORT.md` |
| Audit / Security | `AUDIT.md` |
| Architektur / Design | `SPEC.md` |
| Coding / Implementierung | `IMPLEMENTATION_PLAN.md` |
| Release / Rollout | `RELEASE_REVIEW.md` |
| Entscheidungsgrundlage | `DECISION.md` |
| Doku-Generierung | `DOCUMENTATION.md` |

**Pflicht-Inhalt** jedes Abschluss-Artefakts:
1. Executive Summary (max. 200 Wörter)
2. Hauptsektionen mit klaren H2-Überschriften
3. Quellenverzeichnis mit Links/Pfaden
4. Verweis auf `gate_review.md` (PASS-Status)
5. Bekannte Limitierungen / offene Punkte

## Header-Schema für Task-Cards

Jeder Long-Run bekommt einen strukturierten Header zur Nachvollziehbarkeit:

```json
{
  "sessionId": "hermes-longrun-001",
  "taskCardId": "TC-2026-07-08-001",
  "workflowType": "research",
  "requiredReviewers": ["reviewerA", "reviewerB"],
  "artifactScope": "run-scoped",
  "providerPreference": "hermes-native",
  "executionMode": "long-agentic-run",
  "riskLevel": "high",
  "fallbackPolicy": "delta-not-silence",
  "laneBudget": 4,
  "promotionRule": "only-after-gate-pass"
}
```

Felder erklärt:

| Feld | Werte | Bedeutung |
|---|---|---|
| `workflowType` | research, audit, release, coding, architecture, debugging, documentation | Bestimmt Phasen-Template und Default-Lanes |
| `riskLevel` | critical, high, medium, low | Bestimmt Reflexions-Häufigkeit und Gate-Strenge |
| `artifactScope` | run-scoped, session-scoped, permanent | Run-Artefakte vs persistente Doku |
| `providerPreference` | hermes-native, glm-5.2, perplexity, openrouter | Welcher Provider den Hauptlauf macht |
| `laneBudget` | 1–4 | Max Anzahl paralleler Worker-Lanes |
| `fallbackPolicy` | delta-not-silence, block-on-fail, best-effort | Wie mit Teil-Fehlern umgegangen wird |
| `promotionRule` | only-after-gate-pass, best-effort | Gate als harter Pflicht-Step? |

## Statusbilder zwischen Phasen

Nach jeder Hauptphase kurzes Statusbild (Queen-Bee-Check-in):

```markdown
## Status nach Phase [X]
- Fortschritt: [%] [Was fertig ist]
- Aktuelle Lane: [Welche aktiv]
- Offene Punkte: [Risiken, Blocker]
- Nächste Phase: [Was kommt als nächstes]
- Compaction-Status: [% Context-Auslastung]
```

Bei **>85% Context-Auslastung**: Phase vorzeitig beenden, Compaction triggern (siehe `hermes-context-budget`), dann Resume.

## Pitfalls

1. **Phase B überladen**: "Inventur" ist kein Daten-Pre-Loading. Nur referenzieren, Inhalte kommen in den Lanes. Bei Verstoß → Context-Budget-Konflikt.
2. **Phase D ohne Lane-Budget**: Zu viele parallele Lanes → schwerer zu konsolidieren. Faustregel: max `laneBudget` aus Header, nicht mehr.
3. **Phase F als Formsache**: Gate ist kein Häkchen-Setzen. Reviewer A/B müssen **echte Befunde** finden können, sonst war die Konsolidierung zu oberflächlich.
4. **Phase G ohne Gate-Verweis**: Abschluss-Artefakte MÜSSEN auf `gate_review.md` referenzieren. Ohne Verweis → Status unklar.
5. **Append-only verletzt**: Lane-Artefakte still überschrieben → Nachvollziehbarkeit zerstört. Versionierung mit Suffix `_v2`.
6. **BLOCKED vertuscht**: Wenn Gate FAIL oder BLOCKED sagt, ist der Lauf nicht fertig. Nicht in Phase G springen mit "wir liefern halt was wir haben" — lieber Delta-Plan + Pause.
7. **Lane-Mixing**: Lane-Outputs ohne Quellen-Tagging in Konsolidierung mischen → Reviewer können nicht mehr prüfen.

## Integration mit anderen Hermes-Skills

| Hermes-Skill | Rolle in diesem Template |
|---|---|
| `hermes-react-pattern` | Micro-Loop innerhalb jeder Lane (Thought→Action→Obs) |
| `hermes-context-budget` | 85%-Compaction-Trigger zwischen Phasen |
| `hermes-agentic-patterns` | Outcome-Prompt-Formulierung in Phase A; NOTES.md-Pattern für Cross-Session-Übergabe |
| `multi-agent-master-workflow` | Lanes als `delegate_task`-Subagenten dispatchen |
| `workflow-template` | Vorlage für `plan.md` in Phase C |
| `critic-gate` | Reviewer A/B-Logik in Phase F (kann Verifier-Subagent rufen) |
| `context-mode` | JIT-Retrieval-Heuristiken für Phase B/D |

## Externer Provider-Modus (GLM-5.2 / Perplexity)

Wenn der Long-Run **nicht** in Hermes selbst, sondern in einem externen Provider läuft, gelten diese Anpassungen:

1. **Header-Schema statt freier Text**: Der externe Provider bekommt das JSON-Header-Schema als ersten Input — nicht den freien Phasen-Fließtext.
2. **Reviewer A/B explizit simulieren**: Externe Provider haben keine native Gate-Logik → "Simuliere Reviewer A" als explizite Anweisung.
3. **Append-only via Session-ID**: Phase-Artefakte heißen `[TYP]_[session-id]_[phase].md` (z.B. `PLAN_hermes-longrun-001_C.md`), damit sie nach Rückimport in Hermes referenzierbar sind.
4. **No silent fallback**: `fallbackPolicy: "delta-not-silence"` ist Pflicht für externe Provider — sie neigen eher zu "klingt plausibel"-Outputs.
5. **Import nach Hermes**: Nach externem Lauf zurück in Hermes → Artefakte in Hermes-v7 Run-Verzeichnis ablegen + Mnemosyne-Summary schreiben.

### Minimaler Starter-Prompt für externen Provider

```text
Nutze das Hermes Long-Run Pattern für [PROVIDER].

Session-ID: [SESSION_ID]
Task: [DEINE GROSSE AUFGABE]
Zielartefakt: [SPEC.md | AUDIT.md | RESEARCH_REPORT.md | DECISION.md]
Priorität: [critical|high|medium|low]
Quellenklassen: GitHub, Google Drive, akademisch
Constraints:
- Arbeite 10–30 Minuten stabil und mehrphasig
- 7 Phasen: Scope → Inventur → Plan → Lanes → Konsolidierung → Gate → Abschluss
- Erzeuge Zwischenartefakte: task_card.md, inventory.md, plan.md, lane_<N>.md, consolidation.md, gate_review.md
- Simuliere Reviewer A (technische Korrektheit) und Reviewer B (Vollständigkeit)
- BLOCKED statt Schönreden
- Keine Abschlussbehauptung ohne Gate-PASS
```

## Beispiel-Mini-Lauf

**Task**: "Analysiere greyhack-tools Repo auf Sicherheits-Risiken im PR-Workflow"

```json
{
  "sessionId": "greyhack-security-001",
  "taskCardId": "TC-2026-07-08-002",
  "workflowType": "audit",
  "requiredReviewers": ["reviewerA", "reviewerB"],
  "artifactScope": "run-scoped",
  "providerPreference": "hermes-native",
  "executionMode": "long-agentic-run",
  "riskLevel": "high",
  "fallbackPolicy": "delta-not-silence",
  "laneBudget": 3,
  "promotionRule": "only-after-gate-pass"
}
```

**Phasen-Durchlauf**:
- **A**: Scope = "Security-Audit PR-Workflow greyhack-tools", Done = "Liste aller Risiken + Fix-Empfehlungen", Abbruch = "wenn Repo-Zugriff scheitert"
- **B**: Inventur = `[repo: greyhack-tools, files: ci-build.sh, pytest.ini, github-workflow files]`
- **C**: Plan = 3 Lanes: (1) Secret-Handling in CI, (2) Dependency-Risks, (3) PR-Approval-Policy
- **D**: 3× `delegate_task` an Subagenten mit `hermes-react-pattern` Briefing
- **E**: Konsolidierung trennt "bestätigt durch GH-Settings" vs. "plausibel aber nicht verifizierbar"
- **F**: Reviewer A findet 2 Logikfehler in Lane 2 → DELTA, Lane nachgeschärft
- **G**: `AUDIT.md` mit Executive Summary + Findings + Fix-Empfehlungen + Verweis auf `gate_review.md` (PASS)

## Verwandte Skills

- `hermes-react-pattern` — Micro-Loop (ReAct) innerhalb jeder Lane
- `hermes-context-budget` — 85%-Compaction-Trigger zwischen Phasen
- `hermes-agentic-patterns` — Outcome-Prompts, NOTES.md-Pattern, Spec→Fresh-Session
- `multi-agent-master-workflow` — Lanes als Subagenten dispatchen
- `workflow-template` — Plan-Struktur für Phase C
- `critic-gate` — Reviewer-Logik für Phase F
- `context-mode` — JIT-Retrieval-Heuristiken

## Provenance & Methodology

Dieser Skill wurde durch die **Document-to-Skill-Pipeline** aus einem 14K-Token-Referenzdokument über LLM Long-Running-Prompts abgeleitet. Die vollständige Evaluierungs-Methodik, das Mapping von Dokument-Sektionen zu Hermes-Skills und die Gap-Analyse sind in `references/document-to-skill-pipeline.md` dokumentiert.

**Pipeline-Übersicht**: Externes Dokument lesen → Sektionen klassifizieren (EXISTING_SKILL / EXTEND / NEW_SKILL / NOISE) → Gap-Analyse → Skill bauen → Cross-Referenzen + Navigator updaten → Mnemosyne-Memory. Siehe Reference-File für Details inkl. Beispiel-Mapping-Tabelle und Anti-Patterns.