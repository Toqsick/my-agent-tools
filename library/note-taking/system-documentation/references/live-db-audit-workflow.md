# Datenquellen-Audit: GreyHack-DB gegen Vault-Dokumente

> Session: 2026-07-14
> Validierte Quelle: `GreyHackDB.db` (SQLite 3.45.1, 6.97 MB, mtime 2026-07-06)
> Vault-Quellen: `greyhack-deep-systems-2026-07-04.md`, `greyhack-deep-intel-2026-07-04.md`, `greyhack-weekly-insights-2026-07-05.md`

## Erkannte Schema-Quirks

### `Computer.FileSystem` ist valides JSON
```sql
SELECT FileSystem FROM Computer LIMIT 1;
-- -> JSON-String, nicht Base64 oder Binary
-- Python: json.loads(row[0]) -> dict mit 'Root', 'Size', 'Children', 'FreeSpace'
```

### `Map.libVersions` ist **kein** JSON — es ist ein Python-Dict-Literal
```python
# Fehlschlag: json.loads(row)
# Korrekt: ast.literal_eval(row) -> dict mit IP -> Version-Mapping
# Fallback-Pattern in Extraktions-Script:
import ast
try:
    lib_ver = json.loads(row)
except (json.JSONDecodeError, TypeError):
    try:
        lib_ver = ast.literal_eval(row)
    except (ValueError, SyntaxError):
        lib_ver = {"parse_error": str(row)[:100]}
```

### `Computer.PasswordBlob` enthält **kein** root-Passwort direkt
Der PasswordBlob ist ein Binary-Feld (BLOB), kein Klartext. Die Passwörter liegen in der `Passwords`-Tabelle als Klartext.

### DB-18-Tabellen-Schema (vollständig)
```
Computer, Map, Passwords, Files, Logs, MailAccounts, BankAccounts,
WebPages, Stocks, Coins, Wallets, CTFs, BackupPlayers, BackupPlayerFiles,
PlayerConns, SharedConns, Players, InfoGen
```

### `Files`-Tabelle hat nur 3 Spalten
```sql
.schema Files
-- CREATE TABLE Files (ID blob, Content text, refCount integer);
-- KEINE nombre/computer_pk wie in alten GreyScript-Notizen angenommen
```

### `Passwords`-Tabelle: Klartext + ComputerID
```sql
.schema Passwords
-- CREATE TABLE Passwords (ID blob, Password text, ...);
-- Password ist Plain-Text, NICHT gehasht
```

### `Computer`-Essid-Format
15 Router: Essid ist ein sprechender NPC-Name wie `Beha_Lehann_Tycoon_S1-7`.
Player-Computer (1 Stück): Essid ist leer (weil Player-PC keinen WLAN-Hotspot broadcastet).
Server (2 Stück): ebenfalls ohne Essid.

## Bewährte Extraktions-Befehle

```bash
# Tabellen-Liste
sqlite3 GreyHackDB.db ".tables"

# Schema einer einzelnen Tabelle
sqlite3 GreyHackDB.db ".schema Computer"

# Count pro Tabelle
sqlite3 GreyHackDB.db "
SELECT 'Computer', COUNT(*) FROM Computer
UNION ALL SELECT 'Map', COUNT(*) FROM Map
UNION ALL SELECT 'Files', COUNT(*) FROM Files
UNION ALL SELECT 'Passwords', COUNT(*) FROM Passwords
UNION ALL SELECT 'Logs', COUNT(*) FROM Logs
"

# Map.Date-Distribution
sqlite3 GreyHackDB.db "SELECT Date, COUNT(*) AS cnt FROM Map GROUP BY Date ORDER BY Date"

# Player-State aus InfoGen
sqlite3 GreyHackDB.db "SELECT Clock, Seed, DeleteVersion FROM InfoGen"

# Active Missions
sqlite3 GreyHackDB.db "SELECT Missions FROM Players"

# Passwort-Längen (ohne Klartext)
sqlite3 GreyHackDB.db "SELECT length(Password) AS pwlen, COUNT(*) AS cnt FROM Passwords GROUP BY pwlen ORDER BY pwlen"
```

## Bekannte Falle: GameClock vs Wall-Clock

Die `InfoGen.Clock` ist die **In-Game-Welt-Zeit** (Jahr 2000), nicht die echte Systemzeit.
- `2000-01-06T14:54:44` = Stand 04.07.2026 (wall-clock)
- `2000-01-07T22:10:16` = Stand 06.07.2026 (wall-clock, nach VIPER-Deployment)
- Die DB `mtime` (Filesystem-Timestamp) ist der echte Zeitstempel für "wann wurde gespeichert"
- Ein Unterschied von 8+ Tagen zwischen mtime und Audit-Tag heißt **eingefrorener Stand** (GameOver=1)

## Essid-Stichproben-Verifikation

```python
# Alle 15 Router-Essids aus der DB extrahieren und mit Vault-Liste matchen
router_essids = [row[0] for row in cursor.execute(
    "SELECT Essid FROM Computer WHERE IsRouter = 1"
).fetchall()]
vault_essids = [...]  # aus Note extrahiert
assert set(router_essids) == set(vault_essids), f"Mismatch: {set(router_essids) ^ set(vault_essids)}"
# -> 15/15 match (validiert 2026-07-14)
```

## Password-Längen als Drift-Indikator

Statt Klartext zu loggen: nur Längen-Buckets dokumentieren.
Ändert sich die Verteilung, sind neue Passwörter dazugekommen.

```bash
# Distribution
sqlite3 GreyHackDB.db "SELECT length(Password) AS l, COUNT(*) AS cnt FROM Passwords GROUP BY l ORDER BY l"
# Typisches Ergebnis nach VIPER (Stand 2026-07-06):
# 3|23  4|11  5|5  6|2  7|12  8|11  9|1  12|1  -> 66 + 216 = 282 total
```