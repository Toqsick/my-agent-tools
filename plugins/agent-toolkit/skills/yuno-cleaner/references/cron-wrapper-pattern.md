# Yuno Cleaner — Crontab-Sicherheit & ENV-Mapping

> Gelernt 2026-07-05: Working-Agreement §7 konsequent umgesetzt.

## Problem

Crontab-Eintrag enthielt `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` im Klartext in
`/var/spool/cron/crontabs/bratan`. Bei jedem `crontab -l` und jedem Backup waren
die Secrets lesbar.

## Lösung: Wrapper-Pattern

1. Wrapper-Skript in `~/50-System/bin/yuno-cleaner-cron.sh`
2. Wrapper sourced `~/.hermes/.env` (Single-Source-of-Truth)
3. Mappt `TELEGRAM_HOME_CHANNEL → TELEGRAM_CHAT_ID`
4. Ruft `yuno_cleaner.py scan --dry-run --notify` auf
5. Crontab enthält nur Pfad-Referenz, keine Tokens

## Verification

```bash
# Cron-Modus-Test (ohne Login-ENV):
env -i HOME="$HOME" PATH="/usr/bin:/bin" \
  bash -c 'set -a; . "$HOME/.hermes/.env"; set +a; [ -n "${TELEGRAM_HOME_CHANNEL:-}" ] && [ -z "${TELEGRAM_CHAT_ID:-}" ] && export TELEGRAM_CHAT_ID="$TELEGRAM_HOME_CHANNEL"; echo "$TELEGRAM_CHAT_ID"'

# Pattern-Check: keine Secrets in Crontab?
crontab -l | grep -E "(bot|Token|BOT_TOKEN|CHAT_ID|\"[0-9]{6,}\")" || echo "clean"
```

## Verwandte Skills

- `linux-system-maintenance/references/crontab-safety-patterns.md`
- `yuno-cleaner/SKILL.md` — Cron-Job-Abschnitt
