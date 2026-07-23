# Skill-Curation Orchestration Pipeline

> Established 2026-07-15 during self-improving skill refine plan execution.
> Applies when refining/sectioning a single large SKILL.md via multi-agent pipeline.

## When This Template Applies

You're orchestrating edits to **one primary file** (usually a SKILL.md) that:
- Needs 5-12 task sections inserted, reordered, or rewritten
- Tasks appear independent but all target the same file
- Subagents need Mnemosyne IDs, section anchors, and verification commands
- Quality matters enough for Voll-2-Stage reviews (3 subagents per task)

## Pipeline Structure

```
Phase 0: ID Discovery      ← 1 subagent (read-only, resolves all external IDs)
Phase 1: Snapshot/Layout   ← 1-3 subagents (inventory + plan update)
Phase 2: File Edits        ← N×3 subagents (implementer + spec + quality, SERIAL per file)
Phase 3: Verification      ← 1-2 subagents (full audit + lessons check)
Phase 4: Tooling+Report    ← 2 subagents (hygiene script + curation report)
```

## Serial-Execution Rule

**ALL file-edit phases MUST be serial when targeting the same file.** Even tasks at different line numbers shift reference points after each `patch` call. Dispatch one task → verify → spec review → quality review → mark complete → then dispatch the next.

```python
# CORRECT: serial pipeline
# Task 5: Insert Quality Gates section
impl_result = delegate_task(goal="Insert ## Quality Gates after Hygiene", ...)
spec_result = delegate_task(goal="Verify Quality Gates spec compliance", ...)
qual_result = delegate_task(goal="Review Quality Gates code quality", ...)

# Task 6: Insert Pitfall Catalog — SAFE because line numbers settled
impl_result = delegate_task(goal="Insert ## Pitfall-Katalog after Quality Gates", ...)
spec_result = delegate_task(goal="Verify Pitfall-Katalog spec compliance", ...)
qual_result = delegate_task(goal="Review Pitfall-Katalog code quality", ...)
```

## Anchor-Table Template

Create this BEFORE dispatching any file-edit subagent. Every `patch` target is a specific header or known-unique text block.

```markdown
## Section Anchors (canonical — verify before each edit)

| Task | Operation | Insert AFTER | Verify with |
|---|---|---|---|
| 5 | Insert `## Quality Gates` | `### Flush-Kopplung` (end of Hygiene) | `grep -nE '^## ' SKILL.md` |
| 6 | Insert `## Pitfall-Katalog` | `## Quality Gates` | `grep -nE '^## ' SKILL.md` |
| 7 | Insert `## Skill-Curation Hygiene` | `## References` | `grep -nE '^## ' SKILL.md` |
| 8 | Insert `### Discovery-Tuning` | `## Cross-Session` (last subsection) | `grep -A5 '^## Cross-Session' SKILL.md` |

**If grep shows the expected anchor is missing → STOP and report to Queen.** Do NOT guess.
```

## Step-By-Step Dispatch Sequence (12-Task Example)

### Phase 0: ID Discovery (1 subagent, 30-60s)

```python
delegate_task(
    goal="Resolve Mnemosyne IDs for 5 lessons",
    context="""
    KNOWN IDs:
    - replace_all: 9a88228f4e99bf07
    - daily_quality_gate: 4845ce726ddace4a
    
    NEEDED (batch-resolve via mnemosyne_recall):
    - subagent_self_test: query="subagent self-test deception"
    - fts5_truncation: query="FTS5 Phrasen Truncation 179792"
    - tier_drift: query="Tier-Drift Three-File-Check 2026-07-11"
    
    Return: Markdown ID table with importance, tier, veracity
    """,
    toolsets=['mnemosyne', 'file'],
)
```

### Phase 1: Inventory + Plan Update (3 subagents, serial, ~5 min)

1. **Inventory** — Snapshot current SKILL.md state: line count, sections, file list, refs
2. **Decision Matrix** — Which lessons go where (promote rules)
3. **Anchor Table** — Write the section-anchor table into the plan file

### Phase 2: File Edits (N×3 subagents, serial, ~8 min per task)

Each task gets a triple:

1. **Implementer** — Executes the actual `patch`/`write_file` edit
   - Includes anchor table row + verification command in brief
   - NICHT ERLAUBT: replace_all=true, write_file > 4KB, placeholder IDs
2. **Spec Reviewer** — Verifies spec compliance against original task spec
   - Checks: section present at correct position, all requirements met, nothing extra
3. **Quality Reviewer** — Verifies code quality
   - Checks: clear naming, proper formatting, no security issues

### Phase 3: Verification (1-2 subagents, ~3 min)

- Full audit of the completed file
- Lessons check: all 5 promoted lessons present in correct sections?
- Filesystem check: all referenced paths exist?
- Mnemosyne check: all 7 Mnemosyne updates applied with correct IDs?

### Phase 4: Tooling + Report (2 subagents, ~5 min)

1. **Hygiene Script** — Create `scripts/skill-curator-hygiene.sh` with `--brief` flag
2. **Curation Report** — Write final report to `~/.hermes/docus/reports/`

## Verification Commands

```bash
# Section order integrity (after each insert)
grep -nE '^## ' ~/.hermes/skills/meta/self-improving/SKILL.md

# Specific section content (verify insertion point)
grep -B2 -A2 '^## Quality Gates$' SKILL.md

# Total size check (prevent bloat)
wc -l ~/.hermes/skills/meta/self-improving/SKILL.md

# File reference check (all referenced paths exist)
grep -oP '`~/[^`]+`' SKILL.md | tr -d '`' | xargs ls -la 2>&1 | grep -v 'No such file'

# Mnemosyne lesson count
# (manual: look up mnemosyne_recall(query='self-improving', limit=100) and count lessons with tags=['self-improving'])
```

## Pitfalls Specific to Skill Curation

| Pitfall | Symptom | Prevention |
|---|---|---|
| Wrong section order (anchor drift) | New section inserted at wrong position because prior patch shifted line numbers | Run `grep -nE '^## ' SKILL.md` BEFORE each edit to confirm current structure |
| replace_all triple-injection | `patch` replaces N>1 occurrences because old_string too generic | Always include 2+ lines of surrounding context; NEVER use `replace_all=true` |
| Mnemosyne placeholder ID | Update silently targets wrong ID or fails | Phase 0 MUST resolve IDs; embed resolved IDs in brief, not plan-file references |
| write_file truncation | Content >4KB silently truncated on write | Break into targeted `patch` calls; never `write_file` on a file >4KB for bulk edits |
| Spec drift from plan | Subagent adds scope ("while I'm here...") | Spec reviewer checks "Nothing extra added (no scope creep)" as a checklist item |

## Template Anti-Patterns

- ❌ Dispatching 3 edit subagents in parallel for the same file ("they target different sections!")
- ❌ Embedding `<TO_RESOLVE>` IDs in subagent briefings
- ❌ Skipping verification between tasks ("it's just a section insert")
- ❌ Letting Phase 3 run before Phase 2 is 100% complete
- ❌ Using `write_file` to overwrite SKILL.md instead of `patch` for targeted inserts