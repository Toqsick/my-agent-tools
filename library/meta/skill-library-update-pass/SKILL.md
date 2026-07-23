---
name: skill-library-update-pass
title: "Skill Library Update Pass — Diagnose → Backup → Patch → Split → Verify"
description: "Use when the user explicitly asks for a destructive mass-update of the skill library after a read-only audit — frontmatter hygiene pass, trigger-keyword polish, monolith split into routing-stub + sub-skills. NOT for single-skill edits (use patch/skill_manage), read-only audits (use skill-reviewer), or creating brand-new skills (use skill-creator). Always backs up to tar.gz before destructive work, validates YAML after every pass, restores from backup on any silent corruption."
category: meta
version: 1.0.0
created: '2026-07-23'
author: Yuno (Basti-orchestrierte Session 2026-07-23)
lane: koenigin
agent: Yuno
trigger_keywords:
- skill library update
- frontmatter hygiene
- monolith split
- skill library audit + update
- patch all skills
- trigger keyword polish
- library wide patch
- destructive skill edit
- tar.gz backup skills
keywords:
- skills
- update
- patch
- audit
- monolith
- split
- frontmatter
- hygiene
- tar.gz
- backup
related_skills:
- skill-reviewer
- skill-library-maintenance
- skill-creator
- skill-polisher
- skill-duplicate-audit
- self-improving
- clarify-options-pattern
last_curated: '2026-07-23'
curated_by: 'Yuno'
routing_hint: |
  Trigger when user says "audit + update the skill library" or "patch all
  skills" or "split the monoliths". Bridges read-only skill-reviewer with
  destructive skill-library-maintenance. Three-step: Diagnose (skill-reviewer
  v2.0.0 Mode 2) → Plan + Backup → Execute (Frontmatter / Polish / Split
  scripts) → Verify. Never run without tar.gz backup.

changelog:
- '1.0.0 (2026-07-23): Initial release. 4 production scripts (patch_frontmatter_v3,
  polish_triggers_v3, split_mirofish, split_kanban). Verified on 337 active
  skills + 2 monolith splits (mirofish 101KB→5 files, kanban-system-health
  86KB→5 files). 0 data loss, 346/346 YAML-valid.'
---


# Skill Library Update Pass

Companion to `skill-reviewer` (which is **strictly read-only**): this skill governs the **destructive update workflow** — frontmatter hygiene, trigger-keyword polish, monolith splits — with mandatory backup, validation, and reversibility.

## When To Use

Trigger when the user asks for **both audit AND update** in one go:
- "audit and update all skills"
- "patch frontmatter hygiene across the library"
- "split the 5 biggest monoliths"
- "polish trigger keywords library-wide"
- "diagnose + update pass"

When the user asks only for **read-only audit** → use `skill-reviewer`. This skill assumes destructive action is approved.

## When NOT to Use

- Single-skill edits (use `skill_manage(action='patch')` directly)
- Read-only audits without update (use `skill-reviewer`)
- Creating brand-new skills from scratch (use `skill-creator`)
- Just listing skills or building an index (use `skill-navigator`)

## The 6-Phase Workflow

### Phase 0 — Gate (one clarify() call only)

Use `clarify()` with 2-4 options covering scope/risk/reversibility:

```
clarify(
  question="Wie tief soll der Update-Pass laufen?",
  choices=[
    "A: Hygiene-Only — nur Frontmatter vereinheitlichen, kein Content-Refactor",
    "B: Top-N Largest — die N größten Monolithen splitten + Hygiene",
    "C: Full Library Audit + Update — alle Skills reviewen, Duplikate mergen, archivieren",
    "D: Strikt nach skill-reviewer-Schema — 6-Block-Output vollständig durchziehen",
  ]
)
```

After the user picks an option, **STOP asking further sub-questions**. If the user replies mid-task with "Orchestriere" / "Mach" / "Go", switch to fully autonomous mode (see `clarify-options-pattern` Lessons Learned v2).

### Phase 1 — Diagnose (read-only, ~5 min)

Run `skill-reviewer` Mode 2 (Library-Wide Audit) over `~/.hermes/skills/`:

| Phase | What it finds |
|-------|---------------|
| 1 Trigger-Phrase Coverage | Skills with weak descriptions (`<120` chars, no "Use when") |
| 2 TF-IDF Cosine Overlap | Suspected duplicates (cross-domain >0.4, same-domain >0.4) |
| 3 Token Budget | Monoliths (>50KB), top-15 size leaders |
| 4 Yuno-Frontmatter Convention | Missing `lane`/`agent`/`trigger_keywords`/`keywords`/`related_skills`/`last_curated`/`curated_by` |
| 5 FP-Classification | Distinguish YAML-parse failures from real convention drift |

Output: 6-block report (INVENTORY, STRUCTURE, ORCHESTRATION, VERDICT).

### Phase 2 — Plan + Backup (mandatory, ~3 min)

**2a.** Decide which scripts to run:

| Pass | Script | When |
|------|--------|------|
| Frontmatter-Hygiene | `patch_frontmatter_v3.py` | Phase 4 reports <90% Yuno-frontmatter coverage |
| Trigger-Polish | `polish_triggers_v3.py` | Phase 1 reports >50% weak-trigger skills |
| Monolith-Split | `split_<skill>.py` (per skill) | Phase 3 reports any skill >50KB AND split is approved |

**2b.** Take tar.gz backup BEFORE running any script:

```bash
mkdir -p /tmp/skill-audit-$(date +%Y-%m-%d)
tar -czf /tmp/skill-audit-$(date +%Y-%m-%d)/skills-backup-pre-update.tar.gz \
  -C ~/.hermes skills
ls -lh /tmp/skill-audit-$(date +%Y-%m-%d)/skills-backup-pre-update.tar.gz
```

**Reversibility is 100% via `tar -xzf` from backup.** `~/.hermes/skills/` is NOT a git repo, so this is the only restore path.

**2c.** For each script, write **dry-run** mode first (validate on 5-20 random skills, compare before/after, revert). Only when dry-run is clean → full run.

### Phase 3 — Execute (destructive, ~30 min for 318 patches)

Run each script in sequence:

```bash
# 1. Frontmatter hygiene
python3 scripts/patch_frontmatter_v3.py
# Expected: "Patched: ~319 | Skipped: ~18 | Errors: 0"

# 2. Trigger polish
python3 scripts/polish_triggers_v3.py
# Expected: "Polished: ~117 | Skipped: ~220 | Errors: 0"

# 3. Monolith splits (per-skill)
python3 scripts/split_mirofish.py
python3 scripts/split_kanban.py
# Each writes N sub-skills + a routing-stub at the original path
```

Between scripts: re-validate YAML across the whole library:

```bash
python3 -c "
import yaml, glob
bad = []
for f in glob.glob('/home/bratan/.hermes/skills/**/SKILL.md', recursive=True):
    if '.archive' in f or '.curator_backups' in f: continue
    with open(f) as fh: c = fh.read()
    if not c.startswith('---'): continue
    parts = c.split('---', 2)
    if len(parts) < 3: continue
    try: yaml.safe_load(parts[1])
    except yaml.YAMLError as e: bad.append((f, str(e)))
print(f'OK: 0 bad' if not bad else f'INVALID: {len(bad)}')
for f, e in bad[:5]: print(f'  {f}: {e}')
"
```

If `INVALID > 0` → STOP, restore from backup, investigate.

### Phase 4 — Verify (mandatory, ~3 min)

| Check | Expected |
|-------|----------|
| YAML-Valid count | Same as before + (new sub-skills created) |
| File count delta | +N sub-skills for each monolith split |
| Total bytes | Slightly reduced (overhead eliminated) |
| Frontmatter coverage | 95%+ on `trigger_keywords`/`keywords`/`last_curated`/`curated_by`/`related_skills` |
| Monolith count | Reduced by N for each successful split |

### Phase 5 — Document

Write a single `AUDIT-REPORT.md` in `/tmp/skill-audit-<date>/` with:

- TL;DR table (before/after)
- Per-phase findings
- Scripts run + their results
- Pitfalls encountered (link to `self-improving` pitfall catalog)
- TODOs for separate sessions (next monoliths, manual `related_skills`, etc.)

Mirror key insights to Mnemosyne (memory + scratchpad).

---

## The 4 Production Scripts

All scripts are in `scripts/` and were verified on 337 active skills (2026-07-23) with 0 errors. **Run them in this order; never modify in-place without dry-run.**

> **Source code + decision logic recipe:** `references/scripts-recipe.md` — captures the exact patterns, anti-patterns, and verified results for all 4 scripts. Live copies are in `/tmp/skill-audit-2026-07-23/` (Basti's backup).

### `scripts/patch_frontmatter_v3.py` — Frontmatter-Hygiene

Auto-derives and patches missing Yuno-frontmatter keys:

- `trigger_keywords`: TF-Top from description
- `keywords`: thematic tags from description
- `last_curated: '2026-07-23'`
- `curated_by: 'Yuno'`
- `related_skills: []` (placeholder, manual later)

**Method:** raw-text injection at end of FM block. **NOT** yaml.safe_load + re-render (see Pitfall #45 below).

Reversibility: `tar -xzf skills-backup-pre-update.tar.gz -C ~/.hermes/`.

### `scripts/polish_triggers_v3.py` — Trigger-Keyword-Polish

Replaces generic tokens (`user`, `asks`, `task`, `hands`, `need`, `its`, `use`, `when`, `trigger`, `for`, `can`, `may`, `will`, `do`) in auto-curated `trigger_keywords` with distinktive domain tokens.

**Strict selectivity:** Only touches skills whose `curated_by` matches `auto-curated` regex or equals `Yuno`. Hand-curated skills (`Yuno (Biene 3 von 2026-07-17)` etc.) are preserved.

### `scripts/split_mirofish.py` + `scripts/split_kanban.py` — Monolith Split Templates

Both follow the same pattern (template, customize per skill):

1. `parse_sections()` — extract H2/H3/H4 sections
2. Route sections to buckets (e.g. mirofish-pipeline gets Step 1+2+4)
3. `render_skill()` — generate FM block + body per bucket
4. Write to `<bucket>/SKILL.md`
5. Overwrite original with **routing-stub** (FM + 1-page "which sub-skill for which intent" table)

**Each split creates 4 sub-skills + 1 routing-stub = 5 files total.** Max sub-skill size: ~50KB (pitfalls/collections), ideal 10-25KB.

---

## Pitfalls (the 6 most expensive bugs from this workflow)

### Pitfall #45 — yaml.safe_load + manual re-render of FM-Blocks destroys content (CRITICAL)

**Symptom:** After a script that does `yaml.safe_load(fm_raw)` then re-renders the dict back to YAML, nested dicts become string representations:
```yaml
# Before
metadata:
  hermes:
    tags: ['A', 'B', 'C']

# After
metadata: >
  {'hermes': {'tags': ['A', 'B', 'C']}}
```

Also: `description: >` (folded scalar) becomes plain string. `routing_hint: |` (literal scalar) loses indentation.

**Root Cause:** `yaml.safe_load` returns native Python objects that lose the YAML-presentation hints (`>`, `|`, indentation, list-of-dicts vs dict-of-lists). A custom re-renderer cannot reliably reproduce the original.

**Fix:** **Never** yaml.safe_load + re-render for FM blocks. Use **raw-text injection**:

```python
fm_raw, body = split_fm_and_body(content)  # regex split on first \n---\n pair
new_keys = ['trigger_keywords: [...]', 'keywords: [...]', ...]
new_fm = fm_raw.rstrip('\n') + '\n' + '\n'.join(new_keys)
new_content = '---\n' + new_fm + '\n---\n' + body
path.write_text(new_content)
```

**Guard:** Validate YAML AFTER every script run with `yaml.safe_load(parts[1])` over the entire library. If invalid count > 0 → restore from backup.

**Status:** verified (3 iteration: v1 broke nested dicts, v2 broke folded scalars, v3 raw-injection works for 319 files).

### Pitfall #46 — Monolith split MUST have tar.gz backup BEFORE running (CRITICAL)

**Symptom:** Split script deletes sections from the original file. If the script errors midway (e.g. user interrupts, YAML parse fails mid-write), the original is partially destroyed.

**Root Cause:** `write_file` is atomic at the OS level, but the script logic is not — interrupted runs leave orphaned sub-skills or empty stubs.

**Fix:** ALWAYS run `tar -czf .../skills-backup-pre-update.tar.gz -C ~/.hermes skills` BEFORE running a split script. If the script errors: `rsync -a --delete /tmp/restore-test/skills/ ~/.hermes/skills/` restores from backup.

**Guard:** Put backup command in a wrapper that exits 1 if backup didn't succeed:
```bash
tar -czf $BACKUP/skills-backup-pre-update.tar.gz -C ~/.hermes skills || exit 1
[ -s $BACKUP/skills-backup-pre-update.tar.gz ] || exit 1
```

**Status:** verified (Polish-bug at 2026-07-23 destroyed arxiv trigger_keywords; rsync restore in 5 sec, 0 loss).

### Pitfall #47 — Trigger-Polish must check `curated_by` content, not just presence (IMPORTANT)

**Symptom:** A naive "if `curated_by` contains 'Yuno'" filter matches hand-curated entries like `Yuno (Biene 3 von 2026-07-17)` or `Yuno (v2.5.0 — Dual-Path Cross-Validation Strategy)`. Polish script overwrites the hand-curated list, losing domain expertise.

**Root Cause:** The Yuno-frontmatter convention allows `curated_by: 'Yuno'` (auto) AND `curated_by: Yuno (free-text note)` (hand-curated). The presence of "Yuno" is not a reliable signal of auto-curation.

**Fix:** Strict matcher:
```python
def looks_auto(curated_by):
    if not curated_by: return False
    cb = str(curated_by).strip().strip("'\"").lower()
    if cb == 'yuno': return True
    if 'auto-curated' in cb: return True
    if 'audit 2026' in cb: return True
    return False
```

**Guard:** Always check `curated_by` content BEFORE touching `trigger_keywords` on existing lists. If `looks_auto()` returns False, skip.

**Status:** verified (mirofish v2.6 trigger_keywords had `'mirofish', 'simulation', 'multi-agent', 'distill', 'monitor', 'ontology', 'report'` — would have been overwritten by naive filter).

### Pitfall #48 — Self-reference in `related_skills` after monolith split (IMPORTANT)

**Symptom:** Original `mirofish` had `related_skills: ['mirofish', 'multi-agent-cluster-patterns', ...]`. After split, `mirofish-pipeline` lists `mirofish-pipeline` in its own `related_skills`. Confuses routing.

**Root Cause:** Split script doesn't update `related_skills` lists automatically — author must hand-edit them.

**Fix:** When splitting a monolith, OVERWRITE the original with a routing-stub whose `related_skills` lists ALL sub-skills. Each sub-skill's `related_skills` lists the OTHER sub-skills (peers), NOT itself.

**Guard:** After split, grep for self-references:
```bash
for d in <new-sub-skills>; do
  if grep -q "$d:" "$d/SKILL.md"; then echo "SELF-REF: $d"; fi
done
```

**Status:** verified (mirofish had `related_skills: ['mirofish', ...]` — fixed during split to point at sub-skills).

### Pitfall #49 — Section-routing per H2/H3 misses same-name collisions (MEDIUM)

**Symptom:** mirofish had two `## Step 3:` headings (one for Runbook Documentation, one for some Pitfall section). Split script routed both to pitfalls bucket, missing context.

**Root Cause:** Heuristic section-routing uses heading-prefix matching. When multiple sections start with the same prefix (`## Step 3:`), the script can't distinguish without full-content inspection.

**Fix:** Use **ordering + first-occurrence** heuristic:
- First occurrence of a section → routes to its primary bucket
- Subsequent same-prefix sections → context-dependent bucket (look at body content for keywords)

For mirofish: `## Step 3: Runbook Documentation` was the FIRST Step-3 heading → pitfalls (pitfalls collection); the implicit Step-3-pitfalls was just `### 1.` ... `### 35.` markers.

**Guard:** After split, run `grep -c "^## " <new-skill>/SKILL.md` and check counts match expected distribution. If any sub-skill has 0 sections, routing failed.

**Status:** verified (mirofish split delivered 16/11/43/24 sections to pipeline/analysis/pitfalls/runbook — all non-zero).

### Pitfall #50 — `>2 ---` lines in SKILL.md body looks like broken YAML but isn't (LOW)

**Symptom:** A skill body that uses `---` as a section divider (e.g. `## Section\n---\nContent`) shows up as 5+ `---` lines. A naive FM-validator reports "broken YAML".

**Root Cause:** Markdown uses `---` (horizontal rule) inside bodies. The validator checks only the FIRST `---` pair, but reports based on all `---` counts.

**Fix:** FM validator MUST use `split('---', 2)` with content that starts with `---\n` and look for the SECOND `---\n` followed by body. Body `---` markers are legitimate markdown.

**Guard:** When measuring "is FM valid", count `---` lines BETWEEN the first and second `---` (excluding the delimiters). Anything else is body content.

**Status:** verified (124 skills have >2 `---` lines in raw text; all have valid FM — the extra `---` are body section dividers).

---

## The "Orchestriere" Pattern (mid-task steering)

When Basti says "Orchestriere", "Mach", "Go", "Full send", "kein Micromanagement" mid-task:

1. STOP all further `clarify()` calls for sub-decisions.
2. Run remaining scripts autonomously.
3. Validate between scripts (YAML check, file count delta).
4. Document every decision in the final report.
5. If something fails: rsync restore from tar.gz and report.

See `clarify-options-pattern` "Lessons Learned v2" for full pattern.

---

## Verification Checklist (post-pass)

- [ ] tar.gz backup exists, size matches pre-pass disk size
- [ ] YAML-valid count >= pre-pass count + (new sub-skills created)
- [ ] File count delta == expected (e.g. +4 sub-skills per monolith split)
- [ ] Frontmatter coverage >= 95% on the 5 added keys
- [ ] Monolith count decreased by N for each successful split
- [ ] `AUDIT-REPORT.md` written to `/tmp/skill-audit-<date>/`
- [ ] Mnemosyne scratchpad updated with final state
- [ ] Mnemosyne `remember` for top-3 lessons (one per pitfall if applicable)
- [ ] Related skills (e.g. `self-improving`) PATCHED with new pitfalls (if curator allows)
- [ ] TODOs for next session documented (remaining monoliths, manual `related_skills`)

---

## Related Skills

- `skill-reviewer` — the read-only predecessor; run Mode 2 first
- `skill-library-maintenance` — slim-down (extract into references/); complementary
- `skill-creator` — for creating brand-new skills
- `skill-polisher` — batch quality improvements (different from mass-update)
- `self-improving` — owns the pitfall catalog (Pitfall #45-50 live here)
- `clarify-options-pattern` — owns the "Orchestriere" mid-task steering pattern

## Reference Files

- `references/scripts-recipe.md` — patterns for the original 4 scripts (patch, polish, mirofish-split, kanban-split)
- `references/monolith-split-playbook.md` — generic v2 splitter (`split_remaining_v2.py`), FM-parsing bug (#51), state-machine section routing, 4 production splits via config