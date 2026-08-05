"""Unit-Tests für get_firewall_state (mocked subprocess.run)."""

from __future__ import annotations

import subprocess

import pytest

pytest.importorskip("mcp_server_basti.server")
from fastmcp.exceptions import ToolError

from mcp_server_basti.server import _SS_BIN, _UFW_BIN, get_firewall_state

_UFW_ARGV = ("sudo", "-n", "--", _UFW_BIN, "status", "verbose")
_SS_ARGV = ("sudo", "-n", "--", _SS_BIN, "-tlnp")


def _install(
    monkeypatch: pytest.MonkeyPatch,
    responses: dict[tuple[str, ...], subprocess.CompletedProcess[str] | Exception],
) -> None:
    """Patcht subprocess.run mit einem Lookup argv-tuple → CompletedProcess|Exception."""

    def _fake(argv, **kwargs):
        key = tuple(argv)
        if key not in responses:
            raise AssertionError(f"unexpected call: {argv}")
        v = responses[key]
        if isinstance(v, Exception):
            raise v
        return v

    monkeypatch.setattr("mcp_server_basti.server.subprocess.run", _fake)


def _completed(
    stdout: str = "", stderr: str = "", returncode: int = 0
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )


def test_get_firewall_state_success(monkeypatch):
    """Beide Kommandos liefern Output → {ufw, listening_ports}."""
    _install(
        monkeypatch,
        {
            _UFW_ARGV: _completed(stdout="Status: active\n"),
            _SS_ARGV: _completed(stdout="State Recv-Q 0.0.0.0:22\n"),
        },
    )
    f = get_firewall_state()
    assert f["ufw"] == "Status: active\n"
    assert "0.0.0.0:22" in f["listening_ports"]


def test_get_firewall_state_no_sudoers(monkeypatch):
    """sudo -n scheitert mit 'password' im stderr → ToolError verweist auf SUDOERS_SETUP.md."""
    _install(
        monkeypatch,
        {
            _UFW_ARGV: subprocess.CalledProcessError(
                1, _UFW_ARGV, stderr="sudo: a password is required\n"
            ),
        },
    )
    with pytest.raises(ToolError) as exc:
        get_firewall_state()
    assert "SUDOERS_SETUP.md" in str(exc.value)


def test_get_firewall_state_ufw_nonzero_other_error(monkeypatch):
    """Non-zero exit ohne 'password' im stderr → allgemeiner ToolError (kein Sudoers-Hinweis)."""

    def _fake(argv, **kwargs):
        raise subprocess.CalledProcessError(2, argv, stderr="ufw: unknown command\n")

    monkeypatch.setattr("mcp_server_basti.server.subprocess.run", _fake)
    with pytest.raises(ToolError) as exc:
        get_firewall_state()
    assert "SUDOERS_SETUP.md" not in str(exc.value)
    assert "unknown command" in str(exc.value)


def test_get_firewall_state_ufw_missing(monkeypatch):
    """Fehlt sudo/ufw (OSError) → ToolError, kein Crash."""

    def _boom(argv, **kwargs):
        raise OSError("sudo: command not found")

    monkeypatch.setattr("mcp_server_basti.server.subprocess.run", _boom)
    with pytest.raises(ToolError):
        get_firewall_state()
