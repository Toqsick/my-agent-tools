# Memory-Hygiene Patterns & Pitfalls (2026-06-30)

Praktische Snippets und Decision-Trees für Mnemosyne-Cleanup. Hauptanlass: 9 Background-Process-Quittungen mit Bash-IOCTL-Diagnose-Lärm in einer Session, die Recalls dominiert haben.

## Quick-Decision-Tree: Was passiert wenn Mnemosyne zu voll wird?

```
Memory-Wachstum erkannt (stats.working.unconsolidated wächst >50/Session)
│
├── Sind es System-Notification-Receipts?  ───► siehe Cleanup-Pattern §1
│   (Background-Quittungen, "Permission granted"-Receipts, AutoConsolidation-Logs)
│
├── Sind es Duplikate vom selben Fakt?       ───► siehe Cleanup-Pattern §2
│   (gleicher content, unterschiedliche IDs aus Whitespace-Varianten)
│
├── Sind es veraltete Cross-Session-Memos?    ───► siehe Cleanup-Pattern §3
│   ("Phase X offen" Recalls die schon done sind)
│
└── Sind es sinnvolle aber low-importance-    ───► siehe Cleanup-Pattern §4
    Fakten? (importance < 0.3 mit viel scope='session')
```

## §1: System-Notification-Receipts cleanupen

**Erkennung:**
```python
mnemosyne_recall(query="IMPORTANT Background process bash IOCTL", limit=20)
# Hohe Anzahl Hits, alle importance 0.30, alle scope='session', alle source='conversation'
```

**Pattern (3 Schritte):**

```python
# STEP 1: Konsolidiert-Memory schreiben — fasst die Episode zusammen
summary_id = mnemosyne_remember(
    content="""Session 2026-06-30 — 9 Background-Process-Quittungen (Server-Start/Stop + SSE-Curl-Tests) erzeugt harmlosen Mnemosyne-Spam.

Alle mit 'bash: Kann die Prozessgruppe des Terminals nicht setzen (-1)' IOCTL-Quirk.

Konsolidiert 2026-06-30T04:50 damit Recalls nicht von Quit-Receipts dominiert werden.

Ursprüngliche proc-IDs:
- proc_2ca76845aef2 (Server npm start)
- proc_93eaef0ef427 (Port 3030 Server)
- proc_13fd862ffa20 (npm run dev)
- proc_dd420bab41ef (Port 3001 SSE-v2 dev)
- proc_9df45836d800 (canary-E2E curl-SSE-Stream)
- proc_b3cbf3d556a7 (sse-live)
- proc_5c756b3d195e (sse-bridge)
- proc_dfeb7c55aca1 (sse-leak)
- proc_294c38c6a58c (sse-long)

Pattern: jeder Background-Test erzeugte ein 0.30-Receipt-Memo + meine 0.20-Bestätigungs-Antwort = 18 redundante Memories aus identischem Diagnose-Lärm.

Lesson für die Zukunft:
- Background-Receipt-Quittungen NICHT als Memory persistieren — sie sind ephemeral
- Antwort-Memos dazu ebenfalls nicht (waren schon 0.20, sollten gar nicht erst gespeichert werden)
- Cross-Reference: hermes-maintenance §13""",
    importance=0.4,
    source='insight',
    scope='session',
    veracity='tool',
    extract_entities=True
)

# STEP 2: Alle Quittungs-Originale + User-Receipt-Memos chainen
for old_id in [user_receipt_ids + assistant_antwort_ids]:
    mnemosyne_invalidate(memory_id=old_id, replacement_id=summary_id)

# STEP 3: Stats checken
stats = mnemosyne_stats()
print(f"Working: {stats['working']['total']} (unconsolidated: {stats['working']['unconsolidated']})")
```

**Erwartetes Ergebnis:** working.total fällt um ~18, consolidated bleibt gleich, keine der invalidierten IDs taucht in `mnemosyne_recall(...)` mehr auf.

## §2: Duplicate-Fakt Detection

**Erkennung:** Wenn der gleiche Fakt zwei Mal mit leicht unterschiedlichem Whitespace (z.B. Newlines) gespeichert wurde, oder nach Recall-Loop mehrmals "remembered" wurde.

```python
# Häufig: gleicher Setup-Fakt mehrfach persistiert
candidates = mnemosyne_recall(query="Arbeit Setup Docker Ubuntu", limit=20)
# Mehrere Einträge mit 80%+ ähnlichem content — pick den neuesten/highest-importance als primary
```

**Pattern:**
```python
# Sortiere nach timestamp DESC, neueste behalten
candidates.sort(key=lambda m: m['timestamp'], reverse=True)
primary_id = candidates[0]['id']
for dup in candidates[1:]:
    if similarity(dup['content'], primary.content) > 0.8:
        mnemosyne_invalidate(memory_id=dup['id'], replacement_id=primary_id)
```

## §3: Veraltete Cross-Session-Memos

**Erkennung:** Mnemosyne sagt "Phase X ist offen", Realität: Phase X war letzte Session done.

```bash
# Reality-Check BEVOR du 2h investierst:
grep -r "Phase X" <repo>/docs/  # zeigt ob Doku schon sagt "done"
git log --oneline --all | grep "Phase X"  # zeigt ob Commits existieren
cat <repo>/dist/server/index.js | head -20  # zeigt aktuellen Code-Stand
```

**Pattern:**
```python
# Mnemosyne-Recall mit "is X already done?"-Frage querchecken
mnemosyne_recall(query="was the implementation done or still open", limit=10)
# Bei widersprüchlichen Recalls: Real-Check gewinnt. Mnemosyne updaten:
mnemosyne_invalidate(memory_id=old_incorrect, replacement_id=new_correct_id)
```

## §4: Low-importance Session-Memos ohne Wert

**Erkennung:** Mnemosyne-Stats zeigen 200+ working_memory Einträge mit importance 0.2-0.3, scope='session'. Recalls liefern hauptsächlich diese.

**Pattern:**
```python
# Bulk-Cleanup: alle importance < 0.3, scope='session', älter als 7 Tage
low_value = mnemosyne_recall(query="", limit=200)  # oldest-first
# Filter per Code: importance < 0.3 AND scope=='session' AND age > 7d
# -> mnemosyne_forget (da kein Replacement-Fakt)
```

**Pitfall:** Bulk-Forget ist destruktiv. Lieber manuell loopen mit `recall()` und einzeln entscheiden, oder Threshold höher (0.4+) um nicht versehentlich wichtige Memos zu killen.

## Mnemosyne-API-Cheat-Sheet

| Action | Wann | Funktion |
|---|---|---|
| Neuer Fakt | Initial-Learn oder Correction | `mnemosyne_remember(content, importance=0.5, ...)` |
| Fakt updaten | Alte Version falsch, neue korrekt | `mnemosyne_invalidate(old_id, replacement_id=new_id)` + `mnemosyne_remember(new)` |
| Fakt löschen ohne Replacement | Komplett unwichtig / Spam | `mnemosyne_forget(memory_id)` |
| Konsolidieren | Working-Memory zu viel | `mnemosyne_sleep(all_sessions=True)` |
| Recallen | Suche nach Fakt | `mnemosyne_recall(query, limit=5, scope='user'/'session'/'project')` |

## Cross-Reference

- `devops/hermes-maintenance` §13 "Memory-Hygiene: System-Receipts NICHT in Memory" — gleiche Lesson aus Session-Perspektive
- Haupt-Skill: `devops/mnemosyne-memory-provider` § "Memory Hygiene: Was NICHT in Mnemosyne speichern"
