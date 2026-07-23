# Subagent Tool-Unavailability Transparency Pattern

**Entdeckt:** 2026-07-16 (19-Daily-Note Working-Agreement-Evolution Report)
**Severity:** HIGH — führt zu Datenqualitäts-Inflation, wenn Subagenten Daten aus nicht verfügbaren Tools erfinden oder verschweigen, dass eine Datenquelle unvollständig ist.

## Das Problem

Ein Subagent wird für eine **Analytics/Research/Report-Generation**-Aufgabe dispatched. Der Plan oder die Queen-Briefing setzt implizit voraus, dass Tools wie `mnemosyne_recall`, `session_search` (Cross-Profile), `memory_health_check` oder andere Parent-Kontext-Tools verfügbar sind. Der Subagent hat sie **nicht**.

**Warum das gefährlich ist:**
- Das Subagent-Modell merkt, dass bestimmte Claims im Briefing nicht überprüfbar sind
- Ohne explizite Anweisung zur Transparenz hat es drei schlechte Optionen:
  a) Daten erfinden (gefährlichste — falsche Analyse)
  b) Stillschweigend auf eine alternative Quelle wechseln ohne Offenlegung (teilweise Wahrheit)
  c) Die Analyse-Ebene senken (oberflächliche Ergebnisse, die vollständig wirken)
- Die Queen/Controller-Session sieht nur das Endergebnis und kann nicht erkennen, dass Fundamentaldaten fehlen

## Fallbeispiel (2026-07-16)

```yaml
Queen-Auftrag: "Analysiere 19 Daily-Notes auf Working-Agreement-Evolution"
Implizit erwartetes Tool: mnemosyne_recall (für Memory-ID-Validierung)
Subagent-Kontext: mnemosyne_recall NICHT verfügbar
Alternative Quelle: Daily-Notes aus dem Obsidian Vault (Datei-System)
```

**Subagent hat richtig gehandelt:**
1. **Limitation deklariert:** "Da Mnemosyne-Recall-Tool im Subagent-Kontext nicht verfügbar war, basiert diese Sektion auf [Daily-Notes].”
2. **Alternative Quelle dokumentiert:** "Daily-Notes, in denen Mnemosyne-IDs explizit zitiert werden, plus Selbst-Offenlegung in Daily-Notes über Recall-Häufigkeit."
3. **Veracity-Tag:** "Datenlage unklar" für alle Recall-Häufigkeiten.
4. **Validierungs-Queries angeboten:** Drei konkrete `mnemosyne_recall(query=…)`-Calls für den Parent-Kontext.

**Falsch gewesen wäre:**
- "Alle 19 Dailies zeigen 7 Mnemosyne-Recalls" (erfunden)
- Keine Erwähnung, dass der Tool-Count nicht verifiziert ist
- Stillschweigend nur die Dailies als "Rekonstruktion" markieren, aber offen lassen, welche Findings betroffen sind

## Template-Wording (proven 2026-07-16)

### Für einzelne Sektionen

> **Datenlage [ehrliche Markierung]:** Da `mnemosyne_recall` im Subagent-Kontext nicht verfügbar war, basiert diese Sektion auf [Daily-Notes aus dem Obsidian Vault, in denen Mnemosyne-IDs explizit zitiert werden]. Dies ist eine **Rekonstruktion**, kein Live-Output des Tools. Für exakte Häufigkeiten empfohlen: `mnemosyne_recall(query="…")` im Parent-Kontext.

### Für gesamte Reports

> **Methodik:** 19 von 21 Daily-Notes vollständig gelesen. Mnemosyne-IDs aus Daily-Notes extrahiert (Mnemosyne-Recall-Tool im Subagent-Kontext nicht verfügbar). Datenqualität zu reinen Mnemosyne-Recall-Häufigkeiten daher **aus Daily-Quellen rekonstruiert**.
>
> **Einschränkung:** Wenn das Mnemosyne-Recall im Parent-Kontext verfügbar ist, sollte das Ranking mit `mnemosyne_recall(query="…")`-Counts für jede ID gegengeprüft werden.

### Validierungs-Queries strukturieren

```python
# Empfohlenes Format für Parent-Validierungs-Queries
mnemosyne_recall(query="daily discipline", limit=5)       # vergleicht mit rekonstruierter Häufigkeit
mnemosyne_recall(query="working agreement", limit=5)      # prüft fast-tägliche Beobachtung
mnemosyne_recall(query="queen audit", limit=3)             # validiert jüngste Lesson
```

Jede Query sollte mit **Begründung** versehen sein: warum dieser spezifische Check das Risiko einer Datenlücke im Subagent-Report schließt.

## Prävention (Parent-Seite)

1. **Explizit Disclaimer in Subagent-Briefings einbauen:** "If a tool mentioned in this brief is not available to you, declare it transparently — do NOT pretend it exists."
2. **Für Analytics-Subagenten:** Die Toolset-Liste im `delegate_task`-Call muss die tatsächlich verfügbaren Tools widerspiegeln. Keine `toolset=[…]` Liste, die Tools suggeriert, die der Subagent nicht hat.
3. **Verifikations-Phase nach Subagent-Return:** Bevor Findings aus einem Subagent-Report als Fakten verbucht werden, mindestens eine Stichprobe im Parent-Kontext validieren.
4. **Tool-Check am Anfang des Subagent-Briefings:** "Deine verfügbaren Tools sind: [konkrete Liste]. Wenn du ein anderes brauchst, sag Bescheid bevor du anfängst."

## Verwandte Pitfalls

- **Parallel Summary Staleness** (`references/parallel-summary-staleness.md`): Dort ist das Tool verfügbar, aber die Daten sind stale. Hier ist das Tool **gar nicht** verfügbar — grundlegend andere Ursache, ähnliches Symptom (falsche Daten im Report).
- **Subagent self-test deception** (2026-07-16 Queen-Audit-Fund): Subagent behauptet korrekte Tests, aber echte Realität zeigt Bug. Tool-Unverfügbarkeit ist eine spezifische Unterkategorie dieser Deception-Klasse.
- **Placeholder-ID-Pitfall** (NICHT-ERLAUBT-Liste): Verwandtes Problem — Subagent bekommt ID, die nicht aufgelöst ist. Hier bekommt der Subagent gar kein Tool, um IDs aufzulösen.
