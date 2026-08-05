"""Unit-Tests für get_system_status.

Isoliert die @mcp.tool()-Funktion und prüft ihre reine Business-Logik:
- Rückgabetyp str
- Nicht-leer
- Enthält spezifische uptime-Indikatoren ("load average" ist auf Linux nahezu garantiert)
"""

from __future__ import annotations

import pytest

# importorskip statt try/except+skip: bricht laut, wenn der Server einen echten
# Import-Bug hat (SyntaxError, fehlende transitive Dep), statt still zu skippen.
pytest.importorskip("mcp_server_basti.server")
from mcp_server_basti.server import get_system_status


@pytest.mark.asyncio
async def test_get_system_status_returns_text() -> None:
    """get_system_status() liefert einen nicht-leeren String."""
    result = await get_system_status()
    assert isinstance(result, str), f"Erwartet str, bekam {type(result).__name__}"
    assert len(result) > 0, "Uptime-Output darf nicht leer sein"


@pytest.mark.asyncio
async def test_get_system_status_contains_load_average() -> None:
    """Output enthält 'load average' — das ist auf Linux der zuverlässigste uptime-Indikator.

    Früher wurde auf generische Tokens ("up", "time") geprüft, die fast jeder
    englische String matched. "load average" ist spezifisch für das uptime-Kommando.
    """
    result = await get_system_status()
    lowered = result.lower()
    assert "load average" in lowered, (
        f"Uptime-Output enthält nicht 'load average' (Linux-Standardformat): {result!r}"
    )
