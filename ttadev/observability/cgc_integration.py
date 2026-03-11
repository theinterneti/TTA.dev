"""CodeGraphContext integration for observability dashboard.

Availability is checked by pinging FalkorDB directly via its Unix socket
(fast, <1ms).  Graph queries spawn a stdio subprocess per call with a
generous timeout — acceptable since they're infrequent and cached.
"""

import asyncio
import json
import os
import shutil
import socket
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

# Direct binary path avoids uv startup overhead on each call
_CGC_BIN = shutil.which("cgc") or "cgc"
_FALKORDB_SOCK = os.path.expanduser("~/.codegraphcontext/falkordb.sock")
_CGC_ENV = {
    **os.environ,
    "DEFAULT_DATABASE": "falkordb",
    "FALKORDB_SOCKET_PATH": _FALKORDB_SOCK,
    "ENABLE_APP_LOGS": "CRITICAL",
    "LIBRARY_LOG_LEVEL": "WARNING",
}

# Timeout for each subprocess+MCP call (startup ~8-12s, plus query time)
_CALL_TIMEOUT = 25.0


def _falkordb_reachable() -> bool:
    """Synchronous socket ping — returns True in <5ms when FalkorDB is up."""
    if not os.path.exists(_FALKORDB_SOCK):
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            s.connect(_FALKORDB_SOCK)
            s.send(b"*1\r\n$4\r\nPING\r\n")
            return s.recv(10) == b"+PONG\r\n"
    except OSError:
        return False


class CGCIntegration:
    """Integration with CodeGraphContext MCP server."""

    def __init__(self) -> None:
        self.server_params = StdioServerParameters(
            command=_CGC_BIN,
            args=["mcp", "start"],
            env=_CGC_ENV,
        )

    # ------------------------------------------------------------------
    # Internal: spawn a subprocess for one batch of tool calls
    # ------------------------------------------------------------------

    async def _run(self, tool: str, args: dict[str, Any] | None = None) -> Any:
        """Spawn cgc subprocess, call one tool, return parsed result."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), timeout=_CALL_TIMEOUT)
                result = await asyncio.wait_for(
                    session.call_tool(tool, args or {}), timeout=_CALL_TIMEOUT
                )
                first = result.content[0]
                raw = first.text if isinstance(first, TextContent) else str(first)
                return json.loads(raw) if raw.strip().startswith(("{", "[")) else raw

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def is_available(self) -> bool:
        """Fast check: is FalkorDB reachable?

        Uses a direct Unix socket ping instead of spawning a subprocess,
        so it completes in <5ms even when the CGC binary is slow to start.
        """
        try:
            return await asyncio.get_event_loop().run_in_executor(None, _falkordb_reachable)
        except Exception:
            return False

    async def get_repository_stats(self) -> dict[str, Any]:
        return await asyncio.wait_for(self._run("get_repository_stats"), timeout=_CALL_TIMEOUT)

    async def find_code(self, keyword: str) -> list[dict[str, Any]]:
        result = await asyncio.wait_for(
            self._run("find_code", {"keyword": keyword}), timeout=_CALL_TIMEOUT
        )
        return result if isinstance(result, list) else []

    async def analyze_relationships(self, query_type: str, target: str) -> dict[str, Any]:
        return await asyncio.wait_for(
            self._run(
                "analyze_code_relationships",
                {"query_type": query_type, "target": target},
            ),
            timeout=_CALL_TIMEOUT,
        )

    async def get_primitives_graph(self) -> dict[str, Any]:
        cypher = """
        MATCH (c:Class)
        WHERE c.name CONTAINS 'Primitive'
        OPTIONAL MATCH (c)-[r:CALLS|INHERITS]->(related)
        RETURN c, r, related
        LIMIT 100
        """
        return await asyncio.wait_for(
            self._run("execute_cypher_query", {"query": cypher}), timeout=_CALL_TIMEOUT
        )

    async def get_agent_files(self) -> list[dict[str, Any]]:
        return await self.find_code("agent")

    async def get_workflow_files(self) -> list[dict[str, Any]]:
        return await self.find_code("workflow")

    async def get_live_nodes(self, primitive_names: list[str]) -> list[dict[str, Any]]:
        """Return CGC nodes matching the given primitive names (for live overlay)."""
        if not primitive_names:
            return []
        results: list[dict[str, Any]] = []
        for name in primitive_names:
            try:
                results.extend(await self.find_code(name))
            except Exception:
                pass
        return results
