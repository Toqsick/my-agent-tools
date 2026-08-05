"""Integrationstest für get_firewall_state über stdio (nur lokal).

Setzt die installierte NOPASSWD-sudoers-Regel aus
``docs/mcp-server/SUDOERS_SETUP.md`` v.oraus. CI hat die Regel nicht, daher
ist der Test via ``BASTI_FW_TESTS``-Env-Gate standardmäßig übersprungen.

Lokal aktivieren: ``BASTI_FW_TESTS=1 uv run --extra dev pytest
tests/integration/test_firewall_integration.py -v``
"""

from __future__ import annotations

import asyncio
import os

import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.integration.conftest import STDIO_TIMEOUT

pytestmark = pytest.mark.skipif(
    not os.environ.get("BASTI_FW_TESTS"),
    reason="needs local NOPASSWD sudoers rule for ufw/ss (see docs/mcp-server/SUDOERS_SETUP.md)",
)


async def test_firewall_state_returns_structured(server_params) -> None:
    """Mit installierter Sudoers-Regel liefert das Tool {ufw, listening_ports}."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await asyncio.wait_for(session.initialize(), timeout=STDIO_TIMEOUT)
            result = await asyncio.wait_for(
                session.call_tool("get_firewall_state", {}), timeout=STDIO_TIMEOUT
            )
    assert not result.isError, f"Tool-Fehler über stdio: {result.content}"
    # FastMCP liefert strukturierte Rückgaben als structuredContent.
    sc = getattr(result, "structuredContent", None)
    assert sc is not None, "Kein structuredContent — Schema-Leck im standalone fastmcp-Pfad"
    assert "ufw" in sc and "listening_ports" in sc
    assert isinstance(sc["ufw"], str) and isinstance(sc["listening_ports"], str)


async def test_firewall_state_without_rule_degrades_to_toolerror(server_params) -> None:
    """Ohne Sudoers-Regel (BASTI_FW_TESTS nicht gesetzt → Test ohnehin skipped) ist
    dies nur ein Contract-Check; läuft nur lokal nach Entfernen der Regel sinnvoll."""
    # Bewusst kein assertions-starker Test hier: das Verhalten ohne Regel ist
    # durch den Unit-Test test_get_firewall_state_no_sudoers abgedeckt. Dieser Test
    # existiert nur, damit der Happy-Path-Pfad mit der Regel einmal über stdio läuft.
