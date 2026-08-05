"""Unit-Tests für echo_tool.

Isoliert die @mcp.tool()-Funktion und prüft ihre reine Business-Logik:
- Standard-ASCII ("hello") mit strikter Equality
- Leere Zeichenkette (Edge Case)
- Unicode ("üöäß") mit strikter Equality
"""

from __future__ import annotations

import pytest

pytest.importorskip("mcp_server_basti.server")
from mcp_server_basti.server import echo_tool


@pytest.mark.asyncio
async def test_echo_tool_hello() -> None:
    """Standard-ASCII-Input wird exakt (stripped) zurückgegeben."""
    result = await echo_tool("hello")
    assert result == "hello", f"Erwartet 'hello', bekam {result!r}"


@pytest.mark.asyncio
async def test_echo_tool_empty_string() -> None:
    """Leere Zeichenkette wird unverändert (leer) zurückgegeben."""
    result = await echo_tool("")
    assert result == "", f"Erwartet '', bekam {result!r}"


@pytest.mark.asyncio
async def test_echo_tool_unicode() -> None:
    """Unicode-Zeichen (Umlaute, Eszett) bleiben byte- und zeichengenau erhalten."""
    payload = "üöäß"
    result = await echo_tool(payload)
    assert result == payload, f"Erwartet {payload!r}, bekam {result!r}"
