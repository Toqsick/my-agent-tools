# Telegram Gateway Diagnostics — Log Patterns & Authorization Internals

Session-sourced diagnostic reference for when Telegram messages aren't getting through.

## Log Pattern → Diagnosis Map

### "Unauthorized user: 7222661188 (Gregor) on telegram"

**Meaning:** The user DM'd the bot but is not authorized. The gateway's authorization layer rejected the message before it reaches the agent.

**Resolution order:**
1. Check if a pairing code was generated: `hermes pairing list`
2. If NO pending code exists → the bot couldn't send the pairing code to the user (look for send errors above this line in logs)
3. Quick fix for personal bots: `hermes config set telegram.dm_policy open && hermes gateway restart`
4. Proper fix: approve the pairing code once you can see it

### "Failed to send Telegram message: invalid literal for int() with base 10: '@OlympAgentBot'"

**Meaning:** The home channel is set to a @BotUsername string instead of a numeric chat ID. The gateway tries `int(chat_id)` and fails.

**Impact:** ONLY affects the startup "I'm online" notification. Does NOT block actual message handling. Cosmetic issue.

**Fix (optional):** Set the home channel to a numeric chat ID, or just ignore this warning.

### "[Telegram] Primary api.telegram.org connection failed"

**Meaning:** DNS or network issue reaching api.telegram.org. The gateway automatically falls back to sticky IP 149.154.166.110.

**Impact:** Usually transient. If fallback also fails, check firewall/proxy settings.

### "Home-channel startup notification failed"

**Meaning:** Consequence of the chat_id parsing error above. The bot couldn't send its "I'm online" message to the configured home channel.

**Impact:** Cosmetic only. Doesn't affect message handling.

### `systemctl --user status hermes-gateway.service` is inactive with systemd SIGTERM

**Meaning:** The gateway daemon is stopped. This is a service-state problem, not a Telegram protocol/auth bug.

**Resolution order:**
1. Check the latest journal for the shutdown context:
   ```bash
   journalctl --user -u hermes-gateway.service -n 120 --no-pager
   ```
2. If it ends with `Stopping hermes-gateway.service` and `signal=SIGTERM under_systemd=yes`, restart cleanly:
   ```bash
   systemctl --user stop hermes-gateway.service || true
   sleep 3
   systemctl --user start hermes-gateway.service
   sleep 8
   journalctl --user -u hermes-gateway.service -n 120 --no-pager
   ```
3. Verify the healthy Telegram connect sequence:
   ```text
   Connecting to telegram...
   [Telegram] Connected to Telegram (polling mode)
   ✓ telegram connected
   Gateway running with 1 platform(s)
   Channel directory built: 1 target(s)
   ```

### Loaded gateway config says Telegram disabled/token empty while files look correct

**Meaning:** `config.yaml` and `.env` may contain correct values, but the currently loaded gateway config or systemd unit environment does not expose them.

**Resolution order:**
1. Do the clean restart above before assuming config corruption.
2. Check the systemd unit environment:
   ```bash
   systemctl --user show hermes-gateway.service -p Environment
   ```
3. Check whether the running `hermes` process is actually the gateway daemon or just the CLI agent:
   ```bash
   pgrep -a -u bratan 'hermes|python.*hermes|gateway'
   ```
4. Re-check both config layers:
   - `~/.hermes/config.yaml`
   - `~/.hermes/.env`
   - loaded `load_gateway_config()` result
5. Never use `telegram`, `telegram:toqsick`, or `telegram:@OlympAgentBot` as delivery targets; use numeric IDs such as `telegram:7222661188`.

## Authorization Flow (from source code)

The gateway checks authorization in this order (from `gateway/run.py`):

1. **Pairing store** — `PairingStore.is_approved(platform, user_id)` checks `~/.hermes/pairing/{platform}-approved.json`. If approved here, message goes through regardless of other config.

2. **Config-driven policy** — Checks `dm_policy` / `group_policy` / `allow_from` in config.yaml. For Telegram, `dm_policy: open` skips all further checks.

3. **If unauthorized** — In DMs, the gateway tries to generate and send a pairing code. In groups, it silently ignores.

**Key insight:** If step 1 fails AND step 2 isn't set to open, the gateway tries to send a pairing code via the bot. If the bot can't send messages (network, config error), the user sees nothing and you only see "Unauthorized" in logs with no pending pairing request.

## Pairing Store File Format

Location: `~/.hermes/pairing/`

Files:
- `telegram-pending.json` — pending pairing requests (with expiry)
- `telegram-approved.json` — approved users
- `_rate_limits.json` — rate limit tracking (prevents spam)

### telegram-approved.json format:
```json
{
  "7222661188": {
    "user_name": "Gregor",
    "approved_at": 1748862000.0
  }
}
```

Keys are user IDs (as strings). Values have `user_name` and `approved_at` (unix timestamp).

### Creating an approved entry manually (if pairing codes aren't working):
```json
{
  "<telegram_user_id>": {
    "user_name": "<display_name>",
    "approved_at": <unix_timestamp>
  }
}
```

Write to `~/.hermes/pairing/telegram-approved.json` and restart the gateway.

## Telegram-Specific Config Keys

| Config Key | Purpose | Example |
|-----------|---------|---------|
| `telegram.allowed_chats` | Comma-separated chat IDs for group filtering | `"123456,-987654"` |
| `telegram.dm_policy` | DM access: `pairing` (default), `open`, `allowlist`, `disabled` | `"open"` |
| `telegram.reactions` | Enable reaction indicators | `true` / `false` |
| `telegram.channel_prompts` | Per-channel system prompt overrides | `{}` |

Note: `telegram.allowed_chats` controls GROUP access filtering, not DM authorization. For DMs, use `dm_policy`.
