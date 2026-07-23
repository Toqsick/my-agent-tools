# GreyHack Build Pipeline — Session 2026-06-17

## GreyHack Terminal vs CodeEditor — CRITICAL

The GreyHack terminal is Bash-like, NOT a GreyScript interpreter. You CANNOT type GreyScript commands in the terminal.

**WRONG:** `pc = get_shell.host_computer` → "command not found"

**CORRECT — CodeEditor (preferred):**
1. Computer → CodeEditor → New
2. Paste code → Save as `/home/Bratan/bin/<tool>.src`
3. Build button → Save binary as `<tool>`

**CORRECT — Terminal + pc.wget:**
```
pc = get_shell.host_computer
pc.wget("http://<HOST_IP>:8765/lib_core/lib_core.src", "/home/Bratan/bin/lib_core.src")
shell.build("/home/Bratan/bin/lib_core.src", "/home/Bratan/bin/lib_core")
```

## greybel-js Import Path Bug

Resolves relative paths to `/root/` instead of actual location.

**Workaround:** Copy + sed:
```bash
cp portscan/portscan.src bin/portscan.src
sed -i 's|import_code("../lib_core/lib_core.src")|import_code("lib_core")|g' bin/portscan.src
```

Or: `~/bin/greyhack-deploy`

## Regex Double-Paren Trap

```python
# WRONG: creates import_code("lib_core"))
re.sub(r'import_code\("..."\)', 'import_code("..."))', content)

# CORRECT:
re.sub(r'import_code\("[^"]*"\)', 'import_code("lib_core")', content)
```

## greybel-js Incompatibilities

| Issue | Fix |
|-------|-----|
| Backslash-escaped quotes | Use single quotes |
| In-Game-only APIs | Comment out |
| Code generators (installer.src) | Cannot build with greybel-js |
| Double parens `))` | Remove extra `)` |
| Import paths | Copy + sed |
| **Single-line `if/then/action/end if`** | **Convert to multi-line:** `if X then\n  action\nend if` |
| **Ternary `("a" if cond else "b")`** | **Convert to if/else block** |
| **`end function` used where `end if` belongs** | Replace with `end if`; add `end function` after |
| **Orphaned code fragments** (incomplete functions without end) | Remove or complete the fragment |

### Single-line if/then/end if → Multi-line Conversion

greybel-js rejects `if X then Y end if` on one line. Must be:
```
if X then
  Y
end if
```

Batch fix with Python:
```python
import re
lines = content.split('\n')
result = []
for line in lines:
    stripped = line.strip()
    match = re.match(r'^(\s*)if\s+(.+?)\s+then\s+(.+?)\s+end\s+if\s*$', stripped)
    if match:
        indent, condition, action = match.groups()
        result.extend([
            f"{indent}if {condition} then",
            f"{indent}\t{action}",
            f"{indent}end if"
        ])
    else:
        result.append(line)
```

### Ternary Expression Fix

GreyScript has no ternary operator. Convert:
```greyscript
# WRONG (greybel-js rejects):
prefix = (" d " if e.is_dir else " f ")

# CORRECT:
if e.is_dir then
    prefix = " d "
else
    prefix = " f "
end if
```

### Structural Repair Pattern: end function as end if

When `end function` appears where `end if` should be:

1. Parse the file tracking block stack (if/for/while/function)
2. Identify unclosed blocks
3. Insert missing `end if` before `end function` that closes a function containing unclosed if-blocks
4. Verify: every multi-line `if/then` has matching `end if`, every `function` has matching `end function`

### Orphaned Fragment Removal

Incomplete functions from failed merges appear as:
```
// Comment describing the function
funcName = function(params)
  // partial body
// Next function or header starts here (no end function!)
```

Fix: either complete the function properly or remove the entire fragment.

## Build Success (2026-06-17)

OK: lib_core, portscan, metaxploit, decypher, routerinfo, wifi_crack, forcer, scp_upload, ps, smtp_enum, grsa
FAIL: xmem (44 functions, 22 end function)

## Build Success (2026-06-17, post-fix)

OK: lib_core, portscan, metaxploit, decypher, routerinfo, wifi_crack, forcer, scp_upload, ps, smtp_enum, grsa, xmem, filecore
FAIL: none (13/13)

## Community Libraries

~/greyhack-tools/includes/: json.src, networking.src, tqdm.src (from salmon85)

## Repos Analyzed

- salmon85/Grey_hack_scripts — useful libraries
- psimonson/greyhack-scripts — v0.8 structure
- ftzi/grey-hack — best practices (SOLID, list.sort() bug)
