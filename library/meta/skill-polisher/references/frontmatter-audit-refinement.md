# Frontmatter Audit Refinement

> **Source:** 2026-07-15 Skill-Audit — Erste Schätzung meldete 331 Issues, davon 265 false positives.
> **Topics:** YAML frontmatter, multiline descriptions, issue quantification.

## Das Problem

Der naive Audit (`validate-fm` ohne Multiline-Bewusstsein) zählt **jede Description ohne Punkt** als Issue. Aber YAML-Multiline-Descriptions (`|`, `>` style) haben **legitim keinen Punkt in der ersten Zeile** — die Description setzt sich über mehrere Zeilen fort.

## Die Technik

### Schritt 1: Refined Regex

Statt `description:\s*(.+)` (greedy, erwischt auch Multiline):

```python
desc_match = re.search(r'^description:\s*(.+)$', fm, re.M)
```

Der `$` Anchor matched nur eine echte einzelne Zeile.

### Schritt 2: Multiline-Check

```python
if desc_match:
    line = desc_match.group(1).strip()
    # Multiline YAML block scalars — legit no period on first line
    if line.startswith('|') or line.startswith('>'):
        MULTILINE_DESC.append(rel)
        continue
    # Single-line: must end with period
    if not line.rstrip().endswith('.'):
        TRUE_PERIOD_ISSUES.append((rel, line[:100]))
```

### Schritt 3: Report mit FP-Ratio

```python
print(f"REAL period issues: {len(TRUE_PERIOD_ISSUES)}")
print(f"FP (multiline):    {len(MULTILINE_DESC)}")
print(f"Accuracy:          {len(TRUE_PERIOD_ISSUES)}/{len(TOTAL_PERIOD_CANDIDATES)} = {pct}")
```

## Ergebnisse (2026-07-15)

| Metrik | Wert |
|---|---|
| Total SKILL.md | 482 |
| Naiver Audit | 331 Issues |
| Davon Multiline-FPs | ~265 |
| **Echte Issues** | **~66** (36 missing author, 23 missing version, 7 period/name) |

## Anwendung

Diese Technik gehört in die `validate-fm` und `fix-fm` Subcommands des skill-polisher. Der `fix-fm` Subcommand sollte `--only` Parameter haben um Kategorien einzeln zu fixen (author zuerst, dann version, dann period, zuletzt name).

## Pitfalls

- **`ruamel.yaml` (round-trip) vs `PyYAML`** — `PyYAML` zerschießt Quote-Stil und Kommentare. `ruamel.yaml` preserviert alles.
- **`description: |` style** — Der YAML-Dumper schreibt Multiline anders zurück. Im Zweifel: nur single-line Descriptions auto-fixen, Multiline manuell reviewen.
- **Name-Slugification** — `' ' → '-'` und Lowercase kann kollidieren wenn zwei Skills ähnliche Namen haben. Nach jedem Name-Fix: Check auf Dupes via `find-duplicates`.