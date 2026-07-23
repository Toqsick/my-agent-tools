# GreyScript Language Pitfalls — Detailed Reference

> Extracted from SKILL.md (sections "Critical Language Pitfalls", "Critical API Pitfalls", "Auto-Fix Strategie für Bulk-P0-Cleanup").
> Read this when a `.src` file fails at `build` time or behaves unexpectedly.
> For the short version see SKILL.md "Critical Language Pitfalls (quick ref)".

## 1. String literal rules

- **Double quotes only.** Single quotes cause silent syntax failures.
  - Error signature: `Invalid character 39 (Code: ')`
  - Fix: replace all `'...'` with `"..."`. Escape inner `"` with double-double: `""inner""`.
- **No backslash escapes.** `greybel-js` rejects `\` (Code 92). Affects nested string escaping and shell-command strings.
  - Error signature: `Invalid character 92 (Code: \)`
  - Fix: use `char(code)` instead, or omit the escape entirely. For `print("...\""...)` use single-quote outside, double-quote inside: `print("  importcode('bin/X.src')")`.
- **`\n` is literal text, not newline.** Use `char(10)` for real newlines.
- **`.strip()` does NOT exist** (NEW 2026-07-03) — silent in mock-env, CRASHES in real game with `Path "strip" not found in string intrinsics`. Use manual trim-loop. See section 8 for full list of missing string methods.

## 2. Indexing and iteration

- **Negative indexing `params[^0]` does NOT work.** Causes `compiler error` with no clear message.
  - Fix: `params[params.len - 1]` or a `lastParam()` helper.
- **`for x in list` iterates VALUES, not indices.** In MiniScript/GreyScript `for elem in myList` gives each ELEMENT, not the position.
  - To iterate by index: `for i in myList.indexes` (returns `[0, 1, 2, ...]`). Note: `.indexes` is a **property** on lists/maps — both `myList.indexes` and the **global function** `indexes(myList)` work (verified via `listLib.src` and `gsc-compiler` source).
  - To iterate both: loop over `.indexes` and index into the list.
  - Common symptom: `for i in headers; ... widths[i] ...` where `i` is a header string like `"name"` instead of integer `0`. The code then tries `widths["name"]` which crashes on arrays. Fix: `for i in headers.indexes`.
- **`hasIndex(key)` works** (verified 2026-07-07 via `gsc-compiler/src/runtime/object.bs` — map/list inherits from `collection.bs` which provides `hasIndex`). Returns `true`/`false` for key existence on lists, maps, and strings. Safer than unchecked index access:
  ```
  if myList.hasIndex(i) then ...     // safe even if i is out of bounds
  if myMap.hasIndex("key") then ...  // safer than myMap["key"] == null
  ```
- **⚠️ `range(N)` and `range(start, end)` are BOTH inclusive both ends** (discovered 2026-07-07, confirmed experimentally via greybel execute).
  - `range(7)` produces 8 iterations: `7, 6, 5, 4, 3, 2, 1, 0` (N down to 0 inclusive). That is `[N, 0]` with **N+1 elements**.
  - `range(0, 7)` produces 8 iterations: `0, 1, 2, 3, 4, 5, 6, 7` (start through end inclusive). That is `[start..end]` with **end-start+1 elements**.
  - This **differs from standard MiniScript** where `range(N)` produces N elements `[0..N)` and `range(start, end)` is end-exclusive.
  - **Practical effect:** Every `for i in range(N)` loop executes **N+1 times**, not N times. If you need exactly N iterations, use a `while` counter loop instead:
    ```
    i = 0
    while i < n
        body()
        i = i + 1
    end while
    ```
  - **Detection:** If a loop's expected output is always 1 element too long (e.g. a progress bar fills 6 cells when math says 5), check whether `range(n)` or `range(0, n)` is used. Both are affected.
- **List and string slicing work.** Full MiniScript 1.5.1 slice syntax: `list[start:]`, `list[:end]`, `list[start:end]`. String slices follow the same rules. No negative index bounds — use `list.len - N` instead.

## 3. Multi-line map/list literals

- Avoid in `lib_core` and large generated tools. Some GreyScript builds accept multi-line maps, but the legacy parser/installer path can fail with `got EOL where comma or rcurly is required`.
- **Prefer incremental assignment for maximum compatibility:**
  ```
  m = {}
  m["a"] = 1
  m["b"] = 2
  ```
  ```
  items = []
  items.push(value)
  ```
- If a map/list build fails, switch to incremental construction BEFORE debugging the business logic.

## 4. Exact compiler error signatures (cheat sheet)

| Error signature | Cause | Fix |
|-----------------|-------|-----|
| `got EOL () where comma or rcurly is required` | multi-line map or list literal | incremental assignment |
| `unexpected token` near `^` | negative index `params[^0]` or other Python idiom | use `params.len - 1` |
| `undefined function` near `.len` or `.join` or `.upper` | string/object API mismatch | check api-objects.md |
| `no matching open if block` at `<file>:<line>` | single-line `if ... then` has unwanted `end if` after it | either remove the `end if` or switch to multi-line `if cond then\n  body\nend if` |
| `Path "<method>" not found in string intrinsics` at any line with `.strip()`, `.trim()`, `.toLowerCase()` etc. | method doesn't exist in MiniScript/GreyScript | use manual loop or built-in alternative (see section 8) |
| `Invalid character 39 (Code: ')` | single quote `'` used | replace with `"..."` |
| `Build error: got Keyword where number, string, or identifier is required` | one-line `if ... then ... end if` in greybel | multi-line form only |
| `Build error: got Punctuator where number, string, or identifier is required` | `=======` separator line | delete or convert to `// ====` comment |
| `Build error: got Keyword 'if' where ")" is required` | ternary expression `("OK" if cond else "X")` | explicit `if/else/end if` block |
| `Invalid character 92 (Code: \)` | backslash escape in string | use `char()` or remove escape |

## 5. Single-line `if ... then` — greybel vs GreyScript

| Form | In-Game GreyScript | greybel-js |
|------|-------------------|------------|
| `if cond then action` (no `end if`) | ✅ accepted | ❌ rejected |
| `if cond then action end if` (one line) | ✅ accepted | ❌ rejected |
| `if not X then return end if` (one line) | ✅ accepted | ❌ rejected |
| multi-line `if cond then\n  body\nend if` | ✅ accepted | ✅ accepted |

**Confirmed 2026-06-19 + reinforced 2026-07-03:** All forms of one-line `if ... then ... end if` fail in greybel — regardless of whether body is assignment, return, function call, or expression. **NEW (2026-07-03)**: also the form `if not X then return end if` — counter-intuitive because it "looks like" the multi-line form compressed. Always expand to multi-line. Only multi-line works.

**`-u` flag does NOT work around this.** `greybel build` (with or without `-u`) rejects one-line `if`. The `-u` flag only affects output formatting/minification, NOT parser strictness. Tested 2026-06-19 across 10 files, re-confirmed 2026-07-03 (YUNO V3→V4 refactor: 18 inline-then-return end-if patterns needed conversion).

**`else if` chains are valid.** When a build error points at `else if`, check the PREVIOUS branch for one-line `if ... then ... end if`.

## 6. `=======` separator lines

Lines of `=` (e.g. `==========`) on their own cause `Build error: got Punctuator where number, string, or identifier is required`. greybel parses `=` as `==` operator and expects operands.

**Fix:** delete the line or convert to `// =====` comment. Verified 2026-06-25 in `src/filecore.src:276`.

## 7. Ternary expressions NOT supported

GreyScript and greybel do NOT support ternary `if`-expressions inside `(...)`. The parser treats `if` as a keyword, not an operator.

```
// FALSCH:
print("Result: " + ("OK" if ok else "FAILED"))

// RICHTIG:
if ok then
    print("Result: OK")
else
    print("Result: FAILED")
end if
```

Error signature: `Build error: got Keyword 'if' where ")" is required`.

## 8. Missing standard library functions

- **No `str_repeat()`** — define your own:
  ```
  space = function(n)
      if n < 0 then n = 0
      end if
      s = ""
      while s.len < n
          s = s + " "
      end while
      return s
  end function
  ```
- **No `get_system_time`** — not available. Use fixed prefixes like `[Hermes]`.
- **No `mkdir`** — use `pc.touch(path + "/.__init"); tmp = pc.File(...); if tmp then tmp.delete` to force directory creation.
- **No `is_folder` on File objects** — `not null` accidentally works. Use `is_binary` only and check `f.is_folder` only if you confirm it exists.
- **No `HTTP.Request()`** — GreyScript has no general HTTP client. For **file downloads** (URL → local file) the in-game replacement is `pc.wget(url, destPath)` (Computer method, returns nothing, creates/overwrites `destPath` on success). For **non-file HTTP** (JSON APIs, status endpoints like Hermes-API port 8333) there is no in-game replacement — probe via `pc.wget(url, probePath)` and check `pc.File(probePath)` for existence, OR fall back to host-side scripts and `import_code` for status. See section 8a below for the `pc.wget` probe pattern.
- **No `try` / `catch` / `end try` blocks** (NEW 2026-07-07) — GreyScript has no exception handling. Error signatures: `unexpected keyword Keyword[N:1 - N:8: value = 'end try'] at start of line` or `unexpected keyword Keyword[N:1 - N:6: value = 'catch']`. Replacement: pre-check inputs, null-guard every API call, use `pc.File()`-existence to detect failure (works for `pc.wget`), use `typeof()` to discriminate null/string/list/object returns.
- **No `number.floor` or `number.to_int`** (discovered 2026-07-07) — GreyScript numbers are **always floating-point**. The methods `.floor()` and `.to_int()` that exist in standard MiniScript are NOT available. For **non-negative** numbers, floor can be computed as `v - (v % 1)`. For negative numbers, use `(v - 1) - ((v - 1) % 1)` or test for sign. Common use case: converting a calculated count (like progress bar fill-cells) from float to integer.
  ```greyscript
  // FLOOR for non-negative numbers only:
  progressFloor = function(v)
      return v - (v % 1)
  end function

  // Example: progress bar fill-cell count
  percent = 35                            // 35% of 20 width
  filledRaw = (percent * 20) / 100        // → 7.0 (float)
  filled = progressFloor(filledRaw)       // → 7 (as float, no decimal)
  ```
- **`repeat` is a reserved keyword** (discovered 2026-07-07) — Do NOT define functions or variables named `repeat`, `repeat_`, or any variant. greybel's parser treats `repeat` as a keyword and produces build errors when it appears as an identifier. Rename to `progressRepeat`, `strRepeat`, `rep`, or similar.
  ```greyscript
  // FALSCH — "repeat" is reserved:
  repeat = function(text, n) ... end function

  // RICHTIG:
  progressRepeat = function(text, n) ... end function
  ```
- **No `.strip()` on strings** (NEW 2026-07-03) — MiniScript/GreyScript has no built-in string trim. Common JS/Python idiom fails silently in mock-env but **crashes in real game** with `Path "strip" not found in string intrinsics`. **Use manual trim-loop:**
  ```
  trim = function(s)
      while s.len > 0 and s[0] == " "
          s = s[1:]
      end while
      while s.len > 0 and s[s.len - 1] == " "
          s = s[:s.len - 1]
      end while
      return s
  end function
  ```
  Other missing string methods to be aware of: `.trim()`, `.trimLeft()`, `.trimRight()`, `.toLowerCase()` (use `s.lower()`), `.toUpperCase()` (use `s.upper()`), `.startsWith()`/`endsWith()` (use `indexOf` + length check). See `references/known-quirks.md` for the full list.

## 9. Recursive helper-function bug (NEW 2026-07-03)

When refactoring a script to extract boilerplate into a helper, a common mistake is to apply the SAME regex-replace that converts the boilerplate to the helper's OWN definition. This causes infinite recursion and build failure.

### Symptom
```
Build error: got Keyword[352:27 - 352:33: value = 'end if'] where number, string, or identifier is required
```
or runtime error: `Path "<method>" not found in string intrinsics` from the recursive call.

### Wrong pattern (auto-replace applied too broadly)
```greyscript
// Before refactor:
obj = main_session.object
if not obj or typeof(obj) != "shell" then
    print("[!] Not in shell!", "red")
    return
end if
pc = obj.host_computer

// Step 1: write the helper
require_shell = function()
    pc = require_shell()        // ← BUG: recursive self-call
    if not pc then return end if
    return obj.host_computer
end function

// Step 2: regex-replace the boilerplate in rest of file (CORRECT step)
// But because helper contains "pc = obj.host_computer", the helper ITSELF may
// get matched by the same regex if not careful.
```

### Correct pattern
1. **Write the helper FIRST** with its full body.
2. **Then run the regex** on the rest of the file.
3. **Never apply the helper's own pattern to itself** — exclude the helper definition from the regex scope (e.g. by reading the file, finding the helper's line range, and applying the replace only outside that range).
4. **Test build immediately** after each patch — don't batch 10 regex-replaces before testing.

### Verified lesson (YUNO V3 → V4 refactor, 2026-07-03)
Helper `require_shell()` was auto-replaced from `pc = obj.host_computer` pattern, creating `pc = require_shell()` inside the helper itself. Build error pointed at line 352 (a function call site), not at the helper definition. Solution: read the helper's body, restore the original `obj = main_session.object` + `if not obj or typeof(obj) != "shell" then` + `return obj.host_computer` lines.

## 10. Type-safety on return values

- **`.val` can return `null` on bad input** — always null-guard.
- **`list.remove(x)` is by INDEX, not value** — must `indexOf()` first and null-check.
- **`chmod()` returns `1` on success**, not the new mode value.
- **Type-check EVERY return.** Crypto/Metaxploit functions return `null`, an error string, a list, or a typed object depending on outcome. Triple-check with `typeof()`:

```
result = crypto.smtp_user_list(ip, port)
if result == null then fail("No response")
end if
if typeof(result) == "string" then fail("SMTP error: " + result)
end if
if typeof(result) != "list" then fail("Unexpected type: " + typeof(result))
end if
```

Same pattern for `lib.overflow()` — always `typeof()` the result before processing. It may return Shell, Computer, File, String, or Number.

## 11. Suffix check vs indexOf for file extensions

`path.indexOf(".src")` matches `.src` anywhere in the path (e.g. `.src_backup.lib`). For file extensions use suffix check with length:

```
isSrc = false
if path.len >= 4 then
    if path.slice(path.len - 4) == ".src" then
        isSrc = true
    end if
end if
```

## 12. Unvollständige Funktionen brechen den Build downstream

If a function starts with `function(...)` but has no `end function`, or an `if ... then BODY` has no `end if`, greybel does NOT complain at the broken place — it complains at the NEXT block that tries to close the structure. Symptom: error points at an entirely harmless line.

**Verified 2026-06-25** in `src/filecore.src` (`safeWriteFile` without `end function` + `return`; `safeCopy` without `end function`; a single `if ... then` without `end if`).

**Diagnostic strategy:** when a build error points at a syntactically correct line, walk BACKWARD and check the previous functions/if-blocks for missing `end function` / `end if`.

## 13. `import_code` vs `include_lib`

| Function | Use for | When evaluated |
|----------|---------|----------------|
| `import_code(absolutePath)` | YOUR code, helpers (`lib_core`) | compile time (baked in) |
| `include_lib(libPath)` | SYSTEM libraries (`crypto.so`, `metaxploit.so`, `aptclient.so`) | runtime |

Rule: *eigener Baustein* → `import_code`. *System-Library* → `include_lib`.

## 14. Missing `)` after `]`/`}` in array/map literals — wrong-line cascade (NEW NP-81, 2026-07-07)

Section 12 above covers the case where greybel reports an error on a syntactically correct line because of a **missing `end function`/`end if` further up**. The same wrong-line cascade happens for **missing closing bracket** in array/map literals — but with a different signature.

### Symptom

A multi-line `render([...], [...])` or `[fn(...), fn(...)]` block where one of the inner `]` lines lacks the closing `)` produces a parser error pointing at a **seemingly-unrelated token dozens of lines later**:

```
got Identifier[47:1 - 47:5: value = 'step'] where any of ",", ")" is required at wifi_crack.src:38:22
```

The error says line 47 (`step(...)`) is the problem, but `step` is actually fine — the **real** bug is on line 44 (or wherever the bracket is unclosed):

```greyscript
// BEFORE — broken: line 44 has ] without  ):
render("WiFi Crack", [
    "Interface: " + iface,
    "BSSID:     " + bssid,
    ...
    "Capture:   " + captureFile
]                       // ← missing ")" — parser keeps consuming

// AFTER — both lines:
    "Capture:   " + captureFile
])                      // ← "])" closes render(...)
```

### Why this is harder to spot than section 12

Section 12's cascade errors point at an inner keyword (`end if`, `end function`). This cascade errors at **whatever the next unparseable identifier happens to be** — could be `step`, `print`, `ok`, anything. The line:col numbers can be **off by tens of lines** because greybel walks forward looking for `)`.

### Diagnostic recipe (NEW 2026-07-07)

When a build error points at a syntactically valid identifier (a function name, a variable name, a method call) at `file:line1:col`, AND the `:col` is suspiciously early in the line (col 1-5), assume **bracket cascade**:

1. Open the file and **search backward** from the line number mentioned in the error (`:line1`), looking for multi-line `(`/`[`/`{` blocks that may be missing their closer.
2. Specifically check every line in the previous 20-40 lines that ends with `]`, `}`, or `)`. If any one lacks the **outer closer** it expects (e.g. `]` followed by `\n` instead of `]), `}, `),), the bug is there — not at the error site.
3. **If the file has multiple such blocks, fix and re-build between each** — the error cascades through every one of them, and fixing the first may surface a second.
4. **Walk backward, then forward, then forward again.** Wifi_crack had TWO missing `)`s (lines 44 AND 111). Fixing only line 44 made the error re-emerge at line 114 (a different bracket). Don't stop at the first fix.

### Verified session (Welle-2 fix, 2026-07-07, `wifi_crack.src`)

- Initial error: `got Identifier[47:1 - 47:5: value = 'step'] where any of ",", ")" is required at wifi_crack.src:38:22`
- First fix attempt (Z44): `]` → `])` → **new** error `got Identifier[114:1 - 114:10: value = 'logToFile'] where any of ",", ")" is required at wifi_crack.src:106:29`
- Second fix (Z111): `]` → `])` → Build done.

### Distinguishing from section 12

| Section 12 cascade | Section 14 cascade (NP-81) |
|---|---|
| Missing `end function` / `end if` | Missing `)` after `]`/`}` |
| Error usually at next `end if`/`end function` | Error at next unparseable identifier anywhere |
| Col near 1-3 typically | Col usually 1-5 |
| Sympton: `got Keyword 'end if' where ...` | Symptom: `got Identifier[<name>] where any of ",", ")" is required` |
| Diagnostic: walk back ~10 lines | Diagnostic: walk back 20-40 lines, check every `]`/`}` for trailing closer |

## 14a. String-in-String without `+` — quote-in-print crash (NEW NP-80, 2026-07-07)

Distinct from NP-81 (missing closer) and section 1 (backslash escape): when a print() or any string literal **already inside double-quotes** embeds another double-quoted word **without `+` concatenation**, greybel parses it as two separate adjacent strings and crashes.

### Symptom

```
got Identifier[159:47 - 159:57: value = 'metaxploit'] where any of ",", ")" is required at <file>:158:1
```

…where line 159 contains `print("Adressen (manueller Exploit via "metaxploit"):")` — the inner `"metaxploit"` Quotes brechen the outer string. The parser sees `"Adressen (manueller Exploit via "` (string ends), then `metaxploit` (identifier, unexpected), then `""` (empty string), and bails at `metaxploit`.

### Three fix variants

**1. Use `char(34)` (always works, no parser ambiguity):**
```greyscript
print("Adressen (manueller Exploit via " + char(34) + "metaxploit" + char(34) + "):")
```

**2. Drop the inner quotes when context is unambiguous:**
```greyscript
print("Adressen (manueller Exploit via metaxploit):")
```

### Detection grep

```bash
# Find lines with two `"` pairs where the inner ones are not preceded by `+`
grep -nE '"[^"]*"[^,)+]*"[^"]*"' *.src
```

Each match is a candidate for the fix. False positives are print-message strings containing nested-data (suid_exploit.src's GTFOBins entries — see pattern (d) false-positive lesson 2026-07-07) — verify with `read_file` + 3 lines context.

### Why this is NOT the same as section 1 (backslash escape)

Section 1 covers `\"` (backslash-escape) inside a double-quoted string — that's `Invalid character 92`. This section covers **bare nested `"`** without escape, without concatenation — that's `got Identifier`. Different signature, different fix.

### Verified session (Welle-2 fix, 2026-07-07, `auto_exploit.src:159`)

- Error: `got Identifier[159:47 - 159:57: value = 'metaxploit'] where any of ",", ")" is required at <file>:158:1`
- Code: `print("  Adressen (manueller Exploit via "metaxploit"):")`
- Fix: `char(34)` concatenation → builds clean.

## 15. Inline multi-line `function` body in argument position (NEW NP-82, 2026-07-07)

GreyScript's `function(...) ... end function` block is a **statement**, not a general expression. greybel's parser rejects it when used **inline as an argument** to another call, regardless of whether the body is multi-line or single-line. Multi-line is by far the more common failure mode (existing `bug-sweep-2026-07-07-learnings.md` pattern (a) covers the single-line version of this trap for `if`, not `function`).

### Symptom

```
got Identifier[23:2 - 23:7: value = 'print'] where any of ",", ")" is required at <file>:22:8
```

…where line 22 is `obj.method(function(kv)` (or any multi-arg `function(...)` opener). The next line's `print(...)` body is what greybel reports, but the **real** problem is that the inline function-as-argument expression never closes properly.

### Why this fails even with a SINGLE parameter

Reproduced in `/tmp/test-each{2,4,5,6}.src`. **Every** variation fails:

```greyscript
// All four fail the same way:
obj.method(function(name); body; end function)
obj.method(function(); body; end function)
obj.method(function(name)
body
end function)
obj.method(function()
end function)
```

greybel parses `obj.method(EXPR)` and `EXPR` must be a complete expression in that position. `function(name); body; end function` is **not** a complete expression in argument context — the parser looks for `,` or `)`, sees `print` (or whatever the body starts with), and bails.

### Correct pattern: assign the function to a variable first

```greyscript
// CORRECT (verified 2026-07-07):
printer = function(name); print(name); end function
obj.method(printer)
```

The function-as-statement form only works when the parser sees it on the **right side of `=`**. Assignment makes it a complete top-level statement, which the parser accepts. Verified with `/tmp/test-each7.src`, `test-each8.src`, `test-each9.src` — all build successfully.

### Implications for `each`/`map`/`reject`/`select`/`lsort` callbacks

The listLib (`greyhack-tools/list-lib/listLib.src`) defines `map.each(func)` as:

```greyscript
map.each = function(func)
    list = self.to_list(true)
    result = list[0:]
    for i in indexes(list)
        func(result[i][0], result[i][1])     // ← 2-arg callback
    end for
end function
```

…which **does** call `func(key, value)`. The lib API is correct. The problem is on the **call site**: you cannot declare `function(k, v)` because greybel's `function` header doesn't accept multi-param either — only `function(name)` where `name` becomes an implicit args-list.

### Complete fix recipe

```greyscript
// BEFORE (broken — both inline AND multi-param):
a.each(function(k, v)
    print(k + ":" + v)
end function)

// AFTER (correct — variable-assigned, single param, indexed):
kvPrinter = function(kv); print(kv[0] + ":" + kv[1]); end function
a.each(kvPrinter)
```

Single-line `;`-separated body in the variable assignment is preferred for one-liners; multi-line `function(kv)\n body \n end function` also works **when assigned to a variable**. The restriction is only on the **inline-as-argument** form.

### Detection grep

For an existing codebase, scan for this pattern:

```bash
grep -nE '\.\w+\(function\(' *.src
```

Every match is a candidate for the variable-assignment refactor.

### Verified session (Welle-2 fix, 2026-07-07, `list-lib/tests.src`)

- Initial error: `got Identifier[23:2 - 23:7: value = 'print'] where any of ",", ")" is required at tests.src:22:8`
- Reporter's diagnosis: "wrong each() API" — **WRONG.** `map.each` does call `func(key, value)` per listLib.src:53-58.
- Real diagnosis: inline `function(k, v)\n print()\n end function` is invalid argument expression.
- Fix: 5 blocks converted to `name = function(...); body; end function; obj.method(name)`.
- Verified builds clean: `Build done. Available in /tmp/build-agent-h/tests/build.`

## 16. `continue` in for-loops — verified (NEW 2026-07-07)

`continue` works correctly inside both `for i in range(N) ... end for` and `for elem in list ... end for` loops. Verified via existing greyhack-tools codebase (`auto_exploit.src` uses `continue` inside `for i in range(targLen)` at line 208).

### Correct usage

```greyscript
for i in range(targets.len)
    if not targets[i] then
        continue        // skip null entries, continue to next i
    end if
    // process targets[i]
end for
```

### Common pattern: filter-then-process inside a single loop

```greyscript
for elem in fileList
    if not elem or elem.len < 4 then
        continue
    end if
    suffix = elem.slice(elem.len - 4)
    if suffix != ".src" then
        continue
    end if
    // only .src files reach here
end for
```

### When NOT to use `continue`

- **In `while` loops** — no verified examples in codebase (may or may not work, prefer explicit `if/else` branches).
- **In inline one-line `if cond then action` blocks** — `continue` inside a one-liner would be rejected by greybel anyway (see section 5).

### Distinguishing from section 7 (ternary) and section 15 (inline function)

`continue` is a **statement**, not an expression. It does NOT conflict with ternary restrictions or inline-function restrictions — but it CAN cascade if an outer `for` has a missing `end for` (see section 12 pattern). If a loop stops halfway through, check whether the `end for` is present.

## 8a. `pc.wget()` as in-game file-fetch / HTTP-replacement (NEW 2026-07-07)

The skill historically stated "GreyScript has no HTTP" and pointed to host-side workarounds (greybel-js installer, manual copy-paste, SQLite). That is **wrong for file downloads** — GreyScript's `Computer` object exposes `pc.wget(url, destPath)` which downloads a URL to a local file. Discovered 2026-07-07 fixing `bootstrap.src` (4 `HTTP.Request(...)` calls all replaced).

### Signature

```
pc.wget(url: string, destPath: string)   // Computer method
```

- **Returns:** nothing (`null`). No boolean, no error string. **The only way to detect success is to check `pc.File(destPath)` afterwards.**
- **Effect on success:** creates or **overwrites** the file at `destPath`. Does NOT require the parent directory to exist (GreyScript auto-creates parent dirs on `pc.touch()`/`pc.File()` access).
- **Effect on failure:** does nothing. `pc.File(destPath)` returns `null`.
- **Availability in greybel-js Mock Env:** ❌ **NOT exposed.** Mock-env execution throws `Runtime error: Path "wget" not found in map`. This is a known greybel-vs limitation, NOT a real bug — the method works in-game. Always verify with `greybel build -dbf` (compile check), not `greybel execute -et Mock`.

### Three proven patterns

**1. File download (URL → local file in for-loop):**
```greyscript
for f in files
    url  = baseUrl + "/" + f
    path = BIN_DIR + "/" + f
    print("  Download: " + f)
    pc.wget(url, path)
    file = pc.File(path)
    if file then
        downloaded = downloaded + 1
        print("    -> OK (" + file.size + " Bytes)")
    else
        failed.push(f + " (download fail)")
        print("    -> FEHLER (Download)")
    end if
end for
```

**2. URL reachability probe (host detection / fallback chain):**
```greyscript
// pc.wget writes to probePath on success; existence = URL reachable
probePath = "/tmp/.bootstrap_probe"
pc.touch(probePath)
probeFile = pc.File(probePath)
if probeFile then
    probeFile.delete
end if
probeFile = null

sourceURL = null
pc.wget(URL_A + "/known_file", probePath)
probeFile = pc.File(probePath)
if probeFile then
    sourceURL = URL_A
    probeFile.delete
end if

if not sourceURL then
    pc.wget(URL_B + "/known_file", probePath)
    probeFile = pc.File(probePath)
    if probeFile then
        sourceURL = URL_B
        probeFile.delete
    end if
end if
```

**3. Non-file HTTP probe (status check, JSON API like Hermes-API port 8333):**
```greyscript
// pc.wget may or may not work depending on whether endpoint serves a file
apiURL = "http://127.0.0.1:8333/status"
apiProbe = "/tmp/.hermes_api_probe"
pc.touch(apiProbe)
apiProbeFile = pc.File(apiProbe)
if apiProbeFile then
    apiProbeFile.delete
end if
pc.wget(apiURL, apiProbe)
apiRespFile = pc.File(apiProbe)
if apiRespFile then
    print("  [OK] Hermes API erreichbar (pc.wget)")
    apiRespFile.delete
else
    print("  [!] Hermes API nicht erreichbar (Port 8333)")
end if
```
For endpoints that don't serve files (true JSON APIs), `pc.wget` will fail silently → `pc.File(apiProbe)` returns null → user sees the "not reachable" branch. **Comment the file with TODO if the response body is actually needed — `pc.wget` cannot read the response, only write it to disk.** For richer HTTP interaction (POST, headers, JSON parsing), use host-side scripts (`curl`, `python3`) and `import_code`.

### Cleanup-before-wget: usually unnecessary

`pc.wget` overwrites the destination if it already exists, so the
`pc.touch(probePath); pc.File(probePath); if file then file.delete` dance
is only needed when you want the probe to fail on the second iteration
of a retry loop (i.e., you need `pc.File` to return null BEFORE the call,
not after a previous successful probe). For one-shot probes or for-loop
downloads, skip the pre-cleanup.

### Replacement recipe for `HTTP.Request(url, "GET")` + try/catch

**Before (compile error: `unexpected keyword 'end try'`):**
```greyscript
try
    content = HTTP.Request(url, "GET")
catch e
end try
if content and content.len > 10 then
    // use content
end if
```

**After (two-step: download, then read content):**
```greyscript
destPath = "/tmp/.dl_" + f
pc.wget(url, destPath)
downloaded = pc.File(destPath)
if downloaded then
    content = downloaded.get_content   // File.get_content() returns string
    if content.len > 10 then
        // use content
    end if
    downloaded.delete
end if
```

The pattern splits the old "fetch + check size" into two steps because `pc.wget` returns nothing — success is detected via `pc.File()`, content is read via `File.get_content()`.

### Proven session benchmarks

- 2026-07-07, `greyhack-tools/bootstrap/bootstrap.src` v1.1.0 → v1.2.0: replaced **4 `HTTP.Request(...)` calls** + **3 `try/catch/end try` blocks**, builds clean via `greybel build -dbf`.
- 2026-07-07, `tests/run_all.src`: replaced **1 ternary** `status = "PASS" if r["ok"] else "FAIL"` → multi-line if/else, builds clean.

### Migration checklist for files with HTTP.Request

1. `grep -n 'HTTP\.Request' file.src` → count sites.
2. `grep -nE '^\s*(try|catch|end try)\s*$' file.src` → count try-blocks.
3. For each `HTTP.Request(url, "GET")`: replace with `pc.wget(url, destPath)`.
4. For each `try/catch/end try`: remove all three lines. Replace `catch` body (error logging) with a plain `else` branch on the existence check after the `pc.wget` call.
5. Build-verify: `greybel build file.src /tmp/out/ -dbf` → expect `Build done`.
6. Pair-balance check: `grep -cE '^\\s*if\\b' file.src` should equal `grep -cE '^\\s*end if\\b' file.src`.

---

## 17. Description-line / module-identity line: `greybel build` ✓ → `greybel execute` ✗ (NEW 2026-07-07)

GreyScript `.src` files commonly start with a **description-line identity pattern**: a bare name on its own line, followed by a description string literal on the next:

```greyscript
uicore
"UI-Helper fuer das Control Center"
```

This pattern is used by `libcore.src`, `cliFeedback.src`, and the new `uicore.src`/`configcore.src` from the Control Center v1.0 session. **`greybel build` accepts it without error** — the compiler treats it as a top-level metadata annotation.

**However, `greybel execute` (the interpreter) crashes** with:

```
Path "uicore" not found in scope
```

### Root cause

The `greybel` parser interprets a bare identifier on a line by itself as a **path reference**, not a declaration. When the interpreter tries to execute the script, it attempts to resolve `uicore` as a scope-relative path, fails, and throws a runtime error before the description line is even reached.

The `greybel build` compiler, by contrast, skips standalone identifiers that appear to be metadata, so the build succeeds.

### Impact

- **All files using this pattern** (libcore.src, cliFeedback.src, uicore.src, configcore.src) crash on `greybel execute` but build fine
- The pattern is **harmless in-game** — the game's runtime parser handles it correctly
- Only affects **greybel-js Mock-Env execution**, not real in-game deployment

### Verified scope

| File | Pattern | `greybel build` | `greybel execute` |
|------|---------|-----------------|-------------------|
| `libcore.src` | `libcore` + `"..."` | ✅ Build done | ❌ `Path "libcore" not found` |
| `uicore.src` | `uicore` + `"..."` | ✅ Build done | ❌ `Path "uicore" not found` |
| `configcore.src` | `configcore` + `"..."` | ✅ Build done | ❌ `Path "configcore" not found` |

### Strategy

- **Keep the pattern for real deployment** — it's the standard GreyScript module identity convention
- **Do NOT rely on `greybel execute` for smoke-testing files that use this pattern** — use `greybel build` + in-game testing instead
- For Mock-Env testing: import these modules via a wrapper that doesn't use the description-line convention

### Detection

```bash
grep -n '^[a-zA-Z_][a-zA-Z0-9_]*$' *.src | head -20
```

If followed by a string literal, it IS the pattern. If it's a standalone `for`, variable declaration, or assignment, it is something else.

### Verified session (Control Center v1.0, 2026-07-07)

Built: `uicore.src`, `configcore.src`, `controlcenter.src` — all 3 pass `greybel build`.
Runtime test: `uicore.src` fails `greybel execute` with `Path "uicore" not found in scope`.
Verdict: **build tool is the authoritative check**; interpreter limitations are a known Mock-Env quirk.

---

## 18. `import_code` path rewriting by `greybel build` (NEW 2026-07-07)

When you use **relative** `import_code()` paths in a `.src` file, `greybel build` rewrites them to **absolute in-game paths** at compile time.

### Behavior

Source file `tools/controlcenter.src` contains:
```greyscript
import_code("../src/uicore.src")
```

After `greybel build`, the compiled output contains:
```greyscript
import_code("/root/src/uicore.src")
```

The tool resolves the relative path against the source file's location, then converts it to an absolute path in the build tool's internal "in-game root" (`/root/` by default).

### What this means for deployment

- The build output is **already path-rewritten for in-game use** — no manual path fixing needed
- If you run the build output in greybel's Mock-Env, rewritten paths fail (because `/root/src/` doesn't exist on your dev machine) — this is expected
- The original `.src` source files keep their relative paths (only the build output changes)

### Compile-time dependency bundling

`greybel build` also **bundles dependencies** when it encounters `import_code()`:

```
build/                     ← output base dir
  controlcenter.src        ← main file, imports rewritten
  src/                     ← bundled dependency dir
    uicore.src             ← uicore module (full content)
    configcore.src         ← configcore module (full content)
```

This bundling is automatic — no configuration needed.

### Practical workflow

```bash
# 1. Build with relative import_code paths — tool handles resolution
greybel build tools/controlcenter.src -o /tmp/build

# 2. Verify the build output contains correct in-game paths
grep "import_code" /tmp/build/build/controlcenter.src
# → import_code("/root/src/uicore.src")  ← automatically rewritten

# 3. Deploy via setup script or copy-paste — paths work in-game
```

### Verified session (Control Center v1.0, 2026-07-07)

- Source: `tools/controlcenter.src` with `import_code("../src/uicore.src")`
- Build: `greybel build tools/controlcenter.src -o /tmp/test-controlcenter.build`
- Output: dependency rewriting successful, bundled correctly under `build/` with `src/` subdirectory

---

## 19. Map-based module export pattern (NEW 2026-07-07)

For modular multi-file GreyScript projects, the recommended pattern is **map-based namespace export** — a clean alternative to `lib_core`'s framework singleton.

### Pattern

Instead of relying on `lib_core`'s `getContext()`, each module exposes its API via a **top-level map**:

```greyscript
// src/uicore.src — UI-Helfer-Modul

// Helper functions defined with a unique prefix to avoid name collisions
_uicoreRepeat = function(text, n)
    out = ""
    if typeof(text) != "string" then return out
    if typeof(n) != "number" or n <= 0 then return out
    i = 0
    while i < n
        out = out + text
        i = i + 1
    end while
    return out
end function

// Public functions
_uicoreLine = function()
    print(_uicoreRepeat("-", 30))
end function

_uicoreHeader = function(title)
    print("")
    _uicoreLine()
    if title.len > 0 then print(" " + title)
    _uicoreLine()
end function

// Export via map — @ is PFLICHT (verified 2026-07-14 Mock)
// OHNE @: Function wird SOFORT mit null-Args ausgeführt, Map speichert den Return (oft null)
// MIT @: Function-Ref wird gebunden, Aufruf später via uicore.line()
uicore = {}
uicore["line"] = @uicoreLine
uicore["header"] = @uicoreHeader
uicore["clear"] = @uicoreClear
// ... more exports ...
```

Consumers import and use it:

```greyscript
import_code("/home/user/bin/uicore.src")
uicore.header("Hauptmenue")          // map-dispatch call
```

### Why map-based export?

| Aspect | lib_core pattern | Map-export pattern |
|--------|-----------------|-------------------|
| **API surface** | Inferred from `getContext()` + global functions | Explicit via map keys |
| **Name collisions** | All helper functions are global | Only the map name is global |
| **Intelli-sense** | None in GreyScript | Map keys self-document |
| **Dependency** | Requires full lib_core framework | Standalone module |
| **Module boundary** | Implicit | Clear (the map is the API) |

### ⚠️ Bare Identifier + Docstring line is NOT identity — it CRASHES at execute

```greyscript
// ❌ BREAKS at runtime: Path "uicore" not found in scope
uicore
"UI-Helfer fuer das Control Center v1.0"

// ✅ Use comments only for the module label; export map later
// uicore — UI-Helfer fuer das Control Center v1.0
uicore = {}
uicore["line"] = @uicoreLine
```

Same for `configcore`, `libcore`, `controlcenter` bare headers discovered 2026-07-14 controlcenter session.

### Combined with the description-line identity (historical / unsafe)

Do **not** use bare identifier + string docstring identity lines as module headers in executables. Prefer comments + map export with `@`.

```greyscript
// configcore — key=value Config-Persistenz
configcore = {}
configcore["load"] = @configcoreLoad
configcore["save"] = @configcoreSave
```

### Config persistence pattern (companion)

For modules that need persistent state, use the **config map** pattern:

```greyscript
// configcore — key=value Config-Persistenz-Modul (comment only, no bare id)

// Defaults (merged when config file is missing keys)
_DEFAULTS = {}
_DEFAULTS["theme"] = "classic"
_DEFAULTS["defaultScanRange"] = "192.168.0.0/24"
_DEFAULTS["showHints"] = "1"

_configParse = function(raw)
    // Parse "key=value" lines into map
    // ...
end function

_configSerialize = function(data)
    // Serialize map back to key=value lines
    // ...
end function


configLoad = function(pc, path)
    // Load: pc.File(path) → get_content() → parse → merge with defaults
    configFile = pc.File(path)
    if configFile == null then
        return _DEFAULTS  // file doesn't exist → use defaults
    end if
    raw = configFile.get_content
    if raw == null or raw.len == 0 then
        return _DEFAULTS
    end if
    parsed = _configParse(raw)
    // Merge parsed into _DEFAULTS (parsed takes precedence)
    // ...
    return mergedMap
end function

configSave = function(pc, path, data)
    // Save: serialize → pc.touch(path) → pc.File(path).set_content()
    serialized = _configSerialize(data)
    pc.touch(path)
    f = pc.File(path)
    if f == null then return 0
    return f.set_content(serialized)
end function

configcore = {}
configcore["load"] = configLoad
configcore["save"] = configSave
```

Key points of the config persistence pattern:

- **`pc.touch(path)` creates the file** if it doesn't exist (returns `""` on success, string on error)
- **`pc.File(path).get_content()` reads content** as a single string (returns `null` if file doesn't exist)
- **`pc.File(path).set_content(string)` writes content** (returns `1` on success, `null` on failure)
- **Defaults merging** ensures missing keys don't crash the app — the config always contains at least the defaults

### Verified session (Control Center v1.0, 2026-07-07)

- `src/uicore.src` (163 lines) — 6 API functions exposed via `uicore` map
- `src/configcore.src` (216 lines) — load/save with defaults merging via `configcore` map
- `tools/controlcenter.src` (290 lines) — event loop consuming both modules
- All 3 files: `greybel build` ✅, 22/22 CI build ✅

---

## 20. MiniScript-Manual vs. GreyHack-Engine: 1-based Indexierung (source-confirmed 2026-07-14)

GreyScript basiert auf MiniScript 1.5.1 — und **die offiziellen MiniScript-Manuals sagen 0-based Indexierung**. Die GreyHack-Engine (V0.9.6771-beta) verwendet jedoch **1-based** Indexierung für Listen, Strings und `range()`.

### Der Konflikt

| Quelle | Indexierung | Beleg |
|--------|------------|-------|
| MiniScript 1.5.1 Manual (offiziell) | 0-based | `myList[0]` = erstes Element |
| GreyHack Engine (V0.9.6771-beta) | **1-based** | `myList[1]` = erstes Element |
| `greybel-js` (Mock-Env) | **1-based** | Folgt GreyHack, nicht MiniScript |
| Community-Doku (documentation.greyscript.org) | **1-based** | "In-game implementation uses 1-based" |

### Betroffene Konstrukte

- **Listen-Zugriff:** `list[1]` = erstes Element (nicht `list[0]`)
- **String-Zugriff:** `str[1]` = erstes Zeichen (nicht `str[0]`)
- **`range(5)`:** liefert 6 Werte `[5, 4, 3, 2, 1, 0]` — inklusive beider Enden (nicht `[0, 1, 2, 3, 4]`)
- **Slicing:** `list[1:3]` = Elemente 1 und 2 (nicht 0 und 1)

### Praktische Konsequenz

Wenn Code aus MiniScript-Tutorials oder alter Doku 1:1 übernommen wird, greift er auf das **falsche Element** zu — oder crasht bei Index 0:

```greyscript
// FALSCH (MiniScript-Standard — 0-based):
if list[0] == nil then ...   // würde list[1] erreichen wollen, greift auf nonexistentes Element 0

// RICHTIG (GreyHack — 1-based):
if list[1] == nil then ...
// Alternativ: Prüfe Existenz mit hasIndex
if not list.hasIndex(1) then ...
```

### Quellen-Nachweis

- `main.greyscript.org/manuals/` — MiniScript-basierte Manuals: `Numbers: 0. Introduction (0-based)`
- `documentation.greyscript.org/` — "Indexing differences: In-game implementation uses 1-based indexing"
- `greyscript.net/api` — "Note: GreyScript uses 1-based indexing"
- In-Game-Test (V0.9.6771-beta) bestätigt 1-based

### Siehe auch

- Abschnitt 2 (Indexing and iteration) oben — speziell `range()` und `hasIndex()`
- Abschnitt 21 (Undocumented built-in functions) — `format()`, `floppy()` etc. sind NICHT in der offiziellen API

---

## 21. Undocumented Built-in Functions — game-intern, nicht in der offiziellen API (discovered 2026-07-14)

Die folgenden Funktionen tauchen in KEINER der 5 offiziellen/inoffiziellen GreyScript-Quellen auf. Sie sind **interne Game-Befehle** und existieren NICHT als API-Funktionen:

### Liste der nicht-konformen Built-ins

| Funktion | Status | Alternative / Hinweis |
|----------|--------|----------------------|
| `format(formatStr, val1, val2, ...)` | ❌ Nicht in API | Manuelle String-Konkatenation: `"Wert: " + val + " Einheiten"` |
| `floppy(path)` | ❌ Nicht in API | Spezifischer floppy-disk-access (niedrige Ebene) — vermutlich game-interner Pfad |
| `file_diff(path1, path2)` | ❌ Nicht in API | Dateivergleich manuell per `File.get_content()` + `==` |
| `file_router_ip(ip)` | ❌ Nicht in API | Router-IP via `network_gateway` Property |
| `file_bits(path)` | ❌ Nicht in API | Dateigröße via `File.size` Property |
| `input()` | ❌ Nicht in API | `user_input(prompt, [password], [key])` verwenden |
| `clear()` | ❌ Nicht in API | `clear_screen()` verwenden |
| (irgendein `HTTP.Request()`) | ❌ Nicht in API | `pc.wget(url, destPath)` für Downloads; host-seitige Tools für API-Calls |
| `try/catch/end try` | ❌ Nicht in API | Pre-Checks + `typeof()`-Guards verwenden |

### Warum diese Liste wichtig ist

Code aus inoffiziellen Quellen, YouTube-Tutorials oder AI-generierte GreyScript-Snippets nutzen oft diese nicht-existenten Funktionen. Der Fehler ist schwer zu debuggen, weil:

1. `format()` wird als globale Funktion gesucht → `Path "format" not found in scope`
2. `input()` crasht mit → `Path "input" not found in string intrinsics`
3. `try/catch` erzeugt → `unexpected keyword 'end try'`

### Prüf-Regex für Code-Reviews

```bash
# Nach undokumentierten Built-ins suchen
grep -nE '\b(format|floppy|file_diff|file_router_ip|file_bits|input)\s*\(' *.src
# Nach try/catch suchen
grep -nE '^\s*(try|catch|end try)\s*$' *.src
```

### Quellen-Nachweis

- `documentation.greyscript.org` — API-Doku: **keine** der genannten Funktionen gelistet
- `main.greyscript.org/manuals/` — 5 Manuals: **keine** der genannten Funktionen
- `greyscript.net/api` — API-Übersicht: **keine** der genannten Funktionen
- `codedocs.ghtools.xyz` — Such-Doku: **keine** der genannten Funktionen
- `github.com/ayecue/greybel-js` — greybel Source: **keine** der genannten Funktionen in `src/runtime/`

**Fazit:** Diese Funktionen existieren NICHT in der GreyScript-Programmiersprache. Sie sind entweder game-interne C++-Funktionen des GreyHack-Servers oder Halluzinationen aus AI-Training.
