"""Tests for Prometheus metrics exporter."""

from __future__ import annotations

import pytest

from tta_dev_primitives.observability.enhanced_collector import (
    get_enhanced_metrics_collector,
)

# Check if prometheus_client is available
try:
    from tta_dev_primitives.observability.prometheus_exporter import (
        PrometheusExporter,
        get_prometheus_exporter,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

pytestmark = pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")


class TestPrometheusExporter:
    """Test Prometheus metrics exporter."""

    def test_exporter_initialization(self):
        """Test exporter initializes correctly."""
        exporter = PrometheusExporter()
        assert exporter.namespace == "tta"
        assert exporter.subsystem == "workflow"
        assert exporter.max_label_cardinality == 1000
        assert exporter.registry is not None

    def test_custom_namespace_subsystem(self):
        """Test custom namespace and subsystem."""
        exporter = PrometheusExporter(namespace="custom", subsystem="test")
        assert exporter.namespace == "custom"
        assert exporter.subsystem == "test"

    def test_metrics_initialization(self):
        """Test Prometheus metrics are initialized."""
        exporter = PrometheusExporter()
        assert exporter.latency_histogram is not None
        assert exporter.slo_compliance is not None
        assert exporter.error_budget is not None
        assert exporter.request_total is not None
        assert exporter.active_requests is not None
        assert exporter.cost_total is not None
        assert exporter.savings_total is not None
        assert exporter.build_info is not None

    def test_cardinality_check(self):
        """Test label cardinality checking."""
        exporter = PrometheusExporter(max_label_cardinality=2)

        # First two combinations should succeed
        assert exporter._check_cardinality(("label1", "value1"))
        assert exporter._check_cardinality(("label2", "value2"))

        # Third should fail (exceeds limit)
        assert not exporter._check_cardinality(("label3", "value3"))

        # Existing combination should still succeed
        assert exporter._check_cardinality(("label1", "value1"))

    def test_update_percentile_metrics(self):
        """Test updating percentile metrics."""
        collector = get_enhanced_metrics_collector()
        collector.reset()

        # Record some executions
        collector.record_execution("test_primitive", duration_ms=100.0, success=True)
        collector.record_execution("test_primitive", duration_ms=200.0, success=True)
        collector.record_execution("test_primitive", duration_ms=300.0, success=True)

        # Export to Prometheus
        exporter = PrometheusExporter()
        exporter.update_metrics()

        # Verify histogram was updated
        metrics_text = exporter.export().decode("utf-8")
        assert "tta_workflow_primitive_duration_seconds" in metrics_text
        assert 'primitive_name="test_primitive"' in metrics_text

    def test_update_slo_metrics(self):
        """Test updating SLO metrics."""
        collector = get_enhanced_metrics_collector()
        collector.reset()

        # Configure SLO
        collector.configure_slo("test_primitive", target=0.99, error_rate_threshold=0.01)

        # Record executions
        for _ in range(99):
            collector.record_execution("test_primitive", duration_ms=100.0, success=True)
        collector.record_execution("test_primitive", duration_ms=100.0, success=False)  # 1 failure

        # Export to Prometheus
        exporter = PrometheusExporter()
        exporter.update_metrics()

        # Verify SLO metrics
        metrics_text = exporter.export().decode("utf-8")
        assert "tta_workflow_slo_compliance_ratio" in metrics_text
        assert "tta_workflow_error_budget_remaining" in metrics_text

    def test_update_throughput_metrics(self):
        """Test updating throughput metrics."""
        collector = get_enhanced_metrics_collector()
        collector.reset()

        # Start some requests
        collector.start_request("test_primitive")
        collector.start_request("test_primitive")

        # Export to Prometheus
        exporter = PrometheusExporter()
        exporter.update_metrics()

        # Verify throughput metrics
        metrics_text = exporter.export().decode("utf-8")
        assert "tta_workflow_active_requests" in metrics_text
        assert 'primitive_name="test_primitive"' in metrics_text

    def test_update_cost_metrics(self):
        """Test updating cost metrics."""
        collector = get_enhanced_metrics_collector()
        collector.reset()

        # Record costs
        collector.record_execution("test_primitive", duration_ms=100.0, success=True, cost=0.50)
        collector.record_execution("test_primitive", duration_ms=100.0, success=True, savings=0.25)

        # Export to Prometheus
        exporter = PrometheusExporter()
        exporter.update_metrics()

        # Verify cost metrics
        metrics_text = exporter.export().decode("utf-8")
        assert "tta_workflow_cost_total" in metrics_text
        assert "tta_workflow_savings_total" in metrics_text

    def test_export_format(self):
        """Test export returns valid Prometheus format."""
        collector = get_enhanced_metrics_collector()
        collector.reset()

        # Record some data
        collector.record_execution("test_primitive", duration_ms=100.0, success=True)

        # Export
        exporter = PrometheusExporter()
        metrics_bytes = exporter.export()

        # Verify format
        assert isinstance(metrics_bytes, bytes)
        metrics_text = metrics_bytes.decode("utf-8")
        assert "# HELP" in metrics_text
        assert "# TYPE" in metrics_text

    def test_build_info(self):
        """Test build info is exported."""
        exporter = PrometheusExporter()
        metrics_text = exporter.export().decode("utf-8")

        assert "tta_workflow_build_info" in metrics_text
        assert 'version="0.1.0"' in metrics_text
        assert 'package="tta-dev-primitives"' in metrics_text

    def test_global_exporter(self):
        """Test global exporter singleton."""
        exporter1 = get_prometheus_exporter()
        exporter2 = get_prometheus_exporter()

        assert exporter1 is exporter2

    def test_cardinality_limit_prevents_explosion(self):
        """Test cardinality limit prevents metric explosion."""
        collector = get_enhanced_metrics_collector()
        collector.reset()

        # Create exporter with low limit
        exporter = PrometheusExporter(max_label_cardinality=5)

        # Try to create many unique primitives
        for i in range(10):
            collector.record_execution(f"primitive_{i}", duration_ms=100.0, success=True)

        # Update metrics (should respect cardinality limit)
        exporter.update_metrics()

        # Verify we didn't exceed limit
        assert len(exporter._label_combinations) <= 5

    def test_multiple_operations_cost_tracking(self):
        """Test cost tracking for multiple operations."""
        collector = get_enhanced_metrics_collector()
        collector.reset()

        # Record costs for different operations
        collector.record_execution(
            "test_primitive",
            duration_ms=100.0,
            success=True,
            cost=0.10,
            operation="llm",
        )
        collector.record_execution(
            "test_primitive",
            duration_ms=100.0,
            success=True,
            cost=0.05,
            operation="cache",
        )

        # Export
        exporter = PrometheusExporter()
        exporter.update_metrics()
        metrics_text = exporter.export().decode("utf-8")

        # Verify both operations are tracked
        assert 'operation="llm"' in metrics_text
        assert 'operation="cache"' in metrics_text

    def test_histogram_buckets(self):
        """Test histogram has appropriate buckets."""
        exporter = PrometheusExporter()

        # Verify histogram was created
        assert exporter.latency_histogram is not None

        # Record a value and verify it works
        exporter.latency_histogram.labels(
            primitive_name="test", primitive_type="primitive"
        ).observe(0.5)

        # Export and verify histogram is present
        metrics_text = exporter.export().decode("utf-8")
        assert "tta_workflow_primitive_duration_seconds" in metrics_text

    def test_reset_collector_clears_metrics(self):
        """Test resetting collector clears exported metrics."""
        collector = get_enhanced_metrics_collector()
        collector.reset()

        # Record data
        collector.record_execution("test_primitive", duration_ms=100.0, success=True)

        # Export
        exporter = PrometheusExporter()
        exporter.update_metrics()
        metrics1 = exporter.export().decode("utf-8")

        # Reset and export again
        collector.reset()
        exporter2 = PrometheusExporter()
        exporter2.update_metrics()
        metrics2 = exporter2.export().decode("utf-8")

        # Metrics should be different (second should have no data)
        assert len(metrics1) > len(metrics2)
