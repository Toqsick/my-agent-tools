# GitHub Copilot CLI — Full Reference

Extracted from the `copilot-cli` skill. Complete guide for GitHub Copilot CLI.

## Prerequisites
- **Install:** Pre-installed on this system (`copilot --version` → v1.0.61+)
- **Auth:** `COPILOT_GITHUB_TOKEN` in `~/.hermes/.env` or interactive `/login`
- **Verify:** `copilot -p "hello" --allow-all`

## Three Modes

### Print Mode (`-p`) — Preferred
```bash
copilot -p "Add error handling to API calls" --allow-all
```
Non-interactive, skips all permission dialogs.

### ACP Mode (`--acp --stdio`)
```python
delegate_task(
    goal="Refactor auth module",
    acp_command="copilot",
    acp_args=["--acp", "--stdio"]
)
```

### VS Code ACP Integration
1. Install: `code --install-extension formulahendry.acp-client`
2. Configure `~/.config/Code/User/settings.json`:
   ```json
   {"acp.agents": {"GitHub Copilot": {"command": "copilot", "args": ["--acp", "--stdio"]}}}
   ```

## Auth Setup
- **Interactive:** `copilot` → `/login` (browser OAuth)
- **Token:** Add `COPILOT_GITHUB_TOKEN=***` to `~/.hermes/.env`
- **Verify:** `copilot -p "hello" --allow-all`

## Configuration
- **Model:** `copilot --model <model>` or `~/.copilot/config.json`
- **Config dir:** `~/.copilot/`
- **Logs:** `~/.copilot/logs/`

## Tips
- Prefer `-p` for quick tasks
- Use `--allow-all` in non-interactive mode
- Set `workdir` to project directory
- For Hermes integration, ACP mode via `delegate_task` is cleanest
- **copilot-instructions.md** — use `templates/copilot-instructions.md` for project-specific guidance
