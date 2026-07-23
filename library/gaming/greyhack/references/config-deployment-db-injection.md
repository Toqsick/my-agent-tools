# Config/-Deployment via DB Injection (2026-07-04)

## Problem

GreyHack V0.9.6771-beta erkennt Source-Scripts in der DB nur, wenn sie:
1. `//command: <name>` als erste Zeile haben
2. Unter `/home/<USER>/Config/` im FileSystem-JSON liegen
3. In der `Files`-Tabelle mit `refCount > 0` existieren

Ein reiner `INSERT INTO Files` reicht NICHT — die Datei muss auch im
`Computer.FileSystem`-JSON des Player-Computers verlinkt sein, sonst
findet der CodeEditor sie nicht.

## Die Zwei-Schritte-Methode

### Schritt 1: Files-Tabelle befüllen

```sql
INSERT INTO Files (ID, Content, refCount) 
VALUES ('Config/<name>.src', '<kompletter Source-Code mit //command: als erster Zeile>', 1);
```

**ID-Format:** Relativer Pfad `Config/<name>.src` (NICHT UUID, NICHT absolut).
Das Spiel löst den Pfad relativ zu `/home/<user>/` auf.

**Content:** MUSS mit `//command: <name>` beginnen — sonst erkennt das Spiel
die Datei nicht als Script (Fehler: "Can't build. Binary file.").

### Schritt 2: FileSystem-JSON aktualisieren

```python
import sqlite3, json

db = sqlite3.connect("GreyHackDB.db")
fs = json.loads(db.execute("SELECT FileSystem FROM Computer WHERE IsPlayer=1").fetchone()[0])

def find_folder(node, target):
    if isinstance(node, dict):
        if node.get('nombre') == target:
            return node
        for f in node.get('folders', []):
            result = find_folder(f, target)
            if result:
                return result
    return None

# Config-Ordner unter /home/<user>/Config/ finden
config = find_folder(fs, 'Config')
if not config:
    user_folder = find_folder(fs, '<username>')
    config = {"nombre": "Config", "owner": "<user>", "files": [], "folders": []}
    user_folder["folders"].append(config)

new_entry = {
    "ID": "Config/<name>.src",
    "nombre": "<name>.src",
    "permisos": {"permisos": "-rwxr-xr-x"},
    "owner": "<user>",
    "group": "<user>",
    "isBinario": False,
    "allowImport": True,
    "typeFile": 0,
    "size": <länge>,
    "comando": "",
    "saved": True,
    "isProtected": False,
}
config["files"].append(new_entry)
db.execute("UPDATE Computer SET FileSystem = ? WHERE IsPlayer = 1", (json.dumps(fs, separators=(',', ':')),))
db.commit()
```

### Schritt 3: Verifikation

```sql
SELECT ID, length(Content), refCount FROM Files WHERE ID LIKE 'Config/%';
SELECT json_extract(FileSystem, '$') FROM Computer WHERE IsPlayer = 1;
PRAGMA integrity_check;
```

## In-Game-Nutzung

Nach erfolgreicher Injection:
1. CodeEditor → Ctrl+O → `/home/<user>/Config/<name>.src`
2. Build-Button → `<name>`
3. Shell: `<name>`

**Ohne Build:** Config/-Dateien mit `//command:` sind automatisch als Shell-Commands
verfügbar. Einfach `<name>` in der Shell tippen.

## Bekannte Fehler

| Fehler | Ursache | Fix |
|--------|---------|-----|
| "Can't build. Binary file." | `//command:` fehlt | Erste Zeile fixen |
| Datei in CodeEditor unsichtbar | FileSystem-JSON nicht aktualisiert | Schritt 2 ausführen |
| "File not found" beim Öffnen | ID-Mismatch Files↔FileSystem | IDs angleichen |
| Build-Output nicht in Shell | Datei nicht in Config/ | Nach Config/ verschieben |
