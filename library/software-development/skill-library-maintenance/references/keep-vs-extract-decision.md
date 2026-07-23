# Keep vs Extract — Decision Guide for Skill Slim-Down

When slimming a SKILL.md, the hardest call is which content stays in the slim main file vs which goes to `references/`. This guide captures the line that worked in real extractions, with concrete examples.

## The 80/20 Line

The reader of a slim SKILL.md is **scanning for what to do next**, not reading linearly. Keep anything that supports scanning. Extract anything that only matters during deep execution.

## KEEP in SKILL.md (high signal-per-byte)

| Content type                   | Why keep                                                              | Example                                               |
|--------------------------------|-----------------------------------------------------------------------|-------------------------------------------------------|
| YAML frontmatter               | REQUIRED — name/description/triggers must stay intact                 | Top of file, never touch                              |
| Intro + 1-paragraph "what this is" | Sets context in <2s                                                  | "Von Research bis Implementierung in einem Durchlauf" |
| Mode/comparison tables         | High info-density, skim-readable                                      | Delivery vs Experiment; /research vs /multi-agent-work|
| Architecture ASCII diagram     | Visual mental model in <50 lines                                      | Supervisor → Worker/Critic/Researcher                 |
| Phase outline (ASCII flow)     | Skim the whole pipeline in <30s                                       | 6-phase workflow box diagram                          |
| Phase-0 as **checklist**       | Active gate before action; must be inline                             | `- [ ] delegate_task smoke test`                      |
| Short code blocks ≤10 lines    | Inline-runnable; reader doesn't have to open another file             | `mkdir -p ~/projects/...`                             |
| One-line pointers to references | Tells reader "detail exists, here's where"                           | `→ See references/phase-details.md for ...`           |
| Trigger pattern + 3 examples   | User needs to know how to invoke                                     | `/multi-agent-work "..."`                             |

## EXTRACT to `references/` (deep-dive content)

| Content type                       | Why extract                                                   |
|------------------------------------|---------------------------------------------------------------|
| Step-by-step instructions          | Belongs in execution flow, not overview                       |
| Code blocks >10 lines              | Token cost on every `skill_view` load                         |
| Bug logs, fix histories            | Session-specific, bloats overview                             |
| Session references                 | Point to them from SKILL.md, don't inline                     |
| Long pitfall lists                 | One consolidated `references/pitfalls.md` beats inline noise  |
| API deep-dives, schema definitions | Reference material, not skim material                         |
| Detailed config examples           | Belongs in execution references                               |
| Multi-row comparison tables (>6 cols)| Tables over ~6 columns hurt skim-flow; extract                |

## Decision Examples From Real Sessions

**`multi-agent-work` slim-down (47KB → 12KB):**

| Content                                    | Decision         | Reasoning                                                     |
|--------------------------------------------|------------------|---------------------------------------------------------------|
| 6-phase ASCII workflow diagram             | KEEP             | 30 lines, visual pipeline, skim-readable                      |
| Architecture diagram (Supervisor/Worker/Critic) | KEEP          | 12 lines, mental model                                        |
| Mode table (Delivery vs Experiment)        | KEEP             | 2 rows × 6 cols, immediate scanning value                     |
| Comparison table (`/research` vs `/multi-agent-work`) | KEEP | 4 rows × 2 cols, sets context                                |
| Trigger pattern + 3 examples               | KEEP             | Required for invocation                                       |
| Phase 0 as ~140 lines of gate-test commands | EXTRACT         | Execution detail, not skim material                           |
| Critic-Gate script + integration bash      | EXTRACT         | 100+ lines of bash, only run during Phase 4                   |
| Phasen-Timeout table                       | EXTRACT         | 5 rows × 5 cols, reference, not overview                      |
| Kontext-Template (full delegate_task block) | EXTRACT         | 50-line code block, copy-paste during execution               |
| Queen-Rule allow/forbid table              | EXTRACT (link)  | Long philosophical rule — keep pointer + 1-line summary inline |
| 25 pitfalls with numbered duplicates       | EXTRACT         | Long list, group by category in references/pitfalls.md        |
| GreyScript deployment details              | EXTRACT         | Domain-specific to GreyHack use case                          |
| Slash-command registration YAML            | EXTRACT         | One-time config, not workflow-relevant                        |

## Pitfalls of the Slim-Down Process Itself

1. **Don't over-extract tables.** Tables <6 rows are skim-friendly. A 4-row comparison table in `references/` is harder to read than inline.

2. **Don't keep prose because it's "important."** The slim SKILL.md is an INDEX, not the manual. If prose doesn't change what the reader does in the next 5 minutes, it goes.

3. **Keep the ASCII diagrams even when they cost bytes.** A 30-line ASCII diagram = ~1KB. Worth it for the skim-value. Don't extract them to references/ — that breaks the mental model.

4. **Preserve historical numbering when extracting pitfalls.** If pitfalls.md has "17, 18, 19, 17, 18, 19" because duplicates existed in the original, KEEP them. Renumbering creates confusion when session notes reference "pitfall #22" by number.

5. **Add the reference list to SKILL.md front-matter block, not buried at bottom.** First thing after the intro block: a "Referenzen" list with the new `references/<file>.md` entries FIRST, then external session references. The reader sees "where do I drill" before reading the workflow.

6. **Use the `todo` tool with merge=true to track the extraction phases.** Pattern that worked:
   - Read full file
   - Plan (identify keep vs extract per section)
   - Create reference files (parallel `write_file` calls where possible)
   - Rewrite SKILL.md slim version
   - Verify sizes + reference links

7. **When the slim target is "≤10KB" but the intro + frontmatter + 2 diagrams is already 4KB, plan for ~6-8KB of body content.** Don't over-slim — readable > minimum-bytes.

8. **Test that every reference link in SKILL.md points to a file that exists.** Before declaring done, list both directories and verify all paths resolve. Missing references are worse than over-extracted content.

## Size Budget Cheatsheet

| Slim target    | Frontmatter | Diagrams | Tables | Body prose | Code blocks |
|----------------|-------------|----------|--------|------------|-------------|
| ≤8KB           | ~2KB        | 1 only   | 2-3    | 1-2KB      | 0-1 inline  |
| ≤12KB (typical)| ~2KB        | 2-3      | 3-5    | 3-4KB      | 1-2 short   |
| ≤15KB          | ~2KB        | 3-4      | 5-7    | 5-6KB      | 2-3 short   |

For most slim-downs the realistic floor is ~10-12KB — below that, the SKILL.md becomes a bare index with no skim value.

## Phase-Organized Skills (One Ref Per Phase)

A common slim-down target is a skill organized as a linear pipeline of phases (e.g. "Phase 0 through Phase 7" with a numbered workflow). These have a characteristic extraction shape: **one reference file per phase**, named to match the SKILL.md section.

### Naming convention

| Source section in SKILL.md      | Reference file                       |
|---------------------------------|--------------------------------------|
| `## Phase 0: Project Setup`     | `references/phase0-setup.md`         |
| `## Phase 1: Literature Review` | `references/phase1-literature.md`    |
| `## Phase N: <Title>`           | `references/phaseN-<slug>.md`        |

The top-level heading inside the reference file should mirror the SKILL.md section exactly: `# Phase N: Title`. This makes the reference self-describing if opened in isolation.

### The overview-table pattern (the right shape for SKILL.md)

Replace the original "phase N prose subheading + 1-paragraph summary per phase" block with a **single 4-column table**:

```markdown
| # | Phase | Goal | Reference |
|---|-------|------|-----------|
| 0 | Project Setup | Establish workspace, identify contribution | [phase0-setup.md](references/phase0-setup.md) |
| 1 | Literature Review | Find papers, gather verified citations (never hallucinate BibTeX) | [phase1-literature.md](references/phase1-literature.md) |
| 2 | Experiment Design | Map claims → experiments, define baselines | [phase2-experiment-design.md](references/phase2-experiment-design.md) |
| 3 | Execution & Monitoring | Run reliably, recover from failures | [phase3-execution.md](references/phase3-execution.md) |
```

One row per phase, the **Goal** column carries the rich-sentence summary that the old prose subheading carried, and the **Reference** column carries the link. Saves ~1.5-2KB versus keeping both the table AND the prose subheadings, and it's more skim-friendly.

### Cross-cutting reference docs (separate from per-phase files)

Some reference docs span multiple phases (e.g. writing-style guide used in both Phase 5 drafting and Phase 6 review). Don't force these into a single phase file — list them in their own "Cross-cutting reference docs" subsection right after the phase-overview table:

```markdown
### Cross-cutting reference docs (used across phases)

- [references/writing-guide.md](references/writing-guide.md) — Gopen & Swan, Lipton, Steinhardt
- [references/citation-workflow.md](references/citation-workflow.md) — Citation APIs, CitationManager class
```

This signals to the reader: "this is a multi-phase tool, not tied to one phase."

### Worked example: `research-paper-writing` (104.95KB → 14.5KB)

A 2,496-line ML-paper-writing pipeline organized as 8 phases plus cross-cutting topics (LaTeX preamble, writing style, reviewer guidelines). Original size 104,950 bytes.

| Content | Decision | Reasoning |
|---------|----------|-----------|
| YAML frontmatter | KEEP | Required, never modify |
| ASCII pipeline diagram (8-phase box flow) | KEEP | ~30 lines, mental model, skim value |
| "When To Use" + "Core Philosophy" (5-point list) + Proactivity tables | KEEP | High-signal intro, sets the tone |
| Per-phase headings (`### Phase 0: Project Setup` + 4-sentence summary) | EXTRACT and replace with table | 8 phase subheadings + summaries = ~2.5KB that the table captures in 1.5KB |
| Phase 0 step-by-step (workspace, git, contribution, compute budget) | EXTRACT → `references/phase0-setup.md` | 7 detailed steps with bash blocks |
| Phase 1 (literature, breadth-depth search, citation verification 5-step protocol, DOI→BibTeX Python code) | EXTRACT → `references/phase1-literature.md` | Includes a 14-line Python snippet — clear extract |
| Phase 5 (largest section: full LaTeX preamble, 3 TikZ templates, algorithm2e, latexdiff, SciencePlots, every section writing guidance) | EXTRACT → `references/phase5-drafting.md` | Came out at 32KB / 783 lines — that's the largest single reference. Don't try to keep any of it inline. |
| Phase 8 (post-acceptance poster/talk/blog), Workshop/Short Papers, Paper Types Beyond Empirical ML | EXTRACT → `references/phase7-submission.md` | Phase 8 wasn't in the original SKILL.md's numbered pipeline; bundled with Phase 7 in the reference because it's post-submission material |
| Hermes Agent Integration (tool list, related skills, experiment monitoring loop, session startup) | KEEP, but compact | Standard pattern across skills — keep as a section, but inline-link rather than bullet-explaining every tool |
| Common Issues table (12 rows of "issue → solution") | REPLACE with quick-index table | Original had full prose solutions per row; new table points to the relevant phase reference instead |
| Key External Sources | KEEP, compact | One line per category instead of bulleted URLs |

Final: SKILL.md = **14,513 bytes / 250 lines** (86% size reduction). 8 reference files totaling 85,561 bytes / 2,088 lines. All cross-links verified to resolve.

### Pitfalls specific to phase-organized skills

1. **Don't create `references/phaseN-<slug>.md` files smaller than ~50 lines.** A 30-line reference file means you didn't extract enough. Either extract more content from that phase or merge it with an adjacent phase file.

2. **Don't invent a phase numbering scheme that doesn't match the original SKILL.md.** If the original calls it "Step 0.3: Set Up Version Control", the reference file is `references/phase0-setup.md` (matching the parent phase heading), not `references/step0-3-version-control.md`. The phase-level granularity is what makes the extraction scannable.

3. **Long LaTeX/TikZ-heavy phases produce 30-50KB reference files.** That's fine. References don't have the same size budget as SKILL.md — they get loaded only when needed.

4. **If a phase has fewer than ~10 substantive steps, consider merging it into the adjacent phase's reference file.** Eight tiny reference files are harder to navigate than six substantive ones.

5. **The "common issues" table is a great skim-and-fix tool.** Build it as a quick-index (issue → link to relevant reference section) instead of repeating solutions. Saves ~2KB.

## Content/Technique Skills (No Phase Structure)

Not every skill is a pipeline. Some are **content/technique skills** organized around a taxonomy of items (e.g. "29 patterns to recognize and rewrite") plus a worked example. These need a different extraction shape than phase-organized skills.

### Key differences from phase-organized skills

| Aspect | Phase-organized | Content/technique |
|--------|-----------------|-------------------|
| Section shape | Linear numbered pipeline (Phase 0 → N) | Taxonomy of N items, grouped by category |
| Reader goal | "What step am I on?" | "What's the rule for this kind of mistake?" |
| Primary extract | One file per phase | One file for "all techniques" + one file for "full worked example" |
| Skim-table shape | `# / Phase / Goal / Reference` columns | Pattern name → one-line summary, grouped by category heading |
| Numbering | Sequential (0, 1, 2, …) | Stable from source — **never renumber when extracting** |

### Recommended split: two reference files

For content/technique skills, the slim-down almost always produces **exactly two** reference files:

1. `references/techniques-detailed.md` — full detail per item (words-to-watch, problem statement, before/after examples). One file beats N tiny files when items share structure.
2. `references/<example>-walkthrough.md` — the full worked end-to-end example (input → draft → audit → final → change list). Process checklists often live at the top of this file.

**Why not one big file?** The reader is in different modes: "give me the rulebook for pattern X" (techniques-detailed) vs "show me what a complete rewrite looks like" (walkthrough). Splitting them matches those modes.

**Why not N tiny files (one per item)?** With ~29 items, 29 reference files is navigation hell. One consolidated `techniques-detailed.md` with anchor headers (`### 7. Overused "AI Vocabulary" Words`) lets the reader grep, scroll, or jump-to-section from SKILL.md pointers.

### Worked example: `humanizer` (30,117 → 11,211 bytes, ≤12KB target)

A creative-category skill ported from `blader/humanizer` (MIT) — 29 anti-AI-pattern rules plus personality/soul guidance plus a 7-paragraph worked example. Original 30,117 bytes / 593 lines.

| Content | Decision | Reasoning |
|---------|----------|-----------|
| YAML frontmatter (29 lines) | KEEP | Required, never modify |
| Intro paragraph + "Key insight" callout | KEEP | Sets context in <2s |
| "When to use" trigger list | KEEP | Required for skill invocation |
| "How to use it in Hermes" (3 input modes) | KEEP | Compact, high-signal |
| Voice Calibration (sentence length, word choice, transitions) | KEEP (condensed) | Compact 8-bullet form; not a phase, just a checklist |
| "Your task" 7-step process | KEEP | Inline checklist, reader needs it |
| **PERSONALITY AND SOUL** (signs-of-soulless-writing + how-to-add-voice + before/after) | KEEP verbatim | The voice-addition core, not just pattern-stripping. Distinguishes this skill from a generic anti-AI-tells checklist. ~1.5KB but irreplaceable. |
| Technique overview (29 items grouped by 5 categories) | KEEP as compact one-line summaries | Reader skims to find the category, drills into references/ for the full before/after |
| All 29 patterns with words-to-watch + before/after | EXTRACT → `references/techniques-detailed.md` | ~16KB / 325 lines, opt-in detail |
| Full 7-paragraph worked example + 10-step process checklist + changes-made bullet list | EXTRACT → `references/full-example-walkthrough.md` | ~7.6KB / 70 lines, demo of end-to-end flow |
| Critical rules / pitfalls (NEW distilled bullets) | KEEP as new section | 9 bullets distilled from the 29 patterns; SKILL.md gets quick-reference pitfalls without bloating |
| Attribution | KEEP | Required for license |
| Output format | KEEP (4 lines) | Compact |

Final: SKILL.md = **11,211 bytes / 195 lines** (63% reduction, under the ≤12KB hard cap). 2 reference files totaling ~24KB. One `skill_view` call to confirm `linked_files.references` exposes both new files (`{"references": ["references/full-example-walkthrough.md", "references/techniques-detailed.md"]}` — order alphabetical).

### Pitfalls specific to content/technique skills

1. **Don't renumber the items when extracting.** If the source says "1. Significance inflation, 2. Notability inflation, …, 29. Fragmented headers", the references file keeps numbers 1–29 and the SKILL.md overview keeps numbers 1–29. Future readers cross-referencing "pattern #7" by number will silently break otherwise. Verified 2026-07-03: `humanizer` overview uses the same numbering as `techniques-detailed.md` headings.

2. **Keep the section that gives the skill its character, even if it's bulky.** For `humanizer`, PERSONATLITY AND SOUL (~1.5KB of kept prose + before/after) is what makes the skill "add voice" rather than just "strip AI tells". A subagent optimizing for size alone would extract it. The slimming operator must judge: would removing this section change what the skill DOES, or just change its bulk? If the former, KEEP.

3. **Two reference files, not one mega-file.** Tempting to merge `techniques-detailed.md` and `<example>-walkthrough.md` into a single `references/full-content.md`. Don't — the reader's mode is different (rule lookup vs walk-through demo). Verified 2026-07-03: split form yields cleaner SKILL.md pointers ("see techniques-detailed for the rulebook" vs "see walkthrough for end-to-end").

4. **Compact overview form: name + one-line summary, grouped by category heading.** Not a 4-column table (no `#` column needed for non-phase content). Not a flat bullet list (loses category structure). Pattern that worked:

   ```markdown
   **Content patterns** — puffy framing that says nothing:
   1. Significance/legacy/broader-trends inflation — "pivotal moment", "vital role", …
   2. Notability & media-coverage pile-on — listing outlets and follower counts without context
   …

   **Style** — visual tells:
   14. Em-dash overuse — for "punchy" rhythm; usually commas/periods work better
   …
   ```

5. **Add a "Critical rules / pitfalls" distilled-bullets section in SKILL.md even if the detailed patterns are extracted.** Readers who only load SKILL.md need a top-10 quick reference; readers who load `techniques-detailed.md` get the full before/after. The two modes serve different scan needs. Verified 2026-07-03: 9 critical rules distilled from the 29 patterns, ~600 bytes, catches the most common issues at a glance.

## Code-Contract Skills (Architectural / API Skills)

A third class of skill is the **architectural / code-contract skill** — its value is "here's the class hierarchy, the safety pattern, the CLI contract" that a future builder will copy as scaffolding. The slim-down target is the code contracts, not the prose.

### Spotting them

- Source SKILL.md is mostly code blocks (ABC classes, manager patterns, argparse setups) interleaved with usage notes
- The headline value is "the pattern that other modules conform to"
- Without the contracts inline, the SKILL.md becomes useless as a quick-reference for new builders

### Recommended split (typical ≤12KB target)

| File                                | Content                                                                 |
|-------------------------------------|-------------------------------------------------------------------------|
| `SKILL.md`                          | Frontmatter + intro + **all small contracts inline** + workflow outline |
| `references/<topic>-procedures.md`  | Long step-by-step procedures, command sequences, ordering rules          |
| `references/<topic>-analysis.md`    | Manual inspection workflows, search/audit guides, worked examples       |
| `references/safety-patterns.md`     | Pitfall lists, JSON-output workarounds, error helpers, cron integration |
| Pre-existing reference files        | LEVERAGE them — do not duplicate. Point to them from SKILL.md's References list |

### KEEP in SKILL.md (the contracts)

Even at <12KB, keep these in SKILL.md if the skill is code-contract-shaped:

| Content                     | Why keep                                                |
|-----------------------------|---------------------------------------------------------|
| Base class ABC interface    | Every scanner extends it — needs to be visible on load  |
| SafetyManager / guard class | Destructive operation gate — readers need the contract  |
| CLI argparse skeleton       | Future builders copy-paste it as scaffolding            |
| Cleanup-targets table       | 1-row-per-cache quick reference, never extract          |

The size budget for code contracts is "≤15 lines per block". A 30-line class extraction is fine; a 60-line class extraction is too much — extract it.

### Pitfalls specific to code-contract skills

1. **Don't extract the central ABC / Manager contract to references/ even if it's "long".** A 20-line BaseScanner class IS the skill's value. If a builder has to drill into a reference file to remember the interface, you've over-extracted. Verified 2026-07-03: `linux-system-maintenance` kept `BaseScanner` and `SafetyManager` in SKILL.md despite combined ~30 lines, because they ARE the skill's contribution.

2. **Don't re-create reference files when pre-existing ones cover the topic.** If the skill already has `references/system-inspection-2026-06-03.md` (worked example) and `references/yuno-cleaner-implementation.md` (architecture), point to them from the new slim SKILL.md — don't write parallel "all-architecture.md" or "all-examples.md" files. Verified 2026-07-03: `linux-system-maintenance` already had 9 reference files; the slim-down added only 3 new ones (`cleanup-procedures.md`, `disk-analysis.md`, `safety-patterns.md`), keeping existing files intact.

3. **Audit the source for prior-editing artifacts BEFORE extracting.** Skills that have been through multi-line patch operations often carry:
   - Stray literal `set -euo pipefail` lines (artifact of incomplete code-block edits) — 22× seen in `linux-system-maintenance` pre-slim
   - Duplicate sections (e.g. `## Hermes Integration` appears 2× because two editors added the same block) — verify with `grep -c '^## <Heading>' SKILL.md`
   - Truncated half-headings (`## Ergebnis` followed by a table with no body, mid-section) — look for headings with `##` marker but no following prose

   Pattern that worked:
   ```bash
   grep -n '^## ' SKILL.md                              # spot duplicates
   grep -c '^set -euo pipefail' SKILL.md                # spot code artifacts
   ```
   Clean these up in the slim-down — leaving them propagates the corruption forward and confuses future readers.

4. **Don't merge Chrome/Brave/etc. caches into one row without care.** Browser caches look identical but each browser's directory layout differs. A "merged" row using brace-expansion syntax reads as a single path in the slimmed table but confuses readers who copy-paste it. If the merged form obscures meaning, leave separate rows even if it costs bytes.

## Recommended Reference-File Count by Source Size

Realistic count of NEW reference files a single slim-down should add (excluding pre-existing files):

| Source SKILL.md size | Frontmatter + intro floor | Body to extract | Recommended NEW ref files |
|----------------------|---------------------------|-----------------|---------------------------|
| <20KB                | ~3KB                      | ~5-8KB          | 0-1 (often nothing to do)  |
| 20-35KB              | ~3KB                      | ~15-25KB        | 2-3                       |
| 35-60KB              | ~3KB                      | ~30-50KB        | 3-5                       |
| >60KB                | ~3KB                      | massive         | 5-8 (may warrant delegation) |

Verified 2026-07-03: `linux-system-maintenance` was 28,066 bytes source, target ≤12KB (12,288B) → added exactly 3 new reference files (9,063 + 3,731 + 9,229 = 22,023 B extracted). Below 20KB source, do NOT create new reference files — the overhead of one new file exceeds its slimming benefit.