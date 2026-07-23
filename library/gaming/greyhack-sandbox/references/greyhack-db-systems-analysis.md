# GreyHack DB — Systems Analysis Methodology

> Entstanden aus der Tiefenanalyse aller 18 Computer-Systeme (1 Player, 15 Router, 2 Server) am 2026-07-04.
> Ergänzt die existierenden Schema- (greyhack-db-schema-detailed.md), File- (greyhack-db-file-analysis.md) und Forensic-Queries (greyhack-db-forensic-queries.md) um die **systemübergreifende, vergleichende Methodik**.

## Übersicht

Die GreyHack DB enthält 18 Computer-Systeme in der `Computer`-Tabelle, jedes mit eigenem FileSystem (JSON), ConfigOS (JSON), Hardware (JSON), Users (JSON) und Procs (JSON). Eine vollständige Systemanalyse extrahiert **alle 18 Systeme parallel** und vergleicht sie über **5 Kategorien** hinweg: Hardware, FileSystem, OS-Config, Prozesse, und NPC-Persona.

## Phasen-Modell

### Phase 0 — Schema Discovery

```sql
-- 1. Alle Tabellen
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- 2. Schema einer Tabelle
SELECT sql FROM sqlite_master WHERE name='Computer';

-- 3. JSON-Spalten identifizieren
-- Computer: FileSystem, ConfigOS, Hardware, Users, Procs, PortsMap
-- Players: Storage, ShopHardware, Missions, PassiveTraces
-- BankAccounts: Transactions (JSON)
-- MailAccounts: emails (JSON)
-- InfoGen: Exploits, VersionsControl, AllLibs
-- Map: LibVersions
```

### Phase 1 — Population Scan

```sql
-- Row count pro Tabelle
SELECT 'Computer', COUNT(*) FROM Computer
UNION ALL SELECT 'Players', COUNT(*) FROM Players
UNION ALL SELECT 'Files', COUNT(*) FROM Files
-- ... alle Tabellen
```

Python-Code zur Klassifizierung der Computer (Router vs Server vs Player):
```python
routers = []   # ID enthält ':' (IP:PortHash)
servers = []   # ID enthält ':' UND IsPlayer=0 und andere PortHash2
players = []   # ID ist UUID (kein ':') ODER IsPlayer=1

for row in rows:
    is_player = row['IsPlayer'] == 1
    has_colon = ':' in row['ID']
    
    if is_player:
        players.append(row)
    elif has_colon and row['IdPortHash'] != row['IdPortHash2']:
        servers.append(row)  # Server
    else:
        routers.append(row)  # Router
```

### Phase 2 — Identity Verification

**Kernfrage:** Sind Systeme derselben Rolle (z.B. alle 15 Router) identisch oder individuell?

```python
import hashlib
def check_uniqueness(rows, json_extractor):
    """Prüft ob N Systeme derselben Rolle identische JSON haben."""
    hashes = set()
    for r in rows:
        json_str = json_extractor(r)
        hashes.add(hashlib.md5(json_str.encode()).hexdigest())
    n_unique = len(hashes)
    n_total  = len(rows)
    return n_unique, n_total  # n_unique == n_total -> alle individuell
```

**Prüf-Kategorien pro Rolle:**

| Spalte | Uniqueness | Erwartung | Bedeutung |
|--------|-----------|-----------|-----------|
| FileSystem | n_unique == n_total | **Alle unterschiedlich** | NPC-Daten + UUIDs | 
| ConfigOS | n_unique == n_total | **Alle unterschiedlich** | NPC-Profil + WiFi-Config + Router-Pwd |
| Users | n_unique == n_total | **Alle unterschiedlich** | Root- und User-Passwörter |
| Hardware | n_unique == n_total | **Alle unterschiedlich** | UUIDs/Komponenten-IDs |
| Procs | n_unique == 1 | **Alle gleich (leer)** | GameOver -> keine Prozesse |

**Pitfall:** Server teilen sich den Router-NPC (gleiche public IP). `substr(ID, 1, instr(ID, ':') - 1)` extrahiert die reine IP -- gleiche IP + gleicher NPC-Name -> Router+Server-Kombination desselben Characters.

### Phase 3 — Hardware-Klassenanalyse

```python
# Hardware-Struktur parsen
hw = json.loads(row['Hardware'])
cpu  = hw.get('cpus', [{}])
ram  = hw.get('rams', [{}])
hdd  = hw.get('hardDisk', {})
psu  = hw.get('powerSupply', {})
mb   = hw.get('motherBoard', {})
netcards = hw.get('netCards', [])

# Router-Template: arm_cpu @ 0.25GHz, 64MB RAM, 1000MB HDD
# Server-Template: Generic 4XX @ 1.5-2.3GHz, 1024MB RAM, 5-7GB HDD  
# Player-Template: Generic XY @ 1.0GHz, 128MB RAM, 350MB HDD
```

**Wichtige Felder pro Komponente:**

| Component | Router | Server | Player |
|-----------|--------|--------|--------|
| CPU speed | 0.25 GHz | 1.58-2.28 GHz | 1.0 GHz |
| RAM | 64 MB | 1024 MB | 128 MB |
| HDD | 1000 MB | 5293-7299 MB | 350 MB |
| MB sockets | maxRAM=1024 MB, 1 socket | maxRAM=1024 MB, **2 sockets** | maxRAM=1024 MB, 1 socket |

### Phase 4 — ConfigOS Deep Dive

**Player-spezifische Felder:**
```python
osd = json.loads(row['ConfigOS'])
player_id    = osd.get('playerID')
user_mail    = osd.get('userMail')       # {"userName":"x", "password":"y", ...}
user_bank    = osd.get('userBank')       # {"userName":"x", "password":"y", ...}
personas     = osd.get('personas', [])   # Leer bei Player!
saved_netw   = osd.get('savedNetworks', [])  # List von {"essid":"x", "password":"y"}
puertos      = osd.get('puertos', [])    # [{ID, port, OPEN|CLOSED, lanIP, ...}]
servicios    = osd.get('servicios', [])  # [{ID, port, exe, db, pathExe}]
active_net   = osd.get('activeNetCard')
ip_publica   = osd.get('ipPublica')
pc_name      = osd.get('pcName')
```

**Router-spezifische Felder:**
```python
router_pwd   = osd.get('routerPassword')
network_lan  = osd.get('networkLan', {})
rd           = network_lan.get('routerDevice', {})
essid        = rd.get('essid')
bssid        = rd.get('bssid')
local_ip     = rd.get('localIp')

# Port-Map (Port-Forwarding):
# puertos[0] = {"port": 80, "isClosed": false, "lanIP": "172.16.x.x"}
```

**Server-spezifische Felder:**
Beide Server haben identische Service-Maps:
- Port 80 -> httpd (Public/htdocs/website.html)
- Port 141 -> accountsd (server/conf/account.db)

### Phase 5 — NPC-Persona-Extraktion

```python
personas = json.loads(row['ConfigOS']).get('personas', [])
for p in personas:
    npc = p.get('npcInfo', {})
    npc_id       = npc.get('ID')           # Eindeutig pro NPC
    name         = npc.get('name')
    surname      = npc.get('surname')
    gender       = npc.get('gender')        # 0=m, 1=w
    age          = npc.get('age')
    mail         = npc.get('userMail')      # Vorname@domain
    mail_pass    = npc.get('emailPass')     # Klartext!
    inteligencia = npc.get('inteligencia')  # 0-6
    job_role     = npc.get('jobRole')
    company_align= npc.get('companyAlign')  # 0 = loyal
    forced_pass  = npc.get('forcedPass')    # None = nicht erzwungen
    bank_domain  = npc.get('origBankDomain')
    bank_addr    = npc.get('origBankAddress')
    has_rumor    = npc.get('hasRumor')
    day_alarm    = npc.get('dayAlarm')      # 0-23
    local_ip     = npc.get('localIP')
    phone        = npc.get('phoneNumber')
```

**NPC-Duplikat-Erkennung:**
```python
# Gleicher NPC auf Router + Server = dasselbe Individuum
# Router: NPC arbeitet beim ISP
# Server: NPC arbeitet im Firmen-Netzwerk
# Erkennung: gleiche npc['ID'] ueber Systeme hinweg
from collections import defaultdict
npc_id_map = defaultdict(list)
for system in all_systems:
    for npc in system.personas:
        npc_id_map[npc['ID']].append(system.id)
```

### Phase 6 — FileSystem-Baum-Analyse

```python
def walk_fs(entry, path="/", depth=0):
    """Rekursiver Dateisystem-Baum-Parser."""
    stats = {'dirs': 0, 'files': 0, 'max_depth': depth, 'total_size': 0}
    if entry.get('type') == 0:  # Ordner
        stats['dirs'] += 1
        for child in entry.get('children', []):
            child_stats = walk_fs(child, path + child.get('nombre', '?') + '/', depth + 1)
            # Merge child stats
    else:  # Datei (type=1 oder andere)
        stats['files'] += 1
        stats['total_size'] += entry.get('size', 0)
    return stats
```

**Spanische Feldnamen-Referenz:**
| Feld | Deutsch | Beispielwert |
|------|---------|-------------|
| `nombre` | Name | `"bin"` |
| `size` | Größe | `5471337` (künstlich) |
| `type` | Typ | `0` (Ordner), `1` (Datei) |
| `owner` | Besitzer | `"root"`, `"gregor"` |
| `permisos` | Permissions | `"-rwxr-xr-x"` |
| `typeFile` | Datei-Subtyp | `0` (normal), `6` (PDF), `7` (Log) |
| `isBinario` | Ist Binary | `true/false` |
| `comando` | Shell-Command | `""` (leer wg `//command:`) |

### Phase 7 — Prozess-Analyse

```python
procs = json.loads(row['Procs'])
for p in procs:
    name     = p.get('nombre')
    user     = p.get('user')
    ram      = p.get('ram') / 1024 / 1024  # Bytes -> MB
    cpu      = p.get('cpu')                 # 0.0-100.0
    pid      = p.get('pid')
    path     = p.get('exePath')             # "(kernel)" oder Pfad
    is_prot  = p.get('isProtected', False)
    is_script= p.get('isScript', False)
```

**Erwartung bei GameOver=1:** Alle `Procs`-Arrays sind leer (`[]`) — das Spiel löscht Prozesse beim Beenden. NUR der Player-PC in einer aktiven Session hat Prozesse.

### Phase 8 — Player-Trace-Felder

| Feld | JSON-Typ | Inhaltstyp | Wert (leer) | Bedeutung |
|------|----------|-----------|-------------|-----------|
| `PassiveTraces` | `str` (JSON) | `list` | `"[]"` | Passiv-Scan-Ergebnisse |
| `TokenTrace` | `str` | `uuid` | `null` | Aktive Session-UUID (NICHT Array!) |
| `TLCooldown` | `str` | `ISO-date` | `"0001-01-01T00:00:00"` | Time-Limited Cooldown |
| `BankTraces` | `str` (JSON) | `list` | `"[]"` | Bank-Audit-Log |
| `GuiLaunchCooldown` | `str` | `ISO-date+tz` | Wall-Clock | Realer UI-Cooldown |
| `ZeroDayRequest` | `str` (JSON) | `map` | `{"zeroDayRequest":"0001-..."}` | 0Day-Status |

**Wichtig:** `TokenTrace` in `Players` ist die AKTUELLE Session-UUID. `tokenTrace` in `Logs.contentLog[]` ist ein HISTORISCHER Scan-Token — die Werte unterscheiden sich!

### Phase 9 — Report-Erstellung

Die vollständige Analyse mündet in einen strukturierten Markdown-Report mit 15+ Sektionen:
1. Global Inventory — Record-Counts pro Tabelle, Storage-Werte
2. Computer Inventory — Anzahl Player/Router/Server, IDs, Rollen
3. Player PC — Hardware, ConfigOS, Procs, FS-Baum, savedNetworks, Ports/Services
4. Router Analysis — Hardware-Template, Identity-Check, Router-Tabelle, Port-Map
5. Server Analysis — HW-Vergleich, Service-Map, FS-Baum, NPC-Homes, Loot
6. NPC Database — Alle Charaktere, Duplikat-Erkennung, Feld-Struktur
7. Player Storage — Inventory, ShopHardware, Spezialfelder
8. InfoGen — Seed, Clock, Library-Versionen, Exploit-Counts, Invoices
9. Bank/Mail/Web — Accounts, Passwörter, Domains, Transaktionen
10. Logs — Player-Aktivität, TokenTrace-Diskrepanz
11. Traces — PassiveTraces/TokenTrace/TLCooldown Detail
12. Passwords — Distribution, Patterns
13. Map — Wireless-Landschaft, AccessTypes, TypRed, LibVersions
14. Summary — Player-Status, offene Punkte, wertvolle Ziele
15. Research Recommendations — Offene Forschungsfragen
16. Anhang — Raw-Statistics

## Iterativer Script-Entwicklungs-Workflow

Die Analyse erfolgt **niemals in einem einzigen Script**. Stattdessen:

```
analyze.py  -> Phase 0+1: Schema Discovery + Population Scan
analyze2.py -> Phase 2+3: Identity Check + Hardware-Klassen
analyze3.py -> Phase 4+5+6: ConfigOS + NPC + FileSystem
analyze4.py -> Phase 7+8+9: Detail-Analysen (Logs, Traces, NPC-Detail, Bank)
```

**Warum iterativ:** Jede Phase produziert Erkenntnisse, die die nächste Phase steuern. Phase 2 zeigt z.B., ob Router-Klone existieren — wenn ja, reicht ein Router-Sample.

## Cross-Reference Matrix

| Von | Nach | Wie | Wofür |
|-----|------|-----|-------|
| Computer.ID (Player) | Players.PlayerID | UUID-Match | Player-zugehöriges Inventar |
| Computer.ID (Router) | Map.IpAddress | `substr(ID,1,instr(':')-1)` | Netzwerk-Topologie |
| Computer.ConfigOS.userMail | MailAccounts.Address | E-Mail-User | Player-Mail |
| Computer.ConfigOS.userBank | BankAccounts.User | Bank-Account | Player-Bank |
| Players.BankUser | BankAccounts.User | Direkt | Aktiver Bank-Account |
| InfoGen.Exploits.lib | Map.LibVersions.lib | Hash-Vergleich | Library-Version auf jedem System |
| BankAccounts.origBankAddress | Computer.ID | IP-Match | Welcher Server hostet die Bank? |
| MailAccounts.origDomain | WebPages.Address | Domain-Match | Mail-Server-Host |
| InfoGen.Invoices.playerID | Players.PlayerID | UUID | Passive Einkommens-Struktur |

## Report Template (Markdown)

```markdown
# GreyHack MMO — Tiefenanalyse der Computer-Systeme (DB-Stand YYYY-MM-DD)

> **Datenquelle:** `<db-path>` (X MB, SQLite X.X.X)
> **Version:** GreyHack MMO V0.9.6771-beta
> **Spieler:** 1 Player (UUID `<uuid>`, GameOver=1)
> **Methodik:** Alle 19 DB-Tabellen via sqlite3 CLI + Python-JSON-Parsing.

## 1. Global Inventory
## 2. Computer Inventory (N Systeme)
## 3. Player PC
## 4. Router (Nx)
## 5. Server (Nx)
## 6. NPC Database — N Charaktere
## 7. Player Storage / Inventory
## 8. InfoGen
## 9. Bank / Mail / Web Infrastructure
## 10. Logs — Player-Aktivitäts-Historie
## 11. Player Trace Fields
## 12. Passwords (N Eintraege)
## 13. Map — N Eintraege
## 14. Zusammenfassung
## 15. Research Recommendations
## Anhang: Raw Statistics
```

## Pitfalls

1. **JSON-Spalten in SQLite:** Viele GreyHack-Felder sind JSON, aber als `TEXT` gespeichert. Bei tiefen Strukturen (FileSystem mit 5+ Ebenen) ist Python-Parsing stabiler als `json_extract()`.

2. **Dateigrößen sind künstlich:** In-Game-Binaries haben aufgeblasene `size`-Werte (z.B. 5.4 MB für ein 2 KB Script). Nicht mit echter Disk-Usage verwechseln. Die HDD-Kapazität in MB (`hardDisk.totalSize`) ist der relevante Wert.

3. **Router !== Server:** Nur weil zwei IDs die gleiche IP-Substring haben (`163.72.70.125:766615037` und `163.72.70.125:2078686309`), sind Sie NICHT dasselbe System. Der Port-Hash unterscheidet. Router haben `routerPassword` + `networkLan.routerDevice`, Server haben `personas` + `server/`-Binary-Pfade.

4. **NPC-Duplikat auf Router+Server:** Dasselbe Individuum (gleiche `npc['ID']`) kann auf einem Router (als ISP-Kunde) UND auf einem Server (als Mitarbeiter) existieren. Immer via `npc['ID']` matchen, nicht via IP.

5. **Files.Content hat KEINE Fremdschlüssel:** Die `Files`-Tabelle verwendet GUIDs als `ID`, NICHT Dateinamen. Die Verknüpfung erfolgt über das `FileSystem.Content`-Feld (das den MD5-Hash oder UUID des File-Contents enthält).

6. **TokenTrace ist KEIN Array:** `Players.TokenTrace` ist ein einzelner UUID-String, NICHT ein JSON-Array. `Logs.contentLog[].tokenTrace` ist ein HISTORISCHER Scan-Token — beide unterscheiden sich.

7. **GameOver=1 = Session beendet:** Computer mit GameOver=0 haben echte Prozess-Listen. GameOver=1 -> archivierte Session -> alle Procs sind leer, aber FS+Config+HW bleiben erhalten.

8. **Backup-Tabellen prüfen:** `BackupPlayers` und `BackupPlayerFiles` können historische Spieler-Daten enthalten. Wenn beide leer sind, gab es noch nie einen Backup.
