# Build Cleanup — 2026-06-19

## Scope

P0 fixes + full CI syntax cleanup on `feat/p0-build-fixes-develop` → merged to `develop`, pushed.

## P0 Core Fixes

| File | Fix | Details |
|------|-----|---------|
| `src/filecore.src` | Orphan fragments, merge marker, ghost `main`, `is_folder` | 3 Stellen `is_folder` → `not is_binary`, removed `main` after `return false` at line 187 |
| `src/cli_core.src` | `for i in headers` → `for i in headers.indexes` | 4 Stellen — MiniScript iterates VALUES not indices |
| `src/debugcore.src` | Import path comments fixed | Absolute → relative paths |
| `src/tools/recon.src` | One-line if expanded | Single-line if/then/end if → multi-line |
| 6 files | Import path comments | `/home/root/bin/...` → relative paths |

## CI Syntax Fixes (48 one-liner + 3 inline-if + 5 backslash)

All 10 files fixed via Python regex replacement script then hand-verified:

| File | Fixes | Result |
|------|-------|--------|
| `src/buildcore.src` | 4 one-liners expanded | ✅ Build |
| `src/crypto/decypher.src` | 1 one-liner + 3 inline-if → if/else | ✅ Build |
| `src/crypto/grsa_v2.src` | 5 one-liners expanded | ✅ Build |
| `src/libcore.src` | 1 one-liner expanded | ✅ Build |
| `src/netcore.src` | 8 one-liners expanded | ✅ Build |
| `src/security/grsa_v2.src` | 5 one-liners expanded | ✅ Build |
| `src/security/hardening.src` | 13 one-liners expanded | ✅ Build |
| `src/tools/mxwrap.src` | 6 one-liners expanded | ✅ Build |
| `src/tools/portmon.src` | 5 one-liners expanded | ✅ Build |
| `tools/setup.src` | 5 backslash `\"` → `'` | ✅ Build |

## CI Build Result

```text
Build complete: 18 file(s) ok
```

## Fileserver Verify

```bash
curl -s http://localhost:8765/lib_core/lib_core.src | head -1  # OK
curl -s http://localhost:8765/src/cli_core.src | head -1       # OK
curl -s http://localhost:8765/src/tools/recon_lite.src | head -1 # OK
curl -s http://localhost:8765/src/tools/mission_report.src | head -1 # OK
```

## Files Committed

21 files, commit `af4e241`:
```text
feat(p0-build-fixes): fix ci-build, import paths, is_folder and greybel syntax
```
Fast-forward merge to `develop`, pushed to origin.
