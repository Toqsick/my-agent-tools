# Yuno V5 Fix Session (2026-07-03)

> Case study: Debugging and fixing a large (66KB, 64+ command) GreyScript source that failed to compile.
> Demonstrates the systematic bug-scanning approach documented in SKILL.md.
> Source: `yuno_v5.src`, 66.263 bytes, injected into GreyHackDB in `/home/gregor/Config/yuno_v5.src`.

## Session Timeline

| Phase | What Happened | Duration |
|-------|--------------|----------|
| DB Injection | Injected yuno_v5 into Files + FileSystem | 2 min |
| First Build Attempt | `build /home/gregor/Config/yuno_v5.src` | No error reporting in initial user message |
| User Report | "vergisst teilweise kommas bei auflistungen" + "Compiler Error: got Identifier(pass) where EOL is required line 1308" | — |
| Root Cause Analysis | Found 3 bug classes in the source | 15 min |
| All Fixes Applied | 10+ trailing commas, 5 string-in-string, 1 comment-in-object | 10 min |
| Result | Yuno V5 compiles and runs with all 3 libs loaded | ✅ |

## Bug Class 1: Missing Trailing Commas in Map Literals (10+ occurrences)

**Error Signature:** `Compiler Error: got ELO() where Comma or RCurly is required line N`

**Root Cause:** The last `"key": "value"` pair in a `{}` block was missing a trailing comma. The compiler error line number points at the `}` closing brace, NOT the line with the missing comma.

**Affected sections:**
- Theme definitions (3 themes × 10 colors each = the last color in each theme set was missing)
- `main_session` object initialization (the very last key-value pair)

### Example (THEME_OCEAN, original)

```greyscript
THEME_OCEAN = {
    "red": "#ff5577",
    "green": "#55ffaa",
    "blue": "#0055aa",
    // ... 7 more colors ...
    "pink": "#ff99cc",
    "cyan": "#aaffff"   // ← MISSING COMMA! Error at line 24 (the })
}
```

### Fix applied
Add trailing comma after every last key-value pair in every `{}` block. GreyScript accepts trailing commas at `}` just fine.

### Systematically Found (Python)

```python
for i, line in enumerate(lines, 1):
    stripped = line.rstrip()
    if not stripped.endswith(','):
        continue
    # Correct: object entries start with "key":
    if re.match(r'^\s*"[^"]+"\s*:', stripped):
        continue  # Object entry, OK
    # Bug: statement ending with trailing comma
    if re.match(r'^\s*\w+(\[[^\]]+\])?\s*=\s*.+,\s*$', stripped):
        bugs.append((i, stripped))
```

## Bug Class 2: String-in-String in Dynamic Code Generation (5 occurrences)

**Error Signature:** `Compiler Error: got Identifier(pass) where EOL is required line 1308`

**Root Cause:** The `cmd_jump` function builds GreyScript source code as a string at runtime. The naive approach of embedding `"` inside a `"..."` string causes the compiler to misinterpret the line, since the inner `"` terminates the outer string.

### Original (broken) — line 1308

```greyscript
content = content + "pass = "pass"" + char(10)
```

The compiler sees:
```
"pass = "   ← string ends
pass        ← identifier — ERROR!
""          ← empty string
```

### Fix (9 lines rewritten)

Every `"` inside the dynamically-built code was replaced with `char(34)`:

```greyscript
content = content + "pass = " + char(34) + "pass" + char(34) + char(10)
```

### Full set of fixed lines

| Line | Original (Broken) | Fixed |
|------|-------------------|-------|
| 1294-1308 | `"pass = "pass""`, `"object[\"shell\"] = shell"`, `"if typeof(shell) != ""shell"" then"` | All inner quotes → `char(34)` |
| 1317 | `"interop[\"shell\"] = shell"` | `"interop[" + char(34) + "shell" + char(34) + "] = shell"` |
| 1321 | `"shell.launch(\"/bin/rshell-server\", \"\")"` | `"shell.launch(" + char(34) + "/bin/rshell-server" + char(34) + ", " + char(34) + char(34) + ")"` |

Translation table: see SKILL.md "Dynamic Code Generation" section.

## Bug Class 3: Comments Inside `{}` Object Literals (1 occurrence)

**Error Signature:** (Silent — causes the entire `main_session` initialization to be malformed)

**Root Cause:** A `// === V5 STATE ===` comment was placed between `{` and `}` in the `main_session` initialization literal.

### Example

```greyscript
main_session = {
    "version": "6.0.0",
    // === V5 STATE ===   ← ILLEGAL!
    "exit": false,
```

### Fix

Moved the comment outside the object:

```greyscript
// === V5 STATE ===
main_session = {
    "version": "6.0.0",
    "exit": false,
```

## Additional Fixes: `//command:` Marker + Banner Version

1. **Missing `//command:` marker** — The source started with `// ========` as first line. Added `//command: yuno_v5` as line 1.
2. **Stale V4 banner** — All `print(style("... V4 ...", ...))` messages were updated to `V5`.
3. **`comando: ""` in DB** — The FileSystem entry had `comando: "run /home/gregor/yuno_v5"` which prevented auto-loading. Fixed to empty string.

## Lessons for Future Sessions

1. **When importing GreyScript source from V5→V6 → always scan for these 3 bug types first**, even if the source appears to be "already working"
2. **The `cmd_jump` function is particularly bug-prone** because it builds code strings that contain `"` — always use `char(34)` for generated-code patterns
3. **Theme definitions are high-risk** for missing trailing commas because they're large, homogeneous `{}` blocks where the last entry is easily overlooked
4. **The user's tolerance for bugs is LOW** — after surviving the V5 debugging session, they expect V6 modules to compile on first try. Always proactively scan before deployment.
