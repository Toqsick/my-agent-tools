# GreyHackDB.db Schema

## Schema Stand (2026-07-03, Version V0.9.6771-beta)

**LIVE DB Schema (vereinfacht):** (`/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db`)

```sql
CREATE TABLE Files (ID TEXT PRIMARY KEY, Content TEXT, refCount INTEGER NOT NULL DEFAULT 1);
-- KEINE Spalten "nombre", "computer_pk", "content_type" mehr im aktuellen Schema!
```

Die Backups haben das gleiche Schema. Alte Erinnerungen an `nombre`/`computer_pk` sind veraltet.

## ⚠️ Dual-ID-Class Discovery (2026-07-04)

Die `Files`-Tabelle hat **zwei ID-Klassen**:
- **UUID/MD5-IDs** (246/247 Einträge) — via `Computer.FileSystem`-JSON referenziert.
- **Pfad-String-IDs** (1 Eintrag: `Config/yuno.src`, refCount=1) — direkter Pfad als ID, erzeugt durch in-game `touch()`/`set_content()`.
- **BackupPlayerFiles** hat 0 Zeilen im aktuellen Save — normal, kein Bug.

## Wichtig für Injection

`INSERT INTO Files` mit Pfad-ID allein macht die Datei NICHT im Game sichtbar. Zusätzlich muss ein `Computer.FileSystem`-JSON-Eintrag ergänzt werden.

## Storage Limits

**Grösstes File in der LIVE DB:** ~78 KB (YUNO V6, analysiert 2026-07-04). TOP-5 Files machen 54 % des gesamten File-Contents aus (296 KB von 1.423 KB). SQLite TEXT kann ~2 GB, aber der CodeEditor im Spiel hat vermutlich ein UI-Limit (~30K Zeichen).

**Konsequenz für Deployment von Files:**
- Files <30 KB → CodeEditor Copy-Paste (sicher)
- Files 30-100 KB → DB-Injection direkt per `INSERT INTO Files` oder Chunking im CodeEditor
- Files >100 KB → immer DB-Injection verwenden