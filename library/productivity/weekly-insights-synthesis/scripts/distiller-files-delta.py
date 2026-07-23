#!/usr/bin/env python3
"""
distiller-files-delta.py — Findet neue/gelöschte Dateien zwischen zwei DB-Snapshots.

Verwendung:
    python3 distiller-files-delta.py --db-pre <vorher.db> --db-post <nachher.db>

Extrahiert die Files-Tabelle aus zwei GreyHackDB Snapshots und zeigt:
    - Neue Dateien (nur in post)
    - Gelöschte Dateien (nur in pre)
    - Geänderte Dateien (gleiche ID, unterschiedlicher Inhalt)
    - Count-Zusammenfassung

Anwendung: Distiller-Phase-2 für GreyHack Weekly-Insights.
           Findet exakt welche Dateien im Spiel hinzugekommen/entfernt wurden.
"""
import sqlite3
import argparse
import hashlib


def get_files(db_path):
    """Liest alle Files aus einer GreyHackDB (ID, Content-Preview, Laenge)."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("SELECT ID, Content FROM Files")
        rows = cur.fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()

    result = {}
    for fid, content in rows:
        preview = content[:80].replace("\n", "\\n") if content else "(empty)"
        md5 = hashlib.md5((content or "").encode()).hexdigest()[:12]
        size = len(content) if content else 0
        result[fid] = {"preview": preview, "md5": md5, "size": size, "content_hash": hashlib.sha256((content or "").encode()).hexdigest()[:16]}
    return result


def main():
    parser = argparse.ArgumentParser(description="Vergleicht Files-Tabellen zwischen zwei GreyHackDB Snapshots")
    parser.add_argument("--db-pre", required=True, help="Vorher-Snapshot")
    parser.add_argument("--db-post", required=True, help="Nachher-Snapshot")
    parser.add_argument("--verbose", "-v", action="store_true", help="Alle neuen/gelöschten Dateien auflisten")
    args = parser.parse_args()

    pre = get_files(args.db_pre)
    post = get_files(args.db_post)

    pre_ids = set(pre.keys())
    post_ids = set(post.keys())

    new_ids = post_ids - pre_ids
    deleted_ids = pre_ids - post_ids
    common_ids = pre_ids & post_ids

    modified = []
    for fid in sorted(common_ids):
        if pre[fid]["content_hash"] != post[fid]["content_hash"]:
            modified.append(fid)

    print("=" * 65)
    print(f"  Files-Delta: {args.db_pre} → {args.db_post}")
    print("=" * 65)
    print(f"  Vorher:  {len(pre)}  Dateien")
    print(f"  Nachher: {len(post)}  Dateien")
    print(f"  Delta:   {len(post) - len(pre):+d}  Dateien")
    print(f"  Neu:     {len(new_ids)}  Dateien")
    print(f"  Gelöscht: {len(deleted_ids)}  Dateien")
    print(f"  Geändert: {len(modified)}  Dateien")
    print()

    if new_ids and args.verbose:
        print("─" * 65)
        print(f"  NEUE Dateien ({len(new_ids)}):")
        for fid in sorted(new_ids):
            f = post[fid]
            print(f"  + {fid}")
            print(f"    Size: {f['size']:>6} B  |  MD5: {f['md5']}  |  {f['preview']}")
        print()

    if deleted_ids and args.verbose:
        print("─" * 65)
        print(f"  GELÖSCHTE Dateien ({len(deleted_ids)}):")
        for fid in sorted(deleted_ids):
            f = pre[fid]
            print(f"  - {fid}")
            print(f"    Size: {f['size']:>6} B  |  MD5: {f['md5']}  |  {f['preview']}")
        print()

    if modified and args.verbose:
        print("─" * 65)
        print(f"  GEÄNDERTE Dateien ({len(modified)}):")
        for fid in modified:
            pre_f = pre[fid]
            post_f = post[fid]
            size_delta = post_f["size"] - pre_f["size"]
            sign = "+" if size_delta > 0 else ""
            print(f"  ~ {fid}")
            print(f"    Size: {pre_f['size']:>6} → {post_f['size']:>6} ({sign}{size_delta})")
            print(f"    MD5:  {pre_f['md5']} → {post_f['md5']}")
        print()

    # Check if total IDs differ from total rows (duplicate IDs)
    if len(pre) != len(pre_ids) or len(post) != len(post_ids):
        print("⚠️  WARNUNG: Doppelte IDs in Files-Tabelle gefunden!")
        if len(pre) != len(pre_ids):
            print(f"   Vorher: {len(pre)} rows, {len(pre_ids)} unique IDs")
        if len(post) != len(post_ids):
            print(f"   Nachher: {len(post)} rows, {len(post_ids)} unique IDs")


if __name__ == "__main__":
    main()
