# Edge-Case Test Matrix — tiktok-design-assistant Validator

> Letzte Validierung: 2026-07-15 · **v0.4.0** (D-Serie + 2 Production-Bugs gefunden)
> Bash → Python Migration: Ja (4 Bugs im Bash-Validator gefunden)
> Gesamtzahl Self-Tests: **30** (v0.1.0: 9 → v0.2.0: +7 → v0.3.0: +9 D-Serie → v0.4.0: +2 + 3 Wiederholungen)
> Real-World-Impact: **2 Production-Bugs** (23 kaputte Posts in echten Daten entdeckt)

## Warum diese Matrix existiert

Der ursprüngliche Bash-Validator (`validate-design-kit.sh`) verwendete `awk -F','` für CSV-Parsing.
Bei der Polish-Iteration wurden 4 Bugs entdeckt, die nur durch Edge-Case-Tests auffielen.
**Diese Matrix dokumentiert ALLE getesteten Szenarien**, damit zukünftige Iterationen nicht bei Null anfangen
und Regressionen sofort erkennbar sind.

## Vollständige Test-Matrix (30 Self-Tests)

### Baseline (v0.1.0 — 9 Tests)

| # | Test | Typ | v0.1.0 | v0.2.0 | v0.4.0 | Exit-Code |
|---|---|---|---|---|---|---|
| 1 | Happy-Path Kreditkarten (10 Posts) | Happy | ✅ | ✅ | ✅ | 0 |
| 2 | Happy-Path Produktivität (10 Posts) | Happy | ✅ | ✅ | ✅ | 0 |
| 3 | Fehlendes brand-system JSON | Failure | ✅ | ✅ | ✅ | 1 |
| 4 | Fehlendes pitch-variants JSON | Failure | ✅ | ✅ | ✅ | 1 |
| 5 | Fehlendes CSV | Failure | ✅ | ✅ | ✅ | 1 |
| 6 | Fehlende Anleitung-MD | Failure | ✅ | ✅ | ✅ | 1 |
| 7 | Invalid JSON Syntax | Failure | ✅ | ✅ | ✅ | 1 |
| 8 | CSV < 11 columns | Failure | ✅ | ✅ | ✅ | 1 |
| 9 | CSV < 10 data rows | Failure | ✅ | ✅ | ✅ | 1 |

### C-Serie — Scharfschaltung (v0.2.0 — +7 Tests)

| # | Test | Typ | v0.2.0 | v0.4.0 | Exit |
|---|---|---|---|---|---|
| C1 | CSV mit 0 data rows (header only) | Failure | ✅ | ✅ | 1 |
| C2 | Empty pitch cells | Failure | ✅ | ✅ | 1 |
| C3 | CSV mit quoted fields (Caption, mit Komma) | Failure | ✅ **BUG FIX** | ✅ | 1 |
| C4 | Mixed valid+invalid rows (5 OK, 5 empty pitch) | Failure | ✅ | ✅ | 1 |
| C5 | Naked umlauts (ä,ö,ü,ß) in CSV | Failure | ✅ | ✅ | 1 |
| C6 | Brand-JSON missing required fields | Failure | ✅ **BUG FIX** | ✅ | 1 |
| C7 | Pitch-JSON missing target niche | Failure | ✅ **BUG FIX** | ✅ | 1 |
| C8 | Anleitung-MD leer (0 bytes) | Failure | ✅ | ✅ | 1 |
| C9 | Backward-Compat via Bash-Wrapper | Happy | ✅ | ✅ | 0 |

### D-Serie — Tiefenbohrung (v0.3.0 — +9 Tests)

| # | Test | Typ | v0.3.0 | v0.4.0 | Exit | Finding |
|---|---|---|---|---|---|---|
| D1 | LATIN-1 encoded CSV (Windows-Excel export) | Info | ✅ | ✅ | 0 | ⚠️ Silent: utf-8-sig decodiert 1-byte Ä als ASCII. Naked-Umlaut-Check erkennt's nicht. |
| D2 | 500 Posts, 47KB CSV | Perf | ✅ | ✅ | 0 | 34ms, kein Perf-Problem |
| D3 | **Pitch-JSON Schema-Drift (nische-level)** | Info | ✅ **NEU** | ✅ | 0 | Fehlte komplett — war asymmetrisch zu Brand-JSON |
| D4 | Symlinked files | Happy | ✅ | ✅ | 0 | Path.exists() folgt Symlinks korrekt |
| D5 | Whitespace-only Anleitung (size trick) | Failure | ✅ | ✅ | 1 | Heading-Check fängt ab |
| D6 | Multi-line CSV fields | Happy | ✅ | ✅ | 0 | csv.reader handled via newline="" |
| D7 | Brand-JSON nested objects (deep nesting) | Happy | ✅ | ✅ | 0 | Schema-Check geht nur 1 deep — OK |
| D8 | Concurrent reads (3 parallel processes) | Perf | ✅ | ✅ | 0 | Idempotent, kein Race |
| D9 | **CSV inconsistent row widths** (10|11|12 cols) | Failure | ✅ **CRITICAL FIND** | ✅ | 1 | **REAL-WORLD-BUG: 23 Posts in 3 Nischen hatten 10 statt 11 cols** |

### v0.4.0 Ergänzungen (+3 Tests)

| # | Test | Typ | v0.4.0 | Exit | Finding |
|---|---|---|---|---|---|
| D9a | Quoted + Empty-Pitch Kombi | Failure | ✅ | 1 | Counter korrekt trotz Quotes |
| D9b | BOM + Schema-Drift + große Anleitung (Kombi) | Happy | ✅ | 0 | Alle INFOs + 0 Errors |
| D9c | Pitch-JSON top-level Schema-Drift | Info | ✅ **NEU** | 0 | Fehlte komplett — jetzt nische+top-level |

## Entscheidende Bugs (durch Edge-Tests gefunden)

### C-Serie: Bash→Python Migration Bugs (v0.1.0 → v0.2.0)

1. **awk ignoriert CSV-Quotes** — `awk -F','` zählt `"Caption, mit Komma"` als 2 Spalten → 13 statt 11
2. **Brand-JSON only Syntax, not Schema** — valid JSON ≠ alle 6 Required-Felder da
3. **Pitch-JSON nur Existenz, nicht Inhalt** — Datei da ≠ Nische da
4. **Exit-Code durch Pipe maskiert** — `tail | grep` liefert Exit vom grep, nicht vom Validator

### D-Serie: Tiefenbohrung-Bugs (v0.2.0 → v0.3.0)

5. **Pitch-JSON Schema-Drift asymmetrisch** — Brand-JSON hatte unknown-field-Detection, Pitch-JSON nicht. ❌ **Fixed in D3**
6. **CSV Row-Width-Check fehlte komplett** — csv.reader zählte nur Header. 23 von 40 echten Posts hatten 10 statt 11 Spalten (card_7 fehlend). Validator sagte "11 columns" = OK. ❌ **CRITICAL — Fixed in D9**
7. **Pitch-JSON top-level Schema-Drift fehlte** — nur nische-level, top-level Felder wie `always_use`, `anti_patterns`, `usage_recommendation` wurden silent ignoriert. ❌ **Fixed in D9c**

### Real-World-Impact der gefundenen Bugs

| Bug | Betroffene Posts | Effekt | Erkannt durch |
|---|---|---|---|
| Card 7 fehlend in KK (Posts 2,3,4) | 3 | bild_keyword in nische-Spalte, pitch in card_7 | D9 Row-Width |
| Card 7 fehlend in Produktivität (alle 10) | 10 | Alle 10 Posts 1 Spalte zu kurz, pitch + nische + keyword verschoben | D9 Row-Width |
| Card 7 fehlend in Schulden (alle 10) | 10 | Wie Produktivität | D9 Row-Width |
| pitch-variants ohne Produktivität-Nische | — | Canva Slide 8 = default pitch (nicht rotiert) | v0.2.0 C5 |

## Faustregel: Wann von Bash nach Python migrieren

> **Wenn ein Validator/Script mehr als 3 Edge-Cases abdecken muss ODER CSV-Quoting involviert → sofort in Python. Bash ist ab 4 Failure-Pfaden nicht mehr reliability-safe.**

## Workflow: Neuen Edge-Case hinzufügen

1. In diese Matrix eintragen (Test # + Typ + Status)
2. Validator patchen (neue Check-Funktion)
3. Gegen synthetischen Test-Case testen: `python3 validate-design-kit.py <nische>`
4. Expect: Exit 1 + klare Error-Message (oder Exit 0 für INFOs)
5. Happy-Path erneut testen (0 Regressions)
6. **Auf echten Daten testen** — nicht nur auf synthetischen Test-Cases
7. Ergebnis + Datum + Edge-Test-ID in Matrix aktualisieren
8. Wenn realer Bug gefunden → Liste der realen betroffenen Datensätze dokumentieren