# DB Snapshot & Backup (Sandbox Clone)

Fuer sichere Analysen und Experimente — die GreyHack-DB wird NIE direkt beschrieben.
Alle Operationen arbeiten auf READ-ONLY-Kopien via `sqlite3 -readonly .backup`.

## Sandbox-Konzept

```
GreyHackDB.db (6.9 MB)
    |
    +-- sqlite3 .backup (READ-ONLY)
    |
    +-- Snapshot_20260704_120000.db
    +-- Snapshot_20260704_180000.db
    +-- ...
    +-- sandbox-latest.db -> Snapshot_20260705_060000.db (Symlink)
    |
    +-- Analyse-Tools arbeiten nur auf sandbox-latest.db
```

## Snapshot-Erstellung (sicher)

```bash
DB_SOURCE="/pfad/zu/GreyHackDB.db"
BACKUP_DIR="$HOME/backups/greyhack"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SNAPSHOT="$BACKUP_DIR/GreyHackDB_${TIMESTAMP}.db"
SANDBOX_LINK="$BACKUP_DIR/sandbox-latest.db"

# Atomare, konsistente Kopie — NUR READ-ONLY auf Source
sqlite3 -readonly "$DB_SOURCE" ".backup '$SNAPSHOT'"

# Symlink aktualisieren
ln -sf "$SNAPSHOT" "$SANDBOX_LINK"

# Rotation: letzte 7 behalten
ls -t "$BACKUP_DIR"/GreyHackDB_*.db | tail -n +8 | xargs -r rm -f
```

**Warum .backup und nicht cp oder VACUUM INTO:** .backup erzeugt eine atomare,
konsistente Kopie auch wenn parallel geschrieben wird. Das Spiel merkt nichts
vom Backup. cp kann bei aktivem Write-Cache eine inkonsistente Kopie liefern.

## Cross-DB Diff (ATTACH DATABASE)

Vergleich Original vs. Vorgaenger-Snapshot via LEFT JOIN ueber zwei geoeffnete Datenbanken:

```sql
ATTACH DATABASE '/path/to/previous_snapshot.db' AS snap;

-- Neue Computer (im Original aber nicht im Snapshot)
SELECT 'NEW_COMPUTER: ' || c.ID
FROM Computer c LEFT JOIN snap.Computer s ON c.ID = s.ID
WHERE s.ID IS NULL;

-- Neue BankAccounts
SELECT 'NEW_BANK: ' || b.User
FROM BankAccounts b LEFT JOIN snap.BankAccounts s ON b.User = s.User
WHERE s.User IS NULL;

-- Neue Passwoerter
SELECT 'NEW_PASSWORD: ' || p.ID
FROM Passwords p LEFT JOIN snap.Passwords s ON p.ID = s.ID
WHERE s.ID IS NULL;

-- Neue Map-IPs / MailAccounts / WebPages (gleiches LEFT JOIN-Pattern)

DETACH DATABASE snap;
```

## Anomalieerkennung (Watchdog)

| Ausloeser | Typ | Schwere |
|-----------|-----|---------|
| Grossensprung >20% | Size Anomaly | Mittel |
| Neuer Computer mit IsPlayer=1 | Zweiter Spieler | Hoch |
| Neue BankAccounts | Spieler hat neue Konten | Mittel |
| Neue CTF-Computer | Neue CTF-Events | Niedrig |

## Vollstaendige DB-Analyse (Python, strukturiert)

Das Skript `scripts/greyhack-db-analyze.py` extrahiert alle Zustaende aus einem Snapshot:

```bash
# Zusammenfassung (Terminal)
python3 scripts/greyhack-db-analyze.py sandbox-latest.db --summary

# Vollstaendiges JSON (fuer andere Tools)
python3 scripts/greyhack-db-analyze.py sandbox-latest.db --json --pretty -o analyse.json

# Nur Player-State
python3 scripts/greyhack-db-analyze.py sandbox-latest.db --player-only
```

**Analyse-Bereiche:** player (State, Missions, Cooldowns), computers (18 Geräte),
bank_accounts (Accounts + Transaktionen), mail_accounts (Konten + Mail-Inhalte),
passwords (267 IDs), network_map (56 IPs mit Typ-Verteilung), web_pages (48 Sites),
files (248 Dateien), economy (Coins/Stocks/Wallets), ctfs, info_gen.

**DB-URI:** `file:{path}?mode=ro&immutable=1` (garantiert READ-ONLY).

## Workflow fuer Cron (MaxClaw-Integration)

Siehe `scripts/greyhack-db-snapshot.sh` (vollstaendiges Bash-Skript) und
`references/greyhack-db-snapshot-workflow.md`:

```
Schedule:  0 */6 * * *  (alle 6 Stunden)
Modell:    heartbeat (billig)
Pattern:   Watchdog — silent on success, alert on anomaly
Exit-Code: 0 = ok, 1 = Anomalie (Cron registriert Alarm)

Ablauf:
1. sqlite3 .backup -> ~/backups/greyhack/GreyHackDB_YYYYMMDD_HHMMSS.db
2. Symlink sandbox-latest.db aktualisieren
3. Rotation: nur letzte 7 Snapshots behalten
4. ATTACH-Diff gegen Vorgaenger (Computer/Banken/Mails/Passwoerter)
5. Groessen-Tracking: size-history.csv
6. Nur bei Anomalie Output (sonst absolut still)
```

## Gespeicherte Skripte

| Pfad | Beschreibung |
|------|-------------|
| `scripts/greyhack-db-snapshot.sh` | Bash-Snapshot-Skript (Dry-Run, Force, Rotation, ATTACH-Diff, Anomalie) |
| `scripts/greyhack-db-analyze.py` | Python-CLI: JSON-Extraktion, Summary, Player-State, Bank/Mail/Password Analyse |
| `scripts/greyhack-db-watchdog.py` | **Cron-safe Per-Table Watchdog** — entdeckt Tabellen, hasht + canonicalisiert, klassifiziert (`clock_only_tick`/`row_count_delta`/`real_change`), reseeded `db-state.json`. Läuft in cron mode (kein `execute_code`/heredoc nötig). Aufruf: `python3 scripts/greyhack-db-watchdog.py` |
| `scripts/watchdog-reseed.py` | **NEU 2026-07-06** — State-Reseed-Helper (Pitfall #34). Liest neuesten Snapshot, schreibt `canonical` + `row_counts` + `table_hashes` neu nach `db-state.json`. Verwendung NUR nach Cross-Snapshot-History-Beweis (Pitfall #30) — sonst überschreibt man echte Events. Cron-safe. Aufruf: `python3 scripts/watchdog-reseed.py` |
| `scripts/greyhack-snapshot-history.sh` | **NEU 2026-07-06** — Cross-Snapshot-History-Scanner (Pitfall #30). Ein bash-Aufruf scannt die letzten N Snapshots und zeigt Row-Counts aller wichtigen Tabellen. Beweist State-Drift vs echte Mutation. Cron-safe. Aufruf: `bash scripts/greyhack-snapshot-history.sh [N]` |

**Integration mit MaxClaw:** Das Repo `maxclaw-clone/workflows/greyhack-db-snapshot.md`
beschreibt den Cron-Aufruf fuer Hermes. Der Workflow delegiert an
`~/bin/greyhack-db-snapshot.sh` und `~/bin/greyhack-db-analyze.py`, die
`sandbox-latest.db` lesen — nie das Original.