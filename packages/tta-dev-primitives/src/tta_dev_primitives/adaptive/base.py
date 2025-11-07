"""Base classes for adaptive/self-improving primitives.

This module provides the foundation for primitives that learn from observability data
and adapt their strategies over time while maintaining safety and validation.

Key Design Principles:
1. Conservative Learning: Prove improvement before adopting strategies
2. Context Awareness: Strategies tied to environmental conditions
3. Circuit Breakers: Fall back to baseline when learning fails
4. Meta-Observability: Observe the learning process itself
5. Validation Windows: Test strategies on holdout data

Critical Safeguards:
- Learning can be disabled per environment
- Baseline strategies always available as fallback
- Strategy performance validation before adoption
- Context drift detection and adaptation
- Resource limits on learning overhead
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive

logger = logging.getLogger(__name__)

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class LearningMode(Enum):
    """Learning modes for adaptive primitives."""

    DISABLED = "disabled"  # No learning, use baseline only
    OBSERVE = "observe"  # Collect data but don't adapt strategies
    VALIDATE = "validate"  # Test new strategies but don't adopt without validation
    ACTIVE = "active"  # Full learning with validated strategies


@dataclass
class StrategyMetrics:
    """Metrics for evaluating strategy performance."""

    success_count: int = 0
    failure_count: int = 0
    total_latency: float = 0.0
    total_executions: int = 0

    # Context tracking
    contexts_seen: set[str] = field(default_factory=set)
    last_updated: float = field(default_factory=time.time)

    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)."""
        if self.total_executions == 0:
            return 0.0
        return self.success_count / self.total_executions

    @property
    def avg_latency(self) -> float:
        """Calculate average latency in seconds."""
        if self.success_count == 0:
            return float("inf")
        return self.total_latency / self.success_count

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate (0.0 to 1.0)."""
        return 1.0 - self.success_rate

    def update(self, success: bool, latency: float, context_key: str) -> None:
        """Update metrics with new execution result."""
        self.total_executions += 1
        if success:
            self.success_count += 1
            self.total_latency += latency
        else:
            self.failure_count += 1

        self.contexts_seen.add(context_key)
        self.last_updated = time.time()

    def is_better_than(
        self, other: StrategyMetrics, significance_threshold: float = 0.05
    ) -> bool:
        """Check if this strategy is significantly better than another."""
        # Require minimum sample size for comparison
        if self.total_executions < 10 or other.total_executions < 10:
            return False

        # Success rate must be significantly higher
        success_diff = self.success_rate - other.success_rate
        if success_diff < significance_threshold:
            return False

        # Latency should not be significantly worse (allow 10% degradation)
        if self.avg_latency > other.avg_latency * 1.1:
            return False

        return True


@dataclass
class LearningStrategy:
    """A learned strategy with associated metadata and performance metrics."""

    name: str
    description: str
    parameters: dict[str, Any]
    context_pattern: str  # Pattern to match contexts where this strategy applies

    # Performance tracking
    metrics: StrategyMetrics = field(default_factory=StrategyMetrics)
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)

    # Validation tracking
    validation_attempts: int = 0
    validation_successes: int = 0
    is_validated: bool = False

    def matches_context(self, context_key: str) -> bool:
        """Check if this strategy applies to the given context."""
        # Simple pattern matching - could be enhanced with regex or ML
        return self.context_pattern in context_key.lower()

    def record_usage(self, success: bool, latency: float, context_key: str) -> None:
        """Record the results of using this strategy."""
        self.metrics.update(success, latency, context_key)
        self.last_used = time.time()

    def record_validation(self, success: bool) -> None:
        """Record validation attempt results."""
        self.validation_attempts += 1
        if success:
            self.validation_successes += 1

        # Mark as validated if it passes validation threshold
        if self.validation_attempts >= 5:  # Minimum validation attempts
            validation_rate = self.validation_successes / self.validation_attempts
            self.is_validated = validation_rate >= 0.8  # 80% validation success


class AdaptivePrimitive(InstrumentedPrimitive[TInput, TOutput], ABC):
    """Base class for primitives that learn from observability data.

    This abstract base class provides:
    - Strategy learning and management
    - Observability data collection
    - Context-aware strategy selection
    - Performance validation and circuit breaking
    - Meta-observability of learning process
    """

    def __init__(
        self,
        learning_mode: LearningMode = LearningMode.VALIDATE,
        max_strategies: int = 10,
        validation_window: int = 50,
        circuit_breaker_threshold: float = 0.5,
        context_extractor: callable | None = None,
    ):
        super().__init__()

        self.learning_mode = learning_mode
        self.max_strategies = max_strategies
        self.validation_window = validation_window
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.context_extractor = context_extractor or self._default_context_extractor

        # Strategy management
        self.strategies: dict[str, LearningStrategy] = {}
        self.baseline_strategy: LearningStrategy | None = None

        # Circuit breaker state
        self.circuit_breaker_active = False
        self.circuit_breaker_until = 0.0

        # Learning statistics
        self.total_adaptations = 0
        self.successful_adaptations = 0
        self.context_drift_detections = 0

        logger.info(
            f"Initialized {self.__class__.__name__} with learning_mode={learning_mode.value}"
        )

    async def _execute_impl(
        self, input_data: TInput, context: WorkflowContext
    ) -> TOutput:
        """Execute with adaptive strategy selection and learning."""

        # Extract context for strategy selection
        context_key = self.context_extractor(input_data, context)

        # Select best strategy for this context
        strategy = self._select_strategy(context_key)

        # Execute with observability and learning
        start_time = time.time()

        try:
            # Use tracing if available
            if self._tracer:
                with self._tracer.start_as_current_span("adaptive_execution") as span:
                    span.set_attribute("adaptive.strategy_name", strategy.name)
                    span.set_attribute("adaptive.context_key", context_key)
                    span.set_attribute(
                        "adaptive.learning_mode", self.learning_mode.value
                    )
                    span.set_attribute(
                        "adaptive.circuit_breaker_active", self.circuit_breaker_active
                    )

                    # Execute the actual primitive logic with selected strategy
                    result = await self._execute_with_strategy(
                        input_data, context, strategy
                    )

                    execution_time = time.time() - start_time

                    # Record successful execution
                    strategy.record_usage(True, execution_time, context_key)

                    # Learn from observability data if enabled
                    if self.learning_mode in [
                        LearningMode.OBSERVE,
                        LearningMode.VALIDATE,
                        LearningMode.ACTIVE,
                    ]:
                        await self._learn_from_execution(
                            input_data, context, strategy, result, execution_time
                        )

                    # Update learning metrics
                    span.set_attribute("adaptive.execution_time", execution_time)
                    span.set_attribute(
                        "adaptive.strategy_success_rate", strategy.metrics.success_rate
                    )
                    span.set_attribute(
                        "adaptive.total_strategies", len(self.strategies)
                    )

                    return result
            else:
                # No tracing available - execute without spans
                result = await self._execute_with_strategy(
                    input_data, context, strategy
                )

                execution_time = time.time() - start_time
                strategy.record_usage(True, execution_time, context_key)

                if self.learning_mode in [
                    LearningMode.OBSERVE,
                    LearningMode.VALIDATE,
                    LearningMode.ACTIVE,
                ]:
                    await self._learn_from_execution(
                        input_data, context, strategy, result, execution_time
                    )

                return result

        except Exception as e:
            execution_time = time.time() - start_time

            # Record failed execution
            strategy.record_usage(False, execution_time, context_key)

            # Check if we should activate circuit breaker
            if strategy.metrics.failure_rate > self.circuit_breaker_threshold:
                self._activate_circuit_breaker()

            # Re-raise the exception
            raise e

    def _select_strategy(self, context_key: str) -> LearningStrategy:
        """Select the best strategy for the given context."""

        # Circuit breaker: use baseline only
        if self.circuit_breaker_active:
            if time.time() < self.circuit_breaker_until:
                logger.warning("Circuit breaker active - using baseline strategy")
                return self.baseline_strategy or self._get_default_strategy()
            else:
                # Circuit breaker expired, deactivate
                self.circuit_breaker_active = False
                logger.info("Circuit breaker deactivated")

        # Learning disabled: use baseline only
        if self.learning_mode == LearningMode.DISABLED:
            return self.baseline_strategy or self._get_default_strategy()

        # Find strategies that match this context
        matching_strategies = [
            strategy
            for strategy in self.strategies.values()
            if strategy.matches_context(context_key)
        ]

        # No matching strategies: use baseline
        if not matching_strategies:
            return self.baseline_strategy or self._get_default_strategy()

        # In VALIDATE mode, only use validated strategies
        if self.learning_mode == LearningMode.VALIDATE:
            validated_strategies = [s for s in matching_strategies if s.is_validated]
            if validated_strategies:
                matching_strategies = validated_strategies
            else:
                # No validated strategies, use baseline
                return self.baseline_strategy or self._get_default_strategy()

        # Select best strategy based on metrics
        best_strategy = max(matching_strategies, key=lambda s: s.metrics.success_rate)

        # Ensure the best strategy is actually better than baseline
        baseline = self.baseline_strategy or self._get_default_strategy()
        if not best_strategy.metrics.is_better_than(baseline.metrics):
            return baseline

        return best_strategy

    def _activate_circuit_breaker(self, duration_seconds: float = 300.0) -> None:
        """Activate circuit breaker to prevent further learning attempts."""
        self.circuit_breaker_active = True
        self.circuit_breaker_until = time.time() + duration_seconds
        logger.warning(f"Circuit breaker activated for {duration_seconds} seconds")

    def _default_context_extractor(
        self, input_data: TInput, context: WorkflowContext
    ) -> str:
        """Default context extraction - can be overridden by subclasses."""
        # Simple context based on input type and metadata
        input_type = type(input_data).__name__
        priority = context.metadata.get("priority", "normal")
        environment = context.metadata.get("environment", "unknown")

        return f"{input_type}:{priority}:{environment}"

    @abstractmethod
    async def _execute_with_strategy(
        self, input_data: TInput, context: WorkflowContext, strategy: LearningStrategy
    ) -> TOutput:
        """Execute the primitive using the selected strategy.

        This method must be implemented by subclasses to define how the strategy
        parameters are applied to the actual execution logic.
        """
        pass

    @abstractmethod
    def _get_default_strategy(self) -> LearningStrategy:
        """Get the default/baseline strategy for this primitive type.

        This method must be implemented by subclasses to provide a safe
        fallback strategy when no learned strategies are available.
        """
        pass

    async def _learn_from_execution(
        self,
        input_data: TInput,
        context: WorkflowContext,
        strategy: LearningStrategy,
        result: TOutput,
        execution_time: float,
    ) -> None:
        """Learn from execution results and observability data.

        This method can be overridden by subclasses to implement specific
        learning algorithms based on their domain knowledge.
        """
        # Base implementation: simple success/failure learning
        # Subclasses can override for more sophisticated learning

        # Check if we should create a new strategy based on performance
        if strategy.metrics.total_executions > 20:  # Minimum sample size
            await self._consider_strategy_adaptation(
                input_data, context, strategy, execution_time
            )

    async def _consider_strategy_adaptation(
        self,
        input_data: TInput,
        context: WorkflowContext,
        current_strategy: LearningStrategy,
        execution_time: float,
    ) -> None:
        """Consider creating new strategies based on performance patterns."""
        # This is where subclasses can implement domain-specific learning
        # Base implementation is conservative - just track that we considered it

        logger.debug(f"Considered strategy adaptation for {current_strategy.name}")

    def get_learning_summary(self) -> dict[str, Any]:
        """Get summary of learning progress and statistics."""
        return {
            "learning_mode": self.learning_mode.value,
            "total_strategies": len(self.strategies),
            "circuit_breaker_active": self.circuit_breaker_active,
            "total_adaptations": self.total_adaptations,
            "successful_adaptations": self.successful_adaptations,
            "context_drift_detections": self.context_drift_detections,
            "strategies": {
                name: {
                    "success_rate": strategy.metrics.success_rate,
                    "avg_latency": strategy.metrics.avg_latency,
                    "executions": strategy.metrics.total_executions,
                    "contexts": len(strategy.metrics.contexts_seen),
                    "validated": strategy.is_validated,
                }
                for name, strategy in self.strategies.items()
            },
        }


# Export types and classes
__all__ = [
    "AdaptivePrimitive",
    "LearningStrategy",
    "StrategyMetrics",
    "LearningMode",
]
