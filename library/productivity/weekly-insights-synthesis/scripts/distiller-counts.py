#!/usr/bin/env python3
"""
distiller-counts.py — Vergleich zweier SQLite-DB-Snapshots nach Tabellen-Zeilenanzahl.

Verwendung:
    python3 distiller-counts.py --db-pre <vorher.db> --db-post <nachher.db>
    python3 distiller-counts.py --db-pre GreyHackDB-20260704-0507.db --db-post GreyHackDB-20260704-0631.db

Ausgabe: Tabelle mit allen Tabellen und ihren Zeilen-Deltas.
         Nur Tabellen mit delta != 0 werden standardmäßig angezeigt (--all zeigt alle).

Anwendung: Distiller-Phase-2 für GreyHack-Weekly-Insights.
           Vergleicht zwei DB-Snapshots um zu sehen, was sich im Spielzustand verändert hat.
"""
import sqlite3
import sys
import argparse


def get_table_counts(db_path):
    """Extrahiert alle Tabellennamen und Zeilenanzahlen aus einer SQLite-DB."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cur.fetchall()]

    counts = {}
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM \"{table}\"")
        counts[table] = cur.fetchone()[0]

    conn.close()
    return counts


def main():
    parser = argparse.ArgumentParser(description="Vergleicht Zeilenanzahlen zwischen zwei DB-Snapshots")
    parser.add_argument("--db-pre", required=True, help="Vorher-DB (z.B. vor Deployment)")
    parser.add_argument("--db-post", required=True, help="Nachher-DB (z.B. nach Deployment)")
    parser.add_argument("--all", action="store_true", help="Auch unveränderte Tabellen anzeigen")
    args = parser.parse_args()

    pre = get_table_counts(args.db_pre)
    post = get_table_counts(args.db_post)

    all_tables = sorted(set(list(pre.keys()) + list(post.keys())))

    print(f"{'Tabelle':<25} {'Vorher':>8} {'Nachher':>8} {'Delta':>8}")
    print("-" * 53)

    total_pre = 0
    total_post = 0
    changed = 0

    for t in all_tables:
        c_pre = pre.get(t, 0)
        c_post = post.get(t, 0)
        delta = c_post - c_pre
        total_pre += c_pre
        total_post += c_post

        if delta == 0 and not args.all:
            continue

        sign = "+" if delta > 0 else ""
        print(f"{t:<25} {c_pre:>8} {c_post:>8} {sign}{delta:>7}")
        changed += 1

    print("-" * 53)
    print(f"{'GESAMT':<25} {total_pre:>8} {total_post:>8} {total_post - total_pre:>+8}")

    if changed == 0 and not args.all:
        print("\nKeine Änderungen in irgendeiner Tabelle — Snapshots sind identisch.")
    elif changed == 0 and args.all:
        print("\nAlle Tabellen unverändert — Snapshots sind identisch.")


if __name__ == "__main__":
    main()
