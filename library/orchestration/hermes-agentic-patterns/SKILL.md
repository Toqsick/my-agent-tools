---
name: hermes-agentic-patterns
description: |
  Use when choosing between outcome prompts and strict procedures, preserving notes across long agent runs, or bridging multiple Hermes orchestration patterns.
  NOT for executing a domain task directly, replacing specialized workflow skills, or using flexible outcome prompts where compliance requires exact reproducibility.
  Explains cross-cutting agentic patterns and routes them to the appropriate persistent-state and orchestration practices.
version: 1.0.0
author: Yuno for Basti
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - patterns
    - outcome-prompt
    - notes
    - spec-fresh-session
    - bridge
    related_skills:
    - hermes-react-pattern
    - hermes-context-budget
    - hermes-long-run-template
    - multi-agent-master-workflow
    - workflow-template
    - context-mode
    - critic-gate
    lane: koenigin
    reasoning_effort: medium
trigger_keywords: ['outcome', 'prompts', 'orchestration', 'patterns', 'choosing']
keywords: ['outcome', 'prompts', 'orchestration', 'patterns', 'choosing']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['video-prompting']
---


# Hermes Agentic Patterns

Dieser Skill ist die **Navigationsbrücke** zwischen allen agentischen Work-Patterns in Bastis Hermes-Setup. Er beschreibt drei fundamentale Pattern-Shifts, die quer zu allen anderen Skills liegen.

## Pattern 1: Outcome-Prompts statt Prozedurlisten

**Prozedurlisten sind fragil** — sobald ein Schritt unerwartet verläuft, bricht die Kette. Outcome-Prompts beschreiben das **fertige Resultat**, nicht den Weg dorthin.

### ❌ Fragil (Prozedur)

```
1. Öffne die CSV-Datei
2. Finde die Revenue-Spalte
3. Summiere nach Region
4. Schreibe einen Absatz
5. Speichere als report.docx
```

### ✅ Resilient (Outcome)

```
Analysiere die Sales-CSV. Erstelle ein Word-Dokument mit:
- Total Revenue nach Region
- Top-Region mit Erklärung
- Alle Data-Quality-Issues
Speichere als report.docx
```

**Wann anwenden**: Bei Tasks mit unsicherer Datenlage, unbekanntem Schema, explorativen Aufgaben.
**Wann nicht**: Bei compliance-pflichtigen, exakt reproduzierbaren Tasks (Security-Audit, Finanz-Reporting) — dort sind Prozeduren nötig.

### Code-Snippet für Skill-Ersteller

Wenn du einen Skill schreibst (`skill_manage(action='create')`), bevorzuge Outcome-Beschreibungen in der Description und vermeide über-spezifische Schritt-für-Schritt-Anleitungen ausserhalb des Body — der Skill-Description-Parser triggert stärker auf "was", nicht "wie".

## Pattern 2: NOTES.md / Persistent Notes

Bei langen agentischen Läufen schreibt der Agent **regelmäßig Notes außerhalb des Context Windows** auf Disk. Bei Hermes nutzen wir dafür `mnemosyne_remember` (nicht `NOTES.md`), aber das **Konzept** ist identisch: wichtiger Kontext überlebt Session-Wechsel.

### Wann Notes schreiben

Nach jedem **größeren Meilenstein** in einem langen Task:
- Sub-Agent-Batch abgeschlossen → Zusammenfassung in Mnemosyne
- Architekturentscheidung getroffen → `mnemosyne_triple_add` für die Relation
- Bug/Problem gelöst → Memory mit `source="lesson"` und `veracity="tool"`

### Wann Notes lesen

- Nach **Model-Wechsel** → `mnemosyne_recall(query="session context")`
- Bei **Ambiguity** → "Wurde X schon entschieden?"
- Vor **Gate** → "Haben wir alle offenen Punkte dokumentiert?"

### Vergleich: Disk-File vs Mnemosyne

| Aspekt | `NOTES.md` (Literatur) | `mnemosyne_remember` (Hermes) |
|---|---|---|
| Persistenz | Datei auf Disk | SQLite-Vektor-DB |
| Lesbar | Texteditor + Agent | FTS5/Vec-Suche |
| Struktur | Manuelle Markdown | Metadaten + Timestamps |
| Agent-Zugriff | `read_file` | `mnemosyne_recall` |
| **Empfehlung** | Für externe Artefakte (nicht internen Zustand) | Für Agenten-Gedächtnis |

## Pattern 3: Spec → Fresh Session

Der effektivste Pattern gegen Context Rot:

```
1. Lass den Agenten eine Spezifikation in SPEC.md schreiben
2. ✓ SPEC.md verifizieren
3. /new (frische Session)
4. Neue Session bekommt nur die Spec + Dateien
5. Fortschritt in plan.md / progress.md
```

**Vorteil**: Jede Session hat maximale Kapazität für die eigentliche Aufgabe.
**Nachteli**: Kein Gedächtnis der vorherigen Session — deswegen braucht man Pattern 2 (NOTES/Mnemosyne).

### Wann anwenden

- Task >30 Minuten Laufzeit oder >20 Tool-Calls erwartet
- Task wechselt die Domäne (z.B. von Research zu Implementation)
- Context-Budget zeigt >50% Auslastung bei Task-Start

## Pattern 4: Skill-Load als Session-Start-Hook

Hermes hat **keine nativen Session-Start-Hooks** (kein `on_session_start` Event,
kein Lifeycle-Trigger). Trotzdem kann man zuverlässig Code bei jeder neuen Session
ausführen — via **SOUL.md-mandated Skill-Loading**.

### Mechanismus

```yaml
# SOUL.md schreibt vor:
# - daily-briefing Skill wird bei jedem Session-Start geladen
# - Laden = Skill-Inhalt wird in System-Prompt injiziert
# - Skill kann Instruktionen enthalten die beim Laden assoziiert werden
```

Der Skill wird nicht nur geladen — sein **Inhalt wird Teil des System-Prompts**.
Das bedeutet: Instruktionen, Verhaltensregeln und Prüfungen im Skill-Body sind
bei jeder Session automatisch aktiv, ohne dass der User sie explizit aufruft.

### Anwendung bei Basti (2026-07-16)

Basti wollte eine Lösung für Tagesbericht-Reminder die NICHT an Cron-Fix-Zeiten
hängt (Laptop wird zu unterschiedlichen Zeiten beendet). Lösung: Statt Cron →
`daily-briefing` Skill um §0.9 erweitert. Der §0.9 führt beim Skill-Load einen
Daily-Note-Health-Check aus und hängt einen passiven Reminder-Satz ans Briefing.

**Vorteile gegenüber Cron:**
- Triggert EXAKT dann wenn der User da ist (Session-Start) — nicht wenn der Laptop aus ist
- Kein neuer Service/Daemon nötig
- Nutzt existierende Infrastruktur
- Leise und passiv (ein Satz im Briefing, keine Push-Notification)

**Voraussetzungen:**
- SOUL.md muss das Skill-Loading mandatieren (siehe Bastis SOUL.md §Session-Start:
  `skill_view(name='daily-briefing')` laden)
- Der Skill muss selbst-identifizierend sein (kein externer Trigger nötig)
- Der User-Agent muss den Skill-Rückgabewert aktiv in die erste Reply einbauen

### Pattern als generische Lösung

| Problem | Ohne Pattern | Mit Pattern |
|---------|-------------|-------------|
| "Erinnere mich an Tagesbericht" | Cron (fixe Zeit, Laptop aus) | Skill §X beim Session-Start |
| "Prüfe API-Key-Gültigkeit" | Manueller Befehl | Skill-Check läuft automatisch |
| "Sind Backups aktuell?" | Vergessen bis es zu spät ist | Skill-Kontrolle beim Start |
| "System-Audit fällig?" | Nur wenn dran gedacht wird | Skill evals beim Laden |

**Pitfalls:**
1. **Ein Satz-Regel brechen**: Der Hook ist ein passive Check, kein Task-Starter.
   Ein Satz Reminder, dann arbeiten lassen. Niemals den User mit einer Checkliste
   überfallen wenn er "was machen" will.
2. **Performance**: Der Skill-Check muss <0.5s sein (kein Network, kein heavy I/O).
   Sonst fühlt sich jede Session-Start träge an.
3. **Cross-Skill-ID**: SOUL.md referenziert den Skill beim Namen. Wenn der Skill
   umbenannt wird, muss SOUL.md mitaktualisiert werden.
4. **Kein Cron-Ersatz für zeitkritische Tasks**: Cron ist besser wenn etwas
   UM 06:00 passieren muss (Daily-Note erstellen). Skill-Hook ist besser wenn
   etwas passieren soll WENN der User da ist (Reminder, Checks).

### Cross-Reference

- `SOUL.md` (Basti's identity config) — §Session-Start definiert Skill-Loading
- `daily-briefing` Skill — §0.9 implementiert den Health-Check-Hook
- `plan-glm` Skill — spawned subprocess für komplexe Plan-Aufgaben
- Memory `b14b658422f017aa` — Stub-Heuristik (<1000 Bytes)

## Skill-Index: Wann welches Pattern?

| Situation | Skill |
|---|---|
| "Ich will ReAct-Labels + Reflexion" | `hermes-react-pattern` |
| "Context wird voll, ich brauche Management" | `hermes-context-budget` |
| "Ich will Outcome statt Prozedur" | Dieser Skill (Pattern 1) |
| "Wo langfristige Notes?" | Dieser Skill (Pattern 2) + `mnemosyne_remember` |
| "Task >15 Min — wie strukturieren?" | `multi-agent-master-workflow` |
| "Domain-spezifischer Plan" | `workflow-template` (5 Templates) |
| "Code-Implementierung mit Test" | `subagent-driven-development` |
| "Qualitäts-Gate vor Abschluss" | `critic-gate` |
| "Token sparen bei Tool-Output" | `context-mode` |
| "Brainstorming / Ideation" | `ideation` |
| "GitHub PR als Deliverable" | `github-pr-workflow` |

## Pitfalls

1. **Pattern-Shifting mitten im Task**: Nicht in einer laufenden Session von Outcome- auf Prozedur-Modus wechseln. Einmal angefangen → am Pattern bleiben.
2. **NOTES.md vs Mnemosyne verwechseln**: Im Hermes-Setup ist Mnemosyne das primäre Gedächtnis. `NOTES.md` nur für Artefakte, die der User selbst lesen will.
3. **Spec→Fresh-Session ohne Notes**: Wenn du die Spec-Session schliesst ohne Mnemosyne zu setzen, ist alles weg. Immer **vor** /new einen Memory-Call machen.
4. **Brücken-Skill nicht selbstständig einsetzen**: Dieser Skill ist **kein Worker**, sondern **Navigation**. Wenn du den triggert, erwarte nicht, dass er allein einen Task ausführt — er zeigt dir nur, welchen anderen Skill du brauchst.
