"""Integration-Test: Strukturierte Tool-Errors statt Crashes.

Verifiziert, dass der Server fehlerhafte oder unbekannte Inputs als
strukturierte Tool-Errors (isError=True) oder als McpError zurückgibt —
aber NIEMALS als Server-Crash oder Connection-Verlust.

Drei Szenarien:
1. Unbekanntes Tool aufrufen → isError oder McpError
2. echo_tool ohne Pflicht-Argument → isError oder McpError
3. Nach einem Fehler bleibt die Session funktionsfähig
"""

from __future__ import annotations

import asyncio

import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import McpError

from tests.integration.conftest import STDIO_TIMEOUT


async def _call_and_get_error_state(
    session: ClientSession,
    tool_name: str,
    arguments: dict,
) -> bool:
    """Ruft ein Tool auf und gibt True zurück, wenn ein Fehler signalisiert wurde.

    Akzeptiert sowohl McpError (Protokoll-Ebene) als auch result.isError=True
    (Tool-Ebene) als korrekte Error-Signalisierung. Löst eine AssertionError aus,
    wenn KEIN Fehler gemeldet wird (der eigentliche Test-Fail).
    """
    try:
        result = await asyncio.wait_for(
            session.call_tool(tool_name, arguments),
            timeout=STDIO_TIMEOUT,
        )
        # Kein Exception → muss isError=True sein.
        assert result.isError, (
            f"Erwartet isError=True oder McpError für {tool_name}({arguments}), "
            f"bekam isError=False: {result!r}"
        )
        return True
    except McpError:
        # McpError ist ebenfalls ein gültiger strukturierter Fehler.
        return True


async def test_unknown_tool_returns_error_not_crash(server_params) -> None:
    """Aufruf eines nicht existierenden Tools liefert isError, kein Crash."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await asyncio.wait_for(session.initialize(), timeout=STDIO_TIMEOUT)
            await _call_and_get_error_state(session, "does_not_exist", {})


async def test_echo_tool_missing_required_argument(server_params) -> None:
    """echo_tool ohne 'text' liefert strukturierten Fehler, kein Crash."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await asyncio.wait_for(session.initialize(), timeout=STDIO_TIMEOUT)
            await _call_and_get_error_state(session, "echo_tool", {})


async def test_session_still_alive_after_error(server_params) -> None:
    """Nach einem fehlerhaften Tool-Call bleibt die Session funktionsfähig."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await asyncio.wait_for(session.initialize(), timeout=STDIO_TIMEOUT)

            # Fehler provozieren — muss strukturierter Error sein, kein Crash.
            await _call_and_get_error_state(session, "does_not_exist", {})

            # Wenn die Session diesen Aufruf nicht überlebt hätte, wäre das ein
            # Connection-Error oder Timeout — nicht ein erfolgreicher echo-Call.
            result = await asyncio.wait_for(
                session.call_tool("echo_tool", {"text": "alive"}),
                timeout=STDIO_TIMEOUT,
            )
            assert not result.isError, (
                f"Erwartet isError=False für erfolgreichen echo, bekam: {result!r}"
            )
            text = "".join(
                getattr(block, "text", "") for block in result.content
            )
            assert text.strip() == "alive", (
                f"Erwartet exakt 'alive', bekam: {text!r}"
            )
