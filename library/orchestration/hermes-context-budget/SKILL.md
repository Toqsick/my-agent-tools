---
name: hermes-context-budget
description: Use when proactively managing context window with 85 percent compaction triggers. Includes M3 interleaved-thinking trace hygiene (ultra=49152 tok/round, H-10-persistent) vs GLM-5.2.
version: 1.1.0
author: Yuno for Basti (evaluiert aus Context-Engineering-Literatur)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - context-management
    - compaction
    - token-budget
    - jit-retrieval
    - context-health
    related_skills:
    - hermes-react-pattern
    - context-mode
    - multi-agent-master-workflow
    - hermes-agentic-patterns
    lane: koenigin
    reasoning_effort: high
trigger_keywords: ['proactively', 'managing', 'context', 'window', 'percent']
keywords: ['proactively', 'managing', 'context', 'window', 'percent']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['context-mode', 'context-diet']
---


# Hermes Context Budget

Context-Window-Überlastung ist die #1-Ursache für Agent-Versagen bei langen Tasks. Nicht das Modell scheitert — der Kontext scheitert (Context Rot). Dieser Skill definiert **proaktive** Strategien, bevor es kritisch wird.

## Trigger

- "context budget" / "context full" / "token limit"
- "compaction" / "komprimieren" / "aufräumen"
- Task mit **>10 erwarteten Tool-Calls** (im Plan erkennen)
- "KV cache" / "attention budget"
- "context health" / "context metrics"

## Die 85%-Regel

**Compaktion proaktiv bei 85% statt 98% Context-Auslastung.**
Wenn das Window erst bei 98% kompaktiert wird, passt die Zusammenfassung selbst nicht mehr rein.

### Faustformel für Token-Verbrauch

| Aktion | Ungefähre Token | Strategie |
|---|---|---|
| 1 Tool-Call + Ergebnis | 500–2000 | Kein Eingriff |
| **1 M3-Reasoning-Runde @ ultra** | **bis 49152** | ⚠️ **Dominiert das Budget — siehe unten** |
| 5 Tool-Calls | 5k–15k | Nach 5 Calls: Check ob <85% |
| 10 Tool-Calls | 15k–40k | ⚠️ **85%-Check fällig** |
| 20+ Tool-Calls | 40k–100k+ | 🛑 **Compaction erzwingen** |

**Achtung — die Tabelle unterschätzt M3 massiv:** die Zeilen unten zählen Tool-Ergebnisse, aber auf dem Session-Default **MiniMax-M3** kommt bei `reasoning_effort: ultra` ein **Thinking-Trace von bis zu 49152 Token *pro Runde*** obendrauf (`THINKING_BUDGET["ultra"]`), und der wird per H-10 (`_manage_thinking_signatures`) **über Tool-Runden erhalten** statt verworfen. Eine einzige M3-Denkrunde wiegt damit bis zu ~25 durchschnittliche Tool-Calls. Der 85%-Punkt kommt auf M3 also **deutlich früher** als die reine Tool-Call-Zählung suggeriert.

## M3-Thinking-Traces vs GLM-5.2 — Reasoning im Budget

Der größte modell-spezifische Kontext-Kostenfaktor sind **erhaltene Reasoning-Traces**, und M3 und GLM-5.2 verhalten sich hier gegensätzlich:

| | **MiniMax-M3** (Session-Default, `anthropic_messages`) | **GLM-5.2** (1. Fallback / Planer, `chat_completions`) |
|---|---|---|
| Thinking-Persistenz | **Ja** — H-10 hält unsignierte Thinking-Blöcke über Tool-Runden (Qualitätshebel, aber teuer) | **Nein** — kein Signature-Replay; Reasoning bläht die Historie nicht dauerhaft |
| Kosten/Runde @ ultra | bis **49152** Token | moderat (`reasoning_effort: max`, kein persistenter Trace) |
| Temp/Tokens | Temp auf **1 gezwungen**, `max_tokens`-Floor ~53k (kein Temp-Tuning als Spar-Hebel) | normal |
| Budget-Konsequenz | Historie füllt sich **schnell** → 85%-Regel greift früh | Historie bleibt **leicht** → Compaction-Kadenz darf seltener sein |

### Thinking-Trace-Hygiene (nur M3-relevant)

Die H-10-Persistenz ist gewollt (M3s Interleaved-Thinking ist der dokumentierte Qualitätshebel) — aber sie ist **nicht umsonst**. Regel:

- **Behalten**, solange der Trace zur *aktiven* Kette gehört: laufende Tool-Argument-Herleitung, mehrstufige Reasoning-Kette, die die nächste Runde speist.
- **Beim Compaction fallenlassen**, sobald der zugehörige Sub-Task *abgeschlossen* ist: das Reasoning, das zu einem bereits verifizierten Ergebnis führte, muss nicht mit — nur das Ergebnis + der Extrakt-Pfad. Ohne aktives Compaction schleppt H-10 alte Traces sonst unbegrenzt mit.
- **Nie** den Trace der *gerade laufenden* Runde kürzen (bricht M3s Kette mitten im Denken).

### Praktische Konsequenz für Rollen

- **M3-Königin / M3-Vision-Worker:** Checkpoint-Rhythmus straffen (eher alle 3–4 Tool-Cluster statt 5), lange narrative Zwischenergebnisse vermeiden — M3 füllt das Fenster mit Denken, nicht nur mit Tool-Output.
- **GLM-5.2-Planer:** kann längere Kontexte tragen, bevor Compaction nötig wird — sein Reasoning verschwindet nach der Antwort. Ideal für den Plan-heavy-Teil einer Pipeline.
- **Lane-Bezug statt Modell-ID:** wer auf `worker-vision`/Session-Default (M3) läuft, wendet die Thinking-Hygiene an; wer auf `koenigin`/`worker-heavy` (GLM) läuft, nicht. Siehe LANE-TRUTH.

## Drei Compaction-Levels

### Level 1 — Tool-Result Clearing (40–60% Reduktion)
Jedes Tool-Ergebnis, das verarbeitet wurde, ersetzen durch:
```json
{"compact": "read_file(path) → 340 Zeilen, 2 Fehler gefunden", "detail_path": "/full/path"}
```
Statt der vollen 340 Zeilen nur den Extrakt behalten.

### Level 2 — Selective Summarization
Alte Nachrichtenblöcke (älter als letzte 5 Turns) zusammenfassen:
```
## Compaction-Summary (vor Turn 12)
- Architekturentscheidungen: PostgreSQL selected (ACID)
- Offene Bugs: API-Timeout >10k Records
- Implementation: Phase 1 done, Phase 2 gestartet
- Nächste Schritte: Phase-2-Gate, dann Phase 3
```
**Fokus der Summary**: Architekturentscheidungen · Offene Bugs · Implementierungsdetails

### Level 3 — Intelligent File Access
Nur die 5 zuletzt genutzten Dateien voll im Kontext halten.
Rest als Referenz mit Pfad + Zusammenfassung:

| Datei | Status | Summary |
|---|---|---|
| `src/core/main.ts` | 🔴 Aktiv | 340 Zeilen, Einstiegspunkt |
| `config/default.yaml` | ✅ Done | Baseline-Konfiguration |
| `docs/ARCHITECTURE.md` | ⏸️ Referenz | 12 Seiten, nicht mehr aktiv editiert |

## Context-Health-Metriken

| Metrik | Ziel | Bedeutung |
|---|---|---|
| KV-Cache Hit Rate | >80% | Wiederverwendung bereits geladener Tokens → Latency & Cost |
| Context Utilization | >70% | `meaningful_tokens / total_context_tokens` |
| Context Overflow Rate | <5% | Wie oft läuft das Window voll |
| Compaction Effectiveness | >0.8 | 80% Info-Behalt bei 50% Size-Reduktion |
| Avg Active Context | <50k Token | Realistisches Budget für Production-Agents |

### Messmethode (bei Hermes)

```python
# Faustformel — kein direkter API-Call, aber aus Tool-Call-Volumen schätzbar
total_tokens = sum(len(result) for result in tool_results)
if total_tokens > 40000:  # ca. 80-85% von 50k
    compact()
```

Hermes hat keinen nativen Token-Zähler im Tool-Loop — diese Skill definiert die **Verhaltensregel**: nach jedem Task-Cluster (5+ Calls) kurz innehalten und Context-Budget checken.

## Just-in-Time Retrieval (JIT)

Statt alle Daten vorab zu laden, referenziere nur **wo** Informationen liegen:

```markdown
## Data Access
- Customer data: /data/customers.csv
- Product catalog: /data/products.json
- DO NOT load upfront. Load only the specific rows
  relevant to the current step using read_file(limit=50).
```

Vorteil: Active Context bleibt schlank, Attention-Budget fokussiert.

## Tool-Output-Optimierung

Jedes Tool sollte token-effiziente Returns liefern:

```python
# ✅ Smart — kompakte Zusammenfassung
def search_codebase(query, max_results=5):
    results = search(query)[:max_results]
    return {
        "matched_files": [f.path for f in results],
        "total_matches": len(results),
        # Full content via read_file(path) on demand
    }
```

```python
# ❌ Dumb — volle 50k Rohdaten
def search_codebase(query):
    return search(query)  # alle Ergebnisse, alle Felder
```

Bei Hermes-Tools:
- `read_file` → `limit=50` statt Default 500
- `web_extract` → `char_limit=5000` für große Seiten
- `search_files` → `limit=10` statt Default 50
- `terminal(command="grep ... | head -20")` statt `cat ...`

## Verhältnis zu anderen Strategien

Dieser Skill arbeitet **Hand in Hand** mit:
- `context-mode` — Virtualisierungsschicht für Token bei großen Outputs (Level-1-Compaction als Prinzip)
- `hermes-react-pattern` — ReAct-Loop mit eingebautem Reflexion-Stop (Gelegenheit zum Kompaktieren)
- `multi-agent-master-workflow` — Subagent-Isolation verhindert Context-Cross-Contamination (die beste Compaction ist die, die gar nicht erst nötig wird)

## Pitfalls

1. **Overly Aggressive Compaction**: Zu frühes oder zu starkes Zusammenfassen verliert subtile Details. Erst auf Recall optimieren (alle relevanten Infos bleiben erhalten), dann auf Precision (Überflüssiges entfernen).
2. **85% nicht als Alarm, sondern als Routine**: Nicht panisch kompaktieren — die 85% sind ein **Proactiv-Schwellwert**, kein Notfall.
3. **Garbage-In-Garbage-Out**: Wenn der Input bereits komprimiert war (z.B. `head -5` Output), nicht nochmal kompaktieren — das verliert Information.
4. **Compaction ≠ Vergessen**: Das kompaktierte Artefakt muss referenzierbar bleiben (Pfad im Output). Kein "das löschen wir einfach" ohne Trail.
