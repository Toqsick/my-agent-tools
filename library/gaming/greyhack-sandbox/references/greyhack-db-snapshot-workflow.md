# GreyHack DB Snapshot Workflow — Sandbox Clone

**Stand:** 2026-07-04
**Ursprungssession:** Hermes-Agent erstellte `~/bin/greyhack-db-snapshot.sh`, `~/bin/greyhack-db-analyze.py`, `~/docs/system/greyhack-db-snapshot-2026-07-04.md`

## Vollständige Tabellenstruktur 2026-07-04

Die GreyHackDB.db enthaelt **18 Tabellen** und **0 explizite Foreign Keys**.

| Table | Rows | Beschreibung |
|---|---|---|
| Players | 1 | Spieler-Charakter (PlayerID `e85129e9…`) |
| Computer | 18 | 1x IsPlayer=1, 15x IsRouter=1, 2x Standard |
| Files | 248 | Datei-Content + refCount |
| Map | 56 | IPs, BSSID, AccessType, Missionen |
| WebPages | 48 | Gehostete Webseiten |
| Passwords | 267 | Passwort-Klartext (4-6 Zeichen) |
| Logs | 21 | Log-Eintraege |
| BankAccounts | 4 | User + JSON-Transactions |
| MailAccounts | 7 | User + JSON-Mails |
| InfoGen | 1 | Globale Spielkonfiguration (1.9 MB Exploits) |
| Coins / Stocks / Wallets / CTFs | 0 | Spiel-Oekonomie leer |
| SharedConns / PlayerConns | 0 | Verbindungen leer |
| BackupPlayers / BackupPlayerFiles | 0 | Backups leer |

### Logische Foreign-Key-Beziehungen (nicht in DB definiert)

| Quelle | Ziel | Bedeutung |
|---|---|---|
| Players.ComputerID | Computer.ID | Spieler gehört zu einem PC |
| Players.WalletID | Wallets.WalletID | Spieler-Wallet |
| Coins.OwnerPlayerID | Players.PlayerID | Coin-Besitz |
| CTFs.OwnerPlayerID | Players.PlayerID | CTF-Besitz |
| Passwords.ID | Files.ID | Passwort = File-ID (MD5) |
| Logs.ID | Files.ID | Log = File-ID |
| PlayerConns.RouterID | Computer.ID | Router-Verbindung |
| BackupPlayerFiles.RouterID | Computer.ID | Backup-Router |

## Snapshot-Workflow

1. `sqlite3 -readonly $DB_SOURCE ".backup '$SNAPSHOT'"` — atomare READ-ONLY-Kopie
2. `ln -sf $SNAPSHOT $BACKUP_DIR/sandbox-latest.db` — Symlink
3. Rotation: `ls -t | tail -n +8 | xargs -r rm -f` (letzte 7 behalten)
4. ATTACH-Diff: `ATTACH DATABASE '$LAST' AS snap; LEFT JOIN ...; DETACH`
5. Groessen-Tracking: `size-history.csv`
6. Nur bei Anomalie Alarm (sonst silent)

Siehe `scripts/greyhack-db-snapshot.sh` fuer die Bash-Implementierung und
`scripts/greyhack-db-analyze.py` fuer die Python-basierte Strukturanalyse.
