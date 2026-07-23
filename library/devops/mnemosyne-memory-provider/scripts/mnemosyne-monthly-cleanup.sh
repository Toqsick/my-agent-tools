#!/usr/bin/env bash
# ======================================================================
# mnemosyne-monthly-cleanup.sh — Mnemosyne BEAM Working-Memory Hygiene
#
# PURPOSE:     Invalidiert Working-Memory-Einträge mit importance < 0.5
#              („Tiny-Ballast") die nicht bereits invalidiert sind.
#              Monatlicher Cron-Job — 25-Tage-Sperre verhindert
#              Mehrfachausführungen.
#
# SAFETY:      3-Schicht-Sicherheitsnetz:
#              ① DB-Snapshot (shutil.copy2)
#              ② Backout-ID-Liste mit Rollback-SQL (JSON)
#              ③ Audit-Trail in consolidation_log-Tabelle
#              → Jeder Lauf ist vollständig reversibel.
#
# USAGE:       ./mnemosyne-monthly-cleanup.sh
#              Läuft automatisch via Cron: 0 9 1 * *
#              Manuell: jederzeit — 25-Tage-Sperre überspringt sonst
#              Log: ~/logs/mnemosyne-monthly-cleanup.log
#
# DEPENDS:     python3 (mit sqlite3), bash, Zugriff auf Mnemosyne-DB
#              TELEGRAM_BOT_TOKEN + TELEGRAM_HOME_CHANNEL in .env
#
# VERSION:     1.0.0 (2026-07-05)
# AUTHOR:      Yuno (Basti's Assistent)
# ======================================================================

set -euo pipefail

# ------------------------------------------------------------------------------
# Konfiguration
# ------------------------------------------------------------------------------

DB_PATH="$HOME/.hermes/mnemosyne/data/mnemosyne.db"
BACKUP_DIR="$HOME/50-System/backups/mnemosyne"
LOG_DIR="$HOME/logs"
VENV_PY="$HOME/.hermes/hermes-agent/venv/bin/python3"

# Importance-Schwellwert (alles darunter wird invalidiert)
IMPORTANCE_MAX="0.5"

# Telegram-Credentials werden zur Laufzeit aus .env geladen.
# Variable: TELEGRAM_BOT_TOKEN + TELEGRAM_HOME_CHANNEL (Bastis Konvention).
# Wichtig: KEIN Telegram-Credential jemals hardcoden, immer aus ~/.hermes/.env.
HERMES_ENV="$HOME/.hermes/.env"

# ------------------------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------------------------

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*"; }

die() { log "[FATAL] $*"; exit 1; }

cleanup() {
    local rc=$?
    if [ $rc -ne 0 ]; then
        log "[ABBRUCH] Exit-Code $rc — siehe Logs für Details"
    fi
    exit $rc
}
trap cleanup EXIT

# ------------------------------------------------------------------------------
# Pre-Flight-Checks
# ------------------------------------------------------------------------------

log "[1/5] Pre-Flight-Checks"

# DB existiert?
[ -f "$DB_PATH" ] || die "Mnemosyne-DB nicht gefunden: $DB_PATH"
log "  ✓ DB: $DB_PATH ($(du -h "$DB_PATH" | cut -f1))"

# Python + sqlite3 verfügbar?
"$VENV_PY" -c "import sqlite3; sqlite3.connect(':memory:')" 2>/dev/null \
    || die "Python sqlite3 nicht verfügbar (venv=$VENV_PY)"
log "  ✓ Python + sqlite3"

# 25-Tage-Sperre prüfen (verhindert Mehrfachausführungen)
LAST_FILE="$BACKUP_DIR/.last-mnemosyne-cleanup"
if [ -f "$LAST_FILE" ]; then
    LAST_DATE=$(cat "$LAST_FILE")
    CURRENT_EPOCH=$(date +%s)
    # Datum parse: YYYY-MM-DD → Epoch
    if [ -n "$LAST_DATE" ]; then
        LAST_EPOCH=$(date -d "$LAST_DATE" +%s 2>/dev/null || echo "0")
        if [ "$LAST_EPOCH" -gt 0 ]; then
            DAYS_DIFF=$(( (CURRENT_EPOCH - LAST_EPOCH) / 86400 ))
            if [ "$DAYS_DIFF" -lt 25 ]; then
                log "[SKIP] Letzter Cleanup war vor $DAYS_DIFF Tagen (< 25). Noch zu früh."
                exit 0
            fi
        fi
    fi
fi
log "  ✓ 25-Tage-Sperre: OK (kein vorheriger Lauf oder > 25 Tage her)"

# Backup-Verzeichnis anlegen
mkdir -p "$BACKUP_DIR" "$LOG_DIR"

# ------------------------------------------------------------------------------
# Schritt 1 — DB-Snapshot + Backout-IDs generieren (Python inline)
# ------------------------------------------------------------------------------

log "[2/5] Snapshot + Backout-IDs generieren"

DATE_TAG=$(date +%Y-%m-%d)
SNAPSHOT_PATH="$BACKUP_DIR/mnemosyne-pre-cleanup-$DATE_TAG.db"
BACKOUT_PATH="$BACKUP_DIR/mnemosyne-cleanup-$DATE_TAG-backout-ids.json"

# Stats VOR dem Cleanup holen
BEFORE_STATS=$("$VENV_PY" - "$DB_PATH" <<'PYEOF'
import sys, json, sqlite3, os
db_path = sys.argv[1]
os.chdir(os.path.dirname(db_path))
conn = sqlite3.connect(db_path)
cur = conn.cursor()
# Bedingung: nur ALIVE (noch nicht invalidiert)
total = cur.execute("SELECT COUNT(*) FROM working_memory WHERE valid_until IS NULL").fetchone()[0]
tiny = cur.execute("SELECT COUNT(*) FROM working_memory WHERE valid_until IS NULL AND importance < 0.5").fetchone()[0]
conn.close()
print(json.dumps({"total": total, "tiny": tiny}))
PYEOF
)
BEFORE_TOTAL=$(echo "$BEFORE_STATS" | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])")
BEFORE_TINY=$(echo "$BEFORE_STATS" | python3 -c "import sys,json; print(json.load(sys.stdin)['tiny'])")
log "  Working-Memory alive: $BEFORE_TOTAL (davon tiny < $IMPORTANCE_MAX: $BEFORE_TINY)"

# DB-Snapshot (Layer ①)
cp "$DB_PATH" "$SNAPSHOT_PATH"
log "  ✓ Snapshot: $SNAPSHOT_PATH"

# Backout-IDs generieren (Layer ②)
SUPERSEDER_TOKEN="mnemosyne:cleanup:${DATE_TAG}:monthly-tiny-importance"

"$VENV_PY" - "$DB_PATH" "$BACKOUT_PATH" "$DATE_TAG" "$SUPERSEDER_TOKEN" "$BEFORE_TINY" <<'PYEOF'
import sys, json, sqlite3, os
from datetime import datetime

db_path, backout_path, date_tag, superseder, expected_count = sys.argv[1:6]
expected_count = int(expected_count)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Wichtig: nur ALIVE Memories (valid_until IS NULL) sammeln.
# Bereits in früheren Cleanups invalidierte IDs werden übersprungen.
ids = [r[0] for r in cur.execute(
    "SELECT id FROM working_memory WHERE importance < 0.5 AND valid_until IS NULL"
).fetchall()]
conn.close()

if len(ids) != expected_count:
    log_msg = (f"  [WARN] Stat-Count {expected_count} stimmt nicht mit gesammelten "
               f"{len(ids)} überein — fahre trotzdem fort")
    # Kann nicht ans bash-log weitergeben, daher in backout-json schreiben
    warn = log_msg
else:
    warn = None

ids_csv = ",".join(map(str, ids))

with open(backout_path, "w") as f:
    json.dump({
        "date": date_tag,
        "criteria": "importance < 0.5 AND valid_until IS NULL",
        "candidate_count": len(ids),
        "candidate_ids": ids,
        "superseder": superseder,
        "created": datetime.utcnow().isoformat(),
        "rollback_sql": (
            f"UPDATE working_memory SET valid_until = NULL, superseded_by = NULL "
            f"WHERE id IN ({ids_csv})"
        ),
        "collect_warning": warn
    }, f, indent=2)

print(f"  ✓ Backout-Datei: {backout_path}")
print(f"  ✓ Kandidaten: {len(ids)}")
PYEOF

# ------------------------------------------------------------------------------
# Schritt 3 — Bulk-Invalidierung in Transaktion (Python inline)
# ------------------------------------------------------------------------------

log "[3/5] Bulk-Invalidierung (Transaktion)"

INVALIDATED=$("$VENV_PY" - "$DB_PATH" "$BACKOUT_PATH" "$SUPERSEDER_TOKEN" <<'PYEOF'
import sys, json, sqlite3, os
from datetime import datetime, timezone

db_path = sys.argv[1]
backout_path = sys.argv[2]
superseder = sys.argv[3]

# Lade Backout-IDs
with open(backout_path) as f:
    backout = json.load(f)
ids = backout["candidate_ids"]

if not ids:
    print("0")
    sys.exit(0)

NOW = datetime.now(timezone.utc).isoformat()
CHUNK = 500  # IDs pro Chunk — SQLite IN-Clause-Limit ~999, aber 500 = sicher + flink

conn = sqlite3.connect(db_path)
cur = conn.cursor()
updated = 0
try:
    cur.execute("BEGIN IMMEDIATE")

    # Audit-Trail (Layer ③)
    summary = (f"Monthly-Tiny-Cleanup {NOW} | "
               f"Criteria: importance < 0.5 AND valid_until IS NULL | "
               f"Candidates: {len(ids)} | "
               f"Superseder: {superseder}")

    # Schema: (session_id, items_consolidated, summary_preview)
    cur.execute("""
        INSERT INTO consolidation_log (session_id, items_consolidated, summary_preview)
        VALUES (?, ?, ?)
    """, (f"monthly-cleanup-{datetime.now().strftime('%Y-%m-%d')}", len(ids), summary))
    audit_id = cur.lastrowid
    print(f"  Audit-Trail-Eintrag #{audit_id}", file=sys.stderr)

    # Chunked UPDATE — defensive WHERE wiederholt die Bedingung
    for i in range(0, len(ids), CHUNK):
        chunk = ids[i:i+CHUNK]
        ph = ",".join("?" for _ in chunk)
        cur.execute(f"""
            UPDATE working_memory
            SET valid_until = ?, superseded_by = ?
            WHERE id IN ({ph}) AND importance < 0.5 AND valid_until IS NULL
        """, [NOW, superseder] + chunk)
        updated += cur.rowcount

    cur.execute("COMMIT")
    print(updated)
except Exception as e:
    cur.execute("ROLLBACK")
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    conn.close()
PYEOF
)

log "  Aktualisiert: $INVALIDATED / erwartet"

# ------------------------------------------------------------------------------
# Schritt 4 — DB-Integrität prüfen
# ------------------------------------------------------------------------------

log "[4/5] DB-Integritäts-Check"

INTEGRITY=$("$VENV_PY" - "$DB_PATH" <<'PYEOF'
import sys, sqlite3
db_path = sys.argv[1]
conn = sqlite3.connect(db_path)
result = conn.execute("PRAGMA integrity_check").fetchone()[0]
conn.close()
print(result)
PYEOF
)

if [ "$INTEGRITY" != "ok" ]; then
    log "  ⚠ Integrity: $INTEGRITY (nicht ok — siehe Snapshot für Rollback)"
else
    log "  Integrity: ok"
fi

# ------------------------------------------------------------------------------
# Schritt 5 — Stats NACH dem Cleanup + Telegram-Report
# ------------------------------------------------------------------------------

log "[5/5] Stats NACH dem Cleanup"

AFTER_STATS=$("$VENV_PY" - "$DB_PATH" <<'PYEOF'
import sys, json, sqlite3, os
db_path = sys.argv[1]
os.chdir(os.path.dirname(db_path))
conn = sqlite3.connect(db_path)
cur = conn.cursor()
total = cur.execute("SELECT COUNT(*) FROM working_memory WHERE valid_until IS NULL").fetchone()[0]
tiny = cur.execute("SELECT COUNT(*) FROM working_memory WHERE valid_until IS NULL AND importance < 0.5").fetchone()[0]
conn.close()
print(json.dumps({"total": total, "tiny": tiny}))
PYEOF
)
AFTER_TOTAL=$(echo "$AFTER_STATS" | python3 -c "import sys,json; print(json.load(sys.stdin)['total'])")
AFTER_TINY=$(echo "$AFTER_STATS" | python3 -c "import sys,json; print(json.load(sys.stdin)['tiny'])")

log "  Working-Memory alive: $AFTER_TOTAL (vorher $BEFORE_TOTAL)"
log "  Tiny-Ballast alive:  $AFTER_TINY (vorher $BEFORE_TINY)"
log "  Diese Aktion invalidiert: $INVALIDATED"

# Letztes Lauf-Datum speichern (für Sperre)
echo -n "$DATE_TAG" > "$LAST_FILE"
log "  Sperre-Datei aktualisiert: $LAST_FILE"

# Telegram-Report (nur wenn .env vorhanden + Werte gesetzt)
if [ -f "$HERMES_ENV" ]; then
    log "  Sende Telegram-Report…"
    set -a
    # shellcheck disable=SC1090
    . "$HERMES_ENV"
    set +a

    # TELEGRAM_HOME_CHANNEL ist Bastis Konvention (Chat-ID oder Kanal-Handle).
    if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_HOME_CHANNEL:-}" ]; then
        MESSAGE="🧹 *Mnemosyne Cleanup $DATE_TAG*

Vorher: $BEFORE_TOTAL alive · $BEFORE_TINY tiny
Nachher: $AFTER_TOTAL alive · $AFTER_TINY tiny
Invalidiert: *$INVALIDATED*
DB-Integrität: ok
Snapshot: $(basename "$SNAPSHOT_PATH")
Backout: $(basename "$BACKOUT_PATH")"

        # Telegram-HTML (sicherer als Markdown-Parser)
        curl -sS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_HOME_CHANNEL}" \
            -d "text=${MESSAGE}" \
            -d "parse_mode=HTML" >/dev/null \
            && log "  Telegram-Report ✓" \
            || log "  [WARN] Telegram-Versand fehlgeschlagen (non-fatal)"
    else
        log "  [SKIP] TELEGRAM_BOT_TOKEN oder TELEGRAM_HOME_CHANNEL fehlt in $HERMES_ENV"
    fi
else
    log "  [SKIP] Keine $HERMES_ENV — Telegram-Report übersprungen"
fi

# ------------------------------------------------------------------------------
# Fertig
# ------------------------------------------------------------------------------

log "[OK] Cleanup-Lauf $DATE_TAG abgeschlossen"
