#!/usr/bin/env python3
"""
GreyHack DB Watchdog — cron-safe per-table hash + canonical-JSON classifier.

Designed for cron mode (no execute_code, no heredoc, no -c-flag).
Run via: terminal python3 /path/to/greyhack-db-watchdog.py

Phases:
1. Discover tables in LIVE DB
2. For each watched table: compute raw SHA256 hash + canonical-JSON hash + row count
3. Load previous state from db-state.json
4. Classify deltas:
   - clock_only_tick: raw changed, canonical same, count same -> silent
   - row_count_delta: count changed -> alert
   - real_change: canonical changed -> alert
   - no_change: nothing differs -> silent
5. Reseed state.json with current hashes
6. Exit 0 (silent) or 1 (anomaly) for cron pickup

Author: Yuno (2026-07-06)
"""
import sqlite3
import hashlib
import json
import time
import sys
from pathlib import Path

# === CONFIG (edit here or via env-vars if needed) ===
DB_PATH = "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db"
STATE_PATH = Path("/home/bratan/.local/share/maxclaw/db-state.json")

# Tables to skip (high-frequency noise, no player-action impact)
SKIP_TABLES = {"InfoGen"}

# Player-Spur-Tabellen: Wenn ALLE stabil sind (count + canonical), und nur
# Computer/InfoGen canonical-diff haben → npc_background_tick, KEIN Alert.
# (NEU 2026-07-06: aus Cron-Lauf 11:31 UTC, in dem 3 Computer mit
# ConfigOS.networkLan/personas Mutationen 17/18 Player-Spuren stillstanden.)
PLAYER_TRACE_TABLES = {"Files", "Passwords", "Logs", "MailAccounts", "BankAccounts", "Map"}
NPC_OR_PROCS_TABLES = {"Computer"}


def discover_tables(db):
    """List all real (non-internal) tables."""
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as c:
        cur = c.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return [r[0] for r in cur.fetchall()]


def table_hash_and_canonical(db, table):
    """
    Returns (raw_hash, row_count, canonical_hash, canonical_json_str).
    raw_hash: SHA256 of rows as raw string concat (drift-sensitive)
    canonical_hash: SHA256 of canonical-JSON representation (drift-stable)
    """
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as c:
        cur = c.cursor()
        cur.execute(f"SELECT * FROM {table}")
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
    h = hashlib.sha256()
    for r in rows:
        h.update(("\x00".join(str(x) if x is not None else "" for x in r) + "\n").encode("utf-8", "ignore"))
    raw_hash = h.hexdigest()[:16]
    canon_items = [dict(zip(cols, r)) for r in rows]
    canon_str = json.dumps(canon_items, sort_keys=True, default=str, ensure_ascii=False)
    canon_hash = hashlib.sha256(canon_str.encode("utf-8")).hexdigest()[:16]
    return raw_hash, len(rows), canon_hash, canon_str


def classify(prev, cur):
    """Return one of: no_change, clock_only_tick, row_count_delta, real_change."""
    if prev is None:
        return "initial_seed"
    p_raw, p_canon, p_count = prev
    c_raw, c_canon, c_count = cur
    raw_changed = p_raw != c_raw
    canon_changed = p_canon != c_canon
    count_changed = p_count != c_count
    if not raw_changed and not canon_changed and not count_changed:
        return "no_change"
    if raw_changed and not canon_changed and not count_changed:
        return "clock_only_tick"
    if count_changed:
        return "row_count_delta"
    if canon_changed:
        return "real_change"
    return "raw_only_noise"


def main():
    if not Path(DB_PATH).exists():
        print(f"FATAL: DB not found: {DB_PATH}", file=sys.stderr)
        return 2
    if not STATE_PATH.parent.exists():
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    tables = discover_tables(DB_PATH)
    watch = [t for t in tables if t not in SKIP_TABLES]

    current = {}
    for tbl in watch:
        raw, count, canon, _ = table_hash_and_canonical(DB_PATH, tbl)
        current[tbl] = {"raw": raw, "count": count, "canon": canon}
        print(f"  {tbl:20s} rows={count:4d} raw={raw} canon={canon}")

    # Load previous state (or initialize empty)
    if STATE_PATH.exists():
        prev_state = json.loads(STATE_PATH.read_text())
    else:
        prev_state = {"row_counts": {}, "canonical": {}, "table_hashes": {}}

    prev_hashes = prev_state.get("table_hashes", {})
    prev_canon = prev_state.get("canonical", {})
    prev_counts = prev_state.get("row_counts", {})

    # Classify deltas
    deltas = []
    for tbl in watch:
        cur = current[tbl]
        prev_tuple = (prev_hashes.get(tbl), prev_canon.get(tbl), prev_counts.get(tbl, 0))
        cur_tuple = (cur["raw"], cur["canon"], cur["count"])
        cls = classify(prev_tuple, cur_tuple)
        if cls in ("no_change", "initial_seed", "clock_only_tick"):
            continue
        deltas.append({
            "table": tbl,
            "classification": cls,
            "prev": {"raw": prev_tuple[0], "canon": prev_tuple[1], "count": prev_tuple[2]},
            "cur": {"raw": cur_tuple[0], "canon": cur_tuple[1], "count": cur_tuple[2]},
        })

    # NEU 2026-07-06: Player-Spur-Filter (Phase 3)
    # Wenn alle Player-Spur-Tabellen KEIN Delta haben und nur Computer/InfoGen
    # canonical-diff zeigen → npc_background_tick (kein Player-Event, silent).
    changed_tables = {d["table"] for d in deltas}
    real_player_changes = [d for d in deltas if d["table"] in PLAYER_TRACE_TABLES]
    npc_or_procs_changes = [d for d in deltas if d["table"] in NPC_OR_PROCS_TABLES]

    if npc_or_procs_changes and not real_player_changes:
        # Alle Player-Spuren stillstand, nur NPC/Procs-Mutation → demote
        for d in deltas:
            d["classification"] = "npc_background_tick"
        # Mark in output
        print("\n[Player-Spur-Filter] Alle Player-Spuren stillstand — Klassifikation demoted: npc_background_tick")

    # Reseed state.json with current hashes
    new_state = {
        "last_run": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        "row_counts": {tbl: current[tbl]["count"] for tbl in watch},
        "canonical": {tbl: current[tbl]["canon"] for tbl in watch},
        "table_hashes": {tbl: current[tbl]["raw"] for tbl in watch},
        "last_alert": {
            "tables": [d["table"] for d in deltas],
            "summary": "; ".join(f"{d['table']}={d['classification']}" for d in deltas),
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        } if deltas else prev_state.get("last_alert", {}),
    }
    STATE_PATH.write_text(json.dumps(new_state, indent=2))

    if not deltas:
        print("\nNo changes. Silent exit.")
        return 0

    # NEU 2026-07-06: npc_background_tick ist still (kein Alert-Bullet).
    # Nur echte Player-Events (real_change / row_count_delta) lösen Alert aus.
    alert_deltas = [d for d in deltas if d["classification"] != "npc_background_tick"]
    if not alert_deltas:
        print("\n[Silent] Alle Deltas sind npc_background_tick (NPC-Hintergrundsimulation).")
        print("         Kein Player-Event — kein Alert.")
        return 0

    print(f"\n=== {len(alert_deltas)} DELTAS (alert-worthy) ===")
    for d in alert_deltas:
        print(f"  {d['table']}: {d['classification']}")
        print(f"    count: {d['prev']['count']} -> {d['cur']['count']}")
        print(f"    canon: {d['prev']['canon']} -> {d['cur']['canon']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())