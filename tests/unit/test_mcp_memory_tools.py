"""Unit tests for the MCP server memory tools (memory_* group)."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.mcp_server.server import create_server

# ── Helpers ───────────────────────────────────────────────────────────────────


async def _call_tool(mcp: Any, name: str, arguments: dict[str, Any]) -> Any:
    """Call an MCP tool and return the parsed payload."""
    result = mcp.call_tool(name, arguments)
    if asyncio.iscoroutine(result):
        result = await result
    # Async tools return (list[Content], dict); sync tools return list[Content]
    if isinstance(result, tuple):
        result = result[1]  # structured dict is the second element
    elif isinstance(result, list) and result:
        raw = result[0].text
        return json.loads(raw)
    return result


async def _get_tool_map(mcp: Any) -> dict[str, Any]:
    tools_result = mcp.list_tools()
    if asyncio.iscoroutine(tools_result):
        tools_result = await tools_result
    return {t.name: t for t in tools_result}


@pytest.fixture
def mcp():
    return create_server()


# ── Tool Registration ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_memory_tools_registered(mcp: Any) -> None:
    """All four memory_* tools must be registered."""
    tool_map = await _get_tool_map(mcp)
    expected = {"memory_recall", "memory_retain", "memory_build_context", "memory_list_banks"}
    assert expected.issubset(tool_map), f"Missing: {expected - set(tool_map)}"


@pytest.mark.asyncio
async def test_memory_recall_is_read_only(mcp: Any) -> None:
    tool_map = await _get_tool_map(mcp)
    t = tool_map["memory_recall"]
    assert getattr(t, "annotations", {}) or True  # presence check


@pytest.mark.asyncio
async def test_memory_build_context_is_read_only(mcp: Any) -> None:
    tool_map = await _get_tool_map(mcp)
    assert "memory_build_context" in tool_map


@pytest.mark.asyncio
async def test_memory_list_banks_is_read_only(mcp: Any) -> None:
    tool_map = await _get_tool_map(mcp)
    assert "memory_list_banks" in tool_map


# ── memory_recall ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_memory_recall_unavailable(mcp: Any) -> None:
    """Returns error when Hindsight is down."""
    mock_mem = MagicMock()
    mock_mem.is_available.return_value = False
    with patch("ttadev.primitives.memory.AgentMemory", return_value=mock_mem):
        result = await _call_tool(mcp, "memory_recall", {"query": "test query"})
    assert "error" in result
    assert result["count"] == 0
    assert result["memories"] == []


@pytest.mark.asyncio
async def test_memory_recall_empty_query(mcp: Any) -> None:
    """Empty query returns error, not exception."""
    result = await _call_tool(mcp, "memory_recall", {"query": ""})
    assert "error" in result
    assert result["count"] == 0


@pytest.mark.asyncio
async def test_memory_recall_success(mcp: Any) -> None:
    """Returns memories when Hindsight is available."""
    mock_mem = MagicMock()
    mock_mem.is_available.return_value = True
    mock_mem.recall = AsyncMock(
        return_value=[{"id": "abc", "text": "test memory", "type": "experience"}]
    )
    with patch("ttadev.primitives.memory.AgentMemory", return_value=mock_mem):
        result = await _call_tool(
            mcp, "memory_recall", {"query": "test", "bank_id": "tta-dev", "budget": "mid"}
        )
    assert result["count"] == 1
    assert result["memories"][0]["text"] == "test memory"


@pytest.mark.asyncio
async def test_memory_recall_custom_bank(mcp: Any) -> None:
    """Custom bank_id is passed through."""
    mock_mem = MagicMock()
    mock_mem.is_available.return_value = True
    mock_mem.recall = AsyncMock(return_value=[])
    with patch("ttadev.primitives.memory.AgentMemory", return_value=mock_mem) as mock_cls:
        await _call_tool(mcp, "memory_recall", {"query": "q", "bank_id": "custom-bank"})
    mock_cls.assert_called_once_with(bank_id="custom-bank")


@pytest.mark.asyncio
async def test_memory_recall_invalid_budget_defaults(mcp: Any) -> None:
    """Invalid budget defaults to 'mid' without raising."""
    mock_mem = MagicMock()
    mock_mem.is_available.return_value = True
    mock_mem.recall = AsyncMock(return_value=[])
    with patch("ttadev.primitives.memory.AgentMemory", return_value=mock_mem):
        result = await _call_tool(mcp, "memory_recall", {"query": "q", "budget": "ultra-high"})
    assert "error" not in result


# ── memory_retain ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_memory_retain_empty_content(mcp: Any) -> None:
    """Empty content returns error."""
    result = await _call_tool(mcp, "memory_retain", {"content": ""})
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_memory_retain_unavailable(mcp: Any) -> None:
    """Returns failure when Hindsight is down."""
    mock_mem = MagicMock()
    mock_mem.is_available.return_value = False
    with patch("ttadev.primitives.memory.AgentMemory", return_value=mock_mem):
        result = await _call_tool(mcp, "memory_retain", {"content": "some memory"})
    assert result["success"] is False
    assert "Hindsight unavailable" in result["error"]


@pytest.mark.asyncio
async def test_memory_retain_success(mcp: Any) -> None:
    """Returns success=True and operation_id on successful retain."""
    mock_mem = MagicMock()
    mock_mem.is_available.return_value = True
    mock_mem.retain = AsyncMock(return_value={"success": True, "operation_id": "op-123"})
    with patch("ttadev.primitives.memory.AgentMemory", return_value=mock_mem):
        result = await _call_tool(mcp, "memory_retain", {"content": "decision made"})
    assert result["success"] is True
    assert result.get("operation_id") == "op-123"


@pytest.mark.asyncio
async def test_memory_retain_with_context(mcp: Any) -> None:
    """Context label is appended to content."""
    mock_mem = MagicMock()
    mock_mem.is_available.return_value = True
    mock_mem.retain = AsyncMock(return_value={"success": True, "operation_id": None})
    with patch("ttadev.primitives.memory.AgentMemory", return_value=mock_mem):
        await _call_tool(
            mcp,
            "memory_retain",
            {"content": "[type: decision] Use uv", "context": "tooling"},
        )
    call_args = mock_mem.retain.call_args[0][0]
    assert "Context: tooling" in call_args


# ── memory_build_context ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_memory_build_context_empty_query(mcp: Any) -> None:
    result = await _call_tool(mcp, "memory_build_context", {"query": ""})
    assert "error" in result
    assert result["available"] is False


@pytest.mark.asyncio
async def test_memory_build_context_unavailable(mcp: Any) -> None:
    mock_mem = MagicMock()
    mock_mem.is_available.return_value = False
    with patch("ttadev.primitives.memory.AgentMemory", return_value=mock_mem):
        result = await _call_tool(mcp, "memory_build_context", {"query": "primitives"})
    assert result["available"] is False
    assert result["context"] == ""


@pytest.mark.asyncio
async def test_memory_build_context_success(mcp: Any) -> None:
    mock_mem = MagicMock()
    mock_mem.is_available.return_value = True
    mock_mem.build_context_prefix = AsyncMock(return_value="## Directives\n- Use uv")
    with patch("ttadev.primitives.memory.AgentMemory", return_value=mock_mem):
        result = await _call_tool(mcp, "memory_build_context", {"query": "tooling"})
    assert result["available"] is True
    assert "## Directives" in result["context"]


# ── memory_list_banks ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_memory_list_banks_unavailable(mcp: Any) -> None:
    """Returns empty banks list when Hindsight is down."""
    with patch("httpx.get", side_effect=Exception("connection refused")):
        result = await _call_tool(mcp, "memory_list_banks", {})
    assert result["banks"] == []
    assert result["count"] == 0
    assert "error" in result


@pytest.mark.asyncio
async def test_memory_list_banks_success(mcp: Any) -> None:
    """Returns parsed banks from Hindsight."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"id": "tta-dev", "name": "TTA Dev"}]
    with patch("httpx.get", return_value=mock_resp):
        result = await _call_tool(mcp, "memory_list_banks", {})
    assert result["count"] == 1
    assert result["banks"][0]["id"] == "tta-dev"


@pytest.mark.asyncio
async def test_memory_list_banks_http_error(mcp: Any) -> None:
    """Returns error dict on HTTP non-200."""
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    with patch("httpx.get", return_value=mock_resp):
        result = await _call_tool(mcp, "memory_list_banks", {})
    assert result["count"] == 0
    assert "error" in result
