# Hermes V7 SSE-Pipeline — Production-Grade Implementation

> **Scope:** Wie man ein echtes SSE-Dashboard mit Live-Stream an Hermes V7 baut. Verified 2026-06-30 mit funktionierendem `packages/hermes-sse` v0.1.0.

---

## 1. Architektur-Überblick

```
┌─────────────────────────────────────────────────────┐
│  Browser (Dashboard)                                │
│  - EventSource('/api/events')                       │
│  - fetch('/api/status') alle 5s als Fallback        │
│  - Demo-Buttons rufen POST /api/demo/*              │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP + SSE
┌──────────────────▼──────────────────────────────────┐
│  Express Server                                     │
│  - helmet() + cors() + rate-limiter()               │
│  - /api/status → runtime-store snapshot             │
│  - /api/events → sse-server-v2.handleSSEv2()        │
│  - /api/demo/* → mutiert store + emittiert Events   │
└──────────────────┬──────────────────────────────────┘
                   │ Unix Domain Socket (optional) ODER In-Process
┌──────────────────▼──────────────────────────────────┐
│  runtime-store (in-memory)                          │
│  - lanes[] + queue[] + computed metrics             │
│  - mutation API: claimNextReady, markGateApproved,  │
│                  addLeaseConflict, updateLane       │
└──────────────────┬──────────────────────────────────┘
                   │ Aufruf
┌──────────────────▼──────────────────────────────────┐
│  event-bus                                          │
│  - emitQueueClaim, emitGateApproved, emitLeaseDedup │
│  - broadcastSSE → sse-server-v2 → alle clients      │
└─────────────────────────────────────────────────────┘
```

## 2. ENV-Flag-Pattern (v1 vs v2 Switch)

```typescript
const sseVersion = (process.env.SSE_VERSION ?? 'v2') as 'v1' | 'v2';

app.get('/api/events', sseLimiter, (req, res) => {
  if (sseVersion === 'v2') {
    handleSSEv2(req, res);
  } else {
    handleSSE(req, res);
  }
});
```

**Vorteil:** v1 und v2 parallel verfügbar, A/B-Test pro Deployment, kein Big-Bang-Risiko.

## 3. Runtime-Store mit Computed Metrics

```typescript
// FALSCH (anti-pattern):
const metrics = { activeLanes: 4, queueDepth: 12, gateBacklog: 3 };

// RICHTIG (single source of truth):
const queue: QueueCard[] = [
  { id: 'T-401', claim: 'ready', ... },
  { id: 'T-402', claim: 'blocked', ... },
];

function computeGateBacklog(): number {
  return queue.filter(c => c.claim === 'blocked' || c.claim === 'deduped').length;
}

function getRuntimeState(streamClients: number): DashboardSnapshot {
  return {
    stream: { clients: streamClients },
    metrics: {
      activeLanes: lanes.filter(l => l.active > 0).length,
      queueDepth: queue.filter(c => c.claim === 'ready' || c.claim === 'claimed').length,
      gateBacklog: computeGateBacklog(),
      leaseConflicts: queue.filter(c => c.claim === 'deduped').length,
    },
    lanes: lanes.map(l => ({ ...l })),
    queue: queue.map(c => ({ ...c })),
  };
}
```

**Vorteil:** Wenn `queue` sich ändert, stimmen KPIs automatisch. Keine Drift.

## 4. Mutation API Pattern

```typescript
// FALSCH (überall im Code):
queue[0].claim = 'claimed';
queue[0].owner = 'queen';

// RICHTIG (single entry point):
function claimNextReady(owner: string): QueueCard | null {
  const card = queue.find(item => item.claim === 'ready');
  if (!card) return null;
  card.claim = 'claimed';
  card.owner = owner;
  return card;  // Caller macht SSE-Event
}

// Im Express-Handler:
app.post('/api/demo/claim', validateBody(claimSchema), (req, res) => {
  const { owner } = req.body;
  const card = claimNextReady(owner);
  if (!card) return res.status(404).json({ ok: false, message: 'No ready task.' });
  emitQueueClaim(card.id, owner, card.mode);  // SSE-Event automatisch
  return res.json({ ok: true, card });
});
```

**Vorteil:** Validation, Logging, Event-Emission an einer Stelle. Single entry point für UI-Actions.

## 5. SSE v2 Features (Production-Grade)

```typescript
// sse-server-v2.ts Features:
const MAX_CLIENTS = Number(process.env.SSE_MAX_CLIENTS ?? 100);
const IDLE_TIMEOUT_MS = Number(process.env.SSE_IDLE_TIMEOUT_MS ?? 120_000);
const HEARTBEAT_MS = Number(process.env.SSE_HEARTBEAT_MS ?? 15_000);

// Backpressure: res.write() returnvalue → drain
function writeEventToClient(client: SSEClient, event: HermesSSEEvent): boolean {
  const ok = client.res.write(`event: ${event.type}\ndata: ${...}\n\n`);
  if (!ok) {
    client.paused = true;
    client.res.once('drain', () => { client.paused = false; });
  }
  return ok;
}

// Idle-Timeout: alle 10s checken
function evictIdleClients(): void {
  for (const [id, client] of clients) {
    if (Date.now() - client.lastEventAt > IDLE_TIMEOUT_MS) {
      client.res.end();
      clients.delete(id);
    }
  }
}

// LRU-Eviction: ältester Client raus
function evictOldestClient(): void {
  if (clients.size >= MAX_CLIENTS) {
    const oldestKey = clients.keys().next().value!;
    clients.delete(oldestKey);
  }
}

// Last-Event-ID Support (Resume nach Reload)
const lastEventId = req.headers['last-event-id'];
if (lastEventId) {
  client.lastSentId = parseInt(lastEventId, 10);
}

// Selektive Subscriptions
const subParam = req.query.subscriptions as string ?? '';
const subscriptions = new Set(subParam.split(',').map(s => s.trim()).filter(Boolean));
```

## 6. Status-Route SSE-Stats-Include

```typescript
import { getSSEv2Stats } from './sse-server-v2.js';

export function buildDashboardStatus() {
  const sseVersion = process.env.SSE_VERSION ?? 'v2';
  const streamStats = sseVersion === 'v2'
    ? getSSEv2Stats()
    : { ...getSSEStats(), maxClients: null, idleTimeoutMs: null, heartbeatMs: null, pausedCount: 0 };

  return {
    ...getRuntimeState(streamStats.clients),
    stream: { ...streamStats, version: sseVersion },
  };
}
```

Dashboard zeigt damit live: `clients: 3, maxClients: 100, heartbeatMs: 15000, idleTimeoutMs: 120000, pausedCount: 0`.

## 7. Dashboard-Frontend (vanilla JS, kein Framework)

```javascript
// State (single source of truth)
const state = {
  snapshot: null,
  events: [],
  spark: new Array(30).fill(24),
  conn: null,
};

// SSE Connect
function connect() {
  state.conn = new EventSource('/api/events');
  state.conn.onopen = () => { setConnState('connected'); fetchStatus(); };
  state.conn.onmessage = (msg) => {
    const event = JSON.parse(msg.data);
    pushEvent(event);
    if (['queue.claimed', 'gate.approved', 'lease.deduped'].includes(event.type)) {
      fetchStatus();  // Refresh KPIs nach Mutation
    }
  };
}

// Demo-Buttons (echte API, kein Mock)
async function demoClaim() {
  await fetch('/api/demo/claim', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ owner: 'queen' }),
  });
}

// Periodischer Fallback-Refresh
setInterval(fetchStatus, 5000);
```

**Vorteil:** Kein Build-Step, statisches HTML, direkt in Express-Static-Serve einbindbar.

## 8. Smoke-Test Pattern (manuell)

```bash
PORT=3030 node dist/server/index.js &
SERVER_PID=$!
sleep 2

# 1. Health
curl -s http://localhost:3030/health
# → {"ok":true,"service":"hermes-v7-sse","sse_version":"v2"}

# 2. Status (initial)
curl -s http://localhost:3030/api/status | python3 -m json.tool

# 3. Mutation
curl -s -X POST http://localhost:3030/api/demo/claim \
  -H "Content-Type: application/json" \
  -d '{"owner":"queen"}'

# 4. Status (verify mutation visible)
curl -s http://localhost:3030/api/status | python3 -m json.tool

# 5. SSE-Subscribe (5s beobachten)
timeout 5 curl -N http://localhost:3030/api/events

# 6. Cleanup
kill $SERVER_PID
```

**Expected:** alle 6 Tests grün, SSE-Stream zeigt stream.open + heartbeat.

## 9. Häufige Pitfalls

| Problem | Symptom | Lösung |
|---------|---------|--------|
| Status zeigt hardcoded values | `activeLanes: 4` obwohl Lane leer ist | Computed functions statt literals |
| SSE disconnectet nach 60s | Browser zeigt "verbinde..." | Heartbeat implementieren (15s) |
| Backpressure verlangsamt alle Clients | Ein langsamer Client bremst Stream | res.write() returnvalue checken + drain-Event |
| Last-Event-ID Header fehlt | Reload zeigt keine neuen Events | `req.headers['last-event-id']` lesen |
| Demo-Buttons rufen Mock statt API | UI zeigt was nicht im store ist | echte fetch() mit POST /api/demo/* |

## 10. Build-Report Template

Nach erfolgreichem Build:

```
~/docs/system/dashboard-build-<YYYY-MM-DD>.md

Inhalt:
- Datum + Scope
- Vorher/Nachher-Tabelle
- Architektur-Entscheidungen (warum X statt Y)
- Smoke-Test-Resultate (10/10 grün)
- Geänderte Dateien (Pfad + Größe)
- Lessons Learned
```

Plus Update: `~/docs/system/README.md` Index-Eintrag.

---

*Verified 2026-06-30, 632 Zeilen Dashboard-HTML, 1128 Zeilen TypeScript-Änderungen, 4 Files, 1 Git-Commit, 10/10 Smoke-Tests grün. Siehe `~/docs/system/dashboard-build-2026-06-30.md`.*
