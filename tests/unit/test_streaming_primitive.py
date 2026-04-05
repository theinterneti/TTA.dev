"""Tests for ttadev.primitives.streaming.streaming_primitive."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.streaming.streaming_primitive import StreamingPrimitive


class WordStreamPrimitive(StreamingPrimitive[str, str]):
    """Simple concrete implementation for tests."""

    async def stream(self, input_data: str, context: WorkflowContext) -> AsyncGenerator[str, None]:
        for word in input_data.split():
            yield word


class ErrorStreamPrimitive(StreamingPrimitive[str, str]):
    """Raises mid-stream for error-path tests."""

    async def stream(self, input_data: str, context: WorkflowContext) -> AsyncGenerator[str, None]:
        yield "first"
        raise RuntimeError("stream error")


def make_ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="stream-test")


class TestStreamingPrimitiveExecute:
    @pytest.mark.asyncio
    async def test_execute_collects_all_tokens(self):
        p = WordStreamPrimitive()
        ctx = make_ctx()
        result = await p.execute("hello world foo", ctx)
        assert result == ["hello", "world", "foo"]

    @pytest.mark.asyncio
    async def test_execute_empty_input(self):
        p = WordStreamPrimitive()
        ctx = make_ctx()
        result = await p.execute("", ctx)
        assert result == []

    @pytest.mark.asyncio
    async def test_execute_raises_on_stream_error(self):
        p = ErrorStreamPrimitive()
        ctx = make_ctx()
        with pytest.raises(RuntimeError, match="stream error"):
            await p.execute("input", ctx)

    @pytest.mark.asyncio
    async def test_execute_custom_name(self):
        p = WordStreamPrimitive(name="MyStream")
        assert p._name == "MyStream"
        ctx = make_ctx()
        result = await p.execute("a b", ctx)
        assert result == ["a", "b"]


class TestStreamingPrimitiveStreamWithTracing:
    @pytest.mark.asyncio
    async def test_stream_with_tracing_yields_tokens(self):
        p = WordStreamPrimitive()
        ctx = make_ctx()
        tokens = []
        async for token in p.stream_with_tracing("one two three", ctx):
            tokens.append(token)
        assert tokens == ["one", "two", "three"]

    @pytest.mark.asyncio
    async def test_stream_with_tracing_propagates_error(self):
        p = ErrorStreamPrimitive()
        ctx = make_ctx()
        tokens = []
        with pytest.raises(RuntimeError):
            async for token in p.stream_with_tracing("x", ctx):
                tokens.append(token)
        assert tokens == ["first"]


class TestStreamingPrimitiveWithOtel:
    @pytest.mark.asyncio
    async def test_execute_with_otel_tracing(self):
        """execute() records span attributes when tracing is available."""
        import ttadev.primitives.streaming.streaming_primitive as mod

        fake_span = type(
            "Span",
            (),
            {
                "set_attribute": lambda self, k, v: None,
                "record_exception": lambda self, e: None,
                "end": lambda self: None,
            },
        )()
        fake_tracer = type(
            "Tracer",
            (),
            {
                "start_span": lambda self, name: fake_span,
            },
        )()
        fake_otel = type(
            "OTel",
            (),
            {
                "get_tracer": lambda self, name: fake_tracer,
            },
        )()

        with (
            patch.object(mod, "_TRACING_AVAILABLE", True),
            patch.object(mod, "_otel_trace", fake_otel),
        ):
            p = WordStreamPrimitive()
            ctx = make_ctx()
            result = await p.execute("a b", ctx)
        assert result == ["a", "b"]

    @pytest.mark.asyncio
    async def test_execute_error_with_otel_tracing(self):
        """execute() records exception on span when stream errors."""
        import ttadev.primitives.streaming.streaming_primitive as mod

        recorded: list = []

        class Span:
            def set_attribute(self, k, v):
                pass

            def record_exception(self, e):
                recorded.append(e)

            def end(self):
                pass

        fake_tracer = type("T", (), {"start_span": lambda self, n: Span()})()
        fake_otel = type("O", (), {"get_tracer": lambda self, n: fake_tracer})()

        with (
            patch.object(mod, "_TRACING_AVAILABLE", True),
            patch.object(mod, "_otel_trace", fake_otel),
        ):
            p = ErrorStreamPrimitive()
            ctx = make_ctx()
            with pytest.raises(RuntimeError):
                await p.execute("x", ctx)
        assert len(recorded) == 1
