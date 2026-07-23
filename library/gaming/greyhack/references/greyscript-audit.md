# GreyScript Deep Audit — Full Reference

Extracted from the `greyhack-greyscript-deep-audit` skill.

## Purpose
Systematic bug analysis for GreyScript community scripts. Goes beyond pattern scanning: control flow analysis, API verification, edge-case checking.

## Data Sources (Priority)
1. `~/Downloads/greyrepo/*/*.src` — Original community scripts
2. `~/greyhack-tools/*/*.src` — Curated tool collection

## Audit Workflow

### Phase 1: Pattern Scanning
Use proven grep recipes to find known bug patterns:
```bash
# From ~/greyhack-tools/
grep -rn 'split("char(10)")' --include="*.src"      # String literal in split()
grep -rn '"char(10)"' --include="*.src"              # String literal concatenation
grep -rn "indexOf.*== null\\|indexOf.*!= null" --include="*.src"
grep -rn 'get_content or ""' --include="*.src"
grep -rn '\.delete\b' --include="*.src"
grep -rn '\.is_folder' --include="*.src"
grep -rn '\.is_binary' --include="*.src"
grep -rn 'build.*== 1\b' --include="*.src"
grep -rn '\.chmod(600)\|\.chmod(700)\|\.chmod(755)' --include="*.src"
grep -rn 'catch\b' --include="*.src"
grep -rn 'while true' --include="*.src"
grep -rn 'str_repeat' --include="*.src"          # No str_repeat() in GreyScript
grep -rn 'file_ownership' --include="*.src"       # Wrong: use file.owner
grep -rn 'getcontent\\b' --include="*.src"         # Check for mixed API style
grep -rn 'user_input' --include="*.src"            # Check for null/EOF handling (NP-22)
grep -rn 'http://' --include="*.src"               # Hardcoded IPs/URLs (NP-23)
grep -rn 'self = self' --include="*.src"           # No-op self-assignment in closures (NP-24)
grep -rn 'str(item)\\|str(i)\\|str(key)' --include="*.src"  # Potential str() collision in dedup (NP-25)
grep -rn '^\\s*=======\\s*$' --include="*.src"       # Merge conflict marker — always a bug
grep -rn '\\\\n' --include="*.src"                # Literal \n in strings, not newline
grep -rn 'getcontent\\b' --include="*.src"         # Check for mixed API style
grep -rn 'user_input' --include="*.src"            # Check for null/EOF handling (NP-22)
grep -rn 'http://' --include="*.src"               # Hardcoded IPs/URLs (NP-23)
grep -rn 'self = self' --include="*.src"           # No-op self-assignment in closures (NP-24)
grep -rn 'str(item)\\|str(i)\\|str(key)' --include="*.src"  # Potential str() collision in dedup (NP-25)
grep -rn '^\\s*=======\\s*$' --include="*.src"       # Merge conflict marker — always a buge
grep -rn 'user_input' --include="*.src"            # Check for null/EOF handling (NP-22)
grep -rn 'http://' --include="*.src"               # Hardcoded IPs/URLs (NP-23)
grep -rn 'self = self' --include="*.src"           # No-op self-assignment in closures (NP-24)
grep -rn 'str(item)\\|str(i)\\|str(key)' --include="*.src"  # Potential str() collision in dedup (NP-25)
grep -rn '^\\s*=======\\s*$' --include="*.src"       # Merge conflict marker — always a bug

### Phase 1b: Control-Flow Balance Check
For each `.src` file, verify `if`/`end if`, `for`/`end for`, `while`/`end while` balance.
See **Control-Flow Balance Checking** section below for the correct counting methodology.
A naive count (all `if` vs all `end if`) will produce false positives from `else if` and single-line `if...then`.

### Phase 1c: Mixed API Style Check
Search for both underscore and no-underscore variants of the same API in a single file:
```bash
# Files using BOTH styles indicate a bad merge or incomplete refactor
for f in $(grep -rl 'get_content\b' --include="*.src" .); do
  if grep -q 'getcontent\b' "$f"; then
    echo "MIXED API: $f (get_content + getcontent)"
  fi
done
```
Correct GreyScript API uses **no underscore**: `getcontent`, `setcontent`, `getfiles`.
The underscore variants (`get_content`, `set_content`, `get_files`) are from MixedConvention layers or different codebases.

### Phase 2: Control Flow Analysis
For each script:
1. Trace all function entry/exit points
2. Check every API return value is handled
3. Verify error paths don't silently swallow
4. Check for infinite loops or missing exit conditions

### Phase 3: API Verification
Cross-reference every API call against the official GreyScript API:
- `Shell.build()` → returns File|String, NOT `1`
- `File.delete()` → returns null|String, NOT `1`
- `File.is_folder` → VALID but needs null-check
- `File.is_binary` → true for binaries, false for text AND folders
- `Metaxploit.overflow()` → always `typeof()` the result

### Phase 4: Edge Cases
- Empty lists: `range(0, len-1)` → `range(0, -1)` when len=0
- Null returns: `pc.File(path)` returns null if path doesn't exist
- Missing null-checks before `.is_folder`, `.get_content`, `.delete`
- String immutability: `s[0] = x` throws Runtime-Error

## Bug Categories (56 Total)
See `~/greyhack-tools/references/BUG-PATTERNS.md` for the full catalog.

Top categories:
1. `split("char(10)")` or `"char(10)"` in strings (HIGH) — string literal instead of `char(10)` function call
2. `\n` in strings (HIGH)
3. Explicit `self` param on map methods (MEDIUM)
4. `indexOf` returns `-1` (not `null`) when not found — compare with `== -1`, never `== null` (HIGH)
5. `get_content or ""` masking null errors (HIGH)
5. `shell.build() == 1` wrong return check (HIGH)
6. `File.chmod(600)` integer instead of string (MEDIUM)
7. `delete == 1` or `delete == null` wrong return check — correct: `== ""` (HIGH)
8. Silent catch blocks (MEDIUM)
9. `range(0, -1)` empty list edge case (MEDIUM)
10. `include_lib` no null-check (MEDIUM)
11. `HTTP.Request()` usage — does NOT exist in Vanilla GreyScript (HIGH)
12. **Mixed API underscore styles** — `get_content` vs `getcontent`, `set_content` vs `setcontent`, `get_files` vs `getfiles` in the same file. Indicates bad merge or incomplete refactor. Correct GreyScript API uses no underscore: `getcontent`, `setcontent`, `getfiles`. (HIGH)
13. **Merge conflict markers** — Raw Git merge artifacts (`<<<<<<<`, `=======`, `>>>>>>>`) in `.src` files. GreyScript cannot parse these. Always a bug. Often co-occurs with orphaned code fragments and mixed API styles. (CRITICAL)
14. **Inverted `is_binary` logic** — Using `if not f.is_binary then return` in a file-processing loop skips text files and only processes binaries. For ransomware/file tools this is backwards: text files (Bank.txt, Mail.txt, configs) are the primary targets. Check intent: if the tool should process text files, the condition should be `if f.is_binary then return` (skip binaries, process text). (HIGH)
15. **Weak password validation** — Only checking `password == ""` (empty) without complexity requirements. Weak passwords produce weak encryption. Also: passwords passed as plaintext function parameters may appear in logs. (MEDIUM)
16. **Resource cleanup gaps** — Cleanup functions (e.g., stopping monitor mode, closing connections) only called on one error path but not others. On failure paths between resource acquisition and cleanup call, the resource leaks. Ensure cleanup runs on ALL exit paths. (MEDIUM)
17. **Length-only input validation** — Checking `len(input) < N` without format validation. A string like `abcdefg` (7 chars) passes an IP length check. Always validate format (e.g., `validIP()`, regex) in addition to length. (MEDIUM)
| 18 | **Unbounded recursion on user input** — Recursive function calls (e.g., re-prompting for input on invalid entry) without a retry limit. Malicious or accidental repeated invalid input can cause stack overflow. Add a max-retry counter. (MEDIUM) |
| 19 | **`globals.x = value` does NOT create local `x`** — `globals.sh = get_shell` makes `sh` undefined. Use direct `shell = get_shell`. (HIGH) |
| 20 | **`is_folder` is unreliable** — Use `is_binary == false` for folders, `is_binary` for files. `is_folder` can return wrong results. (MEDIUM) |
| 21 | **No null-check before `.delete()`** — Calling `pc.File(path).delete` without first checking if `pc.File(path)` returns null. If the file doesn't exist, the null reference crashes. Always assign to a variable, check for null, then call `.delete()`. (HIGH) |
| 22 | **No EOF/null check on `user_input()`** — `user_input()` can return `null` (EOF, signal, pipe close). Calling `.trim()` on null crashes. Always check: `cmd = user_input(...); if not cmd then continue` or `if cmd == null then exit()`. (HIGH) |
| 23 | **Hardcoded IP addresses / ports** — IP addresses like `192.168.1.100:8765` hardcoded in source. Makes scripts non-portable and requires recompilation to change. Use command-line parameters or config files instead. (MEDIUM) |
| 24 | **`self = self` no-op in closures** — In GreyScript, `self = self` inside a nested function is a no-op. If the intent was to capture the outer `self` for use in a closure, GreyScript's scoping already provides it. The line is dead code and may indicate a misunderstood fix attempt. (LOW) |
| 25 | **`str(item)` collision in `unique()`** — Using `str(item)` as a deduplication key in `unique()` functions. Different types with the same string representation (e.g., `str(1)` and `str("1")` both produce `"1"`) are incorrectly treated as duplicates. Acceptable for same-type lists, but a latent bug for mixed-type lists. (LOW) |
| 26 | **Unescaped quotes in generated code strings** — When generating code as strings (e.g., in compilers or code generators), file paths or user content containing double quotes (`"`) break the generated code's syntax. Always escape or sanitize quotes in string interpolation contexts. (HIGH) |
| 27 | **Wrong type check: `is_binary` as folder detector** — Using `if folder.is_binary then` to check directories. `is_binary` checks content type, not folder status. Directories return `is_binary == true`. Correct: `if f.is_binary then skip` else treat as dir, with null-check first. (HIGH) |
| 28 | **chmod only on target, not contents** — Applying `chmod` to a folder after processing files inside. Files retain original permissions. Use recursive chmod to lock contents. (MEDIUM) |
| 29 | **Recursive user input without retry limit** — Recursive re-prompt on invalid input without max-retry counter. Add `retries` parameter with limit 3. (MEDIUM) |
| 30 | **Overly complex padding/string building** — Using array push loop + join + replace where string multiplication (`" " * n`) suffices. O(n²) vs O(1). Simplify. (LOW) |
| 31 | **touch() return misinterpretation (NP-42)** — Checking `pc.touch() != 1` or `== 1`. `touch()` returns `""` (empty string) on success, `null` on failure. Check `== null` for failure, not `!= 1`. Same applies to `delete()` which returns `""` on success. (HIGH) |
| 32 | **Empty field after split() (NP-43)** — Checking `split_result.len < 2` but not checking for empty strings. `":".split(":")` → `["", ""]` passes len check. Also validate individual fields are non-empty. (HIGH) |
| 33 | **Multi-line script via string concat (NP-44)** — Building shell scripts or multi-line content via `s = s + ...` in sequence. Use list + `join(char(10))` for O(n) construction. (MEDIUM) |

## Control-Flow Balance Checking (IF/FOR/WHILE)

When auditing `end if` / `end for` / `end while` mismatches, use this methodology:

### Step 1: Count raw occurrences
```
grep -c '^[\t ]*if\b' file.src        # all lines starting with "if"
grep -c '\bend if\b' file.src         # all "end if" (inline + multi-line)
grep -c '^[\t ]*else if\b' file.src   # "else if" branches
```

### Step 2: Count single-line `if...then` (no `end if` needed)
```
grep -c '^[\t ]*if\b.*\bthen\b' file.src
```

### Step 3: Compute the balance
```
standalone_if = raw_if_count - else_if_count - single_line_if_count
expected_end_if = standalone_if    # each multi-line if needs one end if
```
If `actual_end_if < expected_end_if` → **missing `end if` (real bug)**.
If `actual_end_if > expected_end_if` → **orphaned `end if` (real bug)** — a stray closing token with no matching block.

### Important
- Single-line `if cond then stmt` is **valid GreyScript** — no `end if` required.
- `else if` does **not** need its own `end if` — it shares the parent's `end if`.
- Apply the same logic for `for`/`end for` and `while`/`end while`.

### Verified example — ORPHANED end if (htop/script.src)
```
Line 32: if line.len < 5 then continue    ← single-line, no end if needed
Line 33: if not line[0] ... then continue ← single-line, no end if needed
Line 34: end if                          ← ORPHANED — no matching multi-line if
```
Diagnosis: `raw_if = 2`, `single_line_if = 2`, `standalone_if = 0`, but `actual_end_if = 1`. Since `actual_end_if > standalone_if`, there's a **stray `end if`**.

### Verified example — BALANCED (run_all.src)
```
raw_if = 2, else_if = 0, single_line_if = 1
standalone_if = 2 - 0 - 1 = 1
actual_end_if = 1  → balanced ✓
```

## Orphaned Code Block Detection

Beyond simple `if`/`end if` counting, watch for **orphaned code blocks** — remnants of incomplete refactors or bad merges where code exists outside any function or has dangling control flow. Signs:

- **Stray code between functions** — executable lines that aren't inside any `function...end_function` block (e.g., `// main` markers, raw `end if`/`return` with no matching block)
- **Mixed API conventions in same file** — see bug category 12 above
- **Inconsistent indentation within a block** — suggests copy-paste from different sources
- **`end if`/`end for`/`end while` without matching opening** — counted ends exceed computed standalone openings

When found, read the surrounding context (5-10 lines before/after) to determine if it's intentional scaffolding or a real merge artifact.

## Variable-Named-Function False Positives

When scanning for dangerous calls like `rm`, remember:
- **Variable assignment** `rm = fc_move(...)` is NOT a call to `rm()`.
- Only flag `rm(...)` with parentheses as a potential command invocation.
- Same applies to other shell commands used as variable names.
- **Test files** commonly use short variable names like `rm`, `rd`, `sz` for test results — always check context before flagging.
## Merge Conflict Artifact Detection

GreyScript files that have been through Git merges may contain raw merge conflict markers. These are **always bugs** — GreyScript has no concept of `<<<<<<<`, `=======`, `>>>>>>>` and will fail to parse them.

### Detection
```bash
grep -rn '^\s*=======\s*$' --include="*.src" ~/greyhack-tools/
grep -rn '^\s*<<<<<<<\s' --include="*.src" ~/greyhack-tools/
grep -rn '^\s*>>>>>>>\s' --include="*.src" ~/greyhack-tools/
```

### Verified example — filecore.src:264
```
263|end function
264|=======
265|// ── Verzeichnis anlegen ──────────────────────────────────────
```
The `=======` at line 264 is a raw Git merge separator. Lines 1–37 (old API fragment) and lines 39+ (new API) are two versions of the same file that were never properly merged. The file is **not compilable** in this state.

### Related: Orphaned Code Fragments
When merge markers are present, also check for **orphaned code blocks** — functions or code fragments that exist outside any proper structure:
- `safeWriteFile` (lines 30–37) is incomplete: missing `end if` after line 37 and missing `end function`
- `safeCopy` (lines 178–185) is incomplete: missing `end if` after line 184 and missing `end function`
- These fragments use the old underscore API (`get_content`, `set_content`) while the rest of the file uses no-underscore (`getcontent`, `setcontent`)

### Fix
Resolve the merge conflict: pick one version (preferably the new API), delete the old fragment and the `=======` marker, and ensure all control flow is balanced.

## Cron Job Constraints

### File List Command (CRITICAL)
```bash
# CORRECT — filters out backup directories:
find ~/greyhack-tools/ -name "*.src" | grep -v '/backups/' | sort

# WRONG — includes backup duplicates:
find ~/greyhack-tools/ -name "*.src" | sort
```

**The cron job MUST use `grep -v '/backups/'`.** Backups contain old snapshots with known bugs already fixed in active files. Scanning them produces only redundant context waste and duplicate findings. Even when the index counter includes backup files in the total count, skip them during actual analysis.

**IMPORTANT:** The `last-scan-index.txt` counter should track position in the *filtered* list (without backups), not the unfiltered list. If the unfiltered list is used for indexing, the scan will advance past backup files without scanning any active files, producing empty reports. Always build the file list with `grep -v '/backups/'` first, then use `sed -n 'N,N+10p'` to select the batch.

When running as scheduled cron:
- Use only file tools and terminal
- Don't ask questions — make reasonable decisions autonomously
- `write_file` max ~8K tokens per call
- `BUG-PATTERNS.md` is the authority — read first, append only genuinely new patterns
- **SKIP backup directories entirely** — filter with `grep -v '/backups/'` when building the file list. Backup files are duplicates of already-scanned active files and produce only redundant findings.
- **Preferred file list command**: `find ~/greyhack-tools/ -name "*.src" | grep -v '/backups/' | sort`
- **Patch tool encoding issue**: When patching German text (umlauts, ß, etc.) into markdown files, the patch tool may produce garbled/mojibaked characters. Always re-read patched lines to verify correctness and fix encoding corruption with a follow-up patch.

## Backup Directory Rule

**ALWAYS ignore `backups/` directories entirely.** They contain old snapshots with known bugs that have typically already been fixed in the active files. Scanning backups produces only false positives and wastes context. Before scanning, mentally exclude any path containing `backups/`.

**This applies even when the index counter includes backup files.** The `find | sort` pipeline naturally includes backups. The cron job MUST filter them with `grep -v '/backups/'` before selecting the next batch. If the unfiltered list is used, the scan will process duplicate files and produce redundant findings that waste the context window.

**Preferred file list command:**
```bash
find ~/greyhack-tools/ -name "*.src" | grep -v '/backups/' | sort
```

## Installer Code-Generation vs. Active Code Mismatch

The `installer/installer*.src` files generate code via `.push()` strings. The generated code may contain patterns (e.g., `\\n` instead of `char(10)`, `HTTP.Request`) that differ from the actual deployed files. When auditing:

1. **Audit the active/deployed file** (e.g., `hermes/hermes_daemon.src`), not just the installer that generates it.
2. If the installer generates buggy code but the deployed file is correct, the installer is **out of sync** — note it as a medium-priority finding (the installer would re-introduce the bug if re-run).
3. The `hermes_daemon.src` uses `char(10)` correctly despite the installer generating `\\n` — this means the deployed file was manually corrected after initial generation.

## Analysis Methodology: False Positive Triage

When a scan produces findings, **always read the actual code context** before classifying:

1. **For `.indexes`**: Check if the variable is a Map or Array. Read the function that creates/returns the variable. If it's a Map and the loop uses `map[key]`, it's correct. See "Known False Positives" above.
2. **For `indexOf == null`**: Always a real bug — `indexOf` returns `-1`, never `null`. No FP possible.
3. **For `"char(10)"`**: Always a real bug — string literal vs function call. No FP possible.
4. **For `exit` without code**: Check context — import guards (print error + exit) are OK; error paths in tools should use `exit(1)`.
5. **For `split()[N]`**: Check if there's a length guard (`if parts.len >= N+1`) before the index access. If not, it's a real bug.
6. **For `range(0, x.len - 1)`**: Always a real Off-by-One bug — the last element is skipped. Check if the intent is to skip the last element (rare).
7. **For `.values` on variables**: Check the variable type. `.values` does NOT exist on Strings in GreyScript — this is always a crash. Maps and Lists have `.values` but the semantics differ (Map.values = values, List.values = the list itself).

**Rule of thumb**: When in doubt, read 10 lines of context around the finding. A 30-second read prevents false positives that waste everyone's time.

## Known False Positives (Do NOT Report)

The scan pattern `for x in obj.indexes` is flagged as "Map-Keys statt Indizes" but is **correct GreyScript** when `obj` is a Map and the code uses the keys to access values:

```grey
// CORRECT — Map key iteration via .indexes
for port in snap.indexes
    print(snap[port])  // port is a key, snap[port] is the value
end for
```

**Do NOT flag** `.indexes` when:
- The variable is a Map (constructed with `{}` or populated with `map[key] = value`)
- The loop body uses the iterated variable as a key: `map[key]`
- Examples: `portmon.src` (snap/saved/before/after are Maps), `recon.src` (report["whois"] is a Map), `decypher.src` (counts is a Map), `gsc/Util.src` (addRange parameter), `minitest/runner.src` (tests is a Map of functions)

**Only flag** `.indexes` when the code expects **numeric indices** (0, 1, 2...) but the variable is a Map with non-numeric keys — this is rare in practice.

### `HTTP.Request` in Deprecated/Commented Code

These files reference `HTTP.Request` but are NOT bugs:

| File | Why it's safe |
|------|--------------|
| `hermes/hermes_api.src` | Fully deprecated — only prints deprecation message, zero API calls |
| `hermes/hermes_daemon.src` | `HTTP.Request` appears only in comments (lines 15, 243). Daemon uses file-based architecture by design |
| `installer/installer.src` | Code generation context — `.push()` strings that generate other files. The generated files (bootstrap.src) are the actual bug, not the installer itself |
| `installer/installer_part1.src` | Same as above — string generation context (line 821, 828) |
| `installer/installer_part2.src` | Same as above — string generation context (lines 24, 252) |
| `docs/*.md`, `references/*.md` | Documentation — not executable GreyScript |
| `backups/**` | Backup copies — ignore entirely |
| `tests/test_filecore.src` | `rm = fc_move(...)` at line 113 — variable named `rm`, not the `rm` command. Common in test files for short result variable names. **False positive.** |

**Rule:** Only flag `HTTP.Request` in files that are directly executed as GreyScript (`.src` files in `bootstrap/`, `src/`, `src/tools/`, `src/security/`, `src/crypto/`). When in doubt, check if the line is inside a `.push("...")` string literal — if so, it's code generation, not a direct call.

## Script-Specific Audit Notes

| File | Finding | Severity |
|------|---------|----------|
| `src/filecore.src` | Line 238: ` main` instead of `end if` — corrupted code fragment in `fc_delete()`. The `if typeof(res)` block at line 235 is never properly closed. Line 238 reads ` main` (likely a botched edit of `end if`). Combined with `=======` merge marker at line 264 and orphaned old-API fragments (lines 1–37, 149–186). File is **not compilable**. | CRITICAL |
| `src/filecore.src` | Lines 30–37: Orphaned `safeWriteFile` fragment — missing `end if` (after line 37) and missing `end function`. Uses old underscore API (`get_content`/`set_content`). Same file has working `fc_write` at line 123 with no-underscore API. Incomplete merge. | HIGH |
| `src/filecore.src` | Lines 178–185: Orphaned `safeCopy` fragment — missing `end if` (after line 184) and missing `end function`. Same pattern as `safeCopy` above. | HIGH |
| `src/filecore.src` | Dual API style: `getcontent`/`setcontent`/`getfiles` (no underscore, lines 113,145,313) mixed with `get_content`/`set_content`/`get_files` (underscore, lines 26,76). REF-FIX comments claim no-underscore is correct, but both coexist. Indicates incomplete refactor / bad merge. | MEDIUM |
| `forcer/forcer.src` | `split("char(10)")` at line 19 — string literal instead of `char(10)` function call. Splits on literal text "char(10)", not newline. | HIGH |
| `bootstrap/bootstrap.src` | `HTTP.Request()` called 4× directly (lines 36, 46, 95, 173). Not code generation, not in `.push()` — actual runtime calls that fail in Vanilla GreyScript. By design for Host-Terminal, but won't work in-game. | HIGH (context-dependent) |
| `launcher/launcher.src` | Line 134: `+ ")"` Tippfehler — should be `""` or removed. Cosmetic, not functional. | LOW |
| `src/security/hardening.src` | All `.delete()` calls properly null-checked. Clean control flow. All blocks balanced. | OK |
| `htop/script.src` (active, non-backup) | **CLEAN** — uses `char(10)` correctly (lines 28, 66). All `if`/`end if`, `for`/`end for`, `while`/`end while` balanced. Previous orphaned `end if` bug (backup version) has been fixed. | OK |
| `htop/script.src` (backup copies only) | Orphaned `end if` at line 34 in old snapshot. Already fixed in active file. **Ignore — backup only.** | N/A |
| `ransomeware/ransomeware.src` | Line 73: Inverted `is_binary` — `if not f.is_binary then return` skips all text files, only encrypts binaries. Backwards for ransomware. | HIGH |
| `ransomeware/ransomeware.src` | Lines 130-138: Password only checked for empty, no complexity validation. Password passed as plaintext parameter to encrypt/decrypt. | MEDIUM |
| `wifi_crack/wifi_crack.src` | Lines 64-77: `cleanup()` only called on `aireplay` error path. If `airecrack` (Z96) fails or `pc.File(captureFile)` (Z88) returns null, monitor mode stays active. | MEDIUM |
| `xmem/xmem.src` | Lines 245-252: MagicMenu input validation only checks string length, not format. IP `abcdefg` passes 7-char check. No hex validation for memory_address. | MEDIUM |
| `xmem/xmem.src` | Lines 180-185: `ShellConnect` calls itself recursively on invalid input with no retry limit — stack overflow risk. | MEDIUM |
| `ps/ps.src` | Line 24: `computer.show_procs` called without null-check on `computer` or result. Crash if show_procs fails. | MEDIUM |
| `ps/ps.src` | Lines 44-53, 60-69: String concatenation in loops (`r = r + ...`) — inefficient for large process lists. | LOW |
| `greyhack-tools/alias-cli/alias.src` | **FIXED in PR #18** — `globals.sh = get_shell` replaced with local `shell = get_shell`. `builder.build` was using `globals.sh.build()` which crashed. | FIXED |
| `greyhack-tools/dankestein/secure.src` | **FIXED in PR #18** — Single quotes in `print("can't access folders")` escaped. | FIXED |
| `greyhack-tools/lib_core/lib_core.src` | **FIXED in PR #18** — `is_folder` replaced with `is_binary` check in `getDir()`. | FIXED |
| `src/filecore.src` | **FIXED in PR #18** — `is_folder` replaced with `not is_binary` in `dirExists()`. **Still has** merge conflict marker at line 264 and orphaned fragments — these predate this fix. | PARTIAL |
| `deploy_all.src` | Line 14: Hardcoded IP `192.168.1.100:8765`. Line 63: `pc.File(local_src).delete` without null-check. | HIGH |
| `hermes/hermes_daemon.src` | Line 315: No null/EOF check on `user_input()` return value. Line 87: No path validation before `pc.touch(path)`. Log read-modify-write pattern (read entire file, append, write back) doesn't scale. | HIGH |
| `gsc/gsc.src` | Line 83: `self = self` no-op in `makeCurry`. Line 118: `makeStr` doesn't escape quotes in file paths — generates broken code for paths containing `"`. | MEDIUM |
| `gsc/Util.src` | Line 165: `str(item)` as dedup key in `unique()` — collision risk for different types with same string representation. | LOW |

## Output Format
Write audit report to `~/greyhack-tools/docs/BUG-REVIEW.md`:
- Script name + path
- Bug category number
- Line number
- Description
- Suggested fix
