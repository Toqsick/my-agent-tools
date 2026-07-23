# Pattern 13: Analytical-Dimension Fan-Out

**Source:** Wire-Capture-Analyse 2026-07-15 (17,6 MB / 3091 ss-Snapshots / 104,7 min)
**Proven:** 3 parallele Bienen, 245s Gesamtlaufzeit, 5 Findings identifiziert + Live-Verifikation
**Dispatch Mode:** 🅱️ Standard (3 Worker parallel + Queen-Konsolidierung, ohne Verify-Biene)

## When This Pattern Applies

Use Pattern 13 when:

- **Eine einzelne große Datenquelle** (Log-Datei, Dump, Export, Corpus) soll analysiert werden
- **File-Chunking ist nicht sinnvoll** weil Querbezüge zwischen Chunks nötig wären
- Die Analyse hat **mehrere natürliche Dimensionen** (z.B. Wer, Wohin, Wann)
- Jede Dimension ist **unabhängig beantwortbar** ohne die anderen gesehen zu haben

Nicht anwenden wenn:
- Die Quelle in unabhängige File-Chunks teilbar ist (`split -n N` → Pattern 2 Standard)
- Die Analyse sequentielle Abhängigkeiten hat (Schritt A → Schritt B → Schritt C)
- Eine einzelne Frage ausreicht (Subagent direkt dispatchen, kein Fan-Out)

## Kern-Prinzip: Analyse-Dimension statt File-Chunk

| Split-Strategie | Beispiel | Wann |
|---|---|---|
| **File-Chunk** | `split -n 10 large.log` → jede Biene kriegt 1/10 | Wenn Zeilen/Knoten **unabhängig** pro Chunk auswertbar sind |
| **Analytical-Dimension** | Alle Bienen kriegen das **gleiche gesamte File**, aber jede eine **andere Frage** | Wenn Zeilen/Knoten **durchgehende Metrik-Bildung** brauchen (unique-count, lifecycle) |
| **Kombiniert** | File-Chunk + jeder Chunk auf alle Dimensionen | Nur bei extrem großen Daten (>100 MB), dann aber Sampling nötig |

**Faustregel:** Kann eine Biene mit 1/10 der Daten dieselbe Analyse liefern wie mit 100%? Ja → File-Chunk, Nein → Dimension-Split.

## Die 5 Dimensionen der Netzwerk/Datendiagnose (Leitfaden)

Wenn du eine unbekannte Netzwerk-Capture (ss, tcpdump, netstat) analysierst, verteile diese 5 Dimensionen auf Subagents:

| # | Dimension | Frage | Typischer Output |
|---|---|---|---|
| 1 | **Talker** | Welche Prozesse reden, wie viele unique Connections, Top-10-Prozesse | Tabelle Prozesse × unique Conns × Destinationen |
| 2 | **Destinations** | Welche Remote-IPs/AS/Domains, Top-25, PTR/WHOIS, CDN-Anteil | IP-Ranking mit AS + PTR + Anomalien |
| 3 | **Sequenz** | Zeitverlauf: Bursts, Idle-Phasen, Lifecycle, Heatmap | Lifecycle-Tabelle + Burst-Liste + Idle-Detection |
| 4 | **Payload** | (nur mit tcpdump/pcap) Welche Protokolle, SNI, TLS-Versionen | TLS-Erkennung, DNS-Analyse |
| 5 | **Security** | Unbekannte Prozesse, ungewöhnliche Ports, bekannte Bad-IPs | Alarm-Liste mit IP-Reputation |

Für ss-Wire-Captures sind Dimension 1-3 die Kernmenge (ss enthält keine Payload-Informationen). Für tcpdump-Pcaps kommen 4+5 hinzu.

## Brigfing-Struktur (Template für Dimension-Split)

Jede Biene bekommt **exakt** dieses Briefing:

```markdown
## QUELLE (read-only, NIE ändern)
`/pfad/zur/datei.log` (N MB, N Snapshots)
Diese Datei wird von ALLEN Bienen gleichzeitig gelesen.
DU liest sie nur, DU schreibst sie nie.

## DEINE DIMENSION
<Dimension-Name, z.B. "Talker-Profile">

## FRAGEN
1. <Eine konkrete Frage zur Dimension>
2. <Nächste Frage>
3. <Dritte Frage>

## KRITISCHE REGELN
- Datei ist read-only — kein Schreiben, kein Kopieren ins Workspace
- Nutze Python/awk, KEINE externen Tools ohne Bestätigung
- Output als Markdown, max ~80 Zeilen
- Falls ein Fehler auftritt (Permission, Format kaputt) → MELDEN, nicht improvisieren
```

**Der Satz "read-only, NIE ändern" ist kritisch** — ohne ihn könnte eine Biene die Log-Datei versehentlich modifizieren oder einen großen temporären Export schreiben.

## Consolidation-Methodik (5-Schritte)

Nachdem alle N Bienen zurück sind:

### Schritt 1: Findings-Matrix bauen
Lege eine Tabelle an: Finding | Biene-1 | Biene-2 | Biene-3 | Queen-Urteil

### Schritt 2: Overlap erkennen und deduplizieren
Wenn 2 Bienen dasselbe Finding melden (z.B. `69.46.46.21` taucht bei Talker UND Destinations auf), zitiere es einmal und merke den Cross-Bee-Konsens an.

### Schritt 3: Konflikte auflösen
Wenn Bienen widersprechen (z.B. Biene-1 sagt "Prozess X hat 494 unique Conns", Biene-2 sagt eine abweichende Zahl), **glaube keiner blind**. Lauf eine eigene Quick-Count mit `grep -c` / `wc -l` gegen die Quelldatei. Dokumentiere im Report: "Queen-Quick-Count: N (Biene-1 hatte M, Biene-2 hatte O)".

**Praxis (2026-07-15):** 3 Bienen hatten 0 Widersprüche — die Dimensionen waren disjunkt genug dass keine Überschneidung entstand. Das ist der Idealfall und zeigt gutes Dimension-Splitting.

### Schritt 4: Top-Findings priorisieren + live-verifizieren
Wähle 3-5 Findings, die du **live gegen das System** verifizieren kannst:
```bash
# Für Netzwerk-Findings:
ss -tupn | grep <auffaellige-ip>
# Für Prozess-Findings:
ps aux | grep <verdaechtiger-prozess>
# Für Config-Findings:
ls -la /pfad/zum/vermuteten/artefakt
```

Live-Verifikation ist **der größte Qualitätssprung** gegenüber reiner Log-Analyse: sie trennt "historisch korrekt" von "gerade aktuell".

### Schritt 5: "Bewertungs-Bias" notieren
Jede Biene hat einen **Bias durch ihre Dimension**:
- Talker-Biene: Alamiert jeden Prozess der viele Connections hat (auch wenn normal)
- Destination-Biene: Alamiert jede ungewöhnliche AS (auch wenn seltene aber legitime API)
- Sequenz-Biene: Alamiert jeden Burst (auch wenn durch User-Aktion verursacht)

Notiere im Report: "Bewertungs-Bias dieser Analyse: <Liste>". Gibt dem Leser eine Kalibrierung.

## Output-Struktur (Konsolidierte Notiz)

Erstelle immer **zwei Schichten**:
1. **Konsolidierte Hauptnotiz** (3-7 KB) — Findings, Prioritäten, Live-Verifikation, nächste Schritte
2. **Raw-Subagent-Reports** (behalten, nicht löschen) — als `.raw-<dimension>-<date>.md` im selben Ordner

```markdown
# <Thema der Analyse>

**Quelle:** `/pfad/zum/artefakt` (N MB)
**Bienen:** 3 parallel (Talker, Destinations, Sequenz) in 245s
**Live-Verifikation:** 2026-07-15, `ss -tupn`-Cross-Check

## Top-3 Findings
1. 🔴 <kritischstes Finding>
2. 🟡 <zweitwichtigstes>
3. 🟢 <normale Erkenntnis>

## Konsolidierte Findings
| # | Finding | Bienen | Priorität | Verifikation |
|---|---|---|---|---|
| 1 | ... | 1+2 | 🔴 | ss -tupn bestätigt |

## Empfohlene nächste Schritte
1. <Aktion 1>
2. <Aktion 2>

## Methodische Validität
- N Snapshots, 0 leer, max Gap X s — Datenqualität <gut/mittel/schlecht>
- <Anzahl> von <Gesamt> Rows ohne Owner → <Grund>
- <Eventuelle Limitationen>

## Raw-Artefakte
- `.raw-<dim1>-<date>.md` (N Z.)
- `.raw-<dim2>-<date>.md` (N Z.)
- `.raw-<dim3>-<date>.md` (N Z.)
```

## Worked Example: Wire-Capture 2026-07-15

**Setup:**
- Quelle: `grok-monitor-ss-20260714T214248Z.log` (17,6 MB, 3091 Snapshots über 104,7 Min)
- 3 Bienen parallel dispatched (jede mit `role='leaf'`, ca. 80s Durchschnitt)
- Keine Verify-Biene (Dimensionen waren disjunkt genug — Findings ergänzen sich, widersprechen sich nicht)

**Dimension-Split:**

| Biene | Dimension | Kern-Fragen | Output |
|---|---|---|---|
| Talker | Welche Prozesse → unique Conns → Top-10 | `hermes` (494), `claude-desktop` (372), `brave` (367) | 132 Zeilen |
| Destinations | IPv4/IPv6 Top-25 → PTR → AS → CDN-Anteil | `69.46.46.21` (36%), `2607:6bc0::10` (20%) | 130 Zeilen |
| Sequenz | Lifecycle → Bursts → Idle → Heatmap | `brave` Burst 01:22 (4,29×), `hermes` Burst 01:07 (2,4×) | 119 Zeilen |

**Findings-Matrix (Schritt 1):**

| Finding | Talker | Destinations | Sequenz | Queen |
|---|---|---|---|---|
| `69.46.46.21` dominiert | ✅ hermes → 13.283 Zeilen | ✅ Railway AS400940, 36% IPv4 | ✅ langlebig, keine Bursts | 🔴 Heartbeat, kein Risiko |
| `2607:6bc0::10` = Anthropic | ✅ claude-desktop → 9.431 Zeilen | ✅ AS399358, 20% IPv6 | ✅ kein Burst, konstante Aktivität | 🟢 Bestätigte Session |
| Tor-Snowflake `2a0c:dd40...` | ✅ brave (pid 10710) | ✅ PTR `snowflake-01.torproject.net`, 2.126 obs | ✅ persistent über 1,7h | 🔴 **Klärung nötig** |
| Alibaba-CN `121.41.77.126` | ✅ brave + hermes | ✅ 4 IPs, 6.239 obs, AS37963/45102 | ✅ kein Burst | 🟡 nachverfolgen |
| Brave Burst 01:22 | ✅ 60 neue conns, breitester Fan-Out | — | ✅ **4,29× Median, peak** | 🟢 Brave normal |

**Live-Verifikation (Schritt 4):**
```bash
ss -tupn | grep 2a0c:dd40
# → brave (pid 10710) ESTAB — Tor-Snowflake ist Brave-Feature, kein Schädling

ss -tupn | grep 69.46.46.21
# → hermes (pid 223141) ESTAB — Telegram-Polling, kein Alarm

ss -tupn | grep 47.252.72.253
# → hermes (pid 223141) ESTAB + brave (pid 10710) — Hermes zu Alibaba-US ist ungewöhnlich
```

**Bewertungs-Bias (Schritt 5):**
- Talker-Biene: `hermes` mit 494 unique Conns alarmiert zuerst — aber Telegram-Polling ist sein Design-Pattern. Bias: Übergewichtung von Prozessen mit "ungewöhnlich vielen" Verbindungen.
- Destination-Biene: Alibaba-CN-IPs alarmieren, weil China-Range auf DE-Workstation ungewöhnlich. Bias: Geo-basierte Alarmierung kann legitime CDN-Edge-Nodes treffen.
- Sequenz-Biene: Brave-Burst 4,29× wirkt alarmierend, aber Brave ist der Browser — Bursts sind durch Tab-Öffnen/normalen Traffic erklärt. Bias: Prozess-Charakteristik wird nicht im Kontext gewertet.

**Ergebnis:** 5 Findings → Live-Verifikation von 4/5 → 1 🔴 (Tor-Snowflake klären), 2 🟡 (Alibaba, Railway-Bestätigung), 2 🟢 (Anthropic, Brave-Burst normal). Vault-Note: `Wire-Capture-Audit 2026-07-15.md` (6,4 KB) + 3 Raw-Reports (7,2 / 9,1 / 10,1 KB).

## Pitfalls

| # | Pitfall | Lösung |
|---|---|---|
| 1 | Bienen konkurrieren um Schreibzugriff auf dieselbe Datei | Briefing: "read-only, NIE ändern" + `chmod -w` als Fallback |
| 2 | Überlappende Findings — 2 Bienen melden dasselbe (verschiedene Wörter) | Findings-Matrix bauen + deduplizieren vor Final-Report |
| 3 | Bienen widersprechen sich (unterschiedliche Zählmethoden) | Queen-Quick-Count via `grep -c` + Live-Verifikation |
| 4 | Konsolidierte Notiz enthält nur Findings, keine Limitationen | Schritt 5 (Bewertungs-Bias) ist PFLICHT |
| 5 | Raw-Reports werden nach Konsolidierung gelöscht | Raw-Transcripts als `.raw-*.md` erhalten — Beweissicherung |
| 6 | Findings ohne Priorisierung → User kriegt 20-Punkte-Liste | Top-3 Findings + Bewertung (🔴🟡🟢) + nächste Schritte |

## Verwandte Patterns

- **Pattern 2 (Standard Fan-Out):** Geschwister-Pattern für file-chunk-basierte Parallelisierung
- **Pattern 10 (MERGER Worker):** Wenn die Bienen konkurrierende/komplementäre Edits am **selben Text-Artefakt** liefern (Transkript-Polishing)
- **Pattern 13 (dieses):** Wenn die Bienen disjunkte Analysen am **selben Daten-Artefakt** liefern (Logs, Dumps)
- **Pattern 11 (Rolling-Wave):** Wenn >5 Sub-Anforderungen + Bericht-Plan-Diff nötig sind

**Merker:** Pattern 10 vs Pattern 13 = "alle Bienen bearbeiten denselben Text" vs "alle Bienen lesen dieselben Daten, jede beantwortet eine andere Frage".

## Generalisierung auf andere Domänen

| Domäne | Statt Wire-Capture | Analytische Dimensionen |
|---|---|---|
| Code-Review | Großer Pull-Request-Diff | Security • Performance • Legibility • Test-Coverage |
| Server-Logs | `/var/log/syslog` (100 MB) | Auth-Failures • Error-Rate • Timing-Anomalies • Resource-Consumption |
| DB-Dumps | SQL-Dump | Schema-Health • Data-Quality • Index-Analysis • FK-Integrity |
| Configs | Registry/Konfig-Export | Drift-vs-Baseline • Deprecated-Keys • Permission-Mismatch |

Das Prinzip bleibt gleich: gib allen Bienen denselben Input, aber jede beantwortet eine disjunkte analytische Frage.