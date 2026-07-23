# Python 3.12+ TypedDict `extra_items` Fix for lm-eval-harness

## Problem

lm-eval-harness v0.4.12 uses the deprecated `extra_items` parameter in `TypedDict` which was removed in Python 3.12 (PEP 728).

## Error Traceback

```
Traceback (most recent call last):
  File "/home/bratan/.local/bin/lm-eval", line 8, in <module>
    sys.exit(cli_evaluate())
  ...
  File "/home/bratan/.local/lib/python3.12/site-packages/lm_eval/result_schema.py", line 110, in <module>
    class _TaskMetrics(TypedDict, Generic[T], extra_items=T):
TypeError: _TypedDictMeta.__new__() got an unexpected keyword argument 'extra_items'
```

After fixing line 110, second occurrence at line 163:
```
  File "/home/bratan/.local/lib/python3.12/site-packages/lm_eval/result_schema.py", line 163, in <module>
    class SampleResult(TypedDict, extra_items=float):
TypeError: _TypedDictMeta.__new__() got an unexpected keyword argument 'extra_items'
```

## Fix

Replace `extra_items=T` / `extra_items=float` with `total=False` in both class definitions.

### File: `/home/bratan/.local/lib/python3.12/site-packages/lm_eval/result_schema.py`

**Line 110** (before):
```python
class _TaskMetrics(TypedDict, Generic[T], extra_items=T):
```

**Line 110** (after):
```python
class _TaskMetrics(TypedDict, Generic[T], total=False):
```

**Line 163** (before):
```python
class SampleResult(TypedDict, extra_items=float):
```

**Line 163** (after):
```python
class SampleResult(TypedDict, total=False):
```

## One-liner Patch

```bash
sed -i 's/extra_items=T/total=False/' /home/bratan/.local/lib/python3.12/site-packages/lm_eval/result_schema.py
sed -i 's/extra_items=float/total=False/' /home/bratan/.local/lib/python3.12/site-packages/lm_eval/result_schema.py
```

## Verification

```bash
lm-eval ls tasks
```

Should list tasks without TypeError.

## Notes

- This fix is only needed for lm-eval-harness <= 0.4.12 on Python 3.12+
- The GitHub main branch (0.4.13.dev+) may already have this fixed
- Install from git to get latest: `pip install git+https://github.com/EleutherAI/lm-evaluation-harness.git`