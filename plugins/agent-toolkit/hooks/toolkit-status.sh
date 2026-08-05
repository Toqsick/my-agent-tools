#!/usr/bin/env bash
# toolkit-status.sh — SessionStart banner for the agent-toolkit plugin.
# Prints a compact one-line status of the installed toolkit. Sensor only.
# Never prints tokens or credentials. Exits 0; failures are non-fatal.
set -u

root="${CLAUDE_PLUGIN_ROOT:-}"
[ -z "$root" ] && exit 0

skills_dir="$root/skills"
agents_dir="$root/agents"
manifest="$root/packs/manifest.json"

# Count skills (dirs with a SKILL.md) and agents (*.md).
skill_count=$(find "$skills_dir" -maxdepth 2 -name SKILL.md -type f 2>/dev/null | wc -l)
agent_count=$(find "$agents_dir" -maxdepth 1 -name '*.md' -type f 2>/dev/null | wc -l)

# Count packs from the manifest (fast, single python call).
pack_count=$(python3 - "$manifest" <<'PY' 2>/dev/null
import json, sys
try:
    m = json.load(open(sys.argv[1]))
    print(len(m.get("packs", [])))
except Exception:
    print(0)
PY
)

# MCP server count from .mcp.json (top-level mcpServers keys).
mcp_count=$(python3 - "$root/.mcp.json" <<'PY' 2>/dev/null
import json, sys
try:
    m = json.load(open(sys.argv[1]))
    print(len((m.get("mcpServers") or {})))
except Exception:
    print(0)
PY
)

printf 'agent-toolkit: %s skills · %s packs · %s agents · %s MCP servers — run /toolkit to browse, /toolkit doctor to health-check.\n' \
    "$skill_count" "$pack_count" "$agent_count" "$mcp_count"
exit 0