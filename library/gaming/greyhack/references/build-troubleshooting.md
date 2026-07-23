# Build Troubleshooting & Pipeline

## Build Troubleshooting Quick Reference

| Problem | Cause | Fix |
|---------|-------|-----|
| `wget` returns 0 | Fileserver not running or wrong IP | Check `curl http://<IP>:8765/` from host |
| `shell.build()` returns null | Syntax error in .src | Check for single quotes, `\n` in strings, multi-line maps |
| `shell.build()` returns String | API error message | Read the string — it's the error description |
| Tool crashes at runtime | Missing null-checks | Add `if not result then exit("error")` after API calls |
| `import_code` fails | Wrong path | Use relative paths or verify file exists with `pc.File(path)` |

## greybel-js Build Pipeline

### Installation
```bash
npm install -g greybel-js
```

### Build Command
```bash
greybel build <input.src> <output_dir> -u -dbf -si
# -u       = uglify (minify)
# -dbf     = disable build folder (output directly, not in /build subdir)
# -si      = silent (suppress noise)
```

### greybel CLI Version Mismatch (CRITICAL pitfall, 2026-06-25)

There are **at least two different greybel CLIs**, and the command syntax differs:

| CLI | Build syntax | Out dir flag |
|-----|--------------|--------------|
| `greybel` (greybel-js 3.7+, NPM-installed) | `greybel build <file.src> <out-dir>` (positional) | No `--out-dir` flag |
| `greybel-js` (older npm package, possibly deprecated) | `greybel-js build <file.src> --out <out-dir>` | `--out` and `--type exe` flags |

**Detection:** Run `greybel build --help` or `greybel --help`. The output shows `Commands: build [options]  filepath [output]` for the newer CLI (positional out-dir).

**Symptoms of using wrong syntax:**
- `(Did you mean --port?)` → CLI doesn't recognize the flag
- `error: unknown option '--out'` → same as above

**Mitigation:** Always check `greybel build --help` first; use `scripts/ci-build.sh` (which detects both) instead of calling greybel directly.

## greybel-js Import Path Resolution — Definitive Rules

`greybel build` resolves `import_code` paths **relative to the source file's directory**, NOT the working directory. This is the single most common source of build failures.

**Rule 1: Path resolution is file-relative, not CWD-relative**
```
File: bin/metaxploit.src
Path in file: import_code("bin/lib_core.src")
greybel resolves to: bin/bin/lib_core.src  ← WRONG (prepends file's directory)
```

**Rule 2: Use `../` to go up from the file's directory**
```
File: bin/metaxploit.src (depth 1)
Correct: import_code("../bin/lib_core.src")
Resolves to: bin/../bin/lib_core.src = bin/lib_core.src ✓
```

**Rule 3: Depth-based prefix calculation**
For a file at depth N (N subdirectories deep from repo root):
- Files in repo root (depth 0): use `bin/lib_core.src` directly
- Files in 1 subdirectory (depth 1, e.g., `bin/`, `ps/`): use `../bin/lib_core.src`
- Files in 2 subdirectories (depth 2, e.g., `src/crypto/`): use `../../bin/lib_core.src`

**Rule 4: Bulk fix with Python (safer than sed for many files)**
```python
import os, re, glob

repo = '/home/bratan/greyhack-tools'
for f in glob.glob(f'{repo}/**/*.src', recursive=True):
    if any(s in f for s in ['.git', 'node_modules', 'backups', '.claude', 'installer']):
        continue
    depth = os.path.relpath(f, repo).count(os.sep)
    prefix = '../' * depth
    with open(f, 'r') as fh:
        content = fh.read()
    # Fix old absolute paths
    content = content.replace('/root/lib_core/lib_core.src', f'{prefix}bin/lib_core.src')
    with open(f, 'w') as fh:
        fh.write(content)
```

**Rule 5: `#import ... from "..."` syntax (ftzi style)**
The `#import` directive also resolves file-relative. Fix similarly:
```
File: includes/ftzi_lib.src
Old: #import Std from "std"
New: #import Std from "../src/lib/std.src"
```

**Symptom:** Build error `Dependency /home/bratan/greyhack-tools/includes/includes/std.src does not exist` — double directory prefix from incorrect relative path.

## Known greybel-js Incompatibilities

| Issue | Example | Fix |
|-------|---------|-----|
| Backslash-escaped quotes | `\\\"text\\\"` in strings | Use single quotes `'text'` |
| In-Game-only APIs | `shell.start_terminal` | Comment out: `// shell.start_terminal` |
| Missing `end function` | xmem.src (44 functions, 22 closes) | Manual fix required per file |
| Double closing parens | `import_code(\"lib_core\"))` | Remove extra `)` |
| Import path resolution | `../lib_core/lib_core.src` → resolved to `/root/lib_core/lib_core.src` | Copy .src files directly, then `sed -i` import paths |
| Code generators | installer.src, launcher.src | Cannot be built with greybel-js |
| Single-line `if/then/end if` | `if X then Y end if` | Use multi-line `if X then\nY\nend if` |
| Ternary expressions | `("a" if cond else "b")` | Not valid GreyScript — use if/else block |
| Bare `exit` | `exit` without `()` | Always use `exit()` |
| Unclosed if-blocks | `else` ... `end function` | Missing `end if` before `end function` |
| `=======` Section Separator | `=======` standalone line | Remove or replace with `// ---` comment |
| Backslash-Escape in `print()` | `print("  importcode(\\\"bin/lib_core.src\\\")")` | Use single quotes for inner path |
| Half-written functions (missing `end function`) | `safeCopy = function(...)` body but no closing | Scan backward when seeing "open block" errors |
| `if X then BODY` without `end if` | `if result != null then fail("…")` | Same as above — check preceding block |
| Inline-if assignment | `prefix = (" d " if e.is_dir else " f ")` | Replace with explicit `if/else/end if` |

## greybel Build Error Iteration Strategy
1. Run `greybel build <file.src> /tmp/out` for each failing file (NOT the full script, gives clearer error messages)
2. Fix the FIRST reported error (often masks others)
3. Re-run, get the next error
4. Build errors of the form "found open block X at line N" mean the actual bug is BEFORE line N — scan backward
5. After all individual files build clean, run the full `bash scripts/ci-build.sh --out-dir /tmp/ci-build-full` to confirm

**Validated sequence:** 13/15 files → 2 manual fixes → 15/15 green in ~6 iterations.

## Build Success Rate History

### 2026-06-17 — 11/12 buildable
- OK: lib_core, portscan, metaxploit, decypher, routerinfo, wifi_crack, forcer, scp_upload, ps, smtp_enum, grsa
- ❌ xmem (structural `end function` mismatch) → later fixed

### 2026-06-24 — 12/12 ALL TOOLS!
**12/12 buildable with greybel:**
- ✅ xmem (xmem/xmem.src) — formerly FAIL, fixed via `get_shell()` parameter removal
- ✅ src/buildcore.src, src/debugcore.src, src/security/hardening.src — 25 P0 syntax fixes
- ✅ src/netcore.src, src/libcore.src, src/lib/std.src — 11 P0 syntax fixes
- ✅ src/tools/recon.src, src/tools/portmon.src, src/tools/mxwrap.src — 11 P0 syntax fixes
- ✅ src/crypto/decypher.src — 3 inline-ternary fixes
- ✅ src/security/grsa_v2.src — 5 P0 syntax fixes
- ✅ includes/*, lzw/*, gsc/*, bltings/*, lib_core/* — build OK
- ✅ bin/* — build OK (deprecated copies)

## P0 Build Fixes — 2026-06-19

**Pass 1 — P0 core fixes:**
- Removed orphan/duplicate old blocks from `filecore.src`
- Removed merge marker `=======` from `filecore.src`
- Replaced all unsafe one-line `if ... then BODY end if` forms
- Replaced the invalid ternary expression in `filecore.src`
- Expanded one-line `if` blocks in `recon.src`
- Fixed `cli_core.src` `cli_table`: `for i in headers` iterates VALUES not indices → use `headers.indexes`
- Fixed `filecore.src`: `is_folder` → `not is_binary` (3 Stellen)
- Removed ghost `main` after `return false` in `filecore.src:187`
- Updated import path comments: absolute → relative in 6 files

**Pass 2 — 51 Syntax fixes for CI greenfield (18/18):**
- Expanded 48 one-line `if ... then BODY end if` to multi-line across 10 files
- Fixed `"` backslash escapes in setup.src → `'` single quotes (5 lines)
- Expanded 3 inline-if expressions in decypher.src
- Updated `.gitignore` for greybel build artifacts

Validated: `bash scripts/ci-build.sh --out-dir .ci-build` → `Build complete: 18 file(s) ok`

## CI Pipeline (GitHub Actions) — Added 2026-06-24
- `.github/workflows/greyscript-build.yml` — Matrix build of all 35 .src files, triggered on push/PR to master/develop on *.src changes. Uses Node 20 + `npm install -g greybel`.
- `.github/workflows/bug-scan.yml` — Daily schedule (05:00 UTC) scanning for P0 patterns. Outputs as GitHub Step Summary.
- Badges in README: `[![Build](...)]` linking to Actions page.

## CI Pipeline Patterns — Lessons from PR #29 (2026-06-25)

**`on:` YAML key triggers yamllint truthy warning** in older yamllint versions. Fix: quote it: `"on":`.

**`paths:` filter** limits when CI triggers. After push to a feature branch, **wait 5+ minutes** for the PR event to trigger CI re-run.

**`scripts/ci-build.sh` in PR #29** builds `src/` + `tools/` only — does NOT scan `bin/`, `bltings/`, `build/`. This is by design (deprecated copies), but means the local DMZ bug-scanner can find bugs the CI never checks.

**Actionlint shellcheck warnings on inline `node -e "..."` blocks** — extract to a separate file (e.g., `.github/scripts/<name>.js`).

## Repo Restructure Pattern (2026-06-27)

When the user restructures the repo (moving libraries, renaming directories), import paths break across many files. The systematic fix is:
1. **Map old → new paths** (create a JSON/YAML mapping)
2. **Calculate depth** of each .src file from repo root
3. **Apply prefix** = `../` * depth + mapped_relative_path
4. **Verify** with `greybel build` on CI matrix first, then full scan

See `references/repo-restructure-2026-06-27.md` for the full 2026-06-27 session (80→25 broken files fixed, CI 31/31 green).

## Build & Deploy Scripts

### Build Script
`/home/bratan/bin/greyhack-build` — builds all tools with one command:
```
greyhack-build all    # Build all tools
greyhack-build <name> # Build single tool
```
Output: `~/greyhack-tools/bin/<tool>.src` (uglified, ready for in-game use)

**NOTE:** Due to greybel-js import path bug, the build script may produce files with broken import paths. Use `/home/bratan/bin/greyhack-deploy` instead for reliable builds.

### Deploy Script (Recommended)
`/home/bratan/bin/greyhack-deploy` — builds all tools and fixes import paths:
```bash
greyhack-deploy
```
Output: `~/greyhack-tools/deploy/` with all tools ready for in-game use.

### Fileserver (Port 8765)
```bash
# Start (background):
cd ~/greyhack-tools && python3 ~/bin/temp_fileserver.py &

# Test:
curl http://localhost:8765/
```
Serves `~/greyhack-tools/` for in-game `pc.wget()` downloads.

### Session-Start Repo Review
```bash
cd /home/bratan/greyscripts
git status --short --branch
git branch --show-current
git rev-parse --short HEAD
git remote -v
./scripts/ci-build.sh --help
./scripts/ci-build.sh --out-dir /tmp/greybel-build
curl -fsS http://localhost:8765/lib_core/lib_core.src >/tmp/lib_core_check.src
wc -c /tmp/lib_core_check.src
git diff --stat
git diff --name-only
```

**Wichtige Erkenntnisse aus 2026-06-19:**
- `./scripts/ci-build.sh --out-dir /tmp/greybel-build all` ist falsch; das Script akzeptiert keine `all`-Position. Ohne Argumente baut es alle `.src` unter `src/` und `tools/`.
- Korrekter Full-Build: `./scripts/ci-build.sh --out-dir /tmp/greybel-build`
- Validierter Build-Output: `Build complete: 19 file(s) ok`
- `git status` kann auf `develop` sauber sein, aber trotzdem viele untracked Research-/Plan-Dateien zeigen. Nicht automatisch entfernen.
- Root-Level-`.src`-Artefakte prüfen: erst Größe/Inhalt vergleichen und als Artefakt markieren.

See `references/greyhack-build-status-review-2026-06-19.md` for the concrete session.
