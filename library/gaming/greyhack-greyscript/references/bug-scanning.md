# Systematic Bug-Scanning for Non-Compiling Sources

When a user reports "Compiler Error at line N" in a large source (50+ KB, 60+ commands), systematically scan for these three bug types in order — they account for ~95% of yuno_v5/v6-class build failures:

## 1. String-in-String (dynamic code generation)

Search pattern: `"text1"text2"` where two `"` appear inside a `"..."` string with no `+` operator between them.
Fix: replace inner quotes with `char(34)` concatenation.

```python
# Python regex to find candidate lines:
import re
issues = []
for i, line in enumerate(lines, 1):
    m = re.search(r'"[^"]*"[a-zA-Z_][^"]*"', line)  # two " without + between
    if m and 'char(34)' not in line:
        issues.append((i, line))
```

See "Dynamic Code Generation" section above for the full `char(34)` translation table.

## 2. Trailing Comma Bugs in Map Literals

Two variants:

- **Missing comma before `}`** — last entry in `{}` has no `,`. Error points at the `}` line, not the missing-comma line. Search: find lines ending with `"value"` or `value` immediately before a `}`.
- **Stray comma after assignment** — `x = y,` at end of line inside a function (NOT inside a `{}` literal). This happens when a line like `main_session[lib + "Ver"] = "loaded",` accidentally gets a trailing comma. Search: `^\s*\w+(\[[^\]]+\])?\s*=\s*[^,]+,\s*$` and verify the line is NOT inside a `{}` literal.

## 3. Comments Inside `{}` Object Literals

GreyScript rejects `//` comments between `{` and `}` in a map literal. Search: find `//` inside an open `{...}` block. Fix: move the comment outside the literal.

```python
# Detect comments in object literals
brace_depth = 0
in_obj = False
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if not in_obj and '{' in line and '}' not in line.split('{')[1:]:
        in_obj = True
    if in_obj:
        brace_depth += line.count('{') - line.count('}')
        if brace_depth <= 0: in_obj = False
        elif stripped.startswith('//') and ':' not in stripped:
            issues.append(f"L{i}: comment in object")
```

## Why this order

String-in-String errors crash the compiler immediately (reported error may be far from actual cause). Trailing commas are the most common in large map literals (themes, configs). Comments-in-objects are rare but catastrophic (silent failure on the whole literal block).

## Real-world benchmark

yuno_v5.src (66KB, 64 commands) had 10+ trailing comma bugs, 5 string-in-string bugs, and 1 comment-in-object bug. All found and fixed in <5 minutes with this systematic approach.