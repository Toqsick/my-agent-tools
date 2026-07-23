---
name: greyhack-greyscript
description: "Use when user asks for GreyScript syntax, GreyScript escape handling, GreyHack game scripting, char() codepoint patterns. NOT for non-GreyHack scripting or other MMO scripting. GreyHack MMO scripting (GreyScript — actual game V0.7+ reference)."
tags:
- gaming
- greyhack
- miniscript
- scripting
- hacking-sim
triggers:
- grayhack
- greyhack
- greyscript
- Grey Decode
- metaxploit
- airmon / aireplay / aircrack
- viper-guide
- Viper-Guide-Struktur
- backslash escape pattern (f) fix
- char(34) quote replacement
- char(92) backslash literal
- char(39) inner apostrophe
- single-quote code-vs-user pattern
- pattern (d) single-quote
version: 2.15.0
author: Hermes Agent
license: MIT
lane: worker-flash
reasoning_effort: high
trigger_keywords: ['scripting', 'greyscript', 'greyhack', 'game', 'user']
keywords: ['scripting', 'greyscript', 'greyhack', 'game', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['greyhack', 'greyhack-sandbox', 'greyhack-hermes-api']
---


# GreyHack / GreyScript

## String Literals, Escapes & `char()` Codepoints (added 2026-07-07)

GreyScript does **not** interpret C-style backslash escapes (`\n`, `\t`, `\"`, `\\`, …). When a `.src` file contains a literal `\` inside a double-quoted string, the greybel compiler emits it as the character itself — but the visual escape `\"` and `\\` in source is a frequent bug source (looks intentional to humans and LLMs, does nothing semantic).

> **Pattern (d) Single-Quote Cleanup** — 4-bucket classification + the "no string escape = nested apostrophe is NOT a delimiter" rule, plus a 2026-07-07 case study: see `references/pattern-d-single-quote-cleanup.md`.

### Pattern (f): replace backslash-escapes with `char()`

| Sequence | ASCII | Replacement |
|---|---|---|
| `\"` (quote in `"…"`) | 34 | `char(34)` |
| `\\` (literal backslash) | 92 | `char(92)` |
| `\n` (newline) | 10 | `char(10)` (preferred form, already standard in this repo family) |

Migration: split the string at each `\` boundary (`"foo\"bar"` → `"foo" + char(34) + "bar"`).

### Pitfalls (real ones hit 2026-07-07)

- **Tab-indent stripping by `patch` tool.** Tab-indented `.src` files lose leading tabs when patched; verify with `sed -n '<range>p' file | cat -A` (look for `^I`) and restore with `sed -i '<N>s/^/\t/'` per line. GreyScript files in this repo family use tab indentation throughout.
- **Multi-occurrence ambiguity.** Lines like `.replace("\", "_")` can repeat three times in a row (e.g. `mission_report.src:106-108`). Expand `patch` `old_string` to the enclosing function definition + `end function` to disambiguate.
- **Out-of-scope build failures.** `greybel build` errors like `Dependency /home/<user>/bin/lib_core does not exist` come from `import_code(…)` — environment problem, NOT Pattern (f). Confirm `rg "\\\\"` returns 0 before declaring done.

### Verification checklist

```
rg "\\\\" <files>                       # expect 0 matches
greybel build <src> <out> -dbf          # expect "Build done"
```

**Session transcript & diffs:** see [`references/pattern-f-backslash-fix.md`](references/pattern-f-backslash-fix.md) for the 2026-07-07 batch (mission_report / testApi / portscan / secure).

**Game version verified 2026-07-03:** V0.9.6771-beta. `run` and `launch` commands do NOT exist — the correct workflow is:

1. **Write source** to `/home/<USER>/Config/<name>.src` with `//command: <name>` as first line
2. **Type** `<name>` in the shell — GreyHack auto-loads it as a command

`build <src> <dest-folder>` EXISTS but is for compiling into proper binaries (system-level, /bin/). User scripts with `//command:` placed in Config/ do NOT need building. The `/bin/` directory contains system commands (no `wget`/`curl` binary).

User's in-game account: `gregor` (lowercase, verified 2026-07-03, formerly `Bratan`, migrated 2026-06-27). Standard paths: `/home/Bratan/bin/`, `/home/Bratan/.logs/`, `/home/Bratan/.ssh/`, `/home/Bratan/data/`. In-game config still uses `Bratan` as filesystem owner but player shell name is `gregor`. Mail: `gregor@gusesamoz.org`. Bank user: `O1bx8eS6-niyufumay.com`. Public IP: `158.14.166.104`.

## Three-Layer Mental Model

- **Sprachebene** — variables, lists, strings, maps, functions, conditions, loops.
- **Objektebene** — Shell, Computer, File, Router, Crypto, Metaxploit, AptClient.
- **Werkzeugebene** — portscan, routerinfo, smtp_enum, wifi_crack, metaxploit workflow, launcher.

Never teach GreyScript as a flat command list. Frame every tool against these three layers. Start explanations from layer 1 or 2 when the question asks "why".

## Critical Language Pitfalls

See `references/language-pitfalls.md` for the full pitfall catalog (56+ categories).

| Issue | Fix |
|-------|-----|
| Strings: single quotes cause `Invalid character 39` | Use double quotes only |
| `.strip()` does NOT exist | Use manual trim-loop: `while s.len > 0 and s[0] == " "; s = s[1:]; end while; while s.len > 0 and s[s.len-1] == " "; s = s[:s.len-1]; end while` |
| Negative indexing `params[^0]` | Use `params[params.len - 1]` |
| `for x in list` iterates VALUES, not indices | Use `for i in myList.indexes` for position |
| Multi-line map/list literals | Avoid. Use incremental assignment `m = {}; m["a"] = 1` |
| `\\n` in strings (literal backslash-n) | Use `char(10)` for real newlines |
| Backslash `\\` ist KEIN gültiges Escape-Zeichen | **IMMER `char(34)` statt `\"`**, auch in statischen String-Literalen |
| One-line `if X then Y end if` | Always use multi-line (greybel-js rejects one-line) |
| Ternary `("X" if c else "Y")` | Use explicit `if/else/end if` block |
| `=======` separator lines | Delete or convert to `// ====` comment |
| Fehlende Kommas in Map-Literalen | Nach dem letzten `"key": "value"`-Paar IMMER ein Komma setzen |
| Kommentare INNERHALB von Map-Literalen | Kommentare müssen ENTFERNT oder AUSSERHALB des Objects platziert werden |
| Unvollständige Funktionen | error points at NEXT block, not broken one. Walk backward when build error points at harmless line |

## Bug Scanning & Audits

### Systematic Bug-Scanning (Non-Compiling Sources)

→ **See:** `references/bug-scanning.md`

When a user reports "Compiler Error at line N" in a large source (50+ KB, 60+ commands), systematically scan for these three bug types in order — they account for ~95% of yuno_v5/v6-class build failures:

1. **String-in-String (dynamic code generation)** — `"text1"text2"` where two `"` appear inside a `"..."` string with no `+` operator between them. Fix: replace inner quotes with `char(34)` concatenation.
2. **Trailing Comma Bugs in Map Literals** — missing comma before `}` or stray comma after assignment inside function.
3. **Comments Inside `{}` Object Literals** — GreyScript rejects `//` comments between `{` and `}`. Fix: move the comment outside the literal.

**Real-world benchmark:** yuno_v5.src (66KB, 64 commands) had 10+ trailing comma bugs, 5 string-in-string bugs, and 1 comment-in-object bug. All found and fixed in <5 minutes.

### 5-Build-Breaker Pattern Audit

→ **See:** `references/build-breaker-audit.md`

| # | Pattern | GreyScript Status | Regex |
|---|---------|-------------------|-------|
| (a) | Einzeilige `if X then Y end if` | ❌ Breaks greybel-js build; in-game GreyScript tolerates it but greybel rejects | `\bif\b.*\bthen\b.*\bend\s+if\b` |
| (b) | Ternary `X if cond else Y` | ❌ NOT supported at all | `\bif\b.*\belse\b` (on same line without `then`) |
| (c) | `\n` statt `char(10)` | ❌ `\n` is literal backslash-n, not newline | `\\n` in string context |
| (d) | Single-quotes `'text'` | ❌ `Invalid character 39` if used in code-strings | `'[^']*'` — **but only flag in code context, not in user-facing print text** |
| (e) | Inline-if assignment `X = (Y if C else Z)` | ❌ NOT supported — same as ternary | `=\s*\(.*\bif\b.*\belse\b` |

**Real-world benchmark (2026-07-04, Yuno Viper modules, 5 files, 3008 lines):** Pattern (a): 142 findings across 3 of 5 modules; Patterns (b)–(e): 0 findings each (clean).

### Greybel-JS Compatibility Scan

→ **See:** `references/compatibility-scan.md`

The in-game GreyScript engine and greybel-js interpret the SAME language spec but diverge on some edge cases. This audit checks 5 known divergence patterns:

1. **Escaped Quotes `\"` in print-Strings** — some greybel-js parsers handle escaped quotes differently
2. **`start_terminal` Method Access** — valid GreyScript API but greybel-js Mock may NOT support it
3. **Function/`end function` Balance** — three-pattern counting (var assignment, statement, obj.method)
4. **`import_code(...))` Double-Closing Paren** — copy-paste bug
5. **Multi-line Map Literals** — brace-depth balance

**Case study — yuno_viper modules (5 files, 3008 lines total, 2026-07-04):** All 5 modules pass all 5 compatibility checks. Only watchlist: `result.start_terminal` in `scan.src:481`.

### Runtime Bug Analysis (Compiling Sources)

→ **See:** `references/runtime-bug-analysis.md`

A file that BUILDS successfully may still fail at runtime. When a user reports "build passes but crashes when I run `<cmd>`", run this distinct audit:

1. **Undefined module-level variables — `commands` dict missing**
2. **Missing fields on shared state objects (YUNO_SHARED/main_session)**
3. **API results used without type check** — `typeof()` before use
4. **Dead code from API calls — result assigned but never used**
5. **Fields accessed without `hasIndex` guard on map-literals**

**Real-world benchmark:** `yuno_crypto_net.src` (175 lines, 6KB) had 3 runtime bugs. All compiler-clean. All found in <5 minutes.

### Static Code Audit: Deep Bug Search

→ **See:** `references/deep-bug-search.md`

This audit works on source alone — no `build`, no in-game execution, no feedback loop. Finds issues the compiler cannot catch.

**Order — scan in this sequence:**

1. **Balance Analysis — Control Flow Matching** — `if` vs `end if`, `function` vs `end function`
2. **Cross-Module Reference Audit** — symbols not defined locally
3. **Variable Name Mismatch Pattern (Copy-Paste Residue)**
4. **Dead Code Block Detection (Double Guard Pattern)**
5. **Initialization Gap Pattern** — fields used but not in init dict
6. **Severity Classification** — compiler / runtime / logic / warning
7. **GreyScript Null-Safety & Robustness Audit** (10-point checklist) — mandatory second pass for metaxploit code

**Case study — yuno_attack.src (295 lines):** 0 compiler bugs, but 6 runtime crashes found (commands dict missing, try_exploit undefined, COMMON_PORTS/BRUTE_USERS/BRUTE_PASSES/read_configs undefined, variable mismatch, dead code, objectList not in main_session).

### GreyScript Null-Safety & Robustness Audit

→ **See:** `references/null-safety-audit.md`

**10-Point Checklist — scan in this order:**

| # | Pattern | Search Hint | Fix Template |
|---|---------|------------|--------------|
| 1 | `get_shell.host_computer.*` without null-guard | `grep -nE 'get_shell\.host_computer' *.src` | `sh = get_shell; if not sh then return end if; pc = sh.host_computer; if not pc then return end if` |
| 2 | Port `0` in `net_use(ip, 0)` | `grep -nE 'net_use\(.*,\s*0\b' *.src` | Use actual kernel-service port or valid remote port |
| 3 | `run_exploit` result without `typeof(shell) == "shell"` check | `grep -nE 'run_exploit\(.*\)' *.src` | `if typeof(shell) != "shell" then return null end if` |
| 4 | `chmod(path, perms, true)` with root path `"/"` | `grep -nE 'chmod\("/",' *.src` | Target specific directories, never root `/` |
| 5 | `chmod()` return values silently discarded | `grep -nE '\.chmod\(' *.src \| grep -vE '^\\s*res?\\s*='` | Wrap each call: `res = pc.chmod(...); if typeof(res) == "string" then warn("[!] chmod: " + res) end if` |
| 6 | `network_gateway` without null-guard | `grep -nE 'network_gateway' *.src` | `router = sh.host_computer.network_gateway if sh != null and sh.host_computer != null else null` |
| 7 | `router.device_ports(ip)` without null-guard on router | `grep -nE 'device_ports' *.src` | `if router == null then return [] end if` BEFORE router method call |
| 8 | `targetShell.host_computer` without null-check | `grep -nE 'targetShell\.host_computer' *.src` | `if targetShell == null or targetShell.host_computer == null then return end if` |
| 9 | `pc.local_ip` without null-guard | `grep -nE 'pc\.local_ip' *.src` | `ok("... " + (pc.local_ip if pc != null else "unknown"))` |
| 10 | Any `.host_computer` chain from foreign computer | Manual review | Guard immediately before chaining |

**Real-world benchmark (2026-07-04, mxwrap.src, 299 lines):** 10 concrete issues that passed both compiler and the 6-phase audit above.

## Critical API Pitfalls (quick ref)

### Shell method assumptions
- **`get_shell.get_name` does NOT exist.** Use `get_shell.host_computer.lan_ip` / `.public_ip`.
- **`connect_service` returns a STRING on failure, not null.** Always `typeof(remote) == "string"` first.
- **No `shell.cat` / `shell.ls` / `pc.cat`.** Use `pc.File(path).get_content()` / `get_files()`.

### `import_code` vs `include_lib`
- `import_code(absolutePath)` — YOUR code, baked in at compile time. Use for `lib_core`, helpers.
- `include_lib(libPath)` — SYSTEM libraries (`crypto.so`, `metaxploit.so`, `aptclient.so`), loaded at runtime.

### `import_code` Path Resolution — In-Game CodeEditor vs greybel-CLI (NEU 2026-07-15)

**KRITISCHER UNTERSCHIED** zwischen den zwei Build-Pfaden für DB-deployed Scripts:

| Environment | `import_code("yuno_viper_core")` | `import_code("/home/gregor/Config/yuno_viper_core.src")` |
|-------------|:--:|:--:|
| **greybel CLI** (Host-Build) | ✅ Funktioniert — sucht im CWD/Verzeichnis | ❌ **Failed** — interpretiert absoluten Pfad falsch |
| **CodeEditor** (In-Game Build) | ❌ **Failed** — `import_code: File path yuno_viper_core not found.` | ✅ Funktioniert — absoluter Config-Pfad wird erkannt |

**Validierter Workflow (2026-07-15, Viper-Redeploy):**
1. greybel CLI baut mit bare names (`import_code("yuno_viper_core")`) — Host-Testing
2. **Vor DB-Injection** müssen alle `import_code()` auf **absolute In-Game-Pfade** umgestellt werden
3. Korrekter Pfad: `import_code("/home/gregor/Config/yuno_viper_core.src")` — User + Config + `.src`
4. Nach DB-Injection: Spieler öffnet Datei im CodeEditor → Build → läuft

**Pitfall — Dual-Resolution:** greybel braucht bare paths, CodeEditor braucht absolute paths. Workaround: beim Deploy automatisch patchen, oder Source mit absoluten Pfaden schreiben und Sub-Module ohne import_code separat testen. **User-Pfad variabel** — immer Live-DB-Player-Namen verwenden:
```bash
sqlite3 GreyHackDB.db "SELECT Name FROM Players WHERE IsPlayer=1"  # → gregor
```

**Verifikation nach DB-Deploy:**
```bash
sqlite3 GreyHackDB.db "SELECT substr(Content,1,120) FROM Files WHERE ID LIKE '%scan%'" | 
  grep -oE 'import_code\([^)]+\)'
# Erwartet: import_code("/home/gregor/Config/yuno_viper_core.src")
# Nicht: import_code("yuno_viper_core")
```

### Triple type-checking (Crypto / Metaxploit returns)
Always `typeof()` results before processing. May return null / error-string / list / typed object.

### File / Object handling
- Always `f = pc.File(path); if not f then fail(...)` before using.
- Check `f.is_folder` and `f.is_binary` before reading — `get_content` fails on folders.
- `chmod()` returns 1 on success, not the new mode value.

**Full API reference (verified against greyscript-meta 2026-06-27):** `references/api-signatures-verified.md`.

## `//command:` Magic Marker (CRITICAL — discovered 2026-07-03, reality-gap 2026-07-14)

**`//command:` ist PFLICHT für DB-Injection und Auto-Load** — aber **nicht für den CodeEditor-Build-Workflow.** Das ist der wichtigste Unterschied:

| Deployment-Art | `//command:` nötig? |
|----------------|---------------------|
| **DB-Injection** (SQLite INSERT in GreyHackDB.db) | ✅ **Zwingend** als erste Zeile — sonst "Can't build. Binary file." |
| **Direkt in Config/ schreiben** (cat/nano/rsync) | ✅ Nötig — sonst kein Auto-Load beim Shell-Start |
| **CodeEditor paste + Build-Button** (user-präferiert) | ❌ **Nicht nötig** — CodeEditor baut ein echtes Binary, egal welche erste Zeile |

```
//command: my_tool     ← Line 1: nur für DB-Injection / Config-Direkt-Workflow
// rest of script...
```

**REALITÄT-CHECK (Tool-Arsenal-Audit 2026-07-14 / P0-Fix 2026-07-14):**
Das existierende 39-File-Arsenal (`yuno-tools/`) hatte initial **0 von 39 Files** mit `//command:`-Direktive.

**P0-Fix 2026-07-14:** Die 7 aktiven Deploy-Tools + Flagship `yuno_v6` wurden mit `//command:` als Zeile 1 versehen:
- `bank_grab`, `hardening_audit`, `multihop_strike`, `strike1/2/3_*`, `yuno_v6`
- `//command: <name>` — exakter Binary-Name für Launch-Kompatibilität
- Tote/Prototype-Tools (32 weitere) blieben ohne `//command:`
- Backups unter `*.src.bak-cmdfix-20260714`
- Siehe `references/p0-command-fix-2026-07-14.md`

**`yuno-deploy.sh` wurde parallel aktualisiert:**
- Inkludiert jetzt `yuno_v6.src` in der Deploy-Liste (vorher nur 6 Tools)
- Build-Check prüft `//command:` Zeile 1 (❌ bei Fehlen)
- Hardcoded IP `192.168.178.92` → dynamisch via `ip route get`
- Fileserver-Log nach `/tmp/yuno-fileserver.log`
- Exit-Code 0 = alle Checks grün, 1 = Fehler

**Lektion:** Wenn Basti ein neues Tool bekommt, frage NACH dem Workflow:
"Was für ein Deployment? CodeEditor paste (kein `//command:` nötig) oder Deploy-Script (`//command:` Pflicht)?"

**DB injection requirements for executability (FileSystem JSON entry):**
- Content first line: `//command: <name>` (IMPORTED in `Files.Content`)
- `isBinario: false` for source (true only for system built commands like `/bin/cd`)
- `typeFile: 0` for source scripts (verified in V0.9.6771-beta — 0 = regular file)
- **`comando: ""` (MUST be empty string!)** — prevents auto-loading command if non-empty
- **File MUST be in `/home/<USER>/Config/` directory** — sources in `/home/` root are NOT loaded
- **Source size limitation (~12KB ceiling for `//command:` auto-detection)** — keep sources under ~12KB. Anything larger needs modular split or alternative loading. See `references/greyscript-size-limits.md` for validated thresholds, quick-check command, and decision framework.

### Modular Source Splitting for Sources >12KB

Split into **independent modules** under 12KB each. Each module becomes its own shell command with its own `//command:` marker.

**Core pattern — YUNO_SHARED global state bridge:**

```greyscript
// yuno_core.src — Line 1:
//command: yuno_core
if not globals.hasIndex("YUNO_SHARED") then
    YUNO_SHARED = {}
    YUNO_SHARED.style = function(t, c)
        // shared helpers here
    end function
    YUNO_SHARED.main_session = {"version":"6.0.0", "exit": false, "object": get_shell}
end if
style = YUNO_SHARED.style
main_session = YUNO_SHARED.main_session
```

### Parallel Variant Strategy (comment-only trim for just-over-limit files, validated 2026-07-15)

When a single-file tool is **just over** the ~12 KB `//command:` soft limit (12–13 KB) and its runtime logic is stable, the safest approach is **not** a full modular split but a side-by-side parallel variant — keeping the canonical file untouched and trimming ONLY the header/comments in a copy.

**When to use:** Single file, stable runtime, header >1 KB of decorative comments, expected savings ≥500 bytes.

**When NOT to use:**
- File is under 10 KB — **leave it** ("green tools stay untouched")
- Runtime logic needs changes — modular split instead
- File needs one-line-if or ternary to fit — stop (pattern-a ban)

**Procedure:**

1. Copy: `tools/tool.src` → `tools/tool_size_safe.src`
2. Trim ONLY the documentation header (banner comments, redundant usage notes, decorative `====` separators)
3. Keep all `import_code(...)` lines identical
4. Verify body identity: compare both files from the first `import_code(` or code line — must be **byte-identical**
5. Run gates on **both** files:
   - `wc -c` — size-safe must be ≤12288
   - `rg '\bif\b.*\bthen\b.*\bend\s+if\b'` — 0 hits (pattern-a ban)
   - `greybel build <src> /tmp/out` — exits 0
   - `printf '\n0\n' | timeout 15 greybel execute <src> -et Mock --silent` — no runtime error, shows menu
6. Document the relationship so no future agent "fixes" the canonical

**Case study (2026-07-15):** `tools/controlcenter.src` (12560 B → 11386 B for size-safe variant), header-only trim, body identical, both build+mock green. Repo-level doc: `docs/CONTROLCENTER-SIZE-SAFE-PARALLEL.md` in `greyhack-tools`.

**User preference (critical):** Basti's explicit instruction was *"mach einen bug fix und speicher es parallel so das unsere version einwandfrei noch funktioniert"* — **never replace the canonical, always create a parallel copy.** A future agent that overwrites the canonical with the trimmed version violates this preference. The answer to "genereller trimm sinn?" is: **nein** — selective parallel copy only, never bulk-trim green tools, never bulk-apply to the whole repo.

## YUNO VIPER Framework Architecture (v1 — 2026-07-04)

**YUNO VIPER** ist die nächste Framework-Generation nach YUNO V6. Es führt ein neues Module-Registrierungssystem ein — das `h`-Dict statt V6's `commands`-Dict — sowie eigene Konstanten (`I.F*`), einen Colorizer (`N()`), und spezielle Globals (`Z` = Computer, `P` = State).

| Aspekt | YUNO V6 | YUNO VIPER |
|--------|---------|-------------|
| Command-Dict | `commands = { "cmd": @handler, ... }` | `h = { "cmd": HandlerObj, ... }` |
| Color-Konstanten | String-Referenzen | `I.F*` Container von Core |
| Colorizer | `style(text, "red")` | `N(text, I.FC)` |
| Computer-Zugriff | `get_shell.host_computer` | `Z` Global (einmal init in Core) |
| State-Object | `main_session` (Map) | `P` (Map: Profiler-Object) |
| Module-Header | `//command: <name>` | `//command: <name>` + `//include: yuno_viper_core` |
| Handler-Struktur | `cmd_X.run = function(args)` | `UtilX = {}` + `UtilX.run = function(Cc)` |
| Interaktion | Passiv (Argumente) | Aktiv (`user_input()`) |

**VIPER-Module-Skeleton:**

```greyscript
//command: yuno_viper_beispiel
//include: yuno_viper_core

UtilBeispiel = {}
UtilBeispiel.run = function(Cc)
    BX = Z
    if not BX then return
    BE = I.Fa + P.current_user
    if P.current_user == I.FU then BE = I.Fx
    Cd = BX.File(BE + I.Fh + "datei.txt")
    if not Cd then
        print(N("[!] Fehler", I.FC))
        return
    end if
    print(N("[+] Erfolg", I.FD))
end function

if not h then h = {} end if
h["beispiel"] = UtilBeispiel
```

## Dynamic Code Generation

**Problem:** Some GreyScript tools need to dynamically generate `.src` files at runtime. The naive approach of embedding `"` inside a `"..."` string causes **Compiler Error**.

**Fix — use `char(34)` for ANY inner quote in dynamically-generated code:**

```greyscript
// Generates: pass = "pass" (as a string of GreyScript code)
content = content + "pass = " + char(34) + "pass" + char(34) + char(10)
```

**Translation table for dynamic string building:**

| Intended Generated Code | WRONG Pattern | RIGHT Pattern |
|------------------------|---------------|---------------|
| `pass = "pass"` | `"pass = "pass""` | `"pass = " + char(34) + "pass" + char(34)` |
| `shell = connect("IP",...)` | `"connect(""IP"",...)"` | `"connect(" + char(34) + IP + char(34) + ",...)"` |

## Deployment Debugging: Mini-Test-First Pattern

**Pattern — always test in this order:**

1. **Deploy a 1.5KB proof-of-concept first.** This verifies the PIPELINE is correct.
2. **Only when the tiny script works, scale up.**
3. **If the PoC works but the real script doesn't, the issue is size or content.**

## First Script / Beginner Tutorial Pattern

When a new user is IN the game (not on the host), teach them the **two-step flow** before any code:

1. **Write** a `.src` file via `cat > /home/<USER>/Config/script.src`
2. **Type** `<name>` in the shell — the command auto-loads if placed in Config/

## Core Library (`lib_core.src`)

See `templates/lib_core.src` for the canonical starter. Must include:

| Group | Functions |
|-------|-----------|
| Output | `render()`, `hr()`, `banner()` |
| Status | `fail()`, `warn()`, `ok()`, `info()`, `step()` |
| Params | `requireParam()`, `optionalParam()`, `lastParam()` |
| Validation | `validIP()`, `validPort()` |
| Files | `getFile()`, `getDir()`, `fileExists()`, `ensureDir()` |
| Context | `getContext()` |
| Help/Prompt | `showHelp()`, `confirm()` |
| Logging | `logToFile()` |

## Workflow Metaxploit (6 Stufen)

1. `meta = include_lib("/lib/metaxploit.so"); if not meta then fail("not found")`
2. `lib = meta.load(path)` for local OR `net = meta.net_use(ip, port); lib = net.dump_lib` for remote
3. `print(lib.lib_name); print(lib.version)`
4. `addrs = meta.scan(lib)`
5. For each `addr`: `info = meta.scan_address(lib, addr)`
6. `result = lib.overflow(addr, unsecValue)` — **always typeof() before processing**

## greybel-js Interpreter (Testing Outside the Game)

```bash
greybel execute script.src -et Mock -si    # execute in mock mode
greybel build script.src /tmp/output/ -dbf # build (compile)
```

**Mock Environment Limitations:** outdated, does NOT support `computer.ConfigOS`, `computer.users`, `computer.FileSystem.GetFolder`, `include_lib`, most Computer properties. **Critical: `map.keys` does NOT exist in greybel-js mock mode** — use `myMap.indexes` instead.

## Code Smells to Call Out

1. Repeated `get_shell.host_computer` calls — capture once to `shell`/`pc`.
2. God-scripts doing scan + SSH + copy + exploit + menu — one script, one job.
3. Error checked too late — check return value immediately after every API call.
4. Clever string formatting — prefer simple lines and short headers.
5. No `--help` output — a tool that can't explain itself is half-finished.
6. **Hardcoded `127.0.0.1` in Flatpak environments** — use LAN-IP for Host-Zugriff.
7. **Annahme dass Host-Dateien im Spiel sichtbar sind** — deployment required (installer, copy-paste, SQLite).

## Compile-First Workflow

User communicates in German. Respond in German, keep comments and print strings in German, but use English identifiers in code (`shell`, `pc`, `fail`).

**Always compile incrementally, not in bulk.** Preferred sequence:

1. Edit only `lib_core.src` first; compile and sanity-check with `--help`.
2. Then build one tool at a time.
3. Only after all core tools compile, run `build_all` as a final verification step.

## Deployment (Stufe 2→3)

GreyHack läuft als Steam-Flatpak → **kein direkter Host-Datei-Zugriff**. `~/greyhack-tools/` ist vom Spiel aus nicht sichtbar.

**KRITISCH:** GreyScript hat KEINEN `HTTP.Request()` Befehl. Drei Wege: (1) **greybel-js Installer** (bevorzugt); (2) **Manueller Copy-Paste** für Dateien <160K Zeichen; (3) **SQLite-Injektion** (Persistenz über Neustarts).

### DB Duplicate Cleanup

**Problem:** Jedes Mal wenn ein Modul mit demselben `//command:` Marker erneut injiziert wird, entsteht ein DUPLIKAT-Eintrag. Das Spiel lädt das ERSTE passende File — nicht unbedingt die aktuellste Version.

**Erkennung & Cleanup:** Siehe `references/deployment.md`.

### CodeEditor-Direkt-Workflow (PRIMÄR — user-preferred ab 2026-07-03)

Der Benutzer baut SELBER — `.src`-Dateien in Config/ ablegen, der User öffnet sie im CodeEditor, editiert/pasted und buildet selbst.

**Ablauf (User-seitig im Game):**
1. Yuno sorgt dafür dass die `.src` in `/home/gregor/Config/` liegt
2. Im Spiel: Computer → CodeEditor → Ctrl+O → Datei auswählen
3. Ctrl+A → aus Chat neue Version pasten (bei Updates)
4. Ctrl+S → speichern
5. Build-Button → kompiliert zu Binary
6. Close → Shell → `/bin/<name>` → ausführen

## Hermes GreyHack Co-Pilot

Zwei UIs für Hermes-Integration:
- **Host-Terminal:** `~/bin/hermes-ask "frage"` (Alt-Tab nötig)
- **Steam-Overlay-UI:** `http://127.0.0.1:8766/` (Shift+Tab)

GreyScript kann den Hermes-API-Server (Port 8333) NICHT direkt ansprechen (kein HTTP). Setup, CORS-Preflight-Pitfall mit `do_OPTIONS()` Fix, API-Endpunkte, Architektur: `references/hermes-gh-api-server.md` + `references/copilot-web-ui.md`.

## Module Development Conventions (Network APIs)

When writing GreyScript modules that interact with network APIs, follow the patterns in `references/greyscript-network-api-patterns.md`.

**Module skeleton for network tools:**
```greyscript
//command: <name>
//include: <core>

PREFIX_safe_router = function(ip)
    // local gateway fallback + connect_service remote
end function
```

**Key API methods covered in the reference:**
- `connect_service(ip,22,"root","","ssh")` — returns `Service` (success) or `string` (error)
- `router.whois_info(ip)` — returns `string`/`map` or `null`
- `PortSniffer.start_sniffer(router, port)` — returns `bool` or `false`
- `pc.trace_route(target)` — returns `list` (hops) or `null`/`string`
- `router.device_ports(ip)` / `used_ports` — returns `list` (port-maps) or `null`/`string`
- `router.devices_lan_ip` — returns `list` (IP strings) or `null`/`string`
- `chat.so.join_channel(svc,chan,nick)` — returns service obj or `null`

## Support Files

- `references/tool-arsenal-audit-2026-07-14.md` — Arsenal-Audit-Methodik + Real-World-Data-Point (0/39 Files mit `//command:`, 2026-07-14)
- `templates/lib_core.src` — core library starter
- `references/api-objects.md` — Shell/Computer/File/Router/Crypto/Metaxploit/AptClient methods
- `references/api-signatures-verified.md` — verified API signatures (2026-06-27)
- `references/greyscript-library-catalog.md` — 20 libraries: live DB hashes, function signatures, pitfalls (2026-07-14)
- `references/language-pitfalls.md` — full critical-pitfall reference
- `references/p0-pattern-reference-2026-06-25.md` — auto-fix recipes
- `references/third-party-pack-evaluation.md` — **NEU 2026-07-15:** 7-step methodology for evaluating external AI-generated GreyScript packs against a hardened baseline. Similarity scoring, P0 pattern scan, build + mock verify, report cross-ref, merge recommendation framework. Includes real GLM 5.2 Starter Pack case study (3.5/10 → reject as master).
- `references/greyscript-size-limits.md` — **NEU 2026-07-15:** Validated `//command:` auto-load size thresholds (12KB soft ceiling), quick-check command, per-tool size decision framework, real-world repo sizes.
- `references/parallel-variant-controlcenter-2026-07-15.md` — **NEU 2026-07-15:** Case study: parallel size-safe variant for `controlcenter.src`. Body-identity gate, user preference (never replace canonical), gate results (12560B→11386B).
- `references/viper-reexport-build-mock-pipeline.md` — **NEU 2026-07-15:** Systematic Viper v1 module re-export health check. 5 module build + mock-smoke setup (core in `build/root/` für sub-modules via `import_code`), pattern scan, bekanntes util-Mock-Quirk (pre-shortened source, `Path "h"` not found), strukturiertes Report-Format.
- `references/greydecode-notes.md` — condensed Greydecode 1.5 Extended Edition PDF notes
- `references/known-quirks.md` — concrete compile-time traps and workarounds
- `references/greyscript-network-api-patterns.md` — Network API patterns
- `references/deployment.md` — Steam Flatpak deployment workflows
- `references/greybel-js-workaround.md` — greybel-js path resolution workaround
- `references/greybel-js-interpreter.md` — Mock Environment, VSCode extension
- `references/in-game-shell-commands.md` — terminal/file/network command reference
- `references/hermes-gh-api-server.md` — API server setup, endpoints
- `references/sqlite-database.md` — DB structure and filesystem JSON layout
- `references/viper-guide-structure.md` — Lib_core-basierte Viper-Guide-Architektur
- `scripts/extract-paired-blocks.py` — CLI to extract paired `cmd_X = {}` + `cmd_X.run = function` blocks
- `scripts/bug-scan-pattern-audit.sh` — Static-Scan + Build-Verifikation mit 14 Patterns
- `scripts/greyhack-bug-scan.py` — Full-repo bug scanner

## 🧭 Related Skills (Cross-Cluster Navigation)

Skills that support this GreyScript cluster but live elsewhere:

- **`skill-navigator`** (orchestration/) — Meta-Navigator for all 169 Hermes skills
- **`multi-agent-pitfalls-cheatsheet`** (orchestration/) — TRIGGER-WATCHLIST for `delegate_task` calls
- **`multi-agent-orchestration`** (orchestration/) — The 3-Expert Research PATTERN
- **`multi-agent-code-gen-pipeline`** (orchestration/) — 6-Phase pipeline for building multi-module GreyHack tools
