"""Privater FastMCP-Server für lokale Werkzeuge.

Architektur:
- Transport: stdio (fd 0/1), Logging nach stderr (fd 2) — niemals stdout.
- Tool-Errors: fastmcp.ToolResult mit is_error=True, NICHT mcp.types.CallToolResult.
- Subprocess-Aufrufe via asyncio.to_thread, um den Event-Loop nicht zu blockieren.
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastmcp.tools.base import ToolResult
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from mcp_server_basti.logging_setup import LOGGER

# Standard-Repository für get_repo_info — kann via Env überschrieben werden.
DEFAULT_REPO_PATH = Path(__file__).resolve().parent.parent.parent

CONNECTION_ID = "local-stdio"
mcp = FastMCP("mcp-server-basti")


def _log_context(tool_name: str, request_id: str, **extra: Any) -> dict[str, Any]:
    """Erzeugt die gemeinsamen strukturierten Felder für einen Tool-Aufruf."""
    return {
        "request_id": request_id,
        "connection_id": CONNECTION_ID,
        "tool_name": tool_name,
        **extra,
    }


def _structured_error(message: str) -> ToolResult:
    """Liefert einen FastMCP-konformen Tool-Fehler (isError=True).

    WICHTIG: FastMCP v3 erwartet fastmcp.tools.base.ToolResult mit snake_case.
    mcp.types.CallToolResult wird von FastMCP nicht erkannt und als Text serialisiert.
    """
    return ToolResult(
        content=[TextContent(type="text", text=message)],
        is_error=True,
        structured_content=None,
    )


def _log_completion(
    tool_name: str,
    request_id: str,
    started_at: float,
    is_error: bool,
) -> float:
    """Loggt tool_call_success/error mit Duration und gibt duration_ms zurück."""
    duration_ms = round((time.perf_counter() - started_at) * 1000, 3)
    log_method = LOGGER.error if is_error else LOGGER.info
    log_method(
        "tool_call_error" if is_error else "tool_call_success",
        extra=_log_context(
            tool_name,
            request_id,
            duration_ms=duration_ms,
            is_error=is_error,
        ),
    )
    return duration_ms


@mcp.tool()
async def get_system_status() -> str | ToolResult:
    """Gibt den aktuellen Systemstatus aus dem Programm ``uptime`` zurück."""
    tool_name = "get_system_status"
    request_id = str(uuid4())
    started_at = time.perf_counter()
    LOGGER.info("tool_call_start", extra=_log_context(tool_name, request_id))

    try:
        result = await asyncio.to_thread(
            subprocess.run,
            ["uptime"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as exc:
        _log_completion(tool_name, request_id, started_at, is_error=True)
        return _structured_error(
            f"Systemstatus konnte nicht ermittelt werden: {exc}"
        )

    _log_completion(tool_name, request_id, started_at, is_error=False)
    return result.stdout


@mcp.tool()
async def echo_tool(text: str) -> str:
    """Gibt den übergebenen Text unverändert zurück.

    Nützlich als Health-Check und zum Testen der stdio-Verbindung.
    """
    tool_name = "echo_tool"
    request_id = str(uuid4())
    started_at = time.perf_counter()
    LOGGER.info("tool_call_start", extra=_log_context(tool_name, request_id))

    _log_completion(tool_name, request_id, started_at, is_error=False)
    return text


@mcp.tool()
async def get_repo_info() -> str | ToolResult:
    """Gibt den aktuellen Git-Branch und den letzten Commit des Server-Repos zurück."""
    tool_name = "get_repo_info"
    request_id = str(uuid4())
    started_at = time.perf_counter()
    LOGGER.info("tool_call_start", extra=_log_context(tool_name, request_id))

    try:
        # Subprocess-Aufrufe in Thread auslagern, um Event-Loop nicht zu blockieren.
        # cwd= garantiert, dass immer dasselbe Repo abgefragt wird (Server-Repo).
        branch = (
            await asyncio.to_thread(
                subprocess.run,
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(DEFAULT_REPO_PATH),
            )
        ).stdout.strip()
        last_commit = (
            await asyncio.to_thread(
                subprocess.run,
                ["git", "log", "-1", "--oneline"],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(DEFAULT_REPO_PATH),
            )
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError) as exc:
        _log_completion(tool_name, request_id, started_at, is_error=True)
        return _structured_error(
            f"Repository-Informationen konnten nicht ermittelt werden: {exc}"
        )

    _log_completion(tool_name, request_id, started_at, is_error=False)
    return f"Branch: {branch}\nLetzter Commit: {last_commit}"


def main() -> None:
    """Startet den lokalen MCP-Server über den stdio-Transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
