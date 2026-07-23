#!/usr/bin/env python3
"""
GreyHack DB Watchdog — Standalone Cron-Runner (v2.0)

Erzeugt einen Snapshot der live GreyHackDB, vergleicht Tabellen-Hashes
mit dem letzten gespeicherten State und klassifiziert Änderungen.

Verbesserungen gegenüber v1.x:
  - Dynamische Spalten per PRAGMA table_info() — keine Phantom-Diffs
  - Canonical-JSON-Fallback bei BLOB-Noise-Verdacht
  - Klassifikation: clock_only_tick, blob_noise, real_change
  - Robuster gegen shutil.copy2/.backup Re-Serialisierungs-Artefakte

Exit-Codes:
  0 — Keine Änderungen (silent exit)
  1 — Änderungen erkannt (hat output)
  2 — Fehler (DB nicht gefunden, korrupt, etc.)

Aufruf (als Cron):
  python3 /pfad/zu/greyhack-db-watchdog.py

Konfiguration (Konstanten am Dateianfang):
  - SRC_DB: Pfad zur live GreyHackDB.db des Spiels
  - SNAPSHOTS_DIR: Wo Snapshot-Kopien landen
  - STATE_FILE: JSON-State mit Hashes + Counts
  - WATCH_TABLES: Liste der zu überwachenden Tabellen
"""

import sqlite3
import hashlib
import json
import os
import sys
import shutil
from datetime import datetime

# ── Konfiguration ──────────────────────────────────────────────────────────

SRC_DB = "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db"
SNAPSHOTS_DIR = os.path.expanduser("~/.local/share/maxclaw/snapshots")
STATE_FILE = os.path.expanduser("~/.local/share/maxclaw/db-state.json")
RETENTION_MAX = 96  # max Snapshots behalten

# Tabellen, die überwacht werden. Spalten werden dynamisch per PRAGMA table_info()
# ermittelt — harte Spalten-Listen sind anfällig für Phantom-Diffs (siehe
# references/db-hash-delta-forensics.md §0c Anti-Pattern).
WATCH_TABLES = [
    "Computer", "MailAccounts", "BankAccounts", "Passwords",
    "Logs", "Map", "Files", "Players", "WebPages", "InfoGen",
]

# Nur für gezielte Overrides: wenn eine Tabelle nicht alle Spalten braucht.
COLUMN_OVERRIDES = {
    # "InfoGen": ["Clock"],  # Beispiel: nur Clock checken (schneller)
}


# ── Hilfsfunktionen ────────────────────────────────────────────────────────

def get_columns(db_path: str, table: str) -> list[str]:
    """Liefert dynamisch alle Spalten einer Tabelle via PRAGMA table_info."""
    if table in COLUMN_OVERRIDES:
        return COLUMN_OVERRIDES[table]
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as c:
        return [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]


def table_hash(db_path: str, table: str) -> tuple[str, int]:
    """Berechnet SHA256-Präfix (16 Hex) + Row-Count.
    Arbeitet auf Zeilenebene (column-by-column), nicht auf Datei-BLOB —
    daher immun gegen .backup()/copy2-Re-Serialisierungs-Artefakte."""
    cols = get_columns(db_path, table)
    with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as c:
        sel = ", ".join(f'"{col}"' for col in cols)
        rows = c.execute(f"SELECT {sel} FROM {table} ORDER BY rowid").fetchall()
        cnt = c.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    h = hashlib.sha256()
    for r in rows:
        line = "\x00".join(str(x) if x is not None else "" for x in r) + "\n"
        h.update(line.encode("utf-8", "ignore"))
    return h.hexdigest()[:16], cnt


def canonical_json_hash(db_path: str, table: str) -> str | None:
    """Alternativer Hash über json_group_array(json_object(...)).
    Nützlich wenn table_hash() False Positives produziert (BLOB-Noise).
    Liefert SHA256-Präfix oder None bei Fehler."""
    try:
        cols = get_columns(db_path, table)
        pairs = ", ".join(f"'{col}', \"{col}\"" for col in cols)
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as c:
            result = c.execute(
                f"SELECT json_group_array(json_object({pairs}) ORDER BY rowid) FROM {table}"
            ).fetchone()[0]
        h = hashlib.sha256()
        h.update(result.encode("utf-8"))
        return h.hexdigest()[:16]
    except Exception:
        return None


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_state(path: str) -> dict:
    if not os.path.exists(path):
        return {"hashes": {}, "canonical": {}, "counts": {}, "last_snap": None, "last_run": None}
    with open(path, "r") as f:
        return json.load(f)


def save_state(path: str, state: dict) -> None:
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def create_snapshot(src: str, dst_dir: str) -> str | None:
    """Kopiert die live DB in einen timestamped Snapshot.
    Pflegt den sandbox-latest.db Symlink."""
    ensure_dir(dst_dir)
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    dst = os.path.join(dst_dir, f"GreyHackDB-{ts}.db")
    shutil.copy2(src, dst)

    # Symlink aktualisieren
    link = os.path.join(dst_dir, "sandbox-latest.db")
    if os.path.islink(link) or os.path.exists(link):
        os.remove(link)
    os.symlink(os.path.basename(dst), link)

    return dst


def rotate_snapshots(dst_dir: str, max_count: int) -> int:
    """Löscht älteste Snapshots über max_count hinaus.
    Gibt gelöschte Anzahl zurück."""
    files = sorted([
        f for f in os.listdir(dst_dir)
        if f.startswith("GreyHackDB-") and f.endswith(".db")
    ])
    to_delete = len(files) - max_count
    if to_delete <= 0:
        return 0
    for f in files[:to_delete]:
        os.remove(os.path.join(dst_dir, f))
    return to_delete


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> int:
    # 1. Source prüfen
    if not os.path.exists(SRC_DB):
        print(f"FEHLER: GreyHackDB nicht gefunden: {SRC_DB}", file=sys.stderr)
        return 2

    # 2. Snapshot erstellen
    snap_path = create_snapshot(SRC_DB, SNAPSHOTS_DIR)
    if snap_path is None:
        print("FEHLER: Snapshot konnte nicht erstellt werden", file=sys.stderr)
        return 2

    # 3. State laden
    state = load_state(STATE_FILE)

    # 4. Hashes berechnen
    new_hashes: dict[str, str] = {}
    new_canonical: dict[str, str | None] = {}
    new_counts: dict[str, int] = {}
    changes: list[str] = []

    for table in WATCH_TABLES:
        try:
            h, cnt = table_hash(snap_path, table)
        except Exception as e:
            changes.append(f"FEHLER {table}: {e}")
            continue
        new_hashes[table] = h
        new_counts[table] = cnt

        # Canonical-JSON-Hash für BLOB-Noise-Verifikation
        new_canonical[table] = canonical_json_hash(snap_path, table)

        old_h = state.get("hashes", {}).get(table)
        old_c = state.get("counts", {}).get(table)

        if not old_h:
            changes.append(f"{table}: NEU verfolgt (count={cnt})")
            continue

        if old_h == h:
            continue  # Keine Änderung

        # Hash-Diff! Prüfe Counts und canonical-JSON.
        delta = cnt - (old_c or 0)
        if delta == 0:
            # Möglicher BLOB-Noise oder In-Place-Mutation
            old_canon = state.get("canonical", {}).get(table)
            if old_canon and new_canonical.get(table) == old_canon:
                # Canonical-JSON identisch → BLOB-Noise bestätigt
                changes.append(
                    f"{table}: Hash-Change aber canonical-JSON identisch (BLOB-Noise)"
                )
            else:
                changes.append(
                    f"{table}: Hash geändert + Count gleich (In-Place-Mutation)"
                )
        else:
            changes.append(
                f"{table}: Hash geändert, Zeilen {old_c} → {cnt} (Δ{delta:+d})"
            )

    # 5. Klassifikation
    real_diff = [c for c in changes if "BLOB-Noise" not in c and "NEU verfolgt" not in c]
    blob_noise_only = all("BLOB-Noise" in c for c in changes)
    info_gen_only = all(
        c.startswith("InfoGen:") or "NEU verfolgt" in c or "BLOB-Noise" in c
        for c in changes
    )
    new_rows = any("Δ+" in c for c in changes)

    if not real_diff and not new_rows:
        if info_gen_only:
            classification = "clock_only_tick"
        elif blob_noise_only:
            classification = "blob_noise"
        else:
            classification = "watchdog_rebaseline"
    else:
        classification = "real_change"

    # 6. Rotation
    deleted = rotate_snapshots(SNAPSHOTS_DIR, RETENTION_MAX)

    # 7. State persistieren
    state["last_snap"] = os.path.basename(snap_path)
    state["last_run"] = datetime.now().isoformat(timespec="minutes")
    state["row_counts"] = new_counts
    state["hashes"] = new_hashes
    state["canonical"] = new_canonical

    if real_diff or new_rows:
        state["last_alert"] = {
            "tables": [c.split(":")[0] for c in real_diff],
            "summary": "; ".join(changes),
            "classification": classification,
            "ts": datetime.now().isoformat(timespec="seconds"),
        }
    else:
        # Auch bei BLOB-Noise/Clock-Tick den Alert aktualisieren,
        # damit state.json konsistent bleibt.
        state["last_alert"] = {
            "tables": [],
            "summary": (
                f"Clock-only tick — nur InfoGen Clock geändert. Kein Player-Event."
                if classification == "clock_only_tick"
                else (
                    f"BLOB-Noise — Snapshots unterschiedlich, aber canonical-JSON identisch."
                    if classification == "blob_noise"
                    else f"Watchdog-Rebaseline — {len(changes)} Tabellen bootstrapped."
                )
            ),
            "classification": classification,
            "ts": datetime.now().isoformat(timespec="seconds"),
        }

    save_state(STATE_FILE, state)

    # 8. Ausgabe
    if real_diff or new_rows:
        print(f"[ALERT] {classification} — {len(real_diff)} Tabelle(n) geändert:")
        for c in changes:
            print(f"  {c}")
        if deleted:
            print(f"Rotation: {deleted} alte Snapshots gelöscht")
        return 1
    else:
        if changes:
            print(f"[SILENT] {classification} — keine echte Änderung. State updated.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
