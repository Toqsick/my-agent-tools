# yuno_attack.src Deep Bug Search (2026-07-03)

> Case study: Systematic static code audit of yuno_attack.src (295 lines, 9.8KB)
> using the Static Code Audit methodology documented in SKILL.md.
> Source: `/home/bratan/greyhack-tools/config_modules/yuno_attack.src`

## Session Context

The user asked for a "Deep Bug Search" on yuno_attack.src — a GreyScript module from the Yuno V6 modular toolset. The file is part of a 10-module architecture using YUNO_SHARED globals state bridge.

## Audit Results

### Balance Analysis — PASS ✅

| Metric | Count | Notes |
|--------|-------|-------|
| `if` | 50 | includes 11 one-line ifs, 39 multi-line |
| One-line `if` (no `end if`) | 11 | e.g. `if p.is_closed then st = "zu"` |
| Adjusted multi-line `if` | 39 | 50 - 11 = 39 |
| `end if` | 39 | ✅ Matches |
| `function` | 7 | 1 inner (style=function) + 6 cmd_X.run=function |
| `end function` | 7 | ✅ Matches |

**Key technique:** One-line `if X then Y` needs NO `end if`. Count them separately and subtract.

### Cross-Module Reference Audit — 6 UNDEFINED ⚠️

| Symbol | Used at Line(s) | Status |
|--------|-----------------|--------|
| `commands` | 289, 290 | ❌ Undefined in file — no `commands = {` in yuno_attack.src |
| `COMMON_PORTS` | 77 | ❌ Undefined in file — should be in yuno_core.src |
| `BRUTE_USERS` | 101 | ❌ Undefined in file — should be in yuno_core.src |
| `BRUTE_PASSES` | 102 | ❌ Undefined in file — should be in yuno_core.src |
| `try_exploit` | 87 | ❌ Undefined in file — should be in yuno_core.src |
| `read_configs` | 128, 148 | ❌ Undefined in file — should be in yuno_core.src (or yuno_recon.src) |

All 6 are module-architecture bugs: the symbols exist in other Yuno modules but are not accessible from yuno_attack.src in a shared-globals architecture. Each will cause a `Variable not declared` runtime error.

### Variable Name Mismatch — 1 BUG 🐛

**Line 148:** `read_configs(obj)` — `obj` is never assigned in the `cmd_loot.run` function. The surrounding context uses `pc` (from `require_shell()`). **Fix:** `read_configs(pc)`

Root cause: copy-paste from a different function that used `obj` as its context variable name.

### Dead Code Blocks — 2 WARNINGS ⚠️

**Location 1 — cmd_loot (lines 139-146):**
```greyscript
pc = require_shell()
if not pc then
    return                    // ← Line 141: FIRST guard exits
end if

if not pc then                // ← Line 143: NEVER REACHED
    print(style("[!] No host computer!", "red"))
    return
end if
```

**Location 2 — cmd_defend (lines 156-163):**
Same pattern — `if not pc then return` followed by `if not pc then print(...)`. Exact duplication.

Both are syntactically legal but produce unreachable code. The second blocks were likely intended to print an error message but were never restructured after the first guard was added.

### Initialization Gap — 1 RUNTIME BUG 🐛

**Line 13:** `main_session` initialized with key `"object"` (value: `get_shell` function reference).

**Lines 48, 129, 272:** Code accesses `main_session.objectList[X]` — `objectList` is NEVER in the init dict.

The `cmd_ssh` function (line 272) adds entries to `main_session.objectList`, but the first access (line 48, cmd_exploit) will crash with `Key Not Found: objectList`.

**Fix:** Add `"objectList": []` to the `main_session` init dict in yuno_core.src.

### No Compiler-Syntax Bugs Found ✅

| Pattern | Check | Result |
|---------|-------|--------|
| String-in-String | `"text"text"` without `char(34)` | ✅ None |
| Trailing/Missing Comma | `}` after last key:value | ✅ Clean |
| Comments in `{}` | `//` between `{` and `}` | ✅ None |
| `//command:` marker | First line | ✅ Present |
| Double quotes only | Single quotes | ✅ Clean |
| `""""` sequences | 4+ consecutive quotes | ✅ None |

## Summary

| Severity | Count | Fix Complexity |
|----------|-------|----------------|
| Compiler-blocking | 0 | — |
| Runtime-crashing | 7 | 6 cross-module refs + 1 var mismatch + 1 init gap |
| Logic/warning | 2 | Dead code (second guard blocks, unreachable) |

**Estimated runtime impact:** All 6 commands (`cmd_exploit`, `cmd_hack`, `cmd_ssh`, `cmd_loot`, `cmd_defend`, `cmd_bank`) will crash on first `main_session.objectList` access or undefined-symbol reference. The module is non-functional as-is without the core initializer being fixed first.
