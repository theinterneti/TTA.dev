"""FalkorDBClient — direct Python client for CGC's FalkorDB graph.

Connects via Unix socket (same approach as ttadev/observability/cgc_integration.py).
Schema assumed by the Cypher queries here:
  Function(name, path, line_number, cyclomatic_complexity)
  Class(name, path, line_number)
  CALLS, IMPORTS, INHERITS relationships
See tests/primitives/code_graph/test_schema_smoke.py for schema verification.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
from concurrent.futures import ThreadPoolExecutor
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_SOCK = os.path.expanduser("~/.codegraphcontext/falkordb.sock")
_GRAPH_NAME = "codegraph"


def _falkordb_reachable(socket_path: str) -> bool:
    """Synchronous socket ping — returns True in <5ms when FalkorDB is up."""
    if not os.path.exists(socket_path):
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            s.connect(socket_path)
            s.send(b"*1\r\n$4\r\nPING\r\n")
            return s.recv(10) == b"+PONG\r\n"
    except OSError:
        return False


class FalkorDBClient:
    """Direct Python client for CGC's FalkorDB graph.

    Connects via Unix socket using the ``falkordb`` package (already installed
    as a transitive dep of ``codegraphcontext``).  All public methods are async;
    the sync FalkorDB calls run in a thread executor.

    Schema coupling: see module docstring and test_schema_smoke.py.
    """

    def __init__(self, socket_path: str | None = None) -> None:
        self._socket_path = socket_path or os.environ.get("FALKORDB_SOCKET_PATH") or _DEFAULT_SOCK
        self._graph: Any | None = None  # falkordb.Graph, lazy-init
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="falkordb")

    # ── Internal ─────────────────────────────────────────────────────────────

    def _get_graph(self) -> Any:
        """Lazy-init FalkorDB connection. Must be called inside the executor."""
        if self._graph is None:
            import falkordb  # optional dep — present when cgc is installed

            db = falkordb.FalkorDB(unix_socket_path=self._socket_path)
            self._graph = db.select_graph(_GRAPH_NAME)
        return self._graph

    def _query_sync(self, cypher: str, params: dict[str, Any] | None = None) -> list[Any]:
        """Run synchronous FalkorDB query. Call via _query()."""
        graph = self._get_graph()
        result = graph.query(cypher, params or {})
        return result.result_set

    async def _query(self, cypher: str, params: dict[str, Any] | None = None) -> list[Any]:
        """Async wrapper: runs _query_sync in thread executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: self._query_sync(cypher, params),
        )

    # ── Public ────────────────────────────────────────────────────────────────

    def is_reachable(self) -> bool:
        """Fast (<5ms) Unix socket ping. Call before any query."""
        return _falkordb_reachable(self._socket_path)

    async def find_code(self, target: str, repo_path: str | None = None) -> list[dict[str, Any]]:
        """Find Functions and Classes whose name contains ``target``.

        Returns list of dicts: {name, path, line_number, kind}.
        """
        repo_filter = f" AND f.path STARTS WITH '{repo_path}'" if repo_path else ""
        results: list[dict[str, Any]] = []

        rows = await self._query(
            f"MATCH (f:Function) WHERE f.name CONTAINS $target{repo_filter} "
            f"RETURN f.name, f.path, f.line_number",
            {"target": target},
        )
        for row in rows:
            results.append(
                {"name": row[0], "path": row[1], "line_number": row[2], "kind": "Function"}
            )

        rows = await self._query(
            f"MATCH (c:Class) WHERE c.name CONTAINS $target{repo_filter} "
            f"RETURN c.name, c.path, c.line_number",
            {"target": target},
        )
        for row in rows:
            results.append({"name": row[0], "path": row[1], "line_number": row[2], "kind": "Class"})

        return results

    async def get_callers(self, target: str, repo_path: str | None = None) -> list[dict[str, Any]]:
        """Find functions that CALL any function whose name contains ``target``."""
        repo_filter = f" AND callee.path STARTS WITH '{repo_path}'" if repo_path else ""
        rows = await self._query(
            f"MATCH (caller:Function)-[:CALLS]->(callee:Function) "
            f"WHERE callee.name CONTAINS $target{repo_filter} "
            f"RETURN DISTINCT caller.name, caller.path, caller.line_number",
            {"target": target},
        )
        return [{"name": r[0], "path": r[1], "line_number": r[2]} for r in rows]

    async def get_callees(self, target: str, repo_path: str | None = None) -> list[dict[str, Any]]:
        """Find functions called BY any function whose name contains ``target``."""
        repo_filter = f" AND caller.path STARTS WITH '{repo_path}'" if repo_path else ""
        rows = await self._query(
            f"MATCH (caller:Function)-[:CALLS]->(callee:Function) "
            f"WHERE caller.name CONTAINS $target{repo_filter} "
            f"RETURN DISTINCT callee.name, callee.path, callee.line_number",
            {"target": target},
        )
        return [{"name": r[0], "path": r[1], "line_number": r[2]} for r in rows]

    async def get_complexity(self, target: str, repo_path: str | None = None) -> float:
        """Get highest cyclomatic complexity among functions matching ``target``.

        Returns 0.0 if not found or if complexity property is null.
        """
        repo_filter = f" AND f.path STARTS WITH '{repo_path}'" if repo_path else ""
        rows = await self._query(
            f"MATCH (f:Function) WHERE f.name CONTAINS $target{repo_filter} "
            f"RETURN f.cyclomatic_complexity "
            f"ORDER BY f.cyclomatic_complexity DESC LIMIT 1",
            {"target": target},
        )
        if rows and rows[0][0] is not None:
            return float(rows[0][0])
        return 0.0

    async def execute_cypher(self, query: str) -> list[dict[str, Any]]:
        """Execute raw Cypher query. Returns list of {values: [...]} dicts."""
        rows = await self._query(query)
        return [{"values": list(row)} for row in rows]
