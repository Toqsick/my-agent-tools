# Greybel Build Pipeline — PR #29 Session 2026-06-25

Session-specific detail for fixing the `feat/p0-ci-greybel-build` PR in
Toqsick/greyscripts. This document captures the exact CI failure modes,
the fixes that worked, and the validation sequence.

## PR Context

- **PR #29:** `feat/p0-ci-greybel-build` (open since 2026-06-18, 7 days stale)
- **Branch:** `feat/p0-ci-greybel-build` (NOT in `on.push.branches: [main, develop]`)
- **Files in PR:** `.github/workflows/ci.yml`, `.gitignore`, `docs/hermes-automation.md`, `scripts/ci-build.sh`
- **Upstream Scope:** `ci-build.sh` scans `src/` + `tools/` only — does NOT touch `bin/`, `bltings/`, `build/`

## Initial CI Failure (Run 27794084488)

`greybel-build` job failed: 13/15 source files failed with `no matching open if block`.
`lint-workflows` job failed: `pr-reminder.yml:94` ShellCheck SC1036/SC1088/SC2215 + truthy warnings.

## Fixes Applied (commit `bd4343d`)

### 1. P0 Single-Line if/then/end if (81 fixes, 13 files)

Used Python regex fixer (`/tmp/p0-fix-single-line-if.py`). Indent regex
uses `[ \t]+` (NOT just `\t+`) because some files (grsa_v2, hardening)
use 4-space indent while others use tabs.

Files modified and fix counts:
- `src/buildcore.src` — 4
- `src/debugcore.src` — 8
- `src/filecore.src` — 17
- `src/libcore.src` — 1
- `src/netcore.src` — 8
- `src/security/hardening.src` — 13
- `src/tools/mxwrap.src` — 6
- `src/tools/portmon.src` — 5
- `src/crypto/grsa_v2.src` — 5
- `src/security/grsa_v2.src` — 5
- `src/crypto/decypher.src` — 1
- `src/tools/recon.src` — 3
- `tools/setup.src` — 5 (single-quote escape fix, see below)

### 2. Manual Fixes Beyond Auto-Fixer

The auto-fixer handles single-line `if/then/end if` but NOT:

- **Inline-if expressions** (`"X" if cond else "Y"`): 3 occurrences in `decypher.src`, 1 in `filecore.src:647`
  → Replace with explicit `if/else/end if` blocks
- **Missing `end if`**: `filecore.src:188`, `filecore.src:271`
  → Add `end if` before next function/statement
- **Half-written functions** (`safeWriteFile`, `safeCopy` in filecore.src):
  → Add missing `end function` and `return true`
- **`=======` separator** in filecore.src → Remove (greybel interprets `==` as Punctuator)

### 3. `tools/setup.src` Escape Fix

Line 54 had `print("  importcode(\"bin/libcore.src\")")` — greybel-js 3.7+
rejects `\"` in print strings. Replaced 5 occurrences with single-quote inner
strings: `print("  importcode('bin/libcore.src')")`.

### 4. Lint Fixes

- `ci.yml`: `"on":` → `on:` (and back, since yamllint flags unquoted too in some configs)
- Actually settled on: `on:` (unquoted, truthy warning is WARNING not ERROR)
- 4 workflow YAMLs received `on:` → `"on":` quote-flip (yamllint warning only)
- `pr-reminder.yml:94`: extracted inline `node -e "..."` to `.github/scripts/pr-reminder-email.js`
- Comment-spacing fix: `cron: '0 9 * * *' # daily` → `cron: '0 9 * * *'  # daily` (2 spaces)

### 5. `.github/scripts/pr-reminder-email.js` (NEW)

Pure JavaScript extracted from inline workflow script. Single-quote style,
no backticks, no inline shell escaping. Verified runs locally with `node`.

## Validation Sequence

```bash
# 1. Per-file build (clearer error messages than full script)
greybel build src/filecore.src /tmp/gb-build
greybel build src/crypto/decypher.src /tmp/gb-build
# ... for each file

# 2. Full pipeline
bash scripts/ci-build.sh --out-dir /tmp/ci-build-full
# Expected: "Build complete: 15 file(s) ok"

# 3. Lint
bash .github/workflows/lint-workflows.sh
# Expected: exit 0, no warnings
```

## What Still Doesn't Work

After PR #29 fixes, the DMZ local bug-scanner (`greyhack-create-issues.sh --scan`)
still finds 43 bugs in the local `~/greyhack-tools/` checkout, but **most are
in `bin/`, `bltings/`, `build/`** — outside CI scope. The pattern breakdown:

| Pattern | Count | Already fixed in PR #29? |
|---------|-------|--------------------------|
| Negativer Index | 20 | N/A (CI accepts minus-sign) |
| Einzeiliges if/then/end if | 12 | YES (in src/ and tools/) |
| char(10) als String | 5 | N/A (in bin/, bltings/) |
| import_code ohne .src-Endung | 5 | N/A (in bin/) |
| get_shell() mit Parametern | 1 | N/A (in bin/) |

**The CI-vs-DMZ scope mismatch is the next problem to solve.** Options:
1. Extend `ci-build.sh` to scan `bin/` and `bltings/` too (risky — deprecated code)
2. Auto-delete `bin/`, `bltings/`, `build/` (cleanest)
3. Move local DMZ scanner to use CI's scope only (reduces noise)

## GitHub Issue Sync Attempt (Step B)

Tried posting a 43-issue batch from local DMZ scans to Toqsick/greyscripts
using `gh issue create --label auto-finding --label syntax --label p0 …`.
**Failed** at the first issue with: `could not add label: 'auto-finding' not found`.

The Toqsick/greyscripts repo only has labels: `bug`, `enhancement`, `ci`,
`docs`, `roadmap`, `new tool`. Auto-generated labels (`auto-finding`, `p0`,
`syntax`, `runtime`, `logic`) need to be created first.

**Fix for next session:** Use `gh label create auto-finding --color FF6B6B
--description "Auto-generated by Yuno DMZ scanner"` etc. before bulk-posting,
OR batch by existing label (e.g., just `bug` + `enhancement`).

**Resolution (same session, 2026-06-25):** Followed the SKILL.md Sammel-Issue
pattern instead. Created Issue #31 as a single structured issue with
5 Pattern-Cluster sections and per-finding tables. Used only standard label
`bug`. Result: https://github.com/Toqsick/greyscripts/issues/31. This is
the new preferred approach — see SKILL.md "GitHub Issue Sync for Local DMZ
Findings" for the full template.

## Branch State at End of Session

- Master: `b17d8fc chore(dmz): sync 43 P0-Bug-Logs + Daily-Scan 2026-06-25` (pushed)
- PR #29 branch: `bd4343d fix(greyhack): P0-Syntax-Fixes + Lint-Cleanup für CI-Build-Pipeline` (pushed)
- Working tree on master: clean
- CI status: locally validated (15/15 build + 0 lint warnings), but
  GitHub Actions re-run not yet triggered (paths filter or GitHub delay)

## Key References

- CI build script: `scripts/ci-build.sh` (handles both greybel CLI variants)
- Auto-fixer: `/tmp/p0-fix-single-line-if.py` (ad-hoc, not in repo)
- Daily scan: `logs/daily-scan-2026-06-25.log` (43 findings, 113 files scanned)
