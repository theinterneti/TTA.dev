"""Adaptive Retry Primitive that learns optimal retry strategies from observability data.

This primitive demonstrates the self-improving pattern by:
1. Learning which retry strategies work best for different error types
2. Adapting backoff strategies based on actual success patterns
3. Using observability data (traces, metrics) as learning input
4. Maintaining safety with circuit breakers and validation

The key insight: Instead of static retry logic, this primitive learns from
real execution patterns to optimize retry behavior over time.

# See: [[TTA.dev/Primitives/AdaptiveRetryPrimitive]]
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass
from typing import Any

from tta_dev_primitives.core.base import WorkflowContext

from .base import AdaptivePrimitive, LearningMode, LearningStrategy

logger = logging.getLogger(__name__)


@dataclass
class RetryStrategyParams:
    """Parameters for retry strategies that can be learned and adapted."""

    max_retries: int = 3
    initial_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0
    jitter: bool = True
    jitter_factor: float = 0.1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for strategy storage."""
        return {
            "max_retries": self.max_retries,
            "initial_delay": self.initial_delay,
            "backoff_factor": self.backoff_factor,
            "max_delay": self.max_delay,
            "jitter": self.jitter,
            "jitter_factor": self.jitter_factor,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RetryStrategyParams:
        """Create from dictionary."""
        return cls(**data)


class AdaptiveRetryPrimitive(AdaptivePrimitive[dict[str, Any], dict[str, Any]]):
    """Retry primitive that learns optimal retry strategies from execution patterns.

    This primitive demonstrates self-improvement by:
    - Learning which retry parameters work best for different error types
    - Adapting strategies based on observability data (success rates, latencies)
    - Using context awareness to apply different strategies in different environments
    - Maintaining safety with circuit breakers and strategy validation

    Key Learning Inputs from Observability:
    - Error types and frequencies from spans/logs
    - Success/failure patterns by retry count
    - Latency distributions for different backoff strategies
    - Resource usage patterns during retries
    - Context patterns (environment, priority, error types)
    """

    def __init__(
        self,
        target_primitive: Any,
        learning_mode: LearningMode = LearningMode.VALIDATE,
        max_strategies: int = 8,
        logseq_integration: Any | None = None,
        enable_auto_persistence: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(learning_mode=learning_mode, max_strategies=max_strategies, **kwargs)

        self.target_primitive = target_primitive
        self.logseq_integration = logseq_integration
        self.enable_auto_persistence = enable_auto_persistence

        # Initialize with baseline strategy
        self.baseline_strategy = self._create_baseline_strategy()
        self.strategies[self.baseline_strategy.name] = self.baseline_strategy

        logger.info(
            f"Initialized AdaptiveRetryPrimitive with target={type(target_primitive).__name__}, "
            f"logseq_enabled={logseq_integration is not None}, "
            f"auto_persist={enable_auto_persistence}"
        )

    async def _execute_with_strategy(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext,
        strategy: LearningStrategy,
    ) -> dict[str, Any]:
        """Execute the target primitive with retry using the selected strategy."""

        # Extract retry parameters from strategy
        retry_params = RetryStrategyParams.from_dict(strategy.parameters)

        # Execute with optional tracing
        if self._tracer:
            with self._tracer.start_as_current_span("adaptive_retry_execution") as span:
                return await self._execute_retry_with_tracing(
                    input_data, context, strategy, retry_params, span
                )
        else:
            return await self._execute_retry_with_tracing(
                input_data, context, strategy, retry_params, None
            )

    async def _execute_retry_with_tracing(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext,
        strategy: LearningStrategy,
        retry_params: RetryStrategyParams,
        span: Any | None,
    ) -> dict[str, Any]:
        """Execute retry logic with optional tracing."""

        if span:
            span.set_attribute("retry.strategy_name", strategy.name)
            span.set_attribute("retry.max_retries", retry_params.max_retries)
            span.set_attribute("retry.initial_delay", retry_params.initial_delay)
            span.set_attribute("retry.backoff_factor", retry_params.backoff_factor)

        attempts = 0
        last_exception = None

        for attempt in range(retry_params.max_retries + 1):
            attempts += 1
            if span:
                span.set_attribute("retry.current_attempt", attempts)

            try:
                # Execute the target primitive
                result = await self.target_primitive.execute(input_data, context)

                # Success! Record metrics and return
                if span:
                    span.set_attribute("retry.final_attempts", attempts)
                    span.set_attribute("retry.success", True)

                return {
                    "result": result,
                    "attempts": attempts,
                    "strategy_used": strategy.name,
                    "success": True,
                }

            except Exception as e:
                last_exception = e
                if span:
                    span.add_event(
                        "retry_attempt_failed",
                        {
                            "attempt": attempts,
                            "error_type": type(e).__name__,
                            "error_message": str(e)[:200],  # Truncate long messages
                        },
                    )

                # Don't sleep after the last attempt
                if attempt < retry_params.max_retries:
                    # Calculate delay with backoff and optional jitter
                    delay = retry_params.initial_delay * (retry_params.backoff_factor**attempt)
                    delay = min(delay, retry_params.max_delay)

                    if retry_params.jitter:
                        jitter = delay * retry_params.jitter_factor * (2 * random.random() - 1)
                        delay = max(0, delay + jitter)

                    if span:
                        span.set_attribute(f"retry.delay_attempt_{attempt + 1}", delay)
                    await asyncio.sleep(delay)

        # All retries exhausted
        if span:
            span.set_attribute("retry.final_attempts", attempts)
            span.set_attribute("retry.success", False)
            span.set_attribute("retry.final_error", str(last_exception)[:200])

        return {
            "result": None,
            "attempts": attempts,
            "strategy_used": strategy.name,
            "success": False,
            "error": str(last_exception),
            "error_type": type(last_exception).__name__,
        }

    def _get_default_strategy(self) -> LearningStrategy:
        """Get the default retry strategy."""
        return self._create_baseline_strategy()

    def _create_baseline_strategy(self) -> LearningStrategy:
        """Create the baseline retry strategy."""
        return LearningStrategy(
            name="baseline_exponential",
            description="Conservative exponential backoff with jitter",
            parameters=RetryStrategyParams(
                max_retries=3,
                initial_delay=1.0,
                backoff_factor=2.0,
                max_delay=60.0,
                jitter=True,
                jitter_factor=0.1,
            ).to_dict(),
            context_pattern="",  # Matches all contexts
        )

    def _context_extractor(self, input_data: dict[str, Any], context: WorkflowContext) -> str:
        """Extract context key for retry strategy selection."""
        # Build context key from:
        # - Environment (prod vs dev vs test)
        # - Priority level
        # - Expected error patterns
        # - Time sensitivity

        environment = context.metadata.get("environment", "unknown")
        priority = context.metadata.get("priority", "normal")
        time_sensitive = context.metadata.get("time_sensitive", False)

        # Look for hints about expected error types in input
        error_hints = []
        if "timeout" in str(input_data).lower():
            error_hints.append("timeout")
        if "rate_limit" in str(input_data).lower():
            error_hints.append("rate_limit")
        if "network" in str(input_data).lower():
            error_hints.append("network")

        error_context = "_".join(error_hints) if error_hints else "general"

        return f"env:{environment}|priority:{priority}|time_sensitive:{time_sensitive}|errors:{error_context}"

    async def _learn_from_execution(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext,
        strategy: LearningStrategy,
        result: dict[str, Any],
        execution_time: float,
    ) -> None:
        """Learn from retry execution patterns and observability data."""

        if self.learning_mode == LearningMode.OBSERVE:
            return  # Just observe, don't adapt

        success = result.get("success", False)
        attempts = result.get("attempts", 1)
        error_type = result.get("error_type", "unknown")

        # Analyze patterns for potential strategy improvements
        context_key = self._context_extractor(input_data, context)

        # Use tracer if available for learning observability
        span = None
        if self._tracer:
            span = self._tracer.start_span("retry_learning")
            span.__enter__()
            span.set_attribute("learning.context_key", context_key)
            span.set_attribute("learning.success", success)
            span.set_attribute("learning.attempts", attempts)
            span.set_attribute("learning.error_type", error_type)

            # Learning opportunities based on execution patterns:

            # 1. If we succeeded on first try repeatedly, maybe we can reduce max_retries
            if success and attempts == 1 and strategy.metrics.success_rate > 0.9:
                await self._consider_reducing_retries(context_key, strategy, context)

            # 2. If we're consistently failing after max retries, maybe increase them
            elif not success and strategy.metrics.failure_rate > 0.3:
                await self._consider_increasing_retries(context_key, strategy, error_type, context)

            # 3. If we see specific error patterns, create specialized strategies
            if error_type in ["TimeoutError", "ConnectionError", "HTTPException"]:
                await self._consider_error_specific_strategy(
                    context_key, error_type, success, attempts, context
                )

            # 4. If execution time is consistently high, maybe adjust delays
            if execution_time > 30.0:  # More than 30 seconds total
                await self._consider_faster_backoff(context_key, strategy, context)

            span.set_attribute("learning.strategies_considered", len(self.strategies))

    async def _consider_reducing_retries(
        self, context_key: str, strategy: LearningStrategy, context: WorkflowContext
    ) -> None:
        """Consider creating a strategy with fewer retries for high-success contexts."""

        strategy_name = f"low_retry_{hash(context_key) % 1000}"

        if strategy_name not in self.strategies and len(self.strategies) < self.max_strategies:
            # Create strategy with reduced retries for fast-succeeding contexts
            new_params = RetryStrategyParams.from_dict(strategy.parameters.copy())
            new_params.max_retries = max(1, new_params.max_retries - 1)
            new_params.initial_delay = min(0.5, new_params.initial_delay)  # Faster initial delay

            new_strategy = LearningStrategy(
                name=strategy_name,
                description=f"Reduced retries for reliable context: {context_key[:50]}",
                parameters=new_params.to_dict(),
                context_pattern=context_key.split("|")[0],  # Match on environment pattern
            )

            self.strategies[strategy_name] = new_strategy
            self.total_adaptations += 1

            logger.info(f"Created low-retry strategy: {strategy_name}")

            # Auto-persist to Logseq if enabled
            if self.enable_auto_persistence and self.logseq_integration:
                await self._persist_strategy_to_logseq(new_strategy, context)

    async def _consider_increasing_retries(
        self,
        context_key: str,
        strategy: LearningStrategy,
        error_type: str,
        context: WorkflowContext,
    ) -> None:
        """Consider creating a strategy with more retries for failure-prone contexts."""

        strategy_name = f"high_retry_{error_type.lower()}_{hash(context_key) % 1000}"

        if strategy_name not in self.strategies and len(self.strategies) < self.max_strategies:
            # Create strategy with more retries and longer delays for problematic contexts
            new_params = RetryStrategyParams.from_dict(strategy.parameters.copy())
            new_params.max_retries = min(8, new_params.max_retries + 2)  # Add more retries
            new_params.backoff_factor = max(1.5, new_params.backoff_factor * 0.8)  # Gentler backoff
            new_params.max_delay = min(120.0, new_params.max_delay * 1.5)  # Allow longer delays

            new_strategy = LearningStrategy(
                name=strategy_name,
                description=f"Increased retries for {error_type} in context: {context_key[:50]}",
                parameters=new_params.to_dict(),
                context_pattern=f"errors:{error_type.lower()}",
            )

            self.strategies[strategy_name] = new_strategy
            self.total_adaptations += 1

            logger.info(f"Created high-retry strategy: {strategy_name}")

            # Auto-persist to Logseq if enabled
            if self.enable_auto_persistence and self.logseq_integration:
                await self._persist_strategy_to_logseq(new_strategy, context)

    async def _consider_error_specific_strategy(
        self,
        context_key: str,
        error_type: str,
        success: bool,
        attempts: int,
        context: WorkflowContext,
    ) -> None:
        """Consider creating error-type-specific strategies."""

        strategy_name = f"error_specific_{error_type.lower()}_{hash(context_key) % 1000}"

        if strategy_name not in self.strategies and len(self.strategies) < self.max_strategies:
            # Create error-specific strategy based on known patterns
            params = RetryStrategyParams()

            if error_type == "TimeoutError":
                # For timeouts, use longer delays and fewer retries
                params.max_retries = 2
                params.initial_delay = 2.0
                params.backoff_factor = 3.0
                params.jitter_factor = 0.2  # More jitter for timeout scenarios

            elif error_type == "ConnectionError":
                # For connection errors, use more retries with moderate delays
                params.max_retries = 5
                params.initial_delay = 0.5
                params.backoff_factor = 1.8
                params.max_delay = 30.0

            elif error_type in ["HTTPException", "RequestException"]:
                # For HTTP errors, use quick retries initially
                params.max_retries = 4
                params.initial_delay = 0.2
                params.backoff_factor = 2.5
                params.max_delay = 45.0

            new_strategy = LearningStrategy(
                name=strategy_name,
                description=f"Specialized strategy for {error_type} errors",
                parameters=params.to_dict(),
                context_pattern=f"errors:{error_type.lower()}",
            )

            self.strategies[strategy_name] = new_strategy
            self.total_adaptations += 1

            logger.info(f"Created error-specific strategy: {strategy_name}")

            # Auto-persist to Logseq if enabled
            if self.enable_auto_persistence and self.logseq_integration:
                await self._persist_strategy_to_logseq(new_strategy, context)

    async def _consider_faster_backoff(
        self, context_key: str, strategy: LearningStrategy, context: WorkflowContext
    ) -> None:
        """Consider creating a faster backoff strategy for time-sensitive contexts."""

        strategy_name = f"fast_backoff_{hash(context_key) % 1000}"

        if strategy_name not in self.strategies and len(self.strategies) < self.max_strategies:
            # Create strategy with faster backoff for time-sensitive scenarios
            new_params = RetryStrategyParams.from_dict(strategy.parameters.copy())
            new_params.initial_delay = max(0.1, new_params.initial_delay * 0.5)
            new_params.backoff_factor = max(1.2, new_params.backoff_factor * 0.7)
            new_params.max_delay = min(20.0, new_params.max_delay * 0.6)
            new_params.jitter_factor = 0.05  # Less jitter for predictable timing

            new_strategy = LearningStrategy(
                name=strategy_name,
                description=f"Fast backoff for time-sensitive context: {context_key[:50]}",
                parameters=new_params.to_dict(),
                context_pattern="time_sensitive:true",
            )

            self.strategies[strategy_name] = new_strategy
            self.total_adaptations += 1

            logger.info(f"Created fast-backoff strategy: {strategy_name}")

            # Auto-persist to Logseq if enabled
            if self.enable_auto_persistence and self.logseq_integration:
                await self._persist_strategy_to_logseq(new_strategy, context)

    async def _persist_strategy_to_logseq(
        self, strategy: LearningStrategy, context: WorkflowContext
    ) -> None:
        """Persist learned strategy to Logseq knowledge base."""
        if not self.logseq_integration:
            return

        try:
            await self.logseq_integration.save_learned_strategy(
                strategy=strategy,
                primitive_type="AdaptiveRetryPrimitive",
                context=context,
                performance_data={
                    "latency_percentiles": {},  # Could be populated from metrics
                    "error_breakdown": {},  # Could be populated from execution history
                },
            )
            logger.info(f"Persisted strategy '{strategy.name}' to Logseq")
        except Exception as e:
            logger.warning(f"Failed to persist strategy to Logseq: {e}")


# Export the adaptive retry primitive
__all__ = ["AdaptiveRetryPrimitive", "RetryStrategyParams"]
