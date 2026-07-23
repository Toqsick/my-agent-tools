# Forensische Analyse-Muster (NEU: 2026-07-04)

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