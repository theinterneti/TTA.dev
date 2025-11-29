# Observability Implementation Guide

**Purpose:** Step-by-step guide to implement production-ready observability for TTA.dev
**Target Audience:** Developers implementing observability improvements
**Prerequisites:** Understanding of OpenTelemetry, distributed tracing, and TTA.dev primitives

---

## Phase 1: Foundation - Trace Context Propagation

### 1.1 Enhanced WorkflowContext

**File:** `platform/primitives/src/tta_dev_primitives/core/base.py`

```python
from __future__ import annotations

import time
import uuid
from typing import Any

from pydantic import BaseModel, Field


class WorkflowContext(BaseModel):
    """Context passed through workflow execution with full observability support."""

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
        """Record a timing checkpoint."""
        self.checkpoints.append((name, time.time()))

    def elapsed_ms(self) -> float:
        """Get elapsed time since workflow start in milliseconds."""
        return (time.time() - self.start_time) * 1000

    def create_child_context(self) -> WorkflowContext:
        """Create a child context for nested workflows."""
        return WorkflowContext(
            workflow_id=self.workflow_id,
            session_id=self.session_id,
            player_id=self.player_id,
            metadata=self.metadata.copy(),
            state=self.state.copy(),
            trace_id=self.trace_id,
            parent_span_id=self.span_id,  # Current span becomes parent
            correlation_id=self.correlation_id,
            causation_id=self.correlation_id,  # Chain causation
            baggage=self.baggage.copy(),
            tags=self.tags.copy(),
        )

    def to_otel_context(self) -> dict[str, Any]:
        """
        Convert to OpenTelemetry context attributes.

        Example:
            ```python
            from opentelemetry import trace

            context = WorkflowContext(workflow_id="wf-123", session_id="sess-456")
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
```

### 1.2 Trace Context Injection

**File:** `packages/tta-dev-observability/src/tta_dev_observability/context/propagation.py`

```python
"""W3C Trace Context propagation for WorkflowContext."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tta_dev_primitives.core.base import WorkflowContext

try:
    from opentelemetry import trace
    from opentelemetry.trace import SpanContext, TraceFlags

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    # When OpenTelemetry is unavailable, graceful degradation occurs:
    # - inject_trace_context() returns context unchanged
    # - extract_trace_context() returns None
    # - create_linked_span() creates spans without parent linkage

logger = logging.getLogger(__name__)


def inject_trace_context(context: WorkflowContext) -> WorkflowContext:
    """
    Inject current OpenTelemetry trace context into WorkflowContext.

    Args:
        context: WorkflowContext to inject trace info into

    Returns:
        Updated context with trace information

    Example:
        ```python
        from tta_dev_primitives.core.base import WorkflowContext

        # At workflow entry point (e.g., HTTP handler)
        context = WorkflowContext(workflow_id="process-123")
        context = inject_trace_context(context)  # Injects current span info

        # Now context.trace_id and context.span_id are populated
        result = await workflow.execute(data, context)
        ```
    """
    if not TRACING_AVAILABLE:
        return context

    current_span = trace.get_current_span()
    if not current_span or not current_span.is_recording():
        return context

    span_context = current_span.get_span_context()
    if not span_context.is_valid:
        return context

    # Inject W3C Trace Context
    context.trace_id = format(span_context.trace_id, '032x')
    context.span_id = format(span_context.span_id, '016x')
    context.trace_flags = span_context.trace_flags

    logger.debug(
        f"Injected trace context: trace_id={context.trace_id}, "
        f"span_id={context.span_id}"
    )

    return context


def extract_trace_context(context: WorkflowContext) -> SpanContext | None:
    """
    Extract OpenTelemetry SpanContext from WorkflowContext.

    Args:
        context: WorkflowContext with trace information

    Returns:
        SpanContext if valid trace info present, None otherwise
    """
    if not TRACING_AVAILABLE:
        return None

    if not context.trace_id or not context.span_id:
        return None

    try:
        trace_id = int(context.trace_id, 16)
        span_id = int(context.span_id, 16)
        trace_flags = TraceFlags(context.trace_flags)

        return SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            is_remote=True,
            trace_flags=trace_flags,
        )
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to extract trace context: {e}")
        return None


def create_linked_span(
    tracer: trace.Tracer,
    name: str,
    context: WorkflowContext,
    **kwargs
) -> trace.Span:
    """
    Create a span linked to the trace context in WorkflowContext.

    Args:
        tracer: OpenTelemetry tracer
        name: Span name
        context: WorkflowContext with trace information
        **kwargs: Additional span creation arguments

    Returns:
        New span linked to parent context
    """
    parent_context = extract_trace_context(context)

    if parent_context:
        # Create span with explicit parent
        span = tracer.start_span(
            name,
            context=trace.set_span_in_context(
                trace.NonRecordingSpan(parent_context)
            ),
            **kwargs
        )
    else:
        # Create new root span
        span = tracer.start_span(name, **kwargs)

    # Add workflow context attributes
    for key, value in context.to_otel_context().items():
        span.set_attribute(key, value)

    # Update context with new span info
    span_context = span.get_span_context()
    context.span_id = format(span_context.span_id, '016x')
    if not context.trace_id:
        context.trace_id = format(span_context.trace_id, '032x')

    return span
```

### 1.3 Auto-Instrumented Base Primitive

**File:** `packages/tta-dev-observability/src/tta_dev_observability/instrumentation/base.py`

```python
"""Auto-instrumented workflow primitive base class."""

from __future__ import annotations

import logging
import time
from typing import Any, TypeVar

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
    - Metrics collection
    - Error tracking

    Example:
        ```python
        class MyPrimitive(InstrumentedPrimitive[dict, dict]):
            async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
                # Your logic here
                return {"result": "success"}
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
        """
        # Inject trace context if not present
        if TRACING_AVAILABLE and self._tracer:
            context = inject_trace_context(context)

        start_time = time.time()

        # Create span
        if self._tracer:
            span = create_linked_span(
                self._tracer,
                f"{self.name}.execute",
                context,
                attributes={
                    "primitive.name": self.name,
                    "primitive.type": self.__class__.__name__,
                }
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
                        }
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
                        exc_info=True
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
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _execute_impl"
        )
```

---

## Phase 2: Core Primitive Instrumentation

### 2.1 Instrumented SequentialPrimitive

**File:** `platform/primitives/src/tta_dev_primitives/core/sequential.py`

Add instrumentation to existing SequentialPrimitive:

```python
async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
    """Execute primitives sequentially with instrumentation."""

    # Record start checkpoint
    context.checkpoint("sequential_start")

    result = input_data
    for idx, primitive in enumerate(self.primitives):
        step_name = f"step_{idx}_{primitive.__class__.__name__}"

        # Log step start
        logger.info(
            "sequential_step_start",
            step=idx,
            total_steps=len(self.primitives),
            primitive=primitive.__class__.__name__,
            workflow_id=context.workflow_id,
        )

        # Execute step
        result = await primitive.execute(result, context)

        # Record checkpoint
        context.checkpoint(step_name)

        # Log step completion
        logger.info(
            "sequential_step_complete",
            step=idx,
            total_steps=len(self.primitives),
            primitive=primitive.__class__.__name__,
            elapsed_ms=context.elapsed_ms(),
            workflow_id=context.workflow_id,
        )

    # Record end checkpoint
    context.checkpoint("sequential_end")

    return result
```

### 2.2 Instrumented ParallelPrimitive

**File:** `platform/primitives/src/tta_dev_primitives/core/parallel.py`

```python
import asyncio  # Required for parallel execution

async def execute(self, input_data: Any, context: WorkflowContext) -> list[Any]:
    """Execute primitives in parallel with instrumentation."""

    # Record start checkpoint (uses WorkflowContext.checkpoint from Section 1.1)
    context.checkpoint("parallel_start")

    logger.info(
        "parallel_execution_start",
        branch_count=len(self.primitives),
        workflow_id=context.workflow_id,
    )

    # Create child contexts for each branch
    child_contexts = [context.create_child_context() for _ in self.primitives]

    # Execute all branches
    tasks = [
        primitive.execute(input_data, child_ctx)
        for primitive, child_ctx in zip(self.primitives, child_contexts)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Check for exceptions
    exceptions = [r for r in results if isinstance(r, Exception)]
    if exceptions:
        logger.error(
            "parallel_execution_failed",
            failed_count=len(exceptions),
            total_count=len(self.primitives),
            workflow_id=context.workflow_id,
        )
        raise exceptions[0]  # Raise first exception

    # Record end checkpoint
    context.checkpoint("parallel_end")

    logger.info(
        "parallel_execution_complete",
        branch_count=len(self.primitives),
        elapsed_ms=context.elapsed_ms(),
        workflow_id=context.workflow_id,
    )

    return results
```

---

## Phase 3: Testing

### 3.1 Test Trace Context Propagation

**File:** `platform/primitives/tests/observability/test_context_propagation.py`

```python
"""Tests for trace context propagation."""

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_observability.context.propagation import (
    extract_trace_context,
    inject_trace_context,
)


@pytest.mark.asyncio
async def test_inject_trace_context():
    """Test trace context injection."""
    context = WorkflowContext(workflow_id="test")

    # Should not fail even without active span
    updated = inject_trace_context(context)
    assert updated.workflow_id == "test"


@pytest.mark.asyncio
async def test_extract_trace_context():
    """Test trace context extraction."""
    context = WorkflowContext(
        workflow_id="test",
        trace_id="0123456789abcdef0123456789abcdef",
        span_id="0123456789abcdef",
    )

    span_context = extract_trace_context(context)
    # Should extract valid span context or None
    assert span_context is None or span_context.is_valid


@pytest.mark.asyncio
async def test_child_context_creation():
    """Test child context preserves trace info."""
    parent = WorkflowContext(
        workflow_id="parent",
        trace_id="abc123",
        span_id="def456",
    )

    child = parent.create_child_context()

    assert child.workflow_id == parent.workflow_id
    assert child.trace_id == parent.trace_id
    assert child.parent_span_id == parent.span_id
    assert child.correlation_id == parent.correlation_id
```

---

## Next Steps

1. **Review this implementation guide**
2. **Create feature branch:** `feature/observability-foundation`
3. **Implement Phase 1** (trace context propagation)
4. **Write comprehensive tests** (target: 80% coverage)
5. **Create PR and get review**
6. **Proceed to Phase 2** (primitive instrumentation)

**Estimated Timeline:**
- Phase 1: 2-3 weeks
- Phase 2: 2-3 weeks
- Phase 3: 1 week (testing)

**Total:** 5-7 weeks for production-ready observability foundation
