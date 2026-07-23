# Sequential Perplexity-Artefakt Ingest — Single-Source Workflow

> Workflow für das Ingieren von **Perplexity-generierten Repo-Artefakten**
> in die Wiki. Im Gegensatz zum parallelen Scout-Pattern (Bulk-Ingest mehrerer
> Quellen) ist dies ein **sequentieller Single-Source-Ingest** mit Fokus auf
> Präzision, Verbatim-Code-Extraktion und Provenance.
>
> Gelernt aus: Session 2026-07-17 — Ingest von hermes-v7-repo-starters
> (3 Varianten), hermes-webui (Templates+Skills), Master Operativ System.

## Wann Dieses Pattern

Nutze diese Reference wenn:

- Du **eine einzelne Source** hast (ein Perplexity-Export, ein Repo-Clone,
  ein PDF-Report), keine 10+ parallelen Quellen
- Die Quelle **lebendigen Code** enthält (package.json, server.ts,
  hermes.config.json, SKILL.md) — kein reines Prosa-Material
- Du **Verbatim-Exzerpte** aus der Quelle brauchst, keine Zusammenfassung
- Der Fokus auf **einem Domain-Cluster** liegt (orchestration, cross-domain)
- Du unter **Zeitdruck** stehst — sequential ingest ist schneller im
  Single-Source-Fall als Scout-Overhead zu rechtfertigen

Nicht nutzen wenn ≥10 Quellen parallel existieren → paralleles
Scout-Pattern aus dem Haupt-Skill.

## Workflow (6 Phasen)

### Phase 1: Source Survey

```
Für jede Source-Directory:
  ls -laR <dir>                          # Gesamtstruktur
  cat <dir>/README.md                    # Kontext
  cat <dir>/package.json                 # bei Node-Repos
  wc -c <dir>/*.ts <dir>/*.html          # Größe der Haupt-Dateien
  du -sh <dir>/                          # Gesamt-Größe (Warnung: +100 MB → nur scannen)
```

**Besonderheit bei Perplexity-Exports:**
- Jedes Verzeichnis kann 1–10+ Dateien haben (README, package.json,
  server.ts, index.html, SKILL.md, skill.schema.json, etc.)
- Große Artefakte (`hermes-v7-repo-starter-node-express-v0-quickstart/`
  mit 155 MB) enthalten oft launchable/provisionable Code — **NICHT kopieren**,
  nur Topologie scannen und im Log vermerken.

**Einlese-Reihenfolge (effizient):**
1. `README.md` — Kontext, Zweck, Variante
2. `package.json` — Dependencies, Scripts, Projekt-Metadaten
3. Haupt-Server-Datei (server.ts, app.py, index.html) — Code-Struktur
4. Konfigurationsdateien (hermes.config.json, skill.schema.json)
5. Alle Skills/SKILL.md — falls vorhanden

### Phase 2: Raw-Artikel Erstellen

Pro Source-Variante **eine** `raw/articles/<slug>-<date>.md` Datei:

```yaml
---
title: <Source Title>
source_url: "file://<absoluter Pfad>"
source_type: perplexity-export
extracted: 2026-07-17
domain: <Domain aus SCHEMA>
sha256: <body-hash>
---
# <Source Title>

> Quell-Pfad: `~/Dokumente/Perplexity/<dir>/`

## Topologie

- README.md — Beschreibung
- package.json — Dependencies, Scripts
- src/server.ts — Express-Server (Hauptdatei)
- src/routes/status.ts — Dashboard-Route (optional)
- ...

## Code-Beispiele (verbatim)

```typescript
// Aus src/server.ts — exakt aus der Quelle kopiert
import express from 'express';
const app = express();
// ...
```

> **Wichtig:** Code-Beispiele müssen **verbatim** aus der Quelle sein.
> Keine synthetisierten Beispiele, keine "analogen" Versionen.
> Bei PDF/Text-Quellen: wörtliche Zitate mit `> ` Blockquote.

```

**sha256-Berechnung:** Nur über den Body (nach Frontmatter `---`):
```python
import yaml, hashlib
with open(path) as f:
    content = f.read()
lines = content.split('\n')
if lines[0].strip() == '---':
    close_idx = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == '---')
    body = '\n'.join(lines[close_idx+1:])
    sha256 = hashlib.sha256(body.encode()).hexdigest()
```

### Phase 3: Concept-Pages Synthetisieren

Pro Konzept (nicht pro Source!) eine Concept-Page. Die
Source-Topologie bestimmt die Aufteilung:

| Source-Typ | Typische Pages |
|---|---|
| Server-Architektur (1 Mainfile) | 1 Concept: Vollständige Architektur |
| Client + Server (getrennt) | 2 Concepts: Frontend, Backend |
| 3+ Skill-Dateien + Templates | 1 Concept: Skills-Bundle |
| Referenz-Dokument (PDF/Wiki) | 1 Concept: Überblick |

**Frontmatter-Regeln:**
- `sources:` → Liste aller Raw-Artikel, aus denen synthetisiert wurde
- `domain:` → aus SCHEMA.md Taxonomie (`orchestration`, `cross-domain`, ...)
- `tags:` → **strikt aus SCHEMA.md Taxonomy** (65 Tags). Vor dem Schreiben
  prüfen: `grep "^- \`<tag>\`" SCHEMA.md`
- `linked_files:` → `[]` bei Neu-Erstellung
- Bei alleiniger Quelle (`sources:` hat nur 1 Eintrag) → `confidence: medium`

**Provenance-Marker:** Jeder Absatz, der aus einer Quelle synthetisiert
wurde, endet mit `^[raw/articles/<dateiname>]`.

**Wikilink-Regeln:**
- Minimum **3 outbound Wikilinks** pro Page (nicht die 2 aus SCHEMA — Ziel 3)
- Wikilinks nur auf Pages die **existieren** (Prüfung nach Phase 4)
- Wikilinks auf **eigene Domain-Kollegen** priorisieren (orchestration → andere orchestration-Pages)
- Keine Wikilinks auf raw/ oder log/ oder andere Nicht-Content-Pages

### Phase 4: Index + Log Update

**Index.md (patch):**

```patch
Nach der Section "### Concepts" eine neue Zeile einfügen:
- [[slug|Display Title]] — Beschreibung (max 80 Zeichen)

Page-Count in der Header-Zeile inkrementieren:
ALT: Hier findest du **N** kuratierte Pages
NEU: Hier findest du **N+<anzahl_neuer_pages>** kuratierte Pages
```

**Critical: Race-Condition-Awareness bei index.md:**
```bash
# Vor jedem Patch prüfen:
grep -c "page-title" ~/wiki/index.md
# Wenn >0 → Page existiert schon → skip
# Wenn <0 → ggf. Leerzeichen-Problem → check mit cat -A
```

**Log.md (append):**

```markdown
## [YYYY-MM-DD] ingest | <Kurztitel der Aktion>

- **Domain**: <Domain(en)>
- **Sources ingested**: Liste mit Pfaden und Größen
- **Raw artifacts created (N)**: Liste neuer raw/articles/
- **New wiki pages (N, alle ≥180 lines, alle ≥3 outbound wikilinks)**: Liste
- **Index.md updated**: N new entries under <Section>
- **Log updated**: Dieser Eintrag
- **Provenance**: Jeder Paragraph trägt `^[raw/articles/...]` Marker
- **Quality gates met**: Frontmatter, Wikilinks, Tags, Broken-Links-Check
```

### Phase 5: Quality Gates (Verification)

Nach allen Patches die folgenden Checks durchführen:

| Gate | Befehl | Erwartung |
|---|---|---|
| **Frontmatter** | `grep "^---$" <page> \| wc -l` | == 2 (Öffner + Schließer) |
| **Wikilink Count** | `grep -oE "\[\[[^\]]+\|" <page> \| wc -l` | ≥3 |
| **Broken Wikilinks** | `grep -oE "\[\[[a-z0-9-]+(\|[^\]]+)?\]\]" <page> \| sed ... \| while read slug; do [ -f "concepts/\$slug.md" ] \|\| echo MISSING; done` | 0 MISSING |
| **Tag Taxonomy** | `grep -oP "tags: [\[][^\]]+[\]]" <page> \| sed 's/tags: //; s/[\[\]]//g; s/, /\n/g' \| while read tag; do grep -q "^- \`\$tag\`" ~/wiki/SCHEMA.md \|\| echo "BAD TAG: \$tag"; done` | 0 BAD TAG |
| **Domain Match** | `grep "^domain:" <page>` | Stimmt mit SCHEMA-Domains überein |
| **Page Count in Index** | `grep -oE "\[\[[a-z0-9-]+\|" ~/wiki/index.md \| sort -u \| wc -l` | Stimmt mit Header-Count überein |

**Kompakter One-Liner für den Broken-Link-Check:**

```bash
cd ~/wiki
for page in concepts/hermes-*-*.md concepts/master-*.md; do
  echo "=== $(basename $page) ==="
  grep -oE "\[\[[a-z0-9-]+(\|[^\]]+)?\]\]" "$page" | sed 's/\[\[//; s/|.*$//' | while read slug; do
    found=$(find concepts/ comparisons/ entities/ _meta/ -name "$slug.md" 2>/dev/null | head -1)
    [ -z "$found" ] && echo "  MISSING: [[$slug]]"
  done
done
```

### Phase 6: Tag Taxonomy Correction (im Fehlerfall)

Wenn Phase 5 einen inkorrekten Tag findet:

```bash
# 1. Korrekten Tag aus SCHEMA.md finden
grep "^- \`" ~/wiki/SCHEMA.md | grep -i "<stichwort>"
# 2. In der Page patchen
patch(
  path="concepts/<page>.md",
  old_string="tags: [..., <falscher_tag>, ...]",
  new_string="tags: [..., <korrekter_tag>, ...]"
)
# 3. Re-run Phase 5
```

**Beispiel aus der Praxis (2026-07-17):**
`tags: [..., system, ...]` → `system` existiert nicht als Tag.
SCHEMA.md hat `systems`. Fix: `tags: [..., systems, ...]`.

## Häufige Fehler

| Fehler | Symptom | Fix |
|---|---|---|
| Slug mit Punkt | `hermes-v7-repo-starter-node-express-v0` | Punkt → Bindestrich im Frontmatter-Title |
| Tag nicht in Taxonomie | `grep <tag> SCHEMA.md` = empty | Korrekten Tag aus 65-Tag-Katalog suchen |
| Provenance-Marker vergessen | Paragraph hat keine `^[raw/...]` Quelle | Nachtragen, sonst weiss niemand woher die Info kommt |
| Code erfunden (nicht verbatim) | Code sieht "zu sauber" aus, hat keine Source-Kennung | **Nicht machen.** Immer aus Source kopieren. Lieber leer lassen. |
| Quickstart zu groß | 155 MB → würde Wiki aufblähen | Nur Topologie scannen, `NICHT KOPIERT` im Raw-Artikel vermerken |
| Wikilink auf sich selbst | `[[hermes-webui-skills-bundle|...]]` im selben File | Rausnehmen |
| Patch auf veralteten index.md Stand | "Found 2 matches" oder Sibling-Warning | Re-read + erneut patchen |

## Vergleich: Sequential vs. Parallel

| Aspekt | Sequential (diese Ref) | Parallel (Scout-Pattern) |
|---|---|---|
| Quellen pro Session | 1–3 | 10–50 |
| Context-Last | Niedrig (du siehst alles) | Hoch (Subagenten brauchen Context) |
| Fehlerrate | Niedrig (du kontrollierst) | Mittel (Race-Conditions, Duplikate) |
| Geschwindigkeit | 1× | 3–5× |
| Wann | Präzision > Geschwindigkeit | Speed > Perfektion |
| Code-Verbatim | Ja, direkt aus Source | Scouts müssen kontext bekommen |
| Race-Conditions auf index.md | Selten (1 Agent) | Häufig (muss explizit behandelt werden) |
