---
name: subagent-self-verify-gates
title: Subagent Self-Verification Gates
description: >-
  Use when user asks for adding numerical gates to a subagent briefing, checking worker JSON, file counts, or word counts, preventing phantom-write claims, or reducing Queen verification overhead. NOT for replacing parent-side final verification or writing ordinary application unit tests. Supplies copy-paste validation gates and briefing patterns so workers prove artifact existence, shape, and minimum completeness before returning.
triggers:
- In subagent briefings: numerical thresholds for file count / JSON validity / line
    count
- Bee soll Output selbst verifizieren (nicht nur Queen nach Landung)
- Verification-Gates als PFLICHT-Kriterium im Briefing
version: 1.0.0
author: Yuno
lane: koenigin
reasoning_effort: xhigh
related_skills:
- queen-bee-schwarm-dispatch
- multi-agent-orchestration
- multi-agent-pitfalls-cheatsheet
- worklow-template
license: MIT
trigger_keywords: ['gates', 'briefing', 'counts', 'verification', 'user']
keywords: ['gates', 'briefing', 'counts', 'verification', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
---

# Subagent Self-Verify Gates

> Embed copy-paste-bare verification commands direkt in subagent briefings.
> Die Biene prüft sich WÄHREND der Arbeit selbst — nicht erst die Queen nach der Landung.
> Reduziert Queen-Verify-Overhead von ~100% auf Stichproben.
>
> Validated: Galaxy-Health-Bridge 2026-07-19 (3 Bienen, 0 Queen-Patches nach Erst-Wurf)

## Problem

Die bestehenden Queen-Verify-Patterns (Tier 1/2/3, siehe queen-bee-schwarm-dispatch) setzen
erst NACH der Bienen-Landung an. Dazwischen liegen Sekunden bis Minuten, in denen die Queen
weitere Aktionen starten kann. Ein Phantom-Write (Datei existiert nicht, obwohl Biene schrieb)
fliegt erst auf, wenn die Queen selbst `read_file` aufruft.

Zusätzlich: Bienen behaupten im Self-Report "All criteria met", während grep 17 Boldface-Fehler
zeigt (validiert 2026-07-13). Ein reiner Self-Report ohne Verification-Gate ist unzuverlässig.

## Lösung

Gib der Biene konkrete, ausführbare Verification-Befehle ALS TEIL DER BRIEFING-Constraints.
Die Biene führt sie als letzten Schritt aus und MUSS alle Gates passieren, bevor sie
"done" meldet.

## Verfügbare Gates (Copy-Paste)

### Gate 1: JSON-Validität

Für JSON-Dateien (Grafana-Dashboards, Configs, Schemas):

```text
VERIFICATION-GATES (PFLICHT — letzte Aktion vor Self-Report):
  python3 -c "import json; json.load(open('<PFAD>'))"
  — MUSS ohne Fehler durchlaufen. Bei Syntax-Error: `patch()` fixen, erneut testen.
  — Wenn nicht behebbar: im Self-Report dokumentieren WARUM.
```

### Gate 2: File-Count-Schwellen

Für Multi-File-Outputs (Projekt-Scaffold, Doku-Sets):

```text
VERIFICATION-GATES (PFLICHT):
  1. find ~/<PFAD>/ -type f | wc -l  (erwartet >= N)
  2. find ~/<PFAD>/ -name "*.kt" | wc -l  (erwartet >= M)

  Wenn unterschritten: fehlende Dateien rekursiv auflisten und nachliefern.
```

### Gate 3: Wordcount / Zeilen-Gates

Für Doku-Outputs:

```text
VERIFICATION-GATES (PFLICHT):
  1. wc -l ~/docs/system/<DATEI>.md  (erwartet zwischen N und M)
  2. wc -w ~/docs/system/<DATEI>.md  (erwartet zwischen X und Y)

  Bei <= X: Prosa verdichten, fehlende Sektionen ergänzen.
  Bei >= Y: Straffen, Redundanzen entfernen.
```

### Gate 4: Datei-Typ-spezifische Zählung

Für gemischte Projekte (Gradle + Kotlin + Resources):

```text
VERIFICATION-GATES (PFLICHT):
  1. find ~/<PFAD>/ -type f | wc -l           (erwartet >= 15)
  2. find ~/<PFAD>/ -name "*.kt" | wc -l      (erwartet >= 8)
  3. find ~/<PFAD>/ -name "*.kts" | wc -l     (erwartet >= 2)
```

### Gate 5: Kombi-Gate für heterogene Outputs

Biene erstellt Doku + Code + Schema parallel:

```text
VERIFICATION-GATES (PFLICHT — alle drei nacheinander):
  1. python3 -c "import json; json.load(open('.../dashboard.json'))"
  2. ls -la ~/docs/system/galaxy-watch6-*.md
  3. find ~/<PFAD>/influxdb-schema -type f | wc -l (erwartet >= 3)

  Nur wenn alle drei Gates grün: Self-Report schreiben mit "VERIFIED: OK".
```

## Integration ins Briefing

Die Gates gehören NACH den Tasks und VOR die Self-Report-Anweisung.
Immer als eigener Abschnitt mit PFLICHT-Header:

```text
AUFGABEN:
1. ...
2. ...

VERIFICATION-GATES (PFLICHT — letzte Aktion vor Self-Report):
  1. python3 -c "import json; json.load(open('<PFAD>'))"
  2. find ... | wc -l (erwartet >= N)

  Nur wenn alle Gates grün: Self-Report mit "VERIFIED: OK".
  Wenn ein Gate scheitert: Fehler beheben, dann erneut testen.
  Wenn nicht behebbar: im Self-Report dokumentieren.
```

## Warum das funktioniert

**Validierte Heuristik (2026-07-19, 3 Bienen):**
- Bienen MIT Verification-Gates im Briefing: 0 Queen-Patches nach Erst-Wurf
- Bienen OHNE Gates (frühere Sessions): 1-3 Nachbesserungen nötig

**Mechanismus:** Die Biene bekommt einen deterministischen, ausführbaren Check
den sie nicht ignorieren kann (anders als "Achte auf Format"). Sie merkt sofort
wenn ein write_file nicht ankam (Gate scheitert → debug → fix → re-test).

**Grenzen:**
- Nicht für subjektive Qualität (Stil, Lesbarkeit) — dafür Format-Constraints
- Nicht für Content-Korrektheit (ob die Doku fachlich richtig ist)
- Gate-Count auf 2-3 pro Biene begrenzen (sonst Overhead > Nutzen)

## Relationship to existing patterns

Dieser Skill ergänzt queen-bee-schwarm-dispatch und multi-agent-orchestration
um die **Bee-Self-Verify-Ebene**. Die bestehende Queen-Verify (Tier 1/2/3) bleibt
als Backstop erhalten — Self-Verify-Gates reduzieren nur den Bedarf.

| Ebene | Wer prüft | Wann | Was |
|-------|-----------|------|-----|
| Self-Verify Gate | Biene | Während Arbeit | File-Count, JSON-Validity, Wordcount |
| Queen Tier 1 | Queen | Nach Landung | Datei-Existenz, Zeilen |
| Queen Tier 2 | Queen | Nach Landung | Content-Validierung (Überschriften, Zahlen) |
| Queen Tier 3 | Queen | Nach Landung | Realitäts-Check gegen Live-State |
