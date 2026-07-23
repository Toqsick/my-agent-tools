# Development Pitfalls (ESM/TS, Terminal, Build)

> Extracted from hermes-maintenance SKILL.md Sections 11, 11.1, 11.4, 11.4.1, 11.5.

## dist/ ist stale nach Rebuild — Server-Restart ist PFLICHT (2026-06-30)

**Symptom:** `npm run build` (TSC exit 0), aber `curl /api/canary` returnt `404`. Tests laufen durch, aber neue Routes fehlen.

**Ursache:** `tsc` schreibt nach `dist/`, aber der **laufende Node-Prozess** hat die alten Files in seinem Speicher geladen.

**Fix:**
```bash
pkill -f "node dist/server"
sleep 2
PORT=4321 node dist/server/index.js &
```

**Schnellere Alternative:** `tsx watch src/server/index.ts` statt `tsc -p` + `node dist`.

## Hermes-CLI bash-background IOCTL-Quirk (2026-06-30)

**Symptom:** Foreground-Kommandos die `cmd &; sleep N; kill $!; wait` mischen brechen mit:
```
bash: Kann die Prozessgruppe des Terminals nicht setzen (-1).: Unpassender IOCTL
```

**Workaround für SSE-Tests:**
1. **Background-Prozess** via `terminal(background=true, notify_on_complete=true, command="timeout 15 curl -sN http://localhost:4321/api/events > /tmp/sse-out.log 2>&1")`
2. **Warten** via `process(action='wait', session_id=..., timeout=10)`
3. **Output lesen** via `process(action='log', session_id=...)`
4. **Trigger in eigenem Call**

**Lesson:** Diese Terminal-Umgebung erlaubt Foreground-Background-Mischung nicht stabil. Multi-Step-Prozesse IMMER auf mehrere `terminal()`-Calls aufteilen.

## nohup/setsid/disown Auto-Rejected in Foreground (2026-07-02)

**Symptom:** Du willst `nohup node dist/server/index.js &` oder `setsid some-server &` starten. → Hermes rejected mit Approval-Prompt BEVOR der Befehl startet.

**Verbotene Wrapper in Foreground-Calls:** `nohup`, `disown`, `setsid`, trailing `&`

**Fix:** `terminal(background=true, notify_on_complete=<bool>)` benutzen:
```python
terminal(background=True, notify_on_complete=True,
         command='cd <pkg> && ENV=val node dist/server/index.js')
```

**Readiness-Probe IMMER in separatem `terminal()`-Call** (3-5s nach Start):
```bash
sleep 3
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:<port>/health
```

**Diagnose-Triage bei "Server startet nicht" (3-Schicht):**
1. Hermes Approval-Reject mit "shell-level background wrappers"? → `terminal(background=true)` benutzen
2. Bash-IOCTL-Fehler nach erfolgreichem Background-Start? → Multi-Step auf mehrere Calls aufteilen
3. Server läuft laut `pgrep`, antwortet aber nicht auf Port? → EADDRINUSE oder CORS-Block

## ESM/TS Pitfall-Cluster: 3 Stolpersteine (2026-06-30)

**Pitfall A — `require` ist nicht definiert in ESM:**
```typescript
// ❌ Wirft: ReferenceError: require is not defined
const os = require('node:os') as typeof import('node:os');

// ✅ ESM-Imports oben in der Datei
import os from 'node:os';
```

**Pitfall B — `await` braucht `async`-Context:**
```typescript
// ❌ TS2308: 'await' expressions are only allowed within async functions
function snapshot(): Snapshot {
  ({ DatabaseSync } = await import('node:sqlite') as any);
}

// ✅ async function
async function snapshot(): Promise<Snapshot> {
  ({ DatabaseSync } = await import('node:sqlite') as any);
}
```

**Pitfall C — SQLite3-CLI `ORDER BY 2` ohne Sub-Select wirft:**
```sql
-- ❌ "ORDER BY term out of range"
SELECT COALESCE(source,'(none)') || '|' || COUNT(*) FROM memories GROUP BY source ORDER BY 2 DESC

-- ✅ Sub-Select macht ORDER BY auf echte Spalten referenzierbar
SELECT s || '|' || c FROM (
  SELECT COALESCE(source,'(none)') AS s, COUNT(*) AS c
  FROM memories GROUP BY source ORDER BY c DESC LIMIT 5
)
```

## Chained `patch()`-Calls auf derselben Datei (2026-06-30)

**Symptom:** Du willst `rate-limiter.ts` refactoren (1 globaler Limiter → 4 separate). Du machst 4+ gezielte Patches. Resultate: Indentation fliegt auseinander, doppelte Property-Keys (`standardHeaders: true` 2× → TS1117).

**Workaround (proven):** Für strukturellen Refactor → **`write_file()`** als einzelner kompletter Rewrite.

**Anti-Pattern für `patch()`:**
- ❌ Refactor das Object-Literals neu strukturiert (mehrere Keys anfassen)
- ❌ Mehrere Imports hinzufügen oder umorganisieren
- ❌ Funktion hinzufügen UND gleicher Name woanders löschen
- ❌ Kommentar-Block komplett ersetzen — Indentation fliegt auseinander
- ❌ 3x gleicher String in einer Datei → patch wirft "Found N matches"

**Sweet-Spot für `patch()`:**
- ✅ Einzelne Funktion / Funktions-Tail ändern (kleine Sektion)
- ✅ Variable/Konstante umbenennen (`replace_all=true`)
- ✅ Imports in der gleichen Zeile einzeln hinzufügen
- ✅ DOM-Marker oder CSS-Snippet ins HTML einfügen

**Lesson:** `patch()` ist ein SCALPEL nicht ein SÄGE. Für Refactors > 50 Zeilen oder > 3 gleichzeitige Stellen: `write_file()`.
