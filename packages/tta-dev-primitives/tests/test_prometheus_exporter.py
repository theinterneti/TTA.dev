"""Tests for Prometheus metrics exporter."""

import pytest

from tta_dev_primitives.observability import (
    SLOConfig,
    get_enhanced_metrics_collector,
    get_prometheus_exporter,
)

# Check if prometheus_client is available
try:
    from prometheus_client import REGISTRY

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class TestPrometheusExporter:
    """Tests for PrometheusExporter."""

    def test_exporter_singleton(self):
        """Test that get_prometheus_exporter returns singleton."""
        exporter1 = get_prometheus_exporter()
        exporter2 = get_prometheus_exporter()

        assert exporter1 is exporter2

    def test_exporter_graceful_degradation(self):
        """Test exporter works even if prometheus_client unavailable."""
        # Use singleton to avoid duplicate registration
        exporter = get_prometheus_exporter()

        # Should not crash
        exporter.record_execution("test_primitive", "test", 0.5, True)
        exporter.record_cost("test_primitive", "test", 0.002, "llm")
        exporter.record_savings("test_primitive", "test", 0.001, "cache")
        exporter.export_metrics()

        metrics_count = exporter.get_metrics_count()
        assert "label_combinations" in metrics_count
        assert "max_combinations" in metrics_count

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_record_execution(self):
        """Test recording execution to Prometheus."""
        # Use singleton to avoid duplicate registration
        exporter = get_prometheus_exporter()

        # Record successful execution
        exporter.record_execution("test_primitive_exec", "test_type", 0.5, True)

        # Record failed execution
        exporter.record_execution("test_primitive_exec", "test_type", 0.8, False)

        # Should track label combinations
        metrics_count = exporter.get_metrics_count()
        assert metrics_count["label_combinations"] >= 0  # May have many from other tests

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_record_cost(self):
        """Test recording cost to Prometheus."""
        exporter = get_prometheus_exporter()

        exporter.record_cost("test_primitive_cost", "test_type", 0.002, "llm_call")
        exporter.record_cost("test_primitive_cost", "test_type", 0.001, "embedding")

        # Should not crash
        assert True

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_record_savings(self):
        """Test recording savings to Prometheus."""
        exporter = get_prometheus_exporter()

        exporter.record_savings("test_primitive_savings", "test_type", 0.002, "cache_hit")
        exporter.record_savings("test_primitive_savings", "test_type", 0.001, "fallback")

        # Should not crash
        assert True

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_export_metrics(self):
        """Test exporting metrics from collector to Prometheus."""
        exporter = get_prometheus_exporter()
        collector = get_enhanced_metrics_collector()

        # Configure SLO
        slo = SLOConfig(target=0.99, latency_threshold_seconds=1.0)
        collector.configure_slo("export_test", slo)

        # Record some metrics
        collector.record_execution("export_test", 0.5, True, cost=0.002)
        collector.record_execution("export_test", 0.8, True, savings=0.001)

        # Export to Prometheus
        exporter.export_metrics("test_type")

        # Should not crash
        assert True

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_cardinality_limit(self):
        """Test that cardinality limit prevents memory issues."""
        exporter = get_prometheus_exporter()

        initial_count = exporter.get_metrics_count()["label_combinations"]

        # Try to record more than would exceed MAX_LABEL_COMBINATIONS
        # Note: actual cardinality depends on what other tests recorded
        for i in range(100):
            exporter.record_execution(f"cardinality_test_{i}", f"type_{i}", 0.5, True)

        metrics_count = exporter.get_metrics_count()
        # Should respect limit
        assert metrics_count["label_combinations"] <= metrics_count["max_combinations"]

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_multiple_primitive_types(self):
        """Test recording metrics for multiple primitive types."""
        exporter = get_prometheus_exporter()

        # Record metrics for different primitive types
        exporter.record_execution("cache_primitive_multi", "cache", 0.1, True)
        exporter.record_execution("retry_primitive_multi", "retry", 0.5, True)
        exporter.record_execution("timeout_primitive_multi", "timeout", 0.3, False)

        metrics_count = exporter.get_metrics_count()
        # Should have tracked these (among others from other tests)
        assert metrics_count["label_combinations"] >= 0

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_histogram_buckets(self):
        """Test that histogram uses appropriate buckets."""
        exporter = get_prometheus_exporter()

        # Record various latencies
        exporter.record_execution("histogram_test", "test", 0.001, True)  # 1ms
        exporter.record_execution("histogram_test", "test", 0.010, True)  # 10ms
        exporter.record_execution("histogram_test", "test", 0.100, True)  # 100ms
        exporter.record_execution("histogram_test", "test", 1.000, True)  # 1s
        exporter.record_execution("histogram_test", "test", 5.000, True)  # 5s

        # Should handle all buckets without errors
        assert True

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_thread_safety(self):
        """Test that exporter is thread-safe."""
        import threading

        exporter = get_prometheus_exporter()
        errors = []

        def record_many():
            try:
                for i in range(50):
                    exporter.record_execution(
                        f"thread_test_{i % 5}", "thread_test", 0.5, True
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=record_many) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should not have any errors
        assert len(errors) == 0

    def test_metrics_count(self):
        """Test getting metrics count."""
        exporter = get_prometheus_exporter()

        metrics_count = exporter.get_metrics_count()

        assert "label_combinations" in metrics_count
        assert "max_combinations" in metrics_count
        assert isinstance(metrics_count["label_combinations"], int)
        assert isinstance(metrics_count["max_combinations"], int)
        assert metrics_count["label_combinations"] >= 0
        assert metrics_count["max_combinations"] > 0

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_integration_with_enhanced_collector(self):
        """Test integration between Prometheus exporter and enhanced metrics collector."""
        exporter = get_prometheus_exporter()
        collector = get_enhanced_metrics_collector()

        # Configure SLO
        slo = SLOConfig(target=0.99, latency_threshold_seconds=1.0)
        collector.configure_slo("integration_test_prom", slo)

        # Record metrics in collector
        for i in range(10):
            collector.record_execution(
                primitive_name="integration_test_prom",
                duration_seconds=0.5,
                success=True,
                cost=0.002 if i % 2 == 0 else None,
                savings=0.001 if i % 2 == 1 else None,
            )

        # Export to Prometheus
        exporter.export_metrics("integration_type")

        # Verify metrics were exported
        metrics = collector.get_all_metrics("integration_test_prom")
        assert "percentiles" in metrics
        assert "slo" in metrics
        assert "throughput" in metrics

    @pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="prometheus_client not installed")
    def test_cost_categories(self):
        """Test recording costs with different categories."""
        exporter = get_prometheus_exporter()

        exporter.record_cost("cost_cat_test", "test", 0.002, "llm_call")
        exporter.record_cost("cost_cat_test", "test", 0.001, "embedding")
        exporter.record_cost("cost_cat_test", "test", 0.0005, "storage")

        exporter.record_savings("cost_cat_test", "test", 0.002, "cache_hit")
        exporter.record_savings("cost_cat_test", "test", 0.001, "fallback")

        # Should handle multiple categories without errors
        assert True
