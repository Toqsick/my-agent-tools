#!/usr/bin/env python3
"""
GreyHack DB Watchdog — Cross-Achsen-Diagnose (Pitfall #38, #40)

Liest db-state.json und vergleicht Live-DB-Hashes über ALLE drei Achsen
(raw, canonical, row_counts), beweist Stabilität via Cross-Snapshot-History
(Pitfall #30), und entscheidet ob der aktuelle Lauf State-Drift oder ein
echtes Event ist.

WICHTIG: Cron-safe. Nutzt KEIN execute_code, KEIN heredoc, KEIN python3 -c.
Aufruf: python3 scripts/greyhack-watchdog-cross-check.py
"""
import sqlite3
import hashlib
import json
import os
import sys
from pathlib import Path

DB = "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db"
SNAPDIR = Path.home() / ".local/share/maxclaw/snapshots"
STATEFILE = Path.home() / ".local/share/maxclaw/db-state.json"

# Production-Script WATCH (9 tables, no InfoGen)
WATCH_PROD = {
    "Computer":     ["ID", "FileSystem", "Hardware", "ConfigOS", "Procs", "Users"],
    "MailAccounts": ["User", "Mails", "password"],
    "BankAccounts": ["User", "Transactions", "Password"],
    "Passwords":    ["ID", "PlainPassword"],
    "Logs":         ["ID", "Log"],
    "Map":          ["IpAddress", "Bssid", "Essid", "WebAddress", "Mission", "LibVersions"],
    "Files":        ["ID", "Content", "refCount"],
    "Players":      ["PlayerID", "ComputerID", "Missions", "TokenTrace"],
    "WebPages":     ["PublicIp", "LocalIp", "Web", "Address"],
}


def raw_hash(path, table, columns):
    """Bytewise SHA256 — was Production-Pipeline schreibt."""
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as c:
        cur = c.cursor()
        sel = ", ".join(columns)
        cur.execute(f"SELECT {sel} FROM {table} ORDER BY rowid")
        rows = cur.fetchall()
    h = hashlib.sha256()
    for r in rows:
        h.update(("\x00".join(str(x) if x is not None else "" for x in r) + "\n").encode("utf-8", "ignore"))
    return h.hexdigest()[:16], len(rows)


def canonical_hash(path, table, columns):
    """JSON-normalisierter SHA256 — was Skill-Pipeline schreibt."""
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as c:
        cur = c.cursor()
        sel = ", ".join(columns)
        cur.execute(f"SELECT {sel} FROM {table} ORDER BY rowid")
        rows = cur.fetchall()
    h = hashlib.sha256()
    for r in rows:
        out = []
        for v in r:
            if v is None:
                out.append("")
            elif isinstance(v, str) and (v.startswith("{") or v.startswith("[")):
                try:
                    out.append(json.dumps(json.loads(v), sort_keys=True, separators=(",", ":")))
                except Exception:
                    out.append(v)
            else:
                out.append(str(v))
        h.update(("\x00".join(out) + "\n").encode("utf-8", "ignore"))
    return h.hexdigest()[:16]


def main():
    if not Path(DB).exists():
        print("DB_MISSING", file=sys.stderr)
        return 2

    # Phase 0: Mtime-Check (Pitfall #36 + #40)
    live_mtime = os.path.getmtime(DB)
    snaps = sorted(SNAPDIR.glob("GreyHackDB-*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not snaps:
        print("NO_SNAPSHOTS")
        return 0
    latest = snaps[0]
    snap_mtime = latest.stat().st_mtime

    if live_mtime < snap_mtime:
        print(f"[MTIME-STABLE] LIVE ({live_mtime:.0f}) < SNAP ({snap_mtime:.0f}) "
              f"→ {snap_mtime - live_mtime:.0f}s older than latest snapshot")
        print(f"[SILENT] 100% no player activity since last snapshot. Skipping hash compute.")
        return 0
    elif live_mtime == snap_mtime:
        print(f"[MTIME-EQUAL] LIVE == SNAP — game saved at exactly snapshot time")
    else:
        print(f"[MTIME-FRESH] LIVE ({live_mtime:.0f}) > SNAP ({snap_mtime:.0f}) "
              f"→ game saved {live_mtime - snap_mtime:.0f}s AFTER last snapshot, hash check needed")

    # Phase 1: Cross-Achsen-Vergleich (Pitfall #38)
    state = json.loads(STATEFILE.read_text()) if STATEFILE.exists() else {}
    print()
    print(f"{'Table':<14} {'live_raw':<18} {'state_raw':<18} {'live_canon':<18} {'state_canon':<18} {'cnt':<5} {'old_cnt':<8}")
    print("-" * 105)

    raw_changed = []
    canon_changed = []
    cnt_changed = []

    for tbl, cols in WATCH_PROD.items():
        live_raw, cnt = raw_hash(DB, tbl, cols)
        live_can = canonical_hash(DB, tbl, cols)
        state_raw = state.get("table_hashes", {}).get(tbl, "")
        state_can = state.get("canonical", {}).get(tbl, "")
        state_cnt = state.get("row_counts", {}).get(tbl, 0)

        r_chg = "!" if live_raw != state_raw else " "
        c_chg = "!" if live_can != state_can else " "
        n_chg = "!" if cnt != state_cnt else " "
        if live_raw != state_raw:
            raw_changed.append(tbl)
        if live_can != state_can:
            canon_changed.append(tbl)
        if cnt != state_cnt:
            cnt_changed.append(tbl)
        print(f"{tbl:<14} {live_raw:<18} {state_raw:<18} {live_can:<18} {state_can:<18} {cnt:<5}{n_chg} {state_cnt:<8}")

    # Phase 2: Cross-Snapshot-History (Pitfall #30)
    print()
    print("=== Cross-Snapshot-History (letzte 10 Snapshots) ===")
    history_snaps = snaps[:10]
    unique_per_table = {tbl: set() for tbl in WATCH_PROD}
    counts_per_table = {tbl: [] for tbl in WATCH_PROD}
    for s in history_snaps:
        for tbl, cols in WATCH_PROD.items():
            unique_per_table[tbl].add(raw_hash(s, tbl, cols)[0])
            counts_per_table[tbl].append(raw_hash(s, tbl, cols)[1])

    for tbl in WATCH_PROD:
        n_unique = len(unique_per_table[tbl])
        n_changes = sum(1 for c in counts_per_table[tbl] if c != counts_per_table[tbl][0])
        label = "STABLE" if n_unique == 1 and n_changes == 0 else f"CHANGED ({n_unique}h, {n_changes} cnt)"
        print(f"  {tbl:<14} {label}")

    # Phase 3: Diagnose (Pitfall #38, #40)
    print()
    print("=== Diagnose ===")
    if not raw_changed and not canon_changed and not cnt_changed:
        print("[CLASSIFICATION: silent] Live == state — no drift, no event.")
        return 0

    # Wenn Achsen A/B über 10 Snapshots stabil sind und Achse-C (counts) auch:
    # Live ist unverändert seit Tagen → alle Deltas sind State-Drift
    drift = []
    for tbl in WATCH_PROD:
        n_unique = len(unique_per_table[tbl])
        if n_unique == 1 and tbl in (raw_changed + canon_changed + cnt_changed):
            drift.append(tbl)
    real_change = [t for t in (raw_changed + canon_changed + cnt_changed) if t not in drift]

    if drift and not real_change:
        print(f"[CLASSIFICATION: state_drift] Tables: {drift}")
        print(f"  Cross-Snapshot-History (10 snapshots) shows ZERO mutations on these tables.")
        print(f"  Next-run: run scripts/watchdog-reseed.py to align state-file with reality.")
        return 0
    elif real_change:
        print(f"[CLASSIFICATION: real_change] Tables: {real_change}")
        print(f"  Cross-Snapshot-History confirms mutation. ALERT may be warranted.")
        if drift:
            print(f"  Also state_drift: {drift}")
        return 1
    else:
        print(f"[CLASSIFICATION: indeterminate] raw={raw_changed} canon={canon_changed} cnt={cnt_changed}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
