# Safety Patterns — Detailed Reference

Pitfalls, telegram-notification pattern, JSON-output workaround, and cron
integration patterns for cleanup tools. Loaded on demand from the slim
`SKILL.md` when building or debugging scanner tools.

## Pitfalls

1. **Never recurse into `~/.ssh/`, `~/.gnupg/`, `~/.config/` blindly.** Always
   whitelist or target specific subdirectories.
2. **Browser caches must only be cleaned when the browser is closed.** Otherwise
   you corrupt the profile.
3. **Steam shadercache is huge but regenerates.** Warn the user: "Shader-Cache
   wird beim nächsten Spielstart neu erzeugt — erstes Laden dauert länger."
4. **journalctl requires root.** If running as user, silently skip or warn.
5. **APT cache cleanup is better done by `apt clean`.** Prefer shelling out to
   the native tool rather than manually deleting `.deb` files.
6. **Always check `os.access(path, os.W_OK)` before reporting a deletable item.**
   Otherwise you report files the user can't actually delete.
7. **`apt autoremove --purge` does NOT fully clean rc packages.** It only removes
   automatically-installed packages that are no longer needed. Explicit
   `dpkg --purge` on rc-state packages is required for the rest. See
   `cleanup-procedures.md` §"rc Package Purge".
8. **steam-installer postrm debconf dialog.** When purging non-interactively,
   pre-remove the postrm script. See `cleanup-procedures.md` §"steam-installer
   Purge Workaround". The user's Steam data in `~/.steam/` is NOT affected.
9. **For complex multi-line file edits, prefer `execute_code` over `patch`.**
   When patching requires multiple coordinated changes across a file (e.g.,
   renaming a variable that's used in 5 places + adding a new argparse
   argument), `patch` often fails with "old_string not found" or creates
   partial states. Use `execute_code` with Python file I/O to read,
   regex-replace, and write back atomically:

   ```python
   with open("main.py") as f:
       content = f.read()
   content = content.replace("old_func()", "new_func()")
   content = re.sub(r'pattern', r'replacement', content)
   with open("main.py", "w") as f:
       f.write(content)
   ```

   Reserve `patch` for single unique replacements with clear context.

10. **`shutil.disk_usage` does NOT have a `.percent` attribute.**
    It returns a `usage` namedtuple with `.total`, `.used`, `.free` only.
    Always calculate percentage manually:

    ```python
    disk = shutil.disk_usage("/")
    percent = disk.used / disk.total * 100  # NOT disk.percent!
    ```

    Using `disk.percent` raises `AttributeError`.

11. **Backtick characters inside f-strings break Python syntax.**
    Never include backtick (`) characters inside f-string expressions, even
    if they appear in string literals. Python's f-string parser treats them
    as format specifiers and produces `SyntaxError: unterminated f-string literal`.
    Workaround: build strings outside the f-string or escape differently:

    ```python
    # WRONG — SyntaxError
    line = f"| {name} | `{path}` | {status} |"
    # CORRECT — build path display separately
    path_display = f"`{path}`"
    line = f"| {name} | {path_display} | {status} |"
    ```

12. **`f3probe --destructive` benötigt sudo + echtes Terminal.** Im
    Background-Modus (Hintergrundprozess) crasht sudo, weil kein Passwort-
    Terminal existiert. `sudo -S` ist von Hermes blockiert (Security). Lösung:
    `pty=True` im Terminal-Befehl, oder `f3write`/`f3read` auf dem gemounteten
    Volume als Workaround (braucht kein sudo). Siehe
    `references/fake-storage-validation.md`.

13. **`err_msg()` helper for sudo-required errors.** When non-interactive
    terminals hit `sudo`, the error is "sudo: ein Terminal ist erforderlich".
    Provide an `err_msg(code, err)` function that maps this to a user-friendly
    "sudo nötig — im echten Terminal ausführen". All cleanup functions that
    use sudo should reference this helper:

    ```python
    def err_msg(code, err):
        if err and "terminal erforderlich" in err:
            return "sudo nötig — im echten Terminal ausführen"
        return (err or f"Fehler (Code {code})")[:120]
    ```

    Call in every sudo cleanup handler:

    ```python
    r, code, err = run(["apt", "clean"], sudo=True)
    if code == 0: print("  ✅ Done")
    else: print(f"  ❌ {err_msg(code, err)}")
    ```

## CLI UX Pattern (full)

```python
parser = argparse.ArgumentParser(...)
parser.add_argument("command", choices=["scan", "clean", "status"])
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--no-backup", action="store_true")
parser.add_argument("--json", action="store_true",
                    help="Machine-readable JSON output (suppresses TUI)")
parser.add_argument("--notify", action="store_true",
                    help="Send scan summary to Telegram/etc. after run")
args = parser.parse_args()

safety = SafetyManager(dry_run=args.dry_run or args.command == "scan")
```

- `scan` → always dry-run, shows tables, no changes
- `clean` → dry-run unless `--execute` or explicit flag
- `clean` requires typing "JA" interactively
- `--no-backup` skips the safety backup

## JSON Output Mode

When building CLI scanner tools, support `--json` for machine-readable output.
This is essential for cron integration, Telegram reports, and piping into other tools.

**Critical: rich-Console + JSON incompatibility.**
`redirect_stdout` does NOT catch rich console output — rich snapshots the
output stream at creation time. Output will contain rich formatting artifacts
and NOT be valid JSON.

**Workaround: `console.quiet = True`**

```python
if args.json:
    console.quiet = True  # suppresses ALL console.print() calls in scanners
    results, total_size = scan_all(scanners, dry_run=True)
    console.quiet = False
    print(json.dumps(build_results(results, total_size), indent=2))
    return
```

## Telegram Notification Pattern

When adding `--notify`, use the minimal-dependency pattern:

```python
def notify_telegram(results, total_size):
    try:
        from telegram_helper import send_telegram, is_configured
    except ImportError:
        console.print("[yellow]telegram_helper.py nicht gefunden[/yellow]")
        return
    if not is_configured():
        return
    # Build compact summary text
    lines = ["🧹 Scan Report"]
    for cat in sorted(categories, key=lambda c: c['size'], reverse=True):
        lines.append(f"• {cat['name']}: {human_size(c['size'])}")
    send_telegram("\n".join(lines))
```

The `telegram_helper.py` uses only stdlib (`urllib`), no external packages.
Token/chat_id from environment variables (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).

## Auto-Cron Integration (Agent-Based)

```python
def setup_cron(schedule_type: str = "weekly"):
    schedules = {
        "weekly": "0 3 * * 0",   # Sunday 3 AM
        "daily":  "0 3 * * *",   # Daily 3 AM
        "monthly": "0 3 1 * *"   # 1st of month
    }
    cron_line = f'{schedules[schedule_type]} cd {script_dir} && python3 {script_path} scan --dry-run >> /tmp/cleaner.log 2>&1'
    # Append to crontab via `crontab -`
```

Agent-based cron should **always** run with `--dry-run`. Never auto-delete
without user review.

## Auto-Cron Integration (no_agent=True — Script-Based)

For deterministic, safe operations that don't need an LLM, use Hermes cron's
`no_agent=True` mode. This runs a standalone script on schedule and delivers
its stdout verbatim — no tokens consumed, no agent loop.

```bash
hermes cron create "0 8 * * 0" \
  "Wöchentliche Reinigung" \
  --no-agent \
  --script ~/bin/my-script \
  --name my-job \
  --workdir /home/bratan
```

**When is no_agent=True appropriate?** Server-side operations with fixed
thresholds (IMAP SEARCH BEFORE X date), deterministic actions, scripts that
handle errors gracefully. NOT for tasks needing reasoning or variable actions.

**Script pattern:** print + log simultaneously. Print() goes to stdout
(delivered to user). Log() writes to a file AND prints, so both get the same info.
Handle errors, timeouts, and edge cases independently — no LLM to explain failures.

## Hermes Integration (Agent Cron)

For recurring cleanup, register as a cron skill that loads this skill and runs:

```bash
hermes cron create "0 8 * * 0" \
  "Lade linux-system-maintenance Skill. Scanne mit Dry-Run. \
   Wenn > 5 GB gefunden, sende Zusammenfassung und frage nach Clean." \
  --skill linux-system-maintenance
```

## Multi-Tool Testing Pattern

When the user asks to test multiple new tools ("der Reihe nach"):

1. **Test in order of dependency** — simplest/fastest first, most complex last
2. **One tool at a time** — test, verify output, then move to next
3. **Fix immediately** — if a tool errors, patch the code and re-test before
   touching the next tool. Never batch-test without verifying each.
4. **Final confirmation** — after all pass, present the success summary
5. **Document** — update `~/docs/builds/README.md` with any new info discovered
   during testing

This avoids confusion where error output from tools 2+ gets mixed with
successful output from tool 1, and stops broken tools from being marked as
"works" without verification.