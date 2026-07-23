---

name: sqlite-forensic-diff
description: "Use when user asks for SQLite database comparison, forensic diff of DBs, schema/row diff across multiple SQLite files. NOT for live production DB writes or non-SQLite databases. Systematic forensic comparison of multiple SQLite databases."
version: 1.1.0
author: Hermes Agent (derived from GreyHack DB diff analysis session)
tags:
- sqlite
- forensics
- db-comparison
- diff
- data-analysis
triggers:
- vergleiche die DBs
- diff zwischen *db*
- was hat sich geändert seit
- sqlite vergleich
- forensischer db vergleich
- db diff analyse
- savegame diff
- database comparison
- was ist neu in der db
- unterschiedliche versionen vergleichen
- db-diff
- daten aus der db extrahieren
- vollständigen extrakt
- deep intel extraction
- alle daten aus der db
- sub-bee cross-verify
metadata:
  hermes:
    changelog:
    - '1.1.0 (2026-07-14): Neues #4b Quality Gate — Sub-Agent Cross-Verification für
      DB-Extrakte (Triple-Verifikation: DB vs Report vs JSON). Password-Handling §5.1
      erweitert: Längen-Verteilung, Zeichenklassen-Klassifikation (5 Pattern-Klassen),
      Output-Checkliste. Dual-Output Verification Pattern dokumentiert. Erweitertes
      Auslöser-Set.'
related_skills:
- greyhack
- git-clone-audit
lane: worker-flash
reasoning_effort: high
license: MIT
trigger_keywords: ['sqlite', 'comparison', 'forensic', 'diff', 'multiple']
keywords: ['sqlite', 'comparison', 'forensic', 'diff', 'multiple']
last_curated: '2026-07-23'
curated_by: 'Yuno'
---
# SQLite Forensic Diff

## Überblick

Systematische 3-Phasen-Methodik zum Vergleich mehrerer SQLite-Datenbanken.
Entwickelt aus der GreyHack-DB-Forensik, anwendbar auf **jede** SQLite-DB
(Speicherstände, Config-Backups, App-Daten, Spiel-Saves).

## 1. Vorbereitung — Read-Only Working Copy

**Niemals die Original-DB direkt öffnen.** Immer Kopien anlegen.

```bash
# Working-Copy anlegen
mkdir -p /tmp/forensic-diff
cp "$ORIGINAL_DB1" /tmp/forensic-diff/db1.db
cp "$ORIGINAL_DB2" /tmp/forensic-diff/db2.db
chmod 444 /tmp/forensic-diff/*.db

# Basis-Metadaten sammeln
ls -la /tmp/forensic-diff/
md5sum /tmp/forensic-diff/*.db
```

## 2. Phase 1 — Integritätsprüfung

### 2.1 MD5 + Größen-Vergleich
```bash
for f in /tmp/forensic-diff/*.db; do
  echo "$(md5sum "$f" | cut -d' ' -f1)  $(stat -c%s "$f")  $(basename "$f")"
done
```

Größen-Identität ≠ Inhalts-Identität. Gleiche Größe + unterschiedliche MD5s
= echte Inhaltsänderungen.

### 2.2 Byte-Exaktheit
```bash
cmp -s /tmp/forensic-diff/db1.db /tmp/forensic-diff/db2.db && echo "IDENTISCH" || echo "UNTERSCHIEDLICH"
```

### 2.3 Befund-Formulierung
```
Integrität: ✅ PASS — N DBs haben einzigartige MD5s bei identischer Größe
(= echte Inhaltsmodifikationen, keine Null-/Kopie-Artefakte).
```

## 3. Phase 2 — Row-Count-Delta

Schema entdecken + pro Tabelle zählen:

```bash
cd /tmp/forensic-diff
DB1="db1.db"
DB2="db2.db"

# Schema entdecken (Einmal pro DB)
sqlite3 "$DB1" ".tables"
sqlite3 "$DB1" ".schema"

# Row-Count-Matrix erstellen
echo "=== Row Counts ==="
printf "%-25s | %-8s | %-8s | Δ\n" "TABLE" "DB1" "DB2"
echo "--------------------------|----------|----------|---"
for table in $(sqlite3 "$DB1" ".tables"); do
  c1=$(sqlite3 "$DB1" "SELECT COUNT(*) FROM [$table];")
  c2=$(sqlite3 "$DB2" "SELECT COUNT(*) FROM [$table];")
  delta=$((c2 - c1))
  echo "$table" | awk -v c1="$c1" -v c2="$c2" -v d="$delta" \
    '{printf "%-25s | %-8s | %-8s | %+d\n", $0, c1, c2, d}'
done
```

Nur Tabellen mit Δ ≠ 0 sind relevant für Phase 3.

> **⚠️ Pitfall:** `sqlite3 .tables` trennt Leerzeichen, wenn Tabellennamen
> Leerzeichen enthalten. Für solche Fälle `sqlite3 "$DB1" "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"` verwenden.

## 4. Phase 3 — Content-Diffs

### 4.1 ID-level Diff (Primary-Key-basierte Tabellen)

Für Tabellen mit UUID/Integer-PK:

```bash
sqlite3 "$DB2" "SELECT ID FROM <table> ORDER BY ID;" > /tmp/ids-db2.txt
sqlite3 "$DB1" "SELECT ID FROM <table> ORDER BY ID;" > /tmp/ids-db1.txt

# Nur in DB2 (vorher) → in DB1 neu hinzugekommen
comm -13 /tmp/ids-db2.txt /tmp/ids-db1.txt
```

**Warum `comm -13`**: Zeile 1 = nur in Datei-1 (DB2), Spalte 2 = nur in Datei-2 (DB1).
`-13` unterdrückt Spalten 1 und 3 → nur neue IDs aus DB1.

### 4.2 Cross-DB Content-Diff (SQLite ATTACH)

Wenn IDs stabil sind aber Inhalt sich ändern kann:

```bash
sqlite3 "$DB2" <<'SQL'
ATTACH DATABASE '/tmp/forensic-diff/db1.db' AS d1;
SELECT <pk>, <changed_field1>, <changed_field2>
FROM <table> d2
JOIN d1.<table> d1 ON d2.<pk> = d1.<pk>
WHERE d2.<field> != d1.<field>
LIMIT 50;
DETACH d1;
SQL
```

**💡 Tipp:** Für große Tabellen zuerst mit `LIMIT 5` spot-checken, ob
Content-Diffs überhaupt existieren.

### 4.3 Numerische IDs mit `rowid` (implizit)

Wenn Tabellen keine explizite ID-Spalte haben:

```bash
# Alle rowids mit Hash des ROW-Contents
sqlite3 "$DB2" "SELECT rowid, * FROM <table> ORDER BY rowid;" > /tmp/rows-db2.txt
sqlite3 "$DB1" "SELECT rowid, * FROM <table> ORDER BY rowid;" > /tmp/rows-db1.txt
diff /tmp/rows-db2.txt /tmp/rows-db1.txt
```

### 4.4 Large-Content-Diffs (BLOBs/JSON)

Bei TEXT/BLOB-Spalten:

```bash
# Größen-Vergleich
sqlite3 "$DB1" "SELECT ID, length(content_column) FROM <table> WHERE ID IN (...);"
# Content-Auszug nur bei Änderungen
sqlite3 "$DB1" "SELECT substr(content_column, 1, 200) FROM <table> WHERE ID = '<changed_id>';"
```

## 4b. Cross-Verification durch Sub-Agent (Quality Gate)

Nach einem vollständigen DB-Extrakt oder -Vergleich **niemals blind vertrauen.** Spawne einen unabhängigen Sub-Agenten zur Triple-Verifikation.

### 4b.1 Trigger

Immer wenn ein Extrakt abgeschlossen wurde der:
- Einen Markdown-Report schreibt
- Ein Side-Effect JSON erzeugt
- Mehr als 5 Tabellen umfasst

### 4b.2 Workflow

```
1. Dein Extrakt ist fertig → Report.md + side-effect.json liegen vor
2. Spawne delegate_task(role='leaf') mit:
   - DB-Pfad (read-only!)
   - Report-Pfad
   - JSON-Pfad
   - Liste aller Tabellen (damit Sub-Agent weiss, was er zählen soll)
3. Sub-Agent führt SELBSTSTÄNDIG aus:
   - sqlite3 "SELECT COUNT(*) FROM [table]" für ALLE Tabellen
   - PRAGMA integrity_check
   - Extrahiert claimed counts aus Report (Section 1 der Tabelle)
   - Extrahiert table_counts aus JSON
   - Vergleicht 3-fach: Mine vs Report vs JSON
4. Output als Markdown-Tabelle: | Table | Mine | Report | JSON | Match? |
5. Verdict: PASS (alle match) oder FAIL (erste Mismatch-Stelle reporten)
6. Sub-Agent schreibt Verifikations-Report (.md) ins Arbeitsverzeichnis
```

### 4b.3 Sub-Agent Constraints

- ❌ DB niemals modifizieren (read-only via `mode=ro`)
- ❌ Keine INSERT/UPDATE/DELETE — nicht mal Transaktionen
- ❌ Keine Klartext-Passwörter extrahieren
- ❌ Keine Annahmen aus Report übernehmen — eigene COUNTs fahren
- ✅ Darf write_file / terminal / read_file nutzen

### 4b.4 Dual-Output Verification Pattern

Der Side-Effect JSON ist die **maschinenlesbare Source of Truth**, der Markdown-Report die human-readable Ableitung. Beide müssen konsistent sein:

| Eigenschaft | JSON | Markdown |
|-------------|------|----------|
| Zweck | Maschinen-Verifikation | Mensch-Lektüre |
| Struktur | `table_counts`, `summary`, `key_findings` | Sektionen, Tabellen, Erklärungen |
| Verifikation | Sub-Agent matched gegen DB | Sub-Agent parst Section-1-Tabelle |
| Enthält | Alle Aggregatzahlen | Nur relevante + interpretierte Daten |

**Praktischer Check:** Der Sub-Agent liest IMMER beide Dateien und matched gegen die DB. Wenn JSON ≠ Report → FAIL (Inkonsistenz).

### 4b.5 Dokuplicht nach Cross-Verify

- Report → `09 System-Doku/<Domain>/<topic>-<date>.md`
- Side-Effect JSON → `/tmp/<scan-folder>/<scan-id>.json`
- Verification Report → `/tmp/<scan-folder>/<scan-id>-sub.md`

### 4b.6 Typische Fehler beim Cross-Verify

| Fehler | Symptom | Lösung |
|--------|---------|--------|
| Sub-Agent kopiert aus Report statt eigene Queries | Match ist wertlos | EXPLIZIT im Briefing: "eigene COUNTs, nicht Report abschreiben" |
| Tabellennamen mit Leerzeichen | sqlite3 .tables parst falsch | `SELECT name FROM sqlite_master WHERE type='table'` |
| Report Section 1 nicht korrekt geparst | Mismatch weil Parsing fehlschlug | Briefing: "Tabelle in Zeilen 9-28 parsen" |
| Sub-Agent hat kein JSON-Tool | Kann JSON nicht lesen | `python3 -c "import sys,json; d=json.load(sys.stdin); print(d['table_counts'])"` |
| Sub-Agent schreibt in falsches Verzeichnis | Report wird nicht gefunden | Briefing: absoluten Pfad für Output mitgeben |

## 5. Spezial-Fälle

### 5.1 Password-Handling (Policy — immer einhalten)

Wenn die DB Passwort-Tabellen enthält:

1. **NIEMALS Plaintext in Report-Dateien schreiben**
2. **NIEMALS Plaintext an Sub-Agenten übergeben**
3. Nur **Patterns und Statistiken extrahieren**

#### Mindest-Extrakt (Pflicht)

Jeder Password-Extrakt muss mindestens diese 4 Werte liefern:

| Kennzahl | Berechnung | Beispiel |
|----------|-----------|----------|
| `total` | `SELECT COUNT(*)` | 282 |
| `unique` | `SELECT COUNT(DISTINCT PlainPassword)` | 282 |
| `min_length` | `SELECT MIN(length(PlainPassword))` | 3 |
| `max_length` | `SELECT MAX(length(PlainPassword))` | 12 |

#### Erweiterte Statistik (empfohlen)

```sql
-- Längen-Verteilung (z.B. 95× 6-Zeichen, 72× 5-Zeichen)
SELECT length(PlainPassword) as len, COUNT(*) as cnt
FROM Passwords GROUP BY len ORDER BY len;

-- Numerische vs. alphabetische Passwörter
SELECT
  SUM(CASE WHEN PlainPassword GLOB '[0-9]*' THEN 1 ELSE 0 END) as numeric_count,
  SUM(CASE WHEN PlainPassword GLOB '[a-zA-Z]*' AND PlainPassword NOT GLOB '*[0-9]*' THEN 1 ELSE 0 END) as alpha_count,
  COUNT(*) as total
FROM Passwords;
```

Daraus ableiten:
- `avg_length` = gewichtetes Mittel über die Verteilung
- `char_pattern_distribution`: Anteile der Klassen (z.B. 47.5% pure-lower, 41.8% mixed-case, 5.0% digits-only)

#### Zeichenklassen-Klassifikation

| Pattern-Klasse | Beispiel | Regex-Check | Beschreibung |
|----------------|----------|-------------|-------------|
| `letters_only_lower` | `passwort` | `^[a-z]+$` | Nur Kleinbuchstaben |
| `mixed_lower_upper` | `PassWort` | `^[a-zA-Z]+$` | Groß+Klein gemischt |
| `digits_only` | `12345` | `^[0-9]+$` | Nur Ziffern |
| `lower_digits` | `pass123` | `^[a-z0-9]+$` | Kleinbuchstaben + Ziffern |
| `mixed_letters_digits` | `Pass123` | `^[a-zA-Z0-9]+$` | Mixed Case + Ziffern |

```python
import re

def classify_password(pw: str) -> str:
    if re.match(r'^[a-z]+$', pw): return 'letters_only_lower'
    if re.match(r'^[a-zA-Z]+$', pw): return 'mixed_lower_upper'
    if re.match(r'^[0-9]+$', pw): return 'digits_only'
    if re.match(r'^[a-z0-9]+$', pw): return 'lower_digits'
    if re.match(r'^[a-zA-Z0-9]+$', pw): return 'mixed_letters_digits'
    return 'special_chars'
```

#### Entropie-Schätzung

```python
import math
pw = "Beispiel"
pattern = "".join("U" if c.isupper() else "L" if c.islower() else "D" if c.isdigit() else "X" for c in pw)
uniq = len(set(pw.lower()))
entropy = round(math.log2(uniq ** len(pw)), 2) if uniq > 0 else 0.0
```

#### Output-Checkliste

✅ `total` + `unique` + `min_length` + `max_length` + `avg_length` vorhanden
✅ `length_distribution` als Map {len: count}
✅ `char_pattern_distribution` als Map {class: count}
✅ `numeric_range` (bei digits-only: min-max)
✅ **Kein einziger Plaintext** in Reports, JSONs oder Sub-Agent-Briefings
✅ Bei wiederholten gleichen Zeichen oder sehr geringer Komplexität: `"note": "trivial: all same char"`

### 5.2 JSON-Felder in Text-Spalten

Manche DBs speichern komplexe State-Strukturen als JSON in TEXT-Spalten
(z.B. `Computer.FileSystem`, `Players.Missions`).

```bash
# Pretty-Print für Lesbarkeit
sqlite3 "$DB1" "SELECT json(json_field) FROM <table> WHERE ID = '<id>';"
```

### 5.3 Date-basierte Änderungen

Wenn Tabellen ein Datumsfeld haben und IDs stabil bleiben:

```bash
# Prüfen ob sich NUR das Datum geändert hat (reiner Clock-Tick)
sqlite3 "$DB2" <<'SQL'
ATTACH DATABASE '/tmp/forensic-diff/db1.db' AS d1;
SELECT d2.ID, d2.Date, d1.Date
FROM <table> d2
JOIN d1.<table> d1 ON d2.ID = d1.ID
WHERE d2.Date != d1.Date AND d2.<other_field> = d1.<other_field>;
DETACH d1;
SQL
```

## 6. Output-Format

### 6.1 Maschinenlesbar (JSON)

Immer ein JSON-Report mit:

| Key | Inhalt |
|-----|--------|
| `report_id` | Timestamp-basierte ID |
| `databases` | Pfade, Größen, MD5s der Quellen |
| `integrity_check` | Ergebnis der Integritätsprüfung |
| `row_counts` | Vollständige N×M-Zellen-Matrix |
| `active_tables_with_changes` | Nur Tabellen mit Δ |
| `diffs` | Detaillierte Diff-Objekte pro Tabelle |
| `summary` | Key Findings + Aggregate |

JSON-Schema (minimal):
```json
{
  "row_counts": { "<table>": { "db1": N, "db2": M, "delta": M-N } },
  "diffs": {
    "files": { "added": [...], "removed": [...] },
    "passwords": { "added_count": N, "patterns": [...] },
    "<table>": { ... }
  },
  "summary": { "files_added": N, "passwords_added": M, "key_findings": [...] }
}
```

### 6.2 Menschlesbar (Markdown)

- Tabellen-Row-Count-Matrix (Markdown-Tabelle)
- Passwörter: nur Pattern-Tabellen (Länge, Unique-Zeichen, Entropie, Klasse)
- Detail-Sektionen pro geänderter Tabelle
- TL;DR Summary-Box am Anfang

## 7. Dokuplicht

Nach jeder SQLite-Forensik gilt Dokuplicht laut SOUL.md:
- JSON-Report ablegen (`/tmp/.../<report_id>.json`)
- Markdown-Report im Obsidian-Vault unter `09 System-Doku/<Domain>/`
- Sub-Task-Reports (z.B. MD5-Verifikation) als separate `.md`-Datei

## 8. Bekannte Fallstricke

| Fallstrick | Symptom | Lösung |
|-----------|---------|--------|
| **Tabellennamen mit Leerzeichen** | sqlite3 .tables gibt falsche Ergebnisse | `SELECT name FROM sqlite_master WHERE type='table'` |
| **Implizite rowid vs explizite PK** | `comm -13` zeigt keine Änderungen obwohl Inhalt anders | Content-Diff via ATTACH statt ID-Diff |
| **JSON-Felder normalisieren sich nicht** | Text-Rohvergleich schlägt fehl trotz semantischer Identität | `json_extract()` für semantischen Vergleich |
| **Passwörter in Plaintext** | Versehentliches Ausgeben in Reports | Policy §5.1 strikt einhalten — nie Plaintext |
| **Date-Feld nur Tick, kein Inhalt** | Alle Zeilen scheinen geändert | Cross-Check ob nur Date sich geändert hat |
| **Chmod 444 vergessen** | Versehentliches Bearbeiten der Working-Copy | IMMER `chmod 444` nach `cp` |
| **Originals unter /mnt/ pfad** | Können beim nächsten Mount nicht verfügbar sein | Working-Copy in `/tmp/` ablegen |

## 9. Quick-Start (Minimal-Rezept)

```bash
# 1. Working copies
mkdir -p /tmp/forensic-diff
cp <db1> /tmp/forensic-diff/db1.db; cp <db2> /tmp/forensic-diff/db2.db
chmod 444 /tmp/forensic-diff/*.db

# 2. Integrity
md5sum /tmp/forensic-diff/*.db
cmp -s /tmp/forensic-diff/db1.db /tmp/forensic-diff/db2.db

# 3. Row counts
for t in $(sqlite3 /tmp/forensic-diff/db1.db ".tables"); do
  c1=$(sqlite3 /tmp/forensic-diff/db1.db "SELECT COUNT(*) FROM [$t];")
  c2=$(sqlite3 /tmp/forensic-diff/db2.db "SELECT COUNT(*) FROM [$t];")
  echo "$t: $c1 → $c2 ($((c2-c1)))"
done

# 4. ID diff
for t in $(sqlite3 /tmp/forensic-diff/db1.db "SELECT name FROM sqlite_master WHERE type='table';"); do
  sqlite3 /tmp/forensic-diff/db1.db "SELECT rowid FROM [$t];" | sort > /tmp/ids1.txt
  sqlite3 /tmp/forensic-diff/db2.db "SELECT rowid FROM [$t];" | sort > /tmp/ids2.txt
  new=$(comm -13 /tmp/ids1.txt /tmp/ids2.txt | wc -l)
  del=$(comm -23 /tmp/ids1.txt /tmp/ids2.txt | wc -l)
  echo "$t: +$new / -$del records"
done

# 5. Content diff (ATTACH) — for tables with IDs but content changes
sqlite3 /tmp/forensic-diff/db1.db <<'SQL'
ATTACH DATABASE '/tmp/forensic-diff/db2.db' AS d2;
SELECT ...
DETACH d2;
SQL
```

## 10. Ausbau-Richtungen

- Automatisierung: Shell-Script mit `sqlite3 -json` und `jq`
- Sub-Agent-Aufteilung: MD5-Check delegieren, Haupt-Thread macht Schema
- CI-Integration: Vergleich von Tages-Backups im Cron
- Webhook-Benachrichtigung bei delta > threshold
