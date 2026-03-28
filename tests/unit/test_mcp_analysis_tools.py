"""Unit tests for MCP analysis tools: code size guard and tool annotations."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from ttadev.primitives.mcp_server.server import _MAX_CODE_CHARS, _check_code_size, create_server

# ── _check_code_size unit tests ───────────────────────────────────────────────


def test_check_code_size_allows_small_input() -> None:
    assert _check_code_size("x = 1") is None


def test_check_code_size_allows_input_at_limit() -> None:
    assert _check_code_size("x" * _MAX_CODE_CHARS) is None


def test_check_code_size_blocks_oversized_input() -> None:
    big = "x" * (_MAX_CODE_CHARS + 1)
    result = _check_code_size(big)
    assert result is not None
    assert "error" in result
    assert "25,000" in result["error"]


# ── MCP tool invocation helpers ───────────────────────────────────────────────


async def _call_tool(mcp: Any, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call an MCP tool and return its structured payload (dict return types only)."""
    result = mcp.call_tool(name, arguments)
    if asyncio.iscoroutine(result):
        result = await result
    assert isinstance(result, tuple)
    _, payload = result
    assert isinstance(payload, dict)
    return payload


# ── Code size guard via MCP tool boundary ─────────────────────────────────────


@pytest.mark.asyncio
async def test_analyze_code_size_guard_returns_error_dict() -> None:
    """analyze_code returns an error dict when code exceeds the character limit."""
    mcp = create_server()
    big_code = "x = 1\n" * (_MAX_CODE_CHARS // 6 + 1)
    result = await _call_tool(mcp, "analyze_code", {"code": big_code})
    assert "error" in result


@pytest.mark.asyncio
async def test_transform_code_size_guard_returns_error_dict() -> None:
    """transform_code returns an error dict when code exceeds the character limit."""
    mcp = create_server()
    big_code = "x = 1\n" * (_MAX_CODE_CHARS // 6 + 1)
    result = await _call_tool(
        mcp, "transform_code", {"code": big_code, "primitive": "RetryPrimitive"}
    )
    assert "error" in result


@pytest.mark.asyncio
async def test_suggest_fixes_size_guard_returns_error_dict() -> None:
    """suggest_fixes returns an error dict when code exceeds the character limit."""
    mcp = create_server()
    big_code = "x = 1\n" * (_MAX_CODE_CHARS // 6 + 1)
    result = await _call_tool(mcp, "suggest_fixes", {"code": big_code})
    assert "error" in result


@pytest.mark.asyncio
async def test_detect_anti_patterns_size_guard_returns_error_dict() -> None:
    """detect_anti_patterns returns an error dict when code exceeds the character limit."""
    mcp = create_server()
    big_code = "x = 1\n" * (_MAX_CODE_CHARS // 6 + 1)
    result = await _call_tool(mcp, "detect_anti_patterns", {"code": big_code})
    assert "error" in result


@pytest.mark.asyncio
async def test_analyze_and_fix_size_guard_returns_error_dict() -> None:
    """analyze_and_fix returns an error dict when code exceeds the character limit."""
    mcp = create_server()
    big_code = "x = 1\n" * (_MAX_CODE_CHARS // 6 + 1)
    result = await _call_tool(mcp, "analyze_and_fix", {"code": big_code})
    assert "error" in result


@pytest.mark.asyncio
async def test_rewrite_code_size_guard_returns_error_dict() -> None:
    """rewrite_code returns an error dict when code exceeds the character limit."""
    mcp = create_server()
    big_code = "x = 1\n" * (_MAX_CODE_CHARS // 6 + 1)
    result = await _call_tool(mcp, "rewrite_code", {"code": big_code})
    assert "error" in result


# ── Tool annotation tests ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analysis_tools_carry_read_only_annotation() -> None:
    """Analysis tools expose readOnlyHint=True in their MCP metadata."""
    mcp = create_server()
    tools_result = mcp.list_tools()
    if asyncio.iscoroutine(tools_result):
        tools_result = await tools_result
    tool_map = {t.name: t for t in tools_result}

    read_only_tools = [
        "analyze_code",
        "get_primitive_info",
        "list_primitives",
        "search_templates",
        "get_composition_example",
        "suggest_fixes",
        "detect_anti_patterns",
        "transform_code",
        "analyze_and_fix",
        "rewrite_code",
    ]
    for name in read_only_tools:
        ann = tool_map[name].annotations
        assert ann is not None, f"{name} has no annotations"
        assert ann.readOnlyHint is True, f"{name} should have readOnlyHint=True"
