# SSE v2 Architecture Deep-Dive

**File:** `src/api/sse-server-v2.ts`
**Header:** `X-Accel-Buffering: no` (nginx passthrough), `Content-Type: text/event-stream`

The v2 implementation is in-house (no `express-sse` dep). It adds four production-grade behaviors on top of plain SSE: backpressure handling, idle-timeout eviction, LRU cap, and heartbeat. Plus a global event-ID ring buffer for replay.

## Module-Level State

```ts
const MAX_CLIENTS     = Number(process.env.SSE_MAX_CLIENTS     ?? 100);
const IDLE_TIMEOUT_MS = Number(process.env.SSE_IDLE_TIMEOUT_MS ?? 120_000);  // 120s
const HEARTBEAT_MS    = Number(process.env.SSE_HEARTBEAT_MS    ?? 15_000);   // 15s
const BUFFER_SIZE     = Number(process.env.SSE_BUFFER_SIZE     ?? 30);

const clients: Map<string, SSEClient> = new Map();   // Insertion-order = LRU order
let   eventIdCounter = 0;                             // global, monotonically increasing
const eventBuffer: HermesSSEEvent[] = [];             // ring-buffer (Array.shift, OK @ 30)
```

The `Map` is used **deliberately** — its iteration order is insertion order, which is exactly the LRU order. `evictOldestClient()` simply takes `clients.keys().next().value` (first inserted = oldest).

## SSEClient Shape

```ts
interface SSEClient {
  id: string;             // crypto.randomUUID()
  res: Response;         // the Express response (kept open)
  connectedAt: number;    // ms epoch
  lastEventAt: number;    // updated on send OR heartbeat → idle-timer source of truth
  subscriptions: Set<string>;  // empty Set = "all events"
  lastSentId: number;     // monotonic, per-client
  paused: boolean;        // true while backpressure is active
}
```

## `handleSSEv2(req, res)` — New Connection Lifecycle

1. Generate `id = crypto.randomUUID()`.
2. Write SSE headers (`Content-Type: text/event-stream`, `Cache-Control: no-cache, no-transform`, `Connection: keep-alive`, `Access-Control-Allow-Origin: *`, `X-Accel-Buffering: no`).
3. Write initial `retry: 2500\n\n` so the browser's reconnect interval is 2.5s (matches our `Last-Event-ID` semantics).
4. **LRU check**: if `clients.size >= MAX_CLIENTS` → `evictOldestClient()`.
5. Parse `?subscriptions=foo,bar` from query → `Set<string>` (empty = all events).
6. Construct `SSEClient` object, store reference to `setInterval` heartbeat as `(client as any)._heartbeat` (for later cleanup).
7. Insert into `clients` Map → `clients.set(id, client)`.
8. Send `stream.open` event with **global** event-ID via `nextEventId()`.
9. If `Last-Event-ID: N` header present → filter `eventBuffer` for `parseInt(e.id) > N` → replay each via `writeEventToClient`.
10. Register `req.on('close', ...)` to clear heartbeat, delete from map.

## `broadcastSSEv2(event)` — One Logical Event, Many Recipients

```ts
export function broadcastSSEv2(event: HermesSSEEvent): void {
  const eid = nextEventId();                              // ← ONCE per event
  const stampedEvent = {
    ...event,
    ts: event.ts ?? new Date().toISOString(),
    id: String(eid),
  };

  pushToBuffer(stampedEvent);                             // buffer FIRST, always

  for (const [, client] of clients) {
    if (client.subscriptions.size > 0 &&
        !client.subscriptions.has(stampedEvent.type)) continue;  // filter
    if (client.paused) continue;                          // skip backpressured
    writeEventToClient(client, stampedEvent);
  }
}
```

**Critical invariant:** `nextEventId()` runs **once** per broadcast, not per client. The stamped event is passed identically to `pushToBuffer` and every `writeEventToClient`. Same logical event → same `id:` line for every recipient. This is the Layer 8 fix; without it, `Last-Event-ID` resume is meaningless.

Buffer-push runs **before** the client broadcast loop, so even events that reach no client (empty `clients` map, or everyone subscribed to something else) are still retained for late-arriving reconnects.

## Backpressure Handling — `writeEventToClient`

```ts
function writeEventToClient(client: SSEClient, event: HermesSSEEvent & { id: string }): boolean {
  const ok = client.res.write(`id: ${event.id}\n`);
  client.res.write(`event: ${event.type}\n`);
  client.res.write(`data: ${JSON.stringify(event)}\n\n`);

  if (ok) {
    client.lastSentId = parseInt(event.id, 10) || client.lastSentId;
    client.lastEventAt = Date.now();
    client.paused = false;
  } else {
    client.paused = true;
    client.res.once('drain', () => {
      client.paused = false;
      client.lastEventAt = Date.now();
    });
  }
  return ok;
}
```

`res.write()` returns `false` when the kernel send buffer is full. We **pause** that client (set `client.paused = true`) and wait for a one-shot `'drain'` event. While paused, the broadcast loop skips the client — events still flow to other clients. No client ever blocks the broadcaster.

## Idle-Timeout — `evictIdleClients()`

Runs every 10s via `startIdleTimeoutChecker()` (called once at server boot). Iterates `clients` Map; any client with `Date.now() - lastEventAt > IDLE_TIMEOUT_MS` (default 120s) is removed:

- Clear its heartbeat interval.
- `try { client.res.end() } catch {}` — close the socket.
- `clients.delete(id)`.

Note: `lastEventAt` updates on **every successful write** AND on every heartbeat send. So a client that receives heartbeats stays connected indefinitely, even with no events.

## Heartbeat — `sendHeartbeat(client)`

Writes `: heartbeat <ISO timestamp>\n\n` — a **comment line** in SSE format. The browser's `EventSource` ignores it (doesn't fire `onmessage`), but it forces a TCP write, which updates `lastEventAt` and keeps proxies from killing an idle connection.

If `res.write` returns `false` here too, `lastEventAt` is **not** updated — that's correct, the heartbeat itself is failing, so the client should be marked idle.

## LRU-Eviction — `evictOldestClient()`

```ts
function evictOldestClient(): void {
  if (clients.size === 0) return;
  const oldestKey = clients.keys().next().value!;       // first-inserted
  const oldest = clients.get(oldestKey)!;
  console.log(`[SSE v2] LRU-Eviction: Client ${oldestKey} entfernt (Max: ${MAX_CLIENTS})`);
  clearInterval((oldest as any)._heartbeat);
  try { oldest.res.end() } catch {}
  clients.delete(oldestKey);
}
```

Triggered from `handleSSEv2` **before** inserting a new client, when `clients.size >= MAX_CLIENTS`. Insertion order in a `Map` matches `set()` order, so `keys().next().value` is genuinely the oldest.

## Public Stats — `getSSEv2Stats()`

Returns `{ clients, maxClients, idleTimeoutMs, heartbeatMs, pausedCount, bufferSize, bufferCount }`. Mounted at `GET /api/sse-stats`. Useful for the dashboard's "Verbundene N" counter and for diagnosing backpressure (`pausedCount > 0` = some clients are slow to drain).

## Trade-Offs / Known Limitations

- **In-memory only**: `eventBuffer`, `clients`, `eventIdCounter` all vanish on restart. Document this in user-facing errors.
- **`Array.shift()` on the buffer is O(n)** but `n=30`, so negligible. If `BUFFER_SIZE` ever grew past ~10k, switch to a true ring with head/tail indices.
- **No event-type filtering in the buffer**: a canary-only client sees ALL missed events on replay (then filters in JS). Buffer holds all events.
- **`safeEqual`-style constant-time checks** are in `auth-gate.ts`, not here.