#!/usr/bin/env python3
"""greyhack-db-analyze.py — Strukturierte DB-Analyse eines GreyHack-Snapshots.

Productive version: ~/bin/greyhack-db-analyze.py

Usage:
  python3 greyhack-db-analyze.py sandbox-latest.db --summary
  python3 greyhack-db-analyze.py sandbox-latest.db --json --pretty -o report.json
  python3 greyhack-db-analyze.py sandbox-latest.db --player-only
"""
import argparse, json, os, sqlite3, sys
from collections import defaultdict
from datetime import datetime


class GreyHackDBAnalyzer:
    def __init__(self, db_path):
        if not os.path.isfile(db_path):
            raise FileNotFoundError(f"DB nicht gefunden: {db_path}")
        uri = f"file:{db_path}?mode=ro&immutable=1"
        self.conn = sqlite3.connect(uri, uri=True)
        self.conn.row_factory = sqlite3.Row
        self.path = db_path

    def close(self):
        self.conn.close()

    def _fetchone(self, sql, params=()):
        row = self.conn.execute(sql, params).fetchone()
        return dict(row) if row else None

    def _fetchall(self, sql, params=()):
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def get_player_state(self):
        p = self._fetchone("SELECT * FROM Players LIMIT 1")
        if not p:
            return {"player_found": False}
        comp = self._fetchone("SELECT * FROM Computer WHERE ID=?", (p["ComputerID"],))
        result = {
            "player_found": True, "player_id": p["PlayerID"],
            "computer_id": p["ComputerID"], "nickname": p["Nickname"] or "(none)",
            "game_over": bool(p["GameOver"]), "last_connection": p["LastConnection"],
            "bank_user": p.get("BankUser") or "(none)",
            "missions_raw_length": len(p.get("Missions") or ""),
            "shop_hardware_length": len(p.get("ShopHardware") or ""),
            "computer": {"hardware": bool(comp.get("Hardware"))} if comp else None,
        }
        missions_raw = p.get("Missions", "")
        if missions_raw and len(missions_raw) > 2:
            try:
                result["missions"] = json.loads(missions_raw)
            except (json.JSONDecodeError, TypeError):
                pass
        return result

    def get_bank_accounts(self):
        return self._fetchall("SELECT User, Password, length(Transactions) as tx_count FROM BankAccounts")

    def get_mail_accounts(self):
        return self._fetchall("SELECT User, length(Mails) as mail_bytes FROM MailAccounts")

    def get_passwords(self, limit=50):
        total = self.conn.execute("SELECT COUNT(*) FROM Passwords").fetchone()[0]
        samples = self._fetchall("SELECT ID, length(PlainPassword) as pwd_len FROM Passwords LIMIT ?", (min(limit, total),))
        return {"total": total, "samples": samples}

    def get_computers(self):
        return self._fetchall("""
            SELECT ID, IsPlayer, IsRouter, IsCTF, IsRented,
                   length(FileSystem) as fs_length FROM Computer
            ORDER BY IsPlayer DESC, IsCTF DESC""")

    def get_network_map(self):
        entries = self._fetchall("SELECT IpAddress, Bssid, TipoRed, AccessType, posX, posY FROM Map")
        type_dist = defaultdict(int)
        for e in entries:
            type_dist[f"tipo_{e['TipoRed']}"] += 1
        return {"total_ips": len(entries), "type_distribution": dict(type_dist), "entries": entries}

    def get_files(self, limit=10):
        total = self.conn.execute("SELECT COUNT(*) FROM Files").fetchone()[0]
        files = self._fetchall("SELECT ID, refCount, length(Content) as c_len FROM Files ORDER BY refCount DESC LIMIT ?", (limit,))
        return {"total": total, "top": files}

    def get_info_gen(self):
        return self._fetchone("SELECT Seed, Clock, length(Exploits) as exploits_length FROM InfoGen") or {}

    def full_analysis(self):
        return {
            "metadata": {"database": os.path.basename(self.path), "time": datetime.now().isoformat(),
                         "size_bytes": os.path.getsize(self.path)},
            "player": self.get_player_state(),
            "computers": self.get_computers(),
            "bank_accounts": self.get_bank_accounts(),
            "mail_accounts": self.get_mail_accounts(),
            "passwords": self.get_passwords(),
            "network_map": self.get_network_map(),
            "files": self.get_files(),
            "info_gen": self.get_info_gen(),
        }

    def generate_summary(self):
        a = self.full_analysis()
        lines = ["=" * 56,
                  f"  DB: {a['metadata']['database']} ({a['metadata']['size_bytes']/1048576:.2f} MB)",
                  "=" * 56]
        p = a["player"]
        if p.get("player_found"):
            lines.append(f"  Player: {p['nickname']} | GameOver: {'JA' if p['game_over'] else 'Nein'}")
            lines.append(f"  Missions: {p['missions_raw_length']} Bytes | Bank: {p['bank_user']}")
        lines.append(f"  Computer: {len(a['computers'])} | Files: {a['files']['total']}")
        accts = a['bank_accounts']
        lines.append(f"  Banken: {len(accts)} Accounts")
        for b in accts:
            lines.append(f"    {b['User']} ({b['tx_count']} TX)")
        lines.append(f"  Mails: {len(a['mail_accounts'])} Accounts")
        lines.append(f"  Passwoerter: {a['passwords']['total']}")
        nm = a['network_map']
        lines.append(f"  Map: {nm['total_ips']} IPs")
        for t, c in sorted(nm.get('type_distribution', {}).items()):
            lines.append(f"    {t}: {c}")
        ig = a.get('info_gen', {})
        if ig:
            lines.append(f"  InfoGen: Seed={ig.get('seed')} | Exploits={ig.get('exploits_length')} Bytes")
        lines.append("=" * 56)
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="GreyHack DB Analyzer")
    parser.add_argument("database", help="Pfad zum DB-Snapshot")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--player-only", action="store_true")
    parser.add_argument("-o", "--output", help="Ausgabedatei")
    args = parser.parse_args()

    if not any([args.json, args.summary, args.player_only]):
        args.summary = True

    try:
        a = GreyHackDBAnalyzer(args.database)
    except (FileNotFoundError, sqlite3.DatabaseError) as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)

    if args.player_only:
        r = a.get_player_state()
        r["_metadata"] = {"database": os.path.basename(args.database)}
    elif args.json:
        r = a.full_analysis()
    else:
        r = a.generate_summary()

    a.close()
    output = json.dumps(r, indent=2, default=str, ensure_ascii=False) if isinstance(r, dict) else r

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
            if not output.endswith("\n"):
                f.write("\n")
        print(f"Geschrieben: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
