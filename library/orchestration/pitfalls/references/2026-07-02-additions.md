# 2026-07-02 Additions — From Two Live Sessions

This file bundles two proven patterns that emerged from real Yuno sessions
on 2026-07-02 and the skill library updates that followed. Both are validated
against actual subagent runs and verified by the parent, not theoretical.

---

## 1. Pitfall #34 — Subagent Leaves Broken Reference Links

**Status:** NEW, added to cheatsheet on 2026-07-02 after Skill-Slim-Down mission.

### Trigger Symptom
After a subagent rewrites a SKILL.md (or any markdown with `references/` links),
one or more of the linked files doesn't exist on disk. Common manifestations:

```
$ for r in $(grep -oE 'references/[a-zA-Z0-9_-]+\.md' SKILL.md | sort -u); do
    [ ! -f "$r" ] && echo "BROKEN: $r"
  done
BROKEN: references/claude-flow-orchestration-patterns.md
BROKEN: references/dmz-dual-review-patterns.md
...
```

### Three Common Sources (lesson from 2026-07-02)

| Source | What happens | How subagent behaves |
|---|---|---|
| **Pre-existing TODO-Refs** | Original SKILL.md already listed `references/<file>.md` for files that never existed | Subagent preserves them in the slim-down, doesn't notice they're broken |
| **Extraction without creation** | Subagent extracts content from inline code into `references/<file>.md` but forgets the corresponding file | Cross-reference between code and file becomes broken |
| **Invented cross-cutting structure** | Subagent invents a "Cross-cutting reference docs" or "Session-Referenzen" bullet-list that mirrors a pattern from OTHER skills but the files were never there | Adds new broken refs that didn't exist before |

### Detection
Always run this after ANY subagent that edits markdown with reference links:

```bash
SKILL=<path-to-SKILL.md>
DIR=$(dirname "$SKILL")
broken=0
for ref in $(grep -oE 'references/[a-zA-Z0-9_-]+\.md' "$SKILL" | sort -u); do
  if [ ! -f "$DIR/$ref" ]; then
    echo "BROKEN: $ref"
    broken=$((broken + 1))
  fi
done
echo "Total: $broken broken refs"
```

### Fix — Three Options (in preference order)

**Option A: Block-replace with note (RECOMMENDED for bullet-list sources)**
When the broken refs are inside a "Siehe auch" / "Related" / "Session-Referenzen" bullet-list that has no workflow dependency:

```markdown
> **Note:** Diese Session-Referenzen wurden beim Slim-Down entfernt,
> da die referenzierten Dateien nie existierten und nur als Bullet-Liste
> dokumentiert waren. Workflow-Inhalte sind vollständig in den oben
> gelisteten references/-Dateien erhalten.
```

Pros: no ghost files, no information loss, future agents understand the history.
Cons: removes the bullet-list entirely (but it was broken anyway).

**Option B: Stub files (when content is promised but missing)**
When the broken ref promises central content that doesn't exist elsewhere:
```markdown
# references/<topic>.md (stub)

TODO: This file was referenced in SKILL.md but never authored.
Move content from <other-source> here during next cleanup pass.
```
Use only if Option A would lose important context.

**Option C: Workflow re-anchoring (when ref is in [text](link) form)**
For inline link references in workflow text:
```diff
- For details on X, see [references/x.md](references/x.md).
+ For details on X, see the section below.
```

### What NOT to Do
- ❌ Create ghost-stub files for every broken ref (26 ghost files = noise)
- ❌ Re-spawn the subagent to "fix" the broken refs (context bloat, same output)
- ❌ Silently ignore broken refs (Pitfall #5 violation — verified, not trusted)
- ❌ Trust subagent's "all references intact" claim without verification

### Verification Mandate
After ANY subagent rewrites markdown:
1. Run broken-ref detection script above
2. If 1+ broken: apply Option A/B/C
3. Re-run detection script → expect 0 broken
4. Document in master report: "X broken refs found, Y fixed via Option Z"

### Real-World Case (2026-07-02)
- 9 skills slimmed
- 26 broken refs detected in 2 skills (multi-agent-work: 17, research-paper-writing: 9)
- All fixed via Option A in single inline patch per skill (~10 lines edit each)
- Subagent #4 transparently noted broken refs in its summary; others were silent
- Lesson: verify even when subagent says "clean"

---

## 2. Multi-Wave Subagent Pattern (Skill-Slim-Down, 2026-07-02)

**Status:** NEW, validated on 9 skills in two waves.

### When to Use
When `max_concurrent_children=5` (or whatever your config is) limits the
parallelism per wave, but you have MORE than 5 tasks. Example: 9 skills
to slim down.

### Pattern

```
Phase 0: PARENT runs pre-scan → produces ranked list of candidates
Phase 1: PARENT spawns WAVE 1 (5 subagents in parallel, delegate_task tasks=[])
         → Wait for ALL to complete (async batch)
Phase 2: PARENT verifies Wave 1 outputs (broken-ref check, file sizes, frontmatter)
         → Fix any issues inline
Phase 3: PARENT spawns WAVE 2 (next 5 subagents in parallel)
         → Wait for ALL to complete
Phase 4: PARENT verifies Wave 2 outputs
Phase 5: PARENT writes master report (combines Wave 1 + Wave 2)
```

### Why Multi-Wave instead of all-at-once

| Approach | Pros | Cons |
|---|---|---|
| **Single batch (≤5)** | Simple, all-parallel | Limited by `max_concurrent_children` |
| **Multi-wave (5+5)** | Scales to any size, parent can verify between waves | Slightly more orchestration |
| **Sequential** | Easy debugging | Slow (5x slower than parallel) |

### Configuration (Hermes)
- `max_concurrent_children` lives in `delegation.max_concurrent_children` in
  Hermes config (typically 5 by default).
- `max_spawn_depth=1` means nested delegation is OFF — every batch is leaves.
- Use `delegate_task(tasks=[...])` (BATCH MODE) for multi-wave, not multiple
  sequential `delegate_task(goal=...)` calls.

### Subagent Briefing Consistency Across Waves

Each subagent in each wave should receive the **same briefing template**
with skill-specific substitutions. Example for Skill-Slim-Down:

```
SKILL.md is at ~/.hermes/skills/<category>/<skill>/SKILL.md (<SIZE>KB).

PROTOCOL:
1. Read the full SKILL.md.
2. Keep in SKILL.md: YAML frontmatter (EXACT as-is), intro paragraph,
   section headings as outline (1-2 sentence summaries), critical warnings/
   pitfalls in short bullet form, links to references.
3. Extract into references/: all code blocks >10 lines, step-by-step
   procedures, bug logs, version histories, API details.
4. Suggested new files: references/<topic>.md (one per logical section).
5. Each reference file opens with a top-level heading matching the SKILL.md
   outline.
6. Target: SKILL.md ≤<X>KB.
7. Report the final sizes.
```

The `<category>/<skill>` and `<SIZE>KB` and `<X>KB` differ per task; the
protocol is identical.

### Wave-Verification Checkpoint

Between waves, run this checklist:

```bash
# 1. All Wave-N files exist?
for skill in "${wave_n_skills[@]}"; do
  [ -f "$skill/SKILL.md" ] && echo "✅ $skill" || echo "❌ $skill MISSING"
done

# 2. Size targets met?
for skill in "${wave_n_skills[@]}"; do
  size=$(($(wc -c < "$skill/SKILL.md") / 1024))
  target=$(grep -oP '≤\K[0-9]+' briefing_template)
  [ "$size" -le "$target" ] && echo "✅ $skill: ${size}KB ≤ ${target}KB" || \
    echo "⚠️  $skill: ${size}KB > ${target}KB (still acceptable, log it)"
done

# 3. Frontmatter intact?
for skill in "${wave_n_skills[@]}"; do
  has_name=$(head -50 "$skill/SKILL.md" | grep -c '^name:')
  fm_end=$(head -50 "$skill/SKILL.md" | grep -n '^---$' | tail -1)
  [ "$has_name" -ge 1 ] && [ -n "$fm_end" ] && echo "✅ $skill frontmatter" || \
    echo "❌ $skill frontmatter BROKEN"
done

# 4. Broken refs?
for skill in "${wave_n_skills[@]}"; do
  broken=$(grep -oE 'references/[a-zA-Z0-9_-]+\.md' "$skill/SKILL.md" | \
    sort -u | while read r; do [ ! -f "$skill/$r" ] && echo x; done | wc -l)
  echo "$skill: $broken broken refs"
done
```

If any check fails, **fix inline** (Option A for broken refs, manual patch
for broken frontmatter) before spawning Wave 2. Don't re-spawn the failing
subagent — context is already lost.

### Proven Impact (2026-07-02)
- 9 skills slimmed in 2 waves (5+4)
- Wall-clock: ~25 min total (12 min Wave 1 + ~13 min Wave 2)
- 0 Subagent-Crashes
- 0 in-place content loss
- 26 broken refs caught and fixed post-Wave-2 in ~2 min inline
- Master-Report: ~/docs/system/skill-slim-down-2026-07-02.md

---

## 3. Cross-Skill Insight: The "Verify Subagent Output" Meta-Pattern

**Status:** Distilled from Pitfall #5, #29, #34.

All three pitfalls share the same root cause: **parent trusts subagent
output without independent verification**. The cheatsheet already documents
the 3-Tier Verification (Datei-Existenz + Content-Validierung + Realitäts-Check).

The Skill-Slim-Down mission added a 4th tier worth documenting:

### Tier 0: Pre-Edit Snapshot
Before the subagent runs, capture the BEFORE state of the file:

```bash
mkdir -p ~/docs/system/<mission>/snapshots
cp -r <target-dir>/ ~/docs/system/<mission>/snapshots/<skill>-before/
```

After subagent completes, run `diff -rq` between snapshot and current:

```bash
diff -rq ~/docs/system/<mission>/snapshots/<skill>-before/ <target-dir>/ \
  | grep -v "^Only in.*\.references"
```

This catches the case where the subagent rewrote a file but in a way that
DOESN'T match the briefing (e.g., slimmed a section it shouldn't have, lost
a critical pitfall).

### Tier 4: Subagent Meta-Check
Subagents can self-deceive in their own summary ("all references intact").
Add this to every multi-wave briefing:

```
META-CHECK: Before reporting success, run:
  for r in $(grep -oE 'references/[a-zA-Z0-9_-]+\.md' SKILL.md | sort -u); do
    [ ! -f "$r" ] && echo "BROKEN: $r"
  done
Report any broken refs in your summary. Parent will fix them — your
job is to honestly report, not to silently preserve or hide them.
```

Subagent #4 in the 2026-07-02 mission DID follow this pattern (transparently
noted 17 broken refs). Subagents #1, #2, #3, #5 did NOT mention their broken
refs in the summary, even though they had them. The 4-tier pattern works
when the briefing asks for it explicitly.

### Master-Report Verifikations-Matrix v2

```markdown
| Subagent | Tier 0 Snapshot | Tier 1 Datei-Existenz | Tier 2 Content | Tier 3 Realität | Tier 4 Broken-Refs | Status |
|---|---|---|---|---|---|---|
| #1 | ✅ captured | ✅ exists | ✅ matches | ✅ verified | ⚠️ 9 broken (fixed post) | OK |
| #2 | ✅ captured | ✅ exists | ✅ matches | ✅ verified | ✅ 0 broken | OK |
| #3 | ✅ captured | ✅ exists | ✅ matches | ✅ verified | ✅ 0 broken | OK |
| #4 | ✅ captured | ✅ exists | ✅ matches | ✅ verified | ⚠️ 17 broken (fixed post) | OK |
```

The Tier 0 column is the new addition. Tier 4 is renamed from "Broken-Refs"
to clarify the meta-check nature.

---

## 4. Cross-Reference to Master-Report

Full details, before/after table, lessons learned, and workflow:

→ `~/docs/system/skill-slim-down-2026-07-02.md`

This file (references/2026-07-02-additions.md) is the **skill-side mirror**
of patterns that emerged from the same mission. Use both together when
planning the next multi-wave subagent mission.

---

## 5. Round 2 Additions — 2026-07-03 (Skill-Slim-Down Wave 2)

The Skill-Slim-Down mission continued the next day with **Round 2: 10 more skills slimmed across 2 waves**. Three new patterns emerged:

### 5a. Subagent-Strategie-Selbstwahl (claude-design)

Subagent #3 (claude-design) was briefed with the standard multi-batch template but **self-selected Parent-Direct sequential** as its execution strategy. Reasoning it gave: "Single-skill Parent-Direct path is more efficient — dispatch overhead would have exceeded the actual work."

**Pattern:** The Skill-Slim-Down Protocol's "When to skip the subagent step (Parent-Direct)" section (now in cheatsheet SKILL.md) already documents this decision rule. The lesson is: **trust subagent judgment when it cites the documented rule** rather than forcing the multi-batch template.

**Heuristic:** When a subagent reports strategy deviation with a citation to the documented protocol, the deviation is a feature. Don't force it back to the briefing template.

### 5b. Markdown-Compression-Iterations (10 patch rounds)

Subagent #3 (claude-design Parent-Direct) needed **10 successive patch iterations** to land SKILL.md under the 12KB target. Initial write was ~15-25% over target (15KB → 12KB target).

**Pattern:** When slimming a content-dense creative SKILL.md in Parent-Direct mode:
- First write targets ~80% of size target, not 100% (e.g. write to ~10KB when target is ≤12KB)
- Each patch round removes ~200-500 bytes (whitespace, comma consolidation, redundant trailers)
- Apply ONE compression lever per round (Pitfall #27 in skill-library-maintenance): table conversion, row folding, layer prefix-coding, redundant-trailer removal
- Don't try to compress multiple things in one patch — risk of adjacent-region merge bugs (Pitfall #13)

**Verified 2026-07-03:** claude-design 25.2KB → 11.9KB, 10 patches, ~9 min wall-clock.

### 5c. Wave-Clock-Variance Heuristic

Wave 2 of Round 2 took **33 min** vs Wave 1's **8 min** for the same N=5. Root cause: content-dense skills (creative-class, code-documenting) require 5-10x more API calls.

**Heuristic for parent planning:**

| Skill Class | API Calls | Duration |
|---|---|---|
| Tutorial/Wiki-style | 10-25 | 3-5 min |
| Creative-class | 30-80 | 10-30 min |
| Code-documenting | 40-60 | 25-35 min |

**Mitigation options if wall-clock is too long:**
- Split into sub-waves (creative/code-documenting first, others after)
- Use Parent-Direct for the densest skill (saves ~30-50% wall-clock)
- Communicate timing expectations to user BEFORE dispatch

**Verified 2026-07-03:** Wave 2 subagent durations: 132s (hermes-mcp-integration), 210s (ollama-local-hosting), **1896s claude-design (80 calls)**, **1757s hermes-v7-sse (42 calls)**, 273s (hermes-v7-sse-server).

### 5d. Stub-vs-Block-Replace (Markdown tables)

When broken refs appear in **Markdown table cells** (not bullet-lists), the bullet-block-replace approach from Round 1 §1 doesn't work — block-replacing the table would destroy the table structure.

**Pattern:** Create stub-files with TODO-status headers. Each stub:
- Has topic-relevant Quick-Reference content (~600-800 bytes each)
- Honest about being planned-for-expansion: `> **Status:** Stub — geplant für Ausbau. Subagent #N (Wave X, DATE) hat diesen Link aus dem Original-SKILL.md übernommen, aber nicht ausgearbeitet.`
- Preserves table-cell link structure
- Document the gap, provide genuine starter content

**Verified 2026-07-03:** `creative/p5js` had 8 broken refs all in table-column "Reference" cells. Solution: 8 stub files, all linked correctly, parent-side cleanup.

### 5e. Pre-Existing-Reference-Audit (avoid duplication)

When the briefing claims "skill has N reference files", verify N before delegating. Briefing may conflate:
- `references/*.md` — real skill content
- `memory/runs/*.json` — execution artifacts
- `.archive/duplicates-*/...` — duplicate copies

**Verified 2026-07-03:** hermes-orchestration briefing said "63 reference files"; actual `references/` count was 7 (+ 56 run-artifacts in `memory/runs/`). Subagent correctly identified the discrepancy and avoided creating duplicate content.

**Heuristic for parent:**
```bash
ls ~/.hermes/skills/<category>/<skill>/references/*.md 2>/dev/null | wc -l
# vs claimed count in briefing
```

If discrepancy, correct the briefing BEFORE dispatching the subagent.

### 5f. MD5-Frontmatter-Verifikation (high-confidence audit)

For critical audits where frontmatter drift would silently break skill loading, use MD5-hash verification instead of `diff`:

```bash
head -50 ~/.hermes/skills/<skill>/SKILL.md | grep -A100 '^---$' | sed '/^---$/q' | md5sum
```

Verified 2026-07-03 by hermes-mcp-integration subagent: hash `282410bc...` matched pre-slim hash byte-for-byte. Don't use MD5 for routine verification — `diff` is more readable when something actually breaks.

---

**Last validated:** 2026-07-03, Round-2 mission (10 skills, 2 waves, 244KB → 109KB, all clean post-cleanup). Pattern sources: cheatsheet "Skill-Slim-Down Pattern" + skill-library-maintenance Pitfalls #17-#30.