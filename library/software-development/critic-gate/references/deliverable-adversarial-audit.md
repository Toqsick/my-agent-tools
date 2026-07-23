# Deliverable Adversarial Audit

> **Methodology for systematically probing AI-generated deliverables.**
> Not a code review of diffs — an adversarial investigation of a *completed deliverable*
> that claims certain features, exit codes, and robustness guarantees.
>
> Derived from a real session: audit of a `csv_summary.py` CLI tool (7 July 2026) that
> passed 9/9 tests but broke on 5 common real-world scenarios on the first adversarial probe.

## Purpose

When a subagent or external AI delivers a finished artifact (CLI tool, library, web app),
standard code review checks diffs — but misses **claims-reality gaps**. This methodology
closes that gap by treating the deliverable as a black-box and probing until it breaks.

## Phase 1 — Surface scan

### Read everything
- The main source file
- All tests
- README / docs
- Any config files

### Inventory claims
Document every claim the deliverable makes about itself:

| Claim source | Example from session |
|---|---|
| Exit code contract | "0=success, 1=empty, 2=not found, 3=invalid CSV" |
| Feature documentation | "Detects rows with wrong field count" (line 145 comment) |
| Error handling | "Invalid file returns clean error message" |
| Security | "Reads files, no write or network" |
| Test coverage | "7 tests" (actual: 9 — doc drift) |

### Run the tests
```
cd <project> && pytest -v 2>&1
```
Confirm all pass. If they don't, that's already a blocker — escalate.

## Phase 2 — Adversarial probing

For each category below, construct minimal inputs and observe behavior.
Log exit code, stdout, stderr. Record every stack trace.

### A. File access edge cases

| Input | What it tests | Session finding |
|---|---|---|
| Non-existent file | `FileNotFoundError` handling | ✅ Caught cleanly (exit 2) |
| Existing directory (e.g. `/etc`) | `IsADirectoryError` | 🔴 Unhandled — stack trace leak |
| File with `chmod 000` | `PermissionError` | 🔴 Unhandled — stack trace leak |
| `stdin` (pipe to `/dev/stdin`) | Pipe support | ⚪ Works if explicitly handled |
| Empty file (0 bytes) | Empty input | ✅ Caught cleanly |
| Header-only file | Degenerate case | ✅ Works if handled |
| Symlink to missing target | Follow or fail? | Check documentation |

### B. Encoding edge cases

| Input | What it tests | Session finding |
|---|---|---|
| UTF-8 BOM | MS Office default export | ⚪ May or may not handle |
| Latin-1 / Windows-1252 | European CSVs (e.g. `Müller,straße,hôtel`) | 🔴 `UnicodeDecodeError` — stack trace leak |
| UTF-16 | Excel-Europe default | 🔴 Same crash |
| Mixed encoding in cells | Escaping issues | ⚪ Unlikely to be handled |

**Pattern:** AI tools almost always hardcode `encoding="utf-8"` without `errors="replace"` or fallback.

### C. Numeric edge cases

These typically break `statistics` stdlib calls.

| Input | What it tests | Session finding |
|---|---|---|
| Large-but-legal values (e.g. `9999`, `1e308`) | `stdev` overflow | 🔴 `AttributeError` in `stdev` on large values because `(x-mean)**2` overflows |
| `NaN` string literal | Scientific/ML exports | 🔴 `fmean` crashes with `ValueError: -inf + inf` |
| `Inf` / `-Inf` strings | Same sources | 🔴 Same crash |
| European decimal format (`,`) vs US (`.`) | Locale awareness | ⚪ Silently typed as categorical |
| Currency symbols (`$100`, `€50`) | Value stripping | ⚪ Silently typed as categorical |
| Mixed types (e.g. `"N/A"` in numeric column) | Coerce-or-categorical | ✅ Often handled — counted as missing |

**Pattern:** AI test data uses clean, small integers. Real-world data has `NaN`, `Inf`, locales, and floats near IEEE 754 limits.

### D. CSV structure edge cases

| Input | What it tests | Session finding |
|---|---|---|
| Extra field: `a,b,c\n1,2,3,4` | Ragged-over detection | 🔴 Code *claims* detection on line 145, but `csv.DictReader` packs extra under `None` key — check never fires |
| Missing trailing field: `a,b,c\n1,2` | Ragged-short detection | 🔴 Parser fills `None` — `len(row) == 3` always, detection useless |
| Quoted field with embedded newline | Multi-line CSV cells | ✅ `csv.DictReader` handles correctly |
| Empty header name: `,b\n1,2` | Column name collision | ⚪ Renders empty column name — works but confusing |
| Column named `_top_n` | Internal-key collision | 🔴 JSON filter `if not k.startswith("_")` silently drops column data |
| Very long categorical values (>20 chars) | Formatting safety | ⚪ Display truncated, bar chart meaningless |

### E. CLI argument edge cases

| Input | What it tests | Session finding |
|---|---|---|
| `--top 0` | Zero-limit edge case | 🔴 Accepted silently, output empty |
| `--top -3` | Negative limit | 🔴 Accepted silently, output empty |
| `--top abc` | Type validation | ✅ Caught by argparse |
| Missing required argument | Usage error | ✅ Caught by argparse |
| Unknown flag (`--nonexistent`) | Flag validation | ✅ Caught by argparse |
| No arguments | Help screen | ✅ Usually handled |
| `--json` flag | Output format | ✅ Works if implemented |

### F. Output contract verification

| Check | Method | Session finding |
|---|---|---|
| Exit codes match docs | Run 10 edge cases, check `echo $?` each | 🔴 Exit 1 conflates "empty file" and "unhandled OSError" |
| Error messages are clean | Check stderr for stack traces | 🔴 3 bugs produced raw Tracebacks |
| JSON output is parseable | `python3 -c "import json,sys; json.load(sys.stdin)"` | ✅ Schema valid |
| JSON doesn't leak internal paths | Check `path` field in JSON | 🔴 Absolute path leaked (`/home/alice/MH-records/`) |
| JSON doesn't drop columns | Compare CLI output vs JSON output | 🔴 `_`-prefixed columns silently dropped |

## Phase 3 — Claim verification

Take each claim from Phase 1 and test it explicitly.

| Claim | Test | Session finding |
|---|---|---|
| "Detects rows with wrong field count" | Ragged CSV | 🔴 Claim false — detection is structurally broken |
| "Bad cells counted as missing" | Column with `1,2,abc,4` | ✅ Works |
| "ASCII bar chart" | Long category labels | ⚪ Labels truncated, bars meaningless |
| "Exits 3 for invalid CSV" | Truly malformed CSV | ✅ Works |
| "7 tests" | `grep -c "^def test_" test_file` | 🔴 Doc stale — actually 9 tests |

## Phase 4 — Risk callouts

After probing, classify findings into a production-risk summary:

| Risk class | Meaning | Session examples |
|---|---|---|
| **CRITICAL** | Silent corruption, data loss, or crash on common real-world input | stdev overflow, NaN/Inf crash |
| **HIGH** | Feature claim is false — code doesn't do what docs say | Ragged detection broken |
| **MEDIUM** | Works on happy path, fails on predictable inputs | Non-UTF-8, permission errors |
| **LOW** | Annoying but usable | Doc drift, path leak in JSON |
| **OBSERVATION** | Not a bug, but worth noting | Boolean typed as numeric, empty-header edge |

## Phase 5 — Verdict

```
┌─────────────────────────────────────────────────────┐
│  VERDICT: FAIL │
│  (or PASS / CONDITIONAL-PASS) │
│                                                     │
│  Passes 9/9 tests but breaks on 5 common            │
│  real-world scenarios. NOT safe for production.     │
│                                                     │
│  Blocking issues:                                   │
│  • [CRITICAL] stdev overflow on large values        │
│  • [CRITICAL] NaN/Inf crash in fmean                │
│  • [HIGH]    Ragged detection is broken             │
│  • [MEDIUM]  PermissionError stack trace leaks      │
│  • [MEDIUM]  Non-UTF-8 encoding crash               │
│  • [LOW]     Doc drift (7→9 tests)                  │
└─────────────────────────────────────────────────────┘
```

## Re-audit methodology (after fixes are applied)

After an earlier audit produced bugs and an Engineer applied fixes, the re-audit
answers a different question: *did the fixes actually work, and what new issues
did they introduce?*

**Key difference from the initial audit:** You're not testing the original
code on unhappy paths — you're testing someone else's fix on paths they
*changed*, plus probing for new failure modes the fix may have opened.

### The 4-phase re-audit

**Phase 1 — Fix verification (one per bug).** Run each repro command from
the original audit and confirm it now produces the *correct* (non-broken)
behavior. Do this with the tool's actual repro command, not a custom one:

```bash
python3 csv_summary.py /tmp/verifier-repro/nan_inf.csv
echo "EXIT=$?"
```

For each fix, check:
- Exit code matches the documented contract
- No "Traceback" in stderr
- Error messages are clean and informative
- The fix actually resolves the original symptom (e.g. mean computed over
  finite values only, not crashing)

**Phase 2 — Adversarial regression hunt.** Create a dedicated directory
for throwaway test fixtures (e.g. `/tmp/verifier-repro/`) so you can create
and destroy fixtures freely without contaminating the project:

```bash
mkdir -p /tmp/verifier-repro
```

Then probe with inputs the fixes may have broken or missed. Categories:

| Category | What to test | Session findings |
|---|---|---|
| Encoding edge cases | UTF-8 BOM, mixed EOL, Latin-1 bytes | **Issue #9: BOM leaks into column keys** (`\ufeffa` in JSON) |
| CSV structure | Duplicate headers, ragged rows, quoted commas, embedded newlines | **Issue #10: Duplicate headers silently overwrite** — column count says 3, dict has 2 keys |
| Numeric bounds | All-NaN/Inf columns (no finite values), very large ints, zero-row files | All-NaN should produce "(no numeric data)" not a crash |
| CLI arguments | `--top` with huge int, combined `--json --chart`, negative values | Should not conflict or crash |
| File types | Symlinks to dirs, fifos/named pipes, binary files | Should exit cleanly, not crash |
| Path leakage | Verify both stdout AND stderr for absolute path leaks | Error messages in stderr may carry absolute paths while stdout is clean |

**Issue #10 identification pattern (silent data loss):** When a tool reports
a column count (e.g. "3 columns") but JSON output shows fewer dict keys,
something is swallowing data. The root cause: using header strings as dict
keys. Duplicate names overwrite earlier columns. Detect by comparing the
tool's stated count with the actual dict key count:

```bash
python3 csv_summary.py --json dup.csv | python3 -c "
import json,sys
d = json.load(sys.stdin)
cols = d['columns']
print('claimed columns:', d.get('column_count', 0))
print('actual keys:', list(cols.keys()))
print('key count:', len(cols))
"
```

This caught Issue #10 because the tool reported "Columns: 3" but JSON showed
only 2 keys — one entire column of data was silently gone.

**Issue #9 identification pattern (invisible characters in keys):** BOM
(U+FEFF) is invisible in terminal output but visible in JSON. Always inspect
raw JSON keys for unexpected characters:

```bash
python3 -c "
import json,sys
d = json.load(sys.stdin)
for k in d.get('columns', {}):
    if any(ord(c) > 127 for c in k):
        print(f'ISSUE: key has non-ASCII: {k!r}')
"
```

This caught Issue #9 because the key appeared as `'a'` in stdout but was
actually `'\ufeffa'` in JSON — an invisible BOM prefix that would cause
pipeline consumers to miss the column entirely.

**Phase 3 — Run the full test suite.** After the adversarial probes, confirm
no regressions from the fixes:

```bash
python3 -m pytest tests/ -v
```

**Important:** The test suite may be stale relative to documentation (e.g.
README says "7 tests", actual count is more). Always count and report the
actual number, not the documented number.

**Phase 4 — End-to-end file read.** Read every shipped file completely:

1. **Module docstring (usage line)** — Compare the `usage:` line at the top
   of the source file against the actual argument parser (`build_parser()`,
   `argparse`, etc.). Flags documented in the usage line but missing from the
   parser are **module-docstring drift** — a subclass of doc drift that's more
   visible than README drift because the usage line is the first thing printed
   when someone reads the source. Pattern from a real 3rd re-audit: docstring
   said `--no-color` was a valid flag, `build_parser()` had no such argument,
   and argparse rejected it with `unrecognized arguments`.

2. **Main source (body)** — check for TODOs, FIXMEs, HACK, XXX markers
   (evidence of incomplete fixes or sloppy patches)

3. **Test file** — verify coverage matches what you observed

4. **README** — check for doc drift (stale test counts, stale exit code
   tables, outdated feature claims, flag tables that mismatch the actual CLI)

5. **Cross-reference scan** — grep every flag defined in the parser, then
   grep the README flags table. Every flag in one source that's missing from
   the other is drift. Also grep the module docstring usage line separately —
   that line is often hand-maintained and drifts independently.

### Re-test plan format

After a re-audit concludes, the deliverable should include a structured
re-test plan for any new issues found:

```markdown
## Re-test plan

After Engineer addresses Issues #9 and #10, re-run:

    cd <project> && python3 -m pytest tests/ -v

Add new tests:
- test_bom_does_not_leak_into_column_names
- test_duplicate_header_names_rejected_or_renamed

Manual probes to re-verify:
- `printf '\xef\xbb\xbfa,b\n1,2\n' | tool --json` → column key must be
  `'a'`, not `'\ufeffa'`
- `printf 'a,b,a\n1,2,3\n4,5,6\n' | tool --json` → must not lose the
  first column's data (3 keys, not 2)
```

### Inputs that should NOT break but didn't (tested envelope)

Always keep a running list of everything you tried that worked. This is not
boasting — it documents the edge of the tested envelope so the next round
knows what's been checked and what hasn't. From the re-audit session:

- Empty-but-not-zero-byte (`\n` only) → clean exit
- Header-only with trailing newline → clean exit
- All-NaN column → "(no numeric data)" message, no crash
- Mixed-ragged rows → specific row names in error
- CRLF, mixed EOL, embedded quotes/commas/newlines in headers → all handled
- 10000-column file → processed in 0.2s, no OOM
- `--top 99999` → safe (capped at unique count)
- `--json --chart` → no conflict
- Symlink-to-dir → handled
- Binary file → doesn't crash (output is garbage but exit is clean)

---

## Pitfalls

1. **Trusting claims.** Don't. "Detects ragged rows" doesn't mean the detection works. Test every documented claim with an adversarial input.
2. **Only testing the happy path.** AI-generated testdata is always clean integers, always UTF-8, always well-formed. Your adversarial inputs must look nothing like the test data.
3. **Stopping at the first bug.** The session found 5 bugs because I kept poking after finding the first one. Bugs cluster — if you found one encoding issue, there's probably another in the same area.
4. **Missing the test suite's blind spot.** Tests only cover what the author thought of. The adversarial probe finds what they *didn't* think of.
5. **Failing to check JSON output separately.** A tool can produce correct CLI output but broken JSON (e.g. leaked path, dropped columns). Always verify with `python3 -c "json.load(sys.stdin)"`.
6. **Skipping exit code verification.** A tool that says it exits 3 might actually exit 1 on that code path. Run every edge case and capture `echo $?`.
7. **Treating the re-audit as a re-test plan.** A re-test plan says "re-run these commands and check." A re-audit says "probe adversarially for what the fix broke." They are different activities — the re-audit happens BEFORE the re-test plan is written.
8. **Stopping at stdout inspection.** Fixes may clean stdout but leave absolute paths in stderr error messages. Always check BOTH streams.
9. **Missing the hidden-key pattern.** A tool that uses dicts with header keys can silently lose data when column names collide. Always compare stated column count with actual dict key count in JSON output.

10. **Trusting the module docstring usage line.** The `usage:` line at the
    top of a Python module is often hand-maintained and drifts independently
    from both the README and the `argparse.ArgumentParser` definition. A flag
    listed in the docstring but not in `build_parser()` produces an
    `unrecognized arguments` error at runtime — a UX regression that affects
    every user who reads the source before running the tool. Always
    cross-reference the docstring usage line against the actual parser, not
    just against the README. (Real finding from a 3rd re-audit: `--no-color`
    was in the docstring but missing from argparse.)
