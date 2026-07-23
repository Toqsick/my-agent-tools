#!/usr/bin/env bash
# greyhack-db-snapshot.sh — Sandbox-Snapshot fuer GreyHack DB
# Productive version: ~/bin/greyhack-db-snapshot.sh
# ==============================================================================
set -euo pipefail

DB_SOURCE="/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db"
BACKUP_DIR="$HOME/backups/greyhack"
SANDBOX_LINK="$BACKUP_DIR/sandbox-latest.db"
MAX_SNAPSHOTS=7
ANOMALY_THRESHOLD_PCT=20
DRY_RUN=false; FORCE=false; VERBOSE=false

usage() { cat <<'USAGE'
Usage: greyhack-db-snapshot.sh [--dry-run|--force|--help]
  --dry-run  Trockentest — nur Analyse, kein Backup
  --force    Immer Report ausgeben (auch ohne Anomalie)
  --help     Hilfe
USAGE
exit 0; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; VERBOSE=true ;;
        --force)   FORCE=true; VERBOSE=true ;;
        --help)    usage ;;
        *)         echo "Unbekannt: $1"; usage ;;
    esac; shift
done

info()   { $VERBOSE && echo -e "$*"; }
error()  { echo -e "$*" >&2; }

# Voraussetzungen
command -v sqlite3 >/dev/null || { error "sqlite3 fehlt"; exit 1; }
[[ -f "$DB_SOURCE" ]] || { error "DB nicht gefunden: $DB_SOURCE"; exit 1; }
mkdir -p "$BACKUP_DIR"

ORIG_SIZE=$(stat --format=%s "$DB_SOURCE")
ORIG_SIZE_MB=$(awk "BEGIN {printf \"%.2f\", $ORIG_SIZE/1048576}")
info "Original-DB: $ORIG_SIZE_MB MB"

# Letzten Snapshot finden
LAST_SNAPSHOT=""
SNAPSHOT_GLOB=("$BACKUP_DIR"/GreyHackDB_*.db)
if [[ -f "${SNAPSHOT_GLOB[0]}" ]]; then
    LAST_SNAPSHOT=$(ls -t "${SNAPSHOT_GLOB[@]}" | head -1 2>/dev/null || true)
fi

LAST_SIZE=0
if [[ -n "$LAST_SNAPSHOT" ]]; then
    LAST_SIZE=$(stat --format=%s "$LAST_SNAPSHOT" 2>/dev/null || echo 0)
    LAST_SIZE_MB=$(awk "BEGIN {printf \"%.2f\", $LAST_SIZE/1048576}")
    info "Letzter: $(basename "$LAST_SNAPSHOT") (${LAST_SIZE_MB} MB)"
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SNAPSHOT_FILE="$BACKUP_DIR/GreyHackDB_${TIMESTAMP}.db"
TEMP_DIR=$(mktemp -d /tmp/greyhack-snapshot.XXXXXX)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Anomalie-Check
ANOMALY=false; ANOMALY_REASONS=()
if [[ $LAST_SIZE -gt 0 ]]; then
    GROWTH=$(( ORIG_SIZE - LAST_SIZE ))
    PCT=$(awk "BEGIN {printf \"%.1f\", ($GROWTH/$LAST_SIZE)*100}" 2>/dev/null || echo "0")
    info "Groessenveraenderung: ${PCT}%"
    if (( $(echo "$PCT > $ANOMALY_THRESHOLD_PCT" | bc -l 2>/dev/null || echo 0) )); then
        ANOMALY=true; ANOMALY_REASONS+=("Groessensprung ${PCT}%")
    fi
fi

if $DRY_RUN; then
    echo "--- DRY-RUN ---"
    echo "Groesse: $ORIG_SIZE_MB MB | Letzter: ${LAST_SIZE_MB:-keiner}"
    if [[ -n "$LAST_SNAPSHOT" ]]; then
        echo "--- Diff ---"
        sqlite3 -readonly "$DB_SOURCE" "
            ATTACH DATABASE '$LAST_SNAPSHOT' AS snap;
            SELECT 'NEU: Computer ' || c.ID FROM Computer c
              LEFT JOIN snap.Computer s ON c.ID = s.ID WHERE s.ID IS NULL;
            SELECT 'NEU: Bank ' || b.User FROM BankAccounts b
              LEFT JOIN snap.BankAccounts s ON b.User = s.User WHERE s.User IS NULL;
            DETACH DATABASE snap;" 2>/dev/null || true
    fi
    echo "Anomalie: $($ANOMALY && echo JA || echo NEIN)"
    exit 0
fi

# Snapshot via .backup (READ-ONLY)
sqlite3 -readonly "$DB_SOURCE" ".backup '$SNAPSHOT_FILE'"
ln -sf "$SNAPSHOT_FILE" "$SANDBOX_LINK"

# Rotation
SNAPSHOTS_COUNT=$(ls -1 "$BACKUP_DIR"/GreyHackDB_*.db 2>/dev/null | wc -l)
if [[ $SNAPSHOTS_COUNT -gt $MAX_SNAPSHOTS ]]; then
    ls -t "$BACKUP_DIR"/GreyHackDB_*.db | tail -n $((SNAPSHOTS_COUNT - MAX_SNAPSHOTS)) | xargs -r rm -f
fi

# Diff
DIFF_REPORT="$TEMP_DIR/diff_report.txt"
: > "$DIFF_REPORT"
if [[ -n "$LAST_SNAPSHOT" ]] && [[ -f "$LAST_SNAPSHOT" ]]; then
    sqlite3 -readonly "$DB_SOURCE" "
        ATTACH DATABASE '$LAST_SNAPSHOT' AS snap;
        SELECT 'NEW_COMPUTER: ' || c.ID FROM Computer c LEFT JOIN snap.Computer s ON c.ID = s.ID WHERE s.ID IS NULL;
        SELECT 'NEW_BANK: ' || b.User FROM BankAccounts b LEFT JOIN snap.BankAccounts s ON b.User = s.User WHERE s.User IS NULL;
        SELECT 'NEW_MAIL: ' || m.User FROM MailAccounts m LEFT JOIN snap.MailAccounts s ON m.User = s.User WHERE s.User IS NULL;
        SELECT 'NEW_PASSWORD: ' || p.ID FROM Passwords p LEFT JOIN snap.Passwords s ON p.ID = s.ID WHERE s.ID IS NULL;
        SELECT 'NEW_MAP_IP: ' || m.IpAddress FROM Map m LEFT JOIN snap.Map s ON m.IpAddress = s.IpAddress WHERE s.IpAddress IS NULL;
        DETACH DATABASE snap;
    " >> "$DIFF_REPORT" 2>/dev/null || true
fi

# Anomalie aus Diff
if [[ -s "$DIFF_REPORT" ]]; then
    grep -q "NEW_COMPUTER.*IsPlayer=1" "$DIFF_REPORT" && { ANOMALY=true; ANOMALY_REASONS+=("Neuer Player!"); }
    grep -q "NEW_BANK" "$DIFF_REPORT" && { ANOMALY=true; ANOMALY_REASONS+=("Neue Banken!"); }
fi

# Groessen-Log
SIZE_LOG="$BACKUP_DIR/size-history.csv"
[[ ! -f "$SIZE_LOG" ]] && echo "timestamp,source_bytes,snapshot_bytes,growth_pct,anomaly" > "$SIZE_LOG"
echo "${TIMESTAMP},${ORIG_SIZE},$(stat --format=%s "$SNAPSHOT_FILE" 2>/dev/null || echo 0),${PCT},${ANOMALY}" >> "$SIZE_LOG"

# Watchdog: nur bei Anomalie/Force Output
if $ANOMALY || $FORCE; then
    echo "=== Snapshot Report ==="
    echo "Snapshot: $(basename "$SNAPSHOT_FILE") | $ORIG_SIZE_MB MB"
    $ANOMALY && echo "ANOMALIE: ${ANOMALY_REASONS[*]}"
    [[ -s "$DIFF_REPORT" ]] && cat "$DIFF_REPORT"
fi

exit $($ANOMALY && echo 1 || echo 0)
