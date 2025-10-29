"""Sampling strategies for distributed tracing and metrics."""

from __future__ import annotations

import hashlib
import logging
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SamplingDecision(Enum):
    """Sampling decision for a trace."""

    SAMPLE = "sample"
    DROP = "drop"


@dataclass
class SamplingResult:
    """Result of a sampling decision."""

    decision: SamplingDecision
    reason: str
    sampler_name: str
    sample_rate: float | None = None


class SamplingConfig(BaseModel):
    """
    Configuration for observability sampling strategies.

    This configuration controls how traces and metrics are sampled
    to balance observability with performance and cost.

    Example:
        ```python
        config = SamplingConfig(
            default_rate=0.1,  # Sample 10% of traces
            always_sample_errors=True,
            always_sample_slow=True,
            slow_threshold_ms=1000.0,
            adaptive_enabled=True,
            adaptive_min_rate=0.01,
            adaptive_max_rate=1.0,
            adaptive_target_overhead=0.02,
        )
        ```
    """

    # Probabilistic sampling
    default_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Default sampling rate (0.0-1.0). 0.1 means 10% of traces sampled.",
    )

    # Tail-based sampling
    always_sample_errors: bool = Field(
        default=True, description="Always sample traces with errors"
    )
    always_sample_slow: bool = Field(
        default=True, description="Always sample slow traces"
    )
    slow_threshold_ms: float = Field(
        default=1000.0, ge=0.0, description="Threshold for slow traces in milliseconds"
    )

    # Adaptive sampling
    adaptive_enabled: bool = Field(default=False, description="Enable adaptive sampling")
    adaptive_min_rate: float = Field(
        default=0.01, ge=0.0, le=1.0, description="Minimum sampling rate for adaptive sampling"
    )
    adaptive_max_rate: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Maximum sampling rate for adaptive sampling"
    )
    adaptive_target_overhead: float = Field(
        default=0.02, ge=0.0, le=1.0, description="Target overhead percentage (e.g., 0.02 = 2%)"
    )

    class Config:
        arbitrary_types_allowed = True


class ProbabilisticSampler:
    """
    Probabilistic sampler with consistent trace-based decisions.

    Uses deterministic hashing of trace_id to ensure consistent sampling
    decisions across distributed services.

    Example:
        ```python
        sampler = ProbabilisticSampler(sample_rate=0.1)

        # Same trace_id always gets same decision
        result1 = sampler.should_sample("trace-123")
        result2 = sampler.should_sample("trace-123")
        assert result1.decision == result2.decision
        ```
    """

    def __init__(self, sample_rate: float = 0.1):
        """
        Initialize probabilistic sampler.

        Args:
            sample_rate: Probability of sampling (0.0-1.0)
        """
        if not 0.0 <= sample_rate <= 1.0:
            raise ValueError(f"Sample rate must be between 0.0 and 1.0, got {sample_rate}")
        self.sample_rate = sample_rate

    def should_sample(self, trace_id: str | None, **kwargs: Any) -> SamplingResult:
        """
        Determine if a trace should be sampled.

        Uses consistent hashing to ensure same trace_id always gets
        same sampling decision.

        Args:
            trace_id: Trace identifier (e.g., correlation_id, workflow_id)
            **kwargs: Additional context (unused but accepted for interface compatibility)

        Returns:
            Sampling result with decision and metadata
        """
        if self.sample_rate == 0.0:
            return SamplingResult(
                decision=SamplingDecision.DROP,
                reason="sampling_rate_zero",
                sampler_name="probabilistic",
                sample_rate=0.0,
            )

        if self.sample_rate == 1.0:
            return SamplingResult(
                decision=SamplingDecision.SAMPLE,
                reason="sampling_rate_one",
                sampler_name="probabilistic",
                sample_rate=1.0,
            )

        # Use consistent hashing for deterministic sampling
        if trace_id:
            # Hash trace_id to get consistent random value [0, 1)
            hash_value = int(hashlib.md5(trace_id.encode()).hexdigest()[:8], 16)
            sample_value = hash_value / 0xFFFFFFFF
        else:
            # No trace_id, use random sampling
            sample_value = random.random()

        decision = (
            SamplingDecision.SAMPLE if sample_value < self.sample_rate else SamplingDecision.DROP
        )

        return SamplingResult(
            decision=decision,
            reason="probabilistic_hash" if trace_id else "probabilistic_random",
            sampler_name="probabilistic",
            sample_rate=self.sample_rate,
        )


class TailBasedSampler:
    """
    Tail-based sampler that always samples errors and slow traces.

    This sampler makes decisions after trace completion based on
    actual execution characteristics.

    Example:
        ```python
        sampler = TailBasedSampler(
            always_sample_errors=True,
            always_sample_slow=True,
            slow_threshold_ms=1000.0
        )

        # Always samples if error present
        result = sampler.should_sample_after_completion(
            has_error=True,
            duration_ms=500.0
        )
        assert result.decision == SamplingDecision.SAMPLE

        # Always samples if slow
        result = sampler.should_sample_after_completion(
            has_error=False,
            duration_ms=1500.0
        )
        assert result.decision == SamplingDecision.SAMPLE
        ```
    """

    def __init__(
        self,
        always_sample_errors: bool = True,
        always_sample_slow: bool = True,
        slow_threshold_ms: float = 1000.0,
    ):
        """
        Initialize tail-based sampler.

        Args:
            always_sample_errors: Always sample traces with errors
            always_sample_slow: Always sample slow traces
            slow_threshold_ms: Threshold for slow traces in milliseconds
        """
        self.always_sample_errors = always_sample_errors
        self.always_sample_slow = always_sample_slow
        self.slow_threshold_ms = slow_threshold_ms

    def should_sample_after_completion(
        self,
        has_error: bool,
        duration_ms: float,
        **kwargs: Any,
    ) -> SamplingResult:
        """
        Determine if a trace should be sampled after completion.

        Args:
            has_error: Whether the trace has any errors
            duration_ms: Total trace duration in milliseconds
            **kwargs: Additional context (unused but accepted for interface compatibility)

        Returns:
            Sampling result with decision and metadata
        """
        # Always sample errors
        if self.always_sample_errors and has_error:
            return SamplingResult(
                decision=SamplingDecision.SAMPLE,
                reason="tail_error",
                sampler_name="tail_based",
            )

        # Always sample slow traces
        if self.always_sample_slow and duration_ms >= self.slow_threshold_ms:
            return SamplingResult(
                decision=SamplingDecision.SAMPLE,
                reason="tail_slow",
                sampler_name="tail_based",
            )

        # Don't sample
        return SamplingResult(
            decision=SamplingDecision.DROP,
            reason="tail_normal",
            sampler_name="tail_based",
        )


class AdaptiveSampler:
    """
    Adaptive sampler that adjusts rate based on system load.

    Monitors system overhead and dynamically adjusts sampling rate
    to maintain target overhead percentage.

    Example:
        ```python
        sampler = AdaptiveSampler(
            base_rate=0.1,
            min_rate=0.01,
            max_rate=1.0,
            target_overhead=0.02,
            adjustment_interval=60.0
        )

        # Sampling rate adjusts based on load
        result = sampler.should_sample("trace-123", current_overhead=0.03)
        # If overhead too high, rate decreases
        ```
    """

    def __init__(
        self,
        base_rate: float = 0.1,
        min_rate: float = 0.01,
        max_rate: float = 1.0,
        target_overhead: float = 0.02,
        adjustment_interval: float = 60.0,
    ):
        """
        Initialize adaptive sampler.

        Args:
            base_rate: Initial sampling rate
            min_rate: Minimum allowed sampling rate
            max_rate: Maximum allowed sampling rate
            target_overhead: Target overhead percentage (e.g., 0.02 = 2%)
            adjustment_interval: Seconds between rate adjustments
        """
        if not min_rate <= base_rate <= max_rate:
            raise ValueError(
                f"base_rate {base_rate} must be between min_rate {min_rate} "
                f"and max_rate {max_rate}"
            )

        self.current_rate = base_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.target_overhead = target_overhead
        self.adjustment_interval = adjustment_interval

        self._last_adjustment_time = time.time()
        self._overhead_samples: list[float] = []
        self._sample_count = 0
        self._total_count = 0

        self._probabilistic_sampler = ProbabilisticSampler(self.current_rate)

    def should_sample(
        self,
        trace_id: str | None,
        current_overhead: float | None = None,
        **kwargs: Any,
    ) -> SamplingResult:
        """
        Determine if a trace should be sampled with adaptive rate.

        Args:
            trace_id: Trace identifier for consistent hashing
            current_overhead: Current system overhead percentage (0.0-1.0)
            **kwargs: Additional context (unused but accepted for interface compatibility)

        Returns:
            Sampling result with decision and metadata
        """
        # Update overhead tracking
        if current_overhead is not None:
            self._overhead_samples.append(current_overhead)

        # Check if we should adjust rate
        current_time = time.time()
        if current_time - self._last_adjustment_time >= self.adjustment_interval:
            self._adjust_rate()
            self._last_adjustment_time = current_time

        # Use probabilistic sampler with current rate
        result = self._probabilistic_sampler.should_sample(trace_id)
        result.sampler_name = "adaptive"

        # Track sampling statistics
        self._total_count += 1
        if result.decision == SamplingDecision.SAMPLE:
            self._sample_count += 1

        return result

    def _adjust_rate(self) -> None:
        """Adjust sampling rate based on overhead measurements."""
        if not self._overhead_samples:
            return

        # Calculate average overhead
        avg_overhead = sum(self._overhead_samples) / len(self._overhead_samples)

        # Adjust rate based on target
        if avg_overhead > self.target_overhead * 1.2:  # 20% over target
            # Reduce sampling rate
            new_rate = max(self.min_rate, self.current_rate * 0.8)
            logger.info(
                f"Reducing sampling rate: {self.current_rate:.3f} -> {new_rate:.3f} "
                f"(overhead: {avg_overhead:.3f} > target: {self.target_overhead:.3f})"
            )
            self.current_rate = new_rate
        elif avg_overhead < self.target_overhead * 0.8:  # 20% under target
            # Increase sampling rate
            new_rate = min(self.max_rate, self.current_rate * 1.2)
            logger.info(
                f"Increasing sampling rate: {self.current_rate:.3f} -> {new_rate:.3f} "
                f"(overhead: {avg_overhead:.3f} < target: {self.target_overhead:.3f})"
            )
            self.current_rate = new_rate

        # Update internal probabilistic sampler
        self._probabilistic_sampler = ProbabilisticSampler(self.current_rate)

        # Reset tracking
        self._overhead_samples.clear()

    def get_stats(self) -> dict[str, Any]:
        """
        Get adaptive sampler statistics.

        Returns:
            Statistics dictionary with current rate, sample count, etc.
        """
        actual_rate = self._sample_count / self._total_count if self._total_count > 0 else 0.0
        return {
            "current_rate": self.current_rate,
            "min_rate": self.min_rate,
            "max_rate": self.max_rate,
            "target_overhead": self.target_overhead,
            "total_decisions": self._total_count,
            "sampled": self._sample_count,
            "actual_sample_rate": actual_rate,
        }


class CompositeSampler:
    """
    Composite sampler combining multiple sampling strategies.

    Evaluates samplers in order and returns first SAMPLE decision.
    This enables layered sampling logic (e.g., always sample errors,
    then probabilistically sample normal traces).

    Example:
        ```python
        sampler = CompositeSampler(
            config=SamplingConfig(
                default_rate=0.1,
                always_sample_errors=True,
                always_sample_slow=True,
                slow_threshold_ms=1000.0,
            )
        )

        # Before completion: probabilistic sampling
        result = sampler.should_sample_head(trace_id="trace-123")

        # After completion: tail-based sampling
        result = sampler.should_sample_tail(
            trace_id="trace-123",
            has_error=True,
            duration_ms=500.0
        )
        ```
    """

    def __init__(self, config: SamplingConfig):
        """
        Initialize composite sampler.

        Args:
            config: Sampling configuration
        """
        self.config = config

        # Create samplers based on config
        if config.adaptive_enabled:
            self.probabilistic = AdaptiveSampler(
                base_rate=config.default_rate,
                min_rate=config.adaptive_min_rate,
                max_rate=config.adaptive_max_rate,
                target_overhead=config.adaptive_target_overhead,
            )
        else:
            self.probabilistic = ProbabilisticSampler(sample_rate=config.default_rate)

        self.tail_based = TailBasedSampler(
            always_sample_errors=config.always_sample_errors,
            always_sample_slow=config.always_sample_slow,
            slow_threshold_ms=config.slow_threshold_ms,
        )

    def should_sample_head(
        self, trace_id: str | None, current_overhead: float | None = None, **kwargs: Any
    ) -> SamplingResult:
        """
        Head-based sampling decision at trace start.

        Args:
            trace_id: Trace identifier
            current_overhead: Current system overhead (for adaptive sampling)
            **kwargs: Additional context

        Returns:
            Sampling result
        """
        return self.probabilistic.should_sample(
            trace_id=trace_id, current_overhead=current_overhead, **kwargs
        )

    def should_sample_tail(
        self,
        trace_id: str | None,
        has_error: bool,
        duration_ms: float,
        head_decision: SamplingResult | None = None,
        **kwargs: Any,
    ) -> SamplingResult:
        """
        Tail-based sampling decision after trace completion.

        If head decided to sample, that decision is preserved.
        Otherwise, tail-based rules apply (errors, slow traces).

        Args:
            trace_id: Trace identifier
            has_error: Whether trace has errors
            duration_ms: Trace duration in milliseconds
            head_decision: Optional head-based decision to preserve
            **kwargs: Additional context

        Returns:
            Sampling result
        """
        # If head already sampled, keep that decision
        if head_decision and head_decision.decision == SamplingDecision.SAMPLE:
            return head_decision

        # Apply tail-based rules
        return self.tail_based.should_sample_after_completion(
            has_error=has_error, duration_ms=duration_ms, **kwargs
        )
