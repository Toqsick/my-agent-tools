# Audit-Biene Pattern — Session 2026-07-14

> Validierte Vorlage für Audit-Bienen in Yunos Schwarm-Dispatch.
> Komplette Drift-Matrix + Stale-Marker + Cross-Source-Triangulation.

## Voraussetzungen

- SQLite3 muss installiert sein (`which sqlite3`)
- Live-DB muss lesbar sein (read-only, kein sudo nötig)
- Vault-Notes mit Stand-Datum im Frontmatter (zur Drift-Bestimmung)

## Live-DB-Extraktions-Befehle (SQLite)

Standard-Befehle für GreyHack Vault-Audit:

```bash
# Metriken
sqlite3 GreyHackDB.db 'SELECT COUNT(*) FROM Computer'
sqlite3 GreyHackDB.db 'SELECT COUNT(*) FROM Map'
sqlite3 GreyHackDB.db 'SELECT COUNT(*) FROM Files'
sqlite3 GreyHackDB.db 'SELECT COUNT(*) FROM Passwords'
sqlite3 GreyHackDB.db 'SELECT COUNT(*) FROM Logs'
sqlite3 GreyHackDB.db 'SELECT COUNT(*) FROM WebPages'
sqlite3 GreyHackDB.db 'SELECT COUNT(*) FROM MailAccounts'
sqlite3 GreyHackDB.db 'SELECT COUNT(*) FROM BankAccounts'

# Player-State
sqlite3 GreyHackDB.db 'SELECT * FROM Players'
sqlite3 GreyHackDB.db 'SELECT * FROM InfoGen'

# Schema-Validierung
sqlite3 GreyHackDB.db '.tables'
sqlite3 GreyHackDB.db '.schema Computer'
sqlite3 GreyHackDB.db '.schema Map'

# Map-Distribution ueber Zeit
sqlite3 GreyHackDB.db 'SELECT Date, COUNT(*) FROM Map GROUP BY Date ORDER BY Date'
```

Fuer nicht-SQLite Quellen: `cat`, `ls -la`, `grep -c`, `wc -l` verwenden.

## Drift-Matrix-Template

```markdown
## Tabellen-Drift-Matrix

Stand vor `<vault-note-datum>` gegen Live-Stand `<audit-datum>`.

| Tabelle | Stand <alt> | Stand <neu> | Delta | Bemerkung |
|---------|------------:|-------------:|------:|-----------|
| Computer | 18 | 18 | 0 | Identisch |
| Files | 247 | 256 | +9 | <Ursache dokumentieren> |
| Passwords | 267 | 282 | +15 | <Ursache dokumentieren> |
| Logs | 21 | 22 | +1 | <Ursache dokumentieren> |
| Map | 56 | 56 | 0 | Kein neuer Host seit <Datum> |
| Player | 1 | 1 | 0 | Identisch |
| InfoGen.Clock | <Alt-Timestamp> | <Neu-Timestamp> | +<Differenz> | <Ursache dokumentieren> |
```

## Stale-Marker YAML-Vorlage

Fuer jede Note mit Drift-Befund:

```yaml
---
type: system-doku-vault
quelle: "<ursprünglicher-pfad>"
importiert: <import-datum>
status: stale-empfehlung
freshness: <ursprüngliches-stand-datum>
verified_<audit-datum>: ja (siehe <Audit-Note-Name> — drift erkannt: +9 Files, +15 Pwds, +1 Log)
wikilinks: <anzahl>
---
```

**Wichtig:** Den `status` von z.B. `importiert-referenz` auf `stale-empfehlung` aendern. Der `verified_`-Tag ist ein eigener Frontmatter-Key (kein Tag-Array), der im Obsidian nicht kollidiert. Die Audit-Note sollte im Body den Drift-Bericht und in der Einleitung den Wiki-Backlink auf die gedriftete Note haben.

## Cross-Source-Triangulation-Checkliste

| Quelle | Liest | Status |
|--------|-------|--------|
| Live-DB | SQLite-Extraktion | ✅ Rohe Fakten (Counts, Timestamps) |
| Vault-Notes | `greyhack-deep-systems-*.md`, etc. | Behauptungen mit Stand-Datum |
| Web-Recherche | documentation.greyscript.org, etc. | API-Signaturen, Syntax |
| Existing Manuals | `dmz-greyhack-handbook.md`, etc. | Operative Doku, Workflow |
| JSON-Dump | `/tmp/gh-audit-<datum>.json` | Vollstaendiger Tabellen-Dump fuer spaetere Referenz |

Wenn 3 von 4 Quellen uebereinstimmen → gesicherter Befund. Bei 2:2 → Widerspruch markieren. Bei <2 Quellen → "unbekannt" schreiben.

## Briefing-Vorlage

```text
Du bist Biene N (Audit) in Yunos <Topic>-Schwarm.

Kontext: Vault hat <Datum>-Notes mit Live-Counts.
Der aktuelle Stand ist im <DB-Pfad> (<version>).
Read-only Session, kein INSERT/UPDATE/DELETE auf die DB.

DEINE TASKS:
1. Lies <DB-Pfad> (SQLite, read-only):
   - `sqlite3 <db> 'SELECT COUNT(*) FROM <table1>'`
   - `sqlite3 <db> 'SELECT COUNT(*) FROM <table2>'`
   - Ggf. `sqlite3 <db> 'SELECT * FROM <Players/InfoGen>'`
2. Lies <vault-note-1> und <vault-note-2>
3. Erstelle Drift-Matrix: alle Counts vergleichen, Timestamps vergleichen
4. Schreibe <output-file>.md mit:
   - Drift-Matrix-Tabelle (7-10 Zeilen)
   - Player-State-Diff-Tabelle
   - Map-Diff (keine neuen Hosts? seit wann?)
   - Liste der veralteten Vault-Behauptungen (dokumentiert, nicht patched)
   - Aktualisierungs-Empfehlungen

OUTPUT: <output-file>.md
CONSTRAINTS: 0 boldface, <=1 em-dash, >=8 Wiki-Links,
  read-only DB, kein INSERT/UPDATE/DELETE
```

## Quality-Gate fuer Audit-Output

```bash
echo "EmDashes:     $(grep -c '—' '<output-file>')"      # Ziel <= 1
echo "Boldface:     $(grep -oE '\*\*[^*]+\*\*' '<output-file>' | wc -l)"  # Ziel: 0
echo "InlineHdr:    $(grep -c '^- \*\*[A-Z]' '<output-file>')"  # Ziel: 0
echo "Wiki-Links:   $(grep -c '\[' '<output-file>')"      # Ziel >= 8
echo "Groesse:      $(stat -c '%s' '<output-file>') Bytes / $(wc -l < '<output-file>') Zeilen"
```

## Bekannte Limitationen

- `Map.LibVersions` ist Python-Dict-Literal (kein JSON) — Fallback-Wert verarbeiten, nicht parsen
- Passwoerter im Dump nur als Laengen-Buckets dokumentieren (3/4/5/6/7/8/9/12), kein Klartext
- DB-freigeschaltet seit GameOver=1 -> Zaehlungen sind eingefroren, kein weiterer Drift erwartbar
- Nicht alle Tabellen sind fuer jeden Vault relevant (`Stocks`, `Coins`, `CTFs`, `Wallets` sind haeufig 0-Eintraege)

## Validierungs-Daten (Session 2026-07-14)

| Metrik | Wert |
|--------|------|
| DB-Groesse | 6.97 MB, SQLite 3.45.1 |
| DB-mtime | 2026-07-06 (seit 8 Tagen eingefroren) |
| Tabellen | 18 |
| Tabellen-Drift | 0 (keine Schema-Aenderungen) |
| Befunde | 7 veraltete Aussagen in 04.07.-Notes |
| JSON-Dump | 2.4 MB, `/tmp/gh-audit-2026-07-14.json` |