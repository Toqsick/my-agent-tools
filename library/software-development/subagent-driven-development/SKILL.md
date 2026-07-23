---
name: subagent-driven-development
description: "Use when user asks to execute an implementation plan through fresh delegate_task subagents with spec-compliance review, code-quality review, and final verification. NOT for direct coding without a plan or research-only work. Dispatches one implementer per task, verifies claimed files and anchors, runs review gates, and integrates the completed changes safely."
version: 1.3.0
author: Hermes Agent (adapted from obra/superpowers) + Basti/Yuno 2026-07-16
license: MIT
platforms:
  - linux
  - macos
  - windows
metadata:
  hermes:
    tags: ['delegation', 'subagent', 'implementation', 'workflow', 'parallel']
    related_skills: ['writing-plans', 'requesting-code-review', 'test-driven-development', 'report-synthesis', 'glm-plan-m3-execute']
lane: koenigin
reasoning_effort: xhigh
agent: Engineer
routing_hint: |
  **Agent-Scope:** Code-Tasks (build / fix / refactor / debug / review). Off-scope: visual design, long-form copy, data modeling — say 'this is Designer/Writer/Analyst's territory' and return to Yuno.
  
  Routing-Spec: `yuno-team-routing`.
trigger_keywords: ['review', 'and', 'plan', 'subagent-driven-development', 'execute']
keywords: ['review', 'plan', 'task', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['step-execution', 'plan-review-and-orchestrate', 'plan']
---
---

# Subagent-Driven Development

## Overview

Execute implementation plans by dispatching fresh subagents per task with systematic two-stage review.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

## When to Use

Use this skill when:
- You have an implementation plan (from writing-plans skill or user requirements)
- Tasks are mostly independent
- Quality and spec compliance are important
- You want automated review between tasks

**Also applies to non-code work:** Knowledge base expansion (Obsidian vaults), documentation generation, content writing, and research synthesis all benefit from the same structure — fresh subagent per task, file-scope conflict tables, two-stage review, post-expansion verification.

**For vault/note expansion specifically**, see the `vault-architecture` skill's Phase 2 section — it provides file-scope conflict tables, Templater setup, and post-expansion verification tailored to Obsidian vaults.

**vs. manual execution:**
- Fresh context per task (no confusion from accumulated state)
- Automated review process catches issues early
- Consistent quality checks across all tasks
- Subagents can ask questions before starting work

## The Process

### 0. Discovery Phase (resolve external IDs before edit)

When subagents need to write to systems that use opaque identifiers (Mnemosyne memory IDs, GitHub issue numbers, database record IDs), **resolve ALL external IDs before dispatching any edit subagent**. A subagent that receives a placeholder ID will write to a wrong target or fail silently.

```python
# Phase 0: ID-Discovery — always runs before any edit task
# Known IDs from current session context:
known_ids = {
    "replace_all_triple": "9a88228f4e99bf07",
    "daily_quality_gate": "4845ce726ddace4a",
}

# Unknown IDs: batch-resolve via mnemosyne_recall in the controller session
for topic in ["subagent self-test deception", "FTS5 Phrasen Truncation"]:
    results = mnemosyne_recall(query=topic, limit=3)
    # Manually pick the highest-importance working-tier result
    
# Write resolved IDs into a reference block in the plan file
# so every subagent brief can cite them.
```

**Rule:** If a plan references external IDs (Mnemosyne, GitHub, DB), insert a Step 0 task that:
1. Resolves all IDs via `mnemosyne_recall` / `session_search` / API lookups
2. Writes the ID table into the plan file
3. Marks itself complete BEFORE any edit subagent starts

### 1. Read and Parse Plan

Read the plan file. Extract ALL tasks with their full text and context upfront. Create a todo list:

```python
# Read the plan
read_file("docs/plans/feature-plan.md")

# Create todo list with all tasks
todo([
    {"id": "task-1", "content": "Create User model with email field", "status": "pending"},
    {"id": "task-2", "content": "Add password hashing utility", "status": "pending"},
    {"id": "task-3", "content": "Create login endpoint", "status": "pending"},
])
```

set -euo pipefail
**Key:** Read the plan ONCE. Extract everything. Don't make subagents read the plan file — provide the full task text directly in context.

### 2. Per-Task Workflow

For EACH task in the plan:

#### Step 1: Dispatch Implementer Subagent

Use `delegate_task` with complete context:

```python
delegate_task(
    goal="Implement Task 1: Create User model with email and password_hash fields",
    context="""
    TASK FROM PLAN:
    - Create: src/models/user.py
    - Add User class with email (str) and password_hash (str) fields
    - Use bcrypt for password hashing
    - Include __repr__ for debugging

    FOLLOW TDD:
    1. Write failing test in tests/models/test_user.py
    2. Run: pytest tests/models/test_user.py -v (verify FAIL)
    3. Write minimal implementation
    4. Run: pytest tests/models/test_user.py -v (verify PASS)
    5. Run: pytest tests/ -q (verify no regressions)
    6. Commit: git add -A && git commit -m "feat: add User model with password hashing"

    PROJECT CONTEXT:
    - Python 3.11, Flask app in src/app.py
    - Existing models in src/models/
    - Tests use pytest, run from project root
    - bcrypt already in requirements.txt
    """,
    toolsets=['terminal', 'file']
)
```

**Modell-passendes Briefing (M3 vs GLM — Rollen, keine IDs).** Der Kind-System-Prompt hängt seit G-2 automatisch eine modell-passende Notiz an (M3 bzw. GLM), aber dein `context`-Text sollte in dieselbe Richtung ziehen:

- **Wenn das Kind auf MiniMax-M3 läuft** (Session-Default / `worker-vision`): starker nativer Tool-Caller mit erhaltenem Reasoning → **knappes** Briefing genügt, es denkt selbst. Kein „erkläre erst deinen Plan"-Ballast; direkt Task + Verify-Kommandos + Erfolgskriterium. Lange narrative Prosa treibt nur M3s Kontext hoch (siehe `hermes-context-budget`).
- **Wenn das Kind auf GLM-5.2/GLM läuft** (`koenigin`/`worker-heavy`/`gate`): braucht explizite **Tool-Disziplin** und **flache Argumente**. Formuliere „rufe das Tool, beschreibe es nicht" und halte erwartete Argument-Shapes simpel (Strings, flache Arrays) — GLM emittiert sonst gelegentlich Repr-Listen wie `"['a','b']"`, die `coerce_tool_args` reparieren muss. GLMs Reasoning ist nicht persistent → es verträgt längeren Kontext.
- **Lane statt Modell-ID:** welches Modell ein Assignee/Profil fährt, steht in `skill_lanes` (Single Source of Truth) — briefe nach Rolle, nicht nach ID.

set -euo pipefail
#### Step 2: Dispatch Spec Compliance Reviewer

After the implementer completes, verify against the original spec:

```python
delegate_task(
    goal="Review if implementation matches the spec from the plan",
    context="""
    ORIGINAL TASK SPEC:
    - Create src/models/user.py with User class
    - Fields: email (str), password_hash (str)
    - Use bcrypt for password hashing
    - Include __repr__

    CHECK:
    - [ ] All requirements from spec implemented?
    - [ ] File paths match spec?
    - [ ] Function signatures match spec?
    - [ ] Behavior matches expected?
    - [ ] Nothing extra added (no scope creep)?

    OUTPUT: PASS or list of specific spec gaps to fix.
    """,
    toolsets=['file']
)
```

set -euo pipefail
**If spec issues found:** Fix gaps, then re-run spec review. Continue only when spec-compliant.

#### Step 3: Dispatch Code Quality Reviewer

After spec compliance passes:

```python
delegate_task(
    goal="Review code quality for Task 1 implementation",
    context="""
    FILES TO REVIEW:
    - src/models/user.py
    - tests/models/test_user.py

    CHECK:
    - [ ] Follows project conventions and style?
    - [ ] Proper error handling?
    - [ ] Clear variable/function names?
    - [ ] Adequate test coverage?
    - [ ] No obvious bugs or missed edge cases?
    - [ ] No security issues?

    OUTPUT FORMAT:
    - Critical Issues: [must fix before proceeding]
    - Important Issues: [should fix]
    - Minor Issues: [optional]
    - Verdict: APPROVED or REQUEST_CHANGES
    """,
    toolsets=['file']
)
```

set -euo pipefail
**If quality issues found:** Fix issues, re-review. Continue only when approved.

#### Step 4: Mark Complete

```python
todo([{"id": "task-1", "content": "Create User model with email field", "status": "completed"}], merge=True)
```

set -euo pipefail
#### Step 5: Queen-Verify Mnemosyne-Anchor (Mandatory — Pitfall #36 Mitigation)

**Why this exists:** Every subagent across 3 independent tasks and a batch-mode dispatch in the 2026-07-17 audit-recovery session appeared to hallucinate Mnemosyne memory IDs. Original pattern: subagent reports "✅ Mnemosyne-Anker gesetzt mit ID abc123", but `mnemosyne_get(abc123)` returns `not_found`. ***This was later REVISED*** — the subagents DID correctly persist their anchors. The tool `mnemosyne_get` is broken (Pitfall #44: returns `not_found` for ALL memory IDs, even self-set ones). Verification via `mnemosyne_recall(query=...)` and SQLite directly confirmed all 7/7 anchors real. The lesson: use `mnemosyne_recall` (content-based query) for verification, not `mnemosyne_get` (ID-based lookup). The Queen MUST do this after EVERY subagent result, before marking complete:

**The Queen MUST do this after EVERY subagent result, before marking complete:**

```python
# Step 5a: Verify the claimed Mnemosyne anchor via recall (mnemosyne_get is BROKEN — see Pitfall #44)
reported_id = subagent_result.get("memory_id", subagent_result.get("id", None))
if reported_id:
    # mnemosyne_get is known-broken (Pitfall #44: returns not_found for ALL IDs).
    # Use Dual-Verification Workflow instead:
    # 1) mnemosyne_recall with query on known content
    # 2) SQLite cross-check if recall is inconclusive
    content_tag = subagent_result.get("content", "")[:60] or f"task-{task_name}"
    verify = mnemosyne_recall(query=content_tag, limit=3)
    found = any(r.get("id") == reported_id for r in verify.get("results", []))
    if not found:
        # Subagent anchor NOT verified via recall. Queen sets the anchor herself.
        queen_anchor = mnemosyne_remember(
            content=f"### [YYYY-MM-DD] {task_name} — Queen-Anker (Subagent-ID nicht via recall bestätigt)",
            importance=0.7,
            source="self-improving"
        )
        # Verify queen's anchor via recall (not mnemosyne_get)
        verify_queen = mnemosyne_recall(query=queen_anchor.get("content_preview", "queen-anchor")[:60], limit=3)
        found_queen = any(r.get("id") == queen_anchor.get("memory_id", "") for r in verify_queen.get("results", []))
        assert found_queen, f"FAIL: Queen anchor {queen_anchor.get('memory_id')} nicht via recall bestätigt"
else:
    # No ID claimed — Queen must set one
    ...

# Step 5b: Verify claimed file output exists
for claimed_file in subagent_result.get("files", []):
    stat = terminal(f"ls -la {claimed_file}")
    assert stat["exit_code"] == 0
```

**Guard:** Include this verification step in the Queen's todo list for every subagent task. Never mark a subagent task complete before Step 5 passes.

### 3. Final Review

After ALL tasks are complete, dispatch a final integration reviewer:

```python
delegate_task(
    goal="Review the entire implementation for consistency and integration issues",
    context="""
    All tasks from the plan are complete. Review the full implementation:
    - Do all components work together?
    - Any inconsistencies between tasks?
    - All tests passing?
    - Ready for merge?
    """,
    toolsets=['terminal', 'file']
)
```

set -euo pipefail
### 4. Verify and Commit

```bash
# Run full test suite
pytest tests/ -q

# Review all changes
git diff --stat

# Final commit if needed
git add -A && git commit -m "feat: complete [feature name] implementation"
```

### 5. Real-World Cross-Check (Heuristic/Detection Tasks Only)

**Skip this step** for standard CRUD / backend / UI implementation tasks. **Mandatory** for tasks that classify, detect, parse, or analyse real-world data (daily notes, logs, file structures, directory inventories, website scraping — anything where the input format varies beyond the plan's template).

#### Why this exists

A subagent writing a detection script will naturally:
- Build test fixtures from the **plan's example** (a template, a single file)
- Test against those fixtures → all green
- Report "N/N Tests grün — Implementation 1:1 wie im Plan"

But the plan's example is **one data point**. Real-world data has variation the plan never inventoried. In a proven case (2026-07-16), this caused **5 of 18 files (28%) to be misclassified** because real section-headers had 5 variations the plan never showed.

#### The Cross-Check Procedure

**Step A — Inventory the real data:**
```bash
# Discover ALL structural variation
find <target-dir> -name "*.md" | xargs grep -hE "^## " | sort | uniq -c | sort -rn | head -20
```
If the variation space >3 unique patterns, the heuristic MUST use multi-marker substring matching, not exact string matching.

**Step B — Run detection against EVERY real file:**
```bash
for f in $(find <target-dir> -name "*.md" | sort); do
    date=$(basename "$f" .md)
    python3 /path/to/detection.py --date "$date" --json
done
```
Verify each output matches the expected class. Document each mismatch with file path, actual output, expected output, and the specific structural variation that caused it.

**Step C — Report findings:**
- Total files tested: N
- Correct: M
- Misclassified: N-M (X%)
- List of misclassified files with root cause per file

If misclassifications >0: dispatch a fix subagent with the complete gap inventory.
Do NOT accept "close enough" — every misclassification is a false positive/negative at session start.

#### Cross-reference
- Full fall-study: `~/.hermes/docus/reports/2026-07-16-subagent-self-test-deception-fallstudy.md`
- `references/heuristic-subagent-real-world-cross-check.md` — briefing template and verification checklist
- Red flag in this skill: "Accept a heuristic/detection subagent's N/N Tests grün without real-world cross-check"

## Task Granularity
## Task Granularity

**Each task = 2-5 minutes of focused work.**

**Too big:**
- "Implement user authentication system"

**Right size:**
- "Create User model with email and password fields"
- "Add password hashing function"
- "Create login endpoint"
- "Add JWT token generation"
- "Create registration endpoint"

## Red Flags — Never Do These

- **Accept a subagent's "Mnemosyne-Anker gesetzt mit ID <xyz>" claim without mnemosyne_recall verification** (REVISED 2026-07-17 — original 4/4 was a false positive). Every subagent in the 2026-07-17 audit-recovery DID correctly persist their memory anchors — `mnemosyne_get` was the broken tool (Pitfall #44: returns not_found for ALL IDs). The Queen MUST verify via `mnemosyne_recall(query=<content_preview>)` rather than `mnemosyne_get(id=<reported_id>)`. If recall finds the anchor, it was correctly persisted. Dual-Verification Workflow: recall + SQLite cross-check for final certainty. The Queen still sets her own anchor as defense-in-depth.
- **Skip the mandatory Mnemosyne-Anchor-Verification step between subagent waves** (REVISED 2026-07-17). After each subagent completes, before marking the task done and before dispatching the next wave: `mnemosyne_recall(query=<content_preview>)` + `ls -la` on claimed output files. Both must check out. If recall does not find the subagent's anchor, the Queen sets the anchor independently using `mnemosyne_remember`. Do NOT use `mnemosyne_get` for this check — it is broken (Pitfall #44: returns not_found for ALL memory IDs). See Step 5 in §Per-Task Workflow.
- Start implementation without a plan
- Skip reviews (spec compliance OR code quality)
- Proceed with unfixed critical/important issues
- Dispatch multiple implementation subagents for tasks that touch the same files
- Make subagent read the plan file (provide full text in context instead)
- Skip scene-setting context (subagent needs to understand where the task fits)
- Ignore subagent questions (answer before letting them proceed)
- Accept "close enough" on spec compliance
- Skip review loops (reviewer found issues → implementer fixes → review again)
- Let implementer self-review replace actual review (both are needed)
- **Start code quality review before spec compliance is PASS** (wrong order)
- Move to next task while either review has open issues
- **Trust a parallel subagent's "X/Y tests grün" claim without re-reading** (NEW 2026-07-04) — see `references/parallel-summary-staleness.md`. When two subagents run in parallel and one validates what another fixes, the validator's summary is accurate at dispatch time but STALE after the fixer's edit. Always re-run tests yourself.
- **Apply scout findings without source-code verification at high reasoning** (NEW 2026-07-04). At `reasoning_effort: high`, scouts produce ~60% false positives (10 false vs 5 real findings observed). Queen MUST verify every actionable finding against source code before dispatching fixes — open the file, read the line, confirm the claim. See `multi-agent-pitfalls-cheatsheet` §3-Tier Verification for the procedure.
- **Dispatch parallel subagents for tasks that edit the same file** (NEW 2026-07-15). Even when tasks edit different sections of the same file, they MUST be serial — `patch` operations shift line numbers, and concurrent `patch`/`write_file` calls on the same file cause race conditions. The exception is genuinely independent files (different paths). When in doubt, serialize. Use:
  ```python
  # WRONG: parallel subagents both patching SKILL.md
  delegate_task(goal="Add Quality Gates section", context="Edit SKILL.md...")  # parallel
  delegate_task(goal="Add Pitfall Catalog section", context="Edit SKILL.md...")  # ← line numbers shifted!
  
  # RIGHT: serial, one at a time
  delegate_task(goal="Add Quality Gates section", context="Edit SKILL.md...")  # wait for result
  # ... verify, spec-review, quality-review ...
  delegate_task(goal="Add Pitfall Catalog section", context="Edit SKILL.md...")  # now it's safe
  ```
  See `references/skill-curation-orchestration.md` for the full pipeline template.

- **Subagent reports data from a tool it cannot access** (NEW 2026-07-16). When a Subagent is dispatched for an analytics/research/report-generation task and discovers that a tool the Parent context implied (e.g. `mnemosyne_recall`, `session_search` for cross-profile reads, `memory_health_check`) is NOT available in its own toolset, it MUST NOT:
  1. Fabricate data and claim it came from the tool
  2. Skip the critical data-gathering step entirely
  3. Silently switch to an undocumented alternative source without disclosure
  4. Present partial data as complete

  Instead, the Subagent MUST:
  1. Declare the tool limitation in the output ("Tool `<tool>` is not available in this Subagent context — using [alternative source] instead")
  2. Document the alternative source and why it was chosen
  3. Mark which findings are fully reliable vs. "reconstructed from [alternative source]" with a clear veracity tag
  4. Offer concrete validation queries the Parent can run to close the gap

  Proven 2026-07-16 on a 19-Daily-Note analytics report: the Subagent lacked `mnemosyne_recall`, marked all ID-based analysis as "Datenlage unklar — reconstructed from Daily Notes, not live recall", and provided 3 concrete `mnemosyne_recall(…)` calls the Parent could run for validation.

  See `references/subagent-tool-unavailability.md` for the full pattern with template wording and examples.

- **Accept a heuristic/detection subagent's "N/N Tests grün" without real-world cross-check** (NEW 2026-07-16). When a subagent is dispatched for a heuristic/detection/classification task (detecting Daily status, classifying files, parsing variable-format logs), its tests cover what the **plan assumed reality looks like** — NOT what reality actually looks like. The subagent wrote test fixtures from a template, ran 6/6 green, and reported "Implementation 1:1 wie im Plan". Queen ran the code against the real vault: **5 of 18 files misclassified (28%)** because real section-headers had 5 variations the plan never inventoried. The spec-review gate didn't catch it because spec compliance was measured against the plan, not against reality.

  **The deception mechanism:** The subagent didn't lie. Every claim ("6/6 Tests grün", "Implementation spec-konform") was *technically* true — but the tests were acceptance tests for the *plan's template model*, not acceptance tests for *real variation*. This is distinct from parallel-summary-staleness (two subagents where one's data goes stale during another's edit) — here, a SINGLE subagent produced tests that verify plan compliance while remaining blind to real-world data variety.

  **Fix:** For every heuristic/detection task, add a mandatory Step 5 "Real-World Cross-Check" between the subagent's completion and the Queen's sign-off. The Queen MUST:
  1. Inventory the real data: `find <target> -name "*.md" | xargs grep -hE "^## " | sort | uniq -c | sort -rn`
  2. Run the detection against EVERY real file, not just test fixtures
  3. Count misclassifications exactly (absolute + %), then dispatch a fix subagent

  See `references/heuristic-subagent-real-world-cross-check.md` for the full pattern with briefing template, verification checklist, and anti-patterns.
  Cross-ref: self-improving Pitfalls #38 (exact string match) and #39 (subagent self-report false-green).

- **Blindly trust a subagent's real-world cross-check that it ran itself** (NEW 2026-07-16) — corollary of the above. Even if the subagent claims it tested against real data, the Queen MUST re-verify independently. The 2026-07-16 subagent DID recommend smoke-testing against `--date 2026-07-03` — and then assumed 07-03 was MISSING (it actually existed with 4946 bytes and a parenthetical header variant). The subagent *thought* it checked reality but its own assumption was wrong. **Queen re-verify is non-delegable.**

## Handling Issues

### If Subagent Asks Questions

- Answer clearly and completely
- Provide additional context if needed
- Don't rush them into implementation

### If Reviewer Finds Issues

- Implementer subagent (or a new one) fixes them
- Reviewer reviews again
- Repeat until approved
- Don't skip the re-review

### If Subagent Fails a Task

- Dispatch a new fix subagent with specific instructions about what went wrong
- Don't try to fix manually in the controller session (context pollution)

## Efficiency Notes

**Why fresh subagent per task:**
- Prevents context pollution from accumulated state
- Each subagent gets clean, focused context
- No confusion from prior tasks' code or reasoning

**Why two-stage review:**
- Spec review catches under/over-building early
- Quality review ensures the implementation is well-built
- Catches issues before they compound across tasks

**Cost trade-off:**
- More subagent invocations (implementer + 2 reviewers per task)
- But catches issues early (cheaper than debugging compounded problems later)

### Delegation Prompt Efficiency (User-Preference 2026-07-04)

Keep delegation context **~60-70% of first-draft length** while retaining essentials:
- Core goal (1 sentence)
- File paths + line numbers
- Toolset restrictions (read-only, call budget, output path)
- Verification command (so you can confirm claims)

CUT: redundant descriptions, multi-paragraph "as you know" context, explanatory fluff the subagent already inherits from the system prompt. Proven 2026-07-04: 3 parallel scouts finished in **69 seconds** at this length vs 2-3 minutes previously with longer briefings. Subagents still returned full structured reports with exact line numbers.

**Anti-pattern:** Writing mini-essays in delegation prompts. The subagent shares the same model — it needs the *essential* data, not hand-holding.

## Integration with Other Skills

### With writing-plans / glm-plan-m3-execute

This skill EXECUTES plans created by the `writing-plans` skill or the multi-phase
`glm-plan-m3-execute` pipeline (orchestration/):

1. User requirements → `glm-plan-m3-execute` Phase 1-3 (GLM 5.2 plant, Queen verifies)
2. `glm-plan-m3-execute` Phase 4 → this skill (M3 subagents execute wellenweise)
3. This skill → working code + Queen-Verify zwischen Wellen

**When using with `glm-plan-m3-execute`:** The GLM plan already passed S1-S7
Quality Gates. This skill's Step 5 (Mnemosyne-Verify) and the Real-World
Cross-Check (Phase 5) are already baked into the pipeline. No need to re-do
them — the Queen handles wave-gates.

### With test-driven-development

Implementer subagents should follow TDD:
1. Write failing test first
2. Implement minimal code
3. Verify test passes
4. Commit

Include TDD instructions in every implementer context.

### With requesting-code-review

The two-stage review process IS the code review. For final integration review, use the requesting-code-review skill's review dimensions.

### With systematic-debugging

If a subagent encounters bugs during implementation:
1. Follow systematic-debugging process
2. Find root cause before fixing
3. Write regression test
4. Resume implementation

## Briefing Template (skill curation / file-edit pipelines)

For file-edit pipelines (skill curation, documentation updates, config changes), use this structured briefing template. It reduces subagent context-waste by packing all constraints into a compact checklist.

### Per-Task Anchor-Table Pattern

Before dispatching any subagent that edits a structured file, create an anchor table:

```markdown
| Task | Operation | Target file | Anchor section | Verification command |
|---|---|---|---|---|
| 5 | Insert section after | SKILL.md | `## Hygiene-Regeln` | `grep -B2 -A2 '^## Quality Gates$' SKILL.md` |
| 6 | Insert section after | SKILL.md | `## Quality Gates` | `grep -B2 -A2 '^## Pitfall-Katalog$' SKILL.md` |
```

Include the anchor table in EVERY relevant implementer's brief so they verify their insertion point hasn't shifted.

### Implementer Briefing Structure

```python
delegate_task(
    goal=f"Implement Task {n}: {task_name}",
    context="""
    TASK FROM PLAN: <paste full task text>
    
    ANCHOR-TABLE: <per-task anchor from the table above>
    
    MNEMOSYNE-IDS (resolved in Phase 0):
    - replace_all: 9a88228f4e99bf07
    - daily_quality_gate: 4845ce726ddace4a
    
    VERIFICATION (run AFTER each edit):
    1. grep -B2 -A2 '<anchor-pattern>' <target-file>
    2. <file-specific verify command>
    
    NICHT ERLAUBT (hard constraints, breach = abort):
    - replace_all=true (Pitfall: replaces unintended occurrences)
    - write_file > 4KB without chunk strategy (Pitfall: write-file truncation)
    - Mnemosyne-Update with placeholder IDs (Pitfall: silent failure on bad ID)
    - patch with non-unique old_string (will fail with "Found N matches")
    """,
    toolsets=['terminal', 'file', 'mnemosyne'],
)
```

### NICHT-ERLAUBT Explained

| Constraint | Why |
|---|---|
| `replace_all=true` | Triple-injection risk: replaces unintended occurrences across the file. Proven pitfall 2026-07-14 on self-improving skill. |
| `write_file > 4KB without chunk strategy` | `write_file` that resends the full content can silently truncate lines at ~4KB boundary due to terminal output capping. Always break large writes into targeted `patch` calls. |
| `Mnemosyne-Update with placeholder IDs` | Updating with ID="to_resolve" or "id-from-plan" writes to a wrong memory or fails silently. Phase 0 MUST resolve all IDs first. |
| `patch with non-unique old_string` | `patch` requires a unique match. When `old_string` appears N>1 times, the call fails. Always include sufficient surrounding context (2+ lines above and below). |

## Example Workflow

```
[Read plan: docs/plans/auth-feature.md]
[Create todo list with 5 tasks]

--- Task 1: Create User model ---
[Dispatch implementer subagent]
  Implementer: "Should email be unique?"
  You: "Yes, email must be unique"
  Implementer: Implemented, 3/3 tests passing, committed.

[Dispatch spec reviewer]
  Spec reviewer: ✅ PASS — all requirements met

[Dispatch quality reviewer]
  Quality reviewer: ✅ APPROVED — clean code, good tests

[Mark Task 1 complete]

--- Task 2: Password hashing ---
[Dispatch implementer subagent]
  Implementer: No questions, implemented, 5/5 tests passing.

[Dispatch spec reviewer]
  Spec reviewer: ❌ Missing: password strength validation (spec says "min 8 chars")

[Implementer fixes]
  Implementer: Added validation, 7/7 tests passing.

[Dispatch spec reviewer again]
  Spec reviewer: ✅ PASS

[Dispatch quality reviewer]
  Quality reviewer: Important: Magic number 8, extract to constant
  Implementer: Extracted MIN_PASSWORD_LENGTH constant
  Quality reviewer: ✅ APPROVED

[Mark Task 2 complete]

... (continue for all tasks)

[After all tasks: dispatch final integration reviewer]
[Run full test suite: all passing]
[Done!]
```

set -euo pipefail
## Remember

```
Fresh subagent per task
Two-stage review every time
Spec compliance FIRST
Code quality SECOND
Never skip reviews
Catch issues early
```

**Quality is not an accident. It's the result of systematic process.**

## Further reading (load when relevant)

When the orchestration involves significant context usage, long review loops, or complex validation checkpoints, load these references for the specific discipline:

- **`references/context-budget-discipline.md`** — Four-tier context degradation model (PEAK / GOOD / DEGRADING / POOR), read-depth rules that scale with context window size, and early warning signs of silent degradation. Load when a run will clearly consume significant context (multi-phase plans, many subagents, large artifacts).
- **`references/gates-taxonomy.md`** — The four canonical gate types (Pre-flight, Revision, Escalation, Abort) with behavior, recovery, and examples. Load when designing or reviewing any workflow that has validation checkpoints — use the vocabulary explicitly so each gate has defined entry, failure behavior, and resumption rules.
- **`references/parallel-summary-staleness.md`** — Parallel subagent summary staleness pattern: when subagents are dispatched concurrently and one validates what another fixes, the validator's summary is stale by the time the fixer lands. Includes symptom detection, fix procedure, and prevention. Proven 2026-07-04 on SecurityKernel PR #7.
- **`references/skill-curation-orchestration.md`** (NEW 2026-07-15) — Full pipeline template for refining a single SKILL.md via multi-agent pipeline: serial-execution rule, anchor-table pattern, per-task NICHT-ERLAUBT constraints, verification commands, and anti-patterns. Load this when orchestrating a 5+ task skill-curation plan.
- **`references/preflight-check-pattern.md`** — Layered multi-layer pre-flight check pattern for risky autonomous operations (Computer-Use, file system writes, network calls). Tiered exit codes (GO/CONDITIONAL/NO-GO), companion install helper, dry-run as pre-flight, anti-patterns. Proven 2026-07-06 on GreyHack mission system — caught 5 critical bugs before live run.
- **`references/subagent-tool-unavailability.md`** (NEW 2026-07-16) — Pattern for when a Subagent discovers that a tool the Parent context implied (e.g. `mnemosyne_recall`, `session_search` cross-profile) is NOT available in its own toolset. Template wording, veracity-tagging conventions, and Parent-validation-query format. Load this before dispatching any analytics/research Subagent that may need tools only the Parent has.
- **`references/heuristic-subagent-real-world-cross-check.md`** (NEW 2026-07-16) — Mandatory for any Subagent task that implements a detection/heuristic/classification on real-world input data with structural variation. Contains: briefing template with 3 mandatory checklist items, multi-marker vs exact-match code comparison, verification checklist, fix procedure, and anti-patterns. Provensource on 2026-07-16 Daily-Report-Trigger implementation where 5/18 files were misclassified by a spec-compliant but reality-blind subagent. Cross-refs: self-improving Pitfalls #38, #39.

Both references adapted from gsd-build/get-shit-done (MIT © 2025 Lex Christopherson).

## 🧭 Related Skills (Cross-Cluster Navigation)

- **`skill-navigator`** (orchestration/) — Meta-Navigator for all 169 active Hermes skills. **Load FIRST when unsure which skill applies.** Maps 10 domain-clusters and 60+ singletons.
- **`multi-agent-pitfalls-cheatsheet`** (orchestration/) — TRIGGER-WATCHLIST for `delegate_task` calls. **ESSENTIAL companion for this skill** — subagent-driven-development IS multi-agent work. Cheatsheet defends against Phantom-Fixes, Background-Review 90+90s timeouts, and the new Hybrid Pre-Scan pattern.
- **`multi-agent-orchestration`** (orchestration/) — Sibling pattern. Use when research is the goal; use this skill (subagent-driven-development) when implementation is the goal.
- **`report-synthesis`** (orchestration/) — Consolidate 3+ parallel subagent reports into a single coherent master document. Natural successor to this skill: after subagent waves complete and reports land, load this skill to consolidate them.
- **`plan`** (software-development/) — Companion for the planning phase. Writes implementation plans before subagent dispatch.
- **`glm-plan-m3-execute`** (orchestration/) — Full 5-phase pipeline (Reality-Check → GLM plan → Queen-verify → M3 execute → Review loop). This skill handles **Phase 4** of that pipeline: subagent wave execution.
