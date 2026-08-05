"""Privater FastMCP-Server für lokale Werkzeuge.

Architektur:
- Transport: stdio (fd 0/1), Logging nach stderr (fd 2) — niemals stdout.
- Standalone FastMCP (>=3.0) statt des mcp[cli]-Shims: nur standalone bietet
  ``tags``, ``output_schema``, ``timeout`` und ``run_in_thread``. Tools sind
  sync ``def``; FastMCP lagert sie via ``run_in_thread=True`` in einen
  Threadpool aus, sodass ``asyncio.to_thread`` entfällt.
- Tool-Errors: werden via ``ToolError``-Exception signalisiert.
  Hintergrund: der mcp-lowlevel-Pfad baut Wire-Antworten in
  ``mcp/server/lowlevel/server.py`` — nur Exceptions werden zu
  ``CallToolResult(isError=True)``. Return-Werte werden pauschal mit
  ``isError=False`` gewrappt. Daher raise statt return.
- Pro-Aufruf-Logging ist im ``@with_tool_logging``-Dekorator
  (``instrumentation.py``) gekapselt; die Tool-Body selbst sind reine Logik.
- Alle Tools advertise ``readOnlyHint=True`` und ``tags={"system","read-only"}``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from mcp_server_basti.instrumentation import with_tool_logging
from mcp_server_basti.schemas import RepoInfo, SystemStatus

# Standard-Repository für get_repo_info — wird relativ zu dieser Datei bestimmt.
# (Portabel; kein Env-Override notwendig, da der Server immer im Repo läuft.)
DEFAULT_REPO_PATH = Path(__file__).resolve().parent.parent.parent

mcp = FastMCP("mcp-server-basti")

# Gemeinsame Annotations/Tags für alle read-only-System-Tools.
_READ_ONLY = ToolAnnotations(
    title="Read-only System-Tool",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)
_SYSTEM_TAGS = {"system", "read-only"}
_TOOL_TIMEOUT = 15.0
_SUBPROC_TIMEOUT = 10


@mcp.tool(
    tags=_SYSTEM_TAGS,
    annotations=_READ_ONLY,
    timeout=_TOOL_TIMEOUT,
)
@with_tool_logging()
def get_system_status() -> SystemStatus:
    """Gibt den aktuellen Systemstatus aus dem Programm ``uptime`` zurück."""
    try:
        result = subprocess.run(
            ["uptime"],
            check=True,
            capture_output=True,
            text=True,
            timeout=_SUBPROC_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as exc:
        raise ToolError(f"Systemstatus konnte nicht ermittelt werden: {exc}") from exc
    return SystemStatus(uptime=result.stdout)


@mcp.tool(
    tags={"system", "smoke-test"},
    annotations=ToolAnnotations(
        title="Echo (Smoke-Test)",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
    timeout=_TOOL_TIMEOUT,
)
@with_tool_logging()
def echo_tool(text: str) -> str:
    """Gibt den übergebenen Text unverändert zurück.

    Nützlich als Health-Check und zum Testen der stdio-Verbindung.
    """
    # Bewusst roher str (kein Schema) — Health-Check muss beliebigen Text
    # inkl. Leer/Unicode unverändert round-tripen.
    return text


@mcp.tool(
    tags=_SYSTEM_TAGS,
    annotations=_READ_ONLY,
    timeout=_TOOL_TIMEOUT,
)
@with_tool_logging()
def get_repo_info() -> RepoInfo:
    """Gibt den aktuellen Git-Branch und den letzten Commit des Server-Repos zurück."""
    try:
        # symbolic-ref --short gibt im detached-HEAD-State non-zero zurück,
        # sodass wir die echte Detached-Branch erkennen können.
        branch_proc = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=_SUBPROC_TIMEOUT,
            cwd=str(DEFAULT_REPO_PATH),
        )
        detached = branch_proc.returncode != 0
        if not detached:
            branch = branch_proc.stdout.strip()
        else:
            # Detached HEAD — symbolic-ref schlägt fehl, fallback auf rev-parse.
            short_sha = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                timeout=_SUBPROC_TIMEOUT,
                cwd=str(DEFAULT_REPO_PATH),
            ).stdout.strip()
            branch = f"detached@{short_sha}"

        last_commit = subprocess.run(
            ["git", "log", "-1", "--oneline"],
            check=True,
            capture_output=True,
            text=True,
            timeout=_SUBPROC_TIMEOUT,
            cwd=str(DEFAULT_REPO_PATH),
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as exc:
        raise ToolError(
            f"Repository-Informationen konnten nicht ermittelt werden: {exc}"
        ) from exc

    return RepoInfo(branch=branch, last_commit=last_commit, detached=detached)


def main() -> None:
    """Startet den lokalen MCP-Server über den stdio-Transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
