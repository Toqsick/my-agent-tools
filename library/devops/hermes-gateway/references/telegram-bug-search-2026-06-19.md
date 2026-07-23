# Telegram Bug Search — 19.06.2026

Session-derived reference for `hermes-gateway` troubleshooting.

## User task

`mach mal bug serarch von telegram`

## Findings

### Historical Telegram errors are known and fixed

Old gateway logs contain these patterns:

```text
ValueError: invalid literal for int() with base 10: '@OlympAgentBot'
ValueError: invalid literal for int() with base 10: 'toqsick'
WARNING gateway.run: Unauthorized user: 7222661188 (Gregor) on telegram
```

Diagnosis:

- `@OlympAgentBot` / `toqsick` were used where a numeric Telegram chat ID was required.
- `Unauthorized user: 7222661188 (Gregor)` meant the user was known but not in the authorization/allowlist path.
- Existing docs (`hermes-gateway-messaging-2026-06-06.md`, `cronjob-overview.md`) show these were fixed by using numeric `7222661188` for home channel, allowed users/chats, and cron delivery targets.

### Current outage is not a Telegram protocol bug

Current checks showed:

```text
systemctl --user status hermes-gateway.service --no-pager -l
exit 3
```

The latest relevant journal lines were:

```text
Jun 19 05:48:00 bratan-17-P1 systemd[1776]: Stopping hermes-gateway.service - Hermes Agent Gateway - Messaging Platform Integration...
Jun 19 05:48:00 bratan-17-P1 python[98730]: WARNING gateway.run: Shutdown context: signal=SIGTERM under_systemd=yes parent_pid=1776 parent_name=systemd loadavg_1m=1.58 parent_cmdline='/usr/lib/systemd/systemd --user'
```

Diagnosis: the gateway daemon was stopped by systemd SIGTERM. There was no new Telegram send/auth/network error in the current run.

### Runtime config mismatch

A direct Python load of the gateway config reported:

```text
telegram.enabled False
telegram.bot_token_set False
telegram.home_channel None
telegram.allowed_chats []
```

But `~/.hermes/config.yaml` and `~/.hermes/.env` still contained the correct Telegram values:

```text
telegram.bot_token: <redacted>
telegram.allowed_chats: 7222661188
telegram.home_channel: 7222661188
TELEGRAM_ALLOWED_USERS=7222661188
TELEGRAM_HOME_CHANNEL=7222661188
```

Diagnosis: files on disk can be correct while the loaded gateway config is not visible/active in the current runtime. Restart the gateway before treating this as a config corruption.

### Running process may be CLI agent, not gateway

`pgrep -a -u bratan 'hermes|python.*hermes|gateway'` showed a running Hermes CLI process, not the gateway daemon. Do not assume any running `hermes` process is the gateway.

## Recommended fix flow

```bash
systemctl --user stop hermes-gateway.service || true
sleep 3
systemctl --user start hermes-gateway.service
sleep 8
systemctl --user status hermes-gateway.service --no-pager -l
journalctl --user -u hermes-gateway.service -n 120 --no-pager
```

Expected healthy log lines:

```text
Connecting to telegram...
[Telegram] Connected to Telegram (polling mode)
✓ telegram connected
Gateway running with 1 platform(s)
Channel directory built: 1 target(s)
```

Then test delivery with the agent tool if available:

```python
send_message(target="telegram:Gregor (dm)", text="Telegram-Gateway-Test 19.06.2026")
```

## Durable lessons for this skill

- Treat systemd SIGTERM + inactive gateway as a service-state problem first.
- Always compare three layers during Telegram debugging:
  1. `config.yaml`
  2. `.env`
  3. loaded gateway config + systemd unit environment
- `.env` can override `config.yaml`; check both.
- Use numeric Telegram IDs, never `telegram`, `telegram:toqsick`, or `telegram:@OlympAgentBot`.
- Do not repeat old historical errors as current bugs unless the same pattern appears in the current logs.
