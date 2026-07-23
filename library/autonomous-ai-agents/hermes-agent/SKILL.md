---

name: hermes-agent
description: Use when user asks for hermes agent, Quick Start, Install, Interactive chat (default). NOT for writing code, web browsing. Configures, extends, and contributes to the Hermes Agent framework.
version: 2.1.0
author: Hermes Agent + Teknium
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - hermes
    - setup
    - configuration
    - multi-agent
    - spawning
    - cli
    - gateway
    - development
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills:
    - claude-code
    - codex
    - opencode
lane: koenigin
reasoning_effort: xhigh

---



# Hermes Agent

Hermes Agent is an open-source AI agent framework by Nous Research that runs in your terminal, messaging platforms, and IDEs. It belongs to the same category as Claude Code (Anthropic), Codex (OpenAI), and OpenClaw — autonomous coding and task-execution agents that use tool calling to interact with your system. Hermes works with any LLM provider (OpenRouter, Anthropic, OpenAI, DeepSeek, local models, and 15+ others) and runs on Linux, macOS, and WSL.

What makes Hermes different:

- **Self-improving through skills** — Hermes learns from experience by saving reusable procedures as skills. When it solves a complex problem, discovers a workflow, or gets corrected, it can persist that knowledge as a skill document that loads into future sessions. Skills accumulate over time, making the agent better at your specific tasks and environment.
- **Persistent memory across sessions** — remembers who you are, your preferences, environment details, and lessons learned. Pluggable memory backends (built-in, Honcho, Mem0, and more) let you choose how memory works.
- **Multi-platform gateway** — the same agent runs on Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email, and 10+ other platforms with full tool access, not just chat.
- **Provider-agnostic** — swap models and providers mid-workflow without changing anything else. Credential pools rotate across multiple API keys automatically.
- **Profiles** — run multiple independent Hermes instances with isolated configs, sessions, skills, and memory.
- **Extensible** — plugins, MCP servers, custom tools, webhook triggers, cron scheduling, and the full Python ecosystem.

People use Hermes for software development, research, system administration, data analysis, content creation, home automation, and anything else that benefits from an AI agent with persistent context and full system access.

**This skill helps you work with Hermes Agent effectively** — setting it up, configuring features, spawning additional agent instances, troubleshooting issues, finding the right commands and settings, and understanding how the system works when you need to extend or contribute to it.

**Docs:** https://hermes-agent.nousresearch.com/docs/

## Quick Start

```bash
# Install
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# Interactive chat (default)
hermes

# Single query
hermes chat -q "What is the capital of France?"

# Setup wizard
hermes setup

# Change model/provider
hermes model

# Check health
hermes doctor
```

---

## Key Commands (Quick Reference)

**Chat:** `hermes` (interactive) · `hermes chat -q "..."` (one-shot) · `hermes -w` (worktree mode)

**Config:** `hermes setup` · `hermes model` · `hermes config edit` · `hermes config set KEY VAL` · `hermes doctor`

**Tools/Skills:** `hermes tools` · `hermes tools enable/disable NAME` · `hermes skills list` · `hermes skills install ID`

**Gateway:** `hermes gateway run` · `hermes gateway install` · `hermes gateway setup`

**Sessions:** `hermes sessions browse` · `hermes --continue` · `hermes --resume SESSION`

**MCP:** `hermes mcp add NAME` · `hermes mcp list` · `hermes mcp test NAME`

**Cron:** `hermes cron list` · `hermes cron create SCHED` · `hermes cron edit ID`

**Profiles:** `hermes profile create NAME` · `hermes profile use NAME` · `hermes profile list`

> **Full CLI reference:** `skill_view(name="hermes-agent", file_path="references/cli-reference.md")`
> **Full slash command reference:** `skill_view(name="hermes-agent", file_path="references/slash-commands.md")`

---

## Key Paths & Config

```
~/.hermes/config.yaml       Main configuration
~/.hermes/.env              API keys and secrets
$HERMES_HOME/skills/        Installed skills
~/.hermes/sessions/         Session transcripts (*.jsonl)
~/.hermes/state.db          Canonical session store (SQLite + FTS5)
~/.hermes/logs/             Gateway and error logs
~/.hermes/auth.json         OAuth tokens and credential pools
~/.hermes/hermes-agent/     Source code (if git-installed)
```

Profiles use `~/.hermes/profiles/<name>/` with the same layout.

**20+ providers supported** — OpenRouter, Anthropic, Nous Portal, OpenAI Codex, GitHub Copilot, Google Gemini, DeepSeek, xAI, Hugging Face, Z.AI/GLM, MiniMax, Kimi, DashScope, and more. Set via `hermes model` or `hermes setup`.

> **Full config sections, provider table, and toolset list:** `skill_view(name="hermes-agent", file_path="references/configuration.md")`

---

## Spawning Additional Hermes Instances

Run additional Hermes processes as fully independent subprocesses for long autonomous missions.

**One-shot mode:**
```
terminal(command="hermes chat -q 'Research GRPO papers and write summary to ~/research/grpo.md'", timeout=300)
```

**Interactive PTY mode** (via tmux for prompt_toolkit):
```
terminal(command="tmux new-session -d -s agent1 -x 120 -y 40 'hermes -w'", timeout=10)
terminal(command="sleep 8 && tmux send-keys -t agent1 'Build a FastAPI auth service' Enter", timeout=15)
terminal(command="sleep 20 && tmux capture-pane -t agent1 -p", timeout=5)
```

**Prefer `delegate_task`** for quick bounded subtasks — less overhead. Use spawning for hours/days-long work.

> **Full spawning guide (multi-agent coordination, session resume, tips):** `skill_view(name="hermes-agent", file_path="references/spawning-agents.md")`

---

## Durable & Background Systems

Four systems run alongside the main conversation loop:

- **Delegation** (`delegate_task`) — synchronous subagent spawn, isolated context. Config: `delegation.*`
- **Cron** — durable scheduler. Drive via `cronjob` tool, `hermes cron`, or `/cron`. 3-min hard interrupt, `.tick.lock` prevents duplicate ticks.
- **Curator** — background skill lifecycle maintenance. Only touches `created_by: "agent"` skills. Never deletes (max action: archive). Config: `curator.*`
- **Kanban** — durable SQLite board for multi-profile/multi-worker collaboration. Gated `kanban_*` toolset for workers.

> **Full details on all four systems:** `skill_view(name="hermes-agent", file_path="references/durable-systems.md")`

---

## Security & Privacy

Key toggles (most require a fresh session to take effect):

- **Secret redaction** (on by default): `hermes config set security.redact_secrets true|false`
- **PII redaction** in gateway: `hermes config set privacy.redact_pii true|false`
- **Command approval** modes: `manual` (default) | `smart` | `off` — `hermes config set approvals.mode smart`
- **YOLO bypass**: `hermes --yolo` or `export HERMES_YOLO_MODE=1` (independent of secret redaction)

> **Full security/privacy toggle reference:** `skill_view(name="hermes-agent", file_path="references/security-privacy.md")`

---

## Voice & Transcription

- **STT:** Auto-detected provider priority — local faster-whisper (free) → Groq → OpenAI → Mistral. Config: `stt.enabled`, `stt.provider`.
- **TTS:** Edge TTS (default, free), ElevenLabs, OpenAI, MiniMax, Mistral, NeuTTS. `/voice on|tts|off`.

> **Full voice config reference:** `skill_view(name="hermes-agent", file_path="references/voice-transcription.md")`

---

## Troubleshooting Quick Fixes

| Problem | First step |
|---------|-----------|
| Voice not working | Check `stt.enabled: true`, verify provider installed, `/restart` or relaunch |
| Tool not available | `hermes tools` → check toolset enabled → `/reset` |
| Model/provider issues | `hermes doctor` → `hermes auth` → check `.env` |
| Changes not taking effect | `/reset` (tools/skills) or restart process (config/code) |
| Skills not showing | `hermes skills list` → `hermes skills config` → `/skill name` |
| Gateway issues | Check `~/.hermes/logs/gateway.log` |

> **Full troubleshooting guide:** `skill_view(name="hermes-agent", file_path="references/troubleshooting.md")`
> **Windows-specific quirks:** `skill_view(name="hermes-agent", file_path="references/windows-quirks.md")`

---

## Where to Find Things

| Looking for... | Location |
|----------------|----------|
| Config options | `hermes config edit` or [Configuration docs](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Available tools | `hermes tools list` or [Tools reference](https://hermes-agent.nousresearch.com/docs/reference/tools-reference) |
| Slash commands | `/help` in session or [Slash commands reference](https://hermes-agent.nousresearch.com/docs/reference/slash-commands) |
| Skills catalog | `hermes skills browse` or [Skills catalog](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog) |
| Provider setup | `hermes model` or [Providers guide](https://hermes-agent.nousresearch.com/docs/integrations/providers) |
| Platform setup | `hermes gateway setup` or [Messaging docs](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/) |
| MCP servers | `hermes mcp list` or [MCP guide](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) |
| Source code | `~/.hermes/hermes-agent/` |

---

## Contributing

Full contributor guide with project layout, tool/command authoring, testing, and prompt-builder extension notes:

> `skill_view(name="hermes-agent", file_path="references/contributor-guide.md")`

**Key rules:** Never break prompt caching · Maintain message role alternation · Use `get_hermes_home()` for paths · Config in `config.yaml`, secrets in `.env` · New tools need a `check_fn`.

Commit conventions: `fix:` · `feat:` · `refactor:` · `docs:` · `chore:`

---

## All Reference Files

| File | Content |
|------|---------|
| `references/cli-reference.md` | Full CLI command reference (all subcommands) |
| `references/slash-commands.md` | All in-session slash commands |
| `references/configuration.md` | Config sections, providers, toolsets |
| `references/security-privacy.md` | Security & privacy toggle details |
| `references/voice-transcription.md` | STT/TTS provider setup |
| `references/spawning-agents.md` | Spawning Hermes instances, multi-agent coordination |
| `references/durable-systems.md` | Delegation, cron, curator, kanban deep-dive |
| `references/troubleshooting.md` | Detailed troubleshooting guide |
| `references/windows-quirks.md` | Windows-specific issues and fixes |
| `references/contributor-guide.md` | Project layout, adding tools/commands, testing |
| `references/native-mcp.md` | MCP client integration details |
| `references/webhooks.md` | Webhook setup and event-driven patterns |
