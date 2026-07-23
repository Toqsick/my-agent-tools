# Config/ Deployment — Source Script Commands (V0.9.6771-beta)

> Verified 2026-07-03 on Basti's setup (Steam Native Linux, GreyHack 0.9.6771-beta)

## Core Discovery

**Source scripts in `/home/<USER>/Config/` with `//command:` marker are directly executable as shell commands — no `build` step needed.**

This was the critical missing piece. Previous documentation assumed `build + launch` was the workflow, but:
- `launch` command does NOT exist in V0.9.6771-beta
- `build` compiles to /bin/ binaries (non-persistent across restarts)
- Source scripts in `/home/<USER>/Config/` are auto-detected by the GreyHack shell

## Verified DB Schema (LIVE, not backup)

```sql
CREATE TABLE Files (
    ID TEXT PRIMARY KEY,
    Content TEXT,
    refCount INTEGER NOT NULL DEFAULT 1
);

-- NO named columns (nombre, computer_pk, content_type) in live V0.9.6771-beta!
-- Backups may have old schema with extra columns
```

**FileSystem JSON** lives in `Computer.FileSystem` as a nested folder/file JSON structure. The player's FS has ~79 linked files; the DB `Files` table has 236 total (157 orphaned — these are system /bin/ binaries and memory exploits not linked in player FS).

## FileSystem JSON Entry — Correct Fields

Minimal working entry for a source script in `/home/gregor/Config/`:

```json
{
  "ID": "<uuid>",
  "nombre": "yuno_v6.src",
  "size": 78155,
  "isBinario": false,
  "typeFile": 0,
  "allowImport": true,
  "comando": "",
  "permisos": {"permisos": "-rwxr-xr-x"},
  "owner": "gregor",
  "group": "gregor",
  "saved": true,
  "isProtected": false,
  "isDefaultContent": false,
  "precio": 0,
  "isEditedOtherPlayer": false,
  "origOwnerID": "",
  "desc": null,
  "helperImport": null,
  "passEncrypt": "",
  "symlink": "",
  "process": "",
  "serverPath": "",
  "missionID": ""
}
```

### Field Details

| Field | Correct Value | Wrong Value (common mistake) |
|-------|--------------|------------------------------|
| `isBinario` | `false` | `true` — only for /bin/ system binaries |
| `typeFile` | `0` | `1` — 0 = regular file, and source scripts ARE regular files |
| `comando` | `""` (empty) | `"run /path/script"` — game handles this via `//command:` |
| `size` | `len(Content)` | `0` — if size is 0, game treats it as empty |
| `allowImport` | `true` | `false` — must be true for `import_code` to work |
| `nombre` | `name.src` | without .src extension — .src IS required for detection |

## `//command:` Marker Format

The marker is parsed by GreyHack's shell to register commands from source scripts.

```
//command: command_name
// rest of script (comments, code, etc.)
```

**Rules:**
- MUST be the very first line of `Files.Content` (byte position 0)
- Colon+space after `//command:` is required
- Command name must match the filename (without .src) for consistency
- All 46 system source scripts in /bin/ use this pattern
- Scripts WITHOUT this marker trigger "Can't build. Binary file." if build is attempted, and won't auto-load as commands out of Config/

## Source Size Limits

| Measurement | Value |
|------------|-------|
| Biggest DB file (player FS) | 66 KB (verified live) |
| Biggest system /bin/ source | 1.9 KB (ls.src) |
| `yuno_v6` source | 78 KB (injected via SQLite, worked) |
| SQLite TEXT limit | ~2 GB (theoretical) |
| CodeEditor UI limit | ~30K characters (estimated) |

Files <30 KB → CodeEditor copy-paste works
Files 30-100 KB → DB injection via `INSERT INTO Files` with Content
Files >100 KB → Always DB injection (chunking unreliable)

## Build Command (for reference)

Still exists but NOT needed for user scripts in Config/:

```bash
build /path/source.src /existing-folder/
```

- Source must have `//command:` or build fails with "Binary file"
- Destination must be an EXISTING FOLDER or build fails with "can't find destination" (misleading!)
- Output is a /bin/-style binary with inflated size (~2M) and `isBinario: true`
- Outputs LOST on game restart (unlike Config/ sources)

## Common Mistakes (Session 2026-07-03)

1. **Source in /home/gregor/ root** — does NOT work. Must be in `/home/gregor/Config/`. The root-level files appear in `ls` but are NOT loaded as commands.

2. **`//command:` missing** — without it, file looks like a binary to the game. "Can't build. Binary file." even though `isBinario: false`.

3. **`size: 0` in FileSystem JSON** — game treats as empty even if Content exists in Files table. Always set `size = len(Content)`.

4. **`comando` filled** — older documentation says to set `comando: "run /path/..."`. This is WRONG. Leave empty.

5. **DB schema misconception** — old column names (nombre, computer_pk from backup schema) don't exist in live V0.9.6771-beta. Only `Files(ID, Content, refCount)`.
