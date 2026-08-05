"""Gemeinsame Fixtures für Integration-Tests.

Zentralisiert die Server-Parameter, damit Schema-Änderungen an einer Stelle
gepflegt werden (verhindert Drift zwischen 3 Test-Dateien).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp.client.stdio import StdioServerParameters

# Repo-Root = zwei Ebenen über dieser Datei (tests/integration/ → repo-root).
REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)

# Timeout für alle stdio-Operationen, um CI-Hänger zu vermeiden.
STDIO_TIMEOUT = 15.0


@pytest.fixture
def server_params() -> StdioServerParameters:
    """Server-Startparameter mit korrektem cwd= (Repo-Root)."""
    return StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "mcp_server_basti.server"],
        cwd=REPO_ROOT,
    )
