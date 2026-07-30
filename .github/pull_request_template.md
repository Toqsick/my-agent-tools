## Summary

<!-- What does this PR do? One sentence. -->

## Type of change

- [ ] `feat` — new skill / MCP server / workflow
- [ ] `fix` — bug fix
- [ ] `docs` — documentation only
- [ ] `chore` — maintenance (deps, config, scripts)
- [ ] `refactor` — code change without new features

## Checklist

- [ ] No secrets or tokens committed (`.env` is in `.gitignore`)
- [ ] If adding a skill: `SKILL.md` has `name`, `description`, `triggers` frontmatter
- [ ] If adding a skill: `python3 scripts/build_index.py` has been run locally
- [ ] If adding an MCP server: entry added to `.mcp.json` with `${ENV_VAR}` references only
- [ ] If adding an MCP server: env var added to `.env.example`
- [ ] CI passes (secret-scanning, skill-lint, mcp-health-check)

## Related

<!-- Link issues, skills, or MCP servers this relates to -->
