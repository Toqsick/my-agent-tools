# GreyScript Bug Patterns — 2026-06-18

## Round 7 (Index 171–180)

Scanned files: `bin/decypher_v3.src`, `bin/filecore.src`, `bin/forcer.src`, `bin/grsa.src`, `bin/lib_core.src`, `bin/metaxploit.src`, `bin/portscan.src`, `bin/ps.src`, `bin/routerinfo.src`, `bin/scp_upload.src`

### New Patterns

| ID | Pattern | Severity | Files |
|----|---------|----------|-------|
| NP-49 | `"char(10)"` string literal vs `char(10)` | HIGH | `forcer.src:14` |
| NP-50 | Variable referenced outside defining scope | HIGH | `decypher_v3.src:72-81` |
| NP-51 | Password as CLI parameter | MEDIUM | `scp_upload.src:19` |
| NP-52 | `rnd` without seed for crypto | MEDIUM | `grsa.src:83-86` |

### Known Patterns Confirmed in New Files

| Pattern | Files |
|---------|-------|
| Hardcoded `/root/lib_core/lib_core.src` import | `bin/metaxploit.src:8`, `bin/routerinfo.src:8` |
| Hardcoded `/home/Bratan/.logs/` paths | `bin/metaxploit.src:63,113`, `bin/scp_upload.src:71` |
| Hardcoded user "Bratan" | `bin/lib_core.src:103-107` |
| Missing bounds check on split fields | `bin/ps.src:24-38` (same as backup NP pattern) |
| No try/catch on external calls | `bin/forcer.src:22-34` (get_shell in loop) |

### Clean Files (no new issues)

- `bin/filecore.src` — Excellent error handling, null checks on all File operations, proper use of `typeof` for error detection
- `bin/lib_core.src` — Well-structured utility library (hardcoded paths pre-existing issue, not new)

### Statistics
- **Files scanned:** 10
- **New bugs found:** 4 (4 NP patterns)
- **Known patterns confirmed:** 8 occurrences across 6 files
- **Clean files:** 2
- **Cumulative total (all rounds):** 22 NP patterns, 91+ findings across 30+ files
