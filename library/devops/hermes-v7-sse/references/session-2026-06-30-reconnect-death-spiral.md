# Session 2026-06-30 — Reconnect Death-Spiral (Layer 6)

## Symptom Chain (from user)

1. ✅ "sse verbunden — Queen/Worker/Gate Live, 1 Verbundene" — working end-to-end
2. ✅ Workload test fires 11+ triggers in 2s — KPI numbers jump correctly
3. ❌ "Verbindung fehlgeschlagen SSE geschlossen status 429" — reconnect loop begins
4. ❌ Console fills with `EventSource ERROR: {readyState: 2}` repeating
5. ❌ Dashboard stays on red dot, `clients=0` server-side (because reconnects are short-lived and back-to-back)

## Root Cause

The auto-reconnect logic in `connect()` used `setTimeout(() => connect(), 3000)` on every `onerror`. Combined with a server-side `sseLimiter` of 10 connections/min, a 2s reconnect interval produces 15 attempts/min — over the limit, every one of them gets 429, every 429 triggers another reconnect, no progress.

The same problem applied to the periodic `setInterval(fetchStatus, 5000)` polling. Once any 429 lands, every poll after it hits the same window, the cooldown never elapses, the UI never recovers.

## The 3-Part Fix

### Part 1: apiFetch reads Retry-After and sets a global cooldown

```javascript
let rateLimitCooldownUntil = 0;

function apiFetch(path, opts = {}) {
  if (Date.now() < rateLimitCooldownUntil) {
    const wait = Math.ceil((rateLimitCooldownUntil - Date.now()) / 1000);
    return Promise.reject(new Error(`rate-limit-cooldown (${wait}s)`));
  }
  const userHeaders = opts.headers || {};
  const headers = {
    ...userHeaders,
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

### Part 2: SSE connect uses exponential backoff

```javascript
let sseReconnectAttempt = 0;
let sseReconnectTimer = null;

// in onerror:
if (rs === EventSource.CLOSED) {
  sseReconnectAttempt++;
  const delay = Math.min(60000, 2000 * Math.pow(2, sseReconnectAttempt - 1));
  setConnState('error', `Reconnect in ${Math.round(delay/1000)}s (Versuch ${sseReconnectAttempt})`);
  if (sseReconnectTimer) clearTimeout(sseReconnectTimer);
  sseReconnectTimer = setTimeout(() => {
    if (!state.conn || state.conn.readyState === EventSource.CLOSED) connect();
  }, delay);
}

// in onopen:
sseReconnectAttempt = 0;
if (sseReconnectTimer) { clearTimeout(sseReconnectTimer); sseReconnectTimer = null; }
```

### Part 3: Optional — raise server-side limits

For single-user localdev, the conservative defaults are over-protective. In `src/middleware/rate-limiter.ts`:

```typescript
export const sseLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 30,  // was 10 — high enough for reconnect-loops to converge
  // ...
});
```

Trade-off: high values help UX, low values protect against runaway clients. For production multi-user, keep low.

## Sweep-replace pattern for apiFetch migration

If the dashboard still has 15+ `fetch('/api/...')` calls and you need to migrate to `apiFetch`:

```bash
python3 << 'EOF'
p = 'dashboard/hermes-sse-dashboard.html'
with open(p) as f:
    c = f.read()
before = c.count("fetch('/api/")
c = c.replace("fetch('/api/", "apiFetch('/api/")
c = c.replace('fetch("/api/', 'apiFetch("/api/')
with open(p, 'w') as f:
    f.write(c)
print(f"Replaced: {before} fetch → apiFetch")
EOF

# Sanity check
grep -c "fetch('/api" dashboard/hermes-sse-dashboard.html  # should be 0
grep -c "apiFetch('/api" dashboard/hermes-sse-dashboard.html  # should be 16+
```

After the sweep, run the burst-hammer (8+ triggers in <2s). If the dashboard stays connected and KPIs stay correct, the fix is good.

## Diagnostic console.log pattern for future triage

Add these at the start of `connect()` and in `onerror`:

```javascript
console.log('[SSE] Connecting to:', url);
// in onerror:
console.error('[SSE] ERROR:', { readyState: rs, status: es.status, url: es.url });
```

User can copy-paste these into the browser console (F12) to immediately see whether the SSE layer is even being attempted, and what state it's in. Saves a round-trip of "what does the browser show?" questions.

## Lessons Embedded in the Parent Skill

- Layer 6 in the diagnostic checklist
- Workload-test hammer pattern (regression check for the fix)
- Pitfalls: "Fixed-interval reconnect → death-spiral after 429", "apiFetch is mandatory for all /api/* calls"
