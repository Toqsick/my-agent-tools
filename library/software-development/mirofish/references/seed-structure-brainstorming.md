# Brainstorming Seed Structure (10 Personas)

> Für Basti's Performance + Zuverlässigkeit Fokus. Validierte Struktur aus 2026-07-12 Run.

## Grundstruktur

Ein Brainstorming-Seed unterscheidet sich von einem Whitepaper-Seed:
- **Whitepaper**: Vorhersagen, Framework-Vergleiche, Cost-Modelle
- **Brainstorming**: Lessons Learned, konkrete Crashes, Engineering-Praxis, A2A-Patterns

## Pflicht-Sektionen

### 1. Executive Summary (1-2 Absätze)
Worum geht's, was ist das Ziel, wer sind die Beteiligten.

### 2. Technische Details (tabellarisch, mit Code-Snippets)
Konkrete Metriken, Benchmarks, API-Formate.

### 3. Bewährte Patterns (mit #warum)
Pattern + Beschreibung + Warum es funktioniert.

### 4. Anti-Patterns (mit #warum-schlecht)
Anti-Pattern + Beschreibung + Warum es nicht funktioniert.

### 5. Konkrete Crash-Szenarien
Wie sieht der Crash aus, Anti-Pattern der dazu führt, Bewährter Fix.

### 6. Persona-Profile (10 Stück — Zep-Limit)
Tabelle: Persona, Domäne, Starke Meinung / Erfahrung.

**Verteilungstypisch:**
| Funktion | Personas |
|---|---|
| Architektur (3) | Maintainer, Tooling-Migration, Workspace-Integration |
| Reliability (2) | Senior SRE, Performance-Lawyer |
| Local-AI (2) | Local-LLM-Ops, Open-Weight-Vendor |
| Tooling/Provider (3) | Anthropic, OpenAI, xAI (oder Google/Mistral) |

### 7. Persona-Interaktions-Matrix
Tabelle: Persona, Diskutiert kontrovers mit, Streitpunkt.

Beispiel:
| Persona | Würde diskutieren mit | Streitpunkt |
|---|---|---|
| Basti (Maintainer) | Tooling-Migration-Dev | "Strict Schemas non-negotiable" vs "Legacy bricht sofort" |
| Senior SRE | Performance-Lawyer | "Reliability > Performance" vs "Latency budget matters" |

### 8. Performance-Tradeoff-Topology
Tabelle: Metrik, Primary Owner, Secondary Owner, Trade-Off.

Beispiel:
| Metrik | Primary | Secondary | Trade-Off |
|---|---|---|---|
| P50 Latenz | xAI (Realtime) | OpenAI | Throughput vs Accuracy |
| P95 Latency | Performance-Lawyer | Anthropic | SLO vs Cost |

### 9. Diskussions-Stil-Vorgabe (optional)
- Sprache: Deutsch + Englisch gemischt
- Code-Snippets: erwünscht
- Quantitative Argumente > rhetorische
- "Aus Erfahrung" als Brücke

### 10. Plattform-Setup
- Twitter only (schneller, fokussierter)
- 60 Rounds
- chunk_size=400, overlap=60