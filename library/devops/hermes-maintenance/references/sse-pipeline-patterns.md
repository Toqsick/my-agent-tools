# Hermes V7.3 SSE-Pipeline — Production-Grade Pattern Details

> Extracted from hermes-maintenance SKILL.md Section 6. Full details for SSE v2 architecture, Helmet/CSP/CORS pitfalls, and rate-limiting.

## SSE v2 Production Features

- Backpressure-Handling (res.write() Returnwert → drain)
- Idle-Timeout (default 120s, ENV-tunable)
- Max-Clients (default 100, LRU-Eviction)
- Last-Event-ID Support (Resume nach Reload)
- Selektive Subscriptions (Query-Param)
- Heartbeat (default 15s)

**Architecture Decision: ENV flag statt hardcoded v2**
```
SSE_VERSION=v2   # v1=legacy, v2=production
SSE_MAX_CLIENTS=100
SSE_IDLE_TIMEOUT_MS=120000
SSE_HEARTBEAT_MS=15000
```

Vorteil: pro Deployment schaltbar, Vergleich/Migration einfach, kein Big-Bang-Risiko.

## Runtime-Store Pattern: Computed Metrics > Hardcoded

```typescript
// FALSCH: hardcoded in store
const metrics = { activeLanes: 4, queueDepth: 12, gateBacklog: 3 };

// RICHTIG: computed aus queue
function computeGateBacklog(): number {
  return queue.filter(c => c.claim === 'blocked' || c.claim === 'deduped').length;
}
```

Vorteil: Single source of truth = `queue` Array. Konsistenz garantiert. Wenn queue sich ändert, stimmen KPIs automatisch.

**Mutation API statt direct state access:**

```typescript
// FALSCH:
queue[0].claim = 'claimed';
queue[0].owner = 'queen';

// RICHTIG:
function claimNextReady(owner: string): QueueCard | null {
  const card = queue.find(item => item.claim === 'ready');
  if (!card) return null;
  card.claim = 'claimed';
  card.owner = owner;
  emitQueueClaim(card.id, owner, card.mode);  // SSE-Event automatisch
  return card;
}
```

Vorteil: Validation, Logging, Event-Emission an einer Stelle. Single entry point für UI-Actions.

**Vollständiges Pattern in `references/sse-pipeline-v2.md`.**

## Helmet SSE-Blocker (kritischer Pitfall)

**Symptom:** Browser-EventSource verbindet sich nicht, Console zeigt entweder nichts oder "EventSource's response has a MIME type ('text/html')". Server-seitig sieht alles gut aus (`curl /api/events` zeigt 200 + `text/event-stream`).

**Ursache:** Helmet-Default `Cross-Origin-Resource-Policy: same-origin` blockt Browser-EventSource wenn Origin-Header nicht 100% matched. SSE über Localhost mit anderem Port (z.B. Dashboard 3001, Server 3000) ist der typische Trigger.

**Diagnose:**
```bash
curl -s -i http://localhost:3001/api/events | grep -i cross-origin
# Wenn "Cross-Origin-Resource-Policy: same-origin" → Bug da
```

**Fix:** Helmet-Konfiguration beim Server-Setup lockern:
```typescript
import helmet from 'helmet';
app.use(helmet({
  crossOriginResourcePolicy: false,  // SSE + Static-Assets brauchen das
  crossOriginEmbedderPolicy: false,  // Optional: für iframe-Embeds
}));
```

`crossOriginOpenerPolicy: 'same-origin'` und CSP bleiben aktiv — nur die Resource-Policy muss auf, weil SSE eine Cross-Origin-Resource ist.

**Lesson (2026-06-30):** Bei SSE-Setups IMMER Helmet-Cross-Origin-Resource-Policy prüfen. Default ist same-origin, das blockt Browser. Andere Security-Header (CSP, X-Frame-Options) bleiben intakt.

## CSP inline-script Blocker (Helmet default)

**Symptom:** Dashboard-UI lädt, sieht aber komplett tot aus. Browser-Console zeigt:
```
hermes-sse-dashboard.html:565 Executing inline script violates the following
Content Security Policy directive 'script-src 'self''. Either the 'unsafe-inline'
keyword, a hash ('sha256-...'), or a nonce ('nonce-...') is required to enable
inline execution. The action has been blocked.
```

**Ursache:** Helmet-Default CSP setzt `script-src 'self'` ohne `'unsafe-inline'`. Dashboard hat aber Inline-`<script>`-Block (single-file vanilla-JS-Pattern). Helmet blockt das, weil CSP default-strict ist.

**Diagnose (schnell):**
```bash
curl -s -i http://localhost:<port>/dashboard/hermes-sse-dashboard.html | grep -i "content-security"
# → Content-Security-Policy: ...;script-src 'self';... (ohne 'unsafe-inline' = Bug da)
```

**Fix:** Helmet-CSP explizit konfigurieren mit `'unsafe-inline'` für lokale Dev-Dashboards:
```typescript
import helmet from 'helmet';
app.use(helmet({
  crossOriginResourcePolicy: false,  // SSE
  crossOriginEmbedderPolicy: false,
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],   // ← für Inline-Scripts
      styleSrc: ["'self'", "'unsafe-inline'", "https:"],  // fontshare etc.
      fontSrc: ["'self'", "https:", "data:"],
      imgSrc: ["'self'", "data:"],
      connectSrc: ["'self'"],  // EventSource + fetch
    },
  },
}));
```

**Production-Hardening (statt 'unsafe-inline'):** Inline-Script als externe `.js` auslagern, dann braucht es nur `'self'`. Für lokale Single-User-Dashboards ist 'unsafe-inline' OK.

**Lesson (2026-06-30):** SSE-Dashboards brauchen IMMER Helmet-Custom-Config. Der Default ist zu strikt. `crossOriginResourcePolicy: false` + `script-src: unsafe-inline` + `connect-src: self` ist das Minimum.

## CORS-Origin-Array-Pitfall

**Symptom:** `cors({ origin: allowedOrigins })` mit `allowedOrigins = ['http://localhost:3001']` (Array) setzt **keinen** `Access-Control-Allow-Origin` Header wenn der Request **keinen** Origin-Header hat (z.B. curl ohne `-H Origin:`). Browser schickt aber immer Origin → CORS sollte funktionieren.

**Diagnose (was Browser vs. Curl sehen):**
```bash
# KEIN Origin-Header (curl default):
curl -s -i http://localhost:3001/api/status
# → KEIN Access-Control-Allow-Origin (das ist OK so)

# MIT Origin-Header (Browser-style):
curl -s -i -H "Origin: http://localhost:3001" http://localhost:3001/api/status
# → Access-Control-Allow-Origin: http://localhost:3001 (das ist richtig)
```

**Falsche Diagnose:** "CORS-Header fehlt" → ist nur sichtbar wenn curl Origin mitschickt.

**Preflight-Test (echter Browser-Style):**
```bash
curl -s -i -X OPTIONS \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: content-type" \
  http://localhost:3001/api/events
# → HTTP/1.1 204 No Content
# → Access-Control-Allow-Origin: http://localhost:3001
# → Vary: Origin, Access-Control-Request-Headers
```

**Lesson:** CORS-Bug-Diagnose IMMER mit echtem Origin-Header machen, nicht mit nacktem curl. Browser schickt immer Origin, Curl nur wenn man es explizit anfordert.

## SSE-Rate-Limit (10/60s default)

**Symptom:** Browser-Dashboard verbindet einmal, dann plötzlich nicht mehr. Console zeigt nichts. Server-Logs zeigen "RateLimit-Limit: 10, Remaining: 0".

**Ursache:** SSE-Endpoint hat standardmäßig `sseLimiter` (10 Verbindungen pro 60s pro IP). Wer beim Dev zu viel F5/Ctrl+Shift+R drückt, ist raus.

**Verifikation:**
```bash
curl -s -i http://localhost:3001/api/events | grep -i ratelimit
# → RateLimit-Policy: 10;w=60
# → RateLimit-Limit: 10
# → RateLimit-Remaining: 0 (wenn blockiert)
```

**Fix (wenn man drüber stolpert):**
- ENV: `SSE_RATE_LIMIT=100` in Server-Start
- Oder warten bis Window zurücksetzt (60s)
- Oder `express-rate-limit` Config in `middleware/rate-limiter.ts` lockern

**Lesson:** SSE-Rate-Limit ist gut für Production, aber nervig beim Dev. Bei `npm run dev` immer wieder Pausen oder Limit rauf setzen.

## SSE-Aggregate Route mit Ring-Buffer Retention (C-4)

**Use-Case:** Hermes-v7 Dashboard hat 2 Datenpfade (SSE-Stream + Polling für Status/Security). User will SSE als Single-Source-of-Truth. Polling bleibt für Time-Varying-Disk-Stats.

**Architektur:**

1. **Server-seitiger Ring-Buffer in `sse-server-v2.ts`** (default 30, SSE_BUFFER_SIZE env-override):
```typescript
const BUFFER_SIZE = Number(process.env.SSE_BUFFER_SIZE ?? 30);
const eventBuffer: HermesSSEEvent[] = [];

function pushToBuffer(event: HermesSSEEvent): void {
  eventBuffer.push({ ...event, ts: event.ts ?? new Date().toISOString() });
  if (eventBuffer.length > BUFFER_SIZE) eventBuffer.shift();
}

export function getRecentSSEEvents(limit = BUFFER_SIZE): HermesSSEEvent[] {
  const start = Math.max(0, eventBuffer.length - limit);
  return eventBuffer.slice(start);
}

// pushToBuffer() wird IN broadcastSSEv2() aufgerufen, VOR dem Client-Loop
// → auch ohne aktive Clients: Buffer füllt sich
```

2. **Aggregate-Route (separates File)**:
```typescript
// /api/state/aggregate — 1 GET liefert Snapshot + RecentEvents
export const stateAggregateRouter = Router();
stateAggregateRouter.get('/aggregate', (req, res) => {
  const limit = Math.min(Number(req.query.limit ?? BUFFER_SIZE), 100);
  res.json({
    ok: true,
    enabled: process.env.HERMES_USE_AGGREGATE === 'true',
    ts: new Date().toISOString(),
    recentCount: getRecentSSEEvents(limit).length,
    snapshot: buildDashboardStatus(),  // ← kompletter /api/status payload
    recentEvents: getRecentSSEEvents(limit),
  });
});
```

3. **Trade-offs (transparent):**
   - ✅ Polling-Reduce von 2s→8s = 75% weniger Requests für Security-Tab
   - ✅ Snapshot im Buffer auch ohne aktive Clients
   - ⚠️ Array.shift() O(n) bei Ring-Push — bei 30 OK, bei Size=1000 rechenintensiv
   - ⚠️ In-Memory only (kein Persist) — Server-Restart = leerer Buffer
   - ⚠️ Initial-Payload 1-1.5KB statt 3 separate Requests à 200-500B

**Lesson (2026-06-30, C-4):** Ring-Buffer für SSE-Aggregate ist effizienteste Brücke zwischen Polling und SSE-Only — keine DB nötig, kein Subprocess, ~7.5KB RAM bei Size=30. Implementation in ~20 LoC pro File.

## Trust-Proxy für Express hinter nginx/Cloudflare

**Symptom:** Lokal funktioniert Rate-Limiter + Auth-Gate. Hinter nginx/Cloudflare tun sie nicht mehr weil `req.ip` immer `127.0.0.1` ist (= Express selber), alle Clients teilen sich einen Bucket.

**Fix (env-gesteuert, default-secure):**
```typescript
// src/server/index.ts
const trustProxy = process.env.TRUST_PROXY;
if (trustProxy !== undefined) {
  const num = Number(trustProxy);
  app.set('trust proxy', Number.isFinite(num) ? num : trustProxy);
}
```

**Werte:**
- `TRUST_PROXY=1` → 1-Hop (Standard nginx-setup)
- `TRUST_PROXY=true` → alle Hops (nur private Networks!)
- `TRUST_PROXY=loopback` → nur 127.0.0.1/::1
- nicht gesetzt = off (default sicher, aber Bug hinter Proxy)

**Lesson:** Immer wenn Hermes-V7-SSE hinter reverse-proxy deployed wird, MUSS `TRUST_PROXY` gesetzt sein. Sonst teilen alle Enduser denselben Rate-Limit-Bucket (= Limiter unbrauchbar).
