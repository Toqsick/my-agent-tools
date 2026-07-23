# Recurring Gmail Cleanup via Cron (no_agent Pattern)

Built 2026-06-03 for Basti. Cron job: `gmail-organizer` runs Sundays 8 AM via
Hermes cron with `no_agent=True`. Script: `~/bin/gmail-organizer-cron`.

## Architecture

```
Hermes Cron Scheduler ──(tick, no_agent=True)──→ ~/bin/gmail-organizer-cron
                                                        │
                                                        ├── IMAP server-side SEARCH (2s)
                                                        ├── Delete old/no-reply/spam
                                                        ├── Log to ~/.logs/gmail-organizer-cron.log
                                                        └── stdout → delivered to user
```

No agent loop, no tokens spent. The script IS the run.

## The Script

Location: `~/bin/gmail-organizer-cron` (chmod +x, self-contained, no pip deps)

### Key Behaviors

1. **Reads config from** `~/.gmail-organizer.json` (chmod 600)
2. **Connects to Gmail IMAP** with App Password
3. **Server-side SEARCH only** — no header-by-header fetch (see `references/gmail-imap-cleanup.md`)
4. **Logs everything** to `~/.logs/gmail-organizer-cron.log` with timestamps
5. **Delivers summary** to user via stdout (Hermes cron delivery)

### What It Does Each Run

| Step | Server Action | Query |
|------|---------------|-------|
| 1 | Find + delete mails older than 5 years | `BEFORE dd-Mmm-YYYY` |
| 2 | Find + delete no-reply/auto mails | `FROM "noreply"`, `FROM "no-reply"`, etc. (9 patterns) |
| 3 | Find + delete subject-based noise | `SUBJECT "newsletter"`, `SUBJECT "welcome"` |
| 4 | Empty Spam | Select `[Gmail]/Spam`, mark all deleted, expunge |
| 5 | Empty Trash | Select `[Gmail]/Trash`, mark all `1:*` deleted, expunge |

### Error Handling

- Missing config file → log error, return 1
- Login failure (bad password, network) → log error, return 1
- IMAP operation failure → log error, return 1 (partial cleanup still counts)
- Script timeout → Hermes enforces 3-minute hard limit, kills process

### Cron Configuration

```
Name:       gmail-organizer
Schedule:   0 8 * * 0 (Sunday 8 AM)
Script:     gmail-organizer-cron (resolved from PATH)
no_agent:   true
Workdir:    /home/bratan
Deliver:    local (auto to CLI user)
```

Created via:
```python
cronjob(action='create', name='gmail-organizer', schedule='0 8 * * 0',
        script='gmail-organizer-cron', no_agent=True, workdir='/home/bratan')
```

## Safety Design

Unlike agent-based cron (which runs `--dry-run` by default), no_agent cron
does REAL work each tick. Safety comes from:

1. **Server-side SEARCH only** — no risk of accidentally deleting non-matching
   emails because IMAP `FROM`/`BEFORE` is exact
2. **IDEMPOTENT operations** — deleting a non-existent message is a no-op
3. **Log-file audit trail** — every deletion is timestamped and counted
4. **Hard 3-minute timeout** — prevents runaway operations
5. **Password stays in chmod 600 file** — never exposed in process args

## When NOT to Use This Pattern

- If the cleanup requires LLM reasoning (e.g., "is this email spam or not?")
- If the user wants a confirmation before deletion
- If the operation is not idempotent (e.g., renaming folders)
- If the script has interactive prompts
