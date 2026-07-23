# Mnemosyne Read-only Audit — SQL Recipes & Smoke-Test Patterns

Companion to `SKILL.md § Read-only Mnemosyne Audit Recipe`. Full query library for the 6-schichten-standard-audit. **All queries are read-only.** Source session: 2026-07-10 Phase-1-Audit.

## Pre-Flight: DB-Pfad & Locks

```bash
DB=~/.hermes/mnemosyne/data/mnemosyne.db
ls -la "$DB" "$DB-wal" "$DB-shm" 2>&1     # WAL aktiv = jemand schreibt
sqlite3 "$DB" "PRAGMA quick_check;"        # ok | DB corrupted
sqlite3 "$DB" "PRAGMA integrity_check;"    # ok | drt/rtree/… mismatches
```

`~/.hermes/hermes-agent/venv/bin/mnemosyne verify --quick` ist die bequeme Variante — macht dasselbe.

## Schicht 1 — Stats + Diagnose

```bash
~/.hermes/hermes-agent/venv/bin/mnemosyne stats
~/.hermes/hermes-agent/venv/bin/mnemosyne diagnose
```

**Erwartete Werte (2026-07-10):** working ~3.300, episodic ~480, facts ~2.800, triples ~36, embedding-vectors ~17 (int8 backend). `Checks passed: 7/25` ist normal — die übrigen 18 sind optional-checks (z.B. vec0-extension nicht geladen, kein Problem).

## Schicht 2 — Live-Counts pro Tabelle

```sql
-- Read-only count-snapshot
SELECT 'working_memory' tbl, COUNT(*) n FROM working_memory
UNION ALL SELECT 'episodic_memory', COUNT(*) FROM episodic_memory
UNION ALL SELECT 'memoria_facts', COUNT(*) FROM memoria_facts
UNION ALL SELECT 'memoria_instructions', COUNT(*) FROM memoria_instructions
UNION ALL SELECT 'memoria_preferences', COUNT(*) FROM memoria_preferences
UNION ALL SELECT 'memoria_kg', COUNT(*) FROM memoria_kg
UNION ALL SELECT 'triples', COUNT(*) FROM triples
UNION ALL SELECT 'graph_edges', COUNT(*) FROM graph_edges
UNION ALL SELECT 'scratchpad', COUNT(*) FROM scratchpad
UNION ALL SELECT 'memory_embeddings', COUNT(*) FROM memory_embeddings
UNION ALL SELECT 'memories_root', COUNT(*) FROM memories;
```

**Pitfall:** Der `memories`-Root-Table hat nur 4–10 Einträge — das ist NICHT der Working-Memory! Working-Memory lebt in BEAM `working_memory`. Wer zum ersten Mal per `sqlite3` connectet und nur 4 sieht, denkt die DB sei kaputt. Ist sie nicht.

## Schicht 3 — Importance-Histogramm (working)

**Der wichtigste Health-Indikator.** Zeigt sofort, wieviel Noise vs. Gold im Working-Tier liegt.

```sql
-- Importance-Verteilung (0.1-Schritte)
SELECT
  ROUND(importance, 1) AS imp_bucket,
  COUNT(*)              AS n,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM working_memory
WHERE valid_until IS NULL   -- soft-deleted auslassen
GROUP BY ROUND(importance, 1)
ORDER BY imp_bucket DESC;
```

**Realistisches Ergebnis (2026-07-10):**

| Imp-Bucket | n | % |
|---|---|---|
| 0.95+ | 124 | 3.8 % |
| 0.85 | 171 | 5.2 % |
| 0.70 | 66 | 2.0 % |
| 0.60 | 21 | 0.6 % |
| 0.50 | 33 | 1.0 % |
| 0.40 | 4 | 0.1 % |
| **0.30** | **1.378** | **41.9 %** |
| **0.20** | **1.493** | **45.4 %** |
| 0.10 | 1 | 0.0 % |

→ **87 % aller Working-Einträge haben imp ≤ 0.30** = reiner Noise. Das ist der Cleanup-Hebel.

**Symmetrisch für episodic_memory:**

```sql
SELECT tier, COUNT(*), ROUND(AVG(importance), 3)
FROM episodic_memory
GROUP BY tier;
-- 2026-07-10: tier=1 → 453, tier=2 → 26. Tier-3 = 0.
-- tier1_to_tier2 = 26 in einer Session = Tier-Degradation hat wieder angefangen.
```

## Schicht 4 — Konsolidierungs-Health

```sql
-- Unconsolidated working
SELECT
  COUNT(*) FILTER (WHERE consolidated_at IS NULL) AS unconsolidated,
  COUNT(*) FILTER (WHERE consolidated_at IS NOT NULL) AS consolidated,
  COUNT(*) AS total,
  MIN(created_at) FILTER (WHERE consolidated_at IS NULL) AS oldest_uncons
FROM working_memory;

-- Tier-Wanderung aus letztem Sleep-Log
-- tail -50 ~/.hermes/logs/mnemosyne-sleep.log | grep tier1_to_tier2
```

**Healthy:** unconsolidated ≤ 5 % von total, oldest_uncons ≤ 2 Tage alt, Tier-Wanderung > 0 in mindestens einer Session pro Woche (sonst stagniert das System).

## Schicht 5 — Recall-Smoke-Test (4 Queries)

```bash
# 1. Setup-Frage (sollte Setup-Wissen finden)
~/.hermes/hermes-agent/venv/bin/mnemosyne recall "Hermes Agent Setup" 5

# 2. User-Modell-Frage (sollte Identity/Stil-Memory finden)
~/.hermes/hermes-agent/venv/bin/mnemosyne recall "Basti Vorlieben Stil" 5

# 3. Pattern-Frage (sollte Pattern-/Verfahrens-Memory finden)
~/.hermes/hermes-agent/venv/bin/mnemosyne recall "Queen Bee Schwarm Dispatch" 3

# 4. Scratchpad-Check (eigene Inspektion)
sqlite3 ~/.hermes/mnemosyne/data/mnemosyne.db "SELECT id, created_at, substr(content,1,100) FROM scratchpad ORDER BY created_at DESC LIMIT 10;"
```

**Auswertungs-Heuristik:**

| Smoke-Test | Score-Spread | Diagnose |
|---|---|---|
| Top-Hit ≥ 0.5 | ≥ 0.2 zum #5 | Gute Kalibrierung, Top-Hit wirklich dominant |
| Top-Hit ≥ 0.4 | < 0.2 | Treffer relevant, aber mehrere konkurrierende — Frage evtl. zu breit |
| Alle Hits < 0.4 | egal | Off-topic-Frage oder Embedding-Reichweite zu eng (siehe § Pitfalls) |
| Recall-Findung 0 Hits bei `< 5` | n/a | Frage vermutlich im falschen Namespace (Tag-Prefix-Mismatch) |

**Bekanntes Problem 2026-07-10:** Identity-Frage „Basti Vorlieben Stil" liefert nur 1/5 Hits, weil die meisten working-Memories mit Tag-Prefix (`[task]`, `[project]`, `[identity]`) gespeichert sind und die Embedding-Suche auf den Tag-Prefix matcht. **Workaround für Audits:** zusätzlich `memoria_preferences` direkt abfragen:

```sql
-- memoria_preferences enthalten die User-Vorlieben explizit
SELECT substr(content, 1, 200) FROM memoria_preferences ORDER BY id DESC LIMIT 20;
```

## Schicht 6 — Graph-Konsistenz (triples ↔ working)

```sql
-- Top-Subjects im Triple-Graph (wissen, was wir über Wen wissen)
SELECT subject, COUNT(*) AS n
FROM triples
GROUP BY subject
ORDER BY n DESC
LIMIT 20;

-- User-bezogene Triples
SELECT subject, predicate, object
FROM triples
WHERE LOWER(subject) LIKE '%user%'
   OR LOWER(subject) LIKE '%basti%'
   OR LOWER(subject) LIKE '%bratan%';

-- KG-Filter „was User NICHT will" (häufigster Predikat-Typ)
SELECT COUNT(*) FROM memoria_kg WHERE predicate = 'negation';
```

**Widerspruch-Cross-Check:** Suche Triples zu einem Pfad/Preference-Statement und prüfe, ob ein hoch-importantes Working-Memory (`imp ≥ 0.85`) das Gegenteil sagt. Realistisches Beispiel 2026-07-10:

```sql
-- Triple behauptet: user:bratan hat-obsidian-vault-unter ~/Dokumente/...
SELECT subject, predicate, object
FROM triples WHERE subject = 'user:bratan' AND predicate LIKE '%vault%';

-- Working imp=0.95 verbietet Schreibtisch/Dokumente-Arbeit
SELECT id, importance, substr(content,1,180)
FROM working_memory
WHERE importance >= 0.85
  AND (content LIKE '%Schreibtisch%' OR content LIKE '%Documents%')
  AND content LIKE '%Workspace%';
```

Wenn beide vorhanden sind: **Widerspruch erkannt** → in der Audit-Sektion „Lösch-/Konsolidierungs-Druck" auflisten mit „mögliche Auflösung: Workspace-Regel nur für Schreib-Aktivitäten, nicht für Lese-Pfade" o.ä.

## Bulk-Cleanup-Kandidaten identifizieren (ohne Schreiben)

```sql
-- Was würde der monatliche Cleanup treffen?
SELECT COUNT(*) AS candidates
FROM working_memory
WHERE valid_until IS NULL
  AND importance < 0.5
  AND recall_count = 0;

-- High-Recall-Check: sind die Candidates wirklich ungenutzt?
SELECT id, importance, recall_count, last_recalled
FROM working_memory
WHERE valid_until IS NULL
  AND importance < 0.5
ORDER BY recall_count DESC
LIMIT 5;   -- zeigt die Top-Ausreißer mit recall>0 — die NICHT gepurgt werden sollten
```

## Recall-High-Hits (für „was wissen wir über X")

```sql
-- High-recall working memories (oft die wertvollsten)
SELECT id, recall_count, last_recalled,
       substr(content, 1, 180) AS excerpt
FROM working_memory
WHERE valid_until IS NULL
  AND recall_count >= 5
ORDER BY recall_count DESC
LIMIT 10;
```

## Episodic High-Importance (konsolidiertes Wissen)

```sql
SELECT id, tier, importance, recall_count,
       substr(content, 1, 180) AS excerpt
FROM episodic_memory
WHERE importance >= 0.7
ORDER BY importance DESC, recall_count DESC
LIMIT 10;
```

## memoria_facts — was sind die dominierenden Fact-Typen?

```sql
SELECT fact_type, COUNT(*) AS n,
       COUNT(DISTINCT key) AS distinct_keys
FROM memoria_facts
GROUP BY fact_type
ORDER BY n DESC;
-- Realistisch: metric (1100+), date (900+), sequence (360), version (300)
-- fact_type 'sequence' sind oft Stop-Word-Keys: dann, danach, als, zuerst

-- Top-Keys (zeigt welche Konzepte am häufigsten extrahiert wurden)
SELECT key, COUNT(*) AS n, MAX(importance) AS max_imp
FROM memoria_facts
GROUP BY key
ORDER BY n DESC
LIMIT 15;
```

**Anti-Pattern:** Wenn Keys wie `dann`, `danach`, `als`, `zuerst` in den Top-15 auftauchen, sind das Wortfragmente, keine atomaren Fakten — die Extraction-Pipeline hat ein Mindestlängen-Problem. Im Audit als „memoria_facts Key-Normalisierung nötig" vermerken.

## Session-Output Vorlage (2026-07-10 — als Referenz)

```markdown
## Tier-Verteilung
| Tier | Count | Avg Importance | Avg Recall | Total Chars |
| working_memory | 3.291 | 0.317 | 1.81 | 1.633.348 |
| episodic_memory | 479 | 0.614 | 2.06 | 1.612.470 |
| memoria_facts | 2.770 | – | – | – |
| triples / KG | 36 | – | – | – |
| scratchpad | 6 | – | – | – |

## Importance-Histogramm
(noise=87 %, gold=9 %)

## Recall-Test (4 Abfragen)
(Score-Spread, Top-Hit, Diagnose)

## High-Importance Memories (Top 5)
(ID, Imp, Recall, Inhalt-Kern, Gültigkeit 2026-07?)

## Graf-Wissens-Konsistenz
(Top-Subjects, KG-Drift, Widersprüche)

## Lösch-/Konsolidierungs-Druck
(Bullet-Liste)

## 5 SOLL-Verbesserungs-Hebel
(Nummeriert, mit Fix-Pfad)
```

## Longitudinal Analysis (Daily Trends)

For activity tracking — "how much was the system used each day" or "is the memory growing too fast":

```sql
-- Working-Memory per Tag (neue Einträge)
SELECT substr(created_at,1,10) AS tag, COUNT(*) AS new_wm
FROM working_memory
WHERE substr(created_at,1,10) >= '2026-07-01'
GROUP BY substr(created_at,1,10)
ORDER BY tag;

-- Episodic per Tag
SELECT substr(created_at,1,10) AS tag, COUNT(*) AS new_ep
FROM episodic_memory
WHERE substr(created_at,1,10) >= '2026-07-01'
GROUP BY substr(created_at,1,10)
ORDER BY tag;

-- Embeddings per Tag
SELECT substr(created_at,1,10) AS tag, COUNT(*) AS new_emb
FROM memory_embeddings
WHERE substr(created_at,1,10) >= '2026-07-01'
GROUP BY substr(created_at,1,10)
ORDER BY tag;
```

**Deutung:** 100–200 WM/Tag = normale Session-Dichte. 300+ = Bulk-Import oder Cron-lastiger Tag. Embeddings wachsen meist parallel zu WM (1:1). Episodic wächst nur an Sleep-Tagen.

## Source Analysis (was füllt die DB)

```sql
-- Top-Quellen (alive working memories)
SELECT source, COUNT(*) AS n
FROM working_memory
WHERE valid_until IS NULL
GROUP BY source
ORDER BY n DESC
LIMIT 15;

-- Realistisch 2026-07-11:
-- conversation (687) | fact (83) | tool (48) | self-improving (42) | task (33) | user (27) | insight (24) | builtin_memory_memory (20)
```

Wenn `conversation` > 80 % dominiert: viel Session-Echo ohne echten Informationswert → Cleanup-Kandidat.

## Consolidation-Log als strukturierte Datenquelle

Statt `grep` auf Text-Logs: SQLite `consolidation_log` hat Sessions, Items und Summaries:

```sql
-- Per-Day Consolidation Activity
SELECT substr(created_at,1,10) AS tag,
       COUNT(*) AS sleep_runs,
       SUM(items_consolidated) AS items,
       COUNT(CASE WHEN summary_preview IS NOT NULL AND summary_preview != '' THEN 1 END) AS summaries
FROM consolidation_log
WHERE substr(created_at,1,10) >= '2026-07-01'
GROUP BY substr(created_at,1,10)
ORDER BY tag;

-- Letzte N Einträge mit Session-ID und Preview
SELECT id, session_id, items_consolidated,
       substr(summary_preview,1,90) AS preview,
       created_at
FROM consolidation_log
ORDER BY id DESC LIMIT 12;

-- Schema (für Ad-hoc-Queries):
-- id INTEGER PRIMARY KEY AUTOINCREMENT
-- session_id TEXT
-- items_consolidated INTEGER
-- summary_preview TEXT
-- created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Schema:** Keine `timestamp`-Spalte trotz des Namens — `created_at` ist der relevante Zeitstempel.

## Veracity-Blindspot Analyse

Ein hoher Anteil `veracity=unknown` bedeutet: viele Memories wurden über einen API-Pfad geschrieben der keine `veracity` setzt (z.B. via `_handle_store` mit Default):

```sql
-- Veracity-Verteilung bei alive Memories
SELECT veracity, COUNT(*) AS n,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
FROM working_memory
WHERE valid_until IS NULL
GROUP BY veracity
ORDER BY n DESC;

-- Blinde Flecken: unknown > 7 Tage alt
SELECT COUNT(*) AS unknown_stale_bloat
FROM working_memory
WHERE veracity='unknown' AND valid_until IS NULL
  AND substr(created_at,1,10) < date('now', '-7 days');

-- Realistisch 2026-07-11: 793 unknown, 74 % aller alive = Cleanup-Signal
```

## Tier-Degradation direkt via SQL

Statt Logs zu greppen — `episodic_memory` hat eine `degraded_at`-Spalte:

```sql
-- Wurde degradiert in den letzten N Tagen?
SELECT id, tier, substr(degraded_at,1,16) AS degraded_when,
       substr(content,1,120) AS excerpt
FROM episodic_memory
WHERE degraded_at IS NOT NULL
  AND substr(degraded_at,1,10) >= date('now', '-14 days')
ORDER BY degraded_at DESC;

-- Tier-2 Bestand (was ist aktuell degradiert)
SELECT id, tier, importance,
       substr(content,1,120) AS excerpt
FROM episodic_memory
WHERE tier = 2
  AND (degraded_at IS NULL OR degraded_at = '')
ORDER BY importance DESC;
```

**Healthy:** Degradation passiert vereinzelt (1–3 pro Session). 26 Demotions in einer Session (wie am 2026-07-10) zeigt eine Bulk-Reorganisation — das ist normal, kein Fehler.

## Pitfalls (alle Audit-Phasen)

1. **WAL-File löschen = Datenverlust.** Nie `.db-wal` oder `.db-shm` per `rm` anfassen.
2. **`mnemosyne sleep` während Audit = vermurkste Stats.** Falls versehentlich getriggert: nächste 60s kein verify, Recall evtl. mit Race-Condition.
3. **„Mnemosyne hat 4 Memories"** siehe Schicht 2 — ist BEAM-Verwirrung, kein Fehler.
4. **DB-Datei ist read-write-gesperrt während Hermes-Agent-Loop.** Audit funktioniert nur, wenn Hermes idle ist oder im WAL-Modus parallel lesen kann (Default).
5. **Triple-Edges (`graph_edges`) ohne `source_id`-Spalte** — bei Schema-Drift das `.schema graph_edges` zuerst checken, dann Queries bauen.
6. **`memoria_kg.entity_type` existiert nicht** (im Gegensatz zu `fact_type` bei memoria_facts) — nicht blind Spalten referenzieren.