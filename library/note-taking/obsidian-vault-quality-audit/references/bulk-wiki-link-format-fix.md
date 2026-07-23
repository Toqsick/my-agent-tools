# Bulk Wiki-Link Format Fix — Vault-Methodik

**Referenz für Pattern 12 (einheitliches Formatierungsproblem in Wiki-Links)**

## Overview

Wenn Wiki-Links im Vault ein **systematisches Formatierungsproblem** haben — z.B.
fälschliche Spaces statt Hyphens in Dateinamen (`[[GreyHack - Hacking Cookbook 2026-07-14]]`
statt `[[GreyHack-Hacking-Cookbook-2026-07-14]]`) — ist ein Bulk-Fix mit Sub-Biene-Verifikation
der richtige Ansatz. Der Workflow ist **nicht auf Spaced-Hyphens beschränkt**: beliebige
Format-Migrationen sind möglich (Groß-/Kleinschreibung, veraltete Präfixe, etc.).

**Abgrenzung zu Pattern 11b (Audit-Report Drift):**
- Pattern 11b patcht **numerische Werte** basierend auf einem Audit-Bericht
- Pattern 12 transformiert **String-Formate in Wiki-Links** nach einer festen Transformationsregel, ohne externen Report

## 6-Phasen-Workflow

### Phase 1 — Inventory (read-only)

Finde den exakten Umfang des Formatierungsproblems mit zwei search_files-Durchgängen:

```bash
# Breiter Scan: Alle Wiki-Links die Spaces um Bindestriche enthalten
rg -n '\[\[Grey(Hack|Script)\s+-\s+' /path/to/vault/

# Enger Scan: Mit konkretem Datum-Filter (zeigt exaktes Pattern)
rg -n '\[\[Grey(Hack|Script)\s+-\s+[^\]]+2026-07-14\]\]' /path/to/vault/

# Verteilung pro Datei (--count-only)
rg -c '\[\[Grey(Hack|Script)\s+-\s+' /path/to/vault/
```

**Dokumentiere:**
- Anzahl betroffener Dateien
- Anzahl kaputter Links
- Genauer Regex für altes Pattern
- Genauer Regex für neues (erwartetes) Pattern
- Edge-Case-Varianten (Links ohne Space vor Datum, etc.)

### Phase 2 — Fix-Script (Python, via write_file + terminal)

Schreibe ein Python-Script statt Bash-sed — das erlaubt:
- Komplexe Regex mit Named Groups
- Edge-Case-Handling (double-hyphen prevention)
- Kontrollierten Dry-Run vor echtem Fix
- Einfache Verifikation der gemachten Änderungen

**Wichtige Edge-Cases (Proven 2026-07-14):**
1. **Double-Hyphen Prevention:** Der Regex-Match kann einen Trailing-Hyphen enthalten
   wenn das ursprüngliche Format bereits einen Bindestrich vor dem Datum hatte. Beispiel:
   `[[GreyHack - Mission-Reports-Index-2026-07-14]]` → nach Replace ohne `strip("-")`
   wird `[[GreyHack-Mission-Reports-Index--2026-07-14]]`. **Lösung:** `middle.strip("-")`
   vor dem Join.

2. **Regex-Reihenfolge:** Beginne mit dem ENGEN Pattern (z.B. Date-Filter) und
   erweitere erst wenn nicht alle Links getroffen werden. Der umgekehrte Weg
   (breit → eng) führt zu unerwarteten Matches.

3. **Date-Literal ohne Space:** Manche Links haben die Form
   `[[GreyHack - X-Y-Z-2026-07-14]]` (ohne Space vor dem Datum).
   Dein Regex MUSS `\s*2026-07-14` verwenden (optionales Whitespace), nicht `\s+2026-07-14`.

**Template:**

```python
#!/usr/bin/env python3
import re, json, pathlib

VAULT = pathlib.Path("/pfad/zum/vault")
LOG_PATH = pathlib.Path("/tmp/vault-fix/log.json")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Erster Durchlauf: Snapshot aller Vorkommen (wichtig für Phase 3!)
old_matches = []  # wird parallel beim Scan befüllt

def normalize(s: str) -> str:
    """Wandelt ein Formatierungsproblem in das korrekte Format um."""
    m = re.search(r"\[\[(Grey(?:Hack|Script))\s+-\s+([^\]\n]+?)\s*2026-07-14\]\]", s)
    if not m:
        return s
    prefix = m.group(1)
    middle = m.group(2).strip().strip("-")       # double-hyphen prevention!
    tokens = [t for t in re.split(r"\s+", middle) if t]
    return f"[[{prefix}-{'-'.join(tokens)}-2026-07-14]]"

# Phase 2a: Dry-Run (simuliert, schreibt nichts)
dry_run_log = []
for md_file in sorted(VAULT.rglob("*.md")):
    content = md_file.read_text(encoding="utf-8", errors="ignore")
    new_content = normalize(content)
    if new_content != content:
        dry_run_log.append({"file": str(md_file), "changes": len(re.findall(old_pattern, content))})

print(f"Dry-Run: {len(dry_run_log)} Dateien mit Änderungen")

# Phase 2b: Echter Fix
for md_file in sorted(VAULT.rglob("*.md")):
    content = md_file.read_text(encoding="utf-8", errors="ignore")
    new_content = normalize(content)
    if new_content != content:
        md_file.write_text(new_content, encoding="utf-8")
```

### Phase 3 — Patch Log (reconstructed from initial snapshot, NEVER accumulated during run)

Das kritischste Anti-Pattern aus der Praxis: **Wenn das Fix-Script die Log-Datei selbst
schreibt und mehrmals läuft, wird der Log jedes Mal überschrieben.** Stattdessen:

1. **Vor** dem Fix: initialen Snapshot aller kaputten Links via `search_files` speichern
   (in JSON, als Markdown-Tabelle, oder als Klartext-Liste)
2. **Nach** dem Fix: aus dem Snapshot + der bekannten Transformationslogik den finalen
   Log rekonstruieren (einmaliger Build-Lauf, kein Akkumulationsfehler)

**JSON-Log-Format:**

```json
[
  {
    "file": "/absoluter/pfad/Datei.md",
    "old_link": "[[GreyHack - X Y 2026-07-14]]",
    "new_link": "[[GreyHack-X-Y-2026-07-14]]",
    "line": 618
  }
]
```

**Pflichtfelder pro Eintrag:** `file`, `old_link`, `new_link`, `line`

### Phase 4 — Sub-Bee Verification (file-existence check)

Dispatch eine **leaf-subagent** mit diesem Briefing-Template:

> Du bist eine reine Lese-Biene — NICHTS patchen, NUR reporten.
>
> 1. Lies die JSON-Log-Datei unter `<LOG_PATH>`. Für jeden Eintrag gibt `new_link` den
>    erwarteten Link an (z.B. `[[GreyHack-Mission-Reports-Index-2026-07-14]]`).
>    Der entsprechende Dateiname ist `<link-target>.md` (alles innerhalb der `[[ ]]` + `.md`).
>
> 2. Suche jede dieser Dateien im Vault unter `<VAULT_PATH>` mit:
>    `find /path/to/vault -type f -name "<Filename>"`
>
> 3. Schreibe die Ergebnisse als Markdown-Tabelle nach `<OUTPUT_PATH>`. Spalten:
>    - Link (der new_link)
>    - File existiert? (`✅ ja` oder `❌ nein`)
>    - Pfad (absoluter Pfad oder `—`)
>
> 4. Gruppiere die Tabelle nach referenzierender Quelldatei (erste Referenz = Section).
>    Dedupliziere so dass jeder eindeutige Link genau einmal erscheint (mit allen
>    referenzierenden Quelldateien als Subtext).
>
> 5. Nach dem Schreiben: `ls -la <OUTPUT_PATH>` zur Verifikation ausführen.
>
> **Self-Report am Ende:**
> - Anzahl eindeutiger Links geprüft
> - Anzahl vorhanden (`✅ ja`)
> - Anzahl fehlend (`❌ nein`)
> - Liste der fehlenden Dateinamen

**Verifikation nach Rückkehr:** `cat <OUTPUT_PATH>` und gegenchecken ob die Anzahl
fehlender Dateien plausibel ist (nicht >20% aller gecheckten Links).

### Phase 5 — Residual-Correction

Wenn die Sub-Bee fehlende Zieldateien meldet, gibt es zwei Möglichkeiten:

| Fall | Indiz | Aktion |
|------|-------|--------|
| **Target wirklich fehlt** | Datei existiert weder mit Space- noch mit Hyphen-Name | Note neu anlegen ODER Link auf existierende Note umbiegen |
| **Link-Formatierung falsch** | Datei existiert mit Space-Name (z.B. `GreyHack - Mission-Reports-Index-2026-07-14.md`), der Hyphen-Link zeigt ins Leere | Entweder Datei umbenennen (mit grep-Kontrolle ob andere Links auf den Space-Namen zeigen) ODER den Bulk-Fix-Rollback machen |

**Rollback-Strategie (nur wenn nötig):**
- Aus dem JSON-Log alte Links wiederherstellen (`search_files` auf `new_link` → ersetzen mit `old_link`)
- Datei-Umbenennung per `mv` auf dem Filesystem

### Phase 6 — Final Verification

Drei unabhängige Checks:

```bash
# Check A: Altes Pattern = 0 Treffer
search_files(pattern="Altes_Pattern_Regex", path="/vault", output_mode="count")
# Erwartet: {"total_count": 0}

# Check B: Double-Hyphen-Artefakte = 0 Treffer (wenn relevant)
search_files(pattern="--2026-07-14", path="/vault", output_mode="count")
# Erwartet: {"total_count": 0}

# Check C: Neues Pattern vorhanden (mindestens so viele wie ursprüngliche kaputte Links)
search_files(pattern="Neues_Pattern_Regex", path="/vault")
# Erwartet: mindestens total_count >= Anzahl ursprünglicher kaputter Links
```

## Pitfalls

| # | Pitfall | Mitigation |
|---|---------|------------|
| 1 | **JSON-Log-Overwrite** bei Mehrfachlauf des Fix-Scripts | Log NACH dem Fix aus initialem Snapshot rekonstruieren, nicht während des Laufs akkumulieren |
| 2 | **Double-Hyphen** (`Index--2026-07-14`) wenn die Mitte bereits einen Trailing-Hyphen hatte | `middle.strip("-")` vor dem Join |
| 3 | **Regex zu eng** erwischt nicht alle kaputten Links | Erst mit engem Pattern scannen, dann erweitern (Date-Literal ohne Space vor Datum) |
| 4 | **Sub-Biene patcht statt zu lesen** | Briefing EXPLIZIT sagen: "NUR reporten, NICHTS editieren" |
| 5 | **Sub-Biene-Output nicht verifiziert** | Nach Rückkehr `cat` / `ls -la` auf das Output-File — Self-Reports können lügen |
| 6 | **Kein initialer Snapshot** → kein vollständiger Patch-Log vorzeigbar | Vor Phase 2 einen vollständigen Snapshot speichern (search_files + redirect) |
| 7 | **`replace_all=true` im patch-Tool** matcht zu breit | Jede Datei einzeln mit `patch` (old_string→new_string) oder via Python-Script fixen |
| 8 | **Missings werden ignoriert** weil "es sind ja nur 2 von 17" | Jede fehlende Zieldatei muss kategorisiert werden (fehlt wirklich? Falscher Link?) |

## Sub-Bee-Briefing-Template

Siehe Phase 4 oben. Das Briefing MUSS enthalten:
- **Rollen-Constraint:** `role='leaf'` (keine delegation möglich)
- **Exakte Pfade:** Vault-Absolutpfad, Log-Datei-Pfad, Output-Datei-Pfad
- **Dateiformat:** `new_link` → Target-File = Text in `[[...]]` + `.md`
- **Deduplizierung:** Jeder eindeutige Link einmal + alle referenzierenden Quelldateien als Kontext
- **Verifikationsschritt:** `ls -la` auf Output-File nach dem Schreiben

## Proven Example (2026-07-14)

| Metrik | Wert |
|--------|------|
| Aufgabe | Spaces → Hyphens in Wiki-Links mit Datum `2026-07-14` |
| Inventory | 17 kaputte Links in 7 Dateien (6 in GreyHack/, 1 in Gaming/) |
| Edge-Case 1 | `[[GreyHack - Mission-Reports-Index-2026-07-14]]` (Space vor Datum = NEIN) |
| Edge-Case 2 | `[[GreyHack - Mission-Reports-Index-2026-07-14]]` (Trailing-Hyphen vor Datum) |
| Fix-Methode | Python-Script mit `strip("-")` + regex-basiertem Normalizer |
| Sub-Bee-Run | 6 unique Links geprüft, 4 vorhanden, 2 fehlend |
| Missing 1 | `GreyHack-Mission-Reports-Index-2026-07-14.md` → existiert nur mit Spaces |
| Missing 2 | `GreyHack-Scripting-Libraries-2026-07-14.md` → existiert als anderer Titel |
| Log | `/tmp/vault-fix-alpha/1784063962.json` (17 Einträge, valide JSON) |
| Verifikation | 0 alte Patterns, 0 double-hyphen-Artefakte, neues Pattern ≥ 17 Treffer |
| Total Aufrufe | 1 Sub-Biene (leaf, 83s, 6 API-Calls) + ~25 eig. Tool-Calls |