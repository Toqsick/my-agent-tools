# Parallel Subagent Summary Staleness

**Entdeckt:** 2026-07-04 (SecurityKernel PR #7)
**Severity:** HIGH — kann zu falschen PR-Bodies, falschen Test-Reportings und Merge-Entscheidungen führen

## Das Problem

Wenn zwei Subagenten **parallel** dispatched werden (via `delegate_task(tasks=[A, B])`) und Task B's Summary von Task A's Output abhängt, ist B's Summary **garantiert stale**.

**Warum:**
- Subagent B wird zum gleichen Zeitpunkt gestartet wie Subagent A
- B bekommt den aktuellen Stand des Repos (ohne A's Änderungen)
- B schreibt sein Summary auf Basis dieses Standes
- A's Fix landet **nach** B's Start — B weiß nichts davon
- Die Queue zeigt beide Summaries als "completed" — kein offensichtlicher Hinweis auf Staleness

## Symptome

- Subagent C (Validator/PR-Writer) meldet "N-1 von N Tests grün" oder "Feature X fehlt noch"
- Nach Überprüfung stellt sich heraus: Subagent A hat genau dieses Problem bereits gefixt
- Die Testanzahl in B's Summary ist **zum Zeitpunkt der Messung korrekt**, aber **zum Zeitpunkt des Lesens falsch**

## Fallbeispiel (SecurityKernel PR #7)

```
Dispatch (parallel):
  ├── Biene A: orchesrator.ts PHASE_ROLE_MAP + Test-Fix
  └── Biene C: PR-Body schreiben (liest Teststatus)

Biene C schreibt: "4/5 orchestrator tests grün"
Biene A fixt:   den 5. Test → 5/5 grün

Richtige Maßnahme: Parent liest Test-Output NEU
```

Biene C war ehrlich — ihr Summary war zum Zeitpunkt der Messung akkurat. Aber parallel dispatchen hieß: sie hat den Stand **vor** A's Fix gesehen.

## Fix (Parent-Seite)

1. **Niemals** die Test-Zahlen aus einem Parallel-Subagent-Summary akzeptieren, wenn ein anderer Subagent am gleichen Code arbeitet
2. **Immer** die relevanten Tests/Dateien selbst nochmal lesen, bevor das Summary weiterverwendet wird
3. **Re-run** der Tests im Parent-Kontext — billig (<5s) und definitiv
4. **Bei Widerspruch zwischen Summary und Realität:** die Realität gewinnt. Das Summary war akkurat zum Dispatch-Zeitpunkt, aber stale

## Prävention

- **Für PR-Bodies/Validator-Subagenten:** dispatch sie NACH dem Implementierer, nicht parallel. Sequential dispatch eliminiert Staleness komplett.
- **Wenn parallel nötig:** der Parent muss nach allen Subagenten eine Verifikations-Phase laufen lassen, die direkte Messungen (Tests, File-Reads) statt fremder Summaries verwendet
- **Edge Case erkennen:** wenn Task B's Goal "verify/test/review Task A's output" ist → NIEMALS parallel dispatchen

## Verwandte Pitfalls

- Pitfall #5 (Phantom-fix): Subagent sagt "fixed" aber nichts geändert — hier sagt Subagent "nicht grün" aber ein anderer hat es gefixt. Umgekehrte Richtung.
- Pitfall #29: File not written — hier wurde das File geschrieben, aber der Inhalt ist stale
- 3-Tier Verification (Datei-Existenz + Content + Realitäts-Check) — Realitäts-Check fängt Staleness
