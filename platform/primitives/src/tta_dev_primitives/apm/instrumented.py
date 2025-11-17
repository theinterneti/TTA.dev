"""APM-enabled workflow primitive base class."""

import logging
import time
from typing import Any

from ..apm import get_meter, get_tracer, is_apm_enabled
from ..core.base import WorkflowContext, WorkflowPrimitive

logger = logging.getLogger(__name__)


class APMWorkflowPrimitive(WorkflowPrimitive):
    """Base workflow primitive with APM instrumentation.

    This class wraps the standard WorkflowPrimitive with OpenTelemetry
    tracing and metrics. It automatically tracks:
    - Execution duration
    - Success/failure rates
    - Input/output sizes
    - Error types

    Example:
        >>> from tta_workflow_primitives.apm import setup_apm
        >>> from tta_workflow_primitives.apm.instrumented import APMWorkflowPrimitive
        >>>
        >>> setup_apm("my-service")
        >>>
        >>> class MyPrimitive(APMWorkflowPrimitive):
        ...     async def execute(self, input_data, context):
        ...         # Your logic here
        ...         return result
        >>>
        >>> # Automatically traced and metered!
        >>> result = await MyPrimitive().execute(data, context)
    """

    def __init__(self, name: str | None = None) -> None:
        """Initialize APM-enabled primitive.

        Args:
            name: Custom name for the primitive (defaults to class name)
        """
        self.name = name or self.__class__.__name__
        self._execution_counter = None
        self._duration_histogram = None
        self._init_metrics()

    def _init_metrics(self) -> None:
        """Initialize metrics instruments."""
        if not is_apm_enabled():
            return

        meter = get_meter(__name__)
        if not meter:
            return

        # Create counter for executions
        self._execution_counter = meter.create_counter(
            f"primitive.{self.name}.executions",
            description=f"Number of executions for {self.name}",
            unit="1",
        )

        # Create histogram for duration
        self._duration_histogram = meter.create_histogram(
            f"primitive.{self.name}.duration",
            description=f"Execution duration for {self.name}",
            unit="ms",
        )

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """Execute with APM instrumentation.

        This wraps the actual execution with tracing and metrics collection.
        Subclasses should override `_execute_impl` instead of this method.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output data
        """
        if not is_apm_enabled():
            return await self._execute_impl(input_data, context)

        tracer = get_tracer(__name__)
        if not tracer:
            return await self._execute_impl(input_data, context)

        # Start span for this execution
        span_name = f"{self.name}.execute"
        with tracer.start_as_current_span(
            span_name,
            attributes={
                "primitive.name": self.name,
                "primitive.type": self.__class__.__name__,
                "workflow.id": context.workflow_id or "unknown",
                "session.id": context.session_id or "unknown",
            },
        ) as span:
            start_time = time.time()

            try:
                # Execute the actual implementation
                result = await self._execute_impl(input_data, context)

                # Record success
                duration_ms = (time.time() - start_time) * 1000

                span.set_attribute("execution.status", "success")
                span.set_attribute("execution.duration_ms", duration_ms)

                # Update metrics
                if self._execution_counter:
                    self._execution_counter.add(1, {"status": "success", "primitive": self.name})

                if self._duration_histogram:
                    self._duration_histogram.record(
                        duration_ms, {"status": "success", "primitive": self.name}
                    )

                return result

            except Exception as e:
                # Record failure
                duration_ms = (time.time() - start_time) * 1000
                error_type = type(e).__name__

                span.set_attribute("execution.status", "error")
                span.set_attribute("execution.duration_ms", duration_ms)
                span.set_attribute("error.type", error_type)
                span.set_attribute("error.message", str(e))

                # Update metrics
                if self._execution_counter:
                    self._execution_counter.add(
                        1, {"status": "error", "primitive": self.name, "error_type": error_type}
                    )

                if self._duration_histogram:
                    self._duration_histogram.record(
                        duration_ms,
                        {"status": "error", "primitive": self.name, "error_type": error_type},
                    )

                logger.error(f"Primitive {self.name} failed after {duration_ms:.2f}ms: {e}")
                raise

    async def _execute_impl(self, input_data: Any, context: WorkflowContext) -> Any:
        """Actual execution implementation.

        Subclasses should override this method instead of `execute`.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Output data
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement _execute_impl")
