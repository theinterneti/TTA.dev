"""Tests for ttadev.primitives.observability.metrics."""

from __future__ import annotations

import pytest

from ttadev.primitives.observability.metrics import (
    MetricsCollector,
    PrimitiveMetrics,
    get_metrics_collector,
)


class TestPrimitiveMetrics:
    def test_defaults(self):
        m = PrimitiveMetrics(name="my_prim")
        assert m.name == "my_prim"
        assert m.total_executions == 0
        assert m.successful_executions == 0
        assert m.failed_executions == 0
        assert m.total_duration_ms == 0.0
        assert m.max_duration_ms == 0.0
        assert m.error_counts == {}

    def test_success_rate_zero_executions(self):
        m = PrimitiveMetrics(name="p")
        assert m.success_rate == 0.0

    def test_success_rate_nonzero(self):
        m = PrimitiveMetrics(name="p", total_executions=4, successful_executions=3)
        assert m.success_rate == pytest.approx(0.75)

    def test_average_duration_zero_executions(self):
        m = PrimitiveMetrics(name="p")
        assert m.average_duration_ms == 0.0

    def test_average_duration_nonzero(self):
        m = PrimitiveMetrics(name="p", total_executions=2, total_duration_ms=100.0)
        assert m.average_duration_ms == pytest.approx(50.0)

    def test_to_dict_no_executions(self):
        m = PrimitiveMetrics(name="p")
        d = m.to_dict()
        assert d["name"] == "p"
        assert d["min_duration_ms"] == 0  # inf replaced with 0
        assert d["success_rate"] == 0.0

    def test_to_dict_with_data(self):
        m = PrimitiveMetrics(
            name="fetch",
            total_executions=3,
            successful_executions=2,
            failed_executions=1,
            total_duration_ms=90.0,
            min_duration_ms=20.0,
            max_duration_ms=40.0,
            error_counts={"ValueError": 1},
        )
        d = m.to_dict()
        assert d["total_executions"] == 3
        assert d["successful_executions"] == 2
        assert d["failed_executions"] == 1
        assert d["average_duration_ms"] == pytest.approx(30.0)
        assert d["min_duration_ms"] == 20.0
        assert d["max_duration_ms"] == 40.0
        assert d["error_counts"] == {"ValueError": 1}


class TestMetricsCollector:
    def test_record_first_execution_success(self):
        c = MetricsCollector()
        c.record_execution("prim", 50.0, success=True)
        m = c.get_metrics("prim")
        assert m["total_executions"] == 1
        assert m["successful_executions"] == 1
        assert m["failed_executions"] == 0

    def test_record_execution_failure_with_error_type(self):
        c = MetricsCollector()
        c.record_execution("prim", 30.0, success=False, error_type="TimeoutError")
        m = c.get_metrics("prim")
        assert m["failed_executions"] == 1
        assert m["error_counts"]["TimeoutError"] == 1

    def test_record_failure_without_error_type(self):
        c = MetricsCollector()
        c.record_execution("prim", 10.0, success=False)
        m = c.get_metrics("prim")
        assert m["failed_executions"] == 1
        assert m["error_counts"] == {}

    def test_duration_tracking(self):
        c = MetricsCollector()
        c.record_execution("p", 10.0, success=True)
        c.record_execution("p", 30.0, success=True)
        m = c.get_metrics("p")
        assert m["min_duration_ms"] == 10.0
        assert m["max_duration_ms"] == 30.0
        assert m["average_duration_ms"] == pytest.approx(20.0)

    def test_get_metrics_missing_primitive(self):
        c = MetricsCollector()
        assert c.get_metrics("nonexistent") == {}

    def test_get_all_metrics(self):
        c = MetricsCollector()
        c.record_execution("a", 10.0, success=True)
        c.record_execution("b", 20.0, success=False, error_type="E")
        all_m = c.get_metrics()
        assert "a" in all_m
        assert "b" in all_m

    def test_reset(self):
        c = MetricsCollector()
        c.record_execution("p", 1.0, success=True)
        c.reset()
        assert c.get_metrics("p") == {}

    def test_error_count_accumulates(self):
        c = MetricsCollector()
        c.record_execution("p", 1.0, success=False, error_type="Err")
        c.record_execution("p", 1.0, success=False, error_type="Err")
        m = c.get_metrics("p")
        assert m["error_counts"]["Err"] == 2


class TestGetMetricsCollector:
    def test_returns_same_instance(self):
        a = get_metrics_collector()
        b = get_metrics_collector()
        assert a is b

    def test_returns_metrics_collector(self):
        assert isinstance(get_metrics_collector(), MetricsCollector)
