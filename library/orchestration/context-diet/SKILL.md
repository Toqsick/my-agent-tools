---
name: context-diet
description: "Context-Diät: Tool-Defaults, Turn-Checkpoints, Token-Tagebuch. Inkl. M3-Thinking-Trace-Rhythmus (ultra=49152 tok/Runde) vs GLM-5.2."
version: 1.1.0
author: Yuno for Basti
license: MIT
lane: koenigin
agent: Yuno
trigger_keywords:
  - kontext diät
  - context diet
  - token tagebuch
  - session post-mortem
  - tool output entschlacken
  - context checkpoint
keywords:
  - context-management
  - token-budget
  - self-improvement
  - session-hygiene
  - tool-output
related_skills:
  - hermes-context-budget
  - context-engineering-kb
  - self-improving
  - hermes-react-pattern
last_curated: 2026-07-21
curated_by: Yuno
routing_hint: "Use when Basti eine Session context-schonend führen will (präventiv), ein Checkpoint fällig ist (aktiv), oder eine Session analysiert werden soll (post-mortem)."
---

# Context-Diät

Operativer Drill für context-schonende Agent-Sessions in drei Modi: präventiv (bevor Token verbrannt werden), aktiv (während der Session), post-mortem (nach Session-Ende). Ergänzt `hermes-context-budget` (das Framework liefert) mit ausführbarem Ablauf, konkreten Parametern und einem Self-Improve-Loop.

## Drei Modi im Überblick

| Modus | Wann | Aktion |
|---|---|---|
| Präventiv | Vor Tool-Call | Default-Parameter setzen, Batch-Strategie wählen |
| Aktiv | Nach N Turns | Checkpoint: Tool-Outputs komprimieren, Budget checken |
| Post-mortem | Nach Session-Ende | Token-Tagebuch schreiben, Lektionen extrahieren |

## MODUS 1: Präventiv (vor dem Tool-Call)

### Tool-Default-Parameter

Diese Werte bei jedem Tool-Call verwenden, außer wenn explizit mehr nötig:

| Tool | Default-Param | Begründung |
|---|---|---|
| `read_file` | `limit=50` | Reicht meist für Kontext |
| `web_extract` | `char_limit=5000` | Head-Tail reicht, Rest via Pfad |
| `web_extract` (Paper) | `char_limit=20000` | Abstract + Results |
| `search_files` | `limit=10` | Top-10-Hits reichen |
| `terminal` (grep/find) | `head -20` pipen | Verhindert 50k-Output |
| `delegate_task` | bei >10 Calls | Isoliert Context |

### Batch-Strategie

Ähnliche Operationen bündeln statt alternieren. Richtig: 10 Dateien via einem Script lesen, Result aggregieren, einmal zurückgeben. Falsch: 10x `read_file` nacheinander. Bei parallelen Tasks: `delegate_task(tasks=[...])` mit bis zu 10 Items.

Bei >10 Items: Batches zu je 10 bilden, incomplete Batches markieren, Ergebnisse aggregiert an den Style-Report übergeben.

### Pre-Flight Check

Vor komplexen Tasks (erkennbar an >5 geplanten Tool-Calls): Token-Volumen schätzen (Calls × 1500), bei >40k Subagent-Delegation planen, JIT-Retrieval (nur referenzieren wo Daten liegen, nicht vorab laden).

**Auf MiniMax-M3 (Session-Default) die Schätzung anders rechnen:** M3 hängt bei `reasoning_effort: ultra` pro Runde bis zu **49152 Thinking-Token** an, die per H-10 über Tool-Runden **erhalten bleiben**. Faustformel dort nicht `Calls × 1500`, sondern **`Calls × 1500 + Runden × ~8–15k`** (reale Trace-Länge, selten das volle Budget). Das verschiebt die Delegations-/Compaction-Schwelle auf M3 deutlich nach vorn. GLM-5.2 (Fallback/Planer) hat diese Persistenz nicht → dort bleibt `Calls × 1500`. Detail + Hygiene-Regel: `hermes-context-budget` → „M3-Thinking-Traces vs GLM-5.2".

## MODUS 2: Aktiv (während der Session)

### Checkpoint-Rhythmus

Nach jedem Cluster von 5 Tool-Calls einen Mikro-Checkpoint:

1. Output-Compression: Verarbeitete Tool-Ergebnisse zu einzeiligen Extrakten zusammenfassen
2. Budget-Check: Grobe Schätzung des aktuellen Token-Stands
3. Decision: Weitermachen, komprimieren, oder an Subagent auslagern

Nach 10 Tool-Calls (oder 85% Context-Auslastung, siehe `hermes-context-budget`): Full-Compaction-Checkpoint.

**Auf M3 den Rhythmus straffen:** wegen der bis zu 49152 Token/Runde persistenten Thinking-Traces eher **alle 3–4 Cluster** statt 5 checkpointen. Beim Full-Compaction die Traces *abgeschlossener* Sub-Tasks fallenlassen (nur Ergebnis + Extrakt-Pfad behalten) — nie den Trace der laufenden Runde kürzen. Auf GLM-5.2 gilt der normale 5er-Rhythmus.

### Output-Compression-Muster

Verarbeitete Tool-Ergebnisse ersetzen durch kompakten Extrakt:

```
[COMPACTED] read_file(config.yaml) → 340 Zeilen, 2 Fehler in Sektion server (Zeile 45, 89), DB-Host fehlt
```

Original-Pfad im Extrakt behalten. Bei Bedarf nachladbar.

### Kompressions-Entscheidung

| Situation | Komprimieren? |
|---|---|
| Ergebnis rein lesend, Info extrahiert | Ja |
| Wird im nächsten Step referenziert (Pfad, ID, SHA) | Nein, Referenz behalten |
| Bereits komprimiert (z.B. `head -5`) | Nein, Doppel-Kompression verliert Info |
| Enthält Fehler/Todo-Liste für später | Partiell, nur erledigte Items entfernen |
| **M3-Thinking-Trace eines *abgeschlossenen* Sub-Tasks** | **Ja** — Ergebnis + Pfad reichen, das Reasoning muss nicht mit |
| **M3-Thinking-Trace der *laufenden* Runde** | **Nein** — bricht M3s Kette mitten im Denken |

## MODUS 3: Post-mortem (nach Session-Ende)

### Token-Tagebuch schreiben

Pfad: `~/20-Workspace/logs/token-tagebuch-YYYY-MM-DD.md`

Struktur:

```markdown
# Token-Tagebuch YYYY-MM-DD

## Session-Ziel
[Was war die Aufgabe?]

## Token-Verschwendung identifiziert
- [Tool] [Call-Beschreibung]: [verschwendete Token geschätzt] — [Ursache]
- Beispiel: web_extract mit char_limit=15000 bei Blogpost der nur 2000 braucht

## Lektionen gelernt
- Lektion 1: [Konkrete Regel für nächste Session]
- Lektion 2: [...]

## Diät-Regeln aktualisiert
- [Neue Default-Parameter oder Batch-Strategie]

## Nächste Session
- [Vorgabe für nächste vergleichbare Session]
```

### Self-Improve-Loop

Nach 3 ähnlichen Verschwendungsmustern (gleicher Tool-Fehler, gleiches Batch-Versäumnis): Pattern in `context-engineering-kb` als Concept-Seite eintragen, neue Diät-Regel zu MODUS 1 hinzufügen. Siehe `self-improving` für den generischen Loop.

### Metriken sammeln

Pro Session grob erfassen (keine exakte Token-API nötig):

| Metrik | Schätzmethode |
|---|---|
| Tool-Calls gesamt | Aus Conversation-Verlauf zählen |
| Geschätzte Token | Calls × Durchschnittslänge der Outputs |
| Compressions durchgeführt | Aus Checkpoint-Markierungen |
| Delegations an Subagents | Zählen |
| Verschwendungs-Muster | Aus Post-mortem-Analyse |

Diese Metriken fließen ins Token-Tagebuch und nach 10 Sessions in eine Quartals-Synthese.

## User-Gates

Der interne Checkpoint ist keine User-Bestätigung. Explizite Freigabe holen bei:

- Delegation an Subagent (kostet Token, nicht reversibel mid-call)
- Full-Compaction mit potentiellem Informationsverlust (bei `confidence: low` Seiten)
- Post-mortem-Aktionen mit dauerhafter Wirkung: Wiki-Eintrag in `context-engineering-kb`, Cron-Einrichtung, Änderung der Default-Tabelle in MODUS 1

Format: 2-3 konkrete Optionen via `clarify(choices=...)`, keine offenen Fragen. Bei reinen Lese-Checks (Read, Search) kein Gate nötig.

## Fehlerpfade

| Failure | Fallback |
|---|---|
| Compaction verliert Info | Extrakt-Pfad im Output behalten, bei Bedarf Original nachladen |
| Kontext nach Compaction noch zu groß | Escalation: erst Subagent-Delegation, dann Session-Split |
| Subagent-Timeout | Parent-direct Weiterarbeit, Delegation-Ergebnis aus Transcript rekonstruieren |
| Batch unvollständig (8/15 Dateien) | Fehlende Dateien markieren, zweiten Batch nachschieben, Report kennzeichnet Lücken |
| Wiki/Cron-Write schlägt fehl | Ersatzpfad `/tmp/context-diet-fallback-YYYY-MM-DD.md`, Retry beim nächsten Post-mortem |
| Token-Schätzung falsch | Korrektur im nächsten Checkpoint, Lektion ins Tagebuch |

## Integration mit anderen Skills

`hermes-context-budget` liefert das Framework (85%-Regel, Compaction-Levels). `context-engineering-kb` nimmt Self-Improve-Erkenntnisse auf. `self-improving` gibt den generischen Loop vor. `hermes-react-pattern` liefert Reflexions-Stop-Gelegenheiten.

## Pitfalls

- Überkompression: zu frühes Zusammenfassen verliert Details. Erst auf Recall, dann Precision.
- Checkpoints nicht übertreiben: nach jedem Call zu checken kostet mehr Token als es spart. 5-Cluster ist Sweet-Spot.
- Tool-Defaults sind Defaults, keine Dogmen. Wenn eine Aufgabe wirklich 500 Zeilen braucht, nimm 500.
- Post-mortem nicht nur für Katastrophen-Sessions. Auch glatte Sessions haben oft 1 bis 2 Lektionen.
- Token-Schätzungen sind grob. Keine Fake-Präzision vortäuschen.