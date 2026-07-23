#!/usr/bin/env python3
"""
DB-Deployment-Template für Multi-Modul GreyHack-Tools.

Schritte:
  1. Backup existierender GreyHackDB.db
  2. Prüfen ob Config/<module>.src bereits existiert (Upsert statt INSERT)
  3. Jedes Modul via INSERT INTO Files (Content) laden
  4. FileSystem-JSON für jedes Modul in Computer.FileSystem.Config[] linken
  5. PRAGMA integrity_check + finaler Count-Report

Usage:
  python3 db-deployment.py --db /path/to/GreyHackDB.db --modules-dir /path/to/modules

Konfiguration (anpassen pro Tool):
  - DB_PATH: Pfad zur GreyHackDB.db (Steam native Linux)
  - MODULES_DIR: Ordner mit *.src Dateien
  - FILES_PREFIX: Pfad-Präfix in der Files-Tabelle (z.B. "Config/yuno_viper")
  - FS_FOLDER: Zielordner im FileSystem-JSON (z.B. "Config")
  - PLAYER_USER: In-Game-Username (z.B. "gregor")
"""

import sqlite3, json, os, shutil, sys
from datetime import datetime
from collections import defaultdict

# ========== KONFIGURATION ==========
DB_PATH = "/mnt/DATA/Programme/Steam/steamapps/common/Grey Hack/Grey Hack_Data/GreyHackDB.db"
MODULES_DIR = "/home/bratan/greyhack-tools/YOUR_TOOL/modules"
FILES_PREFIX = "Config/yuno_viper"       # Prefix in Files.ID
FS_FOLDER = "Config"                      # Zielordner im FileSystem-JSON
PLAYER_USER = "gregor"                    # In-Game-Username
MODULE_NAMES = [                          # Liste der Modul-Namen (ohne .src)
    "yuno_viper_core", "yuno_viper_scan",
    "yuno_viper_post", "yuno_viper_net", "yuno_viper_util",
]
# ====================================

def find_folder(node, target_name):
    """Rekursiv im FileSystem-JSON nach Ordner suchen."""
    if isinstance(node, dict):
        if node.get('nombre') == target_name:
            return node
        for f in node.get('folders', []):
            r = find_folder(f, target_name)
            if r: return r
    if isinstance(node, list):
        for item in node:
            r = find_folder(item, target_name)
            if r: return r
    return None

def main():
    if not os.path.exists(DB_PATH):
        print(f"[!] DB nicht gefunden: {DB_PATH}")
        sys.exit(1)

    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()

    # === 1. BACKUP ===
    bak = f"{DB_PATH}.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    if not os.path.exists(bak):
        shutil.copy2(DB_PATH, bak)
        print(f"[+] Backup: {bak}")
    else:
        print(f"[~] Backup existiert bereits: {bak}")

    # === 2. VORHER-STATUS ===
    existing = cur.execute(
        f"SELECT ID, length(Content) FROM Files WHERE ID LIKE '{FILES_PREFIX}%'"
    ).fetchall()
    print(f"[~] Vorhandene Config-Einträge ({FILES_PREFIX}*): {len(existing)}")

    # === 3. INJECTION (Upsert: UPDATE wenn existiert, INSERT wenn neu) ===
    stats = {"inserted": 0, "skipped": 0, "updated": 0}

    for mod_name in MODULE_NAMES:
        src_path = os.path.join(MODULES_DIR, f"{mod_name}.src")
        if not os.path.exists(src_path):
            print(f"[!] FEHLT: {src_path}")
            continue

        with open(src_path) as f:
            content = f.read()

        file_id = f"{FILES_PREFIX}_{mod_name}.src"
        size = len(content)

        # Prüfen ob bereits vorhanden (via Content-Marker, nicht ID)
        existing_row = cur.execute(
            "SELECT ID FROM Files WHERE ID = ?", (file_id,)
        ).fetchone()

        if existing_row:
            cur.execute(
                "UPDATE Files SET Content = ? WHERE ID = ?",
                (content, existing_row[0])
            )
            print(f"[~] Updated: {file_id} ({size} bytes)")
            stats["updated"] += 1
        else:
            cur.execute(
                "INSERT INTO Files (ID, Content, refCount) VALUES (?, ?, 1)",
                (file_id, content)
            )
            print(f"[+] Injected: {file_id} ({size} bytes)")
            stats["inserted"] += 1

    db.commit()

    # === 4. FILESYSTEM-JSON VERKNÜPFUNG ===
    fs_row = cur.execute(
        "SELECT FileSystem FROM Computer WHERE IsPlayer = 1"
    ).fetchone()

    if not fs_row:
        print("[!] Kein Player-Computer gefunden!")
    else:
        fs = json.loads(fs_row[0])
        config = find_folder(fs, FS_FOLDER)

        if config is None:
            print(f"[!] Ordner '{FS_FOLDER}' im FileSystem nicht gefunden!")
        else:
            existing_names = [f.get('nombre', '') for f in config.get('files', [])]
            linked = 0

            for mod_name in MODULE_NAMES:
                filename = f"{mod_name}.src"
                if filename in existing_names:
                    print(f"[~] Bereits im FileSystem: {FS_FOLDER}/{filename}")
                    stats["skipped"] += 1
                    continue

                new_file = {
                    "ID": f"{FILES_PREFIX}_{mod_name}.src",
                    "precio": 0,
                    "isBinario": False,
                    "allowImport": True,
                    "isEditedOtherPlayer": False,
                    "origOwnerID": "e85129e9ae28753542b97bf10378c645",
                    "saved": True,
                    "desc": None,
                    "helperImport": None,
                    "passEncrypt": "",
                    "nombre": filename,
                    "permisos": {"permisos": "-rwxr-xr-x"},
                    "owner": PLAYER_USER,
                    "group": PLAYER_USER,
                    "comando": "",               # MUSS leer sein!
                    "symlink": "",
                    "size": 0,
                    "process": "",
                    "serverPath": "",
                    "isProtected": False,
                    "missionID": "",
                    "typeFile": 0,
                    "isDefaultContent": False
                }
                config['files'].append(new_file)
                linked += 1
                print(f"[+] FileSystem-Link: {FS_FOLDER}/{filename}")

            updated_json = json.dumps(fs, separators=(',', ':'))
            cur.execute(
                "UPDATE Computer SET FileSystem = ? WHERE IsPlayer = 1",
                (updated_json,)
            )
            db.commit()
            print(f"[+] FileSystem updated ({linked} neue Links)")

    # === 5. VERIFY ===
    integrity = cur.execute("PRAGMA integrity_check").fetchone()[0]
    print(f"\n[+] PRAGMA integrity_check: {integrity}")

    total = cur.execute(
        f"SELECT COUNT(*) FROM Files WHERE ID LIKE '{FILES_PREFIX}%'"
    ).fetchone()[0]
    print(f"[+] {FILES_PREFIX}* Einträge in DB: {total}")

    print(f"\n=== Zusammenfassung ===")
    print(f"  Neu injiziert: {stats['inserted']}")
    print(f"  Aktualisiert:  {stats['updated']}")
    print(f"  Übersprungen:  {stats['skipped']}")
    print(f"  DB-Integrität: {integrity}")

    db.close()

if __name__ == "__main__":
    main()
