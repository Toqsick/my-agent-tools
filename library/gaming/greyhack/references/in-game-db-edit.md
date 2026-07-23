# GreyHack In-Game Storage — Direct DB-Edit Workflow

**Wichtigster Befund 2026-07-03:** Die GreyHack-Spielwelt (inkl. In-Game `/home/Bratan/`-Filesystem) liegt komplett in einer **SQLite-DB** namens `GreyHackDB.db`. Im Spiel gibt es KEIN wget/curl — und der Platz im In-Game-PC ist hart limitiert (z.B. 350 MB HDD auf Bastis PC, belegt mit 358 GB). Script-Konsolidierung allein reicht nicht, wenn der Player eh schon zu viel Müll drin hat.

## Wo liegt das Savegame?

```bash
# Native Linux Steam:
~/.local/share/unity3d/Loading Home/Grey Hack/

# Flatpak Steam (Bastis Setup):
/home/bratan/.var/app/com.valvesoftware.Steam/.config/unity3d/Loading Home/Grey Hack/

# Die eigentliche Game-DB:
Grey Hack_Data/GreyHackDB.db

# Fork/Backup von Basti:
/home/bratan/.hermes/Grayhack Game + Data (fork)/Grey Hack/Grey Hack_Data/GreyHackDB.db
```

**NICHT** in `userdata/<uid>/227860/` (das ist nur Cloud-Sync, hier leer bei Basti).

## DB-Schema (verifiziert 2026-07-03)

```sql
-- Die 19 relevanten Tabellen:
Players              -- Player-Metadaten (ComputerID, Missions, Wallet, ...)
Computer             -- ALLE Computer (Player + NPC + Router)
  WHERE IsPlayer=1   -- Filter für Player-PC
Files                -- File-Content als TEXT (mit refCount)
Passwords            -- 267 Rows, alle Hashes
Map                  -- Netzwerk-Topologie
BankAccounts         -- 4 Rows
MailAccounts         -- 7 Rows
WebPages             -- 48 Rows
Logs                 -- Server-Logs
InfoGen              -- World-Seed, Guilds, Versions
```

### Computer.FileSystem JSON-Struktur

```json
{
  "computerID": "uuid",
  "files": [...],         // top-level files (meist leer)
  "folders": [            // rekursiv verschachtelt
    {
      "nombre": "etc",    // WICHTIG: spanisches Wort für "name"!
      "owner": "root",
      "permisos": {"permisos": "-rw-r--r--"},
      "files": [
        {
          "ID": "uuid",   // verweist auf Files.ID
          "nombre": "passwd",
          "size": 0,      // in KB (GreyHack inflated: 1 Binary ≈ 5 GB)
          "isBinario": false,
          "permisos": {"permisos": "-rw-------"},
          ...
        }
      ],
      "folders": [...]
    }
  ]
}
```

**WICHTIGE Felder:**
- `nombre` (NICHT `name`) — spanisch
- `permisos.permisos` (verschachtelt) — nicht direkt `permissions`
- File-Größen sind künstlich aufgeblasen: jedes Binary ~5 GB im Spiel
- Files haben `ID` als Foreign-Key auf `Files.ID` für Content

## Storage-Problem verstehen

```sql
-- Player-PC HDD-Kapazität:
SELECT Hardware FROM Computer WHERE IsPlayer=1;
-- → {"hardDisk": {"totalSize": 350, ...}}  (in MB, in-game)

-- Belegter Speicher (rekursiv summiert):
SELECT json_extract(Hardware, '$.hardDisk.totalSize') AS hdd_mb,
       Computer.* FROM Computer WHERE IsPlayer=1;
```

Realistischer Workflow:
1. SQL öffnen, Hardware auslesen → HDD-Größe
2. FileSystem-JSON parsen → recursive `size` sum
3. Wenn `sum > hdd_totalSize`: GAME SAGT "NO SPACE" → Cleanup nötig

## Cleanup-Workflow (3-Schritte-Plan)

### SCHRITT 1: Backup (PFLICHT!)

```bash
BACKUP=~/backups/greyhack/GreyHackDB-$(date +%Y%m%d-%H%M%S).db
cp "<STEAM_INSTALL>/Grey Hack/Grey Hack_Data/GreyHackDB.db" "$BACKUP"
# Auch den Fork sichern:
cp "<FORK>/Grey Hack_Data/GreyHackDB.db" "${BACKUP%.db}-fork.db"
```

**Wichtig:** Niemals die DB editieren während GreyHack läuft! SQLite kann inkonsistent werden ohne sauberes WAL/SHM-Handling. Game schließen vor Edit.

### SCHRITT 2: Klassifizierung (Whitelist-Pattern)

User-Scripts vs. System-Programme trennen. **Bei Basti IMMER Whitelist pflegen**, weil er explizit warnt: "da sind System-Programme drin wie apt".

```python
WHITELIST = {
    "apt-get", "bash", "cat", "cd", "chmod", "chgrp", "chown", "cp", "mv",
    "rm", "mkdir", "rmdir", "ls", "pwd", "ln", "touch",
    "ps", "kill", "passwd", "groups", "groupadd", "groupdel",
    "useradd", "userdel", "sudo", "whoami",
    "ssh", "scp", "ftp", "ifconfig", "iwconfig", "iwlist", "ping", "nslookup", "whois",
    "aircrack", "aireplay", "airmon", "sniffer", "rshell-server", "ftp-server",
    "chat-server", "repository-server", "get_lib", "decipher", "scanlib", "scanrouter", "build",
    "man", "reboot",
}
```

USER-SCRIPTS erkennen an:
- Keywords: `dee_strike`, `minimal_dee`, `test_local`, `mission_`, `myprogram`, `nomad`
- Owner: `gregor` statt `root` → wahrscheinlich User-generated
- Naming-Pattern: kein Standard-Unix-Tool

### SCHRITT 3: JSON-Mutation (NICHT File-by-File löschen!)

GreyHack speichert Files in der `Files`-Tabelle mit `refCount`. Saubere Methode:

```python
import sqlite3, json, shutil
import uuid, os

db_path = "<STEAM_INSTALL>/Grey Hack/Grey Hack_Data/GreyHackDB.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Aktuellen Player-PC FileSystem holen
cursor.execute("SELECT FileSystem FROM Computer WHERE IsPlayer=1")
fs = json.loads(cursor.fetchone()[0])

# 2. Helper: Folder rekursiv finden
def find_folder(node, name):
    if node.get("nombre") == name: return node
    for f in node.get("folders", []):
        r = find_folder(f, name)
        if r: return r
    return None

# 3. Files filtern (Whitelist anwenden)
TO_DELETE = {"myprogram", "dee_strike", "test_local", "minimal_dee", "xwifi", ...}
bin_folder = find_folder(fs, "bin")
bin_folder["files"] = [f for f in bin_folder["files"] if f.get("nombre") not in TO_DELETE]

# 4. Zurückschreiben
new_fs = json.dumps(fs)
cursor.execute("UPDATE Computer SET FileSystem = ? WHERE IsPlayer = 1", (new_fs,))
conn.commit()
conn.close()
```

**NICHT** `DELETE FROM Files WHERE ...` machen! Wenn refCount nicht stimmt, crasht das Spiel beim nächsten Laden.

## Neues Script ins Spiel einfügen

### ⚠️ VORBEREITUNG: `//command:` Marker setzen (NEU 2026-07-03)

**Jeder Source-Script-Eintrag in der DB MUSS als erste Zeile `//command: <name>` haben!** Ohne diesen Marker erkennt `build` die Datei als Binary und verweigert die Kompilierung ("Can't build. Binary file.").

```python
# Vor dem Insert prüfen und ggf. fixen:
import os

with open("/path/to/script.src") as f:
    content = f.read()

if not content.startswith("//command:"):
    name = os.path.basename(path).replace(".src", "")
    # Alte erste Zeile durch Marker ersetzen
    lines = content.split("\n")
    lines[0] = "//command: " + name
    content = "\n".join(lines)
```

**Build-Workflow nach DB-Insert (V0.9.6771-beta):**
- `run` existiert NICHT! **`launch` existiert auch NICHT!**
- Der korrekte Workflow: Source in `/home/<USER>/Config/<name>.src` platzieren (via FileSystem JSON) mit `//command:<name>` als erster Zeile → dann einfach `<name>` in der Shell tippen
- Source-Dateien in Config/ mit `//command:` werden automatisch als Shell-Commands geladen — kein Build nötig
- `build <src> <output-folder>` existiert, erzeugt aber /bin/-artige Binaries die nach Game-Restart verloren sind
- `comando`-Feld im FileSystem-JSON sollte immer leer sein (`comando: ""` — nicht `"run ..."` füllen!)
- **Datei darf NICHT in `/home/gregor/` root liegen!** Muss in `/home/gregor/Config/` sein

### Insert in Files-Tabelle + FileSystem-JSON

```python
# yuno.src als File in Files-Tabelle einfügen
import uuid
yuno_id = str(uuid.uuid4())

with open("/path/to/yuno.src") as f:
    content = f.read()

cursor.execute("INSERT INTO Files (ID, Content, refCount) VALUES (?, ?, 1)",
               (yuno_id, content))

# Dann im FileSystem-JSON als neuer Eintrag
config = find_folder(find_folder(fs, "home"), "gregor")
config_folder = find_folder(config, "Config")
if config_folder is None:
    config["folders"].append({"nombre": "Config", "owner": "gregor", "files": [], ...})

config_folder["files"].append({
    "ID": yuno_id,
    "nombre": "yuno.src",
    "permisos": {"permisos": "-rw-------"},
    "owner": "gregor",
    ...
})

# Speichern
cursor.execute("UPDATE Computer SET FileSystem = ? WHERE IsPlayer = 1", (json.dumps(fs),))
conn.commit()
```

## Pitfalls

| Pitfall | Fix |
|---------|-----|
| `nombre` vs `name` | GreyHack nutzt spanisch `nombre` für File-/Folder-Namen |
| `permisos.permisos` doppelt verschachtelt | `f["permisos"]["permisos"]`, nicht `f["permisos"]` |
| File-Größen künstlich 5 GB | Beim Auswerten nicht wundern, ist Game-Design |
| Fork und Main müssen synchron sein | Nach Main-Edit IMMER auch Fork kopieren |
| DB nicht offen lassen während GreyHack läuft | Game schließen, edit, neustarten |
| `DELETE FROM Files` ohne refCount-Update | Spiel crasht — JSON-Filter statt DB-DELETE |
| Player-Hardware-Tausch | Im Spiel `apt upgrade hardware` oder via DB JSON-Edit in `Hardware`-Spalte |
| `//command:` Marker fehlt | Source-Script wird als Binary erkannt → `build` verweigert. Fix: erste Zeile auf `//command: <name>` setzen |
| `comando` Feld darf nicht `"run ..."` sein | Im FileSystem-JSON sollte `comando: ""` für Source-Files sein. Füllen mit `"run ..."` verursacht Fehlinterpretation |

## Lessons Learned (diese Session)

1. **Bastis Warnung war berechtigt:** "da sind System-Programme drin wie apt" — IMMER Whitelist anwenden, sonst killt man `apt-get`, `ssh`, `bash` und das Spiel ist nicht mehr benutzbar.

2. **Storage-Realität:** Bastis PC hat 350 MB HDD aber 358 GB belegt (102% voll). Konsolidierung allein (31 Scripts → 1 Script) reicht NICHT — direkter DB-Edit der In-Game-Files ist nötig.

3. **Sandbox-Trennung:** Zwei Save-Locations:
   - `Grey Hack/yuno-tools/` = TEMPLATE-Sammlung auf Disk (kein In-Game-Speicher)
   - `GreyHackDB.db` = In-Game-Filesystem (BINÄR im Savegame)
   - User kann verwechseln welche "Platz" meint — erst fragen, dann handeln.

4. **Vor jedem DB-Edit: Backup.** Bei diesem Cleanup: 1 Backup von Main, 1 Backup von Fork, beide timestamped. Rollback in 5 Sekunden möglich.

5. **yuno.src ist jetzt im Spiel unter `/home/gregor/Config/yuno.src`** — alle alten /bin/-Scripts sind weg, User hat 47.75 GB freigegeben bekommen.

6. **⚠️ `//command:` Marker + Config/ Path ist kritisch für DB-Injection (NEU 2026-07-03):** Beim Einfügen von Yuno V6 via SQLite (78 KB) wurde der Source-Script-Marker `//command: yuno_v6` vergessen. Nach Fix der ersten Zeile und Platzierung in `/home/gregor/Config/` statt `/home/gregor/` root → Script war als Command verfügbar. Für jeden DB-Insert zwingend prüfen: `//command:` erste Zeile + Datei in Config/ Ordner.

## Verifikations-Checkliste nach Cleanup

```python
# Nach DB-Edit IMMER prüfen:
# 1. System-Programme noch da?
for crit in ["apt-get", "ssh", "bash", "cat"]:
    assert any(f["nombre"] == crit for f in bin_folder["files"]), f"MISSING: {crit}"

# 2. User-Scripts weg?
for deleted in ["myprogram", "dee_strike", "test_local"]:
    assert not any(f["nombre"] == deleted for f in bin_folder["files"]), f"STILL THERE: {deleted}"

# 3. Total belegt?
def total_size(node):
    s = sum(f.get("size", 0) for f in node.get("files", []))
    return s + sum(total_size(f) for f in node.get("folders", []))
print(f"Belegt: {total_size(fs)/(1024*1024):.2f} GB")
```

## Siehe auch

- `references/storage-consolidation.md` — Script-Konsolidierung (Vorstufe zu diesem DB-Edit)
- `templates/yuno-all-in-one.src` — Working Template, 17 KB, alle 6 Subcommands
- `~/docs/system/greyhack-storage-cleanup-2026-07-03.md` — Session-Doku mit konkreten Zahlen