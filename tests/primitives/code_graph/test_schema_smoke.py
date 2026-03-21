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
@pytest.mark.asyncio
async def test_expected_node_labels_exist(live_client: FalkorDBClient) -> None:
    """CALLS, CONTAINS, IMPORTS, INHERITS must exist."""
    rows = await live_client.execute_cypher("CALL db.labels()")
    labels = {r["values"][0] for r in rows}
    assert "Function" in labels, f"Missing 'Function' label. Got: {labels}"
    assert "Class" in labels, f"Missing 'Class' label. Got: {labels}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_function_has_expected_properties(live_client: FalkorDBClient) -> None:
    """Function nodes must have name, path, cyclomatic_complexity."""
    rows = await live_client.execute_cypher(
        "MATCH (f:Function) WHERE f.cyclomatic_complexity IS NOT NULL "
        "RETURN f.name, f.path, f.cyclomatic_complexity LIMIT 1"
    )
    assert rows, "No Function nodes with cyclomatic_complexity found"
    vals = rows[0]["values"]
    assert vals[0] is not None, "f.name is null"
    assert vals[2] is not None, "f.cyclomatic_complexity is null"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_calls_relationship_exists(live_client: FalkorDBClient) -> None:
    """CALLS relationship must exist in the graph."""
    rows = await live_client.execute_cypher("CALL db.relationshipTypes()")
    rel_types = {r["values"][0] for r in rows}
    assert "CALLS" in rel_types, f"Missing CALLS relationship. Got: {rel_types}"
    assert "IMPORTS" in rel_types, f"Missing IMPORTS relationship. Got: {rel_types}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_code_returns_results_for_known_symbol(live_client: FalkorDBClient) -> None:
    """find_code('InstrumentedPrimitive') must return at least one result."""
    results = await live_client.find_code("InstrumentedPrimitive")
    assert results, "find_code returned no results for 'InstrumentedPrimitive'"
    assert any(r["name"] == "InstrumentedPrimitive" for r in results)
