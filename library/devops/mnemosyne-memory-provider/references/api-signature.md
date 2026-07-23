# Mnemosyne API Signatures — Import Paths & Pitfalls

Lessons from live integration (hermes-orchestration Skill, 2026-06-27).
Mnemosyne exposes three import paths with **different function signatures**.
Scripts that call these functions need to know which path is active — and
which keyword arguments each path accepts.

## The Three Import Paths

| Path | Module | `remember` kwargs | `recall` kwargs |
|------|--------|-------------------|-----------------|
| **Direct API** | `import mnemosyne` | `trust_tier`, `bank`, `valid_until`, … | `top_k`, `vec_weight`, `fts_weight`, … |
| **Hermes Tool** | `from hermes_tools import …` | `veracity` (not `trust_tier`) | `limit` (not `top_k`) |
| **Plugin** | `from mnemosyne_hermes import …` | varies — check `inspect.signature()` | varies |

There is **no single canonical signature**. Auto-detect via `inspect.signature`
is the safe approach when writing code that must work across all three.

## Pitfall 1: `veracity` does NOT exist on the direct API

```python
import mnemosyne
mnemosyne.remember(content="...", importance=0.9, veracity="tool")
# → TypeError: remember() got an unexpected keyword argument 'veracity'
```

**Fix:** Use `trust_tier` on the direct API:

```python
mnemosyne.remember(
    content="...",
    importance=0.9,
    trust_tier="tool",   # not veracity
)
```

The `hermes_tools.mnemosyne_remember()` wrapper *does* accept `veracity`
internally and translates it. But the plugin and direct paths don't.

## Pitfall 2: `top_k` vs `limit` on recall

```python
import mnemosyne
mnemosyne.recall(query="...", limit=3)        # WRONG
# → TypeError: recall() got an unexpected keyword argument 'limit'
```

**Fix:** Direct API uses `top_k`:

```python
mnemosyne.recall(query="...", top_k=3)        # correct on direct API
```

The Hermes wrapper uses `limit`. Same auto-detect pattern applies.

## Auto-Detection Helper

When writing scripts that should work regardless of import path:

```python
import inspect

def get_remember_kwargs(**user_kwargs):
    """Filter kwargs to whatever the active remember() actually accepts."""
    import mnemosyne
    sig = inspect.signature(mnemosyne.remember)
    accepted = set(sig.parameters.keys())
    return {k: v for k, v in user_kwargs.items() if k in accepted}

def get_recall_kwargs(top_k=5):
    """Return the right kwarg for whatever recall() is in scope."""
    import mnemosyne
    sig = inspect.signature(mnemosyne.recall)
    if "top_k" in sig.parameters:
        return {"top_k": top_k}
    return {"limit": top_k}  # hermes_tools fallback
```

## Auto-Detect the remember() Function Itself

Try each import path in order, fall back gracefully:

```python
def get_mnemosyne_remember():
    for module_name, attr in [
        ("mnemosyne_hermes", "mnemosyne_remember"),
        ("hermes_tools", "mnemosyne_remember"),
        ("mnemosyne", "remember"),  # last resort: direct API
    ]:
        try:
            mod = __import__(module_name, fromlist=[attr])
            fn = getattr(mod, attr, None)
            if fn is not None:
                return fn
        except ImportError:
            continue
    return None
```

`inspect.signature()` on the result confirms which kwargs are valid before
you call it — protects against silent breakage when Mnemosyne evolves.

## Stable Content-Hash for Dedup

`hash(content)` is **randomized between Python runs** (PYTHONHASHSEED).
Using it as a dedup key causes every cron run to look like a fresh import.

```python
import hashlib
heuristic_id = f"stable-{hashlib.md5(content.encode('utf-8')).hexdigest()[:16]}"
```

Persist imported IDs to `memory/.imported_heuristics.json` and check
membership on each run — `md5` is deterministic, so re-imports are idempotent.

## Field-Name Quick Reference

When passing to `mnemosyne.remember()` (direct API), only these kwarg names
are valid — anything else is silently ignored or rejected:

| Field | Direct API | Hermes Tool |
|-------|------------|-------------|
| `content` | ✅ | ✅ |
| `importance` | ✅ | ✅ |
| `source` | ✅ | ✅ |
| `scope` | ✅ | ✅ |
| `metadata` | ✅ | ✅ |
| `extract` | ✅ | ✅ |
| `extract_entities` | ✅ | ✅ |
| `valid_until` | ✅ | ✅ |
| `trust_tier` | ✅ | ❌ (use `veracity`) |
| `veracity` | ❌ | ✅ |
| `bank` | ✅ | varies |

Use `inspect.signature(fn)` as the source of truth in cross-path code.

## Live-Test Reference

Source of these findings: `~/.hermes/skills/orchestration/hermes-orchestration/scripts/mnemosyne_importer.py`
(built 2026-06-27, imports via `import mnemosyne`, calls `remember()` with
`trust_tier` and `recall()` with `top_k`). Verified recallable on first
import — Score 0.62–0.64 for Stable Heuristiken.