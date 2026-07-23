---
name: skill-polisher
description: |
  Use when running batch quality improvements on the skill library: frontmatter fixes, lint passes, dead-link cleanup, BOM/chmod bug remediation, or duplicate detection across skills.
  NOT for editing a single skill by hand, end-user skill usage, or creating new skills — use skill_manage / skill_creator for those.
  Batch quality-improvement CLI for the Hermes skill library (frontmatter, lint, dead links, duplicates).
version: 1.0.0
author: Hermes
related_skills:
- queen-bee-schwarm-dispatch
- plan-review-and-orchestrate
metadata:
  hermes:
    tags:
    - meta
    - maintenance
    - audit
    - skills
    agent: Verifier
    routing_hint: Audit and remediate Hermes skill library — find BOM bugs, chmod issues, description overflow, duplicates. Single CLI for all skill maintenance tasks.
license: MIT
trigger_keywords: ['skill', 'batch', 'quality', 'library', 'frontmatter']
keywords: ['skill', 'batch', 'quality', 'library', 'frontmatter']
last_curated: '2026-07-23'
curated_by: 'Yuno'
---


# Skill-Polisher

**Single-CLI meta-skill for Hermes skill maintenance.** Detects and remediates common production bugs across all 480+ skills in `~/.hermes/skills/`:

1. **BOM bugs** — Scripts reading files with `encoding="utf-8"` instead of `utf-8-sig` (silently breaks when files have Windows-style BOM)
2. **chmod bugs** — Shebang-scripts without `+x` permission (must be invoked via `python3 script.py` instead of `./script.py`)
3. **Description overflow** — SKILL.md descriptions longer than 60 chars (Hermes system-prompt index truncates to 60 chars, anything past = invisible)
4. **Production duplicates** — Byte-identical scripts in 2+ skills (drift risk)
5. **Frontmatter issues** — Missing `name`/`description`/`version`/`author`, descriptions without trailing period, descriptions over 60 chars

## When to Use

- After pulling a new skill bundle (bundles often re-create known bugs)
- During quarterly skill maintenance (Q1/Q2/Q3/Q4 audit cycles)
- When a skill mysteriously fails to load (might be BOM or chmod issue)
- Before publishing a skill bundle (verify quality before release)
- Whenever user says "audit skills", "fix skill bugs", "polish skills", "skill maintenance"

## Prerequisites

- Python 3.11+ with `pyyaml` (or system Python with `python3 -c "import yaml"` works)
- Read/write access to `~/.hermes/skills/`
- Dry-run mode by default for safety — pass `--apply` to make changes (where supported)

## How to Run

Single CLI script with 6 subcommands:

```bash
# 1. Audit (read-only, all checks)
python3 ~/.hermes/skills/meta/skill-polisher/scripts/skill_polisher.py audit

# 2. Fix BOM bugs
python3 ~/.hermes/skills/meta/skill-polisher/scripts/skill_polisher.py fix-bom [--dry-run]

# 3. Fix chmod (make CLI scripts executable)
python3 ~/.hermes/skills/meta/skill-polisher/scripts/skill_polisher.py fix-chmod [--dry-run]

# 4. Trim SKILL.md descriptions to <=60 chars
python3 ~/.hermes/skills/meta/skill-polisher/scripts/skill_polisher.py fix-description [--dry-run]

# 5. Find production duplicates
python3 ~/.hermes/skills/meta/skill-polisher/scripts/skill_polisher.py find-duplicates

# 6. Validate frontmatter (detailed check)
python3 ~/.hermes/skills/meta/skill-polisher/scripts/skill_polisher.py validate-fm
```

## Quick Reference

| Subcommand | What it does | Modifies? |
|---|---|---|
| `audit` | Runs all 5 checks, prints summary report | NO (read-only) |
| `fix-bom` | Migrates `utf-8` → `utf-8-sig` in read-mode calls | YES (unless `--dry-run`) |
| `fix-chmod` | Adds `+x` to shebang-scripts | YES (unless `--dry-run`) |
| `fix-description` | Trims descriptions >60 chars heuristically | YES (unless `--dry-run`) |
| `find-duplicates` | Lists byte-identical script groups | NO (read-only) |
| `validate-fm` | Reports all frontmatter issues per-file | NO (read-only) |

## Procedure

### Recommended Workflow

1. **Audit first**: `python3 skill_polisher.py audit`
   - Shows all 5 issue categories at once
   - Tells you which `fix-*` command to run

2. **Dry-run fix commands**: Always run with `--dry-run` first
   - See what would change
   - Verify the heuristic is sane (especially for `fix-description`)

3. **Apply fixes**: Run without `--dry-run` after reviewing

4. **Re-audit**: `python3 skill_polisher.py audit` again to confirm 0 issues

5. **Commit changes**: Git diff, review, commit per skill

### Special Notes

- **Self-exclusion**: The polisher skips itself (`meta/skill-polisher/scripts/skill_polisher.py`) when checking BOM, since its own utf-8-sig reads are intentional BOM-stripping.
- **`.archive/` exclusion**: Historical snapshots in `~/.hermes/skills/.archive/` are never touched.
- **`fix-description` heuristic**: Replaces verbose descriptions with the first sentence or pre-colon phrase, truncated to 60 chars. **Always review the output before applying** — the heuristic may produce awkward phrasings.

## Trigger-Coverage KPI

| Metrik | Wert | Ziel | Status |
|---|---|---|---|
| Skills mit "Use when" Trigger | 86/299 (28%) | **40%+** | ⬆️ Braucht ~34 weitere Rewrites |
| Skills ohne Trigger-Phrase | 213/299 (71%) | <50% | ⬇️ Polish-Runde 3 Backlog |
| Descriptions <30 chars | 0 | 0 | ✅ |
| Ellipsis-Endings (... truncation bug) | 0 | 0 | ✅ (110 gefixt) |
| Descriptions 30-60 chars (ohne Trigger) | ~160 | <50 | ⬇️ Primary Pipeline |

**Nicht machen:** Die KPI nur für Master-Berichte messen. Jeder Polish-Cycle MUSS coverage-scan als ersten Schritt haben (vorher/nachher Vergleich).

**Referenz:** `references/trigger-coverage-kpi.md` — vollständige Messmethodik + Kategorisierung der 213 Skills ohne Trigger.

### Semantic Description Rewrite (Use when...)

Der `fix-description` Subcommand trimmt nur auf <=60 Zeichen. Fuer **qualitative Verbesserung** (kurze/triviale Descriptions in Use-when-Trigger umwandeln) gibt es einen separaten Workflow:

**Wann:** Skills mit Description 30-80 chars, die NICHT mit Use when beginnen, aber einen klaren, wiederholbaren Zweck haben.

**Workflow (Queen bestimmt das, nicht fix-description CLI):**
1. **Kandidaten identifizieren**: len(desc) >= 30 AND len(desc) <= 80 AND NOT desc.startswith('Use when')
2. **Nach Kategorie priorisieren**: devops > orchestration > software-development > github > productivity > meta > rest
3. **Rewrite-Logik pro Kandidat**: Use when [Verb]ing [Objekt] [Kontext/Scope]. — praezise, aktiv, kein Fuellwort
4. **Anwenden via String-Patching** (niemals YAML-Roundtrip — siehe Pitfall)
5. **YAML-Parse-Verify nach jedem Patch**
6. **Cross-Check mit Biene P1** (optional): Queen dispatcht eine Verify-Biene die die Rewrites gegen Live-Filesystem checkt. Sinnvoll bei >25 Rewrites pro Welle.

**Validierung (2026-07-16):** 50 Skills in einer Queen-Welle rewrited. 43/50 automatisch matchbar, 7/50 hatten Single-Quoted YAML (siehe Pitfall unten). Die dispatchte Biene P1 bestätigte alle 50 semantisch korrekt.

**Trigger-Coverage nach Rewrite:** 83/299 Skills (27%) mit Use when-Trigger. Ziel: 40%+.

**Nicht machen:** fix-description Subcommand fuer Rewrites nutzen — das Subcommand trimmt nur. Queen-Direct String-Patching verwenden.

**Queen Pre-Execute Pattern (validiert 2026-07-16):** Bei deterministischen Rewrites macht die Königin die 50+ Patches selbst während die Bienen noch die Verify-Phase vorbereiten. Siehe `queen-bee-schwarm-dispatch` → "Queen Pre-Execute While Bees Scout".

## Broken-Ref Cleanup Protocol

**Problem:** Skills haben broken references auf nicht-existente `references/`, `scripts/`, `templates/` Dateien. Drei Kategorien mit unterschiedlichen Fix-Strategien:

| Kategorie | Count (2026-07-16) | Bedeutung | Fix |
|---|---|---|---|
| BUNDLE_MISSING | 151 | Skill hat kein references/ oder scripts/ Dir | Dirs anlegen + `.gitkeep` ODER Ref aus SKILL.md entfernen |
| FILE_MISSING | 110 | Dir existiert, einzelne Datei fehlt | Stub-Datei erstellen ODER Ref entfernen |
| TEMPLATE_PLACEHOLDER | 4 | Ref enthält `example`/`<name>`/`DATE` | Ignorieren (Platzhalter für User) |

**Workflow (Königin führt aus, Biene P2 kategorisiert):**

1. **Welle 1: Scout-Biene P2 dispatchen** (read-only, kategorisiert alle broken refs in die 3 Kategorien)
2. **Welle 1: Königin erstellt Parallel-Baseline** (eigener Live-Scan, validiert Bienen-Ergebnisse)
3. **P0: Hot-Spot Skills mit ≥3 Broken Refs** — Dirs anlegen (mkdir + .gitkeep) um BUNDLE_MISSING zu heilen. SKILL.md Body-Refs bleiben intakt (Doku-Kontext), aber die Pfade werden valid.
4. **P1: FILE_MISSING prüfen** — Bundle existiert aber Einzelfile fehlt → entscheiden ob Stub (für erwartete Erweiterung) oder Ref entfernen (für verwaiste Doku)
5. **P2: Bulk-BUNDLE-MISSING** — Bulk-Script für Single-File-Skills mit Refs auf nicht-existente Dirs. Entweder alle Dirs anlegen ODER alle Refs aus SKILL.md entfernen

**Validierung (2026-07-16):** 9 Bundle-Skills mit Dirs versehen, 1 Typo (scripts/scripts/) gefixt. 265 refs kategorisiert (exkl. Archive).

**Scanner-Script für Bulk-Verify:**
```bash
python3 -c "
import os, re, glob
home = os.path.expanduser('~')
broken = []
for f in glob.glob(f'{home}/.hermes/skills/**/SKILL.md', recursive=True):
    if '.archive/' in f: continue
    d = os.path.dirname(f)
    with open(f) as fh:
        refs = re.findall(r'(?:references|scripts|assets|templates)/[\w./-]+', fh.read())
    for r in set(refs):
        rp = os.path.join(d, r)
        if not os.path.exists(rp) and not os.path.exists(r):
            if not re.search(r'(<|>|{|}|foo|bar|example|DATE)', r):
                broken.append((f,r))
print(f'Real broken refs: {len(broken)}')
"
```

**Referenz:** `references/broken-ref-cleanup-protocol.md` — vollständige Kategorisierung, P0-P2 Empfehlungen, Bulk-Script-Vorlage.

## 2026-07-16 Combine Phase (Audit + Polish + Ellipsis-Batch = 193 Fixes)

**Erkenntnis:** Die Audit-Phase (Morgen), Polish-Phase (Nachmittag) und der Ellipsis-Batch-Fix (110 Skills) ergaben zusammen **193 Fixes** in ~26 Minuten Wall-Time. Der Ellipsis-Bug war ein systematischer Fehler aus einem frueheren `fix-description` Lauf — keine Biene hatte ihn in Welle 1 gefunden, erst die Verify-Bienen in Welle 2.

| Runde | Fixes | Dauer | Methode |
|---|---|---|---|
| Audit-Runde (Welle 1+2) | 43 | ~10 Min | Standard Queen-Bee (4 Scout → Queen-Verify → 2 Verify) |
| Polish-Runde (Welle 1+2) | 64 | ~8 Min | Queen Pre-Execute (Königin machte 50 Rewrites selbst) |
| Ellipsis-Batch (Welle 2 Verify → Hotfix) | 86 | ~8 Min | 107 simple strip + 3 manual + Verify-Bees entdeckten Problem |

**Post-Polish KPI (live verify 2026-07-16, nach Ellipsis-Batch-Fix):**
| Metrik | Vorher | Nachher |
|---|---|---|
| YAML Parse Errors | 0 | 0 ✅ |
| Descriptions <30 chars | 0 | 0 ✅ |
| Descriptions >150 chars | 0 | 0 ✅ |
| Missing author/version/name | 0 | 0 ✅ |
| Shebang without +x | 0 | 0 ✅ |
| Python Syntax Errors | 0 | 0 ✅ |
| BOM read_text utf-8 | 3 | 0 ✅ |
| Ellipsis-Endings (... bug) | 110 | **0** ✅ |
| Missing period | 0 | 0 ✅ |
| Bundle-Dirs created | 0 | 9 ✅ |
| "Use when" Trigger | 83/299 | **86/299** (28%) ⚠️ |
| Broken Refs (real) | 285 | 283 ⚠️ |

**P2 Backlog (nächster Polish-Cycle):**
- 213 Skills ohne Trigger-Phrase (-> Polish-Runde 3)
- 283 Broken Refs (Bulk-Cleanup oder Stub-Generierung)
- 42 Monolithe >500 Zeilen (references/ Extraction)
- 11 Konsolidierungs-Kandidaten (Merge oder Abgrenzung)

**Referenz:** `queen-bee-schwarm-dispatch` → "Queen Pre-Execute While Bees Scout" für das Orchestrierungs-Muster. `references/skill-polish-2026-07-16.md` (dieser Bericht) als vollständiger Session-Report.

## Pitfalls

- **`fix-description` heuristic is imperfect**: For complex multi-feature skills, the auto-truncation may lose important keywords. Review each change before committing.
- **`fix-bom` only catches the most common patterns**: Custom file open patterns (e.g., `aiofiles.open`) are not auto-detected. Manual review may be needed.
- **`fix-chmod` is one-way**: Running it multiple times is idempotent (no harm) but doesn't undo an accidental +x on a library script (libraries have no shebang, so they're excluded).
- **Frontmatter validation is strict**: Some legacy skills may have intentionally non-conforming frontmatter. Use `validate-fm` as advisory, not as a hard gate.
- **Running on entire `~/.hermes/skills/` is safe** because of `.archive/` exclusion, but always commit before bulk operations.
- **⚠️ `yaml.safe_dump` / `yaml.dump` destroys YAML quoting (CRITICAL, 2026-07-15)**: The `fix-fm` subcommand originally used `yaml.safe_dump` to rewrite frontmatter after edits. This silently transforms single-quoted values (`'value'`) to double-quoted (`"value"`), drops flow-style mappings, and changes multiline `|`-style descriptions to block-scalar. A full `yaml.load → edit → yaml.dump` roundtrip corrupts ~40% of skill frontmatter. **Fix:** use regex-based **string patching** instead — parse the YAML frontmatter for validation, but apply fixes via targeted string replacements on the raw text. Always verify with `yaml.safe_load` AFTER the patch (not BEFORE→AFTER roundtrip). See `references/fix-fm-string-patching.md` for the proven approach.
- **False-positive classification matters (2026-07-15)**: A naive audit that flags every "missing period" without context will report 200+ issues in 400+ skills — but ~60% are false positives caused by:
  - **Quoted descriptions with trailing period** (`description: '"Full text with period."'`) — the period is inside the quotes, not at the YAML value end
  - **Multiline `|`-style descriptions ending with period** — YAML multiline already implies the trailing newline; the period before it doesn't count as missing
  - **Archive/backup exclusions** — `.archive/` skills aren't production and shouldn't be fixed
  - **Single-quote patterns** (`description: 'short'`) — period inside single quotes
  Always run the multi-pass filter (scan - FP classification - active-only filter - apply) before declaring results.

- **YAML Single-Quote Description bricht String-Patching (2026-07-16)**: Wenn eine Description als Single-Quoted String in YAML gespeichert ist (`description: 'Kurzer Text.'`), enthaelt der Raw-Text die einfachen Anfuehrungszeichen. String-Matching schlaegt dann fehl, obwohl der optische Eindruck identisch ist. **Erkennung:** `grep '^description:' SKILL.md` zeigt die RAW-Zeile. **Fix:** Vor dem Match beide Varianten pruefen (mit und ohne Quotes). Siehe `references/single-quote-description-pitfall.md`.

- **⚠️ Blinde `sed -i` auf Pattern-Matching-Code zerstoert Such-Strings (CRITICAL, 2026-07-16)**: Ein `sed -i 's/encoding="utf-8"/encoding="utf-8-sig"/g'` auf `skill_polisher.py` ersetzte ALLE Vorkommen — auch in `re.search`-Pattern-Strings, wo `encoding="utf-8"` den **Such-Pattern** (was gefunden werden soll) beschreibt, nicht den Read-Modus. Der Fix-BOM-Scanner suchte anschließend nach dem bereits gefixten Wert und fand nichts mehr.
  - **Symptom:** `fix-bom` Subcommand findet 0 BOM-Bugs, weil der Such-Pattern nach dem Fix-Wert statt nach dem Fehler-Wert sucht.
  - **Root Cause:** `sed` hat keine Semantik — es ersetzt blind. Pattern-Matching-Strings (in `re.search`, `re.match`, `in`, `==`) sind OPFER des selben Replace-Befehls wie echte Read-Calls.
  - **Fix:** Manuelles Revert der Pattern-Matching-Strings zurück zum Original-Suchwert.
  - **Guard:** Vor jedem Batch-Replace via sed: `grep -n '<suchmuster>' <file>` um zu pruefen OB das Muster in Code-Kontexten (nicht Strings) vorkommt. Zwei-Klassen-Schema:
    1. **Read-Calls** (Lese-Operationen): `read_text(encoding="utf-8")` → **soll** ersetzt werden
    2. **Pattern-Matching-Strings** (Sucht nach Muster): `re.search(r'encoding="utf-8"', text)` → **darf NICHT** ersetzt werden
  - **Bessere Alternative (validiert 2026-07-16):** Python-String-Patching, das zwischen `read_text` und `re.search` unterscheidet. Siehe `references/sed-pattern-matching-regression.md`.
  - **Status:** verified (1 File, erfolgreich revertiert)

## Verification

After running fixes:

```bash
# Re-audit should show fewer/no issues
python3 skill_polisher.py audit

# Check specific skill that was changed
head -10 path/to/skill/SKILL.md
# → Description should now be <=60 chars, end with period

# Corruption check (PFLICHT nach Bulk-Fixes, 2026-07-15):
python3 -c "
import yaml, glob, sys, os
from pathlib import Path
home = Path.home()
errs = []
for pattern in ['*/*/SKILL.md', '*/*/*/SKILL.md']:
    for f in glob.glob(str(home / '.hermes/skills' / pattern)):
        with open(f) as fh:
            parts = fh.read().split('---', 2)
        if len(parts) < 2: continue
        try:
            yaml.safe_load(parts[1])
        except Exception as e:
            errs.append((f, str(e)))
if errs:
    for f, e in errs: print(f'❌ CORRUPTED: {f} — {e}')
    sys.exit(1)
else:
    print(f'✅ 0 corrupted files (checked {len(glob.glob(...))})')
"
```

Expected: `audit` reports only the categories you haven't fixed yet. 0 corrupted files.

## What this Audit Caught (2026-07-15)

First full run on the Hermes library:
- **194 SKILL.md files** had descriptions >60 chars (many like kanban-system-health were 1003 chars)
- **23 SKILL.md files** had frontmatter issues (missing author, no trailing period, etc.)
- After targeted fixes in Polish-Round-2: kanban-system-health description now 58 chars, all chmod issues resolved, BOM handled

### 2026-07-15: Mass Frontmatter Fix (fix-fm rewrite)

The `fix-fm` subcommand was rewritten to use **string patching** instead of YAML roundtrip. Applied to all 482 skills:
- **75 skills fixed** with string-patching fix-fm
- **111 individual fixes**: 48 missing period + 35 missing author + 21 missing version + 7 missing name
- **0 corrupted files** (verified via yaml.safe_load on all 482)
- **72 remaining active issues** (not fixable by string patching — require manual review)

Key technique learned: instead of `yaml.safe_load → edit → yaml.dump`, use:
1. `yaml.safe_load` for validation (detect what's missing)
2. Regex-based string replacement on raw text for fixes
3. `yaml.safe_load` again to verify the result is parseable

This meta-skill exists so the next bundle doesn't reintroduce these patterns.

## References

| File | Inhalt |
|---|---|
| `references/polymorphic-polish-pattern.md` | **2026-07-15:** Vollständige 4-Phasen-Polish-Methodik (Scope → Test → Audit → Fix+Verify). Konvergenz-Kriterium, Self-Exclusion-Regel, Encoding-Doppeltür-Pitfall. Aus 4 Polish-Runden destilliert. |
| `references/frontmatter-audit-refinement.md` | **2026-07-15:** Technique: 331 gemeldete Issues → nur 66 echte (265 False Positives durch YAML Multiline). Regex-Pattern + Multiline-Check + ruamel.yaml vs PyYAML. |
| `references/fix-fm-string-patching.md` | **2026-07-15:** String-Patching Technique statt YAML-Roundtrip für Frontmatter-Fixes. Implementierungs-Pattern, False-Positive-Klassifikation (263 flagged → 37 real), Edge Cases. |
| `references/trigger-coverage-kpi.md` | **2026-07-16:** Messmethodik für Use-when-Trigger-Coverage. Kategorisierung der 213 Skills ohne Trigger, Pipeline für Coverage-Verbesserung. |
| `references/broken-ref-cleanup-protocol.md` | **2026-07-16:** BROKEN_MISSING/FILE_MISSING/TEMPLATE-Kategorisierung, Top-20 Hot-Spots, Scanner-Script, Bulk-Dir-Anlage-Skript. |
| `references/single-quote-description-pitfall.md` | **2026-07-16:** YAML Single-Quote Description und deren Impact auf String-Patching. Erkennungs- und Fix-Methodik. |
| `references/sed-pattern-matching-regression.md` | **2026-07-16:** Sed-Replace kollidiert mit Code-Pattern-Matching-Strings. Python-Alternative: Zwei-Klassen-Ersetzung (Read-Calls vs Pattern-Strings). |