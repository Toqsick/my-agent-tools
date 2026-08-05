"""Unit-Tests für echo_tool.

Isoliert die Tool-Funktion und prüft ihre reine Business-Logik:
- Standard-ASCII ("hello") mit strikter Equality
- Leere Zeichenkette (Edge Case)
- Unicode ("üöäß") mit strikter Equality

echo_tool bleibt bewusst roher ``str`` (kein Schema) — der Health-Check muss
beliebigen Text unverändert round-tripen.
"""

from __future__ import annotations

import pytest

pytest.importorskip("mcp_server_basti.server")
from mcp_server_basti.server import echo_tool


def test_echo_tool_hello() -> None:
    """Standard-ASCII-Input wird exakt zurückgegeben."""
    result = echo_tool("hello")
    assert result == "hello", f"Erwartet 'hello', bekam {result!r}"


def test_echo_tool_empty_string() -> None:
    """Leere Zeichenkette wird unverändert (leer) zurückgegeben."""
    result = echo_tool("")
    assert result == "", f"Erwartet '', bekam {result!r}"


def test_echo_tool_unicode() -> None:
    """Unicode-Zeichen (Umlaute, Eszett) bleiben byte- und zeichengenau erhalten."""
    payload = "üöäß"
    result = echo_tool(payload)
    assert result == payload, f"Erwartet {payload!r}, bekam {result!r}"
