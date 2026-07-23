# Idempotency-Key Attestation — hermes-v7 V7.2 worker-bee A2 patch

## Context

Companion to `intent-hash-chain-hermes-v7.md`. Where that file documents the **first** attestation added to `ToolCall` (`intentHash`, a security kernel-bypass detector), this file documents the **second** attestation added to the same type (`cacheHit`, an idempotency-cache bypass detector) plus its two companion fields on `TaskCard` (`idempotencyKey`, `cachedResult`).

Together they illustrate the **multi-pass attestation** variant: a single runtime object carries multiple independent optional fields, each set by a different code path and each enforcing a different invariant at a reviewer or verifier boundary.

## The Gap

After Issue #1 closed the `intentHash` hole, the next observation was: the tool-runtime has no concept of an idempotency cache. Re-running the same `write_file` with the same input re-writes the file, re-emits artifacts, and re-claims the audit log — wasting work and producing noise in the trail. There was no schema field to mark a toolCall as cache-served, no field to key the cache, and no field to carry the cached snapshot.

## Schema changes (all additive, 0 deletions)

```typescript
// File: src/core/types.ts
// Step 1 — Type Extension only. No runtime injection / gate / config wiring
// in this patch; those land in V7.3 follow-up work.

export type ToolCall = {
  toolName: string;
  input: Record<string, unknown>;
  startedAt: string;
  finishedAt?: string;
  outcome: 'success' | 'failure';
  outputArtifactIds: string[];
  intentHash?: string;
  delta?: Delta;
  cacheHit?: boolean;        // ← NEW: Idempotency-cache bypass flag
};

export type TaskCard = {
  // ... existing fields unchanged ...
  idempotencyKey?: string;   // ← NEW: cache-key
  cachedResult?: unknown;    // ← NEW: snapshot of the last successful result
};
```

## Multi-pass attestation reasoning

- **`intentHash`** — set by `logIntent` (Kernel Ebene 4) BEFORE the tool executes. ReviewerA uses it to detect "toolCalls without intentHash dürfen den ReviewerA nicht passieren".
- **`cacheHit`** — set by an idempotency-cache layer (not yet wired, V7.3) BEFORE the tool's `runAtomicToolCall` path. Reviewer/Verifier will use it to short-circuit re-execution checks — but must still verify `intentHash` is present (cache entries originated from legal original runs) and `outputArtifactIds` matches `outputExpected` (cache content wasn't tampered with).
- **`idempotencyKey`** — set by the caller (`implementer` role), drives the cache lookup. Optional: no key = no caching, default = re-execute.
- **`cachedResult`** — set by runtime after a successful run; fed back into the next call that matches `idempotencyKey`.

The two attestations are independent: a toolCall can have `intentHash` but no `cacheHit` (normal fresh execution); it can have both (cache hit on a previously-attested call); it can never have `cacheHit: true` without `intentHash` (the cache only stores fully-attested entries).

## Why strict-additive matters here

This patch was issued as a **Worker-Biene A2 TaskCard**: narrow scope, no enum changes, no breaking changes. The git diff confirms:

```
src/core/types.ts | 52 ++++++++++++++++++++++++++++++++++++++++++++++++++++
1 file changed, 52 insertions(+)
```

Zero existing field touched. The existing test factories (`makeTask`, `makeToolCall`) use `Partial<...>` with spread, so they pick up the new optional fields automatically without source changes. Existing `TaskCard` JSON files on disk (already-serialized workflow state) parse unchanged through `JSON.parse` — the `cacheHit: undefined` and `cachedResult: undefined` round-trip cleanly.

## Optional-vs-default-false JSDoc convention

For boolean attestation flags, the JSDoc must explicitly state that `undefined` is semantically equivalent to `false`. This is the contract that lets us say "additive" with a straight face — old data without the field doesn't need migration, and reviewers checking `call.cacheHit === true` (strict) vs `call.cacheHit` (truthy) behave the same on fresh and legacy entries.

Excerpt from the actual JSDoc added in this patch:

```typescript
/**
 * `true`  = dieser ToolCall wurde aus einem Idempotency-Cache beantwortet ...
 * `false` = normaler, frisch ausgeführter ToolCall (Default-Verhalten).
 * `undefined` = Feld wurde vor dem Idempotency-Patch angelegt und ist
 *               semantisch gleichwertig zu `false`.
 */
cacheHit?: boolean;
```

## Verification commands used

```bash
# Schema-level (no runtime): type-check + targeted test suites
cd /home/bratan/30-Library/hermes-v7
npx tsc --noEmit

# Baseline-equivalence: same .test.ts suites pass before & after the patch
npx jest --ci --testMatch="**/__tests__/**/*.test.ts" \
         --testPathIgnorePatterns="memory-provider" 2>&1 | tail -10

# Expected: 7 test suites passed, 76 tests passed (identical to pre-patch)
```

## Pitfalls observed during this session

1. **`dist/*.test.js` pollution** — Jest's `testMatch` in this repo accepts `.test.js` too. Running `npx jest` (no `--testMatch` override) picks up stale compiled `.test.js` files in `dist/` whose `__fixtures__/` are missing, producing 16 phantom failures. Always use `--testMatch="**/__tests__/**/*.test.ts"` to verify the **real** baseline. Documented in SKILL.md Pitfalls.

2. **`memory-provider.test.ts` is untracked** — pre-existing unversioned file. The standard `--testPathIgnorePatterns="memory-provider"` excludes it from baseline runs. This is repo-specific hygiene, not a TypeScript pattern rule.

3. **Test factories need NO update** — `Partial<TaskCard>` with spread already handles new optional fields. Trying to "register" the new fields in test helpers is a sign the change is breaking (it shouldn't be).

4. **Commit message structure** — for Worker-Biene multi-field additive patches, a `-m` per field with a one-line summary commit makes the eventual squash / cherry-pick trivial. `git -c user.email="worker-bee-a2@hermes-v7.local" -c user.name="Worker-Biene A2" commit -m "..." -m "..." -m "..."` keeps the bee's identity in the commit without polluting global git config.

## What's NOT in this patch (intentional, deferred)

- **Runtime injection** of `cacheHit` (the Idempotency-Cache layer in `tool-runtime.ts`) — separate worker card.
- **Reviewer/Verifier gate** — `cacheHit === true` must STILL verify `intentHash` + `outputArtifactIds`. Needs the cache to exist first.
- **Config exposure** — no new `securityKernel`/`idempotency` config block yet. Land when the runtime path is wired.

This narrow scope is the point: Worker-Biene-A2 lands the schema; Worker-Biene-B lands the runtime; Worker-Biene-C lands the gate. Each has a clean diff, an independent reviewer, and a single responsibility.