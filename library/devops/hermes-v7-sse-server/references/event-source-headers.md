# EventSource Header Limitation — Why and Workarounds

Quick reference for the W3C EventSource API constraint that breaks SSE auth when the only auth path is a custom header.

## The Problem

The W3C `EventSource` spec forbids custom headers on `new EventSource(url)`. Any `X-*` header you try to attach is silently dropped by the browser before the request hits the wire. Symptoms:

- Server returns 401 / 403, browser console shows clean `EventSource ERROR`.
- Server-side `stream.clients` counter stays at 0 despite the dashboard showing "connected".
- `stream.open` event never arrives; `EventSource.readyState` cycles between 0 (CONNECTING) and 2 (CLOSED).

```js
// BROKEN — server returns 401, EventSource can't set custom headers
new EventSource('/api/events');                      // → 401
new EventSource('/api/events', { headers: {...} });  // → headers ignored, still 401
```

## Workaround 1 — Query Token (recommended for self-hosted)

Server accepts the same token via `?token=...` query on the SSE endpoint. Browser appends it inside `connect()`:

```js
// CORRECT — server's /api/events auth-gate accepts ?token= query
new EventSource('/api/events?token=super-secret');
```

Implemented in `dashboard/hermes-sse-dashboard.html` ~line 1415. Make `DEFAULT_TOKEN` a constant overridable via the URL input so users don't have to edit the Stream-URL field.

**Caveats:** token appears in server access logs and browser history; for shared-host deployments, prefer Workaround 2.

## Workaround 2 — Server-Side Session (token-in-cookie)

After a successful `POST /api/login` sets a cookie, the SSE endpoint reads that cookie server-side and authenticates without any token in the URL. Requires a separate `/api/login` endpoint and cookies with `SameSite=Lax; HttpOnly; Secure`. Recommended when the SSE stream is consumed by a logged-in SPA.

## Workaround 3 — Short-Lived JWT in URL

Issue a 5-minute JWT on `POST /api/sse-ticket?token=<secret>`, return `{ticket, expiresAt}`. Browser passes `?ticket=<jwt>` to `new EventSource(...)`. JWT signature is verified server-side per connect; no long-lived secret travels through URLs/proxies.

**Trade-offs:** extra round-trip on every page-load; extra `/api/sse-ticket` endpoint to auth-gate-allow.

## Why Not polyfill / `fetch` + ReadableStream?

`@microsoft/fetch-event-source` and `eventsource-client` support custom headers by switching from `EventSource` to streaming `fetch`. Works in 90% of cases, but:
- Loses native browser auto-reconnect behavior (must reimplement `onerror` retry/back-off).
- Adds a dependency to the dashboard bundle.
- Some old proxies/CDNs buffer HTTP/1.1 chunked responses and break streaming.

Use polyfills only as a last resort for cross-origin scenarios where all three above workarounds fail.

## Verifying the Fix

After applying any workaround, confirm:
1. `curl -s -N "http://localhost:4321/api/events?token=super-secret"` → first lines are `retry: 2500\nid: 1\nevent: stream.open`.
2. Browser DevTools → Network → `/api/events` → status 200, `EventStream` Content-Type.
3. `curl -H "X-Hermes-Token: super-secret" http://localhost:4321/api/sse-stats` → `{clients: 1, ...}` while EventSource is open.

If `clients` reads 0 in step 3, the auth-gate still rejected the request. Check the response status (302 = redirect to dashboard-bypass land; 401 = wrong/no token).
