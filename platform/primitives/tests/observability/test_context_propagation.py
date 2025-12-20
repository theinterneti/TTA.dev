"""Tests for trace context propagation."""

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.observability.context_propagation import (
    extract_trace_context,
    inject_trace_context,
)


@pytest.mark.asyncio
async def test_inject_trace_context_without_otel() -> None:
    """Test trace context injection without OpenTelemetry."""
    context = WorkflowContext(workflow_id="test")

    # Should not fail even without active span
    updated = inject_trace_context(context)
    assert updated.workflow_id == "test"
    # Without OTel, trace fields should remain None
    assert updated.trace_id is None
    assert updated.span_id is None


@pytest.mark.asyncio
async def test_extract_trace_context_with_valid_ids() -> None:
    """Test trace context extraction with valid trace IDs."""
    context = WorkflowContext(
        workflow_id="test",
        trace_id="0123456789abcdef0123456789abcdef",  # 32 hex chars
        span_id="0123456789abcdef",  # 16 hex chars
    )

    # Should extract valid span context
    span_context = extract_trace_context(context)
    assert span_context is not None
    assert span_context.is_valid
    assert span_context.is_remote is True


@pytest.mark.asyncio
async def test_workflow_context_new_fields() -> None:
    """Test that WorkflowContext has all new observability fields."""
    context = WorkflowContext(workflow_id="test")

    # Trace context fields
    assert hasattr(context, "trace_id")
    assert hasattr(context, "span_id")
    assert hasattr(context, "parent_span_id")
    assert hasattr(context, "trace_flags")

    # Correlation fields
    assert hasattr(context, "correlation_id")
    assert hasattr(context, "causation_id")

    # Metadata fields
    assert hasattr(context, "baggage")
    assert hasattr(context, "tags")

    # Timing fields
    assert hasattr(context, "start_time")
    assert hasattr(context, "checkpoints")

    # Verify defaults
    assert context.trace_id is None
    assert context.span_id is None
    assert context.parent_span_id is None
    assert context.trace_flags == 1  # Sampled by default
    assert context.correlation_id is not None  # Auto-generated
    assert context.causation_id is None
    assert context.baggage == {}
    assert context.tags == {}
    assert context.checkpoints == []


@pytest.mark.asyncio
async def test_workflow_context_checkpoint() -> None:
    """Test checkpoint recording."""
    context = WorkflowContext(workflow_id="test")

    # Record checkpoints
    context.checkpoint("start")
    context.checkpoint("middle")
    context.checkpoint("end")

    # Verify checkpoints
    assert len(context.checkpoints) == 3
    assert context.checkpoints[0][0] == "start"
    assert context.checkpoints[1][0] == "middle"
    assert context.checkpoints[2][0] == "end"

    # Verify timestamps are increasing
    assert context.checkpoints[0][1] <= context.checkpoints[1][1]
    assert context.checkpoints[1][1] <= context.checkpoints[2][1]


@pytest.mark.asyncio
async def test_workflow_context_elapsed_ms() -> None:
    """Test elapsed time calculation."""
    import asyncio

    context = WorkflowContext(workflow_id="test")

    # Wait a bit
    await asyncio.sleep(0.1)

    # Check elapsed time
    elapsed = context.elapsed_ms()
    assert elapsed >= 100  # At least 100ms
    assert elapsed < 200  # But not too much more


@pytest.mark.asyncio
async def test_workflow_context_create_child() -> None:
    """Test child context creation."""
    parent = WorkflowContext(
        workflow_id="parent",
        session_id="session1",
        player_id="player1",
        metadata={"key": "value"},
        state={"count": 1},
        trace_id="abc123",
        span_id="def456",
        correlation_id="corr123",
        baggage={"user": "test"},
        tags={"env": "dev"},
    )

    # Create child
    child = parent.create_child_context()

    # Verify inheritance
    assert child.workflow_id == parent.workflow_id
    assert child.session_id == parent.session_id
    assert child.player_id == parent.player_id
    assert child.metadata == parent.metadata
    assert child.state == parent.state

    # Verify trace context inheritance
    assert child.trace_id == parent.trace_id
    assert child.parent_span_id == parent.span_id  # Parent span becomes parent
    assert child.correlation_id == parent.correlation_id  # Inherited
    assert child.causation_id == parent.correlation_id  # Chained

    # Verify metadata inheritance
    assert child.baggage == parent.baggage
    assert child.tags == parent.tags

    # Verify child has its own span_id (not set yet)
    assert child.span_id is None


@pytest.mark.asyncio
async def test_workflow_context_to_otel_context() -> None:
    """Test conversion to OpenTelemetry context attributes."""
    context = WorkflowContext(
        workflow_id="wf123",
        session_id="sess456",
        player_id="player789",
        correlation_id="corr123",
    )

    # Convert to OTel attributes
    attrs = context.to_otel_context()

    # Verify attributes
    assert attrs["workflow.id"] == "wf123"
    assert attrs["workflow.session_id"] == "sess456"
    assert attrs["workflow.player_id"] == "player789"
    assert attrs["workflow.correlation_id"] == "corr123"
    assert "workflow.elapsed_ms" in attrs
    assert isinstance(attrs["workflow.elapsed_ms"], float)


@pytest.mark.asyncio
async def test_workflow_context_defaults() -> None:
    """Test that WorkflowContext can be created with minimal args."""
    context = WorkflowContext()

    # Should have auto-generated correlation_id
    assert context.correlation_id is not None
    assert len(context.correlation_id) > 0

    # Should have default values
    assert context.workflow_id is None
    assert context.session_id is None
    assert context.player_id is None
    assert context.metadata == {}
    assert context.state == {}
    assert context.trace_flags == 1


@pytest.mark.asyncio
async def test_workflow_context_correlation_id_unique() -> None:
    """Test that each context gets a unique correlation_id."""
    context1 = WorkflowContext()
    context2 = WorkflowContext()

    # Should be different
    assert context1.correlation_id != context2.correlation_id


@pytest.mark.asyncio
async def test_workflow_context_baggage_and_tags() -> None:
    """Test baggage and tags functionality."""
    context = WorkflowContext(
        baggage={"user_id": "123", "tenant": "acme"},
        tags={"env": "prod", "region": "us-west"},
    )

    # Verify baggage
    assert context.baggage["user_id"] == "123"
    assert context.baggage["tenant"] == "acme"

    # Verify tags
    assert context.tags["env"] == "prod"
    assert context.tags["region"] == "us-west"

    # Modify baggage
    context.baggage["session"] = "abc"
    assert context.baggage["session"] == "abc"

    # Modify tags
    context.tags["version"] = "1.0"
    assert context.tags["version"] == "1.0"
