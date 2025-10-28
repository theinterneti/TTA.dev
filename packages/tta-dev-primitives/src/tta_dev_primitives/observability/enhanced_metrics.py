"""Enhanced metrics with percentile tracking and SLO monitoring."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


@dataclass
class PercentileMetrics:
    """Percentile-based metrics for latency analysis."""

    name: str
    durations: list[float] = field(default_factory=list)
    max_samples: int = 10000  # Limit memory usage

    def record(self, duration_ms: float) -> None:
        """Record a duration measurement."""
        self.durations.append(duration_ms)
        # Keep only recent samples to limit memory
        if len(self.durations) > self.max_samples:
            self.durations = self.durations[-self.max_samples :]

    def get_percentiles(self) -> dict[str, float]:
        """
        Calculate percentiles (p50, p90, p95, p99).

        Returns:
            Dictionary with percentile values
        """
        if not self.durations:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}

        if NUMPY_AVAILABLE:
            # Use numpy for accurate percentile calculation
            arr = np.array(self.durations)
            return {
                "p50": float(np.percentile(arr, 50)),
                "p90": float(np.percentile(arr, 90)),
                "p95": float(np.percentile(arr, 95)),
                "p99": float(np.percentile(arr, 99)),
            }
        else:
            # Fallback to sorted list approach
            sorted_durations = sorted(self.durations)
            n = len(sorted_durations)
            return {
                "p50": sorted_durations[int(n * 0.50)],
                "p90": sorted_durations[int(n * 0.90)],
                "p95": sorted_durations[int(n * 0.95)],
                "p99": sorted_durations[int(n * 0.99)],
            }

    def reset(self) -> None:
        """Reset all duration samples."""
        self.durations.clear()


@dataclass
class SLOConfig:
    """Service Level Objective configuration."""

    name: str
    target: float  # Target compliance (e.g., 0.99 for 99%)
    threshold_ms: float | None = None  # Latency threshold in ms
    error_rate_threshold: float | None = None  # Error rate threshold (e.g., 0.01 for 1%)
    window_seconds: int = 2592000  # 30 days default


@dataclass
class SLOMetrics:
    """SLO tracking and error budget calculation."""

    config: SLOConfig
    total_requests: int = 0
    successful_requests: int = 0
    requests_within_threshold: int = 0
    window_start: float = field(default_factory=time.time)

    @property
    def availability(self) -> float:
        """Calculate availability (success rate)."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def latency_compliance(self) -> float:
        """Calculate latency SLO compliance."""
        if self.total_requests == 0:
            return 1.0
        return self.requests_within_threshold / self.total_requests

    @property
    def error_budget_remaining(self) -> float:
        """
        Calculate remaining error budget.

        Returns:
            Percentage of error budget remaining (0.0 to 1.0)
        """
        if self.config.error_rate_threshold:
            # Error budget based on error rate
            allowed_errors = self.total_requests * (1 - self.config.target)
            actual_errors = self.total_requests - self.successful_requests
            if allowed_errors == 0:
                return 1.0 if actual_errors == 0 else 0.0
            remaining = (allowed_errors - actual_errors) / allowed_errors
            return max(0.0, min(1.0, remaining))
        else:
            # Error budget based on latency compliance
            required_compliance = self.config.target
            actual_compliance = self.latency_compliance
            if actual_compliance >= required_compliance:
                return 1.0
            return actual_compliance / required_compliance

    @property
    def is_compliant(self) -> bool:
        """Check if SLO is currently being met."""
        if self.config.error_rate_threshold:
            return self.availability >= self.config.target
        else:
            return self.latency_compliance >= self.config.target

    def record_request(self, duration_ms: float, success: bool) -> None:
        """
        Record a request for SLO tracking.

        Args:
            duration_ms: Request duration in milliseconds
            success: Whether the request succeeded
        """
        self.total_requests += 1
        if success:
            self.successful_requests += 1

        if self.config.threshold_ms and duration_ms <= self.config.threshold_ms:
            self.requests_within_threshold += 1

    def reset(self) -> None:
        """Reset SLO metrics."""
        self.total_requests = 0
        self.successful_requests = 0
        self.requests_within_threshold = 0
        self.window_start = time.time()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.config.name,
            "target": self.config.target,
            "threshold_ms": self.config.threshold_ms,
            "total_requests": self.total_requests,
            "availability": self.availability,
            "latency_compliance": self.latency_compliance,
            "error_budget_remaining": self.error_budget_remaining,
            "is_compliant": self.is_compliant,
            "window_age_seconds": time.time() - self.window_start,
        }


@dataclass
class ThroughputMetrics:
    """Throughput and concurrency tracking."""

    name: str
    total_requests: int = 0
    active_requests: int = 0
    window_start: float = field(default_factory=time.time)
    request_timestamps: list[float] = field(default_factory=list)
    max_timestamps: int = 1000  # Keep last 1000 timestamps

    def start_request(self) -> None:
        """Mark a request as started."""
        self.active_requests += 1
        self.total_requests += 1
        self.request_timestamps.append(time.time())
        # Limit memory usage
        if len(self.request_timestamps) > self.max_timestamps:
            self.request_timestamps = self.request_timestamps[-self.max_timestamps :]

    def end_request(self) -> None:
        """Mark a request as completed."""
        self.active_requests = max(0, self.active_requests - 1)

    @property
    def requests_per_second(self) -> float:
        """Calculate requests per second over recent window."""
        if not self.request_timestamps:
            return 0.0

        now = time.time()
        # Calculate RPS over last 60 seconds
        recent_requests = [ts for ts in self.request_timestamps if now - ts <= 60]
        if not recent_requests:
            return 0.0

        time_span = now - min(recent_requests)
        if time_span == 0:
            return 0.0

        return len(recent_requests) / time_span

    def reset(self) -> None:
        """Reset throughput metrics."""
        self.total_requests = 0
        self.active_requests = 0
        self.window_start = time.time()
        self.request_timestamps.clear()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "total_requests": self.total_requests,
            "active_requests": self.active_requests,
            "requests_per_second": self.requests_per_second,
            "window_age_seconds": time.time() - self.window_start,
        }


@dataclass
class CostMetrics:
    """Cost tracking for primitives."""

    name: str
    total_cost: float = 0.0
    total_savings: float = 0.0
    cost_by_operation: dict[str, float] = field(default_factory=dict)

    def record_cost(self, cost: float, operation: str = "default") -> None:
        """Record a cost."""
        self.total_cost += cost
        self.cost_by_operation[operation] = self.cost_by_operation.get(operation, 0.0) + cost

    def record_savings(self, savings: float) -> None:
        """Record cost savings (e.g., from cache hits)."""
        self.total_savings += savings

    @property
    def net_cost(self) -> float:
        """Calculate net cost after savings."""
        return self.total_cost - self.total_savings

    def reset(self) -> None:
        """Reset cost metrics."""
        self.total_cost = 0.0
        self.total_savings = 0.0
        self.cost_by_operation.clear()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "total_cost": self.total_cost,
            "total_savings": self.total_savings,
            "net_cost": self.net_cost,
            "cost_by_operation": self.cost_by_operation,
        }
