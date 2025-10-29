"""Prometheus metrics exporter for enhanced metrics."""

from __future__ import annotations

from typing import Any

try:
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        Info,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from .enhanced_collector import get_enhanced_metrics_collector


class PrometheusExporter:
    """
    Export enhanced metrics to Prometheus format.

    Converts PercentileMetrics, SLOMetrics, ThroughputMetrics, and CostMetrics
    to Prometheus metrics with proper labels and cardinality controls.

    Example:
        ```python
        from tta_dev_primitives.observability import PrometheusExporter

        # Create exporter
        exporter = PrometheusExporter()

        # Export metrics
        metrics_text = exporter.export()
        print(metrics_text)  # Prometheus text format

        # Or use with HTTP server
        from prometheus_client import start_http_server
        start_http_server(8000, registry=exporter.registry)
        ```
    """

    def __init__(
        self,
        registry: Any | None = None,
        namespace: str = "tta",
        subsystem: str = "workflow",
        max_label_cardinality: int = 1000,
    ) -> None:
        """
        Initialize Prometheus exporter.

        Args:
            registry: Prometheus registry (creates new if None)
            namespace: Metric namespace prefix
            subsystem: Metric subsystem prefix
            max_label_cardinality: Maximum unique label combinations
        """
        if not PROMETHEUS_AVAILABLE:
            raise ImportError(
                "prometheus_client not installed. Install with: uv pip install prometheus-client"
            )

        self.registry = registry or CollectorRegistry()
        self.namespace = namespace
        self.subsystem = subsystem
        self.max_label_cardinality = max_label_cardinality

        # Track label cardinality
        self._label_combinations: set[tuple[str, ...]] = set()

        # Initialize Prometheus metrics
        self._init_metrics()

    def _init_metrics(self) -> None:
        """Initialize Prometheus metric collectors."""
        # Latency histogram (for percentiles)
        self.latency_histogram = Histogram(
            name="primitive_duration_seconds",
            documentation="Primitive execution duration in seconds",
            labelnames=["primitive_name", "primitive_type"],
            namespace=self.namespace,
            subsystem=self.subsystem,
            registry=self.registry,
            buckets=(
                0.001,
                0.005,
                0.01,
                0.025,
                0.05,
                0.1,
                0.25,
                0.5,
                1.0,
                2.5,
                5.0,
                10.0,
            ),
        )

        # SLO compliance gauge
        self.slo_compliance = Gauge(
            name="slo_compliance_ratio",
            documentation="SLO compliance ratio (0.0 to 1.0)",
            labelnames=["primitive_name", "slo_type"],
            namespace=self.namespace,
            subsystem=self.subsystem,
            registry=self.registry,
        )

        # Error budget gauge
        self.error_budget = Gauge(
            name="error_budget_remaining",
            documentation="Remaining error budget (0.0 to 1.0)",
            labelnames=["primitive_name"],
            namespace=self.namespace,
            subsystem=self.subsystem,
            registry=self.registry,
        )

        # Throughput counter
        self.request_total = Counter(
            name="requests_total",
            documentation="Total number of requests",
            labelnames=["primitive_name", "status"],
            namespace=self.namespace,
            subsystem=self.subsystem,
            registry=self.registry,
        )

        # Active requests gauge
        self.active_requests = Gauge(
            name="active_requests",
            documentation="Number of active concurrent requests",
            labelnames=["primitive_name"],
            namespace=self.namespace,
            subsystem=self.subsystem,
            registry=self.registry,
        )

        # Cost counter
        self.cost_total = Counter(
            name="cost_total",
            documentation="Total cost in dollars",
            labelnames=["primitive_name", "operation"],
            namespace=self.namespace,
            subsystem=self.subsystem,
            registry=self.registry,
        )

        # Savings counter
        self.savings_total = Counter(
            name="savings_total",
            documentation="Total savings in dollars",
            labelnames=["primitive_name"],
            namespace=self.namespace,
            subsystem=self.subsystem,
            registry=self.registry,
        )

        # Metadata info
        self.build_info = Info(
            name="build",
            documentation="Build information",
            namespace=self.namespace,
            subsystem=self.subsystem,
            registry=self.registry,
        )
        self.build_info.info(
            {
                "version": "0.1.0",
                "package": "tta-dev-primitives",
                "component": "observability",
            }
        )

    def _check_cardinality(self, labels: tuple[str, ...]) -> bool:
        """
        Check if adding labels would exceed cardinality limit.

        Args:
            labels: Label combination to check

        Returns:
            True if within limit, False otherwise
        """
        if labels in self._label_combinations:
            return True

        if len(self._label_combinations) >= self.max_label_cardinality:
            return False

        self._label_combinations.add(labels)
        return True

    def update_metrics(self) -> None:
        """
        Update Prometheus metrics from enhanced metrics collector.

        Reads current state from EnhancedMetricsCollector and updates
        all Prometheus metrics accordingly.
        """
        collector = get_enhanced_metrics_collector()

        # Update percentile metrics (via histogram observations)
        for name, percentile_metrics in collector._percentile_metrics.items():
            labels = (name, "primitive")
            if not self._check_cardinality(labels):
                continue

            # Record all durations in histogram
            for duration_ms in percentile_metrics.durations:
                self.latency_histogram.labels(
                    primitive_name=name, primitive_type="primitive"
                ).observe(duration_ms / 1000.0)  # Convert to seconds

        # Update SLO metrics
        for name, slo_metrics in collector._slo_metrics.items():
            labels_compliance = (name, "availability")
            labels_budget = (name,)

            if self._check_cardinality(labels_compliance):
                # Availability compliance
                if slo_metrics.config.error_rate_threshold:
                    self.slo_compliance.labels(
                        primitive_name=name, slo_type="availability"
                    ).set(slo_metrics.availability)

                # Latency compliance
                if slo_metrics.config.threshold_ms:
                    self.slo_compliance.labels(
                        primitive_name=name, slo_type="latency"
                    ).set(slo_metrics.latency_compliance)

            if self._check_cardinality(labels_budget):
                # Error budget
                self.error_budget.labels(primitive_name=name).set(
                    slo_metrics.error_budget_remaining
                )

        # Update throughput metrics
        for name, throughput_metrics in collector._throughput_metrics.items():
            labels_active = (name,)
            labels_success = (name, "success")

            if self._check_cardinality(labels_active):
                self.active_requests.labels(primitive_name=name).set(
                    throughput_metrics.active_requests
                )

            if self._check_cardinality(labels_success):
                # Note: Counter can only increase, so we set to total
                self.request_total.labels(
                    primitive_name=name, status="success"
                )._value.set(throughput_metrics.total_requests)

        # Update cost metrics
        for name, cost_metrics in collector._cost_metrics.items():
            for operation, cost in cost_metrics.cost_by_operation.items():
                labels_cost = (name, operation)
                if self._check_cardinality(labels_cost):
                    self.cost_total.labels(
                        primitive_name=name, operation=operation
                    )._value.set(cost)

            labels_savings = (name,)
            if self._check_cardinality(labels_savings):
                self.savings_total.labels(primitive_name=name)._value.set(
                    cost_metrics.total_savings
                )

    def export(self) -> bytes:
        """
        Export metrics in Prometheus text format.

        Returns:
            Metrics in Prometheus exposition format
        """
        self.update_metrics()
        return generate_latest(self.registry)


# Global exporter instance
_global_exporter: PrometheusExporter | None = None


def get_prometheus_exporter(
    namespace: str = "tta", subsystem: str = "workflow"
) -> PrometheusExporter:
    """
    Get global Prometheus exporter instance.

    Args:
        namespace: Metric namespace prefix
        subsystem: Metric subsystem prefix

    Returns:
        Global PrometheusExporter instance

    Example:
        ```python
        from tta_dev_primitives.observability import get_prometheus_exporter

        exporter = get_prometheus_exporter()
        metrics = exporter.export()
        ```
    """
    global _global_exporter
    if _global_exporter is None:
        _global_exporter = PrometheusExporter(namespace=namespace, subsystem=subsystem)
    return _global_exporter
