# GreyScript Null-Safety & Robustness Audit (10-Point Checklist)

## Problem

The existing static code audit finds compiler bugs, cross-module refs, variable mismatches, dead code, and init gaps — but misses **runtime null-safety** issues. These are patterns where the code compiles fine, runs, but crashes when an intermediate value in a property chain is `null`. Metaxploit-wrapper code (net_use, run_exploit, chmod, device_ports) is especially vulnerable because GreyScript propagates `null` silently through chained access.

## When to run this audit

AFTER the 6-phase deep-bug-search above passes clean. The null-safety audit is a second pass that catches runtime crashers that the first pass cannot see.

## Trigger

User asks to "audit" or "bug-search" a GreyScript file that deals with metaxploit, network connections, shells, or remote computers. Run this checklist AFTER the main 6-phase audit passes clean.

## 10-Point Checklist — scan in this order (all checks independent)

| # | Pattern | Problem | Search Hint | Fix Template |
|---|---------|---------|------------|--------------|
| 1 | `get_shell.host_computer.*` without null-guard | `get_shell` returns `null` in automated/headless contexts; chained `.host_computer` → null-ref crash | `grep -nE 'get_shell\.host_computer' *.src` | `sh = get_shell; if not sh then return end if; pc = sh.host_computer; if not pc then return end if` |
| 2 | Port `0` in `net_use(ip, 0)` | Port `0` is the kernel local-port, NOT a remote network port. `net_use` with port `0` returns `null` for remote IPs — the attempt always fails remotely | `grep -nE 'net_use\(.*,\s*0\b' *.src` | Use the actual kernel-service port (`targetShell.host_computer.kernel_version` check + local router), or pass a valid remote port |
| 3 | `run_exploit` result used without `typeof(shell) == "shell"` check | `run_exploit` may return a dead/exploded shell that has no `host_computer` property. Crashing on `.host_computer` is the #1 runtime null-ref in exploit chains | `grep -nE 'run_exploit\(.*\)' *.src` | After any `shell = session.run_exploit(...)`, add: `if typeof(shell) != "shell" then return null end if` |
| 4 | `chmod(path, perms, true)` with root path `"/"` | Recursive `chmod("/", "o-rwx", true)` blacks out the entire filesystem — bricks all services, locks the user out. GreyHack sandbox typically forbids this | `grep -nE 'chmod\("/",' *.src` | Target specific directories: `chmod("/etc", "o-rwx", true)` — never root `/` |
| 5 | `chmod()` return values silently discarded | `chmod()` returns a string error message on failure. Discarding the return = user has zero feedback that permissions weren't actually set | `grep -nE '\.chmod\(' *.src \| grep -vE '^\\s*res?\\s*='` | Wrap each call: `res = pc.chmod(...); if typeof(res) == "string" then warn("[!] chmod: " + res) end if` |
| 6 | Router via `network_gateway` as if it were a Router object | Mock+meta 2026-07-14: `pc.network_gateway` is often an **IP string**, not a router. Calling `.device_ports` on it hard-crashes. Prefer `get_router` | `grep -nE 'network_gateway' *.src` | `r = get_router; if r == null or typeof(r) == "string" then return end if` — use `network_gateway` only as string IP if needed |
| 7 | `router.device_ports(ip)` without null-guard on router | If `network_gateway` is null (step 6), `router.device_ports(ip)` throws null-ref BEFORE the existing `if ports == null` guard on the return value | `grep -nE 'device_ports' *.src` | `if router == null then return [] end if` BEFORE any router method call |
| 8 | `targetShell.host_computer` without null-check | If `targetShell` is a dead shell or null (from a failed exploit in a prior step), chained `.host_computer` throws null-ref | `grep -nE 'targetShell\.host_computer' *.src` | `if targetShell == null or targetShell.host_computer == null then return end if` before dereferencing |
| 9 | `pc.local_ip` without null-guard | If `pc` is null (from any prior failure), accessing `pc.local_ip` in confirmation/diagnostic output crashes | `grep -nE 'pc\.local_ip' *.src` | `ok("... " + (pc.local_ip if pc != null else "unknown"))` |
| 10 | Any `.host_computer` chain from a foreign computer object | SSH shells, kernel shells, and remote exploit shells all provide `host_computer` but it may be a different machine than expected, or null if the connection dropped | Manual review of every `variable.host_computer` in the file | After each assignment to a shell-type variable, guard immediately before chaining |

## Verification after fixes

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

## Severity classification (override the main audit's classification for null-safety issues)

| Severity | Definition | Action |
|----------|------------|--------|
| 🔴 runtime | Code compiles but crashes when intermediate value is null | Fix immediately, all 10 checks are runtime-crashers |
| 🟠 logic | Produces wrong output or destructive side effects (e.g. chmod /) | Fix before use |
| 🟡 warning | Code smell, silent failure, no crash risk | Report but non-blocking |

## Real-world benchmark (2026-07-04, mxwrap.src, 299 lines, 12 function blocks)

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

## Why the existing 6-phase audit misses these

The main audit checks control-flow balance, cross-module symbols, variable names, dead code, and init-gaps — but has no check for intermediate-value null propagation. GreyScript's `null` silently propagates through chained access (`a.b.c` where `a.b` is null crashes with `Path 'c' not found in null`). The null-safety audit is a mandatory second pass for any file that calls `net_use`, `run_exploit`, or accesses `.host_computer` chains.