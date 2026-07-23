# GreyScript Build-Error Reference (2026-07-07 Bug-Hunt)

Condensed error catalog from the 2026-07-07 bug-hunt session that took the repo from 41→71 OK.
Use this when a `greybel build` fails and the error is one of the patterns below.

## Pattern Catalog

### (a) one-line-if — CRITICAL (40+ files)
- **Error:** `no matching open if block at L<N>:<C>`
- **Cause:** `if X then Y end if` on one line — greybel 3.7.x parser can't tokenize it
- **Fix:** Expand to multi-line:
  ```greybel
  if X then
      Y
  end if
  ```
- **3 variants:** (1) pure `if then end if`, (2) statement-chain `if then Y; Z end if`, (3) combined `if then for... end for end if`
- **Regex guard:** `\bif\b.*\bthen\b.*\bend\s+if\b`

### (b) ternary expression — CRITICAL
- **Error:** `got Keyword 'else' where 'then' is required`
- **Cause:** `x = "OK" if cond else "FAIL"` — GreyScript has NO inline ternary
- **Fix:** Full if/else/end if block:
  ```greybel
  if cond then
      x = "OK"
  else
      x = "FAIL"
  end if
  ```
- **Regex guard:** `\bif\b.*\belse\b` (without preceding `then` and not `else if`)

### (c) try/catch end try — NOT SUPPORTED
- **Error:** `unexpected keyword 'end try' at start of line`
- **Cause:** Java/JS-habit `try { ... } catch { ... }`. GreyScript has no exceptions.
- **Fix:** Remove entire try/catch block. Replace with if/then/error-print:
  ```greybel
  result = someFunction()
  if result != "expected" then
      print("[ERROR] " + result)
  end if
  ```
- **Regex guard:** `\btry\b|\bcatch\b|\bend\s+try\b`

### (d) single-quote in code context
- **False-positive trap (2026-07-07):** `'...'` inside `"..."` strings is **nested data**, not a code-quote. GreyScript has no escape mechanism — `"vim -c ':!/bin/sh'"` can NOT become `"vim -c ":/bin/sh""`.
- **Only fix:** code-context `if x == 'foo'` or `name = 'bar'` → `if x == "foo"` / `name = "bar"`
- **Do NOT touch:** quotes inside `print("User text 'foo'")` (user-facing), inside `//` comments, or nested in outer DQ strings
- **Regex guard (true positives only):** `[\(\s,=]\s*'\w`

### (e) backslash escapes — NOT SUPPORTED
- **Error:** No compile error — runtime crash. `\"` or `\\` in strings = invalid char 92 at runtime.
- **Fix:** Use `char(34)` for `"`, `char(92)` for `\`, `char(10)` for newline:
  ```greybel
  // CRASHES:
  path = "C:\\Users\\"
  // WORKS:
  path = "C:" + char(92) + "Users" + char(92)
  ```
- **Regex guard:** `\\` in any DQ-string context → must be replaced

### (f) direct HTTP.Request — NOT SUPPORTED
- **Error:** No compile error — runtime fail: "undefined function HTTP.Request"
- **Fix:** Use `pc.wget(url, dst)` for file downloads. For API calls (Hermes on :8333), use file-queue pattern (`/home/hermes/hermes_request.txt` + `/home/hermes/hermes_response.txt`)
- **Regex guard:** `\bHTTP\.Request\b`

### (g) .strip()/.trim() — NOT SUPPORTED at runtime
- **Error:** No compile error — runtime crash: "Path 'trim' not found in string intrinsics"
- **Cause:** greybel mock-env compiles clean, but real GSH has no string .strip()/.trim()
- **Fix — manual trim-loop:**
  ```greybel
  trim = function(s)
      while s.len > 0 and s[0] == " "
          s = s[1:]
      end while
      while s.len > 0 and s[s.len-1] == " "
          s = s[:s.len-1]
      end while
      return s
  end function
  ```
- **Also fix bare references** like `parts[1].trim` (no parens = method reference, not call)
- **Regex guard:** `\.(strip|trim)\b`

### (h) absolute import_code paths
- **Error:** `Build error: Dependency /home/bratan/.../<tool>/home/Bratan/bin/lib_core does not exist`
- **Cause:** Files use in-game absolute paths like `import_code("/home/Bratan/bin/lib_core")` — greybel tries local resolution
- **Fix:** Convert to relative paths from the file's own directory:
  ```greybel
  // FAILS (absolute in-game path):
  import_code("/home/Bratan/bin/lib_core")
  // WORKS (relative to repo structure):
  import_code("../lib_core/lib_core.src")
  ```
- **Stubs needed** when referenced libs don't exist in repo (chat.src, chatform.src, thor.src, etc.)
- **Regex guard:** `import_code\("/` (any absolute path in import_code)

### (i) is_binary → is_folder (API rename)
- **Error:** No compile error — but `is_binary` is deprecated. GreyScript API uses `is_folder` now.
- **Fix:** `not f.is_binary` → `f.is_folder`. `is_dir = not entry.is_binary` → `is_dir = entry.is_folder`
- **Regex guard:** `.is_binary`

### (j) missing //command: marker
- **Standalone executables** need `//command: <name>` as first line. Libraries, tests, and utility .src files do NOT.
- **Library indicator list** (skip these): `lib_core`, `listlib`, `Util.src`, `core/`, `recon_lite`, `tests/`, `cli_core`, `libcore`, `buildcore`, `netcore`, `debugcore`, `filecore`, `cliFeedback`, `lzw/`, `xmem`, `minitest/`, `examples/`, `fix_perms`, `attack_tiers`, `ransomeware`, `installer-utils`
- **For actual tools:** `echo '//command: <toolname>' | cat - <file> > /tmp/tmp && mv /tmp/tmp <file>`

## CI specific

### CI-Bug: `((BUILT++))` under `set -euo pipefail`
- **Symptom:** CI shows "Build done" for first file then stops. All remaining files skipped but exit code says OK.
- **Cause:** `((BUILT++))` with `BUILT=0` returns exit-code 1 ("arithmetic value is 0") → `set -e` kills the loop
- **Fix:** Use `((++BUILT)) || true` (pre-increment swallows exit code). Also: capture stderr separately (`2>err_log`) instead of `2>/dev/null` to surface real errors.

### Pre-Push Mergeable Check
- **Symptom:** PR shows `mergeable: CONFLICTING` — main has moved since branch creation
- **Cause:** Branch was created before refactors (e.g., `src/core/*` → `src/*`). Main had parallel merges.
- **Check:** `gh pr view <N> --json mergeable` + `git log --oneline origin/main..HEAD`
- **Fix:** `git rebase origin/main && git push --force-with-lease`

## Guard Patterns (Pre-Commit)
```bash
# Run these over all .src files before any commit:
echo "=== one-line-if ===" && grep -rnP '\bif\b.*\bthen\b.*\bend\s+if\b' --include='*.src' . | grep -v '.bak-' | wc -l
echo "=== ternary ===" && grep -rnP '\bif\b.*\belse\b' --include='*.src' . | grep -v '.bak-' | grep -v 'else if' | wc -l
echo "=== try/catch ===" && grep -rnP '\btry\b|\bcatch\b|\bend\s+try\b' --include='*.src' . | grep -v '.bak-' | wc -l
echo "=== abs import ===" && grep -rnP 'import_code\("/' --include='*.src' . | grep -v '.bak-' | wc -l
echo "=== .trim() ===" && grep -rnP '\.(strip|trim)\b' --include='*.src' . | grep -v '.bak-' | wc -l
echo "=== backslash ===" && grep -rnP '\\\\' --include='*.src' . | grep -v '.bak-' | grep -v 'char(' | wc -l
echo "=== is_binary ===" && grep -rnP '\.is_binary' --include='*.src' . | grep -v '.bak-' | wc -l
echo "=== HTTP.Request ===" && grep -rnP '\bHTTP\.Request\b' --include='*.src' . | grep -v '.bak-' | wc -l
```
