---
name: skill-reviewer
description: |
  Structured quality + portability review of SKILL.md files and skill inventories.
  Triggers on "review SKILL.md", "audit skill", "skill library audit",
  "skill inventory", "sub-skill proposal", "bundle proposal", "skill export
  readiness", "skill coupling check", "duplicate skill", "weak triggers".
  Four modes: Single-Skill (structure + triggers), Library-Wide (5 phases incl.
  Phase 5 FP-Classification, 86% FP-Reduktion bewiesen), Inventory + Bundle-Proposal
  (Open-Format-style parent->child grouping), Export-Readiness (Agent Skills Open-Format
  portability). Emits canonical 6-block report: INVENTORY, STRUCTURE, BUNDLES,
  PORTABILITY, ORCHESTRATION, VERDICT. Read-only: never edits, moves, installs.
version: 2.0.0
author: Toqsick + Yuno (Hub->Hermes + skill-review v1.0.0 merge)
license: MIT
lane: koenigin
agent: Yuno
trigger_keywords:
  - review skill
  - audit skill
  - skill inventory
  - skill library audit
  - bundle proposal
  - sub-skill proposal
  - skill coupling check
  - duplicate skill
  - weak triggers
  - skill export readiness
  - open-format check
  - skill portability
  - trigger coverage
keywords:
  - meta
  - review
  - audit
  - quality
  - inventory
  - bundle
  - portability
  - open-format
  - trigger-coverage
  - tfidf
  - token-economy
related_skills:
  - skill-creator
  - skill-polisher
  - skill-duplicate-audit
  - skill-library-maintenance
  - skill-install-workflow
last_curated: 2026-07-21
curated_by: Yuno
routing_hint: >
  Use when Basti asks for a SKILL.md audit, skill library review, sub-skill
  bundling proposal, or export-readiness check (Agent Skills Open-Format
  portability). One canonical 6-block report per invocation, read-only.
changelog:
  - '2.0.0 (2026-07-21): Major merge. skill-review v1.0.0 (Agent Skills Open-Format,
    bundle-proposal, export-readiness, 6-block report) integrated as Mode 3+4.
    Yuno-Frontmatter canonized (13 keys). Single source of truth restored.'
  - '1.0.1 (2026-07-15): Phase 5 FP-Classification, 86% FP-Reduktion bewiesen'
  - '1.0.0 (2026-07-07): Library-Wide Audit Mode (TF-IDF, tokens, lane)'
---


# skill-reviewer (v2.0.0)

Read-only quality + portability review for SKILL.md files and skill inventories.
Four modes, one canonical 6-block report. Never edits, moves, or installs.

## Modes (which one to pick)

| Mode | Input | Use when |
|------|-------|----------|
| 1 Single-Skill | One `SKILL.md` path | "review this skill", "audit foo" |
| 2 Library-Wide | Skills root, default `~/.hermes/skills/` | "audit my library", "trigger coverage scan", "frontmatter drift" |
| 3 Inventory + Bundle-Proposal | Skills root | "group by domain", "sub-skill proposal", "bundle these" |
| 4 Export-Readiness | Skill root OR one `SKILL.md` | "is this portable", "open-format check", "export readiness" |

Caller picks one. Default: 1 for a single path, 2 for a directory.

## Canonical Output Schema (6 blocks)

Always emit in this order. Empty block uses `n/a`. Only `BUNDLES` may use `none`.

### INVENTORY

Table of every discovered `SKILL.md`:

| Name | Description (one line) | Scope | Categories | Tags |
|------|------------------------|-------|------------|------|

Scope values: `project`, `user`, `extra`, `built-in`, `unknown`.

### STRUCTURE

Frontmatter + body check (per skill):

| Field | Expected | Actual | Status |
|-------|----------|--------|--------|
| name | kebab-case, matches dir | `<value>` | OK/WARN/FAIL |
| description | trigger + NOT for | `<value>` | OK/WARN/FAIL |
| whenToUse | optional, recommended | `<value>` | OK/WARN/FAIL |
| type | flow (default) | `<value>` | OK/WARN/FAIL |
| version | semver >= 1.0.0 | `<value>` | OK/WARN/FAIL |
| categories | 1-5, snake_case | `<value>` | OK/WARN/FAIL |
| tags | 1-10, snake_case | `<value>` | OK/WARN/FAIL |
| body sections | per declared type | `<value>` | OK/WARN/FAIL |
| secret leakage | none | `<value>` | OK/WARN/FAIL |

### BUNDLES

Parent->child proposals from Mode 3. For each candidate parent emit:

- Parent name (kebab-case, unique)
- Parent description draft (one line, with NOT for clause)
- Children list (existing leaf names preserved)
- `has-sub-skill`: `true` when already declared, otherwise `proposed`
- Travel-with directories per child (references/, examples/, assets/, scripts/, templates/)

`none` when no bundles proposed.

### PORTABILITY

Per-skill export readiness:

- Absolute home paths leaked: `none` | list
- Secrets referenced in body: `none` | list (paths only, never contents)
- Workstation-specific dependencies: `none` | list
- Cross-tool frontmatter fields: list (portable / optional-extension)
- Self-contained: `yes` | `no`

### ORCHESTRATION

Max 5 bullets. Each is one concrete actionable change, ordered by impact.

### VERDICT

Exactly one of:
- `COMPLIANT`: no action required.
- `NEEDS_REVISION`: concrete fixes listed in ORCHESTRATION.
- `REJECTED`: fundamental problem (missing required frontmatter, unparseable YAML,
  hard-coded secrets, hard-coded home path, body depends on workstation).

## Mode 1: Single-Skill Review

1. Parse YAML frontmatter. Parse fail: `REJECTED` with reason in STRUCTURE.
2. Validate required: `name`, `description`, `version`. Missing: `REJECTED`.
3. `name` must be kebab-case and match parent directory basename.
4. `description` must contain a trigger pattern AND an explicit NOT for clause.
5. `version` must be semver `>= 1.0.0` for production use.
6. Body must have canonical sections expected for declared `type` (default `flow`).
7. Emit `STRUCTURE | ORCHESTRATION | VERDICT` (n/a for INVENTORY/BUNDLES/PORTABILITY).

Single-Skill template:

```
## Skill Review: [name]

### Summary
[assessment, line count, file count]

### STRUCTURE
[per-field table]

### ORCHESTRATION
[max 5 bullets]

### VERDICT
[COMPLIANT | NEEDS_REVISION | REJECTED]
```

## Mode 2: Library-Wide Audit (5 Phasen)

For reviewing the ENTIRE skill library, not individual skills. Triggers on
"skill library audit", "check all descriptions", "find weak triggers".

### Phase 1: Trigger-Phrase Coverage

Scan ALL active descriptions for trigger-first quality:

```bash
cd ~/.hermes/skills
find . -name SKILL.md -not -path '*/.archive/*' -not -path '*/.curator_backups/*' |
while read f; do
  name=$(grep -m1 '^name:' "$f" | sed 's/^name: *//')
  desc=$(grep -A8 '^description:' "$f" | head -9)
  has_trigger=$(echo "$desc" | grep -ciE '(trigger|use when|invoke when|triggers on)')
  length=$(echo "$desc" | wc -c)
  [ $length -lt 120 ] && echo "SHORT ($length): $name"
  [ $has_trigger -eq 0 ] && echo "NO_TRIGGER: $name"
done | tee /tmp/weak_triggers.txt
```

Interpretation: `<60%` urgent, `60-80%` moderate, `>80%` good shape.

### Phase 2: TF-IDF Overlap Detection

Find skills with suspiciously similar descriptions (potential duplicates):

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import glob, yaml

skills = []
for f in glob.glob('**/SKILL.md', recursive=True):
    if any(x in f for x in ['/.archive/', '/.curator_backups/', '/.hub/']):
        continue
    parts = open(f).read().split('---', 2)
    if len(parts) < 2: continue
    fm = yaml.safe_load(parts[1])
    skills.append({'path': f, 'name': fm.get('name', ''),
                   'desc': fm.get('description', '')})

vec = TfidfVectorizer(stop_words='english', max_features=100)
matrix = vec.fit_transform([s['desc'] for s in skills])
sim = cosine_similarity(matrix)
for i in range(len(skills)):
    for j in range(i+1, len(skills)):
        if sim[i][j] > 0.75:
            print(f"OVERLAP ({sim[i][j]:.2f}): {skills[i]['name']} <-> {skills[j]['name']}")
```

Interpretation: `>0.85` consolidation candidate, `0.75-0.85` investigate.

### Phase 3: Token Budget Estimation

```bash
cd ~/.hermes/skills
find . -name SKILL.md -not -path '*/.archive/*' -not -path '*/.curator_backups/*' \
  -exec wc -c {} \; | awk '{t+=$1} END{print "Total bytes:", t, "approx", int(t/4), "tokens"}'
find . -name SKILL.md -not -path '*/.archive/*' -not -path '*/.curator_backups/*' \
  -exec wc -c {} \; | sort -rn | head -10
```

Interpretation: top-10 over 25 KB each = urgent slim-down; over 50 KB = monolith.

### Phase 4: Frontmatter Convention (Yuno-spezifisch)

Verify Yuno 13-Key frontmatter (lane / agent / trigger_keywords / keywords /
related_skills / last_curated / curated_by / routing_hint):

```bash
cd ~/.hermes/skills
for key in lane agent trigger_keywords keywords related_skills \
           last_curated curated_by routing_hint; do
  echo "=== $key ==="
  find . -name SKILL.md -not -path '*/.archive/*' -not -path '*/.curator_backups/*' \
    -exec sh -c "grep -q '^$key:' \"\$1\" || echo \$1" _ {} \;
done
```

Yuno convention: `lane: koenigin` for orchestrator/decision, `lane: worker` for
mechanical/executor, `reasoning_effort: xhigh` for complex reasoning, `low` for
lookup.

### Phase 5: Frontmatter False-Positive Classification (NEW 2026-07-15)

Problem: naive audit reports hundreds of false positives (missing period, missing
author) caused by YAML formatting artifacts. Multi-pass classifier reduces FP.

```python
import yaml, glob, re
from pathlib import Path

skills_dir = Path.home() / '.hermes/skills'
raw_issues = []
for pattern in ['*/*/SKILL.md', '*/*/*/SKILL.md']:
    for f in glob.glob(str(skills_dir / pattern)):
        is_archive = '.archive/' in f
        parts = open(f).read().split('---', 2)
        if len(parts) < 2: continue
        fm = yaml.safe_load(parts[1])
        if not isinstance(fm, dict): continue
        issues = []
        desc = fm.get('description', '')
        if isinstance(desc, str) and desc.strip() and not desc.strip().endswith('.'):
            issues.append('missing_period')
        if not fm.get('author'): issues.append('missing_author')
        if not fm.get('version'): issues.append('missing_version')
        raw_issues.append({'file': f, 'issues': issues, 'archive': is_archive})

def is_fp_period(raw_fm: str) -> bool:
    if 'description: |' in raw_fm or 'description: >' in raw_fm: return True
    if re.search(r"""description\s*:\s*['"][^'"]*\.['"]""", raw_fm): return True
    return False

real_issues = []
for item in raw_issues:
    if item['archive']: continue
    raw_fm = open(item['file']).read().split('---', 2)[1]
    real = [iss for iss in item['issues']
            if not (iss == 'missing_period' and is_fp_period(raw_fm))]
    if real:
        real_issues.append({'file': item['file'], 'issues': real})

print(f"Raw: {len(raw_issues)} | After FP: {len(real_issues)}")
print(f"FP rate: {(1 - len(real_issues)/max(len(raw_issues),1))*100:.0f}%")
```

Proven on 482 skills (2026-07-15): raw 263 -> after FP 87 -> after archive 37.
Final real FP-Rate: 14%. **86% of raw issues were false positives.**

Emit Library-Wide report as `INVENTORY | STRUCTURE | ORCHESTRATION | VERDICT`
(BUNDLES and PORTABILITY use `n/a`).

## Mode 3: Inventory + Bundle-Proposal

For cross-skill grouping and parent->child bundling. Triggers on "bundle these",
"sub-skill proposal", "group by domain", "share triggers".

1. Walk root for every `<name>/SKILL.md`. Record name, description, scope guess,
   category, tags.
2. Group skills by domain (infer from categories, tags, first sentence of description).
3. Detect coupling: skills whose description or whenToUse overlap by >= 2 trigger
   phrases, or which reference the same sibling file, are flagged as coupled.
4. Flag granularity:
   - too fine-grained: single trivial example, no whenToUse, body < 30 lines
   - too broad: description covers > 3 distinct domains
5. Propose shallow parent -> child bundles. For each candidate parent emit:
   - parent name (kebab-case, unique)
   - parent description draft (one line, with NOT for clause)
   - children list (existing leaf names preserved)
   - has-sub-skill: true | proposed
   - travel-with directories per child (references/, examples/, assets/, scripts/, templates/)
6. Preserve backward discoverability: existing leaf names must remain reachable.
   Nesting normally at most parent -> child; deeper chains flag + require user opt-in.

Emit full 6-block report. BUNDLES is the headline output of Mode 3.

## Mode 4: Export-Readiness Review

For cross-tool portability of one skill or a whole tree. Triggers on "is this
portable", "open-format check", "export readiness".

1. Hard reject: hard-coded absolute home path, user name, hostname, or
   workstation-specific binary.
2. Hard reject: skill requires reading secrets to function (skill itself fine,
   copying secrets into the export is NOT fine).
3. Self-contained check: body may reference generic concepts (SKILL.md,
   references/, assets/, scripts/, templates/), but MUST NOT require files outside
   the skill root.
4. Cross-tool compatibility:
   - portable baseline: name, description, version
   - optional common: categories, tags
   - vendor-only (whenToUse, type, other): tolerated as optional extensions,
     MUST NOT be required by a cross-tool review, MUST be marked as extensions
5. Per-skill portability score (0-100) and list of blockers.

Emit `INVENTORY | PORTABILITY | ORCHESTRATION | VERDICT` (STRUCTURE and BUNDLES
use `n/a`).

## Workflow (read-only contract)

1. Decide which mode applies. If caller is ambiguous: default 1 for single path,
   2 for directory.
2. Walk or read targets. Never write back.
3. Parse frontmatter. Never execute skill bodies.
4. Classify each skill: domain, scope, coupling, granularity.
5. Compose the 6 output blocks in canonical order.
6. Emit VERDICT last. Stop. Do not perform proposed actions.

## Hard Constraints

- MUST NOT modify, move, install, rename, or delete any skill file.
- MUST NOT print, copy, or echo secret material; if a secret is suspected,
  report the path and stop.
- Exported skill (this file) MUST NOT contain absolute home paths, user names,
  hostnames, or workstation-specific binaries.
- Required frontmatter (`name`, `description`, `version`) MUST be present and
  valid in every audited skill, otherwise VERDICT is `REJECTED`.
- Six output blocks MUST appear in every report, in stated order. Empty blocks
  use `n/a`; only `BUNDLES` may use `none`.

## Soft Constraints

- Prefer shallow parent -> child grouping; deeper chains require explicit request.
- Keep ORCHESTRATION to max 5 bullets.
- Keep body self-contained, target < 500 lines (this is 415).

## Trigger-Test Reference

Should trigger (3):
- "review this SKILL.md"
- "audit my skill library"
- "is this skill portable to another tool"

Should NOT trigger (3):
- "write a new SKILL.md" (use skill-creator)
- "polish this skill for size" (use skill-polisher)
- "merge two skills into one" (orchestration, not read-only review)

## Quick Reference

| Q | A |
|---|---|
| Can this skill edit files? | No, read-only. |
| How many output blocks? | Six, fixed order. |
| Max bundle depth? | Parent -> child. Deeper only on request. |
| Where do secrets go? | PORTABILITY block as paths only, never contents. |
