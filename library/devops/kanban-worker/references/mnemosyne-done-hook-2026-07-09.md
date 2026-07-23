# Kanban → Mnemosyne done_hook Implementation (2026-07-09)

> Part of: `kanban-worker` — reference documenting the first concrete done_hook
> deployment, serving as an implementation example for the pattern in SKILL.md

## Setup (Welle 1 — Foundation)

### Multilingual Embedding + sqlite-vec

**`~/.hermes/mnemosyne/config.env`:**

```bash
export MNEMOSYNE_EMBEDDING_MODEL="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
export MNEMOSYNE_VEC_TYPE="sqlite_vec"
export MNEMOSYNE_WM_MAX_ITEMS="5000"
```

- `paraphrase-multilingual-MiniLM-L12-v2` (384-dim, ~120MB) = supported by fastembed, covers DE+EN+more.
- `sqlite_vec` = uses sqlite-vec ANN extension (0.1.9) for vector search, instead of int8/binary fallback.
- Sourced by both the sleep cron and the done_hook script explicitly.
- **Pitfall:** `MNEMOSYNE_VEC_TYPE` in env does NOT retroactively change already-created episodic tables. The DB's `episodic_vec_type` is set at creation time. After changing to sqlite_vec, run `mnemosyne diagnose --fix` to rebuild.

### Sleep Nacht-Cron

`50-System/bin/mnemosyne-sleep-cron.sh`:

```bash
#!/bin/bash
source /home/bratan/.hermes/mnemosyne/config.env
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
BACKUP_DIR="$HERMES_HOME/state/mnemosyne-sleep-backups"
mkdir -p "$BACKUP_DIR"
gzip -c "$HERMES_HOME/state/episodic.db" > "$BACKUP_DIR/mnemosyne-$(date -Iseconds).db.gz"
# Rolling 7-day cleanup
find "$BACKUP_DIR" -name "*.db.gz" -mtime +7 -delete

python3 -m mnemosyne.cli sleep  # Konsolidierung + Re-Embedding
python3 -m mnemosyne.cli verify --quick
python3 -m mnemosyne.cli stats > "$HERMES_HOME/state/mnemosyne-last-sleep.txt"
```

- **Crontab:** `30 2 * * *`
- **Log:** `/home/bratan/logs/mnemosyne-sleep.log`
- **Important:** CLI is `python3 -m mnemosyne.cli`, NOT `python3 -m mnemosyne` — the top-level package has no `__main__`.

### PEP 668 venv pitfall

The Hermes agent venv at `~/.hermes/hermes-agent/venv/` has PEP 668 active. `pip` is NOT the binary — use `pip3`. The Mnemosyne-Provider's `diagnose --fix` tries to install outside the venv and fails. Install manually:

```bash
/home/bratan/.hermes/hermes-agent/venv/bin/pip3 install sqlite-vec
```

## Schema Migration (Welle 2)

### `tasks.mnemosyne_ref` column

Two changes in `hermes_cli/kanban_db.py`:

1. **`SCHEMA_SQL`:** Added `mnemosyne_ref TEXT` to the `CREATE TABLE tasks (...)` string (for fresh DBs).
2. **`init_db()`:** Added:
   ```python
   _add_column_if_missing(conn, "tasks", "mnemosyne_ref", "TEXT")
   conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_mnemosyne_ref ON tasks(mnemosyne_ref)")
   ```

**Idempotence verified:** `init_db()` ran a second time — no error, column still single, index not duplicated.

## Done Hook Script

**`50-System/bin/kanban-done-hook.py`** (full script at that path):

### Core flow
1. Receives `(task_id, title, body_b64, result_b64, assignee)` as sys.argv[1:6].
2. Decodes base64 fields, builds content string: `Task: <title>\nBody: <body>\nResult: <result>\nAssignee: <assignee>`.
3. Determines Mnemosyne bank name via CWD:
   - If CWD contains `10-Projekte/<name>` → `kanban-<project-name>`
   - Otherwise → `kanban` (default)
4. Spawns `python3 -m mnemosyne.cli store "<content>" "kanban:<task_id>" 0.6` (30s timeout).
5. Parses memory ID from stdout (`Stored: <hex>` → regex `[0-9a-f]{8,64}`).
6. Opens a **separate** sqlite3 connection to kanban DB and writes `UPDATE tasks SET mnemosyne_ref = ? WHERE id = ? AND mnemosyne_ref IS NULL`.

### Bank auto-detection code
```python
def _memory_bank_for_cwd() -> str:
    cwd = Path.cwd()
    try:
        parts = cwd.relative_to(Path.home()).parts
        for i, part in enumerate(parts):
            if part == "10-Projekte" and i + 1 < len(parts):
                proj = parts[i + 1].lower().replace(" ", "-")
                return f"kanban-{proj}"
    except Exception:
        pass
    return os.environ.get("MNEMOSYNE_BANK", "kanban")
```

### DB path resolution in hook
```python
def _kanban_db_path() -> str:
    if "KANBAN_DB_PATH" in os.environ:
        return os.environ["KANBAN_DB_PATH"]
    try:
        from hermes_cli import kanban_db as _kdb
        return str(_kdb.kanban_db_path())
    except Exception:
        return str(Path.home() / ".hermes" / "state" / "kanban.db")
```

## E2E Test Results

```
[1] Created task: t_164f2972
[2] complete_task returned: True
[3] Waiting 6s for done_hook subprocess...
[4] Status: done
[4] mnemosyne_ref: 91b4daee06c5c594
[4] Result-Preview: E2E-Test erfolgreich: done_hook hat gefeuert, Mnemosyne-Capture lief....
```

Mnemosyne recall (semantisch, multilingual):
```
Results for: Kanban done_hook Mnemosyne capture
  ID: 91b4daee06c5c594
  Content: Task: E2E Test: Kanban done_hook fires Mnemosyne capture
  Score: 0.548   ← Top-Hit
```

## ENV Reference

| Variable | Default | Zweck |
|----------|---------|-------|
| `MNEMOSYNE_EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Überschrieben auf multilingual |
| `MNEMOSYNE_VEC_TYPE` | `int8` (binary fallback) | `sqlite_vec` für ANN-Index |
| `MNEMOSYNE_WM_MAX_ITEMS` | unset | 5000 = Soft-Cap für Working-Memory |
| `MNEMOSYNE_BANK` | `kanban` | Bank-Name; überschreibt Auto-Detect |
| `KANBAN_DONE_HOOK` | `~/50-System/bin/kanban-done-hook.py` | Hook-Pfad-Override |
| `KANBAN_DB_PATH` | resolved via `kanban_db.kanban_db_path()` | DB-Pfad-Override |
| `HERMES_VENV_PYTHON` | `~/.hermes/hermes-agent/venv/bin/python3` | Python-Binary für Hook |

## Full system documentation

See `~/docs/system/mnemosyne-tweaks-2026-07-09.md` (8.6 KB) — rendered with all migration details, test transcripts, and decision rationale.