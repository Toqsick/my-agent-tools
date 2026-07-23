---

name: hermes-v7-sse-server
description: |
  Use when running the Hermes V7 SSE service, debugging event delivery or authentication, integrating webhooks and dashboards, or validating server and client behavior.
  NOT for generic Server-Sent Events tutorials, unrelated Express services, or configuring the Hermes messaging gateway.
  Documents the SSE-v2 server architecture, endpoints, auth and rate-limit middleware, event bus, dashboard client, tests, and operational diagnostics.
lane: worker-heavy
reasoning_effort: xhigh
author: Hermes Agent
version: 1.0.0
license: MIT
trigger_keywords: ['server', 'hermes', 'event', 'client', 'running']
keywords: ['server', 'hermes', 'event', 'client', 'running']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['hermes-mcp-integration', 'hermes-v7-sse']
---
# Hermes V7 SSE Server

The `@hermes/sse` package (in `hermes-v7-repo-starter/packages/hermes-sse/`) is an Express + SSE-v2 server with an optional token-auth-gate, rate-limiter, canary/audit bridges, webhook forwarder, and a static HTML dashboard at `/dashboard/hermes-sse-dashboard.html`. Server source in `src/server/index.ts`, client UI in `dashboard/hermes-sse-dashboard.html`, built output in `dist/`.

## Server Architecture (one-screen overview)

**Browser** → EventSource → `/api/events` (auth via `?token=` query)
**Dashboard API calls** → `fetch('/api/status')` (auth via `X-Hermes-Token` header)
**Webhook ingress** → `POST /api/webhook/:channel` (auth via `X-Webhook-Token` header)
**All events flow through** `event-bus.emitHermesEvent()` → SSE-v2 Client Map → connected dashboards.
**Auth gate** (`middleware/auth-gate.ts`) sits in front of `/api/*`; bypass list must include `/dashboard`, `/dashboard/`, `/health`, `/api/webhook/` (prefix).

Full architecture diagram, file layout, auth-gate internals, event-bus, helmet/CORS gotchas → `references/server-implementation.md`. Server-start command, systemd-user-unit, Hermes-terminal `nohup` rejection, and memory-path correction → `references/deployment.md`.

## 8-Layer Diagnostic Checklist

When the browser dashboard shows broken state, check in this exact order. Each layer has a unique symptom and a unique fix.

| # | Layer | Symptom | Fix |
|---|-------|---------|-----|
| 1 | **Port / Process** | `curl` times out, `ss -tlnp \| grep 4321` is empty | Server not running → start it (`references/deployment.md` §Server Start) |
| 2 | **CORS** | Browser console: "blocked by CORS policy", API calls fail with CORS error | `CORS_ORIGINS=http://localhost:<actual-port>` (default is `:3000`, dashboard is on `:4321`) |
| 3 | **Auth-Gate vs Static** | `curl /dashboard/...` returns 401 (HTML page) | Add `/dashboard` + `/dashboard/` to `bypassPaths` in `server/index.ts` AND prefix-match logic in `middleware/auth-gate.ts` (`bypass.has(req.path)` is exact-match only). |
| 4 | **EventSource header limitation** | Browser reports "connected" but `stream.clients` stays 0, `stream.open` event never arrives | **Browser EventSource cannot set custom `X-Hermes-Token` header.** Use `?token=...` query instead. Server-side `auth-gate.ts` already accepts query-token for `/api/events`. Frontend must append it in `connect()`. See `references/event-source-headers.md`. |
| 5 | **Frontend Temporal Dead Zone (TDZ)** | Server is fully healthy (`clients: 1` via curl), main dashboard shows red dot + console `Cannot access '$' before initialization` | Helper-using function runs at init BEFORE the `const $ = ...` declaration → TDZ ReferenceError → entire init script dies. Move all helper `const`s to the **top** of the `<script>` block. See `hermes-v7-sse` skill Layer 5. |
| 6 | **Auto-Reconnect death-spiral after 429** | SSE worked, workload burst triggered 429, dashboard now loops `connect → 429 → reconnect → 429 → ...` forever. Console fills with `EventSource ERROR: readyState: 2` | 3-part fix: (a) `apiFetch` reads `Retry-After` and sets global cooldown, (b) `connect()` uses exponential backoff (2s→4s→8s→16s→60s) with reset on OPEN, (c) optionally raise server-side `sseLimiter.max` via `SSE_LIMITER_MAX` ENV. See `hermes-v7-sse` skill Layer 6. |
| 7 | **Auth-Gate blocks Webhook POST** | `POST /api/webhook/telegram` with `X-Webhook-Token` returns 401 `AUTH_REQUIRED`, `channels: []` stays empty | Global Auth-Gate checks `X-Hermes-Token` only, doesn't know about `X-Webhook-Token`. Add path+method bypass in `auth-gate.ts` for `/api/webhook/` POST. See `hermes-v7-sse` skill Layer 7. |
| 8 | **SSE Event-ID per-client (broken replay)** | `Last-Event-ID` header accepted and logged, but no missed events replayed; same event has different IDs across clients | `writeEventToClient` generated IDs internally. Move ID generation to `broadcastSSEv2`, stamp into event object, replay from buffer on reconnect. See `hermes-v7-sse` skill Layer 8. |

**Always verify server-side state with curl before debugging the browser.** If `curl /api/sse-stats` shows `clients: 1` while a curl SSE-Stream is open, the server is fine — the browser is the problem. This is the fastest way to localize the bug.

Full server-start command, systemd unit, Hermes-terminal pitfalls, and memory-path-correction workflow → `references/deployment.md`. Previous deep-dive session (4-layer cascade) → `references/4-layer-diagnostic.md`.

## EventSource Gotcha (Browser → SSE auth)

Browsers' `EventSource(url)` cannot set custom headers — any `X-Hermes-Token` is silently dropped before the request hits the wire. Symptoms: server returns 401, `stream.clients` stays 0 despite browser showing "connected", `stream.open` never arrives. Workaround: use `?token=` query — `new EventSource('/api/events?token=super-secret')` works because the auth-gate accepts query-token for this endpoint. Full discussion + 3 workarounds (query-token, server-side session, short-lived JWT) → `references/event-source-headers.md`.

## Key Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/health` | bypass | Liveness |
| GET | `/dashboard/*` | bypass | Static HTML / assets |
| GET | `/api/status` | header `X-Hermes-Token` | Snapshot: lanes, queue, metrics, stream |
| GET | `/api/events` | header OR `?token=` | SSE-v2 stream |
| GET | `/api/sse-stats` | header | `{clients, bufferCount, pausedCount, maxClients}` |
| GET | `/api/canary` | header | Canary tokens + alerts |
| POST | `/api/canary/generate` | header | New canary token (body: `{session_id}`) |
| POST | `/api/canary/check` | header | Check payload for leak (body: `{"payload":"..."}`) — returns `{ok, leak}` |
| POST | `/api/webhook/:channel` | `X-Webhook-Token` header | External → SSE bridge (channel: telegram, slack, etc.) |
| POST | `/api/demo/claim` | header | Triggers `queue.claimed` event for smoke tests |
| GET | `/api/system/health` | header | CPU/RAM/Disk snapshot |

## Workload Burst Test (catches reconnect death-spirals)

The Layer 6 death-spiral (fixed-interval reconnect after a 429) is invisible until something triggers the 429. To surface it during localdev, run a **burst of 8-12 trigger calls in <2 seconds** (mix of `/api/demo/claim`, `/api/demo/gate-approve`, `/api/canary/generate`, `/api/webhook/telegram`). If the dashboard then degrades into a reconnect loop, the bug is present. Fix = the 3-part pattern in `hermes-v7-sse` Layer 6: `apiFetch` with `Retry-After` cooldown + exponential backoff in `connect()` + tunable server-side limits.

```bash
# Burst-hammer (no sleeps — that's the point)
for i in 1 2 3 4; do
  curl -s -X POST -H "X-Hermes-Token: super-secret" \
    -H "Content-Type: application/json" -d "{\"owner\":\"basti-$i\"}" \
    http://localhost:4321/api/demo/claim &
done
wait
# Watch browser: cycling red↔green↔red with "Reconnect in 2s (Versuch 1)" = Layer 6 OK.
```

## Smoke-Test Pattern (one bash block)

```bash
# Open SSE in background, trigger events, verify counter went up
( curl -s -N "http://localhost:4321/api/events?token=super-secret" > /tmp/sse.log 2>&1 & )
sleep 0.5
curl -s -X POST -H "X-Hermes-Token: super-secret" -H "Content-Type: application/json" \
  -d '{"owner":"basti"}' http://localhost:4321/api/demo/claim
sleep 0.3
curl -s -H "X-Hermes-Token: super-secret" http://localhost:4321/api/sse-stats
# Expected: { "clients": 1, "bufferCount": 1, ... }
```

`bufferCount > 0` after a trigger = events are queued for slow clients, not dropped. Server-side `clients` is the source of truth — never trust browser-reported counts.

## Pitfalls

- **`HERMES_AUTH_TOKEN` undefined = no-op gate.** Without the env var, the auth-gate is silent bypass (localdev-friendly). Setting it activates header-auth for `/api/*` and query-auth for `/api/events`. There is no "header only" mode.
- **`helmet` blocks EventSource** unless `crossOriginResourcePolicy: false`. Already in the code; if you add a new helmet-directive, don't re-enable CORP.
- **Subscription filter** via `?subscriptions=queue.claimed,gate.approved` — default = all. Useful for reducing noise on busy servers.
- **Server-side `clients` counter is authoritative.** Browser showing "0 Verbundene" while curl shows `clients: 1` = browser's EventSource was rejected at the auth-gate (silent disconnect).
- **Bypass paths in `auth-gate.ts` must include both bare `/dashboard` AND trailing-slash `/dashboard/`.** The `bypass.has(req.path)` check is exact — `req.path` for `/dashboard/foo.html` does NOT equal `/dashboard`. Use the `startsWith` pattern from `references/4-layer-diagnostic.md` to fix.
- **Frontend `const` TDZ crashes silently kill EventSource** — if the dashboard `<script>` block calls a helper-using function at top level before its `const` declaration, you get `ReferenceError: Cannot access '$' before initialization` and the entire init script dies. The browser never opens the EventSource. Server stays healthy. Symptom: red dot + "0 Verbundene" + console ReferenceError, even when sse-debug.html works fine. Fix: move all `const $`, `const setText` etc. to the top of the script. See `hermes-v7-sse` skill Layer 5.
- **`apiFetch` wrapper is required for all dashboard `/api/*` calls.** SSE uses `?token=` query as a workaround, but plain `fetch('/api/status')` from the dashboard cannot. Mixing `EventSource` with raw `fetch` → SSE works but every status call 401s silently. Pattern: define a global `apiFetch(path, opts)` at the top of the dashboard `<script>` that auto-injects `X-Hermes-Token`, then sweep-replace all `fetch('/api/` → `apiFetch('/api/`.
- **Fixed-interval reconnect triggers death-spirals after 429s** — never `setTimeout(reconnect, 3000)` on every `onerror`. With 1-min rate-limit windows, 2s retries produce 15 attempts/min when only 10 are allowed. Use exponential backoff (2s→4s→8s→16s→60s), reset on `OPEN`. See `hermes-v7-sse` skill Layer 6.
- **`setInterval(hookSSE, 500)` re-wraps `onmessage` every tick** unless guarded with a `__hooked` flag. Add early-return when `origHandler.__hooked === true`.
- **Default `CORS_ORIGINS` is `http://localhost:3000`.** Always override when running the dashboard on a different port.
- **The gateway does not restart this process** — use `pkill` directly. For reboot-safe operation, install the systemd-user-unit in `references/deployment.md` §Auto-Restart.

## See Also

- `references/deployment.md` — server start command, systemd-user-unit, Hermes-terminal `nohup` reject, security trade-off, memory-path correction.
- `references/server-implementation.md` — file layout, auth-gate details, SSE-v2 client map, event-bus, helmet/CORS notes, rate-limiter, webhook router.
- `references/event-source-headers.md` — why EventSource can't set headers + 3 workarounds (query token, server-side session, short-lived JWT in URL).
- `references/4-layer-diagnostic.md` — full session log of one debug cascade (port → CORS → static-bypass → EventSource-header), with curl commands and server output at each layer.
- `references/webui-not-reachable-2026-07-02.md` — "WebUI geht nicht mehr" diagnostic session (no auto-restart fix → systemd install).
- `hermes-v7-sse` skill — companion class-level umbrella covering the **5-Layer** pattern including the frontend Temporal Dead Zone bug (Layer 5) where the server is healthy but the browser-side init crashes.
