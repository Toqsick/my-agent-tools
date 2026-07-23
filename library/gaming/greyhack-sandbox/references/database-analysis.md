# Database Analysis

## Datenbank-Analyse (GreyHackDB.db)

Die Spiel-Datenbank enthält die komplette Welt:

```bash
set -euo pipefail
DB="/pfad/zu/Grey Hack/Grey Hack_Data/GreyHackDB.db"

# Tabellen
sqlite3 "$DB" '.tables'

# Schema
sqlite3 "$DB" '.schema Computer'

# Row Counts
sqlite3 "$DB" -separator ' → ' 'SELECT "Players", count(*) FROM Players UNION ALL SELECT "Computers", count(*) FROM Computer'

# Computer mit Dateisystem
sqlite3 "$DB" -json 'SELECT ID, FileSystem FROM Computer LIMIT 3' | head -2000
```

| Tabelle | Typischer Inhalt | Hinweis |
|---------|-----------------|---------|
| Players | 1 Spieler mit Missions, Bank, GameOver-Status | |
| Computer | Computer + FileSystem (JSON mit Dateien/Ordnern/Permissions) | |
| Files | 247+ Spiel-Dateien | **ZWEI ID-Klassen** (neu 2026-07-04): (1) UUID/32-hex-GUID (`07a4ef93…`, `0044c4a5-8c9d-…`) — von `Computer.FileSystem` JSON referenziert. **246 von 247 Einträgen.** (2) **Pfad-String-IDs** (`Config/yuno.src`) — nur 1 Eintrag. Diese entstehen durch In-Game-`touch()`/`set_content()`-Aufrufe, NICHT durch FileSystem-JSON-Referenz. refCount=1 für frische Injektionen. |
| BackupPlayerFiles | Backup-Kopien von Spieler-Files, verknüpft via RouterID | `(ID TEXT PK, Content TEXT, RouterID TEXT)` — zweite File-Storage-Tabelle, für Router-Backups. |
| Passwords | Längen Ø 5.8 (je nach Save 100–300) | ⚠️ **Nur Längen zeigen, nie Plaintext loggen!** |
| BankAccounts | 4 Konten mit JSON-Transaktionen + dinero-Balance | |
| MailAccounts | 7 E-Mail-Konten mit JSON-emails | |
| InfoGen | 20 Library-Versionen, Exploit-Registry, Invoices (1.9 MB) | |
| Map | Router, IPs, Netzwerktopologie | |
| WebPages, Logs | Internet-Seiten, System-Logs | |
| Wallets, Coins, Stocks, CTFs | Spiel-Ökonomie | **Leer bis Spieler System nutzt** — kein DB-Bug! |

**Field-Name Pitfall:** Im `FileSystem`-JSON heißen Datei/Ordnernamen `nombre` (spanisch), NICHT `name`. `Files`-Tabelle hat dagegen `ID`/`Content`/`refCount` — **KEINE** Spalten `nombre`/`path`/`computer_pk`/`content_type` im aktuellen Schema (V0.9.6771-beta). Die Dateityp-Klassifizierung erfolgt heuristisch über den Content-Inhalt (`//command:` Marker, YUNO-Keywords, JSON-Struktur). Siehe `references/greyhack-db-file-analysis.md` für den vollständigen Analyse-Workflow mit SQL-Queries und Content-Heuristik.

**⚠️ Passwort-Sicherheit:** `Passwords.PlainPassword` ist **Klartext**. Für Analysen immer **nur Längen** zeigen (wie im Analyse-Rezept oben). Siehe `references/greyhack-db-schema-detailed.md` (Abschnitt Passwords) für den vollständigen Security-Guide + Längen-Verteilungs-Script.

**Vollständige Schema-Referenz (2026-07-04):** `references/greyhack-db-schema-detailed.md` — alle 19 Tabellen, JSON-Strukturen, Analyse-Rezepte in Python + sqlite3, konkrete Save-Daten (20 Library-Versionen, Bank-Transaktionen, Invoice-Struktur, Missions-Format, Passwort-Verteilung, leere-Table-FAQ).

## Injection: Files-Tabelle (Safe Write Pattern)

Wenn man GreyScript-Source-Code (oder andere Daten) in die `Files`-Tabelle schreiben muss — z.B. für YUNO V6 Deployment — dieses Pattern verwenden, NIEMALS rohes `sqlite3` aus der Shell (Content mit Quotes, Newlines, GreyScript-Syntax crasht die Shell-Quoting):

```python
import sqlite3, shutil, os, time

DB = "/pfad/zu/Grey Hack/Grey Hack_Data/GreyHackDB.db"
SRC = "/tmp/build/yuno_v6.src"
FILE_ID = "Config/yuno.src"

# 1) BACKUP — immer vor Schreibzugriff
ts = time.strftime("%Y%m%d-%H%M")
backup = f"{DB}.backup-{ts}"
shutil.copy2(DB, backup)
assert os.path.getsize(DB) == os.path.getsize(backup), "BACKUP MISMATCH"

# 2) Source laden
with open(SRC, "r", encoding="utf-8") as f:
    content = f.read()

# 3) INSERT via parameterized Query (sicheres Escaping!)
conn = sqlite3.connect(DB)
cur = conn.cursor()
try:
    cur.execute("BEGIN")
    cur.execute(
        "INSERT INTO Files (ID, Content, refCount) VALUES (?, ?, 1)",
        (FILE_ID, content),
    )
    conn.commit()
except Exception as e:
    conn.rollback()
    raise e

# 4) VERIFY: SELECT + integrity_check + roundtrip + rowcount
cur.execute("SELECT ID, length(Content), refCount FROM Files WHERE ID = ?", (FILE_ID,))
row = cur.fetchone()
assert row is not None, f"Row {FILE_ID} not found after insert"

cur.execute("SELECT Content FROM Files WHERE ID = ?", (FILE_ID,))
assert cur.fetchone()[0] == content, "Roundtrip mismatch!"

cur.execute("PRAGMA integrity_check")
assert cur.fetchone()[0] == "ok", "DB integrity_failed!"

# Optionale Checks:
cur.execute("PRAGMA quick_check")         # schnellere integrity
cur.execute("PRAGMA page_count")          # page_count delta (kann 0 sein wenn freie Pages reichen)
cur.execute("SELECT count(*) FROM Files") # rowcount +1 bestätigen

conn.close()
```

**Wichtige Architektur-Erkenntnis (2026-07-04):** `Files.ID` ist NUR ein Primary Key. Die ID ist **nicht** der Pfad im In-Game-Filesystem und auch nicht davon abgeleitet (kein MD5). Der Pfad→ID-Link existiert im `Computer.FileSystem`-JSON als `file_id` oder ähnliches Feld innerhalb der File-Node. Ein `INSERT INTO Files` allein macht die Datei NICHT im Spiel sichtbar — sie ist nur im Blob-Store persistiert. Für Sichtbarkeit müsste auch der `FileSystem`-JSON-Eintrag des Ziel-Computers aktualisiert werden (siehe `references/savegame-storage-cleanup.md` für das FileSystem-JSON-Schema).

**Alternativ: UPDATE statt INSERT** (siehe Pitfall #9 im Skill `greyhack-greyscript`, "DB Duplicate Cleanup"). Vor jeder Reinjektion prüfen ob das Modul bereits existiert:

```python
cur.execute("SELECT ID FROM Files WHERE Content LIKE ? LIMIT 1", (f'//command: {mod_name}%',))
existing = cur.fetchone()
if existing:
    cur.execute("UPDATE Files SET Content = ? WHERE ID = ?", (new_content, existing[0]))
else:
    cur.execute("INSERT INTO Files (ID, Content, refCount) VALUES (?, ?, 1)", (new_id, new_content))
```

**page_count Verhalten:** Wenn SQLite genug freie Pages in der DB-Datei hat, wächst `page_count` nach einem INSERT NICHT. Das ist kein Fehler — SQLite füllt zuerst freie Blöcke. Delta = 0 ist normal, solange `integrity_check` ok ist.

**Speicher-Overflow:** In-Game binaries werden absurd groß angezeigt (~5 GB pro Script), während das HDD-Limit in MB ist. Wenn `total_size(FileSystem) / 1GB > hardDisk.totalSize` → HDD überfüllt, viele Spiel-Aktionen schlagen fehl. Cleanup via `/bin/*` rm oder All-in-One-Scripter (siehe `references/savegame-storage-cleanup.md`).