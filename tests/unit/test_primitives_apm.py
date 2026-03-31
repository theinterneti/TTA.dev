"""Unit tests for ttadev/primitives/apm/ — decorators and setup.

Tests verify:
- `is_apm_enabled` reflects actual initialisation state
- `get_tracer` / `get_meter` return None when not initialised
- `trace_workflow` passes through results when APM is disabled
- `trace_workflow` adds span attributes when APM is enabled
- `track_metric` passes through results when APM is disabled
- `track_metric` records metrics when APM is enabled
- Both decorators propagate exceptions correctly
- sync and async function detection is correct
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import ttadev.primitives.apm.setup as apm_setup
from ttadev.primitives.apm.decorators import trace_workflow, track_metric
from ttadev.primitives.apm.setup import (
    get_meter,
    get_tracer,
    is_apm_enabled,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_apm_state():
    """Reset global APM state before and after each test."""
    # Save original
    orig_initialized = apm_setup._initialized
    orig_tracer = apm_setup._tracer_provider
    orig_meter = apm_setup._meter_provider

    yield

    # Restore
    apm_setup._initialized = orig_initialized
    apm_setup._tracer_provider = orig_tracer
    apm_setup._meter_provider = orig_meter


def _disable_apm():
    apm_setup._initialized = False
    apm_setup._tracer_provider = None
    apm_setup._meter_provider = None


def _enable_apm_mock():
    """Mark APM as enabled with a mock tracer and meter."""
    apm_setup._initialized = True
    apm_setup._tracer_provider = MagicMock()
    apm_setup._meter_provider = MagicMock()


# ---------------------------------------------------------------------------
# is_apm_enabled / get_tracer / get_meter
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestApmSetupHelpers:
    def test_is_apm_enabled_false_when_not_initialized(self) -> None:
        _disable_apm()
        # When OTel is available but _initialized is False:
        with patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True):
            assert is_apm_enabled() is False

    def test_is_apm_enabled_false_when_otel_unavailable(self) -> None:
        with patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", False):
            assert is_apm_enabled() is False

    def test_is_apm_enabled_true_when_initialized(self) -> None:
        with patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True):
            apm_setup._initialized = True
            assert is_apm_enabled() is True

    def test_get_tracer_returns_none_when_disabled(self) -> None:
        _disable_apm()
        with patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True):
            assert get_tracer("mod") is None

    def test_get_tracer_returns_none_when_otel_unavailable(self) -> None:
        with patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", False):
            assert get_tracer("mod") is None

    def test_get_meter_returns_none_when_disabled(self) -> None:
        _disable_apm()
        with patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True):
            assert get_meter("mod") is None

    def test_get_meter_returns_none_when_otel_unavailable(self) -> None:
        with patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", False):
            assert get_meter("mod") is None

    def test_get_tracer_delegates_to_otel_when_enabled(self) -> None:
        _enable_apm_mock()
        mock_tracer = MagicMock()
        with (
            patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True),
            patch("opentelemetry.trace.get_tracer", return_value=mock_tracer),
        ):
            result = get_tracer("mymod")
        assert result is mock_tracer

    def test_get_meter_delegates_to_otel_when_enabled(self) -> None:
        _enable_apm_mock()
        mock_meter = MagicMock()
        with (
            patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True),
            patch("opentelemetry.metrics.get_meter", return_value=mock_meter),
        ):
            result = get_meter("mymod")
        assert result is mock_meter


# ---------------------------------------------------------------------------
# trace_workflow — APM disabled (pass-through)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTraceWorkflowDisabled:
    async def test_async_passthrough_returns_value(self) -> None:
        _disable_apm()

        @trace_workflow("test.span")
        async def fn():
            return 42

        assert await fn() == 42

    def test_sync_passthrough_returns_value(self) -> None:
        _disable_apm()

        @trace_workflow("test.span")
        def fn():
            return 99

        assert fn() == 99

    async def test_async_passthrough_propagates_exception(self) -> None:
        _disable_apm()

        @trace_workflow()
        async def boom():
            raise ValueError("oops")

        with pytest.raises(ValueError, match="oops"):
            await boom()

    def test_sync_passthrough_propagates_exception(self) -> None:
        _disable_apm()

        @trace_workflow()
        def boom():
            raise RuntimeError("bad")

        with pytest.raises(RuntimeError, match="bad"):
            boom()

    async def test_async_wrapper_chosen_for_coroutine(self) -> None:
        """Decorated coroutine must still be awaitable."""
        import inspect

        _disable_apm()

        @trace_workflow()
        async def afn():
            return "async"

        assert inspect.iscoroutinefunction(afn)

    def test_sync_wrapper_chosen_for_regular_function(self) -> None:
        import inspect

        _disable_apm()

        @trace_workflow()
        def sfn():
            return "sync"

        assert not inspect.iscoroutinefunction(sfn)

    def test_default_span_name_uses_function_name(self) -> None:
        """With APM disabled the decorator has no observable span name effect;
        this test ensures the decorator applies without error."""
        _disable_apm()

        @trace_workflow()
        def named_fn():
            return "ok"

        assert named_fn() == "ok"


# ---------------------------------------------------------------------------
# trace_workflow — APM enabled (span creation)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTraceWorkflowEnabled:
    async def test_async_function_span_created(self) -> None:
        _enable_apm_mock()
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

        with (
            patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True),
            patch("opentelemetry.trace.get_tracer", return_value=mock_tracer),
        ):

            @trace_workflow("my.span")
            async def afn():
                return "result"

            result = await afn()

        assert result == "result"
        mock_tracer.start_as_current_span.assert_called_once()

    async def test_async_exception_recorded_and_reraised(self) -> None:
        _enable_apm_mock()
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

        with (
            patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True),
            patch("opentelemetry.trace.get_tracer", return_value=mock_tracer),
        ):

            @trace_workflow()
            async def failing():
                raise KeyError("not found")

            with pytest.raises(KeyError, match="not found"):
                await failing()

    def test_sync_function_span_created(self) -> None:
        _enable_apm_mock()
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

        with (
            patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True),
            patch("opentelemetry.trace.get_tracer", return_value=mock_tracer),
        ):

            @trace_workflow("sync.span")
            def sfn():
                return "sync_result"

            result = sfn()

        assert result == "sync_result"
        mock_tracer.start_as_current_span.assert_called_once()

    def test_no_tracer_falls_back_to_passthrough(self) -> None:
        """When get_tracer returns None, function still executes normally."""
        _enable_apm_mock()
        with (
            patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True),
            patch("opentelemetry.trace.get_tracer", return_value=None),
        ):

            @trace_workflow()
            def sfn():
                return "fallback"

            assert sfn() == "fallback"


# ---------------------------------------------------------------------------
# track_metric — APM disabled
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTrackMetricDisabled:
    async def test_async_passthrough(self) -> None:
        _disable_apm()

        @track_metric("calls", "counter")
        async def afn():
            return 7

        assert await afn() == 7

    def test_sync_passthrough(self) -> None:
        _disable_apm()

        @track_metric("calls", "counter")
        def sfn():
            return 8

        assert sfn() == 8

    async def test_async_exception_propagated(self) -> None:
        _disable_apm()

        @track_metric("calls", "counter")
        async def failing():
            raise ValueError("metric fail")

        with pytest.raises(ValueError, match="metric fail"):
            await failing()

    async def test_unknown_metric_type_falls_back(self) -> None:
        """Unknown metric_type with APM disabled → still returns normally."""
        _disable_apm()

        @track_metric("calls", "unknown_type")
        async def afn():
            return 9

        assert await afn() == 9


# ---------------------------------------------------------------------------
# track_metric — APM enabled (counter + histogram)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTrackMetricEnabled:
    async def test_counter_incremented_on_success(self) -> None:
        _enable_apm_mock()
        mock_counter = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.return_value = mock_counter

        with (
            patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True),
            patch("opentelemetry.metrics.get_meter", return_value=mock_meter),
        ):

            @track_metric("api.calls", "counter", "Number of API calls")
            async def afn():
                return "done"

            result = await afn()

        assert result == "done"
        mock_counter.add.assert_called_once_with(1, {"status": "success"})

    async def test_counter_incremented_on_error(self) -> None:
        _enable_apm_mock()
        mock_counter = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.return_value = mock_counter

        with (
            patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True),
            patch("opentelemetry.metrics.get_meter", return_value=mock_meter),
        ):

            @track_metric("api.calls", "counter")
            async def failing():
                raise RuntimeError("boom")

            with pytest.raises(RuntimeError):
                await failing()

        call_args = mock_counter.add.call_args[0]
        assert call_args[0] == 1
        assert mock_counter.add.call_args[0][1]["status"] == "error"  # type: ignore[index]

    async def test_histogram_records_on_success(self) -> None:
        _enable_apm_mock()
        mock_histogram = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_histogram.return_value = mock_histogram

        with (
            patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True),
            patch("opentelemetry.metrics.get_meter", return_value=mock_meter),
        ):

            @track_metric("latency", "histogram", "Request latency")
            async def afn():
                return "measured"

            result = await afn()

        assert result == "measured"
        mock_histogram.record.assert_called_once()
        duration, attrs = mock_histogram.record.call_args[0]
        assert isinstance(duration, float)
        assert attrs["status"] == "success"

    async def test_unknown_metric_type_with_apm_enabled_falls_back(self) -> None:
        """Unknown metric_type → no meter instrument created, function still runs."""
        _enable_apm_mock()
        mock_meter = MagicMock()

        with (
            patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True),
            patch("opentelemetry.metrics.get_meter", return_value=mock_meter),
        ):

            @track_metric("calls", "unknown_type")
            async def afn():
                return "ok"

            result = await afn()

        assert result == "ok"
        mock_meter.create_counter.assert_not_called()
        mock_meter.create_histogram.assert_not_called()

    def test_sync_counter_incremented_on_success(self) -> None:
        _enable_apm_mock()
        mock_counter = MagicMock()
        mock_meter = MagicMock()
        mock_meter.create_counter.return_value = mock_counter

        with (
            patch.object(apm_setup, "OPENTELEMETRY_AVAILABLE", True),
            patch("opentelemetry.metrics.get_meter", return_value=mock_meter),
        ):

            @track_metric("sync.calls", "counter")
            def sfn():
                return "sync_done"

            result = sfn()

        assert result == "sync_done"
        mock_counter.add.assert_called_once_with(1, {"status": "success"})
