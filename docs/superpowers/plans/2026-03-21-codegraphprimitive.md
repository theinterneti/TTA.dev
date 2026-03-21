# CodeGraphPrimitive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `CodeGraphPrimitive` — a typed, instrumented primitive that wraps FalkorDB (CGC's graph backend) to answer "what does this code touch?" as the Orient step of the DevelopmentCycle loop.

**Architecture:** `FalkorDBClient` connects to CGC's FalkorDB via Unix socket (`~/.codegraphcontext/falkordb.sock`) using the `falkordb` Python package (already in venv as a transitive dep of `codegraphcontext`). `CodeGraphPrimitive` extends `InstrumentedPrimitive[CodeGraphQuery, ImpactReport]` and dispatches five operations (`find_code`, `get_relationships`, `get_complexity`, `find_tests`, `raw_cypher`) to the client. The schema coupling risk is mitigated by an integration smoke test and a Hindsight retention. Degrades gracefully when FalkorDB is unreachable.

> **Approved deviation from spec:** The spec says "wraps the CodeGraphContext (CGC) MCP server." This plan queries FalkorDB directly instead. This was explicitly approved by the spec author: CGC MCP tools are only available inside Claude Code with MCP configured, not in test/E2B/production workflow contexts. CLI output is Rich terminal tables (no JSON), making it unsuitable for programmatic use. Direct FalkorDB is the correct architecture for this constraint.

**Tech Stack:** `falkordb==1.6.0` (already installed), `asyncio.get_event_loop().run_in_executor` for async wrapping of sync FalkorDB calls, `unittest.mock.AsyncMock` for tests, `pytest-asyncio` for async tests.

---

## Key Context

**Existing pattern to follow:** `ttadev/observability/cgc_integration.py` already uses the same FalkorDB Unix-socket ping pattern (`_falkordb_reachable`). Follow that file's conventions.

**FalkorDB facts:**
- Graph name: `codegraph` (single graph for all repos)
- Socket path: `~/.codegraphcontext/falkordb.sock` (env var: `FALKORDB_SOCKET_PATH`)
- `falkordb.FalkorDB` is **synchronous** — wrap with `run_in_executor`
- No `=~` regex support — use `CONTAINS` for substring matching
- Node labels: `Function`, `Class`, `File`, `Module`, `Repository`
- Function properties: `name`, `path`, `line_number`, `cyclomatic_complexity`
- Relationship types: `CALLS`, `IMPORTS`, `INHERITS`, `CONTAINS`

**Import path for `InstrumentedPrimitive`:**
```python
from ttadev.primitives.observability import InstrumentedPrimitive
```

**Import path for `WorkflowContext`:**
```python
from ttadev.primitives.core.base import WorkflowContext
```

**Test patterns:** Use `@pytest.mark.asyncio`, `unittest.mock.AsyncMock`, `unittest.mock.MagicMock`, `unittest.mock.patch`. See `tests/agents/test_agent_primitive.py` for style.

**Risk derivation rule (matches CGC's own `COMPLEXITY_THRESHOLD=10`):**
- `complexity >= 10` → `"high"`
- `complexity >= 5` OR `len(callers) >= 5` → `"medium"`
- else → `"low"`

---

## File Map

| Action | Path | Purpose |
|---|---|---|
| Create | `ttadev/primitives/code_graph/__init__.py` | Package exports |
| Create | `ttadev/primitives/code_graph/types.py` | `CGCOp`, `CodeGraphQuery`, `ImpactReport` |
| Create | `ttadev/primitives/code_graph/client.py` | `FalkorDBClient` — direct DB access |
| Create | `ttadev/primitives/code_graph/primitive.py` | `CodeGraphPrimitive` |
| Modify | `ttadev/primitives/__init__.py` | Export 4 new names |
| Create | `tests/primitives/__init__.py` | Test package |
| Create | `tests/primitives/code_graph/__init__.py` | Test subpackage |
| Create | `tests/primitives/code_graph/test_client.py` | FalkorDBClient unit tests |
| Create | `tests/primitives/code_graph/test_primitive.py` | CodeGraphPrimitive unit tests |
| Create | `tests/primitives/code_graph/test_schema_smoke.py` | Integration smoke test (live FalkorDB) |

---

## Task 1: Retain schema coupling decision to Hindsight (pre-implementation)

**Files:** None (MCP API call only)

- [ ] **Step 1: Retain schema coupling decision**

POST to `http://localhost:8888/v1/default/banks/tta-dev/memories` with body:
```json
{
  "items": [{
    "content": "[type: decision] CodeGraphPrimitive queries FalkorDB directly via Unix socket (graph: 'codegraph') rather than parsing CGC CLI output (no JSON flag, ~1s startup per call). Schema assumed: Function(name, path, line_number, cyclomatic_complexity), Class(name, path, line_number), relationships: CALLS, IMPORTS, INHERITS, CONTAINS. FalkorDB does NOT support =~ (use CONTAINS). Rationale: CLI output is Rich terminal tables — not machine-parseable. Risk: if CGC changes its internal schema, our Cypher queries break silently. Mitigation: schema smoke test in tests/primitives/code_graph/test_schema_smoke.py (@pytest.mark.integration) + this memory. Context: ttadev/primitives/code_graph/client.py"
  }]
}
```

- [ ] **Step 2: Commit**

```bash
git commit --allow-empty -m "docs(hindsight): retain CodeGraphPrimitive schema coupling decision"
```

---

## Task 2: Types module

**Files:**
- Create: `ttadev/primitives/code_graph/types.py`
- Create: `ttadev/primitives/code_graph/__init__.py`

- [ ] **Step 1: Write the failing test**

Create `tests/primitives/__init__.py` (empty) and `tests/primitives/code_graph/__init__.py` (empty), then create `tests/primitives/code_graph/test_primitive.py` with just the import test:

```python
"""Unit tests for CodeGraphPrimitive."""


def test_types_importable() -> None:
    from ttadev.primitives.code_graph.types import CGCOp, CodeGraphQuery, ImpactReport

    assert CGCOp.find_code.value == "find_code"
    assert CGCOp.get_relationships.value == "get_relationships"
    assert CGCOp.get_complexity.value == "get_complexity"
    assert CGCOp.find_tests.value == "find_tests"
    assert CGCOp.raw_cypher.value == "raw_cypher"
```

- [ ] **Step 2: Run to confirm it fails**

```bash
uv run python -m pytest tests/primitives/code_graph/test_primitive.py::test_types_importable -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: Create `ttadev/primitives/code_graph/__init__.py`** (empty for now)

```python
"""CodeGraphPrimitive — typed, instrumented CGC orient step."""
```

- [ ] **Step 4: Create `ttadev/primitives/code_graph/types.py`**

```python
"""CodeGraphPrimitive types — CGCOp enum, CodeGraphQuery, ImpactReport."""

from __future__ import annotations

import enum
from typing import Literal, TypedDict


class CGCOp(enum.Enum):
    """Operations that CodeGraphPrimitive can execute against the code graph."""

    find_code = "find_code"
    get_relationships = "get_relationships"
    get_complexity = "get_complexity"
    find_tests = "find_tests"
    raw_cypher = "raw_cypher"


class CodeGraphQuery(TypedDict, total=False):
    """Input for CodeGraphPrimitive.

    All fields are optional at the TypedDict level, but:
    - ``operations`` is always required at runtime.
    - ``target`` is required for all ops except ``raw_cypher``.
    - ``cypher`` is required for ``CGCOp.raw_cypher``.
    """

    target: str  # function/class name (substring match)
    operations: list[CGCOp]  # required
    depth: int  # default 2, clamped to 5
    cypher: str  # required for CGCOp.raw_cypher
    repo_path: str | None  # optional: filter results to this repo path


class ImpactReport(TypedDict):
    """Output from CodeGraphPrimitive."""

    target: str
    callers: list[str]  # "FuncName (path:line)"
    dependencies: list[str]  # functions called by target
    related_tests: list[str]  # file paths containing "/test" or "test_"
    complexity: float  # cyclomatic complexity; 0.0 if not queried
    risk: Literal["low", "medium", "high"]
    summary: str  # human/LLM-readable paragraph
    cgc_available: bool  # False when FalkorDB was unreachable
```

- [ ] **Step 5: Run to confirm it passes**

```bash
uv run python -m pytest tests/primitives/code_graph/test_primitive.py::test_types_importable -v
```
Expected: `PASSED`

- [ ] **Step 6: Commit**

```bash
git add ttadev/primitives/code_graph/ tests/primitives/
git commit -m "feat(code_graph): add CGCOp, CodeGraphQuery, ImpactReport types"
```

---

## Task 3: FalkorDBClient

**Files:**
- Create: `ttadev/primitives/code_graph/client.py`
- Create: `tests/primitives/code_graph/test_client.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/primitives/code_graph/test_client.py`:

```python
"""Unit tests for FalkorDBClient — all FalkorDB calls mocked."""

from __future__ import annotations

import socket
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from ttadev.primitives.code_graph.client import FalkorDBClient, _falkordb_reachable


# ── _falkordb_reachable ───────────────────────────────────────────────────────

class TestFalkordbReachable:
    def test_returns_false_when_socket_missing(self, tmp_path: object) -> None:
        result = _falkordb_reachable(str(tmp_path / "nonexistent.sock"))  # type: ignore[operator]
        assert result is False

    def test_returns_false_on_connection_refused(self, tmp_path: object) -> None:
        import os
        sock_path = str(tmp_path / "test.sock")  # type: ignore[operator]
        # Bind but don't listen — connect will be refused
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(sock_path)
        try:
            result = _falkordb_reachable(sock_path)
        finally:
            s.close()
            if os.path.exists(sock_path):
                os.unlink(sock_path)
        assert result is False

    def test_returns_true_on_pong_response(self, tmp_path: object) -> None:
        sock_path = str(tmp_path / "pong.sock")  # type: ignore[operator]

        def _server() -> None:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.bind(sock_path)
            s.listen(1)
            conn, _ = s.accept()
            conn.recv(1024)
            conn.send(b"+PONG\r\n")
            conn.close()
            s.close()

        t = threading.Thread(target=_server, daemon=True)
        t.start()
        time.sleep(0.05)
        result = _falkordb_reachable(sock_path)
        assert result is True


# ── FalkorDBClient ────────────────────────────────────────────────────────────

class TestFalkorDBClientFindCode:
    @pytest.mark.asyncio
    async def test_find_code_returns_functions_and_classes(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        call_count = 0

        def _fake_query(cypher: str, params: dict | None = None) -> list:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [["RetryPrimitive", "/src/retry.py", 10]]  # Function row
            return [["RetryPrimitive", "/src/retry.py", 5]]  # Class row

        with patch.object(client, "_query_sync", side_effect=_fake_query):
            result = await client.find_code("RetryPrimitive")

        assert len(result) == 2
        assert any(r["kind"] == "Function" for r in result)
        assert any(r["kind"] == "Class" for r in result)
        assert result[0]["name"] == "RetryPrimitive"

    @pytest.mark.asyncio
    async def test_find_code_with_repo_path_filter(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        captured: list[str] = []

        def _fake_query(cypher: str, params: dict | None = None) -> list:
            captured.append(cypher)
            return []

        with patch.object(client, "_query_sync", side_effect=_fake_query):
            await client.find_code("fn", repo_path="/home/user/myrepo")

        assert all("/home/user/myrepo" in q for q in captured)


class TestFalkorDBClientRelationships:
    @pytest.mark.asyncio
    async def test_get_callers_returns_caller_dicts(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        with patch.object(client, "_query_sync", return_value=[["execute", "/src/base.py", 75]]):
            result = await client.get_callers("_execute_impl")

        assert len(result) == 1
        assert result[0]["name"] == "execute"
        assert result[0]["path"] == "/src/base.py"
        assert result[0]["line_number"] == 75

    @pytest.mark.asyncio
    async def test_get_callees_returns_callee_dicts(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        with patch.object(client, "_query_sync", return_value=[["_run_step", "/src/orch.py", 42]]):
            result = await client.get_callees("execute")

        assert result[0]["name"] == "_run_step"


class TestFalkorDBClientComplexity:
    @pytest.mark.asyncio
    async def test_get_complexity_returns_float(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        with patch.object(client, "_query_sync", return_value=[[7.0]]):
            result = await client.get_complexity("my_fn")
        assert result == 7.0

    @pytest.mark.asyncio
    async def test_get_complexity_returns_zero_when_not_found(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        with patch.object(client, "_query_sync", return_value=[]):
            result = await client.get_complexity("unknown_fn")
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_get_complexity_returns_zero_on_null(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        with patch.object(client, "_query_sync", return_value=[[None]]):
            result = await client.get_complexity("fn_no_complexity")
        assert result == 0.0


class TestFalkorDBClientCypher:
    @pytest.mark.asyncio
    async def test_execute_cypher_returns_row_dicts(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        with patch.object(client, "_query_sync", return_value=[["fn1", "path1"], ["fn2", "path2"]]):
            result = await client.execute_cypher("MATCH (f:Function) RETURN f.name, f.path")

        assert len(result) == 2
        assert result[0]["values"] == ["fn1", "path1"]
        assert result[1]["values"] == ["fn2", "path2"]
```

- [ ] **Step 2: Run to confirm they fail**

```bash
uv run python -m pytest tests/primitives/code_graph/test_client.py -v
```
Expected: `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Create `ttadev/primitives/code_graph/client.py`**

```python
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
        self._socket_path = (
            socket_path
            or os.environ.get("FALKORDB_SOCKET_PATH")
            or _DEFAULT_SOCK
        )
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

    async def find_code(
        self, target: str, repo_path: str | None = None
    ) -> list[dict[str, Any]]:
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
            results.append(
                {"name": row[0], "path": row[1], "line_number": row[2], "kind": "Class"}
            )

        return results

    async def get_callers(
        self, target: str, repo_path: str | None = None
    ) -> list[dict[str, Any]]:
        """Find functions that CALL any function whose name contains ``target``."""
        repo_filter = f" AND callee.path STARTS WITH '{repo_path}'" if repo_path else ""
        rows = await self._query(
            f"MATCH (caller:Function)-[:CALLS]->(callee:Function) "
            f"WHERE callee.name CONTAINS $target{repo_filter} "
            f"RETURN DISTINCT caller.name, caller.path, caller.line_number",
            {"target": target},
        )
        return [{"name": r[0], "path": r[1], "line_number": r[2]} for r in rows]

    async def get_callees(
        self, target: str, repo_path: str | None = None
    ) -> list[dict[str, Any]]:
        """Find functions called BY any function whose name contains ``target``."""
        repo_filter = f" AND caller.path STARTS WITH '{repo_path}'" if repo_path else ""
        rows = await self._query(
            f"MATCH (caller:Function)-[:CALLS]->(callee:Function) "
            f"WHERE caller.name CONTAINS $target{repo_filter} "
            f"RETURN DISTINCT callee.name, callee.path, callee.line_number",
            {"target": target},
        )
        return [{"name": r[0], "path": r[1], "line_number": r[2]} for r in rows]

    async def get_complexity(
        self, target: str, repo_path: str | None = None
    ) -> float:
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run python -m pytest tests/primitives/code_graph/test_client.py -v
```
Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add ttadev/primitives/code_graph/client.py tests/primitives/code_graph/test_client.py
git commit -m "feat(code_graph): add FalkorDBClient with Unix socket + Cypher queries"
```

---

## Task 4: Schema smoke test (integration)

**Files:**
- Create: `tests/primitives/code_graph/test_schema_smoke.py`

This test requires a live FalkorDB socket. It is marked `@pytest.mark.integration` and excluded from the default test run. Run manually to verify schema after CGC upgrades.

- [ ] **Step 1: Create `tests/primitives/code_graph/test_schema_smoke.py`**

```python
"""Schema smoke test — verifies FalkorDB schema assumptions made by client.py.

REQUIRES: live FalkorDB socket at ~/.codegraphcontext/falkordb.sock
RUN WITH: uv run python -m pytest tests/primitives/code_graph/test_schema_smoke.py -m integration -v

If this test fails after a CGC upgrade:
  1. Update the Cypher queries in ttadev/primitives/code_graph/client.py
  2. Retain the schema change to Hindsight tta-dev bank
"""

from __future__ import annotations

import pytest

from ttadev.primitives.code_graph.client import FalkorDBClient, _falkordb_reachable

_SOCK = FalkorDBClient()._socket_path


@pytest.fixture
def live_client() -> FalkorDBClient:
    if not _falkordb_reachable(_SOCK):
        pytest.skip("FalkorDB not reachable — run cgc mcp start first")
    return FalkorDBClient()


@pytest.mark.integration
def test_expected_node_labels_exist(live_client: FalkorDBClient) -> None:
    """CALLS, CONTAINS, IMPORTS, INHERITS must exist."""
    import asyncio

    rows = asyncio.get_event_loop().run_until_complete(
        live_client.execute_cypher("CALL db.labels()")
    )
    labels = {r["values"][0] for r in rows}
    assert "Function" in labels, f"Missing 'Function' label. Got: {labels}"
    assert "Class" in labels, f"Missing 'Class' label. Got: {labels}"


@pytest.mark.integration
def test_function_has_expected_properties(live_client: FalkorDBClient) -> None:
    """Function nodes must have name, path, cyclomatic_complexity."""
    import asyncio

    rows = asyncio.get_event_loop().run_until_complete(
        live_client.execute_cypher(
            "MATCH (f:Function) WHERE f.cyclomatic_complexity IS NOT NULL "
            "RETURN f.name, f.path, f.cyclomatic_complexity LIMIT 1"
        )
    )
    assert rows, "No Function nodes with cyclomatic_complexity found"
    vals = rows[0]["values"]
    assert vals[0] is not None, "f.name is null"
    assert vals[2] is not None, "f.cyclomatic_complexity is null"


@pytest.mark.integration
def test_calls_relationship_exists(live_client: FalkorDBClient) -> None:
    """CALLS relationship must exist in the graph."""
    import asyncio

    rows = asyncio.get_event_loop().run_until_complete(
        live_client.execute_cypher("CALL db.relationshipTypes()")
    )
    rel_types = {r["values"][0] for r in rows}
    assert "CALLS" in rel_types, f"Missing CALLS relationship. Got: {rel_types}"
    assert "IMPORTS" in rel_types, f"Missing IMPORTS relationship. Got: {rel_types}"


@pytest.mark.integration
def test_find_code_returns_results_for_known_symbol(live_client: FalkorDBClient) -> None:
    """find_code('InstrumentedPrimitive') must return at least one result."""
    import asyncio

    results = asyncio.get_event_loop().run_until_complete(
        live_client.find_code("InstrumentedPrimitive")
    )
    assert results, "find_code returned no results for 'InstrumentedPrimitive'"
    assert any(r["name"] == "InstrumentedPrimitive" for r in results)
```

- [ ] **Step 2: Verify unit tests still pass (no regression)**

```bash
uv run python -m pytest tests/primitives/code_graph/test_client.py -v
```
Expected: all `PASSED`

- [ ] **Step 3: Run smoke test manually to confirm it works against live DB**

```bash
uv run python -m pytest tests/primitives/code_graph/test_schema_smoke.py -m integration -v
```
Expected: all `PASSED` (FalkorDB is running)

- [ ] **Step 4: Commit**

```bash
git add tests/primitives/code_graph/test_schema_smoke.py
git commit -m "test(code_graph): add integration schema smoke test for FalkorDB coupling"
```

---

## Task 5: CodeGraphPrimitive

**Files:**
- Create: `ttadev/primitives/code_graph/primitive.py`
- Modify: `tests/primitives/code_graph/test_primitive.py` (expand from the import test)

- [ ] **Step 1: Write failing tests (replace test_primitive.py content)**

```python
"""Unit tests for CodeGraphPrimitive — all FalkorDB calls mocked."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ttadev.primitives.code_graph.client import FalkorDBClient
from ttadev.primitives.code_graph.types import CGCOp, CodeGraphQuery
from ttadev.primitives.core.base import WorkflowContext


def test_types_importable() -> None:
    from ttadev.primitives.code_graph.types import CGCOp, CodeGraphQuery, ImpactReport

    assert CGCOp.find_code.value == "find_code"
    assert CGCOp.get_relationships.value == "get_relationships"
    assert CGCOp.get_complexity.value == "get_complexity"
    assert CGCOp.find_tests.value == "find_tests"
    assert CGCOp.raw_cypher.value == "raw_cypher"


def _mock_client(**overrides: object) -> AsyncMock:
    """Build a mock FalkorDBClient with safe defaults."""
    client = AsyncMock(spec=FalkorDBClient)
    client.is_reachable = MagicMock(return_value=True)  # sync method
    client.find_code = AsyncMock(return_value=[])
    client.get_callers = AsyncMock(return_value=[])
    client.get_callees = AsyncMock(return_value=[])
    client.get_complexity = AsyncMock(return_value=0.0)
    client.execute_cypher = AsyncMock(return_value=[])
    for k, v in overrides.items():
        setattr(client, k, v)
    return client


class TestCodeGraphPrimitiveValidation:
    @pytest.mark.asyncio
    async def test_empty_operations_returns_empty_report(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client()
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="foo", operations=[]),
            WorkflowContext(),
        )
        assert result["risk"] == "low"
        assert result["callers"] == []
        assert result["cgc_available"] is False  # no operations = no query
        client.get_callers.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_target_raises_value_error(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client()
        prim = CodeGraphPrimitive(cgc_client=client)
        with pytest.raises(ValueError, match="target is required"):
            await prim.execute(
                CodeGraphQuery(operations=[CGCOp.get_relationships]),
                WorkflowContext(),
            )

    @pytest.mark.asyncio
    async def test_raw_cypher_without_cypher_field_raises(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client()
        prim = CodeGraphPrimitive(cgc_client=client)
        with pytest.raises(ValueError, match="cypher query string is required"):
            await prim.execute(
                CodeGraphQuery(target="", operations=[CGCOp.raw_cypher]),
                WorkflowContext(),
            )


class TestCodeGraphPrimitiveOperations:
    @pytest.mark.asyncio
    async def test_get_relationships_populates_callers_and_deps(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            get_callers=AsyncMock(
                return_value=[{"name": "execute", "path": "/src/base.py", "line_number": 75}]
            ),
            get_callees=AsyncMock(
                return_value=[{"name": "_run_step", "path": "/src/orch.py", "line_number": 42}]
            ),
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="_execute_impl", operations=[CGCOp.get_relationships]),
            WorkflowContext(),
        )
        assert len(result["callers"]) == 1
        assert "execute" in result["callers"][0]
        assert len(result["dependencies"]) == 1
        assert result["cgc_available"] is True

    @pytest.mark.asyncio
    async def test_get_complexity_high_risk(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(get_complexity=AsyncMock(return_value=12.0))
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="complex_fn", operations=[CGCOp.get_complexity]),
            WorkflowContext(),
        )
        assert result["risk"] == "high"
        assert result["complexity"] == 12.0

    @pytest.mark.asyncio
    async def test_get_complexity_medium_risk_at_5(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(get_complexity=AsyncMock(return_value=5.0))
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="fn", operations=[CGCOp.get_complexity]),
            WorkflowContext(),
        )
        assert result["risk"] == "medium"

    @pytest.mark.asyncio
    async def test_risk_medium_when_five_or_more_callers(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            get_callers=AsyncMock(
                return_value=[
                    {"name": f"fn{i}", "path": "/src/f.py", "line_number": i}
                    for i in range(5)
                ]
            ),
            get_callees=AsyncMock(return_value=[]),
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="popular_fn", operations=[CGCOp.get_relationships]),
            WorkflowContext(),
        )
        assert result["risk"] == "medium"

    @pytest.mark.asyncio
    async def test_find_tests_filters_to_test_paths(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            find_code=AsyncMock(
                return_value=[
                    {"name": "RetryPrimitive", "path": "/src/retry.py", "line_number": 1, "kind": "Class"},
                    {"name": "test_retry", "path": "/tests/test_retry.py", "line_number": 10, "kind": "Function"},
                ]
            ),
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="RetryPrimitive", operations=[CGCOp.find_tests]),
            WorkflowContext(),
        )
        assert result["related_tests"] == ["/tests/test_retry.py"]

    @pytest.mark.asyncio
    async def test_raw_cypher_populates_summary(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            execute_cypher=AsyncMock(return_value=[{"values": ["foo", "/bar.py"]}])
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(
                target="",
                operations=[CGCOp.raw_cypher],
                cypher="MATCH (f:Function) RETURN f.name, f.path LIMIT 1",
            ),
            WorkflowContext(),
        )
        assert result["cgc_available"] is True
        assert len(result["summary"]) > 0

    @pytest.mark.asyncio
    async def test_multiple_ops_in_one_call(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            get_complexity=AsyncMock(return_value=7.0),
            get_callers=AsyncMock(return_value=[]),
            get_callees=AsyncMock(return_value=[]),
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(
                target="fn",
                operations=[CGCOp.get_relationships, CGCOp.get_complexity],
            ),
            WorkflowContext(),
        )
        assert result["complexity"] == 7.0
        assert result["risk"] == "medium"
        client.get_callers.assert_called_once()
        client.get_complexity.assert_called_once()

    @pytest.mark.asyncio
    async def test_otel_span_emitted_with_correct_attributes(self) -> None:
        from unittest.mock import MagicMock, patch

        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            get_callers=AsyncMock(return_value=[]),
            get_callees=AsyncMock(return_value=[]),
        )
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

        prim = CodeGraphPrimitive(cgc_client=client)
        prim._tracer = mock_tracer  # type: ignore[assignment]

        await prim.execute(
            CodeGraphQuery(target="my_fn", operations=[CGCOp.get_relationships]),
            WorkflowContext(),
        )

        mock_tracer.start_as_current_span.assert_called_once_with("cgc.orient")
        set_attr_calls = {call.args[0]: call.args[1] for call in mock_span.set_attribute.call_args_list}
        assert set_attr_calls["target"] == "my_fn"
        assert set_attr_calls["operations"] == ["get_relationships"]
        assert set_attr_calls["risk"] in ("low", "medium", "high")
        assert set_attr_calls["cgc_available"] is True


class TestCodeGraphPrimitiveDegradation:
    @pytest.mark.asyncio
    async def test_cgc_unreachable_returns_graceful_report(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client()
        client.is_reachable = MagicMock(return_value=False)
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="foo", operations=[CGCOp.get_relationships]),
            WorkflowContext(),
        )
        assert result["cgc_available"] is False
        assert result["risk"] == "low"
        assert "unavailable" in result["summary"].lower()
        client.get_callers.assert_not_called()

    @pytest.mark.asyncio
    async def test_cgc_exception_returns_graceful_report(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            get_callers=AsyncMock(side_effect=Exception("connection lost")),
            get_callees=AsyncMock(return_value=[]),
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="foo", operations=[CGCOp.get_relationships]),
            WorkflowContext(),
        )
        assert result["cgc_available"] is False

    @pytest.mark.asyncio
    async def test_depth_over_5_is_clamped_not_raised(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            get_callers=AsyncMock(return_value=[]),
            get_callees=AsyncMock(return_value=[]),
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        # Should not raise, should succeed
        result = await prim.execute(
            CodeGraphQuery(target="fn", operations=[CGCOp.get_relationships], depth=99),
            WorkflowContext(),
        )
        assert "risk" in result


def test_codegraphprimitive_exported_from_primitives_package() -> None:
    from ttadev.primitives import CodeGraphPrimitive

    assert CodeGraphPrimitive is not None
```

- [ ] **Step 2: Run to confirm they fail**

```bash
uv run python -m pytest tests/primitives/code_graph/test_primitive.py -v
```
Expected: `ImportError` (primitive.py doesn't exist yet)

- [ ] **Step 3: Create `ttadev/primitives/code_graph/primitive.py`**

```python
"""CodeGraphPrimitive — typed, instrumented Orient step for the DevelopmentCycle loop.

Queries CGC's FalkorDB graph to understand what a target function/class touches
and what touches it. Degrades gracefully when FalkorDB is unreachable.
"""

from __future__ import annotations

import logging
from contextlib import nullcontext
from typing import Any

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.observability import InstrumentedPrimitive

from .client import FalkorDBClient
from .types import CGCOp, CodeGraphQuery, ImpactReport

logger = logging.getLogger(__name__)

_MAX_DEPTH = 5


# ── Helpers ───────────────────────────────────────────────────────────────────


def _derive_risk(complexity: float, callers: list[str]) -> str:
    if complexity >= 10:
        return "high"
    if complexity >= 5 or len(callers) >= 5:
        return "medium"
    return "low"


def _format_location(name: str, path: str | None, line: int | None) -> str:
    if path and line:
        return f"{name} ({path}:{line})"
    if path:
        return f"{name} ({path})"
    return name


def _is_test_path(path: str | None) -> bool:
    if not path:
        return False
    return "/test" in path or path.split("/")[-1].startswith("test_")


def _build_summary(
    target: str,
    callers: list[str],
    deps: list[str],
    tests: list[str],
    complexity: float,
    risk: str,
) -> str:
    parts = [f"`{target}`: risk={risk}, complexity={complexity:.1f}."]
    if callers:
        preview = ", ".join(callers[:3])
        suffix = "..." if len(callers) > 3 else ""
        parts.append(f"Called by {len(callers)} function(s): {preview}{suffix}.")
    if deps:
        parts.append(f"Calls {len(deps)} function(s).")
    if tests:
        names = ", ".join(t.split("/")[-1] for t in tests[:2])
        parts.append(f"Covered by {len(tests)} test file(s): {names}.")
    else:
        parts.append("No test coverage found.")
    return " ".join(parts)


def _empty_report(target: str, reason: str) -> ImpactReport:
    return ImpactReport(
        target=target,
        callers=[],
        dependencies=[],
        related_tests=[],
        complexity=0.0,
        risk="low",
        summary=reason,
        cgc_available=False,
    )


# ── Primitive ─────────────────────────────────────────────────────────────────


class CodeGraphPrimitive(InstrumentedPrimitive[CodeGraphQuery, ImpactReport]):
    """Orient step: query CGC to understand what code exists and what will change.

    Queries FalkorDB directly via Unix socket using the ``falkordb`` Python package.
    Degrades gracefully if FalkorDB is unreachable — returns an empty ImpactReport,
    never raises.

    Example::

        graph = CodeGraphPrimitive()
        report = await graph.execute(
            CodeGraphQuery(
                target="RetryPrimitive._execute_impl",
                operations=[CGCOp.get_relationships, CGCOp.find_tests, CGCOp.get_complexity],
            ),
            WorkflowContext(),
        )
        # report["risk"] in ("low", "medium", "high")
        # report["related_tests"] — list of test file paths
    """

    def __init__(
        self,
        cgc_client: FalkorDBClient | None = None,
        repo_path: str | None = None,
    ) -> None:
        super().__init__(name="CodeGraphPrimitive")
        self._client = cgc_client or FalkorDBClient()
        self._repo_path = repo_path

    async def _execute_impl(
        self, input_data: CodeGraphQuery, context: WorkflowContext
    ) -> ImpactReport:
        target: str = input_data.get("target", "")
        operations: list[CGCOp] = input_data.get("operations", [])
        requested_depth: int = input_data.get("depth", 2)
        depth = min(requested_depth, _MAX_DEPTH)
        cypher: str = input_data.get("cypher", "")
        repo_path: str | None = input_data.get("repo_path") or self._repo_path

        if requested_depth > _MAX_DEPTH:
            logger.warning("depth clamped to %d (requested %d)", _MAX_DEPTH, requested_depth)

        # ── Validation ────────────────────────────────────────────────────────
        if not operations:
            return _empty_report(target, f"No operations requested for `{target}`")
        if not target and CGCOp.raw_cypher not in operations:
            raise ValueError("target is required for non-cypher operations")
        if CGCOp.raw_cypher in operations and not cypher:
            raise ValueError("cypher query string is required for CGCOp.raw_cypher")

        # ── Availability check ────────────────────────────────────────────────
        if not self._client.is_reachable():
            return _empty_report(target, "CGC unavailable — orient step skipped")

        # ── Execute operations ────────────────────────────────────────────────
        span_cm: Any = (
            self._tracer.start_as_current_span("cgc.orient")
            if self._tracer
            else nullcontext()
        )
        with span_cm as span:
            try:
                callers: list[str] = []
                deps: list[str] = []
                tests: list[str] = []
                complexity: float = 0.0
                raw_result: str = ""

                for op in operations:
                    if op == CGCOp.find_code:
                        await self._client.find_code(target, repo_path)

                    elif op == CGCOp.get_relationships:
                        caller_rows = await self._client.get_callers(target, repo_path)
                        callers = [
                            _format_location(r["name"], r.get("path"), r.get("line_number"))
                            for r in caller_rows
                        ]
                        dep_rows = await self._client.get_callees(target, repo_path)
                        deps = [
                            _format_location(r["name"], r.get("path"), r.get("line_number"))
                            for r in dep_rows
                        ]

                    elif op == CGCOp.get_complexity:
                        complexity = await self._client.get_complexity(target, repo_path)

                    elif op == CGCOp.find_tests:
                        code_results = await self._client.find_code(target, None)
                        seen: set[str] = set()
                        for r in code_results:
                            p = r.get("path", "")
                            if _is_test_path(p) and p not in seen:
                                tests.append(p)
                                seen.add(p)

                    elif op == CGCOp.raw_cypher:
                        rows = await self._client.execute_cypher(cypher)
                        raw_result = "\n".join(str(r["values"]) for r in rows[:50])

                risk = _derive_risk(complexity, callers)

                only_raw = operations == [CGCOp.raw_cypher]
                summary = (
                    raw_result if only_raw else
                    _build_summary(target, callers, deps, tests, complexity, risk)
                )

                if span is not None:
                    span.set_attribute("target", target)
                    span.set_attribute("operations", [op.value for op in operations])
                    span.set_attribute("risk", risk)
                    span.set_attribute("cgc_available", True)

                return ImpactReport(
                    target=target,
                    callers=callers,
                    dependencies=deps,
                    related_tests=tests,
                    complexity=complexity,
                    risk=risk,
                    summary=summary,
                    cgc_available=True,
                )

            except (ValueError, TypeError):
                raise  # validation errors bubble up
            except Exception as exc:
                logger.warning("CGC query failed for target=%r: %s", target, exc)
                return _empty_report(target, f"CGC unavailable: {exc}")
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
uv run python -m pytest tests/primitives/code_graph/test_primitive.py -v
```
Expected: all `PASSED` (except `test_codegraphprimitive_exported_from_primitives_package` which will fail until Task 6)

- [ ] **Step 5: Commit**

```bash
git add ttadev/primitives/code_graph/primitive.py tests/primitives/code_graph/test_primitive.py
git commit -m "feat(code_graph): add CodeGraphPrimitive with 5-op dispatch and graceful degradation"
```

---

## Task 6: Package exports and final verification

**Files:**
- Modify: `ttadev/primitives/code_graph/__init__.py`
- Modify: `ttadev/primitives/__init__.py`

- [ ] **Step 1: Update `ttadev/primitives/code_graph/__init__.py`**

```python
"""CodeGraphPrimitive — typed, instrumented CGC orient step."""

from .client import FalkorDBClient
from .primitive import CodeGraphPrimitive
from .types import CGCOp, CodeGraphQuery, ImpactReport

__all__ = [
    "CodeGraphPrimitive",
    "FalkorDBClient",
    "CGCOp",
    "CodeGraphQuery",
    "ImpactReport",
]
```

- [ ] **Step 2: Add exports to `ttadev/primitives/__init__.py`**

In `ttadev/primitives/__init__.py`, add after the `# ── Core: testing` block and before `__all__ = [`:

```python
# ── Code graph (CGC / FalkorDB) ──────────────────────────────────────────────
from .code_graph import CGCOp, CodeGraphPrimitive, CodeGraphQuery, ImpactReport
```

And add to the `__all__` list:
```python
    # Code graph primitives
    "CodeGraphPrimitive",
    "CodeGraphQuery",
    "ImpactReport",
    "CGCOp",
```

- [ ] **Step 3: Run the full test suite**

```bash
uv run python -m pytest tests/primitives/code_graph/ -v
```
Expected: all `PASSED`

- [ ] **Step 4: Verify the export works**

```bash
uv run python -c "from ttadev.primitives import CodeGraphPrimitive, CGCOp, CodeGraphQuery, ImpactReport; print('OK', CodeGraphPrimitive)"
```
Expected: `OK <class 'ttadev.primitives.code_graph.primitive.CodeGraphPrimitive'>`

- [ ] **Step 5: Run full project test suite to confirm no regressions**

```bash
uv run python -m pytest -q --tb=short -m "not integration and not slow and not external"
```
Expected: all `PASSED` (same count as before + new tests)

- [ ] **Step 6: Commit**

```bash
git add ttadev/primitives/code_graph/__init__.py ttadev/primitives/__init__.py
git commit -m "feat(code_graph): export CodeGraphPrimitive from ttadev.primitives"
```

- [ ] **Step 7: Retain to Hindsight**

POST to `http://localhost:8888/v1/default/banks/tta-dev/memories`:
```json
{
  "items": [{
    "content": "[type: pattern] CodeGraphPrimitive (ttadev/primitives/code_graph/) — Phase 2a complete. FalkorDBClient connects via Unix socket ~/.codegraphcontext/falkordb.sock, graph 'codegraph'. Five ops: find_code/get_relationships/get_complexity/find_tests/raw_cypher. Degrades gracefully when FalkorDB unreachable (returns empty ImpactReport, never raises). Schema smoke test: tests/primitives/code_graph/test_schema_smoke.py (@pytest.mark.integration — run manually after CGC upgrades). Exported from ttadev.primitives as CodeGraphPrimitive, CGCOp, CodeGraphQuery, ImpactReport."
  }]
}
```

---

## What comes next (out of scope for this plan)

| Phase | First step | Key deliverable |
|---|---|---|
| **Phase 2b** | `/specify AgentMemory` | `ttadev/primitives/memory/` + AgentPrimitive integration |
| **Phase 3** | `/specify DevelopmentCycle` | `ttadev/workflows/development_cycle.py` |
| **E2B templates** | Research task | Custom E2B template with TTA.dev deps pre-installed |
