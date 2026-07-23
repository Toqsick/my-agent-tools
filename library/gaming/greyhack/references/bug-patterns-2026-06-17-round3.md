# GreyScript Bug Patterns — 2026-06-17 Round 3

New patterns discovered during automated scan of files 41–50 (backup copies, but with unique files not previously scanned).

## NP-27: Unescaped Quotes in Generated Code (gsc/gsc.src:118)

**Severity:** HIGH — Generated code is syntactically broken if path contains `"`

```grey
# BEFORE (broken if str contains "):
return "import_code(\"" + str + "\")"

# AFTER (safe):
return "import_code(" + "\"\"\"" + str + "\"\"\"" + ")"
# Or better: use list-based code generation, not string concat
```

**MakeStr** in `gsc.src` does not escape double-quotes in the input path. If a path contains `"`, the generated code is syntactically invalid.

---

## NP-28: Off-by-One in Range-Based Loop (parseExploitReqs.src:33)

**Severity:** HIGH — Last element silently skipped

```grey
# BEFORE (skips last element):
for i in range(ExploitNames.len - 1)
    Exploits[ExploitNames[i]] = ExploitRequirements[i]
end for

# AFTER (correct):
for i in range(ExploitNames.len)
    Exploits[ExploitNames[i]] = ExploitRequirements[i]
end for
```

`range(N-1)` produces `[0, 1, ..., N-2]`, so the last element at index `N-1` is never processed.

---

## NP-29: Non-Existent List Method `applyFunction` (parseExploitReqs.src:30)

**Severity:** CRITICAL — Runtime crash

```grey
# BEFORE (method does not exist):
ExploitRequirements.applyFunction(@getCurrentRequirements)

# AFTER (use a loop):
results = []
for req in ExploitRequirements
    results.push(getCurrentRequirements(req))
end for
```

`applyFunction` is not a standard GreyScript List method. The script crashes at runtime.

---

## NP-30: Unvalidated Split Array Access (parseExploitReqs.src:5,20)

**Severity:** HIGH — Crash on malformed input

```grey
# BEFORE (crashes if "<b>" not found):
exploits[i].split("<b>")[1].split("</b>")[0]

# AFTER (safe):
parts = exploits[i].split("<b>")
if parts.len < 2 then continue  // or fail()
name = parts[1].split("</b>")[0]
```

No guard on the split result before accessing index `[1]`. If the expected tag is missing, the script crashes.

---

## NP-31: No Error Handling in Test Runner Loop (minitest/runner.src:29)

**Severity:** HIGH — One failing test kills the entire suite

```grey
# BEFORE (one crash stops everything):
for test in tests_table
    test["test_function"]()
end for

# AFTER (isolate failures):
for test in tests_table
    try
        test["test_function"]()
    catch err
        print("FAIL: " + test["class_name"] + "." + test["test_name"] + " — " + err)
        MiniManager.increment_stat("errors")
    end try
end for
```

GreyScript supports `try/catch`. Without it, a single test crash aborts the entire runner.

---

## NP-32: Null Crash on Build Result (minitest/manager.src:47-48)

**Severity:** HIGH — Crash when build returns null

```grey
# BEFORE (crashes if build returns null):
test_build = self.shell.build(test_src_path, home_dir+"/.tmp")
if test_build.len != 0 then

# AFTER (safe):
test_build = self.shell.build(test_src_path, home_dir+"/.tmp")
if test_build == null then
    print("Build returned null — check syntax")
    self.increment_stat("errors")
    return
end if
if test_build.len != 0 then
```

`shell.build()` can return null on failure. Calling `.len` on null crashes.

---

## NP-33: String Concatenation in Loop (password_generator.src:77)

**Severity:** MEDIUM — Performance degradation on large datasets

```grey
# BEFORE (O(n²) string copies):
out = out + char(10) + i["key"] + "=" + i["value"]

# AFTER (use list + join):
lines = []
for i in HASH_TABLE
    lines.push(i["key"] + "=" + i["value"])
end for
out = lines.join(char(10))
```

Repeated string concatenation in a loop creates O(n²) memory copies. Use a list and `join()` instead.

---

## NP-34: Print in Tight Loop (password_generator.src:78)

**Severity:** MEDIUM — I/O bottleneck

```grey
# BEFORE (print every iteration):
for i in HASH_TABLE
    print(count + " " + HASH_TABLE.len + " " + out.len)

# AFTER (print every N iterations):
if count % 100 == 0 then
    print(count + "/" + HASH_TABLE.len + " (" + out.len + " bytes)")
end if
```

Calling `print()` in every iteration of a large loop creates significant I/O overhead.

---

## NP-35: Unvalidated User Input to Sensitive API (metaxploit/metaxploit.src:139)

**Severity:** MEDIUM — Raw user input passed to overflow

```grey
# BEFORE (no validation):
unsecValue = user_input("  > ")
result = lib.overflow(targetAddr, unsecValue)

# AFTER (basic validation):
unsecValue = user_input("  > ")
if unsecValue == "" or unsecValue == null then
    fail("Kein Overflow-Wert angegeben")
end if
if unsecValue.len > 1024 then
    fail("Overflow-Wert zu lang")
end if
result = lib.overflow(targetAddr, unsecValue)
```

User input is passed directly to `lib.overflow()` without any validation of type, length, or format.

---

## NP-36: Ambiguous Boolean Precedence (password_generator.src:49)

**Severity:** LOW — Undefined behavior

```grey
# BEFORE (ambiguous — no operator precedence docs):
if a==b or "HRL'AEIOU".indexOf(b)==null and "AEIOUS".indexOf(a)==null and ["CH","MC"].indexOf(a+b)==null then

# AFTER (explicit parentheses):
if a==b or ("HRL'AEIOU".indexOf(b)==null and "AEIOUS".indexOf(a)==null and ["CH","MC"].indexOf(a+b)==null) then
```

GreyScript has no official operator precedence documentation. Mixing `or` and `and` without parentheses is error-prone.

---

## Summary Table

| ID | Pattern | Severity | Files |
|----|---------|----------|-------|
| NP-27 | Unescaped quotes in generated code | HIGH | gsc/gsc.src:118 |
| NP-28 | Off-by-One in range loop | HIGH | parseExploitReqs.src:33 |
| NP-29 | Non-existent `applyFunction` method | CRITICAL | parseExploitReqs.src:30 |
| NP-30 | Unvalidated split array access | HIGH | parseExploitReqs.src:5,20 |
| NP-31 | No error handling in test runner | HIGH | minitest/runner.src:29 |
| NP-32 | Null crash on build result | HIGH | minitest/manager.src:47-48 |
| NP-33 | String concatenation in loop | MEDIUM | password_generator.src:77 |
| NP-34 | Print in tight loop | MEDIUM | password_generator.src:78 |
| NP-35 | Unvalidated input to sensitive API | MEDIUM | metaxploit.src:139 |
| NP-36 | Ambiguous boolean precedence | LOW | password_generator.src:49 |
