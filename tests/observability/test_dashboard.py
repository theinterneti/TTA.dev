"""Tests for the observability dashboard."""

import sys
from pathlib import Path

import pytest
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

# Add tta-dev to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tta-dev"))

from observability.dashboard import ObservabilityDashboard


class TestObservabilityDashboard(AioHTTPTestCase):
    """Test ObservabilityDashboard class."""

    async def get_application(self):
        """Create test application."""
        dashboard = ObservabilityDashboard()
        return dashboard.app

    @unittest_run_loop
    async def test_health_endpoint(self):
        """Test health endpoint returns healthy status."""
        resp = await self.client.get("/api/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    @unittest_run_loop
    async def test_metrics_initial_state(self):
        """Test metrics endpoint returns initial state."""
        resp = await self.client.get("/api/metrics")
        assert resp.status == 200
        data = await resp.json()
        assert data["total_workflows"] == 0
        assert data["successful_workflows"] == 0
        assert data["failed_workflows"] == 0
        assert data["avg_duration_ms"] == 0.0

    @unittest_run_loop
    async def test_traces_initial_empty(self):
        """Test traces endpoint returns empty list initially."""
        resp = await self.client.get("/api/traces")
        assert resp.status == 200
        data = await resp.json()
        assert data["traces"] == []

    @unittest_run_loop
    async def test_index_returns_html(self):
        """Test index endpoint returns HTML."""
        resp = await self.client.get("/")
        assert resp.status == 200
        assert resp.content_type == "text/html"
        text = await resp.text()
        assert "TTA.dev Observability Dashboard" in text


@pytest.mark.asyncio
async def test_record_trace_updates_metrics():
    """Test that recording traces updates metrics correctly."""
    dashboard = ObservabilityDashboard()

    # Record successful trace
    dashboard.record_trace("trace-1", 100.0, "success")

    assert dashboard.metrics["total_workflows"] == 1
    assert dashboard.metrics["successful_workflows"] == 1
    assert dashboard.metrics["failed_workflows"] == 0
    assert dashboard.metrics["avg_duration_ms"] == 100.0

    # Record another successful trace
    dashboard.record_trace("trace-2", 200.0, "success")

    assert dashboard.metrics["total_workflows"] == 2
    assert dashboard.metrics["successful_workflows"] == 2
    assert dashboard.metrics["avg_duration_ms"] == 150.0

    # Record failed trace
    dashboard.record_trace("trace-3", 50.0, "error")

    assert dashboard.metrics["total_workflows"] == 3
    assert dashboard.metrics["successful_workflows"] == 2
    assert dashboard.metrics["failed_workflows"] == 1
    assert dashboard.metrics["avg_duration_ms"] == pytest.approx(116.67, rel=0.01)


@pytest.mark.asyncio
async def test_traces_truncated_at_maxlen():
    """Test that traces are capped at max_traces."""
    dashboard = ObservabilityDashboard(max_traces=5)

    # Add 10 traces
    for i in range(10):
        dashboard.record_trace(f"trace-{i}", 100.0, "success")

    # Should only keep last 5
    assert len(dashboard.traces) == 5
    assert dashboard.traces[0]["trace_id"] == "trace-5"
    assert dashboard.traces[-1]["trace_id"] == "trace-9"

    # Metrics should reflect all 10 workflows
    assert dashboard.metrics["total_workflows"] == 10


@pytest.mark.asyncio
async def test_timestamp_uses_utc():
    """Test that timestamps are timezone-aware UTC."""
    dashboard = ObservabilityDashboard()
    dashboard.record_trace("trace-1", 100.0, "success")

    trace = dashboard.traces[0]
    # Should end with '+00:00' for UTC timezone
    assert "+00:00" in trace["timestamp"]
