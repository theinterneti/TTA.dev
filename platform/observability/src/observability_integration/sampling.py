"""Sampling strategies for observability at scale.

This module provides configurable sampling to reduce overhead and costs
while maintaining visibility into important events.
"""

import hashlib
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


def _hash_to_probability(trace_id: str) -> float:
    """Convert trace_id to consistent probability value.

    Args:
        trace_id: Unique trace identifier

    Returns:
        Float between 0.0 and 1.0 derived from consistent hash
    """
    hash_value = int(hashlib.md5(trace_id.encode(), usedforsecurity=False).hexdigest()[:8], 16)
    return hash_value / 0xFFFFFFFF


class SamplingDecision(Enum):
    """Sampling decision for a trace."""

    SAMPLE = "sample"
    DROP = "drop"


class SamplingStrategy(Protocol):
    """Protocol for sampling strategies."""

    def should_sample(self, trace_id: str, context: dict) -> SamplingDecision:
        """Decide whether to sample a trace.

        Args:
            trace_id: Unique trace identifier
            context: Additional context (errors, latency, etc.)

        Returns:
            SamplingDecision indicating whether to sample
        """
        ...


@dataclass
class ProbabilisticSampler:
    """Sample traces based on a fixed probability.

    Uses consistent hashing to ensure the same trace_id always
    gets the same sampling decision.
    """

    sample_rate: float = 0.1

    def __post_init__(self):
        """Validate sample rate."""
        if not 0.0 <= self.sample_rate <= 1.0:
            raise ValueError(f"sample_rate must be 0.0-1.0, got {self.sample_rate}")

    def should_sample(self, trace_id: str, context: dict | None = None) -> SamplingDecision:
        """Decide whether to sample based on probability.

        Args:
            trace_id: Unique trace identifier
            context: Additional context (unused)

        Returns:
            SamplingDecision based on consistent hash
        """
        normalized = _hash_to_probability(trace_id)
        return SamplingDecision.SAMPLE if normalized < self.sample_rate else SamplingDecision.DROP


@dataclass
class TailBasedSampler:
    """Sample traces based on tail characteristics (errors, latency).

    Always samples traces with errors or high latency, regardless of
    probabilistic sampling.
    """

    always_sample_errors: bool = True
    always_sample_slow: bool = True
    slow_threshold_ms: float = 1000.0

    def should_sample(self, trace_id: str, context: dict) -> SamplingDecision:
        """Decide whether to sample based on tail characteristics.

        Args:
            trace_id: Unique trace identifier
            context: Must contain 'has_error' and/or 'duration_ms'

        Returns:
            SamplingDecision based on error/latency
        """
        if self.always_sample_errors and context.get("has_error"):
            return SamplingDecision.SAMPLE

        if self.always_sample_slow:
            duration_ms = context.get("duration_ms", 0.0)
            if duration_ms >= self.slow_threshold_ms:
                return SamplingDecision.SAMPLE

        return SamplingDecision.DROP


@dataclass
class AdaptiveSampler:
    """Adjust sampling rate based on system load.

    Automatically reduces sampling when overhead is high,
    increases when overhead is low.

    Thread-safe for production use with >100K req/day.
    """

    min_rate: float = 0.01
    max_rate: float = 1.0
    target_overhead: float = 0.02
    adjustment_interval: float = 60.0
    current_rate: float = field(init=False)
    _last_adjustment: float = field(default=0.0, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def __post_init__(self):
        """Initialize and validate parameters."""
        if not 0.0 <= self.min_rate <= 1.0:
            raise ValueError(f"min_rate must be 0.0-1.0, got {self.min_rate}")
        if not 0.0 <= self.max_rate <= 1.0:
            raise ValueError(f"max_rate must be 0.0-1.0, got {self.max_rate}")
        if self.min_rate > self.max_rate:
            raise ValueError(f"min_rate ({self.min_rate}) must be <= max_rate ({self.max_rate})")
        self.current_rate = self.max_rate

    def should_sample(self, trace_id: str, context: dict | None = None) -> SamplingDecision:
        """Decide whether to sample with adaptive rate.

        Args:
            trace_id: Unique trace identifier
            context: May contain 'current_overhead' for rate adjustment

        Returns:
            SamplingDecision based on current adaptive rate
        """
        # Adjust rate if overhead data available
        if context and "current_overhead" in context:
            self._maybe_adjust_rate(context["current_overhead"])

        # Use probabilistic sampling with current rate
        normalized = _hash_to_probability(trace_id)
        with self._lock:
            current = self.current_rate
        return SamplingDecision.SAMPLE if normalized < current else SamplingDecision.DROP

    def _maybe_adjust_rate(self, current_overhead: float) -> None:
        """Adjust sampling rate based on current overhead.

        Args:
            current_overhead: Current observability overhead (0.0-1.0)
        """
        with self._lock:
            now = time.time()
            if now - self._last_adjustment < self.adjustment_interval:
                return

            if current_overhead > self.target_overhead:
                # Reduce sampling to lower overhead
                self.current_rate = max(self.min_rate, self.current_rate * 0.9)
            elif current_overhead < self.target_overhead * 0.8:
                # Increase sampling if well below target
                self.current_rate = min(self.max_rate, self.current_rate * 1.1)

            self._last_adjustment = now


@dataclass
class CompositeSampler:
    """Combine multiple sampling strategies.

    Samples if ANY strategy says to sample (OR logic).
    """

    strategies: list[SamplingStrategy]

    def should_sample(self, trace_id: str, context: dict | None = None) -> SamplingDecision:
        """Decide whether to sample using composite strategy.

        Args:
            trace_id: Unique trace identifier
            context: Additional context

        Returns:
            SAMPLE if any strategy says SAMPLE, else DROP
        """
        if not context:
            context = {}

        for strategy in self.strategies:
            if strategy.should_sample(trace_id, context) == SamplingDecision.SAMPLE:
                return SamplingDecision.SAMPLE

        return SamplingDecision.DROP
