# SSE Backend Patterns — Express + event-bus + rate-limiter

Server-side companion to the frontend patterns. All patterns tested with the Hermes V7 SSE server (Express + TypeScript, SSE v2).

## 1. Rate-Limiter ENV-Override (P0 — prevents 429-death-spiral during testing)

**Problem:** Hardcoded rate-limits (e.g. `max: 100` per 15min) fill up during interactive dashboard testing because the dashboard itself polls 3-5 endpoints every 5-8 seconds. Once the bucket is full, ALL `/api/*` calls return 429 — including `fetchStatus` — making the dashboard unusable for 15 minutes.

**Fix:** Every `express-rate-limit` instance reads its `max` and `windowMs` from ENV with a safe fallback.

```typescript
function envInt(key: string, fallback: number): number {
  const v = Number(process.env[key]);
  return Number.isFinite(v) && v > 0 ? v : fallback;
}

export const generalLimiter = rateLimit({
  windowMs: envInt('GENERAL_LIMITER_WINDOW_MS', 15 * 60 * 1000),
  max: envInt('GENERAL_LIMITER_MAX', 100),
  // ...
});
```

**Dev/Test startup with relaxed limits:**
```bash
GENERAL_LIMITER_MAX=500 SSE_LIMITER_MAX=50 node dist/server/index.js
```

**ENV variable naming convention:**
- `GENERAL_LIMITER_MAX` / `GENERAL_LIMITER_WINDOW_MS`
- `CANARY_LIMITER_MAX` / `CANARY_LIMITER_WINDOW_MS`
- `SYSTEM_LIMITER_MAX` / `SYSTEM_LIMITER_WINDOW_MS`
- `SSE_LIMITER_MAX` / `SSE_LIMITER_WINDOW_MS`

## 2. Webhook Dual-Auth in Auth-Gate

**Problem:** A global auth-gate middleware checks `X-Hermes-Token` on ALL `/api/*` routes. But webhooks from external systems authenticate via a separate `X-Webhook-Token`. The auth-gate blocks webhook POSTs with 401 before they reach the webhook router.

**Fix:** Auth-gate detects webhook POST routes and delegates auth to the `X-Webhook-Token` check:

```typescript
// In auth-gate middleware:
if (req.path.startsWith('/api/webhook/') && req.method === 'POST') {
  const webhookToken = process.env.HERMES_WEBHOOK_TOKEN?.trim();
  if (!webhookToken) return next();                    // Localdev: no token configured
  const presented = req.header('X-Webhook-Token');
  if (presented && safeEqual(presented, webhookToken)) return next();
  // Fallback: also accept X-Hermes-Token (for dashboard integration)
  const hermesToken = req.header('X-Hermes-Token');
  if (hermesToken && token && safeEqual(hermesToken, token)) return next();
  return res.status(401).json({ ok: false, error: 'unauthorized', code: 'WEBHOOK_AUTH_REQUIRED' });
}
```

**Key insight:** `GET /api/webhook` (status read) still requires `X-Hermes-Token`. Only `POST /api/webhook/:channel` uses the dual-auth path.

## 3. Global SSE Event IDs (not per-client)

**Problem:** If `writeEventToClient` increments the event-ID counter per client, the same logical event gets different IDs for different clients. `Last-Event-ID` resume is broken because client A's event ID 5 is a different event than client B's event ID 5.

**Fix:** Assign the global event ID ONCE in the broadcast function, then thread the stamped event to all clients:

```typescript
export function broadcastSSEv2(event: HermesSSEEvent): void {
  const eid = ++eventIdCounter;                    // ONCE, globally
  const stampedEvent = {
    ...event,
    ts: event.ts ?? new Date().toISOString(),
    id: String(eid),
  };
  pushToBuffer(stampedEvent);                      // buffer gets the same ID
  for (const [, client] of clients) {
    writeEventToClient(client, stampedEvent);      // clients get the same ID
  }
}
```

**`writeEventToClient` must NOT increment the counter** — it receives the event already stamped with its ID.

## 4. Buffer Replay on Reconnect (Last-Event-ID)

**Problem:** When a client reconnects with `Last-Event-ID: 42`, the server sets `client.lastSentId = 42` but never sends the events the client missed while disconnected.

**Fix:** On connect, check the `Last-Event-ID` header, filter the retention buffer for events with `id > lastId`, and replay them:

```typescript
const lastEventIdHeader = req.headers['last-event-id'] as string | undefined;
if (lastEventIdHeader) {
  const lastId = parseInt(lastEventIdHeader, 10);
  if (!Number.isNaN(lastId)) {
    client.lastSentId = lastId;
    const missedEvents = eventBuffer.filter(e => {
      const eid = parseInt(e.id || '0', 10);
      return eid > lastId;
    });
    if (missedEvents.length > 0) {
      console.log(`[SSE v2] Client replayed ${missedEvents.length} missed events from buffer`);
      for (const evt of missedEvents) {
        writeEventToClient(client, evt);
      }
    }
  }
}
```

**Limitation:** Buffer is in-memory with a fixed size (default 30). If the client was disconnected longer than it takes to fill and rotate the buffer, some events are permanently lost. For full reliability, pair with a persistent audit log.

## 5. Auth-Gate Bypass Patterns

Static assets and public endpoints must bypass the auth-gate. Use both exact match AND prefix match:

```typescript
const bypass = new Set(['/health', '/dashboard', '/dashboard/', '/', '/favicon.ico']);

if (bypass.has(req.path)) return next();
for (const p of bypass) {
  if (p.endsWith('/') && req.path.startsWith(p)) return next();
}
```

**Common bypass list:**
- `/health` — healthcheck endpoint
- `/dashboard` + `/dashboard/` — static HTML files (browser can't send auth headers on initial page load)
- `/` — root redirect to dashboard
- `/favicon.ico` — browser auto-request

## Quick backend checklist

- [ ] Every `rateLimit()` reads `max` and `windowMs` from ENV
- [ ] Auth-gate bypasses static HTML, root redirect, and favicon
- [ ] Auth-gate delegates webhook POSTs to `X-Webhook-Token`
- [ ] `broadcastSSEv2` assigns event ID globally (once per event)
- [ ] `writeEventToClient` does NOT assign IDs (receives pre-stamped event)
- [ ] Retention buffer stores events WITH their global IDs
- [ ] `Last-Event-ID` header triggers buffer replay on reconnect
- [ ] SSE heartbeat (15s) and idle-timeout (120s) are configurable via ENV
