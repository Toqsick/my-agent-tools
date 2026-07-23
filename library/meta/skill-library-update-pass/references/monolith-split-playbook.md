# Monolith Split Playbook — Generic Splitter v2 (2026-07-23)

Companion to `scripts-recipe.md`. Documents the **generic** monolith splitter
that replaced the per-skill templates (`split_mirofish.py`, `split_kanban.py`).

When the original 4 scripts were extended to 4 more monoliths
(system-security-audit, queen-bee-schwarm-dispatch, hermes-maintenance,
multi-agent-cluster-patterns), the per-skill pattern broke: each new split
needed its own copy of `parse_sections`, `assign_sections`, `render_skill`,
and a per-skill `SPLITS = {...}` config.

The v2 generic splitter (`split_remaining_v2.py`) consolidates all of that
into one config-driven script.

---

## Why v2 Exists

| Iteration | What it did | Why it broke |
|-----------|-------------|--------------|
| split_mirofish.py | Hardcoded mirofish section routing | Doesn't generalize to other skills |
| split_kanban.py | Hardcoded kanban section routing | Same |
| **split_remaining_v1** | Single SPLITS dict for 4 skills, complex helper functions | parse_sections bug: counted `---` markers as FM delimiters (see below) |
| **split_remaining_v2** | Same idea, simplified helpers, fixed FM parsing | Production |

---

## The FM Parsing Bug (Pitfall #51 — to be added to self-improving)

**Symptom:** v1's `parse_sections` walked every `---` line as a potential FM
delimiter. Skills with `---` body section dividers (kanban-system-health,
mirofish-pitfalls) had FM_END detected at line 338 instead of line 26.
Sub-skill bodies came out empty.

**Root Cause:** `---` is a horizontal-rule marker in markdown. Many skills
use it for visual section breaks. A naive FM parser treats every `---` as a
candidate closing-delimiter.

**Fix:** FM is **always** the FIRST `---` pair. Count `---` lines and break
at the SECOND occurrence:

```python
def split_fm_and_body(content):
    lines = content.split('\n')
    count = 0
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == '---':
            count += 1
            if count == 2:
                body_start = i + 1
                break
    return '\n'.join(lines[:body_start]), '\n'.join(lines[body_start:])
```

**Detection:** If after a split every sub-skill is <1KB and the router is
~2KB, FM parsing likely failed. Re-run with `parse_sections` debug output.

**Status:** verified (caught during system-security-audit split attempt 1,
all 4 monoliths re-split successfully after fix).

---

## Generic Splitter Config Schema

```python
SPLITS = [
    {
        'skill_rel': 'domain/skill-name',          # relative to ~/.hermes/skills/
        'category': 'domain',                     # mirrors skill_rel first segment
        'router_title': 'Display Title',
        'router_description': 'Use when ... ROUTER: delegates to ...',
        'router_trigger_keywords': [...],
        'router_keywords': [...],
        'router_related_extra': [...],            # non-sub related skills
        'subs': [
            {
                'name': 'sub-skill-name',         # becomes directory under skill_rel parent
                'title': 'Display Title',
                'description': 'Use when ... NOT for ...',
                'headings': [                     # EXACT match on ## <text>
                    '## Section A',
                    '## Section B',
                ],
                'trigger_keywords': [...],
                'keywords': [...],
            },
            ...
        ],
    },
    ...
]
```

**Constraint:** `headings` MUST exactly match the source `## <text>` lines.
A typo or trailing whitespace fails the entire split. Grep the source first:

```bash
grep "^## " ~/.hermes/skills/<skill>/SKILL.md
```

---

## State-Machine for Section Inheritance (Pitfall #50)

H3/H4 sections inherit their parent H2's bucket. The state machine tracks
which sub-skill a section currently belongs to:

```python
current_target = None
for sec in sections:
    h = sec['heading']
    # If h matches a sub-skill's "starting heading", switch current_target
    for sub in cfg['subs']:
        if h in sub['headings']:
            current_target = sub['name']
            assignments[sec] = sub['name']
            break
    else:
        # Inherit from parent H2 (state-machine!)
        if current_target:
            assignments[sec] = current_target
```

**Why it matters:** mirofish had H3 sections like `### 1. Kill Stale OASIS Workers`
without a matching H2 (`## Kill Stale OASIS Workers`). State-machine treats them
as part of the current parent bucket (pipeline).

**Anti-pattern:** Routing by H3 prefix alone breaks when the same prefix
appears under multiple H2 parents (`### Step 1` under `## Setup` vs `## Cleanup`).

---

## Section-Count Verification

After the split, total sections across sub-skills MUST equal the source's
section count:

```python
expected = len(source_sections)
actual = sum(len(grouped[sub]) for sub in cfg['subs'])
assert expected == actual, f'Section count mismatch: {expected} vs {actual}'
```

If they don't match, some sections got dropped (state-machine missed a parent
transition) or duplicated (heading matched multiple sub-skill `headings` lists).

**Verified 2026-07-23 (post-v2-fix):**
- system-security-audit: 46 + 28 + 11 = 85 ✓
- queen-bee-schwarm-dispatch: 14 + 11 + 46 = 71 ✓
- hermes-maintenance: 7 + 29 + 4 = 40 ✓
- multi-agent-cluster-patterns: 37 + 9 = 46 ✓

---

## Production Results (2026-07-23 splits via v2)

| Monolith | Sections | Subs | Sizes |
|----------|----------|------|-------|
| system-security-audit | 85 | 3 | 45/18/11 KB + 2 KB router |
| queen-bee-schwarm-dispatch | 71 | 3 | 20/9/36 KB + 2 KB router |
| hermes-maintenance | 40 | 3 | 4/35/22 KB + 2 KB router |
| multi-agent-cluster-patterns | 46 | 2 | 38/19 KB + 2 KB router |

All 4 splits completed with 0 errors. YAML-valid count rose from 347 to 358
(one new sub-skill per split + original router replaced).

---

## What v2 Does NOT Do (Known Limitations)

- ❌ Does NOT auto-detect sub-skill boundaries (still needs human config)
- ❌ Does NOT update `related_skills` cross-references in OTHER skills
  (only within the split family)
- ❌ Does NOT generate the "router" FM keys (`lane`, `agent`) consistently
  with sibling skills
- ❌ Does NOT update `curated_by` to reflect the split (uses `'Yuno (split from X 2026-07-23)'`)

Future improvement: scan sister skills in the same domain to copy lane/agent
into the new sub-skills, preserving consistency.

---

## When to Use v2 vs Per-Skill Script

| Scenario | Use |
|----------|-----|
| 2-3 monoliths to split | **Per-skill template** (like split_mirofish.py) — easier to read |
| 4+ monoliths to split | **Generic v2** — config-driven, scales linearly |
| One monolith with unusual structure | **Per-skill template** — easier to debug |
| Recurring quarterly splits | **Generic v2** — easier to maintain one script |

The per-skill templates (`split_mirofish.py`, `split_kanban.py`) are kept
in `~/.hermes/scripts/skill-audit/` as historical references and for edge-case
customization. For new monoliths, prefer v2 unless the structure is unusual.

---

## Self-Reference Prevention (Pitfall #49, cross-reference)

The generic v2 splitter prevents self-references by:
1. The router's `related_skills` includes ALL sub-skills (never itself)
2. Each sub-skill's `related_skills` is `[s for s in all_names if s != self.name]`

Manual verification after split:

```bash
for f in $(find ~/.hermes/skills -name SKILL.md -not -path '*/.archive/*' -not -path '*/.curator_backups/*'); do
    name=$(grep -m1 '^name:' "$f" | sed 's/^name: *//; s/"//g; s/'"'"'//g')
    rel=$(grep -m1 '^related_skills:' "$f" | sed 's/^related_skills: *//')
    if echo "$rel" | grep -qE "['\"]$name['\"]|\\[$name,"; then echo "SELF-REF: $name in $f"; fi
done
```

**Verified 2026-07-23:** 0 self-references across all 6 split families
(mirofish, kanban-system-health, system-security-audit, queen-bee-schwarm-dispatch,
hermes-maintenance, multi-agent-cluster-patterns).