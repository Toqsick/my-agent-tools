#!/usr/bin/env python3
"""
GreyHack DB Watchdog — State Reseed Helper.

Liest neuesten Snapshot, schreibt canonical + row_counts + table_hashes neu
nach db-state.json. NUR für Cron-Recovery verwenden, wenn Pitfall #25/30/33
greift (State-Drift, fehlende Tabellen, etc.).

Cron-Safe: kein execute_code, kein heredoc. Aufruf: terminal python3 /path/to/watchdog-reseed.py

Vorher (verpflichtend): Cross-Snapshot-History-Scan (Pitfall #30) ausführen,
um zu beweisen, dass die Deltas NICHT echt sind. Sonst überschreibt man
echte Player-Events mit einer falschen Baseline → false negative.

Beispiel:
    # Stufe 1: BEWEIS (siehe scripts/greyhack-snapshot-history.sh)
    bash scripts/greyhack-snapshot-history.sh
    # Stufe 2: RESEED
    python3 scripts/watchdog-reseed.py
    # Stufe 3: VERIFY
    python3 scripts/greyhack-db-watchdog.py  # → "DB unchanged"

Author: Yuno (2026-07-06)
"""
import sqlite3
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# === CONFIG ===
SNAP_DIR = Path.home() / ".local/share/maxclaw/snapshots"
STATE_PATH = Path.home() / ".local/share/maxclaw/db-state.json"

# Welche Tabellen reseedet werden — sollte exakt WATCH_SCHEMAS im
# Hauptscript entsprechen. Bei Erweiterung von WATCH_SCHEMAS hier
# ebenfalls ergänzen.
WATCH_TABLES = [
    "Computer", "MailAccounts", "Passwords", "BankAccounts", "Logs",
    "Map", "Files", "Players", "WebPages", "InfoGen",
]

# Spalten pro Tabelle (muss mit dem Hauptscript übereinstimmen,
# sonst bekommt man Pitfall #29 Schema-Drift).
COLUMNS_PER_TABLE = {
    "Computer":     ["ID", "FileSystem", "Hardware", "ConfigOS", "Procs", "Users"],
    "MailAccounts": ["User", "Mails", "password"],
    "Passwords":    ["ID", "PlainPassword"],
    "BankAccounts": ["User", "Transactions", "Password"],
    "Logs":         ["ID", "Log"],
    "Map":          ["IpAddress", "Bssid", "Essid", "WebAddress", "Mission", "LibVersions"],
    "Files":        ["ID", "Content", "refCount"],
    "Players":      ["PlayerID", "ComputerID", "Missions", "TokenTrace"],
    "WebPages":     ["PublicIp", "LocalIp", "Web", "Address"],
    "InfoGen":      ["Seed","VersionsControl","Exploits","Guilds","Clock","DeleteVersion","AllLibs","Invoices","GlobalMoney","ZeroDaySystem"],
}


def canonicalize(v):
    """JSON canonical: sort_keys + separators für deterministisches Hashing."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return json.dumps(v, sort_keys=True)
    if isinstance(v, str):
        try:
            return json.dumps(json.loads(v), sort_keys=True, separators=(",", ":"))
        except Exception:
            return v
    return str(v)


def table_data(snap_path, table, columns):
    """Lade (row_count, table_hash, canonical_hash) aus dem Snapshot."""
    with sqlite3.connect(f"file:{snap_path}?mode=ro", uri=True) as c:
        cur = c.cursor()
        sel = ", ".join(columns)
        cur.execute(f"SELECT {sel} FROM {table}")
        rows = cur.fetchall()
    row_count = len(rows)
    # raw hash (drift-sensitive, erkennt Re-Serialisierung)
    h = hashlib.sha256()
    for r in rows:
        h.update(("\x00".join(str(x) if x is not None else "" for x in r) + "\n").encode("utf-8", "ignore"))
    raw_hash = h.hexdigest()[:16]
    # canonical hash (drift-stable)
    ch = hashlib.sha256()
    for r in rows:
        ch.update(("\x00".join(canonicalize(x) or "" for x in r) + "\n").encode("utf-8", "ignore"))
    canon_hash = ch.hexdigest()[:16]
    return row_count, raw_hash, canon_hash


def main():
    snaps = sorted(SNAP_DIR.glob("GreyHackDB-*.db"))
    if not snaps:
        print("FATAL: no snapshots found in", SNAP_DIR, file=sys.stderr)
        return 2
    snap_path = snaps[-1]
    snap_name = snap_path.name

    state = {}
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text())

    counts = {}
    canon = {}
    raw = {}
    for table in WATCH_TABLES:
        cols = COLUMNS_PER_TABLE.get(table)
        if not cols:
            print(f"WARN: no columns for {table}, skipping", file=sys.stderr)
            continue
        try:
            rc, rh, ch = table_data(snap_path, table, cols)
            counts[table] = rc
            raw[table] = rh
            canon[table] = ch
            print(f"  {table:20s} rows={rc:4d} raw={rh} canon={ch}")
        except Exception as e:
            print(f"ERR {table}: {e}", file=sys.stderr)

    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["last_snap"] = snap_name
    state["row_counts"] = counts
    state["canonical"] = canon
    state["table_hashes"] = raw
    state["last_alert"] = {
        "tables": [],
        "summary": "Reseed — state drift recovered, re-aligned with current snapshot baseline. Next watchdog run will be silent if no real change.",
        "classification": "reseed",
        "ts": state["last_run"],
    }
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))

    print(f"\nRESEED OK: {snap_name}")
    print(f"  {len(counts)} tables, state file: {STATE_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
