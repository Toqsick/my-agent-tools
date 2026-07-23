# YUNO V2 — Interactive GreyHack Framework Pattern

Stand 2026-07-03. Inspiriert von Viper 2.2.1 (EntitySeaker, https://github.com/EntitySeaker/viper-git).

## Was ist YUNO V2?

YUNO V2 ist ein **interaktives GreyHack-Hacking-Framework** als kompakte Alternative zu Viper.
**45 KB** in einer einzigen `.src` Datei (Viper: 162 KB = **72% größer**) mit **45 Commands**.

## Architektur

| Komponente | Größe | Funktion |
|------------|-------|----------|
| Color System | ~700 bytes | 7 Farben + `style()` helper |
| Utility | ~1.2 KB | `is_valid_ip`, `to_int` |
| Session Management | ~2.5 KB | `main_session`, `add_session`, `go_back` |
| Library Import | ~800 bytes | Auto-load Metaxploit/Crypto/AptClient |
| 45 Commands | ~30 KB | siehe Befehlsliste unten |
| Main Loop | ~1.5 KB | `user_input` prompt + dispatch |
| **TOTAL** | **45 KB** | (vs Viper: 162 KB) |

## Command-Liste (45 Befehle)

### CORE
- `help`, `exit`, `clear`, `credits`, `echo`

### SESSION (Viper-kompatibel)
- `targets`, `use <N>`, `back`
- `jump [PATH] [NAME]`, `msfconsole`

### SCAN / HACK
- `nmap <IP>`, `exploitscan <IP>`, `deepscan <IP>`
- `exploit <IP> <P> <MEM> <VULN>`
- **⭐ `hack <IP>`** — AUTO-HACK: Exploit + SSH-Brute + Auto-Loot in 1
- `ssh <U@P> <IP> [PORT]`

### FILES
- `ls [PATH]`, `cat <PATH>`, `get <PATH>`, `put [PATH] [N]`, `rm <PATH>`, `write <PATH> [>]`

### USER/SYSTEM
- `passwd <USER>`, `chmod <PATH> <PERMS>`, `chown <PATH> <USER>`, `ps`, `kill <PID>`, `corruptlogs`

### NETWORK
- `nslookup <DOMAIN>`, `whois <DOMAIN>`, `sniffer [N]`

### CRYPTO
- `md5 <STR>`, `sha256 <STR>`, **⭐ `crack <HASH>`**, `gpg` (stub)

### UTILS
- `vars`, `addvar <N> <V>`, `delvar <N>`, `libs`, `getlib <PATH>`, `loop [N]`

### YUNO-KILLER (vs Viper)
- **⭐ `loot`** — Configs vom aktuellen PC lesen
- **⭐ `defend`** — System-Check + Hardening-Tipps
- **⭐ `bank <IP> <u> <p> <acct> <amt>`** — HTTP Bank-Transfer
- `aptget install <PKG>` — apt-get Client-Wrapper

## Was YUNO V2 anders macht als VIPER

| Feature | Viper | YUNO V2 |
|---------|-------|---------|
| Größe | 162 KB | **45 KB (-72%)** |
| Auto-Hack (Exploit+Brute+Loot) | ❌ | ✅ |
| Loot-Command eigenständig | ❌ | ✅ |
| Defend-Command | ❌ | ✅ |
| Bank-Transfer | ❌ | ✅ |
| Theme-System | ✅ (komplex) | ❌ (zu Gunsten der Kompaktheit) |
| Settings speichern/laden | ✅ | ❌ |
| Macros | ✅ (Config-Datei) | ❌ |
| GPG | ✅ (komplex) | ⚠️ Stub |
| AES128 Encryption | ✅ | ❌ |
| JSON Parser | ✅ | ❌ |
| msfconsole | ✅ | ✅ (basic) |
| jump | ✅ | ✅ (basic) |
| libs/getlib/uselib | ✅ | ✅ (simplified) |

## Install-Workflow (DB-Edit)

```python
import sqlite3, json, uuid, shutil
from datetime import datetime

DB = "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db"
SRC = "/path/to/yuno_v2.src"

# 1. Backup
ts = datetime.now().strftime("%Y%m%d-%H%M%S")
shutil.copy2(DB, f"/home/bratan/backups/greyhack/yuno-v2-{ts}.db")

# 2. Source lesen
with open(SRC) as f:
    src_content = f.read()

# 3. DB INSERT (idempotent mit OR IGNORE)
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Check ob schon vorhanden
cur.execute("SELECT ID FROM Files WHERE Content LIKE '%YUNO V2.0 - GreyHack Framework%'")
existing = cur.fetchone()
if existing:
    file_id = existing[0]
    print(f"yuno_v2.src existiert bereits: {file_id}")
else:
    file_id = str(uuid.uuid4())
    cur.execute("INSERT INTO Files (ID, Content, refCount) VALUES (?, ?, 1)",
                (file_id, src_content))
    print(f"yuno_v2.src neu hinzugefügt: {file_id}")

# 4. FileSystem-JSON updaten
cur.execute("SELECT FileSystem FROM Computer WHERE IsPlayer=1")
fs = json.loads(cur.fetchone()[0])

def find(node, name):
    if node.get("nombre") == name: return node
    for f in node.get("folders", []):
        r = find(f, name)
        if r: return r
    return None

config = find(find(find(fs, "home"), "gregor"), "Config")
if config:
    has_it = any(f.get("nombre") == "yuno_v2.src" for f in config.get("files", []))
    if not has_it:
        config["files"].append({
            "ID": file_id, "precio": 0, "isBinario": False,
            "allowImport": False, "isEditedOtherPlayer": False,
            "origOwnerID": "", "saved": True, "desc": None,
            "helperImport": None, "passEncrypt": "",
            "nombre": "yuno_v2.src",
            "permisos": {"permisos": "-rw-------"},
            "owner": "gregor", "group": "gregor",
            "comando": "", "symlink": "", "size": 0, "process": "",
            "serverPath": "", "isProtected": False, "missionID": "",
            "typeFile": 0, "isDefaultContent": False
        })

cur.execute("UPDATE Computer SET FileSystem = ? WHERE IsPlayer = 1",
            (json.dumps(fs),))
conn.commit()

# 5. Fork-DB sync
FORK = "/home/bratan/.hermes/Grayhack Game + Data (fork)/Grey Hack/Grey Hack_Data/GreyHackDB.db"
import os
if os.path.exists(FORK):
    shutil.copy2(DB, FORK)

import os as _os
_os.sync()
conn.close()

print(f"✓ yuno_v2.src installiert: {file_id}")
```

## Test-Workflow (Mock-Env)

```bash
# Build verifizieren
cd "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/yuno-tools/"
npx greybel build yuno_v2.src -u
# → "Build done" wenn OK

# Interactive test mit Mock-Env (Popen mit stdin)
# Test-Script: piped commands
echo -e "credits\nexit" | npx greybel execute yuno_v2.src --silent
```

**Wichtig:** `greybel execute` simuliert die GreyHack-Umgebung aber nicht 100% — Bugs die in Mock crashen würden im Spiel auch crashen, aber Funktionen die nur in Game existieren (z.B. `obj.host_computer`) liefern null.

### Popen-Pattern für interaktive Tests

```python
import subprocess, time

def run_one(cmd, wait=0.5):
    proc = subprocess.Popen(
        ["npx", "greybel", "execute", "yuno_v2.src", "--silent"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(wait)  # WICHTIG: warten bis TTY ready
    try:
        stdout, stderr = proc.communicate(input=cmd + "\nexit\n", timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
    return stdout

# Test
out = run_one("credits")
# Output enthält TTY-noise + prompt — filter raus
```

## Im Spiel nutzen

1. CodeEditor öffnen
2. `/home/gregor/Config/yuno_v2.src` builden
3. Oder im Terminal: `run /home/gregor/Config/yuno_v2.src`
4. Yuno-Shell mit allen 45 Commands verfügbar

## Lessons Learned (Stand 2026-07-03)

1. **Single-file beats multi-file** für GreyHack-Scripts. Viper's 94 files = 162 KB overhead durch Headers/Footers. YUNO V2 in 1 file = 45 KB.
2. **Viper-Architektur (Session + main_session Map + Commands Dictionary) ist solide** — übernehmen, vereinfachen, ergänzen.
3. **Interactive shell = while not exit + user_input** pattern. TTY-Testing via subprocess.Popen mit sleeps.
4. **greybel syntax pitfalls** (siehe greyhack-sandbox SKILL.md Pitfalls #10-13):
   - Kein `if X then stmt; return` Einzeiler
   - Kein `.strip()` (manual loop)
   - Kein `exit("msg")` in then-clause
5. **`while not main_session.exit` + command dispatch via Dictionary** ist das saubere Pattern. Commands-Registry mit `{name: cmd_obj}` für einfaches Erweitern.

## Related

- `references/viper-tool-integration.md` — Viper-Original-Analyse
- `references/savegame-storage-cleanup.md` — FileSystem-JSON-Schema + DB-Edit-Patterns
- `references/greybel-test-pattern.md` — greybel execute Mock-Testing
- `~/docs/system/greyhack-yuno-v2-2026-07-03.md` — YUNO V2 Doku mit allen Details