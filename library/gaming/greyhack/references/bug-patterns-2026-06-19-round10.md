# GreyScript Bug Patterns — 2026-06-19 Round 10

## Scan Details

**Index range:** 71–80 (active files, excluding backups)
**Files scanned:** 10
**New bugs found:** 5
**Clean files:** 5

## Scanned Files

1. `portscan/portscan.src` — Clean (good input validation, error handling)
2. `progress-bar/progressBar.src` — Clean (well-structured library)
3. `ps/ps.src` — **2 bugs found** (BUG-1, BUG-2)
4. `ransomeware/ransomeware.src` — Structurally acceptable
5. `routerinfo/routerinfo.src` — **2 bugs found** (BUG-4, BUG-5)
6. `scp_upload/scp_upload.src` — **1 bug found** (BUG-3)
7. `smtp_enum/smtp_enum.src` — Clean (excellent validation)
8. `src/buildcore.src` — Clean (good error-handling patterns)
9. `src/cli_core.src` — Clean
10. `src/cliFeedback.src` — Clean

## New Patterns

| ID | Pattern | Severity | Files |
|----|---------|----------|-------|
| NP-58 | **Unvalidated array access after split()** — Accessing `line[N]` without checking `line.len >= N+1`. Fragile parsing crashes when API output format varies (empty lines, missing columns, unexpected delimiters). | HIGH | `ps/ps.src:25-28` |
| NP-59 | **Wrong type-check logic: `is_binary` as folder detector** — Using `file.is_binary` in a boolean context to determine if a path is a directory. `is_binary` checks content encoding (text vs binary), NOT directory status. A directory can return `is_binary == true`. The comment on the same file even warns about this but the code still uses it. Use `if not f.is_binary then` with null-check first, or check file extension. | HIGH | `scp_upload/scp_upload.src:83` |
| NP-60 | **String concatenation in render function** — Using `r = r + ...` pattern in a function called per render frame. Each `+` allocates a new string object. Not a performance bug for single calls but compounds in loops. | LOW | `ps/ps.src:45-53` |
| NP-61 | **Potentially undefined function name** — `validIP(p)` used but not a documented GreyScript standard library function. The canonical name is `is_valid_ip()`. If the function exists via an import, this is fine; otherwise it's a runtime crash. | LOW | `routerinfo/routerinfo.src:27` |
| NP-62 | **Property access without null-check on API objects** — Directly accessing `.public_ip`, `.essid_name`, `.bssid_name` on router objects without intermediate null-check. If the API doesn't provide these fields, output shows "null" or crashes depending on GreyScript version. | LOW | `routerinfo/routerinfo.src:51-56` |

## Known Patterns Confirmed

| Pattern | File | Notes |
|---------|------|-------|
| NP-59 (is_binary folder) | `scp_upload/scp_upload.src:83` | Comment on line 46 explicitly warns about this |
| Hardcoded log path | `scp_upload/scp_upload.src:106` | `/home/Bratan/.logs/scp_upload.log` hardcoded |
| Hardcoded log path | `smtp_enum/smtp_enum.src:136` | `/home/Bratan/.logs/smtp_enum.log` hardcoded |

## Clean Files Analysis

- **portscan.src**: Uses `is_valid_ip()`, null-checks router, proper step pattern, clean summary output
- **progressBar.src**: New library, well-structured state pattern, input validation via `__parseStyle()`
- **smtp_enum.src**: Triple type-checking on crypto result, proper save-dir creation, good error messages
- **buildcore/src**: Reusable safe* wrapper functions with consistent error handling
- **cli_core/src / cliFeedback.src**: Utility libraries with no external state dependencies

## Statistics
- **Files scanned:** 10
- **New NP patterns:** 5 (NP-58 through NP-62)
- **Known patterns confirmed:** 3 occurrences
- **Clean files:** 5 (50%)
- **Cumulative total (all rounds):** 32 NP patterns across 50+ files
