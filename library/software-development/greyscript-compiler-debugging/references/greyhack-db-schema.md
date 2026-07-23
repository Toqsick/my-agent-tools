# GreyHackDB Schema Notes (0.9.6771-beta)

Gefunden während Yuno V5 Debug Session (2026-07-03).

## LIVE DB Schema (GreyHackDB.db — wird vom Spiel geöffnet)

Datei: `GreyHack_Data/GreyHackDB.db`

```sql
-- Haupttabelle (vereinfacht, live):
CREATE TABLE Files (
    ID TEXT PRIMARY KEY,      -- UUID-formatierter Key
    Content TEXT,             -- Source-Code oder Binär-Inhalt (Text)
    refCount INTEGER DEFAULT 0
);
```

**NICHT in der LIVE DB vorhanden (obwohl in Backups existent):**
- `nombre` (filename) — existiert NICHT
- `computer_pk` (Büro-Computer-Referenz) — existiert NICHT
- `typeFile` — existiert NICHT
- `comando` (command annotation) — existiert NICHT
- `isBinario` — existiert NICHT

**Wie findet das Spiel die Dateien dann?**
Das Spiel verwaltet Dateien in einer **internen virtuellen Verzeichnisstruktur**, vermutlich über eine andere Tabelle (z.B. FileSystem/Nodes) oder über die Kombination aus `ID` + einer Player-Tabelle. Die `Files`-Tabelle ist nur der Content-Store — das Dateisystem-Layout ist separat.

## Backup DB Schema (ältere Kopie)

```sql
-- Backup-Schema hatte zusätzlich:
CREATE TABLE Files (
    ID TEXT PRIMARY KEY,
    nombre TEXT,              -- Dateiname (z.B. "yuno_v2.src")
    Content TEXT,
    computer_pk INTEGER,      -- Referenz auf Computer/Büro
    typeFile INTEGER,         -- 0=Source, 1=Binary
    refCount INTEGER,
    comando TEXT,             -- Command-String (z.B. "run yuno_v6")
    isBinario INTEGER,        -- 0=Source-File, 1=Binary
    listaZonaMem TEXT         -- Memory-Exploit Daten
);
```

## Source-Files Erkennung

Das Spiel erkennt Source-Files am **`//command:` Marker** in der ersten Zeile von `Content`:

| Merkmal | Source-File | Binary |
|---------|-------------|--------|
| Content erste Zeile | `//command: name` | Beliebig (kein Marker) |
| Grösse | Beliebig (aber <12 KB für Commands) | Beliebig |
| Verwendung | Compilierbar via `build` | Direkt ausführbar |

## Alle funktionierenden Commands (0.9.6771-beta)

Stand 2026-07-03: **52 Source-Scripts** in der DB mit `//command:` Marker:
- `cd`, `ls`, `ps`, `pwd`, `cat`, `cp`, `mv`, `rm`, `mkdir`, `rmdir`, `chmod`, `chown`, `touch`
- `sudo`, `passwd`, `ssh`, `ftp`, `wget`, `nmap`, `ping`, `traceroute`, `netstat`
- `grep`, `head`, `tail`, `sort`, `wc`, `echo`, `print`, `clear`
- `apt-get`, `install`, `update`, `upgrade`
- `crack`, `hash`, `md5`, `sha256`, `base64`
- `shell`, `terminal`, `reset`, `help`, `man`
- `whoami`, `id`, `date`, `uptime`, `uname`, `hostname`
- `kill`, `pkill`, `jobs`, `fg`, `bg`
- `sudoers`, `group`, `useradd`, `userdel`...
