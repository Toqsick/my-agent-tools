# Server Implementation Reference — `@hermes/sse`

Internal architecture, file layout, SSE event types, and auth patterns. Load only when modifying server source or debugging internals — for run/debug/integrate workflows, see SKILL.md.

## File Layout

```
packages/hermes-sse/
├── src/
│   ├── server/index.ts                 ← Express app, helmet, cors, auth-gate, routes
│   ├── middleware/
│   │   ├── auth-gate.ts                ← Bypass list (must include /dashboard), startsWith for prefixes
│   │   └── rate-limiter.ts
│   ├── api/
│   │   ├── sse-server-v2.ts            ← Client Map, getSSEv2Stats, subscription filter
│   │   ├── canary-router.ts            ← /api/canary/*
│   │   ├── webhook-router.ts           ← /api/webhook/telegram (X-Webhook-Token)
│   │   ├── system-health-router.ts
│   │   └── ...
│   └── observability/event-bus.ts      ← emitHermesEvent — ALL events flow through here
├── dashboard/hermes-sse-dashboard.html ← Static HTML, EventSource in connect()
└── dist/                               ← tsc build output (run dist/server/index.js)
```

## Auth Gate (`middleware/auth-gate.ts`)

Central middleware. Bypass list (exact-match) plus prefix-match via `path.startsWith()`. Activated only when `HERMES_AUTH_TOKEN` env var is set; otherwise silent bypass (localdev-friendly).

**Required bypass entries** (all four must be present for the dashboard + webhook to work):
- `/health` — liveness probe
- `/dashboard` and `/dashboard/` — both bare AND trailing-slash (the `bypass.has(req.path)` check is exact-match only — `req.path` for `/dashboard/foo.html` does NOT equal `/dashboard`)
- `/api/webhook/` — prefix-bypass for webhook POSTs (the global gate only knows `X-Hermes-Token`, not `X-Webhook-Token`)

**Token sources accepted per endpoint:**
- `/api/events`: `X-Hermes-Token` header OR `?token=` query (browsers' EventSource can't set headers — query-string is the only browser option)
- `/api/webhook/:channel`: `X-Webhook-Token` header (distinct from the dashboard token)
- Everything else under `/api/*`: `X-Hermes-Token` header only

**Adding a new endpoint under `/api/*`?** Three-step checklist:
1. Add bypass entry in `auth-gate.ts` if it should be unauthenticated.
2. If using a new token type (e.g., `X-Foo-Token`), add path+method bypass entry — the global gate is `X-Hermes-Token`-only.
3. Document the endpoint in the SKILL.md "Key Endpoints" table.

## SSE-v2 Client Map (`api/sse-server-v2.ts`)

In-memory `Client` Map keyed by client-id. Each client carries: `id`, `subscriptions` (Set of event-type filters), `response` (Express `Response` object for streaming), `writeBuffer` (queue), `paused` (back-pressure flag).

Public stats surface (see `/api/sse-stats`):
```ts
{ clients: number; bufferCount: number; pausedCount: number; maxClients: number }
```
`bufferCount > 0` after a trigger = events are queued for slow clients, not dropped. **Server-side `clients` counter is authoritative** — a browser showing "0 Verbundene" while curl shows `clients: 1` means the browser's EventSource was rejected at the auth-gate (silent disconnect).

**Subscription filter:** `?subscriptions=queue.claimed,gate.approved` filters per-client event stream at registration time. Default = all events. Useful for reducing noise on busy servers.

**Per-client Event-ID (replay-on-reconnect):** `Last-Event-ID` header is accepted and logged. For real replay, IDs must be generated in `broadcastSSEv2`, stamped into the event object, and replayed from the in-memory buffer on reconnect. The legacy `writeEventToClient` path generated IDs internally per-write, which broke replay across clients.

## Event-Bus (`observability/event-bus.ts`)

Single chokepoint: `emitHermesEvent({ type, payload, ts })`. **All** events flow through here — never write directly to a client. Events are typed by `type` string (`queue.claimed`, `gate.approved`, `canary.alert`, etc.). The bus fans out to: SSE-v2 Client Map + audit log + canary correlator + (optional) webhook forwarders.

## Helmet / CORS Gotchas

- **`helmet` blocks EventSource** unless `crossOriginResourcePolicy: false` is set in the helmet config. Already in the code; if you add a new helmet-directive, don't re-enable CORP.
- **Default `CORS_ORIGINS` is `http://localhost:3000`.** Always override when running the dashboard on a different port (4321 for localdev, 8787 for the systemd unit). Multiple origins: comma-separated.

## Rate Limiter (`middleware/rate-limiter.ts`)

Three independent limiters in series: `sseLimiter` (per-IP connection cap), `apiLimiter` (per-IP request rate), `webhookLimiter` (per-channel POST rate). Configurable via env vars `SSE_LIMITER_MAX`, `API_LIMITER_RPM`, `WEBHOOK_LIMITER_RPM`. The Layer-6 death-spiral is the client-side reaction to a 429, not the limiter itself — raise `SSE_LIMITER_MAX` as one of three knobs in the burst-test fix.

## Webhook Router (`api/webhook-router.ts`)

`POST /api/webhook/:channel` where `channel ∈ {telegram, slack, ...}`. Auth via `X-Webhook-Token` header (bypass entry in auth-gate required). Body parsed as JSON and wrapped via `emitHermesEvent({ type: 'webhook.' + channel, payload: body })` to fan out to SSE subscribers. Wire this for any external bridge (Telegram bot, Slack app, GitHub webhook, etc.).
