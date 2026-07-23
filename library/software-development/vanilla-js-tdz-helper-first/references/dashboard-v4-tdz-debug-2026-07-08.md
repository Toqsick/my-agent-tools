# Dashboard v4 TDZ-Debug-Transkript — 2026-07-08

## Kontext

Yuno Operator Dashboard (server.py 777 Zeilen + index.html ~2200 Zeilen). Live-Polling alle 3s gegen Hermes CLI, SSR-Snapshot-Embedding, 8 Tabs, Sparklines, 4 Themes.

## Bug #1: Cache-Timestamp

**Symptom:** Jeder `/api/data`-Call dauerte 2.3–2.7s trotz Cache-TTL 30–60s. Nach Warmup kein Speedup.

**Root Cause:** Copy-Paste-Bug — `_cache_ts[key] = ttl` statt `_cache_ts[key] = now`.

```python
# ❌ FALSCH
_cache_ts[key] = ttl  # ttl = 60, also cached_ts = 60
# → (now - 60) ist IMMER > ttl → never cached

# ✅ RICHTIG
_cache_ts[key] = now  # jetzt: (now - now) = 0 < ttl → cached!
```

**Impact:** 10x Performance-Steigerung (2.5s → 0.19s). 4h Debugging auf Frontend-Bug verschwendet weil Server langsam war.

## Bug #2: Unclosed Template-Literal

**Symptom:** `node --check` exit 0, aber Browser zeigt Skeleton. Script parst nicht.

**Root Cause:** Backtick Counting — 205 statt gerader Zahl. Ein Template-String in `renderCron()` hatte keinen schließenden Backtick.

**Fix:** `sed -n '/<script>/,/<\/script>/p' index.html | sed '1d;$d' > /tmp/check.js && node --check /tmp/check.js` gefolgt von Backtick-Paritäts-Check: `grep -o '`' | wc -l` muss gerade sein.

## Bug #3: Temporal Dead Zone (TDZ) — DER KILLER

**Symptom:** Dashboard zeigt Skeletons + "connecting…", Console zeigt leere Exceptions (`{"message":""}`). `renderAll` als function verfügbar, aber `fetchData` und alle `let`-Constraints undefined.

**30+ Tool-Calls Debug-Spirale:** Headless-Chrome-Cache, CORS, Mixed-Content, JS-Syntax, Template-Literals, Unicode-Keys, Timing — alles ausgeschlossen.

**Root Cause:** `switchTab()` (1191) wird durch `initTab()` IIFE (1213) *sofort* aufgerufen, referenziert `lastData`, aber `let lastData = null` steht erst auf Zeile **1290** — 77 Zeilen später. JavaScript's TDZ: `let`/`const` sind block-scoped, Zugriff vor Deklaration → ReferenceError → Script bricht STILL ab.

```html
<script>
// ... 1189 Zeilen Funktionen ...
function switchTab(name) {
  if (lastData) renderAll(lastData);  // ← TDZ!
}
(function initTab() {
  switchTab(savedTab);  // ← wird SOFORT ausgeführt
})();                   //   VOR let lastData = null

let lastData = null;    // ← Zeile 1290 — ZU SPÄT!
</script>
```

**Debug-Technik (Try/Catch-Wrapper):** Wrapper das gesamte `<script>`:

```html
<script>
try {
  // ... gesamter Code ...
} catch(e) {
  console.error('[TDZ-DIAG]', e?.message, e?.stack);
  document.title = '⚠ TDZ-CRASH: ' + (e?.message || '(no message)');
}
</script>
```

→ `document.title` zeigte `"⚠ TDZ-CRASH: Cannot access 'lastData' before initialization"`

**Fix:** `let lastData = null` VOR `switchTab`/`initTab` verschieben (vor Zeile 1191).

## Lessons Learned

1. **Erst Backend debuggen** bevor du Frontend-Fehler jagst. Der Cache-Bug verursachte 2.5s Latenz → headless Chrome's `--virtual-time-budget=8000` reichte nicht für stable rendering = Skeleton. Aber ich habe 4h lang Frontend-JS debuggt bevor ich den Backend-Cache-Fehler fand.

2. **Try/catch + document.title ist die einzige zuverlässige TDZ-Detection** in Headless-Chrome. Browser-Console zeigt leere Exceptions. `node --check` findet den Fehler NICHT weil node keine IIFE-Vor-declaration-Evaluierung macht.

3. **Backtick-Parität** checken nach großen Patch-Sessions: ungerade Anzahl = unclosed Template-Literal.

4. **IIFEs sind TDZ-Anfällig** — jede sofort ausgeführte Funktion die auf `let`/`const` zugreift, muss NACH der Deklaration stehen.

5. **Rule of Three** (aus systematic-debugging): nach 3+ Fix-Versuchen Architektur hinterfragen. Hätte ich hier früher gemacht — der Cache-Bug und der Frontend-Bug waren zwei getrennte Probleme parallel.
