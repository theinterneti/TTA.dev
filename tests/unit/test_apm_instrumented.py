"""Tests for ttadev.primitives.apm.instrumented."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ttadev.primitives.apm.instrumented import APMWorkflowPrimitive
from ttadev.primitives.core.base import WorkflowContext


class ConcreteAPM(APMWorkflowPrimitive):
    """Concrete subclass for testing."""

    def __init__(self, name=None, return_value="result", raise_exc=None):
        super().__init__(name=name)
        self._return_value = return_value
        self._raise_exc = raise_exc

    async def _execute_impl(self, input_data, context):
        if self._raise_exc:
            raise self._raise_exc
        return self._return_value


@pytest.fixture
def ctx():
    return WorkflowContext(workflow_id="test-wf", session_id="sess-1")


class TestAPMWorkflowPrimitiveInit:
    def test_default_name_is_class_name(self):
        p = ConcreteAPM()
        assert p.name == "ConcreteAPM"

    def test_custom_name(self):
        p = ConcreteAPM(name="my-primitive")
        assert p.name == "my-primitive"

    def test_counters_none_when_apm_disabled(self):
        with patch("ttadev.primitives.apm.instrumented.is_apm_enabled", return_value=False):
            p = ConcreteAPM()
        assert p._execution_counter is None
        assert p._duration_histogram is None


class TestAPMExecuteDisabled:
    @pytest.mark.asyncio
    async def test_passes_through_when_apm_disabled(self, ctx):
        with patch("ttadev.primitives.apm.instrumented.is_apm_enabled", return_value=False):
            p = ConcreteAPM(return_value="direct")
            result = await p.execute("input", ctx)
        assert result == "direct"

    @pytest.mark.asyncio
    async def test_raises_when_apm_disabled_and_impl_raises(self, ctx):
        with patch("ttadev.primitives.apm.instrumented.is_apm_enabled", return_value=False):
            p = ConcreteAPM(raise_exc=ValueError("boom"))
            with pytest.raises(ValueError, match="boom"):
                await p.execute("input", ctx)


class TestAPMExecuteEnabledNoTracer:
    @pytest.mark.asyncio
    async def test_passes_through_when_no_tracer(self, ctx):
        with (
            patch("ttadev.primitives.apm.instrumented.is_apm_enabled", return_value=True),
            patch("ttadev.primitives.apm.instrumented.get_tracer", return_value=None),
        ):
            p = ConcreteAPM(return_value="via-tracer-none")
            result = await p.execute("input", ctx)
        assert result == "via-tracer-none"


class TestAPMExecuteEnabledWithTracer:
    def _make_tracer(self):
        span = MagicMock()
        span.__enter__ = MagicMock(return_value=span)
        span.__exit__ = MagicMock(return_value=False)
        tracer = MagicMock()
        tracer.start_as_current_span.return_value = span
        return tracer, span

    @pytest.mark.asyncio
    async def test_success_path(self, ctx):
        tracer, span = self._make_tracer()
        counter = MagicMock()
        histogram = MagicMock()

        with (
            patch("ttadev.primitives.apm.instrumented.is_apm_enabled", return_value=True),
            patch("ttadev.primitives.apm.instrumented.get_tracer", return_value=tracer),
            patch("ttadev.primitives.apm.instrumented.get_meter"),
            patch("ttadev.primitives.apm.instrumented.is_apm_enabled", return_value=True),
        ):
            p = ConcreteAPM(return_value="traced-result")
            p._execution_counter = counter
            p._duration_histogram = histogram
            result = await p.execute("input", ctx)

        assert result == "traced-result"

    @pytest.mark.asyncio
    async def test_failure_path_reraises(self, ctx):
        tracer, span = self._make_tracer()
        counter = MagicMock()
        histogram = MagicMock()

        with (
            patch("ttadev.primitives.apm.instrumented.is_apm_enabled", return_value=True),
            patch("ttadev.primitives.apm.instrumented.get_tracer", return_value=tracer),
        ):
            p = ConcreteAPM(raise_exc=RuntimeError("fail"))
            p._execution_counter = counter
            p._duration_histogram = histogram
            with pytest.raises(RuntimeError, match="fail"):
                await p.execute("input", ctx)


class TestExecuteImplAbstract:
    @pytest.mark.asyncio
    async def test_base_raises_not_implemented(self, ctx):
        class Bare(APMWorkflowPrimitive):
            pass

        p = Bare()
        with pytest.raises(NotImplementedError):
            await p._execute_impl("data", ctx)


class TestInitMetrics:
    def test_metrics_init_with_apm_enabled(self):
        mock_meter = MagicMock()
        mock_meter.create_counter.return_value = MagicMock()
        mock_meter.create_histogram.return_value = MagicMock()

        with (
            patch("ttadev.primitives.apm.instrumented.is_apm_enabled", return_value=True),
            patch("ttadev.primitives.apm.instrumented.get_meter", return_value=mock_meter),
        ):
            p = ConcreteAPM(name="test-prim")

        assert p._execution_counter is not None
        assert p._duration_histogram is not None

    def test_metrics_skip_when_meter_none(self):
        with (
            patch("ttadev.primitives.apm.instrumented.is_apm_enabled", return_value=True),
            patch("ttadev.primitives.apm.instrumented.get_meter", return_value=None),
        ):
            p = ConcreteAPM()

        assert p._execution_counter is None
        assert p._duration_histogram is None
