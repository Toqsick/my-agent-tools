---
name: verify-before-fix
description: "Use when an issue or bug catalog names files, lines, or patterns to fix and the user needs those claims verified before editing. NOT for vague bugs without concrete issue targets or for fixing every similar-looking pattern blindly. Maps the real repository, detects partial fixes, verifies each defect, patches only the confirmed-broken subset, and batch-checks the result."
version: 1.0.0
author: Yuno
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    category: software-development
    tags:
    - bug-fixes
    - issue-execution
    - verification
    - workflow
    related_skills:
    - systematic-debugging
    - github-issues
    - greyscript-compiler-debugging
changelog:
  1.2.0 (2026-07-14): Variant C (bug-catalog cross-mapping), 7-status taxonomy (present_fixed/partial/unfixed/imports_only/doc_only/present_documented/absent_in_active_tree),
    multi-source verification pitfall, references/bug-catalog-cross-map.md.
  1.1.0 (2026-07-07): Variant B (priority-ordered fix loop), regression-test step
    after each fix, batch-final-verify phase, references/fix-loop-reproduction.md.
  1.0.0 (2026-07-07): Initial version — extracted from Issue
agent: Verifier
routing_hint: '**Agent-Scope:** Adversarial QA, audits, security scans, gates. Off-scope:
  building, designing, writing — return to Yuno for re-route.


  Routing-Spec: `yuno-team-routing`.

  '
trigger_keywords: ['issue', 'catalog', 'names', 'files', 'lines']
keywords: ['issue', 'catalog', 'names', 'files', 'lines']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['github-issues']
---

---

# Verify Before Fix: Issue-Driven Bug Fix Execution

When a task asks you to fix bugs defined by an issue with pre-specified
file:line locations (e.g. "Issue #43: 11 GreyScript syntax bugs in
`bin/ps.src`, `xmem.src`, …"), the issue is a **hypothesis, not ground truth**.
It may reference stale paths, already-fixed bugs, or files that no longer exist.

**Core rule (inherited from systematic-debugging):** No fixes without
verification first. Always.

## When to Load This Skill

- The task references a specific issue number with a bug list
- A multi-bug issue gives explicit file:line locations for each fix
- You're working on a branch that may already have partial fixes
- The issue's file paths don't match what you see in the repo
- You need to decide which bugs are truly unfixed before editing
- Your task is to cross-map a curated bug catalog against source code,
  producing a structured inventory of fix statuses (load → Variant C)
- A bug-reports directory exists and the task involves reconciling its
  entries against current or archived source files

## The Workflow

### Step 1: Find the Right Repo

First, locate the actual repo. The working directory hint may be wrong —
check multiple likely locations:

```bash
find ~ -maxdepth 4 -type d -name "<repo-name>" 2>/dev/null
```

Then read the repo structure:

```bash
ls -la <repo>
git branch
git log --oneline -5
```

### Step 2: Map Issue Paths to Repo Layout

Issue paths often follow a different layout than the actual repo:

| Issue says | Repo has | Map |
|---|---|---|
| `bin/ps.src` | `tools/ps/ps.src` | One level deeper, in a named tool dir |
| `test/test_core.src` | `tests/` or no such file | May not exist at all |
| `lib_core` | `libs/lib_core.src` | Moved or renamed |

**Don't jump to conclusions.** A missing file doesn't mean the repo is wrong —
it means the issue path needs remapping. Start by reading the repo root.

### Step 3: Detect Partial Fixes on the Branch

If you're on a feature/fix branch (not `main`), earlier commits may have
already addressed some or all of the listed bugs:

1. **Check git blame** on the suspected files to see when they were last changed
2. **Look for fix comments** in the code — `// FIX NP-49`, `// FIX BUG F-1`,
   `// Fixed 2026-07-04`, etc. These document intentional fixes, not stale code.
3. **Check the branch title** — if the branch is `fix/merge-…-fixes-into-…`,
   it's explicitly a branch carrying partial fixes.

**Crucial:** A fix-comment in the code means the bug was intentionally
corrected. Do NOT re-apply a "fix" to code that was already fixed.

### Step 4: Verify Each Bug Before Touching Code

For each bug in the list, run through this checklist:

1. **Does the file exist** at the mapped path? If not, find it or determine
   it was deleted/renamed.
2. **Does the stated line number** still contain the buggy pattern? (Line
   numbers drift with every commit — always check the actual line.)
3. **Is the bug pattern actually present AND active?** A `"char(10)"` inside a
   `// FIX BUG` comment is **documentation**, not a bug.
4. **Is the bug exclusive to code?** Grep the exact broken pattern and
   subtract matches inside comments. Only code-level matches count.
5. **If the path or line is wrong**, find the actual coordinates. The bug
   may still exist — just not where the issue says it does.

**Verification rule of thumb:** A listed bug is "already fixed" only if
every code-level occurrence of the broken pattern is gone. If even one
code-level occurrence exists anywhere, the bug is still open.

**Useful verification commands:**

```bash
# Check a specific pattern across all .src files
grep -rn '"char(10)"' <repo> --include="*.src" | grep -v '://'

# Check get_shell with parameters
grep -rEn 'get_shell\s*\(' <repo> --include="*.src" | grep -v 'get_shell$'

# Check import_code without .src extension
grep -rEn 'import_code\("[^"]+"\)' <repo> --include="*.src" | grep -v '\.src"'
```

### Step 5: Report a Structured Summary

After verification, organize findings into clear categories. Do NOT just say
"some were already fixed" — enumerate them.

**Primary categories (Variant A/B — issue-driven fix):**

- **Fixed (no action):** Bugs already handled on the branch. For each one,
  state the evidence (fix comment, git log, etc.).
- **Wrong coordinates:** Bugs where the stated file path or line number was
  incorrect. Say what the correct location is, if applicable.
- **Verified broken — fixed now:** The subset you actually edited, with the
  change applied.
- **Out-of-scope sibling bugs:** Additional bugs of the same families found
  during verification but not listed in the issue. Report with file:line.
  Do NOT silently fix or silently ignore — flag them for the user.

**Rich status taxonomy (Variant C — bug-catalog cross-mapping):**

When building a cross-map of a bug catalog against source code, use these
7 statuses. Each match gets exactly one status:

| Status | Meaning | Action |
|---|---|---|
| `present_fixed` | Bug was confirmed and already fixed in active source | Document the fix evidence (FIX comment, git log) |
| `present_partial` | Fix attempted but incomplete — code still has the pattern or risk remains | Document what was fixed and what wasn't |
| `present_unfixed` | Bug pattern still present in active source code | Flag for human fix, include exact line number |
| `imports_only` | Bug exists only in an imports/archive snapshot, not in active tree | Document snapshot path; check if active tree has a clean replacement |
| `doc_only` | Bug is only referenced in a catalog/report file, with no corresponding source file anywhere | Note which catalog file and line; source file may have been deleted or never ported |
| `present_documented` | Bug pattern exists but only in code comments (documentation, not executable code) | Verify no code-level match; if clean, note as non-issue |
| `absent_in_active_tree` | Referenced file or function does not exist in active source tree | Search archives/imports; flag if active tree needs it |

**Output format recommendation (cross-map only):** JSON with bug-key as
top-level keys and arrays of match objects:

```json
{
  "NP-49": [
    {
      "file": "path/to/file.src",
      "line": 9,
      "context": "One-line context excerpt",
      "status": "present_fixed"
    }
  ]
}
```

Each match object includes the line, a one-line context excerpt, and the
status. This is machine-parseable for integration with dashboards, issue
trackers, or the next verification pass.

### Step 6: Fix Only the Verified-Broken Subset

Apply mechanical fixes only to what was confirmed broken at verified
coordinates. Do not touch already-fixed code, even if the issue claims
it needs fixing.

1. Use `patch(mode='replace')` for minimal, targeted changes
2. Verify the change with a follow-up `read_file`
3. **Write a regression test** that asserts the exact bug symptom is gone.
   The test must go RED on the old code and GREEN on the new code. Prefer
   pytest tmp_path fixtures for hermetic file-based inputs.
4. **Run the regression test** alone first to confirm it catches the fix.
5. **Run the full existing test suite** to confirm no regressions from this
   single fix.
6. If instructed not to commit/push, leave changes unstaged.
7. **Only then** mark the bug as done and move to the next one.

**Why regression tests after each fix (not all at once):**
- Each fix is independently verifiable — when a later test suite run fails,
  you know the last fix caused it, not some earlier one.
- The test represents the bug's exact contract — future changes that reintroduce
  the symptom will be caught immediately.
- Cumulative evidence: the final report shows N bugs fixed and N+M tests green.

### Step 7: Record Sibling Bugs (Out-of-Scope)

If verification reveals additional bugs of the same families outside the
issue's scope:

- List them in the summary as a separate section
- Do NOT fix them unless explicitly asked
- Let the user decide whether to create a follow-up issue

This respects the scope boundary while surfacing valuable context.

### Step 8: Batch Final Verification

After ALL fixes and their individual regression tests are applied, run the
**complete test suite** one final time. This catches interaction regressions
— cases where Fix A didn't break anything alone but breaks when combined
with Fix B's data state change.

```bash
cd <project-dir>
pytest tests/ -v 2>&1 | tail -15
```

The batch verification output is the **only** admissible evidence in the final
report. Individual "it worked after the fix" claims from Step 6 loop are not
sufficient — the final green run is the deliverable.

Report the result as: `M passed / N total (P regressions)` where M, N, P come
from the actual terminal output, not from memory or intermediate checks.

## Variant B: Priority-Ordered Fix Loop

Use this variant when bugs arrive **pre-sorted by severity** (HIGH / MED / LOW
with reproducible repro commands for each) rather than as a raw issue list.
This is the Yuno default for explicit fix-loop runs (e.g. Verifier output).

**Key difference from the main workflow:** Do NOT verify all bugs before fixing
any. Instead, fix in priority order: reproduce → fix → add test → next.
This gets the highest-value fixes applied fastest and surfaces blocking
questions early.

### Step 1: Build a Todo List with Priority

Create a `todo()` list ordered by severity: all HIGH first, then MED, then LOW.
Each entry says what the bug is and the one-line repro command:

```json
[
  {"id": "1", "content": "Fix Bug #2: fmean crashes on NaN/Inf", "status": "pending"},
  {"id": "2", "content": "Fix Bug #3: ragged-row detector broken", "status": "pending"},
]
```

### Step 2: Per-Bug Cycle (Repeat for Each Bug in Priority Order)

For each bug, run this tight loop:

1. **Reproduce** — Run the Verifier's repro command or build your own.
   Confirm it's red (exhibits the bug). Takes 1 terminal call.
2. **Root cause** — Read the relevant code. Identify the exact line/pattern
   causing the symptom. Takes 1–2 read_file calls.
3. **Fix** — Apply the minimal change via `patch(mode='replace')`. One call
   per bug.
4. **Re-run repro** — Confirm the repro command is now green. One call.
5. **Write regression test** — Add a pytest test to the test suite that
   asserts the exact bug symptom is resolved:
   - Use `tmp_path` fixtures for hermetic file-based inputs
   - Assert on exit code, stdout content, and stderr (no "Traceback")
   - The test must be RED on old code, GREEN on new code
6. **Run the full suite** — Confirm no regressions from this single fix.
   `pytest tests/ -q` — one call.
7. **Mark todo completed** — Only now.

**Important:** Do NOT batch marks. Each bug gets its own fix → test → verify
cycle. `todo` status transitions from `in_progress` → `completed` only after
a real tool-call produced evidence (test output, file diff, etc.).

### Step 3: Batch Final Verification

After the last bug is fixed and its regression test passes, run the full
test suite one last time as the **definitive evidence** for the report.
Report exact counts from terminal output: M passed / N total.

### When to switch back to Variant A

- Bug list covers multiple repos → you need Variant A's path-mapping first
- Bugs have stale coordinates (file:line from an old release) → Variant A's
  verification comes BEFORE fixing
- Branch may have partial fixes already → you need Variant A's partial-fix
  detection first
- The fix is in GreyScript / unusual language → Variant A's grep patterns apply

When in doubt: **Variant A for stale/uncertain inputs, Variant B for verified
fresh inputs with clean repros.**

## Variant C: Bug-Catalog Cross-Mapping

Use this variant when your task is to **cross-map a curated bug catalog**
(not a one-time issue) against current source code, producing a structured
inventory of what's fixed, what's still broken, and what no longer exists.

This is a **verification-only variant** — do NOT fix any bugs during the
cross-map. The output is a map, not a patch set.

**When to use Variant C:**
- You have a bug-catalog file (e.g. `bug-reports/2026-06-17.md`) listing
  known bugs with file:line references
- The catalog may reference files from an older snapshot or a different
  branch structure than the active tree
- You need to produce a JSON cross-map for tracking or dashboard purposes
- The goal is status classification, not bug fixing

### Step 1: Inventory All Catalog Entries

Read the bug catalog end-to-end first. Extract each bug's key, its
referenced file paths, and the stated line numbers or patterns:

```bash
grep -rn "BUG\|FIX\|char(10)" <catalog-path> | head -40
```

Build a checklist of all referenced files. Note which are expected in the
active tree, which come from imports/archives, and which reference files
that may not exist at all.

### Step 2: Identify All Source Targets

A bug catalog can reference multiple generations of source code:

| Target | What it is | How to find it |
|---|---|---|
| **Active tree** | The current working source | `find <repo-root> -name "*.src" \| grep -v "/backups/"` |
| **Imports snapshot** | A frozen copy at a specific date | Look for `imports/greyhack-tools-<date>[TZ]/` directories |
| **Bug reports only** | Bug cited in catalog, file never existed in source | No grep — only catalog content |
| **Deleted/renamed** | File existed in past but is gone from both active + imports | Search git history |

Grep each target independently — a file that doesn't exist in the active
tree may still have relevant code in an imports snapshot.

### Step 3: Per-Bug Verification (No Fixing)

For every bug in the catalog, run this checklist:

1. **Find the source** — Search both active tree and imports snapshot.
   Does the stated file exist at either location?
2. **Read the line context** — The catalog says line N, but read ±5 lines
   around N. The actual bug pattern may have drifted.
3. **Search for fix markers** — Look for FIX comments referencing the bug
   key: `FIX NP-49`, `// FIX BUG F-1`, `FIX B-04`, `FIX D-PATTERN-i`.
   A fix marker means intentional correction was applied.
4. **Check for the bug pattern itself** — Grep the active tree for the
   broken pattern. A fix comment may claim the bug is fixed but the
   pattern may still exist elsewhere (partial fix).
5. **Distinguish comment from code** — A grep hit inside a `//` comment
   is documentation, not a live bug. Only code-level matches count.
6. **Assign a status** — Use the 7-category taxonomy from Step 5.

**Useful grep patterns for GreyScript bug catalogs:**

```bash
# Fix markers by variant
grep -rn "FIX NP-\|FIX BUG\|FIX B-\|FIX D-PATTERN" <repo> --include="*.src"

# Literal string vs function call (the classic char(10) bug family)
grep -rn '"char(10)"' <repo> --include="*.src"     # literal string — bug
grep -rn 'char(10)' <repo> --include="*.src"       # function call — ok, but also matches the bug above

# Hardcoded paths
grep -rn '"/home/' <repo> --include="*.src" | grep -v '//'

# rnd without seed (non-deterministic)
grep -rn 'rnd' <repo> --include="*.src" | grep -v '//'

# No-op self-assignment
grep -rn 'self = self' <repo> --include="*.src" | grep -v '//'
```

### Step 4: Organise Into Multi-Target JSON

Each bug-key gets an array of match objects, one per file-location where
evidence was found. A single bug may have matches in BOTH the active tree
AND the imports snapshot — include both:

```json
{
  "NP-49": [
    {
      "file": "greyhack-tools/bootstrap/bootstrap.src",
      "line": 9,
      "context": "// HINWEIS: HTTP.Request existiert NICHT in GreyScript.",
      "status": "present_fixed"
    },
    {
      "file": "greyhack-tools/hermes/hermes_api.src",
      "line": 7,
      "context": "// Vanilla GreyScript hat kein HTTP.Request() und kein JSON.Parse().",
      "status": "present_documented"
    }
  ]
}
```

### Step 5: Report Status Distribution

After all bugs are classified, produce a summary:

```
Status distribution (57 total matches):
  present_fixed:   27
  present_partial:  15
  present_unfixed:   5
  imports_only:      4
  doc_only:          3
  present_documented: 2
  absent_in_active_tree: 1
```

List **unfixed bugs needing human follow-up** separately — these are the
action items the catalog owner cares about most. Include exact file:line.

List **source reconciliation items** — bugs where the referenced file
doesn't exist in the active tree. The catalog may need updating (stale
entries) or the source may need porting (missing files).

### When to switch back to Variant A or B

- User asks you to FIX the bugs after seeing the cross-map → Variant B
- Bugs have stale coordinates (catalog is from 4 months ago) → Variant A
  (verify all before fixing any)
- You need to apply patches → go back to the main Workflow (Step 6+)

## References

- `references/fix-loop-reproduction.md` — Concrete fix patterns from a real
  Verifier session: math.isfinite for NaN/Inf, csv.reader for ragged rows,
  argparse type=validators, ascii-bar truncation. Browse for technique
  inspiration when facing the same bug families.
- `references/bug-catalog-cross-map.md` — Concrete bug-catalog cross-map
  methodology from a real GreyHack session. Covers the 7-status taxonomy,
  multi-target grep patterns, and fix-marker catalog for GreyScript projects.

## Pitfalls

### Issue Paths Are Not the Repo Truth

The most common pitfall: the issue says `bin/ps.src` and you spend 10
calls searching for it before realizing the repo has `tools/ps/ps.src`.
Always read the repo root first — it costs one `ls` call.

### Comments Mask as Bugs (False Positive)

A grep for `"char(10)"` will match both:
- `// FIX: split("char(10)") was wrong — corrected 2026-07-04`
- `cache_file_content.split("char(10)")  // still broken`

Only the second one is a real bug. Always verify the match is in code,
not a comment.

### Fix-Comments Signal Fixes, Not Stale Code

If a file has `// FIX NP-49` or `// FIX BUG F-1` in its comment block,
the fix was already applied. Do not re-apply it. The presence of a
documentation comment about a bug means the bug is already corrected.

### Line Number Drift

Issue line numbers are never trustworthy after the first commit on a
branch. Always read the actual line content at the stated position,
then search for the pattern independently.

### The Sibling-Bug Dilemma

When you find 9 out-of-scope bugs of the same families, you have two
bad options: (a) fix them and expand scope without asking, or (b) say
nothing and leave them unfixed. The correct answer is (c): report them
and let the user decide. Do not pick (a) or (b).

### Todo-Execution Dicipline

Do NOT mark a bug as `todo(status="completed")` without an intervening
tool-call (read_file, terminal with test output, patch, etc.). The
`todo` tracker is not a "done in my head" tool. Mark `completed` only
after real evidence exists on disk or in terminal output.

### Multi-Source Verification (Imports/Archive Snapshots)

When a bug catalog references files that could live in multiple places
(active tree, imports/ snapshot, or deleted), search ALL targets before
concluding a file "doesn't exist." A bug may be:

- **Fixed in active tree** but still broken in the imports snapshot
  → The catalog entry is stale; mark `present_fixed` in the active tree
- **Broken only in imports snapshot** (file gone from active tree)
  → Mark `imports_only`; the active tree may have a clean replacement
- **Cited but never in source** (only in `bug-reports/` catalog)
  → Mark `doc_only`; the file was never ported or never existed

Common convention: imports snapshots live at
`<repo>/imports/<project>-<datetime>/` or `<repo>/vendor/`. Always check:

```bash
find <repo> -maxdepth 3 -type d -name "imports" 2>/dev/null
ls -la <repo>/imports/ 2>/dev/null
```

**Key rule:** Do not silently skip a bug because it's in a non-active
snapshot. The catalog says it exists somewhere — it's your job to find
where, even if that place isn't the main source tree.

## Related Skills

- `systematic-debugging` — The parent discipline: find unknown bugs.
  This skill handles the special case of bugs already *described* by
  an issue but whose description may be stale.
- `github-issues` — Create/triage/manage the issues that produce these
  fix lists.
- `greyscript-compiler-debugging` — GreyScript-specific bug patterns
  and fix recipes. Load alongside this skill when the bugs are in .src files.
- `ki-murks-verhindern` — Quality gates for agent workflows. Verification
  is a quality gate; this skill is one specific gate implementation.
