# Pre-Spawn Checklist Protocol

Run through these mentally before calling `delegate_task`:

## 5 Critical Questions

1. **Output path:** Did I specify an explicit `OUTPUT: ~/docs/system/NAME-YYYY-MM-DD.md` for every subagent? (Never let them write to `~/.hermes/skills/` — that tree is for SKILL.md only.)

2. **Call budget:** Did I write `MAX 8 web-calls. After 8 -> synthesis with what you have` for each subagent? (Subagents WILL loop pagination otherwise.)

3. **Source-code paths:** For Hermes/framework questions, did I include exact source paths (e.g. `~/.hermes/hermes-agent/tools/delegate_tool.py:2487`)? (Source-code beats web research every time.)

4. **Read-only or write?** If the briefing has write commands (chmod, rm, patch, systemctl), **parent will execute centrally** — subagent only reports. (See Pitfall #31 — write-commands trigger 90+90s Ollama approval timeouts.)

5. **Verification plan:** Do I know HOW to verify the claims afterwards? (e.g. `grep -n <key> cli-config.yaml.example`, `python3 scripts/verify_subagent_claims.py config_key <path> <expected>`, `ls -la <file>`)

## Decision Rule

**If any answer is "no" → fix the briefing BEFORE spawning.**

This 5-question check prevents the most common subagent failures before they happen.