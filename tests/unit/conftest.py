"""Fixtures für Unit-Tests: subprocess.run mocken, damit CI reproduzierbar läuft.

Die neuen System-Tools rufen Binaries (nvidia-smi, ufw, journalctl, …), die auf
CI (ubuntu-latest) fehlen. Unit-Tests mocken daher subprocess.run und liefern
vorbereitete CompletedProcess-Ergebnisse.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from typing import Any

import pytest


class _FakeRunner:
    """Ersetzt subprocess.run im server-Modul mit einem Lookup nach argv."""

    def __init__(self, mapping: dict[tuple[str, ...], subprocess.CompletedProcess[str]]):
        self.mapping = mapping
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(argv))
        key = tuple(argv)
        if key in self.mapping:
            return self.mapping[key]
        raise AssertionError(
            f"unexpected subprocess.run call: {argv}. "
            f"bekannte Calls: {list(self.mapping)}"
        )


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    """Baut ein CompletedProcess für gefakte subprocess.run-Aufrufe."""
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )


@pytest.fixture
def fake_subprocess(monkeypatch: pytest.MonkeyPatch) -> Callable[..., _FakeRunner]:
    """Installiert einen Fake für ``mcp_server_basti.server.subprocess.run``.

    Usage::
        fake = fake_subprocess({
            ("df", "-h", "--output=..."): _completed(stdout=...),
        })
        result = get_disk_status()
        assert fake.calls == [["df", ...]]
    """

    def install(
        mapping: dict[tuple[str, ...], subprocess.CompletedProcess[str]],
    ) -> _FakeRunner:
        runner = _FakeRunner(mapping)
        monkeypatch.setattr("mcp_server_basti.server.subprocess.run", runner)
        return runner

    return install


@pytest.fixture
def completed() -> Callable[..., subprocess.CompletedProcess[str]]:
    """Factory für CompletedProcess-Objekte im Test."""
    return _completed
