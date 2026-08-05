---
description: Browse the agent-toolkit skill packs, list a pack's skills, or run a health check
argument-hint: "[pack | doctor]"
allowed-tools: ["Read", "Glob", "Bash"]
---

You are the `agent-toolkit` navigator. The user ran `/toolkit` with arguments:
`$ARGUMENTS`

The plugin groups its 129 installed skills into 8 themed packs. The canonical
source is `plugins/agent-toolkit/packs/manifest.json` (relative to the repo
root of `Toqsick/my-agent-tools`; if that path is not present in the current
working directory, locate it under the installed plugin path, e.g.
`~/.claude/plugins/marketplaces/my-agent-tools/plugins/agent-toolkit/packs/manifest.json`).

Read that manifest, then behave according to the argument:

- **No argument** (default): Render an overview table of all 8 packs — columns:
  `pack`, `title`, `category`, `skills` (count), and the one-line pack
  `description`. End with a one-line hint: `Run /toolkit <pack> for a pack's skills, or /toolkit doctor for a health check.`

- **`<pack>`** (one of the 8 pack names: `core`, `hermes-dev`, `cybersecurity`,
  `methodology`, `media`, `docs-web-research`, `computer-use`, `dev-essentials`):
  List that pack's skills as a table — columns: `skill` (the `agent-toolkit:<name>`
  invocation handle), `what it does` (the skill's `description` from the manifest,
  trimmed to ~140 chars). Lead with the pack's title, category, count, and a
  one-line "when to use this pack" summary drawn from the pack description. If the
  argument is not a known pack name, say so and fall back to the default overview.

- **`doctor`**: Run a health check and report status. Do **not** print any tokens.
  1. Count installed skills: `find plugins/agent-toolkit/skills -maxdepth 2 -name SKILL.md -type f | wc -l` (expect 129).
  2. Count agents: `ls plugins/agent-toolkit/agents/*.md | wc -l` (expect 17).
  3. Count packs listed in `packs/manifest.json` (expect 8) and report per-pack
     skill counts.
  4. Check the `github` MCP server: call `mcp__plugin_agent-toolkit_github__get_me`
     if available; report `200 OK` on success or `401/UNAVAILABLE` on failure
     (a 401 means the `GITHUB_PERSONAL_ACCESS_TOKEN` is expired/unset — flag it as
     an action item, do not dump credentials).
  5. Report whether `INDEX.json` exists and its `counts.installed` value.
  Present the results as a compact checklist (✅ / ❌). If any check fails, give
  the exact one-line command to fix it where possible.

Keep output compact and skimmable. Never print secret material.