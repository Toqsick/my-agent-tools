---

name: hermes-v7-sse
description: |
  Use when debugging or operating the Hermes V7 SSE package directly, reading its protocol docs, fixing an SSE event-streaming bug, or integrating a client against the hermes-v7-sse-server.
  NOT for Hermes V6 or earlier SSE work, generic HTTP streaming, or websocket-only clients — wrong package.
  Debug and operate the Hermes V7 SSE package and its protocol.
lane: worker-heavy
reasoning_effort: xhigh
author: Hermes Agent
version: 1.0.0
license: MIT
trigger_keywords: ['hermes', 'package', 'protocol', 'streaming', 'debugging']
keywords: ['hermes', 'package', 'protocol', 'streaming', 'debugging']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['a2a-bridge', 'hermes-v7-sse-server']
---
# Hermes V7 SSE Package

Node.js 18+ / Express 4 / TypeScript server with an in-house SSE v2 implementation (backpressure, idle-timeout, LRU-eviction, heartbeat). Serves a static dashboard at `/dashboard/`, exposes a JSON API, bridges to a Mnemosyne-style event bus.

**Repo:** `~/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart/hermes-v7-repo-starter/packages/hermes-sse/` · **Version:** v0.2.0 (`dist/server/index.js`)

## Run Command (Localdev)

```bash
cd ~/Dokumente/Perplexity/hermes-v7-repo-starter-node-express-v0-quickstart/hermes-v7-repo-starter/packages/hermes-sse
npm run build  # if src/ changed

CORS_ORIGINS="http://localhost:4321" \
HERMES_AUTH_TOKEN=super-secret \
HERMES_WEBHOOK_TOKEN=hook-secret \
PORT=4321 \
GENERAL_LIMITER_MAX=500 \
SSE_LIMITER_MAX=50 \
node dist/server/index.js
```

**URLs:** Dashboard `http://localhost:4321/dashboard/hermes-sse-dashboard.html` · Health `/health` (no auth) · SSE `/api/events?token=super-secret` (header OR query) · API `/api/*` (header `X-Hermes-Token: super-secret`).

## The 8-Layer SSE Connection Bug

If the user reports "dashboard doesn't connect", "0 Verbundene", "nicht erreichbar" — work through these IN ORDER. The user only sees the final symptom; the root cause is almost always one (or several) of these.

| # | Layer | Symptom | Fix |
|---|-------|---------|-----|
| 1 | CORS_ORIGINS | Browser CORS error | `CORS_ORIGINS="http://localhost:4321"`, restart |
| 2 | Auth-Gate blocks `/dashboard/*` | `curl /dashboard/...` → 401 | Add `'/dashboard', '/dashboard/'` to `bypassPaths` |
| 3 | EventSource can't set custom headers | `curl` works, browser `EventSource` fails silently | Auth gate reads `?token=` query for `/api/events` |
| 4 | Frontend must inject token into SSE URL | Browser opens, server 401s, auto-closes | `connect()` appends `?token=super-secret` |
| 5 | Frontend TDZ crash kills EventSource | Server healthy, console: `Cannot access '$' before initialization` | Move `const` helpers to TOP of `<script>`, before any init call |
| 6 | Auto-Reconnect death-spiral after 429 | Burst → connect→429→reconnect forever | `apiFetch` reads `Retry-After`; `connect()` uses exp backoff (2s→4s→8s→16s→60s) |
| 7 | Auth-Gate blocks Webhook POST (X-Webhook-Token collision) | `POST /api/webhook/...` → 401 `code: AUTH_REQUIRED` | Carve out webhook POST in `auth-gate.ts`: check `X-Webhook-Token` first, `X-Hermes-Token` fallback |
| 8 | SSE Event-ID per-client (broken Last-Event-ID replay) | Header logged, no events replayed | Generate ID once in `broadcastSSEv2()`, stamp into event, pass to `pushToBuffer` AND `writeEventToClient` |

Deep-dives: server layers → `references/sse-v2-architecture.md`, `references/ring-buffer-and-event-replay.md`, `references/auth-and-error-handling.md`. Layer 5 → `session-2026-06-30-frontend-tdz-bug.md`. Layer 6 → `session-2026-06-30-reconnect-death-spiral.md`. Layers 7-8 → `session-2026-06-30-audit-fixes-batch.md`. Live 4-layer transcript → `session-2026-06-30-4-layer-bug.md`.

## SSE Pattern Overview

The v2 implementation lives in `src/api/sse-server-v2.ts`, built around a `Map<id, SSEClient>`:

- **Backpressure**: `res.write()` returning `false` pauses the client; resumes on `'drain'`. Other clients keep receiving.
- **Idle-timeout**: 120s with no successful write → evicted. Heartbeat (15s) keeps clients alive across idle periods.
- **LRU eviction**: when `clients.size >= SSE_MAX_CLIENTS` (100), oldest `Map` entry is closed first.
- **Global event IDs**: `nextEventId()` called once per broadcast in `broadcastSSEv2`, stamped into the event, passed identically to `pushToBuffer` and every `writeEventToClient`. This makes `Last-Event-ID` resume meaningful.
- **Ring buffer**: in-memory FIFO of the last `SSE_BUFFER_SIZE` events (30). On reconnect with `Last-Event-ID: N`, buffer is filtered for `id > N` and replayed before live broadcasting. Full architecture, code, trade-offs → `references/sse-v2-architecture.md`, `references/ring-buffer-and-event-replay.md`.

## Debugging Procedure (Live-First)

1. **Server state** — `ps aux | grep "node dist/server"` + `ss -tlnp | grep 4321`. If dead, restart.
2. **Server response** — `curl /health`, `curl /api/status` with token.
3. **SSE with curl** — open in background, trigger event, check `clients`.
4. **Ask the user for browser state** — 2–4 option `clarify` call (headless browser tools can't reach `localhost:4321`).
5. **`Verbundene 0` but server says `clients: 1`** — second EventSource instance, OR main dashboard dying silently. Check console for `ReferenceError` first.
6. **`dashboard/sse-debug.html`** — minimal 4-test page isolating API+/− and SSE+/− (template: `templates/sse-debug.html`).

**Workload-Test Hammer (catches Layer 6):** burst 8–12 trigger calls in <2s — if dashboard polling then degrades into a reconnect loop, you have Layer 6:

```bash
for i in 1 2 3 4; do curl -s -X POST -H "X-Hermes-Token: super-secret" \
  -H "Content-Type: application/json" -d "{\"owner\":\"basti-$i\"}" \
  http://localhost:4321/api/demo/claim & done
wait
```

## Common API Endpoints

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /health` | none | Liveness + SSE version |
| `GET /api/status` / `/api/sse-stats` | header | Dashboard snapshot / SSE stats (`clients`, `bufferCount`, `pausedCount`) |
| `GET /api/events` | header OR `?token=` | SSE stream (v2) |
| `GET /api/canary` / `/tokens` / `/alerts` | header | Canary tokens + alerts |
| `POST /api/canary/generate` / `/check` | header | Generate token / check payload leak (body: `{"payload": "..."}`) |
| `POST /api/webhook/telegram` | `X-Webhook-Token` | Forward external alert to SSE bus |
| `POST /api/demo/{claim,gate-approve,lease-dedup}` | header | Test events: `queue.claimed`, `gate.approved`, `lease.deduped` |
| `GET /api/lanes` / `POST /api/lanes/boost-all` | header | Lane list / boost-all |

**Webhook payload:** `{"type": "...", "message": "...", "level": "ok|warn|err"}` (level strict). **Demo trigger:** `POST /api/demo/claim` with `{"owner":"basti"}` → `queue.claimed` event on SSE stream.

## Environment Variables

| Var | Default | Purpose |
|---|---|---|
| `PORT` | 3000 | Listen port |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-sep allowed origins |
| `HERMES_AUTH_TOKEN` | unset (no-op) | API+header auth |
| `HERMES_WEBHOOK_TOKEN` | unset | Webhook POST auth |
| `SSE_VERSION` | `v2` | `v1` legacy / `v2` production |
| `SSE_MAX_CLIENTS` / `SSE_IDLE_TIMEOUT_MS` / `SSE_HEARTBEAT_MS` / `SSE_BUFFER_SIZE` | 100 / 120000 / 15000 / 30 | Client cap, idle eviction, heartbeat, replay buffer |
| `TRUST_PROXY` | unset | Express `trust proxy` setting |
| `<NAME>_LIMITER_MAX` / `_WINDOW_MS` ×4 (GENERAL, CANARY, SYSTEM, SSE) | 100/30/120/10 per 900000/900000/900000/60000 ms | Rate limits (see `references/rate-limiting.md`) |

Full limiter details + `envInt()` pattern + SSE-specific 429 handler → `references/rate-limiting.md`.

## Pitfalls

- **Headless browser can't reach `localhost:4321`** — use user's local browser + F12, or curl.
- **Server PID changes on restart** — read new `session_id` from latest `terminal(background=true)`.
- **Auth-Gate is GLOBAL** — every `app.use()` before static mount needs to be in `bypassPaths`. `req.path` excludes query string; `?token=...` lives in `req.query.token`.
- **TypeScript strict-mode** — unused params need `_` prefix or build fails. Webhook `level` strict enum (only `ok|warn|err`; `info` → 400).
- **SSE-V2 store is in-memory** — restart loses all subscriptions; check `clients` AFTER connection, not at start.
- **Layer 5 — `const`/`let` TDZ in dashboard HTML** — init function called before its `const` kills whole script. See `session-2026-06-30-frontend-tdz-bug.md`.
- **Layer 6 — fixed-interval reconnect → death-spiral after 429** — always exp backoff, honor `Retry-After`. See `session-2026-06-30-reconnect-death-spiral.md`.
- **`apiFetch` mandatory** for all `/api/*` — auto-injects `X-Hermes-Token`, respects `Retry-After`. See `dashboard-api-helper-pattern.md`.
- **`setInterval(hookSSE, 500)` re-wraps `onmessage`** unless guarded with `__hooked`. **Curl + `&`** backgrounding rejected — use `terminal(background=true)`.
- **Layer 7 — Auth-Gate eats secondary auth schemes** — explicit carve-out for non-`X-Hermes-Token` routes. See `auth-and-error-handling.md`.
- **Layer 8 — Event IDs must be global, not per-client** — see `ring-buffer-and-event-replay.md`.
- **Rate-limiter ENV overrides exist** — never hardcode-lower limits; use `GENERAL_LIMITER_MAX=500 SSE_LIMITER_MAX=50` for localdev.
- **`/api/canary/detect-leak` does NOT exist** — actual endpoint is `POST /api/canary/check` body `{"payload": "..."}` → `{"ok":true,"leak":true|false}`. `/check` requires prior `/generate` (else `409 Conflict`).

## Files of Interest

- `src/server/index.ts` — Express app, middleware order, route mounts. **First place to look for connection bugs.**
- `src/middleware/auth-gate.ts` — Auth gate, bypass, SSE token, webhook carve-out → `references/auth-and-error-handling.md`
- `src/api/sse-server-v2.ts` — SSE v2: clients Map, backpressure, LRU, ring buffer, event IDs → `sse-v2-architecture.md`, `ring-buffer-and-event-replay.md`
- `src/middleware/rate-limiter.ts` — Four limiters + `envInt()` → `references/rate-limiting.md`
- `src/observability/event-bus.ts` — Central event emitter (`HermesSSEEvent`, `emitHermesEvent`)
- `src/api/canary-router.ts` / `audit-router.ts` / `webhook-router.ts` — Routers
- `src/middleware/error-handler.ts` — Global error handler + process-level handlers
- `dashboard/hermes-sse-dashboard.html` — Frontend SPA; `dashboard/sse-debug.html` — 4-test diagnostic (template: `templates/sse-debug.html`)

## Support Files

- `references/sse-v2-architecture.md` — SSE v2 module: clients Map, broadcast loop, backpressure, idle-timeout, LRU, heartbeat, public stats.
- `references/ring-buffer-and-event-replay.md` — Event-ID generation, ring buffer, `Last-Event-ID` replay, Layer 8 fix in detail.
- `references/rate-limiting.md` — Four-limiter split, `envInt()` helper, full ENV-override list, SSE-specific 429 handler.
- `references/auth-and-error-handling.md` — `createAuthGate` deep-dive (bypass, SSE token, webhook carve-out, constant-time compare), `globalErrorHandler` + process handlers.
- `references/session-2026-06-30-4-layer-bug.md` — Live 4-layer incident transcript with diffs and verify commands.
- `references/session-2026-06-30-frontend-tdz-bug.md` — Layer 5: server healthy but browser dead due to `const` TDZ in dashboard init.
- `references/session-2026-06-30-reconnect-death-spiral.md` — Layer 6: naive reconnect after 429 → permanent failure loop.
- `references/session-2026-06-30-audit-fixes-batch.md` — Layers 7-8 + Rate-Limiter ENV + Root-Redirect: 4-fix batch from Gate-Mode audit.
- `references/dashboard-api-helper-pattern.md` — Reusable `apiFetch` + token-state pattern for any auth-required dashboard.
- `templates/sse-debug.html` — Copy into `dashboard/` to isolate API+/− and SSE+/− when user can't connect.

## Workflow Expectations (User Style)

User is an **interactive tester** — wants the system LIVE first, then pokes. Reports in 1–3 word German status updates ("nicht erreichbar", "0 Verbundene"). When server is healthy but client shows different state, **ask the user what the browser shows with a 2–4 option `clarify` call** — don't keep guessing from server logs. He answers fast; dislikes open questions.