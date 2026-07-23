# Queen Verification Pattern — Post-Delegation Snapshot Audit

**Validated:** 2026-07-09 (3 parallel M3 Bienen, ~3 Min Wall-Clock, 5 Findings)
**Domain:** Cron-Flow-Testing (health-check, audit-dashboard, sync-engine)
**Queen-Modell:** DeepSeek V4 Flash (Parent-Modell der Session)

## TL;DR

```
Bienen retour → Queen:
  1. Snapshot vergleichen (Logs, DB, Files)
  2. Claims gegen Dateisystem prüfen
  3. Cross-Phase-Effekte checken
  4. Dinge finden die keine Biene erwähnt hat
```

## Warum Tier 4 nötig ist

Tier 1-3 (Status, Content, Cross-Check) prüfen ob die Biene *das getan hat was sie sagt*.
Tier 4 (Snapshot Audit) prüft ob die Biene *das NICHT getan hat was sie nicht sagen würde*.

**Konkreter Fall (2026-07-09):**
- Biene 1 berichtet: "WARNING provoziert, alerts.md von 206 auf 415 Bytes erweitert, Cleanup OK"
- Queen checkt: alerts.md = **0 Bytes / nicht existent**
- Was passiert ist: Biene hat alerts.md gelöscht (Cleanup hat nur DB restored, nicht alerts.md)
- **Nur Tier 4 findet das** — Tier 1-3 bestätigen Biene 1's Claims, aber der Side-Effect bleibt unsichtbar

## Konkrete Kommandos

### Log-Aging — Welcher Cron läuft wirklich?

```bash
# Alle Logs mit mtime + size
stat -c '%y %s %n' /home/bratan/logs/*.log

# Interpretation:
# memory-health.log:      5483 bytes — health-check läuft alle 5/30 Min ✓
# mnemosyne-sleep.log:    5105 bytes — sleep-cron läuft 02:30 ✓
# nextcloud-processor.log: 4984 bytes — NC-cron läuft alle 2 Min ✓
# sync-engine.log:          561 bytes — sync läuft alle 5 Min ✓
# memory-audit.log:    FEHLT — audit-cron `30 * * * *` hat noch nicht getriggert
```

**Merke:** Fehlendes Log ≠ Bug. Wenn Cron `30 * * * *` um 19:52 installiert wurde, ist um 20:00 noch kein Log da. Nächster Trigger: 20:30.

### mtime-Vergleich — Hat Skip wirklich geskippt?

```bash
# Vor Run
stat -c '%Y %n' /home/bratan/.hermes/dashboards/memory_audit.html > /tmp/mtime_before.txt
# Nach Run  
stat -c '%Y %n' /home/bratan/.hermes/dashboards/memory_audit.html > /tmp/mtime_after.txt
# Vergleich
diff /tmp/mtime_before.txt /tmp/mtime_after.txt
# Leer = Skip ✅
# Unterschied = Regenerate ✅
```

**Wichtig:** `sleep 2` zwischen Vorher und Nachher einbauen, sonst ist mtime in derselben Sekunde identisch (falscher Positiv-Skip).

### DB-Content — Unbeabsichtigte Änderungen

```bash
# Vorher
sqlite3 /path/to/db "SELECT COUNT(*), MIN(created_at), MAX(created_at) FROM episodic_memory"

# Nach Test-Runs (Biene provoziert WARNING)
# COUNT sollte gleich sein, MIN/MAX identisch

# PRAGMA integrity_check — DB nicht korrupt?
sqlite3 /path/to/db "PRAGMA integrity_check; PRAGMA quick_check"
# Erwartet: "ok"
```

### File-Existenz — Gelöscht oder verschoben?

```bash
# Vor Dispatch merken: welche Dateien existieren?
ls -la /path/to/alerts.md /path/to/lock /path/to/output.html 2>&1

# Nach Verifikation: gleiches Kommando → vergleichen
# Unterschied = Side-Effect den keine Biene gemeldet hat
```

### Cron-Accuracy — Läuft wie spezifiziert?

```bash
# Was sagt die Crontab?
crontab -l | grep -v '^#'
# Was sagt die Platte? -> Log-mtimes
stat -c '%y %n' /home/bratan/logs/*.log

# Wenn Cron alle 5 Min feuern soll aber Log-mtime >10 Min alt ist: Problem
# Wenn Cron `30 *` ist und Log fehlt: erwartet, nächster Trigger abwarten
```

## Komplettes Session-Beispiel (2026-07-09)

### Setup
```
3 Bienen dispatched (parallel):
  Biene 1: memory_health_check.py — Cron-Flow testen + WARNING provozieren
  Biene 2: memory_audit_dashboard.py — Skip-Logik testen (4 Runs)
  Biene 3: sync_engine.py — Full Roundtrip (db→md→edit→md→db→verify→cleanup)
  
Dauer: ~2 Min 18s
Queen-Modell: DeepSeek V4 Flash
Subagent-Modell: MiniMax-M3 (geerbt via delegation.model-Pinning)
```

### Queen-Audit (echte Outputs)

```bash
# Schritt 1: Pre-Test Snapshot (VOR Dispatch)
PRE-TEST SNAPSHOT
Logs vorhanden:
  3985  maxclaw-security-audit-LAST.json
  2727  memory-health.log
  5105  mnemosyne-sleep.log
  3560  nextcloud-processor.log
  561   sync-engine.log
Dashboard mtime: 19:52:46, 40328 Bytes
Episodic: 467 Einträge, MAX=2026-07-09 17:09:20
alerts.md: existiert (206 Bytes)
memory-audit.log: FEHLT (erwartet — Cron `30 *` noch nicht gefeuert)

# Schritt 2: Post-Test Audit (NACH Bienen)
```

### 5 Befunde die Queen entdeckt hat

| # | Befund | Severity | Entdeckt durch | Von Biene erwähnt? |
|---|---|---|---|---|
| 1 | **OK, SKIP = 0, 0** — Cron-Monitoring kann Skip nicht von Regenerate unterscheiden | 🔴 Bug | Code-Inspection (Tier 2) + Biene 2's Self-Report erwähnte es als "empfehle Rückfrage" | ⚠️ Ja (als Frage, nicht als Fix) |
| 2 | **memory-audit.log fehlt** — Cron `30 *` hat noch nie gefeuert | 🟡 Erwartet | Log-Aging (Tier 4) | ❌ Nein |
| 3 | **alerts.md gelöscht** — Biene 1's Cleanup hat die Datei entfernt statt nur zu reverten | 🟡 Minor | File-Existenz (Tier 4) | ❌ Nein |
| 4 | **Doppelter Sanity-Block** — Log zeigt 2 identische Sanity-Run-Blöcke | 🟢 Kosmetik | Log-Content (Tier 1) | ❌ Nein |
| 5 | **alerts.md Backup existiert** im /tmp, restorebar | 🟢 Kein Schaden | File-Existenz (Tier 4) | ❌ (Biene erwähnte Backup nicht im Summary) |

### Fixes aus der Queen-Phase

```python
# Fix 1: Exit-Code-Kollision
# In memory_audit_dashboard.py:
OK, SKIP = 0, 0     # ALT — BEIDE 0, Cron kann nicht unterscheiden
OK, SKIP = 0, 75    # NEU — Skip = 75, Cron-Monitor sieht Unterschied

# Fix 2: alerts.md restored
cp /tmp/alerts_pre_healthtest.md ~/Documents/Obsidian/Hermes-Agent/Memory-Review/alerts.md
```

### Lessons

1. **Bienen-Self-Reports sind ~90% korrekt** — aber die 10% Lücke (vergessene Cleanup-Schritte, nicht dokumentierte Side-Effects) findet nur Tier 4
2. **Tier 4 braucht <30 Sekunden** — konkrete `stat` + `sqlite3`-Kommandos, kein langer Code
3. **Nicht alle Befunde sind Bugs** — fehlende Logs können erwartetes Verhalten sein (Cron-Schedule noch nicht erreicht)
4. **Tier 4 als Königin-Audit veröffentlicht** — User sieht "Queen hat X gefunden das Bienen übersehen haben" → Vertrauen in die Orchestrierung steigt
5. **Backup-Protokoll ist kritisch** — ohne `/tmp/alerts_pre_healthtest.md` wäre alerts.md verloren gewesen

## Anti-Patterns

**"Ich vertraue den Bienen"** — Tier 4 überspringen. Folge: Side-Effects bleiben unentdeckt bis der User sie bemerkt.

**"Ich wiederhole die Bienen-Tests"** — Tier 4 bedeutet nicht "alle Bienen-Tests selbst nochmal fahren". Es bedeutet: **unabhängige Metriken** prüfen die keine Biene gemessen hat. mtime, Log-Existenz, DB-Count sind keine Test-Outputs — sie sind Systemzustands-Indikatoren.

**"Ich suche nur nach Fehlern"** — Tier 4 bestätigt auch positive Befunde: "Cron läuft wie spezifiziert", "Sync-Cleanup erfolgreich", "DB-Integrität ok". Beides dokumentieren.