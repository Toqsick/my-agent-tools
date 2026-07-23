---
name: claude-code-provider-profiles
description: "Use when user asks to configure Claude Code with multiple API providers, isolated settings directories, per-provider model routing, wrapper scripts, or provider-profile verification. NOT for one-off model selection or generic API credential setup. Establishes side-by-side profiles, plugin synchronization, supported environment variables, and the `--settings` workflow."
version: 1.0.0
author: Yuno
license: MIT
platforms:
  - linux
  - macos
metadata:
  hermes:
    tags:
      - Claude-Code
      - Provider
      - Profile
      - Z-AI
      - GLM
      - Multi-Config
    related_skills:
      - claude-code
      - coding-agents
trigger_keywords: ['settings', 'provider', 'model', 'side', 'user']
keywords: ['settings', 'provider', 'model', 'side', 'user']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['nous-multi-lane-routing', 'local-ai-security-hygiene']
---

# Claude Code — Multi-Provider Profile Setup

Run multiple Claude Code CLI profiles side-by-side, each pointing to a different API provider. The native binary stays the same; only `~/.claude-{provider}/settings.json` and a wrapper script differ.

## When to Use This Skill

- You want **Anthropic Pro** (OAuth) **AND** a **token-billed provider** (Z-AI, OpenRouter, etc.) on the same machine
- You created an isolated profile during a session and want to find the pattern again
- You need to **verify** a provider profile works (`doctor` subcommand pattern)
- You want **per-provider model routing** (different backend models per Claude tier)

## Core Pattern: `--settings` Flag

Claude Code v2.x supports `--settings <path>` to load a specific settings file instead of `~/.claude/settings.json`. This is the key to multi-provider isolation.

```bash
# Create an isolated settings directory
mkdir -p ~/.claude-{provider}/

# Run with custom settings
claude --settings ~/.claude-zai/settings.json -p "task" --max-turns 5
```

## Step-by-Step

### 1. Create Settings File

Write `~/.claude-{provider}/settings.json`. Minimum viable:

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "<your-token>",
    "ANTHROPIC_BASE_URL": "https://api.provider.com/anthropic"
  }
}
```

### 2. Configure Model Routing (Optional)

Override which Claude-tier maps to which backend model:

```json
{
  "env": {
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "fast-model",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "balanced-model[1m]",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "heavy-model[1m]",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "1000000"
  }
}
```

### 3. Create Wrapper Script

Write to `~/50-System/bin/claude-{provider}` (or wherever your PATH picks up):

```bash
#!/usr/bin/env bash
CLAUDE_BIN="$HOME/.local/bin/claude"
SETTINGS="$HOME/.claude-{provider}/settings.json"

if [ "${1:-}" = "doctor" ]; then
  echo "=== Health Check ==="
  echo "Binary: $CLAUDE_BIN ($($CLAUDE_BIN --version 2>/dev/null || echo '?'))"
  echo "Settings: $SETTINGS"
  exit 0
fi

exec "$CLAUDE_BIN" --settings "$SETTINGS" "$@"
```

```bash
chmod +x ~/50-System/bin/claude-{provider}
```

### 4. Sync Plugins & Marketplaces (Required!)

Custom settings files **start with empty plugins/marketplaces**. Sync from your Anthropic profile:

```python
import json
a = json.load(open('~/.claude/settings.json'))
z = json.load(open('~/.claude-zai/settings.json'))
for key in ['enabledPlugins', 'extraKnownMarketplaces',
            'skipWorkflowUsageWarning', 'agentPushNotifEnabled']:
    if key in a:
        z[key] = a[key]
json.dump(z, open('~/.claude-zai/settings.json', 'w'), indent=2)
```

### 5. Verify

```bash
claude-{provider} doctor                     # Health check
claude-{provider} -p "ok" --max-turns 1      # Print-mode smoke test
claude-{provider} --version                   # Version (no banner)
```

## Wrapper Features (Recommended)

A good wrapper provides:

| Feature | Purpose |
|---|---|
| **`doctor` subcommand** | Health check: binary, settings, token length, endpoint, routing, ping test |
| **Start banner** | Visual signal (cyan=Z-AI, etc.), only in interactive mode |
| **Banner suppression** | No banner for `-p`/`--version`/`--help`/`doctor`/`auth`/`mcp`/`agents`/`update`/`plugin` |
| **PATH independence** | Absolute paths to binary and settings — works from any CWD |

## Supported Env Vars (Claude Code)

| Variable | Purpose |
|---|---|
| `ANTHROPIC_AUTH_TOKEN` | API token (overrides OAuth) |
| `ANTHROPIC_BASE_URL` | Custom API endpoint |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Haiku-tier model override |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Sonnet-tier model override |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | Opus-tier model override |
| `CLAUDE_CODE_AUTO_COMPACT_WINDOW` | Context pressure threshold (e.g. `1000000`) |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Reduce network noise (`1`) |
| `API_TIMEOUT_MS` | Timeout override (e.g. `3000000`) |

## Known Limitations

- **`~/.claude/` is hardcoded** for daemon, history, plans, session DB — never overridable.
- **Two profiles sharing the same CWD** share session history. Use different directories or run sequentially.
- **Rate limits** are per-token, not per-instance.

## Pitfalls

1. **Settings file starts empty** — no plugins, no marketplaces. Always sync from Anthropic profile.
2. **`--settings` flag before `-p`** — `claude --settings X -p "..."` works; `claude -p "..." --settings X` may not.
3. **Token must match endpoint** — Z-AI tokens on Anthropic's API will 401.
4. **Model names are provider-specific** — `glm-5.2[1m]` won't work on Anthropic's endpoint.
5. **Effort levels may differ** — `effortLevel: max` is Z-AI's recommendation; Anthropic defaults to auto.
6. **Doctor ping test costs** — ~$0.001 per call on most providers.
7. **Banner noise in piped output** — always suppress for `-p`/`--version`/non-interactive mode.

## References

- [provider-profiles.md](references/provider-profiles.md) — Basti's verified Z-AI/GLM setup (2026-07-15), full comparison table, verified test results
- [troubleshooting.md](references/troubleshooting.md) — known issues and fixes