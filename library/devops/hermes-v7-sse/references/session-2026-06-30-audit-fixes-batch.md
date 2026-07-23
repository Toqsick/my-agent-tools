# Session 2026-06-30 — Audit Fixes Batch (Layers 7-8 + Rate-Limiter + Root)

**Context:** Gate-Mode Audit identified 6 open items. This session fixed 4 of them in a single batch.

## Fix 1 — Rate-Limiter ENV Override (P0)

**File:** `src/middleware/rate-limiter.ts`

All 4 limiters (general, canary, system, sse) now read their `max` and `windowMs` from environment variables via a `envInt()` helper. No code changes needed to tune limits — just set `GENERAL_LIMITER_MAX=500` on server start.

**ENV vars added:**
- `GENERAL_LIMITER_MAX` (default 100), `GENERAL_LIMITER_WINDOW_MS` (default 900000)
- `CANARY_LIMITER_MAX` (default 30), `CANARY_LIMITER_WINDOW_MS` (default 900000)
- `SYSTEM_LIMITER_MAX` (default 120), `SYSTEM_LIMITER_WINDOW_MS` (default 900000)
- `SSE_LIMITER_MAX` (default 10), `SSE_LIMITER_WINDOW_MS` (default 60000)

**Test:** 20 rapid `/api/status` calls with `GENERAL_LIMITER_MAX=500` → all 200, 0 × 429.

## Fix 2 — Webhook POST Auth-Gate Bypass (P1, Layer 7)

**File:** `src/middleware/auth-gate.ts`

The global Auth-Gate was rejecting `POST /api/webhook/:channel` because the caller sends `X-Webhook-Token` (not `X-Hermes-Token`). Added a path+method-specific bypass:

```typescript
if (req.path.startsWith('/api/webhook/') && req.method === 'POST') {
  const webhookToken = process.env.HERMES_WEBHOOK_TOKEN?.trim();
  if (!webhookToken) return next(); // Localdev: no token configured
  const presented = req.header('X-Webhook-Token');
  if (presented && safeEqual(presented, webhookToken)) return next();
  // Fallback: X-Hermes-Token also accepted (for Dashboard-integration)
  const hermesToken = req.header('X-Hermes-Token');
  if (hermesToken && token && safeEqual(hermesToken, token)) return next();
  return res.status(401).json({ ok: false, error: 'unauthorized', code: 'WEBHOOK_AUTH_REQUIRED' });
}
```

**Key insight:** When a global middleware enforces auth, any secondary auth scheme must be explicitly carved out. The gate is a chokepoint — it doesn't know about route-specific token types.

**Test:** `curl -X POST -H "X-Webhook-Token: hook-secret" .../api/webhook/telegram` → `{"ok":true,"delivered":true,"channel":"telegram"}`.

## Fix 3 — Root + Favicon Bypass (P2)

**File:** `src/server/index.ts`

Added `'/'` and `'/favicon.ico'` to `bypassPaths` in `createAuthGate`. Previously `GET /` redirected to `/dashboard/...` but the Auth-Gate ran first → 401. Now `GET /` → 302 → `/dashboard/hermes-sse-dashboard.html`.

## Fix 4 — SSE Event-ID Global + Last-Event-ID Replay (P1, Layer 8)

**File:** `src/api/sse-server-v2.ts`

**Root bug:** `writeEventToClient()` called `++eventIdCounter` internally → same broadcast event had different IDs for different clients. The `Last-Event-ID` header was accepted and logged but no events were replayed (buffer had no IDs).

**Fix (3-part):**
1. `broadcastSSEv2()` calls `nextEventId()` ONCE, stamps `{ id: String(eid) }` into the event, passes it to both `pushToBuffer()` and all `writeEventToClient()` calls.
2. `writeEventToClient()` signature changed to require `HermesSSEEvent & { id: string }` — it reads the ID, doesn't generate it.
3. `handleSSEv2()` on reconnect with `Last-Event-ID: N`: filters `eventBuffer` for `parseInt(e.id) > N` and replays them.

**Test:** Generate 2 events, connect with `Last-Event-ID: 0` → stream shows `stream.open` (id:4) + `webhook.telegram` (id:1) + `queue.claimed` (id:2) + `queue.claimed` (id:3) — all 3 missed events replayed from buffer.

## Build + Restart Pattern

```bash
cd ~/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart/hermes-v7-repo-starter/packages/hermes-sse
npm run build  # tsc clean check
pkill -f "node.*hermes-sse/dist"
sleep 2
CORS_ORIGINS="http://localhost:4321" \
HERMES_AUTH_TOKEN=super-secret \
HERMES_WEBHOOK_TOKEN=hook-secret \
PORT=4321 \
GENERAL_LIMITER_MAX=500 \
SSE_LIMITER_MAX=50 \
node dist/server/index.js &
```

## Audit Doc Reference

- `~/docs/system/hermes-sse-dashboard-audit-2026-06-30.md` — Gate-Mode Audit (Phase 1-4) that identified these issues
