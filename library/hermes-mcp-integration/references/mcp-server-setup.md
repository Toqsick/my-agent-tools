# MCP Server Setup & Migration Guide

> Extracted from `SKILL.md` (formerly §"Migration-Guide" + integration-test
> code blocks). Load when wiring up an MCP server in plugin form, migrating
> a V7.0 `config.yaml` MCP entry to a plugin, or running the live integration
> test.

## Production-Pattern (Node.js / V7.0-compatible)

```javascript
const { PluginRegistry } = require('./src/plugins/registry');

// V7.0 (unchanged)
const skillLoader = new SkillLoader({ skillsDir: './skills' });
await skillLoader.loadAll();

// V7.1 (additive)
const registry = new PluginRegistry({ pluginsDir: './plugins' });
await registry.discover();

// Invoke
const result = await registry.invoke('mcp:github', {
  tool: 'search_repositories',
  args: { query: 'user:Toqsick' },
});

// List
console.log(registry.list());

// Shutdown (idempotent)
await registry.shutdown();
```

## MCP-Transport-Pattern

```javascript
const { MCPAdapter } = require('./src/plugins/adapters/mcp-transport');

const adapter = new MCPAdapter({
  name: 'github',
  command: 'docker',
  args: ['run', '-i', '--rm', '-e', 'GITHUB_PERSONAL_ACCESS_TOKEN', 'toqsick/github-mcp-server:develop'],
  env: { GITHUB_PERSONAL_ACCESS_TOKEN: process.env.GITHUB_TOKEN },
});

await adapter.connect();           // JSON-RPC initialize handshake
const tools = await adapter.listTools();
const result = await adapter.callTool('search_repositories', { query: 'user:Toqsick' });
await adapter.shutdown();
```

## Plugin-Manifest Example (`plugin.json`)

```json
{
  "name": "github",
  "version": "1.0.0",
  "kind": "mcp_tool",
  "namespace": "mcp",
  "entry_point": "index.js",
  "conflict_policy": "reject",
  "io_schema": {
    "input":  { "type": "object", "required": ["tool", "args"], "properties": {} },
    "output": { "type": "object" }
  },
  "shared_resources": ["github-api"],
  "env_requirements": { "GITHUB_PERSONAL_ACCESS_TOKEN": "required" }
}
```

## Plugin-Dir Layout

```
src/plugins/
├── README.md                          # Overview + Plugin-Manifest-Doku
├── registry.js                        # PluginRegistry-Klasse (Production)
├── adapters/
│   └── mcp-transport.js               # MCPAdapter (JSON-RPC stdio)
├── mocks/                             # 12 Mock-MCP-Plugins
│   └── mock-NAME/
│       ├── plugin.json
│       └── index.js
├── mcp-github/                        # Echtes GitHub-MCP-Plugin
│   ├── plugin.json
│   └── index.js
└── __tests__/
    └── registry.test.js               # 13 Contract-Tests
```

## Migration from V7.0

### Additiv (no breaking change)

```javascript
// V7.0: nur skills/
const sl = new SkillLoader({ skillsDir: './skills' });
await sl.loadAll();

// V7.1: skills/ + plugins/
const sl = new SkillLoader({ skillsDir: './skills' });
await sl.loadAll();

const pr = new PluginRegistry({ pluginsDir: './plugins' });
await pr.discover();
```

### MCP-Integration-Migration

```javascript
// BEFORE: separate MCP-Server-Konfiguration in config.yaml
// mcp_servers: { github: { command: 'docker', args: [...] } }

// AFTER: plugin.json pro MCP-Server
// plugins/mcp-github/plugin.json + index.js
```

### Backward-Kompatibilität

- V7.0 skills with `manifest: { name, version, concurrency_mode }` work unchanged
- V7.0 MCP config in `config.yaml` is still supported via `legacy-mcp-adapter`

## Dependencies

- **Hermes V7.0+** (`skill-loader`, `audit-log`, `gate.js`)
- **Node.js 20+** (for `??` nullish-coalescing and modern async patterns)
- **Docker** (for MCP-server containers — stdio transport)
- **Optional:** GitHub CLI (`gh auth token`) for token resolution

## Live Integration Test (echter MCP-Server)

```bash
# Live: echte GitHub-API via MCP
cd src/plugins && node test-mcp-integration.js
# Erwartet: CONNECTED → TOOLS_COUNT 44 → SEARCH_REPOS → SHUTDOWN_OK
```

### Performance-Benchmark

- **Discovery:** 12 mock-plugins in under 50ms
- **Load-Test:** 12 plugins + 12 probe-invokes in under 300ms
- **MCP-Connect:** stdio-handshake in under 5s
- **Tool-Call:** under 500ms per GitHub-API request
