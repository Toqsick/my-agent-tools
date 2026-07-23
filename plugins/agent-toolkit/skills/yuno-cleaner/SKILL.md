---
name: yuno-cleaner
description: "Use when user asks to run Yuno Cleaner for a Linux scan, cleanup, status check, scheduled cleanup, JSON report, Telegram notification, or handoff. NOT for destructive cleanup without the tool’s safety flow or app-specific uninstall work. Provides the Hermes integration, command forms, dry/report modes, scheduling, and safety guardrails."
version: '1.1'
author: Basti
license: MIT
lane: worker-flash
reasoning_effort: high
---


# Yuno Cleaner Skill

Integration von `~/yuno-cleaner/` als Hermes-Skill. Erlaubt Aufrufe direkt aus dem Chat.

## Verwendung

```
User: "yuno scan"
      "yuno clean"
      "yuno status"
      "yuno schedule weekly"
      "yuno handoff"
```

## Commands

| Befehl | Was passiert |
|--------|-------------|
| `yuno scan` | Dry-Run Scan aller Kategorien |
| `yuno scan system` | Nur System-Junk |
| `yuno scan browser` | Nur Browser-Cache |
| `yuno scan gaming` | Nur Gaming-Junk |
| `yuno scan large` | Große Dateien finden |
| `yuno clean` | Cleanup mit Bestätigung + Backup |
| `yuno status` | System-Status (Platte, RAM, CPU) |
| `yuno schedule weekly` | Auto-Cron einrichten |
| `yuno handoff` | Modell-Handoff generieren |
| `yuno scan --json` | Ergebnis als JSON auf stdout (skriptbar, unterdrückt TUI) |
| `yuno scan --notify` | Telegram-Report senden nach Scan |

### `--json` Output-Modus
Unterdrückt rich-TUI-Ausgabe, gibt valides JSON auf stdout.
Nützlich für Cron-Jobs, Skripte, und API-Integrations.
Beispiel: `python3 yuno_cleaner.py scan --json --category system`

### `--notify` Telegram-Report
Sendet kompakte Zusammenfassung per Telegram an User.
Benötigt `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` in Umgebungsvariablen.
Telegram-Helper: `~/yuno-cleaner/telegram_helper.py` (stdlib-only, urllib).

### Cron-Job mit Telegram-Report
```
0 3 * * 0 TELEGRAM_BOT_TOKEN=*** TELEGRAM_CHAT_ID=*** \
  cd /home/bratan/yuno-cleaner && \
  python3 yuno_cleaner.py scan --dry-run --notify >> /tmp/yuno-cleaner.log 2>&1
```
Läuft jeden Sonntag 03:00, sendet Report automatisch per Telegram.

## Implementierung

Der Skill ruft `~/yuno-cleaner/yuno_cleaner.py` als Subprozess auf:

```python
import subprocess

def yuno_scan(category="all"):
    result = subprocess.run(
        ["python3", "/home/bratan/yuno-cleaner/yuno_cleaner.py", "scan", "--category", category],
        capture_output=True, text=True
    )
    return result.stdout
```

## Safety

- **scan** = immer Dry-Run, niemals löschend
- **clean** = fragt nach Bestätigung, erstellt Backup
- **schedule** = richtet nur Dry-Run Cron ein
- **handoff** = generiert nur Dokumente, ändert nichts am System

## Pitfalls

1. **shutil.disk_usage hat kein `.percent`-Attribut.** Berechne immer manuell: `disk.used / disk.total * 100`
2. **Backticks in f-strings verursachen SyntaxError.** Niemals `\`${var}\`` in f-Strings verwenden.
3. **Patch vs execute_code:** Bei komplexen Multi-Replacement Änderungen ist `execute_code` mit Python file I/O zuverlässiger als `patch`.

## Abhängigkeiten

- Python 3.10+
- `rich` (Terminal-UI)
- `psutil` (System-Info)
- Projekt unter `~/yuno-cleaner/`
