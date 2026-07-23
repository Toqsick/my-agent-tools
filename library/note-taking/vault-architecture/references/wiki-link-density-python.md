# Wiki-Link Density - Python Script

Calculate wiki-link density for vault health checks.

```python
import os, re

vault = "<resolved-vault-path>"
results = []
for root, dirs, files in os.walk(vault):
    if ".obsidian" in root or ".trash" in root:
        continue
    for f in files:
        if not f.endswith(".md"):
            continue
        path = os.path.join(root, f)
        with open(path) as fh:
            content = fh.read()
        links = len(set(re.findall(r"\[\[([^\]|#]+)", content)))
        lines = len(content.splitlines())
        results.append((links, path, lines))

results.sort(reverse=True)
# Report: avg, median, top-hubs, breakdown per folder
```

## Target Metrics

- Average links/note: **≥ 3.5** for a healthy vault
- MOC notes: **≥ 10** links each
- No content note with **0 links** (exclude _MOC.md, _README.md, Willkommen.md)

## Thin Notes Detection

```python
import os

vault = "<resolved-vault-path>"
thin_notes = []
all_notes = []
for root, dirs, files in os.walk(vault):
    if ".obsidian" in root or ".trash" in root or "_templates" in root:
        continue
    for f in files:
        if not f.endswith(".md"):
            continue
        full = os.path.join(root, f)
        rel = os.path.relpath(full, vault)
        with open(full) as fh:
            content = fh.read()
        lines = len(content.splitlines())
        all_notes.append(rel)
        if lines < 60 and "_MOC" not in f and "_README" not in f and "Willkommen" not in f:
            thin_notes.append((lines, rel))

thin_notes.sort()
print(f"Dünne Notes (< 60 Zeilen): {len(thin_notes)} von {len(all_notes)} Gesamt")
for lines, note in thin_notes:
    print(f"  {lines:>3}  {note}")
```

## MOC Density Check

```python
for m in ["MOC - Gaming-Performance.md", "MOC - KI-Architektur.md", "MOC - Obsidian-Vault.md"]:
    full = os.path.join(vault, m)
    if os.path.exists(full):
        with open(full) as fh:
            c = fh.read()
        links = len(set(re.findall(r"\[\[([^\]|#]+)", c)))
        print(f"  {m}: {links} out-links")
```