# The 429 Reconnect-Death-Spiral

**Date:** 2026-06-30
**Context:** Hermes V7-SSE Dashboard, local dev session, port 4321, server has `express-rate-limit` at 100/15min for general API and 10/min for new SSE connections.

## The loop

1. Server has rate limiting (e.g. `express-rate-limit` 100 req / 15 min).
2. Dashboard polls status every 5s and a few other endpoints every 8s. ~12–15 calls/min, well under 100/15min.
3. User (or a stress test) fires 11 calls in 2 seconds. Combined with the polling, this fills the window fast.
4. Server returns 429 with `Retry-After: 30`.
5. Frontend gets the 429, errors out, dashboard goes red.
6. Frontend's auto-reconnect logic was: `setTimeout(connect, 3000)`.
7. After 3s, EventSource reconnects. The EventSource request itself counts against the `sseLimiter` (10/min).
8. 3 seconds later, `fetchStatus()` fires again from the `setInterval`. Still in cooldown window. 429.
9. SSE onerror fires. Auto-reconnect: 3s. Loop forever.
10. Server log shows `clients=1` (the constant reconnect counts as one) but browser shows `Verbundene: 0` because `onopen` never completes — the connection is opened then immediately rejected.

## Symptoms to recognize

- Console fills with: `Failed to load resource: 429 (Too Many Requests)` for `/api/status` AND `/api/events`
- Server returns valid health and `clients=1` (suggests one client IS connected) but the dashboard's `connCount` reads 0
- Reconnect attempts visible in Network tab every 3 seconds
- After hard reload, symptom returns within ~10 seconds

## The fix

Three changes, all in the frontend:

### 1. Exponential backoff (not flat 3s)

```javascript
let sseReconnectAttempt = 0;
let sseReconnectTimer = null;

es.onerror = (e) => {
  if (es.readyState === EventSource.CLOSED) {
    sseReconnectAttempt++;
    const delay = Math.min(60000, 2000 * Math.pow(2, sseReconnectAttempt - 1));
    // attempt 1: 2s, attempt 2: 4s, attempt 3: 8s, ... cap at 60s
    if (sseReconnectTimer) clearTimeout(sseReconnectTimer);
    sseReconnectTimer = setTimeout(() => {
      if (!state.conn || state.conn.readyState === EventSource.CLOSED) connect();
    }, delay);
  }
};

es.onopen = () => {
  sseReconnectAttempt = 0;  // reset on success
  if (sseReconnectTimer) { clearTimeout(sseReconnectTimer); sseReconnectTimer = null; }
};
```

### 2. apiFetch respects Retry-After

```javascript
let rateLimitCooldownUntil = 0;
function apiFetch(path, opts = {}) {
  if (Date.now() < rateLimitCooldownUntil) {
    const wait = Math.ceil((rateLimitCooldownUntil - Date.now()) / 1000);
    return Promise.reject(new Error(`rate-limit-cooldown (${wait}s)`));
  }
  // ... build headers, call fetch
  return fetch(path, { ...opts, headers }).then(r => {
    if (r.status === 429) {
      const ra = parseInt(r.headers.get('Retry-After') || '30', 10);
      rateLimitCooldownUntil = Date.now() + (ra * 1000);
    }
    return r;
  });
}
```

The frontend now STOPS making API calls during cooldown instead of hammering. The 429-error then catches up via try/catch in `fetchStatus()`.

### 3. Make `fetchStatus` quietly stop trying on 429

```javascript
async function fetchStatus() {
  try {
    const r = await apiFetch('/api/status');
    if (!r.ok) throw new Error('status ' + r.status);
    // ... happy path
  } catch (err) {
    if (err.message.startsWith('rate-limit-cooldown')) {
      // silently do nothing; next interval will try again
      return;
    }
    console.error('Status-Fetch fehlgeschlagen:', err);
  }
}
```

## Server-side defense (optional)

For Localdev where you don't want the limiter to bite during exploration, set generous limits at startup:

```typescript
// src/middleware/rate-limiter.ts
export const generalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: process.env.NODE_ENV === 'production' ? 100 : 5000,  // dev: very high
  // ...
});
```

Or expose a `DISABLE_RATE_LIMIT=true` env for one-off exploration runs.

## Key insight

> When the server has a rate limiter AND the client has an auto-reconnect loop, the two compose into a feedback loop. The fix is EITHER disable one OR make the other smart enough to back off based on server response.

In practice: keep the limiter (it's correct for production), make the client smart (exponential backoff + Retry-After).
