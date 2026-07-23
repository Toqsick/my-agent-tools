# Wiki-Link Density - Bash Alternative

Für Subagenten ohne Python-Interpreter, oder für schnelle Post-Batch-Verifikation:

## Full Vault Scan

```bash
bash scripts/wiki-link-density.sh "/home/bratan/Dokumente/Obsidian Vault"
```

## Specific Files Only

```bash
bash scripts/wiki-link-density.sh "/home/bratan/Dokumente/Obsidian Vault" \
  "05 Ressourcen/MOC - Security-Hardening.md" \
  "05 Ressourcen/System-Tuning - GPU-OC-Guide.md"
```

## Output

Per-File (`links | lines | filename`) + Aggregate (total, avg, lowest). Zählt **brutto** (jede `[[...]]`), nicht unique — für Schwellwert-Prüfungen (≥ 5 links) ausreichend. Kein Python nötig.

## Inline Density Check

```bash
# Check avg link density
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
```

## Orphan Check

```bash
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
```