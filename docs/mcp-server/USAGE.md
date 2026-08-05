# MCP-Server Basti – Nutzung

`mcp-server-basti` ist ein privater MCP-Server für drei Aufgaben: Systemstatus abfragen, Text echoen und Repository-Informationen lesen. Der Server nutzt **stdio**; der MCP-Client startet ihn als lokalen Unterprozess und kommuniziert über stdin/stdout.

## Voraussetzungen

- [uv](https://docs.astral.sh/uv/) im `PATH`
- Python **3.11 oder neuer**
- Ein MCP-Client wie Claude Desktop, Cursor oder Hermes
- Für lokale Entwicklung: ein Checkout dieses Repositories

Versionen prüfen:

```bash
uv --version
python3 --version
```

## Lokal starten

Im Repository-Root:

```bash
uv run mcp-server-basti
```

`uv run` löst die Projektabhängigkeiten auf und startet den Entry-Point `mcp-server-basti` (definiert in `pyproject.toml` → `[project.scripts]`).

## Start via uvx (nach Push zu GitHub)

Sobald `pyproject.toml` und `src/` auf GitHub gepusht sind, kann der Server isoliert gestartet werden:

```bash
uvx --from git+https://github.com/Toqsick/my-agent-tools.git mcp-server-basti
```

> **Hinweis:** Dieser Weg funktioniert erst, nachdem der Code zu GitHub gepusht wurde. Vorher nutze `uv run mcp-server-basti` lokal.

## Claude Desktop und Cursor

MCP-Konfigurationen verwenden ein `mcpServers`-Objekt. Beispiel für `.mcp.json`:

```json
{
  "mcpServers": {
    "basti-tools": {
      "command": "uv",
      "args": ["run", "mcp-server-basti"],
      "cwd": "/pfad/zu/my-agent-tools"
    }
  }
}
```

Für `uvx` (nach Push):

```json
{
  "mcpServers": {
    "basti-tools": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/Toqsick/my-agent-tools.git", "mcp-server-basti"]
    }
  }
}
```

> **Server-Name:** Der MCP-Client registriert den Server unter dem Key (`basti-tools`). Der Entry-Point heißt `mcp-server-basti`. Beide können unabhängig gewählt werden, müssen aber konsistent zwischen `.mcp.json` und `check-mcp.sh` sein.

Claude Desktop legt die Konfiguration je nach Betriebssystem in seiner MCP-/`claude_desktop_config.json`-Datei ab; Cursor kann `.mcp.json` im Projekt oder eine globale MCP-Konfiguration verwenden. Nach Änderungen den Client neu starten.

## Hermes-Konfiguration

In Hermes wird der Server als stdio-MCP-Server konfiguriert. Beispiel:

```yaml
mcp_servers:
  basti-tools:
    command: uv
    args: [run, mcp-server-basti]
    cwd: /pfad/zu/my-agent-tools
```

Details zur Hermes-MCP-Konfiguration: `hermes mcp` CLI oder `hermes setup tools`.

## Tests ausführen

```bash
uv run pytest tests/unit tests/integration -v
```

Linting:

```bash
ruff check src/
```

## Logging analysieren

Der Server schreibt strukturierte JSON-Logs nach **stderr** (niemals stdout, da stdout für JSON-RPC reserviert ist). Bei Ausgabe in eine Datei umgeleitet (`2>`):

```bash
# Logs in Datei umleiten und filtern
uv run mcp-server-basti 2>logs.jsonl
jq -c 'select(.is_error == true)' logs.jsonl
jq -r 'select(.tool_name != null) | [.timestamp, .tool_name, .duration_ms, .message] | @tsv' logs.jsonl
```

## Architektur-Übersicht

```text
MCP-Client (Claude/Cursor/Hermes)
        │ JSON-RPC über stdin/stdout (stdio)
        ▼
mcp-server-basti (stderr = JSON-Logs)
   ├── get_system_status  (uptime-Subprocess, read-only)
   ├── echo_tool          (reine Eingabe → Ausgabe, no side-effects)
   └── get_repo_info      (git branch + commit, read-only)
```

Der Client startet pro Konfiguration einen Prozess. Tool-Aufrufe bleiben innerhalb dieses Prozesses.

## Troubleshooting

### `uv: command not found`
Installiere uv nach der offiziellen Anleitung und öffne danach eine neue Shell.

### Python-Version zu alt
Prüfe `python3 --version`; der Server benötigt Python 3.11+.

### Server erscheint nicht im Client
JSON-Syntax, `command`, `args`, `cwd` prüfen. Den Befehl `uv run mcp-server-basti` zunächst im Terminal ausführen. Danach den Client neu starten.

### MCP-Handshake oder JSON-Parse-Fehler
Der Server schreibt Logs nach stderr. Wenn andere Komponenten auf stdout schreiben, wird der JSON-RPC-Stream beschädigt. Sicherstellen, dass nur der MCP-Server auf stdout zugreift.

Das Tool fragt immer das Server-Repo ab (`DEFAULT_REPO_PATH` in `server.py`), nicht das CWD des aufrufenden Prozesses.
Bei normalen Clones ist keine Anpassung nötig, da `DEFAULT_REPO_PATH` relativ zur Datei bestimmt wird.
