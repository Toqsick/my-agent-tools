#!/usr/bin/env python3
"""
greyhack-deploy-tools.py — Inject GreyScript source files into GreyHackDB.

Usage:
  python3 greyhack-deploy-tools.py <name.src> [name2.src ...]

Each file MUST start with "//command: <name>" as its first line.
The script:
  1. Creates a timestamped backup of GreyHackDB.db
  2. INSERTs/UPDATEs each file into the Files table as Config/<name>.src
  3. Walks the FileSystem JSON to find /home/<player>/Config/
  4. Adds/linked each file entry with matching Config/<name>.src ID
  5. Runs PRAGMA integrity_check
  6. Prints verification of each injected tool

Config:
  Update DB_PATH and PLAYER at the top of this file for your setup.
  Or set GREYHACK_DB, GREYHACK_PLAYER env vars.

Requires: Python 3.11+, sqlite3 (stdlib)

Tested: 2026-07-15, GreyHack V0.9.6771-beta, Steam native install
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────

_DEFAULT_DB = (
    "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/"
    "Grey Hack_Data/GreyHackDB.db"
)
_DEFAULT_PLAYER = "gregor"
BACKUP_DIR = None  # None = same dir as DB


# ── Helpers ────────────────────────────────────────────────────────────────


def _resolve_config() -> tuple[Path, str]:
    db_path = Path(os.environ.get("GREYHACK_DB", _DEFAULT_DB))
    player = os.environ.get("GREYHACK_PLAYER", _DEFAULT_PLAYER)
    return db_path, player


def _find_config(fs_node: dict, player: str) -> dict | None:
    """Walk FileSystem JSON to find /home/<player>/Config/ folder."""

    def _walk(node: dict, depth: int = 0) -> dict | None:
        if not isinstance(node, dict) or depth > 20:
            return None
        if node.get("nombre") == "Config":
            return node
        for folder in node.get("folders") or []:
            result = _walk(folder, depth + 1)
            if result is not None:
                return result
        return None

    # First try under /home/<player>
    home = _walk(fs_node, 0)
    if not home:
        return None

    # home is the first "Config" found — but it might be /root/Config.
    # We need /home/<player>/Config. Walk explicitly.
    def _find_home_folder(node: dict, target: str, path: str = "") -> dict | None:
        if not isinstance(node, dict):
            return None
        name = node.get("nombre")
        if path == "/home" and name == target:
            return node
        if name == target and path.startswith("/home/"):
            return node
        for folder in node.get("folders") or []:
            result = _find_home_folder(folder, target, f"{path}/{name if name else ''}")
            if result is not None:
                return result
        return None

    player_folder = _find_home_folder(fs_node, player, "")
    if not player_folder:
        print(f"[WARN] Player folder /home/{player} not found in FileSystem")
        return None

    for folder in player_folder.get("folders") or []:
        if folder.get("nombre") == "Config":
            return folder

    return None


def _ensure_config(player_folder: dict) -> dict:
    """Create Config folder under player home if missing."""
    config = next(
        (f for f in player_folder.get("folders") or [] if f.get("nombre") == "Config"),
        None,
    )
    if config is not None:
        return config
    config = {
        "nombre": "Config",
        "owner": player_folder.get("nombre", "gregor"),
        "group": player_folder.get("nombre", "gregor"),
        "files": [],
        "folders": [],
        "permisos": {"permisos": "drwxr-xr-x"},
    }
    player_folder.setdefault("folders", []).append(config)
    print("[INFO] Created Config folder under player home")
    return config


def _ensure_file_entry(config: dict, name: str, file_id: str, size: int, owner: str) -> None:
    files = config.setdefault("files", [])
    for f in files:
        if f.get("nombre") == f"{name}.src" or f.get("ID") == file_id:
            f["ID"] = file_id
            f["nombre"] = f"{name}.src"
            f["permisos"] = f.get("permisos") or {"permisos": "-rwxr-xr-x"}
            f["owner"] = owner
            f["group"] = owner
            f["isBinario"] = False
            f["allowImport"] = True
            f["typeFile"] = 0
            f["size"] = size
            f["comando"] = ""
            f["saved"] = True
            f["isProtected"] = False
            print(f"[UPDATE] FileSystem entry: {name}")
            return
    files.append(
        {
            "ID": file_id,
            "nombre": f"{name}.src",
            "permisos": {"permisos": "-rwxr-xr-x"},
            "owner": owner,
            "group": owner,
            "isBinario": False,
            "allowImport": True,
            "typeFile": 0,
            "size": size,
            "comando": "",
            "saved": True,
            "isProtected": False,
        }
    )
    print(f"[INSERT] FileSystem entry: {name}")


# ── Main ───────────────────────────────────────────────────────────────────


def main() -> int:
    db_path, player = _resolve_config()
    srcs = [Path(a) for a in sys.argv[1:]]

    if not srcs:
        print("Usage: greyhack-deploy-tools.py <name.src> [name2.src ...]", file=sys.stderr)
        return 2
    if not db_path.exists():
        print(f"[ERROR] DB not found: {db_path}", file=sys.stderr)
        return 2

    errors = 0
    payloads: list[tuple[str, str, int]] = []  # name, content, size

    for spath in srcs:
        if not spath.exists():
            print(f"[ERROR] Source not found: {spath}", file=sys.stderr)
            errors += 1
            continue
        text = spath.read_text(encoding="utf-8-sig")
        # Derive name from first //command: or filename
        if text.startswith("//command:"):
            name = text.split("\n", 1)[0].replace("//command:", "").strip()
        else:
            name = spath.stem
        if not text.startswith(f"//command: {name}"):
            print(f"[WARN] {spath}: first line is '//command: {name}' expected but found:", repr(text.split("\n")[0]))
        payloads.append((name, text, len(text.encode())))
        print(f"[LOAD] {name}: {len(text.encode())} bytes from {spath}")

    if errors:
        return 2

    # Backup
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = Path(BACKUP_DIR) if BACKUP_DIR else db_path.parent
    backup_path = backup_dir / f"GreyHackDB.db.backup-deploy-{stamp}"
    shutil.copy2(db_path, backup_path)
    print(f"[BACKUP] {backup_path}")

    # Connect
    con = sqlite3.connect(str(db_path), timeout=10)
    try:
        con.execute("BEGIN IMMEDIATE")

        # 1. Files table
        for name, content, byte_size in payloads:
            file_id = f"Config/{name}.src"
            row = con.execute("SELECT ID FROM Files WHERE ID=?", (file_id,)).fetchone()
            if row:
                con.execute(
                    "UPDATE Files SET Content=?, refCount=1 WHERE ID=?",
                    (content, file_id),
                )
                print(f"[FILES UPDATE] {file_id}")
            else:
                con.execute(
                    "INSERT INTO Files (ID, Content, refCount) VALUES (?, ?, 1)",
                    (file_id, content),
                )
                print(f"[FILES INSERT] {file_id}")

        # 2. FileSystem JSON
        fs_row = con.execute(
            "SELECT FileSystem FROM Computer WHERE IsPlayer=1"
        ).fetchone()
        if not fs_row:
            raise RuntimeError("No player computer found in DB")
        fs = json.loads(fs_row[0])

        config = _find_config(fs, player)
        if config is None:
            # Fallback: try finding /home/<player> directly
            def _find_player(n, depth=0):
                if not isinstance(n, dict) or depth > 20:
                    return None
                name = n.get("nombre")
                for folder in n.get("folders") or []:
                    if (name == "home" and folder.get("nombre") == player) or folder.get("nombre") == player:
                        return folder
                    result = _find_player(folder, depth + 1)
                    if result:
                        return result
                return None
            player_folder = _find_player(fs)
            if player_folder:
                config = _ensure_config(player_folder)
            else:
                raise RuntimeError(f"Could not find /home/{player}/Config in FileSystem")

        for name, content, byte_size in payloads:
            file_id = f"Config/{name}.src"
            _ensure_file_entry(config, name, file_id, byte_size, player)

        # Compact JSON (matching game's format)
        new_fs = json.dumps(fs, separators=(",", ":"), ensure_ascii=False)
        con.execute(
            "UPDATE Computer SET FileSystem=? WHERE IsPlayer=1",
            (new_fs,),
        )
        con.commit()
        print(f"[COMMIT] FileSystem: {len(new_fs)} bytes")
    except Exception:
        con.rollback()
        print("[ROLLBACK] Error occurred, DB unchanged.", file=sys.stderr)
        raise
    finally:
        con.close()

    # ── Verification ──────────────────────────────────────────────────────
    all_ok = True
    vcon = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        print("\n[VERIFY] Files table:")
        for name, _, _ in payloads:
            fid = f"Config/{name}.src"
            row = vcon.execute(
                "SELECT ID, length(Content) AS L, substr(Content,1,25) AS header, refCount FROM Files WHERE ID=?",
                (fid,),
            ).fetchone()
            if not row:
                print(f"  {fid}: MISSING ✗")
                all_ok = False
                continue
            print(f"  {row[0]}  │ {row[2]}  │ {row[1]} bytes  │ refs={row[3]}")
            if not str(row[2]).startswith("//command:"):
                print(f"         ⚠ header missing //command: marker")
                all_ok = False

        # Re-parse FileSystem from the committed state
        fs_verify = json.loads(
            vcon.execute("SELECT FileSystem FROM Computer WHERE IsPlayer=1").fetchone()[0]
        )
        deployed = set()
        def _collect(n):
            if not isinstance(n, dict):
                return
            if n.get("nombre") == "Config":
                for f in n.get("files") or []:
                    deployed.add(f.get("nombre"))
            for ch in n.get("folders") or []:
                _collect(ch)
        _collect(fs_verify)
        expected = {f"{name}.src" for name, _, _ in payloads}
        fs_ok = expected <= deployed
        missing = expected - deployed
        print(f"\n[VERIFY] FileSystem Config: {'OK ✓' if fs_ok else 'INCOMPLETE ✗'}")
        if missing:
            print(f"  Missing from FS: {missing}")
            all_ok = False

        integ = vcon.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"[VERIFY] integrity_check: {integ}")
        if integ != "ok":
            all_ok = False
    finally:
        vcon.close()

    if all_ok:
        print("\n[DONE] All tools deployed. Restart or reload GreyHack to see them in CodeEditor.")
        return 0
    else:
        print("\n[ERROR] Verification found issues. Backup preserved:", backup_path)
        return 1


if __name__ == "__main__":
    sys.exit(main())
