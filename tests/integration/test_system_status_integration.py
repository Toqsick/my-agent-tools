"""Integrationstest: get_system_status Happy-Path über stdio.

Verifiziert den fehlenden Happy-Path-Wire-Test: Tool liefert strukturierten
SystemStatus zurück, kein isError.
"""

from __future__ import annotations

import asyncio

from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.integration.conftest import STDIO_TIMEOUT


async def test_get_system_status_returns_structured(server_params) -> None:
    """get_system_status liefert {uptime: str} über stdio, kein isError."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await asyncio.wait_for(session.initialize(), timeout=STDIO_TIMEOUT)
            result = await asyncio.wait_for(
                session.call_tool("get_system_status", {}), timeout=STDIO_TIMEOUT
            )
    assert not result.isError, f"Tool-Fehler über stdio: {result.content}"
    sc = getattr(result, "structuredContent", None)
    assert sc is not None, "Kein structuredContent — Schema-Leck im standalone fastmcp-Pfad"
    assert "uptime" in sc
    assert isinstance(sc["uptime"], str) and len(sc["uptime"]) > 0
