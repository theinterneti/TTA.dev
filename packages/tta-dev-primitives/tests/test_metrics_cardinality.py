"""Tests for metrics collection with cardinality controls."""

from __future__ import annotations

import pytest

from tta_dev_primitives.observability.metrics import (
    MetricsCollector,
    PrimitiveMetrics,
)


class TestMetricsCollector:
    """Tests for MetricsCollector with cardinality controls."""

    def test_basic_recording(self) -> None:
        """Test basic execution recording."""
        collector = MetricsCollector()

        collector.record_execution("test_primitive", 100.0, success=True)

        metrics = collector.get_metrics("test_primitive")
        assert metrics["total_executions"] == 1
        assert metrics["successful_executions"] == 1
        assert metrics["failed_executions"] == 0
        assert metrics["total_duration_ms"] == 100.0

    def test_error_recording(self) -> None:
        """Test error recording."""
        collector = MetricsCollector()

        collector.record_execution(
            "test_primitive",
            150.0,
            success=False,
            error_type="ValueError",
        )

        metrics = collector.get_metrics("test_primitive")
        assert metrics["failed_executions"] == 1
        assert "ValueError" in metrics["error_counts"]
        assert metrics["error_counts"]["ValueError"] == 1

    def test_multiple_executions(self) -> None:
        """Test multiple executions tracking."""
        collector = MetricsCollector()

        # Record multiple executions
        collector.record_execution("test_primitive", 100.0, success=True)
        collector.record_execution("test_primitive", 200.0, success=True)
        collector.record_execution("test_primitive", 150.0, success=False, error_type="Error")

        metrics = collector.get_metrics("test_primitive")
        assert metrics["total_executions"] == 3
        assert metrics["successful_executions"] == 2
        assert metrics["failed_executions"] == 1
        assert metrics["min_duration_ms"] == 100.0
        assert metrics["max_duration_ms"] == 200.0
        assert metrics["average_duration_ms"] == pytest.approx(150.0)

    def test_cardinality_limit_primitives(self) -> None:
        """Test cardinality limiting for primitive names."""
        collector = MetricsCollector(max_label_values=10, hash_high_cardinality=False)

        # Record executions for 15 different primitives
        for i in range(15):
            collector.record_execution(f"primitive_{i}", 100.0, success=True)

        # First 10 should be tracked normally
        for i in range(10):
            metrics = collector.get_metrics(f"primitive_{i}")
            assert metrics["total_executions"] == 1

        # Beyond 10, should use placeholder
        stats = collector.get_cardinality_stats()
        assert stats["unique_primitives"] <= 11  # 10 real + 1 placeholder

    def test_cardinality_limit_with_hashing(self) -> None:
        """Test cardinality limiting with hashing enabled."""
        collector = MetricsCollector(max_label_values=5, hash_high_cardinality=True)

        # Record executions for many primitives
        for i in range(10):
            collector.record_execution(f"primitive_{i}", 100.0, success=True)

        stats = collector.get_cardinality_stats()

        # Should have limited unique values
        assert stats["label_cardinality"]["primitive_name"] <= 10  # 5 real + up to 5 hashed
        assert stats["dropped_labels"].get("primitive_name", 0) == 5  # 5 beyond limit

    def test_cardinality_limit_error_types(self) -> None:
        """Test cardinality limiting for error types."""
        collector = MetricsCollector(max_label_values=3, hash_high_cardinality=False)

        # Record many different error types
        for i in range(6):
            collector.record_execution(
                "test_primitive",
                100.0,
                success=False,
                error_type=f"Error{i}",
            )

        stats = collector.get_cardinality_stats()

        # Should have limited error types
        assert stats["dropped_labels"].get("error_type", 0) == 3  # 3 beyond limit

    def test_consistent_hashing(self) -> None:
        """Test that same value gets same hash."""
        collector = MetricsCollector(max_label_values=2, hash_high_cardinality=True)

        # Fill up to limit
        collector.record_execution("primitive_1", 100.0, success=True)
        collector.record_execution("primitive_2", 100.0, success=True)

        # This should get hashed
        collector.record_execution("primitive_overflow", 100.0, success=True)
        collector.record_execution("primitive_overflow", 100.0, success=True)

        # The hashed value should accumulate
        all_metrics = collector.get_metrics()

        # Find hashed metrics
        hashed_metrics = [
            m for name, m in all_metrics.items() if "primitive_name_hash_" in name
        ]

        # Should have one hashed entry with 2 executions
        assert len(hashed_metrics) == 1
        assert hashed_metrics[0]["total_executions"] == 2

    def test_get_cardinality_stats(self) -> None:
        """Test cardinality statistics."""
        collector = MetricsCollector(max_label_values=100, hash_high_cardinality=True)

        # Record some data
        for i in range(5):
            collector.record_execution(f"primitive_{i}", 100.0, success=True)

        stats = collector.get_cardinality_stats()

        assert "label_cardinality" in stats
        assert "dropped_labels" in stats
        assert "max_label_values" in stats
        assert "hash_high_cardinality" in stats
        assert "total_labels" in stats
        assert "unique_primitives" in stats

        assert stats["max_label_values"] == 100
        assert stats["hash_high_cardinality"] is True
        assert stats["unique_primitives"] == 5
        assert stats["label_cardinality"]["primitive_name"] == 5

    def test_reset_clears_cardinality_tracking(self) -> None:
        """Test that reset clears cardinality tracking."""
        collector = MetricsCollector()

        # Record some data
        collector.record_execution("primitive_1", 100.0, success=True)
        collector.record_execution("primitive_2", 100.0, success=True)

        # Reset
        collector.reset()

        # Should be empty
        stats = collector.get_cardinality_stats()
        assert stats["unique_primitives"] == 0
        assert stats["total_labels"] == 0
        assert len(stats["label_cardinality"]) == 0


class TestPrimitiveMetrics:
    """Tests for PrimitiveMetrics dataclass."""

    def test_success_rate_calculation(self) -> None:
        """Test success rate calculation."""
        metrics = PrimitiveMetrics(name="test")
        assert metrics.success_rate == 0.0

        metrics.total_executions = 10
        metrics.successful_executions = 7
        assert metrics.success_rate == 0.7

    def test_average_duration_calculation(self) -> None:
        """Test average duration calculation."""
        metrics = PrimitiveMetrics(name="test")
        assert metrics.average_duration_ms == 0.0

        metrics.total_executions = 5
        metrics.total_duration_ms = 500.0
        assert metrics.average_duration_ms == 100.0

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        metrics = PrimitiveMetrics(
            name="test_primitive",
            total_executions=10,
            successful_executions=8,
            failed_executions=2,
            total_duration_ms=1000.0,
            min_duration_ms=50.0,
            max_duration_ms=200.0,
            error_counts={"ValueError": 1, "TypeError": 1},
        )

        result = metrics.to_dict()

        assert result["name"] == "test_primitive"
        assert result["total_executions"] == 10
        assert result["successful_executions"] == 8
        assert result["failed_executions"] == 2
        assert result["success_rate"] == 0.8
        assert result["total_duration_ms"] == 1000.0
        assert result["average_duration_ms"] == 100.0
        assert result["min_duration_ms"] == 50.0
        assert result["max_duration_ms"] == 200.0
        assert result["error_counts"] == {"ValueError": 1, "TypeError": 1}
