"""Unit-Tests für get_repo_info.

Prüft die reine Business-Logik:
- Rückgabetyp str
- Enthält "Branch:" und "Letzter Commit:" Label
- Der Branch stimmt mit dem echten Git-Branch überein
- Der Commit-Hash stimmt mit `git rev-parse --short` überein
"""

from __future__ import annotations

import subprocess

import pytest

pytest.importorskip("mcp_server_basti.server")
from mcp_server_basti.server import DEFAULT_REPO_PATH, get_repo_info


def _git_branch() -> str:
    """Aktuellen Branch-Namen aus dem Server-Repo ermitteln."""
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        text=True,
        stderr=subprocess.DEVNULL,
        cwd=str(DEFAULT_REPO_PATH),
    ).strip()


def _git_commit_short() -> str:
    """Kurzen Commit-Hash aus dem Server-Repo ermitteln."""
    return subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        text=True,
        stderr=subprocess.DEVNULL,
        cwd=str(DEFAULT_REPO_PATH),
    ).strip()


@pytest.mark.asyncio
async def test_get_repo_info_returns_text() -> None:
    """get_repo_info() liefert einen nicht-leeren String."""
    result = await get_repo_info()
    assert isinstance(result, str), f"Erwartet str, bekam {type(result).__name__}"
    assert len(result) > 0, "Repo-Info darf nicht leer sein"


@pytest.mark.asyncio
async def test_get_repo_info_contains_branch_label() -> None:
    """Output enthält das Label 'Branch:' — strukturelles Format des Tools."""
    result = await get_repo_info()
    assert "Branch:" in result, f"'Branch:' fehlt in Output: {result!r}"


@pytest.mark.asyncio
async def test_get_repo_info_contains_commit_label() -> None:
    """Output enthält das Label 'Letzter Commit:' — strukturelles Format."""
    result = await get_repo_info()
    assert "Letzter Commit:" in result, f"'Letzter Commit:' fehlt in Output: {result!r}"


@pytest.mark.asyncio
async def test_get_repo_info_branch_matches_actual() -> None:
    """Der im Output enthaltene Branch stimmt mit dem echten Git-Branch überein."""
    branch = _git_branch()
    result = await get_repo_info()
    assert branch in result, (
        f"Echter Branch {branch!r} nicht im Output: {result!r}"
    )


@pytest.mark.asyncio
async def test_get_repo_info_commit_matches_actual() -> None:
    """Der im Output enthaltene Commit-Hash stimmt mit git rev-parse überein."""
    actual_short = _git_commit_short()
    result = await get_repo_info()
    assert actual_short in result, (
        f"Kurzer Commit-Hash {actual_short!r} nicht im Output: {result!r}"
    )
