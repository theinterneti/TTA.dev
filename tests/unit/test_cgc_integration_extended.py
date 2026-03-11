"""Unit tests for CGCIntegration extensions — Task 5.

CGC MCP server is mocked in all tests (no real process spawned).
is_available() now uses a direct FalkorDB socket ping (_falkordb_reachable)
rather than spawning a subprocess, so tests mock that helper instead.
"""

from unittest.mock import AsyncMock, patch

import pytest

import ttadev.observability.cgc_integration as cgc_module
from ttadev.observability.cgc_integration import CGCIntegration


@pytest.fixture
def cgc() -> CGCIntegration:
    return CGCIntegration()


@pytest.mark.asyncio
async def test_is_available_returns_false_on_timeout(cgc: CGCIntegration) -> None:
    with patch.object(cgc_module, "_falkordb_reachable", return_value=False):
        result = await cgc.is_available()
    assert result is False


@pytest.mark.asyncio
async def test_is_available_returns_false_on_connection_error(cgc: CGCIntegration) -> None:
    with patch.object(cgc_module, "_falkordb_reachable", side_effect=OSError("refused")):
        result = await cgc.is_available()
    assert result is False


@pytest.mark.asyncio
async def test_is_available_returns_false_on_any_exception(cgc: CGCIntegration) -> None:
    with patch.object(cgc_module, "_falkordb_reachable", side_effect=RuntimeError("boom")):
        result = await cgc.is_available()
    assert result is False


@pytest.mark.asyncio
async def test_is_available_returns_true_on_success(cgc: CGCIntegration) -> None:
    with patch.object(cgc_module, "_falkordb_reachable", return_value=True):
        result = await cgc.is_available()
    assert result is True


@pytest.mark.asyncio
async def test_is_available_uses_socket_ping(cgc: CGCIntegration) -> None:
    """is_available() delegates to _falkordb_reachable (fast socket check)."""
    calls: list[bool] = []

    def mock_ping() -> bool:
        calls.append(True)
        return True

    with patch.object(cgc_module, "_falkordb_reachable", side_effect=mock_ping):
        await cgc.is_available()

    assert calls == [True]  # exactly one ping, no subprocess spawned


@pytest.mark.asyncio
async def test_get_live_nodes_returns_matching_nodes(cgc: CGCIntegration) -> None:
    """Nodes matching primitive names are returned."""
    with patch.object(
        cgc,
        "find_code",
        new_callable=AsyncMock,
        return_value=[
            {"name": "RetryPrimitive", "file": "primitives/retry.py"},
            {"name": "OtherClass", "file": "other.py"},
        ],
    ):
        nodes = await cgc.get_live_nodes(["RetryPrimitive"])
    assert len(nodes) >= 1
    assert any(n["name"] == "RetryPrimitive" for n in nodes)


@pytest.mark.asyncio
async def test_get_live_nodes_returns_empty_on_unavailable(cgc: CGCIntegration) -> None:
    """Returns empty list (no crash) when CGC is unavailable."""
    with patch.object(
        cgc, "find_code", new_callable=AsyncMock, side_effect=ConnectionError("cgc down")
    ):
        nodes = await cgc.get_live_nodes(["RetryPrimitive"])
    assert nodes == []


@pytest.mark.asyncio
async def test_get_live_nodes_empty_input(cgc: CGCIntegration) -> None:
    nodes = await cgc.get_live_nodes([])
    assert nodes == []
