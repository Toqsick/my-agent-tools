# GreyScript Bug-Sweep Session Learnings (2026-07-07)

Full audit + auto-fix sweep over 78 active `.src` files in `~/10-Projekte/10-active/greyhack-tools/`. **Result: 41/66 → 47/66 build-OK (+6 files fixed), CI-Bug NP-99 fixed, Branch `fix/bug-scan-sweep-2026-07-07`, Commit `0dee04f`.**

## Patterns that surfaced (full scan results)

| Pattern | Description | Static-Scan Hits | Real Fixes | Notes |
|---------|-------------|-----------------:|-----------:|-------|
| (a) | one-line `if X then Y end if` | 40 | 7 | greybel-js rejects; always expand to multi-line |
| (b) | ternary `X if C else Y` | 1 | 1 | always expand to if/else/end if |
| (c) | `\n` literal in strings | 0 | 0 | — |
| (d) | single-quote in code | 16 | **0** | **ALL false-positives** — see below |
| (e) | inline-if assignment | 0 | 0 | — |
| (f) | `\` escape in strings | 4 | 4 | replace with `char(34)`/`char(92)` |
| (g) | `===` separator | 0 | 0 | — |
| (h) | `[^N]` negative index | 0 | 0 | — |
| (i) | `.strip()`/`.trim()` runtime crash | 4 | 4 | manual trim-loop required |
| (j) | `str_repeat()` | 0 | 0 | — |
| (k) | `get_system_time()` | 0 | 0 | — |
| (l) | `HTTP.Request()` + try/catch | 4 + 3 try blocks | 1 | `pc.wget()` for file URLs, see decision-tree below |
| (m) | recursive `require_shell` | 0 | 0 | — |
| (n) | missing `//command:` marker | 76 | — | soft (only standalone commands need it) |

## Pattern (d) False-Positive Classification (CRITICAL)

When static scan counts single-quote hits, classify BEFORE editing. GreyScript has **NO string-escape mechanism** — converting `'foo'` to `"foo"` inside an outer-DQ string breaks the build (`Compiler error: got Identifier`).

| Context | Example | Replace? |
|---------|---------|:---:|
| Code comparison | `if x == 'foo'` | ✅ Yes → `if x == "foo"` |
| Assignment | `name = 'bar'` | ✅ Yes → `name = "bar"` |
| Hash key | `arr['key']` | ✅ Yes → `arr["key"]` |
| **Nested data in DQ-string** | `"vim -c ':!/bin/sh'"` | ❌ Leave — inner `'` is literal char, can't escape |
| User-facing print | `print("Tippe 'q' zum Beenden")` | ❌ Leave — German convention |
| Comment | `// vorletztes = 's'` | ❌ Leave — text in `//`-lines |

**Real benchmark (suid_exploit.src):** 9 single-quote hits, ALL inside `"vim -c ':!/bin/sh'"`-style nested-data strings. NONE convertible. Real classification took ~3 minutes, real fix-count = 0.

**Lesson for future sub-agent fix-sweeps:** Pattern (d) Sub-Agent should NEVER auto-replace without per-line classification. Pattern (d) is the **highest false-positive-rate pattern** in the 14-pattern scan set.

## Pattern (i) `.strip()`/`.trim()` — Manual Trim-Loop (GreyScript has no string-strip)

Compiles clean, runs clean in mock-env, **CRASHES in real game** with `Path "strip" not found in string intrinsics`.

```greyscript
// BAD — crashes in real game
s = line.strip()

// GOOD — manual trim-loop
while s.len > 0 and s[0] == " "
    s = s[1:]
end while
while s.len > 0 and s[s.len - 1] == " "
    s = s[:s.len - 1]
end while
```

**Helper-function recommendation:** If >1 occurrence in a file, add `trim(s)` helper to local module. Files with single occurrence: inline-expand.

**Edge case (password_generator.src):** Original code was `s = s.trim.upper` — BOTH wrong (method-ref without parens AND `.upper` works but only after trim). Fix:
```greyscript
// Manual trim-loop
while s.len > 0 and s[0] == " "
    s = s[1:]
end while
while s.len > 0 and s[s.len - 1] == " "
    s = s[:s.len - 1]
end while
// Note: `s.upper` works as GreyScript builtin (verified 2026-07-07)
s = s.upper
```

## Pattern (l) HTTP.Request + try/catch Decision-Tree

GreyScript has **NO** `HTTP.Request()` and **NO** `try/catch`/`end try` syntax. `try/catch end try` blocks cause `Build error: unexpected keyword 'end try' at start of line`.

**Decision-tree for replacement:**

| URL type | Replacement | Notes |
|----------|-------------|-------|
| LAN-IP fileserver `http://192.168.x.x:8765/file.src` | `pc.wget(url, dstPath)` then check `pc.File(dstPath)` | Works for Steam Native Linux (verified) |
| `127.0.0.1:8765/file.src` | `pc.wget(url, dstPath)` | Same — local file URL |
| Hermes-API `http://127.0.0.1:8333/status` | `pc.wget(url, probePath)` then file-exists check + TODO comment | NOT a file endpoint, JSON-API; needs Hermes API gateway |
| External URL `http://example.com/api` | Comment out with `// TODO: needs Hermes gateway` | `pc.wget` only does file downloads |

**Bootstrap.src real fix (commit 0dee04f):**
```greyscript
// VORHER (try/catch around HTTP.Request):
try
    apiResponse = HTTP.Request(apiURL, "GET")
catch e
end try

// NACHHER (Hermes-API is JSON-endpoint, not file):
// Hermes API testen — port 8333 nicht via pc.wget erreichbar (kein endpoint-Datei)
// TODO: external HTTP — needs Hermes API gateway (port 8333)
// GreyScript kann keinen HTTP-Call machen; pc.wget erwartet eine Datei-URL.
probeURL = "http://127.0.0.1:8333/.hermes_api_probe"
probePath = "/tmp/.bootstrap_api_probe"
pc.touch(probePath); probeFile = pc.File(probePath)
if probeFile then probeFile.delete end if
// pc.wget writes a file: if it fails, no file appears
// ...
```

**Helper-pre-init pattern:** Always `shell = get_shell; pc = shell.host_computer` at top before using `pc.wget` — required for both real game and mock-env.

## CI-Bug NP-99 (CRITICAL — `ci-build.sh v2` was fake-grün)

**File:** `~/10-Projekte/10-active/greyhack-tools/scripts/ci-build.sh` (commit 4d9ff4b, 2026-06-25)

**Bug 1: `((VAR++))` exits script under `set -euo pipefail`:**
```bash
set -euo pipefail
BUILT=0
for f in "${FILES[@]}"; do
    if "$GREYBEL" build "$f" "$target" 2>/dev/null; then
        ((BUILT++))        # ← Exit-Code 1 wenn BUILT=0 ("value is 0")
    else
        ((FAILED++))
    fi
done
```

Script aborted after the first iteration. Logged `Build done. Available in /tmp/ci-test/.../build.` (last successful build from previous run) and `==> Build complete: 0 OK, 0 failed` would NEVER print.

**Bug 2: `2>/dev/null` swallowed all greybel errors** — even if loop completed, build-failure messages were invisible.

**Fix applied (commit 0dee04f):**
```bash
# Pre-increment statt post-increment
((++BUILT)) || true
((++FAILED)) || true

# stderr separat erfassen
err_log="$(mktemp)"
if "$GREYBEL" build "$f" "$target" 2>"$err_log"; then
    ((++BUILT)) || true
else
    echo "    ✗ $f"
    head -3 "$err_log" | sed 's/^/        /'    # Erste 3 Zeilen echter Error
    ((++FAILED)) || true
fi
rm -f "$err_log"
```

**Result:** 41 OK / 25 FAIL (honest) — CI was lying for ~2 weeks.

**Cross-reference:** `bash-script-audit` skill, Pattern #22 — same trap applies to ANY counter-pattern in bash under `set -e`.

## Sub-Agent Race-Condition Pattern (Multi-File Overlap)

When 5 parallel sub-agents fix different patterns in the same repo, **race conditions can emerge** on files that match multiple patterns.

**Example (Bug-Sweep 2026-07-07):** `password_generator.src` matched both:
- Pattern (a) Sub-Agent: 6 one-line-if occurrences → needs expansion
- Pattern (i) Sub-Agent: 1 `.trim.upper` runtime-bug

Both sub-agents wanted to edit the same file. Pattern (a) finished first, Pattern (i) waited on backup-locks but `password_generator.src` was still uncommitted.

**Resolution:** Queen-Direct fix — parent took over and patched the `.trim.upper` block manually using the same trim-loop pattern, then verified with `greybel build`.

**Lesson for future fix-sweeps:**
- When dispatching pattern-fix sub-agents in parallel, **file-coverage should be exclusive** (each file owned by exactly one agent)
- Use `git status --short` + `find -name "*.bak-*"` between phases to detect overlap
- If overlap detected, **parent-direct** the conflict zone — never let two sub-agents edit the same file concurrently (Patch-tool failures, line-number shifts)
- Backup naming convention `.bak-YYYYMMDD-HHMMSS` lets you see who touched what when

## Sub-Agent Verify-Pflicht (Pre-Existing vs Introduced)

When sub-agents report "Build FAIL after fix", **ALWAYS verify** whether the failure is:
1. **Pre-existing** (e.g. `lib_core` import-path missing, `chat.src` runtime-path, `metaxploit.so` not on host)
2. **Introduced** (the fix actually broke something)

**Sweep 2026-07-07 verification:** 3 of 8 sub-agent-reported build-fails were pre-existing import-issues that existed BEFORE the fix. Pattern (d) sub-agent explicitly documented "OUT-OF-SCOPE: pre-existing dependency issue".

**Mandatory sub-agent briefing template:**
> "If build fails AFTER your fix, classify the error: (a) pre-existing dependency/import issue — document in report, do NOT rollback your fix; (b) introduced by your patch — ROLLBACK and report."

## `.bak-*` Backup Convention + `.gitignore`

**Pattern:** Every agent-fix creates `<file>.bak-YYYYMMDD-HHMMSS` backup before patching.

**Recovery:** `mv <file>.bak-20260707-095031 <file>` rolls back.

**Git-ignore pattern (added 2026-07-07):**
```gitignore
# Backup files from auto-fix agents (Bug-Scan 2026-07-07)
*.bak
*.bak-*
```

**Lesson:** Backup-naming must include timestamp so multiple fix-attempts don't overwrite each other.

## Static-Scan Implementation (for future audits)

**Tools:** Python `re` regex scan + `greybel build <file> <outdir> -dbf` verification. ~140ms for 78 files.

**Pattern reference for static scan:** see `language-pitfalls.md` + `p0-pattern-reference-2026-06-25.md` + this file.

**Scan order matters:** Run cheap static-regex first (catches 95% of issues), then greybel-build for actual verification (catches issues static-regex misses like `.strip()` runtime crash).

**Output paths:**
- `/tmp/bug-scan-results.json` — raw pattern counts
- `/tmp/greybel-test/<file>/build/` — per-file build verification
- `/tmp/fix-report-agent-<X>.md` — per-agent fix reports (with `##AGENT_X_DONE##` sentinel)
- `~/docs/system/greyhack-bug-scan-2026-07-07.md` — consolidated report

## Lessons for Yuno-Queen Pattern (orchestration)

1. **Pattern-exclusivity for sub-agent files** — when dispatching parallel fix-agents, ensure each file is owned by exactly one agent.
2. **Verify sub-agent claims yourself** — 3/8 reported "build fails" were pre-existing import-issues. Queen runs the final `greybel build` to confirm.
3. **Pitfall #5 (sub-agent self-reports ≠ facts)** — pattern (a) sub-agent changed 7 files but reported nothing. Pattern (d) sub-agent reported "0 fixes needed" (correctly classified 16 as false-positives). Trust the classification, verify the build.
4. **NP-99 silent CI bug** — discovered while reviewing the swarm's first run. CI had been fake-green for ~2 weeks. Fix is essential for any future fix-sweeps to be measurable.
5. **Mnemosyne + Memory** — Schwarm-Resultate sofort persistieren, damit Modell-Wechsel die Findings nicht verlieren.

— Yuno, 2026-07-07