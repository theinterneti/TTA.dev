"""Circuit Breaker Primitive for fault tolerance.

Implements the circuit breaker pattern to prevent cascading failures in workflows.

# See: [[TTA.dev/Primitives/CircuitBreakerPrimitive]]
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.logging import get_logger

logger = get_logger(__name__)


class CircuitState(StrEnum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing immediately
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    failure_threshold: int = 5
    """Number of consecutive failures before opening circuit"""

    recovery_timeout: float = 60.0
    """Seconds to wait before testing recovery (OPEN -> HALF_OPEN)"""

    success_threshold: int = 2
    """Number of consecutive successes in HALF_OPEN to close circuit"""

    expected_exception: type[Exception] = Exception
    """Exception type to catch (others pass through)"""

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.failure_threshold <= 0:
            raise ValueError("failure_threshold must be positive")
        if self.recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be positive")
        if self.success_threshold <= 0:
            raise ValueError("success_threshold must be positive")


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, failure_count: int, last_error: Exception | None = None):
        """Initialize error."""
        self.failure_count = failure_count
        self.last_error = last_error
        super().__init__(f"Circuit breaker is OPEN after {failure_count} consecutive failures")


class CircuitBreakerPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Implements circuit breaker pattern to prevent cascading failures.

    The circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail immediately
    - HALF_OPEN: Testing if the underlying service has recovered

    State transitions:
    - CLOSED -> OPEN: After failure_threshold consecutive failures
    - OPEN -> HALF_OPEN: After recovery_timeout seconds
    - HALF_OPEN -> CLOSED: After success_threshold consecutive successes
    - HALF_OPEN -> OPEN: On any failure

    Example:
        ```python
        from primitives import CircuitBreakerPrimitive, WorkflowContext
        from ttadev.primitives.recovery.circuit_breaker_primitive import (
            CircuitBreakerConfig,
        )

        # Wrap an unreliable primitive
        circuit = CircuitBreakerPrimitive(
            primitive=unreliable_service,
            config=CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30.0,
                success_threshold=2
            )
        )

        # Execute through circuit breaker
        try:
            result = await circuit.execute(data, context)
        except CircuitBreakerError:
            print("Circuit is open, using fallback")
            result = fallback_value
        ```
    """

    def __init__(
        self,
        primitive: WorkflowPrimitive[Any, Any],
        config: CircuitBreakerConfig | None = None,
    ) -> None:
        """
        Initialize circuit breaker primitive.

        Args:
            primitive: The primitive to protect with circuit breaker
            config: Circuit breaker configuration
        """
        self.primitive = primitive
        self.config = config or CircuitBreakerConfig()

        # State tracking
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._last_error: Exception | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get consecutive failure count."""
        return self._failure_count

    @property
    def success_count(self) -> int:
        """Get consecutive success count in HALF_OPEN state."""
        return self._success_count

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute primitive through circuit breaker.

        Args:
            input_data: Input data for the primitive
            context: Workflow context

        Returns:
            Output from the primitive

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If primitive execution fails
        """
        # Check if we should attempt recovery (before acquiring lock)
        should_attempt = False
        if self._state == CircuitState.OPEN and self._should_attempt_reset():
            should_attempt = True

        async with self._lock:
            # Transition to HALF_OPEN if recovery timeout has passed
            if should_attempt and self._state == CircuitState.OPEN:
                logger.info("Circuit breaker transitioning to HALF_OPEN for testing")
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
            elif self._state == CircuitState.OPEN:
                logger.warning(
                    f"Circuit breaker is OPEN, failing immediately "
                    f"(failures: {self._failure_count})"
                )
                raise CircuitBreakerError(self._failure_count, self._last_error)

        # Execute the primitive
        try:
            result = await self.primitive.execute(input_data, context)
            await self._on_success()
            return result
        except self.config.expected_exception as e:
            await self._on_failure(e)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return True
        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.config.recovery_timeout

    async def _on_success(self) -> None:
        """Handle successful execution."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.info(
                    f"Circuit breaker success in HALF_OPEN "
                    f"({self._success_count}/{self.config.success_threshold})"
                )

                if self._success_count >= self.config.success_threshold:
                    logger.info("Circuit breaker closing after successful recovery")
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    self._last_error = None
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0
                self._last_error = None

    async def _on_failure(self, error: Exception) -> None:
        """Handle failed execution."""
        async with self._lock:
            self._last_error = error
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN reopens the circuit
                logger.warning("Circuit breaker reopening after HALF_OPEN failure")
                self._state = CircuitState.OPEN
                self._success_count = 0
            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                logger.warning(
                    f"Circuit breaker failure {self._failure_count}/{self.config.failure_threshold}"
                )

                if self._failure_count >= self.config.failure_threshold:
                    logger.error(
                        f"Circuit breaker opening after {self._failure_count} consecutive failures"
                    )
                    self._state = CircuitState.OPEN

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._last_error = None
        logger.info("Circuit breaker manually reset to CLOSED")
