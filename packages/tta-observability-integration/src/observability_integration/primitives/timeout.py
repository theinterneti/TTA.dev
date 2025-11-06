"""
TimeoutPrimitive - Timeout enforcement workflow primitive.

Wraps async operations with configurable timeouts to prevent hanging workflows.
Tracks timeout rates and execution times for reliability monitoring.
"""

from __future__ import annotations

import asyncio
import builtins
import logging
import time
from typing import Any

from tta_dev_primitives.core.base import (
    WorkflowContext,
    WorkflowPrimitive,
)

from ..apm_setup import get_meter

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Raised when operation exceeds timeout."""

    pass


class TimeoutPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Enforce timeouts on primitive execution.

    Wraps a primitive with timeout enforcement to prevent hanging workflows.
    Provides graceful degradation with optional grace period.

    Example:
        >>> from observability_integration.primitives import TimeoutPrimitive
        >>>
        >>> # Wrap slow operation with 30s timeout
        >>> timeout_wrapper = TimeoutPrimitive(
        ...     primitive=SlowLLMPrimitive(),
        ...     timeout_seconds=30.0,
        ...     grace_period_seconds=5.0,
        ... )
        >>>
        >>> # Use in workflow
        >>> try:
        ...     result = await timeout_wrapper.execute(input_data, context)
        ... except TimeoutError:
        ...     # Handle timeout gracefully
        ...     result = fallback_response()

    Metrics:
        - timeout_successes_total{operation}: Operations completed in time
        - timeout_failures_total{operation}: Operations that timed out
        - timeout_execution_seconds{operation}: Execution time distribution
        - timeout_rate{operation}: Timeout rate (0.0-1.0)
    """

    def __init__(
        self,
        primitive: WorkflowPrimitive,
        timeout_seconds: float,
        grace_period_seconds: float = 5.0,
        operation_name: str | None = None,
    ):
        """
        Initialize timeout primitive.

        Args:
            primitive: Primitive to wrap with timeout enforcement
            timeout_seconds: Max execution time before timeout
            grace_period_seconds: Additional time before hard cancellation
            operation_name: Name for metrics (default: primitive class name)

        Raises:
            ValueError: If timeout_seconds <= 0
        """
        if timeout_seconds <= 0:
            raise ValueError(f"timeout_seconds must be > 0, got {timeout_seconds}")

        self.primitive = primitive
        self.timeout_seconds = timeout_seconds
        self.grace_period_seconds = grace_period_seconds
        self.operation_name = operation_name or primitive.__class__.__name__

        # Track statistics for timeout rate calculation
        self._total_successes = 0
        self._total_failures = 0

        # Initialize metrics (gracefully handles meter=None)
        meter = get_meter(__name__)
        if meter:
            self._successes_counter = meter.create_counter(
                name="timeout_successes_total",
                description="Operations completed within timeout",
                unit="1",
            )
            self._failures_counter = meter.create_counter(
                name="timeout_failures_total",
                description="Operations that exceeded timeout",
                unit="1",
            )
            self._execution_histogram = meter.create_histogram(
                name="timeout_execution_seconds",
                description="Execution time for timeout-wrapped operations",
                unit="s",
            )

            # Observable gauge for timeout rate
            def get_timeout_rate() -> float:
                total = self._total_successes + self._total_failures
                return self._total_failures / total if total > 0 else 0.0

            self._timeout_rate_gauge = meter.create_observable_gauge(
                name="timeout_rate",
                description="Timeout failure rate (0.0-1.0)",
                callbacks=[  # type: ignore  # OpenTelemetry CallbackT variance
                    lambda _: [(get_timeout_rate(), {"operation": self.operation_name})]
                ],
            )
        else:
            self._successes_counter = None
            self._failures_counter = None
            self._execution_histogram = None
            self._timeout_rate_gauge = None

        logger.info(
            f"TimeoutPrimitive initialized for '{self.operation_name}' "
            f"(timeout: {timeout_seconds}s, grace: {grace_period_seconds}s)"
        )

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute with timeout enforcement.

        Args:
            input_data: Input data for the workflow
            context: Workflow execution context

        Returns:
            Result from wrapped primitive

        Raises:
            TimeoutError: If execution exceeds timeout + grace period
            Exception: Any exception from the wrapped primitive
        """
        start_time = time.time()

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self.primitive.execute(input_data, context),
                timeout=self.timeout_seconds + self.grace_period_seconds,
            )

            # Success - completed within timeout
            self._total_successes += 1

            duration = time.time() - start_time

            if self._successes_counter:
                self._successes_counter.add(1, {"operation": self.operation_name})

            if self._execution_histogram:
                self._execution_histogram.record(
                    duration, {"operation": self.operation_name}
                )

            # Warn if operation completed but was slow (within grace period)
            if duration > self.timeout_seconds:
                logger.warning(
                    f"'{self.operation_name}' completed in {duration:.2f}s "
                    f"(exceeded timeout of {self.timeout_seconds}s but within "
                    f"grace period of {self.grace_period_seconds}s)"
                )
            else:
                logger.debug(
                    f"'{self.operation_name}' completed in {duration:.2f}s "
                    f"(within timeout of {self.timeout_seconds}s)"
                )

            return result

        except builtins.TimeoutError as e:
            # Timeout - operation exceeded timeout + grace period
            self._total_failures += 1

            duration = time.time() - start_time

            if self._failures_counter:
                self._failures_counter.add(1, {"operation": self.operation_name})

            if self._execution_histogram:
                self._execution_histogram.record(
                    duration, {"operation": self.operation_name}
                )

            logger.error(
                f"'{self.operation_name}' TIMEOUT after {duration:.2f}s "
                f"(timeout: {self.timeout_seconds}s, "
                f"grace: {self.grace_period_seconds}s)"
            )

            # Wrap in our custom TimeoutError for clarity
            raise TimeoutError(
                f"Operation '{self.operation_name}' exceeded timeout of "
                f"{self.timeout_seconds}s (total wait: {duration:.2f}s)"
            ) from e

        except Exception:
            # Other exception - still count as success (didn't timeout)
            # But record execution time if we have it
            self._total_successes += 1
            duration = time.time() - start_time

            if self._successes_counter:
                self._successes_counter.add(1, {"operation": self.operation_name})

            if self._execution_histogram:
                self._execution_histogram.record(
                    duration, {"operation": self.operation_name}
                )

            # Re-raise the original exception
            raise

    def get_stats(self) -> dict[str, Any]:
        """
        Get current timeout statistics.

        Returns:
            Dictionary with successes, failures, total, and timeout_rate
        """
        total = self._total_successes + self._total_failures
        timeout_rate = self._total_failures / total if total > 0 else 0.0

        return {
            "operation": self.operation_name,
            "successes": self._total_successes,
            "failures": self._total_failures,
            "total": total,
            "timeout_rate": timeout_rate,
            "timeout_seconds": self.timeout_seconds,
            "grace_period_seconds": self.grace_period_seconds,
        }

    def __repr__(self) -> str:
        """String representation of timeout wrapper."""
        stats = self.get_stats()
        return (
            f"TimeoutPrimitive(operation='{self.operation_name}', "
            f"timeout={self.timeout_seconds}s, "
            f"timeout_rate={stats['timeout_rate']:.1%}, "
            f"total={stats['total']})"
        )
