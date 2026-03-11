"""Tests for hierarchical trace view."""

import pytest

from ttadev.observability.trace_context import TraceContext


@pytest.mark.asyncio
async def test_hierarchical_span_creation():
    """Test creating hierarchical spans with proper context."""
    ctx = TraceContext(user="thein", provider="github-copilot", model="claude-sonnet-4.5")

    # Create hierarchical spans
    trace_data = await ctx.create_trace_hierarchy(
        agent="backend-engineer",
        workflow="build_api",
        primitives=["RetryPrimitive", "CachePrimitive"],
    )

    assert trace_data["user"] == "thein"
    assert trace_data["provider"] == "github-copilot"
    assert trace_data["model"] == "claude-sonnet-4.5"
    assert trace_data["agent"] == "backend-engineer"
    assert trace_data["workflow"] == "build_api"
    assert len(trace_data["primitives"]) == 2
