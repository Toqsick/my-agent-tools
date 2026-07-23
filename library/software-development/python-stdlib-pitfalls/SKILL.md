---
name: python-stdlib-pitfalls
description: "Use when user is building Python data-processing or CLI code with standard-library modules and needs to check surprising defaults, silent data corruption, parsing edge cases, or safe fixes. NOT for third-party library documentation or a general Python beginner tutorial. Catalogs reproducible footguns in csv, statistics, argparse, pathlib, JSON, and related stdlib components."
version: 1.1.0
author: Yuno
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - python
    - stdlib
    - pitfalls
    - footguns
    - csv
    - data-processing
    category: software-development
lane: worker-heavy
reasoning_effort: medium
trigger_keywords: ['python', 'data', 'library', 'user', 'building']
keywords: ['python', 'data', 'library', 'user', 'building']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---


# Python Stdlib Pitfalls

Python's standard library is famously "batteries included" — but some batteries have known design quirks that produce **silently wrong results** rather than raising errors. This skill catalogs the most important ones for AI agents building Python CLI tools and data pipelines.

## How to use

When building Python code that uses stdlib modules for data processing, **check this list for the module you're using**. Each entry covers:
- The **pitfall** (what goes wrong by default)
- The **fix** (how to make it safe)
- A code snippet showing both

If you hit a surprising behavior not listed here, **add it** with a reproduction case so future sessions don't waste time on the same bug.

---

## 1. `csv.DictReader` — silently produces garbage on malformed input

### Pitfall

`csv.DictReader` (and `csv.reader`) default to **lenient mode**. On structurally broken CSV — like an unterminated quoted field — the parser does NOT raise. Instead, it silently concatenates everything from the broken quote to the end of the file (or the next matching quote) into a single field value.

```python
# data.csv contains:  id,name\n1,"unterminated\n2,bob\n
import csv
with open('data.csv') as f:
    rows = list(csv.DictReader(f))
# rows = [{'id': '1', 'name': 'unterminated\n2,bob'}]
# ↑ rows[0]['name'] is the rest of the file. No error. No warning.
```

This means the tool reports **wrong row count**, **wrong values**, **wrong column stats** — and exits 0 because nothing technically "failed."

### Fix

Pass `strict=True` to the constructor. This makes the parser raise `csv.Error` on:
- Unterminated quotes
- Structural malformations that the lenient parser would silently absorb

```python
import csv
with open('data.csv', newline='') as f:
    reader = csv.DictReader(f, strict=True)
    try:
        rows = list(reader)
    except csv.Error as e:
        # Exit 3: CSV is structurally invalid
        sys.exit(f"error: invalid CSV — {e}")
```

### Second layer — ragged rows (even `strict=True` doesn't catch this)

`strict=True` does NOT catch rows with a **different number of fields** than the header. A row like `1,Alice,extra_field` produces a `dict` with a `None` key for the extra field (or a silently dropped field), not an error.

```python
# Add a post-parse check for ragged rows:
field_count = len(rows[0])
ragged = [i for i, r in enumerate(rows, start=2) if len(r) != field_count]
if ragged:
    raise InvalidCSVError(
        path,
        ValueError(
            f"row(s) {ragged[:5]}{'…' if len(ragged) > 5 else ''} "
            f"have a different number of fields than the header"
        ),
    )
```

### Third layer — UTF-8 BOM leaks into the first column header

Python's `open()` with `encoding='utf-8'` (the default when `utf-8` is specified) does **not** strip a leading UTF-8 BOM (`0xEF 0xBB 0xBF`). The BOM lands at the start of the first fieldname string — meaning the first column header becomes `"\ufeffa"` instead of `"a"`.

```python
# data.csv starts with:  \xef\xbb\xbfa,b\n1,2\n4,5
import csv
with open('data.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f, strict=True)
    fieldnames = reader.fieldnames
# fieldnames = ['\ufeffa', 'b']   ← BOM glued to 'a'!
# The tool reports "Columns: a, b" with \ufeff hidden in the key.
```

This is insidious because the BOM is invisible in terminal output — the tool looks correct but any code that compares column names will silently fail.

### Fix

Use `encoding='utf-8-sig'` (the `-sig` suffix stands for "signature" and tells Python to strip the BOM if present, without erroring on BOM-less files):

```python
with open('data.csv', newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, strict=True)
```

**Why `utf-8-sig` is safe:** If the file has no BOM, `utf-8-sig` behaves exactly like `utf-8`. If it has a BOM, the BOM is stripped. It's a superset — always prefer it over `utf-8` for real-world CSV data where you don't control the file source.

### Fourth layer — duplicate header names (silent data loss)

`csv.DictReader` builds its dict using `dict(zip(fieldnames, row))`. If the header has duplicate column names — e.g. `a,b,a` — the later column **silently overwrites** the earlier one. No error, no warning. The tool reports "Columns: 3" but the first `a` column's data is gone.

```python
# data.csv contains:  a,b,a\n1,2,3\n4,5,6
import csv
with open('data.csv', newline='') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
# rows = [{'a': '3', 'b': '2'}]   ← '3' from third column overwrites '1' from first!
# Row says "Columns: 3" but DictReader only has 2 keys.
```

### Fix — validate header before dict construction

Check for duplicates in `fieldnames` (the header read by DictReader's first pass). When found, report which names collide and at which 1-based positions, then exit with an error:

```python
seen = {}
for pos, name in enumerate(reader.fieldnames, start=1):
    if name in seen:
        print(
            f"error: invalid CSV: duplicate header column {name!r} "
            f"at positions {seen[name]}, {pos}",
            file=sys.stderr,
        )
        sys.exit(3)
    seen[name] = pos
```

**Key design choice:** Report which columns are duplicated AND at which 1-based positions. "Duplicate column 'a' at positions 1, 3" is actionable — "duplicate column found" is not. Do NOT auto-rename to disambiguate — that silently mutates data and masks provenance issues.

### Full pattern (BOM + strict + ragged + duplicate check)

```python
import csv
import sys

try:
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, strict=True)
        rows = list(reader)
except FileNotFoundError:
    sys.exit(f"error: file not found: {path}")            # exit 2
except csv.Error as e:
    sys.exit(f"error: invalid CSV — {e}")                  # exit 3

if not rows:
    sys.exit("error: file is empty")                       # exit 1

# Duplicate-header check (before parsing data rows)
seen = {}
for pos, name in enumerate(reader.fieldnames, start=1):
    if name in seen:
        sys.exit(
            f"error: invalid CSV: duplicate header column {name!r} "
            f"at positions {seen[name]}, {pos}"
        )                                                  # exit 3
    seen[name] = pos

# Ragged-row check
field_count = len(rows[0])
ragged = [i for i, r in enumerate(rows, start=2) if len(r) != field_count]
if ragged:
    sys.exit(
        f"error: invalid CSV — row(s) {ragged[:5]}{'…' if len(ragged) > 5 else ''} "
        f"have a different number of fields than the header"
    )                                                      # exit 3
```

**Exit code convention:** 1 = empty, 2 = missing file, 3 = malformed content.

---

## 2. `statistics.stdev` vs `pstdev` — sample vs population

### Pitfall

`statistics.stdev()` computes **sample** standard deviation (n−1 denominator, Bessel's correction). If you actually want the **population** standard deviation (divide by n) — e.g. you have the entire dataset, not a sample — `stdev` gives a slightly higher value.

```python
import statistics
data = [1, 2, 3, 4, 5]
statistics.stdev(data)   # 1.5811  (sample, n−1)
statistics.pstdev(data)  # 1.4142  (population, ÷n)
```

### Fix

Be explicit about intent in the code comment:
```python
# Sample std dev (n−1) — use when data is a sample of a larger population
stats['std'] = round(statistics.stdev(nums), 2) if len(nums) > 1 else 0.0
#              ↑ fallback for single-element: stdev([x]) raises StatisticsError
```

For a CLI that produces summary stats on a complete file, population std dev is often more appropriate (`pstdev`).

---

## 3. `argparse` — `type=open` and `type=Path` footguns

### Pitfall

`argparse` accepts **callables** as the `type` argument for argument conversion. Passing `argparse.FileType('r')` opens the file immediately at parse time — but it also **leaves the file descriptor open** until the namespace is garbage-collected.

```python
parser.add_argument('file', type=argparse.FileType('r'))
args = parser.parse_args()
data = args.file.read()   # works, but fd stays open
# args.file.close()       # easy to forget
```

Worse: `pathlib.Path` as `type` doesn't convert to `Path` objects — it actually runs `Path(arg)` which returns a `Path`, but `argparse`'s `type=` runs the callable on the string, so `type=Path` does incidentally work. But it's a gotcha for `type=open` which is really `argparse.FileType` internally.

### Safer pattern

```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('file')
args = parser.parse_args()

# Open manually — explicit, no leaked fds
with open(args.file) as f:
    data = f.read()
```

---

## 4. `json` module — silent non-ASCII escaping

### Pitfall

`json.dumps()` with default settings escapes non-ASCII characters to `\uXXXX` sequences. This produces ASCII-safe but **less human-readable** output.

```python
import json
data = {"name": "München"}
print(json.dumps(data))   # {"name": "M\\u00fcnchen"}
```

### Fix

```python
json.dumps(data, ensure_ascii=False)   # {"name": "München"}
```

Gilt besonders für CSV-Summary-Tools, die deutsche Umlaute in Spaltenwerten haben.

---

## 5. `datetime` — tzinfo-naive comparison pitfall

### Pitfall

Naive `datetime` objects (without `tzinfo`) and timezone-aware `datetime` objects **cannot be compared** — Python raises `TypeError: can't compare offset-naive and offset-aware datetimes`.

### Fix

Always work in UTC internally:
```python
from datetime import datetime, timezone

now = datetime.now(timezone.utc)      # aware
naive = datetime.utcnow()             # naive — avoid
```

For CSV columns containing ISO timestamps, always parse with `fromisoformat()` and check for timezone info before any comparison.

---

## What to add here

If you find another stdlib module that silently produces wrong output under its default configuration, add it here with:
1. Short name + pitfall
2. Example of wrong behavior
3. The fix
4. Reference to the session where it was discovered

## 6. `bytes`-Literals — only ASCII, no Unicode (NEW 2026-07-10)

### Pitfall

Python's `bytes` literals (`b"..."`, `b'...'`) **only accept ASCII characters**. Any non-ASCII character — em-dash `—`, German umlauts `ä ö ü`, smart quotes `“ ”`, emoji — causes `SyntaxError: bytes can only contain ASCII literal characters` at parse time.

This is a sneaky failure mode because the file often *looks* fine in the editor (UTF-8 encoded source), but Python's bytes-literal parser rejects the non-ASCII character before any code runs. The error message points to the offending byte but doesn't say "use a different quote style".

```python
# This is a SyntaxError, even though the file is UTF-8:
em = b"hello — world"
#   SyntaxError: bytes can only contain ASCII literal characters

# Common cases that bite:
error_msg = b"404 — not found"                    # em-dash
user_msg  = b"Grüße aus München"                 # German umlauts
log_line  = b"user said “hello”"                  # smart quotes
banner    = b"Yuno 🐰 ready"                      # emoji
```

### Fix

Three options, in order of preference:

**(a) Use a regular string instead of bytes** — for things like HTTP response bodies, log lines, error messages, this is almost always fine:
```python
error_msg = "404 — not found"          # str, not bytes — no encoding needed
# Or if you really need bytes: error_msg.encode("utf-8")
```

**(b) Use `\xNN` escape sequences** — preserves the byte-exactness:
```python
error_msg = b"404 \xe2\x80\x94 not found"   # em-dash as UTF-8 bytes
```

**(c) Hardcode the bytes via `bytes([...])`** — clunky but works:
```python
error_msg = bytes([0x34, 0x30, 0x34, 0x20, 0xe2, 0x80, 0x94, 0x20])  # "404 — "
```

### Symptom-recognition

The error message says "bytes can only contain ASCII literal characters" — that's the giveaway. Search for the offending character with the column number from the traceback.

### Why this hits the agent workflow specifically

Agents writing user-facing response bodies (HTTP servers, log lines, error responses) often **copy-paste em-dashes, smart quotes, or umlauts** from thinking-text or documentation examples. The first `python -c` / `python script.py` invocation fails before any logic runs. **Fix-Forward-Pattern:** when writing a server that returns user-facing bytes, default to `str` for response bodies and `.encode("utf-8")` only at the wire boundary.

## Session references

- `references/csv-summary-session.md` — reproduction of the csv.DictReader lenient-parse bug in the csv_summary CLI tool, including the failing pytest output and the two-layer fix applied.
- `references/csv-summary-session-2.md` — reproduction of BOM-leak and duplicate-header-name bugs from the second fix-loop run (July 2026). Covers `encoding='utf-8-sig'`, the `seen` dict pattern, and `p.write_bytes()` for BOM-guaranteed test fixtures.
