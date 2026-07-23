# GreyHackDB — File Inventory & Content Analysis (Stand 2026-07-04)

**DB-Pfad:** `/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db`
**DB-Version:** V0.9.6771-beta | **SQLite-Version:** 3.x
**DB-Größe (roh):** 6,66 MB | **1.704 Pages** | **Schema 4**

---

## Schema

```sql
CREATE TABLE Files (ID TEXT PRIMARY KEY, Content TEXT, refCount INTEGER NOT NULL DEFAULT 1);
CREATE TABLE BackupPlayerFiles (ID TEXT PRIMARY KEY, Content TEXT);
```

**Wichtig:** ID ist ein **GUID** (z.B. `96e37239-0ad4-4dcf-b31c-16c4a66d1907`) — kein Dateiname! Die Klassifizierung erfolgt ausschließlich **heuristisch über den Content**. `nombre`/`computer_pk`/`content_type` existieren im aktuellen Schema NICHT mehr.

BackupPlayerFiles ist typischerweise **leer** — die In-Game-Backup-Funktion ist nicht implementiert oder wurde nie genutzt.

---

## Content-basierte Klassifizierung

Da Files-nur GUID-IDs haben, folgende Heuristik:

| Kategorie | Erkennungs-Regel | Typisches Vorkommen |
|-----------|-----------------|---------------------|
| `src (user-defined command)` | Content beginnt mit `//command:` oder `//Command:` | ~64 von 247 Files |
| `src (yuno-module)` | Content enthält `YUNO` oder `yuno_v` | ~18 Files |
| `src (script)` | Content beginnt mit `//` (GreyScript-Kommentar) | ~8 Files |
| `other (data/bin)` | Alles andere (JSON, Metaxploit-Lib-Daten, leer) | ~170 Files |
| `empty` | `LENGTH(Content) = 0` | 1 File (MD5("")) |

### Common Analysis Queries

```sql
-- 1. Files zählen + Gesamtgröße
SELECT COUNT(*) AS total, ROUND(SUM(LENGTH(Content))/1024.0, 1) AS total_kb FROM Files;

-- 2. Top-N größte Files
SELECT LENGTH(Content) AS bytes, ROUND(LENGTH(Content)/1024.0, 1) AS kb, refCount, 
       substr(ID, 1, 12) AS id_short
FROM Files
ORDER BY LENGTH(Content) DESC
LIMIT 20;

-- 3. refCount-Verteilung (Deduplizierung)
SELECT refCount, COUNT(*) AS n_files, ROUND(SUM(LENGTH(Content))/1024.0, 1) AS total_kb
FROM Files GROUP BY refCount ORDER BY refCount DESC;

-- 4. Content-Klassifizierung (SQL CASE Heuristik)
SELECT 
  CASE 
    WHEN Content LIKE '//command:%' OR Content LIKE '//Command:%' THEN 'src_command'
    WHEN Content LIKE '%YUNO%' OR Content LIKE '%yuno%' THEN 'src_yuno'
    WHEN Content LIKE '//%' THEN 'src_script'
    WHEN LENGTH(Content) = 0 THEN 'empty'
    ELSE 'data_bin'
  END AS category,
  COUNT(*) AS n,
  ROUND(SUM(LENGTH(Content))/1024.0, 1) AS total_kb
FROM Files GROUP BY category ORDER BY n DESC;

-- 5. Content-Keyword-Suche (Tool-Namen)
SELECT 'yuno' AS keyword, COUNT(*) AS hits FROM Files WHERE Content LIKE '%yuno%'
UNION ALL SELECT 'metaxploit', COUNT(*) FROM Files WHERE Content LIKE '%metaxploit%'
UNION ALL SELECT 'nmap', COUNT(*) FROM Files WHERE Content LIKE '%nmap%'
-- usw.

-- 6. YUNO-Varianten identifizieren
SELECT 
  substr(ID, 1, 8) AS id_short,
  LENGTH(Content) AS bytes,
  CASE 
    WHEN Content LIKE '%YUNO V6%' THEN 'yuno_v6'
    WHEN Content LIKE '%yuno_v5%' THEN 'yuno_v5'
    WHEN Content LIKE '%yuno_mini%' THEN 'yuno_mini'
    ELSE 'yuno-other'
  END AS variant
FROM Files WHERE Content LIKE '%YUNO%' OR Content LIKE '%yuno_v%' OR Content LIKE '%yuno_mini%'
ORDER BY LENGTH(Content) DESC;

-- 7. Alle //command: Marker extrahieren
SELECT DISTINCT SUBSTR(Content, 11, INSTR(SUBSTR(Content, 11), char(10)) - 1) AS cmd_name
FROM Files
WHERE Content LIKE '//command:%' OR Content LIKE '//Command:%'
ORDER BY cmd_name;
```

---

## Typische Ergebnisse (Bastis Live-DB, 2026-07-04)

| Metrik | Wert |
|--------|------|
| Files total | **247** |
| Davon refCount>1 (dedupliziert) | **8** (3,2 %) |
| Gesamter Files-Content | **1.423 KB (1,39 MB)** |
| TOP-5 Files (Anteil) | **54 %** → 296 KB |
| Größtes File | **78.155 B (YUNO V6)** |
| Kleinste Files | 0 B (MD5("")) |
| Mittlere File-Größe | 5.903 B |
| YUNO-Files (alle Varianten) | **18 Files, 369 KB** |
| Metaxploit-Referenzen | **155 Files** |

### TOP 20 Largest Files (LIVE DB)

| # | ID (short) | Bytes | KB | Type |
|---|------------|------:|:--|:-----|
| 1 | `96e37239…` | 78.155 | 76,3 | YUNO V6 |
| 2 | `5d677974…` | 66.499 | 64,9 | YUNO V5 |
| 3 | `049c07ec…` | 53.698 | 52,4 | yuno-modul |
| 4 | `ffe3175a…` | 52.161 | 50,9 | yuno-modul |
| 5 | `8914f808…` | 45.220 | 44,2 | yuno-modul |
| 6 | `71893a5b…` | 17.813 | 17,4 | yuno-modul |
| 7 | `93d2f622…` | 16.050 | 15,7 | Metaxploit-Lib |
| 8 | `145b13c8…` | 14.561 | 14,2 | Metaxploit-Lib |
| 9 | … | ~13-12 KB | ~13-11 | Metaxploit-Libs |
| 20 | `ab9c3307…` | 11.080 | 10,8 | Metaxploit-Lib |

### refCount-Verteilung

| refCount | Files | Gesamt-KB | Bedeutung |
|:--------:|:-----:|:---------:|-----------|
| 5 | 1 | 0,0 | MD5("") — leeres File, 5× referenziert |
| 2 | 7 | 5,7 | Kleine Populär-Files (wiederverwendet) |
| 1 | 239 | 1.418,3 | Regelfall |

### 61 Extrahiert //command:-Namen

System-Tools: `cd`, `ls`, `ps`, `pwd`, `ifconfig`, `iwconfig`, `iwlist`, `cat`, `rm`, `mv`, `cp`, `ssh`, `ftp`, `mkdir`, `chmod`, `reboot`, `whois`, `sudo`, `useradd`, `userdel`, `passwd`, `nslookup`, `build`, `touch`, `chown`, `chgrp`, `groupadd`, `groupdel`, `groups`, `kill`, `ping`, `apt-get`, `man`, `whoami`, `ln`, `scp`, `airmon`, `aireplay`, `aircrack`, `sshd`, `decipher`, `scanrouter`, `rshell-server`, `nmap`, `repository-server`, `repod`, `ftp-server`, `chat-server`

YUNO-Module: `yuno`, `yuno_v6`, `yuno_v5`, `yuno_mini`, `yuno_attack`, `yuno_core`, `yuno_crypto_net`, `yuno_macros`, `yuno_mission`, `yuno_recon`, `yuno_snapshots`, `yuno_suggest_plugin`, `yuno_util`, `yuno_files`

---

## Praktischer Workflow für Content-Analyse

### 1. DB kopieren (niemals live öffnen)
```bash
DB_SRC="/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db"
cp "$DB_SRC" /tmp/greyhack.db
sqlite3 /tmp/greyhack.db "PRAGMA integrity_check;"
```

### 2. Schema erkunden
```bash
sqlite3 /tmp/greyhack.db ".tables"
sqlite3 /tmp/greyhack.db ".schema Files"
sqlite3 /tmp/greyhack.db ".schema BackupPlayerFiles"
```

### 3. Content-Inhaltsprobe (Metaxploit-Lib = JSON, YUNO = GreyScript)
```bash
# Sample von "data_bin" (Metaxploit-Lib ist JSON mit Vulnerability-Defs)
sqlite3 /tmp/greyhack.db "SELECT substr(Content, 1, 200) FROM Files WHERE ID='93d2f622...'"
# Sample von "src" (YUNO Source)
sqlite3 /tmp/greyhack.db "SELECT substr(Content, 1, 200) FROM Files WHERE Content LIKE '//command:yuno%' LIMIT 1"
```

### 4. Komplette Content-Klassifizierung (ein Befehl)
```bash
sqlite3 /tmp/greyhack.db <<'SQL'
SELECT 
  CASE 
    WHEN Content LIKE '//command:%' THEN 'src_command'
    WHEN Content LIKE '%YUNO%' THEN 'src_yuno'
    WHEN Content LIKE '//%' THEN 'src_script'
    WHEN LENGTH(Content) = 0 THEN 'empty'
    ELSE 'data_bin'
  END AS cat,
  COUNT(*) AS n,
  ROUND(SUM(LENGTH(Content))/1024.0, 1) AS kb,
  ROUND(AVG(LENGTH(Content)), 0) AS avg
FROM Files GROUP BY cat ORDER BY n DESC;
SQL
```

---

## Wichtige Erkenntnisse für künftige Sessions

1. **GUIDs statt Dateinamen** → keine Annahme über `nombre`/`Name`/`path` in `Files`-Tabelle machen. Nur `ID`, `Content`, `refCount`.
2. **Content-Heuristik nötig** → `//command:` Marker ist der sicherste Indikator für User-Script-Sources. YUNO-Content für Framework-Module. JSON-Payloads = Metaxploit-Lib-Daten.
3. **BackupPlayerFiles ist immer leer** — wenn Analyse des Spieler-Backups gewünscht, direkt in `Computer.FileSystem` (JSON) suchen.
4. **refCount > 1 bedeutet Deduplizierung** — populäre Files (besonders MD5("")) werden geteilt. Ein File mit refCount=5 bedeutet, dass 5 Computer/Player dieselbe leere Datei referenzieren.
5. **YUNO V6 ist das größte File (76-78 KB)** — gefolgt von V5 (~66 KB). Die Content-Konzentration auf die TOP-5 Files (54 %) zeigt, dass YUNO den dominanten Speicheranteil in der DB hat.
6. **HDD-Anteil der DB ist vernachlässigbar** (~0,002 % der 320 GB HDD) — Storage-Probleme liegen am In-Game-FileSystem-JSON, nicht an der DB-Datei selbst.
