# GreyHack DB — Forensische Analyse-Muster

**Quelle:** Save-Analyse 2026-07-04 (56 ungescannte IPs, Mission-Target-Analyse)
**Englische Bezeichner in Queries — Kommentare auf Deutsch**

## Überblick

Dieses Referenzdokument enthält **analytische Multi-Table-Query-Patterns** zur Rekonstruktion von:
- Missions-Targets aus Spielers Daten
- Angriffsketten (TokenTrace-basiert)
- Kompromittierte Router (bounceIp-Indikatoren)
- Bank-Account → Netzwerk-Zuordnung
- Ziel-Priorisierung für ungescannte IPs

## 1. Mission Target Extraktion

Die Mission des Spielers ist in `Players.Missions` JSON-encoded. Das `targetComputerID`-Feld enthält die Ziel-IP + Port.

```sql
-- Mission-Target-Computer finden
SELECT json_extract(Missions, '$.targetComputerID') AS TargetID,
       json_extract(Missions, '$.typeMission') AS Type,
       json_extract(Missions, '$.anyUser') AS AnyUser,
       json_extract(Missions, '$.reputation') AS Rep,
       json_extract(Missions, '$.karma') AS Karma,
       json_extract(Missions, '$.missionToken') AS Token
FROM Players
LIMIT 1;
```

**Output-Beispiel:**
| TargetID | Type | AnyUser | Rep | Karma | Token |
|----------|------|---------|-----|-------|-------|
| 16.174.201.225:746422179 | 1 | 1 | 0 | 1 | ee23d05c-... |

**Implikation:** Der Token `ee23d05c-...` ist der Mission-Trace-Token, der bei JEDER Aktion im Spiel auf dem Target-Computer geschrieben wird.

## 2. TokenTrace — Komplette Angriffskette rekonstruieren

Der `tokenTrace` im `Logs.contentLog` JSON verbindet ALLE Aktionen eines Spielers für EINE Mission.

```sql
-- Alle Aktionen einer Mission (via tokenTrace)
SELECT json_extract(value, '$.ip') AS IP,
       json_extract(value, '$.puerto') AS Port,
       json_extract(value, '$.action') AS Action,
       json_extract(value, '$.fecha') AS Date,
       json_extract(value, '$.file') AS File,
       json_extract(value, '$.bounceIp') AS Bounce,
       json_extract(value, '$.playerNetID') AS PlayerID,
       json_extract(value, '$.tutorial') AS Tutorial
FROM Logs, json_each(Log, '$.contentLog')
WHERE json_extract(value, '$.tokenTrace') = 'TOKEN_HERE'
ORDER BY json_extract(value, '$.fecha');
```

**Action-Codes:**
| Code | Bedeutung |
|------|-----------|
| 0 | Ping / Port-Scan-Start / Verbindungsaufbau |
| 1 | Firewall-Regel gesetzt |
| 2 | Exploit-Ausführung / Brute-Force-Treffer |
| 3 | Sniffer-Capture / Datei-Download |
| 4 | Port-Scan (via bounceIp) |

**Praxis-Tipp:** Actions 0 + 1 ohne bounceIp = Recon lokal; Action 2 = erfolgreicher Hack; Action 4 mit bounceIp = Scan über kompromittierten Router.

## 3. bounceIp — Kompromittierte Router identifizieren

Wenn ein Router als `bounceIp` in Logs auftaucht, wurde er von jemandem geknackt und als Relay benutzt.

```sql
-- Alle Router, die als Bounce (Relay) genutzt wurden
SELECT json_extract(value, '$.bounceIp') AS BouncedRouter,
       COUNT(*) AS TimesUsed,
       GROUP_CONCAT(DISTINCT json_extract(value, '$.fecha')) AS Dates
FROM Logs, json_each(Log, '$.contentLog')
WHERE json_extract(value, '$.bounceIp') != ''
GROUP BY BouncedRouter
ORDER BY TimesUsed DESC;
```

**Mit Map-Info anreichern:**
```sql
SELECT M.IpAddress, M.Essid, M.AccessType, M.WebAddress, B.TimesUsed, B.Dates
FROM (
    SELECT json_extract(value, '$.bounceIp') AS BouncedIP,
           COUNT(*) AS TimesUsed,
           GROUP_CONCAT(DISTINCT json_extract(value, '$.fecha')) AS Dates
    FROM Logs, json_each(Log, '$.contentLog')
    WHERE json_extract(value, '$.bounceIp') != ''
    GROUP BY BouncedIP
) B
LEFT JOIN Map M ON M.IpAddress = B.BouncedIP
ORDER BY B.TimesUsed DESC;
```

## 4. Ziel-Priorisierung aus Map + Logs + Passwords + BankAccounts

Die Kernlogik für "Welche der N ungescannten IPs ist wichtiger?":

```sql
-- Volle Priorisierungs-Query
SELECT M.IpAddress, M.Essid, M.AccessType, M.WebAddress,
       CASE WHEN M.AccessType = 0 THEN 'PUBLIC' ELSE 'LAN' END AS Reach,
       CASE WHEN P.ID IS NOT NULL THEN 'YES' ELSE 'no' END AS HasPass,
       CASE WHEN B.ID IS NOT NULL THEN 'YES' ELSE 'no' END AS HasBank,
       CASE WHEN L.LogCount > 0 THEN CAST(L.LogCount AS TEXT) ELSE '0' END AS LogHits,
       CASE WHEN Miss.Target IS NOT NULL THEN '🎯MISSION' ELSE '' END AS IsMissionTarget
FROM Map M
LEFT JOIN (SELECT DISTINCT ID, PlainPassword FROM Passwords) P
    ON 1=2  -- Passwords haben keine IP-Verknüpfung — domain-basiert
LEFT JOIN BankAccounts B ON B.ID LIKE '%' || M.WebAddress || '%'
LEFT JOIN (
    SELECT json_extract(value, '$.ip') AS IP, COUNT(*) AS LogCount
    FROM Logs, json_each(Log, '$.contentLog')
    GROUP BY IP
) L ON L.IP = M.IpAddress
LEFT JOIN (
    SELECT json_extract(Missions, '$.targetComputerID') AS Target
    FROM Players
    LIMIT 1
) Miss ON Miss.Target LIKE M.IpAddress || '%'
ORDER BY M.IpAddress;
```

**Praktischere Variante (direkt auf den N ungescannten IPs):**
```sql
-- Priorisierung: Public > Hat BankAccount > Mission-Target > Hat Logs
SELECT M.IpAddress, M.Essid,
       CASE M.AccessType WHEN 0 THEN '🌐PUBLIC' WHEN 1 THEN '🔒LAN' END AS Type,
       M.WebAddress,
       CASE WHEN B.ID IS NOT NULL THEN '💰BANK' ELSE '' END AS HasBank,
       CASE WHEN P.ID IS NOT NULL THEN '🔑PW' ELSE '' END AS HasPass,
       CASE WHEN Miss.Target LIKE M.IpAddress || '%' THEN '🎯MISSION' ELSE '' END AS Target
FROM Map M
LEFT JOIN BankAccounts B ON B.ID LIKE '%' || M.WebAddress || '%'
LEFT JOIN (SELECT ID FROM Passwords) P ON 1=2
LEFT JOIN (
    SELECT json_extract(Missions, '$.targetComputerID') AS Target
    FROM Players LIMIT 1
) Miss ON 1=1
WHERE M.IpAddress NOT IN (
    SELECT DISTINCT json_extract(value, '$.ip')
    FROM Logs, json_each(Log, '$.contentLog')
    WHERE json_extract(value, '$.ip') != ''
)
ORDER BY M.AccessType ASC,  -- Public zuerst
         CASE WHEN B.ID IS NOT NULL THEN 0 ELSE 1 END,
         CASE WHEN Miss.Target LIKE M.IpAddress || '%' THEN 0 ELSE 1 END;
```

## 5. BankAccount → Netzwerk-Zuordnung

BankAccounts enthalten `origBankAddress` und `origBankDomain`. Die dazugehörige IP ist im Map unter `WebAddress` zu finden.

```sql
-- Jeden BankAccount mit seiner Map-IP verbinden
SELECT B.ID AS Account,
       B.WebAddress AS AccountDomain,
       M.IpAddress AS NetworkIP,
       M.Essid AS NetworkName,
       M.AccessType,
       B.isPlayer,
       B.dinero,
       B.origBankAddress,
       B.origBankDomain
FROM BankAccounts B
LEFT JOIN Map M ON M.WebAddress = B.WebAddress
ORDER BY B.dinero DESC;
```

**Mit Transaktionshistorie:**
```sql
-- Letzte Transaktion pro Account
SELECT B.ID AS Account,
       json_extract(T.value, '$.to') AS ToAddr,
       json_extract(T.value, '$.concept') AS Concept,
       json_extract(T.value, '$.quantity') AS Amount,
       json_extract(T.value, '$.fecha') AS Date,
       json_extract(T.value, '$.traza') AS Trace
FROM BankAccounts B,
     json_each(B.Transactions, '$.sendTransfers') AS T
ORDER BY json_extract(T.value, '$.fecha') DESC;
```

## 6. Netzwerk-Topologie aus Computer-Router-Daten

Der `Computer`-Eintrag eines Routers enthält `idxPublicIPs` (10 angeschlossene öffentliche IPs) und `idxLocalIPs` (interne LAN-IPs).

```sql
-- Router-Daten aus Computer-Tabelle extrahieren
SELECT ID AS ComputerID,
       json_extract(Users, '$.pcName') AS RouterName,
       json_extract(Users, '$.ipPublica') AS PublicIP,
       json_extract(Users, '$.ipLocal') AS LocalIP,
       json_extract(Users, '$.maxNumWorkers') AS MaxWorkers,
       json_extract(Users, '$.netSpeed') AS NetSpeed
FROM Computer
WHERE IsRouter = 1;
```

**Alle SmartPhones hinter einem Router:**
```sql
-- SmartPhones eines Routers aus Users->smartPhones JSON
SELECT ID AS ComputerID,
       key AS NPCName,
       value AS SmartPhoneID
FROM Computer,
     json_each(Users, '$.smartPhones')
WHERE IsRouter = 1;
```

## 7. Computer-Tabelle vs Map-Tabelle — Diskrepanz

Ein Target kann in der `Map`-Tabelle sein (scanbar), aber NICHT in der `Computer`-Tabelle (noch nie besucht/gescannt). Das ist **normal** — die Computer-Tabelle wird erst beim ersten Scan/Verbindung befüllt.

```sql
-- In Map aber NICHT in Computer (noch nicht besucht)
SELECT M.IpAddress, M.Essid, M.AccessType, M.WebAddress
FROM Map M
WHERE M.IpAddress NOT IN (
    SELECT DISTINCT substr(ID, 1, instr(ID, ':') - 1)
    FROM Computer
    WHERE instr(ID, ':') > 0
)
ORDER BY M.AccessType, M.IpAddress;
```

## 8. Spieler-Position aus PlayerConns (wenn vorhanden)

```sql
-- Aktuelle Spieler-Position
SELECT P.Name AS PlayerName,
       C.indMap,
       C.posX,
       C.posY,
       C.publicIP,
       C.ipLocal,
       C.ipLAN
FROM PlayerConns PC
JOIN Players P ON P.ID = PC.playerID
JOIN Computer C ON C.ID = PC.computerID
ORDER BY PC.lastUpdate DESC
LIMIT 1;
```

**Hinweis:** `PlayerConns` kann leer sein — dann Spieler-Position aus `Players.Pos.X` / `.Y` lesen.

## 9. Passwort zum BankAccount finden

Das `Passwords`-Table hat KEINE direkte IP-Verknüpfung. Passwörter sind über die Domain verknüpft — der MD5-Hash des Passworts erscheint als `encPassword` im BankAccount-JSON, und der Plaintext steht in `Passwords`.

**Manuelle Korrelation (zwei Schritte):**

Schritt 1: Welche BankAccounts haben Passwörter in der Passwords-Table?
```sql
-- Account-Domain + konkreten Plaintext finden
SELECT BA.ID AS AccountDomain,
       P.PlainPassword,
       BA.dinero,
       BA.isPlayer
FROM BankAccounts BA
JOIN Passwords P ON BA.ID LIKE '%' || P.PlainPassword || '%'
    OR BA.WebAddress = P.PlainPassword;
```

Schritt 2: Transaktionszuordnung (Player-Bank hat `consumeTransactions`):
```sql
-- Wer hat Geld an wen geschickt?
SELECT B.ID AS SourceAccount,
       json_extract(T.value, '$.to') AS TargetAccount,
       json_extract(T.value, '$.quantity') AS Amount,
       json_extract(T.value, '$.fecha') AS Date,
       json_extract(T.value, '$.traza') AS Trace
FROM BankAccounts B,
     json_each(B.Transactions, '$.consumeTransactions') AS T
WHERE json_extract(T.value, '$.quantity') > 0
ORDER BY json_extract(T.value, '$.fecha');
```

## 10. Angriffs-Route aus allen Daten generieren

Diese Query baut eine komplette Multi-Table-Priorisierung:

```sql
SELECT M.IpAddress, M.Essid,
       CASE WHEN M.AccessType = 0 THEN '🌐PUBLIC' ELSE '🔒LAN' END AS Type,
       M.WebAddress,
       IFNULL(B.AccountInfo, '') AS Bank,
       CASE WHEN L.Hits > 0 THEN CAST(L.Hits AS TEXT) ELSE '0' END AS Hits,
       CASE WHEN Bounce.Uses > 0 THEN '🔄bounced' ELSE '' END AS IsBounce,
       CASE WHEN MT.IP = M.IpAddress THEN '🎯MISSION' ELSE '' END AS IsTarget
FROM Map M
LEFT JOIN (
    SELECT DISTINCT WebAddress AS WA,
           GROUP_CONCAT(ID || '(' || CAST(dinero AS TEXT) || '$)') AS AccountInfo
    FROM BankAccounts GROUP BY WebAddress
) B ON B.WA = M.WebAddress
LEFT JOIN (
    SELECT IP, COUNT(*) AS Hits
    FROM (SELECT json_extract(value, '$.ip') AS IP FROM Logs, json_each(Log, '$.contentLog'))
    GROUP BY IP
) L ON L.IP = M.IpAddress
LEFT JOIN (
    SELECT json_extract(value, '$.bounceIp') AS BIP, COUNT(*) AS Uses
    FROM Logs, json_each(Log, '$.contentLog')
    WHERE json_extract(value, '$.bounceIp') != ''
    GROUP BY BIP
) Bounce ON Bounce.BIP = M.IpAddress
LEFT JOIN (
    SELECT substr(
        json_extract(Missions, '$.targetComputerID'),
        1, instr(json_extract(Missions, '$.targetComputerID'), ':') - 1
    ) AS IP
    FROM Players LIMIT 1
) MT ON 1=1
WHERE M.IpAddress NOT IN (
    SELECT DISTINCT substr(ID, 1, instr(ID, ':') - 1)
    FROM Computer WHERE instr(ID, ':') > 0
)
ORDER BY M.AccessType, IsTarget DESC, L.Hits DESC;
```

## Fallstricke

1. **`Computer.ID`-Format:** `IP_Router:Zufallszahl` (z.B. `158.14.166.104:261738086`). Der IP-Teil vor dem `:` ist die öffentliche IP.
2. **`Passwords` ohne IP-Bezug:** Passwords sind über die Domain verknüpft, nicht über die IP. Immer über `BankAccounts.WebAddress` → `Map.WebAddress` joinen.
3. **`json_each` benötigt Pfad:** Bei `Logs` ist der Pfad `'$.contentLog'`, bei `BankAccounts` für Transfers `'$.sendTransfers'` oder `'$.consumeTransactions'`.
4. **`Computer`-Tabelle ≠ alle IPs:** Nur besuchte oder gescannte Computer sind dort. Die `Map`-Tabelle ist der vollständige Scan-Radar.
5. **PlayerConns kann leer sein:** Ist kein Fehler — bedeutet nur "keine aktiven Verbindungen dokumentiert".
6. **`LibVersions` in Map kann null sein:** Nicht jede Map-Zeile hat Library-Versionen. LibVersions werden erst beim Port-Scan oder nach Exploit befüllt.
7. **`substr` für IP-Extraktion:** `substr(ID, 1, instr(ID, ':') - 1)` extrahiert die IP aus `Computer.ID` — funktioniert nur wenn `instr(ID, ':') > 0`.
8. **Action-Code 0 = mehrdeutig:** Kann Ping, Port-Scan-Begin, Verbindungsaufbau ODER Recon bedeuten. Kontext aus bounceIp, Date, und vorherigen Aktionen im gleichen Token-Trace erschließen.
9. **Einzeiler-Variante für Map-Einträge ohne Logs:** Bei 56 ungescannten IPs hat keine einen Log-Eintrag — die LEFT-Joins liefern `null`, was als `0` interpretiert werden muss.
