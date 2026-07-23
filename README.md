# my-agent-tools

**Basti's private, version-controlled Claude Code toolkit.**

One curated source of truth for the skills, subagents, and MCP servers I've actually vetted — so
every Claude Code instance and every agent runs the *same* maintained state instead of drifting into
per-machine, ad-hoc configurations.

This repo is a **Claude Code plugin marketplace** containing a single bundled plugin,
**`agent-toolkit`**. Enable it once on a machine and the whole toolkit syncs.

## What's inside

```
.
├── .claude-plugin/
│   └── marketplace.json          # marketplace manifest → lists the agent-toolkit plugin
└── plugins/
    └── agent-toolkit/
        ├── .claude-plugin/
        │   └── plugin.json        # plugin manifest (registers the skills)
        ├── skills/                # vetted skills (SKILL.md bundles) — 20 total, see table below
        ├── agents/                # vetted subagents (auto-discovered)
        │   ├── coder.md
        │   ├── perf-tuner.md
        │   └── security-auditor.md
        └── .mcp.json              # MCP server declarations (github)
```

### Skills

**Seed set:**

| Skill | Purpose |
|---|---|
| `second-brain` | Use my Obsidian vault as a domain knowledge base (recall + Inbox-first capture). |
| `yuno-cleaner` | Read-only system-cleanup scan (dry-run by default). |
| `mmx-cli` | MiniMax media generation via the `mmx` CLI. |
| `drucker-experte` | 3D printing on the Bambu Lab A1 mini. |

**Yuno/Hermes AI stack:**

| Skill | Purpose |
|---|---|
| `yuno-team-orchestrator` | Orchestrate Yuno's 7-agent team for multi-domain tasks. |
| `yuno-team-routing` | Decide which Yuno team agent should handle a task / how to decompose it. |
| `yuno-user-preferences` | Apply Basti's working-style preferences and decision defaults. |
| `model-selector` | Pick the right model/lane for a job; model-handoff guide. |
| `multi-agent-master-workflow` | Master workflow patterns for coordinating multiple agents. |
| `queen-bee-schwarm-dispatch` | Orchestrate parallel subagent swarms, orthogonal scouts, concurrent audits. |
| `notebooklm-bridge` | Bridge content into NotebookLM workflows. |
| `hermes-mcp-integration` | Hermes V7 native MCP client setup (stdio/HTTP servers, tool discovery). |
| `hermes-desktop-plugins` | Write Hermes desktop plugins, UI panes, custom commands. |
| `messaging-gateway-setup` | Set up messaging gateways (Telegram/Discord/Slack bot integration). |

**Computer-use / GreyHack:**

| Skill | Purpose |
|---|---|
| `greyhack-computer-use-suite` | Drive GreyHack gameplay via the Computer-Use automation suite. |
| `computer-use-game-reconnaissance` | Computer-use reconnaissance patterns for games. |
| `desktop-window-reconnaissance` | Explore a desktop app or game window for reconnaissance. |

**Productivity:**

| Skill | Purpose |
|---|---|
| `daily-briefing` | Session-start status + open items + recent activity summary. |
| `knowledge-digest` | Convert textbooks/PDFs into personalized multimodal learning materials. |
| `tidy-folder` | Safe, read-only-first folder cleanup and organization. |

### Agents
| Agent | Purpose |
|---|---|
| `coder` | Real implementation work across the polyglot dev projects. |
| `perf-tuner` | Read-only performance diagnosis (CPU/GPU/thermal/disk/memory). |
| `security-auditor` | Read-only security-posture audit against the documented baseline. |

### MCP servers
| Server | Notes |
|---|---|
| `github` | `toqsick/github-mcp-server:develop` via Docker. Requires the `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable — the token is **never** stored in this repo, only referenced as `${GITHUB_PERSONAL_ACCESS_TOKEN}`. |

## Install (on any machine)

```bash
# Add this marketplace, then enable the bundled plugin
claude plugin marketplace add Toqsick/my-agent-tools
claude plugin install agent-toolkit@my-agent-tools
```

Verify in an interactive session with `/plugin` (shows `agent-toolkit` and its skills/agents/MCP
servers) and `/agents` (shows `coder`, `perf-tuner`, `security-auditor`).

> The `github` MCP server needs `GITHUB_PERSONAL_ACCESS_TOKEN` exported in the environment where
> Claude Code runs. Set it via your shell profile or a secret manager — do **not** commit it.

## Maintenance — adding a vetted tool

1. **Skill:** copy the skill folder into `plugins/agent-toolkit/skills/<name>/` (a `SKILL.md` plus any
   `references/`, `templates/`, `scripts/`), then add `"./skills/<name>"` to the `skills` array in
   `plugins/agent-toolkit/.claude-plugin/plugin.json`.
2. **Agent:** drop the `<name>.md` (with `name`/`description`/`model` frontmatter) into
   `plugins/agent-toolkit/agents/` — it's auto-discovered, no manifest edit needed.
3. **MCP server:** add an entry to `plugins/agent-toolkit/.mcp.json`. Keep every credential as an
   `${ENV_VAR}` reference, never a literal.
4. Bump `version` in `plugin.json`, commit, push. Re-sync on other machines with
   `claude plugin marketplace update my-agent-tools`.

**Rule:** only vetted, quality tools land here — this is the canonical set, not a dumping ground.
Copies must be self-contained (no symlinks pointing outside the repo).
