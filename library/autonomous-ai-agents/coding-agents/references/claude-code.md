# Claude Code — Full Reference

Extracted from the `claude-code` skill. Complete orchestration guide for Claude Code (Anthropic).

## Prerequisites
- **Install:** `npm install -g @anthropic-ai/claude-code`
- **Auth:** `claude auth login --console` (API key) or `claude auth login --sso` (Enterprise)
- **Health:** `claude doctor`
- **Version:** `claude --version` (requires v2.x+)

## Two Modes

### Print Mode (`-p`) — Preferred
```bash
claude -p "Task" --allowedTools "Read,Edit" --max-turns 10
```
- One-shot, exits when done. No PTY. Skips all interactive dialogs.

### Interactive PTY (via tmux)
```bash
tmux new-session -d -s claude-work -x 140 -y 40
tmux send-keys -t claude-work 'cd /project && claude' Enter
sleep 5 && tmux send-keys -t claude-work 'Your task' Enter
```

**Trust dialog:** `Enter` (default = Yes). **Permissions dialog (with `--dangerously-skip-permissions`):** `Down` then `Enter`.

## Print Mode Deep Dive

### JSON Output
```bash
claude -p "Analyze auth.py" --output-format json --max-turns 5
```
Returns: `session_id`, `num_turns`, `total_cost_usd`, `subtype` (`success`, `error_max_turns`, `error_budget`), `usage`, `modelUsage`.

### Streaming JSON
```bash
claude -p "Write summary" --output-format stream-json --verbose --include-partial-messages
```

### Piped Input
```bash
git diff HEAD~3 | claude -p "Summarize" --max-turns 1
```

### JSON Schema (Structured Extraction)
```bash
claude -p "List functions" --output-format json --json-schema '{"type":"object","properties":{"functions":{"type":"array","items":{"type":"string"}}},"required":["functions"]}' --max-turns 5
```

### Session Continuation
```bash
# Save session ID from JSON output, then:
claude -p "Continue" --resume <session_id> --max-turns 5
# Or resume most recent in same directory:
claude -p "What did you do?" --continue
```

### Bare Mode (CI/Scripting)
```bash
claude --bare -p "Run tests" --allowedTools "Read,Bash" --max-turns 10
```
Skips hooks, plugins, MCP, CLAUDE.md, OAuth. Fastest startup. Requires `ANTHROPIC_API_KEY`.

## CLI Flags Reference

### Session & Environment
| Flag | Effect |
|------|--------|
| `-p, --print` | Non-interactive one-shot |
| `-c, --continue` | Resume most recent in cwd |
| `-r, --resume <id>` | Resume specific session |
| `--fork-session` | New ID on resume |
| `--max-turns <n>` | Limit agentic loops (print only) |
| `--max-budget-usd <n>` | Cap spend (print only) |
| `--fallback-model <model>` | Auto-fallback on overload |
| `--bare` | Skip hooks/plugins/MCP/CLAUDE.md/OAuth |
| `--dangerously-skip-permissions` | Auto-approve ALL tool use |

### Output Format
| Flag | Effect |
|------|--------|
| `--output-format json` | Single result object |
| `--output-format stream-json` | NDJSON events |
| `--json-schema <schema>` | Structured JSON output |
| `--verbose` | Full turn-by-turn output |

### Tool Whitelist/Blacklist
```
Read, Edit, Write, Bash, WebSearch, WebFetch
Bash(git *), Bash(git commit *)
mcp__<server>__<tool>
```

## Settings Hierarchy
1. CLI flags → 2. `.claude/settings.local.json` → 3. `.claude/settings.json` → 4. `~/.claude/settings.json`

## CLAUDE.md Hierarchy
1. `~/.claude/CLAUDE.md` (global) → 2. `./CLAUDE.md` (project) → 3. `.claude/CLAUDE.local.md` (personal)

## Hooks (8 Types)
`UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Notification`, `Stop`, `SubagentStop`, `PreCompact`, `SessionStart`

## MCP Scopes
| Flag | Scope | Storage |
|------|-------|---------|
| `-s user` | Global | `~/.claude.json` |
| `-s local` | Project personal | `.claude/settings.local.json` |
| `-s project` | Project shared | `.claude/settings.json` |

## Cost Tips
1. Use `--max-turns` to prevent runaway loops
2. Use `--max-budget-usd` (min ~$0.05)
3. `--effort low` for simple tasks
4. `--bare` for CI to skip discovery overhead
5. Pipe input instead of having Claude read files
6. Start new sessions for distinct sessions

## Pitfalls
1. Interactive mode REQUIRES tmux
2. `--dangerously-skip-permissions` dialog defaults to "No, exit"
3. `--max-budget-usd` minimum is ~$0.05
4. `--max-turns` is print-mode only
5. Trust dialog only appears once per directory
6. Slash commands only work in interactive mode
7. `--bare` skips OAuth — needs `ANTHROPIC_API_KEY`
8. Context degrades above 70% — use `/compact`
