"""Unit-Tests für get_repo_info.

Prüft die reine Business-Logik der strukturierten Rückgabe:
- Rückgabetyp RepoInfo (dict mit branch/last_commit/detached)
- branch stimmt mit dem echten Git-Branch überein (bzw. detached@<sha>)
- last_commit stimmt mit ``git log -1 --oneline`` überein
- detached ist ein bool und korrekt zum Head-State
"""

from __future__ import annotations

import subprocess

import pytest

pytest.importorskip("mcp_server_basti.server")
from mcp_server_basti.schemas import RepoInfo
from mcp_server_basti.server import DEFAULT_REPO_PATH, get_repo_info


def _git_branch_and_detached() -> tuple[str, bool]:
    """Aktuellen Branch-Namen und Detached-Flag aus dem Server-Repo ermitteln."""
    proc = subprocess.run(
        ["git", "symbolic-ref", "--short", "HEAD"],
        capture_output=True,
        text=True,
        cwd=str(DEFAULT_REPO_PATH),
        check=False,
    )
    if proc.returncode == 0 and proc.stdout:
        return proc.stdout.strip(), False
    # Detached HEAD — fall back to rev-parse
    short_sha = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        text=True,
        stderr=subprocess.DEVNULL,
        cwd=str(DEFAULT_REPO_PATH),
    ).strip()
    return f"detached@{short_sha}", True


def _git_last_commit() -> str:
    """Letzten Commit (oneline) aus dem Server-Repo ermitteln."""
    return subprocess.check_output(
        ["git", "log", "-1", "--oneline"],
        text=True,
        stderr=subprocess.DEVNULL,
        cwd=str(DEFAULT_REPO_PATH),
    ).strip()


def test_get_repo_info_returns_typed_dict() -> None:
    """get_repo_info() liefert ein dict mit den RepoInfo-Schlüsseln."""
    result = get_repo_info()
    assert isinstance(result, dict), f"Erwartet dict, bekam {type(result).__name__}"
    for key in ("branch", "last_commit", "detached"):
        assert key in result, f"Schlüssel {key!r} fehlt in {result!r}"


def test_get_repo_info_branch_matches_actual() -> None:
    """Der branch-Wert stimmt mit dem echten Git-Branch überein."""
    branch, _ = _git_branch_and_detached()
    result = get_repo_info()
    assert result["branch"] == branch, (
        f"Echter Branch {branch!r} != tool-branch {result['branch']!r}"
    )


def test_get_repo_info_last_commit_matches_actual() -> None:
    """Der last_commit-Wert stimmt mit ``git log -1 --oneline`` überein."""
    actual = _git_last_commit()
    result = get_repo_info()
    assert result["last_commit"] == actual, (
        f"Echter Commit {actual!r} != tool-commit {result['last_commit']!r}"
    )


def test_get_repo_info_detached_is_bool_and_consistent() -> None:
    """detached ist ein bool und stimmt mit dem Head-State überein."""
    _, detached = _git_branch_and_detached()
    result = get_repo_info()
    assert isinstance(result["detached"], bool), (
        f"detached muss bool sein, bekam {type(result['detached']).__name__}"
    )
    assert result["detached"] == detached, (
        f"Echter detached-State {detached} != tool-detached {result['detached']}"
    )


def test_repo_info_schema_is_typed_dict() -> None:
    """RepoInfo ist eine TypedDict-Klasse (statischer Contract)."""
    # __annotations__ ist das TypedDict-Merkmal (3.11+).
    assert set(RepoInfo.__annotations__) == {"branch", "last_commit", "detached"}
