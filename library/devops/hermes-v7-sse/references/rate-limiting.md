# Rate-Limiting Pattern

**File:** `src/middleware/rate-limiter.ts`

## The Four-Limiter Split (QuickFix-3)

Instead of one global bucket (which gets eaten by chatty health polls and leaves no room for real work), there are **four** `express-rate-limit` limiters, each scoped to a class of route:

| Limiter        | Default Max | Default Window | Used For                                   |
|----------------|-------------|----------------|--------------------------------------------|
| `generalLimiter` | 100        | 15 min         | `/api/status`, `/api/audit`, canary-reads  |
| `canaryLimiter`  | 30         | 15 min         | `POST /api/canary/generate`, `/check`      |
| `systemLimiter`  | 120        | 15 min         | `/api/system/*`, Mnemosyne, Cron, Health   |
| `sseLimiter`     | 10         | 1 min          | `GET /api/events` (SSE connections)        |

`systemLimiter` is intentionally higher than `generalLimiter` because the dashboard polls `system-health`, `system-mnemosyne`, `system-cron` every 8 seconds — that's `~22 calls/min/endpoint × 3 endpoints = 67/min` baseline. 100/15min for the general bucket is fine; 120/15min for system reads gives headroom for the polling pattern.

`sseLimiter` is **per minute** (not 15 min) because SSE connections are long-lived — a 10/min budget fits the typical "open one tab, leave it open" pattern but blocks reconnect storms.

## `envInt()` Helper — The Whole Pattern in 3 Lines

```ts
function envInt(key: string, fallback: number): number {
  const v = Number(process.env[key]);
  return Number.isFinite(v) && v > 0 ? v : fallback;
}
```

Used in **every** limiter definition:

```ts
export const generalLimiter = rateLimit({
  windowMs: envWindowMs('GENERAL_LIMITER_WINDOW_MS', 15 * 60 * 1000),
  max:      envInt('GENERAL_LIMITER_MAX', 100),
  standardHeaders: true,          // sends RateLimit-* headers
  legacyHeaders: false,
  message: { error: 'Too many requests', message: 'Bitte versuche es später erneut.' },
});
```

Pattern: every limiter exports a fully-configured middleware. **Never** hardcode-lower a limit in this file — instead set the ENV var on server start.

## Full ENV Override List

| Var                          | Default | Effect                                     |
|------------------------------|---------|--------------------------------------------|
| `GENERAL_LIMITER_MAX`        | 100     | `/api/status`, audit, canary-reads / window |
| `GENERAL_LIMITER_WINDOW_MS`  | 900000  | Window for generalLimiter                  |
| `CANARY_LIMITER_MAX`         | 30      | `/api/canary/generate` + `/check` / window |
| `CANARY_LIMITER_WINDOW_MS`   | 900000  | Window for canaryLimiter                   |
| `SYSTEM_LIMITER_MAX`         | 120     | System reads / window                      |
| `SYSTEM_LIMITER_WINDOW_MS`   | 900000  | Window for systemLimiter                   |
| `SSE_LIMITER_MAX`            | 10      | New SSE connections / window               |
| `SSE_LIMITER_WINDOW_MS`      | 60000   | Window for sseLimiter (1 min)              |

Convention: `<NAME>_LIMITER_MAX` and `<NAME>_LIMITER_WINDOW_MS`. Eight total.

## SSE-Specific Rate-Limit Handler

`sseLimiter` differs from the other three because EventSource can't parse JSON error responses cleanly:

```ts
export const sseLimiter = rateLimit({
  // ... envInt + envWindowMs as above ...
  keyGenerator: (req) => {
    const forwarded = req.headers['x-forwarded-for'];
    if (typeof forwarded === 'string') return forwarded.split(',')[0].trim();
    return req.ip ?? 'unknown';
  },
  handler: (req, res) => {
    res.status(429).setHeader('Content-Type', 'text/event-stream');
    res.send('retry: 60000\n\nevent: rate-limit\ndata: {"error":"too-many-sse-connections"}\n\n');
  },
});
```

Two deviations from default:

1. **`keyGenerator`** — explicit `x-forwarded-for` split. By default `express-rate-limit` would use `req.ip`, which works only if `app.set('trust proxy', ...)` is enabled upstream. The custom generator is defensive against misconfigured proxies.
2. **`handler`** — emits an SSE-formatted 429 response with `retry: 60000` (1 minute hint) instead of JSON. The browser's `EventSource` sees a clean retry hint and stops hammering for ~1 minute.

## Localdev Workload-Test Recipe

The default `sseLimiter` (10/min) is conservative. For workload tests and burst-hammering, raise it:

```bash
CORS_ORIGINS="http://localhost:4321" \
HERMES_AUTH_TOKEN=super-secret \
HERMES_WEBHOOK_TOKEN=hook-secret \
PORT=4321 \
GENERAL_LIMITER_MAX=500 \
SSE_LIMITER_MAX=50 \
node dist/server/index.js
```

This is the exact pattern from `references/session-2026-06-30-audit-fixes-batch.md`. With these overrides, the burst-hammer (8-12 trigger calls in <2s) succeeds and you can verify Layer 6's reconnect logic without spurious 429s.

## Trade-Offs

- **High `SSE_LIMITER_MAX`** (e.g. 50 or 100) means a runaway client script can open many concurrent streams and exhaust `SSE_MAX_CLIENTS` (default 100) → LRU eviction kicks in.
- **Low `SSE_LIMITER_MAX`** (default 10) protects the server but punishes legitimate reconnects after a 429 — Layer 6's whole problem.
- **High `GENERAL_LIMITER_MAX`** (e.g. 1000) makes load tests realistic but means a real DoS won't be caught until `SSE_MAX_CLIENTS` saturates.

Production guidance: keep defaults. Localdev: raise `SSE_LIMITER_MAX=50` and `GENERAL_LIMITER_MAX=500`. Document any production override prominently.

## Related Patterns

- `express-rate-limit` ships `standardHeaders: true` which sends `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset` response headers — the dashboard's `apiFetch` reads `Retry-After` on 429 and sets `rateLimitCooldownUntil`. See `references/dashboard-api-helper-pattern.md`.
- The `429 → retry: 60000` SSE handler is what stops Layer 6's death-spiral: a fixed-interval reconnect (`setTimeout(reconnect, 3000)`) hits 10/min budget in 30s; honoring the SSE retry hint jumps to 60s and stays under budget.