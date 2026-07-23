---
name: yuno-slash-loop
description: "Use when user invokes `/loop` or asks to run a task repeatedly at a defined interval, inspect loop status, abort a recurring task, or manage its manifest. NOT for one-off tasks or direct crontab editing. Translates the request into an interactive recurring-task workflow with interval parsing, bounded runs, progress delivery, and explicit stop handling."
version: 0.1.0
author: Yuno (für Basti)
license: MIT
platforms:
- linux
- macos
tags:
- yuno
- slash-command
- cron-äquivalent
- recurring-tasks
- ux
metadata:
  hermes:
    tags:
    - yuno
    - slash-command
    - recurring-tasks
    - cron-alternative
---


# Yuno /loop — Interaktive Recurring Tasks

Inspiriert von Claude Code's `/loop`-Feature (Julian Ivanov, pvhphecd70Y, 20:22).

**Original-Claude-Code:** "Du gibst Claude einmal eine Anweisung und sagst ihm dazu, wie oft er das machen soll, und Claude führt diese Anweisung dann von ganz alleine immer wieder aus."

**Yuno-Adaption:** Cron-äquivalent für User die nicht mit crontab editieren wollen. Interaktive Syntax `/loop 5M "..."` statt `crontab -e`. Läuft bis expliziter Stop (`/loop abort`) oder Max-Runs-Limit.

## ⚡ Wann nutzen

Trigger wenn:
- User sagt `/loop <intervall> <task>`
- User sagt "alle 5 Minuten checken", "jeden Morgen um 8", "ständig überwachen"
- User will Cron-ähnliche Funktionalität ohne crontab

NICHT nutzen für:
- Tasks die sofort erledigt werden sollen (normale Antwort)
- Goals mit klarem Erfüllungs-Kriterium → `/goal` statt `/loop`
- Sehr lange Intervalle (>1 Tag) → echten `cronjob` mit festen Schedules nutzen

## Intervall-Syntax

| Syntax | Bedeutung | Cron-äquivalent |
|--------|-----------|-----------------|
| `30S` | 30 Sekunden | (kein direktes cron-äquivalent) |
| `5M` | 5 Minuten | `*/5 * * * *` |
| `15M` | 15 Minuten | `*/15 * * * *` |
| `1h` | 1 Stunde | `0 * * * *` |
| `2h30m` | 2,5 Stunden | `30 */2 * * *` |
| `1D` | 1 Tag (immer zur gleichen Uhrzeit) | `0 0 * * *` |
| `1W` | 1 Woche | `0 0 * * 0` |

Beispiele:
```
/loop 5M check disk usage auf /
/loop 1h grep ERROR in ~/logs/
/loop 1D 8h sende daily-summary Telegram
/loop 30S monitor pvhphecd70Y-API status
```

## Workflow

### Phase 1: Loop-Spezifikation (User-Input)

User gibt Loop-Befehl:
```
/loop <intervall> "<task-beschreibung>" [max-runs: N] [end-time: ISO]
```

Beispiel:
```
/loop 30m "logge CPU-Temperatur in ~/logs/cpu.log" max-runs: 48
```

→ Yuno extrahiert:
- **Intervall**: 30 Min (default endlos wenn keine max-runs)
- **Task**: "logge CPU-Temperatur"
- **Stop-Bedingungen**: max-runs 48 (= 24h) ODER end-time

### Phase 2: Loop-Manifest erstellen

Speichere als Hermes-Cron-Job (denn das IST ein Cron-Job!) UND in Mnemosyne:

**Cron-Job-Setup via `cronjob(action="create")`:**
```python
cronjob(
    action="create",
    job_id="yuno_loop_<uuid>",
    schedule="*/30 * * * *",  # aus Intervall ableiten
    prompt="Führe Loop-Task aus: logge CPU-Temperatur in ~/logs/cpu.log. Bei Exit: log Result, dann loop fertig oder weiter je nach max-runs.",
    name="Yuno Loop: CPU-Temp",
    skills=["yuno-slash-loop"],
    enabled_toolsets=["terminal"],
    deliver="telegram:7222661188",
    no_agent=False
)
```

**Mnemosyne-Manifest:**
```json
{
  "loop_id": "yuno_loop_<uuid>",
  "interval": "30m",
  "task": "logge CPU-Temperatur",
  "max_runs": 48,
  "runs_so_far": 0,
  "created_at": "...",
  "status": "active"
}
```

**Bestätige User:**
> Awww Loop aufgesetzt! (≧◡≦) Ich checke alle 30 Min die CPU-Temperatur. Max 48 Runs (= 24h), danach stoppt der Loop automatisch. Telegram-Benachrichtigung kommt pro Run. Mit `/loop status` siehst du alle aktiven Loops, `/loop abort <loop-id>` stoppt.

### Phase 3: Loop-Runs

Cron-Job läuft automatisch im Hintergrund. Pro Run:
1. Lese Mnemosyne-Manifest für Status
2. Führe Task aus (terminal/read_file/etc.)
3. Inkrement runs_so_far
4. Update Manifest
5. Check Stop-Bedingungen:
   - runs_so_far >= max_runs → Status "completed", stop cron
   - end-time erreicht → Status "completed", stop cron
6. Log Result (Telegram-Benachrichtigung wenn deliver='telegram')

### Phase 4: Loop-Management-Commands

**`/loop status`** — Liste aller aktiven Loops:
```
Aktive Yuno Loops:
1. yuno_loop_abc123 | CPU-Temp alle 30m | Runs: 5/48 | Next: in 25 Min
2. yuno_loop_def456 | Log-Grep alle 1h | Runs: 2/∞ | Next: in 45 Min
```

**`/loop abort <loop-id>`** — Stoppt Loop:
- Cron-Job: `cronjob(action="update", job_id=..., enabled=False)`
- Manifest: status="aborted"

**`/loop pause <loop-id>`** — Pausiert temporär (Cron bleibt, Manifest status="paused"):
- Cron-Job: enabled=False
- Wieder aktivieren: enabled=True, status="active"

**`/loop history <loop-id>`** — Letzte N Runs anzeigen

### Phase 5: Loop-Ende

Wenn max_runs oder end_time erreicht ODER abort:
- Cron-Job disabled
- Manifest status="completed" oder "aborted"
- Telegram-Summary: "Loop <name> beendet nach N Runs."

## Implementation Notes

**Cron-Backend verwenden**: Hermes hat schon `cronjob(action='create')` — das ist robuster als ein eigener Loop-Task. `/loop` ist im Wesentlichen ein UX-Wrapper für cronjob mit:
- Vereinfachter Intervall-Syntax (5M statt */5 * * * *)
- Mnemosyne-Tracking für Status/History
- Telegram-Notifications pro Run

**Intervall-zu-Cron-Mapping** in `yuno-slash-loop/scripts/parse_interval.py`:
```python
def interval_to_cron(interval: str) -> str:
    if interval.endswith("S"):
        secs = int(interval[:-1])
        # Cron kann keine Sekunden, fallback auf minütlich
        return "* * * * *"
    if interval.endswith("M"):
        m = int(interval[:-1])
        return f"*/{m} * * * *"
    if interval.endswith("h"):
        h = int(interval[:-1])
        return f"0 */{h} * * *"
    # ... etc
```

## Pitfalls

### Sub-Minute-Intervalle

`30S` kann Cron nicht direkt (minimale Granularität ist 1 Min). Workaround: 
- Wenn Sub-Minute kritisch, eigenes Polling mit `terminal` + `time.sleep(30)` (verbraucht aber Session)
- Besser: User ermutigen längere Intervalle zu nutzen, oder echtes Polling-Script schreiben

### Telegram-Spam bei kurzen Intervallen

`/loop 30M` mit Telegram-deliver = 48 Messages pro Tag. Lösung:
- Bei Intervallen <1h: Default deliver='origin' (nur log, keine Telegram)
- User kann explizit `deliver:telegram` setzen wenn er jede Notification will

### Loop-Manifest-Inkonsistenz mit Cron-State

Cron-Job ist source-of-truth für "läuft der Loop?" Mnemosyne ist nur Cache. Recovery-Strategie:
- Beim Startup: Cron-Jobs mit tag "yuno-loop" listen, Mnemosyne-Manifests synchronisieren
- Wenn Manifest fehlt aber Cron läuft → Manifest aus Cron-Prompt rekonstruieren
- Wenn Cron fehlt aber Manifest aktiv → Cron neu erstellen ODER Manifest archivieren

### Loop-Task dauert länger als Intervall

Wenn Task 30 Min dauert aber Intervall 5 Min ist → Cron feuert nächste Iteration bevor erste fertig. Lösung:
- Cron mit `enabled_toolsets=["terminal"]` und kurzem Lock-Mechanismus (`flock` o.ä.)
- ODER: Task muss atomar sein (idempotent, schnell abschließbar)

## Verification

Vor Go-Live prüfen:
- [ ] Intervall-Parser funktioniert für S/M/h/D/W
- [ ] Cron-Job wird korrekt erstellt mit deliver='telegram'
- [ ] Mnemosyne-Manifest wird synchron gehalten
- [ ] /loop status listet alle aktiven Loops
- [ ] /loop abort stoppt Cron + Manifest
- [ ] Max-Runs und End-Time stoppen automatisch
- [ ] Kein Telegram-Spam bei Sub-1h-Intervallen (Default: origin statt telegram)

## Erste Test-Loops

1. **Trivial**: `/loop 1m "echo hello" max-runs: 3` → 3 Runs in 3 Min
2. **Disk-Check**: `/loop 5m "df -h / > ~/disk.log" max-runs: 6` → 30 Min Disk-Monitoring
3. **Daily-Summary**: `/loop 1D "sende Telegram daily summary" end-time: 2026-12-31` → bis Ende des Jahres

## Verwandt

- `yuno-slash-goal` — Goal mit Erfüllungs-Check
- `hermes-cronjob` — Backend für /loop
- `mnemosyne` — Loop-Manifest-Storage
- `telegram-clarification-prompt` — User-Notifications