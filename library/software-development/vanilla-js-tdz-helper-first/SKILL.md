---
name: vanilla-js-tdz-helper-first
title: Vanilla JS — Helper-First Pattern (TDZ vermeiden)
description: "Use when user is debugging vanilla JavaScript initialization failures, Temporal Dead Zone ReferenceErrors, dashboard connection problems, or helper and API-wrapper ordering in a no-bundler page. NOT for framework or ESM projects or backend-only errors. Defines `$`, `setText`, `escapeHtml`, state helpers, and SSR data in safe dependency order."
triggers:
- Working with vanilla HTML/JS dashboards (no bundler, no module system)
- SSE/WebSocket Frontend mit EventSource
- Dashboard reload crasht mit "Cannot access X before initialization"
- SetActiveTab / init function crashed silently
- Debugging 0 Verbundene or Verbindung fehlgeschlagen in a real-time dashboard
- browser_console zeigt leere exceptions (message="") und Dashboard bleibt auf Skeleton
version: 1.1.0
author: Hermes Agent
lane: worker-heavy
reasoning_effort: xhigh
license: MIT
trigger_keywords: ['user', 'debugging', 'vanilla', 'javascript', 'initialization']
keywords: ['user', 'debugging', 'vanilla', 'javascript', 'initialization']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['sse-frontend-patterns']
---



# Vanilla JS — Helper-First Pattern

## Warum

In Vanilla JS (ohne Bundler, ohne ESM) sind `const`/`let` **nicht** gehoisted wie `var`. Sie leben in der **Temporal Dead Zone (TDZ)** bis zu ihrer Definition. Wenn eine Funktion während der Page-Init eine `const` benutzt, die später im Script definiert wird → `ReferenceError`, Script bricht ab, Event-Handler werden nie gebunden.

**Realer Vorfall 2026-06-30:** Hermes SSE Dashboard — `setActiveTab()` rief `$()` auf, bevor `const $ = ...` definiert war. `connect()` lief nie, Dashboard zeigte permanent roten Dot, obwohl Server grün war.

## Pattern

```html
<script>
// 1. HILFSFUNKTIONEN ZUERST (vor state, vor allem anderen)
const $ = (id) => document.getElementById(id);
const setText = (id, text) => { $(id).textContent = text; };
const escapeHtml = (s) => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

// 2. State (nutzt die Helper nicht direkt, ist safe)
const state = { events: [], conn: null };

// 3. Funktionen die Helper nutzen
function setActiveTab(name) {
  const filterLabel = $('activeFilterLabel');  // ← safe, $ ist definiert
  // ...
}

// 4. Init-Code
setActiveTab('live');  // ← safe
</script>
```

## Anti-Pattern (was crashed)

```html
<script>
const state = { activeTab: 'live' };

function setActiveTab(name) {
  const el = $('filterLabel');  // ← TDZ-ReferenceError wenn vor $ definiert
}

setActiveTab(state.activeTab);  // ← CRASH: Cannot access '$' before initialization

const $ = (id) => document.getElementById(id);  // ← zu spät
</script>
```

## Diagnose (Standard)

Console-Error:
```
Uncaught ReferenceError: Cannot access '$' before initialization
    at setActiveTab (file.html:1205:27)
    at file.html:1228:5
```

→ Helper ans Script-Anfang verschieben.

## Diagnose (Silent TDZ — Headless / Desktop-App-Umgebungen)

### Das Problem

In Chromium headless (`google-chrome --headless`) oder Hermes' embedded Browser (`browser_navigate` + `browser_console`) zeigen TDZ-ReferenceErrors sich **ohne Fehlermeldung** in der Console:

```json
{"type": "error", "text": "", "source": "exception", "message": ""}
```

Begründung: ES-Module-Stil-Fehler und Init-TDZ-Violations zeigen in manchen Browser-Kontexten die `.message`-Eigenschaft nicht an. Der Error-Objekt-Stack ist leer. Der einzige Hinweis: das Dashboard zeigt Skeletons, "connecting…", oder leere Sidebar — und alle `console.log`-Aufrufe nach dem Crash fehlen.

### Die Technik

**Wrapper das gesamte `<script>` in einen `try/catch`, der den Fehler in `document.title` schreibt:**

```html
<script>
try {
  // ... gesamter Script-Code ...
} catch(e) {
  console.error('[TDZ-DIAG]', e?.message, e?.stack);
  document.title = '⚠ TDZ-CRASH: ' + (e?.message || '(no message)');
}
</script>
```

Danach:
1. Browser laden
2. `browser_console` checken → `${document.title}` zeigt den echten Fehler
3. Fix: Reihenfolge der `let`/`const`-Deklarationen korrigieren

**Nach dem Fix den try/catch-Wrapper entfernen** — er maskiert echte Laufzeitfehler.

### State-Variablen als TDZ-Victim

**Der häufigste TDZ-Fall in Dashboards sind NICHT Helper-Funktionen (`$()`, `setText()`), sondern State-Variablen, die von IIFEs vor ihrer Deklaration referenziert werden.**

Symptom:
- Dashboard zeigt Skeletons / "connecting…" / leere Sidebar
- Kein Console-Error mit Message
- `renderAll` ist als `function` verfügbar, aber `fetchData` und andere `let`-Constraints sind `undefined`
- `node --check` auf das Script gibt **keinen Fehler** (weil node keine IIFE-Vor-declaration ausführt)

Ursache:
```html
<script>
// ❌ FALSCH — IIFE vor let-Deklaration
function switchTab(name) {
  if (lastData) renderAll(lastData);  // ← refenziert lastData
}
(function initTab() {
  switchTab(savedTab);  // ← wird VOR let lastData ausgeführt
})();

let lastData = null;  // ← zu spät! TDZ!

// ❌ CRASH: Cannot access 'lastData' before initialization
// → Script bricht ab, keine späteren Funktionen werden definiert
</script>
```

Fix:
```html
<script>
// ✅ RICHTIG — State vor Funktionen die ihn referenzieren
let lastData = null;
let lastFetchTs = 0;

function switchTab(name) {
  if (lastData) renderAll(lastData);  // ← safe
}
(function initTab() {
  switchTab(savedTab);  // ← safe
})();
</script>
```

**Rule of Thumb:** ALLE `let`/`const` State-Deklarationen müssen **oberhalb** jeder Funktion stehen, die sie im Body referenziert — auch wenn die Funktion erst später aufgerufen wird. JavaScript `let`/`const` sind block-scoped und haben eine Temporal Dead Zone bis zur Deklaration. IIFEs (die sofort ausgeführt werden) sind besonders anfällig, weil sie den ReferenceError schon beim Laden auslösen.

## Erweitertes Pattern: API-Wrapper + Token-Helper

Wenn dein Dashboard gegen ein auth-required Backend spricht, definiere **zusätzlich** einen zentralen `apiFetch()`-Wrapper ganz oben. Sonst passiert Bug 9 (siehe dev-tools): SSE connected (query-token fallback), aber `fetch('/api/status')` ohne Header → 401 → KPIs leer.

```html
<script>
// 1. HILFSFUNKTIONEN + AUTH-HELPER ZUERST
const $ = (id) => document.getElementById(id);
const setText = (id, text) => { $(id).textContent = text; };

const DEFAULT_AUTH_TOKEN = 'super-secret';
let currentAuthToken = DEFAULT_AUTH_TOKEN;
function apiFetch(path, opts = {}) {
  const userHeaders = opts.headers || {};
  const headers = {
    ...userHeaders,
    'X-Hermes-Token': userHeaders['X-Hermes-Token'] || currentAuthToken,
  };
  return fetch(path, { ...opts, headers });
}

// 2. State
const state = { events: [], conn: null };

// 3. Funktionen die Helper nutzen — IMMER apiFetch() statt fetch('/api/')
async function fetchStatus() {
  const r = await apiFetch('/api/status');  // ← nicht fetch('/api/status')!
  // ...
}
</script>
```

**Rule:** wenn du im Code `fetch('/api/')` siehst, ersetze es durch `apiFetch('/api/')`. Für 14+ Call-Sites geht das in einem `sed -i`/`patch replace_all`-Sweep.

**Detection nach Multi-Section-Patches:** nach jeder Serie von `patch`-Calls, die den `<script>`-Block berührt, Sanity-Check:
- `grep -n '^\\s*const \\$' dashboard.html` → genau 1 Match ganz oben, nicht 2 (verwaister alter + neuer).
- `grep -c \"fetch('/api\" dashboard.html` → 0, alles durch `apiFetch` ersetzt.
- Im Browser: `console.log` direkt nach `const $ = ...` ausführen, um TDZ auszuschließen.

## Erweitertes Pattern 3: SSR-Data-Embedding (0-Wait-Rendering)

### Das Problem

Ein Dashboard das `fetch('/api/data')` beim Laden aufruft, zeigt zuerst Skeletons / connecting... für mindestens einen Request-Cycle. In Headless-Chrome-Umgebungen (Screenshots, Preview) reicht `--virtual-time-budget=8000` nicht aus, wenn das Backend >500ms braucht → Skeleton wird gescreenshotted, nie die Live-Daten.

### Das Pattern

**SSR = Server-Side Rendering des Daten-Snapshots direkt in den HTML-Response, kurz vor dem schließenden `</body>`.**

```html
<!-- Server injected: aktuellster Daten-Snapshot -->
<script>window.__INITIAL_SNAPSHOT__ = {"cpu":30.2,"mem":75.1,"cron":{"active":17,"jobs":[]},"skills":{}};</script>

<!-- Main script lädt und rendert sofort aus dem Snapshot -->
<script>
// Helper + State + Funktionen (wie oben)

if (window.__INITIAL_SNAPSHOT__) {
  renderAll(window.__INITIAL_SNAPSHOT__);  // ← SOFORT sichtbar
}
</script>
```

### SSR-Block-Regeln (damit kein TDZ)

1. **SSR-Block gehört GANZ ans Ende des `<body>`** — nach allem HTML, direkt vor `</body>`
2. **SSR-Block referenziert KEINE JS-Funktionen** — enthält nur das JSON-Objekt
3. **SSR-Block muss AUSSERHALB jedes try/catch-Wrappers sein** — sonst werden Exceptions maskiert
4. **Das `if (window.__INITIAL_SNAPSHOT__)` im Script darf NUR `renderAll()` o.ä. aufrufen** — keine State-Zuweisung, kein `lastData = INIT_SNAPSHOT` im SSR-Block. Zuweisung erst im Main-Script.

### Beispiel (korrekt)

```html
<!-- ... Dashboard-HTML ... -->

<!-- SSR: Daten-Snapshot vom Server -->
<script>window.__INITIAL_SNAPSHOT__ = {"cpu":30.2,"mem":75.1};</script>

<!-- Main Script mit TDZ-safe Reihenfolge -->
<script>
// 1. Helper zuerst
const $ = id => document.getElementById(id);
// 2. State — VOR allen IIFEs und Funktionen die ihn nutzen!
let lastData = null;
// 3. Funktionen
function renderAll(d) { /* ... */ }
function switchTab(name) { if (lastData) renderAll(lastData); }
// 4. Init — SSR-Daten sofort rendern
if (window.__INITIAL_SNAPSHOT__) {
  lastData = window.__INITIAL_SNAPSHOT__;
  renderAll(lastData);  // ← sofort sichtbar, kein Skeleton-Flash
}
// 5. live polling starten
setInterval(fetchData, 3000);
</script>
```

### Backend-Implementierung (Python)

```python
# 1. Snapshot generieren (gleicher Code wie /api/data-Endpoint)
snapshot = get_dashboard_data()

# 2. index.html lesen und SSR-Block injizieren
with open('index.html', 'r') as f:
    html = f.read()

snapshot_json = json.dumps(snapshot, default=str)
ssr_block = f'<script>window.__INITIAL_SNAPSHOT__ = {snapshot_json};</script>\n'
html = html.replace('</body>', f'{ssr_block}</body>')

# 3. Ausliefern (Flask)
return Response(html, mimetype='text/html')
```

### Vorteile

- **0-Wait-Rendering** — Screenshots zeigen Live-Daten ab Frame 1
- **Backend-Cache-Bug tolerant** — wenn das Backend >500ms braucht, sieht der User trotzdem Daten aus dem letzten Response
- **Headless-Chrome-kompatibel** — `--virtual-time-budget=500` reicht, weil kein fetch-Cycle abgewartet werden muss

### Wann NICHT

- **Echtzeit-Dashboard** wo Millisekunden zählen → SSR-Daten sind beim Laden schon alt
- **Auth-sensitive Daten** → SSR-Block könnte rohe Tokens/Keys enthalten (snapshot bereinigen!)
- **Sehr große Snapshots** (>500KB) → erhöht HTML-Response-Größe

## Wann triggern

- Vanilla-JS-Frontends ohne Bundler (single HTML files mit inline `<script>`)
- Multi-File-Setups ohne ESM-Modules
- Quick-Mockups / DevTools-Snippets
- Legacy-Code-Refactorings
- **Headless-Browser-Debugging mit leeren Console-Exceptions**

## Alternative (wenn Helper-First zu invasiv)

IIFE-Wrapper mit Funktions-Scope:
```javascript
(() => {
  const $ = (id) => document.getElementById(id);
  // ... alles andere
})();
```
Pro: saubererer Scope. Contra: schwerer zu debuggen, kein globaler Zugriff.

## Verwandte Docs

- `~/docs/system/hermes-sse-5-layer-debug-2026-06-30.md` — Layer 5
- Skill: `sse-frontend-patterns` — umfassender Pattern-Set für SSE-Dashboards (EventSource, apiFetch, Exponential-Backoff, 429-Cooldown, Audit-UI)
- **Reference: `references/dashboard-v4-tdz-debug-2026-07-08.md`** — Vollständiger Debug-Transkript der 30+ Tool-Call-Session

## Diagnose-Hierarchie für "Dashboard connected nicht"

Wenn du in einem Vanilla-JS+SSE-Dashboard Probleme debugst, prüfe in dieser Reihenfolge (jeder Layer schließt die meisten einfachen Fälle aus):

0. **Layer Zero: Backend-Datenpipeline prüfen** (⚠ Wichtigster und am häufigsten übersprungener Schritt!)  
   `curl -s http://127.0.0.1:PORT/api/data` → kommt überhaupt JSON zurück? Wie lange dauert es?  
   Wenn das Backend langsam ist (>1s) oder gar nicht antwortet, ist JEDER Frontend-Debug sinnlos. Der Headless-Browser hat `--virtual-time-budget=8000` (8s) — ein 2.5s-Cache-Bug lässt ihn noch im Skeleton stecken.  
   Siehe `systematic-debugging` Skill: "Layer Zero: Verify the Data Pipeline".

1. **Server-Health** (`curl /health`) — läuft der Server überhaupt?
2. **CORS** — antwortet der Server mit `Access-Control-Allow-Origin` für deinen Origin?
3. **Auth-Gate** — blockt die Middleware statische HTML-Files? Sollte bypass-Pfade haben für `/dashboard/`.
4. **EventSource-Header** — Browser kann keine custom Header. Token MUSS in URL.
5. **TDZ (dieser Skill)** — `console.log` direkt nach `const $ = ...`. ReferenceError beim Init?
6. **apiFetch-Wrapper** — alle `/api/`-Calls müssen durch den Token-Wrapper, sonst 401.
7. **429-Spirale** — flacher SSE-Reconnect + Rate-Limit = Endlos-Loop. Exponential-Backoff.

Die ersten 4 sind Server-Side-Issues, 5–6 sind typische Vanilla-JS-Front-End-Bugs, 7 ist die häufigste Edge-Case im Betrieb. **Punkt 0 zu überspringen war der teuerste Fehler einer realen 30-Tool-Call-Debug-Session (Dashboard v4, 2026-07-08).**

## Reference-Files

- `references/dashboard-v4-tdz-debug-2026-07-08.md` — Vollständiger Debug-Transkript: TDZ-Detection via try/catch+document.title, Cache-Timestamp-Bug, Unclosed-Backtick-Fix