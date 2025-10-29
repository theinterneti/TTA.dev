"""Prometheus metrics exporter for Phase 3 enhanced metrics."""

from __future__ import annotations

import threading
from typing import Any

from .metrics import EnhancedMetricsCollector, get_enhanced_metrics_collector

# Try to import prometheus_client, gracefully degrade if not available
try:
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class PrometheusExporter:
    """
    Exports enhanced metrics to Prometheus format.

    Provides automatic metric export with cardinality controls to prevent
    memory issues in high-cardinality scenarios.

    Example:
        ```python
        exporter = get_prometheus_exporter()
        
        # Export metrics (called by Prometheus scraper)
        metrics_output = exporter.export_metrics()
        
        # Get metrics as string (for HTTP endpoint)
        metrics_text = exporter.get_metrics_text()
        ```
    """

    # Maximum unique label combinations to prevent cardinality explosion
    MAX_LABEL_CARDINALITY = 1000

    def __init__(self, collector: EnhancedMetricsCollector | None = None) -> None:
        """
        Initialize Prometheus exporter.

        Args:
            collector: Optional metrics collector (uses global if not provided)
        """
        self._collector = collector or get_enhanced_metrics_collector()
        self._registry = CollectorRegistry() if PROMETHEUS_AVAILABLE else None
        self._lock = threading.Lock()
        self._label_counts: dict[str, int] = {}

        if PROMETHEUS_AVAILABLE:
            self._setup_metrics()

    def _setup_metrics(self) -> None:
        """Set up Prometheus metric objects."""
        if not PROMETHEUS_AVAILABLE or not self._registry:
            return

        # Latency histogram for percentiles
        self._duration_histogram = Histogram(
            "primitive_duration_seconds",
            "Primitive execution duration in seconds",
            ["primitive_name", "primitive_type"],
            buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0],
            registry=self._registry,
        )

        # Request counters
        self._requests_total = Counter(
            "primitive_requests_total",
            "Total number of primitive executions",
            ["primitive_name", "primitive_type", "status"],
            registry=self._registry,
        )

        # Active requests gauge
        self._active_requests = Gauge(
            "primitive_active_requests",
            "Number of currently active requests",
            ["primitive_name"],
            registry=self._registry,
        )

        # SLO compliance gauge
        self._slo_compliance = Gauge(
            "primitive_slo_compliance",
            "SLO compliance rate (0.0 to 1.0)",
            ["primitive_name", "slo_name"],
            registry=self._registry,
        )

        # Error budget gauge
        self._error_budget = Gauge(
            "primitive_error_budget_remaining",
            "Remaining error budget (0.0 to 1.0)",
            ["primitive_name", "slo_name"],
            registry=self._registry,
        )

        # Cost counter
        self._cost_total = Counter(
            "primitive_cost_total",
            "Total cost incurred",
            ["primitive_name"],
            registry=self._registry,
        )

        # Savings counter
        self._cost_savings = Counter(
            "primitive_cost_savings_total",
            "Total cost savings from optimizations",
            ["primitive_name"],
            registry=self._registry,
        )

        # Throughput gauge (RPS)
        self._throughput_rps = Gauge(
            "primitive_requests_per_second",
            "Requests per second",
            ["primitive_name"],
            registry=self._registry,
        )

    def _check_cardinality(self, metric_name: str, labels: tuple[str, ...]) -> bool:
        """
        Check if adding a label combination would exceed cardinality limit.

        Args:
            metric_name: Name of the metric
            labels: Tuple of label values

        Returns:
            True if safe to add, False if would exceed limit
        """
        key = f"{metric_name}:{':'.join(labels)}"
        
        with self._lock:
            if key in self._label_counts:
                return True
            
            # Count unique labels for this metric
            metric_labels = [k for k in self._label_counts if k.startswith(f"{metric_name}:")]
            if len(metric_labels) >= self.MAX_LABEL_CARDINALITY:
                return False
            
            self._label_counts[key] = 1
            return True

    def record_execution(
        self,
        primitive_name: str,
        primitive_type: str,
        duration_ms: float,
        success: bool,
        cost: float | None = None,
    ) -> None:
        """
        Record an execution in Prometheus metrics.

        Args:
            primitive_name: Name of the primitive
            primitive_type: Type of the primitive (class name)
            duration_ms: Execution duration in milliseconds
            success: Whether execution succeeded
            cost: Optional cost of execution

        Example:
            ```python
            exporter.record_execution(
                primitive_name="llm_call",
                primitive_type="LLMPrimitive",
                duration_ms=1250.0,
                success=True,
                cost=0.05
            )
            ```
        """
        if not PROMETHEUS_AVAILABLE:
            return

        # Check cardinality before recording
        if not self._check_cardinality("primitive_duration_seconds", (primitive_name, primitive_type)):
            return

        # Record latency histogram
        duration_seconds = duration_ms / 1000.0
        self._duration_histogram.labels(
            primitive_name=primitive_name,
            primitive_type=primitive_type,
        ).observe(duration_seconds)

        # Record request counter
        status = "success" if success else "error"
        if self._check_cardinality("primitive_requests_total", (primitive_name, primitive_type, status)):
            self._requests_total.labels(
                primitive_name=primitive_name,
                primitive_type=primitive_type,
                status=status,
            ).inc()

        # Record cost if provided
        if cost is not None and self._check_cardinality("primitive_cost_total", (primitive_name,)):
            self._cost_total.labels(primitive_name=primitive_name).inc(cost)

    def update_gauges(self, primitive_name: str, metrics: dict[str, Any]) -> None:
        """
        Update gauge metrics from collected metrics.

        Args:
            primitive_name: Name of the primitive
            metrics: Metrics dictionary from EnhancedMetricsCollector

        Example:
            ```python
            metrics = collector.get_all_metrics("api_call")
            exporter.update_gauges("api_call", metrics)
            ```
        """
        if not PROMETHEUS_AVAILABLE:
            return

        # Update throughput gauge
        if "throughput" in metrics and self._check_cardinality("primitive_requests_per_second", (primitive_name,)):
            self._throughput_rps.labels(primitive_name=primitive_name).set(
                metrics["throughput"]["rps"]
            )
            
            if self._check_cardinality("primitive_active_requests", (primitive_name,)):
                self._active_requests.labels(primitive_name=primitive_name).set(
                    metrics["throughput"]["active_requests"]
                )

        # Update SLO gauges
        if "slo" in metrics:
            slo_name = metrics["slo"]["name"]
            if self._check_cardinality("primitive_slo_compliance", (primitive_name, slo_name)):
                self._slo_compliance.labels(
                    primitive_name=primitive_name,
                    slo_name=slo_name,
                ).set(metrics["slo"]["compliance"])
            
            if self._check_cardinality("primitive_error_budget_remaining", (primitive_name, slo_name)):
                self._error_budget.labels(
                    primitive_name=primitive_name,
                    slo_name=slo_name,
                ).set(metrics["slo"]["error_budget"])

    def record_savings(self, primitive_name: str, savings: float) -> None:
        """
        Record cost savings.

        Args:
            primitive_name: Name of the primitive
            savings: Savings amount

        Example:
            ```python
            # Record savings from cache hit
            exporter.record_savings("api_call", 0.05)
            ```
        """
        if not PROMETHEUS_AVAILABLE:
            return

        if self._check_cardinality("primitive_cost_savings_total", (primitive_name,)):
            self._cost_savings.labels(primitive_name=primitive_name).inc(savings)

    def export_metrics(self) -> dict[str, Any]:
        """
        Export all metrics in a structured format.

        Returns:
            Dictionary of all metrics

        Example:
            ```python
            metrics = exporter.export_metrics()
            ```
        """
        # This would collect all metrics from the collector
        # For now, return empty dict as placeholder
        return {}

    def get_metrics_text(self) -> bytes:
        """
        Get metrics in Prometheus text format for scraping.

        Returns:
            Metrics in Prometheus exposition format

        Example:
            ```python
            # In Flask/FastAPI endpoint
            @app.get("/metrics")
            def metrics():
                exporter = get_prometheus_exporter()
                return Response(
                    exporter.get_metrics_text(),
                    media_type="text/plain"
                )
            ```
        """
        if not PROMETHEUS_AVAILABLE or not self._registry:
            return b"# Prometheus client not available\n"

        return generate_latest(self._registry)

    def get_cardinality_stats(self) -> dict[str, int]:
        """
        Get cardinality statistics for monitoring.

        Returns:
            Dictionary with cardinality counts per metric

        Example:
            ```python
            stats = exporter.get_cardinality_stats()
            print(f"Label combinations: {stats['total']}")
            ```
        """
        with self._lock:
            metric_counts: dict[str, int] = {}
            
            for key in self._label_counts:
                metric_name = key.split(":")[0]
                metric_counts[metric_name] = metric_counts.get(metric_name, 0) + 1
            
            return {
                "total": len(self._label_counts),
                "max_allowed": self.MAX_LABEL_CARDINALITY,
                "by_metric": metric_counts,
            }


# Global Prometheus exporter
_prometheus_exporter: PrometheusExporter | None = None
_exporter_lock = threading.Lock()


def get_prometheus_exporter() -> PrometheusExporter:
    """
    Get the global Prometheus exporter (thread-safe singleton).

    Returns:
        Global PrometheusExporter instance

    Example:
        ```python
        exporter = get_prometheus_exporter()
        exporter.record_execution("my_primitive", "MyPrimitive", 123.4, True)
        metrics_text = exporter.get_metrics_text()
        ```
    """
    global _prometheus_exporter
    if _prometheus_exporter is None:
        with _exporter_lock:
            # Double-check locking pattern
            if _prometheus_exporter is None:
                _prometheus_exporter = PrometheusExporter()
    return _prometheus_exporter
