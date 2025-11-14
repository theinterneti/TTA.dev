"""Instrumented workflow primitive with automatic OpenTelemetry tracing."""

from __future__ import annotations

import logging
import time
from abc import abstractmethod
from typing import Any, TypeVar

from ..core.base import WorkflowContext, WorkflowPrimitive
from .context_propagation import create_linked_span, inject_trace_context
from .enhanced_collector import get_enhanced_metrics_collector
from .metrics_v2 import get_primitive_metrics
from .prometheus_metrics import get_prometheus_metrics

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

    def __init__(
        self,
        name: str | None = None,
        primitive_type: str | None = None,
        action: str = "execute",
    ) -> None:
        """
        Initialize instrumented primitive.

        Args:
            name: Optional name for the primitive. Defaults to class name.
                  Used in span names as "primitive.{name}"
            primitive_type: Semantic primitive type (e.g., 'sequential', 'parallel', 'cache').
                           Defaults to lowercase class name without 'Primitive' suffix.
            action: Action being performed (e.g., 'execute', 'step_0', 'validate').
                   Defaults to 'execute'.
        """
        self.name = name or self.__class__.__name__

        # Derive primitive_type from class name if not provided
        if primitive_type is None:
            # Remove 'Primitive' suffix and convert to lowercase
            class_name = self.__class__.__name__
            if class_name.endswith("Primitive"):
                primitive_type = class_name[:-9].lower()  # Remove "Primitive"
            else:
                primitive_type = class_name.lower()

        self.primitive_type = primitive_type
        self.action = action

        self._tracer = (
            trace.get_tracer(__name__)
            if TRACING_AVAILABLE and trace is not None
            else None
        )

    def _get_span_name(self) -> str:
        """
        Get semantic span name following {domain}.{component}.{action} pattern.

        Returns:
            Span name like "primitive.sequential.execute" or "primitive.cache.hit"
        """
        return f"primitive.{self.primitive_type}.{self.action}"

    def _set_standard_attributes(self, span: Any, context: WorkflowContext) -> None:
        """
        Set standard OpenTelemetry attributes on a span.

        Follows the observability strategy's attribute standards for
        consistent filtering, grouping, and analysis.

        Args:
            span: OpenTelemetry span to add attributes to
            context: WorkflowContext with metadata
        """
        # Primitive attributes
        span.set_attribute("primitive.name", self.name)
        span.set_attribute("primitive.type", self.primitive_type)
        span.set_attribute("primitive.action", self.action)

        # Agent attributes (if available in context)
        if context.agent_id:
            span.set_attribute("agent.id", context.agent_id)
        if context.agent_type:
            span.set_attribute("agent.type", context.agent_type)

        # Workflow attributes
        if context.workflow_id:
            span.set_attribute("workflow.id", context.workflow_id)
        if context.workflow_name:
            span.set_attribute("workflow.name", context.workflow_name)
        if context.session_id:
            span.set_attribute("session.id", context.session_id)
        if context.correlation_id:
            span.set_attribute("correlation.id", context.correlation_id)
        if context.player_id:
            span.set_attribute("player.id", context.player_id)

        # LLM attributes (if available in context)
        if context.llm_provider:
            span.set_attribute("llm.provider", context.llm_provider)
        if context.llm_model_name:
            span.set_attribute("llm.model_name", context.llm_model_name)
        if context.llm_model_tier:
            span.set_attribute("llm.model_tier", context.llm_model_tier)

        # Custom tags from context
        for key, value in context.tags.items():
            span.set_attribute(f"tag.{key}", value)

        # Baggage as attributes
        for key, value in context.baggage.items():
            span.set_attribute(f"baggage.{key}", value)

    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """
        Execute the primitive with automatic instrumentation.

        This method handles:
        1. Trace context injection from active span
        2. Span creation with proper parent-child relationships
        3. Adding span attributes from WorkflowContext
        4. Recording checkpoints and timing
        5. Enhanced metrics collection (percentiles, SLO, throughput, cost)
        6. Calling the subclass implementation

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
        start_time = time.time()

        # Get enhanced metrics collector
        metrics_collector = get_enhanced_metrics_collector()
        metrics_collector.start_request(self.name)

        # Inject trace context from active span (if available)
        context = inject_trace_context(context)

        # Execute with or without tracing
        success = False
        try:
            if self._tracer and TRACING_AVAILABLE:
                # Create span with semantic naming
                span_name = self._get_span_name()
                with create_linked_span(self._tracer, span_name, context) as span:
                    # Set standard attributes using helper
                    self._set_standard_attributes(span, context)

                    # Add context metadata attributes (avoid duplication)
                    for key, value in context.to_otel_context().items():
                        # Skip if already set by _set_standard_attributes
                        if not key.startswith(
                            (
                                "primitive.",
                                "agent.",
                                "workflow.",
                                "session.",
                                "correlation.",
                                "player.",
                                "llm.",
                                "tag.",
                                "baggage.",
                            )
                        ):
                            span.set_attribute(key, value)

                    # Execute implementation
                    try:
                        result = await self._execute_impl(input_data, context)
                        span.set_attribute("primitive.status", "success")
                        span.set_attribute("execution.status", "success")
                        # Mark success immediately before return
                        success = True
                        return result
                    except Exception as e:
                        # Record exception in span with detailed error info
                        span.set_attribute("primitive.status", "error")
                        span.set_attribute("execution.status", "error")
                        span.set_attribute("error.type", type(e).__name__)
                        span.set_attribute("error.message", str(e))
                        span.record_exception(e)
                        raise
            else:
                # Execute without tracing (graceful degradation)
                result = await self._execute_impl(input_data, context)
                # Mark success immediately before return
                success = True
                return result
        finally:
            # Record end checkpoint
            context.checkpoint(f"{self.name}.end")

            # Calculate duration and record metrics
            duration_ms = (time.time() - start_time) * 1000
            duration_seconds = duration_ms / 1000.0

            metrics_collector.record_execution(
                self.name, duration_ms=duration_ms, success=success
            )
            metrics_collector.end_request(self.name)

            # Record in new Phase 2 metrics (OpenTelemetry)
            primitive_metrics = get_primitive_metrics()
            primitive_metrics.record_execution(
                primitive_name=self.name,
                primitive_type=self.primitive_type,
                duration_ms=duration_ms,
                status="success" if success else "error",
                agent_type=context.agent_type,
                error_type=None,  # TODO: Track last error type
            )

            # Record in Prometheus metrics (for Grafana dashboards)
            prom_metrics = get_prometheus_metrics()
            prom_metrics.record_primitive_execution(
                primitive_type=self.primitive_type,
                primitive_name=self.name,
                status="success" if success else "failure",
            )
            prom_metrics.record_execution_duration(
                primitive_type=self.primitive_type,
                duration_seconds=duration_seconds,
            )

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
