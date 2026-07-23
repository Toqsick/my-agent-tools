# Real-World Cross-Check — Heuristic/Detection Subagents

> Proven 2026-07-16 on Daily-Report Session-Trigger implementation.
> Full fall-study: `~/.hermes/docus/reports/2026-07-16-subagent-self-test-deception-fallstudy.md`

## The Pattern

A **heuristic/detection subagent** writes code that classifies, detects, or analyses real-world data
(structured files, documents, directories, logs, any dataset with structural variation). The plan
specifies test fixtures based on a *template* or *single known example* — and the subagent writes
tests against those fixtures, gets all green, reports success.

But the *real data has variation the plan never inventoried*. The subagent's tests are acceptance
tests for the **plan's assumptions**, not acceptance tests for **reality**.

## Symptom (what to catch)

The subagent self-report contains any of:
- "N/N Tests grün — Implementation 1:1 wie im Plan"
- "Implementation und Tests sind spec-konform"
- No mention of "run against all real files in the target directory"
- The verification section only shows pytest output, no `ls`/`grep` over real data

## Root Cause

The 2-stage review (spec compliance → code quality) assumes the spec fully describes reality.
For heuristic tasks, the spec is derived from a *hypothetical model* of the data (a template,
a single example), not from an inventory of all actual inputs. The subagent has no way to
know the real variation exists unless the plan explicitly provides an inventory or the
Queen mandates a cross-check step.

## Fix Procedure

### Step 1: Inventory the Real Data

Before accepting ANY detection subagent's results, run:

```bash
# Find what data actually exists — NOT the plan's template
find /path/to/target -name "*.md" | head -30

# Discover structural variation
find /path/to/target -name "*.md" | xargs grep -hE "^## " | sort | uniq -c | sort -rn | head -20
```

If the header/section-variation space is >3 patterns, a **single-exact-match heuristic will fail**.

### Step 2: Test the Subagent's Code Against Real Data

```bash
python3 /path/to/detection-script.py --date YYYY-MM-DD --json  # for each variant found in Step 1
```

Compare actual vs expected output for every file variant.

### Step 3: Document the Gap

If the subagent's code misclassifies real files:
1. Document exactly how many files were misclassified (absolute + %)
2. List the exact file paths and their structural variation
3. Add new test fixtures that mirror the real variation
4. Dispatch a fix subagent with the gap description

### Step 4: Patch the Heuristic

For detection tasks, the heuristic should be a **multi-marker, case-insensitive substring match**
rather than an exact string match:

```python
# WRONG — single exact match (fails on real variations)
def _extract_section(content: str, section_name: str) -> str:
    pattern = rf"^## {re.escape(section_name)}\s*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""

# RIGHT — multi-marker, case-insensitive, any-one-wins
MARKERS = ["was lief", "erkenntnisse", "lessons learned", "hauptaufgaben", "hauptphase"]
def _extract_any_section_with_content(content: str) -> tuple[str, str]:
    """Find the first marker-matched section that has real content."""
    for match in re.finditer(r'^## (.+?)\s*\n(.*?)(?=^## |\Z)', content, re.M | re.DOTALL):
        header = match.group(1).lower()
        body = match.group(2).strip()
        if any(marker in header for marker in MARKERS) and len(body) > 10:
            return match.group(1), body
    return "", ""
```

## Queen Verification Checklist

Before passing a heuristic subagent's work:

- [ ] Ran inventory: `find target -name "*.md" | xargs grep -hE "^## " | sort | uniq -c | sort -rn`?
- [ ] Variation space documented? How many unique header patterns exist?
- [ ] Detection code tested against ALL real files, not just test fixtures?
- [ ] Exact number of misclassifications documented (absolute + %)?
- [ ] New test fixtures added that mirror real variation?
- [ ] Regression tests pass with old + new fixtures?
- [ ] Multi-marker strategy used (not single exact string match)? ← critical guard

## Subagent Briefing Template (for Heuristic/Detection Tasks)

When dispatching a subagent for a heuristic/detection task, the brief MUST include:

```python
delegate_task(
    goal="Implement detection heuristic for <target data>",
    context="""
    TASK: <task description>

    THIS IS A HEURISTIC/DETECTION TASK — REAL-WORLD DATA VARIES.
    
    CRITICAL: Before writing tests, inventory the REAL target data:
    `find <target-dir> -name "*.md" | xargs grep -hE "^## " | sort | uniq -c | sort -rn`
    
    MANDATORY BRIEFING:
    1. List ALL files in the target directory with their expected class
    2. Run the detection script against every file and show output
    3. If real output differs from expected: STOP. Report the gap to Queen.
    
    Do NOT assume the plan's template structure represents all real inputs.
    Use a multi-marker, case-insensitive substring-match strategy, NOT exact string match.
    
    <rest of standard brief>
    """,
    toolsets=['terminal', 'file'],
)
```

## Anti-Patterns

- ❌ Accepting "6/6 Tests grün" from a subagent whose tests only cover plan fixtures
- ❌ Skipping the data-inventory step because "the plan describes it"
- ❌ Using exact string match (`^## Was lief\s*\n`) when real data has 11+ header variations
- ❌ Believing a subagent's "Implementation ist 1:1 wie im Plan" when the plan's model was wrong
- ❌ Adding test fixtures only for the template case, not for all real variations found

## Cross-References

- `subagent-driven-development` SKILL.md: Red Flag "Trust heuristic subagent self-report without real-world cross-check"
- `self-improving` SKILL.md: Pitfall #38 (exact string match), Pitfall #39 (subagent self-report false-green)
- `~/.hermes/docus/reports/2026-07-16-subagent-self-test-deception-fallstudy.md` — full case study (54 KB, 5 sections, 4 appendices)
