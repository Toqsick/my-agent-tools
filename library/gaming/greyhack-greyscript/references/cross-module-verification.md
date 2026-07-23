# Cross-Module Verification Checklist

After splitting a monolithic GreyScript source into independent modules (each under ~12KB with `//command:` markers), verify ALL modules pass these checks **before deploying to the game**.

## Priority Order — Check in This Sequence

### 1. Module Boundary Integrity
**Why first:** Structural errors (missing init, orphaned functions) cause immediate build failures.

| Check | What to look for | Method |
|-------|-----------------|--------|
| `cmd_X = {}` count | Must equal `cmd_X.run = function` count per module | `grep -c "^cmd_.* = {}"` vs `grep -c "cmd_.*\.run = function"` |
| No orphaned bodies | Every `end function` must have a matching `cmd_X.run = function(...) ...` before it | Script: `find_paired_blocks()` — diff between `init_only` and `body_only` sets |
| No indented local vars | `cmd_freq` inside `cmd_suggest.run` is a LOCAL variable, NOT a top-level cmd | Check if `cmd_X = {}` is indented (preceded by whitespace) |
| First line | MUST be exactly `//command: <name>` | `head -1 module.src` |

**Common mismatch:**
- `cmd_freq = {}` inside `cmd_suggest.run` → regex `^cmd_\w+\s*=\s*\{\}` catches it if UNANCHORED. Use `re.MULTILINE` pattern with `^` anchor or check for leading whitespace.

### 2. YUNO_SHARED Guard Check
**Why second:** A guard failure causes state corruption across modules — hard to debug because symptoms appear in a different module than the root cause.

```greyscript
// RICHTIG — YUNO_SHARED = {} NUR innerhalb des if-Blocks:
if not globals.hasIndex("YUNO_SHARED") then
    YUNO_SHARED = {}
    // ... init ...
end if

// FALSCH — YUNO_SHARED = {} AUSSERHALB des if-Blocks:
YUNO_SHARED = {}    // Überschreibt vorherige Initialisierung!
if not globals.hasIndex("YUNO_SHARED") then
    // ... init ...
end if

// FALSCH — kein Guard:
YUNO_SHARED = {}    // Wird bei jedem Laden zurückgesetzt!
```

**Verification:** Read the first ~15 lines of each module. The `YUNO_SHARED = {}` line (if present) MUST be preceded by `if not globals.hasIndex("YUNO_SHARED")` on an earlier line, and followed by `end if` on a later line.

**Python check:**
```python
for mod in modules:
    lines = open(f'{mod}.src').readlines()
    guard_line = None
    init_line = None
    for i, line in enumerate(lines[:20], 1):
        if 'if not globals.hasIndex' in line:
            guard_line = i
        if 'YUNO_SHARED = {' in line:
            init_line = i
    if init_line and (not guard_line or guard_line > init_line):
        print(f"❌ {mod}: init ohne guard oder guard NACH init!")
```

### 3. Cross-Module Field Consistency
**Why third:** A field missing from `main_session` init causes `Key Not Found` crash at unpredictable runtime.

**Check:** Every `main_session.<field>` access across ALL modules must either:
- (a) Be initialized in the core module's `main_session = {}` dict, OR
- (b) Be guarded with `if not main_session.hasIndex("field") then main_session.field = default` before first use

**Python check:**
```python
import re

defined_fields = set(name.group(1) for name in re.finditer(r'main_session\.(\w+)', core_module))
accessed_fields = set()

for mod in all_modules:
    accessed_fields.update(
        name.group(1) for name in re.finditer(r'main_session\.(\w+)', mod)
        if name.group(1) not in ['hasIndex', 'len']
    )

missing = accessed_fields - defined_fields
if missing:
    print(f"⚠️ Fields accessed but not in init: {missing}")
```

### 4. Try-List vs Defined Commands
**Why fourth:** Commands in the footer Try-list that don't exist in the module cause silent "command not found".

Each module's footer has a try block like:
```greyscript
try
    commands = {
        "cmdname": @cmd_cmdname,
        ...
    }
end try
```

**Check:** Every name in the `commands` dict must have a corresponding `cmd_<name> = {}` + `cmd_<name>.run = function(...)` in the same module. And vice versa.

**Python check:**
```python
defined = set(re.findall(r'cmd_(\w+)\s*=\s*\{\}', content))
m = re.search(r'Try:\s*([^"]+)', content)
if m:
    try_cmds = set(c.strip() for c in m.group(1).split(','))
    missing = try_cmds - defined
    extra = defined - try_cmds
```

### 5. Module Size Check
**Why fifth:** A module >12KB may not be auto-loaded as a `//command:` by GreyHack.

| Size | Risk | Action |
|------|------|--------|
| <10KB | Safe | Proceed |
| 10-12KB | Margin | OK but split if adding more cmds |
| 12-15KB | Borderline | Test in-game; split if not recognized |
| >15KB | Likely broken | Split into smaller modules |

**Reference:** The largest reliably working `//command:` source is `ftp` at 12,210 bytes (V0.9.6771-beta).

### 6. Comment-in-Object Scan
**Why sixth:** GreyScript rejects `//` comments inside `{}` map literals silently — the compiler skips the entire block.

```greyscript
// FALSCH — Kommentar INNERHALB des Objects:
main_session = {
    "version": "6.0.0",
    // Das ist ein Kommentar ← ILLEGAL!
    "exit": false
}
```

**Python check:**
```python
brace_depth = 0
in_obj = False
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if not in_obj and '{' in line and '}' not in line.split('{')[0]:
        in_obj = True
    if in_obj:
        brace_depth += line.count('{') - line.count('}')
        if brace_depth <= 0:
            in_obj = False
        elif stripped.startswith('//') and ':' not in stripped:
            print(f"⚠️ L{i}: comment in object literal")
```

## Real-World Benchmark (2026-07-03)

Yuno V6 Monolith (78KB, 65 commands) → 10 modules:

| Module | Size | cmds | All Checks |
|--------|------|------|-----------|
| yuno_core | 6.2KB | helpers | ✅ |
| yuno_recon | 7.3KB | 6 | ✅ |
| yuno_attack | 11.1KB | 6+ | ✅ |
| yuno_files | 8.1KB | 10+ | ✅ |
| yuno_crypto_net | 7.2KB | 4+ | ✅ |
| yuno_util | 8.7KB | 13+ | ✅ |
| yuno_macros | 7.4KB | 6 | ✅ |
| yuno_snapshots | 5.9KB | 3 | ✅ |
| yuno_suggest_plugin | 5.7KB | 3 | ✅ |
| yuno_mission | 6.3KB | 4 | ✅ |

**False positive caught:** `cmd_freq = {}` in `yuno_suggest_plugin` — was a LOCAL variable inside `cmd_suggest.run`, not a top-level command.

## Execution Order When Fixing

If verification fails, fix **in this order** (earlier checks may cause later ones to pass):

1. Fix `//command:` markers (test: game restart + type name)
2. Fix YUNO_SHARED guards (test: call init module, then any other)
3. Fix cross-module fields (test: run each command once)
4. Fix cmd definitions vs try-list (test: each command auto-completes)
5. Fix string-in-string + comma bugs (test: build passes)
