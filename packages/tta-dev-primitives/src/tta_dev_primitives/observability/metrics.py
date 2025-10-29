"""Metrics collection for workflow primitives with Phase 3 enhancements."""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

# Try to import numpy for percentile calculation, fall back to manual implementation
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


@dataclass
class PrimitiveMetrics:
    """Metrics for a single primitive."""

    name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float("inf")
    max_duration_ms: float = 0.0
    error_counts: dict[str, int] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions

    @property
    def average_duration_ms(self) -> float:
        """Calculate average duration."""
        if self.total_executions == 0:
            return 0.0
        return self.total_duration_ms / self.total_executions

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": self.success_rate,
            "total_duration_ms": self.total_duration_ms,
            "average_duration_ms": self.average_duration_ms,
            "min_duration_ms": self.min_duration_ms if self.min_duration_ms != float("inf") else 0,
            "max_duration_ms": self.max_duration_ms,
            "error_counts": self.error_counts,
        }


class MetricsCollector:
    """Collects metrics for all primitives."""

    def __init__(self) -> None:
        self._metrics: dict[str, PrimitiveMetrics] = {}

    def record_execution(
        self,
        primitive_name: str,
        duration_ms: float,
        success: bool,
        error_type: str | None = None,
    ) -> None:
        """
        Record a primitive execution.

        Args:
            primitive_name: Name of the primitive
            duration_ms: Execution duration in milliseconds
            success: Whether execution succeeded
            error_type: Type of error if failed
        """
        if primitive_name not in self._metrics:
            self._metrics[primitive_name] = PrimitiveMetrics(name=primitive_name)

        metrics = self._metrics[primitive_name]
        metrics.total_executions += 1
        metrics.total_duration_ms += duration_ms
        metrics.min_duration_ms = min(metrics.min_duration_ms, duration_ms)
        metrics.max_duration_ms = max(metrics.max_duration_ms, duration_ms)

        if success:
            metrics.successful_executions += 1
        else:
            metrics.failed_executions += 1
            if error_type:
                metrics.error_counts[error_type] = metrics.error_counts.get(error_type, 0) + 1

    def get_metrics(self, primitive_name: str | None = None) -> dict[str, Any]:
        """
        Get metrics for a primitive or all primitives.

        Args:
            primitive_name: Optional primitive name, or None for all

        Returns:
            Metrics dictionary
        """
        if primitive_name:
            metrics = self._metrics.get(primitive_name)
            return metrics.to_dict() if metrics else {}
        else:
            return {name: metrics.to_dict() for name, metrics in self._metrics.items()}

    def reset(self) -> None:
        """Reset all metrics."""
        self._metrics.clear()


# Phase 3: Enhanced Metrics Classes


class PercentileMetrics:
    """
    Tracks latency percentiles (p50, p90, p95, p99) for performance analysis.

    Uses a sliding window to maintain recent latency measurements and calculate
    percentiles efficiently.

    Example:
        ```python
        metrics = PercentileMetrics(window_size=1000)
        
        # Record latencies
        metrics.record(45.2)
        metrics.record(123.5)
        
        # Get percentiles
        p95 = metrics.get_percentile(0.95)
        stats = metrics.get_stats()
        print(f"p50: {stats['p50']}, p95: {stats['p95']}, p99: {stats['p99']}")
        ```
    """

    def __init__(self, window_size: int = 1000) -> None:
        """
        Initialize percentile metrics.

        Args:
            window_size: Maximum number of samples to retain for percentile calculation
        """
        self._window_size = window_size
        self._latencies: deque[float] = deque(maxlen=window_size)
        self._lock = threading.Lock()

    def record(self, latency_ms: float) -> None:
        """
        Record a latency measurement.

        Args:
            latency_ms: Latency in milliseconds
        """
        with self._lock:
            self._latencies.append(latency_ms)

    def get_percentile(self, percentile: float) -> float:
        """
        Calculate a specific percentile.

        Args:
            percentile: Percentile to calculate (0.0 to 1.0, e.g., 0.95 for p95)

        Returns:
            Percentile value in milliseconds, or 0.0 if no data

        Example:
            ```python
            p95 = metrics.get_percentile(0.95)
            p99 = metrics.get_percentile(0.99)
            ```
        """
        with self._lock:
            if not self._latencies:
                return 0.0

            latencies = list(self._latencies)

        if NUMPY_AVAILABLE:
            return float(np.percentile(latencies, percentile * 100))
        else:
            # Fallback: manual percentile calculation
            sorted_latencies = sorted(latencies)
            index = int(len(sorted_latencies) * percentile)
            # Clamp index to valid range
            index = max(0, min(index, len(sorted_latencies) - 1))
            return sorted_latencies[index]

    def get_stats(self) -> dict[str, float]:
        """
        Get common percentile statistics.

        Returns:
            Dictionary with p50, p90, p95, p99 percentiles

        Example:
            ```python
            stats = metrics.get_stats()
            print(f"Median: {stats['p50']}ms")
            print(f"p95: {stats['p95']}ms")
            print(f"p99: {stats['p99']}ms")
            ```
        """
        return {
            "p50": self.get_percentile(0.50),
            "p90": self.get_percentile(0.90),
            "p95": self.get_percentile(0.95),
            "p99": self.get_percentile(0.99),
            "count": len(self._latencies),
        }


@dataclass
class SLOConfig:
    """
    Configuration for a Service Level Objective (SLO).

    Example:
        ```python
        # Latency SLO: 95% of requests under 1000ms
        latency_slo = SLOConfig(
            name="api_latency",
            target=0.95,
            threshold_ms=1000.0,
            window_seconds=2592000.0  # 30 days
        )
        
        # Availability SLO: 99.9% success rate
        availability_slo = SLOConfig(
            name="api_availability",
            target=0.999,
            threshold_ms=None,
            window_seconds=2592000.0
        )
        ```
    """

    name: str
    target: float  # Target SLO (e.g., 0.95 for 95%)
    threshold_ms: float | None = None  # Latency threshold (None for availability SLO)
    window_seconds: float = 2592000.0  # 30 days default


class SLOMetrics:
    """
    Tracks Service Level Objectives (SLOs) with error budget calculation.

    Supports both latency-based SLOs (% of requests under threshold) and
    availability SLOs (% of successful requests).

    Example:
        ```python
        # Configure SLO: 95% of requests under 1000ms
        slo_config = SLOConfig(
            name="api_latency",
            target=0.95,
            threshold_ms=1000.0,
            window_seconds=86400.0  # 24 hours
        )
        
        slo = SLOMetrics(slo_config)
        
        # Record requests
        slo.record_request(success=True, latency_ms=450.0)
        slo.record_request(success=True, latency_ms=1500.0)  # SLO violation
        
        # Check compliance
        compliance = slo.get_compliance()
        print(f"SLO compliance: {compliance:.2%}")
        print(f"Error budget remaining: {slo.get_error_budget():.2%}")
        ```
    """

    def __init__(self, config: SLOConfig) -> None:
        """
        Initialize SLO metrics.

        Args:
            config: SLO configuration
        """
        self.config = config
        self._total_requests: int = 0
        self._conforming_requests: int = 0
        self._window_start: float = time.time()
        self._lock = threading.Lock()

    def record_request(self, success: bool, latency_ms: float | None = None) -> None:
        """
        Record a request for SLO tracking.

        Args:
            success: Whether the request succeeded
            latency_ms: Request latency in milliseconds (required for latency SLOs)

        Example:
            ```python
            # For latency SLO
            slo.record_request(success=True, latency_ms=450.0)
            
            # For availability SLO
            slo.record_request(success=True)
            ```
        """
        with self._lock:
            # Reset window if expired
            current_time = time.time()
            if current_time - self._window_start > self.config.window_seconds:
                self._total_requests = 0
                self._conforming_requests = 0
                self._window_start = current_time

            self._total_requests += 1

            # Check if request conforms to SLO
            if self.config.threshold_ms is not None:
                # Latency SLO: check if latency is under threshold
                if latency_ms is not None and latency_ms <= self.config.threshold_ms and success:
                    self._conforming_requests += 1
            else:
                # Availability SLO: check if request succeeded
                if success:
                    self._conforming_requests += 1

    def get_compliance(self) -> float:
        """
        Get current SLO compliance rate.

        Returns:
            Compliance rate (0.0 to 1.0)

        Example:
            ```python
            compliance = slo.get_compliance()
            if compliance < slo.config.target:
                print("SLO violation!")
            ```
        """
        with self._lock:
            if self._total_requests == 0:
                return 1.0
            return self._conforming_requests / self._total_requests

    def get_error_budget(self) -> float:
        """
        Get remaining error budget as a percentage.

        Error budget = (actual_compliance - target_compliance) / (1 - target_compliance)

        Returns:
            Error budget remaining (0.0 to 1.0)

        Example:
            ```python
            budget = slo.get_error_budget()
            if budget < 0.1:  # Less than 10% remaining
                print("Warning: Error budget nearly exhausted!")
            ```
        """
        compliance = self.get_compliance()
        if compliance >= self.config.target:
            return 1.0  # Full budget remaining
        else:
            # Calculate how much of the error budget has been consumed
            allowed_errors = 1.0 - self.config.target
            actual_errors = 1.0 - compliance
            if allowed_errors == 0:
                return 0.0
            consumed = actual_errors / allowed_errors
            return max(0.0, 1.0 - consumed)

    def get_stats(self) -> dict[str, Any]:
        """
        Get comprehensive SLO statistics.

        Returns:
            Dictionary with compliance, error budget, and request counts

        Example:
            ```python
            stats = slo.get_stats()
            print(f"Compliance: {stats['compliance']:.2%}")
            print(f"Error budget: {stats['error_budget']:.2%}")
            print(f"Total requests: {stats['total_requests']}")
            ```
        """
        return {
            "name": self.config.name,
            "target": self.config.target,
            "compliance": self.get_compliance(),
            "error_budget": self.get_error_budget(),
            "total_requests": self._total_requests,
            "conforming_requests": self._conforming_requests,
            "window_seconds": self.config.window_seconds,
        }


class ThroughputMetrics:
    """
    Tracks throughput metrics (requests per second, active requests).

    Example:
        ```python
        throughput = ThroughputMetrics(window_seconds=60.0)
        
        # Start tracking a request
        throughput.start_request()
        
        # ... process request ...
        
        # End tracking
        throughput.end_request()
        
        # Get metrics
        print(f"RPS: {throughput.get_rps()}")
        print(f"Active: {throughput.get_active_requests()}")
        ```
    """

    def __init__(self, window_seconds: float = 60.0) -> None:
        """
        Initialize throughput metrics.

        Args:
            window_seconds: Time window for RPS calculation
        """
        self._window_seconds = window_seconds
        self._request_times: deque[float] = deque()
        self._active_requests: int = 0
        self._lock = threading.Lock()

    def start_request(self) -> None:
        """
        Mark the start of a request (increments active request count).

        Example:
            ```python
            throughput.start_request()
            try:
                # Process request
                pass
            finally:
                throughput.end_request()
            ```
        """
        with self._lock:
            self._active_requests += 1
            self._request_times.append(time.time())

    def end_request(self) -> None:
        """
        Mark the end of a request (decrements active request count).

        Example:
            ```python
            throughput.start_request()
            try:
                # Process request
                pass
            finally:
                throughput.end_request()
            ```
        """
        with self._lock:
            self._active_requests = max(0, self._active_requests - 1)

    def get_rps(self) -> float:
        """
        Get requests per second over the time window.

        Returns:
            Requests per second

        Example:
            ```python
            rps = throughput.get_rps()
            print(f"Current load: {rps:.1f} req/s")
            ```
        """
        with self._lock:
            current_time = time.time()
            # Remove requests outside the window
            while self._request_times and current_time - self._request_times[0] > self._window_seconds:
                self._request_times.popleft()

            if not self._request_times:
                return 0.0

            # Calculate RPS
            time_span = current_time - self._request_times[0]
            if time_span == 0:
                return 0.0

            return len(self._request_times) / time_span

    def get_active_requests(self) -> int:
        """
        Get number of currently active requests.

        Returns:
            Count of active requests

        Example:
            ```python
            active = throughput.get_active_requests()
            if active > 100:
                print("Warning: High concurrency!")
            ```
        """
        with self._lock:
            return self._active_requests

    def get_stats(self) -> dict[str, Any]:
        """
        Get comprehensive throughput statistics.

        Returns:
            Dictionary with RPS and active request count

        Example:
            ```python
            stats = throughput.get_stats()
            print(f"RPS: {stats['rps']:.1f}")
            print(f"Active: {stats['active_requests']}")
            ```
        """
        return {
            "rps": self.get_rps(),
            "active_requests": self.get_active_requests(),
            "window_seconds": self._window_seconds,
        }


class CostMetrics:
    """
    Tracks cost metrics for workflow execution.

    Supports tracking both actual costs and potential savings from optimizations
    like caching.

    Example:
        ```python
        cost = CostMetrics()
        
        # Record actual cost
        cost.record_cost(0.05)  # $0.05 for API call
        
        # Record savings from cache hit
        cost.record_savings(0.05)  # Saved $0.05 by using cache
        
        # Get metrics
        stats = cost.get_stats()
        print(f"Total cost: ${stats['total_cost']:.2f}")
        print(f"Total savings: ${stats['total_savings']:.2f}")
        print(f"Savings rate: {stats['savings_rate']:.1%}")
        ```
    """

    def __init__(self) -> None:
        """Initialize cost metrics."""
        self._total_cost: float = 0.0
        self._total_savings: float = 0.0
        self._lock = threading.Lock()

    def record_cost(self, cost: float) -> None:
        """
        Record an actual cost.

        Args:
            cost: Cost amount (e.g., in dollars)

        Example:
            ```python
            # Record cost of LLM API call
            cost.record_cost(0.05)
            ```
        """
        with self._lock:
            self._total_cost += cost

    def record_savings(self, savings: float) -> None:
        """
        Record a cost savings.

        Args:
            savings: Savings amount (e.g., in dollars)

        Example:
            ```python
            # Record savings from cache hit
            cost.record_savings(0.05)
            ```
        """
        with self._lock:
            self._total_savings += savings

    def get_total_cost(self) -> float:
        """
        Get total accumulated cost.

        Returns:
            Total cost

        Example:
            ```python
            total = cost.get_total_cost()
            print(f"Total spent: ${total:.2f}")
            ```
        """
        with self._lock:
            return self._total_cost

    def get_total_savings(self) -> float:
        """
        Get total accumulated savings.

        Returns:
            Total savings

        Example:
            ```python
            savings = cost.get_total_savings()
            print(f"Total saved: ${savings:.2f}")
            ```
        """
        with self._lock:
            return self._total_savings

    def get_savings_rate(self) -> float:
        """
        Get savings rate (savings / (cost + savings)).

        Returns:
            Savings rate (0.0 to 1.0)

        Example:
            ```python
            rate = cost.get_savings_rate()
            print(f"Savings rate: {rate:.1%}")
            ```
        """
        with self._lock:
            total = self._total_cost + self._total_savings
            if total == 0:
                return 0.0
            return self._total_savings / total

    def get_stats(self) -> dict[str, float]:
        """
        Get comprehensive cost statistics.

        Returns:
            Dictionary with cost, savings, and savings rate

        Example:
            ```python
            stats = cost.get_stats()
            print(f"Cost: ${stats['total_cost']:.2f}")
            print(f"Savings: ${stats['total_savings']:.2f}")
            print(f"Rate: {stats['savings_rate']:.1%}")
            ```
        """
        return {
            "total_cost": self.get_total_cost(),
            "total_savings": self.get_total_savings(),
            "savings_rate": self.get_savings_rate(),
        }


class EnhancedMetricsCollector:
    """
    Unified metrics collector integrating all Phase 3 metrics types.

    Provides a single interface for collecting percentiles, SLOs, throughput,
    and cost metrics across all primitives.

    Example:
        ```python
        collector = get_enhanced_metrics_collector()
        
        # Configure SLO for a primitive
        collector.configure_slo(
            "api_call",
            SLOConfig(name="api_latency", target=0.95, threshold_ms=1000.0)
        )
        
        # Record execution
        collector.record_execution(
            primitive_name="api_call",
            duration_ms=450.0,
            success=True,
            cost=0.05
        )
        
        # Get comprehensive metrics
        stats = collector.get_all_metrics("api_call")
        ```
    """

    def __init__(self) -> None:
        """Initialize enhanced metrics collector."""
        self._percentiles: dict[str, PercentileMetrics] = {}
        self._slos: dict[str, SLOMetrics] = {}
        self._throughput: dict[str, ThroughputMetrics] = {}
        self._costs: dict[str, CostMetrics] = {}
        self._basic_metrics: MetricsCollector = MetricsCollector()
        self._lock = threading.Lock()

    def configure_slo(self, primitive_name: str, slo_config: SLOConfig) -> None:
        """
        Configure an SLO for a primitive.

        Args:
            primitive_name: Name of the primitive
            slo_config: SLO configuration

        Example:
            ```python
            collector.configure_slo(
                "api_call",
                SLOConfig(name="latency", target=0.95, threshold_ms=1000.0)
            )
            ```
        """
        with self._lock:
            self._slos[primitive_name] = SLOMetrics(slo_config)

    def record_execution(
        self,
        primitive_name: str,
        duration_ms: float,
        success: bool,
        error_type: str | None = None,
        cost: float | None = None,
    ) -> None:
        """
        Record a primitive execution with enhanced metrics.

        Args:
            primitive_name: Name of the primitive
            duration_ms: Execution duration in milliseconds
            success: Whether execution succeeded
            error_type: Type of error if failed
            cost: Optional cost of execution

        Example:
            ```python
            collector.record_execution(
                primitive_name="llm_call",
                duration_ms=1250.0,
                success=True,
                cost=0.05
            )
            ```
        """
        with self._lock:
            # Initialize metrics objects if needed
            if primitive_name not in self._percentiles:
                self._percentiles[primitive_name] = PercentileMetrics()
            if primitive_name not in self._throughput:
                self._throughput[primitive_name] = ThroughputMetrics()
            if primitive_name not in self._costs:
                self._costs[primitive_name] = CostMetrics()

        # Record in basic metrics
        self._basic_metrics.record_execution(primitive_name, duration_ms, success, error_type)

        # Record latency percentiles
        self._percentiles[primitive_name].record(duration_ms)

        # Record SLO if configured
        if primitive_name in self._slos:
            self._slos[primitive_name].record_request(success, duration_ms)

        # Record throughput (end request)
        self._throughput[primitive_name].end_request()

        # Record cost if provided
        if cost is not None:
            self._costs[primitive_name].record_cost(cost)

    def start_request(self, primitive_name: str) -> None:
        """
        Mark the start of a request for throughput tracking.

        Args:
            primitive_name: Name of the primitive

        Example:
            ```python
            collector.start_request("api_call")
            try:
                # Execute primitive
                pass
            finally:
                collector.record_execution(...)
            ```
        """
        with self._lock:
            if primitive_name not in self._throughput:
                self._throughput[primitive_name] = ThroughputMetrics()

        self._throughput[primitive_name].start_request()

    def record_savings(self, primitive_name: str, savings: float) -> None:
        """
        Record cost savings (e.g., from cache hits).

        Args:
            primitive_name: Name of the primitive
            savings: Savings amount

        Example:
            ```python
            # Record savings from cache hit
            collector.record_savings("api_call", 0.05)
            ```
        """
        with self._lock:
            if primitive_name not in self._costs:
                self._costs[primitive_name] = CostMetrics()

        self._costs[primitive_name].record_savings(savings)

    def get_all_metrics(self, primitive_name: str) -> dict[str, Any]:
        """
        Get comprehensive metrics for a primitive.

        Args:
            primitive_name: Name of the primitive

        Returns:
            Dictionary with all metrics types

        Example:
            ```python
            metrics = collector.get_all_metrics("api_call")
            print(f"p95 latency: {metrics['percentiles']['p95']}ms")
            print(f"SLO compliance: {metrics['slo']['compliance']:.2%}")
            print(f"RPS: {metrics['throughput']['rps']}")
            print(f"Total cost: ${metrics['cost']['total_cost']:.2f}")
            ```
        """
        result: dict[str, Any] = {
            "basic": self._basic_metrics.get_metrics(primitive_name),
        }

        if primitive_name in self._percentiles:
            result["percentiles"] = self._percentiles[primitive_name].get_stats()

        if primitive_name in self._slos:
            result["slo"] = self._slos[primitive_name].get_stats()

        if primitive_name in self._throughput:
            result["throughput"] = self._throughput[primitive_name].get_stats()

        if primitive_name in self._costs:
            result["cost"] = self._costs[primitive_name].get_stats()

        return result


# Global enhanced metrics collector
_enhanced_metrics_collector: EnhancedMetricsCollector | None = None
_collector_lock = threading.Lock()


def get_enhanced_metrics_collector() -> EnhancedMetricsCollector:
    """
    Get the global enhanced metrics collector (thread-safe singleton).

    Returns:
        Global EnhancedMetricsCollector instance

    Example:
        ```python
        collector = get_enhanced_metrics_collector()
        collector.record_execution("my_primitive", 123.4, True)
        metrics = collector.get_all_metrics("my_primitive")
        ```
    """
    global _enhanced_metrics_collector
    if _enhanced_metrics_collector is None:
        with _collector_lock:
            # Double-check locking pattern
            if _enhanced_metrics_collector is None:
                _enhanced_metrics_collector = EnhancedMetricsCollector()
    return _enhanced_metrics_collector


# Global metrics collector (original)
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
