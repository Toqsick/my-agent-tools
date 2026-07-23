# Dashboard UI Patterns (Vanilla-JS Single-File)

> Extracted from hermes-maintenance SKILL.md Sections 11.2, 11.3, 11.4, 11.6, 11.7.

## Doppelte Funktionen vermeiden (2026-06-30)

**Symptom:** `patch()` auf eine HTML-Datei mit JS-Block editiert eine Funktion (`renderEvents()`), aber das `old_string` matched anderswo oder du vergisst dass die alte Funktion an anderer Stelle noch existiert. Browser wirft `SyntaxError: Identifier 'renderEvents' has already been declared`.

**Ursache:** Vanilla-JS in single-file-`<script>`-Blöcken hat keine Module-Trennung. `function renderEvents() { ... }` doppelt deklariert = SyntaxError. `tsc --noEmit` bemerkt das NICHT.

**Diagnose (schnell) nach Vanilla-JS-Patches:**
```bash
node -e "const fs=require('fs'); const html=fs.readFileSync('dashboard.html','utf-8'); \
  const m=html.match(/<script>([\\s\\S]*?)<\\/script>/); \
  new Function(m[1]); \
  console.log('JS parses OK')"
```

**Workaround-Pattern:**
1. Vor jedem Patch: `grep -n "function <name>" dashboard.html` zur Unique-Check
2. Falls Match mehrfach: alte Stelle löschen, dann neue hinzufügen
3. Bei strukturellem Refactor: lieber FULL FILE REWRITE statt 6+ targeted patches

## Tab-System Pattern (2026-06-30)

**Use-Case:** Dashboard wächst von 5 auf 8+ Panels, Scroll wird lang, optische Trennung fehlt. User will Tabs aber kein React/Vue-Framework.

```html
<style>
  .header { display: grid; grid-template-columns: 1fr auto 1fr; }
  .tab-bar { grid-column: 2; display: flex; gap: 2px; padding: 4px;
             background: var(--surface); border-radius: 9999px; }
  .tab { padding: 8px 16px; border-radius: 9999px; cursor: pointer; }
  .tab.active { background: var(--primary); color: white; }
  .tab-panel { display: none; }
  .tab-panel.active { display: flex; flex-direction: column; gap: var(--space-5); }
</style>

<header class="header">
  <div class="logo">...</div>
  <nav class="tab-bar">
    <button class="tab active" data-tab="live">📡 Live</button>
    <button class="tab" data-tab="security">🛡️ Security</button>
    <button class="tab" data-tab="system">🧠 System</button>
  </nav>
  <div class="theme-toggle">☾</div>
</header>

<main>
  <div class="tab-panel active" id="panel-live">...</div>
  <div class="tab-panel" id="panel-security">...</div>
  <div class="tab-panel" id="panel-system">...</div>
</main>
```

```javascript
// JS: localStorage-Persist + Polling-Optimierung
function setActiveTab(tabName) {
  state.activeTab = tabName;
  try { localStorage.setItem('hermes.activeTab', tabName); } catch {}
  document.querySelectorAll('.tab').forEach(btn => {
    const isActive = btn.dataset.tab === tabName;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
  });
  document.querySelectorAll('.tab-panel').forEach(p => {
    p.classList.toggle('active', p.id === `panel-${tabName}`);
  });
  if (tabName === 'security') { fetchAudit(); fetchCanary(); }  // Lazy-Load
}

// Polling nur wenn Tab aktiv (spart ~28 Requests/min)
setInterval(() => {
  if (state.activeTab === 'security') { fetchAudit(); fetchCanary(); }
}, 2000);
```

**Trade-offs:**
- ✅ Vanilla JS, kein Build-Step, keine Dependencies
- ✅ localStorage-Persist über Browser-Reload
- ✅ Polling-Optimierung spart echte Requests
- ❌ Keine URL-Hash-Sync (Browser-History geht nicht durch Tabs)
- ❌ Bei 8+ Tabs wird Tab-Bar eng

**Referenz-Implementation:** `packages/hermes-sse/dashboard/hermes-sse-dashboard.html` (Phase C-1 abgeschlossen 2026-06-30).

## Tab-Polling-Lazy-Load Pattern (proven 2026-06-30)

```javascript
const state = { activeTab: 'live', /* ... */ };

try {
  const saved = localStorage.getItem('dashboard.activeTab');
  if (saved) state.activeTab = saved;
} catch {}

function setActiveTab(tabName) {
  state.activeTab = tabName;
  try { localStorage.setItem('dashboard.activeTab', tabName); } catch {}
  document.querySelectorAll('.tab-panel').forEach(p => {
    p.classList.toggle('active', p.id === `panel-${tabName}`);
  });
  document.querySelectorAll('.tab').forEach(btn => {
    const active = btn.dataset.tab === tabName;
    btn.classList.toggle('active', active);
    btn.setAttribute('aria-selected', active ? 'true' : 'false');
  });
  if (tabName === 'security') { fetchAudit(); fetchCanary(); }
  if (tabName === 'system') { fetchSystemHealth(); fetchSystemCron(); }
}

setInterval(() => {
  if (state.activeTab === 'security') { fetchAudit(); fetchCanary(); }
  else if (state.activeTab === 'system') { fetchSystemHealth(); fetchSystemCron(); fetchSystemMnemosyne(); }
}, 8000);
```

**Init-Reihenfolge:** `setActiveTab(state.activeTab)` muss NACH dem DOM ready-State laufen, BEVOR Event-Listener binden.

**Bonus — Tab-Badges:** Counter pro Tab zeigen ohne User-Tab-Wechsel zu erzwingen. Bei Canary-Alert den Security-Tab-Badge rot einfärben.

## Read-Only System-Monitor-Route-Pattern (2026-06-30)

**Architektur:**
1. **System-Health-Route** (`/api/system/health`): nur Node-Builtins (`os`, `fs.statfs`, `process`)
   - `os.cpus()`, `os.totalmem()`, `os.freemem()`, `os.loadavg()`
   - `fs.statfsSync('/').{bsize,blocks,bfree}` → Disk-Stats in GB
   - 5s In-Memory-Cache
2. **Cron-Route** (`/api/system/cron`): `fs.readFileSync('~/.hermes/cron/jobs.json')` + JSON.parse
   - KEIN `systemctl`, KEIN Subprocess-Trigger
   - 10s In-Memory-Cache
3. **Mnemosyne-Route** (`/api/system/mnemosyne`): SQLite read-only via `node:sqlite` (Node 22+) ODER `sqlite3`-CLI
   - DB-Path: `~/.hermes/mnemosyne/data/mnemosyne.db`
   - DB-Open: `new DatabaseSync(dbPath, { readOnly: true })`
   - 30s In-Memory-Cache

**Sicherheit:**
- Cache nur In-Memory (kein Disk-File)
- SQLite READ-ONLY-Mode oder Subprocess mit `stdio: ['ignore', 'pipe', 'ignore']`
- KEINE Secrets / KEINE Tokens in Response (nur Counts/Sizes/Model-Names)

**Referenz-Implementation (Phase C-2):**
- Server: `packages/hermes-sse/src/api/{system-health,system-cron,system-mnemosyne}-route.ts`
- Frontend: `dashboard/hermes-sse-dashboard.html` (Zeilen ~1060–1450)
- Build-Report: `~/docs/system/hermes-v7-sse-system-tab-c2-2026-06-30.md`
