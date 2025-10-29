"""Tests for Phase 3 enhanced metrics."""

import time

import pytest

from tta_dev_primitives.observability.metrics import (
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

    def test_empty_percentiles(self) -> None:
        """Test percentiles with no data."""
        metrics = PercentileMetrics()
        assert metrics.get_percentile(0.95) == 0.0
        stats = metrics.get_stats()
        assert stats["p50"] == 0.0
        assert stats["count"] == 0

    def test_single_value(self) -> None:
        """Test percentiles with single value."""
        metrics = PercentileMetrics()
        metrics.record(100.0)
        
        assert metrics.get_percentile(0.50) == 100.0
        assert metrics.get_percentile(0.95) == 100.0
        assert metrics.get_percentile(0.99) == 100.0

    def test_multiple_values(self) -> None:
        """Test percentiles with multiple values."""
        metrics = PercentileMetrics()
        
        # Record 100 values from 1 to 100
        for i in range(1, 101):
            metrics.record(float(i))
        
        stats = metrics.get_stats()
        
        # Check percentiles are in reasonable ranges
        assert 45 <= stats["p50"] <= 55  # Median around 50
        assert 85 <= stats["p90"] <= 95  # p90 around 90
        assert 90 <= stats["p95"] <= 100  # p95 around 95
        assert 95 <= stats["p99"] <= 100  # p99 around 99
        assert stats["count"] == 100

    def test_window_size_limit(self) -> None:
        """Test that window size limits are enforced."""
        metrics = PercentileMetrics(window_size=10)
        
        # Record 20 values
        for i in range(20):
            metrics.record(float(i))
        
        stats = metrics.get_stats()
        # Should only keep last 10 values
        assert stats["count"] == 10


class TestSLOMetrics:
    """Tests for SLOMetrics."""

    def test_latency_slo_compliance(self) -> None:
        """Test latency-based SLO compliance."""
        config = SLOConfig(
            name="api_latency",
            target=0.95,  # 95% under threshold
            threshold_ms=1000.0,
            window_seconds=60.0,
        )
        slo = SLOMetrics(config)
        
        # Record 100 requests: 96 under threshold, 4 over
        for i in range(96):
            slo.record_request(success=True, latency_ms=500.0)
        for i in range(4):
            slo.record_request(success=True, latency_ms=1500.0)
        
        # Should meet SLO (96% > 95%)
        assert slo.get_compliance() >= 0.95
        assert slo.get_error_budget() > 0.0

    def test_availability_slo_compliance(self) -> None:
        """Test availability-based SLO compliance."""
        config = SLOConfig(
            name="api_availability",
            target=0.999,  # 99.9% success rate
            threshold_ms=None,  # No latency threshold
            window_seconds=60.0,
        )
        slo = SLOMetrics(config)
        
        # Record 1000 requests: 999 successful, 1 failed
        for i in range(999):
            slo.record_request(success=True)
        slo.record_request(success=False)
        
        # Should meet SLO (99.9% = 0.999)
        compliance = slo.get_compliance()
        assert compliance >= 0.999

    def test_slo_violation(self) -> None:
        """Test SLO violation detection."""
        config = SLOConfig(
            name="api_latency",
            target=0.95,
            threshold_ms=1000.0,
            window_seconds=60.0,
        )
        slo = SLOMetrics(config)
        
        # Record 100 requests: 90 under threshold, 10 over
        for i in range(90):
            slo.record_request(success=True, latency_ms=500.0)
        for i in range(10):
            slo.record_request(success=True, latency_ms=1500.0)
        
        # Should violate SLO (90% < 95%)
        assert slo.get_compliance() < 0.95
        # Error budget should be consumed
        assert slo.get_error_budget() < 1.0

    def test_error_budget_calculation(self) -> None:
        """Test error budget calculation."""
        config = SLOConfig(
            name="api_latency",
            target=0.95,
            threshold_ms=1000.0,
            window_seconds=60.0,
        )
        slo = SLOMetrics(config)
        
        # Record 100 requests: all under threshold
        for i in range(100):
            slo.record_request(success=True, latency_ms=500.0)
        
        # Error budget should be full
        assert slo.get_error_budget() == 1.0

    def test_slo_stats(self) -> None:
        """Test SLO statistics."""
        config = SLOConfig(
            name="test_slo",
            target=0.95,
            threshold_ms=1000.0,
            window_seconds=60.0,
        )
        slo = SLOMetrics(config)
        
        slo.record_request(success=True, latency_ms=500.0)
        slo.record_request(success=True, latency_ms=1500.0)
        
        stats = slo.get_stats()
        assert stats["name"] == "test_slo"
        assert stats["target"] == 0.95
        assert "compliance" in stats
        assert "error_budget" in stats
        assert stats["total_requests"] == 2


class TestThroughputMetrics:
    """Tests for ThroughputMetrics."""

    def test_active_requests(self) -> None:
        """Test active request tracking."""
        throughput = ThroughputMetrics()
        
        assert throughput.get_active_requests() == 0
        
        throughput.start_request()
        assert throughput.get_active_requests() == 1
        
        throughput.start_request()
        assert throughput.get_active_requests() == 2
        
        throughput.end_request()
        assert throughput.get_active_requests() == 1
        
        throughput.end_request()
        assert throughput.get_active_requests() == 0

    def test_rps_calculation(self) -> None:
        """Test requests per second calculation."""
        throughput = ThroughputMetrics(window_seconds=1.0)
        
        # Record several requests
        for i in range(10):
            throughput.start_request()
            throughput.end_request()
        
        # RPS should be positive
        rps = throughput.get_rps()
        assert rps > 0

    def test_throughput_stats(self) -> None:
        """Test throughput statistics."""
        throughput = ThroughputMetrics()
        
        throughput.start_request()
        
        stats = throughput.get_stats()
        assert "rps" in stats
        assert "active_requests" in stats
        assert stats["active_requests"] == 1


class TestCostMetrics:
    """Tests for CostMetrics."""

    def test_cost_tracking(self) -> None:
        """Test cost tracking."""
        cost = CostMetrics()
        
        assert cost.get_total_cost() == 0.0
        
        cost.record_cost(1.5)
        assert cost.get_total_cost() == 1.5
        
        cost.record_cost(2.5)
        assert cost.get_total_cost() == 4.0

    def test_savings_tracking(self) -> None:
        """Test savings tracking."""
        cost = CostMetrics()
        
        assert cost.get_total_savings() == 0.0
        
        cost.record_savings(1.0)
        assert cost.get_total_savings() == 1.0
        
        cost.record_savings(2.0)
        assert cost.get_total_savings() == 3.0

    def test_savings_rate(self) -> None:
        """Test savings rate calculation."""
        cost = CostMetrics()
        
        # No cost or savings yet
        assert cost.get_savings_rate() == 0.0
        
        # Record cost and savings
        cost.record_cost(5.0)  # $5 spent
        cost.record_savings(5.0)  # $5 saved
        
        # Savings rate should be 50% (5/(5+5))
        assert cost.get_savings_rate() == 0.5

    def test_cost_stats(self) -> None:
        """Test cost statistics."""
        cost = CostMetrics()
        
        cost.record_cost(10.0)
        cost.record_savings(5.0)
        
        stats = cost.get_stats()
        assert stats["total_cost"] == 10.0
        assert stats["total_savings"] == 5.0
        assert stats["savings_rate"] == 5.0 / 15.0


class TestEnhancedMetricsCollector:
    """Tests for EnhancedMetricsCollector."""

    def test_record_execution(self) -> None:
        """Test recording execution with enhanced metrics."""
        collector = EnhancedMetricsCollector()
        
        collector.record_execution(
            primitive_name="test",
            duration_ms=100.0,
            success=True,
            cost=0.05,
        )
        
        metrics = collector.get_all_metrics("test")
        
        # Check basic metrics
        assert metrics["basic"]["total_executions"] == 1
        assert metrics["basic"]["successful_executions"] == 1
        
        # Check percentile metrics
        assert "percentiles" in metrics
        assert metrics["percentiles"]["count"] == 1
        
        # Check cost metrics
        assert "cost" in metrics
        assert metrics["cost"]["total_cost"] == 0.05

    def test_slo_tracking(self) -> None:
        """Test SLO tracking through collector."""
        collector = EnhancedMetricsCollector()
        
        # Configure SLO
        slo_config = SLOConfig(
            name="test_latency",
            target=0.95,
            threshold_ms=1000.0,
        )
        collector.configure_slo("test", slo_config)
        
        # Record executions
        for i in range(96):
            collector.record_execution("test", 500.0, True)
        for i in range(4):
            collector.record_execution("test", 1500.0, True)
        
        metrics = collector.get_all_metrics("test")
        
        # Check SLO compliance
        assert "slo" in metrics
        assert metrics["slo"]["compliance"] >= 0.95

    def test_throughput_tracking(self) -> None:
        """Test throughput tracking through collector."""
        collector = EnhancedMetricsCollector()
        
        # Start requests
        collector.start_request("test")
        collector.start_request("test")
        
        # Record executions
        collector.record_execution("test", 100.0, True)
        collector.record_execution("test", 200.0, True)
        
        metrics = collector.get_all_metrics("test")
        
        # Check throughput metrics
        assert "throughput" in metrics
        assert metrics["throughput"]["active_requests"] == 0  # Both ended

    def test_savings_recording(self) -> None:
        """Test savings recording through collector."""
        collector = EnhancedMetricsCollector()
        
        # Record cost and savings
        collector.record_execution("test", 100.0, True, cost=1.0)
        collector.record_savings("test", 1.0)
        
        metrics = collector.get_all_metrics("test")
        
        # Check cost metrics
        assert metrics["cost"]["total_cost"] == 1.0
        assert metrics["cost"]["total_savings"] == 1.0
        assert metrics["cost"]["savings_rate"] == 0.5

    def test_global_singleton(self) -> None:
        """Test global singleton accessor."""
        collector1 = get_enhanced_metrics_collector()
        collector2 = get_enhanced_metrics_collector()
        
        # Should be same instance
        assert collector1 is collector2
        
        # Record in one, should be available in other
        collector1.record_execution("test", 100.0, True)
        metrics = collector2.get_all_metrics("test")
        
        assert metrics["basic"]["total_executions"] == 1
