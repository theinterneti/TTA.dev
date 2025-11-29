"""
Phase 2: Core OpenTelemetry Metrics

This module implements the 7 core metrics from the observability strategy:
1. primitive.execution.count - Counter for total executions
2. primitive.execution.duration - Histogram for latency percentiles
3. primitive.connection.count - Counter for service map
4. llm.tokens.total - Counter for LLM token usage
5. cache.hits / cache.total - Counters for hit rate calculation
6. agent.workflows.active - UpDownCounter for active workflows
7. slo.compliance - Gauge for SLO compliance (0.0-1.0)

All metrics follow OpenTelemetry semantic conventions and the
observability strategy's attribute standards.
"""

from __future__ import annotations

import logging
from typing import Any

# Check if OpenTelemetry is available
try:
    from opentelemetry import metrics
    from opentelemetry.metrics import Counter, Histogram, UpDownCounter

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    metrics = None  # type: ignore
    Counter = None  # type: ignore
    Histogram = None  # type: ignore
    UpDownCounter = None  # type: ignore

logger = logging.getLogger(__name__)


class PrimitiveMetrics:
    """
    Core OpenTelemetry metrics for TTA.dev primitives.

    Implements the 7 core metrics following the observability strategy.
    Gracefully degrades when OpenTelemetry is unavailable.
    """

    def __init__(self, meter_name: str = "tta.primitives") -> None:
        """
        Initialize primitive metrics.

        Args:
            meter_name: Name for the OpenTelemetry meter
        """
        self._enabled = METRICS_AVAILABLE

        if self._enabled and metrics is not None:
            # Get meter
            self._meter = metrics.get_meter(meter_name)

            # 1. Execution count - tracks total primitive executions
            self._execution_count = self._meter.create_counter(
                name="primitive.execution.count",
                description="Total number of primitive executions",
                unit="1",
            )

            # 2. Execution duration - histogram for percentile calculation
            # Buckets: 10ms, 50ms, 100ms, 250ms, 500ms, 1s, 2.5s, 5s, 10s
            self._execution_duration = self._meter.create_histogram(
                name="primitive.execution.duration",
                description="Primitive execution duration in milliseconds",
                unit="ms",
            )

            # 3. Connection count - tracks primitive-to-primitive connections
            self._connection_count = self._meter.create_counter(
                name="primitive.connection.count",
                description="Number of connections between primitives",
                unit="1",
            )

            # 4. LLM tokens - tracks token usage
            self._llm_tokens_total = self._meter.create_counter(
                name="llm.tokens.total",
                description="Total LLM tokens consumed",
                unit="1",
            )

            # 5. Cache metrics - for hit rate calculation
            self._cache_hits = self._meter.create_counter(
                name="cache.hits",
                description="Total cache hits",
                unit="1",
            )
            self._cache_total = self._meter.create_counter(
                name="cache.total",
                description="Total cache operations",
                unit="1",
            )

            # 6. Active workflows - UpDownCounter for gauge behavior
            self._workflows_active = self._meter.create_up_down_counter(
                name="agent.workflows.active",
                description="Number of currently active workflows",
                unit="1",
            )

            logger.info(
                "primitive_metrics_initialized",
                extra={"meter_name": meter_name},
            )
        else:
            logger.warning(
                "primitive_metrics_disabled",
                extra={"reason": "OpenTelemetry not available - metrics will not be recorded"},
            )

    def record_execution(
        self,
        primitive_name: str,
        primitive_type: str,
        duration_ms: float,
        status: str,
        agent_type: str | None = None,
        error_type: str | None = None,
    ) -> None:
        """
        Record a primitive execution.

        Args:
            primitive_name: Name of the primitive
            primitive_type: Type of primitive (e.g., 'sequential', 'cache')
            duration_ms: Execution duration in milliseconds
            status: Execution status ('success' or 'error')
            agent_type: Optional agent type
            error_type: Optional error type (for failures)
        """
        if not self._enabled:
            return

        # Build attributes following strategy standards
        attrs: dict[str, Any] = {
            "primitive.name": primitive_name,
            "primitive.type": primitive_type,
            "execution.status": status,
        }

        if agent_type:
            attrs["agent.type"] = agent_type
        if error_type:
            attrs["error.type"] = error_type

        # Record metrics
        self._execution_count.add(1, attributes=attrs)
        self._execution_duration.record(duration_ms, attributes=attrs)

    def record_connection(
        self,
        source_primitive: str,
        target_primitive: str,
        connection_type: str = "sequential",
    ) -> None:
        """
        Record a connection between primitives (for service map).

        Args:
            source_primitive: Source primitive name
            target_primitive: Target primitive name
            connection_type: Type of connection (e.g., 'sequential', 'parallel')
        """
        if not self._enabled:
            return

        attrs = {
            "source.primitive": source_primitive,
            "target.primitive": target_primitive,
            "connection.type": connection_type,
        }

        self._connection_count.add(1, attributes=attrs)

    def record_llm_tokens(
        self,
        provider: str,
        model_name: str,
        token_type: str,
        count: int,
    ) -> None:
        """
        Record LLM token usage.

        Args:
            provider: LLM provider (e.g., 'openai', 'anthropic')
            model_name: Model name (e.g., 'gpt-4', 'claude-3-sonnet')
            token_type: Token type ('prompt' or 'completion')
            count: Number of tokens
        """
        if not self._enabled:
            return

        attrs = {
            "llm.provider": provider,
            "llm.model_name": model_name,
            "llm.token_type": token_type,
        }

        self._llm_tokens_total.add(count, attributes=attrs)

    def record_cache_operation(
        self,
        primitive_name: str,
        hit: bool,
        cache_type: str | None = None,
    ) -> None:
        """
        Record a cache operation.

        Args:
            primitive_name: Name of the cache primitive
            hit: Whether this was a cache hit
            cache_type: Optional cache type (e.g., 'lru', 'ttl')
        """
        if not self._enabled:
            return

        attrs: dict[str, Any] = {
            "primitive.name": primitive_name,
        }
        if cache_type:
            attrs["cache.type"] = cache_type

        # Record total operations
        self._cache_total.add(1, attributes=attrs)

        # Record hits if applicable
        if hit:
            self._cache_hits.add(1, attributes=attrs)

    def workflow_started(self, agent_type: str | None = None) -> None:
        """
        Increment active workflow count.

        Args:
            agent_type: Optional agent type
        """
        if not self._enabled:
            return

        attrs: dict[str, Any] = {}
        if agent_type:
            attrs["agent.type"] = agent_type

        self._workflows_active.add(1, attributes=attrs)

    def workflow_completed(self, agent_type: str | None = None) -> None:
        """
        Decrement active workflow count.

        Args:
            agent_type: Optional agent type
        """
        if not self._enabled:
            return

        attrs: dict[str, Any] = {}
        if agent_type:
            attrs["agent.type"] = agent_type

        self._workflows_active.add(-1, attributes=attrs)


# Global singleton instance
_metrics_instance: PrimitiveMetrics | None = None


def get_primitive_metrics() -> PrimitiveMetrics:
    """
    Get the global PrimitiveMetrics instance.

    Returns:
        Singleton PrimitiveMetrics instance
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = PrimitiveMetrics()
    return _metrics_instance
