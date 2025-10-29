"""Tests for enhanced metrics (percentiles, SLO, throughput, cost)."""

import time

import pytest

from tta_dev_primitives.observability import (
    CostMetrics,
    EnhancedMetricsCollector,
    PercentileMetrics,
    SLOConfig,
    SLOMetrics,
    ThroughputMetrics,
    get_enhanced_metrics_collector,
)


class TestPercentileMetrics:
    """Tests for PercentileMetrics."""

    def test_percentiles_empty(self):
        """Test percentiles with no data."""
        metrics = PercentileMetrics("test")
        percentiles = metrics.get_percentiles()
        
        assert percentiles["p50"] == 0.0
        assert percentiles["p90"] == 0.0
        assert percentiles["p95"] == 0.0
        assert percentiles["p99"] == 0.0

    def test_percentiles_single_value(self):
        """Test percentiles with single value."""
        metrics = PercentileMetrics("test")
        metrics.record_latency(0.5)
        
        percentiles = metrics.get_percentiles()
        assert percentiles["p50"] == 0.5
        assert percentiles["p90"] == 0.5
        assert percentiles["p95"] == 0.5
        assert percentiles["p99"] == 0.5

    def test_percentiles_multiple_values(self):
        """Test percentiles with multiple values."""
        metrics = PercentileMetrics("test")
        
        # Record 100 latencies from 0.0 to 0.99 seconds
        for i in range(100):
            metrics.record_latency(i / 100.0)
        
        percentiles = metrics.get_percentiles()
        
        # p50 should be around 0.5
        assert 0.48 <= percentiles["p50"] <= 0.52
        # p90 should be around 0.9
        assert 0.88 <= percentiles["p90"] <= 0.92
        # p95 should be around 0.95
        assert 0.93 <= percentiles["p95"] <= 0.97
        # p99 should be around 0.99
        assert 0.97 <= percentiles["p99"] <= 1.0

    def test_percentiles_max_samples(self):
        """Test that max_samples limit works."""
        metrics = PercentileMetrics("test", max_samples=10)
        
        # Record more than max_samples
        for i in range(20):
            metrics.record_latency(i / 100.0)
        
        # Should only keep last 10
        assert len(metrics.latencies) == 10
        # Should have values from 0.10 to 0.19
        assert min(metrics.latencies) >= 0.10

    def test_percentiles_reset(self):
        """Test reset clears latencies."""
        metrics = PercentileMetrics("test")
        metrics.record_latency(0.5)
        metrics.record_latency(0.8)
        
        metrics.reset()
        
        assert len(metrics.latencies) == 0
        percentiles = metrics.get_percentiles()
        assert percentiles["p50"] == 0.0


class TestSLOMetrics:
    """Tests for SLOMetrics."""

    def test_slo_empty(self):
        """Test SLO metrics with no data."""
        slo_config = SLOConfig(target=0.99, latency_threshold_seconds=1.0)
        metrics = SLOMetrics("test", slo_config)
        
        status = metrics.get_slo_status()
        
        assert status["slo_compliance"] == 1.0
        assert status["error_budget_remaining"] == 1.0
        assert status["availability"] == 1.0
        assert status["total_requests"] == 0

    def test_slo_all_success(self):
        """Test SLO metrics with all successful requests."""
        slo_config = SLOConfig(target=0.99, latency_threshold_seconds=1.0)
        metrics = SLOMetrics("test", slo_config)
        
        # Record 100 successful requests within SLO
        for _ in range(100):
            metrics.record_request(duration_seconds=0.5, success=True)
        
        status = metrics.get_slo_status()
        
        assert status["slo_compliance"] == 1.0
        assert status["error_budget_remaining"] == 1.0
        assert status["availability"] == 1.0
        assert status["latency_compliance"] == 1.0
        assert status["total_requests"] == 100

    def test_slo_latency_violations(self):
        """Test SLO metrics with latency violations."""
        slo_config = SLOConfig(target=0.99, latency_threshold_seconds=1.0)
        metrics = SLOMetrics("test", slo_config)
        
        # Record 98 fast requests, 2 slow requests
        for _ in range(98):
            metrics.record_request(duration_seconds=0.5, success=True)
        for _ in range(2):
            metrics.record_request(duration_seconds=1.5, success=True)
        
        status = metrics.get_slo_status()
        
        # 98% within SLO (below 99% target)
        assert status["latency_compliance"] == 0.98
        assert status["availability"] == 1.0
        assert status["slo_compliance"] == 0.98  # Min of both
        assert status["latency_violations"] == 2

    def test_slo_availability_violations(self):
        """Test SLO metrics with availability violations."""
        slo_config = SLOConfig(target=0.99, availability_target=0.99)
        metrics = SLOMetrics("test", slo_config)
        
        # Record 97 successful, 3 failed requests
        for _ in range(97):
            metrics.record_request(duration_seconds=0.5, success=True)
        for _ in range(3):
            metrics.record_request(duration_seconds=0.5, success=False)
        
        status = metrics.get_slo_status()
        
        # 97% availability (below 99% target)
        assert status["availability"] == 0.97
        assert status["successful_requests"] == 97
        assert status["total_requests"] == 100

    def test_slo_error_budget(self):
        """Test error budget calculation."""
        slo_config = SLOConfig(target=0.99, latency_threshold_seconds=1.0)
        metrics = SLOMetrics("test", slo_config)
        
        # Target: 99%, Error budget: 1%
        # Record 98 fast, 2 slow (below target)
        for _ in range(98):
            metrics.record_request(duration_seconds=0.5, success=True)
        for _ in range(2):
            metrics.record_request(duration_seconds=1.5, success=True)
        
        status = metrics.get_slo_status()
        
        # At 98% compliance (below 99% target)
        assert status["slo_compliance"] == 0.98
        # Error budget: allowed 1% errors, got 2% errors, so 0% budget remaining
        assert status["error_budget_remaining"] == 0.0

    def test_slo_reset(self):
        """Test reset clears SLO metrics."""
        slo_config = SLOConfig(target=0.99, latency_threshold_seconds=1.0)
        metrics = SLOMetrics("test", slo_config)
        
        metrics.record_request(duration_seconds=0.5, success=True)
        metrics.record_request(duration_seconds=1.5, success=False)
        
        metrics.reset()
        
        status = metrics.get_slo_status()
        assert status["total_requests"] == 0
        assert status["successful_requests"] == 0


class TestThroughputMetrics:
    """Tests for ThroughputMetrics."""

    def test_throughput_empty(self):
        """Test throughput metrics with no data."""
        metrics = ThroughputMetrics("test")
        stats = metrics.get_stats()
        
        assert stats["total_requests"] == 0
        assert stats["active_requests"] == 0
        assert stats["requests_per_second"] == 0.0

    def test_throughput_basic(self):
        """Test basic throughput tracking."""
        metrics = ThroughputMetrics("test")
        
        metrics.record_request_start("req1")
        metrics.record_request_start("req2")
        
        stats = metrics.get_stats()
        assert stats["total_requests"] == 2
        assert stats["active_requests"] == 2
        
        metrics.record_request_end("req1")
        
        stats = metrics.get_stats()
        assert stats["active_requests"] == 1
        
        metrics.record_request_end("req2")
        
        stats = metrics.get_stats()
        assert stats["active_requests"] == 0

    def test_throughput_rps(self):
        """Test requests per second calculation."""
        metrics = ThroughputMetrics("test")
        
        # Record 10 requests
        for i in range(10):
            metrics.record_request_start(f"req{i}")
            metrics.record_request_end(f"req{i}")
        
        stats = metrics.get_stats()
        
        # RPS should be > 0 (depends on execution speed)
        assert stats["requests_per_second"] > 0
        assert stats["total_requests"] == 10

    def test_throughput_window(self):
        """Test throughput window cleanup."""
        metrics = ThroughputMetrics("test")
        metrics._window_seconds = 0.1  # 100ms window
        
        # Record a request
        metrics.record_request_start("req1")
        metrics.record_request_end("req1")
        
        # Wait for window to expire
        time.sleep(0.15)
        
        # Get stats (should clean up old timestamps)
        stats = metrics.get_stats()
        
        # Timestamp should be cleaned up, RPS should be 0
        assert stats["requests_per_second"] == 0.0

    def test_throughput_reset(self):
        """Test reset clears throughput metrics."""
        metrics = ThroughputMetrics("test")
        
        metrics.record_request_start("req1")
        metrics.record_request_start("req2")
        
        metrics.reset()
        
        stats = metrics.get_stats()
        assert stats["total_requests"] == 0
        assert stats["active_requests"] == 0


class TestCostMetrics:
    """Tests for CostMetrics."""

    def test_cost_empty(self):
        """Test cost metrics with no data."""
        metrics = CostMetrics("test")
        stats = metrics.get_stats()
        
        assert stats["total_cost"] == 0.0
        assert stats["total_savings"] == 0.0
        assert stats["net_cost"] == 0.0
        assert stats["savings_rate"] == 0.0

    def test_cost_basic(self):
        """Test basic cost tracking."""
        metrics = CostMetrics("test")
        
        metrics.record_cost(0.002, "llm_call")
        metrics.record_cost(0.001, "llm_call")
        
        stats = metrics.get_stats()
        
        assert stats["total_cost"] == 0.003
        assert stats["cost_breakdown"]["llm_call"] == 0.003

    def test_cost_savings(self):
        """Test cost savings tracking."""
        metrics = CostMetrics("test")
        
        metrics.record_cost(0.002, "llm_call")
        metrics.record_savings(0.002, "cache_hit")
        
        stats = metrics.get_stats()
        
        assert stats["total_cost"] == 0.002
        assert stats["total_savings"] == 0.002
        assert stats["net_cost"] == 0.0
        assert stats["savings_breakdown"]["cache_hit"] == 0.002

    def test_cost_savings_rate(self):
        """Test savings rate calculation."""
        metrics = CostMetrics("test")
        
        # Potential cost: 0.010 (0.006 actual + 0.004 saved)
        metrics.record_cost(0.006, "llm_call")
        metrics.record_savings(0.004, "cache_hit")
        
        stats = metrics.get_stats()
        
        # Savings rate: 0.004 / 0.010 = 40%
        assert stats["savings_rate"] == 0.4

    def test_cost_categories(self):
        """Test cost breakdown by category."""
        metrics = CostMetrics("test")
        
        metrics.record_cost(0.002, "llm_call")
        metrics.record_cost(0.001, "embedding")
        metrics.record_savings(0.002, "cache_hit")
        metrics.record_savings(0.001, "fallback")
        
        stats = metrics.get_stats()
        
        assert stats["cost_breakdown"]["llm_call"] == 0.002
        assert stats["cost_breakdown"]["embedding"] == 0.001
        assert stats["savings_breakdown"]["cache_hit"] == 0.002
        assert stats["savings_breakdown"]["fallback"] == 0.001

    def test_cost_reset(self):
        """Test reset clears cost metrics."""
        metrics = CostMetrics("test")
        
        metrics.record_cost(0.005, "llm_call")
        metrics.record_savings(0.002, "cache_hit")
        
        metrics.reset()
        
        stats = metrics.get_stats()
        assert stats["total_cost"] == 0.0
        assert stats["total_savings"] == 0.0
        assert len(stats["cost_breakdown"]) == 0


class TestEnhancedMetricsCollector:
    """Tests for EnhancedMetricsCollector."""

    def test_collector_singleton(self):
        """Test that get_enhanced_metrics_collector returns singleton."""
        collector1 = get_enhanced_metrics_collector()
        collector2 = get_enhanced_metrics_collector()
        
        assert collector1 is collector2

    def test_collector_record_execution(self):
        """Test recording execution with all metrics."""
        collector = EnhancedMetricsCollector()
        
        # Configure SLO
        slo = SLOConfig(target=0.99, latency_threshold_seconds=1.0)
        collector.configure_slo("test_primitive", slo)
        
        # Record execution
        collector.record_execution(
            primitive_name="test_primitive",
            duration_seconds=0.5,
            success=True,
            cost=0.002,
            savings=0.001,
        )
        
        # Get all metrics
        metrics = collector.get_all_metrics("test_primitive")
        
        assert "percentiles" in metrics
        assert "slo" in metrics
        assert "throughput" in metrics
        assert "cost" in metrics
        
        # Check percentile recorded
        assert metrics["percentiles"]["p50"] == 0.5
        
        # Check SLO recorded
        assert metrics["slo"]["total_requests"] == 1
        assert metrics["slo"]["slo_compliance"] == 1.0
        
        # Check cost recorded
        assert metrics["cost"]["total_cost"] == 0.002
        assert metrics["cost"]["total_savings"] == 0.001

    def test_collector_throughput_tracking(self):
        """Test separate throughput tracking methods."""
        collector = EnhancedMetricsCollector()
        
        collector.record_request_start("test_primitive", "req1")
        metrics = collector.get_all_metrics("test_primitive")
        assert metrics["throughput"]["active_requests"] == 1
        
        collector.record_request_end("test_primitive", "req1")
        metrics = collector.get_all_metrics("test_primitive")
        assert metrics["throughput"]["active_requests"] == 0

    def test_collector_get_all_primitives(self):
        """Test getting metrics for all primitives."""
        collector = EnhancedMetricsCollector()
        
        collector.record_execution("primitive1", 0.5, True)
        collector.record_execution("primitive2", 0.8, True)
        
        all_metrics = collector.get_all_metrics()
        
        assert "primitive1" in all_metrics
        assert "primitive2" in all_metrics

    def test_collector_reset_single(self):
        """Test resetting metrics for single primitive."""
        collector = EnhancedMetricsCollector()
        
        collector.record_execution("primitive1", 0.5, True)
        collector.record_execution("primitive2", 0.8, True)
        
        collector.reset("primitive1")
        
        metrics1 = collector.get_all_metrics("primitive1")
        metrics2 = collector.get_all_metrics("primitive2")
        
        # primitive1 should be reset (empty or zero)
        if "percentiles" in metrics1:
            assert metrics1["percentiles"]["p50"] == 0.0
        # primitive2 should still have data
        assert metrics2["percentiles"]["p50"] == 0.8

    def test_collector_reset_all(self):
        """Test resetting metrics for all primitives."""
        collector = EnhancedMetricsCollector()
        
        collector.record_execution("primitive1", 0.5, True)
        collector.record_execution("primitive2", 0.8, True)
        
        collector.reset()
        
        all_metrics = collector.get_all_metrics()
        
        # All metrics should be reset (or empty)
        for primitive_name, metrics in all_metrics.items():
            percentiles = metrics.get("percentiles", {})
            if percentiles:
                assert percentiles.get("p50", 0.0) == 0.0

    def test_collector_thread_safety(self):
        """Test that collector is thread-safe."""
        import threading
        
        collector = EnhancedMetricsCollector()
        errors = []
        
        def record_many():
            try:
                for i in range(100):
                    collector.record_execution(f"primitive_{i % 5}", 0.5, True)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=record_many) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should not have any errors
        assert len(errors) == 0
        
        # Should have metrics for multiple primitives
        all_metrics = collector.get_all_metrics()
        assert len(all_metrics) > 0
