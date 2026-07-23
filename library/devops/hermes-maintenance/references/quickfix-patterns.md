# QuickFix Patterns: Tests, Auth, Rate-Limiting (Section 12.2)

> Extracted from hermes-maintenance SKILL.md Section 12.2 (QuickFixes 1+2+3).

## QuickFix-2 PITFALL: Auth-Gate vor Static (2026-06-30)

Globaler `app.use(authGate)` läuft **VOR** `app.use('/dashboard', express.static(...))`. Resultat: Dashboard-HTML liefert 401 statt HTML.

```typescript
// ❌ FALSCH: bricht Dashboard-Laden wenn HERMES_AUTH_TOKEN gesetzt ist
app.use(createAuthGate({ token: process.env.HERMES_AUTH_TOKEN }));
app.use('/dashboard', express.static(path.join(repoRoot, 'dashboard')));

// ✅ RICHTIG: Dashboard + Root vor Auth-Gate exempt, prefix-aware
app.use(createAuthGate({
  token: process.env.HERMES_AUTH_TOKEN,
  bypassPaths: ['/health', '/dashboard', '/dashboard/'],
}));
app.use('/dashboard', express.static(path.join(repoRoot, 'dashboard')));
```

**Middleware-Anpassung für prefix-matching** (default `Set.has()` ist exact-match):
```typescript
return function authGate(req, res, next) {
  if (bypass.has(req.path)) return next();
  for (const p of bypass) {
    if (p.endsWith('/') && req.path.startsWith(p)) return next();
  }
  // ... rest of auth logic
};
```

## PITFALL #2 — Browser-EventSource-Header-Workaround (2026-06-30)

Browser-`EventSource`-API kann **keine custom Headers** setzen. Wenn der Server `X-Hermes-Token` verlangt, schickt der Browser den Stream ohne Auth → 401 → automatischer Reconnect-Loop.

**Fix (zwei Stellen):**

1. **Server-SSE-Auth akzeptiert `?token=` Query:**
```typescript
if (req.path === '/api/events') {
  if (!token) return next();   // Localdev-Bypass wenn Env-Token leer
  const headerToken = req.header('X-Hermes-Token');
  const queryToken = typeof req.query.token === 'string' ? req.query.token : null;
  const presented = headerToken ?? queryToken;
  if (!presented || !safeEqual(presented, token)) {
    return res.status(401).json({ ok: false, error: 'unauthorized', code: 'AUTH_REQUIRED' });
  }
  return next();
}
```

2. **Frontend: EventSource-URL um `?token=<default>` erweitern:**
```javascript
let url = $('sseUrl').value.trim();
const DEFAULT_TOKEN = 'super-secret';
if (url && !/[?&]token=/.test(url) && DEFAULT_TOKEN) {
  url += (url.includes('?') ? '&' : '?') + 'token=' + encodeURIComponent(DEFAULT_TOKEN);
}
const es = new EventSource(url);
```

**CORS-Default-Port-Pitfall:** `CORS_ORIGINS` defaulted zu `http://localhost:3000`. Wenn der Server auf `:4321` läuft, MUSS `CORS_ORIGINS="http://localhost:4321"` gesetzt werden.

```bash
# ✅ RICHTIG (CORS-Origin + Auth-Token zusammen):
CORS_ORIGINS="http://localhost:4321" \
  HERMES_AUTH_TOKEN=super-secret \
  HERMES_WEBHOOK_TOKEN=hook-secret \
  PORT=4321 node dist/server/index.js
```

## QuickFix-1: Smoke-Tests mit `node:test` (0 extra deps)

**Warum NICHT Vitest/Jest:** null extra-deps. Node 18+ hat natives `node:test`, ESM-kompatibel.

```javascript
// test/api-smoke.test.mjs
import { test, before } from 'node:test';
import assert from 'node:assert/strict';

const BASE = process.env.BASE_URL ?? 'http://localhost:4321';
let serverOK = false;

before(async () => {
  try {
    const r = await fetch(`${BASE}/health`, { signal: AbortSignal.timeout(2000) });
    serverOK = r.ok;
  } catch { serverOK = false; }
});

async function getJSON(path) {
  if (!serverOK) return null;
  const headers = {};
  if (process.env.X_HERMES_TOKEN) headers['X-Hermes-Token'] = process.env.X_HERMES_TOKEN;
  const r = await fetch(`${BASE}${path}`, { headers, signal: AbortSignal.timeout(3000) });
  return { status: r.status, body: r.ok ? await r.json() : null };
}

test('GET /api/status → lanes+queue+stream', async () => {
  const r = await getJSON('/api/status');
  if (!r) return;
  assert.equal(r.status, 200);
  assert.ok(Array.isArray(r.body.lanes));
});
```

**package.json:**
```json
"scripts": {
  "test": "node --test test/",
  "test:single": "node --test test/api-smoke.test.mjs"
}
```

**Lessons:** Erste Asserts oft falsch — API-Body hat nicht das Format das du annimmst. Auth-Token von Anfang an in Tests vorsehen.

## QuickFix-2: Optional-Token-Auth-Gate (`HERMES_AUTH_TOKEN` env)

**Architektur:** `createAuthGate({ token: process.env.HERMES_AUTH_TOKEN })` als Express-Middleware VOR allen Routes. Token undefined/leer → **no-op** (silent bypass). Token gesetzt → alle `/api/*` verlangen `X-Hermes-Token: <token>` Header.

```typescript
// src/middleware/auth-gate.ts
export function createAuthGate(config: { token?: string }) {
  const token = config.token?.trim();
  if (!token) {
    return function authNoop(_req, _res, next) { next(); };
  }
  const tokenBuf = Buffer.from(token, 'utf-8');
  return function authGate(req, res, next) {
    if (req.path === '/health') return next();
    let presented;
    if (req.path === '/api/events') {
      presented = req.header('X-Hermes-Token') ?? (typeof req.query.token === 'string' ? req.query.token : null) ?? undefined;
    } else {
      presented = req.header('X-Hermes-Token') ?? undefined;
    }
    if (!presented || !safeEqual(presented, token)) {
      return res.status(401).json({ ok: false, error: 'unauthorized', code: 'AUTH_REQUIRED' });
    }
    next();
  };
}

function safeEqual(a, b) {
  const aBuf = Buffer.from(a, 'utf-8');
  const bBuf = Buffer.from(b, 'utf-8');
  if (aBuf.length !== bBuf.length) {
    crypto.timingSafeEqual(bBuf, bBuf);  // dummy um Timing zu verschleiern
    return false;
  }
  return crypto.timingSafeEqual(aBuf, bBuf);
}
```

**Activation:**
```bash
# Localdev: no-op wenn HERMES_AUTH_TOKEN nicht gesetzt
PORT=4321 node dist/server/index.js

# Production:
HERMES_AUTH_TOKEN=$(openssl rand -hex 32) PORT=4321 node dist/server/index.js
```

## QuickFix-3: Granular Rate-Limiter (per-Route-Bucket)

| Limiter | Limits | Use-Case |
|---------|--------|----------|
| `generalLimiter` | 100/15min | Default Lese-Routes (status, audit, canary-read, health) |
| `canaryLimiter` | **30/15min** | Canary POST `/generate` + `/check` |
| `systemLimiter` | **120/15min** | Dashboard-Polling Mnemosyne + Cron + Health |
| `sseLimiter` | 10/min | SSE-Verbindungen (eigener Key mit X-Forwarded-For) |

```typescript
// Mount per-Route-Limiter
canaryRouter.post('/generate', canaryLimiter, handler);
canaryRouter.post('/check', canaryLimiter, handler);
app.use('/api/system', systemLimiter, systemHealthRouter);
```

**SSE-Limiter-Handler muss SSE-Format senden** (nicht JSON):
```typescript
handler: (req, res) => {
  res.status(429).setHeader('Content-Type', 'text/event-stream');
  res.send('retry: 60000\n\nevent: rate-limit\ndata: {"error":"too-many-sse-connections"}\n\n');
}
```
