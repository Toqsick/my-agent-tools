# Cache-Hit Audit Event — hermes-v7 V7.2 worker-bee A4 patch

## Context

Companion to `intent-hash-chain-hermes-v7.md` (A1: schema + gate for `intentHash`) and `idempotency-key-attestation-hermes-v7.md` (A2: schema addition for `cacheHit` / `idempotencyKey` / `cachedResult`).

This file documents **A4**: the **runtime audit-log event** that makes the Idempotency-Cache bypass visible to ReviewerA. Without it, the schema additions from A2 would be inert — `cacheHit: true` would sit on the `ToolCall` but the audit trail would still contain a normal `intent`/`result` pair for an execution that never actually happened.

## The Gap

After A2 added the schema fields, the runtime path in `src/runtime/tool-runtime.ts → runAtomicToolCall()` had an explicit decision at the top:

```typescript
// Wichtig: KEIN logIntent + KEIN invoke() → KEINE Doppel-Ausführung und
// KEIN Schritt-6-Audit-Event (Result wäre eine Täuschung, der Call lief
// nicht). Stattdessen wird der Cache-Hit per `[CACHE-HIT]`-Note dokumentiert.
```

That comment was correct in *spirit* (no fake result-event) but wrong in *mechanics*: it meant the audit trail completely lost track of cache-served calls. ReviewerA could not verify that the `intentHash` on a `cacheHit: true` toolCall corresponded to any logged kernel event. The attestation was orphaned.

## The Fix — New Audit Event Kind `cache_hit`

`src/security/audit-log.ts` was extended with a third `AuditEventKind`:

```typescript
export type AuditEventKind = 'intent' | 'result' | 'cache_hit';

export type AuditEvent = {
  // …existing fields…
  /** ReviewerA-Attestkette für Cache-Hits ohne erneute Ausführung. */
  intentHash?: string;
};

export function logCacheHit(
  taskId: string,
  role: Role,
  toolName: string,
  intentHash: string
): void {
  const event: AuditEvent = {
    kind: 'cache_hit',
    taskId,
    role,
    toolName,
    inputHash: intentHash,   // keep shape consistent with intent/result
    intentHash,              // explicit ReviewerA attestation link
    redactedInput: {},
    timestamp: new Date().toISOString(),
  };
  AUDIT_LOG.push(event);
  console.log(
    `[AUDIT:CACHE_HIT] task=${taskId} role=${role} tool=${toolName} ` +
    `intentHash=${intentHash} ts=${event.timestamp}`
  );
}
```

Three deliberate design choices:

1. **`intentHash` is its own field**, not just a value stuffed into `inputHash`. ReviewerA gates on field presence; mixing the two would force a JSDoc explanation of equivalence on every reader.
2. **`redactedInput: {}` and no `outcome`/`durationMs`** — the event is a *passive attestation*, not a fake execution record. The shape intentionally differs from `result` so log consumers can filter `kind === 'cache_hit'` instead of guessing.
3. **`hashInput` was already exported in a parallel A3 edit** — no new dependency, no new module wiring.

## Test Discipline (TDD, single test)

Per the project's TDD discipline (RED → GREEN), only one new test was added:

`src/security/__tests__/audit-log.cache-hit.test.ts`

```typescript
import { getAuditLog, logCacheHit } from '../audit-log';

describe('audit-log cache_hit event', () => {
  it('records the ReviewerA intent attestation hash without pretending execution occurred', () => {
    const before = getAuditLog().length;

    logCacheHit('task-cache-1', 'implementer', 'write_file', 'deadbeef');

    const event = getAuditLog()[before];
    expect(event).toMatchObject({
      kind: 'cache_hit',
      taskId: 'task-cache-1',
      role: 'implementer',
      toolName: 'write_file',
      inputHash: 'deadbeef',
      intentHash: 'deadbeef',
      redactedInput: {},
    });
    expect(event.outcome).toBeUndefined();
    expect(event.durationMs).toBeUndefined();
  });
});
```

The test name states the *behavior*, not the implementation — and the `expect(event.outcome).toBeUndefined()` assertion locks in the "no fake execution" invariant.

## Verification Commands Used

```bash
cd /home/bratan/30-Library/hermes-v7

# Type-check after the new event kind is exported
./node_modules/.bin/tsc --noEmit --pretty false

# New test + the closest existing suite (kernel test also exercises the
# shared `getAuditLog` interface and must stay green)
./node_modules/.bin/jest \
  src/security/__tests__/audit-log.cache-hit.test.ts \
  src/security/__tests__/kernel.test.ts \
  --runInBand --coverage=false
```

Expected: `tsc_status=0` and `Tests: 17 passed, 17 total`.

## Pitfalls Observed

1. **`hashInput` had to be exported first** — the cache-hit caller needs the same hash function the kernel uses, otherwise `intentHash` on the cache-hit event would diverge from what a real `logIntent` would produce. The repo already had this export from a parallel A3 edit; if it hadn't, the test would have failed at module-load time with a missing symbol, not at runtime with a hash mismatch — which is the better failure mode.
2. **Write the test before the implementation, not as a final verification step** — the LSP server reports stale diagnostics against the *post-patch* state while the test file is mid-execution, which is itself the RED signal. Don't re-write the test after the impl to "verify"; the test's failure-to-pass transition is the only proof the impl is correct.
3. **Do not add `outcome: 'success'` to the cache-hit event** — that would be the "fake execution" trap the original `// Wichtig: KEIN …` comment in `tool-runtime.ts` was warning against. The whole point of `kind: 'cache_hit'` is to be a *different shape* on the wire so log consumers can branch on `kind` rather than inferring.
4. **`redactedInput: {}` is mandatory** — the field is non-optional in the type. Leaving it `undefined` would break any consumer that JSON-stringifies `AuditEvent[]` and expects a uniform object shape (e.g. downstream SIEM parsers, `JSON.stringify(getAuditLog())` snapshots in tests).
5. **Do not call `logCacheHit` *and* `logIntent` on the same toolCall** — that would produce two audit events for one execution, defeating the cache-hit invariant. `tool-runtime.ts` still skips `logIntent` on the cache-hit branch; only the cache-hit event is emitted. A future reviewer gate may want to assert this property (one audit event per toolCall on the cache path).

## Multi-Pass Attestation Status (post-A5)

| Field | Set by | Verified by | Patch |
|---|---|---|---|
| `intentHash` (ToolCall) | `logIntent` in `tool-runtime.ts` | ReviewerA gate | A1 (schema+gate), A4 (audit event variant) |
| `cacheHit` (ToolCall) | Idempotency-Cache branch in `tool-runtime.ts` | (gate pending) | A2 (schema), A3 (runtime wiring) |
| `idempotencyKey` / `cachedResult` (TaskCard) | caller | runtime lookup | A2 (schema), A3 (runtime wiring) |
| `cache_hit` event (AuditEvent) | `logCacheHit` in `audit-log.ts` (now actually CALLED from `runAtomicToolCall`) | downstream SIEM / Reviewer audit | A4 (event), **A5 (call site wired + flag-gated)** |
| `HERMES_IDEMPOTENCY_ENABLED` flag | env > config | operator / emergency rollback | **A5** |
| `config.security.idempotency.enabled` | JSON config | operator opt-in | **A5** |

## What is NOT in this patch (intentional, deferred)

- **ReviewerA audit-event gate** — ReviewerA currently checks `toolCall.intentHash` presence but not that a corresponding audit-log event exists. Cross-referencing the audit log against `task.toolCalls` would be a 5th step (separate worker card, Biene B/C territory). **Status: still pending after A5; A5 only wired the call site, not the gate.**
- ~~**`logCacheHit` call site in `tool-runtime.ts`**~~ — **LANDED in A5**: the cache-hit branch now calls `logCacheHit(task.id, role, toolName, synthesizedIntentHash, config)` immediately after the existing `[CACHE-HIT]` note, completing the A4-deferred item.
- **Config exposure** — **PARTIALLY LANDED in A5**: A5 added the `config.security.idempotency.enabled` block AND the env-layer override `HERMES_IDEMPOTENCY_ENABLED` (default off). The orchestrator does not yet thread `kernelConfig` into `Implementer.execute()`, so JSON-config-driven enablement requires a separate wiring patch; env-driven enablement works today.

## Verification Summary

```text
tsc_status=0
Tests: 17 passed, 17 total (audit-log.cache-hit + kernel)
git diff --check: clean
```

The full repo Jest run was scoped to the new test plus the closest existing suite (`kernel.test.ts` also exercises `getAuditLog`). Other suites were not re-run because the patch touches only `audit-log.ts` (added event kind + new function) and adds one new test file — no existing call site or type consumer changed.