/**
 * MCP Transport Adapter — Hermes V7.1
 *
 * Bridges between Hermes Plugin Registry and Model Context Protocol (MCP) servers
 * running as Docker containers (stdio transport). JSON-RPC 2.0 over newline-delimited
 * stdout. Compatible with official github/github-mcp-server and forks.
 *
 * Source: Toqsick/hermes-v7 branch feature/hermes-v7.1-mcp-skill-integration
 * Last verified: 2026-06-29 with 44 tools loaded and live GitHub API test.
 */

const { spawn } = require('child_process');
const { auditLog } = require('../core/audit-log');

const JSONRPC_VERSION = '2.0';
const PROTOCOL_VERSION = '2024-11-05';

class MCPAdapter {
  constructor(config = {}) {
    if (!config.name) throw new Error('[MCPAdapter] name is required');
    if (!config.command) throw new Error('[MCPAdapter] command is required');
    if (!config.args) throw new Error('[MCPAdapter] args is required');

    this.name = config.name;
    this.command = config.command;
    this.args = config.args;
    this.env = { ...process.env, ...(config.env || {}) };
    this.auditEnabled = config.auditEnabled !== false;

    this.process = null;
    this.requestId = 0;
    this.pendingRequests = new Map();
    this.connected = false;
    this.tools = [];
    this.capabilities = null;
    this.stderrBuffer = '';
  }

  async connect() {
    return new Promise((resolve, reject) => {
      this._log('CONNECTING', { name: this.name, command: this.command });

      this.process = spawn(this.command, this.args, {
        env: this.env,
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      this.process.on('error', (err) => {
        this._log('CONNECT_ERROR', { name: this.name, error: err.message });
        reject(err);
      });

      // PITFALL: stderr is HEAVY in MCP servers. Collect separately.
      // If mixed with stdout, JSON-RPC parsing breaks.
      this.process.stderr.on('data', (chunk) => {
        this.stderrBuffer += chunk.toString();
        if (this.stderrBuffer.length > 10000) this.stderrBuffer = this.stderrBuffer.slice(-10000);
      });

      // Parse newline-delimited JSON-RPC responses from stdout
      let buffer = '';
      this.process.stdout.on('data', (chunk) => {
        buffer += chunk.toString();
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const msg = JSON.parse(line);
            this._handleMessage(msg);
          } catch (e) {
            // Not JSON — could be server log on stdout. Ignore.
          }
        }
      });

      this.process.on('exit', (code) => {
        this.connected = false;
        this._log('EXIT', { name: this.name, code });
      });

      // Initialize MCP handshake
      this._send({
        method: 'initialize',
        params: {
          protocolVersion: PROTOCOL_VERSION,
          capabilities: {},
          clientInfo: { name: 'hermes-v7.1-plugin-registry', version: '0.1.0' },
        },
      }).then((result) => {
        this.capabilities = result.capabilities;
        this.connected = true;
        this._log('CONNECTED', { name: this.name, capabilities: this.capabilities });
        resolve(result);
      }).catch(reject);

      // Timeout safety: 30s for handshake
      setTimeout(() => {
        if (!this.connected) {
          reject(new Error(`[MCPAdapter] Connection timeout for ${this.name}`));
        }
      }, 30000);
    });
  }

  _handleMessage(msg) {
    if (msg.id !== undefined && this.pendingRequests.has(msg.id)) {
      const { resolve, reject } = this.pendingRequests.get(msg.id);
      this.pendingRequests.delete(msg.id);
      if (msg.error) {
        reject(new Error(msg.error.message || JSON.stringify(msg.error)));
      } else {
        resolve(msg.result);
      }
      return;
    }
    if (msg.method) {
      this._log('NOTIFICATION', { method: msg.method, params: msg.params });
    }
  }

  _send(request) {
    return new Promise((resolve, reject) => {
      const id = ++this.requestId;
      this.pendingRequests.set(id, { resolve, reject });

      const jsonrpc = { jsonrpc: JSONRPC_VERSION, id, ...request };

      try {
        this.process.stdin.write(JSON.stringify(jsonrpc) + '\n');
      } catch (err) {
        this.pendingRequests.delete(id);
        reject(err);
      }
    });
  }

  async listTools() {
    if (!this.connected) throw new Error(`[MCPAdapter] ${this.name} not connected`);
    const result = await this._send({ method: 'tools/list' });
    this.tools = result.tools || [];
    return this.tools;
  }

  async callTool(toolName, args) {
    if (!this.connected) throw new Error(`[MCPAdapter] ${this.name} not connected`);
    const result = await this._send({
      method: 'tools/call',
      params: { name: toolName, arguments: args || {} },
    });
    this._log('TOOL_CALL', { name: this.name, tool: toolName });
    return result;
  }

  async shutdown() {
    if (this.process) {
      this._log('SHUTDOWN', { name: this.name });
      // PITFALL: stdin.end() FIRST, then SIGTERM, then SIGKILL.
      // Direct kill() leaves MCP server in unclean state.
      this.process.stdin.end();
      this.process.kill('SIGTERM');
      await new Promise((r) => setTimeout(r, 2000));
      if (!this.process.killed) this.process.kill('SIGKILL');
    }
    this.connected = false;
    this.tools = [];
  }

  _log(event, data) {
    if (this.auditEnabled) {
      auditLog('mcp-adapter', event, data);
    }
  }
}

module.exports = { MCPAdapter, PROTOCOL_VERSION };

/*
 * USAGE (live-tested 2026-06-29 with toqsick/github-mcp-server:develop):
 *
 *   const token = execSync('gh auth token', { encoding: 'utf-8' }).trim();
 *   const a = new MCPAdapter({
 *     name: 'github',
 *     command: 'docker',
 *     args: ['run', '-i', '--rm', '-e', 'GITHUB_PERSONAL_ACCESS_TOKEN',
 *            'toqsick/github-mcp-server:develop'],
 *     env: { GITHUB_PERSONAL_ACCESS_TOKEN: token },
 *   });
 *   await a.connect();
 *   console.log((await a.listTools()).length);  // 44
 *   const r = await a.callTool('search_repositories', { query: 'user:Toqsick' });
 *   await a.shutdown();
 *
 * LIVE-TEST-RESULT (2026-06-29):
 *   CONNECTED
 *   TOOLS_COUNT: 44
 *   TOOL_SAMPLE: add_comment_to_pending_review,add_issue_comment,add_reply_to_pull_request_comment,
 *                assign_copilot_to_issue,create_branch
 *   SEARCH_REPOS_RESULT: {"content":[{"type":"text","text":"{\"total_count\":5,\"items\":[
 *     {"name":"greyscripts","full_name":"Toqsick/greyscripts","stars":1,...}]}}"]}
 *   SHUTDOWN_OK
 */