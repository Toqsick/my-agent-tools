# YUNO VIPER Util Module — Build Session (2026-07-04)

## What was built

A 660-line `yuno_viper_util.src` module with 25 commands (24 in `h` dict + `@-macro` handler). Placed at:
`/home/bratan/greyhack-tools/yuno_viper/modules/yuno_viper_util.src`

## Module structure

- Header: `//command: yuno_viper_util` (line 1) + `//include: yuno_viper_core` (line 2)
- Each command: `UtilX = {}` declaration + `UtilX.run = function(Cc)` body
- Registration: `if not h then h = {} end if` + `h["cmd"] = UtilX` (at file end)
- Final print: `print(N("[OK] yuno_viper_util geladen: 24 Befehle registriert", I.FD))`

## Globals used (from yuno_viper_core)

| Pattern | Purpose |
|---------|---------|
| `Z` | Computer object (shell.host_computer) |
| `P` | Profiler state (current_user, buffer, snapshots, plugins, backups) |
| `I.F*` | Constants (colors, paths, special chars) |
| `N(text, color)` | Colorized output wrapper |
| `g` | Current theme string |
| `O(theme)` | Theme-switch function |

## Convention: Var naming within UtilX.run

All variables inside `run` use single-letter or short codes for bytecode compression:

- `BX` = computer (from Z)
- `BE` = home path
- `Ck`, `Cd`, `Do`, `Dp`, `DG`, `Cz` = files/folders/paths
- `BZ` = file content string
- `Ba` = split lines array
- `Cc` = command arguments (function parameter)
- `Dy`, `DM` = parent path + filename (from path split)
- `BV`, `D_`, `Bs` = objects/procs (various types)
- `Eo`, `Bu` = snapshot/backup data maps
- `Bq` = user_input result

## Command list (all 24 in h)

| h-key | Name | Sub-commands | Notes |
|-------|------|-------------|-------|
| ls | UtilLs | — | Lists /home/user by default, colorized dirs/files |
| cat | UtilCat | — | Line numbers, binary-detect |
| write | UtilWrite | > (overwrite), >> (append) | One-line user_input |
| rm | UtilRm | -f (force skip confirm) | Confirmation prompt default |
| chmod | UtilChmod | — | Supports 777, 755, 644, 700 |
| save | UtilSave | [name] | Writes .sav file, stores in P.snapshots |
| restore | UtilRestore | [name] | Lists all if no arg, restores theme + user |
| backup | UtilBackup | [path] | Stub — counts sources, increments P.backups |
| update | UtilUpdate | [force] | Version display stub |
| notes | UtilNotes | add, clear | Persistent via /Config/notes.txt |
| movies | UtilMovies | — | Static hacker-movie list |
| macros | UtilMacros | rm | Lists /Macros/ files |
| vshell | UtilVshell | — | Mini-subshell (echo/help/exit) |
| repeat | UtilRepeat | [n] | Reads from P.buffer |
| homework | UtilHomework | add, clear | Persistent via /Config/homework.txt |
| sudo | UtilSudo | su | Status display + su-stub |
| killer | UtilKiller | — | Process kill by name |
| rl | UtilRl | [n] | ReadLine history from P.buffer |
| cache | UtilCache | clear, stats | Manages P.buffer |
| copy | UtilCopy | — | File copy via get_content+set_content |
| script | UtilScript | — | Multi-line user_input → file |
| grant | UtilGrant | — | chmod 777 recursive |
| konfig | UtilKonfig | set KEY=VAL, get KEY | Persistent /Config/yuno.cfg |
| special | UtilSpecial | msf, games (1/2/3), jokes | Mini-games + metasploit stub |

## @-macro handler

`UtilAtMacro` is called by the main loop (NOT registered in `h`). Reads `/home/user/Macros/<name>`, splits by newlines, skips comments (`#`).

## File I/O pattern (used by ~10 commands)

```greyscript
// 1. Touch (create parent if needed)
BX.touch(ordner, dateiname)
// 2. Open
Cd = BX.File(pfad)
// 3. Check
if not Cd then print(N("[!] ...", I.FC)); return
// 4. Read
BZ = Cd.get_content
if typeof(BZ) != I.FO then ...  // I.FO = "string"
// 5. Write
Cd.set_content(neuer_inhalt)
```

## Size: 660 lines, ~23 KB

The task asked for 500-600 lines. Actual size is 660 due to:
- Error handling for every command (null-checks, type-checks, user prompts)
- German usage/error strings
- ~10 commands with config-file persistence (notes/homework/konfig)
- @-macro handler with comment-skip logic
- Color output with N() wrapper everywhere
