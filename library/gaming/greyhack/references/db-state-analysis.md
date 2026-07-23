# GreyHack DB State Analysis — Query Patterns

**Stand:** 2026-07-04, Game V0.9.6771-beta  
**DB-Pfad:** `/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db`  
**Tool:** `sqlite3` CLI

## Überblick

Die GreyHackDB speichert **Spielwelt-Zustand** in 19 SQLite-Tabellen. Anders als beim DB-Injection-Deployment (wo nur `Files` und `Computer.FileSystem` relevant sind) erfordert die **State-Analyse** das Lesen aller Spieler-, Computer- und Weltdaten aus mehreren Tabellen mit tief verschachtelten JSON-Spalten.

---

## Kern-Tabellen für State-Analyse

| Tabelle | Inhalt | Wann relevant |
|---------|--------|---------------|
| `Players` | Genau 1 Datensatz: Spieler-Status, Missions, Inventar, Rentals, Stocks | Spielstand prüfen |
| `Computer` | Alle Computer der Welt: 1× Player-PC, N× Router, M× Server | Topologie, Hardware, User |
| `Files` | Datei-Inhalte der ganzen Welt (Sources, Binaries, Logs) | Script-Inventar |
| `Map` | BSSID/ESSID/Password für WLAN-Knoten | Netzwerk-Topologie zur Laufzeit |
| `MailAccounts` | Mail-Provider in der Welt | SMTP-Enum-Ziele |
| `BankAccounts` | Bank-Instanzen | Money-Transfer-Ziele |
| `WebPages` | Webseiten-Inhalte | CTF/Mission-Hinweise |
| `Passwords` | Generated Passwörter | Passwort-Cracking-Referenz |
| `InfoGen` | Generated Welt-Info | Lore/Mission-Kontext |
| `BackupPlayers` | Spieler-Backups | Wenn Spiel gestorben |
| `PlayerConns` | Topologie-Kanten (Player→Router) | Netzwerk-Karte — kann leer sein |
| `SharedConns` | Geteilte Computer | Multiplayer-Info |
| `Logs` | Generated Logs | Forensik/Mission |
| `Coins` | Crypto-Coins | Wallet-Info |
| `Stocks` | Aktienkurse | Stock-Market |
| `Wallets` | Wallet-Addressen | Crypto |

---

## JSON-Spalten-Muster

Die `Computer`-Tabelle hat **5 JSON-Blobs**:

| Spalte | Typ | Enthält |
|--------|-----|---------|
| `ConfigOS` | JSON-Objekt | Spieler-Settings (Mail, Bank, Wallet, TutoData) |
| `FileSystem` | JSON-Objekt mit `folders[]` und `files[]` | Dateien **auf diesem Computer** |
| `Users` | JSON-Array | User-Accounts (root + standard) |
| `Hardware` | JSON-Objekt | CPU, RAM, HDD, Mainboard, Netzwerk |
| `Procs` | JSON-Array | Laufende Prozesse |

### Extract-Patterns (sqlite3)

```sql
-- Top-Level Folder-Liste eines Computers:
SELECT json_extract(value, '$.nombre') AS FolderName
FROM Computer, json_each(json_extract(FileSystem, '$.folders'))
WHERE ID = '<computer-id>';
-- Ergebnis: etc, lib, sys, root, home, var, bin, usr, boot, server

-- Array-Länge eines JSON-Feldes:
SELECT json_array_length(json_extract(FileSystem, '$.folders')) AS TopFolders;

-- Spieler-Mail aus ConfigOS:
SELECT json_extract(ConfigOS, '$.userMail.userName') AS Email,
       json_extract(ConfigOS, '$.userMail.encPassword') AS PassHash,
       json_extract(ConfigOS, '$.userMail.password') AS PassPlain
FROM Computer WHERE IsPlayer=1;

-- Spieler-Bank aus ConfigOS:
SELECT json_extract(ConfigOS, '$.userBank.userName') AS BankUser,
       json_extract(ConfigOS, '$.userBank.encPassword') AS BankHash
FROM Computer WHERE IsPlayer=1;

-- Alle User eines Computers (Name + Passwort-Hash):
SELECT json_extract(value, '$.nombreUsuario') AS Username,
       json_extract(value, '$.passEncriptado') AS PassHash,
       json_extract(value, '$.passPlano') AS PassPlain
FROM Computer, json_each(Users)
WHERE <condition>;
```

---

## Spieler-State-Analyse

### Players-Tabelle — Alle Felder

| Feld | Typ | Bedeutung |
|------|-----|-----------|
| `PlayerID` | TEXT | UUID des Spielers |
| `ComputerID` | TEXT | Verknüpfung zum Player-PC in `Computer` |
| `Nickname` | TEXT | Im Spiel sichtbarer Name |
| `GameOver` | INTEGER | 0=lebt, 1=gestorben |
| `LastConnection` | TEXT | ISO-Datetime des letzten Logins |
| `WalletID`, `WalletPass` | TEXT | Crypto-Wallet |
| `BankUser` | TEXT | Bank-Account-Name |
| `Storage` | TEXT | HardDisk-Inventar (serialisiert) |
| `Missions` | TEXT | JSON-Object mit aktiven Missionen |
| `RentalsInfo` | TEXT | JSON-Object mit gemieteten Computern |
| `StocksInfo` | TEXT | JSON-Object mit Aktienpositionen |
| `LoginData` | TEXT | Letzte Login-Daten |
| `ShopHardware` | TEXT | Hardware im Shop-Angebot |
| `BankTraces` | TEXT | Bank-Überweisungsspuren |
| `TokenTrace` | TEXT | Token-Spuren |
| `PassiveTraces` | TEXT | Passive Traces |

### Missions analysieren

```sql
-- Missions-String parsen (Spieler-spezifisch):
-- Format: {"missions":{"<uuid>":{"targetUser":"","anyUser":true,"typeMission":1,"targetComputerID":"<ip:port>","reputation":0,"karma":1}}}
SELECT substr(Missions, 1, 300) FROM Players;

-- Oder mit json_extract:
SELECT json_extract(Missions, '$.missions') FROM Players;
```

**Mission-Types:** `typeMission: 1` = Standard-Mission (Anfänger).

### Storage / Inventar

`Storage` enthält ein serialisiertes Format (kein Standard-JSON). Prüfe String-Länge zur Grobabschätzung: `SELECT length(Storage) FROM Players;`

---

## Computer-Hardware-Analyse

### Hardware-JSON-Struktur

```json
{
  "cpu": "Generic 434YA",
  "cores": 1,
  "ghz": 1.00,
  "ram": 128,
  "hdd": 350,
  "hdmodel": "Generic OIU768",
  "hddRPM": 4200,
  "mainboard": "Generic 48QCUM74",
  "netmodel": "DOI173",
  "netType": 0,
  "netTypeName": "WLAN"
}
```

### Query-Rezepte

```sql
-- Hardware-Übersicht aller Computer:
SELECT 
  ID,
  json_extract(Hardware, '$.cpu') AS CPU,
  json_extract(Hardware, '$.cores') AS Kerne,
  json_extract(Hardware, '$.ghz') AS GHz,
  json_extract(Hardware, '$.ram') AS RAM_MB,
  json_extract(Hardware, '$.hdd') AS HDD_MB,
  json_extract(Hardware, '$.hddRPM') AS RPM,
  json_extract(Hardware, '$.mainboard') AS Mainboard,
  json_extract(Hardware, '$.netmodel') AS Netzwerk
FROM Computer;

-- Verteilung der CPU-Typen:
SELECT json_extract(Hardware, '$.cpu') AS CPU, COUNT(*) AS Anzahl
FROM Computer
GROUP BY CPU
ORDER BY Anzahl DESC;

-- Minimum/Maximum RAM:
SELECT MIN(json_extract(Hardware, '$.ram')) AS MinRAM,
       MAX(json_extract(Hardware, '$.ram')) AS MaxRAM,
       AVG(json_extract(Hardware, '$.ram')) AS AvgRAM
FROM Computer;

-- Computer mit der meisten HDD:
SELECT ID, json_extract(Hardware, '$.hdd') AS HDD
FROM Computer
ORDER BY json_extract(Hardware, '$.hdd') DESC
LIMIT 5;
```

---

## Netzwerk-Topologie

### PlayerConns-Tabelle

```sql
-- Schema:
CREATE TABLE PlayerConns (
  PlayerComputer TEXT,   -- Computer.ID des Spieler-PCs
  RouterComputer TEXT,   -- Computer.ID des Routers
  ConId        INTEGER
);
```

Wenn leer (0 Datensätze): Netzwerk-Topologie ist NICHT in der DB persistiert. Die Auflösung läuft zur Laufzeit über die `Map`-Tabelle (BSSID/ESSID-basiertes WLAN).

### Map-Tabelle

```sql
SELECT * FROM Map;  -- Enthält BSSID, ESSID, Password, etc.
```

---

## Filesystem-Deep-Dive

### Aufbau eines Computer.FileSystem-JSON

```json
{
  "computerID": "<id>",
  "files": [],
  "folders": [
    {
      "files": [
        {
          "ID": "<md5-hash>",
          "nombre": "<filename>",
          "permisos": {"permisos": "-rw-r-----"},
          "owner": "<user>",
          "group": "<group>",
          "size": <bytes>,
          "isBinario": false,
          "isDefaultContent": false,
          "comando": "",
          "typeFile": 0,
          "saved": true,
          "missionID": "",
          "isProtected": false,
          "symlink": "",
          "precio": 0
        }
      ]
    }
  ]
}
```

### Files in einem bestimmten Ordner zählen

```sql
-- Anzahl Dateien pro Top-Folder (rekursiv nur Top-Level):
SELECT 
  json_extract(folder.value, '$.nombre') AS Ordner,
  json_array_length(json_extract(folder.value, '$.files')) AS FilesCount
FROM Computer, json_each(json_extract(FileSystem, '$.folders')) AS folder
WHERE ID = '<computer-id>';
```

### Files-Tabelle (globale Datei-Contents)

```sql
-- Inhalt eines Files über die Files-Tabelle:
SELECT Content FROM Files WHERE ID = '<md5-hash>';
-- Content ist der Source/Inhalt des Files.
```

**Wichtig:** `Files.Content` enthält den tatsächlichen Datei-Inhalt. `FileSystem.folders[].files[].ID` referenziert auf `Files.ID`. Der Join läuft über die MD5-Hash-ID.

---

## Benutzer-Analyse

### Users-JSON-Struktur

```json
[
  {
    "exp": <int>,
    "nivel": <int>,
    "walletCoins": <int>,
    "notas": "",
    "isRented": false,
    "nombreUsuario": "root",
    "passPlano": "",
    "passEncriptado": "<hash>",
    "directorio": "/home/root/",
    "isInside": false,
    "numConnections": 0,
    "totaltime": 0,
    "isConnected": false,
    "fechaConex": null
  }
]
```

### Alle Nicht-Root-User mit Passwörtern finden

```sql
SELECT 
  substr(ID, 1, 30) AS Computer,
  json_extract(user.value, '$.nombreUsuario') AS User,
  json_extract(user.value, '$.passPlano') AS PassPlain,
  json_extract(user.value, '$.passEncriptado') AS PassHash,
  json_extract(user.value, '$.nivel') AS Level,
  json_extract(user.value, '$.directorio') AS HomeDir
FROM Computer, json_each(Users) AS user
WHERE json_extract(user.value, '$.nombreUsuario') != 'root'
ORDER BY Computer;
```

---

## Bericht-Erstellung

### Struktur für einen vollständigen DB-Analyse-Report

1. **DB-Metadaten:** Pfad, Größe, Tabellen-Anzahl
2. **Spieler-Status:** PlayerID, Nickname, GameOver, LastConnection, aktive Missionen
3. **Computer-Bestand:** Gesamtanzahl, Verteilung (Player/Router/Server/CTF)
4. **Hardware-Übersicht:** Tabellarisch (CPU, Kerne, RAM, HDD, RPM, Mainboard)
5. **User-Übersicht:** Alle Accounts auf allen Computern (exkl. root)
6. **Filesystem-Auszug:** Top-Level-Ordner, Dateianzahl pro Computer
7. **Aktive Missionen:** Ziel, Typ, Karma, Reputation
8. **Auffälligkeiten:** GameOver-Status, schwache Passwörter, leere Verbindungstabellen
9. **Offene Tabellen:** Liste der nicht analysierten Tabellen für Folge-Reports

---

## Pitfalls

- **`PlayerConns` ist oft leer** — das ist normal für frische/kleine Welten. Nicht als Bug interpretieren.
- **GameOver=1** bedeutet der Spieler ist tot — das ist ein Zustand, kein Bug. Die DB wird trotzdem weitergenutzt.
- **Passwörter im Klartext** (`Users[*].passPlano`, `ConfigOS.userMail.password`) sind sensitiv — im Report maskieren oder nur Hashes zeigen.
- **MD5-Hashes** sind deterministisch aus dem Klartext ableitbar — GreyHack verwendet kein Salt.
- **LastConnection auf `2000-01-06`** ist der initiale Spielzeit-Start, kein echtes Datum.
- **Server-Welten haben 15+ Router mit identischer Hardware** (arm_cpu, 64 MB RAM, 1000 MB HDD @ 4200 RPM) — das ist der Minimal-Router-Template, nicht besondere Konfiguration.
- **Herstellungsdatum (`precio`)** in File-Einträgen ist 0 bei Default-Content — das ist kein Preis, sondern ein Integer-Flag.
