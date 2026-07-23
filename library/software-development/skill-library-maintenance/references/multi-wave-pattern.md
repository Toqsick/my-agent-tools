# Multi-Wave Slim-Down Pattern

**Proven:** 2026-07-02 Skill-Slim-Down Mission (9 skills, 2 waves, ~25 min wall-clock, 0 content loss, 26 broken refs caught and fixed post-wave).

## When to Use

Apply this pattern when:
- More than 5 SKILL.md files need slimming (default `max_concurrent_children` is 5)
- You want verification between waves (early issue detection)
- You need a master report at the end

Do NOT use this pattern when:
- 1-3 skills need slimming (single subagent is enough)
- Skills are not yet categorized (do diagnostic scan first)
- The mission has unknowns that need exploration (single-agent discovery better)

## The 5-Phase Workflow

```
Phase 0: PARENT Pre-Scan
Phase 1: PARENT Spawns Wave 1 (parallel)
Phase 2: PARENT Verifies Wave 1
Phase 3: PARENT Spawns Wave 2 (parallel)
Phase 4: PARENT Verifies Wave 2 + Writes Master Report
```

### Phase 0: Parent Pre-Scan (5-10 min)

Run the diagnostic scan from the parent SKILL.md:

```bash
# Size inventory
find ~/.hermes/skills -name "SKILL.md" \
  -not -path "*/.archive/*" -not -path "*/duplicates*" \
  -exec wc -c {} \; | sort -rn | head -25

# Categorize each candidate: Monolith / Partial / OK
# Check existence of references/, templates/, scripts/ per skill
# Decide which skills to slim and how aggressively

# Active-skill pre-check (skip archivelings!)
for skill in "${candidates[@]}"; do
  [ -f "$skill/SKILL.md" ] || continue  # skip duplicates in .archive/
  active=$([ -d "$(dirname $skill)" ] && echo "active" || echo "archive")
  echo "$active $skill"
done
```

**Decision matrix for pre-scan:**

| Pre-Scan Finding | Action |
|---|---|
| Skill exists only in `.archive/` or `duplicates*` | **SKIP** — subagent #5 on 2026-07-02 correctly skipped hermes-admin this way |
| Skill is in `.archive/` AND has active version | Slim the active version (not the archive) |
| Skill >40KB with 0 refs | Priority P0 — full extraction |
| Skill >40KB with refs | Priority P1 — extend refs |
| Skill 25-40KB | Priority P2 — opportunistic extraction |
| Skill <25KB | Skip — no slim needed (Pitfall #6 from SKILL.md) |

**Wave planning:** Sort candidates by priority, split into waves of max 5 by `max_concurrent_children`. Document the wave plan before spawning.

### Phase 1: Parent Spawns Wave 1 (5 min setup + ~12 min execution)

Use `delegate_task` BATCH MODE (NOT multiple sequential `delegate_task` calls):

```python
delegate_task(tasks=[
    {
        "goal": "Slim down <skill-A>: <before-size>KB → <target-size>KB",
        "context": "<full slim-down protocol + skill-specific path>",
        "role": "leaf"
    },
    # ... up to 5
])
```

Each subagent gets the SAME briefing template with skill-specific substitutions. See `multi-agent-pitfalls-cheatsheet/references/2026-07-02-additions.md` §2 for the template.

**Critical briefing inclusions:**
- `OUTPUT: ~/docs/system/<mission>-<skill>.md` (not in skill tree — Pitfall #6)
- `MAX 8 file-calls` (not web-calls for slim-down — different limit!)
- `META-CHECK: Run broken-ref detection before reporting success`
- `FRONTMATTER STAYS EXACT — never modify YAML during slim-down`

### Phase 2: Parent Verifies Wave 1 (2-5 min)

Run the **4-Tier Verification** for each subagent output. See `multi-agent-pitfalls-cheatsheet/references/2026-07-02-additions.md` §3 for the full matrix.

**Verification script** (run inline, not via subagent — parent must verify itself):

```bash
WAVE1_SKILLS=("category/skill-a" "category/skill-b" ...)

for skill in "${WAVE1_SKILLS[@]}"; do
  SKILL=~/.hermes/skills/$skill/SKILL.md
  DIR=$(dirname "$SKILL")
  
  # Tier 0: Frontmatter intact
  has_name=$(head -50 "$SKILL" | grep -c '^name:')
  fm_end=$(head -50 "$SKILL" | grep -n '^---$' | tail -1)
  
  # Tier 1: Datei exists
  exists=$([ -f "$SKILL" ] && echo "✅" || echo "❌")
  
  # Tier 2: Size within target
  size=$(($(wc -c < "$SKILL") / 1024))
  
  # Tier 3: Realitäts-Check (compare to original snapshot if available)
  
  # Tier 4: Broken refs
  broken=0
  for ref in $(grep -oE 'references/[a-zA-Z0-9_-]+\.md' "$SKILL" | sort -u); do
    [ ! -f "$DIR/$ref" ] && broken=$((broken + 1))
  done
  
  echo "$skill: $exists size=${size}KB name=$has_name fm=$fm_end broken=$broken"
done
```

**Decision per Wave-1 skill:**

| Verification Result | Action |
|---|---|
| All tiers ✅ | Continue to Wave 2 |
| Tier 4 broken >0 | Inline-fix with Option A (block-replace) from SKILL.md Pitfall #10 |
| Frontmatter broken | Reconstruct from snapshot or re-spawn |
| Size too large (but otherwise OK) | Acceptable — log it, continue |
| File missing | Re-spawn that ONE subagent (do not redo whole wave) |

### Phase 3: Parent Spawns Wave 2 (5 min setup + ~13 min execution)

Same template as Wave 1, but with:
- Updated Wave-2 candidates (those that didn't make Wave 1)
- Note in briefing: "Sibling skill <X> was slimmed in Wave 1 with <Y> outcome — use as reference for naming conventions"

If Wave 1 revealed a common pattern (e.g. all had broken refs in same place), update the briefing template accordingly.

### Phase 4: Parent Verifies Wave 2 + Master Report (5-10 min)

Repeat Phase 2 verification for Wave 2.

Then write the master report combining both waves. Suggested structure (`~/docs/system/skill-slim-down-DATE.md`):

1. **Executive Summary** — total before/after, savings, key decisions
2. **Per-Skill Table** — before → after, ref count, broken-ref count
3. **Workflow** — what was done in each phase
4. **Lessons Learned** — what worked, what was hard
5. **Decision Log** — e.g. why we used block-replace over CREATE for broken refs
6. **Verification Matrix** — full 4-tier results per skill
7. **Follow-up Actions** — TODO list for future sessions

## Proven Impact (2026-07-02)

| Metric | Value |
|---|---|
| Skills slimmed | 9 |
| Waves | 2 (5+4) |
| Total wall-clock | ~25 min |
| Σ SKILL.md before | 513 KB |
| Σ SKILL.md after | 95 KB |
| Reduction | -81% (-418 KB) |
| Broken refs detected | 26 |
| Broken refs fixed | 26 (block-replace) |
| Subagent crashes | 0 |
| Content lost | 0 |

Master report: `~/docs/system/skill-slim-down-2026-07-02.md`

## Cross-References

- `skill-library-maintenance/SKILL.md` — parent class skill (size thresholds, scan commands, common pitfalls)
- `multi-agent-pitfalls-cheatsheet/references/2026-07-02-additions.md` §2 — Multi-Wave Subagent Pattern (subagent-side view)
- `multi-agent-pitfalls-cheatsheet/references/2026-07-02-additions.md` §3 — 4-Tier Verification matrix
- `~/docs/system/skill-slim-down-2026-07-02.md` — full mission report with all numbers and lessons

## Template: Wave-Spawn Briefing (copy-paste ready)

```markdown
# Slim-Down Mission — Wave {WAVE_N}

## Context
You are subagent {INDEX}/{TOTAL} in Wave {WAVE_N} of a Skill-Slim-Down mission.
Target: SKILL.md at `~/.hermes/skills/{CATEGORY}/{SKILL}/SKILL.md`
Current size: {SIZE_KB}KB → Target: ≤{TARGET_KB}KB

## Protocol
1. Read the full SKILL.md (use read_file with offset/limit for >500 line files)
2. Keep in SKILL.md: YAML frontmatter (EXACT as-is), intro paragraph, section
   headings as outline (1-2 sentence summaries), critical warnings/pitfalls
   in short bullet form, links to references.
3. Extract into references/ (new or existing): all code blocks >10 lines,
   step-by-step procedures, bug logs, version histories, API details.
4. Suggested new files: references/<topic>.md (one per logical section).
5. Each reference file opens with a top-level heading matching the SKILL.md
   outline.
6. Target: SKILL.md ≤{TARGET_KB}KB.

## TOOLING
- Read: read_file, search_files
- Write: write_file (only for new references/ files and the final slim SKILL.md)
- Verify: terminal with wc, grep, find (read-only inspection)
- NEVER: modify YAML frontmatter, edit the original file outside of references/
  subdirectory, run chmod/chown/apt/systemctl.

## META-CHECK (CRITICAL — run before reporting success)
Run this BEFORE you report done:
  for r in $(grep -oE 'references/[a-zA-Z0-9_-]+\.md' SKILL.md | sort -u); do
    [ ! -f "$r" ] && echo "BROKEN: $r"
  done
Report any broken refs in your summary. Parent will fix them — your job is
to honestly report, not to silently preserve or hide them.

## OUTPUT
Write a short summary to your return message including:
- Final SKILL.md size (KB)
- Number of new references/ files created
- List of broken refs found by META-CHECK (if any)
- Anything unexpected (e.g. original had no frontmatter, sub-sections
  that didn't fit the protocol, etc.)
```