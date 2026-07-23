# GreyHack Tools Repo Restructure — 2026-06-27

## What Changed

User restructured `~/greyhack-tools/` (Toqsick/greyscripts) from flat tool directories into a new hierarchy:

### Key Structural Changes
- **Old**: Each tool in its own directory with local copies (`lib_core/lib_core.src`, `bin/lib_core.src`)
- **New**: Centralized libraries in `bin/` and `src/`, tools reference shared libraries
- **New directories**: `src/crypto/`, `src/lib/`, `src/security/`, `src/tools/`
- **Removed root-level duplicates**: `lib_core.src` at root replaced by `bin/lib_core.src`
- **Tests moved**: `test/` → `tests/` with `tests/legacy/` and `tests/test_<name>.src`
- **New tools in `src/tools/`**: `cli_core.src`, `recon_lite.src`, `mission_report.src`, `suid_exploit.src`

### Old vs New Path Mapping
| Old Path | New Path |
|----------|----------|
| `lib_core/lib_core.src` | `bin/lib_core.src` |
| `includes/std.src` | `src/lib/std.src` |
| `includes/ftzi_std.src` | `includes/ftzi_std.src` (kept) |
| `test/test_core.src` | `tests/legacy/test_core.src` |
| `bin/lib_core.src` (deprecated) | `bin/lib_core.src` (still exists as primary) |

### Build Impact & Fix Strategy
After restructure, 80/105 .src files failed `greybel build` due to broken import paths.

**Root cause**: greybel resolves `import_code` paths relative to the **source file's directory**, not CWD.

**Fix approach**:
1. Identify file depth from repo root
2. Prefix import paths with `../` * depth
3. Map old filenames to new locations

**Python bulk fixer** (see SKILL.md Rule 4) handled most files. Remaining issues:
- 5 files with genuine syntax bugs (unclosed if-blocks, inline-if, unescaped quotes)
- 8 files with double-nested dependency paths (needed manual inspection)
- 2 missing files (`build/lzw.src`, `test/test_core.src`)

### CI Matrix Status
`.github/workflows/greyscript-build.yml` — 31/31 matrix files build successfully after fixes.
The CI matrix is a **whitelist** — it only tests files GitHub knows about, not all 105 .src files.

### Cron Jobs Cleanup
Removed 4 broken cron jobs that referenced deleted scripts:
- `greyhack-daily-scan` (error)
- `greyhack-daily-fix` (error)
- `esl-tech-news` (user request)
- `greyscripts-daily-status` (user request)

### Lessons
1. **Always check CI matrix first** — it defines the "must build" whitelist
2. **greybel path resolution is file-relative** — `bin/metaxploit.src` + `import_code("bin/lib_core.src")` → `bin/bin/lib_core.src` ❌
3. **Depth-based prefix calculation** is the reliable pattern for bulk fixes
4. **Don't blindly add `../`** — verify the file's actual depth first
5. **CI ≠ full build** — files outside the matrix (installer/, chat-app/, some tests/) may still be broken
