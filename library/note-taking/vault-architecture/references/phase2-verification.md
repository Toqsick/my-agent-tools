# Phase 2 Post-Expansion Verification

Run after vault expansion phases to verify success.

```bash
# 1. Full note count
find "$VAULT" -name '*.md' -not -path '*/.obsidian/*' | wc -l

# 2. Broken-link audit (see also: scripts/check-broken-wiki-links.py)
python3 scripts/check-broken-wiki-links.py "$VAULT"

# 3. Wiki-link density
python3 -c "
import os, re
vault = '/home/bratan/Dokumente/Obsidian Vault'
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

# 4. Cross-link cleanup — orphan check
python3 -c "
import os, re
vault = '/home/bratan/Dokumente/Obsidian Vault'
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

## Verification Checklist

- Notes count increased as expected
- No broken wiki-links reported
- Wiki-link density improved (avg ≥ 3.5)
- Orphan count reduced
- New notes have frontmatter and wiki-links