# GreyHack `build` Command Internals (V0.9.6771-beta)

> Reverse-engineered 2026-07-03 during Yuno V6 deployment session.
> Verified against live DB, Player FileSystem JSON, and real in-game shell output.

## `build` Syntax

```bash
build <source-path> <dest-folder>
```

- `source-path` = path to a `.src` file (must exist, must have `//command: <name>` first line)
- `dest-folder` = path to an EXISTING folder (not a file!)
- Output: a binary version of the source placed in `dest-folder/` with the source's name (minus `.src`)

## Under the Hood (`get_shell.host_computer.shell.build()`)

The GreyScript API call `shell.build(fileSource, folderDest)` takes **File objects**, not strings. The terminal command `build` converts string paths to File objects before calling the API.

## All Error Messages (and What They Actually Mean)

| Error | What the Game Says | What It Actually Means |
|-------|-------------------|----------------------|
| ❌ "build: can't find SOURCE" | The source file doesn't exist at that path | Typo in source path, or file was deleted/not yet created |
| ❌ "build: can't find DEST" | The destination FOLDER doesn't exist | Run `mkdir <dest-folder>` first. The error is misleading — it mentions the output file name, not the missing folder |
| ❌ "Can't build FILE. Invalid extension." | The destination has a wrong extension or the path doesn't resolve to a folder | Most Common: `build /src.src /dest/something` where `/dest/` doesn't exist. The error mentions "extension" but the real issue is a missing parent folder |
| ❌ "Can't build FILE. Binary file." | The source is not recognized as a script | Four possible causes: (a) first line is NOT `//command: <name>`, (b) DB Content field is empty/missing, (c) `isBinario: true` in FileSystem JSON for the source, (d) file was already compiled (isBinario flipped) |
| ❌ "FILE: command not found" | The shell command `<name>` doesn't exist | Source not in Config/, missing `//command:` marker, OR game restart needed |

## Why "build" Is NOT the Right Target for User Scripts

**Key insight from 2026-07-03:** User scripts with `//command:` marker placed in `/home/<USER>/Config/` do NOT need `build` at all. The `build` command produces binaries for `/bin/` system-level tools that get recompiled per session.

**How to deploy user scripts:**
1. Place source in `/home/<USER>/Config/<name>.src` (via copy-paste or DB injection)
2. Ensure first line is `//command: <name>`
3. Restart game
4. Type `<name>` in shell — GreyHack loads it automatically

**When `build` IS appropriate:**
- Compiling tools that need to go into `/bin/`
- Forcing a syntax check on a `.src` file
- Testing compilation before DB injection

## Source Size Limit for `//command:` Commands

Largest reliably-observed `//command:` source in the live DB: **`ftp` at 12,210 bytes**.

Attempted to deploy `yuno_v6` at **78KB** with correct `//command:` marker — the file was present in Config/ and visible via `ls`, but the command `yuno_v6` returned "command not found".

**Conclusion:** GreyHack's startup scan that registers `//command:` sources skips files above a threshold (~12KB estimated). Sources exceeding this limit must be loaded via CodeEditor, `pc.wget()`, or modular split into sub-commands under 12KB each.

## Game Restart Requirement

**Critical:** New `.src` files in Config/ with `//command:` markers are ONLY registered at game startup. Mid-session DB injection of a new command file will NOT make it available until the player quits to desktop and re-enters. This is a security design (prevents live code injection).

## File Attributes Required in DB

For a source to be recognized as a command:

| Attribute | Value | Reason |
|-----------|-------|--------|
| `//command:` | `<name>` as Content first line | Magic marker |
| `isBinario` | `false` | Source = not compiled |
| `typeFile` | `0` | Regular file |
| `comando` | `""` (empty!) | Not a macro/command string |
| `size` | `len(Content)` | Must match actual content length |
| `allowImport` | `true` | Can be import_code'd |
| Location | `/home/<USER>/Config/` | Command directory |

## `run` and `launch` Commands

**Neither command exists in V0.9.6771-beta.** Despite many old source headers saying "Usage: run yuno_v2", the `run` shell command and `launch` shell command are both deprecated/removed.

The replacement:
- **Old:** `run /path/to/script.src`
- **New:** place in Config/ with `//command:` + game restart, then type `<name>`

## References

- `greyhack-greyscript/references/sqlite-database.md` — DB schema and injection details
- `greyhack-greyscript/references/deployment.md` — Full deployment methods
