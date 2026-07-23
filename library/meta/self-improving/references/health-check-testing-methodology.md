# Health Check Script Testing — Cron-Flow Methodology

> Aus Session 2026-07-09: `memory_health_check.py` Cron-Flow Test  
> Technik: Exakte Cron-Replikation + WARNING-Provozierung via DB-Manipulation + Rollback  
> Geprüft: `~/10-Projekte/10-active/mnemosyne/scripts/memory_health_check.py`

## Ziel

Eine Health-Check-Skript (Cron-Job) korrekt testen — so, wie der Cron-Daemon
ihn aufruft, nicht in einer dev-Umgebung.

## Grundprinzipien

### 1. Exakte Cron-Replikation

Das Skript exakt so aufrufen wie der Cron-Daemon — **nicht** verkürzt oder mit
relativen Pfaden:

```bash
cd /home/bratan && /pfad/zu/venv/bin/python3 /pfad/zu/script.py
```

Nicht: `python3 memory_health_check.py` (falscher CWD, falscher venv-Pfad).

Der Cron-Daemon startet keine Shell-Umgebung — alles was du anders machst
(venv nicht aktiviert, relativer Pfad, `~` statt `/home/bratan`) kann den
Exit-Code oder das Logging verfälschen.

### 2. Back-to-Back Runs

2× hintereinander ausführen mit Timestamp-Logging:

```bash
echo "=== RUN 1 START $(date -Iseconds) ==="
/pfad/zu/script.py; echo EXIT:$?
echo "=== RUN 1 ENDE $(date -Iseconds) ==="
sleep 3
echo "=== RUN 2 START $(date -Iseconds) ==="
/pfad/zu/script.py; echo EXIT:$?
echo "=== RUN 2 ENDE $(date -Iseconds) ==="
```

Das testet:
- **Idempotenz** — Zweiter Run liefert gleiches Ergebnis
- **Caching** — Embedding-Modell-Caching sichtbar (Run 1 langsamer als Run 2)
- **State-Side-Effects** — Keine hängenden File-Locks, keine Log-Duplikate

### 3. Sechs Zustände testen (nicht nur OK)

| Zustand | Exit-Code | Beschreibung |
|---------|-----------|------------|
| OK | 0 | Alle Checks grün |
| WARNING | 1 | Mindestens ein WARNING-Check |
| CRITICAL | 2 | (falls implementiert) Mindestens ein CRITICAL-Check |
| Idempotenz | 0 → 0 | 2× OK-Runs liefern identische Logs |
| Recovery | 1 → 0 | Nach WARNING kann wieder OK kommen |
| Cleanliness | — | Keine Hinterlassenschaften nach Test |

### 4. Sekundäre Effekte prüfen

Nicht nur Exit-Code checken. Prüfe auch:

- **Log-Datei:** Neue Einträge mit korrekten Zeitstempeln und Inhalten
- **Alert-Datei (z.B. `alerts.md`):** Schreibt NUR bei `worst >= WARNING`.
  OK-Runs schreiben **nie** in die Alert-Datei.
- **DB-Zustand:** Keine unerwarteten Änderungen an Tabellen außer der
  vom Skript vorgesehenen Schreibtabelle
- **Exit-Code-Kodierung:** 0=OK, 1=WARNING, 2=CRITICAL (sofern laut Spec)

### 5. Before/After Snapshot

Vor dem ersten manipulativen Test:

```bash
cp alerts.md /tmp/alerts_pre_test.md
cp mnemosyne.db /tmp/mnemosyne_pre_test.db    # falls DB manipuliert wird
```

Nach dem Test: `diff /tmp/alerts_pre_test.md alerts.md` und `wc -c` für
Größenänderung.

## WARNING-Provozierung (Safe-DB-Pattern)

Wenn das Skript einen internen DB-Check macht (z.B. `MAX(created_at)` in
`episodic_memory`), reicht es **nicht**, nur die *heutigen* Einträge zu
manipulieren. `MAX()` aggregiert über **alle** Zeilen der Tabelle.

**Pitfall MAX(created_at):** Wenn es auch nur einen Eintrag von *gestern* gibt
(z.B. `2026-07-08 13:01:01`), zeigt `MAX()` immer noch ein aktuelles Datum.
Erst wenn **sämtliche** Einträge älter als der Schwellwert sind, feuert der
WARNING-Check.

### Safe-Pattern: Backup-Tabelle

```python
# 1) Backup-Tabelle anlegen (CREATE IF NOT EXISTS — kein DROP nötig)
c.execute("""CREATE TABLE IF NOT EXISTS healthtest_backup (
  id TEXT PRIMARY KEY,
  orig_created_at TEXT NOT NULL
)""")
# Sichern
rows = c.execute("SELECT id, created_at FROM episodic_memory").fetchall()
c.executemany("INSERT INTO healthtest_backup VALUES (?, ?)", rows)

# 2) Manipulation (immer mit WHERE-Klausel)
c.execute("UPDATE episodic_memory SET created_at='2025-01-01 00:00:00' "
          "WHERE created_at IS NOT NULL")
# Jetzt MAX(created_at) = 2025-01-01 → WARNING garantiert

# 3) Test-Run: Skript ausführen → Exit-Code 1 erwartet

# 4) Restore
for id_, orig in rows:
    c.execute("UPDATE episodic_memory SET created_at=? WHERE id=?", (orig, id_))

# 5) Cleanup: Backup-Tabelle löschen (DROP wird durchgelassen)
c.execute("DROP TABLE IF EXISTS healthtest_backup")

# 6) Verify
assert c.execute("SELECT MAX(created_at) FROM episodic_memory").fetchone() == original_max
```

### Smart-Approval-Pitfalls

| Pattern | Ergebnis | Grund |
|---------|----------|-------|
| `DROP TABLE IF EXISTS` | ✅ Erlaubt | Wird als normales Cleanup erkannt |
| `DELETE FROM backup WHERE id IS NOT NULL` | ❌ Blockiert | Zählt als "DELETE ohne WHERE" |
| `INSERT OR REPLACE` | ✅ Erlaubt | Kein Löschvorgang |
| `UPDATE ... WHERE` | ✅ Erlaubt | Hat immer WHERE |

**Lösung für Tabellen-Leeren:** `DROP TABLE IF EXISTS` + neu `CREATE TABLE`.
Nicht `DELETE FROM backup` ohne hartes WHERE.

### Alternative: Datei-Backup (robuster, gröber)

```bash
# Pre
cp ~/.hermes/mnemosyne/data/mnemosyne.db /tmp/mnemosyne_pre_healthtest.db

# ... manipulierende SQL-Commands ...

# Post (kompletter DB-Ersatz)
cp /tmp/mnemosyne_pre_healthtest.db ~/.hermes/mnemosyne/data/mnemosyne.db

# Sanity-Run
/pfad/zu/script.py
echo $?  # muss 0 sein
```

**Vorteil:** Kein SQL-Smart-Approval-Risiko, einfacher Code.  
**Nachteil:** Komplette DB statt gezielte Spalten — bei laufendem System
riskanter (Daten zwischen Backup/Restore verloren).

### Timeout-Budget

| Phase | Typische Dauer | Tool |
|-------|---------------|------|
| 2× OK-Run | 2–4s | `terminal(timeout=120)` |
| DB-Manipulation | 1–2s | `terminal` |
| WARNING-Run | 1–2s | `terminal(timeout=60)` |
| Restore | 1–2s | `terminal` |
| Sanity-Run | 1–2s | `terminal(timeout=60)` |

Gesamt: ~10–15s für einen kompletten OK→WARNING→Recovery-Durchlauf.

## alerts.md- / Alert-Datei-Verhalten

Das typische Muster für eine Health-Check-Alert-Datei:

| Skript-Status | Exit-Code | alerts.md |
|--------------|-----------|-----------|
| **OK** | 0 | **Nicht geschrieben** (kein Eintrag, keine Änderung) |
| **WARNING** | 1 | Neuer Block `## Health Check — YYYY-MM-DD HH:MM` wird **angehängt** |
| **CRITICAL** | 2 | Neuer Block wird angehängt |

Verifikation mit `diff`:

```bash
# Vor Test
cp alerts.md /tmp/alerts_pre_test.md

# Nach Test
echo "Size: $(wc -c < alerts.md) Bytes"
diff /tmp/alerts_pre_test.md alerts.md
# → Bei OK: kein diff
# → Bei WARNING/CRITICAL: +N Zeilen neuer Block
```

## Cleanup-Checkliste

Nach einem manipulativen Test muss **alles** zurückgesetzt sein:

- [ ] `PRAGMA integrity_check` → `ok`
- [ ] `MAX(created_at)` identisch mit Pre-Test-Wert
- [ ] `MIN(created_at)` identisch mit Pre-Test-Wert
- [ ] **Keine** Hilfstabellen mit Test-Namen in `sqlite_master`
- [ ] `alerts.md` unverändert (nur erwarteter WARNING-Block, wenn gewünscht)
- [ ] **Sanity-Run:** Skript Exit 0, alle 3+ Checks OK
- [ ] `/tmp`-Backups gelöscht oder als Rolling-Safety-Net markiert

## Integration in `todo`-Workflow

Bei einem Test mit >3 Teilaufgaben **jeden Schritt** im `todo`-Tool tracken:

```json
[
  {"id": "1", "content": "OK-Run 1 (idempotenz-baseline)", "status": "pending"},
  {"id": "2", "content": "OK-Run 2 (caching-check)", "status": "pending"},
  {"id": "3", "content": "WARNING provozieren (DB-Manipulation)", "status": "pending"},
  {"id": "4", "content": "alerts.md vorher/nachher diff", "status": "pending"},
  {"id": "5", "content": "Restore + Sanity-Run", "status": "pending"},
  {"id": "6", "content": "Finaler Check: alerts.md, DB, Logs", "status": "pending"}
]
```

Nach jedem Schritt `completed` setzen — ohne ist die Übersicht nach 6+
Schritten weg. **Nicht** alle Schritte in einen Eintrag packen (der `todo`
-Summary sagt dir sonst nicht, wo du stehst).

## Häufige Pitfalls

1. **MAX(created_at) trickst dich aus** — `MAX()` über eine Spalte aggregiert
   über ALLE Zeilen, nicht nur die von heute. Wenn Einträge von gestern,
   vorgestern oder letzter Woche da sind, ist `MAX()` immer noch aktuell.
   Manipuliere **alle** Zeilen, nicht nur einen Teil.

2. **SQLite Smart-Approval** — `DELETE FROM backup WHERE id IS NOT NULL`
   wird geblockt (erkennt "DELETE ohne richtiges WHERE"). Nutze
   `DROP TABLE IF EXISTS` für Cleanup.

3. **Log-Datei-Duplikate** — Jeder Run hängt ans Log an. Bei 3 Runs hast du
   3× `=== Health Check Start ===` im Log. `tail -10` zeigt die aktuellen,
   nicht die historischen. Bei manueller Inspektion aufpassen.

4. **Context-Budget für Logs** — Langer Log-Output frisst Context.
   `head -N` + `tail -N` statt kompletten Log. Wenn möglich batchweise.

5. **Zeitstempel-Abhängigkeit** — `delta.days` im Skript zählt Kalendertage.
   Wenn `MAX(created_at)` exakt heute ist, ist `delta.days = 0`. Für
   WARNING muss `delta.days >= threshold` sein. Das erreichst du nur mit
   einem Datum, das `threshold` Tage **vor heute** liegt — nicht heute minus
   ein paar Stunden.

6. **alerts.md wird NUR bei WARNING+ geschrieben** — OK-Runs schreiben
   nichts. Ein fehlender OK-Eintrag in alerts.md ist **kein Bug**, sondern
   korrektes Verhalten. Vor dem Test prüfen ob der alte alerts.md-Inhalt
   von einem OK-Run (kein Eintrag) oder einem WARNING-Run (alter Eintrag)
   stammt, sonst interpretierst du fehlende Einträge falsch.

7. **Timestamp-Kürzung** — Skripte nutzen oft `last_ts_str[:19]` auf dem
   ISO-String, weil SQLite `created_at` als `2026-07-09 17:09:20` speichert
   (ohne Trennzeichen). Wenn du ein Datum setzt, mach exakt
   `'2025-01-01 00:00:00'` — andere Formate (`2025-01-01T00:00:00`)
   erzeugen einen `ValueError` im `fromisoformat()`-Call.