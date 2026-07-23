---
name: greyscript-compiler-debugging
description: "Use when user asks to compile or debug GreyScript in GreyHack, diagnose `.src` build errors, verify DB-injected commands, or investigate runtime failures after a successful compile. NOT for generic programming or unrelated in-game tasks. Covers the full source-to-database-to-build pipeline, compiler rules, tiny POCs, sandbox checks, and static review."
version: 1.2.0
author: Yuno
license: MIT
platforms:
- linux
- windows
metadata:
  hermes:
    category: software-development
    tags:
    - greyscript
    - greyhack
    - compiler
    - debugging
    - build-system
changelog:
- 1.2.0 (2026-07-07): Pattern (b) `import_code` absolute-path section. Reference doc
    `references/import-code-absolute-to-relative-fix.md` plus re-runnable verifier
    `scripts/verify_greybel_builds.sh`. Key gotcha - greybel resolves ALL import_code
    paths relative to source-file directory, even absolute-looking strings. 14/14
    fix proven recipe.
- 1.1.0 (2026-07-07): Pattern (a) one-line-if auto-fix section + re-runnable script
    (scripts/expand_one_line_ifs.py) + reference doc (references/one-line-if-auto-fix.md).
    New error-table rows for `got Keyword[...end if]`, `no matching open if block`,
    `No files found!` mit greybel -dbf + relative-path Gotchas.
- 1.0.0 (2026-07-04): Initial version
trigger_keywords: ['compile', 'greyscript-compiler-debugging', 'debug', 'greyscript', 'greyhack']
keywords: ['compile', 'build', 'user', 'asks', 'debug']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['greyhack-sandbox']
---


# GreyScript Compiler Debugging

Non-obvious rules and failure modes when building `.src` files in GreyHack.

## The Full Build Pipeline

```
Source (.src) → DB Injection → Game-Restart → build → executable (.bin)
```

### Step-by-step
1. **Write source** — plain text, `.src` extension, `//command:` marker as **first line**
2. **Inject into DB** — insert into `Files` table with proper fields (see references/)
3. **Game restart** — **MANDATORY** after every DB change (GreyHack caches at startup)
4. **Build** — `build /path/to/source.src /path/to/output.bin`
5. **Launch** — `/path/to/output.bin` or `launch /path/to/output.bin`

## COMPILER RULES (Critical Knowledge)

### 1. The `//command:` Marker (MANDATORY)
Every source file must start with `//command: <name>` on line 1.
- **Without this marker**, GreyHack treats the file as a **binary**, not source.
- The `<name>` after `//command:` becomes the command name users type.
- Example: `//command: yuno_v6`
- **Existing commands** (ls, cd, ps, ftp) follow this pattern — always check them for reference.

**Failure mode:** `build: can't find X.src` — if the file IS there but build can't find it (even though `cat` works), the marker might be wrong or missing.

### 2. Object Literal Rules (HIGH-PRIORITY BUGS)

GreyScript's compiler is **strict** about object/table syntax:

#### 2a. Last entry needs trailing comma
```greyscript
// WRONG — compiler error "got ... where Comma or RCurly is required"
obj = {
    "key": "value"
}

// RIGHT
obj = {
    "key": "value",
}
```

**Error signal:** `Compiler Error: got "}" where Comma or RCurly is required`

#### 2b. NO comments inside object literals
```greyscript
// WRONG — compiler error
main_session = {
    "exit": false,
    // === STATE ===   <-- ILLEGAL
    "recording": false,
}

// RIGHT — comment goes before or after the object
main_session = {
    "exit": false,
    "recording": false,
}
```

#### 2c. Multi-line objects need comma on EVERY line except the `{`/`}` lines
Every line inside `{}` that's not `{` or `}` needs a comma at the end.

### 3. String Construction (char(34) Pattern)

**When building strings that contain `"`:**
```greyscript
// WRONG — first inner " ends the string, then "pass" is parsed as identifier where EOL is expected
content = content + "pass = "pass"" + char(10)

// RIGHT — use char(34) for inner quotes
content = content + "pass = " + char(34) + "pass" + char(34) + char(10)
// Or use single-quote strategy
content = content + "['pass'] = " + value
```

**Error signal:** `Compiler Error: got Identifer(pass) where EOL is required`

### 4. Build Command Syntax Per Version

| GreyHack Version | Build Syntax | Notes |
|---|---|---|
| 0.9.6771-beta | `build /source.src /output.bin` | Source MUST have `.src` ext |
| 1.5.x | `build source.src output` | Might differ |

**Key quirks in 0.9.6771-beta:**
- `build` checks existence of **both** source AND output path
- Output path must be a FOLDER that exists, not a new filename
- `build /src.src /bin/output` where `/bin/` is an existing directory
- `run` command does NOT exist — use direct path or `/bin/name`
- `launch` command also does not exist

### 5. File Size Limits

GreyHack commands have a **practical size limit**:
- Largest built-in command (`ftp`): ~12 KB (12,210 bytes)
- Files >12 KB may silently fail to load as commands
- File appears in `ls` but `build` can't parse it even with correct syntax
- **Solution:** Split into modules of ~12 KB each
- **Verify:** Deploy a tiny (1.5 KB) proof-of-concept first to validate the pipeline

### 6. The Tiny-POC-First Strategy

When the build pipeline is failing and the cause isn't obvious:

1. **Write a 1.5 KB mini-script** with minimal functionality
2. Deploy with correct marker + DB fields
3. Test in-game — if it works, the pipeline is correct
4. Scale up in 12 KB modules
5. If it fails, you've isolated the issue to the pipeline itself

**Why this works:** A 78 KB script failing could be size limits OR syntax OR marker — too many variables. A 1.5 KB script isolates to pipeline problems only.

## DB Injection Details

### GreyHackDB.db Schema (live, 0.9.6771-beta)

```sql
-- Simplified live schema:
CREATE TABLE Files (
    ID TEXT PRIMARY KEY,      -- UUID
    Content TEXT,             -- Raw source code
    refCount INTEGER DEFAULT 0
);
-- No `nombre`, `computer_pk`, `typeFile` in live!
-- Those are only in backup/sample DBs
```

### Critical DB Fields for a Functioning Command

A source file needs ALL these fields set correctly in the Files table:
1. `Content` — the raw source text, starting with `//command: <name>`
2. The file must be referenced from the Player's file system (Files.link_user/computer_pk in backup schema) OR placed directly in a reachable path via the game's internal file system

**When using DB-based injection:**
- Insert into `Files` with proper UUID
- Must also create the player-file-system link so the game knows about it
- The game's internal `/bin/` is a virtual filesystem inside the DB with its own tree structure (node-type enum: 1=root, 2=folder, 3=file)
- Just inserting into `Files` is NOT enough — the file tree entry must exist

### Debugging a Failing Command

When the command isn't found after injection:

1. **Check the marker** — does `Content` start with `//command: <name>`?
2. **Check file tree** — is there a node entry for this file in `Files` linked from a folder node?
3. **Check size** — is the source >20 KB? If yes, split it.
4. **Deploy POC** — 1.5 KB test to verify the pipeline
5. **Check reference scripts** — what do working commands (ls, cd, ftp) look like in the DB?
6. **Game restart required** — every single time after DB change

## Standalone Syntax Verification (Sandbox Pattern) — NEW 2026-07-04

**Problem:** When a GreyScript project uses custom build-infrastructure (`//include:` Viper directives, custom concat scripts, non-standard import paths) that `greybel` doesn't natively support, chasing the full build chain wastes many tool calls on pre-existing infra bugs — not on the actual code fixes.

**Pattern (proven 2026-07-04, yuno_viper audit):** Instead of debugging the build chain, create a **minimal standalone `.src` file** that contains only the patterns you need to verify. Test with `greybel execute` directly:

```bash
# Step 1: Create a minimal test file with the exact patterns from your patches
cat > /tmp/syntax_check.src << 'EOF'
//command: syntax_check
// Test 1: Null-guard before .size access
for i in arr.indexes
    entry = arr[i]
    if entry == null then
        continue
    end if
    print("ok: " + str(entry.size))
end for

// Test 2: Null-guard after split
parts = args.split(":")
if parts == null or parts.len == 0 then
    print("bad split")
    return
end if

// Test 3: Entry null-check in loop (loot pattern)
files = [{"size": 100}, null, {"size": 200}]
for i in files.indexes
    e = files[i]
    if e == null then
        continue
    end if
    print("size: " + str(e.size))
end for

print("ALL_OK")
EOF

# Step 2: Run greybel execute for syntax validation
npx --prefix /path/to/project greybel execute /tmp/syntax_check.src --silent

# Step 3: Pattern-grep the actual file for every changed pattern
grep -n "continue\|parts == null\|entry == null\|e == null" target.src
```

**When to use this pattern:**
- The project uses `//include: <name>` or other custom pre-processing that `greybel build` can't resolve
- The task is targeted source-code fixes (e.g., null-guards, multi-line if/end-if), not a full project build
- You need to verify syntax (not runtime) — `greybel execute` validates parser-level correctness
- The build system has pre-existing issues unrelated to your changes (e.g., missing modules, custom concat scripts)

**What this pattern avoids:**
- Chasing `//include:` resolution bugs that are NOT caused by your changes
- Modifying the project's build infrastructure just to run a syntax check
- Wasting 10+ tool calls on pre-existing infra problems

**Cost of ignoring this pattern (actual 2026-07-04 session):** ~10 extra tool calls debugging `//include: yuno_viper_core` resolution in greybel instead of making the standalone test file (1 call → green result), because `//include:` is a Viper-specific custom directive, not a native greybel feature.

## Dual-Analysis Strategy: Static Scan + Subagent Review

**Core finding (validated 2026-07-03):** Two analysis methods find DIFFERENT bug classes. Both are needed for 100% coverage.

| Method | Finds | Cost | Speed |
|--------|-------|------|-------|
| **Static grep/pattern scan** | Compiler bugs (trailing commas, string-in-string, comments in objects, balance errors) | Cheap (no LLM calls) | Instant |
| **Subagent deep bug search** | Runtime/logic bugs (undefined vars, wrong variable names, dead code, missing field init) | Expensive (1-2 LLM calls per module) | 1-2 min per module |

### The Proven Workflow

```
1. Parent: SYNTAX-SCAN (static grep) → finds Compiler Bugs
2. Parent: DISPATCH 3-5 parallel workers for DEEP CODE REVIEW
3. Workers: Find RUNTIME BUGS (while parent works on compiler fixes)
4. Parent: AGGREGATE worker findings, separate TRUE bugs from FALSE positives
5. Parent: APPLY ALL FIXES (compiler + runtime) in one batch
6. Parent: VERIFY with second static scan
7. Parent: DEPLOY to DB
```

### What Each Found in the Yuno V6 Session

| Module | Static Scan Finds | Worker Finds |
|--------|-------------------|--------------|
| yuno_core | 0 compiler bugs | 4 trailing-comma (FP — legal in GS) + missing `objectList`/`netcatList` init |
| yuno_recon | 0 compiler bugs | `main_session.objectList` uninitialized (runtime crash) |
| yuno_attack | 0 compiler bugs | `read_configs(obj)` typo, double `if not pc then` dead code, 6 undefined externals |
| yuno_files | 0 compiler bugs | `obj` undefined (3 refs), `commands` dict undefined |
| yuno_crypto_net | 0 compiler bugs | `netcatList` uninit, `commands` dict undefined, connect_service result unchecked |

**Key insight:** Workers find ZERO compiler bugs but find CRITICAL runtime bugs. Parent static scan finds zero runtime bugs. They are ORTHOGONAL.

### Worker False-Positive Awareness

Workers can flag false positives. Known patterns:
- **Trailing commas in object literals** — GreyScript REQUIRES them (unlike JSON where they're illegal). Worker may flag as "bug" — this is WRONG.
- **`cmd_var` as local variable** — `cmd_freq` inside function `cmd_suggest` is a local variable, NOT a top-level command. Worker may flag as "orphaned command".
- **`if not pc then` early return** — Proper defensive coding. Only a bug if there's a DUPLICATE block right after.

**Rule:** Cross-check worker findings manually before applying. "Lieber 5 false positives als 1 echter Bug übersehen" but verify before applying.

### Worker Dispatch Template

```python
delegate_task(tasks=[
    {"goal": "Deep Bug Search auf yuno_core.src",
     "context": f"... 8 bug patterns to check ... Keine Aenderungen nur Report ..."},
    {"goal": "Deep Bug Search auf yuno_recon.src", ...},
    ... max 5 parallel
])
```

**Critical context inclusion:** Include ALL 8 bug patterns + explicit "NO changes, read-only analysis". Workers MUST NOT modify files.

### 7. Pattern (a): One-Line-If — Auto-Expandable (NEW 2026-07-07)

GreyScript's non-`-u` Parser (greybel ohne `-u`) rejects single-line `if` statements:

```greyscript
// ❌ CRASH
if n == 0 then return "0" end if

// ✅ FIX — mehrzeilig
if n == 0 then
    return "0"
end if
```

**Compile-time error signatures:**
- `Build error: no matching open if block at <file>:<line>:<col>` (ältere Form)
- `Build error: got Keyword[<line>:<col> - <line>:<col>: value = 'end if'] where number, string, or identifier is required` (greybel 3.7.12)

**Auto-Fix:** `scripts/expand_one_line_ifs.py` — Python-Script das Pattern (a) zuverlässig zu multi-line expandiert und:
- mixed-indent (spaces outer, tab inner) erhält
- statement-chains (`if X then A; B end if`) **NICHT** anfasst (Semantik ändert sich)
- combined one-liner (`then for`, `then if`, etc.) **NICHT** anfasst (würde falsch einrücken)
- idempotent ist (bereits multi-line → kein Match)

Verified 2026-07-07: 37 funde in 7 .src files, 6/7 builds OK danach. Volle Doku + Build-Verifikation-Rezession in `references/one-line-if-auto-fix.md`.

### 8. Pattern (b): `import_code` Absolute In-Game Paths (NEW 2026-07-07)

A common build-failure pattern in multi-tool GreyHack repos: source files use
**absolute in-game paths** like `import_code("/home/Bratan/bin/lib_core")` that
break `greybel build` with:

```
Build error: Dependency <absolute-path-rewritten-as-rel-path> does not exist...
```

**Root cause (critical gotcha):** greybel resolves ALL `import_code` paths — even
absolute-looking strings — **relative to the source file's directory**, NOT to
"/home/..." on the filesystem. There is no "real" absolute-path interpretation.

So `import_code("/home/Bratan/bin/lib_core")` in
`greyhack-tools/backdoor/backdoor.src` becomes a search for
`greyhack-tools/backdoor/home/Bratan/bin/lib_core` — which obviously doesn't exist.

**3-group fix strategy:**

| Group | When | Fix |
|---|---|---|
| **Group 1** | Target lib already exists at repo root (e.g. `../lib_core/lib_core.src`) | One-line sed-replace: `"/home/Bratan/bin/lib_core"` → `"../lib_core/lib_core.src"` |
| **Group 2** | Target lib already exists in a sibling subdir (e.g. `libs/listLib.src`, `manager.src`) | Same sed-replace, but path is relative to tool's dir not repo root |
| **Group 3** | Target lib does NOT exist in repo (e.g. `chat.src`, `chatform.src`, `thor.src`) | Create minimal stub in tool's dir (10-20 lines, only the symbols the importer uses), then rewrite import to `"<stubname>.src"` |

**Bonus gotcha — Group 4 (installers, subdir-relative):** A file like
`installer/master_installer.src` with `import_code("lib_core.src")` was already
"relative" but **wrong** — greybel looks in `installer/lib_core.src`, not the
repo root. **Fix:** Add `../` prefix. All entries in an installer-style "bundle"
script need this.

**Verification pattern:** batch-build all affected files in one loop with
`scripts/verify_greybel_builds.sh` — accepts N file paths, runs `greybel build
-dbf -si` on each, prints pass/fail summary, returns nonzero on any failure.

Pass criterion: clean exit AND build-dir contains the resolved dependency
(e.g. `build/lib_core/lib_core.src`), proving it was found and inlined.

**Stub philosophy:** Minimal — only the symbols the importing file uses. Stubs
are build-scaffolding, not runtime-correctness fixtures. Real behavior comes from
in-game deployment.

Verified 2026-07-07: 14 files fixed in 1 session, 14/14 builds green. Full recipe,
pitfalls (incl. multi-wave backup-suffix collision, string-non-import gotchas in
manager.src, stub minimalism), and the Wave-2 backup convention
(`.bak-agent-g-$STAMP`) at `references/import-code-absolute-to-relative-fix.md`.

## Common Runtime Bug Patterns (Compiles But Crashes)

These bugs pass the compiler but crash at runtime. Static analysis CANNOT detect them.

### Pattern A: `commands` Dict Missing in Dispatch Footer

```greyscript
// COMPILES OK — but crashes: "Variable commands not declared"
if commands.hasIndex(cmd) then     // ← CRASH HERE
    commands[cmd].run(cmdArgs)
end if
```

**Fix:** Define `commands` dict before the dispatch block:
```greyscript
commands = {}
commands.cmd_X = cmd_X
commands.cmd_Y = cmd_Y
// ... all commands in this module

if params.len > 0 then
    cmd = params[0]
    cmdArgs = params[1:]
    if commands.hasIndex(cmd) then
        commands[cmd].run(cmdArgs)
    end if
end if
```

**Root cause:** Modular code — each module has its own dispatch but the `commands` dict was initialized only in the original monolithic source.

### Pattern B: `obj` Variable Undefined

```greyscript
// Main function body uses obj.host_computer but obj is never assigned
srcFile = obj.host_computer.File(srcPath)  // ← CRASH: obj is nil
```

**Fix:** Assign `obj = main_session.object` right after `main_session` init:
```greyscript
main_session = YUNO_SHARED.main_session
obj = main_session.object       // ← MUST add this
```

### Pattern C: Missing Fields in `main_session` Init

```greyscript
// main_session created with fields A, B, C
// But code references main_session.objectList (or netcatList, vars, etc.)
// → Runtime: "Key Not Found"
```

**Fix:** Add ALL fields that any module references to the init dict. Cross-module audit needed — the init in `yuno_core` must include fields used by OTHER modules.

### Pattern D: Variable Typo / Copy-Paste Error

```greyscript
// 'obj' was defined in a DIFFERENT function with a different variable
pc = require_shell()
read_configs(obj)    // ← TYPO: should be read_configs(pc)
```

**Fix:** Manually verify variable names in function bodies. Static analysis won't catch this.

### Pattern E: Dead Code from Duplicate Guards

```greyscript
pc = require_shell()
if not pc then
    return            // ← Early exit
end if

if not pc then        // ← DEAD CODE — pc is already known to be truthy
    print("[!] No host computer!")
    return
end if
```

**Fix:** Remove the second (redundant) guard block.

## Compiler Error Reference

| Error Message | Likely Cause | Fix |
|---|---|---|
| `got Identifier(pass) where EOL is required` | String-in-string — inner `"` breaks parser | Use `char(34)` for inner quotes |
| `got "}" where Comma or RCurly is required` | Missing comma on last object property | Add trailing `,` |
| `got Keyword[...: value = 'end if'] where number, string, or identifier is required` | Pattern (a) one-line-if — `if X then Y end if` rejected by non-`-u` parser | Expand to multi-line. Auto-fix via `scripts/expand_one_line_ifs.py` — see `references/one-line-if-auto-fix.md` |
| `no matching open if block at <file>:<line>:<col>` | Same Pattern (a) — ältere greybel-Error-Form | Same fix |
| `No files found!` (greybel) | Pfad nicht relativ zu CWD, oder Output ist File statt Folder (oder umgekehrt bei `-dbf`) | siehe Gotchas in `references/one-line-if-auto-fix.md` |
| `Build error: Dependency <path> does not exist... at <file>:<line>` | **Pattern (b) `import_code` path-resolution failure** | greybel resolves paths relative to source-file's dir. Convert absolute in-game paths to `../<lib>.src`. For non-existent targets, create a minimal stub. Full recipe + batch verifier: `references/import-code-absolute-to-relative-fix.md` + `scripts/verify_greybel_builds.sh` |
| `Can't build X. Binary file` | File exists but not recognized as source | Add `//command:` as line 1 |
| `Can't find X.src` | Source not in game's file tree OR wrong path | Check DB file tree, verify path in game |
| `build: can't find /path/output` | Output folder doesn't exist | Create folder first with `mkdir` |
| Silent failure — file appears but no command | Source too large (>12 KB) | Split into modules |

## References

- `references/2026-07-03-compiler-bugs.md` — Session-specific bug list from the Yuno V5 fix session
- `references/2026-07-03-runtime-bugs.md` — Yuno V6 modular runtime bugs found via subagent review (2026-07-03). Covers `commands` dict, `obj` init, field initialization, variable typos, dead code patterns, and the worker dispatch template.
- `references/one-line-if-auto-fix.md` — **Pattern (a) automated fix recipe** (2026-07-07): regex-constraints, mixed-indent handling, greybel `build -dbf` semantic gotchas, relative-path resolution. Plus `scripts/expand_one_line_ifs.py` for re-runnable auto-expansion.
- `references/import-code-absolute-to-relative-fix.md` — **Pattern (b) `import_code` absolute-path fix recipe** (2026-07-07): the greybel path-resolution rule, 4-group classification (1=target-at-repo-root, 2=target-in-sibling-dir, 3=target-missing → stub, 4=subdir-installer with wrong relative path), stub philosophy, multi-wave backup convention, the 14/14 fix session narrative. Plus `scripts/verify_greybel_builds.sh` for batch verification.
- `references/greyhack-db-schema.md` — Detailed DB schema notes
- `references/yuno-tools-pattern-catalog.md` — Positive/negative GreyScript pattern catalog extracted from 28 real yuno-tools scripts. 10 working patterns (✅ multiline `if/else/end if`, `typeof`-check, `while i < list.len`, etc.), 10 broken patterns (❌ `else if`, Einzeiler-if, inline-if, `-u` flag, `0`-truthy, negative indices), and 5 reusable code idioms plus builtin frequency table. Load this first when writing new GreyScript that needs to avoid compiler bugs.

## Related Skills

- `greyhack-greyscript` — GreyScript language reference
- `greyhack-sandbox` — Testing tools outside GreyHack
- `yuno-user-preferences` — Basti's working-style preferences (includes Game-Mode Debugging Pattern)
