"""Unit-Tests für get_boot_timing (mocked subprocess.run)."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp_server_basti.server")
from mcp_server_basti.server import get_boot_timing

_BLAME_ARGV = ("systemd-analyze", "blame", "--no-pager")
_CHAIN_ARGV = ("systemd-analyze", "critical-chain", "--no-pager")


def test_get_boot_timing_parses_blame(fake_subprocess, completed):
    """blame-Zeilen ('<time> <unit>') werden in BlameEntry-Dicts geparst."""
    fake_subprocess({
        _BLAME_ARGV: completed(stdout="21.166s apt-daily.service\n13.299s systemd-ask-password-wall.service\n"),
        _CHAIN_ARGV: completed(stdout="critical-chain text\n"),
    })
    b = get_boot_timing()
    assert len(b["blame"]) == 2
    assert b["blame"][0]["time"] == "21.166s"
    assert b["blame"][0]["unit"] == "apt-daily.service"
    assert b["critical_chain"] == "critical-chain text\n"


def test_get_boot_timing_empty_blame(fake_subprocess, completed):
    """Leere blame-Ausgabe → leere Liste, critical_chain trotzdem zurück."""
    fake_subprocess({
        _BLAME_ARGV: completed(stdout=""),
        _CHAIN_ARGV: completed(stdout="chain\n"),
    })
    b = get_boot_timing()
    assert b["blame"] == []
    assert b["critical_chain"] == "chain\n"


def test_get_boot_timing_skips_blank_lines(fake_subprocess, completed):
    """Leere Zeilen im blame-Output werden übersprungen."""
    fake_subprocess({
        _BLAME_ARGV: completed(stdout="\n1.000s foo.service\n\n"),
        _CHAIN_ARGV: completed(stdout=""),
    })
    b = get_boot_timing()
    assert len(b["blame"]) == 1
    assert b["blame"][0]["unit"] == "foo.service"
