# GreyHackDB.db — Complete Schema Reference

> Discovered 2026-07-04, Game V0.9.6771-beta  
> Path: `Grey Hack/Grey Hack_Data/GreyHackDB.db`  
> DB Size: ~7 MB, 19 SQLite tables, single-player save.

---

## Table Overview

| Table | Rows (this save) | Purpose |
|-------|-----------------|---------|
| `InfoGen` | 1 | Global game state, exploit registry, libraries, economy |
| `Players` | 1 | Active player profile |
| `BankAccounts` | 4 | Bank accounts (player + NPC) |
| `MailAccounts` | 7 | Email accounts (player + NPC) |
| `Passwords` | 267 | Saved/cracked passwords (ID = `service:user`) |
| `Files` | varies | In-game filesystem file content store |
| `Map` | varies | Network topology (routers, IPs, positions) |
| `Computer` | varies | All computers in the world (with FileSystem JSON) |
| `Wallets` | 0 (empty) | Crypto wallet records |
| `Coins` | 0 (empty) | Cryptocurrency records |
| `Stocks` | 0 (empty) | Stock market records |
| `CTFs` | 0 (empty) | Capture-the-flag events |
| `WebPages` | varies | Internet web page content |
| `Logs` | varies | System trace logs |
| Other tables | — | Internal game state (Schema, Downloads, ChatRooms, etc.) |

> **Note:** Wallets, Coins, Stocks, CTFs are **zero-row until the player engages those systems**. In an early save (day 6, GameOver=1), they will all be empty. This is normal, not a corrupt DB.

---

## Table Schemas & JSON Structures

### 1. InfoGen — Global Game State

**One row** containing the entire world's exploit registry, library versions, guild data, and invoice state.

```sql
CREATE TABLE InfoGen (
    Seed INTEGER,               -- RNG seed: e.g. -1665370662
    VersionsControl TEXT,       -- JSON: 20+ library exploit mappings (143 KB)
    Clock TEXT,                 -- In-game time: "2000-01-06T14:54:44"
    DeleteVersion INTEGER,      -- Save version counter: 347
    GlobalMoney TEXT,           -- Null unless economy system active
    ZeroDaySystem TEXT,         -- NULL = not triggered
    Exploits TEXT,              -- Exploit definitions (small)
    AllLibs TEXT,               -- All library definitions (8 KB)
    Guilds TEXT,                -- Guild registry (143 KB)
    Invoices TEXT               -- Payment schedules (1.9 MB)
);
```

#### VersionsControl JSON Structure

A JSON dict where keys are **library filenames** (20 total). Each library has:

```json
{
  "libssh.so": {
    "listaZonaMem": {
      "0x3B896752": {
        "vulnerabs": [
          {
            "typeVulner": 0,
            "requiredActions": [0, 5],
            "helperHackResult": {
              "hackResult": 2,
              "randomPath": "/etc",
              "pathExist": "/bin",
              "user": "root",
              "numRegisterUsers": 1,
              "numPortForward": 1,
              "numConnGateway": 3
            },
            "unsecValue": "ittextuitextnewuite",
            "details": "loop in array",
            "reqLibVersion": "1.0.3",
            "isRemote": true,
            "requiredLib": 16,
            "metaxploitVersion": { "version": [0, 0, 9] }
          }
        ],
        "address": "0x3B896752",
        "timesPatched": 0,
        "hide": false
      }
    },
    "version": { "version": [1, 0, 6] },
    "idPatch": 0,
    "idLib": 0,
    "autoPatchTime": "0001-01-01T00:00:00",
    "numPatches": 0
  }
}
```

**Key fields per vulnerability:**
- `helperHackResult.hackResult` — 0=root, 1=normal_user, 2=guest, 3=?, 6=?
- `helperHackResult.randomPath` — simulated path for exploit
- `helperHackResult.user` — privilege level gained (root/guest/normal_user)
- `unsecValue` — the exploit "password" / overflow value
- `reqLibVersion` — required library version (null = any)
- `isRemote` — true = remote exploitable, false = local only
- `requiredLib` — which prerequisite lib ID (16=kernel_module, 17=init.so, 18=net.so)
- `metaxploitVersion` — minimum metaxploit version needed
- `hide` — true = hidden zone (harder to discover in-game)
- `timesPatched` — how often this zone has been patched by sysadmins

**20 Registered Libraries (2026-07-04 save):**

| Library | Version | Zones | Remote |
|---------|---------|-------|--------|
| `libssh.so` | 1.0.6 | 6 | ✅ |
| `libftp.so` | 1.0.6 | 5 | ✅ |
| `libhttp.so` | 1.0.6 | 5 | ✅ |
| `libsql.so` | 1.0.5 | 4 | ✅ |
| `libsmtp.so` | 1.0.5 | 8 | ✅ |
| `libchat.so` | 1.0.6 | 4 | ✅ |
| `libcam.so` | 1.0.6 | 4 | ✅ |
| `librshell.so` | 1.0.6 | 5 | ✅ |
| `librepository.so` | 1.0.6 | 6 | ✅ |
| `blockchain.so` | 1.0.5 | 5 | ✅ |
| `libadb.so` | 1.0.6 | 10 | ✅ |
| `libsmartappliance.so` | 1.0.6 | 7 | ✅ |
| `kernel_router.so` | 1.0.6 | 1 | ✅ |
| `aptclient.so` | 1.0.6 | 9 | ✅ |
| `metaxploit.so` | **2.1.0** | 5 | — |
| `crypto.so` | 1.0.6 | 5 | ✅ |
| `kernel_module.so` | 1.0.6 | 7 | ❌ local |
| `init.so` | 1.0.5 | 5 | ❌ local |
| `net.so` | 1.0.6 | 4 | ❌ local |
| `libtrafficnet.so` | 1.0.6 | 8 | ❌ local |

#### Invoices JSON Structure

```json
{
  "e85129e9ae28753542b97bf10378c645": {
    "BANK": {
      "bankAccount": "O1bx8eS6-niyufumay.com",
      "playerID": "e85129e9ae28753542b97bf10378c645",
      "nextMoney": 50,
      "paymentID": 0,
      "nextDate": "2000-02-04T22:50:00",
      "publicIps": []
    }
  }
}
```

---

### 2. Players — Player Profile

```sql
CREATE TABLE Players (
    PlayerID TEXT PRIMARY KEY,       -- Hash: e85129e9ae28753542b97bf10378c645
    Nickname TEXT,                   -- Can be empty
    WalletID TEXT,                   -- Empty if no wallet
    WalletPass TEXT,                 -- Empty if no wallet
    BankUser TEXT,                   -- Linked bank account: O1bx8eS6-niyufumay.com
    Missions TEXT,                   -- JSON missions state
    LastConnection TEXT,             -- ISO timestamp: "2000-01-06T13:58:58"
    infoMapX REAL,                   -- World map X: 1142.84
    infoMapY REAL,                   -- World map Y: -232.65
    indMap INTEGER,                  -- Map index: 27
    GameOver INTEGER,                -- 1 = dead/lost, 0 = alive
    BankTraces TEXT,                 -- JSON (small or [])
    Storage TEXT,                    -- JSON player storage (390 bytes)
    ShopHardware TEXT,               -- JSON shop inventory (33 bytes)
    TutoData TEXT,                   -- Tutorial state (78 bytes)
    TokenTrace TEXT,                 -- Token trace data (36 bytes)
    PassiveTraces TEXT               -- Passive trace count (2 bytes)
);
```

#### Missions JSON Structure

```json
{
  "missions": {
    "792964c0-f72a-472f-94c8-ec197065755a": {
      "targetUser": "",
      "anyUser": true,
      "typeMission": 1,
      "targetComputerID": "16.174.201.225:746422179",
      "reputation": 0,
      "karma": 1
    }
  }
}
```

- `typeMission: 1` — generic hack mission
- `targetComputerID` — format `IP:ComputerID` (ComputerID is the computer's in-game hash)
- `anyUser: true` — any account on the target computer works

---

### 3. BankAccounts — Banking System

**4 rows** (player + NPC banks). Transactions are stored as a JSON array inside a JSON dict.

```sql
CREATE TABLE BankAccounts (
    User TEXT PRIMARY KEY,           -- uDn8TGq0-okozacuxuv.com
    Transactions TEXT                -- JSON dict (see below)
);
```

#### Transactions JSON Structure

```json
{
  "account": "O1bx8eS6-niyufumay.com",
  "password": "Adelholzener",
  "origBankDomain": "niyufumay.com",
  "origBankAddress": "47.100.26.111",
  "isPlayer": true,
  "dinero": 68.0,
  "transacciones": [
    {
      "cuenta": "Unknown",
      "cantidad": 0,
      "motivo": "Shop item purchased",
      "fecha": "04/Jan/2000 - 23:08",
      "success": true
    },
    {
      "cuenta": "O1bx8eS6-niyufumay.com",
      "cantidad": 68,
      "motivo": "Money transfer",
      "fecha": "05/Jan/2000 - 14:50",
      "success": true
    }
  ]
}
```

**Key fields:**
- `isPlayer` — true = player account, false = NPC/generated
- `dinero` — current account balance (float)
- `password` — plain text password (WARNING: stored unhashed!)
- `origBankAddress` — IP address of the bank server
- `transacciones` — array of transactions, each with:
  - `cuenta` — other account involved ("Unknown" for shop purchases)
  - `cantidad` — amount (negative = debit, positive = credit, 0 = shop)
  - `motivo` — reason (water bill, electricity bill, Shop item purchased, Money transfer, etc.)
  - `fecha` — date in `DD/Mon/YYYY - HH:MM` format
  - `success` — bool

**Common `motivo` values:** `Shop item purchased`, `Money transfer`, `Transaction fee`, `withdraw funds`, `water bill`, `electricity bill`

---

### 4. MailAccounts — Email System

**7 rows** (player + NPC). Each account has a full mailbox JSON.

```sql
CREATE TABLE MailAccounts (
    User TEXT PRIMARY KEY,           -- gregor@okulukuxay.org
    Mails TEXT                       -- JSON dict (see below)
);
```

#### Mails JSON Structure

```json
{
  "address": "gregor@okulukuxay.org",
  "plainPassword": "XXXX",
  "encPassword": "0123456789abcdef0123456789abcdef",
  "blacklist": [],
  "spamFilter": 0,
  "playerPcID": "",
  "emails": [
    {
      "from": "...",
      "to": "...",
      "subject": "...",
      "body": "...",
      "date": "...",
      "read": true
    }
  ]
}
```

**Key observations:**
- `plainPassword` — plain text password (4-12 chars in this save)
- `encPassword` — 32-char hex string (likely MD5 or SHA256-128)
- `blacklist` — array of blocked email addresses
- `spamFilter` — 0 = off, 1 = on (integer flag)
- `playerPcID` — linked player computer ID (empty = not linked)
- `emails` — array of email message objects

---

### 5. Passwords — Saved/Cracked Credentials

**267 entries.** Format: `ID` is `service:user` (e.g. `mail:gregor@okulukuxay.org`, `bank:O1bx8eS6-niyufumay.com`).

```sql
CREATE TABLE Passwords (
    ID TEXT PRIMARY KEY,             -- service:user format
    PlainPassword TEXT               -- Plain text password (⚠️ NOT hashed!)
);
```

**Password Length Distribution (this save):**

| Length | Count |
|-------|------|
| 3 | 12 |
| 4 | 27 |
| 5 | 64 |
| 6 | 91 |
| 7 | 46 |
| 8 | 25 |
| 9 | 1 |
| 12 | 1 |

- Min: 3 · Max: 12 · Avg: 5.8 chars
- ~75 % are 5-7 characters (weak)

> **Security note (for analysis scripts):** Never log `PlainPassword` values to stdout/stderr. Show length stats only. If plaintext must be exported, redact or restrict to explicit user request.

---

### 6. Computer — World Computers

```sql
CREATE TABLE Computer (
    ID TEXT PRIMARY KEY,             -- Hash ID
    FileSystem TEXT,                 -- JSON: full filesystem tree
    Hardware TEXT,                   -- JSON: hardware specs
    ...
);
```

> Full schema and content not explored in this session. See `savegame-storage-cleanup.md` for FileSystem JSON structure (spanish field names: `nombre`, `propietario`, `permisos`).

---

### 7. Files — File Content Store

```sql
CREATE TABLE Files (
    ID TEXT PRIMARY KEY,             -- UUID or hash
    Content TEXT,                    -- File content (text binary, or source code)
    refCount INTEGER DEFAULT 1       -- Reference counter
);
```

- Source scripts have `//command: <name>` as their first line
- Built binaries have `isBinario: true` in their FileSystem entry
- Max `//command:` auto-load size: ~12 KB (verified V0.9.6771-beta)

---

### 8. Empty Tables (Zero Rows in Early Saves)

| Table | Expected when populated |
|-------|------------------------|
| `Wallets` | PlayfabID, PlayerID, WalletID |
| `Coins` | CoinName, CoinContent (JSON), OwnerPlayerID, WebAddress |
| `Stocks` | Id, IpAddress, StocksContent (JSON), points |
| `CTFs` | EventName, EventContent (JSON), OwnerPlayerID |

These tables stay empty until the player engages the corresponding game systems. An empty table does NOT indicate a corrupt save if the player hasn't interacted with that system.

---

## Analysis Recipe (Python + sqlite3)

```python
import sqlite3, json

DB = "/path/to/GreyHackDB.db"
conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
cur = conn.cursor()

# 1. Show all tables and row counts
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
for table in tables:
    cur.execute(f"SELECT COUNT(*) FROM \"{table}\"")
    count = cur.fetchone()[0]
    print(f"{table}: {count} rows")

# 2. Extract JSON from a TEXT column
cur.execute("SELECT User, Transactions FROM BankAccounts")
for user, tx_json in cur.fetchall():
    data = json.loads(tx_json)
    tx_count = len(data.get("transacciones", []))
    balance = data.get("dinero", 0)
    is_player = data.get("isPlayer", False)
    print(f"{user}: balance={balance}, tx={tx_count}, player={is_player}")

# 3. Password length stats (NO plaintext exposure)
cur.execute("SELECT ID, LENGTH(PlainPassword) FROM Passwords")
lengths = [r[1] for r in cur.fetchall()]
print(f"Passwords: {len(lengths)} entries, avg={sum(lengths)/len(lengths):.1f}")
# Distribution
from collections import Counter
for l, c in sorted(Counter(lengths).items()):
    print(f"  len {l}: {c}")

# 4. Parse nested JSON within InfoGen
cur.execute("SELECT VersionsControl FROM InfoGen")
vc = json.loads(cur.fetchone()[0])
for lib_name, lib_data in vc.items():
    version = lib_data.get("version", {}).get("version", "?")
    zones = len(lib_data.get("listaZonaMem", {}))
    print(f"{lib_name}: v{version}, {zones} zones")
```

---

## Deterministic Checksums per Save

The following values **change every save** (RNG-seeded) and cannot be hardcoded:

- `InfoGen.Seed` — RNG seed, determines all generated data
- `Players.Nickname` — empty until player sets a name
- `Players.infoMapX/Y` — player's last map position
- All bank passwords, mail passwords, and IP addresses
- Library versions (may vary between saves if patches were applied)
- `InfoGen.Clock` — in-game timestamp
- `DeleteVersion` — increments with significant game events
