# Pre-Flight-Check / Mission-Readiness Gate

> **Class:** Environment-readiness validation for autonomous systems BEFORE the dry-run, BEFORE live execution.
> **Trigger:** Any system that depends on external prerequisites (binaries, credentials, window detection, network services, APIs, mounted paths) must pass a pre-flight check before the dry-run is meaningful.
> **Source:** GreyHack Mission Orchestrator (`greyhack-mission-orchestrator`) buildout, 2026-07-06.

## The Distinction: Pre-Flight vs. Dry-Run vs. Live-Execute

| Gate | What it validates | Failure mode it prevents | Time/Cost |
|------|-------------------|---------------------------|-----------|
| **Pre-Flight Check** | Environment, binaries, credentials, paths, hardware, network | "Python script works but cua-driver is missing" — script fails on first import | Seconds; catches ~70% of "won't run at all" failures |
| **Dry-Run** | Script logic, parsing, state transitions, kill-switch logic | "Script runs but parses 0 steps and silently does nothing" | Seconds-minutes; catches semantic/logic bugs |
| **Live-Execute** | Actual production behavior with real side effects | Real-world side effects (game state, file writes, API calls) | Minutes-hours; once started, aborting is expensive |

**The lesson from the GreyHack orchestrator build:** Even before running the dry-run, the environment itself was broken in two ways:
1. `cua-driver` not installed → `from hermes_tools import computer_use` raises `ImportError`
2. `wmctrl`/`grim` not installed → window detection fails

A dry-run on a broken environment yields "ImportError" — which is technically valid output but not the bugs you wanted to catch. Pre-flight closes that gap.

## Why Pre-Flight is a Distinct Gate

Dry-run alone is insufficient when:
- **The script depends on binaries you didn't write** (system packages, external CLIs)
- **The script depends on credentials/keys** (API tokens, bot tokens, OAuth credentials)
- **The script depends on live services** (a window manager detecting an app, a database, a daemon)
- **The script depends on filesystem state** (paths exist, files are readable, disk space available)
- **Hardware is involved** (GPU drivers, audio devices, USB hardware)

In these cases, the dry-run can only validate logic — the environment must be validated separately, BEFORE the dry-run, BEFORE live execution.

## The Pre-Flight-Check Architecture (3-Tier Severity)

Every check has a severity flag that determines whether the mission can proceed:

| Severity | Meaning | Mission Status | Examples |
|----------|---------|----------------|----------|
| **CRITICAL** | Mission cannot start without this | NO-GO (exit code 2) | cua-driver missing, Telegram token absent, mission file unparseable |
| **OPTIONAL** | Mission can run but quality may degrade | CONDITIONAL GO (exit code 1) | Screenshot fallback tool, window-detection tool, log-rotation setup |
| **INFO** | Diagnostic only, no impact on GO/NO-GO | Always PASS | Disk space, Python version, log path writability |

## Pre-Flight-Check Script Pattern (Proven 2026-07-06)

The proven architecture from the GreyHack orchestrator:

```python
@dataclass
class CheckResult:
    name: str
    passed: bool
    critical: bool  # If True: NO-GO if failed
    message: str
    details: Optional[str] = None
    fix_suggestion: Optional[str] = None  # What to do if it fails

@dataclass
class PreFlightReport:
    critical_passed: bool  # All critical checks passed?
    all_passed: bool       # All checks (critical + optional) passed?

def run_all_checks() -> PreFlightReport:
    """Aggregate all checks into a single report."""
    report = PreFlightReport(critical_passed=True, all_passed=True)
    for check_fn in [
        check_critical_binary,         # e.g. cua-driver import
        check_critical_service,        # e.g. Telegram token valid
        check_optional_tool,           # e.g. wmctrl present
        check_paths_exist,             # e.g. mission file readable
        check_state_machine_isolated,  # e.g. state classes importable
        check_disk_space,              # e.g. enough GB free
    ]:
        result = check_fn()
        report.add(result)
    return report
```

### Output Modes (Human, Verbose, JSON)

The check must support three output modes:

```bash
# Human-readable for terminal (default)
python3 preflight_check.py

# Verbose for debugging
python3 preflight_check.py --verbose

# JSON for CI/CD pipelines
python3 preflight_check.py --json
```

### Exit Code Semantics (CI/CD-friendly)

```python
# 0 = GO (all checks pass)
# 1 = CONDITIONAL GO (critical OK, optional failed)
# 2 = NO-GO (critical failed — DO NOT proceed)
sys.exit(0 if report.critical_passed else 2)
```

This exit-code semantics is critical for:
- Shell scripts that gate on pre-flight results
- Cron jobs that abort if environment breaks
- Multi-agent orchestrators that check prerequisites before dispatching

## The 10-Standard-Check Battery (Adopted 2026-07-06)

For ANY autonomous system build, run these 10 checks at minimum:

| # | Check | Critical? | Example Fix Suggestion |
|---|-------|-----------|------------------------|
| 1 | Core binary/library importable | YES | `pip install <lib>` or `hermes <feature> install` |
| 2 | External CLI tool available | YES | `sudo apt install <tool>` |
| 3 | All filesystem paths exist and readable | YES | `mkdir -p <path>` or fix typo |
| 4 | Target file/asset parseable | YES | Re-export or regenerate the input |
| 5 | Credentials/tokens present | YES | Add to `~/.config/<service>/credentials` |
| 6 | Live service connectivity | NO | Verify network, restart daemon |
| 7 | Target window/process detectable | NO | Start the application first |
| 8 | Screenshot/input fallback tool | NO | `sudo apt install scrot` |
| 9 | Critical logic (e.g. kill-switch) functional | NO | Re-import module, run isolated test |
| 10 | Resource constraints (disk, memory, handles) | NO | Cleanup, restart, or escalate |

The GreyHack orchestrator pre-flight caught **3 of these as critical fails** (cua-driver missing, environment not importable, validation logic not yet tested) and **2 as optional fails** (wmctrl missing, kill-switch logic not yet proven). Without pre-flight, the dry-run would have wasted 30 seconds on an "ImportError" instead of starting its semantic validation.

## The Pre-Flight + Dry-Run + Live-Execute Pipeline

```
┌─────────────────┐
│  Pre-Flight     │  ← "Is the environment ready?"
│  Check          │
└────────┬────────┘
         │  Exit 0 (GO) or 1 (CONDITIONAL) — proceed
         │  Exit 2 (NO-GO) — abort, fix environment
         ▼
┌─────────────────┐
│  Dry-Run        │  ← "Does the script work in isolation?"
│  (--dry-run)    │
└────────┬────────┘
         │  Output matches expected structure
         │  All state transitions valid
         │  Kill-switch logic proven
         │  ────────────────
         ▼  Proceed
┌─────────────────┐
│  Live-Execute   │  ← "Does the system produce real results?"
│  (no --dry-run) │
└─────────────────┘
```

## Writing a Pre-Flight Check: 5 Rules

1. **Every check is a separate function** with a clear name. `check_<thing>` returns a `CheckResult`.
2. **Every check has a fix_suggestion** for failures. The user shouldn't have to dig for the fix.
3. **Critical vs. Optional severity is explicit** in the check definition, not inferred.
4. **All checks run, even on first failure.** Don't abort on first fail — show the full picture so the user can fix everything in one cycle.
5. **Exit codes map to mission readiness**, not just pass/fail. 0=GO, 1=CONDITIONAL, 2=NO-GO.

## Anti-Patterns

| Anti-Pattern | Why It's Bad | Correct Approach |
|--------------|--------------|------------------|
| "Just run the script and see what happens" | Untracked failures leave user guessing | Pre-flight with structured output |
| Single-pass check that aborts on first fail | User sees one error, fixes it, sees next, fixes it, sees next... | Aggregate all failures in one run |
| Hardcoded paths that fail on different machines | Pre-flight works for you, breaks for the next agent | Use `Path.home()` and resolve at runtime |
| Checks that mutate state | Pre-flight should be read-only | All checks are pure inspections |
| "All checks are critical" | Every minor issue blocks missions | Tag severity per check, report both tiers |
| Exit code 0 on partial success | Shell scripts can't distinguish | Use 0/1/2 for GO/CONDITIONAL/NO-GO |

## The Pre-Flight + Dry-Run Boundary

When does a check belong in pre-flight vs. dry-run?

| Question | Pre-Flight | Dry-Run |
|----------|------------|---------|
| Does it depend on external binaries/services? | ✅ | ❌ |
| Is it a property of the runtime environment? | ✅ | ❌ |
| Can it be validated without invoking the main script? | ✅ | ❌ |
| Does it require the script's logic to be tested? | ❌ | ✅ |
| Would it fail before the script even imports? | ✅ | ❌ |

**Rule of thumb:** If the check fails before your script's first `import` line, it's a pre-flight check. If it fails when running your script with `--dry-run`, it's a dry-run check.

## Key Insight

> **A 5-second pre-flight check that catches "cua-driver not installed" saves 30 seconds of dry-run time AND prevents the user from debugging a script that's actually fine.** The cost-benefit ratio is approximately **1:6** for pre-flight vs. dry-run, and **1:120** for pre-flight vs. live-execute.

## Related Skills

- `output-validator` (parent) — pre-execution validation umbrella
- `references/dry-run-before-live-execute.md` (sibling) — script-logic validation
- `systematic-debugging` — root cause when pre-flight reveals environment issues
- `multi-agent-pitfalls-cheatsheet` — failure modes when environment breaks mid-orchestration
- `critic-gate` — semantic review that happens AFTER both pre-flight and dry-run pass