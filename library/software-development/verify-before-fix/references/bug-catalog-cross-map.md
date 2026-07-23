# Bug-Catalog Cross-Map Reference

Concrete methodology extracted from a real GreyHack bug-catalog-to-source
cross-map session (2026-07-14). Use this as technique inspiration when
facing the same class of task in other projects.

## Session Context

- **Bug catalog:** `greyhack-tools/bug-reports/2026-06-17.md` — 14 known
  persistent bugs with file:line references and severity ratings
- **Active source:** `greyhack-tools/` subdirectory of
  `/home/bratan/10-Projekte/10-active/greyhack-tools/`
- **Imports snapshot:** `imports/greyhack-tools-20260613T144257Z/`
- **Goal:** Produce a JSON cross-map classifying each bug's status against
  current source, NOT fixing anything
- **Output:** 13,467 bytes, 57 matches across 14 bug-keys, 7 status categories

## The 7-Status Taxonomy (In Order of Desirability)

When mapping catalog bugs against source, every match gets exactly one
status. These let a downstream consumer (human or dashboard) filter by
actionability:

| Status | What it means | Action required |
|---|---|---|
| `present_fixed` | Bug confirmed present in source, intentional fix visible | Document fix marker + file:line |
| `present_partial` | Fix applied but incomplete (guard/floor/hack but risky edge cases remain) | Flag remaining risk; fix needs revisiting |
| `present_unfixed` | Bug pattern still live in active source code | Highest-actionability item |
| `imports_only` | Bug exists only in an imports/archive snapshot, NOT in active tree | Check if active tree has a replacement; update catalog |
| `doc_only` | Bug only cited in `bug-reports/` — the referenced file doesn't exist anywhere | Close as won't-fix or port the file |
| `present_documented` | Bug pattern exists but only inside code comments (not executable) | Non-issue; note for audit trail |
| `absent_in_active_tree` | Referenced file/function entirely missing from active source | Investigate whether this is intentional deletion or accidental omission |

### How to Assign Status — Decision Tree

```
Is the referenced file in the active tree?
  ├─ YES → Does the bug pattern still appear in executable code?
  │         ├─ NO  → Is there a fix marker (FIX B-04, FIX BUG F-1, etc.)?
  │         │         ├─ YES → `present_fixed`
  │         │         └─ NO  → Bug pattern gone but no marker found → `present_fixed`
  │         ├─ YES, but with a guard/floor/workaround → `present_partial`
  │         └─ YES, unguarded → `present_unfixed`
  │
  └─ NO  → Is the file in an imports/snapshot directory?
            ├─ YES → `imports_only`
            └─ NO  → Is the bug only cited in the catalog file itself?
                      ├─ YES → `doc_only`
                      └─ NO  → `absent_in_active_tree`
```

## GreyScript Fix-Markers Found in This Session

These are the fix-marker conventions used by the GreyHack tools project.
Load `greyscript-compiler-debugging` alongside `verify-before-fix` when
working on GreyScript .src files. Grep for these markers early to
understand what's already been attempted:

| Marker | Where found | What it fixes |
|---|---|---|
| `FIX B-04` | `getShell.src:36` | Null-pointer crash on `file = null` → has_permission |
| `FIX B-07` | `mapLAN.src:17` | Inverted condition (`!= -1` → `== -1`) causing duplicate insertion |
| `FIX B-11` | `grsa.src:110,125` | Float-index on list (`rnd` → `floor(rnd * len)`) |
| `FIX B-23` | `hermes_daemon.src:12,305-307` | Null-guard on `user_input()` (EOF/Signal crash) |
| `FIX BUG F-1` | `forcer.src:36` | Split on literal `"char(10)"` string vs `char(10)` newline |
| `FIX D-PATTERN-i` | `hermes_daemon.src:176` | `cmd.trim()` doesn't exist in GreyScript; manual trim-loop |
| `FIX M-1, M-2, M-3` | `metaxploit.src` (comments only) | Hardcoded paths — fix documented but NOT applied |

## GreyScript-Specific Grep Patterns

These patterns target the specific bug families found in the GreyHack
catalog. Adjust filenames and include patterns for your project:

```bash
# === Fix markers (find all intentional fixes at once) ===
grep -rn "FIX\|// Fixed" <repo> --include="*.src" | grep -v "FIX.*comment\|FIX.*pattern"

# === NP-49: HTTP.Request non-existence ===
grep -rn "HTTP\.Request" <repo> --include="*.src"

# === GH-KB-07: Literal "char(10)" vs function char(10) ===
grep -rn '"char(10)"' <repo> --include="*.src"      # literal string → bug pattern
grep -rn 'split(char(10))' <repo> --include="*.src"  # correct usage

# === GH-KB-08: Variable scope/cache pollution ===
grep -rn 'cache_file_content\|cache_file\.' <repo> --include="*.src" | grep -v '//'

# === GH-KB-10: Hardcoded paths ===
grep -rn '"/home/' <repo> --include="*.src" | grep -v '//' | grep -v 'git\|import_code'

# === NP-52/GH-KB-09: Unseeded rnd ===
grep -rn 'rnd' <repo> --include="*.src" | grep -v '//'

# === NP-24+22: No-op self-assignment ===
grep -rn 'self = self' <repo> --include="*.src" | grep -v '//'

# === NP-26: str(item) dedup-key collision ===
grep -rn 'str(item)' <repo> --include="*.src" | grep -v '//'

# === User input without null guard ===
grep -rn 'user_input(' <repo> --include="*.src" | grep -v 'null\|//'

# === Keyword-override risk (e.g. `pass` as variable name) ===
grep -rn '\bpass\b' <repo> --include="*.src" | grep -v '//\|password\|"pass"'
```

## Multi-Source Inventory Commands

When the catalog references files from multiple source generations:

```bash
# Check what's in the active tree
find <repo>/greyhack-tools -name "*.src" | grep -v "/backups/" | sort > /tmp/active-files.txt

# Check what's in the imports snapshot
find <repo>/imports -name "*.src" | sort > /tmp/imports-files.txt

# Compare: which files exist in imports but NOT in active
comm -13 /tmp/active-files.txt /tmp/imports-files.txt | grep 'greyhack'

# Files referenced by the catalog that exist in neither
# Then search each catalog file:line reference against both lists
wc -l /tmp/active-files.txt /tmp/imports-files.txt
```

## Output Format

The deliverable is a single JSON file with bug-keys as top-level keys,
each containing an array of match objects. The same bug may have matches
in BOTH the active tree AND the imports snapshot:

```json
{
  "NP-49": [
    {
      "file": "greyhack-tools/bootstrap/bootstrap.src",
      "line": 9,
      "context": "// HINWEIS: HTTP.Request existiert NICHT in GreyScript. (Pattern l — fix 2026-07-07)",
      "status": "present_fixed"
    },
    {
      "file": "greyhack-tools/hermes/hermes_api.src",
      "line": 7,
      "context": "// Vanilla GreyScript hat kein HTTP.Request() und kein JSON.Parse().",
      "status": "present_documented"
    }
  ],
  "NP-50+GH-KB-08": [
    {
      "file": "imports/greyhack-tools-20260613T144257Z/decypher/decypher_v3.src",
      "line": 85,
      "context": "if cache_file_content and cache_file_content.len > 79900 then — cache-scope variable bug",
      "status": "imports_only"
    },
    {
      "file": "greyhack-tools/decypher/decypher.src",
      "line": 1,
      "context": "//command: decypher — active tree, no v3 cache-scope logic",
      "status": "absent_in_active_tree"
    }
  ]
}
```

Validate the JSON before delivery:

```bash
python3 -c "import json; json.load(open('output.json')); print('valid')"
```

## Summary Stats (from the real session)

Run this analysis after classification:

```bash
python3 -c "
import json
from collections import Counter
data = json.load(open('output.json'))
print(f'distinct_bug_keys: {len(data)}')
total = sum(len(v) for v in data.values())
print(f'total_matches: {total}')
status_counter = Counter()
for k,v in data.items():
    for m in v:
        status_counter[m['status']] += 1
for s,c in status_counter.most_common():
    print(f'  {s}: {c}')
zero = [k for k,v in data.items() if len(v) == 0]
print(f'zero-match bugs: {zero}')
"
```

## Pitfalls Specific to Bug-Catalog Cross-Mapping

### The File-Exists-Nowhere Trap

A catalog entry like `deploy_all.src:63` that you cannot find in the
active tree OR the imports snapshot is NOT an error on your part —
it means the file was purposefully removed or never existed in this
repo version. Mark it `doc_only` and move on. Do NOT create the file
to fulfill the catalog's expectations.

### One Bug, Multiple Statuses

A single bug-key can legitimately produce two different statuses when
the same bug appears in different source targets:
- `present_fixed` in the active tree (fix applied)
- `imports_only` in the snapshot (still broken in the old version)

Both go in the same JSON entry with different statuses. This correctly
represents reality: "fixed where it matters, still broken in the archive."

### Comment-Only Fixes

Some files have extensive FIX comments describing what should be done
but never actually applying the fix. `metaxploit.src` in this session
had `FIX M-1, M-2, M-3` comments describing hardcoded-path fixes that
were never applied. Distinguish: a `// FIX` comment describing the fix
is `present_unfixed` (the description is documentation, the bug is live).
A `// FIX BUG F-1: ... corrected` comment describing what WAS changed
is `present_fixed` (the correction was documented and applied).

**Test:** Can you find the broken pattern in executable code? Yes →
`present_unfixed` or `present_partial`. No → `present_fixed` or
`present_documented` (check if it was in comments only).

### The Imports-Snapshot Blindspot

When a file exists ONLY in the imports snapshot and NOT in the active
tree, there are two fundamentally different scenarios:

1. **Clean rewrite** — The active tree has a fresh `decypher.src` that
   doesn't have the `decypher_v3.src` cache-scope bug at all because the
   feature was redesigned. Mark the v3 bug as `imports_only` in the snapshot
   and `absent_in_active_tree` in the active tree.
2. **Missing port** — The active tree is supposed to have the file but
   it was accidentally lost during a restructure. Flag for human follow-up.

Distinguish by reading the active tree's equivalent file (if any). A
completely different implementation suggests scenario 1. A `TO DO` comment
or FIXME suggests scenario 2.

## Related Skills

- `greyscript-compiler-debugging` — GreyScript-specific bug patterns, fix
  recipes, and compiler error interpretation. Load alongside this skill
  when the bugs are in .src files.
- `systematic-debugging` — The parent discipline. Use when the task is
  finding NEW bugs, not mapping a known catalog.
- `codebase-inspection` — pygount-based LOC and language analysis. Use
  when you need a structural overview before diving into the cross-map.