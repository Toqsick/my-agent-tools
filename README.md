# my-agent-tools

[![MCP Health Check](https://github.com/Toqsick/my-agent-tools/actions/workflows/mcp-health-check.yml/badge.svg)](https://github.com/Toqsick/my-agent-tools/actions/workflows/mcp-health-check.yml)
[![MCP Servers](https://img.shields.io/badge/MCP%20Servers-9-blue?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik0xMiAyQzYuNDggMiAyIDYuNDggMiAxMnM0LjQ4IDEwIDEwIDEwIDEwLTQuNDggMTAtMTBTMTcuNTIgMiAxMiAyem0tMSAxNXYtNEg3bDUtOXY0aDRsLTUgOXoiLz48L3N2Zz4=)](plugins/agent-toolkit/.mcp.json)
[![Skills](https://img.shields.io/badge/Skills-129%20installed%20%2B1244%20library-green)](INDEX.json)
[![License](https://img.shields.io/badge/License-Private-lightgrey)](#)

**Basti's private, version-controlled Claude Code toolkit.**

One curated source of truth for the skills, subagents, and MCP servers I've actually vetted — so
every Claude Code instance and every agent runs the *same* maintained state instead of drifting into
per-machine, ad-hoc configurations.

This repo is a **Claude Code plugin marketplace** containing a single bundled plugin,
**`agent-toolkit`**. Enable it once on a machine and the whole toolkit syncs.

## Two tiers + routing (start here)

The toolkit is organized so **any agent can find the right skill by reading one file** over a GitHub
MCP server — even without the plugin installed. Point a GitHub MCP at `Toqsick/my-agent-tools` and:

- **[`INDEX.json`](INDEX.json)** — the machine-readable master catalog of everything (skills, agents,
  workflows) with normalized `triggers`/`tags`/`category`/`path`. Fetch it, match a task, fetch the
  chosen skill by `path`. Generated — never hand-edited.
- **[`ROUTING.md`](ROUTING.md)** — the deterministic match algorithm (word-boundary triggers, scoring,
  gate priority, multi-domain decomposition) an agent follows to self-route.
- **[`NAVIGATION.md`](NAVIGATION.md)** — human/LLM category tables with counts.
- **[`workflows/`](workflows/)** — named multi-skill patterns (phases · owner-agent · exit criteria).

Skills live in **two tiers**:

| Tier | Location | Session-loaded? | How to use |
|---|---|---|---|
| **Installed** | `plugins/agent-toolkit/skills/` | Yes | invoke as `agent-toolkit:<name>` |
| **Library** | `library/<category>/…` | No — browsable reference | fetch by `path` via the MCP when the index points there |

The split is deliberate: ~1,400 skills would bloat every session's skill-matcher if all were loaded.
Installed = curated fast-path; library = the comprehensive Hermes arsenal, pulled on demand.

## What's inside

```
.
├── INDEX.json                    # machine-readable master catalog (generated)
├── NAVIGATION.md                 # human/LLM category nav (generated)
├── ROUTING.md                    # how an agent self-routes to a skill
├── .env.example                  # all MCP env-var templates + setup guide
├── .claude-plugin/
│   └── marketplace.json          # marketplace manifest → lists the agent-toolkit plugin
├── plugins/
│   └── agent-toolkit/
│       ├── .claude-plugin/
│       │   └── plugin.json        # plugin manifest (registers the installed skills)
│       ├── skills/                # 129 installed skills (SKILL.md bundles) — session-loaded
│       ├── agents/                # 17 subagents (coder, perf-tuner, security-auditor + 14 zc-*)
│       ├── commands/              # /toolkit — browse packs + health check (auto-discovered)
│       ├── hooks/                 # SessionStart banner: skills · packs · agents · MCP counts
│       ├── packs/                 # 8 themed skill packs (manifest.json + per-pack READMEs)
│       └── .mcp.json              # MCP server declarations (9 servers)
├── library/                      # 1,244 browsable Hermes-arsenal skills (NOT session-loaded)
│   └── <category>/<skill>/SKILL.md
├── routing/                       # zcode-skills MCP-aware routing metadata
│   ├── registry/                   # generated repository-relative catalogs
│   ├── config/                     # sanitized MCP template + schema
│   ├── bundles/                    # imported skill bundle manifests
│   └── manifests/                  # imported provenance lockfiles
├── workflows/                    # machine-readable multi-skill workflow patterns
└── scripts/
    ├── build_index.py             # regenerates catalogs + routing metadata (calls build_packs)
    ├── build_packs.py             # validates packs/manifest.json + emits routing/bundles/*.yaml
    └── check-mcp.sh               # local MCP server health check
```

## Skill packs (installed-skill grouping)

The 129 installed skills are grouped into **8 themed packs** — a navigation layer over the one
plugin, so the wall of skills becomes scannable by domain. Every skill still loads in every
session and is invokable as `agent-toolkit:<name>`; packs just make browsing and routing
easier. See [`PACKS.md`](PACKS.md) for the full pack index, the per-pack skill rosters, and the
future "install only what you need" split roadmap.

| Pack | Skills | Theme |
|---|---:|---|
| `core` | 10 | Daily-driver layer — Obsidian second-brain, Yuno cleaner, 3D printing, Yuno team orchestration, model selection, daily briefing, skill↔MCP router |
| `hermes-dev` | 18 | Hermes/Yuno platform — CLI internals, gateway protocol/clients, mobile, Ariadne memory, adapters, themes |
| `cybersecurity` | 50 | Defensive security & DFIR — CIS hardening, Docker/K8s, network hunting, forensics, compliance/supply-chain |
| `methodology` | 18 | Superpowers + ZCode team orchestration — brainstorm→plan→TDD→debug→verify→finish, swarm dispatch |
| `media` | 6 | MiniMax + generation — `mmx` CLI, agent builder, crypto trading, DOCX/PDF, Nano Banana Pro |
| `docs-web-research` | 15 | Docs, web & research — PPT/decks, research papers, frontend design, scraping, Excel, n8n, SEO/GEO, business research |
| `computer-use` | 3 | Computer-use & GreyHack — GUI automation + game/desktop-window reconnaissance |
| `dev-essentials` | 9 | Engineering originals — debugging patterns, defensive programming, recon, extraction, ClickHouse |

Browse live in any session with the `/toolkit` slash command: `/toolkit` (overview),
`/toolkit <pack>` (a pack's skills), or `/toolkit doctor` (health check). A `SessionStart` hook
prints a compact `skills · packs · agents · MCP servers` banner at session open.

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
| `daily-briefing` | Session-start status + open items + recent activity summary. Uses Gmail + Calendar MCP when configured. |
| `knowledge-digest` | Convert textbooks/PDFs into personalized multimodal learning materials. |
| `tidy-folder` | Safe, read-only-first folder cleanup and organization. |

**Imported from [`kyssta-exe/skills`](https://github.com/kyssta-exe/skills) (curated, 86):**

A curated subset of the public "Hermes Skills Vault" (886 skills). Cybersecurity skills are listed
by theme rather than individually (50 total) to stay scannable — each is a full `SKILL.md` with
MITRE ATT&CK / NIST CSF mappings where applicable.

*Cybersecurity — defensive/forensics (50):*

| Theme | Count | Examples |
|---|---|---|
| Linux host hardening & forensics | 9 | CIS benchmark hardening, audit-log intrusion analysis, rootkit detection, persistence-mechanism analysis |
| Docker / container security | 10 | Docker Bench assessment, container escape detection, Trivy image scanning, Falco runtime threats, distroless hardening |
| Kubernetes | 1 | Pod Security Standards |
| Network detection & hunting | 12 | Scapy/Wireshark packet & traffic analysis, Suricata/Zeek monitoring, Sigma detection rules, YARA malware triage, APT hunting |
| Forensics & incident response | 9 | Volatility memory forensics, disk/endpoint forensics, IR playbooks, file carving (Foremost/PhotoRec) |
| Compliance & supply-chain | 10 | NIST CSF maturity, CIS cloud audits, gitleaks/TruffleHog secret scanning, SBOM analysis, SLSA/Sigstore provenance |

*Hermes/Yuno dev (14):*

| Skill | Purpose |
|---|---|
| `hermes-cli-internals` | Hermes CLI internals: profiles, home overrides, secret scoping. |
| `hermes-client-development` | Building Hermes clients. |
| `hermes-gateway-integration` | Integrating with the Hermes gateway. |
| `hermes-gateway-client-development` | Gateway client development (WebSocket auth, sessions). |
| `hermes-contribution-workflows` | Contributing to Hermes upstream. |
| `hermes-mobile-development` | Hermes mobile app development. |
| `hermes-mobile-client-development` | Hermes mobile client patterns (auth-gate patches, WS auth). |
| `hermes-ariadne-memory` | Hermes's Ariadne memory subsystem, dev-side. |
| `hermes-gateway-protocol` | Hermes JSON-RPC gateway protocol spec. |
| `modelhub-dashboard` | Hermes ModelHub dashboard operations. |
| `hermes-agent-environment-passthrough` | Environment passthrough for Hermes terminal backends. |
| `hermes-free-tier-setup` | Setting up Hermes on free-tier infrastructure. |
| `gateway-adapter-development` | Developing Hermes gateway adapters. |
| `ariadne-memory` | Ariadne memory system (MLOps angle). |

*Dev/web originals (8):*

| Skill | Purpose |
|---|---|
| `stealth-web-scraping` | Bot-detection bypass: CloakBrowser, undetected-chromedriver, self-hosted Firecrawl. |
| `open-source-extraction` | Extract packages from monorepos for standalone use. |
| `reference-architecture-research` | Researching reference architectures before building. |
| `debugging-patterns` | Concrete debugging tactics: error classification, API verification, multi-location fixes. |
| `defensive-programming` | Defensive-programming patterns. |
| `config-propagation-bugs` | Diagnosing config-propagation bugs. |
| `web-content-reconnaissance` | Web content reconnaissance patterns. |
| `competitive-software-landscape` | Multi-registry competitive-landscape research. |

*Superpowers methodology (14, namespaced `superpowers-*`):*

| Skill | Purpose |
|---|---|
| `superpowers-brainstorming` | Structured brainstorming before writing a plan. |
| `superpowers-dispatching-parallel-agents` | Dispatching independent work to parallel subagents. |
| `superpowers-executing-plans` | Executing a written implementation plan. |
| `superpowers-finishing-a-development-branch` | Closing out a feature branch cleanly. |
| `superpowers-receiving-code-review` | Processing incoming code-review feedback. |
| `superpowers-requesting-code-review` | Requesting a code review well. |
| `superpowers-subagent-driven-development` | Core `delegate_task`-per-task autonomous workflow. |
| `superpowers-systematic-debugging` | Root-cause-first debugging, no random patches. |
| `superpowers-test-driven-development` | Classic red/green/refactor TDD. |
| `superpowers-using-git-worktrees` | Isolated workspaces for parallel feature work. |
| `superpowers-using-superpowers` | Meta: how to use the Superpowers skill set itself. |
| `superpowers-verification-before-completion` | Verifying before declaring a task done. |
| `superpowers-writing-plans` | Bite-sized implementation plans with spec verification. |
| `superpowers-writing-skills` | Authoring new skills. |

**Attribution:** the 86 skills above are adapted from the public
[`kyssta-exe/skills`](https://github.com/kyssta-exe/skills) vault, itself built from
[`obra/superpowers`](https://github.com/obra/superpowers) (MIT) and
[`mukul975/Anthropic-Cybersecurity-Skills`](https://github.com/mukul975/Anthropic-Cybersecurity-Skills)
(Apache-2.0). Not originally authored by Basti — imported and curated for relevance to this toolkit.

**ZCode team (1 skill + 14 agents):**

| Skill | Purpose |
|---|---|
| `zcode-subagent-team` | Hermes-Kanban multi-lane agent swarm (Queen → General/Vision/Coder/Debug/Verify/Gate). Pairs with the `zc-*` agents. |
| `skill-mcp-router` | Resolve intent → skill → configured MCP server → filtered tools with lazy discovery. |

**MiniMax (5):**

| Skill | Purpose |
|---|---|
| `superpower-10x` | Systematic 10x agentic-dev pipeline (brainstorm→plan→TDD→debug→verify→finish) + automation scripts. |
| `minimax-ai-agent-builder` | Guide to building AI agents on MiniMax. |
| `minimax-crypto-trading` | BTC/ETH/SOL trading-decision agent. |
| `minimax-docx` | DOCX generation via OpenXML. |
| `minimax-pdf` | Design-token PDF create/fill/reformat. |

**Curated from the Downloads vault (15):** `pptx-generator`, `n8n`, `clickhouse-best-practices`,
`nano-banana-pro`, `prompt-engineer`, `deep-research-agent`, `frontend-design`,
`mckinsey-presentation-generator`, `research-paper-generator`, `seo-geo-optimization-expert`,
`web-scraper`, `excel-xlsx`, `job-hunter`, `sales-power-map`, `saas-niche-finder`. Plus `hermes-themes`
(Hermes color-theme authoring). All fully self-contained, no secrets/hardcoded paths.

### Library (browsable, not session-loaded)

`library/` holds the full **Hermes skill arsenal — 1,244 skills** across 40+ categories (top: 815
cybersecurity, 81 software-development, 44 orchestration, 44 devops, 43 creative, 29 productivity, …),
a point-in-time snapshot of `~/.hermes/skills/` (`.archive/` excluded). These are **not** registered in
`plugin.json` and never load into a session — agents discover them via [`INDEX.json`](INDEX.json) and
fetch a skill's `SKILL.md` by `path` through the GitHub MCP. Provenance is heterogeneous (each carries
its own frontmatter `license`/`author`); the set includes both defensive and offensive security
material — treat it as a browsable reference arsenal, not a vetted install set.

### Workflows

[`workflows/`](workflows/) defines named, machine-readable multi-skill patterns (frontmatter `phases`
with owner-agent + skills + exit criteria per phase): `superpower-10x-pipeline`, `zcode-6lane-pipeline`,
`security-audit`, `repo-cleanup`, `research-to-report`, `multi-agent-master`. An agent consults
`INDEX.json → workflows[]` for multi-step work and fetches the pattern by `path`.

### Agents
| Agent | Purpose |
|---|---|
| `coder` | Real implementation work across the polyglot dev projects. |
| `perf-tuner` | Read-only performance diagnosis (CPU/GPU/thermal/disk/memory). |
| `security-auditor` | Read-only security-posture audit against the documented baseline. |

### MCP servers

All 9 servers are declared in [`plugins/agent-toolkit/.mcp.json`](plugins/agent-toolkit/.mcp.json).
Credentials are **always** referenced as `${ENV_VAR}` — never stored here. Copy [`.env.example`](.env.example) to `.env` and fill in your values.

| Server | Transport | Purpose | Required env vars |
|---|---|---|---|
| `github` | Docker (`toqsick/github-mcp-server:develop`) | Issues, PRs, commits, file ops, code search | `GITHUB_PERSONAL_ACCESS_TOKEN` |
| `gmail` | npx (`@gongrzhe/server-gmail-autoauth-mcp`) | Read, send, search e-mail | `GMAIL_OAUTH_CLIENT_ID` · `GMAIL_OAUTH_CLIENT_SECRET` · `GMAIL_OAUTH_REFRESH_TOKEN` |
| `google-calendar` | npx (`@cocal/google-calendar-mcp`) | Read & create calendar events | `GOOGLE_CLIENT_ID` · `GOOGLE_CLIENT_SECRET` · `GOOGLE_REFRESH_TOKEN` |
| `filesystem` | npx (`@modelcontextprotocol/server-filesystem`) | Read/write local workspace files | `WORKSPACE_PATH` (default `/workspace`) |
| `brave-search` | npx (`@modelcontextprotocol/server-brave-search`) | Live web search for agents | `BRAVE_API_KEY` |
| `memory` | npx (`@modelcontextprotocol/server-memory`) | Persistent knowledge graph across sessions | `MEMORY_FILE_PATH` (default `~/.agent-memory/memory.json`) |
| `puppeteer` | npx (`@modelcontextprotocol/server-puppeteer`) | Headless browser / web automation | — |
| `sequential-thinking` | npx (`@modelcontextprotocol/server-sequential-thinking`) | Structured multi-step reasoning | — |
| `basti-tools` | `uv run mcp-server-basti` (FastMCP/stdio, local) | Local read-only system diagnostics (`get_system_status`, `get_disk_status`, `get_gpu_status`, `get_memory_status`, `get_failed_units`, `get_kernel_warnings`, `get_boot_timing`, `get_power_profile`, `get_firewall_state`, `get_repo_info`, `echo_tool`) | — (sudoers rule for `get_firewall_state`, see `docs/mcp-server/SUDOERS_SETUP.md`) |

#### Gmail + Google Calendar — Quick OAuth2 Setup

> Both share the same Google Cloud project and OAuth2 credentials.

```bash
# 1. One-shot auth flow — opens browser, writes tokens automatically
npx @gongrzhe/server-gmail-autoauth-mcp auth

# 2. Copy the printed values into your .env
GMAIL_OAUTH_CLIENT_ID=...
GMAIL_OAUTH_CLIENT_SECRET=...
GMAIL_OAUTH_REFRESH_TOKEN=...
GOOGLE_CLIENT_ID=...        # same client_id
GOOGLE_CLIENT_SECRET=...    # same client_secret
GOOGLE_REFRESH_TOKEN=...    # same refresh_token
```

If you prefer manual setup:
1. [Google Cloud Console](https://console.cloud.google.com) → new project
2. Enable **Gmail API** + **Google Calendar API**
3. Create OAuth2 credentials → type **Desktop App** → download JSON
4. Run the auth command above or use `oauth2l` to fetch a refresh token

#### Brave Search — Quick Setup

```bash
# Free tier: 2,000 queries/month
# Sign up at https://api.search.brave.com → copy your API key into .env
BRAVE_API_KEY=BSA_...
```

#### Skills that benefit from the new MCP servers

| Skill | MCP servers used |
|---|---|
| `daily-briefing` | `gmail` + `google-calendar` + `memory` |
| `deep-research-agent` | `brave-search` + `puppeteer` + `memory` |
| `second-brain` | `filesystem` + `memory` |
| `hermes-mcp-integration` | all servers (routing + discovery) |
| `skill-mcp-router` | all servers (intent → tool resolution) |
| `yuno-team-orchestrator` | `github` + `gmail` + `google-calendar` |
| `web-scraper` / `stealth-web-scraping` | `puppeteer` + `brave-search` |
| `queen-bee-schwarm-dispatch` | `github` + `filesystem` + `sequential-thinking` |

## Install (on any machine)

```bash
# Add this marketplace, then enable the bundled plugin
claude plugin marketplace add Toqsick/my-agent-tools
claude plugin install agent-toolkit@my-agent-tools
```

Verify in an interactive session with `/plugin` (shows `agent-toolkit` and its skills/agents/MCP
servers) and `/agents` (shows `coder`, `perf-tuner`, `security-auditor`).

> **Credentials:** export all required env vars before starting Claude Code (see [`.env.example`](.env.example)).
> The `github` MCP server needs `GITHUB_PERSONAL_ACCESS_TOKEN` at minimum. Gmail and Calendar are
> optional but unlock `daily-briefing` and calendar-aware scheduling across the whole toolkit.

## Basti's MCP Server

Zusätzlich zum externen `github`-Server bringt dieses Repo einen **lokalen MCP-Server**
namens `mcp-server-basti` mit. Er läuft über **stdio**, ist in Python/FastMCP
implementiert und wird via [`uv`](https://docs.astral.sh/uv/) gestartet — kein Docker,
kein Netzwerk-Listener, keine externen Secrets in der Default-Konfiguration.

### Tools

Alle Tools advertise `readOnlyHint=True` (keine Mutationen). Strukturierte Rückgaben
sind TypedDicts (Schema-Ableitung via FastMCP); `echo_tool`/`get_kernel_warnings`
geben rohen Text zurück.

| Tool | Zweck |
|---|---|
| `get_system_status` | `uptime`-Output (lokal, ohne Netzwerk). |
| `echo_tool` | Smoke-Test — gibt Eingabe unverändert zurück. |
| `get_repo_info` | Git-Branch + letzter Commit des Server-Repos (strukturiert `{branch,last_commit,detached}`). |
| `get_disk_status` | `df -h` über alle Dateisysteme. |
| `get_gpu_status` | `nvidia-smi` Treiber/Temp/Auslastung/VRAM + Power-Limits. |
| `get_memory_status` | `free -h` + `zramctl` + `swapon --show`. |
| `get_failed_units` | Fehlgeschlagene systemd-Units (`systemctl --failed`). |
| `get_kernel_warnings` | `journalctl -b -p warning` (roher Text). |
| `get_boot_timing` | `systemd-analyze blame` + `critical-chain`. |
| `get_power_profile` | `powerprofilesctl get`. |
| `get_firewall_state` | `sudo -n ufw status verbose` + `ss -tlnp` — **benötigt eine NOPASSWD-sudoers-Regel** (siehe [`docs/mcp-server/SUDOERS_SETUP.md`](docs/mcp-server/SUDOERS_SETUP.md)); ohne sie degradiert der Aufruf sauber zu einem `ToolError`. |

### Installation

Der Server liegt im Repo-Root. Es gibt zwei Install-Wege:

```bash
# 1. Global via uvx (empfohlen — keine lokale venv nötig):
uvx git+https://github.com/Toqsick/my-agent-tools.git

# 2. Lokal aus dem Repo (für Entwicklung/Debugging):
cd /path/to/my-agent-tools
uv run mcp-server-basti
```

### `.mcp.json`-Konfiguration

Der Server ist bereits in `plugins/agent-toolkit/.mcp.json` als `basti-tools`
eingetragen. Der `github`-Eintrag bleibt unverändert daneben bestehen:

```json
{
  "mcpServers": {
    "github":      { "command": "docker", "args": [...], "env": {...} },
    "basti-tools": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "${CLAUDE_PROJECT_ROOT}",
        "mcp-server-basti"
      ]
    }
  }
}
```

Beim Plugin-Start wird der Server automatisch hochgefahren — keine weiteren
Schritte erforderlich. Für `get_firewall_state` muss additionally die
sudoers-Regel aus [`docs/mcp-server/SUDOERS_SETUP.md`](docs/mcp-server/SUDOERS_SETUP.md)
installiert sein; alle anderen 10 Tools laufen ohne Voraussetzung.

### Tests ausführen

```bash
uv sync --all-extras
uv run --extra dev pytest tests/unit tests/integration -v
```

### Architektur

- **Transport:** stdio (kein HTTP, kein Port). Der Parent-Prozess (Claude Code)
  startet den Server als Subprozess und spricht JSON-RPC über stdin/stdout.
- **Framework:** [FastMCP](https://github.com/jlowin/fastmcp) (standalone `>=3.0`,
  nicht der `mcp[cli]`-Shim) auf Basis von [`mcp`](https://pypi.org/project/mcp/) —
  deklarative Tool-Definition via Python-Decorators mit `tags`, `annotations`
  (`readOnlyHint=True`), `timeout` und per-TypedDict abgeleiteten `output_schema`s.
- **Sandboxing:** läuft mit den Rechten des aufrufenden Users. Schreibt nur in
  Bereiche, in denen der User schreiben darf.
- **CI:** `.github/workflows/ci.yml` führt auf jedem Push/PR nach `main` Lint
  (`ruff`), Tests (`pytest`) und Build (`uv build`) aus und lädt das Wheel
  als Artefakt hoch.
- **Health-Check:** `scripts/check-mcp.sh` prüft für **jeden** in `.mcp.json`
  konfigurierten Server, ob `command` im PATH ist und alle `env`-Vars gesetzt
  sind, und gibt ein JSON-Array mit `{server, status, detail}` zurück
  (Exit-Code 1 wenn ein Server down ist).

## Maintenance — adding a vetted tool

1. **Skill:** copy the skill folder into `plugins/agent-toolkit/skills/<name>/` (a `SKILL.md` plus any
   `references/`, `templates/`, `scripts/`), then add `"./skills/<name>"` to the `skills` array in
   `plugins/agent-toolkit/.claude-plugin/plugin.json`.
2. **Agent:** drop the `<name>.md` (with `name`/`description`/`model` frontmatter) into
   `plugins/agent-toolkit/agents/` — it's auto-discovered, no manifest edit needed.
3. **MCP server:** add an entry to `plugins/agent-toolkit/.mcp.json`. Keep every credential as an
   `${ENV_VAR}` reference, never a literal. Document the new server in the table above and add its
   env vars to [`.env.example`](.env.example).
4. **Library:** to add browsable (non-installed) reference skills, drop `SKILL.md` bundles under
   `library/<category>/<name>/` — no `plugin.json` edit (they are discovered via the index, not loaded).
5. **Regenerate the catalogs (required):** run `python3 scripts/build_index.py` to rebuild
   [`INDEX.json`](INDEX.json), [`NAVIGATION.md`](NAVIGATION.md), and `routing/registry/*`. Never hand-edit
   generated files.
6. Bump `version` in `plugin.json`, commit, push. Re-sync on other machines with
   `claude plugin marketplace update my-agent-tools`.

**Rule:** only vetted, quality tools land here — this is the canonical set, not a dumping ground.
Copies must be self-contained (no symlinks pointing outside the repo).
