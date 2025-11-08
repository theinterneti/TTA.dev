"""Adaptive timeout primitive that learns optimal timeout values from latency patterns."""

from __future__ import annotations

import asyncio
import builtins
import time
from typing import Any

from ..core.base import WorkflowContext
from ..observability.instrumented_primitive import InstrumentedPrimitive
from ..observability.logging import get_logger
from .base import AdaptivePrimitive, LearningMode, LearningStrategy, StrategyMetrics

logger = get_logger(__name__)


class TimeoutError(Exception):
    """Timeout exceeded during execution."""

    pass


class AdaptiveTimeoutPrimitive(AdaptivePrimitive[Any, Any]):
    """
    Adaptive timeout primitive that learns optimal timeout values from execution patterns.

    Learns from:
    - Latency percentiles (p50, p95, p99)
    - Success/failure patterns
    - Context-specific execution times
    - Timeout occurrences

    Parameters learned:
    - timeout_ms: Optimal timeout value
    - buffer_factor: Multiplier for percentile (e.g., 1.5x p95)
    - percentile_target: Which percentile to target (50, 95, 99)

    Example:
        ```python
        from tta_dev_primitives.adaptive import (
            AdaptiveTimeoutPrimitive,
            LearningMode
        )

        # Create adaptive timeout that learns optimal values
        adaptive_timeout = AdaptiveTimeoutPrimitive(
            target_primitive=slow_api_call,
            learning_mode=LearningMode.ACTIVE,
            min_observations_before_learning=20
        )

        # Execute - learns from latency patterns
        result = await adaptive_timeout.execute(data, context)

        # Check learned timeouts
        stats = adaptive_timeout.get_timeout_stats()
        print(f"Learned timeout: {stats['current_timeout_ms']}ms")
        print(f"P95 latency: {stats['p95_latency_ms']}ms")
        ```

    Scoring formula:
    - 60% success rate (minimize timeouts)
    - 40% headroom (balance between tight and loose timeouts)
    """

    def __init__(
        self,
        target_primitive: InstrumentedPrimitive[Any, Any],
        baseline_timeout_ms: float = 5000.0,
        baseline_percentile_target: int = 95,
        baseline_buffer_factor: float = 1.5,
        learning_mode: LearningMode = LearningMode.OBSERVE,
        min_observations_before_learning: int = 20,
        max_strategies: int = 5,
        validation_window: int = 10,
        enable_circuit_breaker: bool = True,
        circuit_breaker_threshold: float = 0.5,
        circuit_breaker_duration: float = 300.0,
    ) -> None:
        """
        Initialize adaptive timeout primitive.

        Args:
            target_primitive: Primitive to wrap with adaptive timeout
            baseline_timeout_ms: Initial timeout in milliseconds
            baseline_percentile_target: Which percentile to target (50, 95, 99)
            baseline_buffer_factor: Multiplier for percentile (e.g., 1.5x p95)
            learning_mode: Learning mode (DISABLED, OBSERVE, VALIDATE, ACTIVE)
            min_observations_before_learning: Minimum executions before creating strategies
            max_strategies: Maximum number of strategies to maintain
            validation_window: Number of executions to validate new strategies
            enable_circuit_breaker: Enable circuit breaker on high failure rate
            circuit_breaker_threshold: Failure rate to trigger circuit breaker
            circuit_breaker_duration: How long to disable learning (seconds)
        """
        # Store baseline parameters
        self._baseline_timeout_ms = baseline_timeout_ms
        self._baseline_percentile_target = baseline_percentile_target
        self._baseline_buffer_factor = baseline_buffer_factor
        self._min_observations_before_learning = min_observations_before_learning

        # Initialize base adaptive primitive (no baseline_strategy parameter)
        super().__init__(
            learning_mode=learning_mode,
            max_strategies=max_strategies,
            validation_window=validation_window,
            circuit_breaker_threshold=circuit_breaker_threshold,
        )

        self.target_primitive = target_primitive

        # Timeout tracking
        self._timeout_count = 0
        self._success_count = 0
        self._latency_samples: list[float] = []  # All latencies in ms
        self._context_latencies: dict[str, list[float]] = {}  # Per-context latencies

        # Initialize baseline strategy using _get_default_strategy
        self.baseline_strategy = self._get_default_strategy()
        self.strategies[self.baseline_strategy.name] = self.baseline_strategy

    def _get_default_strategy(self) -> LearningStrategy:
        """
        Get the default baseline timeout strategy.

        Returns:
            Baseline strategy with conservative timeout settings
        """
        return LearningStrategy(
            name="baseline_conservative",
            description=f"Conservative timeout with {self._baseline_timeout_ms}ms at p{self._baseline_percentile_target}",
            parameters={
                "timeout_ms": self._baseline_timeout_ms,
                "percentile_target": self._baseline_percentile_target,
                "buffer_factor": self._baseline_buffer_factor,
            },
            context_pattern="*",
        )

    async def _execute_with_strategy(
        self,
        input_data: Any,
        context: WorkflowContext,
        strategy: LearningStrategy,
    ) -> Any:
        """
        Execute with specific timeout strategy.

        Args:
            input_data: Input data
            context: Workflow context
            strategy: Strategy specifying timeout parameters

        Returns:
            Result from target primitive

        Raises:
            TimeoutError: If execution exceeds timeout
        """
        start_time = time.time()
        timeout_ms = strategy.parameters.get("timeout_ms", 5000.0)
        timeout_seconds = timeout_ms / 1000.0

        # Extract context key for tracking
        context_key = context.metadata.get("environment", "default")
        if context_key not in self._context_latencies:
            self._context_latencies[context_key] = []

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self.target_primitive.execute(input_data, context),
                timeout=timeout_seconds,
            )

            # Record successful execution
            execution_time_ms = (time.time() - start_time) * 1000
            self._latency_samples.append(execution_time_ms)
            self._context_latencies[context_key].append(execution_time_ms)
            self._success_count += 1

            logger.info(
                "adaptive_timeout.success",
                context=context_key,
                latency_ms=execution_time_ms,
                timeout_ms=timeout_ms,
                strategy=strategy.name,
                headroom_pct=(1 - execution_time_ms / timeout_ms) * 100,
            )

            return result

        except builtins.TimeoutError as e:
            # Record timeout
            self._timeout_count += 1
            execution_time_ms = (time.time() - start_time) * 1000

            logger.warning(
                "adaptive_timeout.timeout_exceeded",
                context=context_key,
                timeout_ms=timeout_ms,
                actual_ms=execution_time_ms,
                strategy=strategy.name,
                error=str(e),
                error_type=type(e).__name__,
            )

            # Re-raise as our TimeoutError
            raise TimeoutError(
                f"Execution exceeded timeout of {timeout_ms}ms (actual: {execution_time_ms:.1f}ms)"
            ) from None

    async def _consider_new_strategy(
        self,
        input_data: Any,
        context: WorkflowContext,
        current_performance: StrategyMetrics,
    ) -> LearningStrategy | None:
        """
        Consider creating a new timeout strategy based on latency patterns.

        Args:
            input_data: Input data
            context: Workflow context
            current_performance: Current strategy performance

        Returns:
            New strategy if beneficial, None otherwise
        """
        context_key = context.metadata.get("environment", "default")

        # Need sufficient data
        if len(self._latency_samples) < self._min_observations_before_learning:
            return None

        # Get context-specific latencies if available
        context_latencies = self._context_latencies.get(context_key, [])
        if len(context_latencies) < 5:
            # Not enough context-specific data, use global
            latencies = self._latency_samples
        else:
            latencies = context_latencies

        # Calculate percentiles
        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)

        p50_idx = int(n * 0.50)
        p95_idx = int(n * 0.95)
        p99_idx = int(n * 0.99)

        sorted_latencies[p50_idx] if p50_idx < n else sorted_latencies[-1]
        p95 = sorted_latencies[p95_idx] if p95_idx < n else sorted_latencies[-1]
        p99 = sorted_latencies[p99_idx] if p99_idx < n else sorted_latencies[-1]

        # Determine optimal percentile target
        # If we have many timeouts, use higher percentile
        timeout_rate = self._timeout_count / (self._timeout_count + self._success_count)

        if timeout_rate > 0.1:  # >10% timeouts
            target_percentile = 99
            target_latency = p99
            buffer_factor = 2.0  # More generous
        elif timeout_rate > 0.05:  # >5% timeouts
            target_percentile = 95
            target_latency = p95
            buffer_factor = 1.5
        else:  # Low timeout rate
            target_percentile = 95
            target_latency = p95
            buffer_factor = 1.2  # Tighter timeout

        # Calculate new timeout
        new_timeout_ms = target_latency * buffer_factor

        # Only create new strategy if significantly different
        current_strategy = self._select_strategy(context_key)
        current_timeout = current_strategy.parameters.get("timeout_ms", 5000.0)
        improvement_threshold = 0.15  # 15% difference

        if abs(new_timeout_ms - current_timeout) / current_timeout < improvement_threshold:
            return None

        # Create new strategy
        strategy_name = f"{context_key}_p{target_percentile}_v{len(self.strategies) + 1}"
        description = (
            f"Learned from {len(latencies)} executions: "
            f"p{target_percentile}={target_latency:.1f}ms, "
            f"buffer={buffer_factor}x, "
            f"timeout_rate={timeout_rate:.1%}"
        )

        return LearningStrategy(
            name=strategy_name,
            description=description,
            parameters={
                "timeout_ms": new_timeout_ms,
                "percentile_target": target_percentile,
                "buffer_factor": buffer_factor,
            },
            context_pattern=context_key,
        )

    def get_timeout_stats(self) -> dict[str, Any]:
        """
        Get comprehensive timeout statistics.

        Returns:
            Dictionary with timeout statistics including:
            - total_executions: Total number of executions
            - timeout_count: Number of timeouts
            - success_count: Number of successful executions
            - timeout_rate: Percentage of timeouts
            - latencies: Latency percentiles (p50, p95, p99)
            - contexts: Per-context statistics
            - strategies: Active strategies with their timeouts
            - current_timeout_ms: Currently used timeout
        """
        # Calculate latency percentiles
        if self._latency_samples:
            sorted_latencies = sorted(self._latency_samples)
            n = len(sorted_latencies)

            p50_idx = int(n * 0.50)
            p95_idx = int(n * 0.95)
            p99_idx = int(n * 0.99)

            p50 = sorted_latencies[p50_idx] if p50_idx < n else sorted_latencies[-1]
            p95 = sorted_latencies[p95_idx] if p95_idx < n else sorted_latencies[-1]
            p99 = sorted_latencies[p99_idx] if p99_idx < n else sorted_latencies[-1]

            avg_latency = sum(sorted_latencies) / len(sorted_latencies)
            min_latency = sorted_latencies[0]
            max_latency = sorted_latencies[-1]
        else:
            p50 = p95 = p99 = avg_latency = min_latency = max_latency = 0.0

        # Per-context statistics
        context_stats = {}
        for context_key, latencies in self._context_latencies.items():
            if latencies:
                sorted_ctx = sorted(latencies)
                n_ctx = len(sorted_ctx)

                p95_idx = int(n_ctx * 0.95)

                context_stats[context_key] = {
                    "executions": len(latencies),
                    "avg_latency_ms": sum(latencies) / len(latencies),
                    "p95_latency_ms": sorted_ctx[p95_idx] if p95_idx < n_ctx else sorted_ctx[-1],
                    "min_latency_ms": sorted_ctx[0],
                    "max_latency_ms": sorted_ctx[-1],
                }

        # Get current timeout from baseline or active strategy
        baseline = self.strategies.get("baseline_conservative", self.baseline_strategy)
        current_timeout = baseline.parameters.get("timeout_ms", 5000.0) if baseline else 5000.0

        total_executions = self._timeout_count + self._success_count

        return {
            "total_executions": total_executions,
            "timeout_count": self._timeout_count,
            "success_count": self._success_count,
            "timeout_rate": self._timeout_count / total_executions if total_executions > 0 else 0.0,
            "latencies": {
                "p50_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99,
                "avg_ms": avg_latency,
                "min_ms": min_latency,
                "max_ms": max_latency,
            },
            "contexts": context_stats,
            "strategies": {
                name: {
                    "timeout_ms": strategy.parameters.get("timeout_ms", 0.0),
                    "percentile_target": strategy.parameters.get("percentile_target", 95),
                    "buffer_factor": strategy.parameters.get("buffer_factor", 1.5),
                    "success_rate": strategy.metrics.success_rate,
                    "avg_latency_ms": strategy.metrics.avg_latency * 1000,
                }
                for name, strategy in self.strategies.items()
            },
            "current_timeout_ms": current_timeout,
        }
