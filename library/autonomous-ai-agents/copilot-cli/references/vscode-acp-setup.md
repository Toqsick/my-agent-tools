# VS Code ACP Integration — Setup Guide

## Prerequisites
- VS Code 1.124.0+ installed
- Copilot CLI installed and authenticated

## Installation Steps

### 1. Install ACP Client Extension
```bash
code --install-extension formulahendry.acp-client
```
Version installed: v0.2.0 (2026-06-13)

### 2. Configure settings.json
Create/edit `~/.config/Code/User/settings.json`:
```json
{
  "acp.agents": {
    "GitHub Copilot": {
      "command": "copilot",
      "args": ["--acp", "--stdio"]
    }
  }
}
```

### 3. Connect
- Open VS Code Activity Bar → ACP Client Panel
- Select "GitHub Copilot" from the agent list
- Click Connect

## Troubleshooting

### "No authentication information found"
Run `copilot` interactively and use `/login` for GitHub OAuth.

### Extension not showing in panel
- Reload VS Code window (`Ctrl+Shift+P` → "Reload Window")
- Check extension is enabled: `code --list-extensions | grep acp`

### Connection fails
- Verify Copilot CLI works: `copilot -p "hello" --allow-all`
- Check VS Code output panel for ACP Client logs
