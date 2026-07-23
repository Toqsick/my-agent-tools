---

name: classify-test-failures
description: "Use when user asks for classify test failures, test isolation analysis, CI regression detection. NOT for writing tests, debugging. Classifies CI test failures as real regressions or test isolation issues."
version: 1.0.0
author: Yuno
license: MIT
platforms:
- linux
- macos
metadata:
  hermes:
    category: software-development
    tags:
    - testing
    - debugging
    - test-isolation
    - fixture-leakage
    - flaky-tests
    - audit
    related_skills:
    - systematic-debugging
    - verify-before-fix
    - test-driven-development
changelog:
  1.0.0 (2026-07-13): Initial version — extracted from kanban test-leakage audit (18/18
    classified as fixture-leakage, 0 real regressions).
agent: Engineer
routing_hint: '**Agent-Scope:** Code-Tasks (build / fix / refactor / debug / review).
  Off-scope: visual design, long-form copy, data modeling — say ''this is Designer/Writer/Analyst''s
  territory'' and return to Yuno.

  Routing-Spec: `yuno-team-routing`.

  '

---


---

# Classify Test Failures: Real Regression vs. Test Isolation

## Overview

When CI or a full-run reports N failing tests and you cannot tell whether
production code is broken or the test infrastructure is, do not guess.
Run a structured ordering matrix and let the failure pattern classify the
root cause.

**Core principle:** A test that **always** fails is a regression candidate.
A test that **only** fails in specific orderings is a fixture-leak candidate.
A test that **passes in isolation but fails in cumulative runs** is
ordering-sensitive. The pattern is the diagnosis.

**Iron rule:** Do NOT propose code fixes until every failing test is
classified by observed pattern. Symptom fixes on fixture-leak tests
silently make the suite green while leaving the real bug unfixed.

## When to Load This Skill

- A batch of tests fails in CI or `pytest tests/...` but passes locally
- A specific ordering is needed to reproduce a failure
- The user asks "is this a real regression or a test bug?"
- You need to triage a list of N failing tests before deciding what to fix
- Tests pass in isolation but the cumulative run reports failures
- A recent code change caused "failures" but you're not sure they're real

## When NOT to Load

- A single test fails for an obvious reason (use `systematic-debugging`)
- You have a bug report with file:line (use `verify-before-fix`)
- You need to fix a known regression (use `systematic-debugging` Phase 4)
- The failure is a crash / exception trace you can read directly

## The Classification Workflow

### Phase 1: Establish the Baseline (Reproducibility Check)

Before classifying anything, **prove you can reproduce the original failure
list from a clean state**. If you cannot reproduce it, the original report
may already be stale (e.g. flaky, env-dependent, or fixed by an unrelated
merge). Document the exact commands used.

**Clean-state setup commands (always):**
```bash
cd <repo>
git status              # confirm clean tree (or record uncommitted state)
git diff --quiet; echo $?   # 0 = no diff
export TMPDIR=/tmp/<unique-audit-dir>  # ISOLATE from prior partial runs
export PYTHONDONTWRITEBYTECODE=1       # prevent stale .pyc masking issues
```

**Run the original failing set and record the failure list:**
```bash
PY=<interpreter>
"$PY" -m pytest -p no:cacheprovider -q --tb=line <original-pattern>
```

**Save the failure list to a file** — the terminal buffer truncates and
you WILL need it again.

### Phase 2: Single-File Isolation (eliminates cross-file leakage)

For each file containing one or more of the N failures, run **just that file
in isolation**:

```bash
for f in <file1> <file2> ... ; do
  echo "=== $f ==="
  "$PY" -m pytest -p no:cacheprovider -q --tb=line "$f"
done
```

**Classification at this point:**

| Result | Implication |
|---|---|
| All files pass | The failures are 100% cross-file leakage / ordering |
| One file fails alone | Suspect: bug in that file's own fixtures, OR real regression |
| Several files fail alone | Suspect: production regression in shared code path |

**For any file that fails alone, drill into it** (Phase 4).

### Phase 3: Pairwise Ordering Matrix (finds the leak source)

For each combination of two suspect files, run **in both orders**:

```bash
for order in 'A B' 'B A' ; do
  "$PY" -m pytest -p no:cacheprovider -q --tb=line $order
done
```

**The order-sensitivity tells you who pollutes whom:**

| Pattern | Diagnosis |
|---|---|
| A then B fails; B then A passes | A's teardown leaks state into B |
| Both orders fail with same error | Both rely on broken shared state (real bug or fixture) |
| Both orders pass | A and B are clean — the bug needs 3+ files to surface |

**Build a minimal cascade**: keep adding files to the prefix until the
target test fails. The smallest prefix that reproduces the failure is
your "minimal cross-file dependency" — it's the file whose teardown is
the leak source.

### Phase 4: Within-File Drill-Down (for files failing alone)

For each file that fails in isolation, run the failing tests in different
**within-file orderings**. If two tests in the same file interact via a
module-level singleton, you will see ordering-sensitivity here.

```bash
"$PY" -m pytest -p no:cacheprovider -q --tb=line <file>::<test1> <file>::<test2>
"$PY" -m pytest -p no:cacheprovider -q --tb=line <file>::<test2> <file>::<test1>
```

### Phase 5: Classify Each Failure

For each test ID, fill in this row:

| Test ID | Passes alone? | Passes with prefix X? | Pattern | Classification |
|---|---|---|---|---|
| `test_foo::test_bar` | yes | only with prefix Y or no prefix | ordering-sensitive | FIXTURE_LEAK |
| `test_baz::test_qux` | no | no | always fails | REAL_REGRESSION |
| `test_blah` | yes | no | fails in cumulative only | CROSS_FILE_LEAK |

**Classification taxonomy (use these labels verbatim):**

- **`REAL_REGRESSION`** — Test fails in isolation, fails in cumulative, no
  ordering matters. Production code in `<module>:<line>` is wrong.
- **`FIXTURE_LEAK`** — Test passes in isolation, fails only when a specific
  preceding test/fixture mutates shared state. Test code at `<file>:<line>`
  or `<fixture-name>` is wrong.
- **`TEST_ORDERING`** — Within-file ordering matters (same file, different
  test first = fail). Module-level mutable state in test setup.
- **`CROSS_FILE_LEAK`** — Test passes alone and within-file, but fails when
  another file's tests run before it. `sys.modules` re-imports, conftest
  autouse fixture side-effects, or module-globals across files.
- **`ENV_VAR_BLEED`** — Test depends on env var that gets set/unset by
  another test or by the dev shell. Fix in conftest's autouse isolation.
- **`FLAKY`** — Non-deterministic, sometimes passes sometimes fails.
  Needs tighter loop (see `systematic-debugging` Phase 1).

**Count and report**:
- "M of N tests classified as `FIXTURE_LEAK` (test code issue)"
- "K of N classified as `REAL_REGRESSION` (production code issue)"
- Sum should equal N.

### Phase 6: Mechanism Proof (for non-trivial classifications)

For the leakiest, most non-obvious classifications, **replay the
mechanism without pytest** using a small Python script. This proves your
classification is correct and gives you a regression test to attach
to the eventual fix.

```python
# Standalone reproduction template
import sys, importlib, tempfile, os
sys.path.insert(0, '<repo>')

# 1. Collection-time import (replicates pytest collection)
spec = importlib.util.spec_from_file_location(
    '<test_module>', '<test_file>.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# 2. Capture references (like `from X import Y` at module scope)
captured_ref = mod.<something_bound_at_module_scope>

# 3. Simulate the polluting fixture (e.g. sys.modules wipe)
for k in list(sys.modules.keys()):
    if k.startswith('<module_prefix>'):
        del sys.modules[k]

# 4. Try the test body — observe that the captured reference is now stale
# <test body here>
```

If the standalone repro shows the same empty-capture / wrong-target
symptom as pytest, your classification is locked in. Save the script as
`scripts/<classification-name>-standalone-repro.py` under this skill.

### Phase 7: Report Structure

Write the final report with this layout (see references/example-report.md):

1. **Reproducibility proof** — commands and counts that re-confirm the
   original N failures from clean state.
2. **Isolation results** — per-file single-run pass/fail counts.
3. **Pairwise / ordering matrix** — which orderings reproduce, which don't.
4. **Classification table** — every test ID with its category label and
   root-cause code location.
5. **Mechanism proofs** — for the non-obvious cases, inline the standalone
   repro that demonstrates the leak.
6. **Recommendations (no auto-fix)** — propose the smallest fix per
   category, but do NOT implement without sign-off. List four or five
   options ranked by blast radius.
7. **Reproduction commands** — copy-pasteable for the user to verify.

## Pitfalls

### Do Not Invert the Order of Phase 1 and Phase 2

Reproducing the original failure list FIRST (Phase 1) is non-negotiable.
If you skip to "fix the tests" without first proving you can reproduce,
you'll fix the wrong layer and the original failures will reappear.

### Do Not Edit Test Files Before Classification

Mutating the test fixture "to see if it fixes things" **before**
classification destroys the evidence. You cannot classify what you've
already contaminated. Always restore with `git checkout -- <file>` or
`git show HEAD:<file> > <file>` before each re-run.

### Cache and Bytecode Files

Always use `-p no:cacheprovider` (disables `.pytest_cache`) and
`PYTHONDONTWRITEBYTECODE=1`. Stale `.pyc` files from prior partial runs
cause "impossible" failures that vanish after `find . -name __pycache__ -exec rm -rf {} +`.

### TMPDIR Contamination

If you re-use `/tmp` between audit sessions, the previous session's
fixtures (databases, lock files, plugin caches) can leak in. Always use
a unique `TMPDIR=/tmp/<audit-name>-<date>` per audit session.

### Module-Scope `from X import Y` Is the Usual Suspect

Python's `from X import Y` binds Y at import time. If a test does
`from hermes_cli.plugins import get_plugin_manager` at module scope,
and a sibling test wipes `sys.modules['hermes_cli.plugins']`, the
captured `get_plugin_manager` is now an orphan — it returns the OLD
singleton, but the live plugin module is a NEW one. The fix: use
`importlib.import_module(...).get_plugin_manager()` at call time.
**This is the #1 cause of cross-file test leakage in suites with
plugin systems / singletons / service-locator patterns.**

### Monkeypatch at Module Attribute vs. Local Reference

`monkeypatch.setattr(hermes_cli.kanban_db, "dispatch_once", fake)`
overwrites the **module attribute**. The next test in the same session
that does `from hermes_cli.kanban_db import dispatch_once` will see the
fake, even if monkeypatch's finalizer has "restored" the original —
because finalizers run at fixture teardown but `import X` is cached.
Fix: use `monkeypatch.setattr(target_obj, "attr", fake)` where target
is the **imported module object**, not the name string. And scope
carefully to one test.

### Do Not Classify Without a Mechanism Proof for the Weird Ones

For the obvious "passes alone, fails cumulative" cases, you can classify
by pattern alone. For anything where you're not 100% sure why it's
ordering-sensitive (e.g. "why does adding test_kanban_db.py break
test_kanban_lifecycle_hooks.py?") — write the standalone repro. The
15 minutes you spend proves the classification and gives you the
regression test for free.

### "0 Real Regressions" Is a Valid Finding

If your classification finds 0 real regressions and N fixture leaks,
that's still a successful audit. Report it cleanly. Don't manufacture
a regression to make the audit look more substantial — that's worse
than useless.

## Reference Material

- `references/example-report-kanban.md` — Complete audit of 18 kanban
  test failures (100% fixture-leakage, 0 real regressions). Use as
  template for report structure.
- `references/classification-taxonomy.md` — Detailed definitions and
  decision tree for each classification label.
- `scripts/standalone-repro-template.py` — Copy-paste skeleton for
  proving a classification without pytest.

## Related Skills

- `systematic-debugging` — Phase 1 "tight feedback loop" applies here:
  before classifying, prove the loop can reproduce the failure.
- `verify-before-fix` — When classifications point to real regressions,
  switch to this skill to execute the fixes.
- `test-driven-development` — Once you classify a leak, the standalone
  repro from Phase 6 becomes the regression test for the fix.