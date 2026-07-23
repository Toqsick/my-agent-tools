# Tool Migration Checklist — standalone .src → greyhack-tools tool directory

> Use when migrating a standalone GreyScript (.src) file into a named tool subdirectory
> under `greyhack-tools/` (e.g. `parse-exploit-reqs/`, `progress-bar/`).
> Replaces loosely-organized standalone scripts with structured tools: own directory,
> README, test suite, and live cross-references in the repo index docs.
>
> Working directory: `~/30-Library/greyscripts/greyhack-tools/`

## 1. Pre-flight: what's the source?

```bash
# Find the source file(s) and any existing test/docs
find ~/30-Library -name "*<toolname>*" -type f 2>/dev/null
ls -la standalone.md                                    # check if listed as standalone tool
ls -la docs/                                            # check for existing issue docs
```

Assumptions (check each before starting):
- The source file is a `.src` that builds and runs (or has known, non-blocking bugs).
- The source file is NOT embedded inside another tool's directory (already structured).
- The source file is in `standalone.md` or another index doc — verify before creating.

## 2. Read existing references

Before writing code, establish the expected style:

```bash
# Template: existing migrated tool for README/tests style
head -50 list-lib/README.md
head -50 list-lib/tests.src

# Conventions: tool count, current-phase in ROADMAP
head -10 README.md
grep -A1 -E '^\| parse-exploit.*\\|' NAVIGATION.md   # look for similar entry
grep -B2 -A2 'parse-exploit-reqs' ROADMAP.md           # find phase placement
```

## 3. Create the tool directory

```bash
cd ~/30-Library/greyscripts/greyhack-tools
mkdir -p <tool-name>
```

## 4. Write the cleaned `.src`

- **Copy source logic**, don't rewrite from scratch — avoid introducing new bugs.
- **Apply known bug fixes** (from bug-report/docs if available) as you go:
  - #29 — off-by-one in `range(N-1)` → `range(N)`
  - #30 — non-existent `.applyFunction()` → explicit `for` loop
  - #31 — unguarded `.split()[N]` access → validate length before indexing
- **Fix code-style issues** per migration rules:
  - Convert one-line `if condition then action` to multi-line `if cond then\n  body\nend if`
  - Remove negative list indices (`x[-1]` → `x[x.len - 1]`)
  - Replace ternary patterns (`cond ? X : Y`) with `if/else/end if`
- **Add function guard clauses:** `typeof()`, null-check, early return `[]` or `{}`.
- **Add header comment block** with:
  - Tool name, version
  - Repo / install source URL
  - One-line usage example
  - Dependency notes (`import_code("lib_core")`, `include_lib` requirements)

Pitfall: Don't over-clean. If a control-flow pattern (chained `else if`, `for i in range`, `continue`) already works in the existing codebase, it's verified — don't rewrite it just for style.

## 5. Write `README.md`

Follow the `list-lib/README.md` template structure:

```markdown
# ToolName

> One-line description of what it does.

## Features

- Bullet list of capabilities
- Focus on the *data flow*, not the implementation

## Functions (API)

### `functionName(argType) → returnType`

What the function does.

Parameters:
- `argName` (type) — description

Return value: type + description, null behavior

## Usage

\`\`\`
import_code("/home/Bratan/bin/lib_core")
...
\`\`\`

## Requirement Checks (if applicable)

| Code | Meaning |
|------|---------|
| `activeUser` | requires an active shell user |
| `registeredUsers:N` | requires N registered users |
| ... | ... |

## Known Issues

- If applicable, list known caveats or feature gaps.

## See Also

- List of related tools or dependencies
- Link to issue number in repo
```

## 6. Write `tests.src`

Test coverage rules:
- **Happy-path** for every function return type (string, list, map, empty)
- **Edge-cases:** empty input, null input, wrong type, malformed syntax
- **Multi-exploit blocks** (regression test for off-by-one bug #29)
- **Broken/malformed blocks** (regression test for unguarded split #31)
- **Requirement-type checks** for each supported requirement code

Test-file structure (use `assertEq` / `fail()` helpers):

```
// == Test: <short name> ==
// Input: <description>
// Expected: <expected result>
...

// == Edge-case: <name> ==
...

result = parseExploitRequirements("...")
assertEq(typeof(result), "map", "should return map")
...
```

**Pitfall:** Verify GreyScript-specific syntax in tests before committing:
- `indexes(map)` is a global function, not a property access in all contexts
- `hasIndex()` is a valid method on lists and maps
- `fail()` is a GreyScript built-in (aborts with error) — OK to use in tests
- List slices `list[1:]` work the same as string slices

## 7. Emulate tests (Python)

Before writing the test `.src`, run a Python emulation to validate the parsing logic:

```python
# Quick Python emulation of the GreyScript logic
# Spot-check each test case
def parse_exploit_requirements(...):
    ...
for i in range(tests.len):
    expected = ...
    actual = parse(...)
    assert actual == expected, f"Test {i+1} failed"
```

This catches logical errors that would otherwise only surface at build time.

## 8. Update index docs

### `NAVIGATION.md`

- If the tool name is already listed (dead link → existing entry): update the entry to `✅ implementiert, #N`
- If not listed: add in alphabetical order under the correct category heading
- Update the tool-count header (`N bestehende Tools` → `N+1 bestehende Tools`)

### `README.md` (top-level)

- Update tool count in the header and body: `35 Tools` → `36 Tools`, `55+ .src-Dateien` → `56+`
- The standalone count in `standalone.md` may need decrementing if this tool was previously standalone-only

### `ROADMAP.md`

- In the diagram section: replace `├─ <tool-name> (Parser)` with `├─ <tool-name> (Parser) ✅ #N`
- In the prose list: replace `- <tool-name> — description` with `- <tool-name> — description — ✅ fertig (Issue #N, YYYY-MM-DD)`

### `docs/ORDNER.md` (if applicable)

- Already lists the tool if the entry was created ahead-of-time — verify it's present, no update needed unless the description is stale.

## 9. Verify

```bash
cd ~/30-Library/greyscripts
git diff --stat greyhack-tools/<tool-name>/ greyhack-tools/NAVIGATION.md greyhack-tools/README.md ROADMAP.md
git diff greyhack-tools/NAVIGATION.md greyhack-tools/README.md ROADMAP.md

# Count new files
ls -la greyhack-tools/<tool-name>/

# Verify no one-line if/then or negative indices in the new .src
grep -nE 'then\s*$' <tool-name>/*.src | grep -v "end if"
grep -nE '\[\-' <tool-name>/*.src || echo "No negative indices"
```

## 10. Known issues / traps

- **Pre-existing unrelated changes** may be on the working branch — `git diff --stat` shows ALL diffs. Verify each file is intentionally yours.
- **ROADMAP header counts may be stale.** The diagram section may say `22 Tools` while `README.md` says `23+` — don't chase this inconsistency beyond what the issue dictates.
- **`standalone.md` removed-standalone logic:** If the tool was previously standalone, decrement the standalone count. But if the standalone.md entry says "DEPRECATED — will be removed when migration complete", leave it and only remove when all tools listed there are migrated.
- **Commas in NAVIGATION.md entries:** Existing entries in the markdown table lack trailing commas — follow the existing style (no trailing commas).
- **Do NOT commit or push** unless the task explicitly says so. Leave changes as working-tree modifications.
