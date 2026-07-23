# csv-summary Session — `csv.DictReader` lenient-parse bug

## Datum

2026-07-07 (tuesday)

## Projekt

`csv_summary` Python CLI tool (stdlib only). Build in `/tmp/hermes-team-test/csv_summary/`.

## Bug: csv.DictReader unterminated quote → silent data corruption

### Test

```python
def test_invalid_csv_exit_code_3(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text(textwrap.dedent("""\
        id,name
        1,"unterminated
        2,bob
        """))
    result = run_cli(str(bad))
    assert result.returncode == 3
```

### Failing output (before fix)

```
>       assert result.returncode == 3, f"expected exit 3, got {result.returncode}\nstderr: {result.stderr}"
E       AssertionError: expected exit 3, got 0
```

The test expected exit code 3 (invalid CSV), but got 0 (success). The CSV parsed without error — but produced **wrong data**: `rows[0]['name']` contained `"unterminated\n2,bob"` — the unterminated quote caused the parser to treat the rest of the file as one field.

### Root cause

`csv.DictReader` (and `csv.reader`) default to **lenient mode**. From the Python docs: *"If strict is True, the reader raises an exception on bad CSV input. If False (default), the reader may return garbage."*

### Fix (two layers)

1. **`strict=True`** — causes `csv.DictReader` to raise `csv.Error` on unterminated quotes:
   ```python
   reader = csv.DictReader(raw.splitlines(), strict=True)
   ```

2. **Post-parse ragged-row check** — catches rows with mismatched column count (which `strict=True` does NOT catch):
   ```python
   field_count = len(rows[0])
   ragged = [i for i, r in enumerate(rows, start=2) if len(r) != field_count]
   if ragged:
       raise InvalidCSVError(
           path,
           ValueError(f"row(s) {ragged[:5]}… have a different number of fields than the header"),
       )
   ```

### Verified fix

```
tests/test_csv_summary.py::test_invalid_csv_exit_code_3 PASSED
9 passed in 1.00s
```

All 9 tests pass with the fix.

## Exit code convention used

| Exit code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | Empty file |
| 2 | File not found |
| 3 | Malformed/structurally invalid CSV |

## Lesson

**Never use `csv.DictReader` without `strict=True` when parsing untrusted or real-world CSV files.** The lenient default silently corrupts data. Always add a post-parse ragged-row check for extra safety. Data-processing CLI tools that exit 0 with wrong data are worse than tools that exit non-zero — they give false confidence.
