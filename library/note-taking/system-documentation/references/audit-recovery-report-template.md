# Audit-Recovery-Report — Template

> Vollständiges Template für den Abschluss eines Multi-Task-Recovery-Plans.
> Jede Sektion ist als Platzhalter mit Verweis auf die Live-Session-Daten notiert.

## Context

> **Plan:** `<absoluter Pfad zum Plan>`
> **Ausführender:** `<Agent-Name / Biene X>`
> **Datum:** `<YYYY-MM-DD>`
> **Trigger:** `<Kurzbeschreibung: was hat den Plan ausgelöst?>`

Schreibe 2–3 Absätze: was der Plan bezweckte, welcher Audit/Befund der Auslöser war, und in welchem Arbeitskontext (Daily-Recovery, Post-Incident, Scheduled-Maintenance) das stattfand.

Leitmotiv einfügen, das die Haupt-Lektion des Durchlaufs auf den Punkt bringt.

---

## Reality-Check-Tabelle

Übernimm die Realitäts-Status-Zeilen **verbatim** aus der Plan-Tabelle. Keine neuen Zeilen, keine Umformulierungen. Nur ✅/❌/🆕-Marker ergänzen.

| Audit-Punkt | Geplanter Status | Tatsächlicher Status (verifiziert) | Plan-Aktion |
|---|---|---|---|
| 1. ... | "..." | ✅ **beschreibung** | ❌ STRIKEN / ✅ **ECHTE LÜCKE** |
| ... | ... | ... | ... |

### Disposition

- ❌ Streichen: `<Anzahl>` Punkte (jeweils mit Kurzbegründung)
- ✅ Als fachliche Lücken weiterführen: `<Anzahl>` Punkte
- ✅ Zusätzlich als Meta-Guard: `<Task-Name>` gegen `<Pitfall-Ref>`
- Ergebnis: `<Kernergebnis in einem Satz>`

---

## Plan-Disposition

| Task | Plan-Aufgabe | Geschätzte Zeit | Zweck |
|---|---|---:|---|
| Task 0 | `<Name>` | `<Min>` Min | `<Zweck>` |
| ... | ... | ... | ... |
| **Total** | **N Tasks** | **∑ Min** | **Kern-Zweck** |

### Reihenfolge und Abhängigkeiten

1. Task 0 zuerst — `<Begründung>`
2. Task X und Y unabhängig
3. ...

### Nicht erneut einplanen

- ❌ `<gestrichener Punkt 1>` — `<Begründung>`
- ❌ `<gestrichener Punkt 2>` — `<Begründung>`
- ❌ Alle Punkte aus der Streichen-Liste oben.

---

## Pitfall-Lesson

> **Kurztitel:** `<Pitfall- oder Lesson-Titel>`
> **Nachweis:** `<Datum und Session-Kontext>`

### Symptom

Was war sichtbar falsch? Welcher Schaden / Re-Work / falsche Annahme?

### Root Cause

Der tiefere Mechanismus — nicht *was*, sondern *warum*.

### Fix

Die konkrete Änderung / der Workflow / der Patch, der angewendet wurde.

### Guard

Wie verhindern wir die Wiederholung? (Regel, Skript, Skill-Patch, Cron, Quality-Gate)

### Kostenwirkung

> **Faustregel:** Der Live-Verify kostet Minuten; die Reparatur einer falschen Planannahme kostet 30–60 Minuten.

---

## Cross-Reference

### Vorheriger Audit-Report

- ✅ `<Pfad zum vorherigen Report>` — `<Datum, Größe, Status>`
- `<Beschreibung der Beziehung: ergänzt ersetzt, erweitert?>`

### Verwandte Memories

- `<memory-id>` — `<Kurztitel>`
- ...

### Verwandte Pitfalls

- #`<Nummer>` — `<Titel>`
- ...

### Plan- und Nachweis-Pfade

- Plan: `<absoluter Pfad>`
- Dieser Report: `<absoluter Pfad>`
- Vorheriger Report: `<absoluter Pfad>`

---

## Abschlussstatus

- ✅ `<Schritt 1>` — `<Detail>`
- ✅ `<Schritt 2>` — `<Detail>`
- ✅ Mnemosyne-Anker geschrieben: `` `<memory-id>` ``
- ✅ Zeilen- und Inhaltscheck bestanden: `<Zeilenanzahl>` Zeilen

**Status:** Verifiziert und abgeschlossen.
