---
name: clarify-options-pattern
description: Use clarify() with 2-4 options instead of open questions during multi-step workflows.
version: 0.1.0
author: Hermes
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Clarify, Decision-Making, User-Steering, Workflow]
trigger_keywords: ['clarify', 'options', 'instead', 'open', 'questions']
keywords: ['clarify', 'options', 'instead', 'open', 'questions']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---

# Clarify-Options-Pattern

Strukturierter Nachfragen-Workflow: Yuno stellt bei Entscheidungen nie offene Fragen, sondern bietet 2-4 vorgefertigte Optionen mit Aufwand/Nutzen/Risiko-Bewertung an. Verhindert dass User "weiß nicht was du willst" antworten müssen.

## When to Use

Triggere diesen Skill wenn:
- Eine Aufgabe hat mehrere plausible Pfade und der User eine Richtung wählen muss
- Mehrere Gates/Freigaben erteilt werden müssen (z.B. G1+G2+G3+G4 für eine Aktion)
- Ein destruktiver Schritt bevorsteht (Browser-Kill, Profile-Mutation, File-Löschung)
- Eine vage Anfrage mit vielen möglichen Interpretationen kommt
- Nach Abschluss einer Phase: was als nächstes?
- Bei Cronjob-Erstellung, Skill-Patching, oder größeren API-Aufrufen
- Wenn der User explizit "Optionen" oder "Was sind meine Möglichkeiten" sagt

## Prerequisites

- `clarify()` Tool verfügbar (Hermes-Standard)
- `mnemosyne_scratchpad` für State-Tracking
- Kontext der bisherigen Arbeit im selben Chat

## How to Run

Rufe `clarify` direkt auf mit:
- `question`: kurz, präzise, auf den Punkt
- `choices`: Array mit 2-4 Optionen, je nach Komplexität
- KEINE offenen Fragen ohne Optionen

Pattern bei mehreren Gates: eine `clarify`-Call pro logischer Entscheidungsgruppe, NICHT 5 einzelne Calls hintereinander.

## Quick Reference

```python
# Standard-Pattern
clarify(
    question="Welcher Ansatz?",
    choices=["Option A: Minimal-invasive Reparatur", "Option B: Sauberer Refactor", "Option C: Mit Logging-Debugging"]
)

# Bei Gates/Freigaben
clarify(
    question="Welche Gates erteilen?",
    choices=["Alle 4 Gates", "Nur G1+G3", "Keine Gates"]
)

# Bei destruktiven Aktionen
clarify(
    question="Wie soll ich verfahren?",
    choices=["Mit Bestätigung pro Schritt", "Autonom bis zum ersten Blocker", "Komplett abbrechen"]
)
```

## Procedure

1. **Sammle Kontext** — was ist die aktuelle Situation, welche Optionen gibt es technisch?
2. **Bewerte Aufwand/Nutzen** — für jede Option: Minuten, Risiko, Reversibilität
3. **Formuliere 2-4 distinkte Optionen** — nicht 5 ähnliche Varianten, sondern 2-4 wirklich unterschiedliche Pfade
4. **Eine Frage pro Call** — nicht 5 Fragen in einem `clarify`
5. **Nutze Ampelsprache** für Risiko/Aufwand: ⭐⭐⭐, ⚠️, 🟢, 🟡, 🔴
6. **Warte auf Antwort** — User bekommt die Auswahl, dannach autonom weiter
7. **Dokumentiere Entscheidung** im Mnemosyne-Scratchpad oder im Artefakt

## Pitfalls

- **Nicht zu viele Optionen:** 4 ist Maximum, mehr ist verwirrend. Lieber 2-3 klare Optionen.
- **Nicht "Was möchtest du?" ohne Optionen:** User kann nicht 5 Sachen gleichzeitig entscheiden.
- **Nicht mehrmals hintereinander fragen:** wenn 2 Decisions kommen, mache sie in EINER `clarify`-Call mit Concat-Frage oder warte auf Antwort für erste.
- **Nicht während Cronjobs fragen:** Cron laufen unattended. Stattdessen Defaults konservativ setzen.
- **Nicht bei trivialen Entscheidungen:** wenn nur eine Option sinnvoll ist, einfach machen + im Bericht erwähnen.
- **Kein Marketing-Sprech:** Optionen sollen ehrlich Aufwand/Risiko nennen, nicht beschönigen.
- **Mehrere `clarify` parallel?** Nein, sequenziell. Der User sieht nur einen gleichzeitig.
- **Nach Antwort:** `user_response` extrahieren und autonom umsetzen, nicht nochmal nachfragen "war das richtig?"

## Verification

Nach User-Antwort:
- Die gewählte Option wurde autonom umgesetzt
- Mnemosyne-Scratchpad hat Entscheidung + Begründung
- Falls neuer Gate erteilt: in `gate-report.md` oder `risk-register.md` dokumentiert
- Falls Multi-Step: nächste `clarify` erst NACH Abschluss der aktuellen Wahl

## Beispiele aus echten Sessions

**Beispiel 1 — Gate-Auswahl (Brave-Comparison 2026-07-23):**
```
clarify(
    question="Wie soll das Projekt enden?",
    choices=[
        "Alle 4 Gates erteilen (G1+G2+G3+G4) — Yuno führt Phase 3+4+6 vollständig aus",
        "Nur G1 erteilen — Yuno inspiziert Wrapper-Skript-Inhalt",
        "Keine Gates erteilen — Projekt endet mit Methodik + UNVERIFIED-Tabelle",
        "Comet aus Perplexity-Prompt v3 entfernen + neue v4-Variante bauen"
    ]
)
# User wählt A → Yuno führt alles aus, kein Rückfragen mehr nötig
```

**Beispiel 2 — Destruktive Aktion (Browser-Kill):**
```
clarify(
    question="Welche Phase 6 Messungen konkret ausführen?",
    choices=[
        "Nur Cold/Warm-Start messen — Tabs gehen verloren",
        "Nur CDP-FCP/Heap messen — kein Tab-Verlust",
        "Beides vollständig — Tabs gehen für Cold-Start verloren",
        "Nur read-only Hardware/Inventory — Browser nicht anfassen"
    ]
)
# User wählt C → Yuno sichert Preferences via Backup, killt Browser,
# startet neu mit --remote-debugging-port, misst alles
```

**Beispiel 3 — Phase-Übergang (nach G5-Abschluss):**
```
clarify(
    question="Wie soll es nach Warm-Statistik weitergehen?",
    choices=[
        "Workloads: 5/10 Tabs via CDP parallel öffnen + RSS messen",
        "Projekt abschließen + Vault-Doc schreiben",
        "Perplexity-Prompt v3 → v4 (Comet-Spalte raus)",
        "Alles zusammen: Workloads + Vault-Doc + Perplexity v4"
    ]
)
# User wählt D → Yuno macht alles in einer Session, sequenziell
```

## Lessons Learned (2026-07-23)

1. **Max 4 Optionen:** ab 5 wird es verwirrend, User entscheidet nicht mehr sondern genervt
2. **Eindeutige Bezeichnungen:** "Option A: ..." ist besser als nur "A"
3. **Konkrete Konsequenzen nennen:** nicht "Variante X" sondern "Variante X (2 min, niedriges Risiko)"
4. **Reversibilität erwähnen:** wenn eine Option rückbaubar ist, das sagen
5. **Eine Frage pro clarify:** User kann nicht 3 Sachen gleichzeitig in einem Modal beantworten
6. **Ehrliche Risiko-Ampel:** 🟢 = sicher, 🟡 = mit Vorsicht, 🔴 = irreversibel
7. **Nach Antwort AUTONOM:** Yuno soll nach User-Wahl NICHT nochmal nachfragen ob das richtig war — einfach machen und im Bericht transparent kommunizieren

## Related Skills

- `yuno-team-routing` — Welcher Yuno-Agent für welche Aufgabe
- `plan-review-and-orchestrate` — Plan-Review vor destruktiven Aktionen
- `hermes-react-pattern` — ReAct-Loop mit Reflexion
- `telegram-clarification-prompt` — Spezifische Variante für Telegram-Kanal
