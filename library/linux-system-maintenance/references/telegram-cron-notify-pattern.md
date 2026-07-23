# Telegram-Notify Pattern für Bash-Cron-Jobs

> **Gelernt 2026-07-17:** Bei der Erstellung von 4 Audit-Cron-Wächtern fiel auf:
> `hermes send_message` existiert NICHT als CLI-Subcommand. Der korrekte Weg ist
> `source $HOME/.hermes/.env` + `curl` zur Telegram-Bot-API — exakt wie es
> `daily-note-cron.sh`, `mnemosyne-monthly-cleanup.sh` und `yuno-cleaner-cron.sh`
> bereits machen.

## Das Pattern

```bash
#!/bin/bash
# WRAPPER: <script-name>.sh — <Zweck>
set -euo pipefail

LOG_FILE="/home/bratan/logs/<script-name>.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# ... Logik die einen Alert triggert ...
if [ "$SOME_CONDITION" = "trigger" ]; then
    MSG="⚠️ <Warning-Text>"

    # Telegram-Notification via curl (Bot-Token aus .hermes/.env)
    set +u
    if [ -f "$HOME/.hermes/.env" ]; then
        source "$HOME/.hermes/.env"
        if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_HOME_CHANNEL:-}" ]; then
            curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
                -d "chat_id=${TELEGRAM_HOME_CHANNEL}" \
                -d "text=${MSG}" > /dev/null 2>&1 || echo "[$TIMESTAMP] WARN: Telegram-Send fehlgeschlagen" >> "$LOG_FILE"
        fi
    fi
    set -u
fi
```

## Wichtige Details

| Aspekt | Pattern | Erklärung |
|--------|---------|-----------|
| **Env-Sourcing** | `source "$HOME/.hermes/.env"` | `.env` enthält `TELEGRAM_BOT_TOKEN` + `TELEGRAM_HOME_CHANNEL` |
| **Unbound-Var-Guard** | `set +u` / `set -u` | `.env` hat nicht zwingend beide Vars; ohne `set +u` bricht das Skript bei fehlendem Token |
| **Fallback-Check** | `${TELEGRAM_BOT_TOKEN:-}` | Leere Vars erzeugen keinen curl-Call |
| **Silent-Fail** | `> /dev/null 2>&1 \|\| echo "WARN"` | curl-Fehler (Netzwerk, falscher Token) killen nicht das gesamte Skript |
| **Kein `hermes send_message`** | ❌ Existiert nicht | `hermes` CLI hat kein `send_message` Subcommand |

## Crontab-Einbindung

```bash
# In crontab: Output ins Log, stderr auch
0 22 * * * /home/bratan/50-System/bin/<script>.sh >> /home/bratan/logs/<script>.log 2>&1
```

NICHT: `hermes cron create` (das würde eine Session starten, nicht ein Bash-Script).

## Quellen / Bewährte Implementierungen

| Script | Seit | Telegram-Send-Pattern |
|---|---|---|
| `daily-note-cron.sh` | 2026-06 | `source .env` + curl + `TELEGRAM_HOME_CHANNEL` |
| `mnemosyne-monthly-cleanup.sh` | 2026-07 | `source .env` + curl + `TELEGRAM_BOT_TOKEN` |
| `disk-space-monitor.sh` | 2026-07-17 | `source .env` + curl + silent-fail |
| `logrotate-health.sh` | 2026-07-17 | `source .env` + curl + silent-fail |
| `agents-md-drift-check.sh` | 2026-07-17 | `source .env` + curl + silent-fail |

## Anti-Patterns

- ❌ `hermes send_message ...` — führt zu `usage: hermes [-h] ...` ohne Aktion
- ❌ `command -v hermes` als Gate — `hermes` ist installiert, hat aber nicht das Subcommand
- ❌ Token direkt in Crontab — gehört in `~/.hermes/.env` (Working-Agreement §7)
- ❌ Telegram-Benachrichtigung abhängig von cron-session-check — der Cron-Job muss seinen eigenen Env-Zugriff haben
