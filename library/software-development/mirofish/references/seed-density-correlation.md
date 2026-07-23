# Seed Density ↔ Persona Count / Simulation Output Correlation

> Empirische Daten aus zwei MiroFish-Runs auf demselben Whitepaper mit verschiedenen Seed-Dichten.
> Stand: 2026-07-12

## Kern-Beobachtung

**Mehr Seed = nicht mehr Output, sondern ANDERER Output.**

Eine dichtere Seed-Quelle (+66% Tokens) produzierte **57% weniger Simulation-Actions** (93 vs 154), **57% weniger Personas** (3 vs 7), aber **75% mehr Graph-Chunks** (56 vs 32). Die Output-Qualität verschob sich von narrativem Dialog zu technischen Code-Snippets und konkreten Konfigurationen.

## V1 vs V2 vs V3 Vergleich

| Dimension | V1 („Standard") | V2 („Dense") | V3 („Oversized") |
|---|---|---|---|
| **Seed-Größe** | 1030 Wörter / 7k Tokens | 1706 Wörter / 14.7k Tokens | **~24k chars / one-shot Brainstorming** |
| **Seed-Themen** | Breit: Layering, Cost, Security, Eval | Fokussiert: Pydantic, C0-C4, Trust-Boundaries | **Performance + Zuverlässigkeit, 10 Personas, Code-Snippets** |
| **Chunk-Count** | 32 | 56 | 56 (ähnlich V2) |
| **Node/Edge Count** | 50/50 | 50/50 | geschätzt 50/50 |
| **Personas erwartet** | 7 | 3 | **10 → nur 4 generiert** |
| **Sim-Actions** | 154 (76T+78R) | 93 (43T+50R) | **~19+ nach 10 Runden (Twitter only)** |
| **Rounds** | 60 | 60 | 60 |
| **Laufzeit** | ~50 Min | ~7 Min | **~15+ Min (erste Runde >2 Min LLM)** |
| **Output-Charakter** | Narrativer Dialog, Persona-Interaktion | Technische Code-Snippets, Config-Referenzen | Technisch + tief (wenn es läuft) |
| **run_state.json** | ✅ live aktualisiert | ✅ live aktualisiert | **❌ STUCK bei Round 0 (trotz produktivem OASIS)** |

## V3 Spezifische Erkenntnisse

Der V3-Run mit einem ~24k-Char-Seed (Brainstorming-Session, 10 Personas requested, Twitter-only) zeigte:

1. **Persona-Kollaps**: 10 angefragte Personas produzierten nur 3-4 echte Profiles + 1 Fallback. Der Ontology-Generator hatte nur 3 Entity-Types zur Verfügung, die Config deckte die restlichen Personas über Replik-Logik ab, nicht als eigenständige Akteure.

2. **run_state.json lag**: Das OASIS-Inferencing brauchte >2 Min für die erste LLM-Runde. `run_state.json` blieb auf `current_round: 0, total_actions: 0` obwohl der Worker in `simulation.log` bereits Round 10/60 mit 19+ Posts zeigte. Der `updated_at`-Timestamp änderte sich bis zum ersten Write nach Round 1 nicht.

3. **simulation.log als Wahrheitsquelle**: Bei großen Seeds ist `simulation.log` der EINZIGE verlässliche Live-Indikator. Der Watcher (der nur `run_state.json` pollt) sieht fälschlich einen „stuck"-Zustand.

4. **Stichproben-Validierung**: Die `twitter_simulation.db` (SQLite) kann direkt nach Posts abgefragt werden — zeigte 19 Posts bei 588 KB DB-Größe, obwohl `run_state.json` noch Round 0 anzeigte.

5. **Fazit**: Seeds über 12k Chars sind für >3 aktive Personas kontraproduktiv. Der LLM-Overhead frisst Zeit, die Profile-Zahl sinkt, und das Monitoring wird unzuverlässig.

## Warum?

Der MiroFish-Ontology-Generator (LLM) extrahiert **Personas basierend auf den im Seed prominentesten Rollen**. Ein breiter, narrativer Seed (V1) → viele verschiedene Rollen werden sichtbar → 7 Personas generiert. Ein dichter, technischer Seed (V2) → wenige, aber spezifische Rollen → 3 tiefe, fokussierte Personas.

Die LLM-Entscheidungslogik scheint zu sein:

1. Seed einlesen und thematische Cluster erkennen
2. Pro Cluster: prüfe ob eine distinkte Persona-Rolle existiert  
3. Zu viele überlappende Cluster → verschmelzen zu weniger, stärkeren Personas
4. Einzige Ausnahme: klare organisatorische/geografische Trennung zwingt Splits

## Praktische Implikationen

### Für schnelle Simulationen (< 15 Min)
- **Dichter, fokussierter Seed** (1000-1500 Wörter, konkretes Thema)
- Erwarte: 2-4 Personas, 70-100 Actions, 5-10 Min Laufzeit
- Gut für: schnelle Hypothesen-Tests, technische Tiefenbohrungen

### Für breite Simulationen (> 30 Min)
- **Breiter, narrativer Seed** (600-1000 Wörter, mehrere Themen)
- Erwarte: 5-7 Personas, 120-200 Actions, 30-60 Min Laufzeit
- Gut für: Ökosystem-Analyse, Persona-Konflikt-Matrizen

### Chunk-Größe vs Seed-Größe
- Seed-Tokens bestimmen die **Chunk-Anzahl** (≈ 40 Toks/Chunk bei chunk_size=400)
- Chunk-Anzahl bestimmt die **Graph-Dichte** (Nodes/Edges), aber maximal 50/50 wg. Zep API
- Ab ~60+ Chunks wird der Graph „satt" — mehr Chunks ändern nichts mehr an der Simulation
- Chunk-Overlap hat wenig Einfluss auf Simulation-Qualität (aber verbessert Reasoning-Qualität im GraphRAG)

## Empfehlung

1. **Erst einen breiten Seed (V1-Stil) fahren** — liefert Persona-Landschaft und Konflikt-Matrix
2. **Dann einen fokussierten Seed (V2-Stil) fahren** — liefert technische Tiefe und Code-Beispiele
3. Beide Outputs zusammen ergeben das vollständige Bild

Die Metapher: **V1 zeichnet die Landkarte, V2 gräbt die Schächte.**
