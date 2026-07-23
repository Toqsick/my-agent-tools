---
name: security-attestation-patterns
description: "Use when user asks to add cryptographically signed or audited runtime properties, enforce attestations at a reviewer or gate boundary, expose security parameters in config, or test success and failure attestation paths. NOT for generic authentication or UI validation. Implements the kernel-to-gate attestation pattern with type changes, runtime injection, enforcement, and verification."
version: 1.0.0
author: Yuno
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    category: security
    tags:
    - security
    - attestation
    - audit
    - review-gate
    - typescript
    - architecture
trigger_keywords: ['runtime', 'and', 'attestation', 'security-attestation-patterns', 'add']
keywords: ['runtime', 'gate', 'attestation', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: []
---


# Security Attestation Patterns

## Trigger

Load this skill when:
- A task involves adding cryptographically-signed / audited properties to runtime data structures (e.g. intentHash, nonce, attestation token)
- Work needs enforcement of those properties at a review/inspection/gate boundary
- A security assessment doc lists "gap: missing attestation field X on type Y — enforce at boundary Z"
- Adding a new config block to expose runtime security parameters

## The Pattern: Kernel-Ebene-4-Attest

The core pattern is a 4-step chain that guarantees every tool call or public action is Kernel-attested:

```
Step 1: Type Extension
  → Add attestation field (optional on type, required by gate)
  → Never breaking — old ToolCalls without field still compile

Step 2: Runtime Injection
  → After Kernel logs the intent (logIntent / auditIntention),
    persist the resulting hash/attestation onto the object
  → Single line: call.attestationField = inputHash

Step 3: Reviewer / Gate Enforcement
  → Check at the START of every review, before business logic
  → If attestation field is missing: BLOCK immediately
  → Order: attestation check FIRST (Kernel-Bypass detection)
            → contract checks (failed-without-Delta)
            → output/artifact checks

Step 4: Config Exposure
  → Make attestation parameters configurable via a config block
  → Block must be additive (old configs still parse)
  → Block must be fail-closed by default
    (enabled: true, bypassAllowed: false, failOpen: false)
  → _comment inside JSON explains single-point-of-control for operators
```

### Step Details

#### Step 1: Type Extension

```typescript
// BEFORE
interface ToolCall {
  toolName: string;
  input: Record<string, unknown>;
  outcome: 'success' | 'failure';
  outputArtifactIds: string[];
}

// AFTER — additive, non-breaking
interface ToolCall {
  toolName: string;
  input: Record<string, unknown>;
  outcome: 'success' | 'failure';
  outputArtifactIds: string[];
  intentHash?: string;  // Kernel-Ebene-4-Attest
}
```

Key rule: Make it optional (`?`) on the type. Compliance is enforced at the gate, not the type system. This lets old objects parse without migration.

**Variant: Multi-pass attestation** — a single object can carry *multiple* independent attestations, each enforcing a different invariant at the gate. Example: `ToolCall` carries both `intentHash` (Kernel-Bypass detection) and `cacheHit` (Idempotency-Bypass detection). Each is set by a different runtime path, each is checked by the same or different reviewer, and each is independently optional.

**Optional-vs-default-false distinction** — when the attestation is a `boolean` flag (like `cacheHit`) whose `undefined` and `false` are semantically equivalent (both = "not a cache hit"), DO NOT migrate old serialized data to set the flag explicitly. Document the equivalence in JSDoc: `` `undefined` = Feld wurde vor dem Patch angelegt und ist semantisch gleichwertig zu `false`. `` This keeps the additive guarantee true even after a JSON round-trip through `JSON.parse(taskCard)`.

#### Step 2: Runtime Injection

```typescript
// Find the exact line where logIntent / auditIntention fires
const inputHash = hashString(someInput);
logIntent({ taskId, role, tool, hash: inputHash });

// Persist onto the ToolCall — ONE line
const call: ToolCall = {
  ...existingFields,
  intentHash: inputHash,  // ← Kernel attestation
};
```

Place it so it hits both success AND failure paths (same object literal or assignment).

#### Step 3: Reviewer Gate Enforcement

```typescript
async review(task: TaskCard): Promise<TaskCard> {
  // Check 0 — attestation gate, FIRST
  const missing = task.toolCalls.some(c => !c.intentHash);
  if (missing) {
    task.status = 'blocked';
    task.notes.push('Reviewer: tool call without attestation — Bypass detected');
    task.updatedAt = new Date().toISOString();
    return task;
  }

  // Existing checks follow (contract, output, etc.)
}
```

**Check ordering matters:**
1. Attestation check (Kernel-Bypass detection)
2. Contract checks (failed-without-Delta, atomic contract violations)
3. Output checks (artifacts exist for expected outputs)

This way a bypass attempt is flagged before other violations could confuse the audit trail.

#### Step 4: Config Exposure

```typescript
// In the config type — additive, optional
interface HermesConfig {
  // ... existing fields
  securityKernel?: {
    enabled: boolean;
    bypassAllowed: boolean;
    failOpen: boolean;
  };
}
```

```json
// In the JSON config — fail-closed defaults
{
  "securityKernel": {
    "_comment": "Single-point-of-control for operators — requires explicit action to weaken",
    "enabled": true,
    "bypassAllowed": false,
    "failOpen": false
  }
}
```

**Semantics of each default:**
- `enabled: true` — Kernel actively checks attestations. Set `false` during transition, not permanently.
- `bypassAllowed: false` — No legitimate bypass path exists. Set `true` for trusted debugging contexts.
- `failOpen: false` — If the attestation cannot be verified, block (closed) rather than allow (open).

## Test Patterns

### Attestation Tests (3 scenarios)

| # | Scenario | Expectation |
|---|----------|-------------|
| 1 | Mixed: some toolCalls have attestation, some don't | BLOCKED |
| 2 | All missing attestation + all other checks pass | BLOCKED (attestation fires first) |
| 3 | All toolCalls have attestation, happy path | Passes to next stage |

### Config Defaults Tests (2 scenarios)

| # | Scenario | Expectation |
|---|----------|-------------|
| 1 | Read live config JSON, verify defaults | fail-closed (enabled=true, bypassAllowed=false, failOpen=false) |
| 2 | Schema validation: object with/without securityKernel block | Both compile |

### Anti-Patterns in Testing

- Do NOT test that the *orchestrator* sets the attestation — test that the *gate* enforces it.
- Do NOT test the hash function directly (it changes when input format changes).
- Do NOT test config file path resolution — test the in-memory defaults and type boundaries.

## Verification

After implementing the 4-step chain:

```bash
# Run the full test suite (excluding pre-existing failures)
npx jest --passWithNoTests --testPathIgnorePatterns="/node_modules/" 2>&1 | tail -15

# Specifically verify the attestation + gate tests
npx jest src/roles/__tests__/reviewer-a.test.ts 2>&1 | tail -10

# Verify gate + orchestrator + kernel tests together
npx jest src/security/__tests__/kernel.test.ts src/roles/__tests__/orchestrator.test.ts 2>&1 | tail -10
```

## Pitfalls

- **Do NOT add attestation as a required (non-optional) type field.** Old objects won't parse. Gate enforcement is the correct enforcement point.
- **Do NOT reorder checks.** Attestation FIRST means a bypass is caught even when other checks would also block. The audit trail stays clean.
- **Do NOT make test scenarios too coupled to hash implementation.** Test that the *presence* of the field gates correctly, not that a specific hash value matches.
- **Do NOT forget both success AND failure paths** when injecting attestation at runtime. A failure-path call still needs the attestation.
- **Config defaults MUST be fail-closed**, not fail-open. `failOpen: true` as default is a security incident waiting to happen.
- **The config block is additive** — existing config files without it must still parse. Use `?` on the type field.
- **Pre-existing test failures in unrelated files** — always run with `--testPathIgnorePatterns` to isolate new work from pre-existing issues.
- **`dist/*.test.js` artifacts pollute Jest's `testMatch`.** In TypeScript repos whose `package.json` testMatch accepts both `.test.ts` and `.test.js`, a stale `dist/` directory containing compiled `.test.js` files (from a prior `tsc`) will be picked up by Jest. Their `__fixtures__/` directories are usually missing, so they fail with `ENOENT`. Verify with `--testMatch="**/__tests__/**/*.test.ts"` to confirm green-vs-stale baseline. The "real" baseline is `npx tsc --noEmit` + `npx jest --testMatch="**/__tests__/**/*.test.ts" --testPathIgnorePatterns=<unrelated>`.
- **Do NOT treat `cacheHit === true` as a Kernel-Bypass.** Idempotency-cached calls still came from an originally-legally-executed call (they have an `intentHash`); the reviewer must still verify `outputArtifactIds` against `outputExpected`. Cache only short-circuits the re-execution, not the audit trail.
- **Dual-Layer Feature Flag pattern (env > config > default-off).** When wrapping an additive patch in a kill-switch, use a **two-layer resolver** with `process.env` ABOVE the JSON-config block — never the other way around. The env override enables **One-Way-Rollback without redeploy** in production incidents; putting config above env would force a config-file edit + service restart, which is exactly the wrong speed in an emergency. Three named exports pay off: pure `parseEnvFlag(raw)` (testable via `it.each` without env mutation), IO-side `readEnvLayer()`, pure `readConfigLayer(config)`, and the composer `isIdempotencyEnabled(config?)`. Default must be `false`, never `undefined`/truthy. Use an optional `?` field on the JSON schema so pre-flag configs parse unchanged. Full pattern + operator runbook in [references/feature-flag-kill-switch-hermes-v7.md](references/feature-flag-kill-switch-hermes-v7.md).
- **`git stash` does NOT include untracked files by default.** When verifying "did my change introduce a coverage threshold breach?" via `git stash && npx jest --ci --coverage`, the new untracked files (like a flag-resolver module + its test) stay on disk, producing phantom failures from the post-patch code mixed with pre-patch tracked files. Always use `git stash -u` for this kind of baseline-comparison, OR do the baseline check BEFORE creating any new files (work in two clean steps).
- **Pre-existing coverage-threshold breaches must be documented in the commit body, not bulk-fixed in the same patch.** When `npx jest --ci --coverage` shows thresholds violated, first prove they're PRE-EXISTING via `git stash -u && npx jest --ci --coverage`. If they were pre-existing, mention in the commit body what's `introduced` vs `pre-existing`. Don't bulk-test your way past the threshold — that pollutes the diff with unrelated tests and obscures the actual change. **The two valid fixes when a feature branch needs to land:** (a) narrow `collectCoverageFrom` to exclude pre-existing-untested modules that are explicitly `Geplant` in the project roadmap (justify each exclude path in the commit body); or (b) add one smoke-test per excluded module that exercises the public API at minimal depth. Pick (a) when the threshold breach is large and most excludes are reasonable; pick (b) when the breach is narrow and there's a natural test for each module. Never pick "delete the threshold" or "set it to 0%".
- **The deferred-wiring trap: "land the flag now, wire it up next patch" leaves the flag inert.** When shipping a feature flag with the intent "a follow-up patch will thread the config through to the call site," at least one E2E test in the **flag-shipment** patch must exercise the flag through the real constructor chain — otherwise the follow-up patch silently never lands, and operators set the flag with no effect. Symptom: tests calling `runAtomicToolCall(task, ..., FLAG_ON_CONFIG)` pass (because the flag is read directly), but `new Implementer(adapter).execute(task)` ignores the same flag (because Implementer doesn't forward it to `runAtomicToolCall`). Always assert end-to-end at the level operators actually use, not at the level the flag-shipment patch happens to wire.
- **Reviewer Bypass checks must be SHAPE-AGNOSTIC across all attestation fields.** When adding a new attestation (like `cacheHit`), the temptation is to add a carve-out: "if `cacheHit === true`, skip the `intentHash` check." This re-introduces a Bypass hole — a malicious caller sets `cacheHit: true` on a hand-crafted ToolCall that bypassed `logIntent`, and the reviewer no longer catches it. The correct logic keeps the bypass check universal (`!c.intentHash` regardless of any other field) and uses the new attestation only for downstream behaviour (e.g. "don't re-verify execution, but still check output artifacts"). A regression test that asserts `cacheHit === true` + missing `intentHash` → `blocked` locks this in. See `references/idempotency-a6-reviewer-gate-e2e-orchestrator-coverage-hermes-v7.md` pitfall 2.

## Related Skills

- `test-driven-development` — For RED-GREEN-REFACTOR cycles that pair with attestation gate tests
- `security-code-checker` — For scanning existing code for missing attestation fields
- `verify-before-fix` — For finding the exact location where attestation should be injected

## References

- `references/intent-hash-chain-hermes-v7.md` — Concrete session example (Issue #1 intent-hash chain implementation)
- `references/idempotency-key-attestation-hermes-v7.md` — Concrete session example for the multi-pass attestation variant (V7.2 Idempotency-Key patch: `ToolCall.cacheHit` + `TaskCard.idempotencyKey` + `TaskCard.cachedResult`). Companion to the intent-hash reference; covers the optional-vs-default-false boolean convention and the additive-only diff discipline.
- `references/cache-hit-audit-event-hermes-v7.md` — Concrete session example (V7.2 worker-bee A4) for adding the `cache_hit` `AuditEventKind` so ReviewerA can cross-reference `ToolCall.intentHash` against the actual audit-log event. Covers the new-event-shape-on-the-wire pattern (different shape from `result` so log consumers can branch on `kind`), the `redactedInput: {}` mandatory invariant, and the "no fake execution" trap from the cache-hit branch of `tool-runtime.ts`.
- `references/feature-flag-kill-switch-hermes-v7.md` — Concrete session example (V7.2 worker-bee A5) for wrapping an additive patch in a **Dual-Layer Feature Flag** (env > config > default-off) with One-Way-Rollback. Covers the pure-parser / IO-side / composer export triad for env-deterministic tests, the `?` optional config-field shape, the "do not orphan existing tests" call-site discipline (A4's test now needs to pass a `FLAG_ON_CONFIG` fixture), the `git stash -u` pre-existing-coverage discipline, and the operator rollback runbook. Closes the A4-deferred call site for `logCacheHit` and adds the JSON-config + env kill-switch the Operator needs for incident response.
- `references/idempotency-a6-reviewer-gate-e2e-orchestrator-coverage-hermes-v7.md` — Concrete session example (V7.2 worker-bee A6) closing the four items A5 deferred: ReviewerA gate verification for `cacheHit: true` ToolCalls (`reviewer-a-cache-hit.test.ts` with 5 scenarios), End-to-End pipeline test (`idempotency-e2e.test.ts` walking the cache hit through Implementer → ReviewerA → ReviewerB → Verifier + Orchestrator.run), the **additive config-forwarding chain** Orchestrator → Implementer → runAtomicToolCall (third constructor argument + `?? kernelConfig` fallback), and CI-gate coverage fix via `collectCoverageFrom` scope exclusion with ROADMAP-`Geplant` justification. Five pitfalls worth their own row: the deferred-wiring trap, shape-agnostic bypass checks, "no fake execution" audit-trail invariant, scope-exclusion-vs-bulk-test decision matrix, and direct-Implementer-caller audit gap.
