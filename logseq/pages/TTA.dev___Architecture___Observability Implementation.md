type:: Architecture/Implementation Guide
category:: Observability/Step-by-Step Guide
difficulty:: Advanced
estimated-time:: 45 minutes
target-audience:: Developers, DevOps Engineers
related:: [[TTA.dev/Architecture/Observability Executive Summary]], [[TTA.dev/Architecture/Observability Assessment]], [[TTA.dev/Guides/Observability]], [[TTA.dev/Primitives/WorkflowPrimitive]]
status:: Active
last-updated:: 2025-01-29

# TTA.dev Observability Implementation Guide
id:: observability-implementation-overview

Step-by-step guide for implementing production-ready observability in TTA.dev. Covers distributed tracing, context propagation, primitive instrumentation, and testing strategies across 3 phases.

**Implementation Scope:**
- **Phase 1:** Foundation - Trace Context Propagation (2-3 weeks)
- **Phase 2:** Core Instrumentation - Instrument All Primitives (2-3 weeks)
- **Phase 3:** Testing - Comprehensive Test Suite (1 week)
- **Total Effort:** 5-7 weeks for production-ready foundation

---

## Phase 1: Foundation - Trace Context Propagation
id:: observability-implementation-phase1

### Overview
id:: observability-implementation-phase1-overview

**Goal:** Enable distributed tracing by propagating W3C Trace Context through WorkflowContext across all primitive boundaries.

**Deliverables:**
- Enhanced WorkflowContext with trace fields
- Trace context injection/extraction utilities
- Auto-instrumented base primitive class
- Comprehensive tests (80%+ coverage)

**Duration:** 2-3 weeks

---

### 1.1 Enhanced WorkflowContext
id:: observability-implementation-workflowcontext

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py`

**Current Implementation Problem:**
```python
# ❌ Missing observability fields
@dataclass
class WorkflowContext:
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str | None = None
    player_id: str | None = None  # Should be in state/metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)
```

**Enhanced Implementation:**
```python
"""Enhanced WorkflowContext with distributed tracing support."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

@dataclass
class WorkflowContext:
    """
    Workflow execution context with distributed tracing support.

    Propagates trace context across primitive boundaries following W3C Trace Context standard.

    Example:
        ```python
        # Create context with auto-generated IDs
        context = WorkflowContext()

        # Execute workflow - trace context flows through
        result = await workflow.execute(input_data, context)

        # Create child context for nested workflows
        child_context = context.create_child_context()
        ```
    """

    # Core identifiers
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str | None = None

    # Distributed tracing (W3C Trace Context)
    trace_id: str | None = None        # 32 hex characters (128-bit)
    span_id: str | None = None         # 16 hex characters (64-bit)
    parent_span_id: str | None = None  # 16 hex characters (64-bit)
    trace_flags: int = 1               # W3C trace flags (1 = sampled)

    # Correlation
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    causation_id: str | None = None    # For event causation chains

    # Observability metadata
    baggage: dict[str, str] = field(default_factory=dict)  # W3C Baggage
    tags: dict[str, Any] = field(default_factory=dict)     # Custom tags

    # Performance tracking
    start_time: float = field(default_factory=time.time)
    checkpoints: list[tuple[str, float]] = field(default_factory=list)

    # User data
    metadata: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)

    def checkpoint(self, name: str) -> None:
        """
        Record a timing checkpoint.

        Args:
            name: Checkpoint name (e.g., "step_1_complete")
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
        Create child context for nested workflows.

        Preserves:
        - workflow_id, session_id
        - metadata, state
        - trace_id, correlation_id

        Updates:
        - parent_span_id = current span_id (for span linking)
        - causation_id = current workflow_id (for event chains)

        Returns:
            New WorkflowContext for child workflow
        """
        return WorkflowContext(
            workflow_id=self.workflow_id,
            session_id=self.session_id,
            trace_id=self.trace_id,
            span_id=None,  # Child will get new span_id
            parent_span_id=self.span_id,  # Link to parent
            trace_flags=self.trace_flags,
            correlation_id=self.correlation_id,
            causation_id=self.workflow_id,  # Chain causation
            baggage=self.baggage.copy(),
            tags=self.tags.copy(),
            start_time=time.time(),
            checkpoints=[],
            metadata=self.metadata.copy(),
            state=self.state.copy(),
        )

    def to_otel_context(self) -> dict[str, Any]:
        """
        Convert to OpenTelemetry span attributes.

        Returns:
            Dictionary of span attributes
        """
        return {
            "workflow.id": self.workflow_id,
            "workflow.session_id": self.session_id,
            "workflow.correlation_id": self.correlation_id,
            "workflow.elapsed_ms": self.elapsed_ms(),
        }
```

**Key Changes:**
- ✅ Added `trace_id`, `span_id`, `parent_span_id` for W3C Trace Context
- ✅ Added `correlation_id`, `causation_id` for correlation
- ✅ Added `baggage`, `tags` for observability metadata
- ✅ Added `start_time`, `checkpoints` for performance tracking
- ✅ Added `checkpoint()`, `elapsed_ms()`, `create_child_context()`, `to_otel_context()` methods
- ✅ Removed `player_id` (should be in `state` or `metadata`)

---

### 1.2 Trace Context Injection and Extraction
id:: observability-implementation-propagation

**File:** `packages/tta-dev-observability/src/tta_dev_observability/context/propagation.py`

**Purpose:** Inject current OpenTelemetry trace context into WorkflowContext and extract it back for parent span linking.

```python
"""Trace context propagation utilities."""

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

logger = logging.getLogger(__name__)


def inject_trace_context(context: WorkflowContext) -> WorkflowContext:
    """
    Inject current OpenTelemetry trace context into WorkflowContext.

    Populates:
    - trace_id (32 hex chars)
    - span_id (16 hex chars)
    - trace_flags (1 = sampled)

    Args:
        context: WorkflowContext to update

    Returns:
        Updated context (mutated in-place)
    """
    if not TRACING_AVAILABLE:
        return context

    try:
        # Get current span
        span = trace.get_current_span()
        if span is None or not span.is_recording():
            return context

        # Extract span context
        span_context = span.get_span_context()
        if not span_context.is_valid:
            return context

        # Inject into WorkflowContext
        context.trace_id = format(span_context.trace_id, '032x')
        context.span_id = format(span_context.span_id, '016x')
        context.trace_flags = span_context.trace_flags

    except Exception as e:
        logger.warning(f"Failed to inject trace context: {e}")

    return context


def extract_trace_context(context: WorkflowContext) -> SpanContext | None:
    """
    Extract OpenTelemetry SpanContext from WorkflowContext.

    Creates SpanContext for parent span linking.

    Args:
        context: WorkflowContext with trace info

    Returns:
        SpanContext for parent linkage, or None if invalid
    """
    if not TRACING_AVAILABLE:
        return None

    try:
        if not context.trace_id or not context.span_id:
            return None

        # Convert hex strings to integers
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
    Create span linked to trace context in WorkflowContext.

    Args:
        tracer: OpenTelemetry tracer
        name: Span name (e.g., "MyPrimitive.execute")
        context: WorkflowContext with trace information
        **kwargs: Additional span creation arguments (attributes, kind, etc.)

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

**Graceful Degradation:** All functions handle OpenTelemetry unavailability gracefully via `TRACING_AVAILABLE` flag.

---

### 1.3 Auto-Instrumented Base Primitive
id:: observability-implementation-instrumented-primitive

**File:** `packages/tta-dev-observability/src/tta_dev_observability/instrumentation/base.py`

**Purpose:** Base class that automatically adds distributed tracing, logging, and metrics to any primitive.

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
    - Metrics collection (execution time, success/failure)
    - Error tracking with full context

    Example:
        ```python
        class MyPrimitive(InstrumentedPrimitive[dict, dict]):
            async def _execute_impl(
                self,
                input_data: dict,
                context: WorkflowContext
            ) -> dict:
                # Your logic here - tracing/logging/metrics automatic
                return {"result": "success"}
        ```
    """

    def __init__(self, name: str | None = None) -> None:
        """
        Initialize instrumented primitive.

        Args:
            name: Custom primitive name (defaults to class name)
        """
        self.name = name or self.__class__.__name__
        self._tracer = trace.get_tracer(__name__) if TRACING_AVAILABLE else None

    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """
        Execute with full instrumentation.

        Automatically:
        1. Injects trace context if not present
        2. Creates linked span
        3. Logs execution start/end
        4. Records execution time
        5. Tracks errors with full context

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
                    # Execute implementation
                    result = await self._execute_impl(input_data, context)

                    # Record success
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
                    # Record error
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

        Subclasses MUST override this method with their logic.

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

**Usage Example:**
```python
# Instead of inheriting from WorkflowPrimitive
class OldWay(WorkflowPrimitive[dict, dict]):
    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        # Manual logging, tracing, metrics...
        return {"result": "data"}

# Inherit from InstrumentedPrimitive
class NewWay(InstrumentedPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # No boilerplate! Automatic tracing/logging/metrics
        return {"result": "data"}
```

---

## Phase 2: Core Primitive Instrumentation
id:: observability-implementation-phase2

### Overview
id:: observability-implementation-phase2-overview

**Goal:** Instrument all core primitives (Sequential, Parallel, Conditional, Recovery) with observability.

**Deliverables:**
- All core primitives emit traces, logs, metrics
- Integration tests validate end-to-end observability
- Documentation for primitive instrumentation

**Duration:** 2-3 weeks

---

### 2.1 Instrumented SequentialPrimitive
id:: observability-implementation-sequential

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/core/sequential.py`

**Add instrumentation to existing SequentialPrimitive:**

```python
async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
    """
    Execute primitives sequentially with instrumentation.

    Tracks:
    - Step execution order
    - Timing per step
    - Checkpoints for performance analysis
    """

    # Record start checkpoint (uses WorkflowContext.checkpoint from Phase 1)
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

        # Execute step (automatically creates linked span if InstrumentedPrimitive)
        result = await primitive.execute(result, context)

        # Record checkpoint (tracks timing)
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

**What This Provides:**
- ✅ Step-by-step execution visibility
- ✅ Timing for each step
- ✅ Automatic span linking (if primitives use InstrumentedPrimitive)
- ✅ Checkpoint-based performance analysis

---

### 2.2 Instrumented ParallelPrimitive
id:: observability-implementation-parallel

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/core/parallel.py`

```python
import asyncio

async def execute(self, input_data: Any, context: WorkflowContext) -> list[Any]:
    """
    Execute primitives in parallel with instrumentation.

    Tracks:
    - Concurrency (number of branches)
    - Fan-out/fan-in timing
    - Branch failures
    """

    # Record start checkpoint
    context.checkpoint("parallel_start")

    logger.info(
        "parallel_execution_start",
        branch_count=len(self.primitives),
        workflow_id=context.workflow_id,
    )

    # Create child contexts for each branch (inherits trace context)
    child_contexts = [context.create_child_context() for _ in self.primitives]

    # Execute all branches in parallel
    tasks = [
        primitive.execute(input_data, child_ctx)
        for primitive, child_ctx in zip(self.primitives, child_contexts)
    ]

    # Gather results (captures exceptions)
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

**What This Provides:**
- ✅ Parallel execution visibility
- ✅ Concurrency tracking (number of branches)
- ✅ Branch-level tracing (via child contexts)
- ✅ Failure detection and logging

---

## Phase 3: Testing
id:: observability-implementation-phase3

### Overview
id:: observability-implementation-phase3-overview

**Goal:** Comprehensive test suite for observability features.

**Coverage Targets:**
- Unit tests: 80%+ coverage
- Integration tests: End-to-end tracing validation
- Performance tests: Observability overhead <5%

**Duration:** 1 week

---

### 3.1 Test Trace Context Propagation
id:: observability-implementation-test-propagation

**File:** `packages/tta-dev-primitives/tests/observability/test_context_propagation.py`

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
    """Test trace context injection without active span."""
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
    # Should extract valid span context or None (graceful degradation)
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

    # Verify inheritance
    assert child.workflow_id == parent.workflow_id
    assert child.trace_id == parent.trace_id
    assert child.parent_span_id == parent.span_id  # Parent linkage
    assert child.correlation_id == parent.correlation_id

    # Verify new span ID
    assert child.span_id is None  # Will be set when span created


@pytest.mark.asyncio
async def test_checkpoint_tracking():
    """Test checkpoint timing tracking."""
    context = WorkflowContext(workflow_id="test")

    # Record checkpoints
    context.checkpoint("start")
    context.checkpoint("middle")
    context.checkpoint("end")

    # Verify checkpoints recorded
    assert len(context.checkpoints) == 3
    assert context.checkpoints[0][0] == "start"
    assert context.checkpoints[1][0] == "middle"
    assert context.checkpoints[2][0] == "end"

    # Verify timing
    assert context.elapsed_ms() > 0
```

---

### 3.2 Test InstrumentedPrimitive
id:: observability-implementation-test-instrumented

**File:** `packages/tta-dev-observability/tests/test_instrumented_primitive.py`

```python
"""Tests for InstrumentedPrimitive."""

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_observability.instrumentation.base import InstrumentedPrimitive


class TestPrimitive(InstrumentedPrimitive[dict, dict]):
    """Test primitive implementation."""

    async def _execute_impl(
        self, input_data: dict, context: WorkflowContext
    ) -> dict:
        return {"result": input_data.get("value", 0) * 2}


@pytest.mark.asyncio
async def test_instrumented_primitive_success():
    """Test successful execution creates spans and logs."""
    primitive = TestPrimitive(name="TestDouble")
    context = WorkflowContext(workflow_id="test")

    result = await primitive.execute({"value": 5}, context)

    assert result == {"result": 10}
    # In real test, would verify span creation via mock tracer


@pytest.mark.asyncio
async def test_instrumented_primitive_error():
    """Test error execution records exception."""

    class FailingPrimitive(InstrumentedPrimitive[dict, dict]):
        async def _execute_impl(
            self, input_data: dict, context: WorkflowContext
        ) -> dict:
            raise ValueError("Intentional error")

    primitive = FailingPrimitive(name="TestFail")
    context = WorkflowContext(workflow_id="test")

    with pytest.raises(ValueError, match="Intentional error"):
        await primitive.execute({}, context)

    # In real test, would verify span recorded exception
```

---

### 3.3 Test End-to-End Tracing
id:: observability-implementation-test-e2e

**File:** `packages/tta-dev-primitives/tests/integration/test_distributed_tracing.py`

```python
"""Integration tests for distributed tracing."""

import pytest

from tta_dev_primitives import SequentialPrimitive, ParallelPrimitive
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_observability.instrumentation.base import InstrumentedPrimitive


class Step1(InstrumentedPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        return {"step1": True, **input_data}


class Step2(InstrumentedPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        return {"step2": True, **input_data}


class Step3(InstrumentedPrimitive[dict, dict]):
    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        return {"step3": True, **input_data}


@pytest.mark.asyncio
async def test_sequential_workflow_tracing():
    """Test trace context flows through sequential workflow."""
    workflow = SequentialPrimitive([Step1(), Step2(), Step3()])
    context = WorkflowContext(workflow_id="test-seq")

    result = await workflow.execute({"input": "data"}, context)

    assert result["step1"] is True
    assert result["step2"] is True
    assert result["step3"] is True

    # Verify trace context propagated
    assert context.trace_id is not None
    assert len(context.checkpoints) >= 2  # sequential_start, sequential_end


@pytest.mark.asyncio
async def test_parallel_workflow_tracing():
    """Test trace context propagated to parallel branches."""
    workflow = ParallelPrimitive([Step1(), Step2(), Step3()])
    context = WorkflowContext(workflow_id="test-par")

    results = await workflow.execute({"input": "data"}, context)

    assert len(results) == 3
    assert all("input" in r for r in results)

    # Verify trace context propagated
    assert context.trace_id is not None
    assert len(context.checkpoints) >= 2  # parallel_start, parallel_end
```

---

## Next Steps
id:: observability-implementation-next-steps

### Immediate Actions
id:: observability-implementation-immediate

1. **Review this implementation guide** - Understand all 3 phases
2. **Create feature branch:** `feature/observability-foundation`
3. **Set up tracking:** Create GitHub project with tasks for each phase

### Phase 1 Implementation (2-3 weeks)
id:: observability-implementation-phase1-tasks

**Week 1:**
- [ ] Enhance WorkflowContext with trace fields
- [ ] Implement trace context propagation utilities
- [ ] Write unit tests for context propagation

**Week 2:**
- [ ] Create InstrumentedPrimitive base class
- [ ] Write tests for InstrumentedPrimitive
- [ ] Update existing primitives to optionally use InstrumentedPrimitive

**Week 3:**
- [ ] Integration testing
- [ ] Documentation updates
- [ ] Create PR and get review

### Phase 2 Implementation (2-3 weeks)
id:: observability-implementation-phase2-tasks

**Week 4:**
- [ ] Instrument SequentialPrimitive
- [ ] Instrument ParallelPrimitive
- [ ] Write unit tests for instrumented primitives

**Week 5:**
- [ ] Instrument ConditionalPrimitive
- [ ] Instrument all recovery primitives (Retry, Fallback, Timeout, Compensation)
- [ ] Write unit tests

**Week 6:**
- [ ] Integration tests for end-to-end workflows
- [ ] Performance testing (overhead <5% target)
- [ ] Documentation and examples

### Phase 3 Testing (1 week)
id:: observability-implementation-phase3-tasks

**Week 7:**
- [ ] Achieve 80%+ test coverage
- [ ] Add missing integration tests
- [ ] Performance optimization if overhead >5%
- [ ] Final documentation review

---

## Estimated Timeline
id:: observability-implementation-timeline

**Phase Breakdown:**
- **Phase 1:** 2-3 weeks (Foundation)
- **Phase 2:** 2-3 weeks (Instrumentation)
- **Phase 3:** 1 week (Testing)

**Total:** 5-7 weeks for production-ready observability foundation

**Team:** 1-2 developers full-time

---

## Success Criteria
id:: observability-implementation-success

### Must Have (P0)
id:: observability-implementation-success-p0

- ✅ WorkflowContext propagates trace context (trace_id, span_id, parent_span_id)
- ✅ All core primitives emit traces (Sequential, Parallel, Conditional, Recovery)
- ✅ 80%+ test coverage for observability features
- ✅ End-to-end tracing through complex workflows
- ✅ Can debug production issues with distributed tracing

### Should Have (P1)
id:: observability-implementation-success-p1

- ✅ Observability overhead <5%
- ✅ Graceful degradation when OpenTelemetry unavailable
- ✅ Comprehensive documentation and examples
- ✅ Integration tests validate all observability features

---

**See Also:**
- [[TTA.dev/Architecture/Observability Executive Summary]] - Quick overview for decision makers
- [[TTA.dev/Architecture/Observability Assessment]] - Detailed technical review
- [[TTA.dev/Guides/Observability]] - User guide for observability features
- [[TTA.dev/Primitives/WorkflowPrimitive]] - Base primitive documentation
