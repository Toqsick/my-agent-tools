"""Integrationstest: strukturierte Rückgabe über den echten stdio-Transport.

Beweis, dass der standalone-fastmcp-``output_schema``/structuredContent-Pfad
end-to-end funktioniert. Verwendet get_memory_status (``free -h`` ist auf
ubuntu-latest garantiert vorhanden, im Gegensatz zu nvidia-smi/ufw). Erwartet
ein structuredContent-Dict mit den drei Feldern {free, zram, swaps}.
"""

from __future__ import annotations

import asyncio

from mcp import ClientSession
from mcp.client.stdio import stdio_client

from tests.integration.conftest import STDIO_TIMEOUT


async def test_get_memory_status_returns_structured_content(server_params) -> None:
    """get_memory_status liefert {free, zram, swaps} als structuredContent."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await asyncio.wait_for(session.initialize(), timeout=STDIO_TIMEOUT)
            result = await asyncio.wait_for(
                session.call_tool("get_memory_status", {}), timeout=STDIO_TIMEOUT
            )
    assert not result.isError, f"Tool-Fehler über stdio: {result.content}"
    sc = getattr(result, "structuredContent", None)
    assert sc is not None, "Kein structuredContent — Schema-Leck im standalone fastmcp-Pfad"
    assert set(sc.keys()) >= {"free", "zram", "swaps"}
    assert isinstance(sc["free"], str) and "Mem" in sc["free"]
