# GreyScript Bug Patterns — 2026-06-17 Round 2

New patterns discovered during xmem.src and filecore.src repair session.

## NP-22: Single-Line `if/then/end if` (greybel-js Incompatibility)

**Severity:** HIGH — Causes greybel-js build failures
**Detected by:** `grep -rn 'if.*then.*end if' --include="*.src"`
**Fix:** Convert to multi-line:
```greyscript
# BEFORE (greybel-js cannot parse):
if path == null or path == "" then return "/" end if

# AFTER (correct GreyScript + greybel-js compatible):
if path == null or path == "" then
    return "/"
end if
```
**Note:** Vanilla GreyScript in the game engine DOES accept single-line `if/then/end if`, but greybel-js does not. Always use multi-line for portability.
**Findings in filecore.src:** 17 occurrences, all fixed.

## NP-23: Ternary/Conditional Expression Syntax

**Severity:** HIGH — Not valid GreyScript, causes parse errors
**Fix:** Convert to if/else block:
```greyscript
# BEFORE (invalid):
prefix = (" d " if e.is_dir else " f ")

# AFTER (correct):
if e.is_dir then
    prefix = " d "
else
    prefix = " f "
end if
```
**Findings:** 1 occurrence in filecore.src:637

## NP-24: Unclosed If-Blocks (Structural)

**Severity:** CRITICAL — File cannot be built or parsed
**Detection:** Stack-based parser required (simple count is insufficient). See `references/greyscript-audit.md` Control-Flow Balance Checking section.
**Common pattern:** `else` branch followed directly by `end function` without closing the `if` block first.
**Findings in xmem.src:** 3 occurrences:
- ShellConnect: `if shell == null then` ... `else` ... `end function` (missing `end if`)
- MagicGame: nested if/else with 2 missing `end if`

## NP-25: Bare `exit` Without Parentheses

**Severity:** LOW — Works in some GreyScript versions but inconsistent
**Fix:** Always use `exit()` or `exit("message")`
**Findings in xmem.src:** 8 occurrences

## NP-26: `option.val` vs String Comparison Mismatch

**Severity:** MEDIUM — Silent logic error in greybel-js
**Context:** `user_input()` returns a string in Vanilla GreyScript but greybel-js adds `.val` property for numeric conversion. Code that mixes `option.val == 0` (numeric) with `option == "1"` (string) has silent failures.
**Fix:** Consistently use either `int(option)` for numeric comparison or `option == "N"` for string comparison, never mix both.
**Findings in xmem.src:** 21x `option.val` mixed with 17x `option == "N"` string comparisons.
