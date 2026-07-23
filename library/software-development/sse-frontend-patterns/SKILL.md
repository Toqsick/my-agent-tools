---
name: sse-frontend-patterns
title: SSE / EventSource Frontend Patterns (vanilla browser)
description: "Use when user asks to build or debug a real-time browser dashboard using native Server-Sent Events, token-protected EventSource, REST calls, reconnect backoff, or live audit logs. NOT for WebSocket-only applications or backend-only streaming. Provides vanilla HTML and JavaScript patterns for auth, idempotent handlers, 429 resilience, and production diagnostics."
triggers:
- Building or debugging a real-time dashboard with EventSource or SSE
- Auto-reconnect logic for SSE or WebSocket
- 429 Too Many Requests errors in real-time frontends
- Vanilla HTML+JS dashboard that talks to a token-protected backend
- Browser console shows Permissions-Policy header warnings or ObjectMultiplex noise
- Building a live audit log or event feed from SSE
- Configuring express-rate-limit with ENV overrides for dev/test
- Implementing Last-Event-ID replay in an SSE server
- Auth-gate middleware that needs to exempt webhook POSTs or static assets
version: 1.0.0
author: Hermes Agent
lane: worker-heavy
reasoning_effort: xhigh
license: MIT
trigger_keywords: ['and', 'sse-frontend-patterns', 'build', 'debug', 'real-time']
keywords: ['only', 'user', 'asks', 'build', 'debug']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['vanilla-js-tdz-helper-first']
---


# SSE / EventSource Frontend Patterns

Real-time browser dashboards using native `EventSource` (no libraries, no bundler). All patterns are vanilla HTML+JS, runnable as a single file. Tested in production with the Hermes V7 SSE server.

## When to use this skill

- Single-file HTML dashboard that consumes Server-Sent Events from a token-protected backend.
- Same dashboard also makes REST calls to the same backend (status, audit, canary, etc.).
- Seeing flapping connections, 429s, or "0 Verbundene" when the server says the client IS connected.

## The four core patterns

### 1. Auth via URL query, NOT headers

`EventSource` cannot send custom HTTP headers. If the server requires `Authorization` or `X-Token`, the token MUST go in the URL as `?token=...`. The EventSource constructor silently strips headers you try to set via init dict.

```javascript
const url = `/api/events?token=${encodeURIComponent(token)}`;
const es = new EventSource(url);
```

**Server side** must accept the token from both `header` AND `query`. When the server has no auth at all (Localdev), bypass the gate silently for `/api/events`.

### 2. apiFetch wrapper for the same SPA

You have one auth token. EventSource uses it in URL. fetch() calls use it in header. Wrap fetch() once, then forget about it.

```javascript
let rateLimitCooldownUntil = 0;
function apiFetch(path, opts = {}) {
  if (Date.now() < rateLimitCooldownUntil) {
    const wait = Math.ceil((rateLimitCooldownUntil - Date.now()) / 1000);
    return Promise.reject(new Error(`rate-limit-cooldown (${wait}s)`));
  }
  const userHeaders = opts.headers || {};
  const headers = {
    ...userHeaders,                                     // user's headers FIRST
    'X-Hermes-Token': userHeaders['X-Hermes-Token'] || currentAuthToken,
  };
  return fetch(path, { ...opts, headers }).then(r => {
    if (r.status === 429) {
      const ra = parseInt(r.headers.get('Retry-After') || '30', 10);
      rateLimitCooldownUntil = Date.now() + (ra * 1000);
      console.warn(`[apiFetch] 429 — Cooldown ${ra}s aktiv`);
    }
    return r;
  });
}
```

**Pitfall**: do NOT put the default header before the spread, or callers cannot override it. Spread user headers first, then layer defaults on top.

### 3. Exponential-backoff auto-reconnect (with cap)

When EventSource closes, you almost always want to reconnect. But NEVER use a fixed short delay (like 3s) when the server has rate-limiting. See `references/429-reconnect-death-spiral.md` for the full case study.

```javascript
let sseReconnectAttempt = 0;
let sseReconnectTimer = null;

es.onerror = (e) => {
  const rs = es.readyState;
  if (rs === EventSource.CLOSED) {
    sseReconnectAttempt++;
    // 2s, 4s, 8s, 16s, 32s, then cap at 60s
    const delay = Math.min(60000, 2000 * Math.pow(2, sseReconnectAttempt - 1));
    if (sseReconnectTimer) clearTimeout(sseReconnectTimer);
    sseReconnectTimer = setTimeout(() => {
      if (!state.conn || state.conn.readyState === EventSource.CLOSED) connect();
    }, delay);
  }
  // CONNECTING: browser is already auto-retrying, do NOT double up
};

es.onopen = () => {
  sseReconnectAttempt = 0;                                 // reset on success
  if (sseReconnectTimer) { clearTimeout(sseReconnectTimer); sseReconnectTimer = null; }
};
```

### 4. Live audit log UI (template)

See `templates/live-audit-log-ui.html` for a drop-in component. Features:
- KPIs by level (OK / WARN / ERR / Total / Rate-per-min)
- Filter by type / message / scope (substring)
- Pause / Resume button
- Clear button
- Color-coded rows by level
- Heartbeats and `stream.open` filtered out (not security events)

## Anti-patterns

### The 429-reconnect-death-spiral

Server has rate-limiting (e.g. `express-rate-limit` at 100/15min). Frontend auto-reconnects SSE on close with a short fixed delay. Dashboard also makes periodic REST calls. Fill the window, get 429, reconnect, fill it again. Symptoms: console flooded with 429, "0 Verbundene", server says 1 client connected. Full reproduction: `references/429-reconnect-death-spiral.md`.

### Browser-extension console noise

`Permissions-Policy header: Unrecognized feature: 'private-state-token-*'`, `ObjectMultiplex - orphaned data`, `MaxListenersExceededWarning: 11 close listeners` — these are from MetaMask, Phantom, Brave Wallet content scripts. They appear on every page that has web extensions enabled, regardless of your code. Test in incognito (`Ctrl+Shift+N`) when you need a clean console. Full ID guide: `references/csp-permissions-policy-noise.md`.

### Idempotent handler hooks (no double-wrap)

If you have a `setInterval(hookSSE, 500)` that wraps `es.onmessage`, mark wrapped handlers to prevent recursive re-wrapping:

```javascript
function hookSSE() {
  const es = state.conn;
  if (!es) return;
  const origHandler = es.onmessage;
  if (origHandler && origHandler.__hooked) return;       // already hooked
  es.onmessage = (msg) => {
    if (origHandler) origHandler(msg);
    // ... bridge logic
  };
  if (es.onmessage) es.onmessage.__hooked = true;        // mark
}
```

## Quick checklist for a new SSE dashboard

- [ ] Server accepts token via both header AND query on `/api/events`
- [ ] Server bypasses auth gate silently for `/api/events` when no token is configured
- [ ] Frontend appends `?token=...` to the EventSource URL automatically
- [ ] All `fetch()` calls go through an `apiFetch()` wrapper that attaches the token
- [ ] apiFetch respects `Retry-After` header on 429 and pauses non-essential calls
- [ ] EventSource auto-reconnect uses exponential backoff (2s → 4s → 8s → 16s → 60s cap)
- [ ] Reconnect attempt counter resets on successful `onopen`
- [ ] No reconnect scheduled when `readyState === CONNECTING` (browser already retries)
- [ ] `console.log` the connection URL on connect (debug gold)
- [ ] `console.error` the readyState + url on error (debug gold)
- [ ] Filter `stream.open` and `:heartbeat` from any audit log (they aren't security events)
- [ ] CSP allows `connect-src 'self'` (default with helmet if you use `'self'`)

## Backend companion patterns

This skill focuses on the browser side. For the Express server side — rate-limiter ENV overrides, webhook dual-auth in auth-gate, global event IDs, buffer replay on reconnect, and bypass-pattern lists — see `references/sse-backend-patterns.md`.

## See also

- `vanilla-js-tdz-helper-first` — related TDZ pitfall: defining helpers AFTER functions that use them causes `Cannot access '$' before initialization` and the whole init script crashes
- `references/429-reconnect-death-spiral.md` — full case study with reproduction
- `references/csp-permissions-policy-noise.md` — browser-extension noise ID guide
- `references/sse-backend-patterns.md` — server-side patterns (rate-limiter ENV, webhook auth, global event IDs, buffer replay, auth-gate bypass)
- `templates/minimal-event-source-client.js` — drop-in client with all four patterns
- `templates/live-audit-log-ui.html` — drop-in audit log component
