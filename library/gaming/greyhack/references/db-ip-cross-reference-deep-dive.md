# GreyHack DB — IP Cross-Reference Deep-Dive (Bank/Mail/Computer/Logs)

**Stand:** 2026-07-04, Game V0.9.6771-beta  
**DB-Pfad:** `/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db`  
**Kontext:** Wenn du via `Map`-Tabelle, BankAccounts oder MailAccounts eine Liste von IPs hast und diese **über mehrere Tabellen kreuzreferenzieren** willst — das ist der konkrete Query-Kit dafür.

---

## Goal

Gegeben eine Liste von IPs → finde für jede IP:
- **BankAccount(s)** mit Guthaben + Transaktionen
- **MailAccount(s)** mit Mail-Count
- **Computer-Einträge** (wenn existent) mit Ports, Services, LibVersions, Passwörtern
- **Logs** mit Angreifer-IPs, Ports, Datumsspanne
- **Mission-Relevanz** (ist die IP Ziel einer aktiven Mission?)

Ergebnis: Eine **Scoring-Tabelle** pro IP für Target-Priorisierung.

---

## Phase 1: Basisdaten pro IP sammeln

```bash
DB="/pfad/zu/GreyHackDB.db"
IP="146.153.198.249"

# Computer-Instanzen zählen:
sqlite3 "$DB" "SELECT COUNT(*) FROM Computer WHERE ID LIKE '${IP}:%'"

# Alle Instanzen + Router/Player-Flags:
sqlite3 "$DB" "SELECT ID, IsRouter, IsPlayer, IsCTF, IsRented FROM Computer WHERE ID LIKE '${IP}:%'"
```

**⚠️ ID-Format:** `Computer.ID = IP:PID` (publicIP:portNum). `ID LIKE '${IP}:%'` matcht ALLE Instanzen. Eine öffentliche IP kann mehrere Computer haben (Router + Endgerät dahinter).

---

## Phase 2: BankAccounts Cross-Reference

### JSON-Struktur

```json
{
  "account": "O1bx8eS6-niyufumay.com",
  "password": "Adelholzener",
  "origBankDomain": "niyufumay.com",
  "origBankAddress": "47.100.26.111",
  "isPlayer": true,
  "dinero": 68.0,
  "transacciones": [
    {"cuenta": "Unknown", "cantidad": 0, "motivo": "Shop item purchased",
     "fecha": "04/Jan/2000 - 23:08", "success": true}
  ]
}
```

### Python-Rezept

```python
import sqlite3, json

DB = "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db"
db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = db.execute("SELECT User, Transactions FROM BankAccounts")

for user, tx_json in cur:
    if '-' not in user:
        continue
    domain = user.split('-', 1)[1]
    data = json.loads(tx_json)
    print(f"{user} -> domain={domain}, dinero={data.get('dinero')}, "
          f"tx={len(data.get('transacciones', []))}, "
          f"origIP={data.get('origBankAddress')}, "
          f"player={data.get('isPlayer')}")
```

### 🚨 Domain-IP-Mismatch erkennen

Wenn `origBankAddress` ≠ IP der Domain → **Phishing/Spoof verdächtig!**

```bash
# Domain zu IP auflösen:
sqlite3 "$DB" "SELECT IP FROM Domains WHERE DomainName = 'fogepuhus.info'"
# 16.174.201.225
# Aber origBankAddress = 163.72.70.125 → BANK LÄUFT AUF ANDEREM SERVER!
```

---

## Phase 3: MailAccounts Cross-Reference

### SQL-Mails zählen

```sql
SELECT User,
       json_array_length(json_extract(Mails, '$.emails')) AS MailCount
FROM MailAccounts;
```

### Python: Player vs NPC

```python
cur = db.execute("SELECT User, Mails FROM MailAccounts")
for user, mails_json in cur:
    data = json.loads(mails_json)
    domain = user.split('@')[1]
    player_pc = data.get('playerPcID', '')  # nicht-leer = Player-PC
    mail_count = len(data.get('emails', []))
    print(f"{user} ({'Player' if player_pc else 'NPC'}): {mail_count} mails")
```

---

## Phase 4: Computer.ConfigOS Deep Extraction (Python-Regex-Bridge)

ConfigOS enthält Ports + Services + LibVersions. Bei 2+ Computer-Instanzen pro IP brauchst du Python als Bridge, weil SQLite's `json_tree` an tief verschachtelte Arrays stößt.

### Python-Bridge

```python
import re

def extract_configos(configos_text: str) -> dict:
    """Extrahiert Ports, Services, LibVersions aus ConfigOS per Regex."""
    ports = set()
    for m in re.finditer(
        r'"internalPort":(\d+),"externalPort":(\d+),"isClosed":(true|false)',
        configos_text
    ):
        state = 'closed' if m.group(3) == 'true' else 'open'
        ports.add(f'{m.group(1)}/{m.group(2)}[{state}]')

    libs = {}
    for m in re.finditer(
        r'"libVersions":\{[^}]*?"([^"]+)":\{"version":"([^"]+)"',
        configos_text
    ):
        libs[m.group(1)] = m.group(2)

    services = {}
    for m in re.finditer(
        r'"nomexe":"([^"]+)","probabilidad":(\d+),"isClosed":(true|false)',
        configos_text
    ):
        services[m.group(1)] = f'closed={m.group(3)}, prob={m.group(2)}'

    return {"ports": sorted(ports), "libs": libs, "services": services}

# Kontext: ConfigOS zuerst aus DB holen
import subprocess
result = subprocess.run([
    "sqlite3", "-separator", "|",
    DB,
    f"SELECT ConfigOS FROM Computer WHERE ID LIKE '{ip}:%' LIMIT 1"
], capture_output=True, text=True)
details = extract_configos(result.stdout)
print(f"  Ports: {', '.join(details['ports'])}")
print(f"  Libs: {', '.join(f'{k}={v}' for k,v in details['libs'].items())}")
print(f"  Services: {', '.join(details['services'].keys())}")
```

### Server-Rollen aus libVersions

| Lib-Key | Server-Rolle |
|---------|-------------|
| `bank_account` | 🏦 Bank-Server |
| `http` | 🌐 Web-Server |
| `ftp` | 📁 FTP-Server |
| `ssh` | 🔑 SSH-Server |
| `smtp` | 📧 Mail-Server |
| `smartappliance` | 💡 IoT-Gerät |

---

## Phase 5: Passwords Cross-Reference

### Kette: Computer.Users → MD5-Hash → Passwords.Tabelle

```sql
-- Schritt 1: Hashes aus Computer.Users extrahieren
SELECT DISTINCT json_extract(u.value, '$.passEncriptado') AS pw_hash
FROM Computer, json_each(Users) u
WHERE ID LIKE '${IP}:%';

-- Schritt 2: Gegen Passwords matchen
SELECT COUNT(*) FROM Passwords
WHERE ID IN (
  SELECT DISTINCT json_extract(u.value, '$.passEncriptado')
  FROM Computer, json_each(Users) u
  WHERE ID LIKE '${IP}:%'
);
```

### Python mit Klartext

```python
cur = db.execute("""
    SELECT DISTINCT json_extract(u.value, '$.passEncriptado')
    FROM Computer, json_each(Users) u
    WHERE ID LIKE ?
""", (f'{ip}:%',))
hashes = [r[0] for r in cur if r[0]]

if hashes:
    placeholders = ','.join('?' for _ in hashes)
    cur = db.execute(
        f"SELECT ID, PlainPassword FROM Passwords WHERE ID IN ({placeholders})",
        hashes
    )
    for hash_id, plain in cur:
        print(f"  {hash_id} → {plain}")
```

---

## Phase 6: Logs per IP — Angreifer-Profil

```sql
SELECT
    COUNT(*) AS total,
    COUNT(DISTINCT json_extract(e.value, '$.ip')) AS attackers,
    COUNT(DISTINCT json_extract(e.value, '$.playerNetID')) AS players,
    MIN(json_extract(e.value, '$.fecha')) AS first_seen,
    MAX(json_extract(e.value, '$.fecha')) AS last_seen,
    COUNT(DISTINCT json_extract(e.value, '$.puerto')) AS ports
FROM Logs l, json_each(l.Log, '$.contentLog') e
WHERE l.ID LIKE '${IP}:%';
```

**Interpretation:** 0 Logs → IP wurde noch nie im Spiel kontaktiert → **unentdeckt** (hoher Wert).

---

## Phase 7: Missions-Cross-Reference

```sql
-- Ziel-IP aus Players.Missions extrahieren
SELECT substr(Missions, 1, 500) FROM Players;
```

Python:
```python
cur = db.execute("SELECT Missions FROM Players")
missions_json = json.loads(cur.fetchone()[0])
for uuid, mission in missions_json.get('missions', {}).items():
    target = mission.get('targetComputerID', '')
    ip = target.split(':')[0] if ':' in target else target
    print(f"Mission: target={target} (IP={ip}), type={mission.get('typeMission')}")
```

---

## Phase 8: Unified Scoring Table

### Score-Schema (0–5 ⭐)

| Kriterium | Punkte |
|-----------|--------|
| Bank-Guthaben > 0 | +1 |
| Transaktionen > 5 | +1 |
| Computer-Eintrag vorhanden | +1 |
| Passwörter in DB gefunden | +1 |
| Computer vorhanden + 0 Logs (unentdeckt) | +1 |
| IP ist Missionsziel | +1 |
| **Max** | **5** (+1 bonus) |

### Shell-Einzeiler für eine IP

```bash
DB="/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db"
IP="47.100.26.111"

echo "=== Score für $IP ==="
echo -n "Computer: "; sqlite3 "$DB" "SELECT COUNT(*) FROM Computer WHERE ID LIKE '${IP}:%'"
echo -n "Router: "; sqlite3 "$DB" "SELECT COALESCE(SUM(IsRouter),0) FROM Computer WHERE ID LIKE '${IP}:%'"
echo -n "Passwords: "; sqlite3 "$DB" "SELECT COUNT(*) FROM Passwords WHERE ID IN (SELECT DISTINCT json_extract(u.value,'$.passEncriptado') FROM Computer, json_each(Users) u WHERE ID LIKE '${IP}:%')"
echo -n "Logs: "; sqlite3 "$DB" "SELECT COUNT(json_extract(e.value,'$.fecha')) FROM Logs l, json_each(l.Log,'$.contentLog') e WHERE l.ID LIKE '${IP}:%'"
```

---

## Edge Cases (diese Session gefunden)

### 1. "Ghost-IP" — Ohne Computer-Eintrag

7 von 9 IPs hatten **keinen Computer-Eintrag**. Sie existieren nur in Logs/BankAccounts/MailAccounts. Kein Dateisystem, keine Hardware, keine User. Diese IPs müssen erst durch einen Router-Besuch instantiiert werden.

### 2. Phishing-Bank (isPlayer=false + IP-Mismatch)

- `RHXoV5ad-fogepuhus.info` → `origBankAddress=163.72.70.125`, aber fogepuhus.info = 16.174.201.225
- Bank läuft auf **anderem Server** als die Domain sagt → Spoof/Weiterleitung

### 3. Geteiltes Passwort über Accounts

Zwei verschiedene BankAccounts (jodelimuf + niyufumay) mit gleichem `password="Adelholzener"`.

### 4. Player-BankUser-Verbindung prüfen

```sql
SELECT BankUser FROM Players;  -- muss in BankAccounts.User existieren
```

### 5. 0-Logs-IP (noch nie im Spiel besucht)

`163.72.70.125` hatte 0 Log-Einträge → Bank-Server **unentdeckt**. Maximale Priorität.

---

## Profile-Aware Multi-Profile Guard

**Niemals blind den DB-Pfad nutzen.** Immer vorher bestätigen:

```bash
ls -la "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db"
```

---

## Siehe auch

- `references/db-reconnaissance-pattern.md` — Drei-Phasen-Breitensuche + Library-Hash-Scoring (davor)
- `references/db-state-analysis.md` — Spieler-State, Hardware, Filesystem, User aus Computer
- `references/db-schema-analysis.md` — Map, WebPages, Logs, Computer — alle Schemas
- `references/greyhack-db-schema-detailed.md` (in greyhack-sandbox) — Vollständige 19-Table-Schema-Referenz
