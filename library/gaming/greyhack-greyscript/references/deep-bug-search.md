# Static Code Audit: Deep Bug Search

A GreyScript file that the user asks you to "bug-search" may have NO compiler errors and NO runtime test bed available. This audit works on source alone — no `build`, no in-game execution, no feedback loop. It finds issues the compiler cannot catch.

## Trigger

User asks for "Deep Bug Search", "Audit", "Find bugs", or "Scan for issues" on a `.src` file.

## Order — scan in this sequence (each check independent, no runtime needed)

### 1. Balance Analysis — Control Flow Matching

Track `if X then` block-opens (multi-line only) vs `end if` block-closes. These patterns are NOT mismatches:
- **`else if` chains**: `if A then... else if B then... else if C then... end if` — 3 `if` tokens but exactly 1 `end if`. The `else if` opens NO new block in GreyScript.
- **Inline `if X then Y else Z end if`** — one single balanced line with 1 `if` and 1 `end if`. The whole chain opens and closes on one line.

For the adjusted count, exclude BOTH patterns from the comparison:

```bash
# Bash-based balance check (corrects for else-if chain counting)
if_count=$(grep -coE '\bif\b' file.src)
endif_count=$(grep -co '\bend if\b' file.src)
oneline_if_count=$(grep -cE '^\s*if\s+.+\s+then\s+\S+\s*(//.*)?$' file.src)
elseif_count=$(grep -cE '\belse if\b' file.src)
# else if chains: each has its own `if` token but shares `end if` with the head block
adjusted_if=$((if_count - oneline_if_count - elseif_count))
if [ "$adjusted_if" != "$endif_count" ]; then
    echo "MISMATCH: $if_count if ($oneline_if_count one-line, $elseif_count else-if) - $adjusted_if adjusted vs $endif_count end if"
fi
```

Do the same for `function` vs `end function`:

```bash
func_count=$(grep -cE '^\s*(function|\.\w+\s*=\s*function)\b' file.src)
endfunc_count=$(grep -cE '^\s*end function\b' file.src)
```

**Case study (this session):** `yuno_attack.src` (295 lines): 50 `if` - 11 one-line = 39 adjusted vs 39 `end if` ✅. 7 functions (1 inner style=function + 6 cmd_X.run=function) = 7 `end function` ✅.

### 2. Cross-Module Reference Audit

When a file is part of a multi-module toolset (e.g. YUNO_SHARED architecture), every symbol that is NOT defined in the file itself is a potential runtime undefined-variable crash.

Scan for all-CAPS constants and bare function names that aren't defined locally:

```bash
# Find all symbols that look like cross-module references
grep -oE '\b[A-Z_]{3,}\b' file.src | sort -u | while read sym; do
    # Is it defined in THIS file?
    if ! grep -qE "^\s*$sym\s*=" file.src; then
        echo "UNDEFINED IN FILE: $sym"
    fi
done
```

**Known cross-module symbols from the YUNO/YUMA architecture (check these specifically):**
- `COMMON_PORTS`, `BRUTE_USERS`, `BRUTE_PASSES` — should be in core module (`yuno_core.src` or similar)
- `try_exploit`, `read_configs`, `exploit_scan`, `nmap_scan` — function-level; verify the defining module exists
- `commands` — the local dispatch map; MUST be defined in each module that uses `commands[cmd].run()`
- `main_session.*` fields — every field accessed across modules must exist in the core initializer
- **`obj`** — MUST be initialized with `obj = main_session.object` before any `obj.host_computer` or `obj.passwd()` usage. Many modules access `obj` as if it's a global, but it's actually a local variable that each module must assign. **This is the #1 cross-module lowercase-variable bug.** Unlike ALL-CAPS symbols, `obj` looks like a parameter or local initializer — the compiler never warns, and the crash only happens at runtime when `obj.host_computer.File()` or `obj.passwd()` is called.

Also check neighbouring modules to confirm they define the symbols your target file uses:

```bash
for sym in COMMON_PORTS BRUTE_USERS BRUTE_PASSES try_exploit read_configs; do
    grep -rn "^\s*$sym\s*=" ../*.src 2>/dev/null || echo "NOWHERE DEFINED: $sym"
done
```

### 3. Variable Name Mismatch Pattern (Copy-Paste Residue)

After a variable rename or module extraction, a function may reference an OLD variable name that no longer exists in scope. This is the #1 copy-paste bug.

Search for EVERY `function(args)` and check that all bare identifiers in the body are either:
- Already assigned in that function
- Already assigned at module scope
- Known API globals (`get_shell`, `include_lib`, `print`, `char`, `val`, `str`, `typeof`, `globals`)
- Parameters (`args` + whatever you destructure from `params`)

**Common patterns that signal a mismatch:**
- `read_configs(obj)` where `obj` is never assigned — the original function used `obj` from a different scope; intended `pc` (or the current context variable)
- `main_session.object` used where `main_session.objectList` was intended (singular vs plural swap)
- `netcatList` accessed in one module but the core initializer doesn't have `"netcatList":{}` — see #5

### 4. Dead Code Block Detection (Double Guard Pattern)

A `if not <condition> then return end if` guard followed immediately by a SECOND `if not <condition> then` block is dead code. The second block can never execute because the first guard already returned.

```greyscript
// BUG — second block below is UNREACHABLE:
if not pc then
    return
end if

// THIS NEVER RUNS:
if not pc then
    print(style("[!] No host computer!", "red"))
    return
end if
```

Detect with:

```bash
# Find consecutive guard blocks referencing the same variable
grep -n -A5 'if not .* then' file.src | grep -B2 -A5 'if not .* then'
```

### 5. Initialization Gap Pattern — Fields Used but Not in the Init Dict

For shared state objects (`main_session`, `YUNO_SHARED`), every field accessed as `main_session.someField` must exist in the initializer's dictionary literal.

Method:
1. Collect ALL dot-accesses: `grep -oE 'main_session\.\w+' file.src ../*.src 2>/dev/null | sort -u`
2. Compare against the init dict keys in the core module
3. Flag any field that's accessed but not initialized

**Fix:** Add the missing field to the init dict with a sensible default:

```greyscript
// Core initializer — add objectList if cmd_ssh stores connections there:
main_session = {
    ...
    "objectList": [],     // ← was missing, causes Key Not Found crash
    ...
}
```

### 6. Severity Classification

Assign every finding to one of these categories BEFORE reporting to the user:

| Severity | Definition | Action |
|----------|------------|--------|
| `compiler` | Would cause `build` to reject the file | Fix immediately |
| `runtime` | File builds but crashes on execution | Fix before use |
| `logic` | Produces wrong output or dead code | Fix for correctness |
| `warning` | Code smell, no runtime impact | Report but non-blocking |

### 7. GreyScript Null-Safety & Robustness Audit (10-Point Checklist)

**Problem:** The existing static code audit (sections 1-6 above) finds compiler bugs, cross-module refs, variable mismatches, dead code, and init gaps — but misses **runtime null-safety** issues. These are patterns where the code compiles fine, runs, but crashes when an intermediate value in a property chain is `null`. Metaxploit-wrapper code (net_use, run_exploit, chmod, device_ports) is especially vulnerable because GreyScript propagates `null` silently through chained access.

**When to run this audit:** AFTER the 6-phase deep-bug-search above passes clean. The null-safety audit is a second pass that catches runtime crashers that the first pass cannot see.

**Trigger:** User asks to "audit" or "bug-search" a GreyScript file that deals with metaxploit, network connections, shells, or remote computers. Run this checklist AFTER the main 6-phase audit passes clean.

**10-Point Checklist — scan in this order (all checks independent):**

| # | Pattern | Problem | Search Hint | Fix Template |
|---|---------|---------|------------|--------------|
| 1 | `get_shell.host_computer.*` without null-guard | `get_shell` returns `null` in automated/headless contexts; chained `.host_computer` → null-ref crash | `grep -nE 'get_shell\.host_computer' *.src` | `sh = get_shell; if not sh then return end if; pc = sh.host_computer; if not pc then return end if` |
| 2 | Port `0` in `net_use(ip, 0)` | Port `0` is the kernel local-port, NOT a remote network port. `net_use` with port `0` returns `null` for remote IPs — the attempt always fails remotely | `grep -nE 'net_use\(.*,\s*0\b' *.src` | Use the actual kernel-service port (`targetShell.host_computer.kernel_version` check + local router), or pass a valid remote port |
| 3 | `run_exploit` result used without `typeof(shell) == "shell"` check | `run_exploit` may return a dead/exploded shell that has no `host_computer` property. Crashing on `.host_computer` is the #1 runtime null-ref in exploit chains | `grep -nE 'run_exploit\(.*\)' *.src` | After any `shell = session.run_exploit(...)`, add: `if typeof(shell) != "shell" then return null end if` |
| 4 | `chmod(path, perms, true)` with root path `"/"` | Recursive `chmod("/", "o-rwx", true)` blacks out the entire filesystem — bricks all services, locks the user out. GreyHack sandbox typically forbids this | `grep -nE 'chmod\("/",' *.src` | Target specific directories: `chmod("/etc", "o-rwx", true)` — never root `/` |
| 5 | `chmod()` return values silently discarded | `chmod()` returns a string error message on failure. Discarding the return = user has zero feedback that permissions weren't actually set | `grep -nE '\.chmod\(' *.src \| grep -vE '^\\s*res?\\s*='` | Wrap each call: `res = pc.chmod(...); if typeof(res) == "string" then warn("[!] chmod: " + res) end if` |
| 6 | `network_gateway` used without null-guard | `sh.host_computer.network_gateway` returns `null` when the shell's computer has no active gateway (offline, or shell is on a target PC, not the local router) | `grep -nE 'network_gateway' *.src` | `router = sh.host_computer.network_gateway if sh != null and sh.host_computer != null else null` |
| 7 | `router.device_ports(ip)` without null-guard on router | If `network_gateway` is null (step 6), `router.device_ports(ip)` throws null-ref BEFORE the existing `if ports == null` guard on the return value | `grep -nE 'device_ports' *.src` | `if router == null then return [] end if` BEFORE any router method call |
| 8 | `targetShell.host_computer` without null-check | If `targetShell` is a dead shell or null (from a failed exploit in a prior step), chained `.host_computer` throws null-ref | `grep -nE 'targetShell\.host_computer' *.src` | `if targetShell == null or targetShell.host_computer == null then return end if` before dereferencing |
| 9 | `pc.local_ip` without null-guard | If `pc` is null (from any prior failure), accessing `pc.local_ip` in confirmation/diagnostic output crashes | `grep -nE 'pc\.local_ip' *.src` | `ok("... " + (pc.local_ip if pc != null else "unknown"))` |
| 10 | Any `.host_computer` chain from a foreign computer object | SSH shells, kernel shells, and remote exploit shells all provide `host_computer` but it may be a different machine than expected, or null if the connection dropped | Manual review of every `variable.host_computer` in the file | After each assignment to a shell-type variable, guard immediately before chaining |

**Verification after fixes:**

```bash
# Check all get_shell.host_computer chains are guarded
grep -nE 'get_shell\.host_computer' FILE.src

# Check all chmod return values are captured (not just called for side effect)
grep -nE '\.chmod\(' FILE.src | grep -vE '^\\s*(res|r)\s*='

# Check all .host_computer dereferences are null-guarded
grep -nE '\.host_computer\.' FILE.src

# Verify null-guard count vs property-access count (should approximately match)
echo "get_shell.host_computer: $(grep -c 'get_shell\.host_computer' FILE.src)"
echo "null check: $(grep -c 'host_computer == null\|host_computer!' FILE.src)"
```

**Severity classification (override the main audit's classification for null-safety issues):**

| Severity | Definition | Action |
|----------|------------|--------|
| 🔴 runtime | Code compiles but crashes when intermediate value is null | Fix immediately, all 10 checks are runtime-crashers |
| 🟠 logic | Produces wrong output or destructive side effects (e.g. chmod /) | Fix before use |
| 🟡 warning | Code smell, silent failure, no crash risk | Report but non-blocking |

**Real-world benchmark (2026-07-04, mxwrap.src, 299 lines, 12 function blocks):**

| # | Pattern | Findings | Severity |
|---|---------|----------|----------|
| 1 | get_shell null guard | L27 | 🔴 runtime — silent null-ref |
| 2 | Port 0 in net_use | L140 | 🔴 runtime — always-fails remotely |
| 3 | typeof shell after run_exploit | L147 | 🔴 runtime — dead shell can't provide host_computer |
| 4 | chmod("/", ...) root path | L153 | 🟠 logic — bricks filesystem |
| 5 | chmod return values discarded | L206-210 (5 calls) | 🟡 warning — silent failures |
| 6 | network_gateway null guard | L168 | 🔴 runtime — router not checked |
| 7 | router null before device_ports | L170 | 🔴 runtime — null-ref before existing guard |
| 8 | targetShell null check | L205 | 🔴 runtime — null-ref on all chmods |
| 9 | pc.local_ip null guard | L211 | 🟡 warning — confirmation output crashes |
| 10 | host_computer chain audit | L27, 168, 205 | 🔴 runtime — each unguarded |

Total: **10 concrete issues** in 299 lines that passed both compiler and the 6-phase audit above. All 10 are runtime or logic bugs the existing deep-bug-search would NOT flag.

**Why the existing 6-phase audit misses these:** The main audit checks control-flow balance, cross-module symbols, variable names, dead code, and init-gaps — but has no check for intermediate-value null propagation. GreyScript's `null` silently propagates through chained access (`a.b.c` where `a.b` is null crashes with `Path 'c' not found in null`). The null-safety audit is a mandatory second pass for any file that calls `net_use`, `run_exploit`, or accesses `.host_computer` chains.