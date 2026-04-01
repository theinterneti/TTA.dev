"""Tests for MockPrimitive and WorkflowTestCase."""

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.testing.mocks import MockPrimitive, WorkflowTestCase


@pytest.fixture
def ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test-wf")


class TestMockPrimitiveReturnValue:
    @pytest.mark.asyncio
    async def test_returns_configured_value(self, ctx: WorkflowContext) -> None:
        mock = MockPrimitive("m", return_value={"ok": True})
        result = await mock.execute("input", ctx)
        assert result == {"ok": True}

    @pytest.mark.asyncio
    async def test_returns_none_by_default(self, ctx: WorkflowContext) -> None:
        mock = MockPrimitive("m")
        result = await mock.execute("input", ctx)
        assert result is None

    @pytest.mark.asyncio
    async def test_tracks_call_count(self, ctx: WorkflowContext) -> None:
        mock = MockPrimitive("m", return_value=1)
        await mock.execute("a", ctx)
        await mock.execute("b", ctx)
        assert mock.call_count == 2

    @pytest.mark.asyncio
    async def test_tracks_calls(self, ctx: WorkflowContext) -> None:
        mock = MockPrimitive("m", return_value=1)
        await mock.execute("x", ctx)
        assert mock.calls[0] == ("x", ctx)


class TestMockPrimitiveRaiseError:
    @pytest.mark.asyncio
    async def test_raises_configured_error(self, ctx: WorkflowContext) -> None:
        err = ValueError("boom")
        mock = MockPrimitive("m", raise_error=err)
        with pytest.raises(ValueError, match="boom"):
            await mock.execute("input", ctx)
        assert mock.call_count == 1


class TestMockPrimitiveSideEffect:
    @pytest.mark.asyncio
    async def test_sync_side_effect(self, ctx: WorkflowContext) -> None:
        def side(data, c):
            return data.upper()

        mock = MockPrimitive("m", side_effect=side)
        result = await mock.execute("hello", ctx)
        assert result == "HELLO"

    @pytest.mark.asyncio
    async def test_async_side_effect(self, ctx: WorkflowContext) -> None:
        async def async_side(data, c):
            return data + "_async"

        mock = MockPrimitive("m", side_effect=async_side)
        result = await mock.execute("hi", ctx)
        assert result == "hi_async"


class TestMockPrimitiveAssertions:
    @pytest.mark.asyncio
    async def test_assert_called_passes_after_call(self, ctx: WorkflowContext) -> None:
        mock = MockPrimitive("m", return_value=1)
        await mock.execute("x", ctx)
        mock.assert_called()

    def test_assert_called_fails_before_call(self) -> None:
        mock = MockPrimitive("m")
        with pytest.raises(AssertionError):
            mock.assert_called()

    @pytest.mark.asyncio
    async def test_assert_called_once_passes(self, ctx: WorkflowContext) -> None:
        mock = MockPrimitive("m", return_value=1)
        await mock.execute("x", ctx)
        mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_assert_called_once_fails_on_multiple(self, ctx: WorkflowContext) -> None:
        mock = MockPrimitive("m", return_value=1)
        await mock.execute("x", ctx)
        await mock.execute("y", ctx)
        with pytest.raises(AssertionError):
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_assert_called_with_passes(self, ctx: WorkflowContext) -> None:
        mock = MockPrimitive("m", return_value=1)
        await mock.execute("data", ctx)
        mock.assert_called_with("data")

    @pytest.mark.asyncio
    async def test_assert_called_with_context(self, ctx: WorkflowContext) -> None:
        mock = MockPrimitive("m", return_value=1)
        await mock.execute("data", ctx)
        mock.assert_called_with("data", ctx)

    @pytest.mark.asyncio
    async def test_assert_called_with_wrong_input_fails(self, ctx: WorkflowContext) -> None:
        mock = MockPrimitive("m", return_value=1)
        await mock.execute("actual", ctx)
        with pytest.raises(AssertionError):
            mock.assert_called_with("expected")

    @pytest.mark.asyncio
    async def test_reset_clears_tracking(self, ctx: WorkflowContext) -> None:
        mock = MockPrimitive("m", return_value=1)
        await mock.execute("x", ctx)
        mock.reset()
        assert mock.call_count == 0
        assert mock.calls == []


class TestWorkflowTestCase:
    @pytest.mark.asyncio
    async def test_execute_with_default_context(self) -> None:
        mock = MockPrimitive("m", return_value=42)
        tc = WorkflowTestCase(mock)
        result = await tc.execute("input")
        assert result == 42

    @pytest.mark.asyncio
    async def test_execute_with_explicit_context(self, ctx: WorkflowContext) -> None:
        mock = MockPrimitive("m", return_value=99)
        tc = WorkflowTestCase(mock)
        result = await tc.execute("input", ctx)
        assert result == 99

    @pytest.mark.asyncio
    async def test_assert_primitive_called_passes(self) -> None:
        mock = MockPrimitive("m", return_value=1)
        tc = WorkflowTestCase(mock)
        await tc.execute("x")
        tc.assert_primitive_called(mock)

    @pytest.mark.asyncio
    async def test_assert_primitive_called_with_times(self) -> None:
        mock = MockPrimitive("m", return_value=1)
        tc = WorkflowTestCase(mock)
        await tc.execute("x")
        await tc.execute("y")
        tc.assert_primitive_called(mock, times=2)

    @pytest.mark.asyncio
    async def test_assert_primitive_called_wrong_times_fails(self) -> None:
        mock = MockPrimitive("m", return_value=1)
        tc = WorkflowTestCase(mock)
        await tc.execute("x")
        with pytest.raises(AssertionError):
            tc.assert_primitive_called(mock, times=5)

    def test_assert_primitive_not_called_fails(self) -> None:
        mock = MockPrimitive("m")
        tc = WorkflowTestCase(mock)
        with pytest.raises(AssertionError):
            tc.assert_primitive_called(mock)

    @pytest.mark.asyncio
    async def test_reset_mocks_resets_tracked_mocks(self) -> None:
        mock = MockPrimitive("m", return_value=1)
        tc = WorkflowTestCase(mock)
        tc.mocks.append(mock)
        await tc.execute("x")
        tc.reset_mocks()
        assert mock.call_count == 0
