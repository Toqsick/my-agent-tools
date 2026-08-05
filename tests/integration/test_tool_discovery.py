"""Integration-Test: Tool-Discovery über stdio_client.

Startet den MCP-Server als Subprozess, initialisiert die Session und
verifiziert, dass exakt die 3 Tools aus dem Server-Contract advertised werden.
"""

from __future__ import annotations

import asyncio

from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.integration.conftest import STDIO_TIMEOUT

EXPECTED_TOOLS = {"get_system_status", "echo_tool", "get_repo_info"}


async def test_tool_discovery_lists_all_three_tools(server_params) -> None:
    """Nach session.initialize() sind alle 3 Server-Tools discoverable."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await asyncio.wait_for(session.initialize(), timeout=STDIO_TIMEOUT)
            tools = await asyncio.wait_for(
                session.list_tools(), timeout=STDIO_TIMEOUT
            )
            tool_names = {t.name for t in tools.tools}

            assert EXPECTED_TOOLS.issubset(tool_names), (
                f"Erwartete Tools {EXPECTED_TOOLS}, "
                f"bekam {tool_names}, "
                f"fehlen: {EXPECTED_TOOLS - tool_names}"
            )


async def test_tool_discovery_exactly_three_tools(server_params) -> None:
    """Der Server advertised exakt 3 Tools — keine Extra-Tools, keine fehlenden."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await asyncio.wait_for(session.initialize(), timeout=STDIO_TIMEOUT)
            tools = await asyncio.wait_for(
                session.list_tools(), timeout=STDIO_TIMEOUT
            )
            tool_names = {t.name for t in tools.tools}

            assert tool_names == EXPECTED_TOOLS, (
                f"Erwartet exakt {EXPECTED_TOOLS}, "
                f"bekam {tool_names} ({len(tools.tools)} Tools). "
                f"Extra: {tool_names - EXPECTED_TOOLS}, "
                f"Fehlend: {EXPECTED_TOOLS - tool_names}"
            )

            for tool in tools.tools:
                assert isinstance(tool.name, str) and len(tool.name) > 0
                assert tool.description, f"Tool {tool.name!r} hat keine Description"
