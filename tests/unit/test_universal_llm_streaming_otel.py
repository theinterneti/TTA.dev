"""Unit tests for UniversalLLMPrimitive — token streaming (issue-248) and
OpenTelemetry instrumentation (issue-250).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from ttadev.primitives import WorkflowContext
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    UniversalLLMPrimitive,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="wf-otel-test")


def _request(model: str = "llama3-8b-8192") -> LLMRequest:
    return LLMRequest(model=model, messages=[{"role": "user", "content": "hi"}])


def _groq_chunk(content: str | None) -> SimpleNamespace:
    """Build a mock Groq/OpenAI streaming chunk."""
    delta = SimpleNamespace(content=content)
    choice = SimpleNamespace(delta=delta)
    return SimpleNamespace(choices=[choice])


class _AsyncIter:
    """Minimal async iterator wrapping a list of items."""

    def __init__(self, items: list) -> None:
        self._items = iter(items)

    def __aiter__(self) -> _AsyncIter:
        return self

    async def __anext__(self):
        try:
            return next(self._items)
        except StopIteration:
            raise StopAsyncIteration


# ---------------------------------------------------------------------------
# Fixture — in-memory OTel tracer provider
# ---------------------------------------------------------------------------


@pytest.fixture
def span_exporter():
    """Patch the tracer inside universal_llm_primitive to use an InMemorySpanExporter.

    The global OTel TracerProvider cannot be replaced once set (SDK guard).
    Instead we create a private provider + exporter and patch the module-level
    `otel_trace` inside `universal_llm_primitive` to return tracers from it.
    """
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Build a proxy: calling .get_tracer() on this returns a real tracer
    # backed by our in-memory exporter, so spans land in `exporter`.
    import ttadev.primitives.llm.universal_llm_primitive as llm_mod

    class _FakeOtelTrace:
        def get_tracer(self, name: str):
            return provider.get_tracer(name)

    original_otel = llm_mod.otel_trace
    llm_mod.otel_trace = _FakeOtelTrace()  # type: ignore[assignment]

    yield exporter

    llm_mod.otel_trace = original_otel
    exporter.clear()


# ---------------------------------------------------------------------------
# OTel tests (issue-250)
# ---------------------------------------------------------------------------


async def test_span_emitted_on_success(span_exporter: InMemorySpanExporter) -> None:
    """A completed execute() must emit a span with all gen_ai.* attributes."""
    # Arrange
    mock_usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5)
    mock_message = SimpleNamespace(content="hello")
    mock_choice = SimpleNamespace(message=mock_message)
    mock_resp = SimpleNamespace(choices=[mock_choice], model="llama3-8b-8192", usage=mock_usage)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
    mock_groq = MagicMock()
    mock_groq.AsyncGroq.return_value = mock_client

    primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="k")
    ctx = _ctx()
    request = _request()

    # Act
    with patch.dict("sys.modules", {"groq": mock_groq}):
        result = await primitive.execute(request, ctx)

    # Assert — response is correct
    assert result.content == "hello"

    # Assert — exactly one span was emitted
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]

    assert span.name == "gen_ai.groq.invoke"
    attrs = dict(span.attributes or {})
    assert attrs["gen_ai.system"] == "groq"
    assert attrs["gen_ai.request.model"] == "llama3-8b-8192"
    assert attrs["gen_ai.request.temperature"] == pytest.approx(0.7)
    assert attrs["gen_ai.response.model"] == "llama3-8b-8192"
    assert attrs["gen_ai.usage.prompt_tokens"] == 10
    assert attrs["gen_ai.usage.completion_tokens"] == 5

    # Status should be OK (unset = no error)
    assert span.status.status_code != StatusCode.ERROR


async def test_span_records_error_on_failure(span_exporter: InMemorySpanExporter) -> None:
    """A provider exception must leave the span with ERROR status and recorded exception."""
    # Arrange
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("upstream timeout"))
    mock_groq = MagicMock()
    mock_groq.AsyncGroq.return_value = mock_client

    primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="k")
    ctx = _ctx()
    request = _request()

    # Act & Assert — exception propagates
    with patch.dict("sys.modules", {"groq": mock_groq}):
        with pytest.raises(RuntimeError, match="upstream timeout"):
            await primitive.execute(request, ctx)

    # Assert — span recorded the error
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]

    assert span.status.status_code == StatusCode.ERROR
    # At least one event should be the recorded exception
    event_names = [e.name for e in (span.events or [])]
    assert "exception" in event_names


# ---------------------------------------------------------------------------
# Streaming tests (issue-248)
# ---------------------------------------------------------------------------


async def test_stream_yields_tokens() -> None:
    """stream() must yield tokens in the order the provider emits them."""
    # Arrange
    chunks = [
        _groq_chunk("Hello"),
        _groq_chunk(","),
        _groq_chunk(" world"),
    ]
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_AsyncIter(chunks))
    mock_groq = MagicMock()
    mock_groq.AsyncGroq.return_value = mock_client

    primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="k")
    ctx = _ctx()
    request = _request()

    # Act
    tokens: list[str] = []
    with patch.dict("sys.modules", {"groq": mock_groq}):
        async for token in primitive.stream(request, ctx):
            tokens.append(token)

    # Assert
    assert tokens == ["Hello", ",", " world"]


async def test_stream_empty_content_filtered() -> None:
    """None and empty-string delta.content must be silently dropped."""
    # Arrange — mix of None, "", and real content
    chunks = [
        _groq_chunk(None),  # should be filtered (None → "" → falsy)
        _groq_chunk(""),  # should be filtered (empty → falsy)
        _groq_chunk("real"),  # should pass through
        _groq_chunk(None),  # trailing None — filtered
    ]
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_AsyncIter(chunks))
    mock_groq = MagicMock()
    mock_groq.AsyncGroq.return_value = mock_client

    primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="k")
    ctx = _ctx()
    request = _request()

    # Act
    tokens: list[str] = []
    with patch.dict("sys.modules", {"groq": mock_groq}):
        async for token in primitive.stream(request, ctx):
            tokens.append(token)

    # Assert — only the non-empty token survived
    assert tokens == ["real"]


async def test_stream_raises_on_provider_error() -> None:
    """A provider error during streaming must propagate to the caller."""
    # Arrange
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=ConnectionError("Groq unreachable"))
    mock_groq = MagicMock()
    mock_groq.AsyncGroq.return_value = mock_client

    primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="k")
    ctx = _ctx()
    request = _request()

    # Act & Assert
    with patch.dict("sys.modules", {"groq": mock_groq}):
        with pytest.raises(ConnectionError, match="Groq unreachable"):
            async for _ in primitive.stream(request, ctx):
                pass  # pragma: no cover


# ---------------------------------------------------------------------------
# Sanity: LLMRequest.stream field default
# ---------------------------------------------------------------------------


def test_llm_request_stream_field_defaults_false() -> None:
    """LLMRequest.stream must default to False for backward compatibility."""
    req = LLMRequest(model="any", messages=[])
    assert req.stream is False


def test_llm_request_stream_field_settable() -> None:
    """LLMRequest.stream can be set to True."""
    req = LLMRequest(model="any", messages=[], stream=True)
    assert req.stream is True


# ---------------------------------------------------------------------------
# OTel: Anthropic usage key mapping (input_tokens → prompt_tokens attribute)
# ---------------------------------------------------------------------------


async def test_span_maps_anthropic_usage_keys(span_exporter: InMemorySpanExporter) -> None:
    """Anthropic's input_tokens/output_tokens must map to gen_ai.usage.* attributes."""
    # Arrange
    mock_usage = SimpleNamespace(input_tokens=8, output_tokens=4)
    mock_content = SimpleNamespace(text="hello claude")
    mock_resp = SimpleNamespace(
        content=[mock_content], model="claude-haiku-4-5-20251001", usage=mock_usage
    )

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_resp)
    mock_anthropic = MagicMock()
    mock_anthropic.AsyncAnthropic.return_value = mock_client

    primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="k")
    ctx = _ctx()
    request = LLMRequest(
        model="claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": "hi"}],
    )

    # Act
    with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
        await primitive.execute(request, ctx)

    # Assert — Anthropic keys appear on the span under canonical gen_ai names
    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    attrs = dict(spans[0].attributes or {})
    assert attrs["gen_ai.usage.prompt_tokens"] == 8
    assert attrs["gen_ai.usage.completion_tokens"] == 4
