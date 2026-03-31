"""
Test suite for Phase 1: Observability Collector

Following TDD approach - tests first, implementation second.
Tests are based on OBSERVABILITY_UI_SPEC.md Phase 1 requirements.
"""

import asyncio
import json
from datetime import UTC, datetime

import pytest

from ttadev.observability.collector import ObservabilityCollector, TraceEvent


class TestObservabilityCollector:
    """Test the core trace collection functionality."""

    @pytest.fixture
    def temp_trace_dir(self, tmp_path):
        """Create a temporary directory for traces."""
        trace_dir = tmp_path / "traces"
        trace_dir.mkdir()
        return trace_dir

    @pytest.fixture
    def collector(self, temp_trace_dir):
        """Create a collector instance with temp directory."""
        return ObservabilityCollector(trace_dir=temp_trace_dir)

    def test_collector_initialization(self, temp_trace_dir):
        """Test that collector initializes with proper directory structure."""
        collector = ObservabilityCollector(trace_dir=temp_trace_dir)

        assert collector.trace_dir == temp_trace_dir
        assert temp_trace_dir.exists()
        assert (temp_trace_dir / "active").exists()
        assert (temp_trace_dir / "completed").exists()

    @pytest.mark.asyncio
    async def test_record_trace_event(self, collector, temp_trace_dir):
        """Test recording a single trace event."""
        event = TraceEvent(
            trace_id="test-trace-001",
            span_id="span-001",
            event_type="workflow_start",
            timestamp=datetime.now(UTC).isoformat(),
            data={
                "workflow_name": "test_workflow",
                "provider": "github_copilot",
                "model": "claude-sonnet-4.5",
            },
        )

        await collector.record_event(event)

        # Verify event was written to file
        trace_file = temp_trace_dir / "active" / f"{event.trace_id}.jsonl"
        assert trace_file.exists()

        # Verify content
        with open(trace_file) as f:
            recorded = json.loads(f.readline())
            assert recorded["trace_id"] == "test-trace-001"
            assert recorded["event_type"] == "workflow_start"
            assert recorded["data"]["workflow_name"] == "test_workflow"

    @pytest.mark.asyncio
    async def test_complete_trace(self, collector, temp_trace_dir):
        """Test moving trace from active to completed."""
        trace_id = "test-trace-002"

        # Record some events
        events = [
            TraceEvent(
                trace_id=trace_id,
                span_id=f"span-{i}",
                event_type="primitive_execute",
                timestamp=datetime.now(UTC).isoformat(),
                data={"primitive": f"Primitive{i}"},
            )
            for i in range(3)
        ]

        for event in events:
            await collector.record_event(event)

        # Complete the trace
        await collector.complete_trace(trace_id)

        # Verify moved to completed
        active_file = temp_trace_dir / "active" / f"{trace_id}.jsonl"
        completed_file = temp_trace_dir / "completed" / f"{trace_id}.jsonl"

        assert not active_file.exists()
        assert completed_file.exists()

        # Verify all events preserved
        with open(completed_file) as f:
            lines = f.readlines()
            assert len(lines) == 3

    @pytest.mark.asyncio
    async def test_list_active_traces(self, collector):
        """Test listing active trace IDs."""
        # Create multiple active traces
        trace_ids = ["trace-001", "trace-002", "trace-003"]

        for trace_id in trace_ids:
            event = TraceEvent(
                trace_id=trace_id,
                span_id="span-001",
                event_type="workflow_start",
                timestamp=datetime.now(UTC).isoformat(),
                data={},
            )
            await collector.record_event(event)

        # List active traces
        active = await collector.list_active_traces()

        assert len(active) == 3
        assert set(active) == set(trace_ids)

    @pytest.mark.asyncio
    async def test_get_trace_events(self, collector):
        """Test retrieving all events for a trace."""
        trace_id = "test-trace-004"

        # Record events
        events = [
            TraceEvent(
                trace_id=trace_id,
                span_id=f"span-{i}",
                event_type="step",
                timestamp=datetime.now(UTC).isoformat(),
                data={"step": i},
            )
            for i in range(5)
        ]

        for event in events:
            await collector.record_event(event)

        # Retrieve events
        retrieved = await collector.get_trace_events(trace_id)

        assert len(retrieved) == 5
        assert all(e.trace_id == trace_id for e in retrieved)
        assert [e.data["step"] for e in retrieved] == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_concurrent_writes(self, collector):
        """Test that concurrent writes don't corrupt data."""
        trace_id = "concurrent-trace"

        # Simulate concurrent writes
        async def write_events(start_idx):
            for i in range(start_idx, start_idx + 10):
                event = TraceEvent(
                    trace_id=trace_id,
                    span_id=f"span-{i}",
                    event_type="concurrent_test",
                    timestamp=datetime.now(UTC).isoformat(),
                    data={"index": i},
                )
                await collector.record_event(event)

        # Run 3 concurrent writers
        await asyncio.gather(write_events(0), write_events(10), write_events(20))

        # Verify all 30 events recorded
        events = await collector.get_trace_events(trace_id)
        assert len(events) == 30

        # Verify no duplicates or corruption
        indices = [e.data["index"] for e in events]
        assert len(set(indices)) == 30
