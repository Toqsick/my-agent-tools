# Stdlib-Only CLI Tool Building Pattern

Built 2026-06-03 during session with Basti (DeepSeek V4 Flash).
Three tools created: sysdoctor, greysync, gmail-organizer (renamed from gmail-cleaner).

## Rationale

When the user wants system tools with **zero pip install** overhead,
the stdlib-only approach avoids dependency hell, works immediately,
and keeps ~/projects/ portable across machines.

## Architecture Template

```
~/projects/<tool>/
├── <tool>.py          # Single-file CLI with argparse + subprocess

~/.local/bin/<tool> -> ~/projects/<tool>/<tool>.py  (symlink in PATH)
```

## Tool Renaming Workflow

When the user asks to rename a tool (e.g., `gmail-cleaner` -> `gmail-organizer`):

```bash
# 1. Rename the Python file
mv ~/projects/<old-name>/<old-name>.py ~/projects/<old-name>/<new-name>.py

# 2. Remove the old symlink and create the new one
rm -f ~/bin/<old-name>
ln -sf ~/projects/<old-name>/<new-name>.py ~/bin/<new-name>

# 3. Update the Python file internals (name, docstring, help text)
# Use execute_code with read+replace+write for bulk changes
python3 -c "
content = open('~/projects/<old-name>/<new-name>.py').read()
content = content.replace('<old-name>', '<new-name>')
# Also update the title/header text
content = content.replace('GMAIL-CLEANER', 'GMAIL-ORGANIZER')
content = content.replace('Email Cleaner', 'Email Organizer')
with open('~/projects/<old-name>/<new-name>.py', 'w') as f:
    f.write(content)
"

# 4. Rename the project directory
mv ~/projects/<old-name> ~/projects/<new-name>

# 5. Fix the symlink (it's now broken because the directory moved)
ln -sf ~/projects/<new-name>/<new-name>.py ~/bin/<new-name>

# 6. Update documentation (~/docs/builds/README.md and ~/docs/system/README.md)
# Use execute_code with bulk replace again

# 7. Update memory entry
# memory(action='replace', old_text='old-name', content='new-name...')

# 8. Test the new name works
<new-name> --help
```

**Verify after each step.** The symlink will break after step 4 (directory rename)
and MUST be re-created in step 5.

When doing this via patch: patch is risky for bulk renames across a file.
Prefer `execute_code` with Python file I/O (read, regex-replace, write atomically).
Reserve `patch` for single unique replacements with clear surrounding context.

## Key Patterns

### run() Helper

```python
def run(cmd, capture=True, sudo=False, timeout=30):
    """Return (stdout, returncode, stderr)."""
    full_cmd = ["sudo"] + cmd if sudo else cmd
    try:
        r = subprocess.run(full_cmd, capture_output=capture, text=True, timeout=timeout)
        return r.stdout.strip(), r.returncode, r.stderr.strip()
    except FileNotFoundError:
        return "", -1, f"[!] Befehl nicht gefunden: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return "", -1, "[!] Timeout"
```

Always return 3-tuple. Pass `timeout=N` for long-running commands.

### err_msg() Helper

```python
def err_msg(code, err):
    if err:
        if "terminal erforderlich" in err:
            return "sudo notig - im echten Terminal ausfuhren"
        return err[:120]
    return f"Fehler (Code {code})"
```

### Parse Human-Readable Sizes

```python
def parse_human_size(s):
    s = s.replace(",", ".")
    m = re.match(r"([\d.]+)\s*([KMGTPE]?)(i?)", s)
    if not m: return 0.0
    val = float(m.group(1))
    unit = m.group(2)
    if unit == "K": val *= 1024
    elif unit == "M": val *= 1024**2
    elif unit == "G": val *= 1024**3
    elif unit == "T": val *= 1024**4
    return val
```

### size_human() / du()

```python
def size_human(b):
    if b < 1024: return f"{b} B"
    elif b < 1024**2: return f"{b/1024:.1f} KB"
    elif b < 1024**3: return f"{b/1024**2:.1f} MB"
    else: return f"{b/1024**3:.1f} GB"

def du(path):
    try:
        r = subprocess.run(["du", "-sb", str(path)], capture_output=True, text=True, timeout=10)
        return int(r.stdout.split()[0])
    except: return 0
```

### Top-N Directory Scanner

Use `find` + `du -sb` (NOT `du --exclude` which has syntax quirks):

```python
def check_top_dirs(n=8):
    r, _, _ = run(
        ["find", home, "-maxdepth", "2", "-type", "d",
         "-not", "-path", "*/.*", "-not", "-path", "*/.npm/*",
         "-not", "-path", "*/.cache/*",
         "-exec", "du", "-sb", "{}", ";"], timeout=15)
    dirs = []
    for line in r.split("\n"):
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit():
            dirs.append((int(parts[0]), " ".join(parts[1:])))
    dirs.sort(reverse=True)
    return dirs[:n]
```

### JSON Config Persistence

```python
CONFIG_FILE = Path.home() / ".tool-name.json"
DEFAULT_CONFIG = {"key": "value"}

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        merged = DEFAULT_CONFIG.copy()
        merged.update(cfg)
        return merged
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)
```

### Dict-Dispatch CLI (no argparse)

```python
def main():
    import sys
    cmds = {"check": cmd_check, "clean": cmd_clean, "init": cmd_init}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print("Usage: ...")
        return
    cmds[sys.argv[1]](sys.argv[2:])
```

### JSON + Dry-Run Flags via Manual Parse

```python
def cmd_check(args):
    show_json = "--json" in args
    try:
        ti = args.index("--top")
        n = int(args[ti + 1]) if ti + 1 < len(args) else 8
    except: n = 8
    if show_json:
        print(json.dumps(collect_all(args), indent=2))
        return

def cmd_clean(args):
    dry = "--dry-run" in args or "-d" in args
    clean_npm(dry_run=dry)
```

### --for-real Persistent Safety Toggle

```python
def main():
    args = sys.argv[1:]
    if "--for-real" in args:
        cfg = load_config()
        cfg["dry_run"] = False
        save_config(cfg)
        print("Dry-run deactivated!")
        args.remove("--for-real")
```

## Safety Patterns

1. **Dry-run is the default** — explicit opt-in for real operations
2. **`--for-real` flag** permanently disables dry-run in config (persistent!)
3. **`init` subcommand** for interactive credential setup
4. **Chmod 600** on config files containing passwords/tokens
5. **Fallback chains**: try method A -> try method B -> report failure

## Documentation Integration

After building, add to `~/docs/builds/README.md`:
```markdown
**Pfad:** `~/projects/<tool>/<tool>.py` -> `~/bin/<tool>`
### Commands
| Command | Description |
```

## Tools Built With This Pattern

| Tool | Purpose | Lines | Version |
|------|---------|-------|---------|
| `sysdoctor` | System check + cache cleanup | ~540 | 2.1 |
| `greysync` | Greyhack script deployer | ~330 | 2.1 |
| `gmail-organizer` | Gmail IMAP organizer | ~540 | 2.1 |

## What This Pattern Does NOT Handle

- Rich TUI output (use `linux-system-maintenance` skill's rich approach)
- psutil-based system monitoring
- Multi-module directory structures
- Telegram/cron notifications
