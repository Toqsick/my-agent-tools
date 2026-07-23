# GreyHack DB — Internal FileSystem Audit (Drift Matrix Workflow)

## Wozu

Dieses Dokument beschreibt die **einzel-Computerspezifische Audit-Methodik**:
Vergleich der `Files`-Tabelleninhalte (Content) mit der `FileSystem`-JSON-Baumstruktur
eines bestimmten Computers. Ziel: Drift-Matrix zwischen "was in der DB gespeichert ist"
und "was im Spiel als Datei sichtbar ist".

**Nicht zu verwechseln mit:**
- `sqlite-forensic-diff` (vergleicht *zwei verschiedene* DBs)
- `db-hash-delta-forensics` (vergleicht Hash/Content-Änderungen *über Zeit*)
- `db-deployment-injection` (schreibt *neue* Dateien in die DB)

## Trigger

- "Auditiere den aktuellen Zustand von <Modul> auf dem Player-Computer"
- "Drift-Matrix zwischen DB und FileSystem"
- "Was ist auf dem PC verlinkt vs. was in der Files-Tabelle liegt"
- "Biene B Audit" (Viper Redeploy Pattern)
- "Cross-verify zwischen Files-Tabelle und FS-Tree"

## Workflow

### Phase 1 — Files-Tabelle abfragen

```sql
-- Alle Module eines Patterns finden
SELECT ID, length(Content) AS len, refCount, substr(Content,1,30) AS first30
FROM Files
WHERE ID LIKE '%<pattern>%'
ORDER BY ID;
```

**Wichtige Felder:**
- `ID` — der relative Pfad im Spiel (z.B. `Config/yuno_viper_core.src`)
- `Content` — der eigentliche Dateiinhalt (kann 14 KB+ sein)
- `refCount` — Anzahl Referenzen (1 = gesund, >1 = Mehrfachreferenz-Fragmentierung)

### Phase 2 — FileSystem JSON extrahieren

Das FileSystem ist ein JSON-BLOB in der TEXT-Spalte `Computer.FileSystem`:

```sql
-- Player-Computer identifizieren
SELECT ID, IsPlayer, Users FROM Computer WHERE IsPlayer=1;

-- FileSystem JSON extrahieren
SELECT FileSystem FROM Computer WHERE IsPlayer=1 AND ID='<computer-uuid>';
```

**Export in eigene Datei:**
```bash
sqlite3 "$DB" "SELECT FileSystem FROM Computer WHERE IsPlayer=1 AND ID='<uuid>';" > /tmp/player_fs.json
```

### Phase 3 — JSON-Tree walken (Python)

Das FileSystem-Format ist ein rekursiver Baum:

```json
{
  "computerID": "...",
  "files": [],
  "folders": [
    {
      "nombre": "root",
      "files": [...],
      "folders": [...]
    },
    ...
  ]
}
```

Python-Walker:

```python
import json

with open('/tmp/player_fs.json') as f:
    fs = json.load(f)

def walk_flat(node, path):
    """Flatten tree to list of file entries with full path."""
    out = []
    for f in node.get('files', []) or []:
        nombre = f.get('nombre','')
        out.append({
            'path': path + '/' + nombre,
            'id': f.get('ID'),
            'name': nombre,
            'size': f.get('size'),
            'owner': f.get('owner'),
            'group': f.get('group'),
            'typeFile': f.get('typeFile'),  # 0=file, 1=binary, 2=log, 3=lib, 7=other
            'isBinario': f.get('isBinario'),
            'saved': f.get('saved'),
            'symlink': f.get('symlink',''),
        })
    for folder in node.get('folders', []) or []:
        nombre = folder.get('nombre','')
        new_path = path + '/' + nombre
        out.extend(walk_flat(folder, new_path))
    return out

all_files = walk_flat(fs, '')
```

### Phase 4 — Drift-Matrix bauen

Vergleiche pro Modul:

| Dimension | Files-Tabelle | FileSystem JSON | Drift? |
|-----------|--------------|-----------------|--------|
| Existenz | `SELECT COUNT(*) FROM Files WHERE ID='<path>'` | `any(f.id == '<path>' for f in all_files)` | ⚠ fehlender Link |
| Größe | `length(Content)` | `entry['size']` | ⚠ size=0 obwohl Content > 0 |
| Owner | (nicht in Files) | `entry['owner']` | (nur FS-seitig) |
| Group | (nicht in Files) | `entry['group']` | (nur FS-seitig) |
| refCount | `refCount` | (nicht in FS) | (nur DB-seitig) |
| saved | (nicht in Files) | `entry['saved']` | (nur FS-seitig) |

**Python-Matrix Builder:**

```python
def build_drift_matrix(files_table_entries, fs_entries):
    """
    files_table_entries: list of dicts from SQLite (ID, length, refCount)
    fs_entries: list of dicts from walk_flat()
    Returns: list of drift dicts
    """
    fs_by_id = {e['id']: e for e in fs_entries}
    
    matrix = []
    for db_entry in files_table_entries:
        db_id = db_entry['ID']
        fs_entry = fs_by_id.get(db_id, None)
        
        drift = {
            'module': db_id.split('/')[-1],
            'db_id': db_id,
            'db_content_len': db_entry['length(Content)'],
            'db_refcount': db_entry['refCount'],
            'fs_exists': fs_entry is not None,
            'fs_path': fs_entry['path'] if fs_entry else None,
            'fs_size': fs_entry['size'] if fs_entry else None,
            'fs_owner': fs_entry['owner'] if fs_entry else None,
            'fs_group': fs_entry['group'] if fs_entry else None,
            'fs_saved': fs_entry['saved'] if fs_entry else None,
            'fs_isBinario': fs_entry['isBinario'] if fs_entry else None,
            'size_mismatch': fs_entry and fs_entry['size'] == 0 and db_entry['length(Content)'] > 0,
        }
        matrix.append(drift)
    
    return matrix
```

### Phase 5 — Soft-Limit Analyse (//command Threshold)

GreyHack's `//command`-Channel hat ein Soft-Limit von ~12288 Bytes.
Module >12 KB können nicht über `//command` automatisch geladen werden.

```python
LIMIT = 12288
for mod in modules:
    over = mod['db_content_len'] - LIMIT
    fits = 'JA' if mod['db_content_len'] <= LIMIT else 'NEIN (+%d)' % over
```

**Konsequenz:**
- ✗ `//command yuno_viper_*` scheitert bei Modulen >12 KB
- ✓ `build` + `run /path/to/module.src` funktioniert immer
- ✓ Auto-Dispatch muss den Pfad-Pfad statt des Command-Pfads nutzen

### Phase 6 — Befund-Kategorisierung

| Status | Bedeutung | Aktion |
|--------|-----------|--------|
| 🟢 `present-and-linked` | In DB + FS vorhanden, alles konsistent | Keine |
| 🟡 `present-on-root` | In DB + unter /root/Config, aber nicht unter /home/<user>/Config | Re-Link |
| 🔴 `missing-on-player` | In DB, aber kein FS-Link auf dem Player-PC | Link setzen |
| 🔴 `missing-from-db` | FS-Link ohne DB-Eintrag | Content aus FS extrahieren |
| 🟡 `size_mismatch` | FS-size=0 aber Content > 0 | Meist benign (GreyHack-eigen) |
| 🔴 `refcount_fragmented` | refCount > 1 | Deduplizieren |

## Bekannte Fallstricke

| Fallstrick | Symptom | Lösung |
|-----------|---------|--------|
| **FS-size=0 aber Content gesund** | Alle Module zeigen size=0 | Ist GreyHack-eigen — `Files.Content` ist Source of Truth |
| **JSON > 500KB** | Truncation in sqlite3-Ausgabe | `SELECT FileSystem > /tmp/player_fs.json` umleiten |
| **Mehrere Config-Folder** | root/Config vs gregor/Config vs guest/Config | `find_with_path()` Disambiguierung nötig |
| **Player-UUID unbekannt** | `IsPlayer=1` findet mehrere | Nach `Users LIKE '%<username>%'` filtern |
| **refCount=1 bei Duplikaten** | Gleicher Content, verschiedene IDs | Content-Hash-Vergleich zusätzlich |
| **Symlink-Ziele** | FS-Eintrag ist Symlink, kein echter File | `symlink`-Feld prüfen |

## Beispiel-Output (Drift-Matrix Tabelle)

```
| module                    | Files.Content | Files.refCount | /root/Config size | /root/Config saved | /home/gregor/Config |
|---------------------------|--------------:|---------------:|------------------:|-------------------:|--------------------:|
| yuno_viper_core.src       |         14325 |              1 |                 0 |               True |          FEHLT      |
| yuno_viper_net.src        |         19805 |              1 |                 0 |               True |          FEHLT      |
| yuno_viper_scan.src       |         23574 |              1 |                 0 |               True |          FEHLT      |
```

## Verwandte Skills

- `greyhack` — Haupt-Umbrella (dieses Dokument ist ein Reference davon)
- `sqlite-forensic-diff` — Multi-DB-Vergleich (anderer Use-Case)
- `greyhack-deploy-tools` — Deployment via DB-Injection (Schreib-Pendant zu diesem Audit)

## Changelog

- 2026-07-15: Initiale Version — abgeleitet aus Biene B Viper-Phase-A Audit