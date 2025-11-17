"""Base workflow primitive abstractions."""

from __future__ import annotations

import copy
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


class WorkflowContext(BaseModel):
    """
    Context passed through workflow execution with full observability support.

    Provides distributed tracing, correlation tracking, and observability metadata
    following W3C Trace Context and Baggage specifications.

    See: [[WorkflowContext]] for more details.
    """

    # Core workflow identifiers
    workflow_id: str | None = None
    session_id: str | None = None
    player_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    state: dict[str, Any] = Field(default_factory=dict)

    # Distributed tracing (W3C Trace Context)
    trace_id: str | None = Field(
        default=None, description="OpenTelemetry trace ID (hex)"
    )
    span_id: str | None = Field(default=None, description="Current span ID (hex)")
    parent_span_id: str | None = Field(default=None, description="Parent span ID (hex)")
    trace_flags: int = Field(default=1, description="W3C trace flags (sampled=1)")

    # Correlation and causation tracking
    correlation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique ID for request correlation across services",
    )
    causation_id: str | None = Field(
        default=None, description="ID of the event that caused this workflow"
    )

    # Observability metadata
    baggage: dict[str, str] = Field(
        default_factory=dict,
        description="W3C Baggage for cross-service context propagation",
    )
    tags: dict[str, str] = Field(
        default_factory=dict, description="Custom tags for filtering and grouping"
    )

    # Timing and checkpoints
    start_time: float = Field(default_factory=time.time)
    checkpoints: list[tuple[str, float]] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def checkpoint(self, name: str) -> None:
        """
        Record a timing checkpoint.

        Args:
            name: Name of the checkpoint
        """
        self.checkpoints.append((name, time.time()))

    def elapsed_ms(self) -> float:
        """
        Get elapsed time since workflow start in milliseconds.

        Returns:
            Elapsed time in milliseconds
        """
        return (time.time() - self.start_time) * 1000

    def create_child_context(self) -> WorkflowContext:
        """
        Create a child context for nested workflows.

        Inherits trace context and correlation ID from parent,
        but creates a new span context.

        Returns:
            New WorkflowContext with inherited trace context
        """
        return WorkflowContext(
            workflow_id=self.workflow_id,
            session_id=self.session_id,
            player_id=self.player_id,
            metadata=copy.deepcopy(self.metadata),
            state=copy.deepcopy(self.state),
            trace_id=self.trace_id,
            parent_span_id=self.span_id,  # Current span becomes parent
            correlation_id=self.correlation_id,  # Inherit correlation
            causation_id=self.correlation_id,  # Chain causation
            baggage=copy.deepcopy(self.baggage),
            tags=copy.deepcopy(self.tags),
        )

    def to_otel_context(self) -> dict[str, Any]:
        """
        Convert to OpenTelemetry context attributes.

        Returns:
            Dictionary of span attributes

        Example:
            ```python
            from opentelemetry import trace

            context = WorkflowContext(workflow_id="wf-123")
            span = trace.get_current_span()

            # Add workflow context as span attributes
            for key, value in context.to_otel_context().items():
                span.set_attribute(key, value)
            ```
        """
        return {
            "workflow.id": self.workflow_id or "unknown",
            "workflow.session_id": self.session_id or "unknown",
            "workflow.player_id": self.player_id or "unknown",
            "workflow.correlation_id": self.correlation_id,
            "workflow.elapsed_ms": self.elapsed_ms(),
        }


class WorkflowPrimitive(Generic[T, U], ABC):
    """
    Base class for composable workflow primitives.

    Primitives are the building blocks of workflows. They can be composed
    using operators:
    - `>>` for sequential execution (self then other)
    - `|` for parallel execution (self and other concurrently)

    See: [[TTA.dev___Concepts___Composition]] for more details.

    Example:
        ```python
        workflow = primitive1 >> primitive2 >> primitive3
        result = await workflow.execute(input_data, context)
        ```
    """

    @abstractmethod
    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """
        Execute the primitive with input data and context.

        Args:
            input_data: Input data for the primitive
            context: Workflow context with session/state information

        Returns:
            Output data from the primitive

        Raises:
            Exception: If execution fails
        """
        pass

    def __rshift__(self, other: WorkflowPrimitive[U, V]) -> WorkflowPrimitive[T, V]:
        """
        Chain primitives sequentially: self >> other.

        The output of self becomes the input to other.

        Args:
            other: The primitive to execute after this one

        Returns:
            A new sequential primitive
        """
        from .sequential import SequentialPrimitive

        return SequentialPrimitive([self, other])

    def __or__(self, other: WorkflowPrimitive[T, U]) -> WorkflowPrimitive[T, list[U]]:
        """
        Execute primitives in parallel: self | other.

        Both primitives receive the same input and execute concurrently.

        Args:
            other: The primitive to execute in parallel

        Returns:
            A new parallel primitive
        """
        from .parallel import ParallelPrimitive

        return ParallelPrimitive([self, other])


class LambdaPrimitive(WorkflowPrimitive[T, U]):
    """
    Primitive that wraps a simple function or lambda.

    Useful for simple transformations or adapters.

    Example:
        ```python
        transform = LambdaPrimitive(lambda x, ctx: x.upper())
        workflow = input_primitive >> transform >> output_primitive
        ```
    """

    def __init__(self, func: Any) -> None:
        """
        Initialize with a function.

        Args:
            func: Async or sync function (input, context) -> output
        """
        self.func = func
        import inspect

        self.is_async = inspect.iscoroutinefunction(func)

    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """Execute the wrapped function."""
        if self.is_async:
            return await self.func(input_data, context)
        else:
            return self.func(input_data, context)
