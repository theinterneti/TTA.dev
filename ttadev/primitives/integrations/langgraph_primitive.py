"""LangGraph integration primitive.

Wraps a compiled LangGraph ``CompiledStateGraph`` as a :class:`WorkflowPrimitive`
so that LangGraph workflows compose naturally with the rest of the TTA.dev
primitive ecosystem.

LangGraph is an optional dependency.  Importing this module when ``langgraph``
is not installed raises a clear ``ImportError`` pointing at the missing package.

Example:
    ```python
    from langgraph.graph import StateGraph
    from ttadev.primitives.integrations.langgraph_primitive import LangGraphPrimitive
    from ttadev.primitives.core.base import WorkflowContext

    # Build and compile a LangGraph state machine
    graph = StateGraph(MyState).compile()

    # Wrap as a TTA.dev primitive
    prim = LangGraphPrimitive(graph, name="my-graph")
    ctx = WorkflowContext(workflow_id="demo")
    result = await prim.execute({"messages": []}, ctx)

    # Stream state updates
    async for chunk in prim.stream_output({"messages": []}, ctx):
        print(chunk)

    # Compose with other primitives
    pipeline = prim >> post_processor
    ```
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.logging import get_logger

if TYPE_CHECKING:
    pass

try:
    from opentelemetry import trace as _otel_trace

    _TRACING_AVAILABLE = True
except ImportError:  # pragma: no cover
    _otel_trace = None  # type: ignore[assignment]
    _TRACING_AVAILABLE = False

# LangGraph is an optional dependency — raise a clear error on first use, not on import.
try:
    from langgraph.graph.graph import CompiledGraph as _CompiledGraph  # type: ignore[import]

    _LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _CompiledGraph = None  # type: ignore[assignment]
    _LANGGRAPH_AVAILABLE = False

logger = get_logger(__name__)


class LangGraphPrimitive(WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """Wrap a compiled LangGraph state graph as a ``WorkflowPrimitive``.

    This primitive bridges LangGraph's ``CompiledStateGraph`` with TTA.dev's
    composable primitive ecosystem.  It injects :class:`WorkflowContext`
    metadata into the LangGraph ``config`` so that trace IDs and session
    information flow through to all LangGraph nodes.

    OpenTelemetry instrumentation is automatic when OTel is installed:

    - Span ``langgraph.<name>.execute`` covers the full ``ainvoke`` call.
    - Span ``langgraph.<name>.stream`` covers the full ``astream`` call.
    - Attribute ``langgraph.graph_name`` identifies the primitive.
    - Attribute ``langgraph.status`` is ``"ok"`` or ``"error"``.
    - Attribute ``langgraph.chunk_count`` records chunks yielded by
      :meth:`stream_output`.

    Args:
        graph: A compiled LangGraph ``CompiledStateGraph`` (or any object with
            ``ainvoke`` / ``astream`` async methods matching LangGraph's API).
        config: Optional base LangGraph config dict merged with the
            ``WorkflowContext`` metadata on each call.  Keys in this dict take
            lower precedence than context-derived metadata.
        name: Label used in span names and log messages.  Defaults to the
            class name.

    Raises:
        ImportError: On construction when ``langgraph`` is not installed.

    Example:
        ```python
        from langgraph.graph import StateGraph
        from ttadev.primitives.integrations.langgraph_primitive import LangGraphPrimitive

        graph = StateGraph(dict).compile()
        prim = LangGraphPrimitive(graph)
        result = await prim.execute({"key": "value"}, context)
        ```
    """

    def __init__(
        self,
        graph: Any,
        *,
        config: dict[str, Any] | None = None,
        name: str | None = None,
    ) -> None:
        """Initialise a LangGraph primitive.

        Args:
            graph: Compiled LangGraph state graph.
            config: Optional base LangGraph config dict.
            name: Optional label for spans and logs.

        Raises:
            ImportError: When ``langgraph`` package is not installed.
        """
        if not _LANGGRAPH_AVAILABLE:
            raise ImportError(
                "LangGraphPrimitive requires the 'langgraph' package. "
                "Install it with: pip install langgraph"
            )
        self._graph = graph
        self._base_config: dict[str, Any] = config or {}
        self._name = name or type(self).__name__

    def _build_config(self, context: WorkflowContext) -> dict[str, Any]:
        """Merge base config with WorkflowContext metadata.

        Args:
            context: Current workflow context.

        Returns:
            LangGraph config dict with context metadata injected under
            ``config["metadata"]``.
        """
        ctx_meta: dict[str, Any] = {"workflow_id": context.workflow_id}
        if context.session_id:
            ctx_meta["session_id"] = context.session_id
        if context.trace_id:
            ctx_meta["trace_id"] = context.trace_id

        merged = dict(self._base_config)
        # Merge metadata: context values are additive, not replacing user-supplied keys.
        existing_meta: dict[str, Any] = dict(merged.get("metadata") or {})
        existing_meta.update(ctx_meta)
        merged["metadata"] = existing_meta
        return merged

    async def execute(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext,
    ) -> dict[str, Any]:
        """Invoke the LangGraph state machine and return the final state.

        Calls ``graph.ainvoke(input_data, config=...)`` with the merged config
        derived from the primitive's base config and the :class:`WorkflowContext`.

        OTel span ``langgraph.<name>.execute`` is created when tracing is
        available.

        Args:
            input_data: Initial LangGraph state dict.
            context: Workflow context providing trace/session metadata.

        Returns:
            Final LangGraph state dict after the graph has run to completion.

        Raises:
            Exception: Any exception raised by the underlying graph propagates
                unchanged so callers can apply :class:`RetryPrimitive` or
                :class:`FallbackPrimitive` around this primitive.
        """
        lg_config = self._build_config(context)

        span = None
        if _TRACING_AVAILABLE and _otel_trace is not None:
            tracer = _otel_trace.get_tracer(__name__)
            span = tracer.start_span(f"langgraph.{self._name}.execute")
            span.set_attribute("langgraph.graph_name", self._name)

        try:
            logger.debug("LangGraphPrimitive %s: invoking graph", self._name)
            result: dict[str, Any] = await self._graph.ainvoke(input_data, config=lg_config)
            if span is not None:
                span.set_attribute("langgraph.status", "ok")
            return result
        except Exception as exc:
            if span is not None:
                span.set_attribute("langgraph.status", "error")
                span.record_exception(exc)
            logger.error("LangGraphPrimitive %s failed: %s", self._name, exc)
            raise
        finally:
            if span is not None:
                span.end()

    async def stream_output(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream intermediate state updates from the LangGraph execution.

        Calls ``graph.astream(input_data, config=...)`` and yields each state
        chunk as the graph progresses through its nodes.

        OTel span ``langgraph.<name>.stream`` is created when tracing is
        available.

        Args:
            input_data: Initial LangGraph state dict.
            context: Workflow context providing trace/session metadata.

        Yields:
            Intermediate state dicts as each LangGraph node completes.
        """
        lg_config = self._build_config(context)

        span = None
        if _TRACING_AVAILABLE and _otel_trace is not None:
            tracer = _otel_trace.get_tracer(__name__)
            span = tracer.start_span(f"langgraph.{self._name}.stream")
            span.set_attribute("langgraph.graph_name", self._name)

        chunk_count = 0
        try:
            async for chunk in self._graph.astream(input_data, config=lg_config):
                chunk_count += 1
                yield chunk
            if span is not None:
                span.set_attribute("langgraph.chunk_count", chunk_count)
                span.set_attribute("langgraph.status", "ok")
        except Exception as exc:
            if span is not None:
                span.set_attribute("langgraph.status", "error")
                span.record_exception(exc)
            logger.error("LangGraphPrimitive %s stream failed: %s", self._name, exc)
            raise
        finally:
            if span is not None:
                span.end()
