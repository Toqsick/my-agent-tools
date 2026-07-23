# Fix-Loop Reproduction Reference

Concrete fix patterns extracted from a Verifier-run session on
`csv_summary.py` (2026-07-07). Browse this file for technique inspiration
when facing the same bug families in other projects.

## Numeric Stability: NaN / Inf in Statistical Functions

**Symptom:** `statistics.fmean` raises `StatisticsError` or returns NaN
when a numeric column contains `NaN`, `inf`, or `-inf` literals.

**Root cause:** `float('nan')` and `float('inf')` are valid floats that
ship without `ValueError` but break `mean()`, `median()`, etc.

**Fix pattern — filter before compute:**

```python
import math

def numeric_stats(values: list[float]) -> dict:
    """Compute summary stats, filtering out non-finite values first."""
    finite = [v for v in values if math.isfinite(v)]
    non_finite = len(values) - len(finite)

    if not finite:
        return {"count": 0, "non_finite": non_finite, ...}

    return {
        "count": len(finite),
        "mean": statistics.fmean(finite),
        "non_finite": non_finite,
        ...
    }
```

**Why `math.isfinite`:** Checks for both NaN AND Inf in one call. Better
than `isinstance(v, float) and not math.isnan(v)` which misses `inf`.

**Reporting:** Add non-finite count to the column's `missing` field so the
user sees the real data story: "missing: 3" means 3 values that could not
contribute to statistics, not just absent cells.

## Ragged Rows: Field-Count Mismatch

**Symptom:** A row with more/fewer fields than the header causes an
`AttributeError: 'NoneType' object has no attribute 'get'` or a silent
skip instead of a clean error message.

**Root cause:** `csv.DictReader` silently skips rows that don't match
the header field count. When those rows are the only ones with data,
the summary produces empty results.

**Fix pattern — raw reader + explicit field-count check:**

```python
import csv

def detect_ragged_rows(filepath: str) -> list[int]:
    """Return row numbers (1-indexed) where field count differs from header."""
    with open(filepath, newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise EmptyFileError(filepath)

        header_len = len(header)
        ragged = []
        for i, row in enumerate(reader, start=2):  # 1-indexed, header is row 1
            if len(row) != header_len:
                ragged.append(i)
        return ragged
```

**Why `csv.reader` over `csv.DictReader`:** DictReader silently drops
rows with wrong field count. Reader preserves raw rows so you can
detect and report the mismatch. Use reader for validation, DictReader
only for well-formed data after the check passes.

**Exit convention:** Exit code 3 for ragged rows (INVALID_CSV). Message
format: `error: invalid CSV: row(s) [2, 5, 8] have a different number
of fields than the header`

## I/O Errors: Directory and Permission Rejection

**Symptom:** Passing a directory path or a chmod 000 file produces an
ugly `IsADirectoryError` or `PermissionError` traceback instead of a
clean error message.

**Fix pattern — EAFP with explicit handler order:**

```python
import os

try:
    with open(path) as f:
        ...
except FileNotFoundError:
    print(f"error: file not found: {path}", file=sys.stderr)
    return EXIT_NOT_FOUND
except (IsADirectoryError, PermissionError):
    # These are "not a readable file" — same exit code as not-found.
    print(f"error: cannot read file: {e}", file=sys.stderr)
    return EXIT_NOT_FOUND
except OSError as e:
    # Catch-all for EIO, ENOSPC, etc.
    print(f"error: cannot read file: {e}", file=sys.stderr)
    return EXIT_NOT_FOUND
```

**Key insight:** `IsADirectoryError` and `PermissionError` inherit from
`OSError`, so if you only catch `OSError`, they're caught. But if you
list `OSError` ABOVE them, they never reach their own handler. Order:
put most specific first.

**Exit convention for all of these:** Exit code 2 (NOT_FOUND in this
project's convention). Message format: `error: cannot read file: [Errno
NN] <details>: '<path>'`

## Encoding Errors: Latin-1 / Non-UTF-8 Files

**Symptom:** A CSV file with Latin-1 or other non-UTF-8 bytes crashes
with `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xfc`.

**Fix pattern — `errors='replace'` on open:**

```python
with open(path, newline="", errors="replace") as f:
    reader = csv.reader(f)
```

**Why not `errors='surrogateescape'`:** Surrogateescape produces
surrogate characters that may not display correctly. `replace` shows
`\ufffd` (�) characters that are self-evidently replacements — the
user sees "there was a bad byte here" rather than a crash.

**Belt-and-braces:** Even with `errors='replace'`, catch
`UnicodeDecodeError` in main() as a clean exit path for edge cases
(e.g. if a future refactor drops the parameter).

## CLI Parameter Validation: `--top N` Must Be >= 1

**Symptom:** `--top 0` or `--top -3` is silently accepted and produces
nonsensical output (zero top values shown, or a slicing crash).

**Fix pattern — argparse `type=` callable:**

```python
def _positive_int(s: str) -> int:
    """Argparse type=validator: int >= 1."""
    try:
        n = int(s)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError(f"expected int, got {s!r}")
    if n < 1:
        raise argparse.ArgumentTypeError(
            f"--top must be >= 1 (got {n})"
        )
    return n

parser.add_argument("--top", type=_positive_int, default=5, ...)
```

**Why not post-parse clamping:** `args.top = max(1, args.top)` silently
masks user error. The argparse type= pattern fails explicitly in the
CLI parser, giving the user immediate feedback without ever running
the program logic.

**Exit code:** When argparse rejects an argument, it exits with code 2.

## Path Leakage: Absolute Paths in Output

**Symptom:** Absolute input paths (`/home/user/data/sample.csv`) appear
in stdout or JSON output, which may be consumed by pipelines or shared.

**Fix pattern — basename for display, full path to stderr:**

```python
import os

def main():
    display_path = os.path.basename(args.file)
    abs_path = os.path.abspath(args.file) if os.path.exists(args.file) else args.file

    # Full resolved path goes to stderr only (prefixed with # for grep-ability)
    print(f"# {abs_path}", file=sys.stderr)

    if args.json:
        out = {"path": display_path, ...}  # basename, not abs path
    else:
        print(format_report(..., display_path=display_path))
```

**Why stderr for the full path:** Pipelines capture stdout (`|`),
redirect stderr (`2>`). A downstream script can grep stderr for `#`
to recover the absolute path if needed, but stdout stays clean.

## Truncation: Long Labels Breaking Alignment

**Symptom:** A categorical value longer than the column width in an
ASCII bar chart wraps or misaligns subsequent bars.

**Fix pattern — fixed-width truncation with ellipsis:**

```python
label_width = 14
if len(label) > label_width:
    label = label[: label_width - 1] + "…"

return f"  {label:<{label_width}} | {'█' * bar_len:<{width}} {count}"
```

**Key design choice:** Reserve 1 character for the ellipsis character
(`…`, U+2026, 1 char in Python's `len()`) so the column width stays
exactly `label_width` for every row. Without the `- 1`, the ellipsis
adds a character and misaligns the `|` marker.

## Testing: Regression Tests for Fixed Bugs

When adding tests for regression coverage:

```python
def test_numeric_nan_inf_does_not_crash(tmp_path):
    """Bug #2: NaN/Inf literals must not crash fmean."""
    p = tmp_path / "with_nan.csv"
    p.write_text("x\n1\nNaN\ninf\n-inf\n")
    result = run_cli(str(p))
    assert result.returncode == 0
    assert "missing: 3" in result.stdout
    assert "Traceback" not in result.stderr

def test_ragged_extra_field_returns_exit_3(tmp_path):
    """Bug #3: ragged rows must exit 3, not crash."""
    p = tmp_path / "ragged.csv"
    p.write_text("a,b,c\n1,2,3,4\n")
    result = run_cli(str(p))
    assert result.returncode == 3
    assert "invalid" in result.stderr.lower()
    assert "Traceback" not in result.stderr

def test_latin1_encoding_returns_clean_exit(tmp_path):
    """Bug #4C: Latin-1 encoding must not crash with UnicodeDecodeError."""
    p = tmp_path / "latin1.csv"
    p.write_bytes(b"a,b\nM\xfcnchen,1\n")
    result = run_cli(str(p))
    assert result.returncode in (0, 3)  # either clean decode or clean reject
    assert "Traceback" not in result.stderr
```

**Key patterns in these tests:**
- `tmp_path` for hermetic, self-cleaning file creation (no cleanup code)
- `write_bytes()` for non-UTF-8 content (can't use `write_text` with Latin-1)
- Assert on exit code, stdout content, AND absence of "Traceback"
- Return to `chmod` after `chmod 000` in a `try/finally` block so pytest
  can clean up `tmp_path`
