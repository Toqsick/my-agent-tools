---
name: hermes-mcp-integration
version: 1.0.0
description: Use when integrating Hermes V7 native MCP client (stdio/HTTP servers, tool discovery, config.yaml setup).
summary: V7.1 Plugin-Registry for MCP tools and skill bridges and adapters
triggers:
- User mentions MCP plugin or Model Context Protocol integration or plugin registry
- User references Hermes V7.1 architecture
- Task involves extending Hermes with new tools or services or plugins
- User asks about namespace conflicts between MCP and Skills
- Code review of plugin manifests
entrypoints:
- plugin-discovery
- plugin-registry
- mcp-transport
- manifest-validation
- namespace-resolution
worker_roles:
- plugin-author
- integration-engineer
- contract-test-author
capabilities:
- plugin discovery via filesystem scan and package.json entry-points
- manifest validation JSON-Schema v1 with kind and namespace and io_schema
- namespace conflict resolution reject replace coexist_alias
- MCP stdio transport JSON-RPC over Docker spawn
- contract tests for schema lifecycle conflict adapter loadtest
- audit log integration via Hermes auditLog
- V7.0 additive compatibility no breaking changes to skill-loader
hard_rules:
- always validate plugin.json BEFORE registering
- never silently overwrite existing plugin, use conflict_policy
- always use namespace prefix skill vs mcp vs adapter
- never modify Hermes V7.0 files, V7.1 plugin registry is additive
- always provide contract tests for new plugin types
- always log plugin lifecycle events to audit-log
- MCP transport must handle connection failures gracefully
- io_schema validation should be soft-warning not hard-block
lane: worker-flash
reasoning_effort: high
author: Hermes Agent
license: MIT
---



# Hermes V7.1 MCP Integration und Plugin-Registry

## Mission

Hermes-V7.1 introduces a **Plugin-Registry-Pattern** that registers external
plugins (MCP-Tools, Skill-Bridges, Adapters) alongside the V7.0 skill-loader.
The registry is **additive** — V7.0 skills continue to work unchanged, V7.1
plugins extend the system.

## When to Load This Skill

- Adding a new MCP server, HTTP-API plugin, or skill-bridge to Hermes
- Designing or reviewing a `plugin.json` manifest
- Resolving namespace conflicts between `mcp:` / `skill:` / `adapter:`
- Wiring up an MCP stdio transport (Docker → JSON-RPC)
- Authoring contract tests for the plugin registry
- Questions about the `usage_score` health telemetry pattern

For deep dives, load the matching `references/*.md` file (see References).

## Architecture (Schichtenbild)

```
┌────────────────────────────────────────────────────────────┐
│  Hermes Agent Runtime                                       │
│  ┌──────────────────────┐    ┌──────────────────────┐      │
│  │ V7.0 skill-loader    │    │ V7.1 PluginRegistry  │      │
│  │ (src/modules/)       │    │ (src/plugins/)       │      │
│  │ - loads skills/      │    │ - discovers plugins/ │      │
│  │ - validates manifest │    │ - validates plugin.json│  │
│  │ - V7.0 contract      │    │ - namespace-resolution │  │
│  └──────────────────────┘    └──────────────────────┘      │
│           ↓                            ↓                   │
│       Skill-Aufruf              Plugin-Aufruf              │
│           ↓                            ↓                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Audit-Log (JSONL, append-only)                      │   │
│  │  [skill-loader] LOADED + [plugin-registry] LOADED   │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
              ↓                            ↓
       ┌──────────────┐          ┌──────────────────┐
       │ V7.0 Skills  │          │ V7.1 Plugins     │
       │ skill:NAME   │          │ mcp:NAME         │
       │ (Hermes-Skill)│         │ adapter:NAME     │
       └──────────────┘          └──────────────────┘
                                              ↓
                                   ┌──────────────────┐
                                   │ MCP Server       │
                                   │ (Docker stdio)   │
                                   │ github-mcp-server│
                                   │ json-rpc 2.0     │
                                   └──────────────────┘
```

## Plugin-Manifest-Schema (v1) — Outline

Every plugin ships a `plugin.json` validated by `PluginManifest._validate()`.

**Required fields:** `name` (kebab-case), `version` (semver), `kind`,
`namespace`, `entry_point`.

### Valid `kind` Values

- `mcp_tool` — MCP-transport wrapper (Docker stdio JSON-RPC)
- `skill_bridge` — V7-skill-to-plugin adapter
- `adapter` — generic adapter (e.g. HTTP-client, DB-connector)

### Valid `namespace` Values (Namespace-Prefix-Pattern)

- `mcp` → `mcp:github`
- `skill` → `skill:github`
- `adapter` → `adapter:github`

### Conflict Policies

- `reject` (default) — second plugin with same `full_name` → `LOAD_ERROR`
- `replace` — existing plugin archived in `archivedConflicts[]`, new one wins
- `coexist_alias` — new plugin gets suffix `-2`, `-3`, ...

### Soft vs Hard I/O-Validation

- **Soft (recommended):** logs warning to audit-log, lets invoke proceed
- **Hard (optional):** throws error — caller must fix schema

Soft-warning is preferred for V7.1 to avoid breaking changes.

> Full JSON example for `plugin.json`: see
> `references/mcp-server-setup.md`. Production `PluginRegistry` code:
> `references/plugin-registry-nodejs-production.js`.

## Quickstart

### Discover and Invoke a Plugin

```javascript
const { PluginRegistry } = require('./src/plugins/registry');

const registry = new PluginRegistry({ pluginsDir: './plugins' });
await registry.discover();

const result = await registry.invoke('mcp:github', {
  tool: 'search_repositories',
  args: { query: 'user:Toqsick' },
});

console.log(registry.list());
await registry.shutdown();
```

### Wire up an MCP Server (stdio + JSON-RPC)

```javascript
const { MCPAdapter } = require('./src/plugins/adapters/mcp-transport');

const adapter = new MCPAdapter({
  name: 'github',
  command: 'docker',
  args: ['run', '-i', '--rm', '-e', 'GITHUB_PERSONAL_ACCESS_TOKEN',
         'toqsick/github-mcp-server:develop'],
  env: { GITHUB_PERSONAL_ACCESS_TOKEN: process.env.GITHUB_PERSONAL_ACCESS_TOKEN },
});

await adapter.connect();           // JSON-RPC initialize handshake
const tools = await adapter.listTools();
const result = await adapter.callTool('search_repositories',
                                      { query: 'user:Toqsick' });
await adapter.shutdown();
```

> Full Node.js production code:
> `references/mcp-transport-nodejs-production.js`. End-to-end setup +
> `config.yaml` migration: `references/mcp-server-setup.md`.

## Critical Warnings (Read First)

1. **V7.1 is additive** — never modify V7.0 files; the registry is a parallel layer.
2. **Always validate `plugin.json` BEFORE registering** — fail-fast on bad manifests.
3. **Never silently overwrite** — surface conflicts via `conflict_policy`,
   don't `Map.set` blindly.
4. **Soft I/O-validation** — log warnings, don't block invokes (avoid breaking V7.0).
5. **Audit-log every lifecycle event** — `LOADED`, `INVOKED`, `LOAD_ERROR`,
   `CONFLICT_REPLACED`, `SHUTDOWN`, etc. The audit trail is non-negotiable.
6. **MCP stderr is separate** — never mix with stdout or JSON-RPC parsing breaks.
7. **Shutdown sequence:** `stdin.end()` → wait 2s → `SIGTERM` → `SIGKILL`. Never
   just `kill()` an MCP server.
8. **MCP tool name ≠ REST endpoint** — tool names are server-specific, ALWAYS
   call `listTools()` first.

## Plugin Pattern Outline

A plugin occupies one directory under `plugins/` with two files:

```
plugins/<namespace>-<name>/
├── plugin.json     # validated against JSON-Schema v1
└── index.js        # exports { invoke, [shutdown], [manifest] }
```

The `invoke()` signature is `(input) => Promise<result>`. Errors thrown from
`invoke()` propagate up; the registry's telemetry hook automatically
decrements `usage_score` on error (V7.2+). See
`references/health-score-pattern.md` for the telemetry contract.

For HTTP-transport plugins (REST services without an MCP server), use a
sibling `HTTPAdapter` and follow the pattern in
`references/http-adapter-pattern.md`.

## References

| File                                          | When to Load |
|-----------------------------------------------|--------------|
| `references/mcp-server-setup.md`              | Wiring up an MCP server, migrating `config.yaml` → plugin, end-to-end setup |
| `references/health-score-pattern.md`          | `usage_score` telemetry fields, telemetry hook, `healthReport()`, V7.2 pitfalls |
| `references/http-adapter-pattern.md`          | Plugin against a REST/HTTPS API (Todoist, Notion, Linear) without an MCP server |
| `references/tests-contract.md`                | Contract-test suite, `assert` → Jest migration, production evidence |
| `references/plugin-registry-nodejs-production.js`  | Drop-in `PluginRegistry` + `PluginManifest` production code |
| `references/mcp-transport-nodejs-production.js`    | Drop-in `MCPAdapter` (JSON-RPC over stdio) production code |

## Templates

- `templates/health-score-manifest.template.json` — `plugin.json` template
  with `usage_score` field (copy + replace).
- `templates/health-score-plugin-invoke.template.js` — V7.2-compliant plugin
  stub with action-dispatch + error-propagation.

## Anti-Patterns

- Direct `git push` to main without review
- Plugin-manifest without `io_schema` (blocks soft-validation)
- MCP-Adapter without timeout handling
- Conflict-policy `replace` without an archival strategy
- Token hardcoded in `plugin.json` (use ENV-var / `.env`)
- Skipping audit-log integration (V7.0 audit-log is critical)
- Plugin without contract tests

## Verbundene Skills

- **hermes-orchestration** — Queen-Lane-Plan-Pattern (Multi-Lane-Orchestration)
- **depps-orchestration** — Depp-Worker for mechanical plugin fixes
- **mcp-server-authoring** — MCP-server creation (upstream)
- **native-mcp** — Hermes-internal MCP integration
- **github-workflow** — uses `github`-MCP-plugin for issue/PR workflows
