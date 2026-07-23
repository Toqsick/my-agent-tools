# Phase 11: Vault Cron Automation

> **Cron-gesteuerte Vault-Lebendigkeit.** Nachdem der Vault strukturell gewachsen ist (Phase 1-10), wird er durch automatisierte Cron-Skripte lebendig: tägliche Notes, wöchentliche Digests, Mnemosyne-Sleep.

## Trigger Conditions

- "Automate my daily notes"
- "Cron jobs for vault"
- "Weekly vault digest"
- "Vault temporal awareness"
- "Make the vault alive / lebendig"
- "Phase 11"

Requires: Phase 1-10 complete, vault structure stable, user has confirmed "go" für Cron-Integration.

## Pattern 1: Daily Note Cron with Plain Placeholders

**Kern-Pattern:** `daily-note-cron.sh` — idempotent, läuft 06:00 täglich.

**Placeholder-Strategie (wichtigster Lesson-Learned):**
- **NICHT** Templater `<% tp.date.now(...) %>` — braucht Plugin 1.13.0+ (lokal 1.12.7 → Mismatch)
- **Plain Placeholder** `{{date}}` und `{{session_id}}` im Template
- **sed-Ersetzung** im Cron-Skript: `sed -i "s/{{date}}/$DATE/g; s/{{session_id}}/$SESSION_ID/g" "$TARGET"`
- `session_id = date +%Y%m%d-%H%M` — eindeutig pro Cron-Tick

**Idempotenz:** `if [ -f "$TARGET" ]; then exit 0; fi` als erste Aktion nach dem Date-Check. Nie doppelte Notes.

**Template-Beispiel (Plain-Format):**
```markdown
---
tags:
  - daily
  - journal
datum: {{date}}
session-id: {{session_id}}
modell: MiniMax-M3
stimmung:
---
```

## Pattern 2: Weekly Digest with flock + mnemosyne_sleep

**Kern-Pattern:** `weekly-digest-cron.sh` — Sonntags 22:00, erstellt Weekly-Digest + trigger Mnemosyne-Sleep.

**flock-Idempotenz für Langläufer:**
```bash
exec 9>/tmp/weekly-digest-cron.lock
if ! flock -n 9; then
    exit 0  # Voriger Run läuft noch — silent skip
fi
```

**mnemosyne_sleep-Aufruf (best-effort):**
```bash
if command -v mnemosyne_sleep >/dev/null 2>&1; then
    mnemosyne_sleep 2>/dev/null || true
fi
```

⚠️ **Flag-Pitfall:** `mnemosyne_sleep` akzeptiert KEIN `all_sessions=true dry_run=false` — halluzinierte Flags. Plain `mnemosyne_sleep` = Default-Real-Run. `|| true` = failsafe wenn CLI nicht verfügbar.

**Self-List-Pitfall:**
Wenn der Digest ins gleiche Verzeichnis schreibt wo er auch liest (z.B. `find "$VAULT" -name "*.md"` → erstellt Digest mit `.md` → nächster Run listet den Digest selbst), dann MUSS ein Filter:
```bash
find "$VAULT" -name "*.md" -mtime -7 \
    -not -name "Weekly-Digest-*.md" \
    2>/dev/null | sort | while read -r f; do ...
```

## Pattern 3: Atomic Crontab Update

**NICHT** mit `crontab -e` (interaktiv, hängt). **NICHT** mit echo + Pipe (überschreibt alles). **RICHTIG:**
```bash
(crontab -l; echo "0 6 * * * /path/to/script.sh >> /tmp/log.log 2>&1") | crontab -
```
Das hängt die neue Regel AN die bestehenden an → atomischer Replace. Backup vorher:
```bash
crontab -l > ~/50-System/backups/crontab-pre-$(date +%Y%m%d_%H%M%S).bak
```

**Verifikation nach Update:** `crontab -l | grep -cE "^[0-9*@]"` → zählt Jobs.

## Pattern 4: Telegram Notification Pattern (Working Agreement §7)

- **Token NEVER inline** — via `source "$HOME/.hermes/.env"` (WA §7)
- **Silent on success** — kein Telegram-Ping wenn Skript durchläuft
- **Alert on fail** — `trap` + Telegram-Curl bei Fehler:

```bash
send_alert() {
    local msg="$1"
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_HOME_CHANNEL:-}" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_HOME_CHANNEL}" \
            -d "text=${msg}" > /dev/null || true
    fi
}
trap 'send_alert "SCRIPT FAIL: line ${LINENO} exit $?"' ERR
```