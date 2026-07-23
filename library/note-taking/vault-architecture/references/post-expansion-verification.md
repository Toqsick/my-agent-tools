# Post-Expansion Verification Template

> Run after every vault expansion phase (Phase 2/3/4+) to verify that all new and patched notes meet quality targets.

## Quick-Use Block

```python
import os, re, sys

vault = "/home/bratan/Dokumente/Obsidian Vault"

print("=== POST-EXPANSION VERIFICATION ===\n")

# 1. Define new files created in this phase
new_files = [
    "MOC - Content-Creation.md",
    "04 Bereiche/Content-Creation.md",
    "05 Ressourcen/Youtube-Pipeline-Workflow.md",
    "05 Ressourcen/Podcast-Skript-Templates.md",
    "05 Ressourcen/Content-Pipeline-As-Code.md",
]

# 2. Check each new file
print("--- NEUE NOTES ---")
for f in new_files:
    full = os.path.join(vault, f)
    if not os.path.exists(full):
        print(f"  ❌ MISSING: {f}")
        continue
    size = os.path.getsize(full)
    with open(full) as fh:
        c = fh.read()
    lines = len(c.splitlines())
    links = len(set(re.findall(r"\[\[([^\]|#]+)", c)))
    print(f"  {'✅' if links >= 3 else '⚠️'} {f}")
    print(f"      {lines} Zeilen, {size} Bytes, {links} Wiki-Links")

# 3. Check patched files for Content-Creation references
print()
print("--- GEPATCHTE NOTES (Content-Creation coverage) ---")
patched = ["MOC - Home.md", "04 Bereiche/_MOC.md", "00 Knowledge Graph.md"]
for f in patched:
    full = os.path.join(vault, f)
    with open(full) as fh:
        c = fh.read()
    cc_count = c.count("Content-Creation")
    print(f"  {'✅' if cc_count >= 3 else '⚠️'} {f}: 'Content-Creation' {cc_count}x erwaehnt")

# 4. Consistency check — every new note references its MOC/bereich
print()
print("--- KONSISTENZ-CHECK ---")
expected_moc = "MOC - Content-Creation"
for f in new_files:
    full = os.path.join(vault, f)
    with open(full) as fh:
        c = fh.read()
    has_moc = expected_moc in c
    print(f"  {'✅' if has_moc else '⚠️'} {f}: MOC-Referenz = {has_moc}")

# 5. Vault-wide metrics
print()
print("--- VAULT-METRIKEN ---")
links_per_note = []
for root, dirs, files in os.walk(vault):
    if ".obsidian" in root or ".trash" in root or "_templates" in root:
        continue
    for f in files:
        if not f.endswith(".md"):
            continue
        full = os.path.join(root, f)
        with open(full) as fh:
            c = fh.read()
        links_per_note.append(len(set(re.findall(r"\[\[([^\]|#]+)", c))))

avg = sum(links_per_note) / len(links_per_note)
print(f"  Notes gesamt: {len(links_per_note)}")
print(f"  Wiki-Link-Density avg: {avg:.1f}")
print(f"  Wiki-Link-Density med: {sorted(links_per_note)[len(links_per_note)//2]}")
```

## What Each Section Checks

| Check | Target | Why |
|---|---|---|
| **Neue Notes existieren** | 100 % created | Catches failed write_file calls |
| **Jede Note ≥ 3 Wiki-Links** | 100 % | Vault-Architektur-Rule: no stubs |
| **Patched files have correct references** | ≥ 3 mentions | MOC/bereiche-Tabelle muss aktuell sein |
| **Consistency: new notes reference their MOC** | 100 % | Dead notes = user finds nothing via Hub |
| **Vault-wide link density** | ≥ 3.5 avg / ≥ 3 med | Phase-1 baseline; improves each phase |

## Integration with Broken-Link Check

The broken-link check (`scripts/check-broken-wiki-links.py`) focuses on **false positives**:
- Template placeholders (`[[…]]`, `[[<verlinkte Note>]]`, `[[Dateiname]]`)
- Inline parenthetical comments (`(<-- Platzhalter, ...)`)
- Syntax examples in code blocks

The verification script above focuses on **content quality**:
- Do new notes have enough links?
- Do patched hubs mention the new topics?
- Is vault-wide density improving?

Run **both** after every expansion.

## See Also

- `vault-architecture` SKILL.md → `## Wiki-Link Density Routine`
- `vault-architecture` SKILL.md → `## Vault Health Check Items`
- `scripts/check-broken-wiki-links.py`
