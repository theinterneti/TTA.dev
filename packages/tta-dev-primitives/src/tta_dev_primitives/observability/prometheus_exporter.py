"""Prometheus metrics exporter for enhanced metrics."""

from __future__ import annotations

import logging
import threading
from typing import Any

from .enhanced_metrics import get_enhanced_metrics_collector

# Try to import prometheus_client
try:
    from prometheus_client import (
        REGISTRY,
        Counter,
        Gauge,
        Histogram,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Cardinality limit to prevent memory issues
MAX_LABEL_COMBINATIONS = 1000


class PrometheusExporter:
    """
    Exports enhanced metrics to Prometheus format.

    Provides histogram, gauge, and counter metrics for all primitives
    with automatic label management and cardinality controls.

    Gracefully degrades when prometheus-client is unavailable.

    Example:
        ```python
        from tta_dev_primitives.observability import get_prometheus_exporter
        
        exporter = get_prometheus_exporter()
        
        # Metrics are automatically exported
        # Access via Prometheus scrape endpoint (e.g., /metrics)
        ```
    """

    def __init__(self) -> None:
        """Initialize the Prometheus exporter."""
        self._lock = threading.Lock()
        self._label_combinations: set[str] = set()
        
        if not PROMETHEUS_AVAILABLE:
            logger.warning(
                "prometheus-client not available. Metrics will not be exported to Prometheus. "
                "Install with: pip install prometheus-client"
            )
            self._metrics_initialized = False
            return

        try:
            # Initialize Prometheus metrics
            self._init_metrics()
            self._metrics_initialized = True
            logger.info("Prometheus exporter initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Prometheus metrics: {e}")
            self._metrics_initialized = False

    def _init_metrics(self) -> None:
        """Initialize Prometheus metric collectors."""
        if not PROMETHEUS_AVAILABLE:
            return

        # Latency histogram with percentile-friendly buckets
        self.latency_histogram = Histogram(
            "primitive_duration_seconds",
            "Primitive execution duration in seconds",
            labelnames=["primitive_name", "primitive_type"],
            buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
        )

        # Throughput metrics
        self.requests_total = Counter(
            "primitive_requests_total",
            "Total number of primitive executions",
            labelnames=["primitive_name", "primitive_type", "status"],
        )

        self.active_requests = Gauge(
            "primitive_active_requests",
            "Number of currently active primitive executions",
            labelnames=["primitive_name", "primitive_type"],
        )

        self.requests_per_second = Gauge(
            "primitive_requests_per_second",
            "Primitive execution rate (requests per second)",
            labelnames=["primitive_name", "primitive_type"],
        )

        # SLO metrics
        self.slo_compliance = Gauge(
            "primitive_slo_compliance",
            "SLO compliance ratio (0.0 to 1.0)",
            labelnames=["primitive_name", "primitive_type"],
        )

        self.error_budget_remaining = Gauge(
            "primitive_error_budget_remaining",
            "Error budget remaining (0.0 to 1.0)",
            labelnames=["primitive_name", "primitive_type"],
        )

        # Cost metrics
        self.cost_total = Counter(
            "primitive_cost_total",
            "Total cost in dollars",
            labelnames=["primitive_name", "primitive_type", "category"],
        )

        self.cost_savings = Counter(
            "primitive_cost_savings",
            "Total cost savings in dollars",
            labelnames=["primitive_name", "primitive_type", "category"],
        )

    def export_metrics(self, primitive_type: str = "generic") -> None:
        """
        Export current metrics to Prometheus.

        This method reads metrics from EnhancedMetricsCollector and
        updates Prometheus metric collectors.

        Args:
            primitive_type: Type/category of primitive (for labeling)
        """
        if not self._metrics_initialized:
            return

        collector = get_enhanced_metrics_collector()
        all_metrics = collector.get_all_metrics()

        for primitive_name, metrics in all_metrics.items():
            # Check cardinality limit
            label_key = f"{primitive_name}:{primitive_type}"
            if label_key not in self._label_combinations:
                if len(self._label_combinations) >= MAX_LABEL_COMBINATIONS:
                    logger.warning(
                        f"Reached max label combinations ({MAX_LABEL_COMBINATIONS}). "
                        f"Skipping primitive: {primitive_name}"
                    )
                    continue
                self._label_combinations.add(label_key)

            # Export percentile metrics via histogram observations
            if "percentiles" in metrics:
                percentiles = metrics["percentiles"]
                # Note: Histogram percentiles are calculated by Prometheus from observations
                # We don't set them directly, they're calculated from the histogram buckets
                # The histogram is populated during metric recording, not export

            # Export SLO metrics
            if "slo" in metrics:
                slo = metrics["slo"]
                self.slo_compliance.labels(
                    primitive_name=primitive_name, primitive_type=primitive_type
                ).set(slo["slo_compliance"])
                self.error_budget_remaining.labels(
                    primitive_name=primitive_name, primitive_type=primitive_type
                ).set(slo["error_budget_remaining"])

            # Export throughput metrics
            if "throughput" in metrics:
                throughput = metrics["throughput"]
                self.active_requests.labels(
                    primitive_name=primitive_name, primitive_type=primitive_type
                ).set(throughput["active_requests"])
                self.requests_per_second.labels(
                    primitive_name=primitive_name, primitive_type=primitive_type
                ).set(throughput["requests_per_second"])

            # Export cost metrics
            if "cost" in metrics:
                cost = metrics["cost"]
                # Cost counters need to be set incrementally
                # We track the last known value to calculate increments
                # Note: In production, this would need more sophisticated tracking

    def record_execution(
        self,
        primitive_name: str,
        primitive_type: str,
        duration_seconds: float,
        success: bool,
    ) -> None:
        """
        Record a primitive execution directly to Prometheus.

        This provides real-time metrics recording without going through
        the EnhancedMetricsCollector.

        Args:
            primitive_name: Name of the primitive
            primitive_type: Type/category of primitive
            duration_seconds: Execution duration in seconds
            success: Whether execution succeeded
        """
        if not self._metrics_initialized:
            return

        # Check cardinality limit
        label_key = f"{primitive_name}:{primitive_type}"
        with self._lock:
            if label_key not in self._label_combinations:
                if len(self._label_combinations) >= MAX_LABEL_COMBINATIONS:
                    logger.warning(
                        f"Reached max label combinations ({MAX_LABEL_COMBINATIONS}). "
                        f"Skipping primitive: {primitive_name}"
                    )
                    return
                self._label_combinations.add(label_key)

        # Record histogram observation
        self.latency_histogram.labels(
            primitive_name=primitive_name, primitive_type=primitive_type
        ).observe(duration_seconds)

        # Record request counter
        status = "success" if success else "failure"
        self.requests_total.labels(
            primitive_name=primitive_name, primitive_type=primitive_type, status=status
        ).inc()

    def record_cost(
        self,
        primitive_name: str,
        primitive_type: str,
        cost: float,
        category: str = "default",
    ) -> None:
        """
        Record a cost metric to Prometheus.

        Args:
            primitive_name: Name of the primitive
            primitive_type: Type/category of primitive
            cost: Cost amount in dollars
            category: Cost category
        """
        if not self._metrics_initialized:
            return

        self.cost_total.labels(
            primitive_name=primitive_name, primitive_type=primitive_type, category=category
        ).inc(cost)

    def record_savings(
        self,
        primitive_name: str,
        primitive_type: str,
        savings: float,
        category: str = "default",
    ) -> None:
        """
        Record a cost savings metric to Prometheus.

        Args:
            primitive_name: Name of the primitive
            primitive_type: Type/category of primitive
            savings: Savings amount in dollars
            category: Savings category
        """
        if not self._metrics_initialized:
            return

        self.cost_savings.labels(
            primitive_name=primitive_name, primitive_type=primitive_type, category=category
        ).inc(savings)

    def get_metrics_count(self) -> dict[str, int]:
        """
        Get count of tracked metrics.

        Returns:
            Dictionary with metric counts
        """
        return {
            "label_combinations": len(self._label_combinations),
            "max_combinations": MAX_LABEL_COMBINATIONS,
        }


# Global Prometheus exporter
_prometheus_exporter: PrometheusExporter | None = None
_exporter_lock = threading.Lock()


def get_prometheus_exporter() -> PrometheusExporter:
    """
    Get the global Prometheus exporter.

    Thread-safe singleton pattern.

    Returns:
        Global PrometheusExporter instance
    """
    global _prometheus_exporter

    if _prometheus_exporter is None:
        with _exporter_lock:
            # Double-check locking pattern
            if _prometheus_exporter is None:
                _prometheus_exporter = PrometheusExporter()

    return _prometheus_exporter
