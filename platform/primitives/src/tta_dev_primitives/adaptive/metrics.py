"""Prometheus metrics for adaptive/self-improving primitives.

This module provides OpenTelemetry-based metrics collection for adaptive primitives,
enabling observability into the learning process, strategy effectiveness, and
circuit breaker behavior.

Metrics Categories:
1. Learning Metrics - Strategy creation and adaptation
2. Validation Metrics - Strategy validation success/failure
3. Performance Metrics - Strategy effectiveness vs baseline
4. Safety Metrics - Circuit breaker trips and recovery
5. Context Metrics - Context drift detection and switches

Integration:
- Uses OpenTelemetry Metrics API (graceful degradation if unavailable)
- Compatible with Prometheus via OTLP exporter
- Works with existing observability_integration package
- No external dependencies required (optional enhancement)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opentelemetry.metrics import Counter, Histogram, UpDownCounter

logger = logging.getLogger(__name__)


class AdaptiveMetrics:
    """
    Metrics collector for adaptive primitives.

    Provides comprehensive observability into the learning process using
    OpenTelemetry metrics. Gracefully degrades if OpenTelemetry is not available.

    Metrics Provided:
        Learning Metrics:
        - adaptive_strategies_created_total{primitive_type, context}: New strategies created
        - adaptive_strategies_adopted_total{primitive_type, context}: Strategies adopted after validation
        - adaptive_strategies_rejected_total{primitive_type, context, reason}: Strategies rejected
        - adaptive_learning_rate{primitive_type}: Rate of strategy adaptations per hour

        Validation Metrics:
        - adaptive_validation_success_total{primitive_type, strategy_name}: Successful validations
        - adaptive_validation_failure_total{primitive_type, strategy_name, reason}: Failed validations
        - adaptive_validation_duration_seconds{primitive_type}: Time spent validating strategies

        Performance Metrics:
        - adaptive_strategy_effectiveness{primitive_type, strategy_name, metric}: Performance vs baseline
        - adaptive_performance_improvement_pct{primitive_type, metric}: % improvement over baseline
        - adaptive_strategy_executions_total{primitive_type, strategy_name}: Executions per strategy

        Safety Metrics:
        - adaptive_circuit_breaker_trips_total{primitive_type, reason}: Circuit breaker activations
        - adaptive_circuit_breaker_resets_total{primitive_type}: Circuit breaker recoveries
        - adaptive_fallback_activations_total{primitive_type, trigger}: Fallback to baseline

        Context Metrics:
        - adaptive_context_switches_total{primitive_type, from_context, to_context}: Context changes
        - adaptive_context_drift_detected_total{primitive_type, context}: Context drift detections
        - adaptive_active_strategies{primitive_type}: Current number of active strategies

    Example:
        >>> from tta_dev_primitives.adaptive.metrics import get_adaptive_metrics
        >>>
        >>> # Get metrics collector (singleton)
        >>> metrics = get_adaptive_metrics()
        >>>
        >>> # Record learning event
        >>> metrics.record_strategy_created("AdaptiveRetryPrimitive", "production_v2")
        >>>
        >>> # Record validation
        >>> metrics.record_validation_success("AdaptiveRetryPrimitive", "production_v2", 1.2)
        >>>
        >>> # Record performance
        >>> metrics.record_strategy_execution(
        ...     "AdaptiveRetryPrimitive", "production_v2", success_rate=0.95, latency_ms=250
        ... )
        >>>
        >>> # Record circuit breaker trip
        >>> metrics.record_circuit_breaker_trip("AdaptiveRetryPrimitive", "high_failure_rate")

    Integration with Prometheus:
        If using tta-observability-integration package:
        1. Initialize observability: initialize_observability(service_name="my_app")
        2. Metrics automatically exported on port 9464
        3. Query in Prometheus: adaptive_strategies_created_total{primitive_type="AdaptiveRetryPrimitive"}
        4. Create Grafana dashboards using provided templates
    """

    def __init__(self) -> None:
        """Initialize adaptive metrics collector."""
        self._meter = None
        self._enabled = False

        # Learning metrics
        self._strategies_created: Counter | None = None
        self._strategies_adopted: Counter | None = None
        self._strategies_rejected: Counter | None = None
        self._learning_rate: Histogram | None = None

        # Validation metrics
        self._validation_success: Counter | None = None
        self._validation_failure: Counter | None = None
        self._validation_duration: Histogram | None = None

        # Performance metrics
        self._strategy_effectiveness: Histogram | None = None
        self._performance_improvement: Histogram | None = None
        self._strategy_executions: Counter | None = None

        # Safety metrics
        self._circuit_breaker_trips: Counter | None = None
        self._circuit_breaker_resets: Counter | None = None
        self._fallback_activations: Counter | None = None

        # Context metrics
        self._context_switches: Counter | None = None
        self._context_drift_detected: Counter | None = None
        self._active_strategies: UpDownCounter | None = None

        # Try to initialize OpenTelemetry metrics
        self._initialize_metrics()

    def _initialize_metrics(self) -> None:
        """Initialize OpenTelemetry metrics (graceful degradation if unavailable)."""
        try:
            from opentelemetry import metrics

            # Try to get meter from global meter provider
            meter_provider = metrics.get_meter_provider()
            self._meter = meter_provider.get_meter("tta_dev_primitives.adaptive")

            # Create learning metrics
            self._strategies_created = self._meter.create_counter(
                name="adaptive_strategies_created_total",
                description="Total number of new strategies created",
                unit="1",
            )
            self._strategies_adopted = self._meter.create_counter(
                name="adaptive_strategies_adopted_total",
                description="Total number of strategies adopted after validation",
                unit="1",
            )
            self._strategies_rejected = self._meter.create_counter(
                name="adaptive_strategies_rejected_total",
                description="Total number of strategies rejected during validation",
                unit="1",
            )
            self._learning_rate = self._meter.create_histogram(
                name="adaptive_learning_rate",
                description="Rate of strategy adaptations per hour",
                unit="1/h",
            )

            # Create validation metrics
            self._validation_success = self._meter.create_counter(
                name="adaptive_validation_success_total",
                description="Total successful strategy validations",
                unit="1",
            )
            self._validation_failure = self._meter.create_counter(
                name="adaptive_validation_failure_total",
                description="Total failed strategy validations",
                unit="1",
            )
            self._validation_duration = self._meter.create_histogram(
                name="adaptive_validation_duration_seconds",
                description="Time spent validating strategies",
                unit="s",
            )

            # Create performance metrics
            self._strategy_effectiveness = self._meter.create_histogram(
                name="adaptive_strategy_effectiveness",
                description="Strategy performance metric values",
                unit="1",
            )
            self._performance_improvement = self._meter.create_histogram(
                name="adaptive_performance_improvement_pct",
                description="Percentage improvement over baseline",
                unit="%",
            )
            self._strategy_executions = self._meter.create_counter(
                name="adaptive_strategy_executions_total",
                description="Total executions per strategy",
                unit="1",
            )

            # Create safety metrics
            self._circuit_breaker_trips = self._meter.create_counter(
                name="adaptive_circuit_breaker_trips_total",
                description="Total circuit breaker activations",
                unit="1",
            )
            self._circuit_breaker_resets = self._meter.create_counter(
                name="adaptive_circuit_breaker_resets_total",
                description="Total circuit breaker recoveries",
                unit="1",
            )
            self._fallback_activations = self._meter.create_counter(
                name="adaptive_fallback_activations_total",
                description="Total fallbacks to baseline strategy",
                unit="1",
            )

            # Create context metrics
            self._context_switches = self._meter.create_counter(
                name="adaptive_context_switches_total",
                description="Total context switches",
                unit="1",
            )
            self._context_drift_detected = self._meter.create_counter(
                name="adaptive_context_drift_detected_total",
                description="Total context drift detections",
                unit="1",
            )
            self._active_strategies = self._meter.create_up_down_counter(
                name="adaptive_active_strategies",
                description="Current number of active strategies",
                unit="1",
            )

            self._enabled = True
            logger.info("Adaptive metrics initialized with OpenTelemetry")

        except ImportError:
            logger.info(
                "OpenTelemetry not available - adaptive metrics disabled. "
                "Install 'opentelemetry-api' to enable metrics."
            )
            self._enabled = False
        except Exception as e:
            logger.warning(f"Failed to initialize adaptive metrics: {e}")
            self._enabled = False

    # Learning Metrics

    def record_strategy_created(
        self, primitive_type: str, strategy_name: str, context: str = "default"
    ) -> None:
        """
        Record creation of a new strategy.

        Args:
            primitive_type: Type of adaptive primitive (e.g., "AdaptiveRetryPrimitive")
            strategy_name: Name of the strategy created
            context: Execution context (e.g., "production", "staging")
        """
        if self._strategies_created:
            self._strategies_created.add(
                1,
                {
                    "primitive_type": primitive_type,
                    "strategy_name": strategy_name,
                    "context": context,
                },
            )

    def record_strategy_adopted(
        self, primitive_type: str, strategy_name: str, context: str = "default"
    ) -> None:
        """
        Record adoption of a validated strategy.

        Args:
            primitive_type: Type of adaptive primitive
            strategy_name: Name of the strategy adopted
            context: Execution context
        """
        if self._strategies_adopted:
            self._strategies_adopted.add(
                1,
                {
                    "primitive_type": primitive_type,
                    "strategy_name": strategy_name,
                    "context": context,
                },
            )

    def record_strategy_rejected(
        self,
        primitive_type: str,
        strategy_name: str,
        reason: str,
        context: str = "default",
    ) -> None:
        """
        Record rejection of a strategy during validation.

        Args:
            primitive_type: Type of adaptive primitive
            strategy_name: Name of the strategy rejected
            reason: Reason for rejection (e.g., "performance_regression", "insufficient_data")
            context: Execution context
        """
        if self._strategies_rejected:
            self._strategies_rejected.add(
                1,
                {
                    "primitive_type": primitive_type,
                    "strategy_name": strategy_name,
                    "reason": reason,
                    "context": context,
                },
            )

    def record_learning_rate(self, primitive_type: str, adaptations_per_hour: float) -> None:
        """
        Record learning rate (adaptations per hour).

        Args:
            primitive_type: Type of adaptive primitive
            adaptations_per_hour: Number of strategy adaptations per hour
        """
        if self._learning_rate:
            self._learning_rate.record(adaptations_per_hour, {"primitive_type": primitive_type})

    # Validation Metrics

    def record_validation_success(
        self, primitive_type: str, strategy_name: str, duration_seconds: float
    ) -> None:
        """
        Record successful strategy validation.

        Args:
            primitive_type: Type of adaptive primitive
            strategy_name: Name of the strategy validated
            duration_seconds: Time taken to validate
        """
        if self._validation_success:
            self._validation_success.add(
                1, {"primitive_type": primitive_type, "strategy_name": strategy_name}
            )
        if self._validation_duration:
            self._validation_duration.record(
                duration_seconds,
                {"primitive_type": primitive_type, "strategy_name": strategy_name},
            )

    def record_validation_failure(
        self,
        primitive_type: str,
        strategy_name: str,
        reason: str,
        duration_seconds: float,
    ) -> None:
        """
        Record failed strategy validation.

        Args:
            primitive_type: Type of adaptive primitive
            strategy_name: Name of the strategy that failed validation
            reason: Reason for validation failure
            duration_seconds: Time taken before failure
        """
        if self._validation_failure:
            self._validation_failure.add(
                1,
                {
                    "primitive_type": primitive_type,
                    "strategy_name": strategy_name,
                    "reason": reason,
                },
            )
        if self._validation_duration:
            self._validation_duration.record(
                duration_seconds,
                {"primitive_type": primitive_type, "strategy_name": strategy_name},
            )

    # Performance Metrics

    def record_strategy_execution(
        self,
        primitive_type: str,
        strategy_name: str,
        success_rate: float | None = None,
        latency_ms: float | None = None,
        custom_metrics: dict[str, float] | None = None,
    ) -> None:
        """
        Record strategy execution performance metrics.

        Args:
            primitive_type: Type of adaptive primitive
            strategy_name: Name of the strategy executed
            success_rate: Success rate (0.0 to 1.0)
            latency_ms: Average latency in milliseconds
            custom_metrics: Additional custom metrics
        """
        if self._strategy_executions:
            self._strategy_executions.add(
                1, {"primitive_type": primitive_type, "strategy_name": strategy_name}
            )

        # Record effectiveness metrics
        if self._strategy_effectiveness:
            if success_rate is not None:
                self._strategy_effectiveness.record(
                    success_rate,
                    {
                        "primitive_type": primitive_type,
                        "strategy_name": strategy_name,
                        "metric": "success_rate",
                    },
                )
            if latency_ms is not None:
                self._strategy_effectiveness.record(
                    latency_ms,
                    {
                        "primitive_type": primitive_type,
                        "strategy_name": strategy_name,
                        "metric": "latency_ms",
                    },
                )
            if custom_metrics:
                for metric_name, value in custom_metrics.items():
                    self._strategy_effectiveness.record(
                        value,
                        {
                            "primitive_type": primitive_type,
                            "strategy_name": strategy_name,
                            "metric": metric_name,
                        },
                    )

    def record_performance_improvement(
        self, primitive_type: str, metric_name: str, improvement_pct: float
    ) -> None:
        """
        Record performance improvement over baseline.

        Args:
            primitive_type: Type of adaptive primitive
            metric_name: Name of the metric (e.g., "success_rate", "latency")
            improvement_pct: Percentage improvement (positive = better, negative = worse)
        """
        if self._performance_improvement:
            self._performance_improvement.record(
                improvement_pct,
                {"primitive_type": primitive_type, "metric": metric_name},
            )

    # Safety Metrics

    def record_circuit_breaker_trip(self, primitive_type: str, reason: str) -> None:
        """
        Record circuit breaker activation.

        Args:
            primitive_type: Type of adaptive primitive
            reason: Reason for circuit breaker trip (e.g., "high_failure_rate", "performance_regression")
        """
        if self._circuit_breaker_trips:
            self._circuit_breaker_trips.add(1, {"primitive_type": primitive_type, "reason": reason})

    def record_circuit_breaker_reset(self, primitive_type: str) -> None:
        """
        Record circuit breaker recovery.

        Args:
            primitive_type: Type of adaptive primitive
        """
        if self._circuit_breaker_resets:
            self._circuit_breaker_resets.add(1, {"primitive_type": primitive_type})

    def record_fallback_activation(self, primitive_type: str, trigger: str) -> None:
        """
        Record fallback to baseline strategy.

        Args:
            primitive_type: Type of adaptive primitive
            trigger: What triggered fallback (e.g., "circuit_breaker", "validation_failure")
        """
        if self._fallback_activations:
            self._fallback_activations.add(
                1, {"primitive_type": primitive_type, "trigger": trigger}
            )

    # Context Metrics

    def record_context_switch(
        self, primitive_type: str, from_context: str, to_context: str
    ) -> None:
        """
        Record context switch.

        Args:
            primitive_type: Type of adaptive primitive
            from_context: Previous context
            to_context: New context
        """
        if self._context_switches:
            self._context_switches.add(
                1,
                {
                    "primitive_type": primitive_type,
                    "from_context": from_context,
                    "to_context": to_context,
                },
            )

    def record_context_drift(self, primitive_type: str, context: str) -> None:
        """
        Record context drift detection.

        Args:
            primitive_type: Type of adaptive primitive
            context: Context where drift was detected
        """
        if self._context_drift_detected:
            self._context_drift_detected.add(
                1, {"primitive_type": primitive_type, "context": context}
            )

    def update_active_strategies(self, primitive_type: str, delta: int) -> None:
        """
        Update active strategy count.

        Args:
            primitive_type: Type of adaptive primitive
            delta: Change in strategy count (+1 for new, -1 for removed)
        """
        if self._active_strategies:
            self._active_strategies.add(delta, {"primitive_type": primitive_type})

    @property
    def enabled(self) -> bool:
        """Check if metrics collection is enabled."""
        return self._enabled


# Singleton instance
_adaptive_metrics: AdaptiveMetrics | None = None


def get_adaptive_metrics() -> AdaptiveMetrics:
    """
    Get the global adaptive metrics collector (singleton).

    Returns:
        Singleton AdaptiveMetrics instance

    Example:
        >>> metrics = get_adaptive_metrics()
        >>> metrics.record_strategy_created("AdaptiveRetryPrimitive", "prod_v1")
    """
    global _adaptive_metrics
    if _adaptive_metrics is None:
        _adaptive_metrics = AdaptiveMetrics()
    return _adaptive_metrics


# Convenience function for disabling metrics in tests
def reset_adaptive_metrics() -> None:
    """Reset the global metrics instance (primarily for testing)."""
    global _adaptive_metrics
    _adaptive_metrics = None
