# Session 2026-06-30 — The 4-Layer Connection Bug

Live incident where the dashboard "loaded but showed 0 Verbundene" — symptom of **4 stacked bugs in 4 layers**. Documented because this exact pattern will recur every time someone restarts the SSE server with auth enabled.

## Timeline (real events)

| t | User message | Diagnosis |
|---|---|---|
| 1 | "schalte dash live ich mache interaktiven test" | Server up, but CORS_ORIGINS=localhost:3000 default. Browser on :4321. → Layer 1 |
| 2 | "nicht erreichbar" | After CORS fix, dashboard HTML now returns 401. Auth-Gate global. → Layer 2 |
| 3 | "okay kann verbinden aber im doard steht 0 Verbundene" | curl `?token=` works (counter=1), browser EventSource doesn't (counter=0). → Layer 3 |
| 4 | (next) | Browser EventSource calls without token. → Layer 4 |

## Layer-by-layer fix transcript

### Layer 1: CORS
**File:** `src/server/index.ts:63`
**Bug:** `(process.env.CORS_ORIGINS ?? 'http://localhost:3000').split(',')`
**Fix on server start:** `CORS_ORIGINS="http://localhost:4321"`
**Verify:** `curl -I -H "Origin: http://localhost:4321" -H "X-Hermes-Token: super-secret" http://localhost:4321/api/status | grep -i access-control`

### Layer 2: Auth-Gate static
**Files:** `src/server/index.ts` + `src/middleware/auth-gate.ts`
**Bug:** `app.use(createAuthGate({ token: ... }))` registered globally before `app.use('/dashboard', express.static(...))`. `bypassPaths` default is `['/health']`.
**Fix:**
```ts
// server/index.ts
app.use(createAuthGate({
  token: process.env.HERMES_AUTH_TOKEN,
  bypassPaths: ['/health', '/dashboard', '/dashboard/'],
}));

// auth-gate.ts — add prefix-match support
for (const p of bypass) {
  if (p.endsWith('/') && req.path.startsWith(p)) return next();
}
```
**Verify:** `curl -o /dev/null -w "%{http_code}\n" http://localhost:4321/dashboard/hermes-sse-dashboard.html` → 200

### Layer 3: SSE-EventSource can't set headers
**File:** `src/middleware/auth-gate.ts` (SSE branch)
**Bug:** Original code accepts `?token=` query OR header. But user-set auth means default EventSource without token still gets 401.
**Fix:** When `HERMES_AUTH_TOKEN` is unset, SSE is open. When set, the browser MUST send `?token=`. Documented in `auth-gate.ts` comment. Existing `req.query.token` fallback is enough; no code change needed if layer 4 is correct.

**Verify:**
```bash
# Open stream in background
curl -s -N "http://localhost:4321/api/events?token=super-secret" &
sleep 1
# Check counter
curl -s -H "X-Hermes-Token: super-secret" http://localhost:4321/api/sse-stats
# → { "clients": 1, ... }
```

### Layer 4: Frontend injects token
**File:** `dashboard/hermes-sse-dashboard.html` `connect()` function
**Bug:** `new EventSource('/api/events')` — no token in URL.
**Fix:** Append `?token=<default>` if URL doesn't already contain one:
```js
const DEFAULT_TOKEN = 'super-secret';
if (url && !/[?&]token=/.test(url) && DEFAULT_TOKEN) {
  url += (url.includes('?') ? '&' : '?') + 'token=' + encodeURIComponent(DEFAULT_TOKEN);
}
const es = new EventSource(url);
```

**Note:** `dashboard/*.html` is served as static. No build required for frontend edits. Reload page = new code.

## Diagnostic tool created

`dashboard/sse-debug.html` — minimal 4-test page that isolates API+/− and SSE+/− in one view. User can open it in their local browser and screenshot the output. We can't reach their `localhost` from the headless browser tool.

## Lessons that became pitfalls in SKILL.md

- **Headless browser cannot reach `localhost:4321`** — never use it for visual verification of this dashboard. Ask the user.
- **Server PID changes on restart** — `process(action='kill', session_id=<old>)` returns "not_found". Read new PID from `terminal(background=true)` output.
- **TypeScript strict-mode** — unused params need `_` prefix. Build catches it immediately on `npm run build`.
- **Webhook `level` is strict enum** — `info` is rejected. Use `ok | warn | err`.
- **Curl `&` backgrounding is rejected** — use `terminal(background=true)` + `process(action='log')`.

## Why the bug was hard to find

- Each layer hides the previous. After fixing layer 1, you only see layer 2's symptom (401). After layer 2, only layer 3 (counter=0). The user can only describe the **final** symptom, not the chain.
- Server logs looked healthy through all 4 layers — only browser DevTools or the user's local browser could reveal the issue.
- The "background process completed" notifications in this session were misleading — they were old curl-SSE streams that the **server-side foreground** (not me) had killed. The actual server was always running. Don't read into background-process completion messages from earlier sessions.
