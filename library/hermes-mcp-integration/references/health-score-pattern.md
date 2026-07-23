# V7.2 Plugin Health-Score Pattern

> Extracted from `SKILL.md` (formerly §"V7.2 Health-Score-Pattern"). Load only when
> you need to add telemetry fields to a plugin manifest, implement the `invoke()`
> hook, or interpret `healthReport()` output.

## Purpose

Each plugin receives a runtime `usage_score` (`0.0` – `1.0`) for health
monitoring, auto-deprecation of low-score plugins, and UX prioritization in
plugin browsers. Default for freshly-registered plugins is `1.0`.

## Manifest Schema Extension

```javascript
this.usage_score = typeof data.usage_score === 'number'
  ? Math.max(0, Math.min(1, data.usage_score))   // clamp to [0, 1]
  : 1.0;                                          // default: fresh registration
this.last_invoked_at = null;
this.invoke_count = 0;
this.error_count = 0;
```

## Telemetry Hook in `invoke()`

```javascript
async invoke(fullName, input) {
  const record = this.plugins.get(fullName);
  // ... validation ...
  record.manifest.last_invoked_at = new Date().toISOString();
  record.manifest.invoke_count = (record.manifest.invoke_count || 0) + 1;
  try {
    const result = await record.adapter.invoke(input);
    record.manifest.usage_score = Math.min(1.0, record.manifest.usage_score + 0.01);
    return result;
  } catch (err) {
    record.manifest.error_count = (record.manifest.error_count || 0) + 1;
    record.manifest.usage_score = Math.max(0.0, record.manifest.usage_score - 0.05);
    throw err;
  }
}
```

## `healthReport()` Method

```javascript
healthReport() {
  return Array.from(this.plugins.values()).map(r => ({
    name: r.manifest.full_name,
    version: r.manifest.version,
    usage_score: parseFloat(r.manifest.usage_score.toFixed(3)),
    invoke_count: r.manifest.invoke_count || 0,
    error_count: r.manifest.error_count || 0,
    last_invoked_at: r.manifest.last_invoked_at,
    health: r.manifest.usage_score >= 0.7 ? 'healthy'
          : r.manifest.usage_score >= 0.4 ? 'degraded'
          : 'critical',
  })).sort((a, b) => b.usage_score - a.usage_score);
}
```

## Score Bands

| Score-Bereich  | Klassifikation | Interpretation |
|----------------|----------------|----------------|
| `0.7` – `1.0`  | `healthy`      | Plugin runs reliably |
| `0.4` – `0.7`  | `degraded`     | Has errors but still runs |
| `0.0` – `0.4`  | `critical`     | Many errors or never used |

## Validation Rules (learned 2026-06-30)

- `NaN` → **reject** (Type-Error)
- `string` → **reject** (Type-Error)
- Out-of-Range (e.g. `-0.1`, `1.5`) → **clamp** to `[0, 1]` (NO Error)
- Default when `undefined` → **`1.0`** (freshly registered)

Clear separation: Type-Errors hard-reject, Range-Errors soft-clamp.
Rationale: telemetry drift over time can produce out-of-range values — that is
normal drift, not data corruption.

## Pitfalls (V7.2)

**14. Coverage-Threshold with many mocks.** If `src/plugins/mock-*/` exist for
load-testing, they drag the global coverage number down. Do NOT lower the global
threshold (e.g. 60→25%); instead exclude mocks via `collectCoverageFrom`:

```json
"collectCoverageFrom": [
  "src/**/*.js",
  "healthcheck.js",
  "!src/**/__tests__/**",
  "!src/plugins/mock-*/**"
]
```

Coverage-threshold stays at 60–75% (production-code quality), mocks are
excluded.

**15. Health-Score validation: out-of-range vs type-error.** Tests claiming
"rejects `usage_score > 1.0`" or "rejects `usage_score < 0`" are wrong because
out-of-range is clamped. Tests must check Type-Errors (`NaN`, `string`), not
Range-Errors. Test descriptions should be "rejects `usage_score = NaN`" and
"rejects `usage_score` as string".

**16. Migration `assert`-Runner to Jest.** V7.1 tests were standalone scripts
with a custom `assert + test()` runner. To migrate to Jest:

1. `assert.strictEqual(a, b)` → `expect(a).toBe(b)`
2. `assert.throws(() => fn())` → `expect(() => fn()).toThrow(/pattern/)`
3. Async-Tests: `assert.rejects` → `await expect(promise).rejects.toThrow()`
4. Custom `test()` runner out, replace with `test('name', fn)`
5. `beforeEach`/`afterEach` for tmp-Dir-Setup (instead of global stub)
6. `audit-log` stub for isolated tests in correct path:
   `path.join(__dirname, '..', 'audit-log-XXX-stub.js')` + `Module._resolveFilename` patch

**17. Test "structure requires sections" — order matters.** For the
Todoist-Plugin (and similar): `project_id` is validated FIRST, then `sections`.
Test expectations must match the `project_id|sections` pattern, not only
`sections`. Otherwise the test fails even though the code is correct.

## Templates

- `templates/health-score-manifest.template.json` — `plugin.json` template with
  `usage_score` field. Copy + replace fields.
- `templates/health-score-plugin-invoke.template.js` — Plugin stub with
  V7.2-compliant `invoke()` pattern (input validation, action dispatch,
  error propagation for automatic score decrement).

## Production Evidence (2026-06-30)

- **Issue:** https://github.com/Toqsick/hermes-v7/issues/6
- **Commit:** `7809a6c` (on `feature/hermes-v7.1-mcp-skill-integration`)
- **Test-Result:** 36/36 green (Jest: 18 registry + 10 todoist + 8 health-score)
- **Coverage `registry.js`:** 75% lines, 93% functions, 71% branches
- **Branch-Status:** 8 commits, 2 issues open (#5 V7.1 Complete, #6 V7.2 Polish)

## V7.2+ Roadmap (Update 2026-06-30)

- [x] **Health-Score** — `usage_score` field + telemetry ✅ Commit `7809a6c`
- [x] **Jest-Suite** — Migration from `assert` to Jest with coverage ✅ Commit `7809a6c`
- [ ] **Plugin-Marketplace** — external repo for community plugins
- [ ] **HTTP-Transport for MCP** — not just Docker stdio
- [ ] **Plugin-Sandboxing** — V8 isolation for untrusted plugins
- [ ] **Auto-Update-Mechanismus** — major-version notifications
- [ ] **Manifest-Schema v2** — breaking changes for major-version pin
