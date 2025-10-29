"""Metrics collection for workflow primitives."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


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
    """
    Collects metrics for all primitives with cardinality controls.

    Implements cardinality limiting to prevent metric explosion from
    high-cardinality label values (e.g., user IDs, trace IDs).

    Example:
        ```python
        from tta_dev_primitives.observability.metrics import MetricsCollector

        collector = MetricsCollector(max_label_values=100)

        # Record executions
        collector.record_execution("my_primitive", 150.0, success=True)
        collector.record_execution("my_primitive", 200.0, success=False, error_type="ValueError")

        # Get metrics
        metrics = collector.get_metrics("my_primitive")
        print(f"Success rate: {metrics['success_rate']}")

        # Get cardinality stats
        stats = collector.get_cardinality_stats()
        print(f"Unique primitives: {stats['unique_primitives']}")
        ```
    """

    def __init__(
        self,
        max_label_values: int = 100,
        hash_high_cardinality: bool = True,
    ) -> None:
        """
        Initialize metrics collector with cardinality controls.

        Args:
            max_label_values: Maximum unique label values per label key
            hash_high_cardinality: Hash high-cardinality values to limit growth
        """
        self._metrics: dict[str, PrimitiveMetrics] = {}
        self.max_label_values = max_label_values
        self.hash_high_cardinality = hash_high_cardinality

        # Track cardinality
        self._label_values: dict[str, set[str]] = {}
        self._dropped_labels: dict[str, int] = {}  # Count of dropped labels per key

    def record_execution(
        self,
        primitive_name: str,
        duration_ms: float,
        success: bool,
        error_type: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> None:
        """
        Record a primitive execution with cardinality control.

        Args:
            primitive_name: Name of the primitive
            duration_ms: Execution duration in milliseconds
            success: Whether execution succeeded
            error_type: Type of error if failed
            labels: Optional additional labels (subject to cardinality limits)
        """
        # Apply cardinality control to primitive_name
        primitive_name = self._apply_cardinality_control("primitive_name", primitive_name)

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
                # Apply cardinality control to error_type
                error_type = self._apply_cardinality_control("error_type", error_type)
                metrics.error_counts[error_type] = metrics.error_counts.get(error_type, 0) + 1

    def _apply_cardinality_control(self, label_key: str, label_value: str) -> str:
        """
        Apply cardinality control to a label value.

        If the number of unique values for this label exceeds max_label_values,
        either hash the value or use a placeholder.

        Args:
            label_key: The label key (e.g., "primitive_name", "error_type")
            label_value: The label value to control

        Returns:
            Original value, hashed value, or placeholder
        """
        # Initialize tracking for this label
        if label_key not in self._label_values:
            self._label_values[label_key] = set()

        # Check if value already tracked
        if label_value in self._label_values[label_key]:
            return label_value

        # Check cardinality limit
        if len(self._label_values[label_key]) >= self.max_label_values:
            # Limit exceeded
            self._dropped_labels[label_key] = self._dropped_labels.get(label_key, 0) + 1

            if self.hash_high_cardinality:
                # Hash the value to 8 hex chars
                hash_value = hashlib.md5(label_value.encode()).hexdigest()[:8]
                controlled_value = f"{label_key}_hash_{hash_value}"
                logger.debug(
                    f"Cardinality limit reached for {label_key}: "
                    f"hashing value '{label_value}' -> '{controlled_value}'"
                )
                return controlled_value
            else:
                # Use placeholder
                logger.debug(
                    f"Cardinality limit reached for {label_key}: "
                    f"dropping value '{label_value}'"
                )
                return f"{label_key}_other"

        # Under limit, track and return original
        self._label_values[label_key].add(label_value)
        return label_value

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
        """Reset all metrics and cardinality tracking."""
        self._metrics.clear()
        self._label_values.clear()
        self._dropped_labels.clear()

    def get_cardinality_stats(self) -> dict[str, Any]:
        """
        Get cardinality statistics for all labels.

        Returns:
            Statistics including unique values per label and dropped counts

        Example:
            ```python
            stats = collector.get_cardinality_stats()
            print(f"Unique primitives: {stats['label_cardinality']['primitive_name']}")
            print(f"Dropped labels: {stats['dropped_labels']}")
            ```
        """
        return {
            "label_cardinality": {
                label_key: len(values) for label_key, values in self._label_values.items()
            },
            "dropped_labels": self._dropped_labels.copy(),
            "max_label_values": self.max_label_values,
            "hash_high_cardinality": self.hash_high_cardinality,
            "total_labels": sum(len(values) for values in self._label_values.values()),
            "unique_primitives": len(self._metrics),
        }


# Global metrics collector
_metrics_collector: MetricsCollector | None = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
