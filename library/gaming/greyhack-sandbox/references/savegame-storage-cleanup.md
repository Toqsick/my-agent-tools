# GreyHack Savegame — In-Game Storage Cleanup

Reference für die DB-gestützte Analyse und das Cleanup des In-Game Filesystems.

## Savegame-Pfade (verschiedene Setups)

| Setup | DB-Pfad |
|-------|---------|
| Steam Native Linux (Standard) | `/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db` |
| Flatpak Steam | `/home/bratan/.var/app/com.valvesoftware.Steam/.config/unity3d/Loading Home/Grey Hack/GreyHackDB.db` |
| Fork / Backup | `/home/bratan/.hermes/Grayhack Game + Data (fork)/Grey Hack/Grey Hack_Data/GreyHackDB.db` |

**WICHTIG:** Es gibt **EINE DB pro GreyHack-Installation** — GreyHack speichert alles in einer einzigen `GreyHackDB.db` direkt im Spielordner unter `Grey Hack_Data/`. Cloud-Sync nutzt Steam userdata unter `<userid>/227860/remote/`, ist aber optional und existiert bei Bratan NICHT.

## DB-Schema (Stand 2026-07-03)

19 Tabellen:

- `BackupPlayerFiles` (ID, Content, RouterID)
- `BackupPlayers` (ID, FileSystem, IsRouter, Users, ConfigOS, Hardware)
- `BankAccounts` (Transactions, User PRIMARY KEY, Password)
- `CTFs` (EventName PRIMARY KEY, EventContent, OwnerPlayerID)
- `Coins` (CoinName PRIMARY KEY, CoinContent, OwnerPlayerID, WebAddress)
- `Computer` (FileSystem, Hardware, IsRouter, IsPlayer, IsRented, Users, ConfigOS, Procs, IsCTF, ID PRIMARY KEY)
- `Files` (ID PRIMARY KEY, Content, refCount)
- `InfoGen` (Seed, VersionsControl, Exploits, Guilds, Clock, DeleteVersion, AllLibs, Invoices, GlobalMoney, ZeroDaySystem)
- `Logs` (ID PRIMARY KEY, Log)
- `MailAccounts` (Mails, User PRIMARY KEY, password)
- `Map` (Network topology)
- `Passwords` (267 rows typical)
- `PlayerConns`, `SharedConns` (Network conns)
- `Players` (1 row — current player)
- `Stocks`, `Wallets`, `WebPages`

## Player-Computer identifizieren

```sql
-- Spieler-PC ID + Daten
SELECT ID, FileSystem, Hardware FROM Computer WHERE IsPlayer = 1;

-- Spieler-Info
SELECT ComputerID, Nickname, Storage, Missions, BankUser FROM Players;
```

## FileSystem JSON Struktur (KRITISCH!)

Das `FileSystem`-Feld ist **JSON**, NICHT eine eigene Tabelle. Fieldnames sind **SPANISCH** (`nombre` statt `name`):

```json
{
  "computerID": "171a9e0f-f9f9-4d76-8f37-d125d3f3e181",
  "files": [],
  "folders": [
    {
      "files": [
        {
          "ID": "b54fbd56c5a4f78363fb74dde99d1b56",
          "nombre": "passwd",
          "permisos": {"permisos": "-rw-r-----"},
          "owner": "root",
          "group": "root",
          "size": 0,
          "isBinario": false,
          "isEditedOtherPlayer": false,
          "passEncrypt": "",
          "comando": "",
          "process": "",
          "serverPath": "",
          "symlink": "",
          "isProtected": false,
          "isDefaultContent": false,
          "missionID": "",
          "typeFile": 0,
          "precio": 0,
          "allowImport": false,
          "saved": true,
          "desc": null,
          "helperImport": null,
          "origOwnerID": ""
        }
      ],
      "folders": [...],
      "nombre": "etc",
      "owner": "root",
      "group": "root",
      "permisos": {...},
      "size": 0
    }
  ]
}
```

## In-Game Storage Calculation

```python
import sqlite3, json

db = "/mnt/DATA/.../Grey Hack_Data/GreyHackDB.db"
conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute("SELECT FileSystem FROM Computer WHERE IsPlayer=1")
fs = json.loads(cur.fetchone()[0])

def total_size(node):
    """Rekursive Größen-Summe in BYTES."""
    s = sum(f.get("size", 0) for f in node.get("files", []))
    s += sum(total_size(f) for f in node.get("folders", []))
    return s

# Hardware-Limit (in MEGABYTES, NICHT bytes!)
cur.execute("SELECT Hardware FROM Computer WHERE IsPlayer=1")
hw = json.loads(cur.fetchone()[0])
hdd_total_mb = hw["hardDisk"]["totalSize"]  # z.B. 350 MB

# Tatsächlich belegt (in BYTES → GB konvertieren)
used_gb = total_size(fs) / (1024 ** 3)
print(f"HDD: {hdd_total_mb} MB, Used: {used_gb:.2f} GB")
# WARNUNG: Wenn used_gb > hdd_total_mb → ÜBERFÜLLT (Script-Output Fehler!)
```

**Fallstrick:** GreyHack zählt `size` in BYTES, das HDD-Limit aber in **MB** (Dezimal). Skala ist **nicht 1:1 umrechenbar** — wenn das Spiel ein 5 KB Script als binary kompiliert, wird es ~5 GB groß. Das ist ein Design-Quirk: in-game binaries sind riesig im Vergleich zur HDD.

## Top-Folder Übersicht (typisches Layout)

```
/etc    (3-4 GB)
/lib    (3 GB)
/sys    (13 GB)
/root   (0)
/home   (27 GB)   ← Desktop & Downloads
/var    (3-4 GB)
/bin    (218 GB!)  ← Scripts + binaries
/usr    (61 GB)
/boot   (9 GB)
/server (16 GB)
```

**`/bin/` ist fast immer der Schuldige**, weil dort kompilierte Scripts landen.

## Cleanup-Workflow (wenn HDD voll)

### Option 1: In-Game `rm` (sicherster Weg)

Im Spiel-Terminal:
```bash
# Große Brocken identifizieren
ls -la /bin/ | sort -k5 -n -r | head -10

# Aufräumen
rm /bin/dee_strike
rm /bin/minimal_dee
rm /bin/test_local
```

Vorteil: Spiel speichert automatisch, kein Risiko.
Nachteil: Muss IM SPIEL gemacht werden, dauert.

### Option 2: DB direkt editieren (schneller, aber riskanter)

```python
import sqlite3, json

conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT FileSystem FROM Computer WHERE IsPlayer=1")
fs = json.loads(cur.fetchone()[0])

WHITELIST = {"ssh", "apt-get", "cat", "get_lib", "scp", "ping", "ps"}

def clean_bin(node):
    if node.get("nombre") == "bin":
        kept = [f for f in node.get("files", []) if f.get("nombre") in WHITELIST]
        removed = len(node.get("files", [])) - len(kept)
        node["files"] = kept
        print(f"/bin: {removed} files removed, {len(kept)} kept")
        return
    for sub in node.get("folders", []):
        clean_bin(sub)

clean_bin(fs)
new_fs = json.dumps(fs)
cur.execute("UPDATE Computer SET FileSystem = ? WHERE IsPlayer = 1", (new_fs,))
conn.commit()
conn.close()
```

### Option 3: All-in-One Scripter installieren (BESTE Lösung)

Siehe `~/greyhack-tools/yuno.src` oder `yuno-tools/yuno.src` für ein
~17 KB Script, das 31 separate Scripts ersetzt. Spart 80 KB auf der Disk
UND 200+ GB in-game, weil nur EIN binary gebuildet wird.

## Pitfalls

1. **DB IMMER backup vor direkten Edits:** `cp GreyHackDB.db GreyHackDB.db.bak`
2. **Spiel MUSS geschlossen sein beim DB-Edit** — sonst überschreibt das Spiel deine Änderungen beim nächsten Save.
3. **Field-Name ist `nombre` (spanisch), NICHT `name`** — die `Files`-Tabelle hat ein `ID` Feld, aber Folder/Files im FileSystem-JSON haben `nombre`.
4. **`isBinario: true`** markiert kompilierte Scripts/Binaries. Diese sind die Speicherfresser.
5. **Hardware-Upgrade als Alternative:** Bessere HDD kaufen im Spiel (größere `totalSize`) ist sicherer als Cleanup, aber teurer.
6. **Storage-Overflow ist ein Bug-Trigger:** Das Spiel zeigt Fehlermeldungen, weil die HDD überfüllt ist (size > totalSize in MB). Manche Aktionen schlagen fehl ohne klare Fehlermeldung.

## Whitelist-basierte /bin/ Bereinigung (2026-07-03, verified Bratan-Setup)

**WICHTIG:** NIEMALS blind alle Files in `/bin/` löschen — System-Programme müssen bleiben! Bratan hat das explizit gewarnt ("achte auf apt-get etc.").

### Kategorie A: KRITISCH (nie löschen)
- **Package Manager:** `apt-get`
- **Core File-Ops:** `cat`, `cd`, `cp`, `mv`, `rm`, `mkdir`, `rmdir`, `ls`, `pwd`, `ln`, `chmod`, `chown`, `chgrp`, `touch`
- **User/Process:** `ps`, `kill`, `passwd`, `groups`, `groupadd`, `groupdel`, `useradd`, `userdel`, `sudo`, `whoami`
- **Network Base:** `ssh`, `scp`, `ftp`, `ifconfig`, `iwconfig`, `iwlist`, `ping`, `nslookup`, `whois`
- **Shell/System:** `bash`, `man`, `reboot`

### Kategorie B: HACK-TOOLS (System, behalten)
`aircrack`, `aireplay`, `airmon`, `sniffer`, `rshell-server`, `ftp-server`, `chat-server`, `repository-server`, `get_lib`, `decipher`, `scanlib`, `scanrouter`, `build`

### Kategorie C: USER-SCRIPTS (löschbar)
Erkennungs-Pattern (Keywords im Filename): `dee_strike`, `dee_hack`, `minimal_dee`, `test_local`, `mission_`, `strike`, `myprogram`, `nomad`, `bruteforce`, `decipher_manual`, `phase0`, `phase1`, `dee_recon`, `deep_recon`, `multihop`, `bank_grab`, `hardening`, `game_dee_hack`, `game_test_debug`, `gabriellia`, `bobina_emmer`, `dee_grettib`, `xwifi` (Achtung: `xwifi` ist NICHT Standard-GreyHack, war in Bratan's Welt gregor-owned).

### Detection-Strategie
1. **Field `owner`:** root-owned = wahrscheinlich System, gregor-owned = User-Script
2. **Field `typeFile`:** typeFile=1 = Binary, typeFile=0 = File
3. **Filename-Match:** gegen Keyword-Liste
4. **Bei Unbekannt:** Manuell prüfen — gibt auch False-Positives!

### Vollständiger Cleanup-Workflow (mit Whitelist)

```python
import sqlite3, json, shutil, os
from datetime import datetime

DB = "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db"
FORK_DB = "/home/bratan/.hermes/Grayhack Game + Data (fork)/Grey Hack/Grey Hack_Data/GreyHackDB.db"
BACKUP_DIR = "/home/bratan/backups/greyhack"

# 1. Backup (IMMER vor DB-Edits!)
os.makedirs(BACKUP_DIR, exist_ok=True)
ts = datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy2(DB, f"{BACKUP_DIR}/GreyHackDB-{ts}.db")

# 2. Whitelist (Kategorie A + B)
WHITELIST = {
    "apt-get", "cat", "cd", "cp", "mv", "rm", "mkdir", "rmdir", "ls", "pwd", "ln",
    "chmod", "chown", "chgrp", "touch", "ps", "kill", "passwd", "groups",
    "groupadd", "groupdel", "useradd", "userdel", "sudo", "whoami", "ssh", "scp",
    "ftp", "ifconfig", "iwconfig", "iwlist", "ping", "nslookup", "whois", "bash",
    "man", "reboot", "aircrack", "aireplay", "airmon", "sniffer", "rshell-server",
    "ftp-server", "chat-server", "repository-server", "get_lib", "decipher",
    "scanlib", "scanrouter", "build",
}

# 3. DB öffnen, /bin/ filtern
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT FileSystem FROM Computer WHERE IsPlayer=1")
fs = json.loads(cur.fetchone()[0])

def find(node, name):
    if node.get("nombre") == name: return node
    for f in node.get("folders", []):
        r = find(f, name)
        if r: return r
    return None

bin_folder = find(fs, "bin")
before = len(bin_folder["files"])
bin_folder["files"] = [f for f in bin_folder["files"] if f.get("nombre") in WHITELIST]
after = len(bin_folder["files"])
print(f"/bin/: {before} → {after} Files ({before - after} gelöscht)")

# 4. Zurückschreiben
cur.execute("UPDATE Computer SET FileSystem = ? WHERE IsPlayer = 1", (json.dumps(fs),))
conn.commit()

# 5. Sync zur Fork-DB falls vorhanden (WICHTIG: beide DBs sync halten)
if os.path.exists(FORK_DB):
    shutil.copy2(DB, FORK_DB)

# 6. Disk flush (vor allem bei laufendem Spiel)
os.sync()
conn.close()
```

### Erwartete Ergebnisse (typischer Cleanup)
- 7-10 User-Scripts gelöscht → ~30-50 GB in-game frei
- `/bin/` von 57 → 50 Files
- HDD bleibt ~überfüllt (GreyHack-Design: 350 MB HDD gegen Scripts die ~5 GB zählen)

### Adding new .src files via DB-Edit (yuno.src installieren)

Wenn ein Script in `/home/gregor/Config/` eingefügt werden soll:

```python
import sqlite3, uuid

DB = "/path/to/GreyHackDB.db"
SOURCE_FILE = "/path/to/yuno.src"

with open(SOURCE_FILE) as f:
    content = f.read()

conn = sqlite3.connect(DB)
cur = conn.cursor()

# 1. Neuen Eintrag in Files-Tabelle
file_id = str(uuid.uuid4())
cur.execute("INSERT INTO Files (ID, Content, refCount) VALUES (?, ?, 1)",
            (file_id, content))

# 2. Im FileSystem-JSON referenzieren
cur.execute("SELECT FileSystem FROM Computer WHERE IsPlayer=1")
fs = json.loads(cur.fetchone()[0])

# 3. Config-Folder finden (oder erstellen)
config = None
for f in fs.get("folders", []):  # home, etc.
    if f.get("nombre") == "gregor":
        for sub in f.get("folders", []):
            if sub.get("nombre") == "Config":
                config = sub
                break
        if not config:
            config = {"nombre": "Config", "owner": "gregor", "group": "gregor",
                      "permisos": {"permisos": "drwx------"}, "files": [], "folders": [],
                      "comando": "", "symlink": "", "size": 0, "process": "",
                      "serverPath": "", "isProtected": False, "missionID": "",
                      "typeFile": 1, "isDefaultContent": False}
            f["folders"].append(config)
        break

# 4. File-Entry hinzufügen
if config:
    config["files"].append({
        "ID": file_id, "precio": 0, "isBinario": False,
        "allowImport": False, "isEditedOtherPlayer": False,
        "origOwnerID": "", "saved": True, "desc": None,
        "helperImport": None, "passEncrypt": "", "nombre": "yuno.src",
        "permisos": {"permisos": "-rw-------"}, "owner": "gregor",
        "group": "gregor", "comando": "", "symlink": "", "size": 0,
        "process": "", "serverPath": "", "isProtected": False,
        "missionID": "", "typeFile": 0, "isDefaultContent": False
    })

# 5. Update
cur.execute("UPDATE Computer SET FileSystem = ? WHERE IsPlayer = 1",
            (json.dumps(fs),))
conn.commit()
conn.close()
```

### Sync zwischen Main-DB und Fork-DB

Bratan hat **zwei** GreyHack-Installationen:
- **Main-DB:** `/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db` (aktive)
- **Fork-DB:** `/home/bratan/.hermes/Grayhack Game + Data (fork)/Grey Hack/Grey Hack_Data/GreyHackDB.db` (Backup/Clone)

Beide MÜSSEN nach DB-Edits synchron sein:
```python
shutil.copy2(MAIN_DB, FORK_DB)  # oder umgekehrt
```

Ohne Sync divergieren die Welten, was zu komischen Verhalten führt.

## Test-Commands

```bash
# Player-Inventur — Top 20 größte Files
sqlite3 "$DB" "SELECT FileSystem FROM Computer WHERE IsPlayer=1" | python3 -c "
import json, sys
fs = json.loads(sys.stdin.read())
def walk(node, p=''):
    for f in node.get('files', []):
        print(f'{p}/{f[\"nombre\"]} {f.get(\"size\",0)}B')
    for fold in node.get('folders', []):
        walk(fold, p + '/' + fold.get('nombre','?'))
walk(fs)
" | sort -k2 -n -r | head -20

# Total belegt
sqlite3 "$DB" "SELECT FileSystem FROM Computer WHERE IsPlayer=1" | python3 -c "
import json, sys
fs = json.loads(sys.stdin.read())
def total(n):
    s = sum(f.get('size',0) for f in n.get('files',[]))
    s += sum(total(x) for x in n.get('folders',[]))
    return s
print(f'Total: {total(fs)/(1024**3):.2f} GB')
"
```

## Related

- `greyhack` skill — GreyScript Sprache + Tools
- `yuno-tools-deployment` — In-Game Tool Deployment
- `references/violet-tool-integration.md` — Viper 2.2.1 als erweiterbares Tool (Plugin-Architektur via `getviper`)
- `references/greybel-test-pattern.md` — greybel execute als Mock-Test-Workflow für GreyScript-Validierung

## Viper Integration (2026-07-03)

User-Wunsch: "YunoinGrey über Viper bauen". Viper 2.2.1 ist ein vollständiges interaktives Hacking-Terminal-Tool (162 KB, 85 Commands, Theme-System, Session-Management).

**Viper GitHub:** https://github.com/EntitySeaker/viper-git (Build-Script in build.sh / build.py)

**Plugin-Mechanismus:** Viper hat `getviper [PATH]` Command — lädt eine andere Viper-Instanz und teilt deren Objects + Libraries via `get_custom_object`/`hasIndex` Pattern.

**Viper-Commands im Überblick (Aus main/main.src):**
- **Recon:** `nmap`, `exploitscan`, `exploit`, `targets`, `use`, `back`, `deltarget`
- **Filesystem:** `ls`, `cat`, `fs`, `ps`, `corruptlogs`, `buffer`
- **Crypto:** `md5`, `sha256`, `gpg`, `crack`, `airmon`, `iwlist`, `aireplay`, `aircrack`
- **Netzwerk:** `ssh`, `sudo`, `jump`, `msfvenom`, `msfconsole`, `grab`, `findlib`, `deepscan`, `sniffer`
- **Files:** `mv`, `cp`, `rm`, `touch`, `mkdir`, `write`, `compile`, `chmod`, `chown`, `chgrp`, `passwd`
- **User/Group:** `adduser`, `deluser`, `groups`, `addgroup`, `delgroup`, `passwd`
- **Library:** `libs`, `uselib`, `getlib`, `dellib`, `scanlib`
- **Sessions:** `addobject`, `shell`, `exec`, `kill`
- **Settings:** `vars`, `addvar`, `delvar`, `save-settings`, `load-theme`, `secure`, `wipe`
- **Hilfs:** `help`, `clear`, `credits`, `loop`, `apt-get`, `get`, `put`, `nslookup`, `whois`, `echo`, `exit`, `return`, `getviper`

**Was Yuno ergänzt (was Viper fehlt):**
- `hack` — Auto-Exploit + SSH-Brute + Auto-Loot in EINEM Befehl (Viper: manuell nmap → exploitscan → exploit → ssh → cat)
- `bank` — HTTP-Bank-Transfer (Viper hat keinen Banking-Workflow)
- `defend` — System-Security-Check (Viper hat `corruptlogs` aber keinen Defense-Scan)

**Integrations-Plan (für nächste Session):**
- Option A: `yuno.src` als Viper-Plugin via `getviper` laden (15 min, hybrid)
- Option B: Yuno-Viper-Hybrid-Script (30 min, custom command set)
- Option C: Yuno komplett auf Viper-Skelett (1h, vereinheitlicht)

Viper baut sauber: `greybel build viper.src -u` → Exit 0.

## greybel execute Test-Pattern (2026-07-03)

GreyScript-Scripts können **vor dem Im-Spiel-Einsatz** mit `greybel execute` getestet werden. Das hat einen echten Bug gefunden:

```bash
# Test mit Mock-Env
greybel execute yuno.src -p "defend" --silent
# → Exit 0 wenn OK
# → Exit 1 mit "Runtime error" wenn Bug
```

**Bug-Beispiel:** `print(... + p.service + ...)` crashed in Mock-Env weil nicht alle Port-Objekte ein `service` Map-Feld haben. **Fix:** Robuster `typeof() + indexOf()` Check vor jedem Map-Zugriff.

**Lessons:**
1. IMMER mit `greybel execute` testen, bevor du ein Script ins Spiel packst
2. Mock-Env ist strenger als GreyHack — Bugs die in Mock crashen, würden in Game auch crashen
3. `-p <args>` übergibt PARAMS (nicht Script-Name) — params[0] ist das erste Argument
4. `--silent` unterdrückt Progress-Bar-Warnings