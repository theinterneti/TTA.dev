"""
Prometheus-compatible metrics for TTA.dev primitives.

This module provides Prometheus Counter and Histogram metrics that complement
the existing OpenTelemetry metrics. These metrics use the naming convention
expected by the Prometheus recording rules and Grafana dashboards.

Metrics exported:
- tta_workflow_executions_total: Counter for workflow executions
- tta_primitive_executions_total: Counter for primitive executions
- tta_llm_cost_total: Counter for LLM API costs in USD
- tta_execution_duration_seconds: Histogram for execution durations
- tta_cache_hits_total: Counter for cache hits
- tta_cache_misses_total: Counter for cache misses

All metrics gracefully degrade when prometheus_client is unavailable.
"""

from __future__ import annotations

import logging

# Check if prometheus_client is available
try:
    from prometheus_client import Counter, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = None  # type: ignore
    Histogram = None  # type: ignore

logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """
    Prometheus metrics for TTA.dev primitives.

    Provides Prometheus-formatted counters and histograms that align with
    recording rules and dashboard expectations.
    """

    def __init__(self) -> None:
        """Initialize Prometheus metrics."""
        self._enabled = PROMETHEUS_AVAILABLE

        if self._enabled and Counter is not None and Histogram is not None:
            # Workflow execution counter
            self._workflow_executions = Counter(
                "tta_workflow_executions_total",
                "Total number of workflow executions",
                ["workflow_name", "status", "job"],
            )

            # Primitive execution counter
            self._primitive_executions = Counter(
                "tta_primitive_executions_total",
                "Total number of primitive executions",
                ["primitive_type", "primitive_name", "status", "job"],
            )

            # LLM cost counter (in USD)
            self._llm_cost = Counter(
                "tta_llm_cost_total",
                "Total LLM API costs in USD",
                ["model", "provider", "job"],
            )

            # Execution duration histogram
            # Buckets: 10ms, 50ms, 100ms, 250ms, 500ms, 1s, 2.5s, 5s, 10s, 30s
            self._execution_duration = Histogram(
                "tta_execution_duration_seconds",
                "Primitive execution duration in seconds",
                ["primitive_type", "job"],
                buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
            )

            # Cache hit counter
            self._cache_hits = Counter(
                "tta_cache_hits_total",
                "Total cache hits",
                ["primitive_name", "cache_type", "job"],
            )

            # Cache miss counter
            self._cache_misses = Counter(
                "tta_cache_misses_total",
                "Total cache misses",
                ["primitive_name", "cache_type", "job"],
            )

            logger.info("prometheus_metrics_initialized", extra={"status": "enabled"})
        else:
            logger.warning(
                "prometheus_metrics_disabled",
                extra={"reason": "prometheus_client not available"},
            )

    def record_workflow_execution(
        self, workflow_name: str, status: str, job: str = "tta-primitives"
    ) -> None:
        """
        Record a workflow execution.

        Args:
            workflow_name: Name of the workflow (e.g., 'SequentialPrimitive')
            status: Execution status ('success' or 'failure')
            job: Job label for Prometheus (default: 'tta-primitives')
        """
        if not self._enabled:
            return

        self._workflow_executions.labels(
            workflow_name=workflow_name, status=status, job=job
        ).inc()

    def record_primitive_execution(
        self,
        primitive_type: str,
        primitive_name: str,
        status: str,
        job: str = "tta-primitives",
    ) -> None:
        """
        Record a primitive execution.

        Args:
            primitive_type: Type of primitive (e.g., 'sequential', 'cache')
            primitive_name: Specific name of the primitive instance
            status: Execution status ('success' or 'failure')
            job: Job label for Prometheus (default: 'tta-primitives')
        """
        if not self._enabled:
            return

        self._primitive_executions.labels(
            primitive_type=primitive_type,
            primitive_name=primitive_name,
            status=status,
            job=job,
        ).inc()

    def record_llm_cost(
        self, model: str, provider: str, cost_usd: float, job: str = "tta-primitives"
    ) -> None:
        """
        Record LLM API cost.

        Args:
            model: Model name (e.g., 'gpt-4', 'claude-3-sonnet')
            provider: Provider name (e.g., 'openai', 'anthropic')
            cost_usd: Cost in USD
            job: Job label for Prometheus (default: 'tta-primitives')
        """
        if not self._enabled:
            return

        self._llm_cost.labels(model=model, provider=provider, job=job).inc(cost_usd)

    def record_execution_duration(
        self, primitive_type: str, duration_seconds: float, job: str = "tta-primitives"
    ) -> None:
        """
        Record execution duration.

        Args:
            primitive_type: Type of primitive (e.g., 'sequential', 'cache')
            duration_seconds: Duration in seconds
            job: Job label for Prometheus (default: 'tta-primitives')
        """
        if not self._enabled:
            return

        self._execution_duration.labels(primitive_type=primitive_type, job=job).observe(
            duration_seconds
        )

    def record_cache_hit(
        self, primitive_name: str, cache_type: str = "lru", job: str = "tta-primitives"
    ) -> None:
        """
        Record a cache hit.

        Args:
            primitive_name: Name of the cache primitive
            cache_type: Type of cache (e.g., 'lru', 'ttl')
            job: Job label for Prometheus (default: 'tta-primitives')
        """
        if not self._enabled:
            return

        self._cache_hits.labels(
            primitive_name=primitive_name, cache_type=cache_type, job=job
        ).inc()

    def record_cache_miss(
        self, primitive_name: str, cache_type: str = "lru", job: str = "tta-primitives"
    ) -> None:
        """
        Record a cache miss.

        Args:
            primitive_name: Name of the cache primitive
            cache_type: Type of cache (e.g., 'lru', 'ttl')
            job: Job label for Prometheus (default: 'tta-primitives')
        """
        if not self._enabled:
            return

        self._cache_misses.labels(
            primitive_name=primitive_name, cache_type=cache_type, job=job
        ).inc()


# Global singleton instance
_prometheus_metrics_instance: PrometheusMetrics | None = None


def get_prometheus_metrics() -> PrometheusMetrics:
    """
    Get the global PrometheusMetrics instance.

    Returns:
        Singleton PrometheusMetrics instance
    """
    global _prometheus_metrics_instance
    if _prometheus_metrics_instance is None:
        _prometheus_metrics_instance = PrometheusMetrics()
    return _prometheus_metrics_instance
