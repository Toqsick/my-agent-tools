# Slim-Down Protocol — Full Extraction Protocol

## Keep in SKILL.md (target: 8–15KB)

- YAML frontmatter (EXACT as-is — never modify during slim-down)
- Intro / "When To Use" section
- Phase or section headings as SHORT outline (name + 1–2 sentences)
- Critical pitfalls/warnings (bullet form)
- Code snippets ≤10 lines
- One-line pointers: `→ See references/<file>.md for details`

## Extract into `references/`

- Detailed step-by-step instructions
- All code blocks >10 lines
- Bug logs, changelog entries, fix histories
- Deep-dive explanations, API details, production evidence

## Diagnostic Scan

### Step 1: Size Inventory

```bash
find ~/.hermes/skills -name "SKILL.md" \
  -not -path "*/.archive/*" -not -path "*/duplicates*" \
  -exec wc -c {} \; | sort -rn | head -25
```

**Thresholds:**
- >40KB = urgent (monolith, heavy context cost on every load)
- 25–40KB = candidate (moderate extraction needed)
- <25KB = OK (no action)

### Step 2: References Check

For each oversized skill, check if it already has `references/`:

```bash
for skill in "category/skill-name" "other/ skill"; do
  dir=~/.hermes/skills/$skill
  refs=$(find "$dir" -type f -not -name "SKILL.md" | wc -l)
  has_refs=$([ -d "$dir/references" ] && echo "YES" || echo "no")
  size=$(wc -c < "$dir/SKILL.md")
  echo "$refs files | references=$has_refs | $skill"
done
```

### Step 3: Categorize

| Category | Criteria | Action |
|----------|----------|--------|
| **Monolith** | >25KB SKILL.md + 0 reference files | High priority — create `references/` from scratch |
| **Partial** | >25KB SKILL.md + has `references/` | Medium — move more content out |
| **OK** | <25KB | No action |

## Batch Delegation Pattern

For slimming 5+ skills, delegate to subagents in parallel waves of up to 5:

- Each subagent gets ONE skill + the full extraction protocol
- Subagent reads SKILL.md → creates `references/` files → rewrites lean SKILL.md
- Include explicit target size in the goal
- **Verify after each wave**: frontmatter intact, SKILL.md ≤ target, reference files exist and are non-empty

**Critical:** Subagents must NOT modify the YAML frontmatter. Include this as an explicit instruction in every delegation goal.

## Delegation Prompt Template

```
Task: Slim down the skill {skill_path} from {current_size}KB to target {target_size}KB.

Rules:
1. YAML frontmatter stays EXACT as-is — do NOT modify any frontmatter keys (name, description, version, etc.)
2. Create a references/ directory and extract content into it
3. SKILL.md becomes a cheatsheet: bullet points, tables, short outlines, one-line pointers
4. Extract all code blocks >10 lines into reference files
5. Extract detailed step-by-step instructions, deep prose, bug logs, changelogs
6. Keep only: frontmatter + intro + short section outlines + critical pitfalls + code ≤10 lines + pointers
7. Each reference file must have substantive content (>500 bytes)
8. After extraction, verify: no broken links, all references/ files exist

Target size: {target_size}KB (12-14KB acceptable for smaller candidates)
```

## Post-Slim-Down Verification

```bash
# Check: frontmatter starts with ---
head -1 ~/.hermes/skills/<category>/<skill>/SKILL.md

# Check: size is within target
wc -c ~/.hermes/skills/<category>/<skill>/SKILL.md

# Check: reference files exist and have content
find ~/.hermes/skills/<category>/<skill>/references/ -name "*.md" -exec wc -l {} \;

# Check: every bare references/X.md link target exists (cheatsheet style)
grep -oE 'references/[a-zA-Z0-9_-]+\.md' \
  ~/.hermes/skills/<category>/<skill>/SKILL.md | sort -u | while read f; do
    [ -f "$f" ] || echo "DANGLING LINK: $f"
  done

# Check: full markdown-link resolution for [text](path) form
grep -oE '\]\((references/[a-zA-Z0-9_/.-]+\.md)\)' \
  ~/.hermes/skills/<category>/<skill>/SKILL.md \
  | sed 's/^](\(.*\))$/\1/' | sort -u | while read f; do
    [ -f "$f" ] || echo "DANGLING LINK: $f"
  done
```

## PyYAML Frontmatter Verification

```python
import yaml
with open('SKILL.md') as f:
    parts = f.read().split('---', 2)
fm = yaml.safe_load(parts[1])  # raises yaml.YAMLError if broken
print('Keys:', list(fm.keys()))  # confirms expected fields present
```

## Verified

2026-07-02: Round 1 — 9 skills slimmed 33-105KB → 6-14KB across 2 waves, 26 broken refs caught + fixed.
2026-07-03: Round 2 — 10 skills slimmed 22-29KB → 8.6-12.3KB across 2 waves.