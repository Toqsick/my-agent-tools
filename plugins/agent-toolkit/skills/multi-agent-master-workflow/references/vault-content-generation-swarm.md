# Queen + Vault-Content-Generation Swarm (Content-Bienen)

> 2026-07-14 — GreyHack-Vault-Vervollständigung (4 Bienen parallel)
> Ergänzt `multi-agent-master-workflow` um das Dispatch-Pattern für
> **parallele Content-Produktion in Obsidian/Knowledge-Vaults**, wo
> jede Biene eine eigene Note recherchiert + schreibt + quality-gated.

## Abgrenzung zu bestehenden Patterns

| Pattern | Wann | Bienen-Tätigkeit | Quality-Gate |
|---|---|---|---|
| **Parallel Implementation Swarm** | Code-Skripte, Services, Cron-Jobs | Implementieren + E2E-Test | Exit-Code / Port-Response |
| **Cross-Repo GitHub Cleanup** | Issues/PRs schließen | Lesen + Bewerten + Schließen | PR-Merge-Readiness |
| **Cron-Fleet Audit** | Cron-Job-Inventur | Lesen + Klassifizieren | Report-Format |
| **Vault Content Swarm** (dieses) | Vault-Notizen aus Recherche + Spielstand | Web-Search + Vault-Lesen + Schreiben + Self-Tests | Em-Dash ≤1, Boldface=0, Wiki-Links ≥5 |

## Dispatch-Phasen

### Phase 0: Baseline (vor Dispatch, Queen macht das)

1. **Spielstand/Quelldaten live erfassen** (read-only):
   ```bash
   sqlite3 "<db-path>" ".tables"
   sqlite3 "<db-path>" "SELECT COUNT(*) FROM <table>"
   python3 -c "..."  # JSON-Dump nach /tmp/ (NICHT ins Vault-Verzeichnis)
   ```

2. **Vault-Bestand erfassen**:
   ```bash
   find "<vault-path>" -name "*.md" | wc -l
   ls -la "<vault-path>/"
   ```

3. **File-Affinity-Check vor Dispatch** (Anti-Pattern #10):
   Jede Biene bekommt exakt EINEN Ausgabe-Dateipfad — keine Overlaps.
   ```python
   outputs = {
       "bee1": "Sprachreferenz-2026-07-14.md",
       "bee2": "Hacking-Cookbook-2026-07-14.md",
       "bee3": "Lib-Katalog-2026-07-14.md",
       "bee4": "Audit-2026-07-14.md",
   }
   assert len(set(outputs.values())) == len(outputs), "Overlap detected!"
   ```

### Phase 1: Briefing-Struktur (pro Biene)

Jede Content-Biene bekommt ein strukturiertes Briefing mit 4 Pflicht-Blöcken:

```
### SCHRITT 1 — RECHERCHE
1. Web-Suche mit `web_search` (3-5 Queries)
2. `web_extract` auf TOP-Quellen
3. Lokale Vault-Notes lesen (Liste konkreter Pfade)

### SCHRITT 2 — INTEGRATION
- Lies folgende Vault-Notes als Primärquellen: [...]
- Finde Lücken (was fehlt vs. was Web-Doku hat)
- Antipattern: Keine existierenden Notes überschreiben

### SCHRITT 3 — SCHREIBEN
NEUE Datei: `~/Dokumente/Obsidian Vault/09 System-Doku/GreyHack/<Name>-2026-07-14.md`

Pflicht-Sektionen:
- Frontmatter (tags, quelle, status)
- [...]

### SCHRITT 4 — QUALITY-GATE (MUSS VOR SELF-REPORT LAUFEN)
Führe diese Self-Tests aus BEVOR du den Self-Report abgibst:
  - `wc -l <datei>` (Größe notieren)
  - `grep -c '—' <datei>` (Em-Dashes ≤ 1)
  - `grep -oE '\*\*[^*]+\*\*' <datei> | wc -l` (Mid-sentence Boldface = 0)
  - `grep -c '^- \*\*[A-Z]' <datei>` (Inline-Header = 0)
  - Wiki-Links ([[...]]) ≥ 5

Self-Report MUSS enthalten: finale Größe, Em-Dash-Count, Boldface-Count,
Bestätigung dass alle Tests grün sind, Anzahl Wiki-Links, Top-3 Quellen-URLs.
```

### Phase 2: Queen arbeitet parallel

Während Bienen fliegen (typisch 5-15 min pro Content-Biene):

```python
# Typische Queen-Arbeiten:
# 1. MOC-Anker updaten (Gaming - GreyHack.md, etc.)
# 2. Memory-Triple-Write (Mid-Run-Status)
# 3. Wartungs-Log eintragen
# 4. Wiki-Links in existierenden Notes vorbereiten
# 5. Nächste Batch planen (Phase-2-Gate)
```

### Phase 3: Integration (nach Landung)

1. **Jedes Self-Report gegen Vault-Files verifizieren**:
   ```bash
   # Datei existiert?
   ls -la "<vault-path>/<Name>-2026-07-14.md"
   # Größe plausibel?
   wc -l "<vault-path>/<Name>-2026-07-14.md"
   ```

2. **Wiki-Link-Konsistenz prüfen**:
   ```bash
   grep -o '\[\[[^]]*\]\]' <neue-datei> | sort -u
   ```

3. **Memory-Final-Write**: Lessons from bee outputs

### Sub-Sub Extension (validiert 2026-07-14)

Phase 3 kann **parallel während Phase 2** laufen, indem jede Content-Biene
als `role='orchestrator'` dispatcht wird und eine Sub-Sub-Biene zur
unabhängigen Verifikation abspaltet. Das spart einen seriellen QA-Durchlauf.

**Protokoll:** Die Content-Biene schreibt die Note (Phase 3 Schritt 1-2),
die Sub-Biene verifiziert (Phase 2 — parallel). Der Queen bleibt nur der
Memory-Final-Write nach Landung.

**Vorteil:** Sub-Bienen finden Bonus-Erkenntnisse in verwandten Dateien
(50% Fund-Rate im Cross-Model-Test). Die Vault-Integration wird dadurch
ein einziger Dispatch statt zwei serieller Wellen.

**Voraussetzung:** `role='orchestrator'` + `max_spawn_depth >= 2`.
Siehe `orchestration/sub-sub-workflow` für Details.

## Quality-Gate Kriterien (hart)

| Kriterium | Grenzwert | Prüfbefehl |
|---|---|---|
| Em-Dashes | ≤ 1 | `grep -c '—'` |
| Mid-sentence Boldface | 0 | `grep -oE '\*\*[^*]+\*\*' \| wc -l` |
| Inline-Header (Listen) | 0 | `grep -c '^- \*\*[A-Z]'` |
| Wiki-Links ([[...]]) | ≥ 5 | `grep -c '\[\[.*\]\]'` |

## Subagent Self-Test Protocol (eingebettet)

Aus dem Briefing direkt referenzierbar — die exakten Befehle, die der Subagent
selbst laufen lassen MUSS, bevor er seinen Report abgibt:

```
FÜHRE SELBST-TESTS durch BEVOR du deinen Self-Report abgibst:
   grep -c '—' <datei>      → muss ≤1 sein
   grep -oE '\*\*[^*]+\*\*' <datei> | wc -l  → muss 0 sein
   grep -c '^- \*\*[A-Z]' <datei>   → muss 0 sein
   grep -c '\[\[.*\]\]' <datei> → muss ≥5 sein

Erst wenn ALLE Tests grün sind, den Self-Report abgeben.
Wenn ein Test rot ist, fixen und neu testen.
```

## Pitfalls

| Fehler | Fix |
|---|---|
| Biene überschreibt existierende Note | Jede Biene bekommt NEUEN Dateinamen mit Datum |
| Biene verwendet Spielstand-Pfad für JSON-Dump | `/tmp/` für Dumps, NIE ins Vault-Verzeichnis |
| Biene schreibt Klartext-Passwörter in Report | `[REDACTED]` oder Typ-Muster (z.B. `X[0]=8chars`) |
| Biene behauptet grün ohne Tests auszuführen | Self-Test-Kommandos MÜSSEN im Briefing eingebettet sein |
| Wiki-Links zu Notes die es nicht gibt | Nur zu existierenden Notes im Vault verlinken |
| Audit-Biene schreibt in DB | Read-only Verbindung + `.backup` falls nötig, NIE INSERT/UPDATE |

## Beispiel-Vault-Layout (GreyHack)

```
09 System-Doku/GreyHack/
├── GreyScript-Sprachreferenz-2026-07-14.md    (Biene 1)
├── GreyHack-Hacking-Cookbook-2026-07-14.md     (Biene 2)
├── GreyHack-Lib-Katalog-2026-07-14.md          (Biene 3)
├── GreyHack-Audit-2026-07-14.md                (Biene 4)
├── dmz-greyhack-handbook.md                    (vorhanden, Referenz)
├── GreyHack-Manual-*.md                        (vorhanden, In-Game-OCR)
└── greyhack-deep-*-2026-07-04.md               (vorhanden, Baseline)
```

## Siehe auch

- `multi-agent-pitfalls-cheatsheet` — vor jedem Dispatch laden
- `delegation-anti-patterns` — File-Affinity, Summary-Staleness
- `obsidian` — Vault-Read/Write-Operations-Skill
- `system-documentation` — Format-Standard für Docs