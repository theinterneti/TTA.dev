"""Metrics collection for workflow primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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


# Global metrics collector
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
