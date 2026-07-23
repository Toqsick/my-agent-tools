# Telegram Auth Configuration

## The Env Var System (Not dm_policy)

Telegram uses `TELEGRAM_ALLOWED_USERS` env var for auth — NOT the `dm_policy` config key.

The `dm_policy` config only works for WeCom, Weixin, Yuanbao, QQBot (see `gateway/run.py` line 7130).

### Setting Allowed Users

```bash
# Single user (numeric ID from Telegram)
echo "TELEGRAM_ALLOWED_USERS=7222661188" >> ~/.hermes/.env

# Multiple users, comma-separated
echo "TELEGRAM_ALLOWED_USERS=111111111,222222222" >> ~/.hermes/.env

# Allow everyone (use with caution)
echo "TELEGRAM_ALLOWED_USERS=*" >> ~/.hermes/.env
```

### Finding Your User ID

- Message the bot
- Check gateway logs: `grep "Unauthorized user" ~/.hermes/logs/gateway.log`
- The log shows: `Unauthorized user: 7222661188 (Gregor) on telegram`
- The number is your user ID

### Why This Matters

Without `TELEGRAM_ALLOWED_USERS` set, Telegram fails closed — ALL messages are rejected as "Unauthorized user". This is by design (#24457). The Telegram adapter's `_is_user_authorized()` method checks this env var first.

### Restart Required

After adding the env var, restart the gateway:
```bash
hermes gateway restart
```

Config changes are NOT hot-reloadable for the Telegram adapter.
