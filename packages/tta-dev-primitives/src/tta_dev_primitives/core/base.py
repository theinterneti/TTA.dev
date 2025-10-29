"""Base workflow primitive abstractions."""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


class WorkflowContext(BaseModel):
    """
    Context passed through workflow execution with full observability support.
    
    Provides distributed tracing, correlation tracking, and performance measurement
    capabilities for workflow primitives.
    
    Example:
        ```python
        context = WorkflowContext(
            workflow_id="narrative-gen-123",
            session_id="session-456"
        )
        
        # Record checkpoints
        context.checkpoint("validation_complete")
        
        # Create child context for nested workflows
        child_context = context.create_child_context()
        ```
    """

    # Existing fields
    workflow_id: str | None = None
    session_id: str | None = None
    player_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    state: dict[str, Any] = Field(default_factory=dict)

    # Distributed tracing (W3C Trace Context)
    trace_id: str | None = Field(default=None, description="OpenTelemetry trace ID")
    span_id: str | None = Field(default=None, description="Current span ID")
    parent_span_id: str | None = Field(default=None, description="Parent span ID")
    trace_flags: int = Field(default=1, description="W3C trace flags (sampled=1)")

    # Correlation and causation
    # NOTE: correlation_id is generated fresh for each new workflow.
    # For nested workflows, use create_child_context() which inherits the parent's correlation_id.
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    causation_id: str | None = Field(default=None, description="Event causation chain")

    # Observability metadata
    baggage: dict[str, str] = Field(default_factory=dict, description="W3C Baggage")
    tags: dict[str, str] = Field(default_factory=dict, description="Custom tags")

    # Performance tracking
    start_time: float = Field(default_factory=time.time)
    checkpoints: list[tuple[str, float]] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def checkpoint(self, name: str) -> None:
        """
        Record a timing checkpoint.
        
        Args:
            name: Name of the checkpoint
            
        Example:
            ```python
            context.checkpoint("data_validated")
            context.checkpoint("model_inference_complete")
            ```
        """
        self.checkpoints.append((name, time.time()))

    def elapsed_ms(self) -> float:
        """
        Get elapsed time since workflow start in milliseconds.
        
        Returns:
            Elapsed time in milliseconds
            
        Example:
            ```python
            duration = context.elapsed_ms()
            logger.info(f"Workflow took {duration:.2f}ms")
            ```
        """
        return (time.time() - self.start_time) * 1000

    def create_child_context(self) -> WorkflowContext:
        """
        Create a child context for nested workflows.
        
        The child context inherits trace information and correlation ID from the parent,
        allowing distributed tracing across nested workflow executions.
        
        Returns:
            New child context with inherited trace info
            
        Example:
            ```python
            # In ParallelPrimitive
            child_contexts = [context.create_child_context() for _ in branches]
            ```
        """
        return WorkflowContext(
            workflow_id=self.workflow_id,
            session_id=self.session_id,
            player_id=self.player_id,
            metadata=self.metadata.copy(),
            state=self.state.copy(),
            trace_id=self.trace_id,
            parent_span_id=self.span_id,  # Current span becomes parent
            correlation_id=self.correlation_id,  # Inherit correlation
            causation_id=self.correlation_id,  # Chain causation
            baggage=self.baggage.copy(),
            tags=self.tags.copy(),
        )

    def to_otel_context(self) -> dict[str, Any]:
        """
        Convert to OpenTelemetry context attributes.
        
        Returns:
            Dictionary of attributes for OpenTelemetry spans
            
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
