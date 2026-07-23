# Fix-FM String-Patching Technique (2026-07-15)

**Problem:** The `fix-fm` subcommand used `yaml.safe_load → edit in dict → yaml.safe_dump` to fix frontmatter. This silently corrupts:
- Single-quoted values become double-quoted (`'text'` → `"text"`)
- Multiline `|`-style descriptions become block-scalars
- Flow-style mappings collapse
- YAML key ordering may change
- Comments in frontmatter are lost

**Fix:** String-patching approach — parse only for validation, apply fixes via targeted regex on raw text.

## Implementation Pattern

```python
import re
import yaml

def fix_frontmatter(text: str, skip_archive: bool = True) -> tuple[str, list[str]]:
    """
    Fix common frontmatter issues via string patching.
    Returns (fixed_text, changes_log).
    NEVER uses yaml.dump — only yaml.safe_load for validation.
    """
    parts = text.split('---', 2)
    if len(parts) < 2:
        return text, []
    
    raw_fm = parts[1]
    changes = []
    
    # 1. Validate with yaml (detect issues, don't fix via yaml)
    fm = yaml.safe_load(raw_fm)
    
    # 2. String-patch: missing period in descriptions
    if fm.get('description') and isinstance(fm['description'], str):
        desc_raw = re.search(r'^description:(.*?)$', raw_fm, re.MULTILINE)
        if desc_raw:
            raw_val = desc_raw.group(1).strip()
            # Skip if quoted (period is inside quotes, not at YAML value end)
            if not (raw_val.startswith(("'", '"')) and raw_val.endswith(("'", '"'))):
                if not raw_val.rstrip().endswith('.'):
                    new = re.sub(
                        r'(^description:\s*)(.*?)$',
                        lambda m: m.group(1) + m.group(2).rstrip() + '.',
                        raw_fm,
                        flags=re.MULTILINE
                    )
                    raw_fm = new
                    changes.append(f"Added trailing period to description")
    
    # 3. String-patch: missing author
    if 'author' not in fm:
        raw_fm += '\nauthor: Hermes\n'
        changes.append('Added author: Hermes')
    
    # 4. String-patch: missing version
    if 'version' not in fm:
        raw_fm += '\nversion: 1.0.0\n'
        changes.append('Added version: 1.0.0')
    
    fixed = parts[0] + '---' + raw_fm + '---' + '---'.join(parts[2:])
    
    # 5. VERIFY: yaml.safe_load on result must not error
    verify_parts = fixed.split('---', 2)
    try:
        yaml.safe_load(verify_parts[1])
    except Exception as e:
        raise ValueError(f"Corruption detected after patch: {e}")
    
    return fixed, changes
```

## Key Rules

| Rule | Why |
|---|---|
| NEVER use `yaml.dump` on frontmatter | Loses quoting, formatting, comments |
| Use `yaml.safe_load` ONLY for validation | Tells you what's missing without corrupting |
| Apply fixes via `re.sub` on the **raw text** | Preserves original formatting |
| Verify with `yaml.safe_load` AFTER the fix | Catches corruption immediately |
| Handle quoted descriptions separately | `'text.'` is valid — period is inside quotes |
| Skip `.archive/` skills | Archive is not production, don't touch |

## False-Positive Classification (Critical)

A naive scan reports `missing period` on three categories that are actually fine:

| Category | Example | Action |
|---|---|---|
| Quoted period inside quotes | `description: '"short text."'` | Skip — period is in YAML string, not missing |
| Multiline `\|` with period before `\|` | `description: \|` then `'text.'` on next line | Skip — multiline has implicit newline |
| Single-quote period | `description: 'text.'` | Skip — period inside single quotes |
| Archive skill | `~/.hermes/skills/.archive/foo/SKILL.md` | Skip — not production |

**Proven 2026-07-15:** Of 263 initially flagged "missing period":
- 176 = quoted descriptions (period inside quotes) → false positives
- 39 = in `.archive/` → excluded
- 7 = exempted test skills → excluded
- 4 = single-quote patterns → false positives
- **37 = real missing periods** → fixed

## Edge Cases (from 2026-07-15)

1. **`description: null`** — YAML null value, not a string. Regex patching risks creating `null.` which is invalid.
2. **Empty description** — `description:` followed by nothing. Add a default, never append period to empty.
3. **Multi-line descriptions** — `description: >\n  text` or `description: |\n  text`. Don't patch these — the YAML newline semantics differ from single-line.
4. **Nested `|` in metadata blocks** — `metadata.hermes` blocks with YAML `|` scalars inside flow mappings. String-patching regex must not touch these.
5. **UTF-8 BOM** — File starts with `\xef\xbb\xbf`. The `---` split still works, but `yaml.safe_load` may error. Check BOM before fixing.