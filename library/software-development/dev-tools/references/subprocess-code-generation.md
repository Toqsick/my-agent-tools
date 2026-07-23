# Subprocess Code Generation — Debugging Footguns

Generated Python code executed via `subprocess.run([python, '-c', code])` introduces
a class of bugs invisible in the generator and only surfacing at subprocess runtime.
This reference catalogs the patterns.

## Triple-Layer Quoting Problem

### Situation

```python
# Outer layer: f-string generating Python code for subprocess
code = f"""
import sys
sys.path.insert(0, '{HERMES_HOME}/scripts')   # Layer 1: outer var expansion
target = f'{{INBOX_PATH}}/{remote_name}'        # Layer 2: inner f-string via {{double-brace}}
data = Path('{tmp}').read_bytes()               # Layer 3: literal path from outer var
"""
proc = subprocess.run([python, '-c', code], capture_output=True, text=True)
```

### Layer mapping

| Syntax in generator     | At subprocess execution                                    | Risk                     |
|------------------------|------------------------------------------------------------|--------------------------|
| `'{HERMES_HOME}'`      | literal string, e.g. `'/home/bratan'`                     | Low (straight expansion) |
| `'{{INBOX_PATH}}'`     | `{INBOX_PATH}` — valid Python f-string template            | Medium (easy to miss `{{`) |
| `'{tmp}'`              | literal path, e.g. `'/tmp/nc-file.pdf'`                   | Low                      |
| `Path('{tmp}')`        | `Path('/tmp/nc-file.pdf')`                                | **ZERO if Path not imported** |

## The Classic Trap: Missing Imports in Subprocess Scope

```python
# Generator code — looks correct:
code = f"""
data = Path('{tmp}').read_bytes()       # NO import of Path here!
ok = client.upload(target, data)
"""
proc = subprocess.run([python, '-c', code], ...)
# → NameError: name 'Path' is not defined
```

The subprocess is a **fresh Python interpreter**. It inherits nothing from the
generator — no imports, no variables, no scope. Every import must be repeated
inside the code string.

**Fix:** Always include `from pathlib import Path` (and all other needed imports)
inside the generated code string, not just in the generator.

## The Temp-File Pattern (Workaround for ARG_MAX)

When payloads exceed ~130 KB (base64 expansion of ~100 KB binary), inline base64
hits the kernel's `ARG_MAX` limit (typically 2 MB). Symptom: cryptic
`Argument list too long` from `subprocess.run`.

**Pattern:**

```python
# 1. Write to temp file
tmp = Path("/tmp") / f"payload-{timestamp}-{name}"
tmp.write_bytes(content)

# 2. Generate code that reads from path
code = f"""
from pathlib import Path                    # ← MUST be inside subprocess scope
data = Path('{tmp}').read_bytes()
# ... rest of code ...
"""

# 3. Run subprocess
proc = subprocess.run([python, '-c', code], ...)

# 4. Clean up — try/except, not missing_ok
try:
    tmp.unlink()
except OSError:
    pass
```

**Don't** use `tmp.unlink(missing_ok=True)` if host Python might be < 3.8
(in practice, Ubuntu 24.04 Python 3.11+ supports it, but safe is safe).

## Generated-Code STDERR Swallowing

When subprocess-generated code fails with a Python error, the error goes to
`stderr`. If you only inspect `proc.stdout`, you'll see nothing and conclude
the code ran but produced no output.

**Diagnostic:**

```python
# ALWAYS capture and print stderr on failure
proc = subprocess.run([python, '-c', code], capture_output=True, text=True)
if proc.returncode != 0:
    print("STDERR:", proc.stderr, flush=True)   # ← where the real error is
    print("STDOUT:", proc.stdout, flush=True)
```

## Checkpoints for Debugging

When generated subprocess code **silently fails** (no error raised, but file
not created / upload not visible / wrong output):

| Check | How | Symptom it catches |
|---|---|---|
| Is generated code syntactically valid? | `print(code)` before subprocess call | Unbalanced braces, missing quotes |
| Are ALL imports present? | Scan code string for every identifier used | `NameError` only at runtime |
| Is `Path` declared inside the string? | grep for `Path(` in code string | Most common missing import |
| Is payload too large for inline? | `len(b64encode(data))` > 1.5 MB | `Argument list too long` |
| Does temp file still exist? | Check before subprocess | Race with cleanup |

## Anti-Pattern: The Stale Fast-Fix

When generated subprocess produces no output, instinct is to add more logging.
**Don't.** First print and inspect the actual generated code string. The bug
is almost always in the **code generation** itself, not in the execution logic.

```python
# Debug step 1: dump the generated code
import sys
print("=== GENERATED CODE ===", file=sys.stderr)
print(code)
print("=== END CODE ===", file=sys.stderr)

# Now run — error will be obvious
```

## Real Session: E2E Nextcloud Processor (2026-07-09)

- **Symptom:** E2E test reported `[FAIL] WebDAV PUT .pdf` — upload not visible
- **Root cause:** The test harness generated subprocess code with `Path('/tmp/...').read_bytes()` but `Path` was imported only in the generator, not in the generated code string
- **Fix:** Added `from pathlib import Path` at the top of the generated code block (inside the f-string, as a literal statement)
- **Verification:** After fix, all 20 E2E tests passed, including the same upload path

## See also

- `dev-tools` SKILL.md — developer debugging workflow
- `python-stdlib-pitfalls` — other Python footgun patterns
- `systematic-debugging` — 4-phase root cause process