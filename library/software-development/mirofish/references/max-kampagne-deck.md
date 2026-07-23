# Max-Kampagne Deck — 10 Simulationskarten

> Referenz für das 10-Karten-Deck aus Bastis `mirofish_max_kampagne_komplett.md`.
> Stand: 2026-07-13 (Sim 09 als Proof-of-Concept gefahren)

## One-Pager Template (je Karte)

Jede Simulation braucht einen One-Pager mit diesen Feldern:

| Feld | Beispiel |
|---|---|
| Forschungsfrage | [eine klare Frage, keine Liste] |
| Hypothese | [Primär + Gegenhypothese] |
| Systemkontext | Queen → Worker-Lanes → Gate → Office |
| Variablen | 3 unabhängige, 4 konstante |
| Task-Design | Schwierigkeit, Subtasks, Lanes, Steps |
| Metriken | Quality, Parallelism, Completion, Kosten |
| Failure Modes | Rollendrift, Dubletten, Reviewer-Stau |
| Gate-Kriterien | Mindestwerte + Wer prüft |
| Artefakte | swarmplan.json, shards/*.json, report |

## Die 10 Karten — Übersicht

| # | Karte | Forschungsfrage | Variablen |
|---|---|---|---|
| 01 | Orchestrator vs Mesh | Zentrale vs verteilte Steuerung? | Queen / Peer / Autonom |
| 02 | Agentenzahl-Sweep | Sweet-Spot Nutzen/Kosten? | 1,3,5,8,12,20 Lanes |
| 03 | Rollen-Spezialisierung | Spezialisten vs Generalisten? | 4/8/extended Rollen |
| 04 | Gate-Strenge | Wie streng kalibriert? | niedrig/mittel/hoch, 1/2 Reviewer |
| 05 | Context-Sharding | Wie viel persistenter Kontext? | none / End / pro Lane / verdichtet |
| 06 | Recovery & Resilience | Welche Policy gegen Timeouts? | no / retry / heartbeat+retry |
| 07 | Reviewer-Architektur | 1 oder 2 Reviewer? | 1 / A/B / +Factchecker |
| 08 | Human-in-the-loop | Wann lohnt HITL? | Final / Mid+Final / every lane |
| **09** | **Skill-Chaining** 💚 | **Wiederverwendung alter Findings?** | **Fresh / Template / Derived** |
| 10 | Sim vs Real | Brüche Mock→Real-Runtime? | sim / kanban / backend / hybrid |

## Max-Plan-Rahmen

| Eigenschaft | Wert |
|---|---|
| Plan | Max |
| Credits/Monat | 800 |
| Runs/Monat | 80 |
| Credits/Run | 10 |
| Uploadlimit | 30 MB/Dokument |
| Credits verfallen | Monatsende |

### Kampagnen-Phasen

- **Phase A — Exploration** (48 Runs): Breit streuen, 6-8 Cluster grob abdecken
- **Phase B — Validierung** (20 Runs): Vielversprechende Hypothesen vertiefen
- **Phase C — Finalisierung** (12 Runs): Letzte Kalibrierung + Doku

### Cluster-Struktur (aus der Kampagne)

| Cluster | Runs | Fokus |
|---|---|---|
| 1 — Baselines | 1-8 | Standardfrage mit wechselndem Framing |
| 2 — Extremfälle | 9-16 | Best-/Worst-Case |
| 3 — Parameter-Sweep | 17-24 | Einen Parameter allein variieren |
| … (8 Cluster total, je 8 Runs) | | |

## One-Pager-Vorlage

```markdown
## One-Pager: [Karten-Nummer] [Karten-Name]

### Forschungsfrage
[Eine präzise Frage, z. B. "Lohnt sich Skill-Chaining?"]

### Hypothese
- Primär: [Erwartung]
- Gegen: [Alternative]

### Systemkontext
- Architektur: Queen → Worker-Lanes → Gate → Office
- Recovery: aus / Retries / Heartbeat+Retry
- Rollenmodell: [z. B. searcher, analyzer, writer, reviewer]
- Reviewer: keiner / A / A+B / +Factchecker

### Variablen
- Unabhängig: [3 Stück]
- Konstant: Task, Zeitlimit, Prompt-Set, Gate-Schema

### Task-Design
- Input: [Beschreibung]
- Schwierigkeit: niedrig / mittel / hoch
- Runs: [Anzahl für Power-Analyse]

### Metriken
Q-Score | P-Score | C-Score | Laufzeit | Rework | Reviewer-Korrekturen

### Failure Modes
[Typische Fehler dieser Karte, z. B. "Rollendrift bei Template-Vorgabe"]

### Gate-Kriterien
Min-Q | Min-P | Min-C | Reviewer A+B prüfen

### Artefakte
swarmplan.json | shards/*.json | consolidation.json | gateresult.json | report
```

## Skill-Chaining (Karte 09) — Muster-Ausführung

### Setup

3 Runs mit identischem Seed-Kern, diff = Skill-Datei:

| Run | Skill-Modus | Skill-Typ | Quelle |
|---|---|---|---|
| **R-A** | Fresh | Kein Skill | Zep generiert Personas frei |
| **R-B** | Template | `template-multi-agent-zh.md` | Nur Form + Skelett, LLM füllt |
| **R-C** | Derived | `derived-from-v1-v2-findings.md` | Deterministische Personas + Findings-Struktur |

### Seed-Struktur (für Sim09 optimiert)

```
Section A — Topic Introduction (~2k tokens)
Section B — Personas (10 × ~600 tokens, voll ausformuliert)
Section C — Forschungsfrage (DE + EN)
Section D — 3-Run-Schema mit Skill-Diffs
Section E — Konfliktlinien (3 vorab gesetzt)
Section F — Metriken-Definition (was Personas bewerten)
Section G — Stop-Words / Out-of-Scope
Section H — Closing Brief (was Report liefern soll)
```

### Persona-Set (10, für Skill-Chaining optimiert)

| # | Handle | Rolle | Konflikt mit |
|---|---|---|---|
| 1 | `@basti_synth` | Architekt/Maintainer | `@academic_eth` |
| 2 | `@cost_cfo` | Cost-Optimizer | `@quality_gate` |
| 3 | `@quality_gate` | Reviewer-Strikt | `@cost_cfo` |
| 4 | `@sre_postmortem` | Senior SRE | `@xai_realtime` |
| 5 | `@anthropic_vendor` | Provider (MCP) | `@openai_vendor` |
| 6 | `@openai_vendor` | Provider (FC) | `@mistral_vendor` |
| 7 | `@mistral_vendor` | Open-Weight/EU | `@openai_vendor` |
| 8 | `@gemini_vendor` | Workspace-Provider | `@anthropic_vendor` |
| 9 | `@xai_realtime` | Realtime | `@sre_postmortem` |
| 10 | `@academic_eth` | Academic | `@basti_synth` |

### Ablauf (mit Subagent)

1. **Königin** schreibt ONE-PAGER + definiert Seed-Struktur + Persona-Set
2. **Biene** (subagent/delegate_task) baut:
   - `testdata/simXX-seed.md` — gemeinsamer Seed-Kern
   - `testdata/skills/template-multi-agent-zh.md` — für R-B
   - `testdata/skills/derived-from-v1-v2-findings.md` — für R-C
3. **Königin** sichtet + startet R-A → Report-A → R-B → Report-B → R-C → Report-C
4. **Cross-Run-Synthese**: `SIMXX-SYNTHESE.md` mit Tabellenvergleich

### Erwartete Laufzeit

- 10 Personas × 50 Rounds × Spring = ~50-60 Min pro Run
- 3 Runs + 3 Reports + Synthese = **~4h Gesamt**
- Credits: ~30 (10/Run × 3)