"""Auto-instrumented workflow primitive base class."""

from __future__ import annotations

import logging
import time
from typing import TypeVar

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive

from ..context.propagation import create_linked_span, inject_trace_context

try:
    from opentelemetry import trace

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

T = TypeVar("T")
U = TypeVar("U")

logger = logging.getLogger(__name__)


class InstrumentedPrimitive(WorkflowPrimitive[T, U]):
    """
    Base class for auto-instrumented primitives.

    Automatically adds:
    - Distributed tracing with context propagation
    - Structured logging with correlation IDs
    - Metrics collection (duration, success/failure)
    - Error tracking in spans

    Example:
        ```python
        from tta_dev_observability.instrumentation.base import InstrumentedPrimitive
        from tta_dev_primitives.core.base import WorkflowContext

        class MyPrimitive(InstrumentedPrimitive[dict, dict]):
            async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
                # Your logic here - tracing is automatic
                return {"result": "success"}

        # Use like any other primitive
        primitive = MyPrimitive(name="my-operation")
        context = WorkflowContext(workflow_id="test")
        result = await primitive.execute({"query": "test"}, context)
        ```
    """

    def __init__(self, name: str | None = None) -> None:
        """
        Initialize instrumented primitive.

        Args:
            name: Custom name for the primitive (defaults to class name)
        """
        self.name = name or self.__class__.__name__
        self._tracer = trace.get_tracer(__name__) if TRACING_AVAILABLE else None

    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """
        Execute with full instrumentation.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output data

        Raises:
            Exception: Any exception from _execute_impl
        """
        # Inject trace context if not present
        if TRACING_AVAILABLE and self._tracer:
            context = inject_trace_context(context)

        start_time = time.time()

        # Create span if tracing available
        if self._tracer:
            span = create_linked_span(
                self._tracer,
                f"{self.name}.execute",
                context,
                attributes={
                    "primitive.name": self.name,
                    "primitive.type": self.__class__.__name__,
                },
            )

            with trace.use_span(span, end_on_exit=True):
                try:
                    result = await self._execute_impl(input_data, context)

                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("primitive.duration_ms", duration_ms)
                    span.set_attribute("primitive.status", "success")

                    logger.info(
                        f"{self.name} completed",
                        extra={
                            "primitive": self.name,
                            "duration_ms": duration_ms,
                            "trace_id": context.trace_id,
                            "correlation_id": context.correlation_id,
                        },
                    )

                    return result

                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("primitive.duration_ms", duration_ms)
                    span.set_attribute("primitive.status", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)

                    logger.error(
                        f"{self.name} failed",
                        extra={
                            "primitive": self.name,
                            "duration_ms": duration_ms,
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                            "trace_id": context.trace_id,
                            "correlation_id": context.correlation_id,
                        },
                        exc_info=True,
                    )

                    raise
        else:
            # No tracing available, execute directly
            return await self._execute_impl(input_data, context)

    async def _execute_impl(self, input_data: T, context: WorkflowContext) -> U:
        """
        Actual execution implementation.

        Subclasses MUST override this method.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output data

        Raises:
            NotImplementedError: If not overridden by subclass
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement _execute_impl")
