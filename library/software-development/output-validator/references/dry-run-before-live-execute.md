# Dry-Run Before Live-Execute — Pattern Proven 2026-07-06

> **Class:** Pre-flight validation for autonomous systems (mission orchestrators, computer-use pipelines, cron-driven automations, multi-agent swarms).
> **Trigger:** When you build any system that, once started, will run for >5 minutes or touch live state.
> **Source:** Queen-Bee Autonomous Mission Architecture for GreyHack — see `~/.hermes/skills/computer-use/greyhack-mission-orchestrator/`.

## The Core Rule

```
BUILD → DRY-RUN → BUGFIX LOOP → LIVE EXECUTE
              ↑___________↓
              (never skip)
```

**Dry-run is NOT optional.** Any system that runs autonomously for >5 minutes MUST be validated against all inputs/edge cases before the first live run. The user explicitly validated this principle during the GreyHack orchestrator buildout: "du hast recht erst dry run test" — this is a first-class preference signal.

## Why Dry-Run Matters (the Five Bugs Found In One Round)

During the 2026-07-06 GreyHack orchestrator dry-run, the following bugs surfaced in a single 30-second validation cycle. **None would have been caught by code review alone** — they only manifested at parse/execution time against real input.

| # | Bug | Symptom | Real-World Cost Without Dry-Run |
|---|----|---------|---------------------------------|
| 1 | **Mission parser ignored steps** because section header was `## 📋 Steps (vom Orchestrator...)` not `## Steps` | Orchestrator would have run 0 steps silently, looked "successful" | Wasted 30-60 min mission time, false confidence |
| 2 | **YAML parse error** in SKILL.md frontmatter (colon `:` in description broke YAML) | Skill would be rejected by Hermes validator | 30+ min confusion about why skill isn't loading |
| 3 | **OCR state-detection over-broad**: "Router-View" was misclassified as "Login-Screen" because both contain "password" | Orchestrator would have taken wrong actions based on false state recognition | Mission goals missed, retries piled up, possible game-state corruption |
| 4 | **State-file path mismatch**: code wrote to `Mission-State.md`, existing note was `Mission-State - Live-Status.md` | State persisted to a phantom file, Obsidian never saw it | Mission-state recovery impossible after crash/restart |
| 5 | **Frontmatter overwritten** on every state save (no preservation logic) | Obsidian would have stripped tags/properties | Lost context, broken Dataview queries |

**All 5 bugs found in one dry-run. Estimated cost if discovered mid-mission: 60+ minutes + potential corruption of live state.**

## Dry-Run Checklist (Minimum 8 Stages)

```
□ 1. SCRIPT INVOCATION
     python3 script.py <input> --dry-run
     → Exit code 0?
     → Output matches expected structure?

□ 2. INPUT PARSING
     Feed each known input type through the parser
     → All sections extracted?
     → All edge cases (empty, malformed, unicode headers)?

□ 3. STATE MACHINE ISOLATION TEST
     Import state classes in a separate test script
     → All transitions valid?
     → All enum values reachable?

□ 4. KILL-SWITCH SIMULATION
     Trigger the kill-switch with a mock dangerous state
     → RuntimeError raised?
     → Telegram alert sent (or queued)?
     → State persisted as "KILLED"?

□ 5. STATE PERSISTENCE
     Run a save, re-read file, verify all expected fields present
     → State written to correct path?
     → Frontmatter preserved (if using frontmatter)?
     → No field corruption?

□ 6. YAML/JSON/MARKDOWN FRONTMATTER VALIDATION
     yaml.safe_load() each generated file
     → No parse errors?
     → All required keys present?

□ 7. PYTHON SYNTAX CHECK (if applicable)
     python3 -m py_compile script.py
     → All imported modules resolve?
     → No syntax errors?

□ 8. IMPORT / MODULE-LOAD CHECK
     __import__(module_name) for each script
     → Missing dependencies identified?
     → Circular import risks caught?
```

## The Three-Tier Validation Matrix

Match validation depth to risk level:

| Risk Tier | Examples | Required Dry-Run |
|-----------|----------|------------------|
| **LOW** (read-only, <1 min runtime, no state changes) | Single grep, file copy, Dataview query | Stage 1 only |
| **MEDIUM** (writes files, 1-15 min runtime) | CSV export, image batch convert, document generation | Stages 1, 2, 5, 6 |
| **HIGH** (live-state mutation, autonomous loop, >15 min) | Computer-use orchestrator, cron deployment, multi-agent swarms, game automation | **All 8 stages** |

**The GreyHack orchestrator was HIGH risk — all 8 stages caught the bugs listed above.**

## Common Dry-Run Patterns That Hide Bugs

When designing dry-run tests, watch for these patterns that **look correct in code review but fail at runtime**:

1. **Section header matching**: `line.startswith("## Steps")` fails on `## 📋 Steps`. Use `lstrip("#").strip().lower().startswith(...)` or regex.
2. **YAML in markdown frontmatter**: A colon `:` in a description value breaks YAML unless wrapped in single quotes.
3. **Path string construction**: `f"{dir}/{name}.md"` vs `Path(dir) / f"{name}.md"` — hardcoded strings don't handle spaces or special chars.
4. **State-file frontmatter preservation**: When writing state updates, always read existing frontmatter FIRST, write new content SECOND. Otherwise Obsidian strips tags.
5. **OCR/text matching with shared keywords**: "password" matches both Login-Screen and Router-View. Use priority ordering: specific keywords first, generic last.
6. **Import paths in same-directory scripts**: A script in `scripts/` importing `import orchestrator` works only if you run from inside `scripts/`. Use sys.path manipulation OR package structure.
7. **Default values that look like success**: A `dry_run=True` mode that doesn't actually skip side effects is worse than no dry-run at all.

## The Verification Step (After Bugfixes)

Every fix MUST be re-verified in isolation:

```
1. Patch the bug
2. Re-run the EXACT dry-run command that found it
3. Verify exit code 0
4. Verify expected output structure
5. Re-run all 8 stages (not just the failing one)
6. Document the bug → fix → re-verify chain in CHANGELOG
```

**NEVER claim a fix works without re-running the dry-run that found the bug.** A successful Python compile is not the same as correct runtime behavior.

## Anti-Patterns

| Anti-Pattern | Why It's Bad | Correct Approach |
|--------------|--------------|------------------|
| "The code compiled, it must work" | Compile ≠ semantic correctness | Run actual dry-run with realistic inputs |
| "I tested it once manually" | One-shot tests miss edge cases | Test all known input variations |
| "I'll fix the bugs after we go live" | Live bugs corrupt real state | Fix ALL dry-run bugs before any live run |
| "Dry-run is too slow" | A failed live run is slower | Budget 2-5x normal dev time for validation |
| "I'll just run it once and see" | First live run with bugs is expensive | Iterate dry-run → fix → dry-run until clean |

## When to Skip Dry-Run (Rare)

Only skip when ALL of:
- Total runtime <30 seconds
- No state mutation (pure read)
- Output is logged/visible so errors are obvious
- Idempotent and safe to re-run

If even one condition is false → dry-run is required.

## Proven Workflow Template

```python
# Phase 1: Build the system
write all scripts, skills, configs

# Phase 2: Build the dry-run harness (this file!)
python3 scripts/dry_run.py  # implements all 8 stages

# Phase 3: Fix loop
while dry_run_finds_bugs:
    identify_root_cause(systematic-debugging)
    fix_one_thing_at_a_time
    re_run_dry_run
    document_in_changelog

# Phase 4: LIVE EXECUTE (only when dry-run is 100% clean)
python3 scripts/live_run.py

# Phase 5: Post-flight monitoring
watch for unexpected behavior, kill-switch triggers, state anomalies
```

## Related Skills

- `output-validator` (parent) — pre-flight schema/syntax validation
- `systematic-debugging` — root cause investigation when bugs are found
- `test-driven-development` — write the dry-run as automated tests
- `critic-gate` — semantic review after dry-run passes
- `multi-agent-pitfalls-cheatsheet` — failure modes when delegating the dry-run to subagents

## Key Insight

> **A 30-second dry-run that finds 5 bugs saves 60+ minutes of live execution.** The cost-benefit ratio is approximately **1:120**. Always validate before you activate.