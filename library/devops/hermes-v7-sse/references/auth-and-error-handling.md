# Auth-Gate & Error-Handling Deep-Dive

**Files:** `src/middleware/auth-gate.ts`, `src/middleware/error-handler.ts`

## Auth-Gate (`createAuthGate`)

Single global Express middleware. Activates only when `HERMES_AUTH_TOKEN` env is set; otherwise returns a `next()` no-op (Localdev convenience). When active:

```ts
function authGate(req, res, next) {
  // Bypass: exact match OR prefix-match (for /dashboard/...)
  if (bypass.has(req.path)) return next();
  for (const p of bypass) {
    if (p.endsWith('/') && req.path.startsWith(p)) return next();
  }

  // SSE: accept either header OR ?token= query (EventSource can't set headers)
  if (req.path === '/api/events') {
    if (!token) return next();
    const presented = req.header('X-Hermes-Token') ?? req.query.token;
    if (!presented || !safeEqual(presented, token)) {
      return res.status(401).json({ ok: false, error: 'unauthorized', code: 'AUTH_REQUIRED' });
    }
    return next();
  }

  // Webhook POST: separate X-Webhook-Token, with X-Hermes-Token fallback
  if (req.path.startsWith('/api/webhook/') && req.method === 'POST') {
    const webhookToken = process.env.HERMES_WEBHOOK_TOKEN?.trim();
    if (!webhookToken) return next();
    const presented = req.header('X-Webhook-Token');
    if (presented && safeEqual(presented, webhookToken)) return next();
    const hermesToken = req.header('X-Hermes-Token');
    if (hermesToken && token && safeEqual(hermesToken, token)) return next();
    return res.status(401).json({ ok: false, error: 'unauthorized', code: 'WEBHOOK_AUTH_REQUIRED' });
  }

  // All other /api/* routes: require X-Hermes-Token
  const presented = req.header('X-Hermes-Token');
  if (!presented || !safeEqual(presented, token)) {
    console.warn(`[auth] rejected ${req.method} ${req.path} from ${req.ip} (token-presented=${Boolean(presented)})`);
    return res.status(401).json({ ok: false, error: 'unauthorized', code: 'AUTH_REQUIRED' });
  }
  next();
}
```

### Three Critical Sections

**1. Bypass logic** — exact match in `Set` OR prefix match for paths ending in `/`. This is why `'/dashboard'` and `'/dashboard/'` must both be added to `bypassPaths` (one matches the directory itself, the other matches all files inside it).

**2. SSE token source** — EventSource API can't set custom headers, so the gate reads `?token=...` from `req.query` for `/api/events`. If `HERMES_AUTH_TOKEN` is unset, the entire gate (including this SSE branch) is a no-op.

**3. Webhook carve-out (Layer 7)** — the global gate is **single-tenant** for `X-Hermes-Token`. Any secondary auth scheme (webhook, OAuth-callback, etc.) must be explicitly carved out by path+method, or the global gate eats it before the route handler runs.

### Constant-Time Comparison

```ts
function safeEqual(a: string, b: string): boolean {
  const aBuf = Buffer.from(a, 'utf-8');
  const bBuf = Buffer.from(b, 'utf-8');
  if (aBuf.length !== bBuf.length) {
    crypto.timingSafeEqual(bBuf, bBuf);   // dummy call to normalize timing
    return false;
  }
  return crypto.timingSafeEqual(aBuf, bBuf);
}
```

Defends against timing-based token recovery: a naïve `===` returns as soon as the first byte mismatches, leaking position info. `crypto.timingSafeEqual` always compares all bytes. The dummy call on length-mismatch prevents the timing channel from leaking token length.

**Tokens are never logged** — only length and boolean presence. If you add new logging, log `presented.length` and `token.length`, never the values themselves.

### `req.path` vs `req.query.token`

`req.path` does **not** include the query string. So `'/api/events?token=super-secret'` arrives as `req.path === '/api/events'` and `req.query.token === 'super-secret'`. The gate must read them separately. This is a common bug source — see Pitfalls.

## Error-Handler (`globalErrorHandler`)

Four-argument Express error middleware. Always registered last in `src/server/index.ts`:

```ts
export const globalErrorHandler: ErrorRequestHandler = (err, _req, res, _next) => {
  console.error('[ErrorHandler]', err);

  const statusCode = err.statusCode || err.status || 500;

  const response: { error: string; message?: string } = {
    error: statusCode >= 500 ? 'Internal Server Error' : 'Request Error',
  };

  // Only send the actual error message if (a) it's a client error or (b) dev mode
  if (statusCode < 500 || process.env.NODE_ENV !== 'production') {
    response.message = err.message;
  }

  res.status(statusCode).json(response);
};
```

### Response Shape

| Status range  | `error` field          | `message` field          |
|---------------|------------------------|--------------------------|
| 4xx (client)  | `'Request Error'`      | included (always)        |
| 5xx in prod   | `'Internal Server Error'` | hidden               |
| 5xx in dev    | `'Internal Server Error'` | included             |

Production hides 5xx details by default to avoid leaking stack traces / internal paths. Set `NODE_ENV=production` to enable the gate. (Note: there's a subtle bug — the condition is `statusCode < 500 || NODE_ENV !== 'production'`, which means **both** 4xx and dev-5xx get the message. In production with a 5xx, neither clause is true, so `message` stays absent. That's intentional.)

### Process-Level Handlers — `registerProcessHandlers()`

```ts
export function registerProcessHandlers(): void {
  process.on('unhandledRejection', (reason) => {
    console.error('[unhandledRejection]', reason);
    // No process.exit — Express keeps running
  });

  process.on('uncaughtException', (error) => {
    console.error('[uncaughtException]', error);
    // Could graceful-shutdown here for memory errors, but currently logs only.
  });
}
```

**Important: no `process.exit()`** — both handlers log and return. The intent is to keep the SSE bus alive even when one route handler throws an unhandled async error. In a future iteration, you might add a "memory error" detection that does graceful shutdown, but right now the trade-off favors availability over catching every crash.

## Auth-Gate ↔ Router Mount Order

The middleware order in `src/server/index.ts` is critical:

```ts
app.use(express.json());
app.use(generalLimiter);                  // ← rate limit first
app.use(createAuthGate({ token, bypassPaths: [...] }));  // ← auth second
app.use('/dashboard', express.static(...));             // ← static mounts
app.use('/api', apiRouter);                            // ← routers
app.use(globalErrorHandler);                           // ← error last
```

Why this order:

1. **Rate-limiter first** — even 401 probes count against the limit, so brute-force gets throttled.
2. **Auth-gate before routers** — every route gets auth-checked (except bypasses).
3. **Static mounts** are themselves bypassed (their paths are in `bypassPaths`).
4. **Global error handler last** — catches anything that throws downstream.

If you add a new router with a **different** auth scheme (OAuth callback, API key, etc.), it MUST come either (a) before `createAuthGate` (so the gate doesn't see it) or (b) after `createAuthGate` but with an explicit carve-out in the gate. Otherwise the global gate 401s it before the route handler runs. This is Layer 7's root cause.

## Verifying Auth Wiring

```bash
# 1. Gate is active but token wrong → expect 401 AUTH_REQUIRED
curl -i -H "X-Hermes-Token: WRONG" http://localhost:4321/api/status

# 2. Gate is active and token correct → 200
curl -i -H "X-Hermes-Token: super-secret" http://localhost:4321/api/status

# 3. Webhook with X-Webhook-Token → 200 (carve-out works)
curl -i -X POST -H "X-Webhook-Token: hook-secret" \
  -H "Content-Type: application/json" \
  -d '{"channel":"telegram","type":"info","level":"ok","message":"test"}' \
  http://localhost:4321/api/webhook/telegram

# 4. Webhook with NO token → 401 WEBHOOK_AUTH_REQUIRED (specific code, not AUTH_REQUIRED)
curl -i -X POST -H "Content-Type: application/json" \
  -d '{"channel":"telegram","type":"info","level":"ok","message":"test"}' \
  http://localhost:4321/api/webhook/telegram

# 5. /health always bypassed → 200, no header needed
curl -i http://localhost:4321/health
```

The `code` field in 401 responses is the signal: `AUTH_REQUIRED` = main gate rejection, `WEBHOOK_AUTH_REQUIRED` = webhook carve-out rejection. If you see `AUTH_REQUIRED` on a webhook call, the carve-out isn't running (token mismatch in fallback, or path doesn't match `startsWith('/api/webhook/')`).