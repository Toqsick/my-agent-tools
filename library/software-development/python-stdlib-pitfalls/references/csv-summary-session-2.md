# csv-summary Session 2 — BOM leak & duplicate header bugs

## Date

2026-07-07 (Tuesday), fix-loop run on Verifier re-audit

## Project

`csv_summary` Python CLI tool (stdlib only) in `/tmp/hermes-team-test/csv_summary/`.

## Bug #9: UTF-8 BOM leaks into first column header

### Test

```python
def test_bom_does_not_leak_into_column_names(tmp_path):
    import json as _json
    p = tmp_path / "bom.csv"
    # Write raw bytes — text-mode open() on many platforms strips BOM.
    p.write_bytes(b"\xef\xbb\xbfa,b\n1,2\n4,5\n")
    result = run_cli(str(p), "--json")
    assert result.returncode == 0
    payload = _json.loads(result.stdout)
    keys = list(payload["columns"].keys())
    assert keys == ["a", "b"]  # must NOT be ["\ufeffa", "b"]
```

### Failing output (before fix)

With `encoding='utf-8'`, the JSON output had:
```json
{"a": 1.0, "b": 2.0, ...}
```
BUT the first key was `"\ufeffa"` — invisible in terminal but wrong in any programmatic consumer that compares against expected column names.

### Root cause

`open(path, encoding='utf-8')` does NOT strip the leading UTF-8 BOM (`0xEF 0xBB 0xBF`). The BOM ends up at position 0 of the first fieldname string. From Python docs: *"On encoding the 'utf-8-sig' codec will write 0xEF, 0xBB, 0xBF as the first three bytes to the file. On reading utf-8-sig will skip those bytes if they appear as the first three bytes in the file."*

### Fix

`encoding='utf-8'` → `encoding='utf-8-sig'` (one character added to the open() call).

### Lesson

**Always prefer `encoding='utf-8-sig'` over `'utf-8'` for CSV reading when you don't control the file source.** The `-sig` suffix is a superset — it strips any leading BOM if present and behaves identically to `utf-8` if absent. There is no circumstance where `utf-8` is safer than `utf-8-sig` for reading CSV files.

---

## Bug #10: Duplicate header names silently overwrite earlier columns

### Test

```python
def test_duplicate_header_names_returns_exit_3(tmp_path):
    p = tmp_path / "dup.csv"
    p.write_text("a,b,a\n1,2,3\n4,5,6\n")
    result = run_cli(str(p))
    assert result.returncode == 3
    assert "duplicate" in result.stderr.lower()
    assert "'a'" in result.stderr          # must name the colliding column
    assert "Traceback" not in result.stderr  # no traceback leak
```

### Failing output (before fix)

```
Columns: 3
  a (numeric):  mean = 4.50               ← should be 2.50!
  b (numeric):  mean = 3.50
```

The tool announced "Columns: 3" but silently dropped the first `a` column (values 1, 4) — only the second `a` column (values 3, 6) was kept.

### Root cause

`csv.DictReader` uses `dict(zip(fieldnames, row))`. Python's `dict()` silently overwrites keys on duplicates — no error, no warning, no exception. The first column's data disappears completely.

### Fix

Add a duplicate-detection block right after reading `reader.fieldnames`:

```python
seen = {}
for pos, name in enumerate(reader.fieldnames, start=1):
    if name in seen:
        raise InvalidCSVError(
            path,
            ValueError(
                f"duplicate header column {name!r} at positions {seen[name]}, {pos}"
            ),
        )
    seen[name] = pos
```

Position reporting (1-based) is critical — "duplicate column 'a' at positions 1, 3" tells the user exactly where the source file is broken.

### Verified output (after fix)

```
error: invalid CSV: duplicate header column 'a' at positions 1, 3
---exit: 3---
```

### Design decision

**Do NOT auto-rename** (e.g. `a → a_2`). Auto-renaming silently mutates the schema and masks provenance issues. The tool's job is to report the structural problem and let the user fix the source data.

---

## Test verdict

```
17 passed in 1.46s
```

Both new regression tests pass alongside all 15 existing tests.
