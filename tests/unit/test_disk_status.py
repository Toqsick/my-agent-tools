"""Unit-Tests für get_disk_status (mocked subprocess.run)."""

from __future__ import annotations

import pytest

pytest.importorskip("mcp_server_basti.server")

from mcp_server_basti.server import get_disk_status

_DF_HEADER = "source,fstype,size,used,avail,pcent,target"
_DF_ARGV = ("df", "-h", f"--output={_DF_HEADER}")


def test_get_disk_status_parses_filesystems(fake_subprocess, completed):
    """df-Zeilen werden in Filesystem-Dicts geparst."""
    fake_subprocess({
        _DF_ARGV: completed(stdout=(
            "Filesystem Type Size Used Avail Use% Mounted on\n"
            "/dev/nvme0n1p3 ext4 607G 527G 80G 92% /\n"
            "/dev/nvme0n1p2 ext4 329G 313G 16G 95% /mnt/DATA\n"
        )),
    })
    result = get_disk_status()
    assert result["filesystems"][0]["target"] == "/"
    assert result["filesystems"][0]["pcent"] == "92%"
    assert result["filesystems"][1]["target"] == "/mnt/DATA"
    assert result["filesystems"][1]["pcent"] == "95%"
    assert result["filesystems"][1]["fstype"] == "ext4"


def test_get_disk_status_empty_when_no_filesystems(fake_subprocess, completed):
    """Nur Header, keine Zeilen → leere Liste."""
    fake_subprocess({_DF_ARGV: completed(stdout="Filesystem Type Size Used Avail Use% Mounted on\n")})
    result = get_disk_status()
    assert result["filesystems"] == []


def test_get_disk_status_skips_malformed_rows(fake_subprocess, completed):
    """Zeilen mit != 7 Spalten werden übersprungen, nicht gecrasht."""
    fake_subprocess({
        _DF_ARGV: completed(stdout=(
            "Filesystem Type Size Used Avail Use% Mounted on\n"
            "/dev/nvme0n1p3 ext4 607G 527G 80G 92% /\n"
            "broken row\n"
        )),
    })
    result = get_disk_status()
    assert len(result["filesystems"]) == 1
