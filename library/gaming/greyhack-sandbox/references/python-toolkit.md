# Python Sandbox-Toolkit (NEU: 2026-06-20)

Neben greybel-js gibt es jetzt ein vollständiges Python-Toolkit zum lokalen Arbeiten mit GreyHack:

## Übersicht

```bash
~/projects/greyhack-sandbox/
├── src/
│   ├── greyhack-sandbox.py    # Python-Wrapper für greybel-js + GreyHackDB
│   ├── npc_intel.py           # NPC-Schwachstellen-Scanner (6 Risk-Rules)
│   └── auto_pwn.py            # Auto-Exploit-Generator → GreyScript .src
├── exploits/                  # Fertige GreyScript-Strikes
│   ├── strike1_dee_grettib.src
│   ├── strike2_gabriellia_ingoody.src
│   ├── strike3_bobina_emmer.src
│   └── hardening_audit.src    # System-Hardening (read-only)
├── templates/
│   └── exploit_template.src   # Parametrisierbares Exploit-Template
├── ROADMAP.md                 # Vollständige GreyHack-Progression
├── ARCHITECTURE.md            # Architektur-Report
└── README.md
```

## CLI-Befehle

```bash
# Sandbox-Summary (DB + greybel Status)
python3 src/greyhack-sandbox.py summary

# NPC-Schwachstellen scannen (HIGH severity)
python3 src/npc_intel.py scan --severity HIGH --json

# Verwundbare NPCs finden + Exploit generieren
python3 src/auto_pwn.py scan
python3 src/auto_pwn.py exploit Dee --output dee_pwn.src

# GreyScript-Syntax validieren
~/node_modules/.bin/greybel build exploit.src /tmp/build/
```

## MapLAN-Analyse (Target-Discovery)

Die `Map`-Tabelle (43 Einträge) enthält die komplette Netzwerktopologie:
```sql
-- Position-Cluster finden (gleicher Ort = gleiches LAN!)
SELECT round(posX,0), round(posY,0), COUNT(*), group_concat(IpAddress)
FROM Map GROUP BY 1,2 HAVING COUNT(*) > 1;
```

**Wichtigste Erkenntnis (2026-06-20):** Das Okuhacapos-Gebäude (Position 1261,-199) beherbergt 5 NPCs im SELBEN Netzwerk. Dee Grettib (Int:1, SSH: agle1) ist der Einstiegspunkt für Lateral Movement zu Royal Harrienny (Int:4, ADMIN der Firma).

## Wichtigste Sicherheitsregel

- **DB NUR read-only öffnen:** `sqlite3.connect(f'file:{db}?mode=ro', uri=True)`
- **NIEMALS Klartext-Passwörter loggen** — NPC-Intel zeigt nur Längen + Quellen
- **Backup-Admin vor Passwort-Änderungen** — nie aussperren!

## Forensische Analyse-Muster (NEU: 2026-07-04)

Neben der Schema-Analyse gibt es ein separates Referenzdokument mit **Multi-Table-Query-Patterns** zur Rekonstruktion von Angriffsketten, Mission-Tracking und Ziel-Priorisierung unter N ungescannten IPs:

**`references/greyhack-db-forensic-queries.md`** deckt:
- **TokenTrace-basierte Angriffskette** — `tokenTrace` in Logs.contentLog verbindet ALLE Mission-Aktionen (recon → SSH → bounce → sniffer → transfer). Eine einzelne Token-Trace-ID verknüpft ~20+ Log-Einträge über 8+ IPs zu einer lückenlosen Chronologie.
- **bounceIp als Compromise-Indikator** — Routers deren IP in `bounceIp`-Feldern von Logs auftaucht wurden von jemandem bereits kompromittiert (= wahrscheinlich schwächer gesichert). Erkennung: ein LEFT JOIN zwischen deduplizierten bounceIp-Werten und Map.
- **Computer-Table vs Map-Table Diskrepanz** — ungescannte IPs haben keinen Computer-Eintrag. Die Query `substr(ID, 1, instr(ID, ':') - 1)` extrahiert die reine IP aus dem `Computer.ID`-Format `IP:Zufallszahl`.
- **BankAccount → Netzwerk-Zuordnung** — über `BankAccounts.WebAddress` ↔ `Map.WebAddress` joinen, nicht über `origBankAddress`.
- **10 vollständige SQL-Queries** mit Output-Beispielen, Action-Code-Tabelle (0=Ping, 1=Firewall, 2=Exploit, 3=Sniffer, 4=Port-Scan), und Fallstricken (leere PlayerConns, null LibVersions, mehrdeutiger Action-Code 0).

**Erweiterte Cross-Reference-Patterns — `references/greyhack-db-advanced-patterns.md`** deckt zusätzlich:
- **Essid-Namensmuster** — Brand-Name vs Wireless-Router-SSID (zwei distincte Gruppen, ~31 mit Underscore)
- **Passwort-Klassifikation** — Character-Classes (239 only-letters / 13 only-digits / 15 alphanumeric), trivially-brute-forceable Erkennung, Word-Type-Detection (pseudo-word vs brand vs digit-only)
- **AllLibs Hash-Pool** — 8.3 KB JSON-Struktur (separat von VersionsControl) für Map.LibVersions
- **3-Way Connection Status** — has-webpage / in-logs / untouched aus Map+WebPages+Logs
- **TipoRed Chronologie** — World-Expansion über Generation-Dates erkennen
- **Case-Study-Report** — Vollständige 669-Zeilen-Intel-Analyse in `~/docs/system/greyhack-deep-intel-2026-07-04.md`