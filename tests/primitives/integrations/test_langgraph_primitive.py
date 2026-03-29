"""Tests for LangGraphPrimitive.

LangGraph is NOT installed in the test environment; all graph interaction is
mocked via AsyncMock / MagicMock so these tests run with zero real dependencies.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(**kwargs: Any) -> WorkflowContext:
    """Build a minimal WorkflowContext for testing."""
    return WorkflowContext(workflow_id=kwargs.pop("workflow_id", "test-wf"), **kwargs)


def _make_graph(
    *,
    invoke_result: dict[str, Any] | None = None,
    stream_chunks: list[dict[str, Any]] | None = None,
) -> MagicMock:
    """Return a mock CompiledStateGraph.

    Args:
        invoke_result: Value returned by ``ainvoke``.
        stream_chunks: Sequence of state dicts yielded by ``astream``.
    """

    async def _astream(state: Any, **kwargs: Any):
        for chunk in stream_chunks or []:
            yield chunk

    graph = MagicMock()
    graph.ainvoke = AsyncMock(return_value=invoke_result or {"output": "default"})
    graph.astream = MagicMock(side_effect=_astream)
    return graph


def _make_primitive(**kwargs: Any):
    """Instantiate LangGraphPrimitive with _LANGGRAPH_AVAILABLE forced True."""
    import ttadev.primitives.integrations.langgraph_primitive as _mod

    with patch.object(_mod, "_LANGGRAPH_AVAILABLE", True):
        from ttadev.primitives.integrations.langgraph_primitive import LangGraphPrimitive

        return LangGraphPrimitive(**kwargs)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestLangGraphPrimitiveConstruction:
    def test_raises_import_error_when_langgraph_missing(self):
        """Constructor raises ImportError when langgraph is not installed."""
        import ttadev.primitives.integrations.langgraph_primitive as _mod

        with patch.object(_mod, "_LANGGRAPH_AVAILABLE", False):
            from ttadev.primitives.integrations.langgraph_primitive import LangGraphPrimitive

            with pytest.raises(ImportError, match="langgraph"):
                LangGraphPrimitive(MagicMock())

    def test_is_workflow_primitive_subclass(self):
        """LangGraphPrimitive is a WorkflowPrimitive."""
        prim = _make_primitive(graph=MagicMock())
        assert isinstance(prim, WorkflowPrimitive)

    def test_default_name_is_class_name(self):
        """Default name comes from the class name."""
        prim = _make_primitive(graph=MagicMock())
        assert prim._name == "LangGraphPrimitive"

    def test_custom_name_stored(self):
        """Custom name is stored."""
        prim = _make_primitive(graph=MagicMock(), name="my-graph")
        assert prim._name == "my-graph"

    def test_base_config_stored(self):
        """Base config is stored."""
        prim = _make_primitive(graph=MagicMock(), config={"configurable": {"thread_id": "1"}})
        assert prim._base_config == {"configurable": {"thread_id": "1"}}


# ---------------------------------------------------------------------------
# Config merging
# ---------------------------------------------------------------------------


class TestBuildConfig:
    def test_injects_workflow_id(self):
        """WorkflowContext.workflow_id is injected into metadata."""
        prim = _make_primitive(graph=MagicMock())
        cfg = prim._build_config(_ctx(workflow_id="wf-99"))
        assert cfg["metadata"]["workflow_id"] == "wf-99"

    def test_injects_session_id_when_present(self):
        """session_id is injected when present in context."""
        prim = _make_primitive(graph=MagicMock())
        cfg = prim._build_config(_ctx(session_id="sess-1"))
        assert cfg["metadata"]["session_id"] == "sess-1"

    def test_injects_trace_id_when_present(self):
        """trace_id is injected when present in context."""
        prim = _make_primitive(graph=MagicMock())
        cfg = prim._build_config(_ctx(trace_id="trace-abc"))
        assert cfg["metadata"]["trace_id"] == "trace-abc"

    def test_merges_with_base_config(self):
        """Base config keys outside 'metadata' are preserved."""
        prim = _make_primitive(graph=MagicMock(), config={"configurable": {"thread_id": "t1"}})
        cfg = prim._build_config(_ctx())
        assert cfg["configurable"]["thread_id"] == "t1"
        assert "workflow_id" in cfg["metadata"]

    def test_base_metadata_and_ctx_metadata_are_merged(self):
        """User-supplied metadata and context metadata coexist."""
        prim = _make_primitive(graph=MagicMock(), config={"metadata": {"user_key": "user_val"}})
        cfg = prim._build_config(_ctx(workflow_id="wf-1"))
        assert cfg["metadata"]["user_key"] == "user_val"
        assert cfg["metadata"]["workflow_id"] == "wf-1"


# ---------------------------------------------------------------------------
# execute()
# ---------------------------------------------------------------------------


class TestExecute:
    @pytest.mark.asyncio
    async def test_calls_ainvoke_with_input(self):
        """execute() passes input_data to graph.ainvoke."""
        graph = _make_graph(invoke_result={"answer": 42})
        prim = _make_primitive(graph=graph)
        ctx = _ctx()
        result = await prim.execute({"question": "?"}, ctx)
        graph.ainvoke.assert_awaited_once()
        call_args = graph.ainvoke.call_args
        assert call_args.args[0] == {"question": "?"}
        assert result == {"answer": 42}

    @pytest.mark.asyncio
    async def test_injects_context_into_config(self):
        """execute() injects WorkflowContext metadata into LangGraph config."""
        graph = _make_graph()
        prim = _make_primitive(graph=graph)
        await prim.execute({}, _ctx(workflow_id="wf-ctx"))
        call_args = graph.ainvoke.call_args
        config = call_args.kwargs.get("config") or call_args.args[1]
        assert config["metadata"]["workflow_id"] == "wf-ctx"

    @pytest.mark.asyncio
    async def test_returns_ainvoke_result(self):
        """execute() returns the graph result unchanged."""
        graph = _make_graph(invoke_result={"nodes": ["a", "b"], "final": True})
        prim = _make_primitive(graph=graph)
        result = await prim.execute({}, _ctx())
        assert result == {"nodes": ["a", "b"], "final": True}

    @pytest.mark.asyncio
    async def test_propagates_ainvoke_exception(self):
        """execute() re-raises exceptions from ainvoke."""
        graph = MagicMock()
        graph.ainvoke = AsyncMock(side_effect=RuntimeError("graph error"))

        import ttadev.primitives.integrations.langgraph_primitive as _mod

        with patch.object(_mod, "_LANGGRAPH_AVAILABLE", True):
            from ttadev.primitives.integrations.langgraph_primitive import LangGraphPrimitive

            prim = LangGraphPrimitive(graph)

        with pytest.raises(RuntimeError, match="graph error"):
            await prim.execute({}, _ctx())

    @pytest.mark.asyncio
    async def test_chains_with_double_arrow(self):
        """LangGraphPrimitive composes with >> (execute output fed downstream)."""
        from ttadev.primitives.core.base import LambdaPrimitive

        graph = _make_graph(invoke_result={"value": 10})
        prim = _make_primitive(graph=graph)

        received: list[Any] = []

        async def capture(data: dict, ctx: WorkflowContext) -> dict:
            received.append(data)
            return data

        pipeline = prim >> LambdaPrimitive(capture)
        result = await pipeline.execute({}, _ctx())

        assert received == [{"value": 10}]
        assert result == {"value": 10}


# ---------------------------------------------------------------------------
# stream_output()
# ---------------------------------------------------------------------------


class TestStreamOutput:
    @pytest.mark.asyncio
    async def test_yields_chunks_from_astream(self):
        """stream_output() yields each chunk from graph.astream."""
        chunks = [{"step": 1}, {"step": 2}, {"step": 3}]
        graph = _make_graph(stream_chunks=chunks)
        prim = _make_primitive(graph=graph)

        collected = []
        async for chunk in prim.stream_output({}, _ctx()):
            collected.append(chunk)

        assert collected == chunks

    @pytest.mark.asyncio
    async def test_empty_stream_yields_nothing(self):
        """stream_output() with no chunks yields nothing."""
        graph = _make_graph(stream_chunks=[])
        prim = _make_primitive(graph=graph)

        collected = []
        async for chunk in prim.stream_output({}, _ctx()):
            collected.append(chunk)

        assert collected == []

    @pytest.mark.asyncio
    async def test_injects_context_into_astream_config(self):
        """stream_output() injects WorkflowContext metadata into astream config."""
        captured_config: dict[str, Any] = {}

        async def _astream(state: Any, config: dict | None = None, **_: Any):
            if config:
                captured_config.update(config)
            yield {"node": "done"}

        graph = MagicMock()
        graph.astream = MagicMock(side_effect=_astream)

        import ttadev.primitives.integrations.langgraph_primitive as _mod

        with patch.object(_mod, "_LANGGRAPH_AVAILABLE", True):
            from ttadev.primitives.integrations.langgraph_primitive import LangGraphPrimitive

            prim = LangGraphPrimitive(graph)

        async for _ in prim.stream_output({}, _ctx(workflow_id="stream-wf")):
            pass

        assert captured_config.get("metadata", {}).get("workflow_id") == "stream-wf"

    @pytest.mark.asyncio
    async def test_propagates_astream_exception(self):
        """stream_output() propagates exceptions from astream."""

        async def _bad_astream(*_: Any, **__: Any):
            yield {"partial": "data"}
            raise ValueError("stream broken")

        graph = MagicMock()
        graph.astream = MagicMock(side_effect=_bad_astream)

        import ttadev.primitives.integrations.langgraph_primitive as _mod

        with patch.object(_mod, "_LANGGRAPH_AVAILABLE", True):
            from ttadev.primitives.integrations.langgraph_primitive import LangGraphPrimitive

            prim = LangGraphPrimitive(graph)

        with pytest.raises(ValueError, match="stream broken"):
            async for _ in prim.stream_output({}, _ctx()):
                pass


# ---------------------------------------------------------------------------
# OTel tracing
# ---------------------------------------------------------------------------


class TestOTelTracing:
    @pytest.mark.asyncio
    async def test_execute_creates_otel_span(self):
        """execute() creates an OTel span when tracing is available."""
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_span.return_value = mock_span

        import ttadev.primitives.integrations.langgraph_primitive as _mod

        with (
            patch.object(_mod, "_TRACING_AVAILABLE", True),
            patch.object(_mod, "_LANGGRAPH_AVAILABLE", True),
            patch.object(_mod, "_otel_trace") as mock_otel,
        ):
            mock_otel.get_tracer.return_value = mock_tracer
            from ttadev.primitives.integrations.langgraph_primitive import LangGraphPrimitive

            graph = _make_graph()
            prim = LangGraphPrimitive(graph, name="test-graph")
            await prim.execute({}, _ctx())

        mock_tracer.start_span.assert_called_once_with("langgraph.test-graph.execute")
        mock_span.set_attribute.assert_any_call("langgraph.graph_name", "test-graph")
        mock_span.set_attribute.assert_any_call("langgraph.status", "ok")
        mock_span.end.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_records_error_on_span(self):
        """execute() sets langgraph.status=error on the span when ainvoke fails."""
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_span.return_value = mock_span

        graph = MagicMock()
        graph.ainvoke = AsyncMock(side_effect=RuntimeError("fail"))

        import ttadev.primitives.integrations.langgraph_primitive as _mod

        with (
            patch.object(_mod, "_TRACING_AVAILABLE", True),
            patch.object(_mod, "_LANGGRAPH_AVAILABLE", True),
            patch.object(_mod, "_otel_trace") as mock_otel,
        ):
            mock_otel.get_tracer.return_value = mock_tracer
            from ttadev.primitives.integrations.langgraph_primitive import LangGraphPrimitive

            prim = LangGraphPrimitive(graph)
            with pytest.raises(RuntimeError):
                await prim.execute({}, _ctx())

        mock_span.set_attribute.assert_any_call("langgraph.status", "error")
        mock_span.end.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_output_creates_otel_span(self):
        """stream_output() creates an OTel span when tracing is available."""
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_span.return_value = mock_span

        import ttadev.primitives.integrations.langgraph_primitive as _mod

        with (
            patch.object(_mod, "_TRACING_AVAILABLE", True),
            patch.object(_mod, "_LANGGRAPH_AVAILABLE", True),
            patch.object(_mod, "_otel_trace") as mock_otel,
        ):
            mock_otel.get_tracer.return_value = mock_tracer
            from ttadev.primitives.integrations.langgraph_primitive import LangGraphPrimitive

            graph = _make_graph(stream_chunks=[{"x": 1}, {"x": 2}])
            prim = LangGraphPrimitive(graph, name="stream-graph")
            async for _ in prim.stream_output({}, _ctx()):
                pass

        mock_tracer.start_span.assert_called_once_with("langgraph.stream-graph.stream")
        mock_span.set_attribute.assert_any_call("langgraph.chunk_count", 2)
        mock_span.set_attribute.assert_any_call("langgraph.status", "ok")
        mock_span.end.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_otel_span_when_tracing_unavailable(self):
        """No OTel tracer is created when _TRACING_AVAILABLE is False."""
        import ttadev.primitives.integrations.langgraph_primitive as _mod

        with (
            patch.object(_mod, "_TRACING_AVAILABLE", False),
            patch.object(_mod, "_LANGGRAPH_AVAILABLE", True),
        ):
            from ttadev.primitives.integrations.langgraph_primitive import LangGraphPrimitive

            graph = _make_graph()
            prim = LangGraphPrimitive(graph)
            result = await prim.execute({"in": 1}, _ctx())

        assert result == {"output": "default"}


# ---------------------------------------------------------------------------
# Import guard
# ---------------------------------------------------------------------------


class TestImportGuard:
    def test_langgraph_primitive_is_none_in_integrations_init_when_missing(self):
        """integrations.__init__ sets LangGraphPrimitive=None when langgraph absent."""
        import sys

        # Ensure langgraph is absent
        sys.modules.pop("langgraph", None)
        sys.modules.pop("langgraph.graph", None)
        sys.modules.pop("langgraph.graph.graph", None)

        with patch.dict(sys.modules, {"langgraph": None, "langgraph.graph.graph": None}):
            import ttadev.primitives.integrations.langgraph_primitive as _mod

            with patch.object(_mod, "_LANGGRAPH_AVAILABLE", False):
                from ttadev.primitives.integrations.langgraph_primitive import LangGraphPrimitive

                with pytest.raises(ImportError, match="langgraph"):
                    LangGraphPrimitive(MagicMock())
