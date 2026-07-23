# OpenCode CLI — Full Reference

Extracted from the `opencode` skill. Complete guide for OpenCode CLI.

## Prerequisites
- **Install:** `npm i -g opencode-ai@latest` or `brew install anomalyco/tap/opencode`
- **Auth:** `opencode auth login` or provider env vars (not needed for Ollama-only)
- **Verify:** `opencode --version`, `opencode auth list`

## Binary Resolution
Shell environments may resolve different binaries. If `opencode` not found:
```bash
which -a opencode
npm root -g  # find where npm put it
```
Use full path if needed: `$HOME/.hermes/node/bin/opencode run '...'`

## Ollama Integration (Local Models)
Use `ollama launch opencode --model <name>` — NOT `opencode run --model ollama/<name>`.
```bash
ollama launch opencode --model qwen3.6:27b
ollama launch opencode --model qwen3.6 --yes  # auto-pull if missing
```
Launch with `background=true, pty=true` for interactive use.

## One-Shot Tasks
```bash
opencode run "Add retry logic to API calls"
opencode run "Review config for security" -f config.yaml
opencode run "Debug CI failures" --thinking
opencode run "Refactor auth" --model openrouter/anthropic/claude-sonnet-4
```

## Interactive Sessions (Background)
```bash
terminal(command="opencode", workdir="~/project", background=true, pty=true)
# Send: process(action="submit", session_id="<id>", data="Implement OAuth")
# Exit: process(action="write", session_id="<id>", data="\x03")  # Ctrl+C
```

**Important:** Do NOT use `/exit` — it opens an agent selector. Use Ctrl+C or `process(action="kill")`.

## TUI Keybindings
| Key | Action |
|-----|--------|
| `Enter` | Submit (press twice if needed) |
| `Tab` | Switch agents (build/plan) |
| `Ctrl+P` | Command palette |
| `Ctrl+C` | Exit |

## Session Resume
```bash
opencode -c                    # Continue last session
opencode -s ses_abc123         # Specific session
```

## Common Flags
| Flag | Use |
|------|-----|
| `run 'prompt'` | One-shot execution |
| `-c` / `--continue` | Continue last session |
| `-s <id>` | Continue specific session |
| `--model provider/model` | Force model |
| `-f <path>` / `--file` | Attach file(s) |
| `--thinking` | Show thinking blocks |
| `--variant <level>` | Reasoning effort |

## PR Review
```bash
opencode pr 42
```

## Security & Bug Fix Workflow
```bash
opencode run "Fix SQL injection in login.py with parameterized queries"
opencode run "Replace hardcoded API keys with env vars" -f config.py
```

## Parallel Work
```bash
opencode run "Fix #101 and commit" workdir="/tmp/issue-101" background=true pty=true
opencode run "Add parser tests and commit" workdir="/tmp/issue-102" background=true pty=true
```

## Session & Cost Management
```bash
opencode session list
opencode stats
opencode stats --days 7 --models anthropic/claude-sonnet-4
```

## Pitfalls
1. Interactive `opencode` requires `pty=true`; `opencode run` does NOT
2. `/exit` is NOT valid — use Ctrl+C
3. PATH mismatch: npm global may install to `~/.hermes/node/bin/`
4. Ollama: Do NOT use `opencode run --model ollama/<name>` — use `ollama launch opencode`
5. Avoid sharing one working directory across parallel sessions
6. Enter may need to be pressed twice to submit in TUI

## Verification
```bash
opencode run "Respond with exactly: OPENCODE_SMOKE_OK"
```
