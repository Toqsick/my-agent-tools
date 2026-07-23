# Pattern (d) Single-Quote Cleanup in `.src` Files

**Added 2026-07-07** after Agent-B sweep over `greyhack-tools/` repository.
**Related triggers**: `pattern (d) single-quote`, `single quote code-vs-user pattern`, `char(39) inner apostrophe`.

---

## The core gotcha

GreyScript has **no string escape mechanism**. The only way to embed a quote character inside a quoted string is `char(34)` (for `"`) or `char(39)` (for `'`). Therefore, when you see a `'foo'` substring inside an outer `"..."`-string, that single quote is a **literal apostrophe in the data** — NOT a delimiter that can be flipped to `"foo"`.

**Concrete break (would fail to compile)**:
```
"expect -c 'spawn /bin/sh'"   →   "expect -c "spawn /bin/sh""   ❌ unterminated string
```

## 4-Bucket Classification (mandatory before any sweep)

Every `'`-character must be classified before deciding to change it. Mechanical `grep -c "'"` over a directory gives the WRONG number — it counts every literal apostrophe, not every code-context delimiter.

| Bucket | Pattern shape | Example | Action |
|--------|--------------|---------|--------|
| **CODE-CONTEXT** (single quote IS the delimiter) | `= '...'`, `== '...'`, `['...']`, `('...')` | `if x == 'foo'` | ✅ Replace with `"foo"` |
| **NESTED-DATA** (`'` inside outer `"..."`) | `"outer 'inner' more"` | `"vim -c ':!/bin/sh'"`, `"gdb -ex '!sh'"`, `"rsync -e '/bin/sh'"` | ❌ LEAVE — string has no escape; converting breaks syntax |
| **USER-FACING** (text inside `print()`/`warn()`/`info()`) | `print("... 'word' ...")` | `print("Verwende 'local' um ...")`, assertion labels like `"split_parent_file: folder = '/'"` | ❌ LEAVE — user-visible style |
| **COMMENT** (`'` inside `//` comment) | `// ... '...' ...` | `// vorletztes = 's'`, `// Bratan's Arsenal` | ❌ LEAVE — irrelevant at runtime |

## The fix-menu for code-context hits

When Pattern (d) legitimately flags a single-quote-delimited string that **must** be converted (e.g. linter wants double-quotes for consistency):

```greybel
// Before:
name = 'foo'
if x == 'bar' then ...

// After (option A — direct swap, when no nested quotes):
name = "foo"
if x == "bar" then ...

// After (option B — char() substitution, when output must contain apostrophes):
msg = "It's a " + char(34) + "test" + char(34)   // "It's a \"test\""
```

For SHELL-COMMAND data stored in `cmd`/`description` fields (like `suid_exploit.src`), keep the literal single-quote form — that's actually shell-correct quoting (`vim -c ':!sh'`, `gdb -ex '!sh'`, `sqlite3 -cmd '.shell /bin/sh'`).

## Verification protocol

Before AND after any edits:

```bash
greybel build <file.src> /tmp/build-test-<basename> -dbf
# expected output: "Build done. Available in /tmp/build-test-<basename>."
```

If a file is part of an In-Game tool (e.g. `launcher.src` with `import_code("/home/Bratan/bin/lib_core")`), the greybel build will fail at dependency-resolution with a message like:
```
Build error: Dependency .../home/Bratan/bin/lib_core does not exist... at launcher.src:7:1
```
This is **NOT** a single-quote issue — it's a virtual In-Game path that doesn't exist on the host filesystem. Document it but don't conflate it with Pattern (d).

## Backup before sweep

```bash
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p /tmp/backups-pattern-d-$TS
cp <file>.src /tmp/backups-pattern-d-$TS/<file>.src.bak-$TS
```

## Case study: 2026-07-07 Agent-B sweep

User-supplied counts (mechanical grep):
- `src/tools/suid_exploit.src`: **5 funde**
- `tests/test_grsa.src`: **3 funde**
- `tests/test_decypher.src`: **3 funde**
- `tests/test_libcore.src`: **2 funde**
- `src/core/debugcore.src`: **1 fund**
- `greyhack-tools/launcher/launcher.src`: **1 fund**

Real character-by-character classification yielded **21** `'`-characters across the 6 files. After 4-bucket classification:

| File | Mechanical count | True CODE-CONTEXT count | Action taken |
|------|-----------------|------------------------|--------------|
| suid_exploit.src | 5 (claimed) / 9 (actual `'`-chars) | 0 | None — all NESTED-DATA or USER-FACING or COMMENT |
| test_grsa.src | 3 | 0 | None — all USER-FACING in `print()` assertion labels |
| test_decypher.src | 3 | 0 | None — all USER-FACING in `print()` assertion labels |
| test_libcore.src | 2 | 0 | None — all USER-FACING in `print()` assertion labels |
| debugcore.src | 1 | 0 | None — USER-FACING in `warn()` |
| launcher.src | 1 (claimed) / 3 (actual) | 0 | None — COMMENT + USER-FACING |

**Result**: Zero replacements needed. The user's mechanical count was off by 21:0. All 21 hits were correctly classified as NOT-VERDÄCHTIG per the pattern rules.

## Lesson for future sweeps

**Never trust a mechanical character count for code-style sweeps.** Always:

1. Run `search_files` with regex `'[^']*'` or similar to get the true character positions.
2. For each hit, classify it into one of the 4 buckets above using `read_file` line context.
3. Only act on bucket 1 (CODE-CONTEXT).
4. Document every classification in the fix report (which bucket, why, what action).
5. Verify build before AND after each batch of edits.

This 5-step protocol prevents the most common failure mode of Pattern (d) sweeps: aggressive batch replacement that breaks strings containing literal apostrophes.