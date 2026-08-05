"""Unit-Tests für get_kernel_warnings (mocked subprocess.run)."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp_server_basti.server")
from mcp_server_basti.server import get_kernel_warnings

_ARGV = ("journalctl", "-b", "-p", "warning", "--no-pager")


def test_get_kernel_warnings_returns_raw_string(fake_subprocess, completed):
    """Output ist der rohe journalctl-Text."""
    fake_subprocess({_ARGV: completed(stdout="Aug 05 kernel: warning text\n")})
    result = get_kernel_warnings()
    assert isinstance(result, str)
    assert "warning text" in result


def test_get_kernel_warnings_empty_is_not_error(fake_subprocess, completed):
    """Keine Warnings → leerer String (returncode 0), kein ToolError."""
    fake_subprocess({_ARGV: completed(stdout="", returncode=0)})
    assert get_kernel_warnings() == ""


def test_get_kernel_warnings_journalctl_missing_raises(monkeypatch):
    """Fehlt journalctl → ToolError."""

    def _boom(argv, **kwargs):
        raise OSError("journalctl: not found")

    monkeypatch.setattr("mcp_server_basti.server.subprocess.run", _boom)
    from fastmcp.exceptions import ToolError

    with pytest.raises(ToolError):
        get_kernel_warnings()
