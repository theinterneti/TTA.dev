"""Tests for StreamingPrimitive — async-generator output and OTel tracing."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive
from ttadev.primitives.streaming import StreamingPrimitive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(workflow_id: str = "wf-stream-test") -> WorkflowContext:
    return WorkflowContext(workflow_id=workflow_id)


class _TokenPrimitive(StreamingPrimitive[str, str]):
    """Streams each word of the input as a separate token."""

    async def stream(self, input_data: str, context: WorkflowContext) -> AsyncGenerator[str, None]:
        for token in input_data.split():
            yield token


class _NumberPrimitive(StreamingPrimitive[int, int]):
    """Streams integers 0..n-1."""

    async def stream(self, input_data: int, context: WorkflowContext) -> AsyncGenerator[int, None]:
        for i in range(input_data):
            yield i


class _FailingPrimitive(StreamingPrimitive[str, str]):
    """Raises on the second token."""

    async def stream(self, input_data: str, context: WorkflowContext) -> AsyncGenerator[str, None]:
        yield "first"
        raise RuntimeError("stream exploded")


# ---------------------------------------------------------------------------
# stream() — basic behaviour
# ---------------------------------------------------------------------------


class TestStream:
    @pytest.mark.asyncio
    async def test_yields_tokens(self):
        p = _TokenPrimitive()
        tokens = []
        async for token in p.stream("hello world foo", _ctx()):
            tokens.append(token)
        assert tokens == ["hello", "world", "foo"]

    @pytest.mark.asyncio
    async def test_yields_numbers(self):
        p = _NumberPrimitive()
        nums = []
        async for n in p.stream(5, _ctx()):
            nums.append(n)
        assert nums == [0, 1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_empty_input_yields_nothing(self):
        p = _TokenPrimitive()
        tokens = [t async for t in p.stream("", _ctx())]
        assert tokens == []


# ---------------------------------------------------------------------------
# execute() — collects full stream
# ---------------------------------------------------------------------------


class TestExecute:
    @pytest.mark.asyncio
    async def test_execute_returns_list_of_chunks(self):
        p = _TokenPrimitive()
        result = await p.execute("alpha beta gamma", _ctx())
        assert result == ["alpha", "beta", "gamma"]

    @pytest.mark.asyncio
    async def test_execute_returns_empty_list_for_empty_stream(self):
        p = _TokenPrimitive()
        result = await p.execute("", _ctx())
        assert result == []

    @pytest.mark.asyncio
    async def test_execute_numbers(self):
        p = _NumberPrimitive()
        result = await p.execute(3, _ctx())
        assert result == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_execute_propagates_exceptions(self):
        p = _FailingPrimitive()
        with pytest.raises(RuntimeError, match="stream exploded"):
            await p.execute("x", _ctx())

    @pytest.mark.asyncio
    async def test_execute_result_joinable_for_string_streams(self):
        p = _TokenPrimitive()
        result = await p.execute("join these words", _ctx())
        assert "".join(result) == "jointhesewords"


# ---------------------------------------------------------------------------
# stream_with_tracing() — no OTel installed
# ---------------------------------------------------------------------------


class TestStreamWithTracingNoOTel:
    """stream_with_tracing falls back to plain stream() when OTel absent."""

    @pytest.mark.asyncio
    async def test_yields_same_tokens_without_otel(self):
        with patch("ttadev.primitives.streaming.streaming_primitive._TRACING_AVAILABLE", False):
            p = _TokenPrimitive()
            tokens = [t async for t in p.stream_with_tracing("a b c", _ctx())]
        assert tokens == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_propagates_exception_without_otel(self):
        with patch("ttadev.primitives.streaming.streaming_primitive._TRACING_AVAILABLE", False):
            p = _FailingPrimitive()
            with pytest.raises(RuntimeError, match="stream exploded"):
                async for _ in p.stream_with_tracing("x", _ctx()):
                    pass


# ---------------------------------------------------------------------------
# stream_with_tracing() — OTel present (mocked)
# ---------------------------------------------------------------------------


class TestStreamWithTracingOTel:
    def _make_mock_tracer(self):
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=False)
        mock_tracer = MagicMock()
        mock_tracer.start_span.return_value = mock_span
        return mock_tracer, mock_span

    @pytest.mark.asyncio
    async def test_yields_tokens_with_otel(self):
        mock_tracer, mock_span = self._make_mock_tracer()
        with (
            patch(
                "ttadev.primitives.streaming.streaming_primitive._TRACING_AVAILABLE",
                True,
            ),
            patch("ttadev.primitives.streaming.streaming_primitive._otel_trace") as mock_trace,
        ):
            mock_trace.get_tracer.return_value = mock_tracer
            p = _TokenPrimitive()
            tokens = [t async for t in p.stream_with_tracing("x y z", _ctx())]

        assert tokens == ["x", "y", "z"]

    @pytest.mark.asyncio
    async def test_span_records_token_count(self):
        mock_tracer, mock_span = self._make_mock_tracer()
        with (
            patch(
                "ttadev.primitives.streaming.streaming_primitive._TRACING_AVAILABLE",
                True,
            ),
            patch("ttadev.primitives.streaming.streaming_primitive._otel_trace") as mock_trace,
        ):
            mock_trace.get_tracer.return_value = mock_tracer
            p = _TokenPrimitive()
            tokens = [t async for t in p.stream_with_tracing("one two three four", _ctx())]

        assert len(tokens) == 4
        set_calls = {
            call.args[0]: call.args[1]
            for call in mock_span.set_attribute.call_args_list
            if call.args
        }
        assert set_calls.get("streaming.token_count") == 4
        assert set_calls.get("streaming.status") == "ok"

    @pytest.mark.asyncio
    async def test_span_records_error_on_exception(self):
        mock_tracer, mock_span = self._make_mock_tracer()
        with (
            patch(
                "ttadev.primitives.streaming.streaming_primitive._TRACING_AVAILABLE",
                True,
            ),
            patch("ttadev.primitives.streaming.streaming_primitive._otel_trace") as mock_trace,
        ):
            mock_trace.get_tracer.return_value = mock_tracer
            p = _FailingPrimitive()
            with pytest.raises(RuntimeError):
                async for _ in p.stream_with_tracing("x", _ctx()):
                    pass

        set_calls = {
            call.args[0]: call.args[1]
            for call in mock_span.set_attribute.call_args_list
            if call.args
        }
        assert set_calls.get("streaming.status") == "error"
        mock_span.record_exception.assert_called_once()
        mock_span.end.assert_called_once()

    @pytest.mark.asyncio
    async def test_span_always_ended(self):
        mock_tracer, mock_span = self._make_mock_tracer()
        with (
            patch(
                "ttadev.primitives.streaming.streaming_primitive._TRACING_AVAILABLE",
                True,
            ),
            patch("ttadev.primitives.streaming.streaming_primitive._otel_trace") as mock_trace,
        ):
            mock_trace.get_tracer.return_value = mock_tracer
            p = _TokenPrimitive()
            _ = [t async for t in p.stream_with_tracing("hi", _ctx())]

        mock_span.end.assert_called_once()


# ---------------------------------------------------------------------------
# execute() OTel span
# ---------------------------------------------------------------------------


class TestExecuteOTelSpan:
    def _make_mock_tracer(self):
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_span.return_value = mock_span
        return mock_tracer, mock_span

    @pytest.mark.asyncio
    async def test_execute_span_records_token_count(self):
        mock_tracer, mock_span = self._make_mock_tracer()
        with (
            patch(
                "ttadev.primitives.streaming.streaming_primitive._TRACING_AVAILABLE",
                True,
            ),
            patch("ttadev.primitives.streaming.streaming_primitive._otel_trace") as mock_trace,
        ):
            mock_trace.get_tracer.return_value = mock_tracer
            p = _TokenPrimitive()
            result = await p.execute("a b c d e", _ctx())

        assert len(result) == 5
        set_calls = {
            call.args[0]: call.args[1]
            for call in mock_span.set_attribute.call_args_list
            if call.args
        }
        assert set_calls.get("streaming.token_count") == 5
        assert set_calls.get("streaming.status") == "ok"
        mock_span.end.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_span_records_error(self):
        mock_tracer, mock_span = self._make_mock_tracer()
        with (
            patch(
                "ttadev.primitives.streaming.streaming_primitive._TRACING_AVAILABLE",
                True,
            ),
            patch("ttadev.primitives.streaming.streaming_primitive._otel_trace") as mock_trace,
        ):
            mock_trace.get_tracer.return_value = mock_tracer
            p = _FailingPrimitive()
            with pytest.raises(RuntimeError):
                await p.execute("x", _ctx())

        set_calls = {
            call.args[0]: call.args[1]
            for call in mock_span.set_attribute.call_args_list
            if call.args
        }
        assert set_calls.get("streaming.status") == "error"
        mock_span.end.assert_called_once()


# ---------------------------------------------------------------------------
# Composition — >> and |
# ---------------------------------------------------------------------------


class TestComposition:
    @pytest.mark.asyncio
    async def test_streaming_primitive_chains_with_rshift(self):
        """execute() returns a list, so downstream primitive receives it."""
        from ttadev.primitives.core.base import LambdaPrimitive

        count_tokens = LambdaPrimitive(lambda tokens, ctx: len(tokens))
        pipeline = _TokenPrimitive() >> count_tokens
        result = await pipeline.execute("a b c d", _ctx())
        assert result == 4

    @pytest.mark.asyncio
    async def test_streaming_primitive_is_workflow_primitive(self):
        p = _TokenPrimitive()
        assert isinstance(p, WorkflowPrimitive)

    @pytest.mark.asyncio
    async def test_streaming_primitive_name_defaults_to_class_name(self):
        p = _TokenPrimitive()
        assert p._name == "_TokenPrimitive"

    @pytest.mark.asyncio
    async def test_streaming_primitive_custom_name(self):
        p = _TokenPrimitive(name="my-streamer")
        assert p._name == "my-streamer"


# ---------------------------------------------------------------------------
# Type generics
# ---------------------------------------------------------------------------


class TestGenerics:
    @pytest.mark.asyncio
    async def test_int_stream(self):
        p = _NumberPrimitive()
        result = await p.execute(4, _ctx())
        assert result == [0, 1, 2, 3]

    @pytest.mark.asyncio
    async def test_dict_stream(self):
        class _DictPrimitive(StreamingPrimitive[list[dict], dict]):  # type: ignore[type-arg]
            async def stream(
                self, input_data: list[dict], context: WorkflowContext
            ) -> AsyncGenerator[dict, None]:
                for item in input_data:
                    yield item

        p = _DictPrimitive()
        data = [{"a": 1}, {"b": 2}]
        result = await p.execute(data, _ctx())
        assert result == data
