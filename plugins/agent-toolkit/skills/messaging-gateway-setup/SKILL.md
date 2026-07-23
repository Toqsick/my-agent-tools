---
name: messaging-gateway-setup
description: >-
  Use when user asks for setting up Telegram, WhatsApp, Discord, Signal, or Matrix, configuring the Hermes messaging gateway, checking or restarting gateway status, or removing a messaging platform safely. NOT for sending routine chat messages or changing model-provider configuration. Guides platform setup, environment and persisted-state cleanup, lifecycle commands, and connection verification.
version: 1.2.0
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - gateway
    - telegram
    - discord
    - whatsapp
    - signal
    - setup
    - messaging
author: Hermes Agent
license: MIT
lane: worker-flash
reasoning_effort: high
---


# Messaging Gateway Setup

Set up and configure Hermes for messaging platforms. Each platform has unique requirements, auth flows, and quirks.

## Quick Reference

```bash

set -euo pipefail
# Interactive setup wizard
hermes gateway setup

# Start/stop/restart
hermes gateway install      # install as systemd service
hermes gateway start/stop/restart

# Check status
hermes gateway status
```

## Platform-Specific Setup

### Telegram

1. Create bot via @BotFather on Telegram → get token
2. Configure in Hermes: `hermes gateway setup` → select Telegram
3. **CRITICAL: Allow user access** — Telegram uses a different mechanism than other platforms:

   Set the env var (NOT the `dm_policy` config, which doesn't work for Telegram):
   ```bash

set -euo pipefail
   echo "TELEGRAM_ALLOWED_USERS=123456789" >> ~/.hermes/.env
   ```

   Multiple users: comma-separated. Wildcard `*` allows everyone.

   Then restart:
   ```bash

set -euo pipefail
   hermes gateway restart
   ```

4. **Common error:** If you see "Unauthorized user" in logs, the env var isn't set or doesn't include your user ID.

5. **Home channel error:** If you see `invalid literal for int() with base 10: '@UsernameBot'`, the home channel config uses the bot username instead of numeric chat ID. Fix by finding the correct numeric chat ID and updating the config.

### WhatsApp

1. Configure: `hermes gateway setup` → select WhatsApp
2. **REQUIRES INTERACTIVE TERMINAL:** The pairing command cannot run in pipe/non-interactive subprocess:
   ```bash

set -euo pipefail
   hermes gateway stop          # stop gateway first
   hermes whatsapp              # shows QR code in terminal
   ```
3. Scan QR code with WhatsApp: Settings → Linked Devices → Link Device
4. Start gateway: `hermes gateway start`

### Discord

1. Create bot at https://discord.com/developers/applications
2. Click **"New Application"** → name it → **"Bot"** → **"Add Bot"**
3. Under the Bot tab, **Reset Token** then **Copy** — this is the token, NOT the Application ID or Public Key from General Information
4. Enable **Privileged Gateway Intents**: **Message Content Intent** (critical — without it the bot sees NO messages), Server Members Intent (optional), Presence Intent (optional)
5. Add bot to server via OAuth2 URL Generator:
   - **Scopes:** `bot` + `applications.commands`
   - **Bot Permissions:** Send Messages, Read Messages, Read Message History, Attach Files, Embed Links
   - Open the generated URL → select server → Authorize
6. Set token in Hermes:
   ```bash

set -euo pipefail
   echo "DISCORD_BOT_TOKEN=your_token_here" >> ~/.hermes/.env
   hermes gateway restart
   ```
7. Verify connection in logs:
   ```bash

set -euo pipefail
   grep -i "discord" ~/.hermes/logs/gateway.log
   # Look for: "[Discord] Registered /skill command with N skill(s)" → token works
   # Look for: "Connected to discord..." → full connection
   ```

**Pitfalls:**
- **Token vs Application ID:** The Discord Developer Portal shows Application ID and Public Key on the first page. The Bot Token is ONLY under the "Bot" tab. The token has dots (e.g., `MTUx...abc.def.ghi` format, ~70 chars, 2 dots separating 3 sections). Application ID is a plain number without dots.
- **Connection timeout after setup:** The gateway registers slash commands first, then establishes the WebSocket. Initial timeout (`discord connect timed out after 30s`) is normal — the reconnection watcher retries every 60 seconds and usually succeeds within 2-3 attempts. The gateway log will say `Reconnecting discord (attempt N)...`.
- **If the bot never connects:** Check if the server has WebSocket connectivity to `gateway.discord.gg:443`. Test with: `timeout 5 bash -c 'echo | openssl s_client -connect gateway.discord.gg:443 -servername gateway.discord.gg 2>&1 | grep CONNECTED'`. SSL handshake success = network is fine.
- **⚠️ Token Reset requires OAuth2 Re-Invite (4004 Crash):** If you regenerate the bot token in Discord Developer Portal (Bot → Reset Token), the old OAuth2 invite URL is invalidated. Even with the correct new token in `.env`, the gateway crashes with `WebSocket closed with 4004` (`Authentication failed`). The bot was authorized on the server with the OLD token; the new token has no authorization.

  **Fix:**
  1. Go to Discord Developer Portal → OAuth2 → URL Generator
  2. Scopes: `bot` + `applications.commands`
  3. Permissions: Send Messages, Read Messages, Read Message History, Attach Files, Embed Links
  4. Open generated URL → select server → Authorize (the bot already exists, this re-links the new token)
  5. Restart gateway: `systemctl --user restart hermes-gateway.service`
  6. Verify: `grep -i "discord" ~/.hermes/logs/gateway.log` → look for `Connected to discord`

  **Do NOT** delete and re-create the bot application. This would require re-configuring all intents, permissions, and re-inviting. Just re-authorize via OAuth2.
- **Missing Message Content Intent:** The bot will show as online but never see messages. Go back to Discord Developer Portal → Bot → toggle ON "Message Content Intent".

### Signal / Matrix / Other Platforms

Use `hermes gateway setup` — the interactive wizard walks through each platform's specific requirements.

## Removing a Platform

To fully disconnect and remove a messaging platform from Hermes Gateway:

### 1. Remove Config Entries

Edit `~/.hermes/config.yaml` and remove all references to the platform:

- **Top-level platform block** — e.g. `whatsapp: {}`, `signal: {…}`
- **`disabled_toolsets` section** — if the platform appears there
- **`platform_toolsets` section** — the entire per-platform tool list

```bash

set -euo pipefail
# Use hermes config edit for safety (or python3/sed if you know the exact keys)
hermes config edit
```

### 2. Remove Environment Variables

Edit `~/.hermes/.env` and delete all vars for the platform:

- **Enable flag** — e.g. `WHATSAPP_ENABLED=true`, signalling the gateway to try connecting
- **Tokens & credentials** — `TELEGRAM_BOT_TOKEN`, `DISCORD_BOT_TOKEN`, `SLACK_BOT_TOKEN`, etc.
- **Home channel config** — `WHATSAPP_HOME_CHANNEL`, `WHATSAPP_HOME_CHANNEL_THREAD_ID`
- **Access control** — `WHATSAPP_ALLOWED_USERS`, platform-specific mode flags

### 3. Clean Up Persisted Gateway State (⚠️ Critical Pitfall)

The gateway persists platform health to `~/.hermes/gateway_state.json`. Simply removing config + env vars does **not** clear old fatal/error states — the new gateway process never calls `connect()` for the removed platform, so it never overwrites the stale entry. This causes `hermes gateway status` to keep showing the old error.

```bash

set -euo pipefail
python3 -c "
import json
p = '/home/bratan/.hermes/gateway_state.json'
with open(p) as f:
    data = json.load(f)
data['platforms'].pop('whatsapp', None)   # change platform name
with open(p, 'w') as f:
    json.dump(data, f, indent=2)
print('done')
"
```

Alternatively, just delete the file entirely — the gateway recreates it on next start:
```bash

set -euo pipefail
rm ~/.hermes/gateway_state.json
```

### 4. Full Gateway Restart

A graceful `hermes gateway restart` may not be enough; the old env vars can linger in the process tree. Do a hard stop + start:

```bash

set -euo pipefail
systemctl --user stop hermes-gateway
sleep 2
systemctl --user start hermes-gateway
sleep 10   # wait for connection
```

### 5. Verify

```bash

set -euo pipefail
hermes gateway status          # no platform errors
grep -i 'platform(s)' ~/.hermes/logs/gateway.log   # should match active platforms only
```

If a stale warning still shows, repeat step 3 — the status file may have been re-created from an in-memory cache before the new process fully started.

## ⚠️ Hermes hat ZWEI verschiedene "Gateway"-Begriffe (korrigiert 2026-07-10)

Dieser Skill handelt vom **Messenger-Gateway** (Telegram/Discord/WhatsApp). Aber im Hermes-Repo existiert ein **zweites Gateway** das gerne verwechselt wird:

| Komponente | Zweck | Default-Port | Config | Prozess |
|---|---|---|---|---|
| **Messenger-Gateway** (dieser Skill) | Telegram/Discord/WhatsApp/Signal Bots | randomisiert (war 35395 in einem Setup) | `hermes gateway setup` | eigener Prozess `hermes_cli.main gateway run` |
| **API-Server / API-Gateway** (`gateway/platforms/api_server.py`) | HTTP-API für externe Clients (Mobile-Apps, WebUIs, OpenAI-kompatible Endpoints) | **8642** | ENV-Vars `API_SERVER_HOST/PORT/KEY` in `~/.hermes/.env` | **LÄUFT IM SELBEN PROZESS** wie der Messenger-Gateway (Hermes v0.18+) |

**Wichtige Korrektur:** In Hermes ≥ v0.18 ist `hermes api-server` als Standalone-Command **deprecated** und nicht mehr nötig. Der API-Server-Adapter wird beim Start des Messenger-Gateways automatisch mitgeladen, wenn die ENV-Vars gesetzt sind. Frühere Anleitung "API-Server explizit starten" gilt nicht mehr.

**Symptom der Verwechslung:** Du installierst die Hermes-Android-App, trägst Host + Port ein, aber die App sagt "Connection failed". Grund: Du hast den Messenger-Gateway (Port random) erwischt, nicht den API-Server (Port 8642). Oder: Der API-Server läuft gar nicht (`ss -tlnp | grep 8642` ist leer).

**Diagnose:**

```bash
# Welche Plattformen laufen gerade? (sollte BEIDE zeigen wenn ENV gesetzt)
ss -tlnp | grep -E ':(8642|9119|35395|8787)'
# Beispiel:
#   LISTEN ... 127.0.0.1:35395  ... users:(("hermes",pid=61301,fd=24))    ← Messenger
#   LISTEN ... 0.0.0.0:8642     ... users:(("hermes",pid=61301,fd=27))    ← API-Server, gleiche PID!

# API-Server via ENV-Vars aktivieren (in ~/.hermes/.env):
echo "API_SERVER_HOST=0.0.0.0"  >> ~/.hermes/.env
echo "API_SERVER_PORT=8642"     >> ~/.hermes/.env
echo "API_SERVER_KEY=$(openssl rand -hex 32)" >> ~/.hermes/.env

# Messenger-Gateway restarten (5-10s Telegram-Downtime akzeptieren)
systemctl --user restart hermes-gateway
sleep 10 && hermes gateway status   # beide Plattformen sollten "connected" sein
```

**Domain-Detail-Notizen** (Mobile-Companion-Apps, OpenAI-kompatibles Streaming, `API_SERVER_KEY` aus `~/.hermes/.env`, TCP_NODELAY-Patch für SSE-Echtzeit-Streaming, Tailscale-Serve-Hybrid-Hosting, systemd-units für die 3 Plattformen, Hermes-Android-App-Config-Reference) liegen in `references/api-server-quirks.md`. Nächste Session mit Mobile-Companion-Frage: dort reinlesen statt hier.

**Pitfalls beim Hermes-Gateway/API-Server-Restart (gesammelt 2026-07-10):**

- **`pkill -f "hermes_cli.main"` killt die eigene Terminal-Subshell (Terminal-Tool-Quirk):** Wenn der Match-String zu breit ist und der `terminal()`-Wrapper selbst Hermes-Tooling spawnt, killt pkill den eigenen Subprozess → Exit -15 (SIGTERM, 128+15), aber die Aktion war schon durch. **Fix:** Niemals `pkill -f` von einem Hermes-Terminal-Tool aus aufrufen wenn der Match potentiell die eigene Shell erwischt. Stattdessen PID-basiert arbeiten (`ps -eo pid,args | grep ... | awk '{print $1}' | xargs kill -TERM`) oder über `systemctl --user stop hermes-gateway` gehen — Letzteres ist immer der sichere Weg.
- **`systemctl Restart=always` + Port-Konflikt = Endlosschleife (Yuno-Memory-Eintrag):** Wenn der Service nach SIGTERM wieder gestartet wird, aber der alte Prozess noch den Port hält, stirbt der neue Start mit exit 1 → systemd restartet wieder → Endlos. **Fix:** Service während der Testphase `disabled` lassen, dann nach erfolgreichem Smoke-Test auf `enabled` zurückschalten. Beispiel-Sequenz aus 2026-07-10: `systemctl --user stop hermes-gateway` → Exit-Code 1 wegen Auto-Restart-Versuch → `systemctl --user disable hermes-gateway` → `pkill -TERM <verbleibende PIDs>` → `systemctl --user start hermes-gateway`.

## References

- `references/telegram-auth.md` — Telegram-spezifische Auth-Details
- `references/api-server-quirks.md` — **API-Server** (Port 8642) für Mobile/Web-Clients — Domain-Wissen aus Hermes-Android-Hybrid-Setup
- `scripts/apk-serve.py` — Minimaler Static-File-Server für genau eine APK-Datei (Allowlist, kein Traversal). Kombiniert mit `tailscale serve --bg --https=<PORT> http://127.0.0.1:<PORT>` als APK-Distribution-Werkzeug wenn kein adb verfügbar.
- **User rejected / "Unauthorized":** Set `TELEGRAM_ALLOWED_USERS` env var (Telegram-specific)
- **Bot not responding in channel:** Check bot permissions and intents
- **Service died on logout:** Enable linger — `sudo loginctl enable-linger $USER`

### `send_message` to Telegram fails: "invalid literal for int()"

If `send_message(message="...", target="telegram")` fails with `invalid literal for int() with base 10: '@YourBot'`, the gateway tries to resolve the bare platform name to a numeric chat ID but hits the bot username instead.

**Fix:**
1. Discover available targets: `send_message(action='list')` — shows entries like `telegram:User (dm)`
2. Target the numeric chat ID directly: `send_message(message="...", target="telegram:<numeric_id>")`

If a stale warning still shows, repeat step 3 — the status file may have been re-created from an in-memory cache before the new process fully started.

## ⚠️ Hermes hat ZWEI verschiedene "Gateway"-Begriffe (korrigiert 2026-07-10)

Dieser Skill handelt vom **Messenger-Gateway** (Telegram/Discord/WhatsApp). Aber im Hermes-Repo existiert ein **zweites Gateway** das gerne verwechselt wird:

| Komponente | Zweck | Default-Port | Config | Prozess |
|---|---|---|---|---|
| **Messenger-Gateway** (dieser Skill) | Telegram/Discord/WhatsApp/Signal Bots | randomisiert (war 35395 in einem Setup) | `hermes gateway setup` | eigener Prozess `hermes_cli.main gateway run` |
| **API-Server / API-Gateway** (`gateway/platforms/api_server.py`) | HTTP-API für externe Clients (Mobile-Apps, WebUIs, OpenAI-kompatible Endpoints) | **8642** | ENV-Vars `API_SERVER_HOST/PORT/KEY` in `~/.hermes/.env` | **LÄUFT IM SELBEN PROZESS** wie der Messenger-Gateway (Hermes v0.18+) |

**Wichtige Korrektur:** In Hermes ≥ v0.18 ist `hermes api-server` als Standalone-Command **deprecated** und nicht mehr nötig. Der API-Server-Adapter wird beim Start des Messenger-Gateways automatisch mitgeladen, wenn die ENV-Vars gesetzt sind. Frühere Anleitung "API-Server explizit starten" gilt nicht mehr.

**Symptom der Verwechslung:** Du installierst die Hermes-Android-App, trägst Host + Port ein, aber die App sagt "Connection failed". Grund: Du hast den Messenger-Gateway (Port random) erwischt, nicht den API-Server (Port 8642). Oder: Der API-Server läuft gar nicht (`ss -tlnp | grep 8642` ist leer).

**Diagnose:**

```bash
# Welche Plattformen laufen gerade? (sollte BEIDE zeigen wenn ENV gesetzt)
ss -tlnp | grep -E ':(8642|9119|35395|8787)'
# Beispiel:
#   LISTEN ... 127.0.0.1:35395  ... users:(("hermes",pid=61301,fd=24))    ← Messenger
#   LISTEN ... 0.0.0.0:8642     ... users:(("hermes",pid=61301,fd=27))    ← API-Server, gleiche PID!

# API-Server via ENV-Vars aktivieren (in ~/.hermes/.env):
echo "API_SERVER_HOST=0.0.0.0"  >> ~/.hermes/.env
echo "API_SERVER_PORT=8642"     >> ~/.hermes/.env
echo "API_SERVER_KEY=$(openssl rand -hex 32)" >> ~/.hermes/.env

# Messenger-Gateway restarten (5-10s Telegram-Downtime akzeptieren)
systemctl --user restart hermes-gateway
sleep 10 && hermes gateway status   # beide Plattformen sollten "connected" sein
```

**Domain-Detail-Notizen** (Mobile-Companion-Apps, OpenAI-kompatibles Streaming, `API_SERVER_KEY` aus `~/.hermes/.env`, TCP_NODELAY-Patch für SSE-Echtzeit-Streaming, Tailscale-Serve-Hybrid-Hosting, systemd-units für die 3 Plattformen, Hermes-Android-App-Config-Reference) liegen in `references/api-server-quirks.md`. Nächste Session mit Mobile-Companion-Frage: dort reinlesen statt hier.

**Pitfalls beim Hermes-Gateway/API-Server-Restart (gesammelt 2026-07-10):**

- **`pkill -f "hermes_cli.main"` killt die eigene Terminal-Subshell (Terminal-Tool-Quirk):** Wenn der Match-String zu breit ist und der `terminal()`-Wrapper selbst Hermes-Tooling spawnt, killt pkill den eigenen Subprozess → Exit -15 (SIGTERM, 128+15), aber die Aktion war schon durch. **Fix:** Niemals `pkill -f` von einem Hermes-Terminal-Tool aus aufrufen wenn der Match potentiell die eigene Shell erwischt. Stattdessen PID-basiert arbeiten (`ps -eo pid,args | grep ... | awk '{print $1}' | xargs kill -TERM`) oder über `systemctl --user stop hermes-gateway` gehen — Letzteres ist immer der sichere Weg.
- **`systemctl Restart=always` + Port-Konflikt = Endlosschleife (Yuno-Memory-Eintrag):** Wenn der Service nach SIGTERM wieder gestartet wird, aber der alte Prozess noch den Port hält, stirbt der neue Start mit exit 1 → systemd restartet wieder → Endlos. **Fix:** Service während der Testphase `disabled` lassen, dann nach erfolgreichem Smoke-Test auf `enabled` zurückschalten. Beispiel-Sequenz aus 2026-07-10: `systemctl --user stop hermes-gateway` → Exit-Code 1 wegen Auto-Restart-Versuch → `systemctl --user disable hermes-gateway` → `pkill -TERM <verbleibende PIDs>` → `systemctl --user start hermes-gateway`.

## References

- `references/telegram-auth.md` — Telegram-spezifische Auth-Details
- `references/api-server-quirks.md` — **API-Server** (Port 8642) für Mobile/Web-Clients — Domain-Wissen aus Hermes-Android-Hybrid-Setup
- `scripts/apk-serve.py` — Minimaler Static-File-Server für genau eine APK-Datei (Allowlist, kein Traversal). Kombiniert mit `tailscale serve --bg --https=<PORT> http://127.0.0.1:<PORT>` als APK-Distribution-Werkzeug wenn kein adb verfügbar.
