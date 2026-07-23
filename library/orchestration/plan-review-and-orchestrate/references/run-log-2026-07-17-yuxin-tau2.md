# Inline-Execution Run-Log — Yuxin-Tau2 Benchmark (2026-07-17)

**Model:** yuxin-tau2 (gemma4 11.9B Q4_K_M)
**Suite cloned from:** qwythos-9b (qwen35 9.2B Q6_K) — different architecture
**Total time:** ~75 Min (Plan-Review + Subagent-Dispatch + Inline + Background-Run + Doku)
**Mode:** Hybrid — Phase A inline (Plan-Review), Phase B 1 subagent + inline, Background-Run
**Subagents:** 1 (Task 1.1 — project clone) + 0 crashes

## Structure

This run followed the **Inline Execution** pattern from `plan-review-and-orchestrate`:
Phase A (Plan-Review) before any code, followed by inline patches for
Phase 2-4 instead of subagent dispatch.

## Phase Breakdown

| Phase | Duration | Mode | Tasks | Key Learning |
|---|---|---|---|---|
| A: Plan-Review | 15 Min | Inline | 5-Schwächen-Matrix | Queen-Discovery (Gemma4 tool_calls Format) vor dem Klonen identifiziert |
| 1: Projekt-Skeleton | 8 Min | **Subagent** | Klonen + Tests | **Pitfall: Stale Subagent Tests** — der Subagent hat Tests von qwythos nicht aktualisiert (suchten noch `qwythos-9b-q6`). Queen-Verify nötig. |
| 2: Runner-Konfig | 5 Min | Inline | sed + Patches | Keine Absprung nötig — 4 sed-Befehle für 6 Runner-Files |
| 3: Aggregator + Templates | 3 Min | Inline | Titel + Pre-Flight | Dashboard-Titel patchen (qwythos → yuxin-tau2) |
| 4: Background-Run | 25 Min | Background | Full Suite (Quality skip needle) | Alle Runner beim ersten Versuch erfolgreich |
| 5: Doku + Wiki | 10 Min | Inline | 4 Files + Cross-Comparison | Mnemosyne + Obsidian + docus/reports |

## Why Inline Beat Subagent for Phases 2-4

1. **Lineare Abhängigkeiten:** Jede Phase (Runner → Aggregator → Run) baut auf der vorherigen auf. Subagent-Parallelisierung bringt nichts.
2. **Sed-Präzision:** 4 sed-Befehle sind schneller geschrieben als ein Subagent-Brief mit Ausführungsanweisungen.
3. **Fail-fast mit sed:** Ein Tippfehler (z.B. `10-projekte` statt `10-Projekte`) wird sofort sichtbar und in <20s korrigiert — kein Subagent-Handshake nötig.

## Queen-Discoveries (vor Phase 1 identifiziert)

Die Pre-Smoke-Test **vor** dem Klonen hat 3 Gemma4-spezifische Unterschiede identifiziert:

1. **Thinking-Format:** Plain-text (keine XML-Tags wie qwythos' `<|im_start|>`)
2. **Tool-Call-Streaming:** Tool-Calls im vorletzten Chunk (qwythos: letzter Chunk)
3. **Empty Content:** `content: ""` bei Tool-Only-Responses (qwythos: immer Text)

→ **Der Repository Patcher** (OllamaClient im Source-Modul) wurde **vor** dem Klonen gepatched, sodass der Subagent direkt funktionierenden Code erhielt.

## Pitfall #36a Subagent: Stale Tests gefunden

**Symptom:** Subagent erstellte Tests, die `qwythos-9b-q6` im Model-Namen referenzierten.

**Ursache:** Der klonende Subagent hatte keinen Kontext, dass Tests modellspezifische Namen enthalten.

**Fix:** Queen-Verify nach Phase 1 → manuell die 4 Test-Dateien gepatched (`qwythos-9b-q6` → `yuxin-tau2:latest`).

**Lesson:** Tests müssen nach einem Clone **immer** Queen-verifiziert werden, nicht nur der Source-Code.

## Subagent-Crash vs Inline-Dispatch Statistik

| Phase | Versuche | Crashes | Recovery | Erfolg |
|---|---|---|---|---|
| 1.1 Klonen (Subagent) | 1 | 0 | — | ✅ (mit Queen-Fix) |
| 2-4 (Inline) | 4 sed + 4 patch + 2 write_file | 0 | — | ✅ |
| 4 Background | 1 | 0 | — | ✅ |

**Crash Rate: 0%** (1 Subagent, 0 Crashes). Die Queen-Verify nach dem Subagent war trotzdem nötig.

## Gegenüberstellung: qwythos (Inline) vs yuxin-tau2 (Hybrid)

| Aspekt | qwythos Run (2026-07-17) | yuxin-tau2 Run (2026-07-17) |
|---|---|---|
| Ausgangsbasis | Neues Template | Clone von qwythos-Suite |
| Architektur | qwen35 (bekannt) | gemma4 (unbekannt) |
| Pre-Smoke-Ergebnis | Wenige Überraschungen | **3 kritische Architektur-Unterschiede** |
| Phase 1 Modus | Inline (scaffolding) | Subagent (clone) |
| Runner-Bugs | 3 Iterationen nötig | 0 (Bug-frei) |
| Total Time | ~110 Min (3 Runs) | ~75 Min (1 Run) |
| Doku-Umfang | 1 Wiki + 1 Inbox | **4 Files** (Wiki + Cross-Comp + Report + Inbox) |

## Meta-Lesson

Der **Hybrid-Ansatz** (Plan-Review + 1 Subagent + Inline) hat sich für Multi-Modell-Benchmarks bewährt:
- Plan-Review identifiziert Architektur-Unterschiede VOR dem Code
- Subagent für isolierte, zeitaufwändige Tasks (Klonen)
- Inline für lineare Abhängigkeiten (Patches, Runs, Doku)
- Queen-Verify nach jedem Subagent (auch wenn er grün meldet) als Sicherheitsnetz

## Verwandte Artefakte

- Plan: `~/.hermes/plans/2026-07-17_153515-yuxin-tau2-benchmark.md`
- Report: `~/.hermes/docus/reports/2026-07-17-yuxin-tau2-benchmark.md`
- Cross-Comparison: `~/Dokumente/Obsidian Vault/09 System-Doku/KI-Architektur/qwythos-vs-yuxin-2026-07-17.md`
- Mnemosyne: `dbdf7b80f9135450` (Multi-Modell-Benchmark-Pattern)