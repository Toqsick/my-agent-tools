# Cross-Link Cleanup Procedure

After every expansion, run a **broken-link audit** using the reusable script:

```bash
python3 scripts/check-broken-wiki-links.py <vault-path>
```

The script reports:
1. **Wiki-links** (`[[Non-Existent Note]]`) pointing to files that don't exist — with alias resolution
2. **Markdown-style .md links** (`[text](path%20with%20spaces.md)`) pointing to missing files
3. Exclusive of intentional template placeholders (`[[…]]`, `[[<verlinkte Note>]]`, syntax examples)

## Fix Strategies for Broken Links

### Strategy A — Add an alias (when the source file exists but under a different name)

```yaml
---
tags:
  - moc
aliases:
  - "MOC - Projekte"        # what [[MOC - Projekte]] resolves to
  - "MOC - Projekte-Alias"  # extra alias if used elsewhere
---
```

Apply to: Folder `_MOC.md` files, project `README.md` files, or any note referenced by a truncated/alternative-name wiki-link from the vault.

### Strategy B — Convert markdown links to wiki-links (Obsidian-native style)

| Before | After |
|---|---|
| `[Dev-Work](04%20Bereiche/Dev-Work%20-%20Lokal%20AI%20%26%20Tools.md)` | `[[Dev-Work - Lokal AI & Tools]]` |
| `[2026-07-05](06%20Daily%20Notes/2026-07-05.md)` | `[[2026-07-05]]` |

Wiki-links resolve by **filename stem** in Obsidian — no path needed, and they auto-update on rename.

### Strategy C — Create the missing file (last resort — only if content is actually missing)

Create a minimal stub with frontmatter and 3+ wiki-links. Then link from its parent MOC.

### Strategy D — Acknowledge as intentional (template docs, syntax examples, external refs)

These patterns are excluded by the script automatically:
- `[[…]]`, `[[<verlinkte Note>]]`, `[[<Referenz>]]`
- `[[Dateiname]]` (syntax example)
- `[[Multi-Agent Work Skill]]` (Hermes skill, lives outside vault)
- `[[Neuer Link]]` (Obsidian default welcome-page link)
- `[[YYYY-MM-DD - tool - screen.png]]` (embed syntax example)

## Verification after cleanup

```bash
# 1. Full note count
find "$VAULT" -name '*.md' -not -path '*/.obsidian/*' | wc -l

# 2. Re-run broken-link check
python3 scripts/check-broken-wiki-links.py "$VAULT"

# 3. Wiki-link density
python3 -c "
import os, re
vault = '$VAULT'
links = []
for root, dirs, files in os.walk(vault):
    if '.obsidian' in root or '.trash' in root: continue
    for f in files:
        if not f.endswith('.md'): continue
        with open(os.path.join(root, f)) as fh:
            c = fh.read()
        l = len(set(re.findall(r'\[\[([^\]|#]+)', c)))
        links.append(l)
print(f'Notes: {len(links)}, Avg: {sum(links)/len(links):.1f}, Med: {sorted(links)[len(links)//2]}')
"

# 4. Orphan check (notes with 0 outgoing links)
python3 -c "
import os, re
vault = '$VAULT'
orphans = []
for r, ds, fs in os.walk(vault):
    if '.obsidian' in r or '.trash' in r: continue
    for f in fs:
        if not f.endswith('.md'): continue
        p = os.path.join(r, f)
        with open(p) as fh:
            c = fh.read()
        if not re.search(r'\[\[([^\]|#]+)\]\]', c) and '_MOC' not in f and '_README' not in f and 'Willkommen' not in f:
            orphans.append(os.path.relpath(p, vault))
print(f'Orphans (no outgoing links): {len(orphans)}')
for o in orphans: print(f'  {o}')
"

# 5. Memory save
```

## Pitfalls in Cross-Link Cleanup

- **Escaped pipes in markdown tables**: When creating aliased links inside markdown tables (e.g. inside a dashboard or MOC table), some models or tools try to escape the pipe character as `[[Note\|Alias]]` or `[[Note.canvas\|Alias]]`. Obsidian's internal link indexer parses the backslash `\` as part of the file name (looking for `Note\` on disk), which flags the link as broken. Always use standard unescaped pipes `[[Note|Alias]]` directly inside tables — Obsidian's native parser is robust and will not break the table cells.
- **Regex false positives in code blocks**: When writing automated scripts to audit wiki-links (like Python regex sweeps), bash test expressions using double brackets (e.g., `if [[ -n "$var" ]]`) inside code blocks will be flagged as broken links unless you explicitly strip all triple-backtick and inline code blocks from the markdown text before searching for `[[` patterns.
- **Alphabetical false positives**: `[[…]]`, `[[<Name>]]` look like broken links but are template syntax — always check context.
- **External links**: `[[Multi-Agent Work Skill]]` may be a note in another vault or a Hermes skill — verify before marking as broken.
- **Obsidian auto-create**: Obsidian shows red for unresolved links but can auto-create the file on click — don't create these files until you're sure the content direction is right.
- **URL-encoded hrefs**: `[text](path%20with%20spaces.md)` format appears when someone copied a markdown link from an Obsidian-non-aware editor. Always convert to `[[Wiki-Link]]` style.