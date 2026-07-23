# GreyScript Bug Patterns — 2026-06-17 Scan

Automated scan of 31 .src files against 17 bug patterns. 91 issues found in 25 files.

## New Patterns (NP-18 through NP-21)

### NP-18: `is_folder` Usage
**Severity:** MEDIUM — `is_folder` is unreliable in GreyScript
**Fix:** Use `is_binary == false` for folders, `is_binary` for files

**Findings:** 10 occurrences across 7 files
- `fix_perms.src` (4 occurrences)
- `backdoor.src` (1)
- `gsc.src` (1)
- `lib_core.src` (1) — **FIXED 2026-06-17**
- `ransomeware.src` (2)
- `scp_upload.src` (1) — **FIXED 2026-06-17**
- `filecore.src` (1)

### NP-19: Single Quotes in Strings
**Severity:** MEDIUM — Can cause silent syntax failures

**Findings:** ~15 occurrences across 8 files
- `xmem.src` (8), `secure.src` (1) — **FIXED**, `wifi.src` (2), `getShell.src` (1), `gsc.src` (1), `launcher.src` (2), `ransomeware.src` (1)

### NP-20: Repeated `get_shell.host_computer`
**Severity:** LOW — Performance, should be cached
**Fix:** Store once: `shell = get_shell; pc = shell.host_computer`

- `decypher_v3.src` — 4 calls — **FIXED 2026-06-17**
- `bank_grabber.src` — 4 calls
- `secure.src` — 3 calls
- `xmem.src` — 3 calls

### NP-21: Multi-line Map Literals
**Severity:** MEDIUM — May not parse correctly

**Findings:** 2 occurrences in `gsc/Util.src` (lines 58, 77)
