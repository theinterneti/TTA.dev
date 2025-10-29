"""Tests for Prometheus metrics exporter."""

import pytest

from tta_dev_primitives.observability.metrics import (
    EnhancedMetricsCollector,
    SLOConfig,
)
from tta_dev_primitives.observability.prometheus import (
    PROMETHEUS_AVAILABLE,
    PrometheusExporter,
    get_prometheus_exporter,
)


class TestPrometheusExporter:
    """Tests for PrometheusExporter."""

    def test_initialization(self) -> None:
        """Test exporter initialization."""
        collector = EnhancedMetricsCollector()
        exporter = PrometheusExporter(collector)
        
        # Should initialize without errors
        assert exporter is not None

    def test_record_execution(self) -> None:
        """Test recording execution metrics."""
        exporter = PrometheusExporter()
        
        # Should not raise errors even if prometheus not available
        exporter.record_execution(
            primitive_name="test",
            primitive_type="TestPrimitive",
            duration_ms=100.0,
            success=True,
            cost=0.05,
        )

    def test_update_gauges(self) -> None:
        """Test updating gauge metrics."""
        collector = EnhancedMetricsCollector()
        exporter = PrometheusExporter(collector)
        
        # Configure SLO
        slo_config = SLOConfig(
            name="test_latency",
            target=0.95,
            threshold_ms=1000.0,
        )
        collector.configure_slo("test", slo_config)
        
        # Record some executions
        for i in range(10):
            collector.record_execution("test", 500.0, True)
        
        # Update gauges
        metrics = collector.get_all_metrics("test")
        exporter.update_gauges("test", metrics)

    def test_record_savings(self) -> None:
        """Test recording cost savings."""
        exporter = PrometheusExporter()
        
        # Should not raise errors
        exporter.record_savings("test", 1.0)

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_get_metrics_text(self) -> None:
        """Test getting metrics in Prometheus format."""
        exporter = PrometheusExporter()
        
        # Record some metrics
        exporter.record_execution(
            primitive_name="test",
            primitive_type="TestPrimitive",
            duration_ms=100.0,
            success=True,
        )
        
        # Get metrics text
        metrics_text = exporter.get_metrics_text()
        
        assert isinstance(metrics_text, bytes)
        assert len(metrics_text) > 0

    def test_get_metrics_text_without_prometheus(self) -> None:
        """Test getting metrics when prometheus not available."""
        exporter = PrometheusExporter()
        
        # Should return placeholder even if prometheus not available
        metrics_text = exporter.get_metrics_text()
        
        assert isinstance(metrics_text, bytes)

    def test_cardinality_control(self) -> None:
        """Test cardinality limit enforcement."""
        exporter = PrometheusExporter()
        
        # Record many unique label combinations
        for i in range(PrometheusExporter.MAX_LABEL_CARDINALITY + 10):
            exporter.record_execution(
                primitive_name=f"test_{i}",
                primitive_type="TestPrimitive",
                duration_ms=100.0,
                success=True,
            )
        
        # Check cardinality stats
        stats = exporter.get_cardinality_stats()
        
        # Should not exceed limit
        assert stats["total"] <= PrometheusExporter.MAX_LABEL_CARDINALITY

    def test_cardinality_stats(self) -> None:
        """Test cardinality statistics."""
        exporter = PrometheusExporter()
        
        # Record some metrics
        exporter.record_execution("test1", "TestPrimitive", 100.0, True)
        exporter.record_execution("test2", "TestPrimitive", 200.0, True)
        
        # Get stats
        stats = exporter.get_cardinality_stats()
        
        assert "total" in stats
        assert "max_allowed" in stats
        assert "by_metric" in stats
        assert stats["max_allowed"] == PrometheusExporter.MAX_LABEL_CARDINALITY

    def test_global_singleton(self) -> None:
        """Test global singleton accessor."""
        exporter1 = get_prometheus_exporter()
        exporter2 = get_prometheus_exporter()
        
        # Should be same instance
        assert exporter1 is exporter2

    def test_export_metrics(self) -> None:
        """Test exporting metrics in structured format."""
        exporter = PrometheusExporter()
        
        # Export metrics
        metrics = exporter.export_metrics()
        
        # Should return a dict (even if empty)
        assert isinstance(metrics, dict)

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_histogram_buckets(self) -> None:
        """Test that histogram uses correct buckets."""
        exporter = PrometheusExporter()
        
        # Record executions with various durations
        durations = [0.5, 5.0, 50.0, 500.0, 5000.0]  # ms
        
        for duration in durations:
            exporter.record_execution(
                primitive_name="test",
                primitive_type="TestPrimitive",
                duration_ms=duration,
                success=True,
            )
        
        # Get metrics text and verify it contains histogram data
        metrics_text = exporter.get_metrics_text().decode("utf-8")
        
        assert "primitive_duration_seconds" in metrics_text
        assert "bucket" in metrics_text

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_counter_increments(self) -> None:
        """Test that counters increment correctly."""
        exporter = PrometheusExporter()
        
        # Record multiple executions
        for i in range(5):
            exporter.record_execution(
                primitive_name="test",
                primitive_type="TestPrimitive",
                duration_ms=100.0,
                success=True,
            )
        
        # Get metrics text
        metrics_text = exporter.get_metrics_text().decode("utf-8")
        
        assert "primitive_requests_total" in metrics_text

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_gauge_updates(self) -> None:
        """Test that gauges update correctly."""
        collector = EnhancedMetricsCollector()
        exporter = PrometheusExporter(collector)
        
        # Start some requests
        collector.start_request("test")
        collector.start_request("test")
        
        # Record executions
        collector.record_execution("test", 100.0, True)
        
        # Update gauges
        metrics = collector.get_all_metrics("test")
        exporter.update_gauges("test", metrics)
        
        # Get metrics text
        metrics_text = exporter.get_metrics_text().decode("utf-8")
        
        assert "primitive_active_requests" in metrics_text or "primitive_requests_per_second" in metrics_text

    def test_integration_with_collector(self) -> None:
        """Test integration with EnhancedMetricsCollector."""
        collector = EnhancedMetricsCollector()
        exporter = PrometheusExporter(collector)
        
        # Configure SLO
        slo_config = SLOConfig(
            name="test_latency",
            target=0.95,
            threshold_ms=1000.0,
        )
        collector.configure_slo("test", slo_config)
        
        # Record executions through collector
        for i in range(100):
            collector.start_request("test")
            collector.record_execution("test", 500.0, True, cost=0.01)
        
        # Update Prometheus gauges
        metrics = collector.get_all_metrics("test")
        exporter.update_gauges("test", metrics)
        
        # Record metrics in Prometheus
        exporter.record_execution("test", "TestPrimitive", 500.0, True, cost=0.01)
        
        # Should complete without errors
        assert True
