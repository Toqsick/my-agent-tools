#!/usr/bin/env bash
#
# GreyHack DB Watchdog — Cross-Snapshot History Scan.
#
# Definitiver "echt vs stale" Test (Pitfall #30): scannt die letzten
# N Snapshots und zeigt Row-Counts für alle wichtigen Tabellen. Wenn
# die Counts über alle Snapshots identisch sind, ist jede "Änderung"
# im Watchdog ein State-Drift, KEIN echter Event.
#
# Cron-Safe: nur sqlite3, ls, cat, basename — keine blockierten Patterns.
# Aufruf: bash scripts/greyhack-snapshot-history.sh [N]
#   N = Anzahl Snapshots (default: 8)

set -euo pipefail

SNAP_DIR="$HOME/.local/share/maxclaw/snapshots"
N="${1:-8}"

if [ ! -d "$SNAP_DIR" ]; then
    echo "FATAL: $SNAP_DIR does not exist" >&2
    exit 2
fi

# Hole die letzten N Snapshots, neueste zuerst
SNAPS=$(ls -1t "$SNAP_DIR"/GreyHackDB-*.db 2>/dev/null | head -n "$N" || true)
if [ -z "$SNAPS" ]; then
    echo "FATAL: no snapshots in $SNAP_DIR" >&2
    exit 2
fi

echo "=== Cross-Snapshot History (letzte $N Snapshots) ==="
echo ""

for f in $SNAPS; do
    base=$(basename "$f")
    echo "--- $base ---"
    sqlite3 "$f" <<'SQL' | sed "s/^/  /"
SELECT 'Files      = ' || count(*) FROM Files;
SELECT 'Computer   = ' || count(*) FROM Computer;
SELECT 'Map        = ' || count(*) FROM Map;
SELECT 'Passwords  = ' || count(*) FROM Passwords;
SELECT 'Logs       = ' || count(*) FROM Logs;
SELECT 'Mail       = ' || count(*) FROM MailAccounts;
SELECT 'Bank       = ' || count(*) FROM BankAccounts;
SELECT 'WebPages   = ' || count(*) FROM WebPages;
SELECT 'InfoGen    = ' || count(*) FROM InfoGen;
SELECT 'Players    = ' || count(*) FROM Players;
SQL
done

echo ""
echo "=== Interpretation ==="
echo "Wenn alle Snapshots identische Counts zeigen → KEIN Player-Event."
echo "Wenn ein Snapshot einen Sprung hat → dort ist die Änderung passiert."
echo "Watchdog-Output mit 'echten' Counts = State-Drift (Pitfall #25) oder"
echo "Watchlist-Expansion (Pitfall #33) → reseed via scripts/watchdog-reseed.py"
