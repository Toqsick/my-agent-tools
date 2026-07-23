---
name: wiki-corpus-lint-runner
description: 'Use when user asks to run a wiki or documentation corpus lint across MANY markdown files (e.g. "QA-Linter: pruefe alle Wiki-Pages auf Format + Style"), apply format/style rules uniformly across a flat MkDocs/Hugo/wiki repo, or audit 50+ MD files for em-dashes, mid-sentence bold, broken cross-links, oversized pages, and inconsistent metadata. NOT for single-file humanization (→ quality-gate-runner), Obsidian vault link audits (→ obsidian-vault-quality-audit), or source-code linting.'
version: 1.0.0
author: Hermes Agent
license: MIT
lane: koenigin
triggers:
- wiki lint
- corpus lint
- markdown lint corpus
- alle wiki-pages prüfen
- format check wiki
- style audit wiki
- em-dash audit wiki
- cross-link validation
- stand-date einheitlich
trigger_keywords: ['wiki', 'across', 'files', 'pages', 'format']
keywords: ['wiki', 'across', 'files', 'pages', 'format']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['wiki-scout-ingest', 'bulk-readme-to-wiki-pages']
---

# Wiki Corpus Lint Runner

> Skaliert die 5 Quality-Gates aus `quality-gate-runner` von einer einzelnen Datei
> auf einen **gesamten Wiki-Korpus** (50+ MD-Dateien), ergänzt um Cross-Link-Validierung,
> Page-Size-Limit, Stand-Datum-Konsistenz und einen Auto-Fix-Workflow.

## Wann anwenden

- User sagt: "QA-Linter: pruefe alle Wiki-Pages", "lint alle *.md", "Audit Format + Style", "wiki lint"
- Korpus ab ~20+ Markdown-Files (darunter → direkt `quality-gate-runner` Single-File-Mode)
- Flat markdown wiki (MkDocs, Hugo, Docusaurus, GitHub-wiki) — NICHT Obsidian-`[[...]]`-Syntax
- Spec umfasst mehrere Regeln (Em-Dash, Boldface, Cross-Links, Size, Stand-Datum, etc.)
- Auto-Fix gewünscht (nicht nur Report)

NICHT für: einzelne Humanisierungs-Pass (→ `quality-gate-runner`), Obsidian-Vault-Links (→ `obsidian-vault-quality-audit`), Quellcode-Lint.

## Ausführung (5-Phasen)

### Phase 1 — Inventur

```bash
# Korpus-Pfad bestätigen
ls /path/to/wiki/*.md | wc -l

# Dateien-Liste (für Diff gegen existierende Pages)
ls *.md | sed 's/\.md$//' | sort -u > /tmp/_pages.txt
```

Erwartung: 20-500 Files. Mehr als 1000 → Skript statt Shell-Calls, sonst Token-Explosion.

### Phase 2 — Cross-Link-Resolution (KORPUS-SPEZIFISCH)

```bash
# Alle Cross-Page-Targets extrahieren (nicht http, nicht Anchor)
grep -oE '\]\([^)]+\)' *.md | grep -v 'http' | sed 's/.*](//' | tr -d ')' | sort -u > /tmp/_targets.txt

# Broken-Diff: Targets, die nicht im Korpus existieren (minus #anchors minus Home-Alias)
while IFS= read -r t; do
  if [ "${t#\#}" != "$t" ]; then continue; fi          # Anchor überspringen
  if [ "$t" = "Home" ]; then continue; fi               # Index-Alias häufig
  if ! grep -qxF "$t" /tmp/_pages.txt; then
    echo "BROKEN: $t"
  fi
done < /tmp/_targets.txt
```

**Wichtig:** Anker-Links (`[Core](#core)` in `Tools-Overview.md`) sind Page-intern — NICHT als broken werten. Sie matchen Section-Headings derselben Datei.

### Phase 3 — Quality-Gates (Regex pro Check)

```bash
# 1. Em-Dashes (—)
grep -c '—' *.md | grep -v ':0$'

# 2. En-Dashes (–)
grep -c '–' *.md | grep -v ':0$'

# 3. Mid-Sentence Boldface (\S**...** außerhalb von Callout-Labels)
grep -cPn '\S\*\*[^*]+\*\*' *.md | grep -v ':0$'

# 4. Page-Size > 300 Zeilen
for f in *.md; do l=$(wc -l < "$f"); [ "$l" -gt 300 ] && echo "$f: $l"; done

# 5. Stand-Datum-Konsistenz (z.B. **Stand:** YYYY-MM-DD)
for f in *.md; do
  if [[ "$f" == _* ]]; then continue; fi   # Partial-Includes überspringen
  if ! grep -qE 'Stand:.*2026-07-22' "$f"; then echo "MISSING: $f"; fi
done
```

### Phase 4 — Auto-Fix (Pitfalls siehe unten)

Pro Check-Typ eigene Strategie:
- Em-Dash: `perl -i -pe 's/\s+\xe2\x80\x94\s+/, /g'` für Mid-Sentence, manuell für Tabellen-Platzhalter
- Mid-Sentence-Bold: `patch` mit Unique-Context (kein `replace_all`)
- Cross-Links: `patch` mit Unique-Context pro Link
- Stand-Datum: `patch` mit Unique-Anchor pro Datei

**Bericht schreiben als** `_Audit_Lint.md` mit Tabelle: Check | Vorher | Nachher | Status.

### Phase 5 — Re-Verification

Alle 5 Checks erneut laufen lassen. Vorher-Werte müssen 0 sein (in Wiki-Pages, ohne `_Audit_*`).

## Pitfalls (KORPUS-SPEZIFISCH)

| # | Pitfall | Mitigation |
|---|---------|------------|
| 1 | `perl -i -pe` Regex `s/ — /, /` ersetzt auch `\| — \|` Tabellen-Platzhalter zu `\|, \|` weil `\s+ — \s+` matched | Ersatz-Strategie: Mid-Sentence-Variante zuerst (`\s+ — \s+` → `, `), Tabellen-Platzhalter separat (`\| — \|` → `\| keine \|`). Zwei separate Regex-Pass, sonst zerstörte Tabellen. |
| 2 | Multi-line `terminal`-Befehle werden von der Shell-Blocklist rejected ("BLOCKED hardline") | Statt Heredoc einzelne Befehle aufteilen. Für Bulk-Replace: `perl -i -pe 's/X/Y/g' file` in EINER Zeile. |
| 3 | Mid-Sentence-Bold-Regex `\S\*\*[^*]+\*\*` schlägt auch bei `**Label:** value` in `>`-Callouts zu | Das ist KEIN Mid-Sentence-Bold — strukturiertes Metadaten-Label im Blockquote. Spec sagt "mid-prose", nicht "label token". Akzeptabel, im Report dokumentieren. |
| 4 | 5 Cross-Links mit demselben `Tool-XXX` Prefix haben `_` statt `-` (Underscore/Hyphen-Mismatch) | Pro Link einzeln `patch`en mit Unique-Context. NICHT `replace_all` weil sonst auch andere Texte mit `Tool-fix_perms`-Erwähnung kaputt gehen. |
| 5 | 4 Pages ohne `Stand:`-Header (Stub-Pages) | Bei Stub/Template-Pages manuell ergänzen mit `patch` (Header + Leerzeile + Datum), nicht `write_file` (würde ganzen Inhalt überschreiben). |
| 6 | Partial-Include-Files (`_Sidebar.md`, `_Footer.md`) brauchen keinen `Stand:`-Header | Convention-basiert überspringen: `if [[ "$f" == _* ]]; then continue; fi` |
| 7 | Report-Datei (`_Audit_Lint.md`) zählt sich selbst bei Verification mit | In Re-Verification `_Audit*` ausschließen — sonst Induktion. |
| 8 | Em-Dash-Statistik zählt Audit-Files mit | Gleicher Filter: `_Audit_*.md` aus Endprüfung ausschließen. |

## Spec-Threshold (anpassbar pro Repo)

| Check | Default | Anpassung |
|-------|---------|-----------|
| Em-Dashes | 0 | Stil-Frage; manche Repos akzeptieren 1 |
| En-Dashes | 0 | Strenger |
| Mid-Sentence-Bold | 0 (außer Callout-Labels) | Akzeptiert wenn in Metadaten-Header |
| Page-Size | ≤ 300 Zeilen | Höher für Reference-Pages |
| Stand-Datum | einheitlich `YYYY-MM-DD` | Format wählbar |
| Cross-Link-Validity | 100% | Aliases (`Home` → `INDEX`) müssen als gültig definiert sein |

## Cross-Reference

- `quality-gate-runner` — Single-File-Gates (EmDash, Boldface, InlineHdr, NegParallel, WikiLink-Count) als Basis
- `daily-briefing` §2.8 — Inline-Quality-Gate Spec für Daily-Notes
- `obsidian-vault-quality-audit` — Obsidian-`[[...]]`-Pendant, Pattern 12 für Bulk-Link-Format-Fix
- `patch` (Tool) — Targeted Edits mit Unique-Context
- `write_file` — Nur für neue Audit-Reports, nie auf existierende Inhalte ohne Diff-Vergleich
- `references/2026-07-22-greyscripts-wiki-lint.md` — Erstes echte Anwendungs-Session-Detail (58 MD-Files, 11 Edits, komplette Recipe-Liste + Pitfalls)

## Verification Checklist

Nach Auto-Fix:

```bash
# 1. Alle Korpus-Checks wieder grün
grep -c '—' *.md | grep -v ':0$' | grep -v '_Audit'   # leer
grep -c '–' *.md | grep -v ':0$' | grep -v '_Audit'   # leer
grep -cPn '\S\*\*[^*]+\*\*' *.md | grep -v ':0$' | grep -v '_Audit'  # nur akzeptable Callout-Labels
for f in *.md; do l=$(wc -l < "$f"); [ "$l" -gt 300 ] && echo "$f"; done  # leer
for f in *.md; do
  if [[ "$f" == _* ]]; then continue; fi
  grep -qE 'Stand:.*<DATUM>' "$f" || echo "MISSING: $f"
done  # leer
```

Wenn Output in einem Check: Fix-Pass 2. Wenn mehrere Dimensionen betroffen: Lieber nochmal manuell reviewen als blind weiter-fix-en.
