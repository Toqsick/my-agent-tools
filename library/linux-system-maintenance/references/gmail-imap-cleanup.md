# Gmail IMAP Organizer via stdlib (imaplib)

Built 2026-06-03 as `gmail-organizer` (originally `gmail-cleaner`) for Basti
(Gmail: bastick123@gmail.com via Evolution). Renamed per user request from
"cleaner" to "organizer" for a softer branding.

## When to Use

- User has Gmail with thousands of unread/no-reply/spam emails
- User wants to delete mails older than N years, no-reply auto-mails, or empty spam
- User has no overview and wants a CLI tool (not web GUI)
- User has Evolution (GNOME) configured with Gmail IMAP (all mails server-side)

## Architecture

### Key Constraints
1. **No external packages** — only `imaplib` + `email` (stdlib)
2. **Gmail requires App Passwords** if 2FA is enabled (which it usually is)
3. **Dry-run is the default** — explicit `--for-real` flag to enable deletion
4. **IMAP individual-fetch is SLOW on large mailboxes** — use server-side SEARCH
   instead of header-by-header scanning (100x speedup)

### Gmail IMAP Connection

```python
import imaplib

conn = imaplib.IMAP4_SSL("imap.gmail.com", 993)
conn.login(email, app_password)  # App Password, NOT regular password!
```

**App Password setup:** https://myaccount.google.com/apppasswords
The password is 16 characters, no spaces. Store in config file with chmod 600.

### Folder Names (Gmail-specific)

| Gmail Label | IMAP Folder Name |
|-------------|------------------|
| Inbox | `INBOX` |
| Spam | `[Gmail]/Spam` (or `[Google Mail]/Spam` on old accounts) |
| Trash | `[Gmail]/Trash` |
| Sent | `[Gmail]/Gesendet` or `[Gmail]/Sent Mail` |

Always try multiple names if the first fails.

## CRITICAL: Server-Side SEARCH (100x faster)

**DO NOT fetch headers one-by-one** to find no-reply mails. With 4000+ mails,
individual `conn.fetch()` calls take 10-30 minutes and frequently TIME OUT.

Instead, use Gmail's built-in `SEARCH` with `FROM` and `SUBJECT` criteria.
This happens entirely on the server — the result is INSTANT even for 2000+ mails.

```python
# FAST: server-side search for no-reply senders
patterns = ['noreply', 'no-reply', 'no_reply', 'donotreply',
            'notifications', 'newsletter', 'mailer-daemon']

all_no_reply = set()
for pat in patterns:
    typ, data = conn.search(None, f'(FROM "{pat}")')
    if typ == 'OK' and data[0]:
        ids = data[0].split()
        for id in ids:
            all_no_reply.add(id)  # Use set to deduplicate

# Also search SUBJECT for common patterns
subj_patterns = ['newsletter', 'verification', 'welcome', 'security alert']
for pat in subj_patterns:
    typ, data = conn.search(None, f'(SUBJECT "{pat}")')
    if typ == 'OK' and data[0]:
        ids = data[0].split()
        for id in ids:
            all_no_reply.add(id)
```

**Performance comparison (4093-message inbox on Gmail):**

| Method | Time | Mails Found |
|--------|------|-------------|
| Header-by-header fetch (2000 mails) | TIMEOUT (>5 min) | ~268 |
| **Server-side SEARCH FROM+SUBJECT** | **~2 seconds** | **2165** |

Result: 2165 no-reply mails deleted vs only 268 found via scanning.

### Batch Delete After Server-Side Search

After finding message IDs via SEARCH, delete them in batches of 100:

```python
if all_no_reply:
    ids_list = list(all_no_reply)
    batch_size = 100
    for i in range(0, len(ids_list), batch_size):
        batch = ids_list[i:i+batch_size]
        ids_str = ','.join(id.decode() if isinstance(id, bytes) else str(id) for id in batch)
        conn.copy(ids_str, '[Gmail]/Trash')
        conn.store(ids_str, '+FLAGS', '\\Deleted')
        conn.expunge()
```

**Critical:** Gmail IMAP DOES accept comma-separated message IDs for both
`conn.copy()` and `conn.store()`. This is much faster than individual calls.

### Search Patterns

```python
# Mails older than 5 years
cutoff = datetime.now(timezone.utc) - timedelta(days=365 * years)
cutoff_str = cutoff.strftime("%d-%b-%Y")
typ, data = conn.search(None, f"BEFORE {cutoff_str}")

# ALL mails in folder
typ, data = conn.search(None, "ALL")
```

### No-Reply Sender Detection (for PREVIEW only)

For the `show` command (preview with sender+subject), you still need
individual HEADER fetches on a **small subset** (first 10 old, first 15
no-reply samples). Use BODY.PEEK to avoid marking as read:

```python
def categorize_email(msg_id, conn, cfg):
    typ, data = conn.fetch(msg_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
    raw_str = data[0][1].decode("utf-8", errors="replace")
    from_match = re.search(r"^From:\s*(.+)$", raw_str, re.MULTILINE | re.IGNORECASE)
    from_addr = from_match.group(1).strip() if from_match else ""
    subj_match = re.search(r"^Subject:\s*(.+)$", raw_str, re.MULTILINE | re.IGNORECASE)
    subject = decode_mime(subj_match.group(1)) if subj_match else "(kein Betreff)"
    for pattern in cfg["no_reply_patterns"]:
        if pattern.lower() in from_addr.lower():
            return "no_reply", from_addr, subject
    return None, from_addr, subject
```

**Limit preview fetches to MAX 10-20 samples.**

### Full Sender Patterns

```python
patterns = [
    "no-reply@","noreply@","no_reply@","notifications@","newsletter@",
    "mail@","info@","service@","automail@","donotreply@","do-not-reply@",
    "mailer-daemon@","postmaster@","noreply-","no-reply-",
    "news@","marketing@","team@","accounts@","billing@","support@",
    "update@","updates@","feedback@","alert@","alerts@","invite@",
    "confirm@","confirmation@",
    "noreply.github.com","notifications@github.com","noreply.gitlab.com",
]
```

### Gmail IMAP Delete Pattern

```python
# Copy to Trash + mark deleted
conn.copy(msg_id, "[Gmail]/Trash")
conn.store(msg_id, "+FLAGS", "\\\\Deleted")
conn.expunge()

# Empty Trash entirely
conn.select("[Gmail]/Trash")
conn.store("1:*", "+FLAGS", "\\\\Deleted")
conn.expunge()
```

### `--for-real` Safety Pattern

The `--for-real` flag is a **persistent config toggle**, not a one-shot override:

```python
def main():
    args = sys.argv[1:]
    if "--for-real" in args:
        cfg = load_config()
        cfg["dry_run"] = False
        save_config(cfg)
        print("Dry-Run deactivated! Next clean runs for real.")
        args.remove("--for-real")
```

**Always reset `dry_run` to `true` after a real cleanup run!**
The config persists between sessions.

### Show/Preview Command Pattern

A dedicated `show` subcommand provides richer output than bare `clean`:

```python
def cmd_show(args):
    # 1. Show old mails sample (first 10)
    old_ids = search_old_mails(conn, cfg["max_age_years"])
    for mid in old_ids[:10]:
        cat, sender, subject = categorize_email(mid, conn, cfg)
        if sender:
            print(f"  {sender:<40} {subject}")

    # 2. Server-side SEARCH for no-reply count
    total_noreply = set()
    for pat in patterns:
        base = pat.split("@")[0] if "@" in pat else pat
        typ, data = conn.search(None, f'(FROM "{base}")')
        if typ == 'OK' and data[0]:
            for id in data[0].split(): total_noreply.add(id)

    # 3. Summary
    print(f"  INBOX: {total}")
    print(f"  Older {years}Y: {len(old_ids)}")
    print(f"  No-Reply: {len(total_noreply)}")
```

### MIME Header Decoding

```python
from email.header import decode_header

def decode_mime(s):
    if not s: return ""
    parts = decode_header(s)
    result = []
    for text, charset in parts:
        if isinstance(text, bytes):
            try: result.append(text.decode(charset or "utf-8", errors="replace"))
            except: result.append(text.decode("utf-8", errors="replace"))
        else: result.append(str(text))
    return " ".join(result)
```

## Pitfalls

1. **Gmail IMAP BEFORE date is INCLUSIVE.** Mails from that exact date are included.
2. **IMAP search changes mailbox state.** Re-select INBOX before second search.
3. **conn.fetch() can timeout on large bodies.** Only fetch headers for preview.
4. **Gmail rate-limits IMAP connections.** Stay under 2000 rapid operations.
5. **Gmail IMAP does NOT support DELETE directly.** Must copy-to-Trash + expunge.
6. **App Passwords expire** when Google account password changes.
7. **conn.copy() with comma-separated IDs works on Gmail.** Use batch size 100.
8. **Evolution + Gmail IMAP = mails server-side.** Local cache is tiny.
9. **Re-select folder after each search.** Search changes the selected state.
10. **SEARCH FROM with partial works.** `FROM "noreply"` catches all containing it.
11. **--for-real persists!** Always reset dry_run to true after cleanup.
