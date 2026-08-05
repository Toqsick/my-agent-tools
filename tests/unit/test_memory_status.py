"""Unit-Tests für get_memory_status (mocked subprocess.run)."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp_server_basti.server")
from mcp_server_basti.server import get_memory_status


def test_get_memory_status_returns_raw_blocks(fake_subprocess, completed):
    """free/zram/swaps werden als rohe Text-Blöcke durchgereicht."""
    fake_subprocess({
        ("free", "-h"): completed(stdout="total used free\nMem: 16Gi 8Gi 8Gi\n"),
        ("zramctl",): completed(stdout="NAME ALGORITHM DATA\n/dev/zram0 lzo 2G\n"),
        ("swapon", "--show"): completed(stdout="NAME TYPE SIZE USED PRIO\n/swapfile file 8G 0G -2\n"),
    })
    m = get_memory_status()
    assert "Mem:" in m["free"]
    assert "zram0" in m["zram"]
    assert "swapfile" in m["swaps"]


def test_get_memory_status_empty_when_commands_silent(fake_subprocess, completed):
    """Leere Ausgaben (zram/swaps nicht vorhanden) lieeren String, kein Fehler."""
    fake_subprocess({
        ("free", "-h"): completed(stdout=""),
        ("zramctl",): completed(stdout="", returncode=1),
        ("swapon", "--show"): completed(stdout="", returncode=1),
    })
    m = get_memory_status()
    assert m["free"] == ""
    assert m["zram"] == ""
    assert m["swaps"] == ""


def test_get_memory_status_free_failure_raises(monkeypatch):
    """Schlägt free fehl (check=True) → ToolError."""

    def _boom(argv, **kwargs):
        raise OSError("free: not found")

    monkeypatch.setattr("mcp_server_basti.server.subprocess.run", _boom)
    from fastmcp.exceptions import ToolError

    with pytest.raises(ToolError):
        get_memory_status()
