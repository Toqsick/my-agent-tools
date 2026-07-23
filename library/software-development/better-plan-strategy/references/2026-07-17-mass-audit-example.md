# Plan Mass-Audit: 2026-07-17 Beispiel-Evaluation

Diese Datei dokumentiert die quantitative Plan-Qualitäts-Evaluation vom 2026-07-17
als Referenz. Das Skript `scripts/plan-mass-audit.sh` produziert identische
Ausgaben für jeden Zeitpunkt.

## Gemessener Ist-Zustand (Stand 2026-07-17)

```
=== Plan Health Dashboard (Mass-Audit) ===
Directory: ~/.hermes/plans/
Plans found: 23

=== Trend by Date ===
  2026-06-17 | avg=0.5/6 max=1/6 | ██
  2026-06-18 | avg=2.0/6 max=2/6 | ██████
  2026-06-19 | avg=0.0/6 max=0/6 |
  2026-07-06 | avg=0.0/6 max=0/6 |
  2026-07-09 | avg=3.0/6 max=3/6 | █████████
  2026-07-14 | avg=1.0/6 max=1/6 | ███
  2026-07-15 | avg=0.9/6 max=2/6 | ██
  2026-07-16 | avg=0.7/6 max=1/6 | ██
  2026-07-17 | avg=3.3/6 max=6/6 | ██████████████████  ← after skill was loaded

=== Overall Stats ===
  Total plans:     23
  Average score:   1.2/6
  Strong (≥4/6):   2 (8%)
  Weak (0-1/6):    19 (83%)
  Span:            2026-06-17 to 2026-07-17
```

## Zentrale Erkenntnis

**"Skills existieren, werden aber nicht geladen."**

Die `better-plan-strategy` wurde am 2026-07-17 erstellt. Von 21 historischen Plänen
nutzte KEINER die Quality-Gates. Nach Erstellung nutzen beide neuen Pläne (100%)
die Gates, aber NUR weil sie explizit via `skill_view` geladen wurden.

Die Lücke ist nicht "bessere Plan-Qualität", sondern **konsistente Skill-Anwendung**
über die Plan-Pipeline hinweg.

## Die 6 gemessenen Quality-Gates

| Gate | Abdeckung (23 Pläne) | Beschreibung |
|---|---|---|
| S1 Reality-Check | 2/23 (9%) | Pre-Plan Live-Verifikation aller Annahmen |
| S2 SSOT-Table | 2/23 (9%) | Audit-Status-Tabelle geplant vs. tatsächlich |
| S3 Effort Estimate | 11/23 (48%) | Konkrete Minuten-Schätzung pro Task |
| S5 Risk Section | 1/23 (4%) | R1-Rn nummerierte Risiko-Probes |
| S6 Wave Strategy | 3/23 (13%) | Rolling-Waves + Queen-Verify zwischen Wellen |
| S7 Done-Kriterium | 16/23 (70%) | Checkbox-Liste objektiv prüfbarer Ergebnisse |

## Konsequenz für Skill-Architektur

Jeder Skill der Pläne erzeugt (`plan-glm`, `plan`, `workflow-template`) MUSS
`better-plan-strategy` als Prerequisite laden. Ohne diese Verdrahtung bleibt
der Skill ein reines Doku-Artefakt ohne messbare Wirkung auf 83% der Pläne.

## Siehe auch

- `scripts/plan-mass-audit.sh` — automatisierte Ausführung
- `better-plan-strategy` SKILL.md — Strategien + Pitfalls
