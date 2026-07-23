# Intent-Hash Chain — hermes-v7 Issue #1 Implementation

## Context

This file documents the concrete implementation of the Kernel-Ebene-4-Attest pattern in hermes-v7. It serves as a worked example for `security-attestation-patterns/SKILL.md`.

## The Gap

Issue #1 assessment documented two remaining gaps:

- **Gap #1:** ReviewerA had no attestation check — toolCalls could arrive without an intentHash, bypassing the Kernel audit layer completely.
- **Gap #2:** No `securityKernel` config block existed, so operators couldn't set fail-closed defaults or disable enforcement for debugging.

## Change Chain

### 1. Type Extension (`src/core/types.ts`)

```typescript
// Added to ToolCall interface (already had input, outcome, outputArtifactIds, etc.):
intentHash?: string;
```

Key decision: **optional** (`?`). Old ToolCall objects without the field still compile. Enforcement at the gate.

### 2. Runtime Injection (`src/runtime/tool-runtime.ts`)

Found the existing `logIntent` call inside `runAtomicToolCall()`:

```typescript
const inputHash = hashString(JSON.stringify({ toolName, input }));
logIntent({ taskId, role, tool, hash: inputHash, ts });

const call: ToolCall = {
  toolName,
  input,
  startedAt: new Date().toISOString(),
  outcome: 'failure' as const,  // or 'success' — same object literal
  outputArtifactIds: [],
  error: ...,
  delta: ...,
  intentHash: inputHash,  // ← one line added after logIntent
};
```

Critical detail: inserted the hash reference right after `logIntent` returns it, so both success and failure paths (which use the same `call` object literal pattern a few lines apart) get the attestation.

### 3. Reviewer Gate (`src/roles/reviewer-a.ts`)

Added as **Check 0** (before failed-without-Delta and output-artifact checks):

```typescript
async review(task: TaskCard): Promise<TaskCard> {
  // Check 0 (Ebene-4-Attest)
  const missingIntentHash = task.toolCalls.some(c => !c.intentHash);
  if (missingIntentHash) {
    task.status = 'blocked';
    task.notes.push(
      'ReviewerA: tool call without intent-hash — Kernel-Bypass detected'
    );
    task.updatedAt = new Date().toISOString();
    return task;
  }
  // … Check 1: failed-without-Delta
  // … Check 2: output-artifact
}
```

Check ordering is intentional — Bypass detection is the most critical security failure. We want it flagged before contract violations could confuse the trail.

### 4. Config Exposure

**Type** (`src/security/types.ts`):
```typescript
interface HermesConfig {
  // …existing fields…
  securityKernel?: {
    enabled: boolean;
    bypassAllowed: boolean;
    failOpen: boolean;
  };
}
```

**JSON** (`config/hermes.config.json`):
```json
{
  "securityKernel": {
    "_comment": "Issue #1 Gap #2 — Operator Single-Point-of-Control. Fail-closed by design.",
    "enabled": true,
    "bypassAllowed": false,
    "failOpen": false
  }
}
```

The `_comment` is intentional — it surfaces the design rationale directly in the config file operators interact with.

## Test File

Created `src/roles/__tests__/reviewer-a.test.ts` with 5 tests:

| # | Scenario | Purpose |
|---|----------|---------|
| 1 | Mixed attestations (some present, some missing) | Verifies gate catches partial bypass |
| 2 | All missing + other checks would pass | Verifies attestation fires before other gates |
| 3 | All present + happy path | Verifies no false positive |
| 4 | Config JSON defaults are fail-closed | Schema compliance + policy verification |
| 5 | Type compiles with/without securityKernel | Non-breaking additive schema |

**Test outcome:** 5/5 pass, 133 total tests across 17 suites pass with no regressions.

## Verification Commands Used

```bash
# Full suite (excluding node_modules)
npx jest --passWithNoTests --testPathIgnorePatterns="/node_modules/" 2>&1 | tail -15

# New tests
npx jest src/roles/__tests__/reviewer-a.test.ts 2>&1 | tail -10

# Most-impacted existing suites
npx jest src/security/__tests__/kernel.test.ts src/roles/__tests__/orchestrator.test.ts 2>&1 | tail -10
```

## Notable Details

- **Pre-existing failure in `memory-provider.test.ts`** was untracked/unversioned — not related to this task. Used `--testPathIgnorePatterns` to isolate.
- **No commit/push** — changes were staged but not committed per task instruction.
- **V7.2 follow-up** noted: wiring `securityKernel.enabled=false` to the Orchestrator constructor is out of scope for these additive changes.
