"""Instrumented workflow primitive with automatic OpenTelemetry tracing."""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import TypeVar

from ..core.base import WorkflowContext, WorkflowPrimitive
from .context_propagation import create_linked_span, inject_trace_context

# Check if OpenTelemetry is available
try:
    from opentelemetry import trace

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    trace = None  # type: ignore

logger = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U")


class InstrumentedPrimitive(WorkflowPrimitive[T, U]):
    """
    Base class for workflow primitives with automatic OpenTelemetry instrumentation.

    Automatically creates spans, injects trace context, and adds observability
    metadata for all primitive executions. Subclasses implement `_execute_impl()`
    instead of `execute()`.

    Features:
    - Automatic span creation with proper parent-child relationships
    - Trace context injection from active OpenTelemetry spans
    - Span attributes from WorkflowContext metadata
    - Graceful degradation when OpenTelemetry unavailable
    - Timing and checkpoint tracking

    Example:
        ```python
        class MyPrimitive(InstrumentedPrimitive[dict, str]):
            async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> str:
                # Your implementation here
                return f"Processed: {input_data}"

        # Usage
        primitive = MyPrimitive(name="my_processor")
        context = WorkflowContext(workflow_id="demo")
        result = await primitive.execute({"key": "value"}, context)
        # Automatically creates span "primitive.my_processor" with trace context
        ```
    """

    def __init__(self, name: str | None = None) -> None:
        """
        Initialize instrumented primitive.

        Args:
            name: Optional name for the primitive. Defaults to class name.
                  Used in span names as "primitive.{name}"
        """
        self.name = name or self.__class__.__name__
        self._tracer = trace.get_tracer(__name__) if TRACING_AVAILABLE else None

    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """
        Execute the primitive with automatic instrumentation.

        This method handles:
        1. Trace context injection from active span
        2. Span creation with proper parent-child relationships
        3. Adding span attributes from WorkflowContext
        4. Recording checkpoints and timing
        5. Calling the subclass implementation

        Args:
            input_data: Input data for the primitive
            context: Workflow context with trace information

        Returns:
            Output from the primitive implementation

        Raises:
            Exception: Any exception from the primitive implementation
        """
        # Record checkpoint for timing
        context.checkpoint(f"{self.name}.start")

        # Inject trace context from active span (if available)
        context = inject_trace_context(context)

        # Execute with or without tracing
        if self._tracer and TRACING_AVAILABLE:
            # Create span linked to context
            with create_linked_span(self._tracer, f"primitive.{self.name}", context) as span:
                # Add context attributes to span
                for key, value in context.to_otel_context().items():
                    span.set_attribute(key, value)

                # Add primitive-specific attributes
                span.set_attribute("primitive.name", self.name)
                span.set_attribute("primitive.type", self.__class__.__name__)

                # Execute implementation
                try:
                    result = await self._execute_impl(input_data, context)
                    span.set_attribute("primitive.status", "success")
                    return result
                except Exception as e:
                    # Record exception in span
                    span.set_attribute("primitive.status", "error")
                    span.set_attribute("primitive.error", str(e))
                    span.record_exception(e)
                    raise
                finally:
                    # Record end checkpoint
                    context.checkpoint(f"{self.name}.end")
        else:
            # Execute without tracing (graceful degradation)
            try:
                result = await self._execute_impl(input_data, context)
                return result
            finally:
                context.checkpoint(f"{self.name}.end")

    @abstractmethod
    async def _execute_impl(self, input_data: T, context: WorkflowContext) -> U:
        """
        Implement the primitive's core logic.

        Subclasses override this method instead of `execute()` to get
        automatic instrumentation.

        Args:
            input_data: Input data for the primitive
            context: Workflow context with trace information

        Returns:
            Output from the primitive

        Raises:
            Exception: Any exception from the implementation
        """
        pass
