# MCP Server Setup (Docker-based)

MCP-Server können lokal als Docker-Container laufen und stellen Tools als native Hermes-Tools bereit.

## Konfiguration

```yaml
mcp_servers:
  server_name:
    command: "docker"
    args: ["run", "-i", "--rm", "-e", "API_TOKEN", "ghcr.io/org/server-image"]
    env:
      API_TOKEN: "gho_..."
    timeout: 120
    connect_timeout: 60
```

## CLI Commands

```bash
hermes mcp list              # Server anzeigen
hermes mcp test <name>       # Verbindung testen (NICHT Auth)
hermes mcp add <name>        # Hinzufügen
hermes mcp remove <name>     # Entfernen
```

## Wichtige Hinweise

| Problem | Fix |
|---------|-----|
| **Config.yaml Schreibschutz** | `patch()`/`write_file()` blockiert. Use `hermes config set`, `sed -i`, or `hermes config edit`. |
| **Token in .env reicht nicht** | Token MUSS in `mcp_servers.<name>.env` stehen. |
| **Nach Config-Änderung** | Container killen + `/reset` |
| **`hermes mcp test`** | Testet CONNECTION, NICHT AUTH. |
| **Tool-Präfix** | `mcp_{server}_{tool}` |

## Fork Build + Deploy

```bash
cd ~/dein-fork && docker build -t dein-image:tag .
sed -i 's|ghcr.io/org/old-image|dein-image:tag|' ~/.hermes/config.yaml
docker ps --filter "ancestor=dein-image:tag" -q | xargs -r docker kill
hermes mcp test dein-server
```
