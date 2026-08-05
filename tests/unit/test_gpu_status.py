"""Unit-Tests für get_gpu_status (mocked subprocess.run)."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp_server_basti.server")
from fastmcp.exceptions import ToolError

from mcp_server_basti.server import get_gpu_status

_QUERY_ARGV = (
    "nvidia-smi",
    "--query-gpu=driver_version,name,temperature.gpu,utilization.gpu,"
    "memory.used,memory.total,pstate",
    "--format=csv,noheader,nounits",
)
_POWER_ARGV = ("nvidia-smi", "-q", "-d", "POWER")


def test_get_gpu_status_parses_fields(fake_subprocess, completed):
    """Treiber/Temp/Auslastung/VRAM werden aus der CSV-Zeile geparst."""
    fake_subprocess({
        _QUERY_ARGV: completed(stdout="595.84, RTX 5060 Laptop GPU, 40, 0, 65, 8151, P4"),
        _POWER_ARGV: completed(stdout=(
            "Current Power Limit                            : 25.00 W\n"
            "Default Power Limit                            : 80.00 W\n"
            "Max Power Limit                                : 115.00 W\n"
        )),
    })
    g = get_gpu_status()
    assert g["driver_version"] == "595.84"
    assert g["name"] == "RTX 5060 Laptop GPU"
    assert g["temperature_gpu"] == "40"
    assert g["utilization_gpu"] == "0"
    assert g["memory_used"] == "65"
    assert g["memory_total"] == "8151"
    assert g["pstate"] == "P4"
    assert g["power_limit"] == "25.00 W"
    assert g["power_default"] == "80.00 W"
    assert g["power_max"] == "115.00 W"


def test_get_gpu_status_multi_gpu_first_wins(fake_subprocess, completed):
    """Bei mehreren GPU-Abschnitten im POWER-Output gewinnt der erste (GPU 0)."""
    fake_subprocess({
        _QUERY_ARGV: completed(stdout="595.84, RTX 5060, 40, 0, 65, 8151, P4"),
        _POWER_ARGV: completed(stdout=(
            "Current Power Limit                            : 25.00 W\n"
            "Default Power Limit                            : 80.00 W\n"
            "Max Power Limit                                : 115.00 W\n"
            "Current Power Limit                            : N/A\n"
            "Default Power Limit                            : N/A\n"
            "Max Power Limit                                : N/A\n"
        )),
    })
    g = get_gpu_status()
    assert g["power_limit"] == "25.00 W"
    assert g["power_default"] == "80.00 W"
    assert g["power_max"] == "115.00 W"


def test_get_gpu_status_power_absent(fake_subprocess, completed):
    """Fehlen die Power-Limit-Zeilen, sind power_* None."""
    fake_subprocess({
        _QUERY_ARGV: completed(stdout="595.84, RTX 5060, 40, 0, 65, 8151, P4"),
        _POWER_ARGV: completed(stdout=""),
    })
    g = get_gpu_status()
    assert g["power_limit"] is None
    assert g["power_default"] is None
    assert g["power_max"] is None


def test_get_gpu_status_no_nvidia_raises_toolerror(monkeypatch):
    """Fehlt nvidia-smi (OSError) → ToolError, kein Crash."""

    def _boom(argv, **kwargs):
        raise OSError("nvidia-smi: command not found")

    monkeypatch.setattr("mcp_server_basti.server.subprocess.run", _boom)
    with pytest.raises(ToolError):
        get_gpu_status()


def test_get_gpu_status_bad_format_raises_toolerror(fake_subprocess, completed):
    """CSV-Zeile mit < 7 Feldern → ToolError."""
    fake_subprocess({
        _QUERY_ARGV: completed(stdout="595.84, RTX 5060, 40"),
        _POWER_ARGV: completed(stdout=""),
    })
    with pytest.raises(ToolError):
        get_gpu_status()
