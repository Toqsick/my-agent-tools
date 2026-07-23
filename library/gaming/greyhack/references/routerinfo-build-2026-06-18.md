# Routerinfo Build Session — 2026-06-18

## Context
- Repo: `Toqsick/greyscripts`
- Branch: `feature/routerinfo`
- Issue: #5 (`tool: routerinfo.src — Router-Informationen anzeigen`)
- File: `greyhack-tools/routerinfo/routerinfo.src`

## Fixes Applied

### 1. Single-line `if ... then ... end if` Syntax
**Problem:** `greybel build` failed with:
```
Build error: got Keyword[46:70 - 46:76: value = 'end if'] where number, string, or identifier is required
```

**Root cause:** Greybel does not support single-line `if` with `end if` on the same line.

**Fix:**
```greyscript
// WRONG:
if not router then fail("Router nicht gefunden") end if

// RIGHT:
if not router then
    fail("Router nicht gefunden")
end if
```

### 2. `import_code` Path Resolution
**Problem:** `greybel build` failed with:
```
Dependency /home/bratan/greyscripts/greyhack-tools/routerinfo/home/Bratan/bin/lib_core does not exist
```

**Root cause:** `greybel build` resolves `import_code` paths relative to the `.src` file's directory, not the game filesystem path.

**Fix:**
```greyscript
// WRONG (game path):
import_code("/home/Bratan/bin/lib_core")

// RIGHT (relative to greyhack-tools/routerinfo/routerinfo.src):
import_code("../lib_core/lib_core.src")
```

## Verification
```bash
scripts/hermes-automation.py build --file greyhack-tools/routerinfo/routerinfo.src --verify
```

**Result:**
- ✅ Build successful
- ✅ Verification passed

## Workflow Pattern
```
1. Merge PR #19 (automation foundation)
2. Create branch from develop: `git checkout -b feature/routerinfo develop`
3. Build target file with verify
4. Fix syntax/import errors
5. Commit + push
6. Create PR with `Fixes #5`
7. Clean up duplicate PRs if any
```

## Lessons
- Always build before committing GreyScript changes
- `import_code` paths must work for local greybel builds AND in-game deployment
- Clean `build/` output directory after greybel builds to keep working tree clean
- Use `gh pr comment --body` with single quotes or `--body-file` to avoid shell backtick execution
