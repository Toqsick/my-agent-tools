# Contract Tests & Production Evidence

> Extracted from `SKILL.md` (formerly §"Tests und Verification" + §"Production-Evidence").
> Load when writing the contract test suite for a new plugin type, migrating
> the `assert` runner to Jest, or referencing production evidence in a PR.

## Contract Tests

### Node.js (13 tests with `assert`)

- `TestSchemaValidation` (4 tests)
- `TestPluginLifecycle` (3 tests)
- `TestNamespaceConflictResolution` (3 tests)
- `TestAdapterInterface` (2 tests)
- `TestLoadtest` (1 test, 12+ plugins)

### Python (15 tests with `unittest`)

- `TestSchemaValidationAcceptsValidManifest`
- `TestSchemaValidationRejectsMissingField` (3 tests)
- `TestPluginLifecycle` (4 tests)
- `TestNamespaceConflictResolution` (3 tests)
- `TestAdapterInterfaceContract` (3 tests)
- `TestLoadtestTenPlusPlugins`

## Production-Reference

Complete working implementation:

- **Branch:** `feature/hermes-v7.1-mcp-skill-integration` in
  `Toqsick/hermes-v7`
- **Files:** `src/plugins/{registry.js, adapters/mcp-transport.js,
  mcp-github/, mocks/, __tests__/}`
- **Tests:** 13/13 contract tests green, 12 mock-plugins in 13ms loadtest
- **Live-Test:** Real GitHub API via `search_repositories` returns 5
  Toqsick repos

## Pitfalls (from V7.1 implementation 2026-06-29)

1. **`discover()` catches errors.** `LOAD_ERROR` is logged, not thrown.
   Tests must assert on `loaded.length`, not on `assert.rejects`. (V7.0
   pattern: defensive loading.)

2. **`??` vs `||` for default values.** When `conflict_policy: undefined`,
   `||` doesn't kick in (undefined is not falsy if the property exists).
   Use `??` for nullable-default values.

3. **Validation vs runtime-default mismatch.** `PluginManifest._validate()`
   checks `data.conflict_policy` (the raw value), not the computed default.
   Consistency fix: the validation expression must be identical to the
   setter expression.

4. **`entry_point` is relative to the plugin dir.** `index.js` →
   `plugins/PLUGIN_NAME/index.js`, NOT `plugins/PLUGIN_NAME/lib/main.js`.
   Keep the convention.

5. **MCP stderr collected separately.** MCP servers log heavily on stderr.
   Don't mix with the main buffer, or JSON-RPC parsing breaks.

6. **`process.stdin.end()` before `kill()`.** MCP-Adapter: clean shutdown
   sequence is `stdin.end()` → wait 2s → `SIGTERM` → `SIGKILL`. Direct
   `kill()` leaves the MCP server in an undefined state.

7. **MCP tool name ≠ REST-API endpoint.** `search_repositories`, not
   `list_repositories`. Tool names are MCP-server-specific — ALWAYS call
   `listTools()` first.

8. **`audit-log` path resolution for tests.** When the test directory is not
   in the Hermes repo, stub `core/audit-log` with a `require.resolve` patch
   OR a mock module.

9. **Token via `gh auth token`, not env-var.** GitHub CLI keeps the token
   in the keyring. The shell variable `GITHUB_PERSONAL_ACCESS_TOKEN` is
   empty in subshells unless exported.

10. **Docker-spawn vs HTTP-transport.** V7.1 uses stdio (Docker `run -i`),
    not HTTP. HTTP-Transport would be a future extension (analogous to
    MCP-Adapter transport factory).

11. **Token loading from `.env` with `set -a; source` (V7.2,
    2026-06-29).** When `.env`-lines contain special characters like `:`
    (e.g. `CLIENT_ID=1076d...:abc`), bash without `set -a` interprets the
    line as command substitution. Solution: ALWAYS
    `set -a && source ~/.hermes/.env && set +a` before Node test calls.
    Verify with `echo "${VAR_NAME:0:5}"`.

12. **Audit-log stub path relative to adapter file (V7.2,
    2026-06-29).** When `adapters/FOO.js` resolves `require('../core/audit-log')`,
    Node looks for `src/plugins/core/audit-log.js` (NOT
    `src/core/audit-log.js`). Test scripts must create the stub in the
    correct path: `path.join(__dirname, 'core', 'audit-log.js')`. A common
    error is `REAL_CORE_PATH = '/tmp/hermes-v7/src/core'` instead of
    `'/tmp/hermes-v7/src/plugins/core'`.

13. **Mode-validation BEFORE token-check (V7.2, 2026-06-29).** In the
    plugin's `invoke()`: validate input mode first, then load the token.
    Otherwise on unknown mode the user gets the misleading token-error
    message instead of "unknown mode". Pattern: `validModes.includes(mode)`
    as an early-return BEFORE `ensureConnected()` is called.

## Production-Evidence

- **Branch:** `feature/hermes-v7.1-mcp-skill-integration`
- **Issue:** https://github.com/Toqsick/hermes-v7/issues/5
- **Plugin-Skeleton (Python Reference):** `docs/v7.1-planning/plugin-skeleton.py`
- **Plugin-Registry (Node.js Production):** `src/plugins/registry.js`
- **MCP-Transport:** `src/plugins/adapters/mcp-transport.js`
- **Live-Test:** 44 real GitHub-MCP tools, 5 Toqsick repos via
  `search_repositories`
- **Tests:** 13/13 green in under 500ms
- **Loadtest:** 12 mock-plugins + 12 invokes in 13ms
