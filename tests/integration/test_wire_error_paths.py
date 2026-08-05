"""Integration-Tests für die Wire-Ebene der Tool-Errors.

Diese Tests verifizieren, dass Tool-Fehler als strukturierte Tool-Errors
(isError=True auf der Wire) zurückgegeben werden — NICHT als Crashes oder
nicht-Markierte Success-Results.

Wire-Verhalten wird getestet durch echten stdio_client, weil der mcp-shim-Pfad
(lowlevel/server.py) isError-Flags in einem separaten Codepfad setzt.
Nur echte subprocess-Failures landen im ToolError-Pfad des Tools.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# Repo-Root = zwei Ebenen über dieser Datei (tests/integration/ → repo-root).
REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)


# Timeout für stdio-Operationen.
STDIO_TIMEOUT = 15.0


@pytest.fixture
def not_git_wrapper() -> Iterator[str]:
    """Erstellt ein Python-Wrapper-Script das den Server mit nicht-Git-cwd startet.

    Das provoziert einen echten subprocess-failure im Tool-Body,
    sodass wir den echten ToolError→Wire-Pfad testen.
    """
    wrapper_path = Path(REPO_ROOT) / ".tmp-test-not-repo.py"
    wrapper_content = f"""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, "{REPO_ROOT}/src")
import mcp_server_basti.server as srv
srv.DEFAULT_REPO_PATH = Path(tempfile.mkdtemp(prefix='not-a-repo-'))
srv.main()
"""
    wrapper_path.write_text(wrapper_content)
    yield str(wrapper_path)
    # Cleanup
    try:
        wrapper_path.unlink()
    except OSError:
        pass


async def test_get_repo_info_returns_structured_error_on_git_failure(
    not_git_wrapper: str,
) -> None:
    """Wenn git in der Repo-cwd fehlschlägt, returnt der Server isError=True.

    Verifiziert den echten Wire-Pfad: Tool ruft subprocess auf, subprocess
    schlägt fehl, Tool wirft ToolError, mcp-shim-Pfad baut
    CallToolResult(isError=True). Das ist die Korrektur des Run-1-C1-Fixes.
    """
    params = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "--directory",
            REPO_ROOT,
            "python",
            not_git_wrapper,
        ],
        env=os.environ.copy(),
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await asyncio.wait_for(session.initialize(), timeout=STDIO_TIMEOUT)
            result = await asyncio.wait_for(
                session.call_tool("get_repo_info", {}),
                timeout=STDIO_TIMEOUT,
            )

            assert result.isError, (
                f"Erwartet isError=True auf der Wire (subprocess-failure), "
                f"bekam isError=False. "
                f"content={result.content[0].text[:200] if result.content else 'EMPTY'}"
            )

            assert result.content, "isError=True aber content ist leer"
            text_parts = []
            for block in result.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)
            text = "".join(text_parts)
            assert "Repository" in text or "git" in text, (
                f"Error-Text sollte auf Repository-Fehler hinweisen: "
                f"{text[:300]!r}"
            )
