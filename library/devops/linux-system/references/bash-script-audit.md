# Bash Script Audit — Full Reference

Extracted from the `bash-script-audit` skill.

## Workflow
1. **Inventory:** Find all bash scripts (`search_files(pattern="*.sh")`)
2. **Analysis:** ShellCheck + manual pattern scan
3. **Fix:** One bug per change, verify after each
4. **Verification:** `bash -n script.sh` + run modified script

## Common Bash Bugs
| # | Pattern | Symptom | Fix |
|---|---------|---------|-----|
| 1 | **YAML-sed** | `sed -i` on config.yaml matches multiple lines | Python yaml.safe_load/dump |
| 2 | **Dead code** | Script tries to start removed service | Remove or add check |
| 3 | **Outdated commands** | CLI binary renamed | Update syntax |
| 4 | **Double-eval** | `$(cmd)` evaluated twice | Store in variable first |
| 5 | **Missing deps** | Script calls uninstalled tool | Add check + error message |
| 6 | **Race conditions** | No wait-loop for hardware | Add poll-with-timeout |
| 7 | **Hardcoded paths** | `/home/bratan/` instead of `$HOME` | Use `$HOME` |
| 8 | **Error handling** | `set -e` missing | Add `set -euo pipefail` |
| 9 | **Config drift** | References old config keys | Audit and update |
| 10 | **`set -e` + side-effect failure** | Secondary call fails, kills script | `\|\| true` or `if`-block |
| 11 | **`cp` as SQLite backup** | Corrupt backups (mid-WAL-copy) | Use `sqlite3 .backup` |
| 12 | **Backup verification** | 0-byte backup passes "OK" | Check size + `PRAGMA integrity_check` |
| 13 | **flock wrong** | fcntl vs flock(1) incompatible | `exec 9>file; flock -n 9` |
| 14 | **`$?` with pipefail** | Wrong exit code logged | `${PIPESTATUS[0]}` |
| 15 | **`cd` without check** | Script dies, no error log | `cd "$DIR" \|\| { log "ERROR"; exit 1; }` |
| 16 | **Cron deps not in venv** | sqlite3, jq missing | Add `command -v` checks |

## YAML Editing via sed — NEVER DO THIS
```bash
# BAD — matches 18+ lines
sed -i 's/^  provider:.*/  provider: nous/' config.yaml

# GOOD — Python
python3 -c "
import yaml
with open('$CONFIG') as f:
    cfg = yaml.safe_load(f)
cfg['model']['provider'] = 'nous'
with open('$CONFIG', 'w') as f:
    yaml.dump(cfg, f, default_flow_style=False)
"
```

## SQLite Backup Pattern
```bash
# BAD — produces corrupt backups
cp db.db backup.db

# GOOD — consistent snapshot
sqlite3 db.db ".backup 'backup.db'"
sqlite3 backup.db "PRAGMA integrity_check;"  # must return "ok"

# Verify minimum size
SIZE=$(stat -f%z backup.db 2>/dev/null || stat -c%s backup.db)
[ "$SIZE" -lt 1024 ] && { rm -f backup.db; exit 2; }
```

## flock Pattern
```bash
# Correct non-blocking lock
LOCK_FILE="/tmp/my-cron.lock"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    log "SKIP: another run holds $LOCK_FILE"
    exit 0
fi
# ... do work ...
```
