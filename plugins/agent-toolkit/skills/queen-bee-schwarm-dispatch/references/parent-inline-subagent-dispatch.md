# Parent-Inline + Subagent Parallel Dispatch (SUB-SUB-DISPATCH Pattern)

**Validiert:** 2026-07-14 — SUB-SUB-DISPATCH-TEST mit 14 Bug-Cross-Check
**Modell:** deepseek/deepseek-v4-flash (Parent) → minimax-m3 (Subagent)
**Kosten:** 0 zusätzliche Kosten (beide auf Nous-Plan)

## Pattern-Beschreibung

Der Parent (Haupt-Agent) tut **nicht** nur Queen-Review — er produziert **parallel** ein eigenes Artefakt,
während ein Subagent ein zweites, unabhängiges Artefakt erstellt. Beide werden am Ende **unabhängig verifiziert**
und in einem strukturierten Self-Report zusammengefasst.

## Anwendungsfälle

| Situation | Parent macht | Subagent macht |
|-----------|-------------|---------------|
| Cross-Check + Mapping | Haupttabelle schreiben | JSON-Mapping / strukturierte Extraktion |
| Report + Batch-Execution | Zusammenfassung schreiben | Terminal-Batch-Script parallel testen |
| Architecture-Doku + Live-Audit | Architektur-Skizze schreiben | Live-DB-Extraktion + Drift-Check |
| Guide + Code-Generation | Guide-Markdown schreiben | Code-Generator parallel laufen lassen |
| Analyse + Datenaufbereitung | Human-readable Analyse schreiben | Rohdaten in JSON/CSV/YAML aufbereiten |

## Dispatch-Code (Template)

```python
# Phase 1: Dispatch Subagent parallel
delegate_task(
    goal="...",
    context="...",
    role="leaf"  # Default — Parent macht kein Nested-Delegation-Briefing
)

# Phase 2: Parent macht inline work (kein Warten!)
write_file(...)  # Hauptdatei
terminal(...)    # Verifikationen

# Phase 3: Subagent-Ergebnis kommt automatisch via Message-Back
# → Parent merged + verifiziert beide Outputs
```

**Wichtig:** Der `delegate_task`-Aufruf ist **non-blocking** — er returned sofort und der Subagent
arbeitet im Hintergrund. Das Subagent-Ergebnis kommt als neuer Message-Back in den Chat. In der
Zwischenzeit arbeitet der Parent weiter an eigenen Artefakten.

## Side-Effect File Verification Protocol

JEDER Subagent-Dispatch mit Output-Dateien MUSS nach beiden Seiten verifizieren:

```bash
# Minimale Verify (immer Pflicht)
ls -la /tmp/path/to/file1.md /tmp/path/to/file2.json

# Content-Verify (bei strukturierten Daten)
python3 -c "import json; json.load(open('/tmp/path/to/file.json'))"
python3 -c "print(len(open('/tmp/path/to/file.md').read()), 'bytes')"

# Schema-Verify (bei erwarteten Keys)
python3 -c "
import json; d=json.load(open('/tmp/path/to/file.json'))
print('keys:', len(d), 'total matches:', sum(len(v) for v in d.values()))
"
```

**Anti-Pattern:** Dem Subagent-Self-Report blind vertrauen ohne `ls -la` auf die tatsächlichen Dateien.
Self-Reports können "alles OK" behaupten, während die Datei fehlt oder leer ist.

## Structured Self-Report Template (validiert 2026-07-14)

Nach erfolgreichem Abschluss beider Workstreams:

```markdown
## Self-Report: <Task-Name>

**Hauptdatei:** `<pfad>` — ✅ **<bytes> Bytes**
**Sub-Datei:** `<pfad>` — ✅ **<bytes> Bytes, valid <format>, <N> Keys, <M> Matches**

### Pflicht-Felder

| Feld | Wert |
|------|------|
| **sub_call_count** | **N** (Anzahl delegate_task-Aufrufe) |
| **Anzahl gefundener X (von N)** | **X/N** dokumentiert, Y mit Code-Treffern, Z nur als Doku |
| **Bestätigung beider Files** | ✅ Datei1 (<bytes>) + ✅ Datei2 (<bytes>, valid JSON) |
| **Lohnt-sich-Bewertung** | ✅ **JA — sehr lohnend** oder ❌ **Nein — Einzelfall** |

### Kernergebnisse (gekürzte Tabelle)

- ...

### Lohnt-sich-Entscheidungsmatrix

| Kriterium | Ja | Nein |
|-----------|----|------|
| Subagent-Ergebnis ≠ Parent-Ergebnis? (echte Parallelität) | ✅ | ❌ |
| Subagent hätte >2 Min inline gebraucht? | ✅ | ❌ |
| Dateien unabhängig verifiziert? | ✅ | ❌ |
| Subagent-Ergebnis sofort nutzbar (kein manuelles Nacharbeiten)? | ✅ | ✅ |
| **Gesamt** | **X/4** | **Y/4** |

Bei ≥3/4 Ja → Dispatch hat sich gelohnt. Bei ≤2/4 → besser inline machen.
```

## Lohnt-sich-Bewertung — Definition

Die Bewertung am Ende eines SUB-SUB-DISPATCH entscheidet, ob das Pattern bei **ähnlichen
Aufgaben** wieder eingesetzt werden soll:

| Bewertung | Bedeutung | Nächstes Mal? |
|-----------|-----------|---------------|
| ✅ **JA — sehr lohnend** | Deutlich schneller/breiter als inline, Subagent-Ergebnis hochwertig, sofort nutzbar | Immer dispatchen |
| ✅ **Ja — lohnend** | Etwas schneller, Ergebnisse brauchbar, noch vertretbar | Bevorzugt dispatchen |
| ⚠️ **Grenzwertig** | Minimaler Zeitgewinn, Subagent-Ergebnis mit Nacharbeit | Nur bei sehr großen Scopes |
| ❌ **Nein — Einzelfall** | Subagent-Ergebnis musste nachgearbeitet werden oder war nutzlos | Inline machen |

## Validiertes Beispiel (2026-07-14)

**Task:** Cross-Check 14 bekannte GreyHack-Bugs gegen Live-Repo
**Parent-Modell:** deepseek/deepseek-v4-flash
**Subagent-Modell:** minimax-m3

| Metrik | Wert |
|--------|------|
| sub_call_count | 1 |
| Subagent-API-Calls | 41 |
| Subagent-Laufzeit | 134.8s |
| Parent-inline-Laufzeit | ~45s |
| Match-Count | 57 (14 Bug-Keys) |
| File-Sizes | 6.6 KB (MD) + 13.5 KB (JSON) |
| Lohnt-sich | ✅ JA — sehr lohnend |

**Warum lohnend:** Der Subagent brauchte 41 API-Calls und 134s für die tiefe Code-Durchleuchtung
(14 Dateien, jedes Bug-Pattern einzeln gegrept und bewertet). Der Parent hätte das inline nicht
in vertretbarer Zeit gemacht. Das JSON-Mapping mit 57 Matches war sofort nutzbar für die
Haupttabelle. Die Parallelität brachte ~3x Speedup gegenüber sequenzieller Bearbeitung.

## Voraussetzungen

- **max_concurrent_children ≥ 1** (Default: 6 für Bastis Setup — OK)
- **Subagent-Modell** = Parent-Modell oder Fallback (nicht wählbar)
- **Kein File-Overlap** zwischen Parent und Subagent — sonst Lost-Writes
- **Parent idle nicht erlaubt** — immer einen Plan B haben (eigenes Artefakt)