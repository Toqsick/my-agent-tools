"""Unit-Tests für get_failed_units (mocked subprocess.run)."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp_server_basti.server")
from mcp_server_basti.server import get_failed_units


def test_get_failed_units_empty(fake_subprocess, completed):
    """Keine fehlgeschlagenen Units → leere Liste, Summary-Zeile wird ignoriert."""
    fake_subprocess({
        ("systemctl", "--failed", "--no-pager"): completed(stdout=(
            "  UNIT LOAD ACTIVE SUB DESCRIPTION\n\n"
            "0 loaded units listed.\n"
        )),
    })
    f = get_failed_units()
    assert f["failed"] == []
    assert "0 loaded units listed" in f["raw"]


def test_get_failed_units_with_failures(fake_subprocess, completed):
    """Echte Unit-Namen (mit Punkt) werden erfasst, Header/Summary ignoriert."""
    fake_subprocess({
        ("systemctl", "--failed", "--no-pager"): completed(stdout=(
            "  UNIT LOAD ACTIVE SUB DESCRIPTION\n"
            "  bad.service loaded failed failed something broke\n"
            "  down.mount loaded failed failed mount gone\n\n"
            "2 loaded units listed.\n"
        )),
    })
    f = get_failed_units()
    assert f["failed"] == ["bad.service", "down.mount"]


def test_get_failed_units_preserves_raw(fake_subprocess, completed):
    """raw enthält den unveränderten systemctl-Output."""
    out = "  UNIT LOAD ACTIVE SUB DESCRIPTION\n0 loaded units listed.\n"
    fake_subprocess({("systemctl", "--failed", "--no-pager"): completed(stdout=out)})
    assert get_failed_units()["raw"] == out
