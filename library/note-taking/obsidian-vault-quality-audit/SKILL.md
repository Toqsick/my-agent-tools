---
name: obsidian-vault-quality-audit
description: >-
  Use when user asks for auditing Obsidian vault health, finding orphaned or dead-end notes, checking backlink round trips, or building a Dataview link report. NOT for creating new vault content or restructuring the whole vault architecture. Runs link inventory, orphan detection, alias-aware resolution, Canvas and attachment checks, reports, and post-cluster verification.
category: note-taking
platforms:
- linux
- macos
- windows
version: 1.1.0
author: Yuno (Basti)
source: vault/05 Ressourcen/Skill-Ableitung - Vault-Phase-2-3.md
lane: koenigin
reasoning_effort: high
metadata:
  hermes:
    tags:
    - obsidian
    - vault
    - audit
    - dataview
    - backlinks
    - quality
    - drift
    related_skills:
    - obsidian
    - vault-architecture
    - obsidian-vault-cluster-operations
    - multi-agent-cluster-patterns
triggers:
- vault audit
- backlink audit
- verwaiste notes
- orphan notes
- wiki-link check
- vault health check
- doku drift
- plugin status
- dataview installiert?
- obsidian plugin status
- dataview aktiv?
- audit report drift
- zahlen korrigieren
- wert aktualisieren
- stale fix
- greyhack stale
- bulk link fix
- link format fix
- link formatting
- spaces to hyphens
- wiki-link format
license: MIT
trigger_keywords: ['vault', 'link', 'and', 'obsidian-vault-quality-audit', 'auditing']
keywords: ['vault', 'link', 'user', 'asks', 'auditing']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['obsidian-vault-cluster-operations', 'obsidian', 'obsidian-vault-sync']
---


# Obsidian Vault — Quality Audit

Automatisiere Pattern 6 + 7 aus `Skill-Ableitung - Vault-Phase-2-3.md` (**Backlink-Roundtrip-Audit** + **Verwaiste-Notes-Detection**) sowie Pattern 11 (**Vault-Doku-vs-Plugin-State-Drift**). Dataview-basiert, post-Cluster ausgeführt.

## Trigger Conditions

Use this skill when the user asks to:
- "Vault-Quality-Check" / "Vault Health Check"
- "Sackgassen-Notes finden" / "Verwaiste Notes"
- "Backlink-Audit" / "Welche Notes haben keine In-Links"
- "Wiki-Link-Spread nötig?"
- "Nach Cluster-Phase 2/3 verifizieren"
- "Dataview-Report über Vault-Verlinkung"

Nicht für: einzelne Note-Patches (→ `obsidian`), Architektur-Refactor (→ `vault-architecture`).

## Core Heuristics (2 Patterns)

### Pattern 6: Backlink-Roundtrip-Audit

**Vor Cluster-Abschluss:** Prüfe, ob neue Notes rückverlinkt sind.

**Methode — Dataview-Query pro Note:**

```dataview
LIST FROM "<vault>"
WHERE length(file.outlinks) > 0
SORT length(file.inlinks) ASC
LIMIT 20
```

**Interpretation:**
- `inlinks = 0` UND `outlinks > 3` → **Sackgasse** (Knoten ohne Eingang)
- `inlinks = 0` UND `outlinks = 0` → **Verwaiste Note** (Pattern 7)
- `inlinks ≥ 1` → gesund

**Quick-Spread-Empfehlung:** Bei 0 In-Links prüfen, welche 3–5 thematisch passenden Notes ein Outlink auf diese Note hinzufügen sollten.

### Pattern 7: Verwaiste-Notes-Detection

**Definition:** Note mit **0 In-Links UND 0 Out-Links** = komplett isoliert.

**Dataview-Query:**

```dataview
LIST FROM ""
WHERE length(file.inlinks) = 0 AND length(file.outlinks) = 0
SORT file.mtime DESC
```

**Empfohlene Aktionen:**

| Zustand | Aktion |
|---|---|
| Note ist Platzhalter/Scratchpad | Löschen oder zu `02 Inbox/` verschieben |
| Note ist thematisch relevant | Wiki-Link-Spread: 3+ Outlinks hinzufügen |
| Note ist Template/Vorlage | Als Template in `08 Anhaenge/_Templates/` markieren |
| Note ist abgeschlossen/projektleer | Verschieben zu `07 Archiv/` |
| Note ist persönliche Notiz | Behalten, mit `private:true` Tag markieren |

## Workflow: Audit-Run

### 1. Inventur (Königin, READ-ONLY)

```bash
# Vault-Scope bestätigen
ls "/home/bratan/Dokumente/Obsidian Vault" | head -20

# Anzahl Notes
search_files(pattern="*.md", target="files", path="<vault>") | wc -l

# Schneller, fehlerfreier Link-Audit via ausführbarem Skill-Skript
python3 ~/.hermes/skills/note-taking/obsidian-vault-quality-audit/scripts/genuine-broken-links-audit.py "/home/bratan/Dokumente/Obsidian Vault"
```

### 2. Dataview-Reports generieren

Wenn Dataview-Plugin aktiv ist (typischerweise in Obsidian GUI):

```dataview
// Report A: Notes sortiert nach In-Link-Count (aufsteigend)
TABLE length(file.inlinks) as "In-Links", length(file.outlinks) as "Out-Links"
FROM ""
WHERE contains(file.tags, "vault") OR contains(file.folder, "Projekte") OR contains(file.folder, "Ressourcen")
SORT length(file.inlinks) ASC
LIMIT 30

// Report B: Verwaiste Notes (Pattern 7)
LIST FROM ""
WHERE length(file.inlinks) = 0 AND length(file.outlinks) = 0

// Report C: Notes mit 0 Out-Links (potentielle Sackgassen)
TABLE length(file.inlinks) as "In-Links"
FROM ""
WHERE length(file.outlinks) = 0
SORT length(file.inlinks) DESC
LIMIT 20
```

### 3. Fallback ohne Dataview (Dataview-Plugin fehlt)

```python
# Robuster Python-Parser (Ignoriert Code-Blöcke und löst Aliase auf)
import os, re, yaml, pathlib

vault = pathlib.Path("/home/bratan/Dokumente/Obsidian Vault")
md_files = list(vault.rglob("*.md"))

# 1. Dateistems & Aliase erfassen
all_stems = {f.name.replace(".md", "").lower(): f for f in md_files}
aliases_map = {}
file_contents = {}

for f in md_files:
    rel_path = f.relative_to(vault)
    try:
        content = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    file_contents[rel_path] = content
    
    # YAML Aliase extrahieren
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1])
                if fm and "aliases" in fm:
                    aliases = fm["aliases"]
                    if isinstance(aliases, list):
                        for a in aliases:
                            aliases_map[str(a).lower()] = rel_path
                    elif isinstance(aliases, str):
                        aliases_map[aliases.lower()] = rel_path
            except Exception:
                pass

# Canvas und statische Anhänge finden
canvas_stems = {f.name.lower() for f in vault.rglob("*.canvas")}
attachment_stems = {f.name.lower() for f in vault.rglob("*") if f.suffix not in [".md", ".canvas"]}

# Pitfall #48 (2026-07-23 Welle 9 Biene 2): Wikilinks mit Pfad-Präfix `[[pfad/Excalidraw/X.canvas]]` oder mit Pipe-Anzeigename haben im Basename-Lookup das Problem dass `canvas_stems` nur Basenames mappt (z.B. `yuno-status-dashboard`), der Resolver aber volle Wikilink-Pfade prüft (z.B. `08 anhaenge/excalidraw/yuno-status-dashboard`). Abhilfe: zusätzlicher Basename-Fallback (siehe Patch in genuine-broken-links-audit.py Zeile 132a/b).

def strip_code_blocks(text):
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL) # Code-Blöcke
    return re.sub(r"`.*?`", "", text) # Inline-Code

# 2. Links analysieren
inlinks = {f.relative_to(vault): set() for f in md_files}
outlinks = {f.relative_to(vault): set() for f in md_files}
broken_links = {}

for rel_path, content in file_contents.items():
    clean_content = strip_code_blocks(content)
    matches = re.findall(r"\[\[([^\]]+)\]\]", clean_content)
    
    for m in matches:
        target = re.split(r"[|#]", m)[0].strip()
        if not target or (target.startswith("<") and target.endswith(">")):
            continue
        
        target_lower = target.lower()
        resolved = None
        
        if target_lower in all_stems:
            resolved = pathlib.Path(all_stems[target_lower]).relative_to(vault)
        elif target_lower in aliases_map:
            resolved = aliases_map[target_lower]
        elif target_lower in canvas_stems or (target_lower + ".canvas") in canvas_stems:
            continue # Valider Canvas-Link
        elif target_lower in attachment_stems:
            continue # Valider Anhang
            
        if resolved:
            outlinks[rel_path].add(resolved)
            inlinks[resolved].add(rel_path)
        else:
            broken_links.setdefault(rel_path, []).append(m)

# 3. Auswertung
orphans = [p for p, ins in inlinks.items() if len(ins) == 0 and len(outlinks[p]) == 0 and "Willkommen" not in p.name]
print(f"Gefundene verwaiste Notes: {len(orphans)}")
for o in orphans:
    print(f" - {o}")

print(f"\nEchte Broken Links: {sum(len(v) for v in broken_links.values())}")
for f, bl in broken_links.items():
    print(f" - In {f}: {bl}")
```

### 4. Wiki-Link-Spread (Königin oder Subagent)

Bei gefundenen Sackgassen: pro Note 3–5 thematisch passende Crosslinks identifizieren und patchen.

**Best Practice:** Subagent-Briefing für Link-Spread muss dieselbe File-Scope-Disziplin haben wie Notes-Erstellung (→ `obsidian-vault-cluster-operations` Pattern 5).

### 5. Reporting

Vor Phase-Abschluss an Basti:

- Verwaiste Notes: Anzahl + Liste
- Sackgassen (0 In-Links, >0 Out-Links): Anzahl + Top 10
- Notes mit 0 Out-Links: Anzahl + ob das OK ist (manche Notes sind atomare Container)
- Avg Wiki-Links pro Note (sollte ≥ 3 sein, siehe `vault-architecture` Skill)

### Pitfalls

| # | Pitfall | Mitigation |
|---|---|---|
| 1 | Dataview-Plugin deaktiviert oder JS-Queries off → Reports leer | Fallback-Python-Script (Sektion 3); Plugin-Status prüfen via `.obsidian/community-plugins.json` + `.obsidian/plugins/<id>/manifest.json` |
| 2 | Verwaiste Notes = legitime Template-Files | Tag `template` aus Audit ausschließen |
| 3 | Notes in `02 Inbox/` werden als Verwaiste gezählt | Inbox-Filter in Dataview-Query einbauen (`WHERE !contains(file.folder, "Inbox")`) |
| 4 | Backlink-Spread überschreitet Folder-Grenzen | Wiki-Link-Hygiene: nur thematisch passende Crosslinks, kein Forced-Linking |
| 5 | Snapshot-Vergleich fehlt → Audit-Werte nicht vergleichbar | Vor+Während-Cluster Audit-Werte snapshotten |
| 6 | Dataview-Query langsam bei >1000 Notes | Cache-Ergebnisse, pro Audit max 30 Notes sichten |
| 7 | Escapete Pipes in Tabellen-Wiki-Links (`[[Note\|Alias]]`) | Führt dazu, dass Obsidian nach einer Datei mit schwebendem Backslash am Ende (`Note\`) sucht, was einen Broken Link erzeugt. Nutze reguläre unescapete Pipes `[[Note|Alias]]` — Obsidians Tabellen-Parser bricht nicht bei double-brackets. |
| 8 | Skript-Hilfs-Files (z.B. `update_mocs.py`, `daily_cron.py`) landen im Vault-Root | Bei jedem Audit `find "$VAULT" -maxdepth 1 -name '*.py'` checken, Temp-Files in `.trash/` oder ausserhalb verschieben |
| 9 | MOC-Dateien (z.B. `MOC - Home.md`) als "dünn" markiert weil sie <40 Zeilen haben | MOC-Files aus der Thin-Note-Regex ausschließen (`if "MOC" in rel_path or "moc -" in rel_path.lower()`) — MOCs werden durch Tabellen und Dataview-Queries aufgefüllt, nicht durch Prosa |
| 10 | Verwaiste-Detection zählt `_README.md`, `Willkommen.md`, Template-Files | Diese aus dem Orphan-Filter explizit ausschließen, sonst False-Positives |
| 11 | Skill-Frontmatter: Description mit Doppelpunkt-Zeichen (`:`) im Plain-Text bricht YAML-Parse | Bei Beschreibungen mit Doppelpunkten die ganze Description in Single-Quotes (`'...'`) wrappen — vom Validator als String behandelt statt als Mapping |
| 12 | Mission-Parser ignoriert Sections mit Emoji-Prefix im Header (`## 📋 Steps (vom Orchestrator...)`) | Parser muss `lstrip("#").strip().lower().startswith("steps")` ODER `startswith("📋 steps")` checken, NICHT exaktes `## Steps` |
| 13 | State-File-Pfad-Mismatch: Code zeigt auf `Mission-State.md`, existierende Note heißt `Mission-State - Live-Status.md` | Vor dem Schreiben in Path-Constants prüfen ob Vault-Datei mit dem erwarteten Namen existiert — sonst Pfad korrigieren |
| 14 | Frontmatter wird bei jedem State-Save überschrieben | Bei `write_file`-basierten State-Persistenz: existierende Datei lesen, Frontmatter extrahieren, Body neu generieren, dann mit erhaltenem Frontmatter schreiben |
| 15 | F-String-Escaping in Subprocess-Tests: `f"... {{state}} ..."` escaped `{{` zu `{` | Bei dynamischen Python-Skripts als Subprocess-String: temp-File schreiben statt `-c`-String mit Escaping-Issues |
| 16 | Path-Resolution-Bug: `ORCHESTRATOR_SCRIPT.parent / "scripts"` statt `ORCHESTRATOR_SCRIPT.parent` (Scripts sind schon im selben Verzeichnis) | Bei Definition von `ORCHESTRATOR_SCRIPT = .../scripts/orchestrator.py`: `.parent` IST bereits das scripts/-Verzeichnis, NICHT nochmal `/scripts` anhängen |
| 17 | State-Detection mit generischen Keywords ("password") matched falsch | State-Indikatoren in priorisierter Reihenfolge: SPECIFIC (Permission-Dialog, Loading) zuerst, GENERIC (Login-Screen mit "password") zuletzt |
| 18 | `[[Skill-Name]]` (externe Hermes-Skills) in Vault-Notes erzeugen Broken Links | Skill-Namen in Backticks `` `skill-name` `` setzen, da sie in `~/.hermes/skills/` leben, nicht im Vault. Nur Vault-interne Notes bekommen `[[Wiki-Links]]` |
| 19 | `search_files` mit `target="files"` findet keine Verzeichnisse unter `.obsidian/plugins/` (Tool-Limitation: erkennt nur Dateien, keine Subdirs) — führt zu falschem "Plugin nicht installiert"-Befund | Vor jedem Drift-Befund: `terminal ls -la .obsidian/plugins/` ausführen. Plugin-Dir existiert ≠ Plugin installiert (prüfe `manifest.json` + `main.js`); Plugin-Files vorhanden ≠ Plugin aktiv (prüfe `community-plugins.json`). Beide Quellen abgleichen. |
| 20 | Drift-Audit verwechselt "Plugin enabled in Config" mit "Plugin installiert" mit "Plugin aktiv in Obsidian-GUI" — diese sind drei verschiedene Zustände | Drei-Schichten-Modell: (a) `community-plugins.json` = Config-Flag, (b) `.obsidian/plugins/<id>/manifest.json + main.js` = physische Installation, (c) Obsidian-internes State = Runtime-Aktivierung (JS-Queries, Restricted Mode — nicht datei-sichtbar). Vollständiger Status erst nach Obsidian-Restart verifizierbar. |
| 21 | `vault-audit.sh` bzw. `vault-broken-count.py` löst YAML-Aliase nicht auf und meldet valide Alias-Links (z. B. `[[Daily-Briefing Skill]]` → Alias in `daily-briefing.md`) weiterhin als broken | Für die echte Obsidian-Auflösung zusätzlich `scripts/genuine-broken-links-audit.py` ausführen; im Report den rohen `vault-audit`-Wert und den Alias-False-Positive getrennt benennen. Nicht nur für den Audit Dateinamen oder Links verbiegen. |

### Pattern 8: Thin-Notes-Detection (Proven 2026-07-06)

**Definition:** Notes mit **< 40 Zeilen** werden als "dünn" markiert, weil sie dem Julian-Ivanov-Mindestumfang für Enzyklopädie-Quality nicht genügen. Ausnahmen: MOC-Dateien, `_README.md`, `Willkommen.md`, und Notes in `_templates/` oder `.trash/`.

**Python-Logik:**
```python
for rel_path, content in file_contents.items():
    line_count = len(content.splitlines())
    is_moc = "MOC" in rel_path or "moc -" in rel_path.lower()
    is_template = "_README" in rel_path or "Willkommen" in rel_path or "_templates" in rel_path
    
    if line_count < 40 and not is_moc and not is_template:
        thin_notes.append((line_count, rel_path))
```

**Basti's Hard Target**: **0 thin notes** in der finalen Enzyklopädie. Falls `thin_notes > 0`, müssen diese mit Patterns aus `references/thin-note-expansion-pattern.md` zu vollständigen Notes ausgebaut werden.

### Pattern 9: Enzyklopädie-Import-Workflow (Proven 2026-07-06)

Wenn der User bittet, externe `.md`-Dateien aus `/home/bratan/Dokumente` oder `/home/bratan/Downloads` in den Vault zu importieren, folge diesem 4-Phasen-Pattern:

**Phase 1 — Discovery (Königin, READ-ONLY)**
- Scanne Ziel-Verzeichnisse nach `.md`-Dateien mit Größe > 2 KB (kleinere sind meist Stubs)
- Filtere: keine LICENSE/CHANGELOG Boilerplates, keine CI-Templates, keine `node_modules`/`venv`-Inhalte
- Priorisiere Notes mit Tags die zu existierenden MOCs passen

**Phase 2 — Quality Gate (VOR jedem Import)**
Prüfe pro Datei:
1. Hat Frontmatter? Wenn nein → manuell ergänzen mit YAML-Block:
   ```yaml
   ---
   tags: [<mindestens 2 passende tags>]
   aliases: [<2-4 alternative Namen für Wiki-Lookup>]
   source_path: "<original absoluter Pfad>"
   imported: YYYY-MM-DD
   ---
   ```
2. Ist der Title der erste `#`-Header? Wenn nicht → strippen, neuen Title hinzufügen
3. Ist die Datei unique (kein Duplikat im Vault)? Wenn Duplikat → Alias oder skip

**Phase 3 — Import (mit Patch-Tool, niemals write_file auf existierende Dateien)**
1. Verschiebe die Datei NICHT physisch — die Notiz bleibt als zusätzliche Vault-Notiz an ihrem logischen Ort (`01 Kontext/`, `05 Ressourcen/`, `09 System-Doku/` etc.)
2. Setze Tags aus dem natürlichen Inhalt + Cluster-Zugehörigkeit
3. Setze Aliase aus alternativen Schreibweisen/Abkürzungen für robusten Wiki-Lookup
4. Schreibe mit `write_file` (kein `patch`, weil neu)

**Phase 4 — Vernetzung (Pflicht-Schritt, nicht optional)**
Nach jedem Import-Cluster:
1. Update **MOC - Home.md**: Neue Notes in die zutreffende Sektion (Kontext/Ressourcen/Projekte) mit 1-Satz-Beschreibung
2. Update das zutreffende **Themen-MOC** (KI-Architektur, Gaming-Performance, etc.) mit Backlink-Eintrag
3. Update **`05 Ressourcen/MOC - Ressourcen.md`** mit Cluster-Mapping-Eintrag
4. Update **`CHANGELOG.md`** mit Phase-N (Beispiel: "Phase 14 — Enzyklopädie-Zusammenführung")
5. Bump MOC-Home `version:` und `last-build:` Frontmatter

**Basti-Präferenz**: Bei jedem Import-Cluster **alle** Schritte ausführen, nicht teilweise. Wenn Vernetzung fehlt, werden die Notes zu "Insel-Notizen" mit 0 Inbound-Links — Pattern 7 schlägt dann fälschlicherweise nicht an, aber der Knowledge-Graph bleibt lückenhaft.

### Pattern 10: Hermes-Skill-Compliance-Check

Wenn du Vault-Notizen unter `05 Ressourcen/Skills/<name>.md` findest, prüfe ob sie der **offiziellen Hermes-Skill-Frontmatter** entsprechen. Nur konforme Skills können vom Laufzeit-System geladen werden:

| Required Field | Wert | Example |
|---|---|---|
| `name` | lowercase + hyphens, ≤64 chars | `obsidian-canvas-factory` |
| `description` | Beginnt mit "Use when ...", ≤1024 chars | `Use when you need to create...` |
| `version` | semver | `1.0.0` |
| `author` | Author-Name | `Yuno (Basti)` |
| `license` | SPDX-Identifier | `MIT` |
| `metadata.hermes.tags` | YAML-Liste | `[obsidian, canvas, design]` |
| `metadata.hermes.related_skills` | YAML-Liste | `[obsidian, vault-architecture]` |

**Pflicht-Sektionen in dieser Reihenfolge**:
1. `# Title` (exakte Spiegelung des `name`-Feldes mit Title Case)
2. `## Overview` (1-2 Absätze: Was + Warum)
3. `## When to Use` (Bullet-Liste mit Triggern + "Don't use for"-Counter-Triggern)
4. Body (spezifische Topic-Sektionen)
5. `## Common Pitfalls` (nummerierte Liste mit konkreten Fixes)
6. `## Verification Checklist` (Checkbox-Liste mit `[ ]` Items)

**Refactoring-Workflow für nicht-konforme Skills**:
1. Lies die bestehende Datei vollständig
2. Identifiziere welche Pflicht-Felder fehlen
3. Re-strukturiere das Frontmatter (additiv mit `replace_all=False`, niemals `write_file` auf existierende Skills ohne Diff-Vergleich)
4. Gliedere die Sektionen in die Pflicht-Reihenfolge
5. Speichere nach `~/.hermes/skills/<category>/<skill-name>/SKILL.md` UND behalte die Vault-Notiz als Dokumentation

## Drift-Audit References

Zwei komplementäre Drift-Patterns:

### Pattern 11a: Plugin-State-Drift
Vollständiger Workflow (Fall-Klassifikation A/B/C, Verifikations-Rezepte, Permission-Tabelle, MOC-Tabu-Disziplin) liegt in `references/plugin-state-drift-audit.md` (Proven 2026-07-10, P0-Fix Welle 1).

### Pattern 11b: Audit-Report Drift (numerische Dokumentationswerte)
Wenn ein Audit-Report stale Zahlenwerte (Counts, Timestamps, Splits) in Vault-Dokumentationen identifiziert hat, folge dem 5-Phasen-Workflow in `references/audit-report-drift-fix.md`:
- **Phase 0:** Inventur (Target + Audit parallel lesen)
- **Phase 1:** Alle Vorkommen der stale-Werte finden (nicht singular patchen!)
- **Phase 2:** Batch-Patching durch Königin (sequentiell pro Datei)
- **Phase 3:** Sub-Biene Cross-Check der Schwester-Datei (parallel dispatch)
- **Phase 4:** Diff-Log schreiben (Königin-Buchhaltung, PFLICHT)
- **Phase 5:** Finale Verifikation (search_files: 0 Treffer stale-Werte)

Siehe `references/audit-report-drift-fix.md` für vollständige Methodik, Pitfalls und Proven Example.

### Pattern 12: Bulk Wiki-Link Format Fix

Wenn ein Audit oder eine Sichtung ergibt, dass **viele Wiki-Links im Vault ein einheitliches Formatierungsproblem** haben (z.B. fälschliche Spaces um den Bindestrich im Dateinamen `[[GreyHack - X Y 2026-07-14]]` statt korrektem `[[GreyHack-X-Y-2026-07-14]]`), folge dem 6-Phasen-Workflow in `references/bulk-wiki-link-format-fix.md`:

- **Phase 1 — Inventory:** Finde ALLE betroffenen Dateien + genauen Pattern-Umfang via `search_files` mit breitem und engem Regex
- **Phase 2 — Fix-Script:** Regex-basierte Einweg-Transformation mit Edge-Case-Check (double-hyphen prevention — `strip("-")` vor Join!)
- **Phase 3 — Patch Log:** Durable JSON-Log aus initialem Snapshot rekonstruiert (niemals während des Laufs akkumulieren — Log-Overwrite bei Mehrfachläufen!)
- **Phase 4 — Sub-Bee Verification:** Dispatch eine leaf-subagent um Ziel-Existenzen zu prüfen (file-existence, nicht value-correctness)
- **Phase 5 — Residual-Correction:** Falls Sub-Bee missing targets meldet, entscheiden ob Target fehlt oder Link falsch ist
- **Phase 6 — Final Verification:** `search_files` auf altes Pattern = 0 Treffer, auf double-hyphen-Artefakte = 0 Treffer

**Abgrenzung zu Pattern 11b (Audit-Report Drift):**
- Pattern 11b patcht **numerische Werte** in Dokumentationen basierend auf einem externen Report
- Pattern 12 transformiert **Wiki-Link-Formatierungen** im gesamten Vault nach einer festen Regel (spaces → hyphens), unabhängig von Reports

Siehe `references/bulk-wiki-link-format-fix.md` für vollständige Methodik, Pitfalls, Sub-Bee-Briefing-Template und Proven Example (2026-07-14: 17 Links in 7 Dateien).

## Thin-Note Expansion Reference

Für das systematische Auffüllen dünner Notes zu Enzyklopädie-Tiefe siehe `references/thin-note-expansion-pattern.md`. Bewährte Methoden:
- Lauffähiger Code (Python/Bash) statt nur Theorie
- ASCII-Schaubilder für Workflows
- "Common Pitfalls"-Sektion mit 3-5 nummerierten Items
- Cross-Cluster Wiki-Links (3-7 pro Note)

## Connecting Skills

- **`obsidian`** — Low-Level File-Ops
- **`vault-architecture`** — Link-density-Zielwerte (≥3 Wiki-Links/Note)
- **`obsidian-vault-cluster-operations`** — Phase-D nach jedem Cluster (Pat. 6)
- **`multi-agent-cluster-patterns`** — Pattern 6+7 im Cluster-Reporting

## Source

- Vault: `Skill-Ableitung - Vault-Phase-2-3.md` (05 Ressourcen, 2026-07-05)
- Patterns 6+7 dokumentiert aus Phase-2 + Phase-3-Erfahrungen
- Dataview-Plugin: <https://blacksmithgu.github.io/obsidian-dataview/>
