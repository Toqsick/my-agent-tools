"""Unit-Tests für get_power_profile (mocked subprocess.run)."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp_server_basti.server")
from fastmcp.exceptions import ToolError

from mcp_server_basti.server import get_power_profile


def test_get_power_profile_returns_profile(fake_subprocess, completed):
    """powerprofilesctl get → {profile: <name>}."""
    fake_subprocess({("powerprofilesctl", "get"): completed(stdout="power-saver\n")})
    assert get_power_profile() == {"profile": "power-saver"}


def test_get_power_profile_strips_whitespace(fake_subprocess, completed):
    """Whitespace um den Profilnamen wird entfernt."""
    fake_subprocess({("powerprofilesctl", "get"): completed(stdout="  balanced  \n")})
    assert get_power_profile() == {"profile": "balanced"}


def test_get_power_profile_missing_raises(monkeypatch):
    """Fehlt powerprofilesctl → ToolError."""

    def _boom(argv, **kwargs):
        raise OSError("powerprofilesctl: not found")

    monkeypatch.setattr("mcp_server_basti.server.subprocess.run", _boom)
    with pytest.raises(ToolError):
        get_power_profile()
