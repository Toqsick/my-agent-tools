# SQLite Database Structure (GreyHackDB.db)

> GreyHack speichert Spielzustand in `GreyHackDB.db` (SQLite). Vollständige Pfade: `Grey Hack_Data/GreyHackDB.db` relativ zum Steam-Installationsordner.

## Relevante Tabellen

| Tabelle | Inhalt |
|---------|--------|
| `Files` | Datei-Inhalte (`ID`: TEXT Hash, `Content`: TEXT, `refCount`: INT) |
| `Computer` | Computersysteme (`FileSystem`: JSON-Baum, `Hardware`, `Users`, `IsPlayer`) |
| `Players` | Spieler-Profile (Nickname, Wallet, Storage, Missions) |
| `PlayerConns` | Verbindungen (Computer → Router → LocalIp) |
| `Passwords` | Passwörter (ID + PlainPassword) |
| `Logs` | Log-Einträge |
| `MailAccounts` | In-Game-Email |
| `WebPages` | In-Game-Webseiten |

## Filesystem-Struktur (JSON in `Computer.FileSystem`)

```json
{
  "computerID": "uuid",
  "nombre": "/",
  "files": [],
  "folders": [{
    "files": [{"ID": "md5-hash", "precio": 0, "isBinario": false, ...}],
    "..."
  }],
  "permisos": {"...": "..."},
  "owner": "root",
  "group": "root",
  "size": 261117281
}
```

## Praktische Nutzung via Python

```python
import sqlite3, json
conn = sqlite3.connect('/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db')
cur = conn.cursor()
cur.execute("SELECT FileSystem FROM Computer WHERE IsPlayer=1")
fs = json.loads(cur.fetchone()[0])
```

## SQLite-Injektion (Stufe 3 — Persistenz)

Tools direkt in `GreyHackDB.db` injizieren:
- `Files`-Tabelle: Inhalt → `ID` (MD5-Hash), `Content`
- `Computer`-Tabelle: `FileSystem` (JSON) erweitern
- `PlayerConns`: Hermes-Computer ans Netzwerk hängen

### FileSystem-Eintrag — erforderliche Felder für Command-Registrierung

Damit ein Script als Shell-Command (`//command:` Marker) funktioniert, muss der FileSystem-JSON-Eintrag diese Werte haben:

```json
{
  "ID": "md5-hash-des-content",
  "nombre": "yuno_v6.src",
  "size": 78155,
  "precio": 0,
  "isBinario": false,
  "typeFile": 0,
  "comando": "",
  "allowImport": true,
  "permisos": {"...": "..."}
}
```

**Kritische Felder:**
- `comando: ""` — MUSS leerer String sein! Ein Wert wie `"run /path/to/script"` verhindert die Auto-Registrierung. Die vielen alten Scripts mit `comando: "run /home/..."` funktionieren NICHT mehr in V0.9.6771-beta.
- `isBinario: false` — Source-Datei (nicht kompiliert)
- `typeFile: 0` — Normale Datei (alle Source-Scripts haben 0)

### Backup-Pflicht

**IMMER BACKUP vor Schreibzugriff auf die DB:**
```python
import shutil
shutil.copy(db_path, db_path + '.bak')
```

GreyHack kann die DB bei inkonsistenten Einträgen korrumpieren. Ein Backup rettet Stunden.

Siehe `references/deployment.md` für vollständige Python-Rezepte mit SQLite-Insertion und Bootstrap-Generator.

**Wichtig:** Nach jedem Spielneustart sind alle `build`-Binaries weg — sie werden nur im Arbeitsspeicher gehalten. Die `.src`-Source-Dateien müssen persistiert werden (entweder per Bootstrap neu geladen oder in DB gespeichert).
