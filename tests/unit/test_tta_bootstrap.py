"""Unit tests for the tta_bootstrap MCP orientation tool (GitHub issue #315).

Tests that tta_bootstrap returns a well-formed orientation package including
primitives catalog, MCP tool index, quick-start guide, provider status, and
optional task-hint ranking.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from ttadev.primitives.mcp_server.server import create_server

# ── Helpers ───────────────────────────────────────────────────────────────────


async def _call_bootstrap(mcp: Any, **kwargs: Any) -> dict[str, Any]:
    """Call tta_bootstrap via the MCP interface and return its result dict."""
    result = mcp.call_tool("tta_bootstrap", kwargs)
    if asyncio.iscoroutine(result):
        result = await result
    # FastMCP returns a (content_type, payload) tuple
    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    _, payload = result
    assert isinstance(payload, dict), f"Expected dict payload, got {type(payload)}"
    return payload


@pytest.fixture(scope="module")
def mcp() -> Any:
    """Shared MCP server instance for all bootstrap tests."""
    return create_server()


@pytest.fixture(scope="module")
def bootstrap_result(mcp: Any) -> dict[str, Any]:
    """Cached default tta_bootstrap() result for cheap assertions."""
    return asyncio.run(_call_bootstrap(mcp))


# ── Schema / key presence ─────────────────────────────────────────────────────


class TestBootstrapRequiredKeys:
    """tta_bootstrap() must return all required top-level keys."""

    REQUIRED_KEYS: frozenset[str] = frozenset(
        {
            "version",
            "agent_id",
            "primitives",
            "mcp_tools",
            "quick_start",
            "patterns",
            "provider_status",
            "top_primitives_for_task",
        }
    )

    def test_all_required_keys_present(self, bootstrap_result: dict[str, Any]) -> None:
        """All specified keys exist in the response."""
        for key in self.REQUIRED_KEYS:
            assert key in bootstrap_result, f"Missing key: {key!r}"

    def test_version_is_string(self, bootstrap_result: dict[str, Any]) -> None:
        assert isinstance(bootstrap_result["version"], str)
        assert bootstrap_result["version"]  # non-empty

    def test_agent_id_defaults_to_empty_string(self, bootstrap_result: dict[str, Any]) -> None:
        assert bootstrap_result["agent_id"] == ""

    def test_agent_id_echoed_when_provided(self, mcp: Any) -> None:
        result = asyncio.run(_call_bootstrap(mcp, agent_id="test-agent-42"))
        assert result["agent_id"] == "test-agent-42"

    def test_quick_start_is_non_empty_string(self, bootstrap_result: dict[str, Any]) -> None:
        assert isinstance(bootstrap_result["quick_start"], str)
        assert len(bootstrap_result["quick_start"]) > 50

    def test_patterns_is_non_empty_string(self, bootstrap_result: dict[str, Any]) -> None:
        assert isinstance(bootstrap_result["patterns"], str)
        assert len(bootstrap_result["patterns"]) > 20


# ── Primitives list ───────────────────────────────────────────────────────────


class TestBootstrapPrimitives:
    """primitives field: non-empty list with correct structure per entry."""

    REQUIRED_PRIMITIVE_KEYS: frozenset[str] = frozenset(
        {"name", "category", "when_to_use", "import"}
    )

    def test_primitives_is_non_empty_list(self, bootstrap_result: dict[str, Any]) -> None:
        assert isinstance(bootstrap_result["primitives"], list)
        assert len(bootstrap_result["primitives"]) > 0, "primitives list must not be empty"

    def test_primitives_capped_at_30(self, bootstrap_result: dict[str, Any]) -> None:
        assert len(bootstrap_result["primitives"]) <= 30

    def test_each_primitive_has_required_keys(self, bootstrap_result: dict[str, Any]) -> None:
        for prim in bootstrap_result["primitives"]:
            for key in self.REQUIRED_PRIMITIVE_KEYS:
                assert key in prim, f"Primitive {prim!r} missing key {key!r}"

    def test_each_primitive_name_is_non_empty_string(
        self, bootstrap_result: dict[str, Any]
    ) -> None:
        for prim in bootstrap_result["primitives"]:
            assert isinstance(prim["name"], str) and prim["name"]

    def test_each_primitive_import_starts_with_from(self, bootstrap_result: dict[str, Any]) -> None:
        for prim in bootstrap_result["primitives"]:
            assert prim["import"].startswith("from ttadev"), (
                f"Bad import for {prim['name']!r}: {prim['import']!r}"
            )

    def test_retry_primitive_present(self, bootstrap_result: dict[str, Any]) -> None:
        names = [p["name"] for p in bootstrap_result["primitives"]]
        assert "RetryPrimitive" in names, f"RetryPrimitive missing; got: {names}"

    def test_no_duplicate_primitive_names(self, bootstrap_result: dict[str, Any]) -> None:
        names = [p["name"] for p in bootstrap_result["primitives"]]
        assert len(names) == len(set(names)), f"Duplicate primitives: {names}"


# ── MCP tools index ───────────────────────────────────────────────────────────


class TestBootstrapMcpTools:
    """mcp_tools field: dict grouping tool names by domain."""

    def test_mcp_tools_is_dict(self, bootstrap_result: dict[str, Any]) -> None:
        assert isinstance(bootstrap_result["mcp_tools"], dict)

    def test_mcp_tools_is_non_empty(self, bootstrap_result: dict[str, Any]) -> None:
        assert len(bootstrap_result["mcp_tools"]) > 0

    def test_tta_bootstrap_in_orientation_group(self, bootstrap_result: dict[str, Any]) -> None:
        tools = bootstrap_result["mcp_tools"]
        assert "orientation" in tools, f"No 'orientation' group; keys: {list(tools)}"
        assert "tta_bootstrap" in tools["orientation"]

    def test_all_group_values_are_lists_of_strings(self, bootstrap_result: dict[str, Any]) -> None:
        for group, names in bootstrap_result["mcp_tools"].items():
            assert isinstance(names, list), f"Group {group!r} is not a list"
            for name in names:
                assert isinstance(name, str), f"Tool name {name!r} in {group!r} is not a string"

    def test_llm_tools_grouped(self, bootstrap_result: dict[str, Any]) -> None:
        """LLM-prefixed tools should appear in an 'llm' group."""
        tools = bootstrap_result["mcp_tools"]
        assert "llm" in tools, f"No 'llm' group; keys: {list(tools)}"
        assert len(tools["llm"]) > 0

    def test_control_tools_grouped(self, bootstrap_result: dict[str, Any]) -> None:
        """control_* tools should appear in a 'control' group."""
        tools = bootstrap_result["mcp_tools"]
        assert "control" in tools, f"No 'control' group; keys: {list(tools)}"
        assert len(tools["control"]) > 0


# ── Provider status ───────────────────────────────────────────────────────────


class TestBootstrapProviderStatus:
    """provider_status field: non-empty dict from llm_list_providers()."""

    def test_provider_status_is_dict(self, bootstrap_result: dict[str, Any]) -> None:
        assert isinstance(bootstrap_result["provider_status"], dict)

    def test_provider_status_is_non_empty(self, bootstrap_result: dict[str, Any]) -> None:
        assert len(bootstrap_result["provider_status"]) > 0, "provider_status must not be empty"

    def test_provider_status_has_providers_key(self, bootstrap_result: dict[str, Any]) -> None:
        ps = bootstrap_result["provider_status"]
        # Must have either a 'providers' list or an 'error' key
        assert "providers" in ps or "error" in ps


# ── Task-hint ranking ─────────────────────────────────────────────────────────


class TestBootstrapTaskHint:
    """top_primitives_for_task: ranked by relevance when task_hint given."""

    def test_no_hint_returns_empty_list(self, bootstrap_result: dict[str, Any]) -> None:
        """With no task_hint the top_primitives_for_task list is empty."""
        assert bootstrap_result["top_primitives_for_task"] == []

    @pytest.mark.asyncio
    async def test_retry_hint_surfaces_retry_primitive(self, mcp: Any) -> None:
        """task_hint mentioning 'retry' should rank RetryPrimitive in top 3."""
        result = await _call_bootstrap(mcp, task_hint="build a retry workflow")
        top = result["top_primitives_for_task"]
        assert isinstance(top, list)
        assert len(top) > 0, "top_primitives_for_task must not be empty when hint given"
        top_names = [p["name"] for p in top]
        assert "RetryPrimitive" in top_names, (
            f"Expected RetryPrimitive in top results for 'retry' hint; got {top_names}"
        )

    @pytest.mark.asyncio
    async def test_cache_hint_surfaces_cache_primitive(self, mcp: Any) -> None:
        """task_hint mentioning 'cache' should rank CachePrimitive in top 3."""
        result = await _call_bootstrap(mcp, task_hint="cache expensive database lookups")
        top = result["top_primitives_for_task"]
        top_names = [p["name"] for p in top]
        assert "CachePrimitive" in top_names, (
            f"Expected CachePrimitive for 'cache' hint; got {top_names}"
        )

    @pytest.mark.asyncio
    async def test_top_primitives_capped_at_3(self, mcp: Any) -> None:
        """top_primitives_for_task never exceeds 3 items."""
        result = await _call_bootstrap(mcp, task_hint="build retry cache timeout circuit breaker")
        assert len(result["top_primitives_for_task"]) <= 3

    @pytest.mark.asyncio
    async def test_top_primitives_have_required_keys(self, mcp: Any) -> None:
        """Each entry in top_primitives_for_task has the standard primitive keys."""
        result = await _call_bootstrap(mcp, task_hint="build a resilient parallel workflow")
        for prim in result["top_primitives_for_task"]:
            for key in ("name", "category", "when_to_use", "import"):
                assert key in prim, f"Top primitive missing key {key!r}: {prim!r}"


# ── Token / size budget ───────────────────────────────────────────────────────


class TestBootstrapSizeBudget:
    """Total serialized response must fit within 8000 characters."""

    def test_response_under_8000_chars(self, bootstrap_result: dict[str, Any]) -> None:
        serialized = json.dumps(bootstrap_result, default=str)
        assert len(serialized) < 8000, (
            f"Response is {len(serialized)} chars — exceeds 8000-char budget"
        )

    @pytest.mark.asyncio
    async def test_response_with_long_hint_under_8000_chars(self, mcp: Any) -> None:
        result = await _call_bootstrap(
            mcp,
            agent_id="budget-test-agent",
            task_hint="build a retry cache timeout parallel sequential workflow with circuit breaker",
        )
        serialized = json.dumps(result, default=str)
        assert len(serialized) < 8000, (
            f"Response with task_hint is {len(serialized)} chars — exceeds budget"
        )
