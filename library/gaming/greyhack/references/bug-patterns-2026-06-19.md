# GreyScript Bug Patterns — 2026-06-19

## Round 8 (Index 11–20)

**Note:** These files are all from `backups/20260612_003843/`. The primary versions contain identical code. Findings are reported for completeness but represent the same bugs as would be found in the active files.

Scanned files: `chat-app/ChatInput.src`, `chat-app/ChatMain.src`, `dankestein/corrupt.src`, `dankestein/farRepo.src`, `dankestein/getShell.src`, `dankestein/getUser.src`, `dankestein/mapLAN.src`, `dankestein/secure.src`, `dankestein/wifi.src`, `decypher/decypher_v2.src`

### New Patterns

| ID | Pattern | Severity | Files |
|----|---------|----------|-------|
| NP-53 | `print("char(10)")` string literal in print — prints literal string "char(10)" instead of a newline. Same root cause as NP-49 but in `print()` context. | LOW | `dankestein/mapLAN.src:10` |
| NP-54 | Variable declared but never assigned, then used — `file = null` at top scope, but `file.has_permission("r")` called later without intermediate assignment. Always null-crash. | HIGH | `dankestein/getShell.src:33` |
| NP-55 | Hardcoded credentials in `connect_service()` — password as string literal in SSH connection call. Should come from config or user input. | HIGH | `dankestein/farRepo.src:2` |
| NP-56 | `input.len` on String from `user_input()` — checks character count of input string, not token count. `input` is a String, not a List. To check for multiple space-separated values, use `input.split(" ").len`. | MEDIUM | `dankestein/wifi.src:17` |
| NP-57 | `pass` as variable name — `pass` is a reserved keyword in some GreyScript versions. Using it as a variable name can cause parse errors or shadow the keyword. | LOW | `dankestein/wifi.src:62` |

### Known Patterns Confirmed in New Files

| Pattern | Files |
|---------|-------|
| NP-49 (char literal) | `dankestein/mapLAN.src:49` — `portPrint = portPrint + ("...char(10)")` |
| String concat in loop (NP-44) | `dankestein/wifi.src:10-14`, `dankestein/mapLAN.src:41-50` |
| Missing null-check before `.delete()` | `dankestein/corrupt.src:6` |
| Missing error handling on external calls | `chat-app/ChatInput.src:13`, `chat-app/ChatMain.src:9` |
| Missing input validation | `chat-app/ChatInput.src:9`, `dankestein/getShell.src:3` |
| Wrong condition check (portPrint) | `dankestein/mapLAN.src:52` — `if portPrint != "<i>      ["` compares against impossible string |

### Clean Files (no new issues)

- `dankestein/secure.src` — Proper parameter validation, recursive chmod with error checking
- `decypher/decypher_v2.src` — Already contains //FIX comments, guards on split results, type-checks on crypto calls
- `dankestein/getUser.src` — Well-structured with proper type checking (computer/shell/file branches)

### Statistics
- **Files scanned:** 10
- **New bugs found:** 5 (5 NP patterns)
- **Known patterns confirmed:** 6 occurrences across 5 files
- **Clean files:** 3
- **Cumulative total (all rounds):** 27 NP patterns, 100+ findings across 40+ files

### Lessons for Cron Job

1. **Backup files produce duplicate findings**: The sorted `find` list interleaves backup and active files. Scanning backups wastes cycles on already-known bugs. The cron prompt should filter with `grep -v '/backups/'` before indexing.
2. **Index drift**: With 269 total files (including backups) but only ~90 active files, the index will drift into backup territory after the first wrap-around. Build the filtered list FIRST, then index into it.
