# Known Bugs & Bug Patterns

## Known Persistent Bugs (as of 2026-06-19)
- `bootstrap/bootstrap.src` — HTTP.Request() (4 calls)
- `greyhack-tools/deploy_all.src` — Hardcoded IP, no null-check before .delete()
- `greyhack-tools/hermes/hermes_daemon.src` — No null/EOF check, no path validation
- `greyhack-tools/gsc/gsc.src` — self = self no-op, unescaped quotes
- `greyhack-tools/gsc/Util.src` — str(item) collision risk in unique()
- `greyhack-tools/scp_upload/scp_upload.src` — Password as CLI param, hardcoded log path, **wrong is_binary folder check (NP-59)**
- `greyhack-tools/forcer/forcer.src` — char(10) literal bug, no try/catch, no rate limiting
- `greyhack-tools/decypher/decypher_v3.src` — Cache-scope variable bug
- `greyhack-tools/grsa/grsa.src` — rnd without seed for crypto
- `greyhack-tools/metaxploit/metaxploit.src` (bin/) — Hardcoded import path, hardcoded log path
- `greyhack-tools/dankestein/farRepo.src` — Hardcoded credentials in connect_service()
- `greyhack-tools/dankestein/getShell.src` — Variable declared but never assigned
- `greyhack-tools/dankestein/mapLAN.src` — char(10) literal bug, wrong condition
- `greyhack-tools/dankestein/wifi.src` — input.len confusion, pass as reserved keyword

⚠️ **xmem update (2026-07-14):** See SKILL.md → Build Success Rate → "Caveat: xmem branch-merge gap".
The fix was committed to `refactor/2026-07-05-cleanup` but never merged to `develop`.
The `~/greyhack-tools/xmem/` directory is currently empty — no source files present.

## Bug Pattern Catalog (NP-18 through NP-79)

### NP-18 — `is_folder` usage
10 occurrences across 7 files. 2 fixed (lib_core, scp_upload).

### NP-19 — Single quotes in strings
15 occurrences across 8 files. 1 fixed (secure.src).

### NP-20 — Repeated `get_shell.host_computer`
10+ files, up to 4x in one file. 1 fixed (decypher_v3.src).

### NP-21 — Multi-line Map Literals
2 occurrences (gsc/Util.src). Pending.

### NP-22 — No null-check before `.delete()`
`deploy_all.src:63` — `pc.File(local_src).delete` without null-check.

### NP-23 — No EOF/null check on `user_input()`
`hermes_daemon.src:315` — `user_input()` return passed to `.trim()` unchecked.

### NP-24 — Hardcoded IP addresses
`deploy_all.src:14` — `FILESERV = "http://192.168.1.100:8765"` hardcoded.

### NP-25 — `self = self` no-op in closures
`gsc/gsc.src:83` — dead code in `makeCurry`.

### NP-26 — `str(item)` collision in `unique()`
`gsc/Util.src:165` — type collision in dedup key.

### NP-27 — Unescaped quotes in generated code
`gsc/gsc.src:118` — `makeStr` doesn't escape `"` in paths.

### NP-28 — Off-by-One in `range(N-1)` loop
HIGH severity.

### NP-29 — Non-existent `applyFunction` method
CRITICAL severity. **✅ RESOLVED 2026-07-04** — Commit `c374c52` on `develop`.
Dead `list.applyFunction = function(func)` declaration entfernt (GreyScript unterstützt keine Typ-Erweiterung von Built-Ins). Globale Helfer-Funktion `applyFunction(lst, func)` eingeführt. `hex()` in `bltings/bltings.src` von `.applyFunction(@dectohex)` auf `applyFunction(digits, @dectohex)` umgestellt.
Build: green. Mock-Env verifiziert: `hex(255)="ff"`, `hex(16)="10"`, `hex(4096)="1000"`.
Root cause in Language-Reference unter «Type extension of built-in types» dokumentiert.

### NP-30 — Unvalidated split array access `[1]`
HIGH severity.

### NP-31 — No try/catch in test runner loop
HIGH severity.

### NP-32 — Null crash on `.build()` result `.len`
HIGH severity.

### NP-33 — String concatenation in loop (O(n²))
MEDIUM severity.

### NP-34 — Print in tight loop (I/O overhead)
MEDIUM severity.

### NP-35 — Unvalidated user input to `overflow()`
MEDIUM severity.

### NP-36 — Ambiguous boolean precedence (no parens)
LOW severity.

### NP-42 — `touch()` return misinterpretation
Checking `pc.touch() != 1` or `== 1`. `touch()` returns `""` (empty string) on success, `null` on failure. Check `== null` for failure, not `!= 1`. Same applies to other GreyScript APIs with non-integer returns. (HIGH)

### NP-43 — Empty field after split()
Checking `split_result.len < 2` but not checking for empty strings. `":".split(":")` → `["", ""]` passes len check. Also validate individual fields are non-empty. (HIGH)

### NP-44 — Multi-line script via string concat
Building shell scripts or multi-line content via `s = s + ...` in sequence. Use list + `join(char(10))` for O(n) construction. (MEDIUM)

### NP-45 — `touch()` return value
`pc.touch(path)` returns `""` (empty string) on success, `null` on failure. NOT `1`. Check `== null` for failure, NOT `!= 1`. Same pattern as `delete()`. (HIGH)

### NP-46 — Function name shadowing `map()`
Naming a function `map` shadows the global `map()` constructor, breaking all map operations. Rename to `list_map`. Found in `alias-cli/alias.src`. (HIGH)

### NP-47 — File size check without null-check
Checking `file.size < 1000` without first checking `if file then`. Always null-check File objects before accessing properties. (MEDIUM)

### NP-48 — Infinite parent traversal loop
`while file.name != "/"` with `file = file.parent` can loop forever if `parent` returns self at root. Add guard: `next = file.parent; if next == file then break; file = next`. (LOW)

### NP-49 — `"char(10)"` string literal instead of `char(10)`
Using `"char(10)"` (a 6-char literal string) instead of `char(10)` (the newline character) in `split()` or string operations. Found in `forcer.src:14`. (HIGH)

### NP-50 — Variable referenced outside defining scope
Variables defined inside `if`/`for` blocks referenced later outside that block. When the block is skipped, variables are undefined → crash. Found in `decypher_v3.src:72-81`. (HIGH)

### NP-51 — Password as CLI parameter
Passing passwords as command-line arguments makes them visible in process list and shell history. Use `user_input()` or credential files instead. Found in `scp_upload.src:19`. (MEDIUM)

### NP-52 — `rnd` without seed for crypto
Using `rnd` to select random primes for RSA key generation without seeding. Produces predictable primes. Found in `grsa.src:83-86`. (MEDIUM)

### NP-53 — `print("char(10)")` string literal vs `char(10)` in print
Using `"char(10)"` (6-char literal) instead of `char(10)` (newline) inside `print()`. Same root cause as NP-49. (LOW)

### NP-54 — Unassigned variable usage
`file = null` at top scope, then `file.has_permission("r")` without intermediate assignment. Always crashes. Trace all code paths between declaration and usage. (HIGH)

### NP-55 — Hardcoded credentials in connect_service()
Credentials embedded directly in `connect_service()` call. (HIGH)

### NP-56 — `input.len` on String vs List confusion
`user_input()` returns a String. `input.len` gives character count, not token count. Use `input.split(" ").len` to count space-separated tokens. (MEDIUM)

### NP-57 — `pass` as variable name
`pass` is a reserved keyword in some GreyScript versions. Causes parse errors. Use `passwd`, `pw`, or `password`. (LOW)

### NP-58 — Unvalidated array access after `split()`
Accessing `line[N]` without checking `line.len >= N+1`. Found in `ps/ps.src:25-28`. (HIGH)

### NP-59 — `is_binary` as folder detector (repeated)
Same as NP-21 but in new context. Found in `scp_upload/scp_upload.src:83`. (HIGH)

### NP-60 — String concatenation in render function
Using `r = r + ...` pattern per render frame. Found in `ps/ps.src:45-53`. (LOW)

### NP-61 — Potentially undefined function name
`validIP()` is not a documented GreyScript standard library function. Canonical name is `is_valid_ip()`. Found in `routerinfo/routerinfo.src:27`. (LOW)

### NP-62 — Property access without null-check on API objects
Directly accessing `.public_ip`, `.essid_name`, etc. without `or "(n/a)"` guard. Found in `routerinfo/routerinfo.src:51-56`. (LOW)

### NP-63 — `range(0, x.len - 1)` Off-by-One
`range(a, b)` produces `a..b-1`, so `range(0, x.len-1)` skips the last element. Found in 15+ files: grsa, decypher, parseExploitReqs, bltings, lib_core, networking. Differs from NP-54 (empty list edge case). (HIGH)

### NP-64 — `map.count` returns string length, not occurrence count
`bltings.src:76`: `map.count = function(item) return str(self[item]).len` returns `str(value).len`, not count of occurrences. (MEDIUM)

### NP-65 — `list.applyFunction` Off-by-One
`bltings.src:116`: `range(self.len - 1)` skipped last element. **✅ bltings resolved 2026-07-04** (dead `list.applyFunction` declaration entfernt, neuer globaler Helper iteriert `for item in lst` — korrekt). Check `parseExploitReqs.src:30` separately. (MEDIUM)

### NP-66 — `.join("char(10)")` string literal
`ps.src:73`: joins with literal string `"char(10)"` instead of newline `char(10)`. Related to NP-49 but different context. (MEDIUM)

### NP-67 — `show_procs` split result indexed without length check
`ps.src:24-28`: `line[2][:-1].val` without checking `line.len >= 4`. (MEDIUM)

### NP-68 — Port object property access without guard (mock-env crash)
`yuno.src:409`: `p.service` crashed in `greybel execute` Mock-Env with `Runtime error: Path "service" not found in map.` Some Port objects in Mock-Env return maps where `service` key is missing — direct property access throws, `typeof(p.service) == "string"` also fails (typeof itself crashes on missing key).

**Lösung:** 4-stufige Guard-Kette mit `hasIndex()` (siehe Fix Template unten).

**Root Cause:** GreyScript Maps erlauben property-read via dot-Notation (`p.service`) und Bracket-Notation (`p["service"]`). Fehlt der Key, crashed BEIDE Schreibweisen mit "Path not found in map". **`typeof(p.service)` crashed ebenfalls** — typeof selbst löst den Zugriff aus, bevor er den Typ prüft. Einziger sicherer Weg: zuerst `hasIndex("key")` prüfen, dann mit Bracket-Notation lesen.

Gefunden während `yuno defend` Test 2026-07-03. Fix bestätigt 2026-07-04 auf 4 aktiven Tools (recon, recon_lite, mxwrap, portmon). (HIGH)

**Fix template (4-stufige Guard-Kette, bestätigt 2026-07-04):**
```greyscript
// Stufe 1: Type-Filter — nicht-Maps ueberspringen
if typeof(p) != "map" then continue end if

// Stufe 2: Flag-Prüfung — kein is_closed-Key oder geschlossen → skip
if not p.hasIndex("is_closed") or p["is_closed"] then continue end if

// Stufe 3: Port-Number — fehlender Key ist akzeptabel (null-Fallback)
portNum = null
if p.hasIndex("port_number") then portNum = p["port_number"] end if

// Stufe 4: Service/Version — Type-Check + Fallback
svc = ""
if p.hasIndex("service") and typeof(p["service"]) == "string" then
    svc = p["service"]
end if
```
⚠️ Kein `indexOf()` auf Maps verwenden! `indexOf(key)` existiert NUR auf Listen und Strings — auf Maps liefert `indexOf` immer `-1`, selbst wenn der Key existiert. Für Map-Key-Existenz IMMER `hasIndex(key)` nutzen.

**Detection grep:**
```bash
grep -rn 'p\.\(service\|port_number\|is_closed\|get_lan_ip\)' --include="*.src" ~/greyhack-tools/ | grep -v 'if p\.'
```

### NP-79 — `.strip()` / `.trim()` existieren NICHT in GreyScript
`.strip()` und `.trim()` (mit oder ohne Klammern) kompilieren clean in `greybel build`, crashen aber im echten GreyHack-Game mit `Runtime error: Path "trim" not found in string intrinsics`. Beide Methoden existieren weder in MiniScript 0.x noch im GreyScript-Wrapper der Game-Engine — sie sind reine Python-/Ruby-/JS-Konzepte, die durch Mock-Env-Tests schlüpfen können. Viele Community-Scripts fallen damit erst beim In-Game-Run auf die Nase.

**Symptom:** Build erfolgreich, aber `Runtime error: Path "trim" not found in string intrinsics` direkt bei der ersten Verwendung. Bei `return parts[1].trim` (Bareword, ohne Klammern) wird die Methode als Referenz statt Aufruf interpretiert — beim Hash-/Vergleichs-Use crasht sie ebenfalls.

**Lösung:** Manuelle trim-Loop (leading + trailing spaces). Rezept (kopierbar, inline-expand wenn ≤2 Vorkommen pro File):
```greyscript
// Leading spaces strippen
while inp.len > 0 and inp[0] == " "
    inp = inp[1:]
end while
// Trailing spaces strippen
while inp.len > 0 and inp[inp.len - 1] == " "
    inp = inp[:inp.len - 1]
end while
```

**Inline-Expand vs. Helper-Funktion:**
- **Inline-Expand** wenn pro File nur 1 Fund (häufigster Fall): weniger Code, lesbarer.
- **Helper `trim(s)` als globale Funktion** erst, wenn ≥2 trims im selben File vorkommen — typischerweise in `lib_core.src` zentralisiert.

**Verifizierter Workflow 2026-07-07 (Pattern-i-Bug-Fix-Schwarm, 3/4 Files OK):**
1. `search_files pattern='\.trim\('` in betroffenen Files → exakte Live-Calls (Kommentare ausnehmen).
2. Patch via `patch old_string/new_string`.
3. `greybel build <file>.src /tmp/out -dbf` — Build muss grün sein.
4. `grep -c '\.trim' /tmp/out/*.src` im kompilierten Artefakt — muss 0 sein (bestätigt, dass Loop emittiert wurde).
5. Backups vor Patch nach `/tmp/fix-backups-*/<file>.src.bak-<STAMP>`.

**Verifizierte Fix-Beispiele (3 Files, alle gebaut am 2026-07-07):**
- `greyhack-tools/gsc/gsc.src:75` — `return parts[1].trim` → Inline-Loop auf `depName`-Lokalvariable
- `greyhack-tools/hermes/hermes_daemon.src:170` — `cmd = cmd.trim()` → Inline-Loop mit Re-Assign auf `cmd`
- `greyhack-tools/chat-app/ChatInput.src:15` — `message.trim()` → Inline-Loop mit Re-Assign auf `message`
- ⚠️ `greyhack-tools/password-gen/password_generator.src:26` (`s = s.trim.upper`) — Out-of-Scope für Pattern-i-Schwarm, weil Pattern-a-Agenten die Datei besitzen. Race-Condition-Vermeidung: andere Pattern-Agents haben Ownership.

**Verwandtes Issue (nicht Pattern-i):** `greyhack-tools/hermes/hermes_daemon.src:287` liest `user_input(...)` ohne Null-Guard. Der hier eingebaute trim-Loop crasht NICHT mehr bei `null.trim()` (war NP-23), aber Pattern (j) für `user_input`-Null-Guard ist weiter offen — separate Pattern-Reports.

Found + fixed 2026-07-07 während Pattern-i-Bug-Fix-Schwarm (Yuno-Queen-Pattern, 4 Files). (HIGH für In-Game-Runtime)

### NP-74 — `if not <bare-name> then` an undefinierter Top-Level-Variable
Wenn eine globale Variable `h` (oder ähnlich) noch nie zugewiesen wurde, wirft `if not h then` in MiniScript einen Runtime-Error `Path "h" not found in scope`. Anders als z.B. Python/JS kennt MiniScript **kein** `null`/`undefined`-Default für ungesetzte Variablen — der erste Read ist sofort ein Hard-Crash.

**Symptom:** `Runtime error: Path "h" not found in scope` direkt nach dem Build (compile ist OK), oft erst beim Modul-Load.

**Lösung:** `globals.hasIndex("h")` für optionale Top-Level-Globals verwenden:
```greyscript
// FALSCH — crasht wenn h nicht existiert:
if not h then
    h = {}
end if

// RICHTIG — sicheres Idiom:
if not globals.hasIndex("h") then
    globals["h"] = {}
end if
h = globals["h"]
```

Gefunden 2026-07-04 in `yuno_viper/yuno_viper_util.src:670` (und Duplikat in `yuno_viper/modules/yuno_viper_util.src`). Fix bestätigt via `greybel execute -p help` (kein Crash mehr an dieser Stelle). (HIGH)

**Detection grep:**
```bash
# Scannt nach `if not NAME then` wo NAME nirgends im File zugewiesen wird.
# Achtung: False-Positives bei Funktionsparametern (Name in `function(Name)`) und
# Loop-Variablen (`for Name in ...`) — manuell pruefen.
grep -rnE "^\s*if not [a-zA-Z_]+ then\s*$" --include="*.src" ~/greyhack-tools/yuno_viper/
```

## Detection Grep Commands (Master-Grep)
```bash
# NP-63: Off-by-One range
grep -rn 'range.*\.len.*-.*1' --include="*.src" ~/greyhack-tools/ | grep -v '/backups/'
# NP-64: map.count definition
grep -rn 'map\.count.*function' --include="*.src" ~/greyhack-tools/
# NP-65: applyFunction definition
grep -rn 'applyFunction' --include="*.src" ~/greyhack-tools/
# NP-66: join with char(10) literal
grep -rn 'join.*"char(10)"' --include="*.src" ~/greyhack-tools/
# NP-67: show_procs split without length check
grep -rn 'show_procs.*split' --include="*.src" ~/greyhack-tools/
# NP-79: .strip() / .trim() Live-Calls (filtert Kommentare raus)
grep -rnE '^[^/]*\.trim\b' --include="*.src" ~/greyhack-tools/ | grep -v '/backups/' | grep -v 'FIX.*PATTERN'
# Strenger (nur echte Methoden-Calls, ohne Kommentar-Präfix):
grep -rnE '\.trim\s*[(]?\s*[^=]' --include="*.src" ~/greyhack-tools/ | grep -v '/backups/' | grep -v '^[^:]*:[[:space:]]*[/-]'
```

## False Positive / Duplicate Directories
- `backups/` — old snapshots, **MUST filter with `grep -v '/backups/'`** — scanning backups produces only duplicate findings. With 269 total files but only ~90 active, the index drifts into backup territory after first wrap-around.
- `installer/` — code generation (`.push()` strings), not deployed code
- `tests/` — short variable names trigger false positives
- `hermes/` — deprecated wrapper files

## Detailed Scan Round Results
- `bug-patterns-2026-06-17-round2.md` — NP-22 through NP-26
- `bug-patterns-2026-06-17-round3.md` — NP-27 through NP-36
- `bug-patterns-2026-06-17-round4.md` — NP-37 through NP-41
- `bug-patterns-2026-06-17-round5.md` — NP-42 through NP-44
- `bug-patterns-2026-06-17-round6.md` — NP-48
- `bug-patterns-2026-06-18.md` — NP-49 through NP-52
- `bug-patterns-2026-06-19.md` — NP-53 through NP-57
- `bug-patterns-2026-06-19-round9.md` — backup file index drift lesson
- `bug-patterns-2026-06-19-round10.md` — NP-58 through NP-62
- `bug-patterns-2026-06-19-round11.md` — NP-63 through NP-67
