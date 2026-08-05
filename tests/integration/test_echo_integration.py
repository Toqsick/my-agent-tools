"""Integration-Test: echo_tool über stdio_client (echter StdIO-Transport).

Startet den Server, schickt ein `call_tool("echo_tool", {"text": "ping"})`
über das MCP-Protokoll und prüft, dass "ping" exakt zurückkommt.
"""

from __future__ import annotations

import asyncio

from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.integration.conftest import STDIO_TIMEOUT


async def test_echo_tool_returns_ping(server_params) -> None:
    """echo_tool('ping') -> 'ping' über vollständigen MCP-Transport (strikt)."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await asyncio.wait_for(session.initialize(), timeout=STDIO_TIMEOUT)

            result = await asyncio.wait_for(
                session.call_tool("echo_tool", {"text": "ping"}),
                timeout=STDIO_TIMEOUT,
            )

            assert not result.isError, (
                f"call_tool meldete isError=True: {result.content!r}"
            )

            text = "".join(
                getattr(block, "text", "") for block in result.content
            )
            assert text.strip() == "ping", (
                f"Erwartet exakt 'ping', bekam: {text!r}"
            )


async def test_echo_tool_unicode_over_wire(server_params) -> None:
    """Unicode-Echo funktioniert auch über den echten StdIO-Transport (strikt)."""
    payload = "üöäß"
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await asyncio.wait_for(session.initialize(), timeout=STDIO_TIMEOUT)

            result = await asyncio.wait_for(
                session.call_tool("echo_tool", {"text": payload}),
                timeout=STDIO_TIMEOUT,
            )

            assert not result.isError
            text = "".join(
                getattr(block, "text", "") for block in result.content
            )
            assert text.strip() == payload, (
                f"Erwartet exakt {payload!r}, bekam: {text!r}"
            )
