# Tool Reference — mcp-server-basti

## Tools

| Tool | Parameter | Rückgabetyp | Beschreibung | Side-Effect |
|------|-----------|-------------|--------------|-------------|
| `get_system_status` | keine | `str` (uptime-Output) | Führt `uptime` aus und gibt den stdout zurück. | read (Subprocess, keine Mutation) |
| `echo_tool` | `text: str` (required) | `str` | Gibt den übergebenen Text unverändert zurück. Health-Check-Tool. | none |
| `get_repo_info` | keine | `str` | Git-Branch und letzter Commit des Server-Repos (`DEFAULT_REPO_PATH`). | read (git-Subprocess, keine Mutation) |

## Beispiele

### get_system_status

**Input:** keine Parameter

**Output (beispielhaft, Linux):**
```
 04:24:40 up  2:46,  1 user,  load average: 9,64, 8,19, 6,85
```

> Format hängt vom Betriebssystem ab. Der Server gibt den rohen `uptime`-stdout zurück ohne weitere Formatierung.

**Fehlerfall:** Wenn `uptime` nicht gefunden wird oder mit Exit-Code ≠ 0 terminiert, gibt das Tool einen strukturierten Fehler zurück (`isError: true`).

### echo_tool

**Input:**
```json
{"text": "hello"}
```

**Output:**
```
hello
```

**Fehlerfall:** FastMCP validiert via Pydantic, dass `text` ein String ist. Fehlt der Parameter → `McpError` auf Client-Seite.

### get_repo_info

**Input:** keine Parameter

**Output (beispielhaft):**
```
Branch: main
Letzter Commit: 634ff36 Merge pull request #1 from Toqsick/integrate/zcode-routing
```

> Das Tool ruft `git rev-parse --abbrev-ref HEAD` und `git log -1 --oneline` für das Server-Repo (`DEFAULT_REPO_PATH` in `server.py`) auf. Es liefert **nur** Branch und Commit — kein Remote, keine Tags.

**Fehlerfall:** Wenn das Verzeichnis kein Git-Repo ist oder `git` fehlschlägt, gibt das Tool einen strukturierten Fehler zurück (`isError: true`).

## Fehlerformat

Tool-Errors nutzen `fastmcp.tools.base.ToolResult` mit `is_error=True`:

```json
{
  "isError": true,
  "content": [{"type": "text", "text": "Systemstatus konnte nicht ermittelt werden: ..."}]
}
```

## skill-mcp-router Integration

Der Server ist für die Integration mit dem bestehenden `skill-mcp-router` vorbereitet, aber **noch nicht aktiv verdrahtet**. Die `routing/registry/registry.json` hat ein `mcp_server`-Feld pro Skill, in das `"mcp-server-basti"` eingetragen werden kann, um Skill-Intents zu diesen Tools aufzulösen.

**Status:** Derzeit nutzt kein Skill in der Registry den Server `mcp-server-basti`. Um ihn zu aktivieren, müssten Skills mit passenden Intents angelegt und in der Registry registriert werden. Siehe `routing/registry/registry.json` für das Format.
