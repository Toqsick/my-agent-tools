# Production Scripts — Source Code Recipe (2026-07-23)

The 4 production scripts used during the Basti-orchestrierte Full Library Audit
on 2026-07-23. Each script was verified with 0 errors on 337 active skills.

**Where the live scripts live:** `/tmp/skill-audit-2026-07-23/` (Basti's local backup).
**This file:** Recipe-only — patterns and decision logic, not full source. To
recover the live scripts, copy from the tar.gz backup or re-author from this
recipe + the SKILL.md workflow.

---

## Script 1: `patch_frontmatter_v3.py`

**Purpose:** Auto-derive and patch missing Yuno-frontmatter keys on every active SKILL.md.

### Decision logic

```python
def split_fm_and_body(content):
    # MUST use regex to find FIRST \n---\n pair, not split('---', 2)
    m = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not m: return None
    return m.group(1), m.group(2)

def get_existing_keys(fm_raw):
    # Line-state machine: parse top-level keys only, ignore nested dicts/lists
    keys = set()
    for line in fm_raw.split('\n'):
        if line and not line[0].isspace():
            m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:', line)
            if m: keys.add(m.group(1))
    return keys

def extract_words(desc, n=5):
    # TF-based word extraction from description
    if isinstance(desc, list): desc = ' '.join(desc)
    words = re.findall(r'[a-z]{4,}', desc.lower())
    STOP = {'the','a','an','use','when','to','for','of','in','and','or',...}
    c = Counter(w for w in words if w not in STOP and not w.isdigit())
    return [w for w, _ in c.most_common(n)]
```

### What it adds (only if missing)

| Key | Value |
|-----|-------|
| `trigger_keywords` | `[w1, w2, w3, w4, w5]` from description TF |
| `keywords` | Same as trigger_keywords (broader) |
| `last_curated` | `'2026-07-23'` |
| `curated_by` | `'Yuno'` |
| `related_skills` | `[]` (placeholder) |

### Critical anti-pattern: what NOT to do

```python
# ❌ WRONG: yaml.safe_load + re-render
fm = yaml.safe_load(parts[1])
fm['trigger_keywords'] = new_words
new_content = '---\n' + yaml.safe_dump(fm) + '---\n' + body
# Result: nested dicts become strings, folded scalars break, descriptions
# lose their `>` literal-scalar indicator. CONFIRMED 3x iteration history.

# ✅ RIGHT: raw-text injection
new_keys = ['trigger_keywords: [...]', ...]
new_fm = fm_raw.rstrip('\n') + '\n' + '\n'.join(new_keys)
new_content = '---\n' + new_fm + '---\n' + body
```

### Verified result (2026-07-23)

```
Candidates: 337
Patched: 319
Skipped: 18 (already complete)
Errors: 0
```

---

## Script 2: `polish_triggers_v3.py`

**Purpose:** Replace generic tokens in `trigger_keywords` with distinktive domain tokens. STRICT selectivity: only auto-curated skills.

### Decision logic

```python
GENERIC_TOKENS = set("user asks task hands need its use when trigger for can may will do".split())

def looks_auto(curated_by):
    """Strict auto-curation check — NOT substring 'yuno'."""
    if not curated_by: return False
    cb = str(curated_by).strip().strip("'\"").lower()
    if cb == 'yuno': return True
    if 'auto-curated' in cb: return True
    if 'audit 2026' in cb: return True
    return False

def needs_polish(trigger_list):
    """Only polish if >=2 generic tokens in current list."""
    flat = set(str(t).lower() for t in trigger_list)
    return len(flat & GENERIC_TOKENS) >= 2

def clean_trigger_words(text, name, max_n=5):
    """Re-derive TF-based, name-boosted (2x weight)."""
    text = (text + ' ' + (name + ' ') * 2).lower()
    words = re.findall(r'[a-z][a-z0-9-]{2,}', text)
    c = Counter(w for w in words if w not in GENERIC_TOKENS and len(w) >= 3)
    return [w for w, _ in c.most_common(max_n)]
```

### Anti-pattern (CRITICAL)

```python
# ❌ WRONG: naive substring match
if 'yuno' in curated_by.lower():  # matches 'yuno (biene 3 von...)'
    polish()  # destroys hand-curated work

# ✅ RIGHT: strict content check (looks_auto above)
if not looks_auto(curated_by): skip
```

### Verified result (2026-07-23)

```
Polished: 117
Skipped: 220 (hand-curated or already good)
Errors: 0
```

### Example transformation

```
arxiv (before): ['user', 'asks', 'search', 'papers']
arxiv (after):  ['arxiv', 'search', 'papers', 'keyword', 'author']
```

---

## Script 3: `split_mirofish.py`

**Purpose:** Split a >50KB monolith into a routing-stub + 4 sub-skills.

### Section parsing

```python
def parse_sections(text):
    """Return list of {level: 2|3|4, heading: str, body: [lines]}."""
    lines = text.split('\n')
    sections = []
    current = None
    for line in lines:
        if line.startswith('# ') and not line.startswith('## '):
            current = None  # H1 = title, skip
        elif line.startswith('## '):
            current = {'level': 2, 'heading': line[3:].strip(), 'body': []}
            sections.append(current)
        elif line.startswith('### '):
            current = {'level': 3, 'heading': line[4:].strip(), 'body': []}
            sections.append(current)
        # ... same for ####
        else:
            if current is not None: current['body'].append(line)
    return sections
```

### Section routing (mirofish-specific)

| Section heading | Bucket |
|-----------------|--------|
| `Trigger`, `Pipeline Overview`, `Pre-Run Checklist` | pipeline |
| `Step 1*`, `Step 2*`, `Step 4*` | pipeline |
| `Step 3a*`, `Step 3b*`, `Step 3c*` | analysis |
| `Step 3: Runbook Documentation`, `Skills-Version History`, `### 1.` to `### 35.` | pitfalls |
| `Step 5*`, `Übersicht*`, `Personas*`, `Konfiguration*` | runbook |
| Unknown H2 | pitfalls (default) |

### Sub-skill rendering

```python
def render_skill(name, title, description, sections,
                 trigger_keywords, keywords, related_skills):
    fm = f"""---
name: {name}
title: "{title}"
description: "{description}"
version: '2.7'
created: '2026-07-23'
author: Yuno (split from mirofish v2.6)
lane: software-development
agent: universal
trigger_keywords: {trigger_keywords}
keywords: {keywords}
related_skills: {related_skills}
last_curated: '2026-07-23'
curated_by: 'Yuno (split from mirofish 2026-07-23)'

license: MIT
---

# {title}
"""
    body_parts = [f"\n{title}\n\n"]
    for sec in sections:
        prefix = '#' * sec['level']
        body_parts.append(f"\n{prefix} {sec['heading']}\n\n")
        body_parts.append('\n'.join(sec['body']))
    return fm + ''.join(body_parts)
```

### Routing-stub (overwrites original)

The original file is REPLACED with a thin "router" that maps user-intent to sub-skill:

```markdown
## When to use which sub-skill

| User intent | Sub-skill |
|-------------|-----------|
| Set up pipeline, seed, monitor | mirofish-pipeline |
| Analyze, compare runs, agent chat | mirofish-analysis |
| Recovery from known pitfall | mirofish-pitfalls |
| Write runbook, Max-Kampagne deck | mirofish-runbook |
```

### Verified result (2026-07-23)

```
Pipeline: 16 sections, ~8.4KB → 10.1KB with FM
Analysis: 11 sections, ~6.6KB → 8.2KB with FM
Pitfalls: 43 sections, ~41.5KB → 44.9KB with FM
Runbook: 24 sections, ~13.9KB → 16.6KB with FM
Original (replaced): 101KB → 3KB routing-stub
```

---

## Script 4: `split_kanban.py`

**Purpose:** Same pattern as split_mirofish, customized for kanban-system-health structure.

### Section routing (kanban-specific)

| Section heading | Bucket |
|-----------------|--------|
| `Quick-Start`, `1. Live-State*`, `2. Diagnose-Baum`, `11. Status-Report*` | diagnostics |
| `3. Phase 0*` through `9. 2-Wellen*` | phases |
| `10. Pitfalls*`, `15. Hermes-v2*` | pitfalls |
| `12. Cross-Board*`, `14. Source-Code*`, `13. Verwandte*`, `Changelog` | audit |
| Unknown sub-section | stays in current_group |

### Verified result (2026-07-23)

```
Diagnostics: 14 sections, ~5.8KB → 7.9KB with FM
Phases: 30 sections, ~7.9KB → 10.8KB with FM
Pitfalls: 17 sections, ~30.7KB → 33.1KB with FM
Audit: 18 sections, ~18.3KB → 20.7KB with FM
Original (replaced): 86KB → 3KB routing-stub
```

---

## Universal guard: YAML validation

After EACH script run, validate the whole library:

```python
import yaml, glob

bad = []
for f in glob.glob('/home/bratan/.hermes/skills/**/SKILL.md', recursive=True):
    if '.archive' in f or '.curator_backups' in f: continue
    with open(f) as fh: c = fh.read()
    if not c.startswith('---'): continue
    parts = c.split('---', 2)
    if len(parts) < 3: continue
    try:
        yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        bad.append((f, str(e)))

if bad:
    print(f'INVALID: {len(bad)}')
    for f, e in bad[:5]: print(f'  {f}: {e}')
    # → rsync restore from tar.gz backup
```

**Verified 2026-07-23:** 0 invalid across 346 active skills (337 before + 8 sub-skills + 1 missing count).

---

## Reversibility (mandatory before any destructive script)

```bash
# 1. Backup
tar -czf /tmp/skill-audit-$(date +%Y-%m-%d)/skills-backup-pre-update.tar.gz \
  -C ~/.hermes skills

# 2. Run script
python3 scripts/patch_frontmatter_v3.py

# 3. Validate
python3 -c "..."  # YAML check above

# 4. If anything broke: rsync restore
mkdir -p /tmp/restore-test
tar -xzf /tmp/skill-audit-2026-07-23/skills-backup-pre-update.tar.gz \
  -C /tmp/restore-test
rsync -a --delete /tmp/restore-test/skills/ ~/.hermes/skills/
```

**Verified 2026-07-23:** rsync restore in 5 sec, 0 loss.

---

## Why these scripts matter for future sessions

When Basti says "audit + update the skill library", future Yuno shouldn't reinvent:
- YAML-re-render danger (Pitfall #45)
- tar.gz backup requirement (Pitfall #46)
- Strict curated_by check (Pitfall #47)
- Self-reference correction (Pitfall #48)
- Section-routing heuristics (Pitfall #49)
- `>2 ---` false positives (Pitfall #50)

Each is documented in the SKILL.md pitfalls section. The recipe here is the **second line of defense** — when someone re-authors the scripts, they have a working pattern to start from.