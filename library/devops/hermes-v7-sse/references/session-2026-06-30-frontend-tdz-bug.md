# Session 2026-06-30 — Layer 5: Frontend Temporal Dead Zone

Live incident where the **server was fully healthy** but the dashboard's EventSource never opened. The root cause was a JavaScript `const` Temporal Dead Zone crash in the dashboard's own init code.

## Why this incident is special

The 4-layer bug (see `session-2026-06-30-4-layer-bug.md`) is **server-side**. This one is **purely client-side**, and the worst kind: the server can't see it, curl can't reproduce it, and the sse-debug.html page (which has minimal init code) works fine. The bug only shows up in the full dashboard.

## Timeline (real events)

| t | User message | Diagnosis |
|---|---|---|
| 1 | "okay kann verbinden aber im doard steht 0 Verbundene" | Layers 1-4 of the previous bug fixed. Server `clients: 1` with curl. Browser still red dot. |
| 2 | "roter punkt" | Browser shows error state. Server side fine. sse-debug.html user-tested: all 4 tests pass. → Server + sse-debug fine, main dashboard broken. |
| 3 | (user shares console) | F12 reveals: `hermes-sse-dashboard.html:1205 Uncaught ReferenceError: Cannot access '$' before initialization at setActiveTab (hermes-sse-dashboard.html:1205:27) at hermes-sse-dashboard.html:1228:5` |

## Root cause

In `dashboard/hermes-sse-dashboard.html`, the `<script>` block had this order at the bottom of the init section:

```js
// Line 1205 — setActiveTab uses $ helper
function setActiveTab(tabName) {
  ...
  const filterLabel = $('activeFilterLabel');   // ← uses $
  ...
}

// Line 1228 — Init call BEFORE $ is defined
setActiveTab(state.activeTab);

// Line 1233 — Helper definition (too late!)
const $ = (id) => document.getElementById(id);
const setText = (id, text) => { $(id).textContent = text; };
```

`$` is declared with `const`, which has Temporal Dead Zone semantics: the binding exists from the start of the scope, but accessing it before the declaration line throws `ReferenceError`. Unlike `var`, `const`/`let` are NOT hoisted into a usable state.

The init sequence: `setActiveTab()` is called at line 1228 → reads `$` (line 1205) → `$` is in TDZ → **ReferenceError thrown** → the rest of the script never runs → `connect()` is never called → EventSource never opens → counter stays 0.

## Why server logs were clean

The browser crashed **before** `new EventSource()`. The server never saw a connection attempt for the dashboard. Only the sse-debug page and manual curl tests ever hit `/api/events`. So `stream.clients` reported 0 — which was actually correct (no browser was connected).

## The misleading intermediate state

While debugging, I saw `clients: 1` in `/api/sse-stats` for a moment. That was a **parallel curl SSE-Stream from the smoke test** I had open, not the browser. The dashboard was still dead. Lesson: always cross-check the server's `clients` count against an actual browser-driven test, not just curl.

## Fix

Move the `const` declarations of all helpers (`$`, `setText`, etc.) to the **very top of the script block**, before any function that uses them at init time:

```js
// NEW: At the top of <script>
const $ = (id) => document.getElementById(id);
const setText = (id, text) => { $(id).textContent = text; };

// ... rest of code unchanged ...
```

After the fix, `connect()` runs, opens the EventSource with `?token=super-secret`, and the counter jumps to 1.

## Diagnostic tool that caught it

The `sse-debug.html` page (created in the previous session) was crucial. It uses the same backend but has its own minimal `<script>` block with no helper-using init calls. The fact that it worked while the main dashboard didn't was the strong signal that the bug was in the dashboard's own init code, not the server.

## Diagnostic console.log added during debugging

To find this kind of bug in the future, the `connect()` function was patched to log:

```js
console.log('[SSE] Connecting to:', url);
es.onopen = () => { console.log('[SSE] OPEN ✓'); ... };
es.onerror = (e) => { console.error('[SSE] ERROR:', { readyState: rs, status: es.status, url: es.url }); ... };
```

If you see `[SSE] Connecting to:` followed by a ReferenceError, the init code is broken. If you see `[SSE] Connecting to:` followed by `[SSE] OPEN ✓`, the init is fine. If you never see `[SSE] Connecting to:`, the init crashed before `connect()` ran — TDZ is the prime suspect.

## Secondary bug found and fixed

`setInterval(hookSSE, 500)` re-wrapped the EventSource's `onmessage` handler every 500ms because there was no guard. After 10 ticks, the message handler was nested 10 deep. Harmless but smelly. Fixed with a `__hooked` flag:

```js
function hookSSE() {
  const es = state.conn;
  if (!es) return;
  const origHandler = es.onmessage;
  if (origHandler && origHandler.__hooked) return;   // ← guard
  es.onmessage = (msg) => {
    if (origHandler) origHandler(msg);
    // ... bridge call ...
  };
  if (es.onmessage) es.onmessage.__hooked = true;
}
```

## Lessons that became pitfalls in SKILL.md

- **Frontend `const` TDZ is a real failure mode** — order of declarations in `<script>` matters. Always put helpers at the top.
- **Server healthy ≠ browser healthy** — when "0 Verbundene" persists after all server-side fixes, the bug is almost certainly in the browser's own JS.
- **`sse-debug.html` is a powerful isolator** — if it works but the main dashboard doesn't, the bug is in the dashboard's init code, period.
- **Server `clients` count can be misleading during multi-tab debugging** — cross-check with `console.log` in the browser before assuming the dashboard is connected.
- **Diagnostic console.log in `connect()` and `onerror()`** — `[SSE] Connecting to:` and `[SSE] OPEN ✓` markers make silent init failures immediately obvious.

## How to debug this exact pattern in 60 seconds

1. User says "Verbundene 0" or "roter punkt"
2. `curl -s -H "X-Hermes-Token: super-secret" http://localhost:4321/api/sse-stats` → check `clients`
3. If `clients == 0` AND sse-debug.html is also failing → it's a server bug (re-check layers 1-4)
4. If `clients == 0` AND sse-debug.html works → it's a dashboard JS bug
5. User opens F12 → Console on the dashboard
6. Look for `Uncaught ReferenceError: Cannot access '<helper>' before initialization` → TDZ. Move the `const` to the top of `<script>`.
7. Look for `Uncaught TypeError: <something> is not a function` → check if a function definition was deleted or moved
8. Look for `404 on <some-file>.js` → static asset path issue
9. After fix: hard-reload (Ctrl+Shift+R) — localStorage + script cache can mask the fix
