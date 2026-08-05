# Pack: Hermes / Yuno Platform

**Category:** development · **Skills:** 18

Build Hermes/Yuno platform features — CLI internals, gateway protocol/clients, mobile clients, Ariadne memory, gateway adapters, desktop plugins, messaging gateways, themes, and the ModelHub dashboard.

Skills for building on the Hermes/Yuno platform itself — CLI internals, the tui_gateway JSON-RPC protocol, mobile/desktop/CLI clients, Ariadne memory, gateway adapters, desktop plugins, messaging gateways, themes, and the ModelHub dashboard. Use these when contributing to or extending Hermes.

## When to use this pack

See the trigger words in each skill's description. This pack is the right starting point when the task falls in this domain; the `/toolkit <pack>` command lists these skills interactively.

## Skills

| Skill | What it does |
|---|---|
| `hermes-cli-internals` | Hermes CLI architecture patterns — pre-argparse flag handling, environment propagation, profile overrides, and subprocess inheritance. |
| `hermes-client-development` | Build custom clients (mobile, desktop, web, CLI, IDE plugins) that connect to a remote Hermes Agent via its JSON-RPC WebSocket protocol. Covers the hermes se… |
| `hermes-gateway-integration` | Build clients that connect to Hermes Agent via the tui_gateway JSON-RPC WebSocket protocol — mobile apps, web clients, custom UIs, and automations that drive… |
| `hermes-gateway-client-development` | Build mobile, desktop, or CLI clients that connect to a remote Hermes Agent (hermes serve) via WebSocket JSON-RPC. |
| `hermes-contribution-workflows` | Git/PR/terminal tool patterns for contributing to the Hermes Agent codebase. Covers fork-PR gotchas, terminal atomicity, and patch-tool pitfalls. |
| `hermes-mobile-development` | Build native mobile clients (iOS/Android) that connect remotely to a Hermes Agent backend via WebSocket JSON-RPC. |
| `hermes-mobile-client-development` | Building native mobile clients (React Native / Expo) that connect to a remote Hermes Agent gateway via WebSocket JSON-RPC. |
| `hermes-ariadne-memory` | Install, configure, and use Ariadne memory provider for Hermes Agent — local-first hybrid search (FAISS + FTS5 + RRF), knowledge graph, cognitive retention, … |
| `hermes-gateway-protocol` | Build custom clients against the Hermes tui_gateway JSON-RPC protocol — remote connection, WebSocket transport, auth, and the @hermes/shared client library. |
| `modelhub-dashboard` | ModelHub AI Model Benchmark Dashboard - operations, data refresh, and management |
| `hermes-agent-environment-passthrough` | Ensuring environment variables are correctly passed to Hermes agent terminal backends, especially Daytona. |
| `hermes-free-tier-setup` | Class-level skill for configuring Hermes Agent with 100% free LLM providers, intelligent fallback chains, and optimized auxiliary models |
| `gateway-adapter-development` | Develop, debug, and maintain Hermes gateway platform adapters (Telegram, Discord, Slack, Raft, etc.) |
| `ariadne-memory` | Set up and use Ariadne as the local-first hybrid search memory provider for Hermes Agent. |
| `hermes-mcp-integration` | Use when integrating Hermes V7 native MCP client (stdio/HTTP servers, tool discovery, config.yaml setup). |
| `hermes-desktop-plugins` | Use when user asks for writing Hermes desktop plugins, UI panes, custom commands inside Hermes desktop app. NOT for Hermes CLI plugins or non-Hermes desktop … |
| `messaging-gateway-setup` | Use when user asks for setting up Telegram, WhatsApp, Discord, Signal, or Matrix, configuring the Hermes messaging gateway, checking or restarting gateway st… |
| `hermes-themes` | Author a Hermes color theme that skins every surface. |
