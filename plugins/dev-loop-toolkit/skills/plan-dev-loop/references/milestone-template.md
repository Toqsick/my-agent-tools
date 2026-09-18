# milestone-template.md — Struktur des Plan-Docs

Skeleton für den Meilenstein-Plan (an pokerogue „bei-meinem-pokerouge3ds-projekt-rosy-lemon"
angelehnt; Abschnitte kürzen, wo der Anlass trivial ist — aber keine still streichen).

```markdown
# <Projekt> — <M9/M10/M11>: <Titel je Milestone>

## Context
Wo steht das Projekt (main-SHA, Verify-Stand, Tracker-Stand)? Was will der Mensch?
Welche Entscheidung dieses Gesprächs ändert den bisherigen Rahmen? (1–2 nummeriert)

## Ausgangslage (verifiziert, nicht aus Doku übernommen)
Tabelle: Bereich | Stand — jede Zeile gemessen (Befehl im Fußnoten- oder Klartext).
Nur Zahlen, die du selbst erzeugt hast; Doku-Behauptungen landen als „stale?"-Fund
in der Bruchstellen-Sektion oder als Aufräum-Task.

### Ist-Abgleich gegen <Ziel/Upstream>
Tabelle: Dimension | Im Projekt | Referenz | Abdeckung % — der stärkste Hebel des
Gesamtplans ist meist die Zeile mit dem größten Delta.

## Plan

### Schritt 0 — Scope-Fixierung (vor allem anderen)
gov:-Commit-Muster, wenn Scope sich ändert: DECISIONS-Eintrag D-n hebt alte
Entscheidung wörtlich auf + Regelwerks-Nachzug (MASTER_PLAN/ROADMAP/WORKFLOW-Zeilen).

### Schritt 1 — Tracker anlegen
Milestone-Tabelle: Milestone | Titel | Issues (Anzahl + gate:G-n).
Pro Milestone die Task-Tabelle (siehe issue-authoring.md für Body-Format).

### Schritt 2 — Abarbeitung
„Strikt nach Loop-Protokoll" + Besonderheiten (z. B. max. 1 Meilenstein-Block/Tag).

## Reihenfolge ist nicht beliebig
Je nicht-trivialer Kante: „T-9.2 vor T-9.7, sonst zementiert die Ability-Tabelle
den CI/lokal-Unterschied" — Begründung, kein Verweis aufs Bauchgefühl.

## Bruchstellen und Verify-Schleifen
(Brücke zu references/bruchstellen.md — hier die projektspezifischen Fälle.)

## Kritische Dateien
Pfadliste mit je einer Zeile, warum kritisch.

## Wiederverwenden statt neu bauen
Existierende Funktionen/Tests/Werkzeuge, die neue Tasks nur verdrahten.

## Risiken
Je: beobachtbarer Auslöser + wer entscheidet was, wenn er zuschlägt.

## Verifikation
Pro Task (nummerierte Befehlskette) und pro Milestone (zusätzliche Gates:
Parity-Report, Container-Build, Artefakt-Abgleich, Emulator-Durchlauf — je nach Repo).

## Handoff an dev-loop
REIHENFOLGE: [#97, #98(gate:HALT), #86, …] — Issue-Nummern, Dep-Edge-sortiert,
Gates markiert. Wörtlich in den letzten agent-log-Block kopieren.
```

## Milestone-Ende-Vorlage (Gate-Issue-Body)

```markdown
**gate:G-<n> — <Kriterium des Meilensteins>**

Checkliste (alles muss bewiesen verlinkt sein):
- [ ] <Beweispunkt 1 + Link/Report>
- [ ] <Beweispunkt 2 …>

Freigabe: Kommentar „G-<n> approved" von <Mensch>. Ohne Approval beginnt der Agent
den Folge-Meilenstein nicht.
```
