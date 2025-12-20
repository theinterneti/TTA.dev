"""Tests for enhanced metrics with percentiles, SLO tracking, and cost monitoring."""

from tta_dev_primitives.observability.enhanced_collector import (
    EnhancedMetricsCollector,
    get_enhanced_metrics_collector,
)
from tta_dev_primitives.observability.enhanced_metrics import (
    CostMetrics,
    PercentileMetrics,
    SLOConfig,
    SLOMetrics,
    ThroughputMetrics,
)


class TestPercentileMetrics:
    """Test percentile metrics calculation."""

    def test_percentile_calculation(self) -> None:
        """Test percentile calculation with sample data."""
        metrics = PercentileMetrics(name="test")

        # Record sample durations
        for duration in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            metrics.record(duration)

        percentiles = metrics.get_percentiles()

        # Check percentiles are calculated
        assert "p50" in percentiles
        assert "p90" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles

        # P50 should be around 50
        assert 40 <= percentiles["p50"] <= 60

        # P90 should be around 90
        assert 80 <= percentiles["p90"] <= 100

    def test_empty_percentiles(self) -> None:
        """Test percentiles with no data."""
        metrics = PercentileMetrics(name="test")
        percentiles = metrics.get_percentiles()

        assert percentiles["p50"] == 0.0
        assert percentiles["p90"] == 0.0
        assert percentiles["p95"] == 0.0
        assert percentiles["p99"] == 0.0

    def test_max_samples_limit(self) -> None:
        """Test that max_samples limit is enforced."""
        metrics = PercentileMetrics(name="test", max_samples=100)

        # Record more than max_samples
        for i in range(200):
            metrics.record(float(i))

        # Should only keep last 100 samples
        assert len(metrics.durations) == 100
        assert metrics.durations[0] == 100.0  # First kept sample

    def test_reset(self) -> None:
        """Test reset clears all durations."""
        metrics = PercentileMetrics(name="test")
        metrics.record(10.0)
        metrics.record(20.0)

        metrics.reset()

        assert len(metrics.durations) == 0
        percentiles = metrics.get_percentiles()
        assert percentiles["p50"] == 0.0


class TestSLOMetrics:
    """Test SLO tracking and error budget calculation."""

    def test_availability_slo(self) -> None:
        """Test availability-based SLO tracking."""
        config = SLOConfig(
            name="test_slo",
            target=0.99,
            error_rate_threshold=0.01,  # 99% availability
        )
        slo = SLOMetrics(config=config)

        # Record 100 requests, 99 successful
        for _ in range(99):
            slo.record_request(duration_ms=100.0, success=True)
        slo.record_request(duration_ms=100.0, success=False)

        # Should meet 99% availability target
        assert slo.availability == 0.99
        assert slo.is_compliant

    def test_latency_slo(self) -> None:
        """Test latency-based SLO tracking."""
        config = SLOConfig(
            name="test_slo",
            target=0.95,  # 95% of requests
            threshold_ms=1000.0,  # under 1 second
        )
        slo = SLOMetrics(config=config)

        # Record 100 requests, 95 under threshold
        for _ in range(95):
            slo.record_request(duration_ms=500.0, success=True)
        for _ in range(5):
            slo.record_request(duration_ms=1500.0, success=True)

        # Should meet 95% latency target
        assert slo.latency_compliance == 0.95
        assert slo.is_compliant

    def test_error_budget_remaining(self) -> None:
        """Test error budget calculation."""
        config = SLOConfig(
            name="test_slo",
            target=0.99,
            error_rate_threshold=0.01,  # 99% availability
        )
        slo = SLOMetrics(config=config)

        # Record 100 requests, all successful
        for _ in range(100):
            slo.record_request(duration_ms=100.0, success=True)

        # Should have full error budget remaining
        assert slo.error_budget_remaining == 1.0

        # Record 1 failure (uses error budget)
        slo.record_request(duration_ms=100.0, success=False)

        # Error budget should be reduced
        assert slo.error_budget_remaining < 1.0

    def test_slo_violation(self) -> None:
        """Test SLO violation detection."""
        config = SLOConfig(
            name="test_slo",
            target=0.99,
            error_rate_threshold=0.01,  # 99% availability
        )
        slo = SLOMetrics(config=config)

        # Record 100 requests, only 95 successful (below 99% target)
        for _ in range(95):
            slo.record_request(duration_ms=100.0, success=True)
        for _ in range(5):
            slo.record_request(duration_ms=100.0, success=False)

        # Should not be compliant
        assert not slo.is_compliant
        assert slo.availability == 0.95

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        config = SLOConfig(name="test_slo", target=0.99, threshold_ms=1000.0)
        slo = SLOMetrics(config=config)

        slo.record_request(duration_ms=500.0, success=True)

        result = slo.to_dict()

        assert result["name"] == "test_slo"
        assert result["target"] == 0.99
        assert result["threshold_ms"] == 1000.0
        assert result["total_requests"] == 1
        assert "availability" in result
        assert "is_compliant" in result


class TestThroughputMetrics:
    """Test throughput and concurrency tracking."""

    def test_active_requests(self) -> None:
        """Test active request tracking."""
        metrics = ThroughputMetrics(name="test")

        assert metrics.active_requests == 0

        metrics.start_request()
        assert metrics.active_requests == 1

        metrics.start_request()
        assert metrics.active_requests == 2

        metrics.end_request()
        assert metrics.active_requests == 1

        metrics.end_request()
        assert metrics.active_requests == 0

    def test_total_requests(self) -> None:
        """Test total request counting."""
        metrics = ThroughputMetrics(name="test")

        for _ in range(10):
            metrics.start_request()
            metrics.end_request()

        assert metrics.total_requests == 10

    def test_requests_per_second(self) -> None:
        """Test RPS calculation."""
        metrics = ThroughputMetrics(name="test")

        # Record some requests
        for _ in range(10):
            metrics.start_request()

        # RPS should be > 0
        rps = metrics.requests_per_second
        assert rps > 0

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        metrics = ThroughputMetrics(name="test")
        metrics.start_request()

        result = metrics.to_dict()

        assert result["name"] == "test"
        assert result["total_requests"] == 1
        assert result["active_requests"] == 1
        assert "requests_per_second" in result


class TestCostMetrics:
    """Test cost tracking."""

    def test_cost_recording(self) -> None:
        """Test cost recording."""
        metrics = CostMetrics(name="test")

        metrics.record_cost(0.05, operation="gpt-4")
        metrics.record_cost(0.02, operation="gpt-3.5")

        assert metrics.total_cost == 0.07
        assert metrics.cost_by_operation["gpt-4"] == 0.05
        assert metrics.cost_by_operation["gpt-3.5"] == 0.02

    def test_savings_recording(self) -> None:
        """Test savings recording."""
        metrics = CostMetrics(name="test")

        metrics.record_cost(0.10)
        metrics.record_savings(0.03)

        assert metrics.total_cost == 0.10
        assert metrics.total_savings == 0.03
        assert metrics.net_cost == 0.07

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        metrics = CostMetrics(name="test")
        metrics.record_cost(0.05, operation="llm")
        metrics.record_savings(0.01)

        result = metrics.to_dict()

        assert result["name"] == "test"
        assert result["total_cost"] == 0.05
        assert result["total_savings"] == 0.01
        assert result["net_cost"] == 0.04
        assert "cost_by_operation" in result


class TestEnhancedMetricsCollector:
    """Test enhanced metrics collector."""

    def test_configure_slo(self) -> None:
        """Test SLO configuration."""
        collector = EnhancedMetricsCollector()

        collector.configure_slo("test_primitive", target=0.99, threshold_ms=1000.0)

        slo_status = collector.get_slo_status("test_primitive")
        assert slo_status["name"] == "test_primitive"
        assert slo_status["target"] == 0.99

    def test_record_execution(self) -> None:
        """Test recording execution with all metrics."""
        collector = EnhancedMetricsCollector()
        collector.configure_slo("test_primitive", target=0.99, threshold_ms=1000.0)

        collector.start_request("test_primitive")
        collector.record_execution(
            "test_primitive", duration_ms=250.0, success=True, cost=0.05, savings=0.01
        )
        collector.end_request("test_primitive")

        # Check all metrics are recorded
        metrics = collector.get_all_metrics("test_primitive")

        assert "percentiles" in metrics
        assert "slo" in metrics
        assert "throughput" in metrics
        assert "cost" in metrics

        # Check percentiles
        assert metrics["percentiles"]["p50"] > 0

        # Check SLO
        assert metrics["slo"]["total_requests"] == 1
        assert metrics["slo"]["is_compliant"]

        # Check throughput
        assert metrics["throughput"]["total_requests"] == 1

        # Check cost
        assert metrics["cost"]["total_cost"] == 0.05
        assert metrics["cost"]["total_savings"] == 0.01

    def test_get_all_primitives_metrics(self) -> None:
        """Test getting metrics for all primitives."""
        collector = EnhancedMetricsCollector()

        collector.record_execution("primitive1", duration_ms=100.0, success=True)
        collector.record_execution("primitive2", duration_ms=200.0, success=True)

        all_metrics = collector.get_all_primitives_metrics()

        assert "primitive1" in all_metrics
        assert "primitive2" in all_metrics

    def test_reset(self) -> None:
        """Test resetting metrics."""
        collector = EnhancedMetricsCollector()

        collector.record_execution("test_primitive", duration_ms=100.0, success=True)

        collector.reset("test_primitive")

        metrics = collector.get_all_metrics("test_primitive")
        assert metrics["percentiles"]["p50"] == 0.0

    def test_global_collector(self) -> None:
        """Test global collector singleton."""
        collector1 = get_enhanced_metrics_collector()
        collector2 = get_enhanced_metrics_collector()

        assert collector1 is collector2
