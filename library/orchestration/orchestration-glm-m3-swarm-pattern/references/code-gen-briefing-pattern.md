# Code-Gen Briefing Pattern (M3 Workers)

> Validated 2026-07-09: 4 parallel Python scripts (12-28 KB, 319-533 LOC each),
> wall-clock ~3 min including Queen verification. Model: DeepSeek V4 Flash (Queen),
> 4 × M3 (Worker-Bienen). Cost: 0 EUR.

## TL;DR

Concrete schema snapshots + exact file structure + E2E test requirement = M3 finishes
in 2-5 min instead of 10-30 min. Abstract briefings ("schreib ein Audit-Skript")
produce loops and context-bloat.

## Briefing Anatomy for Code-Gen

Each briefing has exactly 4 parts in this order:

### 1. Schema / Meta-Context (15-25% des Briefings)

Not "die DB hat eine Tasks-Tabelle". Sondern:

```
SCHEMA (tasks):
  id TEXT PRIMARY KEY           # UUID
  title TEXT NOT NULL
  status TEXT DEFAULT 'ready'   # ready|active|paused|done|archived
  board_id INTEGER DEFAULT 1
  mnemosyne_ref TEXT            # Zielspalte für done_hook
  tenant TEXT DEFAULT 'default'
  created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  result TEXT
  summary TEXT
  metadata TEXT                 # JSON-blob
  created_cards TEXT            # JSON-array
  expected_run_id TEXT
```

Warum: M3 braucht exakte Spaltennamen + Typen für SELECT/INSERT/UPDATE-Code.
"Oh, die Spalte heißt `mnemosyne_ref` nicht `memory_id`" ist die häufigste
Code-Gen-Quelle von Fehlern.

### 2. File/Verzeichnis-Struktur (5-10% des Briefings)

```
Verzeichnis-Struktur:
  /home/bratan/.hermes/scripts/
    memory_health_check.py      # Dein Skript
    sync_engine.py              # Anderes — NICHT ändern
  
  /home/bratan/.hermes/kanban/boards/hermes/kanban.db  # SQlite-DB
  
  /home/bratan/.hermes/mnemosyne/
    data/banks/vault-phase-6/   # Mnemosyne Speicher
    config.env                  # Env-Vars
```

Warum: M3 importiert sonst aus falschen Pfaden oder schreibt nach /tmp/.

### 3. Funktionale Spec + Constraints (40-50% des Briefings)

Nicht "analysiere die DB". Sondern:

```
PFLICHTEN:
  1. Öffne: /home/bratan/.hermes/kanban/boards/hermes/kanban.db (read-only)
  2. Query: SELECT COUNT(*) FROM tasks WHERE status='done' AND mnemosyne_ref IS NULL
  3. Query: SELECT DISTINCT status FROM tasks — validiere Werte
  4. Query: SELECT * FROM tasks WHERE status='done' AND mnemosyne_ref IS NOT NULL LIMIT 5
  
CONSTRAINTS:
  - READ-ONLY auf kanban.db (öffne mit sqlite3.connect(db_path) — kein INSERT/UPDATE)
  - Mnemosyne DB: /home/bratan/.hermes/mnemosyne/data/banks/vault-phase-6/
  - Backup-Check: ls -la /home/bratan/.hermes/state/mnemosyne-sleep-backups//*.gz | wc -l
  - Output: REPORT.md mit Summary + Tabelle
  - KEINE crontab-Änderungen
  - KEINE sudo-Befehle
```

Warum: Ohne explizite READ-ONLY-Angabe versuchen M3 manchmal INSERTs.

### 4. E2E-Verifikation (10-15% des Briefings)

Jede Biene MUSS am Ende selbst testen dass ihr Output existiert und sinnvoll ist.

```
VERIFIZIERE DIREKT IM SCRIPT:
  import os, sys
  pfad = "/home/bratan/.hermes/scripts/memory_health_check.py"
  if not os.path.exists(pfad):
      print("FEHLER: Datei nicht geschrieben", file=sys.stderr)
      sys.exit(1)
  print(f"OK: Datei existiert ({os.path.getsize(pfad)} bytes)")
  
  # Syntax-Check
  import py_compile
  py_compile.compile(pfad, doraise=True)
  print("OK: Syntax-Check bestanden")
```

## Warum diese Briefing-Dichte funktioniert

| Aspekt | Vages Briefing | Dichtes Briefing |
|--------|---------------|-----------------|
| M3 Time-to-first-Write | ~3-5 min (liest erstmal Doku/Web) | ~30-60 sec (hat alles im Context) |
| Iterationen | 3-5 (falsche Annahmen korrigieren) | 1-2 (trifft gleich die richtigen Imports) |
| Phantom-Fix-Wahrscheinlichkeit | Mittel (rät API-Namen) | Niedrig (hat echte Schema-Pfade) |
| Wall-clock total | ~10-30 min | ~2-5 min |

## Validierte Briefing-Templates

### Template: DB-Audit-Skript
```
SCHEMA: <tabelle mit spalten, typen, constraints>
DB-PFADE: <absoluter Pfad>
PFLICHTEN:
  1. <konkreter SQL-Query>
  2. <Integration mit anderem System>
  3. <Report-Format>
CONSTRAINTS:
  READ-ONLY auf DB, KEINE system commands
OUTPUT: <absoluter Pfad>
VERIFIZIERUNG: <py_compile, ls, content-check>
```

### Template: HTML-Dashboard
```
QUELLE: <DB/API-Pfad/e>
STRUKTUR: <CSS, JS-Lib, Sektionen (mindestens N)>
SEKTIONEN:
  - <Section 1>: <was zeigt sie, welche Query>
  - <Section 2>: <was zeigt sie, welche Query>
  - ...
CONSTRAINTS:
  - Kein externes CSS/JS laden (alles inline)
  - Responsive: dark/light theme
OUTPUT: <absoluter Pfad>
```

### Template: Sync-Engine
```
QUELLE: <Datenbankpfad>
ZIEL: <Dateipfad>
FORMAT: <Markdown/YAML/JSON-Struktur>
CONSTRAINTS:
  - Idempotent (wiederholbar)
  - Keine Datenveränderung in der Quelle (read-only lesen)
  - Richtung: db_to_md / md_to_db / bidirektional
VERIFIZIERUNG: <Beispiel-Output aus dem File lesen>
```

## Baseline-Performance

| Skript-Typ | LOC | Briefing-Länge | M3-Zeit | Iterationen |
|-----------|-----|----------------|---------|-------------|
| DB-Health-Check | ~350 Z | ~60 Zeilen | ~90s | 1 |
| HTML-Dashboard | ~600 Z | ~70 Zeilen | ~120s | 1 |
| Link-Validator | ~320 Z | ~50 Zeilen | ~80s | 1 |
| Sync-Engine | ~375 Z | ~55 Zeilen | ~100s | 1 |
| WebDAV-Processor | ~535 Z | ~65 Zeilen | ~130s | 1 |

**Mittelwert:** 4 Skripte × ~450 LOC = ~3 min wall-clock bei 4+ parallelen M3.
+ ~30-60s Queen-Verifikation (Tier 1-3).
