# GreyHack DB — Schema & Tabellen-Analyse

> Queries und Column-Meanings für die SQLite-DB (`GreyHackDB.db`), ermittelt durch Live-Inspektion 2026-07-03 (V0.9.6771-beta).

## Tabellen-Übersicht

| Tabelle | Zweck |
|---------|-------|
| `Map` | Netzwerk-Knoten (IPs, Router, Bssid/Essid, AccessType) |
| `WebPages` | Gehostete Webseiten (TypeNet, NumVisits) |
| `Logs` | Zugriffs-/Angriffs-Historie (JSON-Logs mit Action-Codes) |
| `Computer` | Detaillierte Computer-Zustände (FileSystem, Hardware, Users) |
| `Files` | Datei-Inhalte (Content als TEXT) |
| `PlayerConns` | Spieler-Verbindungs-Topologie (Computer → Router → LocalIp) |
| `SharedConns` | Shared-Verbindungen zwischen Spielern |

---

## 1. Map — Netzwerk-Knoten

### Schema
```sql
CREATE TABLE Map (
    IpAddress TEXT PRIMARY KEY,
    AccessType INTEGER,
    WebAddress TEXT,
    Essid TEXT,
    Bssid TEXT,
    posX REAL,
    posY REAL,
    Mission TEXT,
    LibVersions TEXT,
    LogsKey TEXT,
    Process INTEGER
);
```

### Spalten-Bedeutung

| Spalte | Typ | Bedeutung |
|--------|-----|-----------|
| `AccessType` | INT | 0 = **public** (direkt aus dem Internet erreichbar), 1 = **LAN-only** (hinter Router) |
| `WebAddress` | TEXT | Domain-Name (z.B. `www.peyasikin.info`). Jede IP hat genau eine. |
| `Essid` | TEXT | WLAN-Name (Router-Name, z.B. `Pall`, `Therwing`, `Kimball`). Eindeutig pro IP. |
| `Bssid` | TEXT | MAC-Adresse des Routers. Eindeutig pro IP. |
| `posX`, `posY` | REAL | Welt-Koordinaten. Gleiche Position → gleiches LAN/Gebäude. |
| `Mission` | TEXT | Mission-Feld (leer `''` wenn keine Mission aktiv). |
| `LibVersions` | TEXT | JSON mit `libVersions`-Object: `libssh.so`, `libftp.so`, `libhttp.so`, `libsql.so` jeweils mit MD5-Hash. |
| `LogsKey` | TEXT | Key in die `Logs`-Tabelle (Format `IP:Timestamp`). Nicht immer gesetzt. |
| `Process` | INT | (unbekannt, meist 0) |

### Nützliche Queries

```sql
-- AccessType-Verteilung
SELECT AccessType, COUNT(*) AS Anzahl FROM Map GROUP BY AccessType;

-- Router ohne Computer-Eintrag (41 von 56 = ungescannt)
SELECT m.IpAddress, m.AccessType, m.WebAddress
FROM Map m LEFT JOIN (
  SELECT DISTINCT substr(ID, 1, instr(ID, ':' )-1) AS IP FROM Computer WHERE ID LIKE '%:%'
) c ON c.IP = m.IpAddress
WHERE c.IP IS NULL
ORDER BY m.IpAddress;

-- Bssid-Cluster: Anzahl IPs pro Router
SELECT Bssid, COUNT(*) AS Ips FROM Map GROUP BY Bssid ORDER BY Ips DESC;
-- (Erwartet: alle = 1 in frischer World)

-- IPs mit Mission != ''
SELECT IpAddress, AccessType, WebAddress FROM Map WHERE Mission != '';

-- LibVersions als extrahierte Hashes
SELECT IpAddress,
  json_extract(LibVersions, '$.libVersions.libssh.so') AS ssh_hash,
  json_extract(LibVersions, '$.libVersions.libhttp.so') AS http_hash
FROM Map LIMIT 5;
```

---

## 2. WebPages — Gehostete Webseiten

### Schema
```sql
CREATE TABLE WebPages (
    Web TEXT,
    ExternalPort INTEGER,
    PublicIp TEXT,
    LocalIp TEXT,
    Address TEXT,
    TypeNet INTEGER,
    NumVisits INTEGER DEFAULT 0,
    DateCreation INTEGER DEFAULT 0,
    PRIMARY KEY(PublicIp, LocalIp)
);
CREATE INDEX idxTypeNet ON WebPages (TypeNet);
CREATE INDEX idxNumVisits ON WebPages (NumVisits);
CREATE INDEX idxDateCreation ON WebPages (DateCreation);
CREATE INDEX idxAddress ON WebPages (Address);
```

### Spalten-Bedeutung

| Spalte | Bedeutung |
|--------|-----------|
| `Web` | HTML-Quelltext der Seite (komplett, als TEXT) |
| `ExternalPort` | Port auf dem Router (z.B. 80) |
| `PublicIp` | Öffentliche IP des Routers |
| `LocalIp` | Lokale IP des Servers innerhalb des LANs (z.B. `192.168.1.2`) |
| `Address` | Domain-Name (z.B. `www.osisuyeyir.com`) |
| `TypeNet` | **Seitentyp-Code** — siehe Tabelle unten |
| `NumVisits` | Besucher-Zähler (frisch: immer 0) |
| `DateCreation` | Erstellungsdatum (Unix-Timestamp; frisch: immer 0) |

### TypeNet-Codes (Live-DB 2026-07-03, 48 Einträge)

| Code | Anzahl | % | Vermutung |
|-----:|------:|--:|-----------|
| 1 | 5 | 10,4 % | (Standard-HTML-Seite / Landing Page) |
| 2 | 1 | 2,1 % | |
| 4 | 1 | 2,1 % | |
| 5 | 2 | 4,2 % | |
| 6 | 1 | 2,1 % | |
| 7 | 3 | 6,3 % | |
| 8 | 6 | 12,5 % | |
| 9 | 2 | 4,2 % | |
| 10 | 5 | 10,4 % | |
| 12 | 6 | 12,5 % | |
| 14 | 6 | 12,5 % | |
| 15 | 5 | 10,4 % | |
| 17 | 5 | 10,4 % | |

**Hinweis:** Die Codes sind nicht dokumentiert. Vermutlich korrespondieren sie mit verschiedenen Seitentypen (Blog, Forum, Shop, Banking, etc.). Zur Bestätigung müsste man den generierten HTML-Quelltext (`Web`-Spalte) pro TypeNet clustern.

### PublicIp ↔ Map JOIN

**48/48 WebPages-PublicIPs sind in Map vorhanden** — es gibt keine verwaisten WebPages.

```sql
-- Prüfe Konsistenz
SELECT COUNT(*) FROM WebPages wp
LEFT JOIN Map m ON m.IpAddress = wp.PublicIp
WHERE m.IpAddress IS NULL;
```

---

## 3. Logs — Zugriffs-/Angriffs-Historie

### Schema
```sql
CREATE TABLE Logs (
    ID TEXT PRIMARY KEY,
    Log TEXT
);
```

### Inhalt

`Log` ist ein JSON-Objekt mit Array `contentLog`. Jeder Array-Eintrag:

```json
{
    "action": 0,
    "ip": "158.14.166.104",
    "fecha": "04/Jan/2000 - 22:58",
    "puerto": 80,
    "file": "",
    "bounceIp": "",
    "player": ""
}
```

### Action-Codes (Live-DB 2026-07-03, 45 Events über 21 Logs)

| Code | Events | Bedeutung |
|-----:|-------:|-----------|
| 0 | 31 | HTTP-/Webzugriff (Standard-Browse) |
| 4 | 8 | (Portscan / Remote-Aktion) |
| 2 | 4 | (Mail / FTP) |
| 3 | 2 | (Capture / Datei-Zugriff — `file.cap` → Sniffer) |

### Port-Verteilung

| Port | Events | Service |
|-----:|-------:|---------|
| 80 | 26 | HTTP |
| 0 | 10 | unspezifiziert / Port-Scan |
| 22 | 5 | SSH |
| 21 | 4 | FTP |

### Ziel-IP-Häufigkeit

```sql
SELECT json_extract(value, '$.ip') AS TargetIP, COUNT(*) AS Anzahl
FROM Logs, json_each(Log, '$.contentLog')
GROUP BY TargetIP ORDER BY Anzahl DESC;
```

**Ziel 158.14.166.104 ist mit 20 Events das Hauptziel** — starke Indizien für aktive Hack-Sequenzen.

### Log-ID-Format

- **Computer-Logs:** `IP:Timestamp` (z.B. `32.119.19.133:1264618053`) — Logs auf Routern/Computern gespeichert
- **UUID-Logs:** UUID-Format (z.B. `171a9e0f-f9f9-4d76-8f37-d125d3f3e181`) — Logs auf dem Player-PC
- **Besondere IDs:** `0.0.0.0`-Einträge mit action=3 sind Sniffer-Captures

### Nützliche Queries

```sql
-- Action-Verteilung
SELECT json_extract(value, '$.action') AS Action, COUNT(*) AS Anzahl
FROM Logs, json_each(Log, '$.contentLog')
GROUP BY Action ORDER BY Anzahl DESC;

-- Logs nach Länge (größter zuerst — enthält die meisten Events)
SELECT ID, LENGTH(Log) AS LogLen FROM Logs ORDER BY LogLen DESC;

-- Logs mit Sniffer-Capture (action=3)
SELECT ID, Log FROM Logs WHERE Log LIKE '%"action":3%';

-- Vollständigen Log-Content lesen
SELECT substr(Log, 1, 500) FROM Logs WHERE ID = '32.119.19.133:1264618053';
```

---

## 4. Computer — Detail-Zustände

### Schema
```sql
CREATE TABLE Computer (
    FileSystem TEXT,
    Hardware TEXT,
    IsRouter INTEGER,
    IsPlayer INTEGER,
    IsRented INTEGER,
    Users TEXT,
    ConfigOS TEXT,
    Procs TEXT,
    IsCTF INTEGER,
    ID TEXT PRIMARY KEY
);
```

### Spalten-Bedeutung

| Spalte | Typ | Bedeutung |
|--------|-----|-----------|
| `FileSystem` | TEXT | Kompletter Dateisystem-Baum als JSON (siehe `sqlite-database.md`) |
| `Hardware` | TEXT | Hardware-Spezifikation als JSON: `hardDisk.totalSize` (MB), `cpus`, `rams` |
| `IsRouter` | INT | 1 = Router, 0 = Endgerät |
| `IsPlayer` | INT | 1 = Player-PC, 0 = NPC/Computer |
| `IsRented` | INT | 1 = gemieteter Server/Hosting |
| `IsCTF` | INT | 1 = CTF-Challenge-Server |
| `ID` | TEXT | Format: `IP:PortNum` für NPCs/Router oder UUID für Player-PC |
| `Users` | TEXT | JSON mit NPCs und deren Passwörtern/Emails/Schedules |
| `ConfigOS` | TEXT | OS-Konfiguration |
| `Procs` | TEXT | Aktive Prozesse (JSON) |

### Computer-ID-Formate

```
# Router/Computer (NPC):  IP:RandomPort
"158.14.166.104:261738086"

# Player-PC:              UUID
"171a9e0f-f9f9-4d76-8f37-d125d3f3e181"
```

### Flag-Verteilung (erwartet)

| IsRouter | IsPlayer | IsRented | IsCTF | Bedeutung | Anzahl (Beispiel) |
|---------:|---------:|---------:|------:|-----------|:-----------------:|
| 1 | 0 | 0 | 0 | Router-NPC | 15 |
| 0 | 0 | 0 | 0 | Computer hinter Router | 2 |
| 0 | 1 | 0 | 0 | Player-PC | 1 |

### Nützliche Queries

```sql
-- Flag-Verteilung
SELECT IsRouter, IsPlayer, IsRented, IsCTF, COUNT(*) FROM Computer GROUP BY 1,2,3,4;

-- Alle Router-IPs extrahiert
SELECT DISTINCT substr(ID, 1, instr(ID, ':')-1) AS IP FROM Computer WHERE IsRouter=1 AND ID LIKE '%:%';

-- Computer hinter Routern (gleiche IP wie Router, aber IsRouter=0)
SELECT c1.ID FROM Computer c1
WHERE c1.IsRouter=0 AND c1.IsPlayer=0 AND c1.ID LIKE '%:%'
AND substr(c1.ID, 1, instr(c1.ID, ':')-1) IN (
  SELECT DISTINCT substr(c2.ID, 1, instr(c2.ID, ':')-1) FROM Computer c2 WHERE c2.IsRouter=1
);

-- Player-PC finden
SELECT ID FROM Computer WHERE IsPlayer=1;
```

### Map ↔ Computer JOIN

```sql
-- Router aus Map mit Computer-Detail
SELECT m.IpAddress, m.AccessType, m.Essid, m.Bssid, m.WebAddress, c.IsRouter, c.IsPlayer
FROM Map m
INNER JOIN (
  SELECT DISTINCT substr(ID, 1, instr(ID, ':' )-1) AS IP FROM Computer WHERE IsRouter=1
) c ON c.IP = m.IpAddress
ORDER BY m.IpAddress;

-- Map-IPs OHNE Computer-Eintrag (ungescannt)
SELECT m.IpAddress, m.AccessType, m.WebAddress
FROM Map m LEFT JOIN (
  SELECT DISTINCT substr(ID, 1, instr(ID, ':' )-1) AS IP FROM Computer
) c ON c.IP = m.IpAddress
WHERE c.IP IS NULL
ORDER BY m.IpAddress;
```

---

## 5. PlayerConns / SharedConns — Topologie

```sql
CREATE TABLE PlayerConns (ComputerID TEXT PRIMARY KEY, RouterID TEXT, LocalIp TEXT);
CREATE TABLE SharedConns (ComputerID TEXT PRIMARY KEY, Players TEXT);
```

- **PlayerConns:** Verbindet Computer-IDs mit Router-IDs → definiert welche Geräte im selben LAN sind. **Kann leer sein** — die Verbindung wird erst persistiert, wenn der Spieler sie dokumentiert hat.
- **SharedConns:** Shared-Verbindungen zwischen Spielern. Ebenfalls **leer in frischen Saves**.

---

## 6. Typische Analyse-Workflows

### A) Netzwerk-Kompromittierungs-Rekonstruktion

1. **Logs analysieren** → welche IP wurde wie oft angegriffen?
2. **Map → Computer JOIN** → welche dieser IPs sind als Router bekannt?
3. **Computer.JOIN erweitern** → welche Computer hängen hinter den Routern?

```sql
-- Schritt 1: Top-Angriffsziel finden
SELECT json_extract(value, '$.ip') AS IP, COUNT(*) AS Hits
FROM Logs, json_each(Log, '$.contentLog')
GROUP BY IP ORDER BY Hits DESC LIMIT 5;

-- Schritt 2: Ist diese IP ein bekannter Router?
SELECT m.IpAddress, m.Essid, m.WebAddress, m.AccessType
FROM Map m WHERE m.IpAddress IN (
  SELECT DISTINCT json_extract(value, '$.ip') FROM Logs, json_each(Log, '$.contentLog')
);

-- Schritt 3: Ports + Actions für die Hauptziel-IP
SELECT json_extract(value, '$.action') AS Action,
       json_extract(value, '$.puerto') AS Port,
       COUNT(*) AS Anzahl
FROM Logs, json_each(Log, '$.contentLog')
WHERE json_extract(value, '$.ip') = '158.14.166.104'
GROUP BY Action, Port ORDER BY Anzahl DESC;
```

### B) Netzwerkgröße und Angriffsfläche

```sql
-- Gesamtgröße: 56 IPs in Map, 18 Computer bekannt
SELECT 'Map_IPs', COUNT(*) FROM Map
UNION ALL SELECT 'Computer', COUNT(*) FROM Computer
UNION ALL SELECT 'Ungescannt', (SELECT COUNT(*) FROM Map) - (
  SELECT COUNT(DISTINCT substr(ID, 1, instr(ID, ':' )-1)) FROM Computer WHERE ID LIKE '%:%'
);

-- Öffentliche IPs (AccessType=0)
SELECT IpAddress, WebAddress FROM Map WHERE AccessType=0;
```

### C) Aktive Spieler-Verbindungen

```sql
-- Wenn PlayerConns nicht leer ist:
SELECT * FROM PlayerConns;
-- JOIN mit Computer um Details zu sehen:
SELECT pc.ComputerID, pc.RouterID, pc.LocalIp, c.FileSystem, c.Hardware
FROM PlayerConns pc LEFT JOIN Computer c ON c.ID = pc.ComputerID;
```

---

## 7. Besonderheiten & Fallstricke

- **DateCreation = 0 für alle WebPages** — in frischer World nie beschrieben. `DateCreation` ist kein Unix-Timestamp.
- **NumVisits = 0 für alle WebPages** — keine dokumentierten Besuche.
- **Computer.FileSystem ist RIESIG** — ein Eintrag kann >300KB JSON sein. Lies nie alle Spalten auf einmal ohne `LIMIT`.
- **In-Game Binary-Größen sind künstlich** (~5GB) im Vergleich zu HDD-Limit in MB. PlayerConns/SharedConns sind typischerweise leer, wenn der Spieler nicht aktiv mitgeteilt hat.
- **`ID` in `WebPages` existiert NICHT** — PRIMARY KEY ist `(PublicIp, LocalIp)`.
- **Die 41 ungescannten Map-IPs** sind die verfügbare Angriffsfläche im aktuellen Savegame. Siehe Anhang B im GreyHack-Netzwerk-Report.
