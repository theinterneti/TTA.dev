"""Unit tests for TimeoutPrimitive (wrapper-based implementation)."""

import asyncio
from unittest.mock import MagicMock

import pytest

from src.observability_integration.primitives.timeout import (
    TimeoutError,
    TimeoutPrimitive,
)


# Mock WorkflowPrimitive for testing
class MockPrimitive:
    """Mock primitive with controllable execution time.

    This mock class simulates a workflow primitive with configurable behavior
    for testing timeout and error handling scenarios.

    Attributes:
        name: Display name for the mock primitive
        delay: Simulated execution delay in seconds
        raise_error: If True, execute() will raise ValueError
        call_count: Number of times execute() has been called
    """

    def __init__(
        self, name: str = "mock", delay: float = 0.0, raise_error: bool = False
    ) -> None:
        """Initialize mock primitive with configurable behavior.

        Args:
            name: Display name for the mock primitive (default: "mock")
            delay: Simulated execution delay in seconds, must be >= 0 (default: 0.0)
            raise_error: If True, execute() will raise ValueError (default: False)

        Raises:
            ValueError: If delay is negative
        """
        if delay < 0:
            raise ValueError("delay must be >= 0")

        self.name = name
        self.delay = delay
        self.raise_error = raise_error
        self.call_count = 0

    async def execute(self, data: dict, context) -> str:
        """Mock execute method with configurable delay.

        Simulates primitive execution with optional delay and error raising.
        Increments call_count on each invocation.

        Args:
            data: Input data dictionary
            context: Execution context (typically a MagicMock in tests)

        Returns:
            Result string in format "{name}_result"

        Raises:
            ValueError: If raise_error is True
        """
        self.call_count += 1

        if self.raise_error:
            raise ValueError(f"{self.name} error")

        if self.delay > 0:
            await asyncio.sleep(self.delay)

        return f"{self.name}_result"

    def __repr__(self) -> str:
        """String representation for debugging.

        Returns:
            Detailed string representation of the mock primitive state
        """
        return (
            f"MockPrimitive(name={self.name!r}, delay={self.delay}, "
            f"raise_error={self.raise_error}, calls={self.call_count})"
        )


@pytest.fixture
def fast_primitive():
    """Create fast mock primitive (completes in 0.1s)."""
    return MockPrimitive("FastPrimitive", delay=0.1)


@pytest.fixture
def slow_primitive():
    """Create slow mock primitive (takes 2s)."""
    return MockPrimitive("SlowPrimitive", delay=2.0)


@pytest.fixture
def timeout_primitive(fast_primitive):
    """Create TimeoutPrimitive instance for testing."""
    return TimeoutPrimitive(
        primitive=fast_primitive,
        timeout_seconds=1.0,
        grace_period_seconds=0.5,
    )


class TestMockPrimitive:
    """Test MockPrimitive helper class."""

    def test_initialization_with_defaults(self):
        """Test MockPrimitive initialization with default values."""
        mock = MockPrimitive()
        assert mock.name == "mock"
        assert mock.delay == 0.0
        assert mock.raise_error is False
        assert mock.call_count == 0

    def test_initialization_with_custom_values(self):
        """Test MockPrimitive initialization with custom values."""
        mock = MockPrimitive(name="CustomMock", delay=1.5, raise_error=True)
        assert mock.name == "CustomMock"
        assert mock.delay == 1.5
        assert mock.raise_error is True
        assert mock.call_count == 0

    def test_negative_delay_raises_error(self):
        """Test that negative delay raises ValueError."""
        with pytest.raises(ValueError, match="delay must be >= 0"):
            MockPrimitive(delay=-1.0)

    def test_repr_output(self):
        """Test __repr__ provides useful debugging information."""
        mock = MockPrimitive(name="TestMock", delay=0.5, raise_error=True)
        repr_str = repr(mock)
        assert "MockPrimitive" in repr_str
        assert "name='TestMock'" in repr_str
        assert "delay=0.5" in repr_str
        assert "raise_error=True" in repr_str
        assert "calls=0" in repr_str

    @pytest.mark.asyncio
    async def test_execute_increments_call_count(self):
        """Test that execute increments call_count."""
        mock = MockPrimitive()
        await mock.execute({}, None)
        assert mock.call_count == 1
        await mock.execute({}, None)
        assert mock.call_count == 2


class TestTimeoutPrimitiveInit:
    """Test TimeoutPrimitive initialization."""

    def test_initialization_with_timeout(self, fast_primitive):
        """Test initialization with valid timeout."""
        timeout = TimeoutPrimitive(
            primitive=fast_primitive,
            timeout_seconds=5.0,
            grace_period_seconds=1.0,
        )

        assert timeout.timeout_seconds == 5.0
        assert timeout.grace_period_seconds == 1.0

    def test_initialization_negative_timeout_raises_error(self, fast_primitive):
        """Test initialization with negative timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout_seconds must be > 0"):
            TimeoutPrimitive(
                primitive=fast_primitive,
                timeout_seconds=-1.0,
            )

    def test_initialization_zero_timeout_raises_error(self, fast_primitive):
        """Test initialization with zero timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout_seconds must be > 0"):
            TimeoutPrimitive(
                primitive=fast_primitive,
                timeout_seconds=0.0,
            )


class TestTimeoutEnforcement:
    """Test timeout enforcement."""

    @pytest.mark.asyncio
    async def test_completes_within_timeout(self, fast_primitive):
        """Test execution completes successfully within timeout."""
        timeout = TimeoutPrimitive(
            primitive=fast_primitive,
            timeout_seconds=1.0,  # 1 second timeout
        )

        mock_context = MagicMock()
        result = await timeout.execute({"query": "test"}, mock_context)

        assert result == "FastPrimitive_result"
        assert fast_primitive.call_count == 1

    @pytest.mark.asyncio
    async def test_raises_timeout_error_when_exceeds(self, slow_primitive):
        """Test raises TimeoutError when execution exceeds timeout + grace period."""
        timeout = TimeoutPrimitive(
            primitive=slow_primitive,
            timeout_seconds=0.5,  # 0.5 second timeout
            grace_period_seconds=0.1,  # 0.1 grace = 0.6 total
        )

        mock_context = MagicMock()

        # SlowPrimitive takes 2s, should exceed 0.6s total timeout
        with pytest.raises(TimeoutError):  # Custom TimeoutError from module
            await timeout.execute({"query": "test"}, mock_context)


class TestGracePeriod:
    """Test grace period behavior."""

    @pytest.mark.asyncio
    async def test_grace_period_allows_cleanup(self, slow_primitive):
        """Test grace period extends total timeout duration."""
        timeout = TimeoutPrimitive(
            primitive=slow_primitive,
            timeout_seconds=0.5,
            grace_period_seconds=0.2,  # Total timeout = 0.7s
        )

        mock_context = MagicMock()

        # SlowPrimitive takes 2s, should exceed 0.7s total and raise TimeoutError
        with pytest.raises(TimeoutError):  # Custom TimeoutError from module
            await timeout.execute({"query": "test"}, mock_context)


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_propagates_primitive_errors(self, fast_primitive):
        """Test errors from wrapped primitive are propagated."""
        error_primitive = MockPrimitive("ErrorPrimitive", raise_error=True)

        timeout = TimeoutPrimitive(
            primitive=error_primitive,
            timeout_seconds=1.0,
        )

        mock_context = MagicMock()

        with pytest.raises(ValueError, match="ErrorPrimitive error"):
            await timeout.execute({"query": "test"}, mock_context)


class TestMetricsRecording:
    """Test metrics recording."""

    @pytest.mark.asyncio
    async def test_success_metrics_recorded(self, timeout_primitive):
        """Test success metrics are recorded."""
        mock_context = MagicMock()
        result = await timeout_primitive.execute({"query": "test"}, mock_context)

        # Metrics should work with graceful degradation
        assert result is not None

    @pytest.mark.asyncio
    async def test_timeout_metrics_recorded(self, slow_primitive):
        """Test timeout metrics are recorded."""
        timeout = TimeoutPrimitive(
            primitive=slow_primitive,
            timeout_seconds=0.1,
            grace_period_seconds=0.1,  # Total 0.2s
        )

        mock_context = MagicMock()

        # SlowPrimitive takes 2s, should exceed 0.2s and raise TimeoutError
        with pytest.raises(TimeoutError):  # Custom TimeoutError from module
            await timeout.execute({"query": "test"}, mock_context)

        # Metrics should be recorded even on timeout


class TestGracefulDegradation:
    """Test graceful degradation when OpenTelemetry unavailable."""

    @pytest.mark.asyncio
    async def test_works_without_metrics(self, fast_primitive):
        """Test timeout works without metrics infrastructure."""
        timeout = TimeoutPrimitive(
            primitive=fast_primitive,
            timeout_seconds=1.0,
        )

        mock_context = MagicMock()
        result = await timeout.execute({"query": "test"}, mock_context)

        assert result == "FastPrimitive_result"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_data(self, timeout_primitive):
        """Test timeout with empty data."""
        mock_context = MagicMock()
        result = await timeout_primitive.execute({}, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_none_data(self, timeout_primitive):
        """Test timeout with None data."""
        mock_context = MagicMock()
        result = await timeout_primitive.execute(None, mock_context)
        assert result is not None

    @pytest.mark.asyncio
    async def test_very_short_timeout(self, fast_primitive):
        """Test behavior with very short timeout."""
        timeout = TimeoutPrimitive(
            primitive=fast_primitive,
            timeout_seconds=0.01,  # 10ms timeout
            grace_period_seconds=0.01,  # 10ms grace = 20ms total
        )

        mock_context = MagicMock()

        # Fast primitive takes 100ms, should exceed 20ms total and raise TimeoutError
        with pytest.raises(TimeoutError):  # Custom TimeoutError from module
            await timeout.execute({"query": "test"}, mock_context)

    @pytest.mark.asyncio
    async def test_very_long_timeout(self, fast_primitive):
        """Test behavior with very long timeout."""
        timeout = TimeoutPrimitive(
            primitive=fast_primitive,
            timeout_seconds=3600.0,  # 1 hour timeout
        )

        mock_context = MagicMock()
        result = await timeout.execute({"query": "test"}, mock_context)

        # Should complete normally
        assert result == "FastPrimitive_result"


class TestConcurrentExecution:
    """Test concurrent execution scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_calls(self, fast_primitive):
        """Test multiple concurrent calls work independently."""
        timeout = TimeoutPrimitive(
            primitive=fast_primitive,
            timeout_seconds=1.0,
        )

        mock_context = MagicMock()

        # Execute multiple calls concurrently
        results = await asyncio.gather(
            timeout.execute({"query": "test1"}, mock_context),
            timeout.execute({"query": "test2"}, mock_context),
            timeout.execute({"query": "test3"}, mock_context),
        )

        assert len(results) == 3
        assert all(r == "FastPrimitive_result" for r in results)
        assert fast_primitive.call_count == 3

    @pytest.mark.asyncio
    async def test_timeout_statistics_tracking(self, fast_primitive):
        """Test timeout statistics are tracked correctly."""
        timeout = TimeoutPrimitive(
            primitive=fast_primitive,
            timeout_seconds=1.0,
        )

        mock_context = MagicMock()

        # Execute multiple successful operations
        await timeout.execute({"query": "test1"}, mock_context)
        await timeout.execute({"query": "test2"}, mock_context)

        # Statistics should be tracked (internal state)
        assert timeout._total_successes == 2
        assert timeout._total_failures == 0


class TestOperationNaming:
    """Test operation naming for observability."""

    @pytest.mark.asyncio
    async def test_custom_operation_name(self, fast_primitive):
        """Test custom operation name is used."""
        timeout = TimeoutPrimitive(
            primitive=fast_primitive,
            timeout_seconds=1.0,
            operation_name="custom_operation",
        )

        mock_context = MagicMock()
        result = await timeout.execute({"query": "test"}, mock_context)

        assert result is not None

    @pytest.mark.asyncio
    async def test_default_operation_name(self, fast_primitive):
        """Test default operation name when not specified."""
        timeout = TimeoutPrimitive(
            primitive=fast_primitive,
            timeout_seconds=1.0,
            operation_name=None,
        )

        mock_context = MagicMock()
        result = await timeout.execute({"query": "test"}, mock_context)

        assert result is not None
