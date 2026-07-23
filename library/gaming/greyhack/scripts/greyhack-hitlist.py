#!/usr/bin/env python3
"""
greyhack-hitlist.py — GreyHack DB-driven LAN Hitlist Generator

Phase-4 des Reconnaissance-Patterns: Analysiert die GreyHackDB.db,
identifiziert ungescannte LAN-IPs, scored sie nach Library-Hash-Einzigartigkeit,
Bank/Mail-Status, TipoRed und metaxploit.so-Seltenheit.

Verwendung:
  python3 scripts/greyhack-hitlist.py \
    --db "/pfad/zu/GreyHackDB.db" \
    --output /tmp/hitlist.md \
    --player-ip "211.240.222.194"
"""

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path


def load_info_gen(db):
    """Lade InfoGen.AllLibs (20 Library-Pools, metaxploit.so mit 100 Hashes)."""
    row = db.execute("SELECT AllLibs FROM InfoGen").fetchone()
    if not row:
        return {}
    return json.loads(row[0])


def get_scanned_ips(db):
    """Ermittle bereits gescannte IPs aus Logs (ID-Format 'IP:port')."""
    rows = db.execute("""
        SELECT DISTINCT SUBSTR(ID, 1, INSTR(ID,':')-1)
        FROM Logs WHERE ID LIKE '%.%.%.%:%'
    """).fetchall()
    return {r[0] for r in rows if r[0]}


def get_lan_hosts(db):
    """Alle LAN-Hosts (AccessType=1) mit LibVersions etc."""
    return db.execute("""
        SELECT IpAddress, Essid, WebAddress, TipoRed, GenerationProfile, LibVersions, ID
        FROM Map WHERE AccessType=1
    """).fetchall()


def identify_bank_hosts(db):
    """Bank-Hosts via JSON-Feld BankAccounts.Transactions → origBankAddress."""
    bank_hosts = {}
    for row in db.execute("SELECT Transactions FROM BankAccounts").fetchall():
        try:
            t = json.loads(row[0])
            addr = t.get("origBankAddress", "")
            domain = t.get("origBankDomain", "")
            if addr:
                bank_hosts[addr] = domain
        except (json.JSONDecodeError, KeyError):
            continue
    return bank_hosts


def identify_mail_hosts(db):
    """Mail-Hosts via MailAccounts → Domain → Map.WebAddress LIKE."""
    mail_hosts = {}
    domains = set()
    for row in db.execute("SELECT Mails FROM MailAccounts").fetchall():
        try:
            t = json.loads(row[0])
            addr = t.get("address", "")
            if "@" in addr:
                domains.add(addr.split("@", 1)[1])
        except (json.JSONDecodeError, KeyError):
            continue

    for domain in sorted(domains):
        host = db.execute(
            "SELECT IpAddress FROM Map WHERE WebAddress LIKE ?",
            (f"%{domain}%",)
        ).fetchone()
        if host:
            mail_hosts[host[0]] = domain
    return mail_hosts


def compute_lib_counters(lan_hosts):
    """Zähle Hash-Frequenzen pro Library über alle LAN-Hosts."""
    counters = {}
    for ip, essid, web, tipo, gen, libs, mid in lan_hosts:
        try:
            L = json.loads(libs)["libVersions"]
            for libname, h in L.items():
                if libname not in counters:
                    counters[libname] = Counter()
                counters[libname][h] += 1
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
    return counters


def score_host(host, lib_counters, bank_hosts, mail_hosts, player_ip):
    """
    Scoring nach Formel:
      Score = (unique_lib_count × 3)
            + 15 wenn Bank-Host
            + 10 wenn Mail-Host
            + 5  wenn TipoRed ∈ {10,12,14,15,17}
            + 2  wenn TipoRed ∈ {5..9}
            + 5  wenn metaxploit.so-Hash global einzigartig
            - 999 wenn Player-PC
    """
    ip, essid, web, tipo, gen, libs_json, mid = host
    try:
        L = json.loads(libs_json)["libVersions"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return None

    unique_count = 0
    meta_hash = L.get("metaxploit.so", "")

    for libname, h in L.items():
        counter = lib_counters.get(libname)
        if counter and counter.get(h, 0) == 1:
            unique_count += 1

    meta_count = lib_counters.get("metaxploit.so", Counter()).get(meta_hash, 0)

    score = unique_count * 3
    is_bank = ip in bank_hosts
    is_mail = ip in mail_hosts

    if is_bank:
        score += 15
    if is_mail:
        score += 10

    # TipoRed-Bonus
    if tipo in (10, 12, 14, 15, 17):
        score += 5
    elif 5 <= tipo <= 9:
        score += 2

    # Einzigartiger metaxploit.so-Hash
    if meta_count == 1:
        score += 5

    # Player-Ausschluss
    is_player = (ip == player_ip)
    if is_player:
        score -= 999

    # Difficulty
    if is_player:
        diff = "Trivial (eigener PC)"
    elif is_bank or is_mail:
        diff = "Mittel (Bank/Mail)"
    elif tipo >= 10:
        diff = "Mittel"
    elif tipo <= 1:
        diff = "Schwer (Home-PC)"
    else:
        diff = "Mittel-Leicht"

    return {
        "ip": ip,
        "essid": essid,
        "web": web or "",
        "tipo": tipo,
        "gen": gen,
        "unique": unique_count,
        "score": score,
        "is_bank": is_bank,
        "is_mail": is_mail,
        "meta_hash": meta_hash[:12] if meta_hash else "",
        "meta_count": meta_count,
        "diff": diff,
        "is_player": is_player,
    }


def generate_report(results, db_path, total_lan, scanned_count, player_ip):
    """Generiere Markdown-Report aus Scoring-Ergebnissen."""
    report = []

    # Header
    report.append("# 🎯 HITLIST: Ungescannte LAN-IPs — GreyHack Recon\n")
    report.append(f"**DB:** `{db_path}` | **Hosts total:** {total_lan} | **Bereits gescannt:** {scanned_count} | **Ungescannt:** {len(results)}")
    if player_ip:
        report.append(f" | **Player-IP:** `{player_ip}` (excluded)\n")
    else:
        report.append("\n")

    report.append("## Scoring-Formel\n")
    report.append("```")
    report.append("Score = (unique_lib_count × 3)         # Jede Library, deren Hash nur 1× im LAN")
    report.append("      + 15 wenn Bank-Host               # Aus BankAccounts.Transactions → origBankAddress")
    report.append("      + 10 wenn Mail-Host               # Aus MailAccounts → Domain → Map.WebAddress")
    report.append("      + 5  wenn TipoRed ∈ {10,12,14,15,17}  # Server-Cluster")
    report.append("      + 2  wenn TipoRed ∈ {5..9}            # Mid-Tier")
    report.append("      + 5  wenn metaxploit.so-Hash global einzigartig")
    report.append("      - 999 wenn Player-PC")
    report.append("```\n")

    # Haupt-Tabelle
    report.append("## Rangliste\n")
    report.append("| Rang | IP | ESSID | TipoRed | Uniq | Score | Bank | Mail | MetaHash | Meta@LAN | Diff |\n")
    report.append("|------|----|-------|---------|------|-------|------|------|----------|----------|------|\n")

    for i, r in enumerate(results, 1):
        bank = "✓" if r["is_bank"] else "—"
        mail = "✓" if r["is_mail"] else "—"
        report.append(
            f"| {i} | `{r['ip']}` | {r['essid']} | {r['tipo']} | {r['unique']} | "
            f"**{r['score']}** | {bank} | {mail} | `{r['meta_hash']}` | {r['meta_count']} | {r['diff']} |\n"
        )

    # Top 10 Detail
    report.append("\n## 🏆 TOP 10 — Detail-Profile\n")
    for i, r in enumerate(results[:10], 1):
        report.append(f"\n### #{i} `{r['ip']}` — {r['essid']}\n")
        report.append(f"- **WebAddress:** {r['web']}")
        report.append(f"- **TipoRed:** {r['tipo']}  |  **GenProfile:** {r['gen']}  |  **Unique Libs:** {r['unique']}")
        report.append(f"- **Score:** {r['score']}  |  **Difficulty:** {r['diff']}")
        report.append(f"- **metaxploit.so:** `{r['meta_hash']}` (kommt {r['meta_count']}× in LAN vor)")
        flags = []
        if r["is_bank"]:
            flags.append("💰 BANK")
        if r["is_mail"]:
            flags.append("📧 MAIL")
        if flags:
            report.append(f"- **{' '.join(flags)}**")

    # Exploit-Kandidaten
    exploit_candidates = [r for r in results if r["meta_count"] == 1 and not r["is_player"]]
    report.append(f"\n## 🔬 Exploit-Kandidaten (seltene metaxploit.so-Hashes)\n")
    report.append(f"**{len(exploit_candidates)}** Hosts mit einem global einzigartigen metaxploit.so-Hash — beste Exploit-Ziele.\n")
    report.append("| Rang | IP | ESSID | TipoRed | MetaHash |\n")
    report.append("|------|----|-------|---------|----------|\n")
    for i, r in enumerate(exploit_candidates[:15], 1):
        report.append(f"| {i} | `{r['ip']}` | {r['essid']} | {r['tipo']} | `{r['meta_hash']}` |\n")

    # Verteilung
    tipo_dist = Counter(r["tipo"] for r in results)
    report.append("\n## 📊 Verteilung nach TipoRed\n")
    report.append("| TipoRed | Anzahl | Kategorie |\n|---------|--------|-----------|\n")
    for t in sorted(tipo_dist.keys()):
        cat = "Server-Cluster" if t in (10, 12, 14, 15, 17) else "Home-PC" if t == 1 else "Mid-Tier"
        report.append(f"| {t} | {tipo_dist[t]} | {cat} |\n")

    # Empfehlung
    report.append("\n## 🎯 Empfohlene Angriffsreihenfolge\n")
    for i, r in enumerate(results[:6], 1):
        if r["is_player"]:
            continue
        flags = []
        if r["is_bank"]:
            flags.append("BANK")
        if r["is_mail"]:
            flags.append("MAIL")
        tag = f" ({'+'.join(flags)})" if flags else ""
        report.append(f"{i}. **`{r['ip']}` ({r['essid']})**{tag} — Score {r['score']}, {r['diff']}")

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="GreyHack LAN Hitlist Generator (Phase 4 Recon)")
    parser.add_argument("--db", required=True, help="Pfad zur GreyHackDB.db")
    parser.add_argument("--output", default="/tmp/greyhack-hitlist.md", help="Ausgabedatei (Markdown)")
    parser.add_argument("--player-ip", default="", help="Eigene Public-IP (wird ausgeschlossen)")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"❌ DB nicht gefunden: {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(f"file:{db_path.absolute()}?mode=ro", uri=True)
    db = conn.cursor()

    # Daten sammeln
    info_gen = load_info_gen(db)
    scanned_ips = get_scanned_ips(db)
    lan_hosts = get_lan_hosts(db)
    bank_hosts = identify_bank_hosts(db)
    mail_hosts = identify_mail_hosts(db)

    print(f"  InfoGen.AllLibs: {len(info_gen)} Library-Pools", file=sys.stderr)
    print(f"  LAN-Hosts total: {len(lan_hosts)}", file=sys.stderr)
    print(f"  Bereits gescannt: {len(scanned_ips)}", file=sys.stderr)
    print(f"  Bank-Hosts (DB): {len(bank_hosts)} → {', '.join(bank_hosts.keys())}", file=sys.stderr)
    print(f"  Mail-Hosts (DB): {len(mail_hosts)} → {', '.join(mail_hosts.keys())}", file=sys.stderr)

    # Ungescannte Hosts filtern
    unscanned = [h for h in lan_hosts if h[0] not in scanned_ips]

    # Lib-Counter
    counters = compute_lib_counters(lan_hosts)
    print(f"  Libraries mit Hashes: {len(counters)}", file=sys.stderr)
    print(f"  metaxploit.so-Hashes total (InfoGen): {len(info_gen.get('metaxploit.so', []))}", file=sys.stderr)

    # Scoren
    results = []
    for host in unscanned:
        r = score_host(host, counters, bank_hosts, mail_hosts, args.player_ip)
        if r:
            results.append(r)

    # Sortieren: Score DESC, TipoRed DESC
    results.sort(key=lambda r: (-r["score"], -r["tipo"]))

    print(f"  Ungescannt (gefiltert): {len(results)}", file=sys.stderr)
    print(f"  TOP 1: {results[0]['ip']} ({results[0]['essid']}) — Score {results[0]['score']}", file=sys.stderr)
    print(f"  Exploit-Kandidaten (meta unique): {sum(1 for r in results if r['meta_count'] == 1 and not r['is_player'])}", file=sys.stderr)

    # Report generieren
    report_md = generate_report(
        results, db_path, len(lan_hosts),
        len(scanned_ips), args.player_ip
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_md)

    print(f"\n✅ Report gespeichert: {output_path} ({len(report_md)} Zeichen)", file=sys.stderr)


if __name__ == "__main__":
    main()
