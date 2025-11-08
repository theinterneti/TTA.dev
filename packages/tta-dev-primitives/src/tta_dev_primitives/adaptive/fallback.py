"""Adaptive fallback primitive that learns optimal fallback strategies."""

from __future__ import annotations

import time
from typing import Any

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.logging import get_logger
from .base import AdaptivePrimitive, LearningMode, LearningStrategy, StrategyMetrics

logger = get_logger(__name__)


class AdaptiveFallbackPrimitive(AdaptivePrimitive[Any, Any]):
    """
    Adaptive fallback that learns which fallback chains work best.

    Learns from execution patterns:
    - Which services fail most often
    - Which fallbacks succeed for different failure types
    - Optimal fallback order based on success rates
    - Context-specific fallback strategies

    Example:
        ```python
        from tta_dev_primitives.adaptive import AdaptiveFallbackPrimitive, LearningMode

        adaptive_fallback = AdaptiveFallbackPrimitive(
            primary=openai_api,
            fallbacks={
                "anthropic": anthropic_api,
                "google": google_api,
                "local": local_llm
            },
            learning_mode=LearningMode.ACTIVE
        )

        result = await adaptive_fallback.execute(data, context)

        # Check learned fallback order
        stats = adaptive_fallback.get_fallback_stats()
        print(f"Optimal fallback order: {stats['best_fallback_order']}")
        ```
    """

    def __init__(
        self,
        primary: WorkflowPrimitive,
        fallbacks: dict[str, WorkflowPrimitive],
        learning_mode: str | LearningMode = "VALIDATE",
        baseline_fallback_order: list[str] | None = None,
        max_strategies: int = 10,
        min_observations_before_learning: int = 10,
        validation_window: int = 20,
        enable_circuit_breaker: bool = True,
        logseq_integration: Any = None,
        enable_auto_persistence: bool = False,
    ) -> None:
        """
        Initialize adaptive fallback primitive.

        Args:
            primary: Primary primitive to try first
            fallbacks: Dictionary of fallback name -> primitive
            learning_mode: Learning mode (DISABLED, OBSERVE, VALIDATE, ACTIVE)
            baseline_fallback_order: Initial fallback order (default: alphabetical)
            max_strategies: Maximum number of learned strategies to keep
            min_observations_before_learning: Minimum observations before creating new strategies
            validation_window: Number of executions to validate new strategies
            enable_circuit_breaker: Enable circuit breaker for bad strategies
            logseq_integration: Optional LogseqStrategyIntegration for persistence
            enable_auto_persistence: Auto-save strategies to Logseq
        """
        self.primary = primary
        self.fallbacks = fallbacks
        self.logseq_integration = logseq_integration
        self.enable_auto_persistence = enable_auto_persistence
        self.min_observations_before_learning = min_observations_before_learning

        # Convert string to LearningMode enum
        from .base import LearningMode as LearningModeEnum

        if isinstance(learning_mode, str):
            learning_mode = LearningModeEnum[learning_mode]

        # Statistics tracking
        self._primary_attempts = 0
        self._primary_failures = 0
        self._fallback_attempts: dict[str, int] = {name: 0 for name in fallbacks}
        self._fallback_successes: dict[str, int] = {name: 0 for name in fallbacks}
        self._fallback_latencies: dict[str, list[float]] = {name: [] for name in fallbacks}

        # Per-context tracking
        self._context_stats: dict[str, dict[str, Any]] = {}

        # Baseline fallback order
        if baseline_fallback_order is None:
            baseline_fallback_order = sorted(fallbacks.keys())

        self._baseline_fallback_order = baseline_fallback_order

        # Convert string to LearningMode enum
        from .base import LearningMode as LearningModeEnum

        if isinstance(learning_mode, str):
            learning_mode = LearningModeEnum[learning_mode]

        # Initialize adaptive base
        super().__init__(
            learning_mode=learning_mode,
            max_strategies=max_strategies,
            validation_window=validation_window,
        )

        # Set baseline using _get_default_strategy
        self.baseline_strategy = self._get_default_strategy()
        self.strategies[self.baseline_strategy.name] = self.baseline_strategy

    def _get_default_strategy(self) -> LearningStrategy:
        """Get default baseline strategy."""
        return LearningStrategy(
            name="baseline",
            description="Default fallback order",
            context_pattern="",  # Matches all contexts
            parameters={
                "fallback_order": self._baseline_fallback_order,
                "primary_timeout_ms": 5000,
                "fallback_timeout_ms": 10000,
            },
        )

    async def _execute_with_strategy(
        self,
        input_data: Any,
        context: WorkflowContext,
        strategy: LearningStrategy,
    ) -> Any:
        """
        Execute with specific fallback strategy.

        Args:
            input_data: Input data
            context: Workflow context
            strategy: Strategy specifying fallback order

        Returns:
            Result from primary or one of the fallbacks

        Raises:
            Exception: If all options (primary + fallbacks) fail
        """
        start_time = time.time()
        fallback_order = strategy.parameters.get("fallback_order", sorted(self.fallbacks.keys()))

        # Extract context key for tracking
        context_key = context.metadata.get("environment", "default")
        if context_key not in self._context_stats:
            self._context_stats[context_key] = {
                "primary_attempts": 0,
                "primary_failures": 0,
                "fallback_usage": {name: 0 for name in self.fallbacks},
                "fallback_successes": {name: 0 for name in self.fallbacks},
            }

        ctx_stats = self._context_stats[context_key]

        # Try primary first
        self._primary_attempts += 1
        ctx_stats["primary_attempts"] += 1

        try:
            logger.info(
                "adaptive_fallback.primary_attempt",
                primary=self.primary.__class__.__name__,
                strategy=strategy.name,
                context=context_key,
            )

            result = await self.primary.execute(input_data, context)

            # Primary succeeded - no fallback needed
            latency_ms = (time.time() - start_time) * 1000
            logger.info(
                "adaptive_fallback.primary_success",
                latency_ms=latency_ms,
                strategy=strategy.name,
                context=context_key,
            )

            return result

        except Exception as primary_error:
            # Primary failed - track failure
            self._primary_failures += 1
            ctx_stats["primary_failures"] += 1

            logger.warning(
                "adaptive_fallback.primary_failed",
                error=str(primary_error),
                error_type=type(primary_error).__name__,
                strategy=strategy.name,
                context=context_key,
            )

            # Try fallbacks in order
            last_error = primary_error

            for fallback_name in fallback_order:
                if fallback_name not in self.fallbacks:
                    logger.warning(
                        "adaptive_fallback.unknown_fallback",
                        fallback_name=fallback_name,
                        available_fallbacks=list(self.fallbacks.keys()),
                    )
                    continue

                self._fallback_attempts[fallback_name] += 1
                ctx_stats["fallback_usage"][fallback_name] += 1

                try:
                    fallback_start = time.time()
                    fallback = self.fallbacks[fallback_name]

                    logger.info(
                        "adaptive_fallback.trying_fallback",
                        fallback_name=fallback_name,
                        fallback_type=fallback.__class__.__name__,
                        strategy=strategy.name,
                        context=context_key,
                    )

                    result = await fallback.execute(input_data, context)

                    # Fallback succeeded!
                    fallback_latency = (time.time() - fallback_start) * 1000
                    total_latency = (time.time() - start_time) * 1000

                    self._fallback_successes[fallback_name] += 1
                    ctx_stats["fallback_successes"][fallback_name] += 1
                    self._fallback_latencies[fallback_name].append(fallback_latency)

                    logger.info(
                        "adaptive_fallback.fallback_success",
                        fallback_name=fallback_name,
                        fallback_latency_ms=fallback_latency,
                        total_latency_ms=total_latency,
                        strategy=strategy.name,
                        context=context_key,
                    )

                    return result

                except Exception as fallback_error:
                    # This fallback failed, try next
                    logger.warning(
                        "adaptive_fallback.fallback_failed",
                        fallback_name=fallback_name,
                        error=str(fallback_error),
                        error_type=type(fallback_error).__name__,
                        strategy=strategy.name,
                        context=context_key,
                    )
                    last_error = fallback_error
                    continue

            # All fallbacks exhausted
            total_latency = (time.time() - start_time) * 1000
            logger.error(
                "adaptive_fallback.all_failed",
                total_latency_ms=total_latency,
                primary_error=str(primary_error),
                last_fallback_error=str(last_error),
                strategy=strategy.name,
                context=context_key,
            )

            # Re-raise the last error
            raise last_error from None

    async def _consider_new_strategy(
        self,
        input_data: Any,
        context: WorkflowContext,
        current_performance: StrategyMetrics,
    ) -> LearningStrategy | None:
        """
        Consider creating a new fallback strategy based on observed patterns.

        Learning signals:
        - Fallback success rates (which fallbacks work best)
        - Primary failure rate (should we try fallbacks sooner?)
        - Context-specific patterns (different strategies per environment)

        Args:
            input_data: Input data
            context: Workflow context
            current_performance: Current strategy performance

        Returns:
            New strategy if learning suggests improvement, None otherwise
        """
        # Need minimum observations
        if self._primary_attempts < self.min_observations_before_learning:
            return None

        context_key = context.metadata.get("environment", "default")

        # Calculate fallback success rates
        fallback_success_rates = {}
        for name in self.fallbacks:
            attempts = self._fallback_attempts.get(name, 0)
            successes = self._fallback_successes.get(name, 0)
            if attempts > 0:
                fallback_success_rates[name] = successes / attempts
            else:
                fallback_success_rates[name] = 0.0

        # Calculate average latencies
        avg_latencies = {}
        for name in self.fallbacks:
            latencies = self._fallback_latencies.get(name, [])
            if latencies:
                avg_latencies[name] = sum(latencies) / len(latencies)
            else:
                avg_latencies[name] = float("inf")

        # Determine optimal fallback order
        # Sort by: success rate (descending), then latency (ascending)
        scored_fallbacks = []
        for name in self.fallbacks:
            success_rate = fallback_success_rates.get(name, 0.0)
            avg_latency = avg_latencies.get(name, float("inf"))

            # Score: 70% success rate, 30% latency (inverted)
            if avg_latency != float("inf"):
                latency_score = 1.0 / (1.0 + avg_latency / 1000.0)  # Lower latency = higher score
            else:
                latency_score = 0.0

            score = (success_rate * 0.7) + (latency_score * 0.3)
            scored_fallbacks.append((score, name))

        # Sort by score (descending)
        scored_fallbacks.sort(reverse=True, key=lambda x: x[0])
        optimal_order = [name for _, name in scored_fallbacks]

        # Check if this is different from current strategy
        # Get current strategy fallback order
        context_key = context.metadata.get("environment", "default")
        current_strategy = self._select_strategy(context_key)
        current_order = current_strategy.parameters.get("fallback_order", [])
        if optimal_order == current_order:
            return None

        # Calculate improvement
        # Current strategy success rate
        current_success_rate = current_performance.success_rate

        # Estimated new success rate (weighted by fallback positions)
        estimated_success_rate = 0.0
        weight_sum = 0.0
        for i, name in enumerate(optimal_order):
            position_weight = 1.0 / (i + 1)  # First fallback has more weight
            estimated_success_rate += fallback_success_rates.get(name, 0.0) * position_weight
            weight_sum += position_weight

        if weight_sum > 0:
            estimated_success_rate /= weight_sum

        # Require 5% improvement to create new strategy
        improvement = estimated_success_rate - current_success_rate
        if improvement < 0.05:
            return None

        # Create new strategy
        strategy_name = f"{context_key}_optimized_v{len(self.strategies) + 1}"

        logger.info(
            "adaptive_fallback.new_strategy",
            strategy_name=strategy_name,
            optimal_order=optimal_order,
            current_success_rate=current_success_rate,
            estimated_success_rate=estimated_success_rate,
            improvement=improvement,
            context=context_key,
        )

        new_strategy = LearningStrategy(
            name=strategy_name,
            description=f"Learned fallback order for {context_key} context based on {self._primary_attempts} observations",
            context_pattern=context_key,
            parameters={
                "fallback_order": optimal_order,
                "primary_timeout_ms": 5000,  # Use default
                "fallback_timeout_ms": 10000,  # Use default
            },
        )

        # Persist to Logseq if enabled
        if self.enable_auto_persistence and self.logseq_integration:
            try:
                await self.logseq_integration.save_learned_strategy(
                    strategy=new_strategy,
                    primitive_type="AdaptiveFallbackPrimitive",
                    context=context_key,
                    notes=f"Fallback success rates: {fallback_success_rates}\nOptimal order: {optimal_order}",
                )
            except Exception as e:
                logger.warning(
                    "adaptive_fallback.persistence_failed",
                    error=str(e),
                    strategy_name=strategy_name,
                )

        return new_strategy

    def get_fallback_stats(self) -> dict[str, Any]:
        """
        Get comprehensive fallback statistics.

        Returns:
            Dictionary with fallback usage statistics including:
            - primary_attempts: Number of primary executions
            - primary_failures: Number of primary failures
            - primary_failure_rate: Percentage of primary failures
            - fallbacks: Per-fallback statistics (attempts, successes, success_rate, avg_latency)
            - contexts: Per-context statistics
            - strategies: Active strategies with their fallback orders
            - best_fallback_order: Current optimal fallback order
        """
        # Calculate fallback stats
        fallback_stats = {}
        for name in self.fallbacks:
            attempts = self._fallback_attempts.get(name, 0)
            successes = self._fallback_successes.get(name, 0)
            latencies = self._fallback_latencies.get(name, [])

            fallback_stats[name] = {
                "attempts": attempts,
                "successes": successes,
                "success_rate": successes / attempts if attempts > 0 else 0.0,
                "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
            }

        # Get current best fallback order
        scored_fallbacks = []
        for name, stats in fallback_stats.items():
            success_rate = stats["success_rate"]
            avg_latency = stats["avg_latency_ms"]

            # Score: 70% success rate, 30% latency (inverted)
            if avg_latency > 0:
                latency_score = 1.0 / (1.0 + avg_latency / 1000.0)
            else:
                latency_score = 1.0

            score = (success_rate * 0.7) + (latency_score * 0.3)
            scored_fallbacks.append((score, name))

        scored_fallbacks.sort(reverse=True, key=lambda x: x[0])
        best_order = [name for _, name in scored_fallbacks]

        return {
            "primary_attempts": self._primary_attempts,
            "primary_failures": self._primary_failures,
            "primary_failure_rate": self._primary_failures / self._primary_attempts
            if self._primary_attempts > 0
            else 0.0,
            "fallbacks": fallback_stats,
            "contexts": self._context_stats,
            "strategies": {
                name: {
                    "fallback_order": strategy.parameters.get("fallback_order", []),
                    "success_rate": strategy.metrics.success_rate,
                    "avg_latency_ms": strategy.metrics.avg_latency * 1000,
                }
                for name, strategy in self.strategies.items()
            },
            "best_fallback_order": best_order,
        }
