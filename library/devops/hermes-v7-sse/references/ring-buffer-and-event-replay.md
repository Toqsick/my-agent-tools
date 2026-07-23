# Ring Buffer & Last-Event-ID Replay

**File:** `src/api/sse-server-v2.ts`

This is the deepest part of SSE v2 — the part that distinguishes "real replay on reconnect" from "cosmetic logging that pretends to support `Last-Event-ID`".

## The Buffer Itself

```ts
const BUFFER_SIZE = Number(process.env.SSE_BUFFER_SIZE ?? 30);
const eventBuffer: HermesSSEEvent[] = [];

function pushToBuffer(event: HermesSSEEvent & { id?: string }): void {
  eventBuffer.push({ ...event, ts: event.ts ?? new Date().toISOString() });
  if (eventBuffer.length > BUFFER_SIZE) eventBuffer.shift();
}

export function getRecentSSEEvents(limit = BUFFER_SIZE): HermesSSEEvent[] {
  const start = Math.max(0, eventBuffer.length - limit);
  return eventBuffer.slice(start);
}
```

- Plain `Array` used as a FIFO ring of length `BUFFER_SIZE` (default 30).
- On overflow, `shift()` drops the oldest entry. O(n) but `n=30`.
- Each entry is the **stamped** event object — i.e. `{ type, message, scope, level?, ts, id }`. The `id` is the global monotonic ID assigned by `nextEventId()` in `broadcastSSEv2`.
- `getRecentSSEEvents(limit)` is consumed by `/api/state/aggregate` so a freshly-loaded dashboard can show the last few events without waiting for the next live event.

## The Old Bug (Layer 8)

Before the audit fix, the code looked like this:

```ts
// BROKEN — Layer 8 bug
function writeEventToClient(client: SSEClient, event: HermesSSEEvent): boolean {
  const eid = ++eventIdCounter;        // ← per-client increment
  client.res.write(`id: ${eid}\n`);
  // ...
}
```

Three consequences:

1. **Per-client IDs**: 3 connected clients receiving the same logical broadcast event would see IDs `1`, `2`, `3` (different `id:` lines for the same broadcast). Replay math is broken by construction.
2. **Buffer had no IDs**: `pushToBuffer` was called with the *raw* event before `writeEventToClient` stamped it. The buffer never carried IDs at all.
3. **`Last-Event-ID` resume was decorative**: the header was parsed and logged (`Client X resume ab Event-ID N`), but `eventBuffer.filter(e => parseInt(e.id || '0') > N)` always returned `0` results because `e.id` was always `undefined`. No replay actually happened.

The dashboard reconnect test looked correct (server logged "replayed 0 missed events") — but that's because the count was zero for the wrong reason.

## The Three-Part Fix

```ts
// FIXED — broadcast assigns ID once, stamps it into event, passes it everywhere
export function broadcastSSEv2(event: HermesSSEEvent): void {
  const eid = nextEventId();                              // (1) ONE call
  const stampedEvent: HermesSSEEvent & { id: string } = {
    ...event,
    ts: event.ts ?? new Date().toISOString(),
    id: String(eid),
  };

  pushToBuffer(stampedEvent);                             // (2) buffer has ID

  for (const [, client] of clients) {
    // ...subscription + paused check...
    writeEventToClient(client, stampedEvent);             // (3) same object to all
  }
}

function writeEventToClient(client: SSEClient, event: HermesSSEEvent & { id: string }): boolean {
  // No more ++eventIdCounter here. Reads event.id.
  client.res.write(`id: ${event.id}\n`);
  client.res.write(`event: ${event.type}\n`);
  client.res.write(`data: ${JSON.stringify(event)}\n\n`);
  // ...
}
```

Three coupled changes:

1. **ID generation moved up** to `broadcastSSEv2`, called exactly once per logical event.
2. **Event object is stamped** with `{ id: String(eid) }` before being passed to either consumer.
3. **`writeEventToClient` signature changed** to `event: HermesSSEEvent & { id: string }` — required field, not optional. The compiler now enforces "you cannot call this without a stamped ID".

## The Replay Logic

```ts
const lastEventIdHeader = req.headers['last-event-id'] as string | undefined;
if (lastEventIdHeader) {
  const lastId = parseInt(lastEventIdHeader, 10);
  if (!Number.isNaN(lastId)) {
    client.lastSentId = lastId;
    console.log(`[SSE v2] Client ${id} resume ab Event-ID ${lastId}`);

    // P1-Fix: replay from buffer
    const missedEvents = eventBuffer.filter(e => {
      const eid = parseInt(e.id || '0', 10);
      return eid > lastId;
    });

    if (missedEvents.length > 0) {
      console.log(`[SSE v2] Client ${id} replayed ${missedEvents.length} missed events from buffer`);
      for (const evt of missedEvents) {
        writeEventToClient(client, evt as HermesSSEEvent & { id: string });
      }
    }
  }
}
```

**Important nuance:** this filter compares `parseInt(e.id || '0') > N`. The `|| '0'` is defensive (paranoia for any buffer entry without an ID — should not happen post-fix but the parse would otherwise return `NaN`, which is never `> N`). With the fix in place, every buffer entry has an ID, so the comparison is meaningful.

**Replay is bounded** by `BUFFER_SIZE`. If the disconnect was longer than the buffer window, the earliest missed events are gone — only the last 30 are replayable. Document this in the dashboard so users don't expect "infinite replay".

## Initial `stream.open` Event

When a client connects, the very first event it sees is a `stream.open` confirmation, **also stamped with a global event ID**:

```ts
const openEventId = nextEventId();
writeEventToClient(client, {
  type: 'stream.open',
  message: `Hermes SSE v2 stream connected. Subscriptions: ${...}`,
  scope: 'sse / transport',
  level: 'ok',
  id: String(openEventId),
});
client.lastSentId = openEventId;
```

This means the very first ID the client sees is non-zero and unique across reconnects. If the client reconnects with `Last-Event-ID: N`, the replay starts strictly *above* `N` — `stream.open` is never replayed (it would have an ID ≤ `lastSentId`).

## Verification Recipe (Live Test)

```bash
# 1. Connect, capture initial stream.open
curl -N "http://localhost:4321/api/events?token=super-secret" &> /tmp/sse-1.log &
CURL_PID=$!

# 2. Fire two events
curl -X POST -H "X-Hermes-Token: super-secret" -H "Content-Type: application/json" \
  -d '{"owner":"basti"}' http://localhost:4321/api/demo/claim
curl -X POST -H "X-Hermes-Token: super-secret" -H "Content-Type: application/json" \
  -d '{"channel":"telegram","type":"info","level":"ok","message":"replay test"}' \
  http://localhost:4321/api/webhook/telegram

# 3. Wait, then kill first connection
sleep 2; kill $CURL_PID

# 4. Reconnect with Last-Event-ID: 0 — should replay all missed events from buffer
curl -N -H "Last-Event-ID: 0" "http://localhost:4321/api/events?token=super-secret" | head -40
```

Expected: stream shows `stream.open` (its own new ID) + the two missed events from buffer, each with the **same** `id:` line that was assigned at broadcast time. If two open clients had been watching, they would have seen identical IDs.

## Prevention Rules

- Event IDs must be globally unique per logical event. **Assign once at the broadcaster, never at the writer.**
- The retention buffer must carry IDs. If you skip stamping, replay is impossible.
- `writeEventToClient`'s signature must require `id` (TypeScript `& { id: string }`), so the compiler refuses a non-stamped event.
- Never use `Last-Event-ID` resume alone as proof of replay — verify that `eventBuffer` is actually populated by inspecting `bufferCount` in `/api/sse-stats`.