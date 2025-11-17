"""Tests for storage module."""

from datetime import UTC

import pytest

from tta_observability_ui.models import Span, SpanStatus, Trace, TraceStatus
from tta_observability_ui.storage import TraceStorage


@pytest.mark.asyncio
async def test_storage_initialization():
    """Test storage initialization."""
    storage = TraceStorage(db_path=":memory:")
    await storage.initialize()

    assert storage._initialized


@pytest.mark.asyncio
async def test_save_and_get_trace():
    """Test saving and retrieving a trace."""
    storage = TraceStorage(db_path=":memory:")
    await storage.initialize()

    # Create test trace
    from datetime import datetime

    now = datetime.now(UTC)

    span = Span(
        span_id="span-123",
        trace_id="trace-456",
        primitive_type="TestPrimitive",
        primitive_name="test_operation",
        start_time=now,
        end_time=now,
        duration_ms=100,
        status=SpanStatus.SUCCESS,
    )

    trace = Trace(
        trace_id="trace-456",
        workflow_name="test_workflow",
        start_time=now,
        end_time=now,
        duration_ms=100,
        status=TraceStatus.SUCCESS,
        spans=[span],
    )

    # Save trace
    await storage.save_trace(trace)

    # Retrieve trace
    retrieved = await storage.get_trace("trace-456")
    assert retrieved is not None
    assert retrieved.trace_id == "trace-456"
    assert retrieved.workflow_name == "test_workflow"
    assert len(retrieved.spans) == 1


@pytest.mark.asyncio
async def test_list_traces():
    """Test listing traces."""
    storage = TraceStorage(db_path=":memory:")
    await storage.initialize()

    from datetime import datetime

    now = datetime.now(UTC)

    # Create multiple traces
    for i in range(5):
        trace = Trace(
            trace_id=f"trace-{i}",
            workflow_name=f"workflow-{i}",
            start_time=now,
            end_time=now,
            duration_ms=100,
            status=TraceStatus.SUCCESS,
            spans=[],
        )
        await storage.save_trace(trace)

    # List traces
    traces = await storage.list_traces(limit=3)
    assert len(traces) == 3


@pytest.mark.asyncio
async def test_get_stats():
    """Test getting storage statistics."""
    storage = TraceStorage(db_path=":memory:")
    await storage.initialize()

    stats = await storage.get_stats()
    assert "total_traces" in stats
    assert "success_rate" in stats
    assert "avg_duration_ms" in stats
    assert "primitive_usage" in stats
