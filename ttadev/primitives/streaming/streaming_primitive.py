"""Streaming primitive for SSE and async-generator output.

Generalises the TTA NGA (Narrative Generator Agent) streaming pattern into a
composable primitive for real-time token delivery via SSE, WebSockets, or any
async consumer.

Example:
    ```python
    from collections.abc import AsyncGenerator
    from ttadev.primitives.streaming import StreamingPrimitive
    from ttadev.primitives.core.base import WorkflowContext

    class NarrativeStreamPrimitive(StreamingPrimitive[str, str]):
        async def stream(
            self,
            input_data: str,
            context: WorkflowContext,
        ) -> AsyncGenerator[str, None]:
            for token in input_data.split():
                yield token + " "

    # Consume from FastAPI SSE
    primitive = NarrativeStreamPrimitive()
    async for token in primitive.stream_with_tracing(prompt, ctx):
        yield f"data: {token}\\n\\n"

    # Or collect the full output (compatible with >> composition)
    tokens = await primitive.execute(prompt, ctx)
    full_text = "".join(tokens)
    ```
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, TypeVar

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

logger = get_logger(__name__)

T = TypeVar("T")
U = TypeVar("U")


class StreamingPrimitive(WorkflowPrimitive[T, list[U]]):
    """Base class for primitives that produce output as an async token stream.

    Subclasses implement :meth:`stream`.  The inherited :meth:`execute`
    convenience method collects all yielded chunks into a list so the
    primitive remains fully compatible with ``>>`` / ``|`` composition and
    the rest of the primitive ecosystem.

    OpenTelemetry instrumentation is automatic when OTel is installed:

    - Span ``streaming.<name>`` covers the full generation lifetime.
    - Span attribute ``streaming.token_count`` records the number of chunks.
    - Span attribute ``streaming.status`` is ``"ok"`` or ``"error"``.

    Args:
        name: Optional label used in span names and log messages.
            Defaults to the class name.

    Example:
        ```python
        class TokenPrimitive(StreamingPrimitive[str, str]):
            async def stream(
                self, input_data: str, context: WorkflowContext
            ) -> AsyncGenerator[str, None]:
                for token in input_data.split():
                    yield token

        p = TokenPrimitive()
        # Streaming consumer (FastAPI SSE, WebSocket …)
        async for token in p.stream_with_tracing(text, ctx):
            ...

        # Collect all tokens (compatible with >> pipelines)
        tokens = await p.execute(text, ctx)
        ```
    """

    def __init__(self, name: str | None = None) -> None:
        self._name = name or type(self).__name__

    @abstractmethod
    def stream(
        self,
        input_data: T,
        context: WorkflowContext,
    ) -> AsyncGenerator[U, None]:
        """Yield output chunks one at a time.

        Subclasses implement this as an async generator function:

        .. code-block:: python

            async def stream(self, input_data, context):
                for token in tokenise(input_data):
                    yield token

        Args:
            input_data: Input data for this primitive.
            context: Workflow context with session/trace metadata.

        Yields:
            Individual output chunks (tokens, lines, JSON fragments, etc.)
        """
        ...  # pragma: no cover

    async def execute(self, input_data: T, context: WorkflowContext) -> list[U]:
        """Collect the full stream and return all chunks as a list.

        This allows seamless use inside ``>>`` pipelines where the downstream
        primitive receives the complete token list.  For string streams the
        caller can join with ``"".join(result)``.

        OTel span ``streaming.<name>.collect`` is created when tracing is
        available.

        Args:
            input_data: Input data for this primitive.
            context: Workflow context.

        Returns:
            All chunks produced by :meth:`stream` collected into a list.
        """
        span = None
        if _TRACING_AVAILABLE and _otel_trace is not None:
            tracer = _otel_trace.get_tracer(__name__)
            span = tracer.start_span(f"streaming.{self._name}.collect")
            span.set_attribute("streaming.primitive", self._name)

        chunks: list[U] = []
        try:
            async for chunk in self.stream(input_data, context):
                chunks.append(chunk)
            if span is not None:
                span.set_attribute("streaming.token_count", len(chunks))
                span.set_attribute("streaming.status", "ok")
            return chunks
        except Exception as exc:
            if span is not None:
                span.set_attribute("streaming.status", "error")
                span.record_exception(exc)
            logger.error("StreamingPrimitive %s failed: %s", self._name, exc)
            raise
        finally:
            if span is not None:
                span.end()

    async def stream_with_tracing(
        self,
        input_data: T,
        context: WorkflowContext,
    ) -> AsyncGenerator[U, None]:
        """Stream with OTel instrumentation for push-delivery contexts.

        Prefer this over :meth:`stream` directly when consuming from FastAPI
        SSE or WebSocket handlers where you need observability without
        buffering the full output into memory.

        OTel span ``streaming.<name>`` is created when tracing is available.

        Args:
            input_data: Input data for this primitive.
            context: Workflow context.

        Yields:
            Individual output chunks, same as :meth:`stream`.
        """
        if not _TRACING_AVAILABLE or _otel_trace is None:
            async for chunk in self.stream(input_data, context):
                yield chunk
            return

        tracer = _otel_trace.get_tracer(__name__)
        span = tracer.start_span(f"streaming.{self._name}")
        span.set_attribute("streaming.primitive", self._name)
        token_count = 0
        try:
            async for chunk in self.stream(input_data, context):
                token_count += 1
                yield chunk
            span.set_attribute("streaming.token_count", token_count)
            span.set_attribute("streaming.status", "ok")
        except Exception as exc:
            span.set_attribute("streaming.status", "error")
            span.record_exception(exc)
            raise
        finally:
            span.end()
