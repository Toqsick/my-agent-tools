"""Unit-Tests für get_system_status.

Isoliert die Tool-Funktion und prüft ihre reine Business-Logik:
- Rückgabetyp SystemStatus (dict mit ``uptime``-Schlüssel)
- uptime ist ein nicht-leerer String
- Enthält spezifische uptime-Indikatoren ("load average" ist auf Linux nahezu garantiert)

Hinweis: ruft das echte ``uptime``-Binary auf (existiert auf dev + CI). Neuere
Tools mocken subprocess.run; dieses alte Test-File bleibt bewusst real —
Tech-Schuld, nicht blockierend.
"""

from __future__ import annotations

import pytest

# importorskip statt try/except+skip: bricht laut, wenn der Server einen echten
# Import-Bug hat (SyntaxError, fehlende transitive Dep), statt still zu skippen.
pytest.importorskip("mcp_server_basti.server")
from mcp_server_basti.server import get_system_status


def test_get_system_status_returns_typed_dict() -> None:
    """get_system_status() liefert ein dict mit dem 'uptime'-Schlüssel."""
    result = get_system_status()
    assert isinstance(result, dict), f"Erwartet dict, bekam {type(result).__name__}"
    assert "uptime" in result, f"Schlüssel 'uptime' fehlt in {result!r}"


def test_get_system_status_uptime_not_empty() -> None:
    """Der uptime-Wert ist ein nicht-leerer String."""
    result = get_system_status()
    uptime = result["uptime"]
    assert isinstance(uptime, str), f"Erwartet str, bekam {type(uptime).__name__}"
    assert len(uptime) > 0, "Uptime-Output darf nicht leer sein"


def test_get_system_status_contains_load_average() -> None:
    """Output enthält 'load average' — zuverlässigster uptime-Indikator auf Linux."""
    result = get_system_status()
    lowered = result["uptime"].lower()
    assert "load average" in lowered, (
        f"Uptime-Output enthält nicht 'load average' (Linux-Standardformat): "
        f"{result['uptime']!r}"
    )
