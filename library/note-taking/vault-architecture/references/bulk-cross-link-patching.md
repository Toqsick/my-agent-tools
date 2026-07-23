# Bulk Cross-Link Patching — Obsidian Vault

Systematisches Hinzufügen mehrerer Wiki-Links zu existierenden Cross-Reference-Sektionen in Obsidian-Notes. Bewährt für Cluster-Vernetzung, Cross-Link-Expansion und Vault-Konsolidierung nach Import-Phasen.

## Workflow

### Phase 0: Inventory

1. Lies die Action-Liste (welche Links in welche Notes)
2. Identifiziere pro Target-Note die **letzte Cross-Reference-Sektion** (Section-Header + letzte dazugehörige Zeile)
3. Prüfe ob es bereits Broken-Links im File gibt (z.B. `[[GreyHack - X 2026-07-14]]` mit Spaces) — diese **nicht** anfassen

### Phase 1: Section-Detection (kritisch!)

**Algorithmus für `find_section_end(lines, header_line_idx)`:**

```python
# 1. Bestimme den Header-Level des Section-Headers (Anzahl '#' Zeichen)
cur_line = lines[header_line_idx]
cur_level = 0
for ch in cur_line:
    if ch == '#':
        cur_level += 1
    else:
        break

# 2. Scanne ab header_line_idx + 1 bis zum nächsten Header
#    mit GLEICHEM oder HÖHEREM Level (= gleiche '#' oder weniger)
n = len(lines)
for i in range(header_line_idx + 1, n):
    m = re.match(r'^(#{1,6})\s+', lines[i])
    if m:
        this_level = len(m.group(1))
        if this_level <= cur_level:
            return i  # Neue Sektion beginnt hier — insert BEFORE this line
return n  # EOF
```

**Warum das wichtig ist:**
- `###`-Sub-Header (z.B. `### 3.1 Aktive Mission-Detail`) gehören **zur Sektion** — sie sind niedrigerer Level
- Nur `##` (gleicher Level) oder `#` (höherer Level) brechen die Sektion
- Ohne diesen Check landen Links zwischen Section-Header und erstem Sub-Header statt am Sektions-Ende

### Phase 2: Duplicate Detection

Vor jedem Insert: **exakte Prüfung über die gesamte Datei** (nicht nur innerhalb der Sektion):

```python
if f'[[{link_name}]]' in full_content:
    skip = True  # Bereits vorhanden → überspringen
```

### Phase 3: Insertion

Insert am Sektions-Ende (vor dem nächsten gleichrangigen Header oder EOF):

```python
new_lines = lines[:section_end] + [f'- [[{link_name}]]\n'] + lines[section_end:]
```

### Phase 4: Backup-Recovery-Pattern

Vor dem ersten Patcher-Durchlauf: **Backup aller zu modifizierenden Files**:

```python
import shutil
from pathlib import Path
shutil.copy2(source_path, backup_path)
```

Bei Fehlern: Restore aller Files, Patcher fixen, nochmal laufen lassen.

### Phase 5: Verification

**Pflicht-Checks nach jedem Bulk-Patch:**

1. **JSON-Validierung**: `json.load(open(output_path))` — alle Patches dokumentiert
2. **Grep-Verifikation**: Jeder Link exakt 1 Mal in der Datei:
   ```bash
   grep -c '\[\[Link-Name\]\]' target.md
   ```
3. **Section-Position check**: Stichprobe per `sed -n` um die Section herum
4. **Encoding**: UTF-8 ohne Korruption (Umlaute vorhanden)
5. **Broken-Links**: Vorher existierende Broken-Links **nicht** verändert

## Section-Naming Conventions (bisher beobachtet)

| Section-Header | Typisch für |
|---|---|
| `## 11. Cross-References (Wiki-Links zu Vault)` | N1 Sprachreferenz |
| `## 📚 Verbindet zu` | N2 Cookbook, N6 Tool-Workflow |
| `## Verbindet zu` | N3 Lib-Katalog |
| `## 8. Cross-Cluster-Wiki-Links` | N4 Audit |
| `## 6. Cross-Links (Vault-Werkzeugkasten)` | N5 Known-Bugs |
| `## 3. Wiki-Cross-Links` | N7 Mission-Reports-Index |

## Proven Example

- **38 Patches** in 7 Files (2026-07-14, GreyHack-Cluster-Cross-Linking)
- **1 Duplikat übersprungen** (Action-Liste hatte doppelte Zeile)
- **1 Bug gefixt** (Section-End-Detection bei `###`-Sub-Headern → Restore + Re-Run)
- **Verifiziert**: 38/38 Links exakt 1 Mal vorhanden, keine Broken-Links dupliziert

## Pitfalls

| # | Pitfall | Mitigation |
|---|---|---|
| 1 | Section-End stoppt bei `###` (Sub-Header) — Links landen falsch | Nur auf gleichen/höheren Header-Level stoppen (siehe Algorithmus) |
| 2 | Duplicate-Check prüft nur innerhalb der Sektion | Über die gesamte Datei prüfen |
| 3 | Patcher läuft mehrmals hintereinander → Duplikate | Dup-Check + `replace_all=False` Modus, sonst wird immer mehr angehängt |
| 4 | N7 hat Cross-Reference-Sektion mittendrin (nicht am Datei-Ende) | Section-End via Header-Level, nicht via EOF |
| 5 | Action-Liste selbst hat Duplikate | Dedup-Check beim Parsen der Action-Liste |
| 6 | Broken-Links (z.B. `[[GreyHack - X]]` mit Spaces) werden als "Duplikat" erkannt | Exakter Link-Vergleich: `[[GreyHack - X]]` ≠ `[[GreyHack-X]]` |
| 7 | YAML-Frontmatter in der Section URI | Section-Header muss außerhalb des Frontmatter-Blocks liegen |
| 8 | Vergessen, Output JSON zu schreiben | `json.dump(patches, f, indent=2, ensure_ascii=False)` — Pflicht-Output |