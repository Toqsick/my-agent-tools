# CLI News-Watchdog Pattern (Poll-Driven Update-Detection)

**Stand:** 2026-07-05 (Basti Gemini/Antigravity Session)
**Use-Case:** Auf eine externe Migration/Deprecation/Launch warten, ohne selbst aktiv zu pollen — der Agent soll dich benachrichtigen sobald sich was ändert.

## Wann dieses Pattern?

Wenn ein Vendor:
- Einen **Login-Weg deprecated** (z.B. Google Gemini Code Assist OAuth → Antigravity)
- Eine **neue Produkt-Linie launcht** die den alten Weg ersetzt
- **Breaking Changes** ankündigt, deren konkrete Form noch unklar ist

Du willst nicht alle 2 Tage selbst die Vendor-Page checken, aber du willst die Info **sobald sie da ist** — auf Telegram, ohne Polling-Aufwand, ohne LLM-Tokens.

## Pattern in 5 Bausteinen

### 1. Watchdog-Skript (kein LLM, nur curl + Hash)

```bash
#!/bin/bash
# ~/.hermes/scripts/<topic>-watchdog.sh
set -euo pipefail

STATE_DIR="$HOME/.cache/<topic>-watchdog"
mkdir -p "$STATE_DIR"
LAST_HASH_FILE="$STATE_DIR/last_status_hash"

SOURCES=(
  "https://vendor-official-page"
  "https://github.com/vendor/repo/releases"
)

STATUS=""
for url in "${SOURCES[@]}"; do
  http=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 15 -L "$url" 2>/dev/null || echo 000)
  title=$(curl -sS --max-time 15 -L "$url" 2>/dev/null \
          | grep -oP '<title>\K[^<]+' | head -1 | tr -d '\n' || echo "<no-title>")
  STATUS+="{\"url\":\"$url\",\"http\":$http,\"title\":\"$title\"},"
done
STATUS="[${STATUS%,}]"
HASH=$(echo -n "$STATUS" | sha256sum | cut -c1-16)

OLD_HASH=""
[ -f "$LAST_HASH_FILE" ] && OLD_HASH=$(cat "$LAST_HASH_FILE")

# Silent exit wenn nichts geändert
if [ "$HASH" = "$OLD_HASH" ]; then
  exit 0
fi

# Output wird per Cron an Telegram geliefert
echo "$STATUS" | head -c 500
echo
echo "Hash: alt=$OLD_HASH neu=$HASH"
echo "$HASH" > "$LAST_HASH_FILE"
```

**Warum Hash und nicht Last-Modified?** Manche Vendor-Pages ändern sich ohne Last-Modified-Header (CDN-cached, dynamisch gerendert). Hash der Title + HTTP-Code Kombination ist robuster.

### 2. Cron mit `no_agent=true`

```bash
cronjob(action='create',
  name='<topic>-watchdog',
  schedule='0 10 * * 0',          # wöchentlich Sonntag 10 Uhr
  script='<topic>-watchdog.sh',   # MUSS in ~/.hermes/scripts/ liegen, kein absoluter Pfad
  no_agent=True,
  deliver='telegram:7222661188')
```

**Pitfalls die die Cron-Registrierung kippen:**
- Absoluter Pfad (`~/.hermes/scripts/foo.sh`) → **FAIL**. Nur Filename, das Skript MUSS in `~/.hermes/scripts/` sein.
- `prompt` mit gesetztem `no_agent=true` → **FAIL**. Entweder LLM oder Script, nicht beides.
- Script-Permissions: `chmod +x` muss vorher gemacht sein.

### 3. Silent-on-no-change Verhalten

`exit 0` mit leerem stdout = Cron deliver nichts. Das ist das gewollte Watchdog-Verhalten — User kriegt nur dann Telegram wenn sich Source-Inhalt ändert.

### 4. Erst-Lauf Init

Beim ersten Lauf ist `OLD_HASH` leer → Skript meldet "init". Das ist OK und hilfreich: User sieht einmalig dass das Watchdog aktiv ist. Danach 7 Tage still, dann nächste Sonntagsmeldung wenn was news ist.

### 5. Manueller Trigger zum Testen

```bash
# Direkt ausführen:
bash ~/.hermes/scripts/<topic>-watchdog.sh

# Status aller Crons:
cronjob(action='list')

# Job sofort triggern (statt auf Schedule zu warten):
cronjob(action='run', job_id='<id-aus-list>')
```

## Pitfalls

| Problem | Fix |
|---|---|
| Cron liefert jeden Lauf Output | `OLD_HASH`/`NEW_HASH` Vergleich im Skript fehlt — beide Pfade ohne Output auf exit 0 |
| Watchdog-Output zu lang (>4096 char Telegram-Limit) | `head -c 500` oder relevante Felder extrahieren, nicht full HTML |
| `code_challenge`/OAuth-Token expired im Watchdog | Watchdog-Skript sollte nur lesen, nie eigene Auth-Flows triggern. Wenn die Quellen selbst hinter Login sind → RSS-Feed oder Status-Page bevorzugen |
| Hash ändert sich bei jedem Lauf obwohl Inhalt gleich | Page hat Timestamp oder Random-ID im HTML. `grep -oP '<title>\K[^<]+'` ist stabiler als full-page hash |
| User will weniger Spam | Intervall erhöhen (`0 10 * * 0` = wöchentlich statt `0 * * * *` = stündlich) |

## Konkretes Beispiel: Antigravity-Watchdog

Siehe `~/.hermes/scripts/antigravity-watchdog.sh` (für Bastis Gemini-Code-Assist-Deprecation-Wait). Cron-Job-ID: `79f08e78c5a6`. Schedule: So 10:00, deliver an Telegram 7222661188.

Quellen:
- `https://antigravity.google` (offizielle Landing-Page)
- `https://github.com/google-gemini/gemini-cli/releases` (CLI-Release-Notes)

Wenn sich Title oder HTTP-Status ändert → Telegram-Notification. Sonst still.

## Verwandte Patterns

- **Push-driven** (Webhook): siehe `webhook-subscriptions` Skill — passt wenn der Vendor echte Webhooks anbietet
- **LLM-driven Cron**: `cronjob(action='create', prompt='...', skills=[...])` — passt wenn Reasoning nötig ist (z.B. RSS-Items zusammenfassen)
- **Filesystem-Watch**: `inotifywait`/`fswatch` — passt wenn lokale Datei-Änderungen überwacht werden sollen