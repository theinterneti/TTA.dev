"""Tests for CircuitBreakerPrimitive.

Comprehensive test suite covering all three circuit states and transitions.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.recovery.circuit_breaker_primitive import (
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerPrimitive,
    CircuitState,
)


class UnreliablePrimitive(WorkflowPrimitive[Any, Any]):
    """Test primitive that can be configured to fail."""

    def __init__(self) -> None:
        """Initialize with controllable failure."""
        self.should_fail = False
        self.call_count = 0
        self.last_input: Any = None

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """Execute with optional failure."""
        self.call_count += 1
        self.last_input = input_data

        if self.should_fail:
            raise ValueError(f"Intentional failure #{self.call_count}")

        return {"result": f"success_{self.call_count}", "input": input_data}


@pytest.fixture
def unreliable_primitive() -> UnreliablePrimitive:
    """Create test primitive."""
    return UnreliablePrimitive()


@pytest.fixture
def context() -> WorkflowContext:
    """Create workflow context."""
    return WorkflowContext(workflow_id="test-circuit-breaker")


class TestCircuitBreakerStates:
    """Test circuit breaker state transitions."""

    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self, unreliable_primitive: UnreliablePrimitive) -> None:
        """Circuit breaker should start in CLOSED state."""
        # Arrange
        circuit = CircuitBreakerPrimitive(unreliable_primitive)

        # Act & Assert
        assert circuit.state == CircuitState.CLOSED
        assert circuit.failure_count == 0
        assert circuit.success_count == 0

    @pytest.mark.asyncio
    async def test_closed_state_allows_requests(
        self,
        unreliable_primitive: UnreliablePrimitive,
        context: WorkflowContext,
    ) -> None:
        """CLOSED state should allow requests through."""
        # Arrange
        circuit = CircuitBreakerPrimitive(unreliable_primitive)

        # Act
        result = await circuit.execute({"test": "data"}, context)

        # Assert
        assert result["result"] == "success_1"
        assert circuit.state == CircuitState.CLOSED
        assert unreliable_primitive.call_count == 1

    @pytest.mark.asyncio
    async def test_transition_to_open_after_threshold_failures(
        self,
        unreliable_primitive: UnreliablePrimitive,
        context: WorkflowContext,
    ) -> None:
        """Circuit should open after failure_threshold consecutive failures."""
        # Arrange
        circuit = CircuitBreakerPrimitive(
            unreliable_primitive,
            config=CircuitBreakerConfig(failure_threshold=3),
        )
        unreliable_primitive.should_fail = True

        # Act - cause 3 failures
        for i in range(3):
            with pytest.raises(ValueError):
                await circuit.execute({"attempt": i}, context)

        # Assert
        assert circuit.state == CircuitState.OPEN
        assert circuit.failure_count == 3
        assert unreliable_primitive.call_count == 3

    @pytest.mark.asyncio
    async def test_open_state_fails_immediately(
        self,
        unreliable_primitive: UnreliablePrimitive,
        context: WorkflowContext,
    ) -> None:
        """OPEN state should fail immediately without calling primitive."""
        # Arrange
        circuit = CircuitBreakerPrimitive(
            unreliable_primitive,
            config=CircuitBreakerConfig(failure_threshold=2),
        )
        unreliable_primitive.should_fail = True

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await circuit.execute({"data": "test"}, context)

        call_count_when_open = unreliable_primitive.call_count

        # Act - try to call when circuit is open
        with pytest.raises(CircuitBreakerError) as exc_info:
            await circuit.execute({"data": "test"}, context)

        # Assert
        assert circuit.state == CircuitState.OPEN
        assert unreliable_primitive.call_count == call_count_when_open  # No new calls
        assert exc_info.value.failure_count == 2
        assert "OPEN" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_transition_to_half_open_after_recovery_timeout(
        self,
        unreliable_primitive: UnreliablePrimitive,
        context: WorkflowContext,
    ) -> None:
        """Circuit should transition to HALF_OPEN after recovery_timeout."""
        # Arrange
        circuit = CircuitBreakerPrimitive(
            unreliable_primitive,
            config=CircuitBreakerConfig(
                failure_threshold=2,
                recovery_timeout=0.1,  # Short timeout for testing
            ),
        )
        unreliable_primitive.should_fail = True

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await circuit.execute({"data": "test"}, context)

        assert circuit.state == CircuitState.OPEN

        # Act - wait for recovery timeout
        await asyncio.sleep(0.15)

        # Now fix the primitive
        unreliable_primitive.should_fail = False

        # Try again - should transition to HALF_OPEN and succeed
        result = await circuit.execute({"data": "test"}, context)

        # Assert
        assert result["result"] == "success_3"
        assert circuit.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success_increments_counter(
        self,
        unreliable_primitive: UnreliablePrimitive,
        context: WorkflowContext,
    ) -> None:
        """Successful calls in HALF_OPEN should increment success counter."""
        # Arrange
        circuit = CircuitBreakerPrimitive(
            unreliable_primitive,
            config=CircuitBreakerConfig(
                failure_threshold=2,
                recovery_timeout=0.1,
                success_threshold=3,
            ),
        )
        unreliable_primitive.should_fail = True

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await circuit.execute({"data": "test"}, context)

        # Wait and transition to HALF_OPEN
        await asyncio.sleep(0.15)
        unreliable_primitive.should_fail = False

        # Act - make successful calls in HALF_OPEN
        await circuit.execute({"data": "test1"}, context)
        assert circuit.state == CircuitState.HALF_OPEN
        assert circuit.success_count == 1

        await circuit.execute({"data": "test2"}, context)
        assert circuit.state == CircuitState.HALF_OPEN
        assert circuit.success_count == 2

    @pytest.mark.asyncio
    async def test_transition_to_closed_after_success_threshold(
        self,
        unreliable_primitive: UnreliablePrimitive,
        context: WorkflowContext,
    ) -> None:
        """Circuit should close after success_threshold successes in HALF_OPEN."""
        # Arrange
        circuit = CircuitBreakerPrimitive(
            unreliable_primitive,
            config=CircuitBreakerConfig(
                failure_threshold=2,
                recovery_timeout=0.1,
                success_threshold=2,
            ),
        )
        unreliable_primitive.should_fail = True

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await circuit.execute({"data": "test"}, context)

        # Transition to HALF_OPEN
        await asyncio.sleep(0.15)
        unreliable_primitive.should_fail = False

        # Act - reach success threshold
        await circuit.execute({"data": "test1"}, context)
        assert circuit.state == CircuitState.HALF_OPEN

        await circuit.execute({"data": "test2"}, context)

        # Assert
        assert circuit.state == CircuitState.CLOSED
        assert circuit.success_count == 0  # Reset
        assert circuit.failure_count == 0  # Reset

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(
        self,
        unreliable_primitive: UnreliablePrimitive,
        context: WorkflowContext,
    ) -> None:
        """Any failure in HALF_OPEN should reopen the circuit."""
        # Arrange
        circuit = CircuitBreakerPrimitive(
            unreliable_primitive,
            config=CircuitBreakerConfig(
                failure_threshold=2,
                recovery_timeout=0.1,
            ),
        )
        unreliable_primitive.should_fail = True

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await circuit.execute({"data": "test"}, context)

        # Transition to HALF_OPEN
        await asyncio.sleep(0.15)

        # Act - fail in HALF_OPEN (primitive still failing)
        with pytest.raises(ValueError):
            await circuit.execute({"data": "test"}, context)

        # Assert
        assert circuit.state == CircuitState.OPEN
        assert circuit.success_count == 0  # Reset


class TestCircuitBreakerConfiguration:
    """Test configuration validation and behavior."""

    def test_config_validation_failure_threshold(self) -> None:
        """Config should validate failure_threshold."""
        with pytest.raises(ValueError, match="failure_threshold must be positive"):
            CircuitBreakerConfig(failure_threshold=0)

    def test_config_validation_recovery_timeout(self) -> None:
        """Config should validate recovery_timeout."""
        with pytest.raises(ValueError, match="recovery_timeout must be positive"):
            CircuitBreakerConfig(recovery_timeout=-1)

    def test_config_validation_success_threshold(self) -> None:
        """Config should validate success_threshold."""
        with pytest.raises(ValueError, match="success_threshold must be positive"):
            CircuitBreakerConfig(success_threshold=0)

    @pytest.mark.asyncio
    async def test_custom_failure_threshold(
        self,
        unreliable_primitive: UnreliablePrimitive,
        context: WorkflowContext,
    ) -> None:
        """Custom failure_threshold should be respected."""
        # Arrange
        circuit = CircuitBreakerPrimitive(
            unreliable_primitive,
            config=CircuitBreakerConfig(failure_threshold=5),
        )
        unreliable_primitive.should_fail = True

        # Act - cause 4 failures (below threshold)
        for _ in range(4):
            with pytest.raises(ValueError):
                await circuit.execute({"data": "test"}, context)

        # Assert - should still be closed
        assert circuit.state == CircuitState.CLOSED
        assert circuit.failure_count == 4

        # Act - 5th failure should open
        with pytest.raises(ValueError):
            await circuit.execute({"data": "test"}, context)

        assert circuit.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_expected_exception_filtering(
        self,
        unreliable_primitive: UnreliablePrimitive,
        context: WorkflowContext,
    ) -> None:
        """Only expected_exception should trigger circuit breaker."""
        # Arrange
        circuit = CircuitBreakerPrimitive(
            unreliable_primitive,
            config=CircuitBreakerConfig(
                failure_threshold=2,
                expected_exception=ValueError,
            ),
        )

        # Act - cause ValueError failures
        unreliable_primitive.should_fail = True
        for _ in range(2):
            with pytest.raises(ValueError):
                await circuit.execute({"data": "test"}, context)

        # Assert
        assert circuit.state == CircuitState.OPEN


class TestCircuitBreakerManualReset:
    """Test manual reset functionality."""

    @pytest.mark.asyncio
    async def test_manual_reset(
        self,
        unreliable_primitive: UnreliablePrimitive,
        context: WorkflowContext,
    ) -> None:
        """Manual reset should close circuit immediately."""
        # Arrange
        circuit = CircuitBreakerPrimitive(
            unreliable_primitive,
            config=CircuitBreakerConfig(failure_threshold=2),
        )
        unreliable_primitive.should_fail = True

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await circuit.execute({"data": "test"}, context)

        assert circuit.state == CircuitState.OPEN

        # Act
        circuit.reset()

        # Assert
        assert circuit.state == CircuitState.CLOSED
        assert circuit.failure_count == 0
        assert circuit.success_count == 0

        # Can execute again
        unreliable_primitive.should_fail = False
        result = await circuit.execute({"data": "test"}, context)
        assert result["result"] == "success_3"


class TestCircuitBreakerEdgeCases:
    """Test edge cases and concurrent scenarios."""

    @pytest.mark.asyncio
    async def test_success_in_closed_resets_failure_count(
        self,
        unreliable_primitive: UnreliablePrimitive,
        context: WorkflowContext,
    ) -> None:
        """Success in CLOSED state should reset failure count."""
        # Arrange
        circuit = CircuitBreakerPrimitive(
            unreliable_primitive,
            config=CircuitBreakerConfig(failure_threshold=3),
        )
        unreliable_primitive.should_fail = True

        # Act - cause 2 failures
        for _ in range(2):
            with pytest.raises(ValueError):
                await circuit.execute({"data": "test"}, context)

        assert circuit.failure_count == 2

        # Success should reset
        unreliable_primitive.should_fail = False
        await circuit.execute({"data": "test"}, context)

        # Assert
        assert circuit.failure_count == 0
        assert circuit.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_multiple_open_attempts_before_timeout(
        self,
        unreliable_primitive: UnreliablePrimitive,
        context: WorkflowContext,
    ) -> None:
        """Multiple attempts when OPEN before timeout should all fail immediately."""
        # Arrange
        circuit = CircuitBreakerPrimitive(
            unreliable_primitive,
            config=CircuitBreakerConfig(
                failure_threshold=2,
                recovery_timeout=1.0,
            ),
        )
        unreliable_primitive.should_fail = True

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await circuit.execute({"data": "test"}, context)

        initial_call_count = unreliable_primitive.call_count

        # Act - try multiple times before timeout
        for _ in range(5):
            with pytest.raises(CircuitBreakerError):
                await circuit.execute({"data": "test"}, context)

        # Assert - no additional calls to primitive
        assert unreliable_primitive.call_count == initial_call_count
        assert circuit.state == CircuitState.OPEN
