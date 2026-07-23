# Greybel-JS Compatibility Scan (5-Check Audit)

## Trigger

User asks to scan `.src` files for greybel-js compatibility, "Inkompatibilitäten suchen", "check patterns (a)-(e)", or when porting code between the in-game GreyScript engine and greybel-js (Mock Environment).

## Purpose

The in-game GreyScript engine and greybel-js interpret the SAME language spec but diverge on some edge cases. This audit checks 5 known divergence patterns that are NOT compiler errors in either engine but cause silent failures or crashes in the other.

## Scan order — run ALL 5 checks in parallel (they are independent)

### 1. Escaped Quotes `\"` in print-Strings

Some greybel-js parsers handle escaped quotes differently in string literals. Check EVERY `print("...\"...")` call:

```python
import re
for f in sorted(os.listdir('.')):
    if not f.endswith('.src'): continue
    for i, line in enumerate(open(f), 1):
        if re.search(r'print\s*\(', line) and r'\"' in line:
            print(f"{f}:{i}: {line.rstrip()}")
```

**Bash pitfall:** `grep` with `\"` and special chars in file paths is fragile. Always use Python for this check to avoid nested-quote-syntax errors in the shell command.

**False-positive note:** `\"` in string *concatenation* (e.g. `lines + "\"name\" + ...`) is NOT a print-string concern. Only flag actual `print(...)` calls. The session found 7 `\"` occurrences in `yuno_viper_net.src:297-321` — all in JSON-string concatenation for botnet serialisation, NOT in `print()`. Zero real findings in this scan.

### 2. `start_terminal` Method Access (Known Divergence)

The pattern `someVar.start_terminal` is valid GreyScript API (opens a terminal for a `shell`-typed object), but greybel-js Mock Environment may NOT support it. Search:

```bash
grep -nE '[a-zA-Z_]+\.start_terminal' *.src
```

**Two sub-patterns:**
- `shell.start_terminal` — calling on a `get_shell` object. **NOT found** in the yuno_viper modules.
- `result.start_terminal` — calling on a return value from `lib.overflow()`. **Found** at `yuno_viper_scan.src:481`. This IS valid GreyScript (the `lib.overflow` result is typed as `shell`) but may silently do nothing or crash in greybel-js Mock. Mark as "verify with greybel-js mock" if user plans to test there.

### 3. Function/`end function` Balance — Three-Pattern Counting

A single `grep -c '\bfunction\b'` misses the `obj.method = function(...)` pattern (used exclusively in `post.src` and `util.src`). Use Python with ALL three declaration forms:

```python
import re
fn_decl = fn_stmt = fn_member = end_fn = 0
for line in lines:
    s = line.strip()
    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*=\s*function\s*\(', s): fn_decl += 1
    elif re.match(r'^function\s+[A-Za-z_][A-Za-z0-9_]*\s*\(', s): fn_stmt += 1
    elif re.match(r'^[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\s*=\s*function\s*\(', s): fn_member += 1
    if re.match(r'^end\s+function\s*$', s): end_fn += 1
total = fn_decl + fn_stmt + fn_member
print(f"opens={total}, end={end_fn}, diff={total-end_fn}")
```

**Case study (2026-07-04):** Initial bash scan with `grep -cE '^[A-Za-z_]* = function\('` on `yuno_viper_util.src` reported 0 function declarations vs 25 `end function` — apparently "broken". But the file uses 25 `obj.method = function(...)` and 0 `var = function(...)`. A three-pattern scan shows 25/25 ✅. **Without all three patterns, every VIPER-style module falsely reports a mismatch.**

### 4. `import_code(...))` Double-Closing Paren

A copy-paste bug where `import_code(f(...))` was intended but the generated code produces `import_code(("..."))` — the outer pair is from a string-concatenation wrapper:

```bash
grep -nE 'import_code\([^)]*\)\)' *.src
# Matches: import_code("x"))     — double paren (BUG)
# Ignores: import_code("x")      — single close (OK)
```

**Found:** 0 in all 5 yuno_viper modules. The only active `import_code` call is `yuno_viper_scan.src:11` → `import_code("yuno_viper_core")` — clean single close.

### 5. Multi-line Map Literals — Brace-Depth Balance

greybel-js accepts multi-line maps, but trailing commas + comments-inside-maps are fragile in BOTH engines. Verify each multi-line map is properly closed:

```python
import re
for i, line in enumerate(lines, 1):
    m = re.match(r'^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{\s*$', line.rstrip())
    if m:
        depth, j = 1, i
        while j < len(lines) and depth > 0:
            j += 1
            depth += lines[j-1].count('{') - lines[j-1].count('}')
        status = 'OK' if depth == 0 else f'NOT CLOSED (depth={depth})'
        print(f'{f}:{i}: "{m.group(2)} = {{" → {status}')
```

Also verify per-file `{` vs `}` count as a quick sanity:

```python
o, c = text.count('{'), text.count('}')
print(f"{f}: {{ = {o}, }} = {c}, diff = {o-c}")
```

**Case study:** 2 multi-line maps found (`yuno_viper_net.src:362` and `yuno_viper_post.src:652`), both correctly closed. Per-file brace balance: 0 diff across all 5 files.

## Reporting format — deliver as a structured table

| # | Check | Status | Findings |
|---|-------|--------|----------|
| (a) | Escaped quotes in print-Strings | ✅ Clean | 0 print() calls with `\"` |
| (b) | `start_terminal` divergence | ⚠️ Watchlist | 1 occurrence (`result.start_terminal` in scan.src:481) — valid API but verify against greybel-js Mock |
| (c) | Function/end function balance | ✅ Clean | All modules 0 diff with 3-pattern counting |
| (d) | import_code double-paren | ✅ Clean | 0 occurrences |
| (e) | Multi-line Maps | ✅ Clean | 2 multi-line maps, both correctly closed. File-level brace diff: 0/5 |

## Case study — yuno_viper modules (5 files, 3008 lines total, 2026-07-04)

| Module | Lines | (a) print `\"` | (b) start_terminal | (c) fn balance | (d) import_code )) | (e) multi-line maps |
|--------|------:|:-----------:|:-------------:|:------------:|:----------------:|:-----------------:|
| yuno_viper_core.src | 411 | 0 | 0 | 19/19 ✅ | 0 | 0 |
| yuno_viper_net.src | 553 | 0 | 0 | 19/19 ✅ | 0 | 1 ✅ (L362→367) |
| yuno_viper_post.src | 666 | 0 | 0 | 19/19 ✅ | 0 | 1 ✅ (L652→666) |
| yuno_viper_scan.src | ~704 | 0 | 1 (result) | 11/11 ✅ | 0 | 0 |
| yuno_viper_util.src | 660 | 0 | 0 | 25/25 ✅ | 0 | 0 |

## Key takeaways

- All 5 modules pass all 5 compatibility checks.
- The only watchlist item is `result.start_terminal` in `scan.src:481` — technically valid GreyScript, but greybel-js Mock may not support it.
- The initial "negative diff" finding for `post.src` and `util.src` was a **tooling artifact** (bash regex missed `obj.method = function(...)` pattern). Always use Python with 3-pattern counting.
- Session-specific audit findings documented: `references/greybel-js-compatibility-scan-2026-07-04.md` (in `greyhack-code-audit-befunde` skill).