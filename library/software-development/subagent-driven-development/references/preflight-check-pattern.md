# Pre-Flight Check Pattern

**Discovered:** 2026-07-06 (GreyHack Computer-Use mission system)
**Severity:** HIGH — autonomous operations on user's actual desktop can cause real damage if prerequisites are missing

## The Problem

Autonomous operations that touch the user's actual system (Computer-Use, file system writes, network calls, service manipulation) have a **multi-layered setup** that can fail silently if any layer is missing. Subagents can claim "all systems go" while missing critical tools, leading to mid-mission failures that leave the user with a half-broken state.

**Real-world example (2026-07-06):** A Computer-Use mission orchestrator for GreyHack was about to start its first live run. Pre-flight check revealed:
- cua-driver binary was installed but `hermes_tools.computer_use` was NOT exposed (different layers)
- Telegram bot token was configured but connectivity was never tested
- GreyHack window detection tool was missing
- OCR detection of permission-dialog keywords had a generic-vs-specific keyword bug

If the orchestrator had started live without this check, the kill-switch would have failed silently mid-mission, leaving GreyHack in an uncontrolled state.

## The Pattern: Pre-Flight Check Before Any Autonomous Operation

Before dispatching a subagent (or running yourself) for any **risky autonomous operation**, run a `preflight_check.py` script with a layered detection pattern.

### Layered Detection (NOT just one check)

A common pitfall is checking only one place (e.g. "is the binary on PATH?"). Real setup has 3-4 layers; missing any one fails silently:

```python
def check_cua_driver():
    # Layer 1: Direct binary on PATH
    try:
        subprocess.run(["cua-driver", "--version"], timeout=5)
        return "✅ via binary"
    except FileNotFoundError:
        pass

    # Layer 2: Wrapper CLI subcommand (often wraps the binary)
    try:
        result = subprocess.run(["hermes", "computer-use", "status"], timeout=10)
        if "installed" in result.stdout and ("✓" in result.stdout or "ok" in result.stdout.lower()):
            return "✅ via CLI"
    except FileNotFoundError:
        pass

    # Layer 3: Direct import (often a thin wrapper)
    try:
        from hermes_tools import computer_use
        return "✅ via import"
    except ImportError:
        pass

    # Layer 4: Fallback tools (last resort)
    for tool in ["scrot", "grim", "gnome-screenshot"]:
        if subprocess.run(["which", tool]).returncode == 0:
            return f"⚠️ fallback {tool}"

    return "❌ all layers failed"
```

**Rule:** When a tool can be reached via multiple layers (CLI wrapper, Python import, direct binary, fallback), check them in order of preference, but mark success at the FIRST layer that works. Don't require all layers to succeed.

### Tiered Exit Codes (for CI/CD integration)

```python
import sys

if critical_passed and not optional_failed:
    sys.exit(0)   # GO — full speed ahead
elif critical_passed:
    sys.exit(1)   # CONDITIONAL GO — critical works, some optionals missing
else:
    sys.exit(2)   # NO-GO — fix criticals first
```

**Critical vs optional:** Critical = operation cannot succeed without it. Optional = operation works but sub-optimally. Example:
- **Critical:** cua-driver, telegram-bot-token, mission-file-parseable
- **Optional:** window-detection-tool (can use fallback), disk-space (only matters for long ops)

### Pre-Flight Check Script Template

```python
#!/usr/bin/env python3
"""preflight_check.py — Gate script for [OPERATION]"""
import argparse
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass

@dataclass
class CheckResult:
    name: str
    passed: bool
    critical: bool
    message: str
    fix_suggestion: str = ""

def check_layered(tool_name: str, cmds: list) -> CheckResult:
    """Try multiple commands in order; first success wins."""
    for cmd in cmds:
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=10)
            if r.returncode == 0:
                return CheckResult(
                    name=tool_name, passed=True, critical=True,
                    message=f"✅ {tool_name} verfügbar via {' '.join(cmd[:2])}"
                )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return CheckResult(
        name=tool_name, passed=False, critical=True,
        message=f"❌ {tool_name} nicht verfügbar",
        fix_suggestion=f"Installiere {tool_name} oder prüfe PATH"
    )

# Define checks
CHECKS = [
    lambda: check_layered("primary-tool", [["tool1"], ["tool2", "--version"]]),
    # ... more checks
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    results = [check() for check in CHECKS]
    critical_passed = all(r.passed for r in results if r.critical)
    optional_failed = [r for r in results if not r.critical and not r.passed]

    # Output
    if args.json:
        print(json.dumps({
            "status": "GO" if critical_passed and not optional_failed else
                     ("CONDITIONAL" if critical_passed else "NO-GO"),
            "critical_passed": critical_passed,
            "results": [r.__dict__ for r in results]
        }))
    else:
        # Human-readable report
        ...

    # Exit code
    sys.exit(0 if critical_passed and not optional_failed else
             (1 if critical_passed else 2))

if __name__ == "__main__":
    main()
```

### Install Helper (companion script)

```bash
#!/bin/bash
# install_prereqs.sh — auto-install all prerequisites
set -e

# Tesseract (or any critical tool)
if ! command -v tesseract &>/dev/null; then
    sudo apt update && sudo apt install -y tesseract-ocr
fi

# Window-detection tools
for tool in wmctrl grim; do
    if ! command -v $tool &>/dev/null; then
        sudo apt install -y $tool
    fi
done

# Wrapper CLI installs (e.g. cua-driver)
if command -v hermes &>/dev/null; then
    hermes tool install
fi
```

**Rule:** Always provide both the pre-flight check AND the install helper. Users shouldn't have to manually remember install commands.

## Dry-Run as Pre-Flight Check

For subagent-driven autonomous operations, the **dry-run mode** of the operation script itself is the most important pre-flight check:

```python
class MissionOrchestrator:
    def run(self, dry_run=False):
        if dry_run:
            # Validate parseable, list steps, verify state, NO actual actions
            print("📋 Mission-Parsing erfolgreich!")
            for i, step in enumerate(steps, 1):
                print(f"   Step {i}: {step[:80]}...")
            return

        # Live run only after dry-run passed
        for i, step in enumerate(steps, 1):
            self._execute_step(i, step)
```

**Two-stage workflow:**
1. **`script.py mission.md --dry-run`** → validates parseable, lists steps, exits cleanly
2. **`script.py mission.md`** → live execution (only if dry-run passed)

**Trap:** A dry-run that ONLY prints "would execute" without checking parseability is useless. Dry-run should exercise the parser, validate inputs, and report concrete warnings — every check that can fail should be exercised.

## Verification After Pre-Flight

Pre-flight check passing does NOT guarantee mission success. Always include:

1. **Dry-run output captured** — paste into session log
2. **Optional re-run of pre-flight** before each major step
3. **Kill-switch tested in isolation** — for autonomous ops, verify the abort path works BEFORE running the live mission
4. **User confirmation gate** — present dry-run summary + pre-flight report to user, await explicit GO

## Anti-Patterns

- **Single-source pre-flight** (only checking one layer) — fails silently when layer is missing
- **Pre-flight that requires user interaction to interpret output** — must be Go/No-Go explicit
- **Pre-flight without install helper** — user is stuck after first failure
- **Pre-flight without --dry-run mode on the actual operation script** — parsing bugs surface mid-mission instead of pre-execution
- **Skipping pre-flight because "it worked last time"** — environment changes (package updates, PATH shifts) silently break setup

## Related Patterns

- **3-Tier Verification** (multi-agent-pitfalls-cheatsheet §3-Tier) — exists → content → reality
- **Parallel Summary Staleness** (this skill's references/parallel-summary-staleness.md) — pre-flight before dispatch prevents it
- **Gates Taxonomy** (subagent-driven-development skill) — Pre-Flight Gate is one of four canonical gate types

**Proven 2026-07-06:** GreyHack Computer-Use mission system. 10-point pre-flight check caught:
- cua-driver multi-layer detection (binary + CLI)
- OCR detection generic-vs-specific keyword bug
- Mission parser emoji-in-header bug
- State-file path mismatch
- Mission-State frontmatter preservation bug

Without pre-flight, ALL of these would have surfaced during live execution, mid-mission, when rollback is hardest.