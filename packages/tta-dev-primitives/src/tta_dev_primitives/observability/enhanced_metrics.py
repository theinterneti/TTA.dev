"""Enhanced metrics for production monitoring with percentiles, SLO tracking, and cost analysis."""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

# Try to import numpy for percentile calculation, fall back to pure Python
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


@dataclass
class PercentileMetrics:
    """
    Tracks latency percentiles (p50, p90, p95, p99) for performance analysis.

    Uses numpy for efficient percentile calculation when available,
    falls back to pure Python implementation otherwise.

    Example:
        ```python
        metrics = PercentileMetrics()
        metrics.record_latency(0.123)
        metrics.record_latency(0.456)
        
        stats = metrics.get_percentiles()
        print(f"p95: {stats['p95']:.3f}s")  # p95: 0.434s
        ```
    """

    name: str
    latencies: list[float] = field(default_factory=list)
    max_samples: int = 10000  # Limit memory usage

    def record_latency(self, duration_seconds: float) -> None:
        """
        Record a latency measurement.

        Args:
            duration_seconds: Latency in seconds
        """
        self.latencies.append(duration_seconds)
        
        # Keep only most recent samples to prevent unbounded growth
        if len(self.latencies) > self.max_samples:
            self.latencies = self.latencies[-self.max_samples :]

    def get_percentiles(self) -> dict[str, float]:
        """
        Calculate latency percentiles.

        Returns:
            Dictionary with p50, p90, p95, p99 values in seconds
        """
        if not self.latencies:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}

        if NUMPY_AVAILABLE:
            # Use numpy for efficient percentile calculation
            latencies_array = np.array(self.latencies)
            return {
                "p50": float(np.percentile(latencies_array, 50)),
                "p90": float(np.percentile(latencies_array, 90)),
                "p95": float(np.percentile(latencies_array, 95)),
                "p99": float(np.percentile(latencies_array, 99)),
            }
        else:
            # Fall back to pure Python implementation
            sorted_latencies = sorted(self.latencies)
            n = len(sorted_latencies)
            
            def percentile(p: float) -> float:
                """Calculate percentile using linear interpolation."""
                k = (n - 1) * p / 100.0
                f = int(k)
                c = min(f + 1, n - 1)
                if f == c:
                    return sorted_latencies[f]
                return sorted_latencies[f] * (c - k) + sorted_latencies[c] * (k - f)
            
            return {
                "p50": percentile(50),
                "p90": percentile(90),
                "p95": percentile(95),
                "p99": percentile(99),
            }

    def reset(self) -> None:
        """Clear all recorded latencies."""
        self.latencies.clear()


@dataclass
class SLOConfig:
    """
    SLO (Service Level Objective) configuration.

    Example:
        ```python
        # 99% of requests should complete within 1 second
        slo = SLOConfig(
            target=0.99,
            latency_threshold_seconds=1.0,
            availability_target=0.999
        )
        ```
    """

    target: float  # Target percentage (e.g., 0.99 for 99%)
    latency_threshold_seconds: float | None = None  # Latency SLO
    availability_target: float | None = None  # Availability SLO (success rate)
    window_seconds: float = 2592000.0  # 30 days default


@dataclass
class SLOMetrics:
    """
    Tracks SLO compliance and error budget.

    Monitors both latency and availability SLOs, calculates error budgets,
    and tracks compliance over time.

    Example:
        ```python
        slo = SLOConfig(target=0.99, latency_threshold_seconds=1.0)
        metrics = SLOMetrics("my_service", slo)
        
        metrics.record_request(duration_seconds=0.5, success=True)
        metrics.record_request(duration_seconds=1.5, success=False)
        
        status = metrics.get_slo_status()
        print(f"Error budget remaining: {status['error_budget_remaining']:.2%}")
        ```
    """

    name: str
    slo_config: SLOConfig
    total_requests: int = 0
    successful_requests: int = 0
    latency_violations: int = 0
    requests_within_slo: int = 0

    def record_request(self, duration_seconds: float, success: bool) -> None:
        """
        Record a request for SLO tracking.

        Args:
            duration_seconds: Request duration in seconds
            success: Whether the request was successful
        """
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
        
        # Track latency SLO
        if self.slo_config.latency_threshold_seconds is not None:
            if duration_seconds <= self.slo_config.latency_threshold_seconds:
                self.requests_within_slo += 1
            else:
                self.latency_violations += 1

    def get_slo_status(self) -> dict[str, Any]:
        """
        Get current SLO status and error budget.

        Returns:
            Dictionary with SLO compliance metrics
        """
        if self.total_requests == 0:
            return {
                "slo_compliance": 1.0,
                "error_budget_remaining": 1.0,
                "availability": 1.0,
                "latency_compliance": 1.0,
                "total_requests": 0,
                "successful_requests": 0,
                "latency_violations": 0,
            }

        availability = self.successful_requests / self.total_requests
        
        # Calculate latency compliance
        if self.slo_config.latency_threshold_seconds is not None and self.total_requests > 0:
            latency_compliance = self.requests_within_slo / self.total_requests
        else:
            latency_compliance = 1.0

        # Overall SLO compliance (minimum of availability and latency)
        slo_compliance = min(availability, latency_compliance)
        
        # Error budget remaining (1.0 = 100% budget remaining)
        target = self.slo_config.target
        error_budget = 1.0 - target
        
        if slo_compliance >= target:
            # Above target, error budget not yet consumed
            error_budget_remaining = 1.0
        elif error_budget > 0:
            # Calculate how much of error budget consumed
            errors = target - slo_compliance
            error_budget_consumed = errors / error_budget
            error_budget_remaining = max(0.0, 1.0 - error_budget_consumed)
        else:
            # Target is 100%, any violation exhausts budget
            error_budget_remaining = 0.0

        return {
            "slo_compliance": slo_compliance,
            "error_budget_remaining": error_budget_remaining,
            "availability": availability,
            "latency_compliance": latency_compliance,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "latency_violations": self.latency_violations,
        }

    def reset(self) -> None:
        """Reset all SLO metrics."""
        self.total_requests = 0
        self.successful_requests = 0
        self.latency_violations = 0
        self.requests_within_slo = 0


@dataclass
class ThroughputMetrics:
    """
    Tracks throughput metrics (requests per second, active requests).

    Example:
        ```python
        metrics = ThroughputMetrics()
        
        # Record request start
        request_id = "req-123"
        metrics.record_request_start(request_id)
        
        # ... process request ...
        
        # Record request end
        metrics.record_request_end(request_id)
        
        stats = metrics.get_stats()
        print(f"Active requests: {stats['active_requests']}")
        print(f"RPS: {stats['requests_per_second']:.2f}")
        ```
    """

    name: str
    total_requests: int = 0
    active_requests: int = 0
    _request_timestamps: list[float] = field(default_factory=list)
    _active_request_ids: set[str] = field(default_factory=set)
    _window_seconds: float = 60.0  # Calculate RPS over last 60 seconds

    def record_request_start(self, request_id: str | None = None) -> None:
        """
        Record a request start.

        Args:
            request_id: Optional request identifier for tracking
        """
        self.total_requests += 1
        self.active_requests += 1
        
        if request_id:
            self._active_request_ids.add(request_id)
        
        self._request_timestamps.append(time.time())

    def record_request_end(self, request_id: str | None = None) -> None:
        """
        Record a request end.

        Args:
            request_id: Optional request identifier for tracking
        """
        self.active_requests = max(0, self.active_requests - 1)
        
        if request_id and request_id in self._active_request_ids:
            self._active_request_ids.discard(request_id)

    def get_stats(self) -> dict[str, Any]:
        """
        Get throughput statistics.

        Returns:
            Dictionary with throughput metrics
        """
        # Clean up old timestamps outside the window
        current_time = time.time()
        cutoff_time = current_time - self._window_seconds
        self._request_timestamps = [
            ts for ts in self._request_timestamps if ts >= cutoff_time
        ]

        # Calculate requests per second
        if len(self._request_timestamps) > 0:
            time_span = current_time - min(self._request_timestamps)
            rps = len(self._request_timestamps) / time_span if time_span > 0 else 0.0
        else:
            rps = 0.0

        return {
            "total_requests": self.total_requests,
            "active_requests": self.active_requests,
            "requests_per_second": rps,
        }

    def reset(self) -> None:
        """Reset all throughput metrics."""
        self.total_requests = 0
        self.active_requests = 0
        self._request_timestamps.clear()
        self._active_request_ids.clear()


@dataclass
class CostMetrics:
    """
    Tracks cost metrics and savings.

    Example:
        ```python
        metrics = CostMetrics()
        
        # Record cost for an operation
        metrics.record_cost(0.002, "llm_call")
        
        # Record savings from cache hit
        metrics.record_savings(0.002, "cache_hit")
        
        stats = metrics.get_stats()
        print(f"Total cost: ${stats['total_cost']:.4f}")
        print(f"Savings: ${stats['total_savings']:.4f}")
        print(f"Savings rate: {stats['savings_rate']:.2%}")
        ```
    """

    name: str
    total_cost: float = 0.0
    total_savings: float = 0.0
    cost_breakdown: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    savings_breakdown: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def record_cost(self, cost: float, category: str = "default") -> None:
        """
        Record a cost.

        Args:
            cost: Cost amount in dollars
            category: Cost category for breakdown
        """
        self.total_cost += cost
        self.cost_breakdown[category] += cost

    def record_savings(self, savings: float, category: str = "default") -> None:
        """
        Record savings (e.g., from cache hit, fallback to cheaper model).

        Args:
            savings: Savings amount in dollars
            category: Savings category for breakdown
        """
        self.total_savings += savings
        self.savings_breakdown[category] += savings

    def get_stats(self) -> dict[str, Any]:
        """
        Get cost statistics.

        Returns:
            Dictionary with cost metrics
        """
        # Calculate savings rate
        potential_cost = self.total_cost + self.total_savings
        savings_rate = self.total_savings / potential_cost if potential_cost > 0 else 0.0

        return {
            "total_cost": self.total_cost,
            "total_savings": self.total_savings,
            "net_cost": self.total_cost - self.total_savings,
            "savings_rate": savings_rate,
            "cost_breakdown": dict(self.cost_breakdown),
            "savings_breakdown": dict(self.savings_breakdown),
        }

    def reset(self) -> None:
        """Reset all cost metrics."""
        self.total_cost = 0.0
        self.total_savings = 0.0
        self.cost_breakdown.clear()
        self.savings_breakdown.clear()


class EnhancedMetricsCollector:
    """
    Unified metrics collector integrating all enhanced metrics types.

    Provides a single interface for collecting percentiles, SLO tracking,
    throughput, and cost metrics across all primitives.

    Thread-safe for concurrent access.

    Example:
        ```python
        from tta_dev_primitives.observability import get_enhanced_metrics_collector
        
        collector = get_enhanced_metrics_collector()
        
        # Configure SLO for a primitive
        slo = SLOConfig(target=0.99, latency_threshold_seconds=1.0)
        collector.configure_slo("my_primitive", slo)
        
        # Record execution
        collector.record_execution(
            primitive_name="my_primitive",
            duration_seconds=0.5,
            success=True,
            cost=0.002
        )
        
        # Get comprehensive metrics
        metrics = collector.get_all_metrics()
        ```
    """

    def __init__(self) -> None:
        """Initialize the enhanced metrics collector."""
        self._lock = threading.Lock()
        self._percentile_metrics: dict[str, PercentileMetrics] = {}
        self._slo_metrics: dict[str, SLOMetrics] = {}
        self._throughput_metrics: dict[str, ThroughputMetrics] = {}
        self._cost_metrics: dict[str, CostMetrics] = {}

    def configure_slo(self, primitive_name: str, slo_config: SLOConfig) -> None:
        """
        Configure SLO for a primitive.

        Args:
            primitive_name: Name of the primitive
            slo_config: SLO configuration
        """
        with self._lock:
            self._slo_metrics[primitive_name] = SLOMetrics(primitive_name, slo_config)

    def record_execution(
        self,
        primitive_name: str,
        duration_seconds: float,
        success: bool,
        cost: float | None = None,
        savings: float | None = None,
        request_id: str | None = None,
    ) -> None:
        """
        Record a primitive execution with all metrics.

        Args:
            primitive_name: Name of the primitive
            duration_seconds: Execution duration in seconds
            success: Whether execution succeeded
            cost: Optional cost in dollars
            savings: Optional savings in dollars
            request_id: Optional request identifier
        """
        with self._lock:
            # Percentile metrics
            if primitive_name not in self._percentile_metrics:
                self._percentile_metrics[primitive_name] = PercentileMetrics(primitive_name)
            self._percentile_metrics[primitive_name].record_latency(duration_seconds)

            # SLO metrics
            if primitive_name in self._slo_metrics:
                self._slo_metrics[primitive_name].record_request(duration_seconds, success)

            # Throughput metrics
            if primitive_name not in self._throughput_metrics:
                self._throughput_metrics[primitive_name] = ThroughputMetrics(primitive_name)
            # Note: throughput start/end should be called separately
            # This is just for backwards compatibility
            self._throughput_metrics[primitive_name].record_request_start(request_id)
            self._throughput_metrics[primitive_name].record_request_end(request_id)

            # Cost metrics
            if cost is not None or savings is not None:
                if primitive_name not in self._cost_metrics:
                    self._cost_metrics[primitive_name] = CostMetrics(primitive_name)
                if cost is not None:
                    self._cost_metrics[primitive_name].record_cost(cost)
                if savings is not None:
                    self._cost_metrics[primitive_name].record_savings(savings)

    def record_request_start(self, primitive_name: str, request_id: str | None = None) -> None:
        """
        Record request start for throughput tracking.

        Args:
            primitive_name: Name of the primitive
            request_id: Optional request identifier
        """
        with self._lock:
            if primitive_name not in self._throughput_metrics:
                self._throughput_metrics[primitive_name] = ThroughputMetrics(primitive_name)
            self._throughput_metrics[primitive_name].record_request_start(request_id)

    def record_request_end(self, primitive_name: str, request_id: str | None = None) -> None:
        """
        Record request end for throughput tracking.

        Args:
            primitive_name: Name of the primitive
            request_id: Optional request identifier
        """
        with self._lock:
            if primitive_name in self._throughput_metrics:
                self._throughput_metrics[primitive_name].record_request_end(request_id)

    def get_all_metrics(self, primitive_name: str | None = None) -> dict[str, Any]:
        """
        Get all metrics for a primitive or all primitives.

        Args:
            primitive_name: Optional primitive name, or None for all

        Returns:
            Dictionary with comprehensive metrics
        """
        with self._lock:
            if primitive_name:
                return self._get_primitive_metrics(primitive_name)
            else:
                return {
                    name: self._get_primitive_metrics(name)
                    for name in set(
                        list(self._percentile_metrics.keys())
                        + list(self._slo_metrics.keys())
                        + list(self._throughput_metrics.keys())
                        + list(self._cost_metrics.keys())
                    )
                }

    def _get_primitive_metrics(self, primitive_name: str) -> dict[str, Any]:
        """Get metrics for a single primitive."""
        metrics: dict[str, Any] = {}

        if primitive_name in self._percentile_metrics:
            metrics["percentiles"] = self._percentile_metrics[primitive_name].get_percentiles()

        if primitive_name in self._slo_metrics:
            metrics["slo"] = self._slo_metrics[primitive_name].get_slo_status()

        if primitive_name in self._throughput_metrics:
            metrics["throughput"] = self._throughput_metrics[primitive_name].get_stats()

        if primitive_name in self._cost_metrics:
            metrics["cost"] = self._cost_metrics[primitive_name].get_stats()

        return metrics

    def reset(self, primitive_name: str | None = None) -> None:
        """
        Reset metrics for a primitive or all primitives.

        Args:
            primitive_name: Optional primitive name, or None for all
        """
        with self._lock:
            if primitive_name:
                if primitive_name in self._percentile_metrics:
                    self._percentile_metrics[primitive_name].reset()
                if primitive_name in self._slo_metrics:
                    self._slo_metrics[primitive_name].reset()
                if primitive_name in self._throughput_metrics:
                    self._throughput_metrics[primitive_name].reset()
                if primitive_name in self._cost_metrics:
                    self._cost_metrics[primitive_name].reset()
            else:
                for metrics in self._percentile_metrics.values():
                    metrics.reset()
                for metrics in self._slo_metrics.values():
                    metrics.reset()
                for metrics in self._throughput_metrics.values():
                    metrics.reset()
                for metrics in self._cost_metrics.values():
                    metrics.reset()


# Global enhanced metrics collector
_enhanced_metrics_collector: EnhancedMetricsCollector | None = None
_collector_lock = threading.Lock()


def get_enhanced_metrics_collector() -> EnhancedMetricsCollector:
    """
    Get the global enhanced metrics collector.

    Thread-safe singleton pattern.

    Returns:
        Global EnhancedMetricsCollector instance
    """
    global _enhanced_metrics_collector
    
    if _enhanced_metrics_collector is None:
        with _collector_lock:
            # Double-check locking pattern
            if _enhanced_metrics_collector is None:
                _enhanced_metrics_collector = EnhancedMetricsCollector()
    
    return _enhanced_metrics_collector
