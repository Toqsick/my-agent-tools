# Classification Taxonomy — Decision Tree

When you have a list of N failing tests and need to label each, walk this
tree. Each label has a fingerprint (the pattern that produces it) and a
default fix layer (where to look first).

## REAL_REGRESSION

**Fingerprint:**
- Fails in isolation (single-file, single-test run)
- Fails the same way in cumulative runs
- Fails the same way regardless of test ordering
- The failure trace points to a real code path with broken logic, not a
  mock / patch / fixture interaction

**Default fix layer:** `hermes_cli/`, `agent/`, `gateway/`, etc. — the
production module that the failing test exercises.

**Diagnostic:** read the failing test, find the production function it
calls, and inspect THAT function. The traceback tells you where the
logic is wrong.

**Switch to `verify-before-fix` or `systematic-debugging` Phase 4 once
you have a confirmed root cause.**

## FIXTURE_LEAK

**Fingerprint:**
- Passes when run alone
- Fails only when one or more specific tests run before it
- The failure mode is typically "missing state" (empty list, None, no
  callback fired) rather than "wrong value"
- Test code uses `monkeypatch.setattr` or mutates a fixture-managed
  resource; the mutation outlives the test scope

**Default fix layer:** the test file's own conftest or the test's
fixtures. Common leak sources:
- `monkeypatch.setattr(MODULE, 'attr', fake)` survives because Python's
  `from X import Y` cached `Y` at the receiving module's import time
- `try/finally` cleanup that doesn't actually call `p.stop()` / `patch.stopall()`
- Module-scope fixture that captures a reference at collection time and
  that reference goes stale

**Diagnostic:** read the test's `try/finally` blocks, monkeypatch
decorators, and any `import`-time references. The thing the test
"thinks" it patched is not the thing that was patched at run time.

## TEST_ORDERING (within-file)

**Fingerprint:**
- Two tests in the same file: A then B fails; B then A passes (or
  single-file run with tests in reverse order changes the outcome)
- Same file, different ordering
- Module-level mutable state shared between tests in the file

**Default fix layer:** test fixtures in the same file. Move shared
mutable state into a per-test fixture (function-scope) instead of
module-scope; reset the state in a `finally` block.

**Diagnostic:** search the file for module-scope state: module-level
variables, `from X import Y` at the top, fixtures without explicit
`scope=` (defaults to `function` but check), class-level attributes in
test classes.

## CROSS_FILE_LEAK

**Fingerprint:**
- Each file passes in isolation
- Cumulative run fails
- The minimal cascade is "file X first, then file Y" (any prefix works)
- Often involves `sys.modules` re-imports, conftest autouse fixtures
  with module-level side-effects, or shared module-globals

**Default fix layer:**
1. The test files' `conftest.py` (autouse fixtures leaking state)
2. The test files themselves (e.g. `del sys.modules[...]` in a
   fixture that leaves the state worse than before)
3. The `tests/conftest.py` root autouse fixtures (e.g. setting
   `_plugin_manager = None` — usually a recovery, but can cascade if
   a test re-registers hooks on the OLD singleton)

**Diagnostic:** identify the polluting file (the FIRST file in the
prefix that triggers the leak). Inspect its `conftest.py` and root
fixtures for `sys.modules`, `monkeypatch.setattr`, and module-level
state.

## ENV_VAR_BLEED

**Fingerprint:**
- Test relies on an env var that's not set in `tests/conftest.py`
  `_hermetic_environment`'s clear-list
- Failure: code reads the env var, gets an unexpected value from
  parent shell or earlier test
- Passes in fresh shell with env var unset
- Fails when run in a shell where the env var is set (dev's machine)

**Default fix layer:** `tests/conftest.py` `_HERMES_BEHAVIORAL_VARS`
set (add the missing var) OR the test's own fixture that explicitly
sets/unsets the var with `monkeypatch.setenv` / `monkeypatch.delenv`.

**Diagnostic:** identify which env var the test reads
(`monkeypatch.setenv` calls in the test file's fixtures, or
`os.environ.get(...)` in the code under test). Check the conftest's
clear-list. If absent → add it.

## FLAKY

**Fingerprint:**
- Passes sometimes, fails sometimes
- No correlation with ordering or other tests
- Likely time-of-day, network, randomness, or PID-based

**Default fix layer:** test or production code that uses real time,
real PIDs, real randomness without seeding.

**Diagnostic:** see `systematic-debugging` Phase 1 step on
non-deterministic bugs. Run 100x with `for i in $(seq 1 100); do …`;
raise the reproduction rate before trying to debug.

---

## Decision Tree (Quick)

```
Fails alone?
├─ yes → REAL_REGRESSION (or FLAKY if non-deterministic)
└─ no
   ├─ Fails only with specific prefix file?
   │  └─ yes → CROSS_FILE_LEAK
   ├─ Within-file ordering matters?
   │  └─ yes → TEST_ORDERING
   ├─ Depends on env var not cleared by conftest?
   │  └─ yes → ENV_VAR_BLEED
   └─ Otherwise → FIXTURE_LEAK (general category)
```

Use the tree to assign the label, then read the corresponding section
above for the diagnostic + default fix layer.