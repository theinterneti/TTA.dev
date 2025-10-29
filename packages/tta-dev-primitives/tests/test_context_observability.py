"""Tests for WorkflowContext observability features."""

import time

import pytest

from tta_dev_primitives.core.base import WorkflowContext


@pytest.mark.asyncio
async def test_workflow_context_defaults() -> None:
    """Test WorkflowContext creates with sensible defaults."""
    context = WorkflowContext()

    # Existing fields default to None or empty
    assert context.workflow_id is None
    assert context.session_id is None
    assert context.player_id is None
    assert context.metadata == {}
    assert context.state == {}

    # New trace fields default appropriately
    assert context.trace_id is None
    assert context.span_id is None
    assert context.parent_span_id is None
    assert context.trace_flags == 1  # Default sampled

    # Correlation ID is auto-generated
    assert context.correlation_id is not None
    assert len(context.correlation_id) > 0

    # Causation ID defaults to None
    assert context.causation_id is None

    # Observability metadata defaults
    assert context.baggage == {}
    assert context.tags == {}

    # Performance tracking defaults
    assert context.start_time > 0
    assert context.checkpoints == []


@pytest.mark.asyncio
async def test_workflow_context_with_trace_info() -> None:
    """Test WorkflowContext with explicit trace information."""
    context = WorkflowContext(
        workflow_id="wf-123",
        trace_id="0123456789abcdef0123456789abcdef",
        span_id="0123456789abcdef",
        parent_span_id="fedcba9876543210",
        trace_flags=1,
    )

    assert context.workflow_id == "wf-123"
    assert context.trace_id == "0123456789abcdef0123456789abcdef"
    assert context.span_id == "0123456789abcdef"
    assert context.parent_span_id == "fedcba9876543210"
    assert context.trace_flags == 1


@pytest.mark.asyncio
async def test_checkpoint_recording() -> None:
    """Test checkpoint recording functionality."""
    context = WorkflowContext(workflow_id="test")

    # Initially no checkpoints
    assert len(context.checkpoints) == 0

    # Record checkpoint
    context.checkpoint("step1")
    assert len(context.checkpoints) == 1
    assert context.checkpoints[0][0] == "step1"
    assert context.checkpoints[0][1] > context.start_time

    # Record another checkpoint
    time.sleep(0.01)  # Small delay
    context.checkpoint("step2")
    assert len(context.checkpoints) == 2
    assert context.checkpoints[1][0] == "step2"
    assert context.checkpoints[1][1] > context.checkpoints[0][1]


@pytest.mark.asyncio
async def test_elapsed_ms() -> None:
    """Test elapsed time calculation."""
    context = WorkflowContext()

    # Immediately after creation, elapsed should be very small
    elapsed1 = context.elapsed_ms()
    assert elapsed1 >= 0
    assert elapsed1 < 100  # Less than 100ms

    # After a delay, elapsed should increase
    time.sleep(0.05)  # 50ms delay
    elapsed2 = context.elapsed_ms()
    assert elapsed2 > elapsed1
    assert elapsed2 >= 50  # At least 50ms


@pytest.mark.asyncio
async def test_create_child_context() -> None:
    """Test child context creation preserves trace information."""
    parent = WorkflowContext(
        workflow_id="parent-wf",
        session_id="session-123",
        player_id="player-456",
        trace_id="0123456789abcdef0123456789abcdef",
        span_id="parent-span-id",
        correlation_id="corr-123",
    )
    parent.metadata["key"] = "value"
    parent.state["count"] = 42
    parent.baggage["user"] = "alice"
    parent.tags["env"] = "test"

    # Create child
    child = parent.create_child_context()

    # Basic fields inherited
    assert child.workflow_id == parent.workflow_id
    assert child.session_id == parent.session_id
    assert child.player_id == parent.player_id

    # Trace context inherited and linked
    assert child.trace_id == parent.trace_id
    assert child.parent_span_id == parent.span_id  # Parent span becomes parent
    assert child.correlation_id == parent.correlation_id  # Same correlation
    assert child.causation_id == parent.correlation_id  # Causation chain

    # Metadata and state copied
    assert child.metadata == parent.metadata
    assert child.state == parent.state
    assert child.baggage == parent.baggage
    assert child.tags == parent.tags

    # But they are independent copies
    child.metadata["new_key"] = "new_value"
    assert "new_key" not in parent.metadata


@pytest.mark.asyncio
async def test_to_otel_context() -> None:
    """Test conversion to OpenTelemetry context attributes."""
    context = WorkflowContext(
        workflow_id="wf-123",
        session_id="sess-456",
        player_id="player-789",
        correlation_id="corr-abc",
    )

    otel_attrs = context.to_otel_context()

    # Should contain workflow attributes
    assert otel_attrs["workflow.id"] == "wf-123"
    assert otel_attrs["workflow.session_id"] == "sess-456"
    assert otel_attrs["workflow.player_id"] == "player-789"
    assert otel_attrs["workflow.correlation_id"] == "corr-abc"

    # Should contain elapsed time
    assert "workflow.elapsed_ms" in otel_attrs
    assert otel_attrs["workflow.elapsed_ms"] >= 0


@pytest.mark.asyncio
async def test_to_otel_context_with_none_values() -> None:
    """Test to_otel_context handles None values gracefully."""
    context = WorkflowContext()  # All IDs are None

    otel_attrs = context.to_otel_context()

    # Should use "unknown" for None values
    assert otel_attrs["workflow.id"] == "unknown"
    assert otel_attrs["workflow.session_id"] == "unknown"
    assert otel_attrs["workflow.player_id"] == "unknown"

    # But correlation_id is auto-generated, not None
    assert otel_attrs["workflow.correlation_id"] != "unknown"


@pytest.mark.asyncio
async def test_baggage_and_tags() -> None:
    """Test baggage and tags functionality."""
    context = WorkflowContext()

    # Initially empty
    assert context.baggage == {}
    assert context.tags == {}

    # Add baggage
    context.baggage["user_id"] = "12345"
    context.baggage["tenant"] = "acme"
    assert len(context.baggage) == 2

    # Add tags
    context.tags["env"] = "production"
    context.tags["version"] = "1.0.0"
    assert len(context.tags) == 2


@pytest.mark.asyncio
async def test_correlation_id_uniqueness() -> None:
    """Test that each context gets a unique correlation_id."""
    context1 = WorkflowContext()
    context2 = WorkflowContext()

    # Should be auto-generated and unique
    assert context1.correlation_id != context2.correlation_id
    assert len(context1.correlation_id) > 0
    assert len(context2.correlation_id) > 0


@pytest.mark.asyncio
async def test_backward_compatibility() -> None:
    """Test that existing code without new fields still works."""
    # Old-style context creation (only old fields)
    context = WorkflowContext(
        workflow_id="old-workflow",
        session_id="old-session",
        metadata={"old": "data"},
    )

    # Should work fine with defaults for new fields
    assert context.workflow_id == "old-workflow"
    assert context.session_id == "old-session"
    assert context.metadata == {"old": "data"}

    # New fields have sensible defaults
    assert context.trace_id is None
    assert context.correlation_id is not None  # Auto-generated
    assert context.baggage == {}
