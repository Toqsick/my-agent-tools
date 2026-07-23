---
name: queen-bee-advanced
title: "Queen-Bee — Advanced Patterns (Audit-Biene, Drift-Marker, Baseline)"
description: "Use when running advanced queen-bee patterns: audit-biene, drift-marker detection, queen pre-execute for audit cross-verification, queen baseline, orthogonal scout, hypothesis-falsification, skip-decision, nested delegation. NOT for basic dispatch (use queen-bee-dispatch-patterns)."
category: queen-bee-schwarm-dispatch
version: '1.0'
created: '2026-07-23'
author: Yuno (split from queen-bee-schwarm-dispatch)
lane: koenigin
agent: universal
trigger_keywords: ['audit-biene', 'drift-marker', 'baseline', 'orthogonal-scout', 'hypothesis', 'falsification', 'skip-decision', 'nested-delegation', 'handoff', 'sycophancy']
keywords: ['audit-biene', 'drift', 'baseline', 'orthogonal-scout', 'handoff', 'queen-bee', 'advanced']
related_skills: ['queen-bee-dispatch-patterns', 'queen-bee-queen-verify']
last_curated: '2026-07-23'
curated_by: 'Yuno (split from queen-bee-schwarm-dispatch 2026-07-23)'

license: MIT
---

# Queen-Bee — Advanced Patterns (Audit-Biene, Drift-Marker, Baseline)

_Extracted from queen-bee-schwarm-dispatch on 2026-07-23._

## Drift-Marker Pattern (NEU 2026-07-14 — validiert an greyhack-deep-systems)

Wenn eine Audit-Biene Drift zwischen Live-DB und Vault-Notes findet:
1. **Sofort Stale-Marker setzen**, nicht warten bis alle Bienen gelandet sind
2. Stale-Marker = YAML-Frontmatter updaten:
   ```
   status: stale-empfehlung
   freshness: 2026-07-04
   verified_2026-07-14: ja (siehe GreyHack-Audit-2026-07-14 — drift erkannt: +9 Files, +15 Pwds)
   ```
3. Wiki-Backlink in der alten Note auf die neue Audit-Note setzen
4. Die Audit-Note selbst enthaelt den kompletten Drift-Bericht (kein Lose-Text in der alten Note)
5. Original-Text der alten Note NICHT loeschen oder ueberschreiben — historischer Wert
6. Erst NACH Stale-Marker: Daily-Addendum schreiben, Memory speichern

## Audit-Biene Pattern (NEU 2026-07-14)

**Zweck:** Read-only Extraktion einer Live-DB (SQLite) + Cross-Source-Triangulation mit bestehenden Vault-Notes + Web-Recherche-Ergebnissen → Drift-Matrix → Stale-Marker.

**Wann einsetzen:**
- "mit audit verifizieren, wir wollen keine drifts"
- Vault enthaelt ältere System-Notes mit Live-Counts (Files, Passwords, etc.)
- Vor grossen Vault-Edits: erst den Ist-Zustand erfassen

**Briefing-Beispiel (aus 2026-07-14 Session):**
```
Du bist Biene 4 (Audit) in Yunos GreyHack-Vault-Schwarm.

Kontext: Vault hat 04.07.-Notes mit Live-DB-Counts. 
Der Spielstand im GreyHackDB.db ist am 06.07. eingefroren (GameOver=1).

DEINE TASKS:
1. Lies GreyHackDB.db (SQLite, read-only):
   - `sqlite3 GreyHackDB.db 'SELECT COUNT(*) FROM Files'`
   - `sqlite3 GreyHackDB.db 'SELECT COUNT(*) FROM Passwords'`
   - `sqlite3 GreyHackDB.db 'SELECT COUNT(*) FROM Logs'`
   - `sqlite3 GreyHackDB.db 'SELECT * FROM Players'`
   - `sqlite3 GreyHackDB.db 'SELECT * FROM InfoGen'`
2. Lies greyhack-deep-systems-2026-07-04.md und greyhack-deep-intel-2026-07-04.md
3. Erstelle Drift-Matrix: alle Counts vergleichen, Zeitstempel vergleichen
4. Schreibe GreyHack-Audit-2026-07-14.md mit:
   - Drift-Matrix-Tabelle (7-10 Zeilen)
   - Player-State-Diff-Tabelle
   - Map-Diff (keine neuen Hosts? seit wann?)
   - Liste der veralteten Vault-Behauptungen (dokumentiert, nicht patched)
   - Aktualisierungs-Empfehlungen

OUTPUT: GreyHack-Audit-2026-07-14.md im Vault-Pfad
CONSTRAINTS: 0 boldface, <=1 em-dash, >=8 Wiki-Links, read-only DB, kein INSERT/UPDATE/DELETE
```

**Validierte Erkenntnis (2026-07-14):** Die Audit-Biene ist immer die kurzeste und praziseste Biene im Schwarm. Sie liefert die harte Evidenz (Zahlen, Timestamps, Diffs) waehrend die anderen Bienen synthetische Inhalte produzieren. Ihre Ergebnisse sind die wertvollsten fuer Queen-Entscheidungen (Stale-Marker, Patch-Priorisierung).

**Cross-Source-Triangulation:** Live-DB + Web-Recherche-Ergebnisse + bestehende Manuals = Wissens-Triangulation ohne Spekulation. Keine einzelne Quelle ist ausreichend.

**Drift-Matrix-Format (bewaehrt):**
```
| Tabelle | Stand 04.07. | Stand 14.07. | Delta | Bemerkung |
|---------|------------:|-------------:|------:|-----------|
| Computer | 18 | 18 | 0 | Identisch |
| Files | 247 | 256 | +9 | VIPER-Injection |
| Passwords | 267 | 282 | +15 | VIPER-Login-Flows |
| Logs | 21 | 22 | +1 | TokenTrace |
```

## Queen Baseline Pre-Execute for Audit Cross-Verification (NEU 2026-07-16)

**Validierung:** Skill-Audit 2026-07-16 — 4 Scout-Bienen dispatched, Queen lief 8 unabhängige Baseline-Scans parallel, die später 100% der Bienen-Claims verifizierten.

### Problem

Das Werkstatt-Pattern sagt "Phase 1 — Bienen auditieren, Queen macht reine Inspektion". Aber was heisst "reine Inspektion"? Bisher: Queen wartet auf Bienen-Landung, dann Verify. **Optimierungslücke:** Die Queen hat volle Tool-Zugriffe (terminal, execute_code) und kann in der Wartezeit **eigene Messungen** erheben — unabhängig von den Bienen.

### Lösung

Dispatche Bienen und starte sofort **eigene Queen-Baseline-Scans** (deterministisch, read-only). Die Baseline wird später zur **Cross-Verification** der Bienen-Self-Reports genutzt.

```text
t=0s     Queen dispatches 4 Scout-Bienen (parallel, background)
t=0s     Queen startet eigene Baseline-Scans (Werkstatt-konform: READ-ONLY)
           ├── Baseline A: Description-Length-Distribution
           ├── Baseline B: Missing-Frontmatter-Fields
           ├── Baseline C: Broken-References-Deep-Dive
           ├── Baseline D: Library-Token-Footprint
           ├── Baseline E: P0/P1/P2 Candidate-Identifikation
           └── [spezifische Metrik des aktuellen Audits]
t=90-180s Bienen landen → Queen erstellt Cross-Check-Matrix
           └── Biene-Claim vs. Queen-Baseline → ✅/⚠️/❌
t=180s    Entscheidung: Bienen-Patchen oder Queen-Direkt-Fix
```

### Wann einsetzen

- **Skill-Audit / Library-Scan:** Queen zählt Skills, Descriptions, Broken-Refs, Token-Budget
- **System-Health-Audit:** Queen scannt Service-Status, Disk-Usage, Prozessliste
- **Memory-Health-Audit:** Queen zählt Memory-Entries, prüft Freshness
- **Cron-Health-Audit:** Queen listet Cron-Einträge, prüft auf tote Pfade
- Jeder Audit wo Queen + Bienen auf gleiche Daten zugreifen können

### Wann NICHT einsetzen

- Queen hat keinen Tool-Zugriff auf die zu messenden Daten (kein terminal/read_file)
- Die Messung ist nicht deterministisch (ändert sich zwischen Messungen)
- Die Bienen erfragen User-Präferenzen die Queen nicht kennt (clarify braucht User)
- Audit ist so klein dass Baseline länger dauert als auf Bienen zu warten (<10 Skills)

### Spezifische Baseline-Befehle (aus 2026-07-16 Skill-Audit)

```bash
# Baseline A: Description-Length-Distribution
cd ~/.hermes/skills
python3 -c "
import yaml, glob
stats = {}
for f in glob.glob('**/SKILL.md', recursive=True):
    if '.archive/' in f: continue
    with open(f) as fh:
        parts = fh.read().split('---', 2)
        fm = yaml.safe_load(parts[1])
    d = len(str(fm.get('description',''))) if isinstance(fm,dict) else -1
    bucket = '<30' if d<30 else '<60' if d<60 else '60-200' if d<=200 else '200-600' if d<=600 else '>600'
    stats[bucket] = stats.get(bucket,0)+1
for k in sorted(stats): print(f'{k}: {stats[k]}')
"

# Baseline B: Missing Frontmatter
python3 -c "
import yaml, glob
for field in ['name','description','author','version']:
    missing = sum(1 for f in glob.glob('**/SKILL.md',recursive=True)
        if '.archive/' not in f and not yaml.safe_load(open(f).read().split('---',2)[1]).get(field))
    print(f'Missing {field}: {missing}')
"

# Baseline C: Broken-References-Deep-Dive
python3 -c "
import os, re, glob
broken = []
for f in glob.glob('**/SKILL.md', recursive=True):
    if '.archive/' in f: continue
    d = os.path.dirname(f)
    with open(f) as fh:
        refs = re.findall(r'(?:references|scripts|assets|templates)/[\w./-]+', fh.read())
    for r in set(refs):
        if not os.path.exists(os.path.join(d,r)) and not os.path.exists(r):
            # Filter false positives: template placeholders with <>/foo/bar/DATE
            if not re.search(r'(<|>|\{|\}|foo|bar|example|DATE)', r):
                broken.append((f,r))
print(f'Real broken refs: {len(broken)}')
# Group by skill category
by_cat = {}
for f,r in broken:
    cat = f.split('/')[0]
    by_cat.setdefault(cat,[]).append(r)
for c in sorted(by_cat, key=lambda c: len(by_cat[c]), reverse=True):
    print(f'  {c}: {len(by_cat[c])}')
"

# Baseline D: Token Budget (Bytes/4 ≈ Tokens)
find . -name SKILL.md -not -path '*/.archive/*' -exec cat {} + | wc -c | awk '{print $0, "bytes =", $0/4, "tokens (est.)"}'

# Baseline E: P0/P1/P2 Candidates
python3 -c "
import yaml, glob, re
p0 = []  # description <30 chars
p1 = []  # no trigger AND description <80 chars
p2 = []  # >500 lines
for f in glob.glob('**/SKILL.md', recursive=True):
    if '.archive/' in f: continue
    with open(f) as fh:
        content = fh.read()
    parts = content.split('---',2)
    fm = yaml.safe_load(parts[1]) if len(parts)>=2 else {}
    desc = str(fm.get('description','')) if isinstance(fm,dict) else ''
    lines = content.count(chr(10))
    if len(desc) < 30: p0.append(f)
    has_trig = bool(re.search(r'(use when|triggers on|trigger:)', content, re.I))
    if not has_trig and len(desc) < 80: p1.append(f)
    if lines > 500: p2.append(f)
print(f'P0 (desc<30): {len(p0)}')
print(f'P1 (no trigger + desc<80): {len(p1)}')
print(f'P2 (>500 Zeilen): {len(p2)}')
"
```

### Queen-Verify-Matrix (Cross-Check bei Bienen-Landung)

Sobald die Bienen Selbst-Reports liefern, prüft die Queen sofort gegen ihre eigene Baseline:

```bash
# Beispiel: Bee behauptet "152 skills with description <60 chars"
# Queen Baseline A hat genau das gemessen → ✅ bestätigt

# Beispiel: Bee behauptet "0 broken refs"
# Queen Baseline C hat 280 echte broken refs → ❌ Self-Report falsch
# → Queen muss nachfragen oder Bienen-Output ignorieren
```

Template für die Verify-Matrix:

```markdown
## Queen Cross-Check Matrix

| Metrik | Queen Baseline | Bee A Claim | Bee B Claim | Status |
|--------|:-------------:|:-----------:|:-----------:|:------:|
| Active Skills | 298 | — | 298 | ✅ Match |
| Broken Refs | 280 | 0 | — | ❌ Bee A falsch |
| ... | ... | ... | ... | ... |
```

### Unterschied zu Queen-Pre-Execute (Mechanik)

| Aspekt | Queen Pre-Execute (Mechanik) | Queen Baseline Pre-Execute (Audit) |
|--------|-----------------------------|-----------------------------------|
| Queen macht | **Gleiche** Aufgabe wie Bienen (Build) | **Andere** Aufgabe (Baseline-Messung) |
| Bienen machen | **Gleiche** Aufgabe (Post-Validierung) | **Andere** Aufgabe (Tiefen-Audit) |
| Risiko | Queen könnte Bienen-Ergebnis vorwegnehmen | Kein Risiko (read-only, kein State-Change) |
| Wall-Time-Gewinn | ~60% | ~30% (keine Wartezeit, Baseline in <30s) |
| File-Affinity | Trivial (Queen + Bienen = verschiedene Files) | Trivial (Baseline wird nicht geschrieben) |
| Pitfall-Risiko | Niedrig (reversibel mit Backup) | **Kein** Risiko (read-only Messung) |
| Werkstatt-Konform | ❌ (Edit in Phase 1) | ✅ (Reine Inspektion in Phase 1) |

### P0/P1/P2 Categorization für Findings

Jedes Queen- oder Bienen-Finding bekommt eine Priorität:

| Priority | Kriterium | Beispiel | Reaktion |
|:--------:|-----------|----------|----------|
| **P0** | Blockiert Kernfunktion, User-Ärger, falsches Verhalten | Description <30 chars, missing version | Sofort-Fix in dieser Session |
| **P1** | Beeinträchtigt Qualität, Auffindbarkeit, Wartbarkeit | Broken refs, no trigger phrase, weak description | Fix in Welle 2, nicht aufschieben |
| **P2** | Cleanup, Optimierung, Kosmetik | >500 Zeilen, duplicate scripts | Notieren für next Polish-Cycle, kein Fix jetzt |
| **P3** | Nice-to-have, nicht-dringend | Tokens, Format-Constraints | Dokumentieren, kein Fix |

### Referenzen

- `references/queen-pre-execute-pattern.md` — Mechanik-Variante des Pre-Execute (Viper-Redeploy)
- `references/queen-baseline-scan-pattern.md` — vollständige Baseline-Befehle als wiederverwendbares Script
- `references/skill-audit-4-bee-workflow.md` — Skill-Audit mit 4 orthogonalen Scout-Bienen, Post-Fix-Verification-Loop, "Confidently Wrong Baseline" Pitfall, Trigger-Coverage Caveat (validiert 2026-07-16, 298 Skills, 43 Fixes)

## Orthogonal Scout-Biene Pattern (NEU 2026-07-15)

**Validierung:** Yuno System-Härtungs-Plan (12 Tasks, 3 Scout-Bienen, 30% Wall-Time-Einsparung).

**Problem:** Viele System-Härtungs-Tasks sind 90%+ Mechanik (Backup, Python-Scripte, Code-Edits, Cron setzen, Memory schreiben). Per Pitfall #34 (Parent-Direct beats subagent) und #17 (Parent-Direct für <30min Lanes) sind diese Tasks NICHT delegierbar. Aber sie sind auch die perfekte Gelegenheit für einen Schwarm — die Queen muss die Bienen nicht aufhalten, sie kann parallel arbeiten.

**Lösung:** Orthogonale Scout-Bienen. Die Bienen machen **NICHT** die Härtung selbst (das ist Queen-Job). Sie arbeiten **orthogonal** — Read-Only-Audits in Bereichen die die Queen bei der Konzentration auf die Mutation übersieht.

### Wann einsetzen

- Queen hat 8+ Tasks mit 80%+ Mechanik-Anteil (Backup, Script-Write, Tool-Run, Cron-Set)
- Es gibt 2-3 klar abgrenzbare Audit-Bereiche die die Queen nicht selbst abdeckt
- Die Bienen-Audits sind **unabhängig** von der Queen-Arbeit (kein Gate, kein Blocking)
- Die Bienen-Ergebnisse **ergänzen** die Queen-Arbeit, bestätigen sie oder zeigen Blinde-Flecken

### Wann NICHT einsetzen

- Bienen-Audit würde Queen-Mutation blockieren (warten auf Bee-Ergebnis)
- Bienen-Audit überschneidet sich mit Queen-Arbeit (doppelte Arbeit)
- Es gibt keine klaren orthogonalen Audit-Scopes (alles was zu tun ist, sind Mutationen)

### Struktur

```text
QUEEN (sequenziell, Mutationen)     BIENEN (parallel, read-only)
  ├── Task 0: Backup                ─── (kein)
  ├── Phase A: Skills fixen         ─── Biene S1: Skill-Health-Audit
  ├── Phase B: Memory härten        ─── Biene S2: Cron-Health-Audit
  │                                  ─── Biene S3: Memory-Health-Audit
  ├── [Bienen landen]               ─── Queen liest Bienen-Outputs
  ├── Queen-Synthesis               ─── Cross-Check Bienen vs. Queen
  └── Final Report                  ─── Bienen-Findings integriert
```

### Unterschied zu Queen-Pre-Execute

| Aspekt | Queen-Pre-Execute | Orthogonal Scout-Biene |
|--------|-------------------|----------------------|
| Queen-Arbeit | Gleiche Aufgabe wie Bienen (Build, Deploy) | **Andere** Aufgabe (Mutationen) |
| Bienen-Arbeit | Gleiche Aufgabe wie Queen (Post-Validierung) | **Andere** Aufgabe (Read-Only-Audit) |
| Risiko | Queen macht Dinge die Biene auch finden würde | Biene findet was Queen **nicht** sieht |
| Wall-Time-Gewinn | ~60% (Queen macht Bienen-Arbeit schneller) | ~30% (Queen + Bienen arbeiten parallel an unterschiedlichen Dingen) |
| File-Affinity | Queen + Bienen schreiben in verschiedene Outputs | Trivial (verschiedene Scopes = verschiedene Outputs) |
| Pitfall-Risiko | Niedrig (Queen validiert sich selbst) | Niedrig (Bienen-Audit ist read-only, kein Phantom-Fix möglich) |

### Briefing-Architektur für Orthogonal-Bienen

Die Briefings folgen dem Standard-Template (Identity, Context, Tasks, Output-Constraints, Toolset-Restrictions, Self-Verify). **Zusätzlich:**

**1. Output-Format:** "REIN TEXT in deiner Antwort (kein File-Write)" — denn die Queen schreibt die Files selbst nach Verify. Das verhindert Pitfall #6 (wrong output path) und Pitfall #29 (file not written but "completed" status).

**2. MAX tool-calls Grenze:** Bienen bekommen eine harte Obergrenze (z.B. MAX 12 terminal-calls). Nach dem Limit → Synthese mit was sie haben. Das verhindert Pitfall #30 (subagent timeout) und Pitfall #19 (web-API hangs).

**3. Self-Report Pflichtfelder:**
```yaml
SELF-REPORT am Ende: "Bienen-Self-Report: N tool-calls, M findings"
```

**4. Self-Verify Anweisung:** "Alle Fakten mit Pfadangabe. Nichts erfinden. Lieber 'konnte nicht prüfen, weil Pfad nicht gefunden' als halluzinieren."

### Queen-Verify Protocol (nach Bienen-Landung)

**Tier 1: Datei-Existenz** — `[ -f "$FILE" ] && echo "✅ $(wc -l < $FILE) lines"` — warum: Check ob Biene wirklich geschrieben hat (Pitfall #35, HTTP 429 silent fail).

**Tier 2: Content-Validierung** — `grep -c "^## " <file>` (mindestens 5 Sections), `grep -cE "[0-9]+" <file>` (konkrete Zahlen vorhanden).

**Tier 3: Realitäts-Check** — CRITICAL (Pitfall #5). Queen verifiziert Bienen-Claims:
```bash
# Beispiel: Skill-Count verifizieren
find ~/.hermes/skills -name SKILL.md | wc -l
# Beispiel: Cron-Count verifizieren
crontab -l | grep -v '^#' | grep -v '^$' | wc -l
```

### Queen-Synthesis Template

```markdown
## Bienen-Schwarm-Synthese

### Biene S1 (Skill-Health): N findings
- [P0/P1/P2] Finding-Beschreibung
- Cross-Check mit Queen-Arbeit: [bestätigt / ergänzt / widerspricht]

### Biene S2 (Cron-Health): N findings
- [P0/P1/P2] Finding-Beschreibung
- Cross-Check mit Queen-Arbeit: [bestätigt / ergänzt / widerspricht]

### Biene S3 (Memory-Health): N findings
- [P0/P1/P2] Finding-Beschreibung
- Cross-Check mit Queen-Arbeit: [bestätigt / ergänzt / widerspricht]

### Schwarm-Verifikations-Matrix
| Biene | Tool-Calls | Findings | Self-Report | Queen-Verify | Status |
|---|---|---|---|---|---|
| S1 | N | N | N calls, N findings | ✅/⚠️/❌ | OK/PARTIAL/FAIL |
| S2 | N | N | N calls, N findings | ✅/⚠️/❌ | OK/PARTIAL/FAIL |
| S3 | N | N | N calls, N findings | ✅/⚠️/❌ | OK/PARTIAL/FAIL |
```

### Referenzen

- `references/orthogonal-scout-skill-health.md` — Briefing für Skill-Health-Audit-Biene (S1)
- `references/orthogonal-scout-cron-health.md` — Briefing für Cron-Health-Audit-Biene (S2)
- `references/orthogonal-scout-memory-health.md` — Briefing für Memory-Health-Audit-Biene (S3)
- `references/queen-pre-execute-pattern.md` — verwandtes Pattern: Queen arbeitet am gleichen Task wie Bienen

## Hypothesis-Falsification via Code-Trace Bee (NEU 2026-07-16)

**Validierung:** Biene-X im System-Audit 2026-07-16 — meine Hypothese ("Mnemosyne will API-Provider X, .env hat falschen Key") wurde in **87s durch Code-Tracing falsifiziert**.

### Problem

Wenn eine Diagnose-Hypothese im Raum steht, dispatche ich oft eine Queen-Rate-Session: .env prüfen, API-Test, logs checken. Das kostet 3-5 Min und bestätigt meist die bestehende Hypothese — oder widerlegt sie ohne Ersatz-Erklärung.

### Lösung: Code-Trace Bee

Dispatche eine **Code-Trace-Biene** die den Source-Code-Pfad live verfolgt, statt die Queen-Hypothese zu raten oder zu bestätigen:

```text
QUEEN: "Mnemosyne-LLM funktioniert nicht → Hypothese: API-Key fehlt"
  ↓ dispatche Code-Trace Bee (87s)
BIENE: "Habe local_llm.py:91 gelesen → import llama_cpp fehlschlagend
       → ModuleNotFoundError → silent fallback.
       GGUF-Modell existiert (656 MB), LLM_ENABLED=True.
       Echter Fehler: llama-cpp-python nicht im venv installiert."
  ↓ QUEEN: "Hypothese FALSIFIZIERT. Echter Fehler = pip-Install"
```

### Wann einsetzen

| Signal | Pattern | Begründung |
|--------|---------|-----------|
| "Modell X antwortet nicht / Provider-Fehler" | **Code-Trace Bee** | Import-Path / Config-Pfad / Module-Load sind debug-bar |
| "Log zeigt Error X, aber warum?" | **Code-Trace Bee** | Source-Code-Level kann Ursache klären |
| "Es muss an .env liegen" | **Zuerst Code-Trace Bee** | Meist liegt es NICHT an .env — Biene findet den echten Fehler in <90s |
| "Port Y antwortet nicht" | **Queen direkt** | Network-Test ist schneller als Subagent |

### Briefing-Struktur

```text
Du bist Biene-X (Code-Trace) in Yunos Diagnose-Schwarm.

KONTEXT:
- Datei/Service: [Name, Pfad]
- Queen-Hypothese: [was ich glaube — als HINWEIS, nicht als Befund]

DEINE TASKS (ALLES READ-ONLY):
1. Lies den Source-Code: [genauen File-Pfad + relevante Zeilen]
2. Prüfe die Import-Kette: [was wird importiert? Scheitert es?]
3. Prüfe vorhandene Ressourcen: [Dateien, Models, Configs]
4. Führe ggf. Test-Import aus: [terminal python3 -c "from X import Y"]
5. FALSIFIZIERE oder BESTÄTIGE die Queen-Hypothese

OUTPUT-CONSTRAINTS (PFLICHT):
- Beginne mit: "Queen-Hypothese '[Zitat]' wird [BESTÄTIGT / FALSIFIZIERT]"
- Gib konkreten Code-Pfad + Zeilennummern
- SELF-REPORT am Ende: N tool-calls, genaue Dauer

MAX <8> tool-calls.
```

### Regel: Erste Hypothese dispatchen, nicht selbst testen

Wenn die Diagnose einen internen Code-Pfad betrifft (nicht Netzwerk, nicht Port): **dispatche zuerst eine Code-Trace Bee, rate nicht selbst.** Die Queen spart 3-5 Min Fehlersuche, die Biene findet in <90s den echten Fehler, und die Hypothese wird oft falsifiziert — das ist erwünscht.

## Skip-Decision Protocol (NEU 2026-07-16)

**Validierung:** Basti sagte "skip D" — der Mnemosyne-Fix wandert in den Sonntags-Runbook.

### Protocol

Wenn der User zu einem Finding sagt "skip", "nicht jetzt", "später", "im nächsten Runbook":

1. **Dokumentiere die Entscheidung im Report** mit Zeitstempel und Begründung des Users
2. **Setze Status auf ⏭ SKIP** — nicht PENDING, nicht DEFERRED. SKIP = bewusste Entscheidung
3. **Verlinke in Runbook-Sektion** — wo und wann der Fix nachgeholt wird
4. **Memory-Notiz schreiben** — damit die nächste Session weiß, dass es einen Runbook-Anker gibt
5. **Bericht abschließen** — nicht auf den Skip warten, den Rest finalisieren

**Nicht machen:**
- ❌ Finding offen lassen (User hat entschieden, respektieren)
- ❌ Im gleichen Runbook nochmal vorschlagen (Skip = Skip)
- ❌ Memory ohne Runbook-Datum (dann wird es vergessen)

**Template für Report-Sektion:**
```markdown
### [ID] — [Finding] · ⏭ SKIP

**Basti-Entscheidung [Zeit]:** ⏭ SKIP — wandert in [Ziel, z.B. Sonntags-Runbook 19.07.]
**Fix:** [1 Befehl / kurze Beschreibung]
**Warum:** [Begründung wenn gegeben]
```

## Nested Delegation (Sub-Sub Dispatch) — Validated 2026-07-14 (v2)

**Primärer Gate: `role='orchestrator'`, NICHT `max_spawn_depth`.**

Die erste Test-Runde (2026-07-14, ~23:11) scheiterte mit sub_call_count=0 obwohl `max_spawn_depth=2` gesetzt war. Grund: die Parent-Bienen wurden mit `role='leaf'` (default) dispatcht. Laut `tools/delegate_tool.py:705` wird `delegate_task` NUR aus dem Toolset entfernt wenn `role != 'orchestrator'` **UND** `max_spawn_depth < 2` — beides leaf + limit. Ein leaf-Biene hat delegate_task nicht, selbst bei `max_spawn_depth=99`.

**Zweite Runde (2026-07-14, ~23:25) mit `role='orchestrator'`:** alle 3 Parent-Bienen hatten sub_call_count=1, alle 3 Sub-Sub-Files existierten, SHA256-Hashes byte-genau verifiziert gegen Parent-recompute. Gesamt: 285s wall-time für 3× Parent + 3× Sub-Sub parallel.

**Resultat-Matrix (Side-Effect-Files als Beweis):**

| Parent | Role | Sub-Calls | Main-File | Sub-File | Beweis |
|--------|------|:---------:|-----------|----------|--------|
| Alpaca | orchestrator | 1 | 2.540b JSON | 1.153b MD | `ls -la /tmp/gh-test-alpaca/` |
| Bumble | orchestrator | 1 | 6.621b MD | 13.467b JSON | `ls -la /tmp/gh-test-bumble/` |
| Cicada | orchestrator | 1 | 5.763b MD | 656b TXT | 5/5 SHA256 match |

**Wann lohnt sich ein Sub-Sub?** Wenn eine Biene innerhalb ihrer Hauptarbeit einen **fokussierten Sub-Task** hat, der:
- Nicht-mechanisches Reasoning enthält (Diagnose, Klassifikation, Cross-Check)
- Genug Output-Volumen hat um Parent-Context zu entlasten (Bumble: 41 API-Calls im Sub-Sub)
- Ein anderes Toolset braucht

**NICHT** lohnen wenn Sub-Task reine IO ist (sha256sum, copy, ls). Die Sub-Sub-Initialisierungs-Overheads (~10s Boot + Tool-Roundtrip) sind höher als die inline-Ausführungszeit. **Faustregel:** Sub-Sub lohnt sich wenn Sub-Task API-Call-Volumen >20 ist oder Reasoning erfordert.

**Config-Änderung für Nested Delegation:**

```bash
# Voraussetzung: max_spawn_depth von 1 nach 2 erhöhen
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%Y%m%d-%H%M%S)   # Backup
hermes config set delegation.max_spawn_depth 2                                 # CLI-Set
hermes config check                                                             # Validierung
grep "max_spawn_depth" ~/.hermes/config.yaml                                    # Verify Platte
```

**⚠️ Config-Session-Caching (wichtigster Pitfall):** Die laufende Hermes-Session hat den config-Wert beim Process-Start gelesen und cached. Änderungen auf Platte (max_spawn_depth: 2) werden für **NEUE Sessions** aktiv, nicht für den laufenden Dispatch. Der Subagent-Loader in `tools/delegate_tool.py:_get_max_spawn_depth()` konsultiert die Config zur Laufzeit — abhängig davon ob der Python-Prozess den neuen Wert sieht oder den alt-cached. Wenn der Test zeigen soll dass Sub-Sub wirklich funktioniert: **Session neu starten nach Config-Change**, dann dispatchen.

**Parallel-Math für Sub-Subs:** `max_concurrent_children: 6` erlaubt maximal 6 gleichzeitige Subagents. Bei Sub-Sub-Dispatch gilt:
- N Parent-Bienen + N Sub-Sub-Bienen ≤ 6
- Beispiel: 3 Parent + 3 Sub-Sub = 6 (exakt am Limit)
- Beispiel: 2 Parent + je 1 Sub-Sub = 4 (2+2=4, komfortabel)
- Wenn mehr als 6 gleichzeitig gebraucht: `max_concurrent_children` vorher erhöhen

**Briefing-Pattern für Orchestrator-Bienen mit Sub-Sub:**

1. Definiere die Parent-Biene als `role='orchestrator'` im `delegate_task`-Call
2. Im Briefing: klarer Trennung zwischen Haupt-Task und Sub-Sub-Task
3. Sub-Sub-Task MUSS eigenständig sein (keine Abhängigkeit von Parent-Output)
4. Self-Report MUSS enthalten: `sub_call_count` (wie oft delegate_task aufgerufen), Sub-Sub-Ergebnis, und eine Bewertung ob die Indirektion sich gelohnt hat
5. Briefing muss sagen "Du MUSST Sub-Sub X aktiv spawnen" — sonst tut die Biene alles selbst (Pitfall: sub_call_count=0)

**Self-Report-Pflichtfelder für Orchestrator-Bienen:**
```yaml
Self-Report MUSS enthalten:
- Anzahl sub_calls (delegate_task-Aufrufe aus dieser Biene)
- Sub-Sub-Ergebnis (welche Daten kamen zurück?)
- Bewertung: "Hat sich gelohnt? (ja/nein) — Begründung"
```

1. **Subagenten geben oft Self-Reports, die halb-richtig sind.** Cross-Check ist Queen-Pflicht.
2. **Skizzen-Drift ist real.** Wenn die Biene "disabled wegen Crash-Loop" behauptet und Live "active" sagt → das Bild ist echt, Skizze ist falsch. **Verifizieren, dann Skizze fixen mit Update-Log Pattern.**
3. **Service-Prozesse luegen oft.** Selbst `systemctl status active` kann einen Auth-required Service zeigen, der nicht antwortet. `curl` mit `Content-Type: application/json` testen.
4. **Background-Process in Hermes: IMMER `terminal(background=true)`** mit `notify_on_complete=true` oder `watch_patterns`, **nie** `nohup/disown` im Foreground-Call — Hermes blockt das (Sicherheits-Sperre).
5. **Updates-Log in Skizzen/Notes** für Audit: `datum: YYYY-MM-DD` im YAML + `update-log` Block mit Sources. Macht Doku-Drift retracing-bar.
6. **Pfad-Wurzel-Verifizierung** — siehe oben; Koenigin hat sich einmal bei Phase 1 Verify vertan (subagent hatte Recht).
7. **Auth-Required ≠ Service-tot.** Biene 2B fand hermes-webui "active+enabled" aber Endpoint wollte Auth — das ist normal, kein Bug. Koenigin haette das gleich erkennen muessen.
8. **Biene-Self-Report zu Format-Constraints ist unzuverlaessig (NEU 2026-07-13).** Eine Biene die "All criteria met" behauptet, während 17 Boldface-Stellen + 5 Inline-Header im Output stecken, hat sich nicht selbst geprueft — sie hat halluziniert dass alles OK ist. **Immer live-read_file + grep auf die Output-Datei, nie dem Self-Report glauben.**
9. **Koenigin-Override ist schneller als Neu-Dispatch (NEU 2026-07-13).** Bei <= 20 Format-Verletzungen: targeted Patches als Queen in ~2 Minuten. Neu-Dispatch + Verify + ggf. Override = 3-5 Minuten + Risiko neuer Fehler.
10. **Quality-Gate-PFLICHT ist der groesste Qualitaetshebel (NEU 2026-07-14).** Bienen mit PFLICHT-Formulierung im Briefing hatten 0 Verstoesse ab erstem Wurf (Biene 1+4). Bienen mit Empfehlungs-Formulierung brauchten 2-3 Patches. Validierte Faustregel: Die Wortwahl im Briefing-Template ist der groesste Einzelfaktor. Formuliere Constraints als "NICHT ERLAUBT" / "VERBOTEN" / "PFLICHT", nicht als "bevorzugen" / "empfehlen" / "idealerweise".
11. **Audit-Biene liefert die harte Evidenz (NEU 2026-07-14).** Waehrend synthetische Bienen (Manual, Cookbook, Library-Katalog) viel Content produzieren, liefert die Audit-Biene die minimal kurzeste Datei mit der hoechsten Signifikanz. Ihre Drift-Matrix ist die einzige Biene deren Output direkten Handlungsbedarf ausloest (Stale-Marker, Patches). **Die Audit-Biene gehoert immer in den Schwarm, auch wenn der User sie nicht explizit verlangt.**
12. **Stale-Marker gehoeren in den ersten Queen-Arbeits-Block (NEU 2026-07-14).** Nicht warten bis alle Bienen-Outputs gelesen sind. Sobald die Audit-Biene Drift identifiziert: sofort YAML-Frontmatter updaten + Wiki-Backlink setzen. Das verhindert, dass die anderen Bienen ihre Cross-Refs auf eine stale Note setzen.

## Typische Outputs der Bienen (was Queen dann bekommt)

Pro Biene **1 strukturiertes Markdown-Report** mit:
- Befund (was Live-State zeigt)
- Konflikt-Punkte (was nicht stimmt)
- Empfehlung-Top-3 (priorisiert)
- Quellen (URLs + lokale Files)

Laenge: 400-700 Woerter pro Biene. Falls laenger → Briefing war zu breit.

**Typische Groessen (validiert 2026-07-14):**

| Biene | Bytes | Zeilen | Wiki-Links |
|-------|------:|-------:|-----------:|
| 1 (Sprachreferenz) | ~20 KB | ~520 | ~16 |
| 2 (Hacking-Cookbook) | ~26 KB | ~600 | ~12 |
| 3 (Lib-Katalog) | ~44 KB | ~1.100 | ~16 |
| 4 (Audit) | ~13 KB | ~190 | ~8 |

Wenn Biene 3 > 40 KB produziert: Briefing war zu breit. Naechstes Mal aufteilen auf 2 Bienen.

## Wann BEENDEN und nicht weiter dispatchen?

- Wenn 2 Wellen durch sind + Skizzen/Notes aktualisiert → STOP (nicht endlos verbessern)
- Wenn eine Biene Failed → andere Bienen laufen lassen, das fehlende Stueck selbst mit `terminal` machen statt neue Welle
- Wenn alle Bienen "OK, kein Handlungsbedarf" sagen → STEP-OUT, Queen macht Wrap-up

## Werkstatt-Phase-Pattern (IST → SOLL → Gap → Plan → Arbeit)

Wenn Basti "Werkstatt" oder "IST-SOLL-Evaluierung" sagt → folgende 4-Phasen-Architektur:

```
Phase 1 — IST-Sammeln (parallel Schwarm 3-4 Bienen)
  Erfasse Vault-Inventar, Memory-Tiers, Skills/Profile-State.
  Eine Biene macht Live-DB-Extraktion für Drift-Check.
  Biene-Cross-Check am Ende.

Phase 2 — SOLL-Definition (Koenigin + Basti-Dialog)
  Vision skizzieren. Keine Bienen hier — Dialog-Phase.
  Basti's Stichworte werden zu konkretem SOLL ausformuliert.

Phase 3 — Gap-Evaluation (Koenigin allein)
  IST vs. SOLL → P0-P3 priorisierte Gap-Liste.
  Was fehlt strukturell? Was ist redundant?

Phase 4 — Plan + erste Arbeit (Koenigin allein, ggf. 1 Welle 2)
  Gaps werden konkrete Tasks. P0-Tasks selbst anfassen oder Welle 2 dispatchen.
  Bei jedem P0-Work: Doku mit-Pflegen (Skill-Update, Vault-Note, Mnemosyne-Memory).
  Stale-Marker aus Phase 1 jetzt fixen.
```

**Wichtige Werkstatt-Regel:** Waehrend Phase 1 (Bienen auditieren) → Koenigin macht KEINE Vault-Edits oder Memory-Mutationen ausser Stale-Marker. Reine Inspektions-Phase. Edits erst ab Phase 4, und dann mit `update-log` in Skizzen/Notes.

Diese Kuerze = schnell + zielgerichtet.

## Production Code Skeletons (2026 Deep Research)

Die Perplexity-Deep-Research-Session vom 2026-07-15 lieferte 3 produktionsreife Python-Skeletons, die die Queen-Bee-Patterns in ausführbaren Code giessen. Sie sind als Referenz-Dateien abgelegt:

| Skeleton | Pattern | Datei | Wann nutzen |
|---|---|---|---|
| **A — Master/Worker** | Queen-Bee Fan-out | `references/skeleton-master-worker.md` | N ≥ 2 unabhängige Subtasks parallel |
| **B — Hierarchical Tree** | `role='orchestrator'` mit Sub-Sub | `references/skeleton-hierarchical-tree.md` | Mehrere Sub-Domänen, je eigene Worker |
| **C — Critic-Loop** | Maker-Checker / Reflexion | `references/skeleton-critic-loop.md` | Korrektheit rechtfertigt Review-Overhead |

**Alle 3 Skeletons enthalten:** `asyncio.Semaphore`-Rate-Limiting, `asyncio.wait_for`-Wall-Clock-Kill, Exponential-Backoff-Retry mit Jitter, Idempotency-Keys, Audit-Trail (append-only JSON-Log), strukturierte `AgentResult`-Dataclasses, und TODOs für echte `delegate_task`-Calls. **Referenz:** vollständiger Perplexity-Report in `~/.hermes/docus/research-prompts/M-agent-orchestration.md`.

## Decision Flowchart (Pattern Selection)

Validierter Entscheidungsbaum — kurz, sofort anwendbar:

```
Neue Aufgabe
      │
      ▼
Ein Tool-Call / einfache Format-Konvertierung?
  JA → direkt tool/execute_code. KEINE Delegation.
  NEIN → Kann in N ≥ 2 unabhängige Subtasks parallelisiert werden?
    JA → Skeleton A (Master/Worker Fan-out)
    NEIN → Mehrere Sub-Domänen mit eigenen Workern?
      JA → Skeleton B (Hierarchical Tree, depth 2, role='orchestrator')
      NEIN → Korrektheit wichtig genug für Review-Overhead?
        JA → Skeleton C (Critic-Loop, max_rounds=3)
        NEIN → Skeleton A (single worker, kein Critic)
```

**Token-Budget-Referenz** (Anthropic Engineering Post June 2025):

| Skeleton | Depth | Branching | Multiplikator vs. Chat | Wall-Clock (3 Worker) |
|---|---|---|---|---|
| A — Master/Worker | 1 | 4 | ~15× | ~100s parallel |
| B — Tree | 2 | 3×3 | ~45× | ~200s |
| C — Critic-Loop | N/A | 3 Runden | ~15× pro Runde | ~100s × Runden |

## HandoffPacket Pattern (Context-Propagation)

**Strukturierte JSON-Context-Pakete statt Raw-History-Kopie über Level-Grenzen hinweg** — löst das „Context-Explosion at depth 2"-Problem.

```python
@dataclass
class HandoffPacket:
    task_id: str
    correlation_id: str       # durch alle Level für Full-Tracing
    depth: int                # aktueller Spawn-Depth
    goal: str
    constraints: list[str]
    relevant_artifacts: list[str]   # Dateipfade/Keys, KEINE Inline-Daten
    output_schema: dict[str, str]
    parent_summary: str = ""        # ≤ 200 Tokens Parent-Kontext
```

**Kernregel:** Subagents starten mit NULL Wissen über Parent-Konversation. ALLES was das Kind braucht, MUSS im Packet. Fat Packets = Context-Explosion auf L2.

## Sycophancy Guard (Neu aus Perplexity Research — in Critic-Loops einbauen)

**Der Critic darf NIEMALS die `rationale` des Workers sehen** (Worker's eigene Selbst-Einschätzung). Sycophancy-Effekt: Critic spiegelt Worker-Bewertung statt unabhängig zu prüfen.

**Fix:** Critic bekommt nur Output, nie rationale. Der rationale ist Worker-intern. Validierung: 2025-2026 Production-Audits zeigen 40-60% Cost-Reduktion durch Cheap-maker + Capable-checker bei gleichbleibender Qualität — VORAUSGESETZT der Sycophancy Guard ist aktiv.

**Praktisch:** Wenn ein Critic Format-Constraints nach Bienen-Landung evaluiert (z.B. Boldface-Count), dann die Bienen-`rationale`/`self-evaluation` SEPARAT halten — nie als Critic-Input übergeben.

## Cross-Reference: hermes-orchestration (V2.4+) & Related Skills

Seit 2026-06-27 existiert `hermes-orchestration` als **dedizierter Ausführungsskill** — dieser Skill bleibt das **Pattern-Repository**, der Ausführungsskill ist `hermes-orchestration`.

| Feature | queen-bee-schwarm-dispatch (Pattern) | hermes-orchestration (Runtime) |
|---|---|---|
| Queen-Bee Schwarm | ✅ Dispatch-Protokoll + Templates | ✅ Hermes Subagent Bridge |
| Code Skeletons A/B/C | ✅ references/ (Python Production-Code) | ❌ |
| HandoffPacket | ✅ Definierte Context-Struktur | ❌ |
| Sycophancy Guard | ✅ Anti-Pattern | ❌ |
| Decision Flowchart | ✅ Pattern-Wahl-Baum | ❌ |
| Heuristic Extraction / Mnemosyne / Cron | ❌ | ✅ |

**Empfehlung:** Für neue Runs `hermes-orchestration` nutzen (es läuft). Diesen Skill für das Pattern-Wissen und die neuen Code-Skeletons laden.

## Reference: Das Original-Briefing (Welle 1, Biene 1A Dataview)

```text
Aufgabe: 4 gezielte Patches in ~/.hermes/skills/{note-taking,obsidian-vault}/
gegen die Drift zwischen Plugin-Wahrheit und Skill-Doku-Behauptung.
Tool-Set: read_file, write_file, search_files (KEIN terminal).
Verify-via: grep -r 'installiert' ~/.hermes/skills/
Output: Markdown, max 500 Woerter, Frontmatter-Liste der 4 Patches.
```

Diese Kuerze = schnell + zielgerichtet.