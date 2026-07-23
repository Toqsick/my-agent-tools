# 4-Layer Diagnostic Cascade — Hermes V7 SSE Server

Session log: 2026-06-30, debugging the `@hermes/sse` package from `hermes-v7-repo-starter/packages/hermes-sse/` on Basti's desktop. The user reported "0 Verbundene" in the browser dashboard. Each layer had to be cleared before the next symptom surfaced.

## Layer 1 — Port / Process

**Symptom:** Browser → "Site not reachable". Curl → timeout.
**Check:** `ss -tlnp | grep 4321` → empty. `ps aux | grep "node dist/server"` → empty.
**Cause:** Server not running.
**Fix:** Start it (see SKILL.md "Server Start"). Foreground first, then background with `terminal(background=true, notify_on_complete=true)`.

```bash
cd .../packages/hermes-sse
CORS_ORIGINS="http://localhost:4321" \
HERMES_AUTH_TOKEN=super-secret \
HERMES_WEBHOOK_TOKEN=hook-secret \
PORT=4321 \
node dist/server/index.js
```

**Verification:** `curl -s http://localhost:4321/health` → `{"ok":true,"service":"hermes-v7-sse","sse_version":"v2"}`.

## Layer 2 — CORS

**Symptom:** Browser loads HTML, but JS API calls fail with "blocked by CORS policy". No data in dashboard.
**Check:**
```bash
curl -s -I -H "Origin: http://localhost:4321" \
  -H "X-Hermes-Token: super-secret" \
  http://localhost:4321/api/status | grep -i access-control
```
**Cause:** Server's `CORS_ORIGINS` defaulted to `http://localhost:3000`, but dashboard is on `:4321`.
**Fix:** Set `CORS_ORIGINS=http://localhost:4321` env var, restart.
**Verification:** `Access-Control-Allow-Origin: http://localhost:4321` in response headers.

## Layer 3 — Auth-Gate vs Static Dashboard

**Symptom:** `curl /dashboard/hermes-sse-dashboard.html` → 401 with JSON body. Browser shows the page only because it ignores the 401, but the response isn't HTML.
**Check:**
```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  http://localhost:4321/dashboard/hermes-sse-dashboard.html
# → 401 (should be 200)
```
**Cause:** The `auth-gate.ts` middleware has `bypassPaths: ['/health']` by default. The global `app.use(createAuthGate(...))` runs before `app.use('/dashboard', express.static(...))`, so the static mount never gets a chance to respond — the gate rejects first.
**Fix:** Two-part fix because `req.path` is the *full* path, not the mount-prefix.
1. In `server/index.ts`, expand the bypass config:
   ```ts
   app.use(createAuthGate({
     token: process.env.HERMES_AUTH_TOKEN,
     bypassPaths: ['/health', '/dashboard', '/dashboard/'],
   }));
   ```
2. In `middleware/auth-gate.ts`, the `bypass.has(req.path)` check is exact-match only. Add a prefix-match loop for paths ending in `/`:
   ```ts
   if (bypass.has(req.path)) return next();
   for (const p of bypass) {
     if (p.endsWith('/') && req.path.startsWith(p)) return next();
   }
   ```
**Verification:**
- `curl /dashboard/hermes-sse-dashboard.html` → 200
- `curl /api/status` (no header) → 401 (gate still works for API)
- `curl /api/status -H "X-Hermes-Token: super-secret"` → 200

**Side bug found:** TypeScript strict-mode rejects `_res` rename if `res` is referenced later. Keep the original param name; use the loop pattern.

## Layer 4 — EventSource Header Limitation

**Symptom:** Browser shows green conn-dot, "Verbunden mit /api/events" message, but the "Verbundene" counter stays at 0. The dashboard renders, but `stream.clients` is always 0.
**Check (the critical step):** Open a curl SSE-Stream and trigger events from another terminal.
```bash
# Terminal 1: open SSE
curl -s -N "http://localhost:4321/api/events?token=super-secret"
# Terminal 2: status check
curl -s -H "X-Hermes-Token: super-secret" http://localhost:4321/api/sse-stats
# → { clients: 0 } if no curl-Stream is currently open
# → { clients: 1 } if a curl-Stream is open RIGHT NOW
```
**Cause:** The browser's `EventSource` API does NOT support custom request headers. The dashboard's `connect()` calls `new EventSource('/api/events')` without `?token=`, and without the `X-Hermes-Token` header. The server's auth-gate rejects with 401 (or, in current code, returns 401 JSON for `/api/events`). EventSource treats 401 as fatal and closes the connection silently — the server never registers the client, so `stream.clients` stays 0.
**Fix:** Two-part, server + client.
1. **Server** (`middleware/auth-gate.ts`): `/api/events` must accept `?token=` query for EventSource. Make the no-env-var case a no-op (localdev convenience):
   ```ts
   if (req.path === '/api/events') {
     if (!token) return next();  // localdev: no token configured, pass through
     const headerToken = req.header('X-Hermes-Token');
     const queryToken = typeof req.query.token === 'string' ? req.query.token : null;
     const presented = headerToken ?? queryToken;
     if (!presented || !safeEqual(presented, token)) {
       return res.status(401).json({ ok: false, error: 'unauthorized', code: 'AUTH_REQUIRED' });
     }
     return next();
   }
   ```
2. **Client** (`dashboard/hermes-sse-dashboard.html`, in `connect()`): append `?token=<default>` to the URL.
   ```js
   let url = $('sseUrl').value.trim();
   const DEFAULT_TOKEN = 'super-secret';
   if (url && !/[?&]token=/.test(url) && DEFAULT_TOKEN) {
     url += (url.includes('?') ? '&' : '?') + 'token=' + encodeURIComponent(DEFAULT_TOKEN);
   }
   const es = new EventSource(url);
   ```
**Verification:** Reload the dashboard (Ctrl+Shift+R). Counter should show "1 Verbundene", SSE-Log tab should populate with `stream.open` + heartbeat events every 15s.

## Cross-Layer Smoke (all 4 green)

```bash
# After all fixes, the following should show clients=1 + bufferCount>=1
( curl -s -N "http://localhost:4321/api/events?token=super-secret" > /tmp/sse.log 2>&1 & )
sleep 0.5
curl -s -X POST -H "X-Hermes-Token: super-secret" -H "Content-Type: application/json" \
  -d '{"owner":"basti"}' http://localhost:4321/api/demo/claim
curl -s -X POST -H "X-Hermes-Token: super-secret" -H "Content-Type: application/json" \
  -d '{"session_id":"smoke","marker":"sk-can-SMOKE","traffic":"leak sk-can-SMOKE","severity":"CRITICAL"}' \
  http://localhost:4321/api/canary/detect-leak
curl -s -X POST -H "X-Webhook-Token: hook-secret" -H "Content-Type: application/json" \
  -d '{"type":"test","message":"🔗 Pipeline-Smoke","level":"warn"}' \
  http://localhost:4321/api/webhook/telegram
sleep 0.5
curl -s -H "X-Hermes-Token: super-secret" http://localhost:4321/api/sse-stats
# Expected: { "clients": 1, "bufferCount": 1, ... }
```

Triggers that come through as SSE events in this run: `queue.claimed` (from demo/claim). Canary + Webhook may also appear depending on subscription filter defaults.

## Lesson

The cascade happens because each layer masks the next. The fix-the-obvious-thing-then-test pattern means you only see the next layer's symptom after the previous one is cleared. **Always verify with curl that server-side state is correct** before chasing browser-side symptoms. If `curl /api/sse-stats` shows `clients: 0` while your curl-SSE is open, the problem is in your test setup (forgot `?token=`, server rejected, etc.) — not in the server.
