# Wave-2 Build-Fix Session Learnings (2026-07-07)

> Companion to `language-pitfalls.md` sections 14 (NP-81) and 15 (NP-82).
> Captures the actual reproduction transcripts and verified fix recipes from the
> 3-bug fix session — patterns that static-scanners miss and that briefs often misdiagnose.

## Session at a glance

3 specific bugs from a static-scan report (Welle-1), fixed by Agent H in Welle-2:

| File | Brief diagnosis | Actual bug | Status |
|---|---|---|---|
| `auto_exploit/auto_exploit.src` | "String-in-String (Quotes-in-String)" | ✅ Correct — Z159 had `via "metaxploit"` | ✅ Build green |
| `wifi_crack/wifi_crack.src` | "unbekannte step() Funktion" | ❌ Brief wrong — real bug: 2× missing `)` after `]` in `render([...]` (Z44, Z111). `step` IS defined in lib_core.src:49. | ✅ Build green |
| `list-lib/tests.src` | "falsche each() API-Nutzung" | ❌ Brief wrong — `map.each` correctly takes `(key, value)` per listLib.src:53-58. Real bug: inline multi-line `function()` is invalid arg-position syntax in greybel. | ✅ Build green |

Full session report: `/tmp/fix-report-agent-h.md` (created by Agent H 2026-07-07).

## NP-81 Reproduction: missing `)` after `]` cascade

Original wifi_crack.src error:
```
Build error: got Identifier[47:1 - 47:5: value = 'step'] where any of ",", ")" is required
  at wifi_crack.src:38:22
```

Two missing-`)` bugs at lines 44 and 111:
```greyscript
// Z44 — render("WiFi Crack", [ ... ])  — initial fix
render("WiFi Crack", [
    "Interface: " + iface,
    "BSSID:     " + bssid,
    "ESSID:     " + essid,
    "ACKs:      " + acks,
    "Capture:   " + captureFile
])                     // ← was: ]

// Z111 — render("PASSWORT GEFUNDEN", [ ... ])  — second fix needed
render("PASSWORT GEFUNDEN", [
    "ESSID:    " + essid,
    "BSSID:    " + bssid,
    "",
    "PASSWORD: " + password
])                     // ← was: ]
```

After fixing Z44 only, the error **moved** to line 114 (logToFile token) — confirming the cascade pattern. Both fixed → Build done.

**Key insight**: when an error like `got Identifier[X:Y: value = 'step'] where any of ",", ")" required` has `Y < 5`, the parser is at the **start** of a line it can't reconcile. This signature is the marker for "missing closer further up" — not "unknown identifier".

## NP-82 Reproduction: inline multi-line `function` as argument

Generated `/tmp/test-each{2,4,5,6,7,8,9}.src` to isolate the issue. **Every** inline form fails:

| Variant | Source | Result |
|---|---|---|
| Multi-line single-param | `a.each(function(kv)\n  print(kv[0])\nend function)` | ❌ Build error |
| Multi-line empty-param | `a.each(function()\n  print("hi")\nend function)` | ❌ Build error |
| Single-line `;`-separated single-param | `a.each(function(kv); print(kv[0]); end function)` | ❌ Build error |
| Single-line empty-param | `a.each(function(); print("hi"); end function)` | ❌ Build error |
| `@`-prefix | `a.each(@function(kv); print(kv[0]); end function)` | ❌ Build error |
| **Variable-assigned** | `f = function(kv); print(kv[0]); end function; a.each(f)` | ✅ Build done |

The pattern is unambiguous: **greybel accepts `function(...) ... end function` only as the right-hand side of `=`**. Inline in argument position is rejected regardless of body shape, param count, or `@`-prefix.

### Why this matters for the listLib API

`listLib.src` defines `map.each` as:
```greyscript
map.each = function(func)
    list = self.to_list(true)
    result = list[0:]
    for i in indexes(list)
        func(result[i][0], result[i][1])     // ← 2-arg callback
    end for
end function
```

This is correct: it calls `func` with `(key, value)`. The lib API is fine.

The caller-side problem is two-fold:
1. **Can't declare `function(k, v)`** — GreyScript `function` header accepts ONE name only.
2. **Can't pass `function(...) body end function` inline** — must assign to variable first.

Solution: assign a single-param callback that takes an args-list, then index:
```greyscript
kvPrinter = function(kv); print(kv[0] + ":" + kv[1]); end function
a.each(kvPrinter)
```

## NP-80 String-in-String `char(34)` Fix Pattern (re-confirmed)

auto_exploit.src Z159 was:
```greyscript
print("  Adressen (manueller Exploit via "metaxploit"):")
```

Fix:
```greyscript
print("  Adressen (manueller Exploit via " + char(34) + "metaxploit" + char(34) + "):")
```

Output: `  Adressen (manueller Exploit via "metaxploit"):` — visually identical to what the author intended. `char(34)` is the only way to embed literal `"` inside a `"..."` string in GreyScript (no backslash escapes, no double-double `""inner""` allowed in mid-string in greybel).

**Detection grep**:
```bash
grep -nE '"[^"]*"[^"]*"[^"]*"' *.src   # 4+ quote-segments = string-in-string collision
```

## Detection greps for the 3 patterns (run as a batch)

```bash
REPO=/home/bratan/10-Projekte/10-active/greyhack-tools

# NP-80: string-in-string collisions
grep -rnE '"[^"]*"[^,\(\)\s][^"]*"[^"]*"[^"]*"' "$REPO" --include='*.src'

# NP-81: render([ / [ where next line doesn't immediately close
grep -rnE '\[$' "$REPO" --include='*.src' | head -20
# Then for each candidate, check the block-end:
grep -nE '^\s*\]\s*$' "$REPO" --include='*.src'

# NP-82: inline function-as-argument
grep -rnE '\.\w+\(function\(' "$REPO" --include='*.src'
```

All three patterns produce **parser errors that point at a different location than the actual bug**. Always reproduce + read the actual error site before patching.

## Backup-and-verify pattern (Agent H, 2026-07-07)

```bash
TS=$(date +%Y%m%d-%H%M%S)
cp file.src file.src.bak-${TS}
# ... apply fix ...
greybel build file.src /tmp/build-test/build -dbf
# Build done? → commit. Build fail? → mv file.src.bak-${TS} file.src, try again.
```

Recovery: `mv file.src.bak-20260707-102056 file.src` rolls back exactly.

Lesson for future wave-fix sessions: **always timestamp-suffix backups** so multiple agents can each have their own backup chain without overwriting each other.