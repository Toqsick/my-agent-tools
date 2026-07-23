# HTTP-Adapter Pattern (V7.2+)

> Extracted from `SKILL.md` (formerly §"HTTP-Adapter-Pattern"). Load when
> integrating a plugin against a service that exposes a REST/HTTPS API and
> has **no** MCP server (e.g. Todoist, Notion, Linear). For MCP servers
> (stdio + JSON-RPC), use the MCP-Adapter pattern instead.

## Use Case

Plugin integration with services that do NOT have an MCP server. REST/HTTPS
APIs are consumed via `https` transport instead of stdio JSON-RPC.

## MCP-Adapter vs HTTP-Adapter

| Aspect          | MCP-Adapter                          | HTTP-Adapter                          |
|-----------------|--------------------------------------|---------------------------------------|
| Transport       | stdio (Docker spawn)                 | HTTPS (Node.js `https` module)        |
| Protocol        | JSON-RPC 2.0                         | REST (HTTP GET/POST/PUT/DELETE)       |
| Discovery       | `tools/list` (all tools upfront)     | Per-endpoint (static in plugin manifest) |
| Auth            | Per-server (Docker env-var)          | Bearer token / OAuth / API-Key        |
| Response Format | `{content: [{type: 'text', text: '...'}]}` | Raw JSON or paginated wrapper     |
| Error           | JSON-RPC error code                  | HTTP status code (`200`–`299` = OK)   |

## Production-Pattern

```javascript
const https = require('https');

class HTTPAdapter {
  constructor(config = {}) {
    if (!config.token) throw new Error('token required');
    this.token = config.token;
    this.host = config.host;            // 'api.service.com'
    this.basePath = config.basePath;    // '/api/v1'
    this.timeout = config.timeout || 30000;
  }

  _request(method, path, body = null) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: this.host,
        port: 443,
        path: this.basePath + path,
        method,
        headers: {
          'Authorization': `Bearer ${this.token}`,
          'User-Agent': 'hermes-v7.2-plugin/1.0.0',
          'Accept': 'application/json',
        },
        timeout: this.timeout,
      };
      let payload = null;
      if (body) {
        payload = JSON.stringify(body);
        options.headers['Content-Type'] = 'application/json';
        options.headers['Content-Length'] = Buffer.byteLength(payload);
      }

      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            try { resolve(data ? JSON.parse(data) : {}); }
            catch (e) { resolve(data); }
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${data.slice(0, 500)}`));
          }
        });
      });
      req.on('timeout', () => req.destroy(new Error(`Timeout after ${this.timeout}ms`)));
      req.on('error', err => reject(err));
      if (payload) req.write(payload);
      req.end();
    });
  }

  // Sample methods
  async listProjects() {
    const response = await this._request('GET', '/projects');
    return response.results || response;  // paginated unwrap (see pitfalls)
  }

  async createTask(taskData) {
    return this._request('POST', '/tasks', taskData);
  }
}
```

## Pitfalls (HTTP-Adapter)

1. **Paginated response wrapper.** Many APIs (Todoist, Notion, Linear) return
   `{results: [...], next_cursor}` instead of a direct array. ALWAYS unwrap with
   `response.results || response` in the plugin code, NOT in the adapter (the
   adapter stays generic).

2. **API docs become stale quickly.** `developer.todoist.com/api/v1/` replaced
   `/rest/v2` in April 2026. On `401`/`410` errors: web-search for current docs
   first, then update the endpoint.

3. **Bearer-Token preferred.** Basic Auth is deprecated by many APIs.
   `Authorization: Bearer ***` is the standard for Personal Access Tokens.

4. **Priority scale is API-specific.** Todoist uses an inverted scale
   (`1`=lowest, `4`=highest) while Hermes / Perplexity use `P1`=highest.
   Map in the plugin layer, NOT in the adapter.

5. **`due_string` format is strict.** Todoist accepts ONLY `today` /
   `tomorrow` / concrete dates, NOT `this-week` / `next-day`. Free strings
   yield HTTP 400 "Invalid date format".

6. **Token security via `.env`.** `chmod 600 ~/.hermes/.env`, NEVER put tokens
   in `plugin.json` or commit them to Git. Hermes blocks direct reads of
   `.env` via defense-in-depth, but a terminal can bypass this.

7. **Audit-Log stub for tests.** Test scripts need a `core/audit-log.js` stub
   in the path relative to the adapter. For `src/plugins/adapters/FOO.js`,
   stub `src/plugins/core/audit-log.js`.

## Reference Implementation: Todoist V7-Plugin

- `src/plugins/adapters/todoist-http.js` — HTTP-Adapter (~180 lines)
- `src/plugins/mcp-todoist/` — Plugin with 6 modes
  (`ping`, `list_projects`, `create`, `review`, `cleanup`, `structure`)
- `src/plugins/yuno-auto-plan.js` — helper: `publishPlan`, `getStand`,
  `getNextUps`
- Live-Test: 7 real projects loaded, test project created, 4 tasks with
  `P1`–`P4` mapping
- Token-Storage: `~/.hermes/.env` (`chmod 600`, NOT in git)

## Discovery-Helper for new HTTP APIs

See `scripts/api-discovery.sh` for quick-probing a REST/HTTP API on current
endpoints and auth mode. Useful for every new plugin integration, BEFORE
hours of code-dev are invested.

```bash
# Sample: Probe Todoist API
./scripts/api-discovery.sh api.todoist.com /api/v1 TODOIST_API_TOKEN
# Sample: Probe Notion API
./scripts/api-discovery.sh api.notion.com /v1 NOTION_API_TOKEN
```

Output shows: HTTP status, auth mode, pagination pattern
(`results` / `data` / `items` / direct-array), auth-failure code.
