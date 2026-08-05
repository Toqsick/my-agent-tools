"""Integrationstest: get_repo_info Happy-Path über stdio.

Verifiziert die strukturierte RepoInfo-Rückgabe {branch, last_commit, detached}
über den echten stdio-Transport (standalone fastmcp structuredContent-Pfad).
"""

from __future__ import annotations

import asyncio

from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.integration.conftest import STDIO_TIMEOUT


async def test_get_repo_info_returns_structured(server_params) -> None:
    """get_repo_info liefert {branch, last_commit, detached} über stdio."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await asyncio.wait_for(session.initialize(), timeout=STDIO_TIMEOUT)
            result = await asyncio.wait_for(
                session.call_tool("get_repo_info", {}), timeout=STDIO_TIMEOUT
            )
    assert not result.isError, f"Tool-Fehler über stdio: {result.content}"
    sc = getattr(result, "structuredContent", None)
    assert sc is not None, "Kein structuredContent — Schema-Leck im standalone fastmcp-Pfad"
    assert set(sc.keys()) >= {"branch", "last_commit", "detached"}
    assert isinstance(sc["branch"], str) and len(sc["branch"]) > 0
    assert isinstance(sc["last_commit"], str) and len(sc["last_commit"]) > 0
    assert isinstance(sc["detached"], bool)
