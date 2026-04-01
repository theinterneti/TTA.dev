"""Tests for ttadev.observability.trace_context."""

import pytest

from ttadev.observability.trace_context import TraceContext


@pytest.fixture
def ctx() -> TraceContext:
    return TraceContext(user="u", provider="openai", model="gpt-4", trace_id="t1")


class TestCreateTraceHierarchy:
    @pytest.mark.asyncio
    async def test_returns_required_keys(self, ctx: TraceContext) -> None:
        result = await ctx.create_trace_hierarchy(
            agent="backend-engineer", workflow="build_api", primitives=["retry", "cache"]
        )
        assert result["trace_id"] == "t1"
        assert result["user"] == "u"
        assert result["provider"] == "openai"
        assert result["model"] == "gpt-4"
        assert result["agent"] == "backend-engineer"
        assert result["workflow"] == "build_api"
        assert result["primitives"] == ["retry", "cache"]
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_empty_primitives_list(self, ctx: TraceContext) -> None:
        result = await ctx.create_trace_hierarchy("agent", "wf", [])
        assert result["primitives"] == []


class TestSpan:
    def test_span_no_parent(self, ctx: TraceContext) -> None:
        with ctx.span("root", color="red") as span:
            assert span["name"] == "root"
            assert span["parent_id"] is None
            assert span["attributes"]["color"] == "red"
            assert span["attributes"]["user"] == "u"
        assert "end_time" in span

    def test_span_with_parent(self, ctx: TraceContext) -> None:
        with ctx.span("outer") as outer:
            with ctx.span("inner") as inner:
                assert inner["parent_id"] == outer["span_id"]

    def test_span_restores_previous_after_exit(self, ctx: TraceContext) -> None:
        with ctx.span("outer") as outer:
            with ctx.span("inner"):
                pass
            # after inner exits, current span is back to outer
            assert ctx._current_span is outer

    def test_span_restores_none_after_top_level_exit(self, ctx: TraceContext) -> None:
        with ctx.span("root"):
            pass
        assert ctx._current_span is None

    def test_span_restores_on_exception(self, ctx: TraceContext) -> None:
        with pytest.raises(ValueError):
            with ctx.span("root"):
                raise ValueError("boom")
        assert ctx._current_span is None

    def test_nested_three_levels(self, ctx: TraceContext) -> None:
        with ctx.span("l1") as l1:
            with ctx.span("l2") as l2:
                with ctx.span("l3") as l3:
                    assert l3["parent_id"] == l2["span_id"]
                assert ctx._current_span is l2
            assert ctx._current_span is l1
