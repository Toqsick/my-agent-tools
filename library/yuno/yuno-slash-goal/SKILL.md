---
name: yuno-slash-goal
description: |
  Use when you need to use the yuno-slash-goal workflow and its documented procedures.
  NOT for unrelated tasks outside the yuno-slash-goal workflow.
  Provides focused guidance for yuno-slash-goal.
version: 0.1.0
author: Yuno (für Basti)
license: MIT
platforms:
  - linux
  - macos
tags:
  - yuno
  - slash-command
  - goal-tracking
  - autonomous
  - multi-agent
metadata:
  hermes:
    tags:
    - yuno
    - slash-command
    - goal-tracking
    - autonomous
trigger_keywords: ['yuno', 'slash', 'goal', 'workflow', 'need']
keywords: ['yuno', 'slash', 'goal', 'workflow', 'need']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['voice-clone', 'github-workflow', 'multi-agent-pitfalls-cheatsheet']
---

# Yuno /goal — Autonomous Goal Completion

Inspiriert von Claude Code's `/goal`-Feature (Julian Ivanov, "Claude Code vom Handy für dich arbeiten lassen", pvhphecd70Y, 16:18).

**Original-Claude-Code:** "Set a goal, keep working until the condition is met."

**Yuno-Adaption:** Da Yuno interaktiv ist und mit Delegation arbeitet, ist `/goal` ein **Polling-Loop-Workflow** der einen Subagent pro Iteration dispatcht und nach jeder Iteration prüft ob die Goal-Bedingung erfüllt ist. Stoppt automatisch bei Erfüllung oder Max-Iter-Limit.

## ⚡ Wann nutzen

Trigger wenn:
- User explizit `/goal ...` sagt
- User sagt "arbeite bis X", "mach fertig", "iteriere bis"
- Task hat **klares Erfüllungs-Kriterium** das geprüft werden kann (Datei existiert, Tests grün, API antwortet, etc.)

NICHT nutzen für:
- Einmalige triviale Tasks (z.B. "was ist die Hauptstadt von Frankreich") — normale Antwort reicht
- Tasks ohne prüfbares Erfüllungs-Kriterium (z.B. "verbessere die Architektur") — wäre endlos
- Tasks wo User sofortige Antwort braucht

## Workflow

### Phase 1: Goal-Spezifikation (User-Input)

User gibt Goal in einer von zwei Formen:

**Form A — Explizite Syntax:**
```
/goal <bedingung> | max-iter: <N> | timeout: <T>
```

Beispiel:
```
/goal Alle Tests grün im greyhack-tools/ pytest | max-iter: 10 | timeout: 30m
```

**Form B — Natürlichsprachlich:**
```
/goal Bring das greyhack-tools pytest zum Laufen
```

→ Yuno extrahiert daraus:
- **Goal-Bedingung**: "Alle Tests grün"
- **Check-Methode**: "pytest ausführen, Exit-Code 0"
- **Max-Iter**: default 10
- **Timeout**: default 60m (oder aus Goal-Wortlaut ableiten)

### Phase 2: Goal-Manifest erstellen

Speichere ein Goal-Manifest als Memory (Mnemosyne) und in `/tmp/yuno_goals/<goal-id>.json`:

```json
{
  "goal_id": "uuid",
  "description": "Alle Tests grün im greyhack-tools/ pytest",
  "check_method": "cd ~/10-Projekte/10-active/greyhack-tools && pytest",
  "check_expected": {"exit_code": 0},
  "max_iter": 10,
  "timeout_seconds": 1800,
  "created_at": "2026-07-09T...",
  "current_iter": 0,
  "history": []
}
```

Bestätige User mit Goal-Manifest:
> Awww Goal aufgesetzt! (≧◡≦) Ich arbeite jetzt bis **alle Tests grün sind im greyhack-tools/ pytest**. Max 10 Iterationen, Timeout 30 Min. Wenn ich fertig bin (oder aufgeben muss), schick ich dir ne Telegram-Nachricht. Mit `/goal status` siehst du den aktuellen Stand.

### Phase 3: Iteration-Loop (Hauptphase)

Pro Iteration:

1. **Read Goal-Manifest** + letzte History
2. **Plan**: Was kann ich diese Iteration tun um Goal näher zu kommen? Lese Code, prüfe Logs, identifiziere nächsten Schritt
3. **Execute**: Arbeite am Plan (eigene Tools ODER `delegate_task` wenn zu groß)
4. **Check**: Führe `check_method` aus
   - **Erfüllt** → Phase 4 (Success-Notification)
   - **Nicht erfüllt** → Log Iteration-Result in Manifest, inkrement current_iter, gehe zu 1
5. **Context-Reset**: Nach jeder Iteration `mnemosyne_sleep` laufen lassen (Memory-Compaction) — sonst läuft Kontext voll
6. **Max-Iter / Timeout**: Wenn erreicht → Phase 5 (Failure-Notification mit History)

### Phase 4: Success-Notification

Wenn Goal erfüllt:

```
🎯 GOAL ERREICHT nach N Iterationen!

Goal: <description>
Check: <check_method> → Exit 0
Iterationen:
  1. <was wurde gemacht>
  2. <was wurde gemacht>
  ...
  
Memory-Update: Manifest gespeichert in ~/.hermes/yuno_goals/<goal-id>.json
```

→ Telegram-DM an Basti (`telegram:7222661188`) mit Goal-Summary

### Phase 5: Failure-Notification

Wenn Max-Iter oder Timeout erreicht ohne Erfüllung:

```
⚠️ GOAL NICHT ERREICHT nach N Iterationen / T Min

Goal: <description>
Letzter Check: <output>
Letzter Versuch: <was wurde probiert>

Was ich brauche:
- User-Input: weiter versuchen? Goal anpassen? Abbrechen?
- Bei "weiter": `/goal continue <goal-id>`
- Bei "anpassen": `/goal <neue-bedingung>`
```

→ Telegram-DM mit Failure-Report + 3 Optionen für Basti

## Implementation Notes

**Goal-Manifest-Storage**: 
- Primary: Mnemosyne Memory mit hoher Importance (1.0) und `goal-tracking` tag
- Secondary: `/tmp/yuno_goals/<goal-id>.json` für schnellen Zugriff + Recovery

**Polling-Loop** ist ein interner Hermes-Workflow, NICHT ein externer Cron. Pro Iteration:
- `delegate_task` für nicht-triviale Sub-Tasks
- Direktes Tool-Calling für Checks (`terminal`, `read_file`)
- Nach max-3 Iterations oder 10 Min → User Status-Update ("bin noch dabei, 3/10 Iter")

**Context-Management**: 
- `/compact`-äquivalent in Yuno = `mnemosyne_sleep()` zwischen Iterationen
- Goal-Manifest bleibt erhalten (es IST die Session-State)
- History im Manifest speichert letzte N Iterations für Re-entry

## Pitfalls

### Goal zu vage → Endlos-Loop

Schlecht: "mach das System besser"
Gut: "Reduce P99-Latency von <endpoint> auf <50ms" (mit prüfbarem Check)

Wenn Goal unklar: Frage User **vor** Iteration-Start: "Was heißt 'fertig'? Konkretes Kriterium?"

### Check-Methode nicht idempotent

Wenn `check_method` selbst Side-Effects hat (z.B. DB-Migration), führt jede Iteration die Side-Effects aus. Lösung: Check-Methode muss READ-ONLY sein. Sonst vor jedem Check Snapshot machen.

### Subagent-Failure verschluckt

Wenn `delegate_task` failed, Iteration muss als "failed" markiert werden und im History sichtbar sein. Nicht als "Fortschritt" werten.

### Goal-Achievement ist binär, nicht graduell

Anders als LLM-Training ist /goal binär: erfüllt oder nicht. Nicht "90% erreicht" werten. Lieber neue Goal definieren: "von 90% auf 100%".

## Verification

Vor Go-Live prüfen:
- [ ] Goal-Manifest wird korrekt gespeichert
- [ ] Check-Methode ist idempotent
- [ ] Max-Iter greift
- [ ] Timeout greift
- [ ] Telegram-DM funktioniert
- [ ] Goal-Manifest-Recovery nach Crash funktioniert (Mnemosyne)
- [ ] Mnemosyne-Sleep zwischen Iterations verhindert Context-Bloat
- [ ] User kann Goal pausieren, fortsetzen, abbrechen via `/goal status`, `/goal continue`, `/goal abort`

## Erste Test-Goals (nach Installation)

1. **Trivial-Test**: `/goal echo hello-world | max-iter: 1` → sofort erfüllt
2. **Einfacher Datei-Test**: `/goal Datei ~/tmp/test.txt existiert und enthält "Yuno" | max-iter: 3`
3. **Real-World-Test**: `/goal Alle pytest Tests grün in ~/10-Projekte/10-active/greyhack-tools | max-iter: 10 | timeout: 30m`

## Verwandt

- `yuno-slash-loop` — Wiederkehrende Tasks (cron-äquivalent)
- `yuno-system-documentation` — Goal-Iterationen dokumentieren
- `hermes-cronjob` — Für fixe Schedules (nicht für Goal-Completion)
- `mnemosyne` — Goal-Manifest-Storage