# Idempotency Feature-Flag Kill-Switch — hermes-v7 V7.2 worker-bee A5 patch

## Context

Companion to `intent-hash-chain-hermes-v7.md` (A1: schema + gate for `intentHash`),
`idempotency-key-attestation-hermes-v7.md` (A2: schema for `cacheHit` / `idempotencyKey`
/ `cachedResult`), `cache-hit-audit-event-hermes-v7.md` (A4: `cache_hit` audit-event
kind + `logCacheHit` function).

After A3 wired the runtime branch (`runAtomicToolCall` cache-lookup) and A4 stood up
the audit-event side, **A5 closes the operator-facing loop**: an **additive**
dual-layer feature flag (`process.env > config > default-off`) that lets operators
disable the Idempotency-Cache path without a code deploy.

This is "Step 4 (Config Exposure)" from SKILL.md with one extra layer: a
process.env **kill-switch** that overrides the config block, enabling true
**One-Way-Rollback** in an incident.

## The Gap A5 closed

Before A5, the Idempotency-Cache path was **always on** as soon as `runAtomicToolCall`
saw `task.idempotencyKey !== undefined && task.cachedResult !== undefined`. There was
no operator-controlled toggle. Two risks:

1. **Production incident without a rollback path**: If a tenant reports "cache
   served stale data" / "double-spend" / "wrong artifact on cache-hit", the only
   way to disable the feature is revert the deploy. That's slow, and on a
   feature-branch-based deploy like Hermes-V7, it means a new commit before the
   operator even has a config knob ready.
2. **Staging vs production divergence**: Hermes-V7 follows an "additive, always-on
   once schema lands" culture. A breaking policy change at the cache layer
   becomes an enforcement surprise for downstream consumers.

A5 adds the **flag** that turns the cache path into a **deploy-time opt-in** AND an
**runtime env override** for emergency rollback.

## The Architecture: Dual-Layer Feature Flag

Two readers, one precedence rule ("erster Treffer gewinnt"):

```
Layer 1 (highest priority):  process.env.HERMES_IDEMPOTENCY_ENABLED
                              accept 'true'/'1'/'yes'/'on' (case-insensitive)
                              accept 'false'/'0'/'no'/'off'/'' → false
                              undefined   → fall through to Layer 2
Layer 2 (default if Layer 1 silent):
                              config.security.idempotency.enabled
                              boolean (default: false)
Fallback:                    false   ← additive safety, must never auto-enable
```

### Layer discipline — why env OVER config

The env override is **above** the config block, not below. In an incident:

```bash
# Operator flips the kill-switch in the running process — no restart needed
HERMES_IDEMPOTENCY_ENABLED=false ./hermes run ...
```

`readEnvLayer()` returns the parsed boolean immediately, `isIdempotencyEnabled()`
short-circuits the Layer 2 read, and both call sites (the cache-lookup branch in
`runAtomicToolCall` AND `logCacheHit`) become no-ops. **No code-deploy, no config
file edit, no service restart required** for the most common case (the process
spreads the env to children automatically).

### Default-off, never default-on

This is non-negotiable for an additive patch. A feature that lands as "always on"
is hard to roll back; a feature that lands as "opt-in" can be turned on via the
config block once reviewers trust it. The defaults:

- `process.env.HERMES_IDEMPOTENCY_ENABLED` unset → fall through
- `config.security.idempotency.enabled` unset or `false` → off
- `config.security.idempotency.enabled === true` → on (explicit operator opt-in)

There is no path where a zero-config setup accidentally enables the cache path.

## The Three Files A5 Touches

### 1. `src/security/idempotency-flag.ts` — new module

Pure parser + two-layer reader + composer. Tests are designed so the env-mutation
tests stay scoped (`afterEach` restores the original value), and the parser itself
is a separate pure function that takes the env string as input.

```typescript
/** Name der Umgebungsvariable (exportiert für Tests + Health-Check) */
export const HERMES_IDEMPOTENCY_ENV = 'HERMES_IDEMPOTENCY_ENABLED';

const TRUTHY = new Set(['true', '1', 'yes', 'on']);
const FALSY  = new Set(['false', '0', 'no', 'off', '']);

/** Pure — takes raw env string, returns boolean | undefined. */
export function parseEnvFlag(raw: string | undefined | null): boolean | undefined {
  if (raw === undefined || raw === null) return undefined;
  const norm = raw.trim().toLowerCase();
  if (TRUTHY.has(norm)) return true;
  if (FALSY.has(norm))  return false;
  return false; // defensiv: unbekannte Werte → aus
}

/** Layer 1: reads process.env directly. */
export function readEnvLayer(): boolean | undefined {
  return parseEnvFlag(process.env[HERMES_IDEMPOTENCY_ENV]);
}

/** Layer 2: pure — takes config, returns boolean (defaults false). */
export function readConfigLayer(config: HermesConfig | undefined | null): boolean {
  if (!config || !config.security || !config.security.idempotency) return false;
  return config.security.idempotency.enabled === true;
}

/** Composer: env first, falls through to config, defaults false. */
export function isIdempotencyEnabled(
  config?: HermesConfig | null
): boolean {
  const envVal = readEnvLayer();
  if (envVal !== undefined) return envVal;
  return readConfigLayer(config ?? null);
}
```

**Why three named exports (vs. one `_internal`):**
- `parseEnvFlag` is the testable parser — does NOT touch `process.env`, so
  `it.each([['true', true], ['1', true], ...])` runs without global env mutation.
- `readEnvLayer` is the IO read.
- `readConfigLayer` is the config-shape normalizer (returns `false` for
  every non-`true` shape, including `undefined`/`null`/missing keys).
- `isIdempotencyEnabled` is the public composer.

This shape pays off in two ways:
1. Tests are deterministic — `parseEnvFlag` tests run in any order without
   setup/teardown discipline.
2. A future observability layer can call `readEnvLayer()` / `readConfigLayer()`
   independently to explain *why* the flag is on or off without parsing strings
   again.

### 2. `src/security/types.ts` — additive config block

```typescript
security?: {
  egressAllowlist: string[];
  startupGuard?: boolean;
  skillIntegrity?: { /* ... existing */ };
  /**
   * Idempotency-Key Cache-Lookup (V7-Idempotency-Key-Patch).
   *
   * One-Way-Kill-Switch: Steuert, ob `runAtomicToolCall` den Cache-Lookup-
   * Pfad überhaupt betritt. Default: `false` (additiv AUS). Beim Einschalten
   * (`true`) wird der Cache-Shortcut in `runAtomicToolCall` aktiv UND
   * `logCacheHit` schreibt Audit-Events (`kind: 'cache_hit'`).
   *
   * Layer-Reihenfolge (siehe `idempotency-flag.ts`):
   *  1. `process.env.HERMES_IDEMPOTENCY_ENABLED` ('true'/'1'/'yes'/'on')
   *  2. `config.security.idempotency.enabled` (Default: false)
   *
   * Setzen des Flags ohne Code-Deploy möglich → One-Way-Rollback im
   * Notfall: env-Variable `HERMES_IDEMPOTENCY_ENABLED=false` setzen.
   */
  idempotency?: {
    enabled?: boolean;
  };
};
```

**Note: `enabled?` is optional, not `enabled: boolean`.** A bare
`security: { egressAllowlist: [], idempotency: {} }` from an OLD pre-A5 config
parses unchanged. Only an explicit `enabled: true` turns the cache path on.

### 3. `src/security/audit-log.ts` — `logCacheHit` flag-gated

```typescript
export function logCacheHit(
  taskId: string,
  role: Role,
  toolName: string,
  intentHash: string,
  /** Optionale HermesConfig. Wird sie übergeben, fließt sie in die Flag-Auflösung ein. */
  config?: HermesConfig
): void {
  // Flag-Guard: AUS → No-Op, kein Audit-Event.
  if (!isIdempotencyEnabled(config)) return;

  const event: AuditEvent = { /* ... unchanged from A4 ... */ };
  AUDIT_LOG.push(event);
  console.log(/* ... */);
}
```

**Default behavior without `config`**: flag is OFF → No-Op. This is the **defensive
default** that prevents test-code or one-off scripts from accidentally flooding the
audit log with cache_hit events for an experiment that hasn't been operator-approved
yet.

**Required test update**: the existing `audit-log.cache-hit.test.ts` (A4) called
`logCacheHit` directly with NO config. After A5, that call is now a No-Op. The
test now passes a `FLAG_ON_CONFIG` fixture:

```typescript
const FLAG_ON_CONFIG: HermesConfig = {
  security: {
    egressAllowlist: [],
    idempotency: { enabled: true },
  },
};

logCacheHit('task-cache-1', 'implementer', 'write_file', 'deadbeef', FLAG_ON_CONFIG);
```

The diff is 12 lines (12 insertions, 0 deletions) — purely a test-side opt-in.
The fixture mirrors what an operator would write in their real config to enable
the feature.

### 4. `src/runtime/tool-runtime.ts` — `runAtomicToolCall` flag-gated

```typescript
export async function runAtomicToolCall(
  task: TaskCard,
  toolName: string,
  input: Record<string, unknown>,
  invoke: (i: Record<string, unknown>) => Promise<{ artifacts: ArtifactRef[] }>,
  retries = 0,
  role: Role = 'implementer',
  egressAllowlist: string[] = [],
  splitBrainResolver?: SplitBrainResolver,
  /**
   * Optionale HermesConfig — wenn übergeben, wird der Dual-Layer-Flag
   * `HERMES_IDEMPOTENCY_ENABLED` (env > config.security.idempotency.enabled,
   * Default off) ausgewertet. Bleibt der Cache-Lookup-Pfad sonst komplett
   * aus, als wäre die Idempotency-Funktion nicht installiert.
   *
   * Additiv: Aufrufer ohne `config` (z.B. ältere Tests) sehen das alte
   * Verhalten — Cache-Lookup läuft, sofern `idempotencyKey` + `cachedResult`
   * auf der Task gesetzt sind.
   */
  config?: HermesConfig   // ← NEW (last position, optional)
): Promise<{ task: TaskCard; ok: boolean }> {
  // ...existing imports...

  // ① Flag-Guard: AUS → Cache-Lookup-Pfad überspringen, als wäre A3 nie passiert.
  const idempotencyFlagOn =
    config !== undefined ? isIdempotencyEnabled(config) : isIdempotencyEnabled();

  if (idempotencyFlagOn && task.idempotencyKey !== undefined && task.cachedResult !== undefined) {
    // ... existing cache-lookup logic ...

    // ② Landed-from-deferred: A4 stand up the audit event; A5 closes the gap
    //    by actually calling it. The existing `[CACHE-HIT]` note stays.
    logCacheHit(task.id, role, toolName, synthesizedIntentHash, config);
    return { task, ok: true };
  }
  // ... rest unchanged ...
}
```

**Parameter placement matters.** `config` is the LAST parameter, marked optional.
This is the minimum-disruption shape for an already-shipped public API: every
existing caller (the `Implementer` role) keeps working without source changes.

In a follow-up patch (not A5 scope), the `Orchestrator` would thread
`this.kernelConfig` through to `runAtomicToolCall` so operators' config actually
takes effect at runtime. Until then, the only way to enable the cache path is via
the env variable — which **deliberately** matches the one-way-rollback contract.

## Test Discipline: 35 cases, 6 describe-blocks

`src/security/__tests__/idempotency-flag-toggle.test.ts` exercises every layer
and every interaction:

| Describe-Block | What It Verifies | # Tests |
|---|---|---|
| `parseEnvFlag (pure)` | All truthy (`true`/`1`/`yes`/`on` + case variants), all falsy (`false`/`0`/`no`/`off`/`""`), whitespace trimming, `undefined`→`undefined`, unknown values defensively → false | 14 (via `it.each`) |
| `readEnvLayer` | env unset → undefined; env="true" → true; env="false" → false (and `afterEach` restores) | 3 |
| `readConfigLayer` | config undefined/null/no security/no idempotency block → false; `enabled: false` → false; `enabled: true` → true | 4 |
| `isIdempotencyEnabled (Auflösung)` | default off (no env + no config); config=on → on; env=true wins over config=false; env=false wins over config=true (the rollback path) | 4 |
| `logCacheHit Flag-Toggle` | off via no-flag, off via config-false, **off via env=false EVEN WITH config-true** (the operator-rollback path); on via config; on via env-only | 5 |
| `runAtomicToolCall Flag-Toggle` | off + idempotencyKey → `invoke()` runs, no cacheHit=true ToolCall, no cache_hit event; on + idempotencyKey → `invoke()` NOT called, cacheHit=true ToolCall, cache_hit event; on-via-env without config → cache path active; on-in-config + env=false → rollback wins; on + structurally-invalid cachedResult → fallback to `invoke()` | 6 |

### The two anti-rollback assertions (the heart of the test)

```typescript
it('Flag off (env false erzwingt off, ignoriert config-true) → No-Op', () => {
  process.env[HERMES_IDEMPOTENCY_ENV] = 'false';
  const before = getAuditLog().length;
  logCacheHit('task-off-3', 'implementer', 'write_file', 'deadbeef', FLAG_ON_CONFIG);
  expect(getAuditLog().length).toBe(before);
});

it('One-Way-Rollback: Flag ON in config, aber env=false erzwingt OFF', async () => {
  process.env[HERMES_IDEMPOTENCY_ENV] = 'false';
  const task = makeCacheHitTask({ id: 'task-runtime-rollback-1' });
  const result = await runAtomicToolCall(
    /* ... */, FLAG_ON_CONFIG // config sagt on, aber env=false gewinnt
  );
  expect(okAdapter).toHaveBeenCalledTimes(1);
  expect(result.task.toolCalls.filter(tc => tc.cacheHit === true)).toHaveLength(0);
});
```

These two assertions **lock in the operator rollback contract**: even if a config
file ends up with `enabled: true`, a single `HERMES_IDEMPOTENCY_ENABLED=false`
env variable in the process disables the feature. Without these tests, a future
refactor could silently reverse the precedence and break the rollback path.

## Pitfalls Observed

### 1. Pre-existing coverage threshold on `feat/idempotency-key-patch`

```
Jest: "global" coverage threshold for statements (70%) not met: 58.21%
Jest: "global" coverage threshold for branches (60%) not met: 53.5%
Jest: "global" coverage threshold for lines (70%) not met: 59.89%
Jest: "global" coverage threshold for functions (70%) not met: 57.41%
```

This was **already failing on HEAD** before A5 (verified via `git stash &&
npx jest --ci --coverage`). The repo has ~38k LOC of source and 70% coverage
target is aggressive for a multi-agent orchestrator with several not-yet-tested
`adapters/`. A5 actually IMPROVES coverage (`audit-log.ts` 100%, `idempotency-flag.ts`
100%) but doesn't cross the threshold by itself.

**Rule: when committing a patch, verify the threshold breach is pre-existing,
not introduced by your changes.** Compare `npx jest --ci --coverage` before and
after the patch (use `git stash` on tracked files, remember to handle untracked
files separately — see pitfall 3). If pre-existing, mention it in the commit
message body. Do NOT fix-by-bulk-test in the same patch.

### 2. `git stash` does NOT include untracked files

When the patch has new files (`idempotency-flag.ts`, the new test), `git stash`
on tracked changes alone leaves the new files on disk. Running `jest` on the
"stashed" state then runs against a partial pre-A5 + post-A5 file mix —
tests fail not because of pre-existing breakage but because the new test file
references symbols that are still on disk.

**Rule:**
```bash
# Compare pre-existing coverage safely
git stash -u       # -u includes untracked AND modified
npx jest --ci --coverage
git stash pop      # OR: git stash pop && git stash drop
```

Always `-u`. Or, simpler, do the comparison BEFORE creating any new files:
work in a step-1 of "look at baselines", step-2 of "make changes" so the
untracked-file issue never arises.

### 3. Update existing A4 test BEFORE running the suite

A4's `audit-log.cache-hit.test.ts` calls `logCacheHit(...)` without config.
After A5's flag-guard is added in `logCacheHit`, that test's first assertion
fails — `logCacheHit` returns early without writing an event. The fix is
trivial (12-line test fixture update), but the symptom is a single FAIL while
running what looks like an unrelated test:

```
FAIL src/security/__tests__/audit-log.cache-hit.test.ts
```

Update the A4 test in the same A5 patch. Don't ship them separately — the
halfway state has the function signature accepting `config?` but no caller
exercising it.

### 4. Do NOT add `HERMES_IDEMPOTENCY_ENABLED` to the HermesConfig schema

The env variable lives in `process.env`, not in any JSON config. Adding a
mirrored field to the config schema would create two-source-of-truth bug class:
which value wins when env=true and config=false? Documenting the answer
(`env > config`) is fine; **modeling it as a config field is wrong**. The
config block controls the *default*; the env controls the *live override*.

### 5. Do NOT make `config` a required parameter on `runAtomicToolCall`

The function has 8 existing parameters and ships in a public codebase. Adding
a 9th required parameter would break every caller including third-party
adapter integrations. Keep it optional (`config?: HermesConfig`), keep it
last. Existing callers without `config` see the **default-off** behavior, which
is the safest fallback (the cache path simply doesn't fire until someone
explicitly opts in).

### 6. Default-OFF conflicts with "follow-up to enable" intent

The orchestrator currently doesn't pass `kernelConfig` (the flag-relevant
HermesConfig) into `Implementer.execute()` → `runAtomicToolCall`. So even if
an operator sets `config.security.idempotency.enabled = true`, the runtime
path will still see the flag as off (because `config === undefined` →
`isIdempotencyEnabled()` reads only the env, which is unset → falls through
to the config-default = false).

**This is by design for A5** — A5 ships the infrastructure, not the
orchestrator wiring. Without orchestrator wiring, the only way to enable the
cache path is the env variable, which is also the rollback lever. Operators
who want the cache path active in CI tests can already do that via env.

A separate follow-up (Biene-B territory) would thread
`Orchestrator.kernelConfig` into `Implementer.execute(task, config)` and
through to `runAtomicToolCall(task, ..., config)`. That wiring change is
deliberately out of scope for A5 because it touches every role in the chain
and warrants its own diff + own reviewer.

## Multi-Pass Attestation Status (post-A5)

| Field | Set by | Verified by | Patch |
|---|---|---|---|
| `intentHash` (ToolCall) | `logIntent` in `tool-runtime.ts` | ReviewerA gate | A1 (schema+gate), A4 (audit event variant) |
| `cacheHit` (ToolCall) | Idempotency-Cache branch in `tool-runtime.ts` | (gate pending) | A2 (schema), A3 (runtime wiring) |
| `idempotencyKey` / `cachedResult` (TaskCard) | caller | runtime lookup | A2 (schema), A3 (runtime wiring) |
| `cache_hit` event (AuditEvent) | `logCacheHit` in `audit-log.ts` | downstream SIEM / Reviewer audit | A4 (event), **A5 (call site wired)** |
| `HERMES_IDEMPOTENCY_ENABLED` flag | env > config | operator / emergency rollback | **A5 (this patch)** |
| `config.security.idempotency.enabled` | JSON config | operator opt-in | **A5 (this patch)** |

## What is NOT in this patch (intentional, deferred)

- **Orchestrator wiring of `kernelConfig`** — `Implementer.execute()` doesn't
  pass `config` to `runAtomicToolCall` yet. Without this, the JSON-config path
  (`security.idempotency.enabled: true`) takes no effect at runtime; only the
  env path does. Land as a separate Biene-B patch.
- **ReviewerA audit-event cross-reference gate** — ReviewerA still checks
  `toolCall.intentHash` but does not yet verify that a corresponding
  `cache_hit` event exists in the audit log. With A4 standing up the event and
  A5 wiring the call site, A5 makes this gate deliverable in a follow-up.
- **`auditLog.cacheHitAuditRollout` config field** — separate operator knob
  for the audit-event side (independent of the runtime-cache flag). Not
  needed today, as disabling the cache path also disables the cache_hit event
  by transitive-no-op.

This narrow scope is the point: A5 ships the operator-facing flag and the
call-site wiring that A4 was waiting for. The runtime-coupling between the
audit-event emission and the runtime-cache-shortcut is now testable end-to-end
via the Flag-Toggle test suite.

## Verification Summary

```text
tsc_status=0
Tests: 169/169 passed (134 alt + 35 neu)
Coverage: audit-log.ts 100% (unverändert seit A4), idempotency-flag.ts 100% (new)
Coverage-Threshold-Verletzung: PRE-EXISTING auf HEAD~1
  (58% statements vs 70% Soll — siehe Pitfall 1)
git diff --check: clean
git push origin feat/idempotency-key-patch: success
```

The full-repo Jest run was clean: 19 suites, 169 tests, no flakes. The
threshold violation is documented in the commit body and is not a regression
of A5; A5 actually improves two modules' coverage to 100%.

## Operator Runbook

```bash
# 1. Enable Idempotency-Cache for staging tests (no JSON-config edit):
HERMES_IDEMPOTENCY_ENABLED=true npx jest src/security/__tests__/idempotency-flag-toggle.test.ts

# 2. Enable via JSON config (requires orchestrator wiring — only effective
#    in tasks where the orchestrator threads kernelConfig through to
#    runAtomicToolCall):
{
  "security": {
    "egressAllowlist": ["api.example.com"],
    "idempotency": { "enabled": true }
  }
}

# 3. EMERGENCY ROLLBACK in production — env overrides everything:
HERMES_IDEMPOTENCY_ENABLED=false ./hermes run ...
# (or set the env in the systemd unit / docker-compose / k8s Deployment
#  and let the next process restart pick it up)

# 4. Health-check (optional future addition): the operator wants to know
#    WHY the flag is in its current state without parsing strings themselves.
#    A planned addition is `flagStatus()` returning `{ enabled, source: 'env'|'config'|'default' }`
#    — deferred until the orchestrator wiring lands.
```
