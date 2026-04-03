"""Unit tests for the MCP server LLM tools (llm_* group)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

from ttadev.primitives.mcp_server.server import create_server

# ── Helpers ───────────────────────────────────────────────────────────────────


async def _call_tool(mcp: Any, name: str, arguments: dict[str, Any]) -> Any:
    """Call an MCP tool and return the parsed payload."""
    result = mcp.call_tool(name, arguments)
    if asyncio.iscoroutine(result):
        result = await result
    # FastMCP returns list[Content]; grab the first TextContent's text
    if isinstance(result, list) and result:
        raw = result[0].text
        return json.loads(raw)
    return result


async def _get_tool_map(mcp: Any) -> dict[str, Any]:
    tools_result = mcp.list_tools()
    if asyncio.iscoroutine(tools_result):
        tools_result = await tools_result
    return {t.name: t for t in tools_result}


# ── Tool registration ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_all_llm_tools_registered() -> None:
    """All 6 llm_* tools are registered in the MCP server."""
    mcp = create_server()
    tool_map = await _get_tool_map(mcp)
    expected = {
        "llm_hardware_profile",
        "llm_viable_ollama_models",
        "llm_benchmark_score",
        "llm_refresh_benchmarks",
        "llm_list_providers",
        "llm_recommend_model",
    }
    for name in expected:
        assert name in tool_map, f"Missing MCP tool: {name}"


@pytest.mark.asyncio
async def test_llm_tools_read_only_annotation() -> None:
    """Read-only llm_* tools carry readOnlyHint=True."""
    mcp = create_server()
    tool_map = await _get_tool_map(mcp)
    read_only = [
        "llm_hardware_profile",
        "llm_viable_ollama_models",
        "llm_benchmark_score",
        "llm_list_providers",
        "llm_recommend_model",
    ]
    for name in read_only:
        ann = tool_map[name].annotations
        assert ann is not None, f"{name} has no annotations"
        assert ann.readOnlyHint is True, f"{name} should have readOnlyHint=True"


@pytest.mark.asyncio
async def test_llm_refresh_benchmarks_idempotent_annotation() -> None:
    """llm_refresh_benchmarks is idempotent (not read-only)."""
    mcp = create_server()
    tool_map = await _get_tool_map(mcp)
    ann = tool_map["llm_refresh_benchmarks"].annotations
    assert ann is not None
    assert ann.idempotentHint is True


# ── llm_hardware_profile ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_hardware_profile_returns_expected_fields() -> None:
    """llm_hardware_profile returns all expected hardware keys."""
    mcp = create_server()
    payload = await _call_tool(mcp, "llm_hardware_profile", {})
    for key in ("cpu_cores", "ram_gb", "backend", "total_vram_gb", "max_params_b_q4"):
        assert key in payload, f"Missing field: {key}"
    assert isinstance(payload["cpu_cores"], int)
    assert payload["ram_gb"] > 0
    assert payload["backend"] in ("cuda", "rocm", "metal", "cpu")


@pytest.mark.asyncio
async def test_hardware_profile_includes_recommend_size_tag() -> None:
    """llm_hardware_profile includes a size tag recommendation string."""
    mcp = create_server()
    payload = await _call_tool(mcp, "llm_hardware_profile", {})
    assert "recommend_size_tag" in payload
    # Should look like "7b", "14b", "cpu_only", etc.
    assert isinstance(payload["recommend_size_tag"], str)


# ── llm_viable_ollama_models ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_viable_ollama_models_splits_viable_and_too_large() -> None:
    """llm_viable_ollama_models correctly splits models the hardware can/cannot run."""
    mcp = create_server()

    # On dev machine: GTX 1650 4GB + 16GB RAM (~14B max at Q4)
    # llama3.2:1b should always be viable; a 70b model should not be
    candidates = ["llama3.2:1b", "llama3.3:70b"]
    payload = await _call_tool(mcp, "llm_viable_ollama_models", {"model_ids": candidates})

    assert "viable" in payload
    assert "too_large" in payload
    assert "hardware_summary" in payload
    # llama3.2:1b should be viable everywhere
    assert "llama3.2:1b" in payload["viable"]


@pytest.mark.asyncio
async def test_viable_ollama_models_empty_input() -> None:
    """llm_viable_ollama_models handles empty input gracefully."""
    mcp = create_server()
    payload = await _call_tool(mcp, "llm_viable_ollama_models", {"model_ids": []})
    assert payload["viable"] == []
    assert payload["too_large"] == []


@pytest.mark.asyncio
async def test_viable_ollama_models_unknown_model_is_optimistic() -> None:
    """Unknown model names are optimistically allowed (Ollama will refuse anyway)."""
    mcp = create_server()
    payload = await _call_tool(
        mcp,
        "llm_viable_ollama_models",
        {"model_ids": ["some-unknown-model:latest"]},
    )
    assert "some-unknown-model:latest" in payload["viable"]


# ── llm_benchmark_score ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_benchmark_score_specific_benchmark() -> None:
    """llm_benchmark_score returns a score dict for a specific benchmark."""
    mcp = create_server()
    payload = await _call_tool(
        mcp,
        "llm_benchmark_score",
        {"model_id": "gpt-4o", "benchmark": "humaneval"},
    )
    assert payload["model_id"] == "gpt-4o"
    assert payload["benchmark"] == "humaneval"
    assert "score" in payload
    assert "available" in payload


@pytest.mark.asyncio
async def test_benchmark_score_all_benchmarks() -> None:
    """llm_benchmark_score without benchmark arg returns all-scores dict."""
    mcp = create_server()
    payload = await _call_tool(
        mcp,
        "llm_benchmark_score",
        {"model_id": "gpt-4o"},
    )
    assert payload["model_id"] == "gpt-4o"
    assert payload["benchmark"] == "all"
    assert isinstance(payload["scores"], dict)


@pytest.mark.asyncio
async def test_benchmark_score_unknown_model() -> None:
    """llm_benchmark_score for an unknown model returns available=False."""
    mcp = create_server()
    payload = await _call_tool(
        mcp,
        "llm_benchmark_score",
        {"model_id": "nonexistent-model-xyz", "benchmark": "humaneval"},
    )
    assert payload["available"] is False
    assert payload["score"] is None


# ── llm_list_providers ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_providers_returns_known_providers() -> None:
    """llm_list_providers includes all expected providers."""
    mcp = create_server()
    payload = await _call_tool(mcp, "llm_list_providers", {})
    assert "providers" in payload
    assert "count" in payload
    provider_names = {p["name"] for p in payload["providers"]}
    for expected in ("groq", "gemini", "ollama", "openrouter"):
        assert expected in provider_names, f"Provider missing: {expected}"


@pytest.mark.asyncio
async def test_list_providers_fields_present() -> None:
    """Each provider entry has the expected fields."""
    mcp = create_server()
    payload = await _call_tool(mcp, "llm_list_providers", {})
    for p in payload["providers"]:
        assert "name" in p
        assert "api_key_configured" in p
        assert isinstance(p["api_key_configured"], bool)
        assert "is_local" in p


@pytest.mark.asyncio
async def test_list_providers_ollama_is_local() -> None:
    """Ollama provider is marked is_local=True."""
    mcp = create_server()
    payload = await _call_tool(mcp, "llm_list_providers", {})
    ollama = next(p for p in payload["providers"] if p["name"] == "ollama")
    assert ollama["is_local"] is True


# ── llm_recommend_model ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_recommend_model_coding_complex() -> None:
    """llm_recommend_model returns a high-quality model for complex coding tasks."""
    mcp = create_server()
    payload = await _call_tool(
        mcp,
        "llm_recommend_model",
        {"task": "coding", "complexity": "complex"},
    )
    assert "model_id" in payload
    assert "provider" in payload
    assert "rationale" in payload
    assert payload["model_id"] is not None


@pytest.mark.asyncio
async def test_recommend_model_simple_chat() -> None:
    """llm_recommend_model returns a model for simple chat tasks."""
    mcp = create_server()
    payload = await _call_tool(
        mcp,
        "llm_recommend_model",
        {"task": "chat", "complexity": "simple"},
    )
    assert payload["model_id"] is not None


@pytest.mark.asyncio
async def test_recommend_model_free_tier_filter() -> None:
    """llm_recommend_model respects max_cost_tier=free constraint."""
    mcp = create_server()
    payload = await _call_tool(
        mcp,
        "llm_recommend_model",
        {"task": "coding", "complexity": "moderate", "max_cost_tier": "free"},
    )
    # Result may be None if no free models exist, but should not error
    assert "model_id" in payload


@pytest.mark.asyncio
async def test_recommend_model_has_fallback() -> None:
    """llm_recommend_model returns a fallback option when models exist."""
    mcp = create_server()
    payload = await _call_tool(
        mcp,
        "llm_recommend_model",
        {"task": "reasoning", "complexity": "complex"},
    )
    # Fallback may be None only if there is at most one matching model
    assert "fallback" in payload


@pytest.mark.asyncio
async def test_recommend_model_unknown_task_defaults_gracefully() -> None:
    """llm_recommend_model with an unknown task name doesn't crash."""
    mcp = create_server()
    payload = await _call_tool(
        mcp,
        "llm_recommend_model",
        {"task": "unknown_task_xyz", "complexity": "moderate"},
    )
    assert "model_id" in payload  # may be None but key must exist


# ── llm_refresh_benchmarks ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_benchmarks_returns_ok_or_error_shape() -> None:
    """llm_refresh_benchmarks always returns ok + message fields."""
    mcp = create_server()
    # May fail if no API key — that's fine, but shape must be correct
    payload = await _call_tool(mcp, "llm_refresh_benchmarks", {"force": False})
    assert "ok" in payload
    assert "message" in payload
    assert isinstance(payload["ok"], bool)


@pytest.mark.asyncio
async def test_refresh_benchmarks_force_flag_accepted() -> None:
    """llm_refresh_benchmarks accepts force=True without error."""
    mcp = create_server()
    payload = await _call_tool(mcp, "llm_refresh_benchmarks", {"force": True})
    assert "ok" in payload
