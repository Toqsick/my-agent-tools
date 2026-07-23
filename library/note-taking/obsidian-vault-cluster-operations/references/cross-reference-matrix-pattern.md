# Cross-Reference-Matrix-Pattern

> Pattern 10 für Vault-Cluster-Operations. Proaktive Cross-Linking-Audits
> zwischen einer bekannten Menge verwandter Notes, statt passiver Backlink-Checks.
> Fundiert: 2026-07-14, GreyHack-7-Notes-Cross-Linker (38 fehlende Links gefunden + gepatcht).

## Wann anwenden

- Du hast N Notes (z.B. 5–10) zu einem Thema erstellt/aktualisiert
- Sie sollen **gegenseitig** verlinken (vollständiger Graph, nicht nur Spokes-to-Hub)
- Du willst Broken-Links erkennen (falsche Titel-Strings, veraltete Aliase)
- Du willst systematisch vorgehen statt manuell jede Note zu editieren

**Nicht anwenden für:** Einzelne Cross-Link-Ergänzungen (→ `obsidian` Skill), Backlink-Prüfung nach Cluster-Run (→ Pattern 6 Backlink-Roundtrip).

## Workflow

### Phase 1: Locate + Extract (Königin selbst)

```bash
# 1. Alle N Notes lokalisieren
find "/home/bratan/Dokumente/Obsidian Vault/" -maxdepth 4 -type f -name "*2026-07-14*.md"

# 2. Pro Note alle Wiki-Links extrahieren
for f in note1.md note2.md ...; do
    grep -oE '\[\[[^]]+\]\]' "$f" | sort -u
done
```

### Phase 2: Matrix bauen (Königin selbst)

Build a 7×6 (or N×(N-1)) matrix. For each Source→Target pair, answer:
- **Exists** — valid existing `[[TargetBasename]]` in source
- **Broken** — link exists but uses wrong title string (spaces instead of dashes, wrong casing)
- **Missing** — no link at all

**Link-Regel für Obsidian:** Ein Wiki-Link resolved NUR wenn der Link-Text EXAKT dem Datei-Basename (ohne `.md`) entspricht. `[[GreyHack - Audit 2026-07-14]]` (mit Spaces) resolved NICHT zu `GreyHack-Audit-2026-07-14.md`.

```python
matrix = {}
for source in all_notes:
    for target in all_notes:
        if source == target: continue
        # Extract all links from source
        links = extract_wiki_links(source_path[source])
        if target_basename[target] in links:
            matrix[(source,target)] = "EXISTS"
        else:
            # Check for broken links
            broken_variants = find_broken_link_variants(links, target_basename[target])
            if broken_variants:
                matrix[(source,target)] = f"BROKEN: {broken_variants[0]}"
            else:
                matrix[(source,target)] = "MISSING"
```

### Phase 3: Action-Liste generieren (Königin selbst)

Schreibe eine Datei nach `/tmp/vault-patch-gamma/<timestamp>.md` mit:
1. Der kompletten Matrix (alle Paare, farbig: ✅ / ❌)
2. Einer nummerierten Action-Liste aller ADD-Aktionen
3. Fix-Hinweisen für Broken-Links (ersetzen statt duplizieren)

**Wichtige Broken-Link-Erkennung:** Wenn ein Link als `[[GreyHack - Audit 2026-07-14]]` (mit Spaces) existiert, dann:
- Zähle ihn **nicht** als existierenden Link (er resolved nicht)
- Der ADD des korrekten `[[GreyHack-Audit-2026-07-14]]` muss den Broken-Link **ersetzene** statt einen zweiten hinzuzufügen

**Format der Action-Liste:**
```
1. ADD [[GreyHack-Audit-2026-07-14]] to GreyScript-Sprachreferenz-2026-07-14
2. ADD [[GreyScript-Sprachreferenz-2026-07-14]] to GreyHack-Hacking-Cookbook-2026-07-14
...
```

### Phase 4: Sub-Biene dispatch (Königin→delegate_task)

Dispatch eine einzelne Sub-Biene (leaf, kein orchestrator nötig da nur 1) mit:

```
goal: "Patche die N Vault-Notes mit den fehlenden Cross-Links aus der Action-Liste.
       Output-JSON nach /tmp/vault-patch-gamma/<timestamp>-sub.json"
context: "Action-Liste in /tmp/vault-patch-gamma/<timestamp>.md. 
          Broken-Links (Spaces statt Dashes) ersetzen statt duplizieren.
          Keine User-Interaktion nötig."
```

### Phase 5: Unabhängige Verifikation (Königin — PFLICHT)

**Niemals** auf den Sub-Bee-Self-Report allein vertrauen. Immer:

```python
import json, pathlib
patches = json.load(open('/tmp/vault-patch-gamma/<ts>-sub.json'))
ok = 0
for p in patches:
    f = pathlib.Path(p['file'])
    text = f.read_text(encoding='utf-8')
    if p['added_link'] in text:
        ok += 1
```

**Warum Phase 5 kritisch ist:** Sub-Agents können `write_file`-Success melden, aber die Datei hat nicht den Link (Section-Boundary-Bug, Sibling-Konflikt, `_warning` ignoriert). Nur ein unabhängiger Grep-Check deckt das auf.

## Known Pitfalls

| Pitfall | Symptom | Lösung |
|---------|---------|--------|
| **Section-Boundary-Bug** | Sub-Bee platziert Link vor `###`-Subheader statt am Ende der `##`-Sektion | `find_section_end` muss NUR bei gleichem/höherem Header-Level stoppen, nicht bei `###`-Subheadern |
| **Broken-Link-Duplikat** | Sub-Bee fügt korrekten Link hinzu, aber der alte Broken-Link bleibt → zwei Einträge für dieselbe Note | Vor jedem ADD: prüfen ob Broken-Variante existiert. Falls ja: REPLACE statt ADD |
| **Action-List-Duplikate** | Zwei Actions in der Liste adressieren dasselbe Source→Target-Paar | Dup-Detection im Sub-Bee: prüfen ob der exakte Link-String bereits in der Datei existiert |
| **Dateiname vs. Link-Text (Spaces!)** | `[[GreyHack - Audit 2026-07-14]]` (mit Spaces) resolved nicht zu `GreyHack-Audit-2026-07-14.md` | IMMER den exakten Datei-Basename (ohne `.md`) als Link-Text verwenden. Keine Spaces zwischen zusammengehörigen Namensbestandteilen. |

## Metrics from Practice

| Metrik | Wert | Quelle |
|--------|------|--------|
| Notes in Audit | 7 | GreyHack-2026-07-14-Set |
| Mögliche Paare (N×(N-1)) | 42 | — |
| Vorhandene Links | 4 (9.5%) | — |
| Fehlende Links | 38 (90.5%) | — |
| Broken Links (falscher Titel) | 6 | N5 + N6 nutzten Spaces |
| Sub-Bee Laufzeit | ~3 Min 39s | MiniMax-M3 |
| Verifikations-Fehler | 0/38 | Unabhängiger Grep-Check |

## Related

- `obsidian-vault-cluster-operations` Pattern 6 (Backlink-Roundtrip für neue Notes)
- `obsidian-vault-quality-audit` — generelle Vault-Health-Checks