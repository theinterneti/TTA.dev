"""Enhanced metrics collector with percentiles, SLO tracking, and cost monitoring."""

from __future__ import annotations

import threading
from typing import Any

from .enhanced_metrics import (
    CostMetrics,
    PercentileMetrics,
    SLOConfig,
    SLOMetrics,
    ThroughputMetrics,
)


class EnhancedMetricsCollector:
    """
    Comprehensive metrics collector for workflow primitives.

    Tracks:
    - Percentile metrics (p50, p90, p95, p99)
    - SLO compliance and error budgets
    - Throughput and concurrency
    - Cost and savings

    Example:
        ```python
        from tta_dev_primitives.observability import get_enhanced_metrics_collector

        collector = get_enhanced_metrics_collector()

        # Configure SLO
        collector.configure_slo(
            "my_workflow",
            target=0.99,
            threshold_ms=1000.0
        )

        # Record execution
        collector.start_request("my_workflow")
        # ... execute workflow ...
        collector.record_execution(
            "my_workflow",
            duration_ms=250.0,
            success=True,
            cost=0.05
        )
        collector.end_request("my_workflow")

        # Get metrics
        metrics = collector.get_all_metrics("my_workflow")
        print(f"P95 latency: {metrics['percentiles']['p95']}ms")
        print(f"SLO compliance: {metrics['slo']['is_compliant']}")
        print(f"RPS: {metrics['throughput']['requests_per_second']}")
        ```
    """

    def __init__(self) -> None:
        self._percentile_metrics: dict[str, PercentileMetrics] = {}
        self._slo_metrics: dict[str, SLOMetrics] = {}
        self._throughput_metrics: dict[str, ThroughputMetrics] = {}
        self._cost_metrics: dict[str, CostMetrics] = {}

    def configure_slo(
        self,
        primitive_name: str,
        target: float,
        threshold_ms: float | None = None,
        error_rate_threshold: float | None = None,
        window_seconds: int = 2592000,
    ) -> None:
        """
        Configure SLO for a primitive.

        Args:
            primitive_name: Name of the primitive
            target: Target compliance (e.g., 0.99 for 99%)
            threshold_ms: Latency threshold in milliseconds
            error_rate_threshold: Error rate threshold (e.g., 0.01 for 1%)
            window_seconds: SLO window in seconds (default: 30 days)

        Example:
            ```python
            collector.configure_slo(
                "llm_call",
                target=0.99,  # 99% of requests
                threshold_ms=1000.0  # under 1 second
            )
            ```
        """
        config = SLOConfig(
            name=primitive_name,
            target=target,
            threshold_ms=threshold_ms,
            error_rate_threshold=error_rate_threshold,
            window_seconds=window_seconds,
        )
        self._slo_metrics[primitive_name] = SLOMetrics(config=config)

    def start_request(self, primitive_name: str) -> None:
        """
        Mark a request as started (for throughput tracking).

        Args:
            primitive_name: Name of the primitive
        """
        if primitive_name not in self._throughput_metrics:
            self._throughput_metrics[primitive_name] = ThroughputMetrics(name=primitive_name)

        self._throughput_metrics[primitive_name].start_request()

    def end_request(self, primitive_name: str) -> None:
        """
        Mark a request as completed (for throughput tracking).

        Args:
            primitive_name: Name of the primitive
        """
        if primitive_name in self._throughput_metrics:
            self._throughput_metrics[primitive_name].end_request()

    def record_execution(
        self,
        primitive_name: str,
        duration_ms: float,
        success: bool,
        cost: float = 0.0,
        savings: float = 0.0,
        operation: str = "default",
    ) -> None:
        """
        Record a primitive execution with all metrics.

        Args:
            primitive_name: Name of the primitive
            duration_ms: Execution duration in milliseconds
            success: Whether execution succeeded
            cost: Cost of execution (e.g., LLM API cost)
            savings: Cost savings (e.g., from cache hit)
            operation: Operation type for cost tracking

        Example:
            ```python
            collector.record_execution(
                "llm_call",
                duration_ms=250.0,
                success=True,
                cost=0.05,
                operation="gpt-4"
            )
            ```
        """
        # Percentile metrics
        if primitive_name not in self._percentile_metrics:
            self._percentile_metrics[primitive_name] = PercentileMetrics(name=primitive_name)
        self._percentile_metrics[primitive_name].record(duration_ms)

        # SLO metrics
        if primitive_name in self._slo_metrics:
            self._slo_metrics[primitive_name].record_request(duration_ms, success)

        # Cost metrics
        if cost > 0 or savings > 0:
            if primitive_name not in self._cost_metrics:
                self._cost_metrics[primitive_name] = CostMetrics(name=primitive_name)
            if cost > 0:
                self._cost_metrics[primitive_name].record_cost(cost, operation)
            if savings > 0:
                self._cost_metrics[primitive_name].record_savings(savings)

    def get_percentiles(self, primitive_name: str) -> dict[str, float]:
        """
        Get percentile metrics for a primitive.

        Args:
            primitive_name: Name of the primitive

        Returns:
            Dictionary with p50, p90, p95, p99 values
        """
        if primitive_name not in self._percentile_metrics:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}
        return self._percentile_metrics[primitive_name].get_percentiles()

    def get_slo_status(self, primitive_name: str) -> dict[str, Any]:
        """
        Get SLO status for a primitive.

        Args:
            primitive_name: Name of the primitive

        Returns:
            Dictionary with SLO metrics
        """
        if primitive_name not in self._slo_metrics:
            return {}
        return self._slo_metrics[primitive_name].to_dict()

    def get_throughput(self, primitive_name: str) -> dict[str, Any]:
        """
        Get throughput metrics for a primitive.

        Args:
            primitive_name: Name of the primitive

        Returns:
            Dictionary with throughput metrics
        """
        if primitive_name not in self._throughput_metrics:
            return {}
        return self._throughput_metrics[primitive_name].to_dict()

    def get_cost_metrics(self, primitive_name: str) -> dict[str, Any]:
        """
        Get cost metrics for a primitive.

        Args:
            primitive_name: Name of the primitive

        Returns:
            Dictionary with cost metrics
        """
        if primitive_name not in self._cost_metrics:
            return {}
        return self._cost_metrics[primitive_name].to_dict()

    def get_all_metrics(self, primitive_name: str) -> dict[str, Any]:
        """
        Get all metrics for a primitive.

        Args:
            primitive_name: Name of the primitive

        Returns:
            Dictionary with all metrics categories

        Example:
            ```python
            metrics = collector.get_all_metrics("llm_call")
            print(f"P95: {metrics['percentiles']['p95']}ms")
            print(f"SLO compliant: {metrics['slo']['is_compliant']}")
            print(f"RPS: {metrics['throughput']['requests_per_second']}")
            print(f"Total cost: ${metrics['cost']['total_cost']}")
            ```
        """
        return {
            "percentiles": self.get_percentiles(primitive_name),
            "slo": self.get_slo_status(primitive_name),
            "throughput": self.get_throughput(primitive_name),
            "cost": self.get_cost_metrics(primitive_name),
        }

    def get_all_primitives_metrics(self) -> dict[str, dict[str, Any]]:
        """
        Get metrics for all primitives.

        Returns:
            Dictionary mapping primitive names to their metrics
        """
        all_primitives = set()
        all_primitives.update(self._percentile_metrics.keys())
        all_primitives.update(self._slo_metrics.keys())
        all_primitives.update(self._throughput_metrics.keys())
        all_primitives.update(self._cost_metrics.keys())

        return {name: self.get_all_metrics(name) for name in all_primitives}

    def reset(self, primitive_name: str | None = None) -> None:
        """
        Reset metrics for a primitive or all primitives.

        Args:
            primitive_name: Optional primitive name, or None for all
        """
        if primitive_name:
            if primitive_name in self._percentile_metrics:
                self._percentile_metrics[primitive_name].reset()
            if primitive_name in self._slo_metrics:
                self._slo_metrics[primitive_name].reset()
            if primitive_name in self._throughput_metrics:
                self._throughput_metrics[primitive_name].reset()
            if primitive_name in self._cost_metrics:
                self._cost_metrics[primitive_name].reset()
        else:
            for metrics in self._percentile_metrics.values():
                metrics.reset()
            for metrics in self._slo_metrics.values():
                metrics.reset()
            for metrics in self._throughput_metrics.values():
                metrics.reset()
            for metrics in self._cost_metrics.values():
                metrics.reset()


# Global enhanced metrics collector with thread-safe initialization
_enhanced_metrics_collector: EnhancedMetricsCollector | None = None
_collector_lock = threading.Lock()


def get_enhanced_metrics_collector() -> EnhancedMetricsCollector:
    """
    Get the global enhanced metrics collector (thread-safe singleton).

    Returns:
        The global EnhancedMetricsCollector instance
    """
    global _enhanced_metrics_collector
    if _enhanced_metrics_collector is None:
        with _collector_lock:
            # Double-check locking pattern
            if _enhanced_metrics_collector is None:
                _enhanced_metrics_collector = EnhancedMetricsCollector()
    return _enhanced_metrics_collector
