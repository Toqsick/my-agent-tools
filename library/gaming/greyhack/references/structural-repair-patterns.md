# GreyScript Structural Repair Patterns

Common structural bugs found in community GreyScript tools and how to fix them.

## 1. Missing `end if` in Multi-line If Blocks

**Pattern**: `if X then` ... `else` ... `end function` (missing `end if` before `end function`)

**Detection**: Track block stack (if/for/while/function). If `end function` closes a function that has unclosed `if` blocks on the stack.

**Fix**: Insert `end if` for each unclosed `if` before `end function`.

**Example from xmem.src ShellConnect**:
```greyscript
# BEFORE (broken):
else
    // some comment
end function

# AFTER (fixed):
else
    // some comment
end if
end function
```

## 2. Nested If/Else Missing Multiple `end if`

**Pattern**: Outer `if` → `else` → inner `if` → `else` → `end function` (missing 2x `end if`)

**Fix**: Add one `end if` per unclosed `if` level.

**Example from xmem.src MagicGame**:
```greyscript
# BEFORE (broken):
if result == null or typeof(result) == "string" then
    ...
else
    if typeof(result) == "computer" then
        ...
    else
        ...
end function

# AFTER (fixed):
if result == null or typeof(result) == "string" then
    ...
else
    if typeof(result) == "computer" then
        ...
    else
        ...
    end if
end if
end function
```

## 3. Orphaned Code Fragments from Failed Merges

**Pattern**: A function starts but is never completed. The body is partial and there's no `end function`. Later, a new header or function starts.

**Example from filecore.src**:
```greyscript
# Orphaned fragment (L29-38):
// Schreibt Inhalt in eine Datei — gibt true zurueck oder bricht ab
safeWriteFile = function(pc, path, content)
    f = pc.File(path)
    if f == null then
        fail("Datei nicht gefunden zum Schreiben: " + path)
    end if
    result = f.set_content(content)
    if result != null then
        fail("Schreiben fehlgeschlaged (" + path + "): " + result)
// Next valid code starts here (no end if, no end function)

// ============================================================
// filecore.src – Erweiterter Datei-Helfer für Grey Hack
```

**Fix**: Remove the entire orphaned fragment (from the comment before the function to where the next valid code starts). If the function is needed, rewrite it completely.

## 4. Merge Conflict Markers

**Pattern**: `=======` or `<<<<<<< HEAD` or `>>>>>>> branch` in source files.

**Fix**: Remove the marker, keep the correct version. Usually the code after `=======` is the intended version.

**Example from filecore.src**:
```greyscript
# BEFORE:
    return f.is_folder
end function
=======
// ── Verzeichnis anlegen ──────────────────────────────────────

# AFTER:
    return f.is_folder
end function

// ── Verzeichnis anlegen ──────────────────────────────────────
```

## 5. `is_folder` → `is_binary` Conversion

**Pattern**: `f.is_folder` used to check if something is a directory.

**Fix**: Replace with `not f.is_binary` (for "is directory?") or `f.is_binary` (for "is file?").

**Always null-check first**:
```greyscript
f = pc.File(path)
if not f then fail("Not found: " + path)
if f.is_binary then fail("Not a directory: " + path)
// Now safe to use as directory
```

## 6. Bare `exit` Without Parentheses

**Pattern**: Bare `exit` instead of `exit()` or `exit("message")`.

**Fix**: Add parentheses. `exit()` for silent exit, `exit("message")` with error text.

**Note**: greybel-js requires `exit()`. Vanilla GreyScript accepts bare `exit`.

## 7. `get_shell.host_computer` Repeated Calls

**Pattern**: Calling `get_shell.host_computer` multiple times in a function.

**Fix**: Cache once at function start:
```greyscript
shell = get_shell
pc = shell.host_computer
// Use pc.File(...), pc.get_files(), etc.
```

## 8. `main` Text Instead of `end if`

**Pattern**: The text ` main` or `end if` replaced with something else (likely a corrupted edit).

**Search**: Look for standalone ` main` text that should be `end if`.

## Structural Validation Script

Use this Python snippet to validate a .src file's block structure:

```python
import re

with open('file.src', 'r') as f:
    lines = f.readlines()

class Block:
    def __init__(self, btype, line_num, indent):
        self.btype = btype
        self.line_num = line_num
        self.indent = indent

stack = []
issues = []

for i, line in enumerate(lines, 1):
    stripped = line.strip()
    indent = len(line) - len(line.lstrip())
    
    if stripped.startswith('//') or not stripped:
        continue
    
    # Single-line if/then (no end if needed)
    if re.match(r'if\s+.+\s+then\s+\S', stripped) and not stripped.endswith('then'):
        continue
    
    if re.match(r'if\s+.+\s+then\s*$', stripped):
        stack.append(Block('if', i, indent))
        continue
    
    if re.match(r'for\s+.+\s+in\s+', stripped):
        stack.append(Block('for', i, indent))
        continue
    
    if re.match(r'while\s+', stripped):
        stack.append(Block('while', i, indent))
        continue
    
    if re.match(r'[A-Z]\w*\s*=\s*function\s*\(', stripped):
        stack.append(Block('function', i, indent))
        continue
    
    if stripped == 'else':
        continue
    
    for closer in ['end if', 'end for', 'end while', 'end function']:
        if stripped == closer:
            match_type = closer.split()[1]  # if, for, while, function
            found = False
            for j in range(len(stack)-1, -1, -1):
                if stack[j].btype == match_type:
                    stack.pop(j)
                    found = True
                    break
            if not found:
                issues.append(f"L{i}: ORPHANED '{closer}'")
            break

for block in stack:
    issues.append(f"L{block.line_num}: UNCLOSED {block.btype}")

for issue in issues:
    print(issue)
```
