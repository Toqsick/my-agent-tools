# GreyHack DB-Driven Reconnaissance Pattern

**Stand:** 2026-07-04, getestet gegen V0.9.6771-beta auf Bastis Setup.

## Konzept

Die GreyHack-DB (`GreyHackDB.db`) persistiert die gesamte Spielwelt. Mit SQLite-Queries + Python-Analyse kannst du aus der DB **Target-Prioritäten ableiten**, bevor du ein Tool im Spiel startest.

## Das Drei-Phasen-Modell

### Phase 1: Breitensuche (Parallel-Subagenten)

Spawn 3-4 parallele Subagenten, jeder tastet eine Domäne ab:

| Agent | Queries | Ziel |
|-------|---------|------|
| **Spieler/Computer** | `Players`, `Computer`, `Map`, `InfoGen` | Wer bin ich? Was hab ich? |
| **Files** | `Files`, `BackupPlayerFiles` | Tools in DB? //command: Marker? |
| **Netzwerk** | `Map`, `WebPages`, `Logs`, `PlayerConns` | IPs? Log-Events? Topologie? |
| **Finanzen/Mission** | `BankAccounts`, `MailAccounts`, `Passwords`, `Coins` | Guthaben? Mails? Missionen? |

### Phase 2: Library-Hash-Analyse (Python)

**Kernidee:** `Map.LibVersions` ist JSON mit 20 Library-Hashes pro IP. Seltene Hashes = andere Lib-Versionen = variable exploit-Chance.

```python
import json, sqlite3
from collections import Counter

db = sqlite3.connect("GreyHackDB.db")
rows = db.execute("""
    SELECT m.IpAddress, m.AccessType, m.Essid, m.WebAddress, m.LibVersions
    FROM Map m
    WHERE m.IpAddress NOT IN (SELECT c.ID FROM Computer c WHERE c.ID = m.IpAddress)
""").fetchall()

# 1) Hash-Frequenzen
lib_hash_counter = Counter()
ip_libs = {}
for r in rows:
    try:
        libs = json.loads(r[4])['libVersions']
        for lib, h in libs.items():
            lib_hash_counter[(lib, h)] += 1
        ip_libs[r[0]] = libs
    except: pass

# 2) Scoring: Durchschnitts-Frequenz + Unique-Count
scored = []
for r in rows:
    libs = ip_libs.get(r[0], {})
    if not libs: continue
    freqs = [lib_hash_counter[(lib, h)] for lib, h in libs.items()]
    unique = sum(1 for f in freqs if f == 1)
    scored.append((ip, sum(freqs)/len(freqs), unique, r))

# 3) Sortieren: meiste unique-Libs zuerst
scored.sort(key=lambda x: (x[2], -x[1]), reverse=True)
```

| Metric | Bedeutung |
|--------|-----------|
| `unique_count` | Wie viele Libs (von 20) hat NUR diese IP? **Höher = exotischer = höheres Exploit-Potenzial** |
| `avg_freq` | Durchschnittliche Häufigkeit pro Lib. **Niedriger = seltenere Libs = höheres Potenzial** |

### Phase 3: Domain-Cross-Reference

BankAccounts/MailAccounts enthalten Domains. Matche gegen `Map.WebAddress`:

```python
bank_domains = set(r[0].split('-')[1] for r in db.execute("SELECT User FROM BankAccounts") if '-' in r[0])
mail_domains = set(r[0].split('@')[1] for r in db.execute("SELECT User FROM MailAccounts") if '@' in r[0])

for r in scored:
    domain = (r[3][3] or "").replace('www.', '')
    tags = (['BANK'] if domain in bank_domains else []) + (['MAIL'] if domain in mail_domains else [])
    if tags: print(f"  {r[0]:<18} -> {r[3][3]:<40} {' '.join(tags)}")
```

**Treffer sind HIGH-VALUE-Targets.**

### Phase 4: Deep-Dive (Parallel-Subagenten)

**Konkrete Query-Rezepte für alle Deep-Dive-Tabellen (BankAccounts, MailAccounts, Computer.ConfigOS, Passwords, Logs, Missions):** `references/db-ip-cross-reference-deep-dive.md`
- BankAccounts: Transaction-JSON parsen → `dinero`, `tx-count`, `origBankAddress`, `isPlayer`
- MailAccounts: Mail-Count + Player-vs-NPC-Detection
- Computer.ConfigOS: Ports/Services/LibVersions via Python-Regex-Bridge
- Passwords: MD5-Hash-Kette Computer.Users → Passwords-Tabelle
- Logs: Angreifer-Profile pro IP (unique attackers, ports, date range)
- Missions: Ziel-IP aus Players.Missions extrahieren
- Unified Scoring Table: 0–5 ⭐ pro IP (kombiniert alle Metriken)
- Edge Cases: Ghost-IPs (kein Computer-Eintrag), Phishing-Bank (IP-Mismatch), Shared-Passwords

| Agent | Ziel |
|-------|------|
| **Target-Deep-Dive** | Mission-target + Log-Hotspot + Public-Router. Logs, Passwords, BankDetails. |
| **Bank/Mail-Cross-Ref** | Alle Bank/Mail-IPs: Guthaben, Mails, Passwords, AccessType. |
| **LAN-Hitlist** | LAN-IPs nach Hash-Einzigartigkeit ranken. TOP 10. |

### Phase 4: Konkrete Scoring-Formel (LAN-Hitlist)

Verwendet in Session 2026-07-04 für 36 ungescannte LAN-Hosts:

```
Score = (unique_lib_count × 3)       # Jede Library, deren Hash nur 1× im LAN vorkommt
      + 15 wenn Bank-Host            # Aus BankAccounts.Transactions → origBankAddress
      + 10 wenn Mail-Host            # Aus MailAccounts → Domain → Map.WebAddress
      + 5  wenn TipoRed ∈ {10,12,14,15,17}  # Server-Cluster
      + 2  wenn TipoRed ∈ {5..9}            # Mid-Tier
      + 5  wenn metaxploit.so-Hash global einzigartig  # Nur 1× im gesamten InfoGen-Pool
      - 999 wenn Player-PC                    # Eigene IP ausschließen
```

**Bank/Mail-Identifikation (JSON-Felder, nicht Tabellen-Spalten!):**

```python
# Bank-Hosts: JSON in BankAccounts.Transactions hat origBankAddress
bank_hosts = Counter()
for row in db.execute("SELECT Transactions FROM BankAccounts"):
    t = json.loads(row[0])
    addr = t.get("origBankAddress", "")
    if addr: bank_hosts[addr] += 1

# Mail-Hosts: MailAccounts.Mails → address → Domain → Map.WebAddress LIKE
for row in db.execute("SELECT Mails FROM MailAccounts"):
    t = json.loads(row[0])
    addr = t.get("address", "")  # z.B. "gregor@okulukuxay.org"
    if "@" in addr:
        domain = addr.split("@", 1)[1]
        host = db.execute("SELECT IpAddress FROM Map WHERE WebAddress LIKE ?",
                          (f"%{domain}%",)).fetchone()
        if host: mail_hosts[host[0]] += 1
```

**metaxploit.so-Hash-Analyse (separate Dimension):**

`InfoGen.AllLibs` enthält 100 metaxploit.so-Hashes. Jeder LAN-Host hat einen davon in seinem LibVersions-JSON. Hashes die nur 1× im LAN vorkommen sind **Exploit-Kandidaten** — kein anderer Host hat dieselbe Version.

```python
meta_counter = Counter()
for ip, libs_json in lan_rows:
    libs = json.loads(libs_json)["libVersions"]
    meta_counter[libs["metaxploit.so"]] += 1
```

Die 38/100 Hashes die nur 1× im LAN vorkommen sind P1-Targets für Metaxploit-Exploitation.

**Difficulty-Heuristik (TipoRed-basiert):**

| TipoRed | Difficulty | Grund |
|---------|-----------|-------|
| ≥ 10 | Mittel (Server-Cluster) | Mehr offene Ports, leichter einzusteigen |
| 5–9 | Mittel-Leicht | Gemischter Host-Typ |
| ≤ 1 | Schwer (Home-PC) | Wenige offene Ports, schwerer zu hacken |
| Player-IP | Trivial | Eigener PC, voller Zugriff |

**Report-Template (Markdown):**

```markdown
## TOP 25 — Hitlist (alle N ungescannten Hosts)

| Rang | IP | ESSID | TipoRed | Uniq | Score | Bank | Mail | MetaHash | Meta@LAN | Schwierigkeit | Begründung |
|------|----|-------|---------|------|-------|------|------|----------|----------|---------------|------------|
| 1 | `163.72.70.125` | Iberkshing_JXCM | 8 | 0 | **27** | ✓ | ✓ | `cd5172aa` | 2 | Mittel (Bank/Mail) | 💰 Bank- UND Mail-Server |

### Detail-Profile für TOP 10:

### #1 `163.72.70.125` — Iberkshing_JXCM
- **WebAddress:** `www.obiyiberox.info`
- **TipoRed:** 8  |  **GenerationProfile:** 0  |  **Unique Libs:** 0
- **Score:** 27  |  **Schwierigkeit:** Mittel (Bank/Mail)
- **metaxploit.so:** `cd5172aa416a` (kommt 2× in LAN vor)
- **Bank:** ✓  |  **Mail:** ✓
- **💰 HOCHWERT-ZIEL:** BANK+MAIL

### Exploit-Kandidaten (seltene metaxploit.so-Hashes):

| Rang | IP | ESSID | TipoRed | MetaHash |
|------|----|-------|---------|----------|
| 1 | `154.19.190.206` | Cebook_VSU | 5 | `b7ab9595` |
```

## Skript: `scripts/greyhack-hitlist.py`

Das Skript implementiert Phase 4 vollständig: SQLite-Queries für Map/Logs/BankAccounts/MailAccounts/InfoGen, Scoring-Formel mit allen Gewichten, Difficulty-Heuristik, Report-Generierung als Markdown. Aufruf:

```bash
python3 scripts/greyhack-hitlist.py \
  --db "/path/to/GreyHackDB.db" \
  --output /tmp/hitlist.md \
  --player-ip "211.240.222.194"
```

## Beispiel (Session 2026-07-04)

**Phase 1:** 56 ungescannte IPs, 247 Files, 4 BankAccounts, 1 Mission (16.174.201.225)
**Phase 2:** 158.14.166.104 (Therwing) unique=1, 47.100.26.111 (Ganne) BANK, 68$ Guthaben
**Phase 3:** 4 Bank-IPs + 5 Mail-IPs identifiziert inkl. gregor@okulukuxay.org (Mail-Server)
**Phase 4 (erweitert):** 36 ungescannte LAN-IPs gescored. #1 = 163.72.70.125 (BANK+MAIL, Score 27). #2 = 154.19.190.206 (MAIL, Score 20). 38 Exploit-Kandidaten (einzigartige metaxploit.so-Hashes). Report: `/home/bratan/hitlist_greyhack_2026-07-04.md`

## Pitfalls

1. **Computer.ID != Map.IpAddress** — IDs haben Port-Suffix. Immer `.split(':')[0]`.
2. **TypeNet-Codes (1-17)** ohne Bedeutungstabelle.
3. **GenerationProfile=0** ist Standard. Abweichung = custom Nodes.
4. **Public-Router (AccessType=0)** = direkt angreifbar, kein Router-Umweg.
