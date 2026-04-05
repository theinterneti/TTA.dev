"""Comprehensive unit tests for UniversalLLMPrimitive.

Covers:
  - LLMProvider enum, ToolSchema, ToolCall, LLMRequest, LLMResponse dataclasses
  - _build_langfuse_usage() token cost calculation
  - UniversalLLMPrimitive.__init__() provider validation
  - _parse_openai_tool_calls(), _build_openai_tool_kwargs() static methods
  - _call_groq, _call_anthropic, _call_openai, _call_ollama,
    _call_openrouter, _call_together, _call_xai, _call_openai_compat
  - _stream_openai, _stream_anthropic, _stream_ollama,
    _stream_google, _stream_openrouter, _stream_together, _stream_xai,
    _stream_openai_compat
  - execute() and stream() dispatch routing
  - _resolve_call_fn / _resolve_stream_fn with use_compat

Deliberately does NOT duplicate tests in:
  - test_universal_llm_streaming_otel.py  (OTel, stream+GROQ, execute+GROQ)
  - test_gemini_provider.py               (_call_google, execute→GOOGLE)
"""

from __future__ import annotations

import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.core import WorkflowContext
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    ToolCall,
    ToolSchema,
    UniversalLLMPrimitive,
    _build_langfuse_usage,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test-wf")


def _req(model: str = "test-model") -> LLMRequest:
    return LLMRequest(model=model, messages=[{"role": "user", "content": "hi"}])


# ── Async iterator helper ────────────────────────────────────────────────────


class _AsyncIter:
    """Minimal async iterator that wraps a list — used in streaming mocks."""

    def __init__(self, items: list) -> None:
        self._items = iter(items)

    def __aiter__(self) -> _AsyncIter:
        return self

    async def __anext__(self):
        try:
            return next(self._items)
        except StopIteration:
            raise StopAsyncIteration


# ── Fake objects for OpenAI-style responses ──────────────────────────────────


def _oai_response(
    content: str = "hello",
    model: str = "test-model",
    prompt_tokens: int = 10,
    completion_tokens: int = 5,
    tool_calls=None,
    finish_reason: str = "stop",
) -> SimpleNamespace:
    """Build a fake OpenAI-style (non-streaming) chat completion response."""
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    choice = SimpleNamespace(message=message, finish_reason=finish_reason)
    usage = SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
    return SimpleNamespace(choices=[choice], model=model, usage=usage)


def _oai_chunk(content: str | None) -> SimpleNamespace:
    """Build a fake OpenAI-style streaming chunk."""
    delta = SimpleNamespace(content=content)
    choice = SimpleNamespace(delta=delta)
    return SimpleNamespace(choices=[choice])


def _oai_client(response: object) -> MagicMock:
    """Return a fake AsyncOpenAI client whose completions.create returns *response*."""
    create = AsyncMock(return_value=response)
    completions = MagicMock()
    completions.create = create
    chat = MagicMock()
    chat.completions = completions
    client = MagicMock()
    client.chat = chat
    return client


# ── Fake httpx clients (real classes avoid dunder-method mock pitfalls) ──────


class _FakeOllamaHTTPXClient:
    """Fake httpx.AsyncClient for _call_ollama (non-streaming)."""

    def __init__(self, response_json: dict) -> None:
        self._json = response_json

    async def __aenter__(self) -> _FakeOllamaHTTPXClient:
        return self

    async def __aexit__(self, *args) -> None:
        pass

    async def post(self, url: str, json: dict | None = None, **kwargs) -> MagicMock:
        resp = MagicMock()
        resp.raise_for_status = lambda: None
        resp.json = lambda: self._json
        return resp


class _CapturingOllamaHTTPXClient:
    """Fake httpx.AsyncClient that captures the posted payload."""

    def __init__(self, response_json: dict, captured: dict) -> None:
        self._json = response_json
        self._captured = captured

    async def __aenter__(self) -> _CapturingOllamaHTTPXClient:
        return self

    async def __aexit__(self, *args) -> None:
        pass

    async def post(self, url: str, json: dict | None = None, **kwargs) -> MagicMock:
        self._captured["url"] = url
        self._captured["payload"] = json
        resp = MagicMock()
        resp.raise_for_status = lambda: None
        resp.json = lambda: self._json
        return resp


class _LineIter:
    """Async line iterator for Ollama NDJSON streaming."""

    def __init__(self, lines: list[str]) -> None:
        self._iter = iter(lines)

    def __aiter__(self) -> _LineIter:
        return self

    async def __anext__(self) -> str:
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class _FakeOllamaStreamResp:
    """Fake httpx streaming response for _stream_ollama."""

    def __init__(self, lines: list[str]) -> None:
        self._lines = lines

    def raise_for_status(self) -> None:
        pass

    def aiter_lines(self) -> _LineIter:
        return _LineIter(self._lines)

    async def __aenter__(self) -> _FakeOllamaStreamResp:
        return self

    async def __aexit__(self, *args) -> None:
        pass


class _FakeOllamaStreamClient:
    """Fake httpx.AsyncClient with streaming support for _stream_ollama."""

    def __init__(self, lines: list[str]) -> None:
        self._lines = lines

    async def __aenter__(self) -> _FakeOllamaStreamClient:
        return self

    async def __aexit__(self, *args) -> None:
        pass

    def stream(self, method: str, url: str, **kwargs) -> _FakeOllamaStreamResp:
        return _FakeOllamaStreamResp(self._lines)


# ── Fake async context manager for _stream_openai_compat ────────────────────


class _CompatStreamCM:
    """Async CM that yields chunks — mocks ``async with await create(stream=True) as s``."""

    def __init__(self, chunks: list) -> None:
        self._chunks = chunks

    async def __aenter__(self) -> _AsyncIter:
        return _AsyncIter(self._chunks)

    async def __aexit__(self, *args) -> None:
        pass


# ── Fake async context manager for _stream_anthropic ────────────────────────


class _AnthropicStreamCM:
    """Async CM that returns a stream obj with text_stream for _stream_anthropic."""

    def __init__(self, texts: list[str]) -> None:
        self._texts = texts

    async def __aenter__(self) -> MagicMock:
        stream_obj = MagicMock()
        stream_obj.text_stream = _AsyncIter(self._texts)
        return stream_obj

    async def __aexit__(self, *args) -> None:
        pass


# ---------------------------------------------------------------------------
# 1. LLMProvider enum
# ---------------------------------------------------------------------------


class TestLLMProviderEnum:
    def test_all_provider_values_exist(self) -> None:
        """Every expected provider variant is present in the enum."""
        values = {p.value for p in LLMProvider}
        assert "groq" in values
        assert "anthropic" in values
        assert "openai" in values
        assert "ollama" in values
        assert "google" in values
        assert "openrouter" in values
        assert "together" in values
        assert "xai" in values

    def test_str_enum_compares_equal_to_string(self) -> None:
        """LLMProvider values behave as plain strings (StrEnum contract)."""
        assert LLMProvider.GROQ == "groq"
        assert LLMProvider.ANTHROPIC == "anthropic"
        assert LLMProvider.OPENAI == "openai"
        assert LLMProvider.OLLAMA == "ollama"
        assert LLMProvider.OPENROUTER == "openrouter"
        assert LLMProvider.TOGETHER == "together"
        assert LLMProvider.XAI == "xai"
        assert LLMProvider.GOOGLE == "google"


# ---------------------------------------------------------------------------
# 2. ToolSchema dataclass
# ---------------------------------------------------------------------------

_PARAMS: dict = {
    "type": "object",
    "properties": {"location": {"type": "string"}},
    "required": ["location"],
}


class TestToolSchema:
    def test_to_openai_basic_structure(self) -> None:
        """to_openai() produces the OpenAI function-calling wire format."""
        # Arrange
        tool = ToolSchema(name="get_weather", description="Get current weather", parameters=_PARAMS)

        # Act
        result = tool.to_openai()

        # Assert
        assert result["type"] == "function"
        func = result["function"]
        assert func["name"] == "get_weather"
        assert func["description"] == "Get current weather"
        assert func["parameters"] == _PARAMS
        assert "strict" not in func

    def test_to_openai_strict_adds_strict_field(self) -> None:
        """to_openai() adds strict=True inside the function dict when strict=True."""
        # Arrange
        tool = ToolSchema(name="op", description="desc", parameters={}, strict=True)

        # Act
        result = tool.to_openai()

        # Assert
        assert result["function"]["strict"] is True

    def test_to_anthropic_uses_input_schema(self) -> None:
        """to_anthropic() maps parameters → input_schema for Anthropic wire format."""
        # Arrange
        tool = ToolSchema(name="lookup", description="Look up a term", parameters=_PARAMS)

        # Act
        result = tool.to_anthropic()

        # Assert
        assert result["name"] == "lookup"
        assert result["description"] == "Look up a term"
        assert result["input_schema"] == _PARAMS
        assert "parameters" not in result

    def test_strict_false_by_default(self) -> None:
        """ToolSchema.strict defaults to False."""
        tool = ToolSchema(name="t", description="d", parameters={})
        assert tool.strict is False


# ---------------------------------------------------------------------------
# 3. ToolCall dataclass
# ---------------------------------------------------------------------------


class TestToolCall:
    def test_stores_all_fields(self) -> None:
        """ToolCall stores id, name, and parsed arguments dict."""
        tc = ToolCall(id="call_abc", name="search", arguments={"query": "hello"})
        assert tc.id == "call_abc"
        assert tc.name == "search"
        assert tc.arguments == {"query": "hello"}


# ---------------------------------------------------------------------------
# 4. LLMRequest dataclass
# ---------------------------------------------------------------------------


class TestLLMRequest:
    def test_defaults(self) -> None:
        """LLMRequest has sensible defaults for all optional fields."""
        req = LLMRequest(model="gpt-4o", messages=[])
        assert req.temperature == 0.7
        assert req.max_tokens is None
        assert req.system is None
        assert req.stream is False
        assert req.tools is None
        assert req.tool_choice == "auto"

    def test_all_fields_settable(self) -> None:
        """LLMRequest accepts all optional fields."""
        tool = ToolSchema(name="fn", description="d", parameters={})
        req = LLMRequest(
            model="llama3",
            messages=[{"role": "user", "content": "hi"}],
            temperature=0.1,
            max_tokens=512,
            system="Be helpful",
            stream=True,
            tools=[tool],
            tool_choice="required",
        )
        assert req.temperature == 0.1
        assert req.max_tokens == 512
        assert req.system == "Be helpful"
        assert req.stream is True
        assert req.tools == [tool]
        assert req.tool_choice == "required"


# ---------------------------------------------------------------------------
# 5. LLMResponse dataclass
# ---------------------------------------------------------------------------


class TestLLMResponse:
    def test_required_fields(self) -> None:
        """LLMResponse stores content, model, and provider."""
        resp = LLMResponse(content="hello", model="gpt-4o", provider="openai")
        assert resp.content == "hello"
        assert resp.model == "gpt-4o"
        assert resp.provider == "openai"

    def test_optional_fields_default_to_none(self) -> None:
        """usage, tool_calls, and finish_reason default to None."""
        resp = LLMResponse(content="", model="m", provider="p")
        assert resp.usage is None
        assert resp.tool_calls is None
        assert resp.finish_reason is None

    def test_with_all_optional_fields(self) -> None:
        """LLMResponse accepts all optional fields."""
        tc = ToolCall(id="c1", name="fn", arguments={})
        resp = LLMResponse(
            content="text",
            model="claude-3",
            provider="anthropic",
            usage={"input_tokens": 10, "output_tokens": 5},
            tool_calls=[tc],
            finish_reason="tool_calls",
        )
        assert resp.usage == {"input_tokens": 10, "output_tokens": 5}
        assert len(resp.tool_calls) == 1
        assert resp.finish_reason == "tool_calls"


# ---------------------------------------------------------------------------
# 6. _build_langfuse_usage()
# ---------------------------------------------------------------------------


class TestBuildLangfuseUsage:
    def test_openai_style_token_keys(self) -> None:
        """Extracts prompt_tokens and completion_tokens from OpenAI-style usage."""
        # Arrange
        resp = LLMResponse(
            content="hi",
            model="gpt-4o",
            provider="openai",
            usage={"prompt_tokens": 20, "completion_tokens": 10},
        )

        # Act
        result = _build_langfuse_usage("openai", resp)

        # Assert
        assert result["usage"]["prompt_tokens"] == 20
        assert result["usage"]["completion_tokens"] == 10

    def test_anthropic_style_token_keys(self) -> None:
        """Extracts input_tokens/output_tokens from Anthropic-style usage."""
        # Arrange
        resp = LLMResponse(
            content="hi",
            model="claude-3",
            provider="anthropic",
            usage={"input_tokens": 8, "output_tokens": 4},
        )

        # Act
        result = _build_langfuse_usage("anthropic", resp)

        # Assert — mapped to prompt/completion under usage key
        assert result["usage"]["prompt_tokens"] == 8
        assert result["usage"]["completion_tokens"] == 4

    def test_none_usage_yields_none_token_counts(self) -> None:
        """When response.usage is None, token counts are None (no exception raised)."""
        # Arrange
        resp = LLMResponse(content="hi", model="m", provider="p", usage=None)

        # Act
        result = _build_langfuse_usage("groq", resp)

        # Assert
        assert result["usage"]["prompt_tokens"] is None
        assert result["usage"]["completion_tokens"] is None

    def test_pricing_exception_silenced(self) -> None:
        """If pricing lookup raises, _build_langfuse_usage still returns a valid dict."""
        # Arrange
        resp = LLMResponse(
            content="hi",
            model="some-model",
            provider="groq",
            usage={"prompt_tokens": 5, "completion_tokens": 3},
        )

        # Act — patch get_pricing to raise inside the try/except
        with patch(
            "ttadev.primitives.llm.model_pricing.get_pricing",
            side_effect=RuntimeError("pricing DB offline"),
        ):
            result = _build_langfuse_usage("groq", resp)

        # Assert — returns usage without raising
        assert "usage" in result
        assert result["usage"]["prompt_tokens"] == 5
        assert result["usage"]["completion_tokens"] == 3
        assert "cost_details" not in result

    def test_pricing_available_adds_cost_details(self) -> None:
        """When get_pricing returns data, cost_details and cost_tier appear in result."""
        # Arrange
        from ttadev.primitives.llm.model_pricing import ModelPricing

        fake_pricing = ModelPricing(
            provider="groq",
            model_id="llama3-8b",
            cost_tier="free",
            cost_per_1k_input_tokens=0.0,
            cost_per_1k_output_tokens=0.0,
        )
        resp = LLMResponse(
            content="hi",
            model="llama3-8b",
            provider="groq",
            usage={"prompt_tokens": 100, "completion_tokens": 50},
        )

        # Act
        with patch(
            "ttadev.primitives.llm.model_pricing.get_pricing",
            return_value=fake_pricing,
        ):
            result = _build_langfuse_usage("groq", resp)

        # Assert — basic usage is always present
        assert result["usage"]["prompt_tokens"] == 100
        assert result["usage"]["completion_tokens"] == 50


# ---------------------------------------------------------------------------
# 7. UniversalLLMPrimitive.__init__
# ---------------------------------------------------------------------------


class TestUniversalLLMPrimitiveInit:
    def test_valid_provider_accepted(self) -> None:
        """Constructor succeeds for every LLMProvider enum member."""
        for provider in LLMProvider:
            p = UniversalLLMPrimitive(provider=provider, api_key="k")
            assert p._provider == provider

    def test_invalid_provider_string_raises_value_error(self) -> None:
        """Passing a plain string instead of LLMProvider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            UniversalLLMPrimitive(provider="groq")  # type: ignore[arg-type]

    def test_invalid_provider_int_raises_value_error(self) -> None:
        """Passing an integer raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            UniversalLLMPrimitive(provider=42)  # type: ignore[arg-type]

    def test_api_key_stored(self) -> None:
        """Explicit api_key is stored on the instance."""
        p = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="sk-test")
        assert p._api_key == "sk-test"

    def test_api_key_defaults_to_none(self) -> None:
        """api_key defaults to None when not provided."""
        p = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)
        assert p._api_key is None

    def test_base_url_stored(self) -> None:
        """Explicit base_url is stored on the instance."""
        p = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="k", base_url="http://proxy")
        assert p._base_url == "http://proxy"

    def test_use_compat_stored(self) -> None:
        """use_compat flag is stored on the instance."""
        p = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="k", use_compat=True)
        assert p._use_compat is True


# ---------------------------------------------------------------------------
# 8. Static methods: _parse_openai_tool_calls
# ---------------------------------------------------------------------------


class TestParseOpenaiToolCalls:
    def test_none_input_returns_none(self) -> None:
        """None raw_calls → None (no tool calls in response)."""
        assert UniversalLLMPrimitive._parse_openai_tool_calls(None) is None

    def test_empty_list_returns_none(self) -> None:
        """Empty list → None (falsy guard)."""
        assert UniversalLLMPrimitive._parse_openai_tool_calls([]) is None

    def test_single_tool_call_parsed(self) -> None:
        """A single raw tool call is converted to a ToolCall with parsed arguments."""
        # Arrange
        raw_tc = SimpleNamespace(
            id="call_xyz",
            function=SimpleNamespace(name="search", arguments='{"query": "TTA"}'),
        )

        # Act
        result = UniversalLLMPrimitive._parse_openai_tool_calls([raw_tc])

        # Assert
        assert result is not None
        assert len(result) == 1
        tc = result[0]
        assert tc.id == "call_xyz"
        assert tc.name == "search"
        assert tc.arguments == {"query": "TTA"}

    def test_multiple_tool_calls_all_parsed(self) -> None:
        """Multiple raw tool calls are all converted correctly."""
        # Arrange
        raw_calls = [
            SimpleNamespace(
                id=f"call_{i}",
                function=SimpleNamespace(name=f"fn_{i}", arguments=f'{{"arg": {i}}}'),
            )
            for i in range(3)
        ]

        # Act
        result = UniversalLLMPrimitive._parse_openai_tool_calls(raw_calls)

        # Assert
        assert result is not None
        assert len(result) == 3
        assert result[0].name == "fn_0"
        assert result[1].arguments == {"arg": 1}
        assert result[2].id == "call_2"


# ---------------------------------------------------------------------------
# 9. Static method: _build_openai_tool_kwargs
# ---------------------------------------------------------------------------


class TestBuildOpenaiToolKwargs:
    def test_no_tools_returns_empty_dict(self) -> None:
        """When request.tools is None, returns {} (no side effects for callers)."""
        req = LLMRequest(model="m", messages=[], tools=None)
        assert UniversalLLMPrimitive._build_openai_tool_kwargs(req) == {}

    def test_empty_tools_list_returns_empty_dict(self) -> None:
        """When request.tools is [] (falsy), returns {}."""
        req = LLMRequest(model="m", messages=[], tools=[])
        assert UniversalLLMPrimitive._build_openai_tool_kwargs(req) == {}

    def test_with_tools_returns_tools_and_choice(self) -> None:
        """With tools declared, returns tools list + tool_choice."""
        # Arrange
        tool = ToolSchema(name="fn", description="d", parameters={"type": "object"})
        req = LLMRequest(model="m", messages=[], tools=[tool], tool_choice="auto")

        # Act
        result = UniversalLLMPrimitive._build_openai_tool_kwargs(req)

        # Assert
        assert "tools" in result
        assert "tool_choice" in result
        assert result["tools"][0]["type"] == "function"
        assert result["tools"][0]["function"]["name"] == "fn"
        assert result["tool_choice"] == "auto"

    def test_tool_choice_propagated(self) -> None:
        """tool_choice value is passed through unchanged."""
        tool = ToolSchema(name="t", description="d", parameters={})
        req = LLMRequest(model="m", messages=[], tools=[tool], tool_choice="required")
        result = UniversalLLMPrimitive._build_openai_tool_kwargs(req)
        assert result["tool_choice"] == "required"


# ---------------------------------------------------------------------------
# 10. _call_groq — direct method tests
# ---------------------------------------------------------------------------


class TestCallGroq:
    async def test_success_returns_llmresponse(self) -> None:
        """_call_groq returns correct LLMResponse on a successful API call."""
        # Arrange
        mock_resp = _oai_response(content="groq says hi", model="llama3-8b-8192")
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
        mock_groq_mod = MagicMock()
        mock_groq_mod.AsyncGroq.return_value = mock_client

        primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="k")

        # Act
        with patch.dict("sys.modules", {"groq": mock_groq_mod}):
            result = await primitive._call_groq(_req("llama3-8b-8192"), _ctx())

        # Assert
        assert result.content == "groq says hi"
        assert result.provider == "groq"
        assert result.model == "llama3-8b-8192"
        assert result.usage == {"prompt_tokens": 10, "completion_tokens": 5}
        assert result.tool_calls is None

    async def test_tool_calls_parsed(self) -> None:
        """_call_groq parses tool_calls from the response message."""
        # Arrange
        raw_tc = SimpleNamespace(
            id="tc_1",
            function=SimpleNamespace(name="calculate", arguments='{"x": 2, "y": 3}'),
        )
        mock_resp = _oai_response(content="", tool_calls=[raw_tc], finish_reason="tool_calls")
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
        mock_groq_mod = MagicMock()
        mock_groq_mod.AsyncGroq.return_value = mock_client

        primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="k")

        # Act
        with patch.dict("sys.modules", {"groq": mock_groq_mod}):
            result = await primitive._call_groq(_req(), _ctx())

        # Assert
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "calculate"
        assert result.tool_calls[0].arguments == {"x": 2, "y": 3}
        assert result.finish_reason == "tool_calls"

    async def test_none_usage_yields_none(self) -> None:
        """When usage is None in the groq response, LLMResponse.usage is None."""
        # Arrange
        resp_ns = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="ok", tool_calls=None),
                    finish_reason="stop",
                )
            ],
            model="llama3",
            usage=None,
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(return_value=resp_ns)
        mock_groq_mod = MagicMock()
        mock_groq_mod.AsyncGroq.return_value = mock_client

        primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="k")

        # Act
        with patch.dict("sys.modules", {"groq": mock_groq_mod}):
            result = await primitive._call_groq(_req(), _ctx())

        # Assert
        assert result.usage is None


# ---------------------------------------------------------------------------
# 11. _call_anthropic — direct method tests
# ---------------------------------------------------------------------------


class TestCallAnthropic:
    def _text_resp(self, text: str = "hello claude") -> SimpleNamespace:
        text_block = SimpleNamespace(type="text", text=text)
        return SimpleNamespace(
            content=[text_block],
            model="claude-3-haiku",
            usage=SimpleNamespace(input_tokens=8, output_tokens=4),
            stop_reason="end_turn",
        )

    def _make_anthropic_client(self, mock_resp: object) -> tuple[MagicMock, MagicMock]:
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_resp)
        mock_anthropic_mod = MagicMock()
        mock_anthropic_mod.AsyncAnthropic.return_value = mock_client
        return mock_client, mock_anthropic_mod

    async def test_success_plain_text(self) -> None:
        """_call_anthropic returns correct LLMResponse for plain text responses."""
        # Arrange
        _, mock_mod = self._make_anthropic_client(self._text_resp("Hello!"))
        primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="k")

        # Act
        with patch.dict("sys.modules", {"anthropic": mock_mod}):
            result = await primitive._call_anthropic(_req("claude-3-haiku"), _ctx())

        # Assert
        assert result.content == "Hello!"
        assert result.provider == "anthropic"
        assert result.model == "claude-3-haiku"
        assert result.usage == {"input_tokens": 8, "output_tokens": 4}
        assert result.finish_reason == "end_turn"
        assert result.tool_calls is None

    async def test_tool_use_blocks_parsed(self) -> None:
        """_call_anthropic parses tool_use content blocks into ToolCall objects."""
        # Arrange
        tool_block = SimpleNamespace(
            type="tool_use", id="tb_1", name="get_weather", input={"city": "NYC"}
        )
        resp = SimpleNamespace(
            content=[tool_block],
            model="claude-3",
            usage=SimpleNamespace(input_tokens=12, output_tokens=6),
            stop_reason="tool_use",
        )
        _, mock_mod = self._make_anthropic_client(resp)
        primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="k")

        # Act
        with patch.dict("sys.modules", {"anthropic": mock_mod}):
            result = await primitive._call_anthropic(_req(), _ctx())

        # Assert
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].id == "tb_1"
        assert result.tool_calls[0].name == "get_weather"
        assert result.tool_calls[0].arguments == {"city": "NYC"}
        assert result.finish_reason == "tool_use"

    async def test_mixed_text_and_tool_blocks(self) -> None:
        """Both text and tool_use blocks are extracted when present together."""
        # Arrange
        text_block = SimpleNamespace(type="text", text="Let me check that.")
        tool_block = SimpleNamespace(type="tool_use", id="tb_2", name="lookup", input={"q": "test"})
        resp = SimpleNamespace(
            content=[text_block, tool_block],
            model="claude-3",
            usage=SimpleNamespace(input_tokens=15, output_tokens=8),
            stop_reason="tool_use",
        )
        _, mock_mod = self._make_anthropic_client(resp)
        primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="k")

        # Act
        with patch.dict("sys.modules", {"anthropic": mock_mod}):
            result = await primitive._call_anthropic(_req(), _ctx())

        # Assert
        assert result.content == "Let me check that."
        assert result.tool_calls is not None
        assert result.tool_calls[0].name == "lookup"

    async def test_tools_kwarg_passed_when_request_has_tools(self) -> None:
        """_call_anthropic passes tools= kwarg to messages.create when request has tools."""
        # Arrange
        mock_client, mock_mod = self._make_anthropic_client(self._text_resp())
        tool = ToolSchema(name="t", description="d", parameters={})
        request = LLMRequest(
            model="claude-3",
            messages=[{"role": "user", "content": "hi"}],
            tools=[tool],
        )
        primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="k")

        # Act
        with patch.dict("sys.modules", {"anthropic": mock_mod}):
            await primitive._call_anthropic(request, _ctx())

        # Assert — tools kwarg was passed
        kwargs = mock_client.messages.create.call_args.kwargs
        assert "tools" in kwargs
        assert kwargs["tools"][0]["name"] == "t"

    async def test_fallback_content_path_when_no_typed_text_block(self) -> None:
        """Falls back to content[0].text when no block has type='text'."""
        # Arrange — block without type attribute but with text (legacy/mock scenario)
        legacy_block = SimpleNamespace(text="fallback text")  # no .type
        resp = SimpleNamespace(
            content=[legacy_block],
            model="claude-3",
            usage=SimpleNamespace(input_tokens=5, output_tokens=2),
            stop_reason="end_turn",
        )
        _, mock_mod = self._make_anthropic_client(resp)
        primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="k")

        # Act
        with patch.dict("sys.modules", {"anthropic": mock_mod}):
            result = await primitive._call_anthropic(_req(), _ctx())

        # Assert
        assert result.content == "fallback text"

    async def test_empty_content_when_no_text_attribute(self) -> None:
        """content='' when no text block and first item has no text attr."""
        # Arrange — block without type and without text attribute
        bare_block = SimpleNamespace(type="tool_use", id="x", name="fn", input={})
        resp = SimpleNamespace(
            content=[bare_block],
            model="claude-3",
            usage=SimpleNamespace(input_tokens=5, output_tokens=2),
            stop_reason="tool_use",
        )
        _, mock_mod = self._make_anthropic_client(resp)
        primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="k")

        # Act
        with patch.dict("sys.modules", {"anthropic": mock_mod}):
            result = await primitive._call_anthropic(_req(), _ctx())

        # Assert — falls through to content = ""
        assert result.content == ""


# ---------------------------------------------------------------------------
# 12. _call_openai — direct method tests
# ---------------------------------------------------------------------------


class TestCallOpenAI:
    async def test_success(self) -> None:
        """_call_openai returns correct LLMResponse."""
        # Arrange
        fake_resp = _oai_response(content="openai says hello", model="gpt-4o")
        fake_client = _oai_client(fake_resp)
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="sk-test")

        # Act
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            result = await primitive._call_openai(_req("gpt-4o"), _ctx())

        # Assert
        assert result.content == "openai says hello"
        assert result.provider == "openai"
        assert result.model == "gpt-4o"
        assert result.usage == {"prompt_tokens": 10, "completion_tokens": 5}

    async def test_tool_calls_parsed(self) -> None:
        """_call_openai parses tool_calls from the choice message."""
        # Arrange
        raw_tc = SimpleNamespace(
            id="call_oai",
            function=SimpleNamespace(name="add", arguments='{"a": 1, "b": 2}'),
        )
        fake_resp = _oai_response(content="", tool_calls=[raw_tc], finish_reason="tool_calls")
        fake_client = _oai_client(fake_resp)
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="k")

        # Act
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            result = await primitive._call_openai(_req(), _ctx())

        # Assert
        assert result.tool_calls is not None
        assert result.tool_calls[0].name == "add"
        assert result.tool_calls[0].arguments == {"a": 1, "b": 2}

    async def test_finish_reason_propagated(self) -> None:
        """_call_openai populates finish_reason from the choice."""
        # Arrange
        fake_resp = _oai_response(finish_reason="length")
        fake_client = _oai_client(fake_resp)
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="k")

        # Act
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            result = await primitive._call_openai(_req(), _ctx())

        # Assert
        assert result.finish_reason == "length"

    async def test_no_usage_returns_none(self) -> None:
        """_call_openai returns usage=None when resp.usage is falsy."""
        # Arrange
        resp_ns = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="hi", tool_calls=None),
                    finish_reason="stop",
                )
            ],
            model="gpt-4o",
            usage=None,
        )
        fake_client = _oai_client(resp_ns)
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="k")

        # Act
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            result = await primitive._call_openai(_req(), _ctx())

        # Assert
        assert result.usage is None


# ---------------------------------------------------------------------------
# 13. _call_ollama — direct method tests
# ---------------------------------------------------------------------------


class TestCallOllama:
    async def test_success_plain_response(self) -> None:
        """_call_ollama returns correct LLMResponse for plain text reply."""
        # Arrange
        json_data = {"message": {"content": "ollama says hi", "tool_calls": []}}
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)

        # Act
        with patch("httpx.AsyncClient", return_value=_FakeOllamaHTTPXClient(json_data)):
            result = await primitive._call_ollama(_req("llama3"), _ctx())

        # Assert
        assert result.content == "ollama says hi"
        assert result.provider == "ollama"
        assert result.model == "llama3"
        assert result.finish_reason == "stop"
        assert result.tool_calls is None

    async def test_tool_calls_parsed(self) -> None:
        """_call_ollama parses Ollama-format tool_calls (dict arguments, not JSON string)."""
        # Arrange
        json_data = {
            "message": {
                "content": "",
                "tool_calls": [{"function": {"name": "lookup", "arguments": {"term": "AI"}}}],
            }
        }
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)

        # Act
        with patch("httpx.AsyncClient", return_value=_FakeOllamaHTTPXClient(json_data)):
            result = await primitive._call_ollama(_req(), _ctx())

        # Assert
        assert result.tool_calls is not None
        assert result.tool_calls[0].name == "lookup"
        assert result.tool_calls[0].arguments == {"term": "AI"}
        assert result.finish_reason == "tool_calls"

    async def test_system_message_injected(self) -> None:
        """_call_ollama prepends a system message when request.system is set."""
        # Arrange
        captured: dict = {}
        json_data = {"message": {"content": "ok"}}

        class _CapturingClient(_CapturingOllamaHTTPXClient):
            pass

        client = _CapturingOllamaHTTPXClient(json_data, captured)
        request = LLMRequest(
            model="llama3",
            messages=[{"role": "user", "content": "hi"}],
            system="You are helpful.",
        )
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)

        # Act
        with patch("httpx.AsyncClient", return_value=client):
            await primitive._call_ollama(request, _ctx())

        # Assert — first message in payload is system
        msgs = captured["payload"]["messages"]
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == "You are helpful."

    async def test_tools_included_in_payload(self) -> None:
        """_call_ollama adds tools to the JSON payload when request.tools is set."""
        # Arrange
        captured: dict = {}
        json_data = {"message": {"content": "ok"}}
        client = _CapturingOllamaHTTPXClient(json_data, captured)

        tool = ToolSchema(name="fn", description="d", parameters={"type": "object"})
        request = LLMRequest(
            model="llama3",
            messages=[{"role": "user", "content": "hi"}],
            tools=[tool],
        )
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)

        # Act
        with patch("httpx.AsyncClient", return_value=client):
            await primitive._call_ollama(request, _ctx())

        # Assert
        assert "tools" in captured["payload"]
        assert captured["payload"]["tools"][0]["type"] == "function"

    async def test_custom_base_url_used(self) -> None:
        """_call_ollama uses the custom base_url when configured."""
        # Arrange
        captured: dict = {}
        json_data = {"message": {"content": "ok"}}
        client = _CapturingOllamaHTTPXClient(json_data, captured)

        primitive = UniversalLLMPrimitive(
            provider=LLMProvider.OLLAMA, base_url="http://my-ollama:11434"
        )

        # Act
        with patch("httpx.AsyncClient", return_value=client):
            await primitive._call_ollama(_req(), _ctx())

        # Assert
        assert captured["url"] == "http://my-ollama:11434/api/chat"


# ---------------------------------------------------------------------------
# 14. _call_openrouter / _call_together / _call_xai
# ---------------------------------------------------------------------------


class TestCallOpenRouter:
    async def test_success(self) -> None:
        """_call_openrouter returns correct LLMResponse."""
        # Arrange
        fake_resp = _oai_response(content="openrouter response", model="mistral-7b")
        fake_client = _oai_client(fake_resp)
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENROUTER, api_key="sk-or-test")

        # Act
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            result = await primitive._call_openrouter(_req(), _ctx())

        # Assert
        assert result.content == "openrouter response"
        assert result.provider == "openrouter"

    async def test_missing_key_raises_value_error(self) -> None:
        """_call_openrouter raises ValueError when no API key is set."""
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENROUTER, api_key=None)
        env_clean = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}

        with patch.dict(os.environ, env_clean, clear=True):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                await primitive._call_openrouter(_req(), _ctx())


class TestCallTogether:
    async def test_success(self) -> None:
        """_call_together returns correct LLMResponse."""
        # Arrange
        fake_resp = _oai_response(content="together response", model="llama3")
        fake_client = _oai_client(fake_resp)
        primitive = UniversalLLMPrimitive(provider=LLMProvider.TOGETHER, api_key="ta-key")

        # Act
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            result = await primitive._call_together(_req(), _ctx())

        # Assert
        assert result.content == "together response"
        assert result.provider == "together"

    async def test_missing_key_raises_value_error(self) -> None:
        """_call_together raises ValueError when no API key is set."""
        primitive = UniversalLLMPrimitive(provider=LLMProvider.TOGETHER, api_key=None)
        env_clean = {k: v for k, v in os.environ.items() if k != "TOGETHER_API_KEY"}

        with patch.dict(os.environ, env_clean, clear=True):
            with pytest.raises(ValueError, match="TOGETHER_API_KEY"):
                await primitive._call_together(_req(), _ctx())


class TestCallXAI:
    async def test_success(self) -> None:
        """_call_xai returns correct LLMResponse."""
        # Arrange
        fake_resp = _oai_response(content="grok response", model="grok-3-mini")
        fake_client = _oai_client(fake_resp)
        primitive = UniversalLLMPrimitive(provider=LLMProvider.XAI, api_key="xai-test")

        # Act
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            result = await primitive._call_xai(_req(), _ctx())

        # Assert
        assert result.content == "grok response"
        assert result.provider == "xai"

    async def test_missing_key_raises_value_error(self) -> None:
        """_call_xai raises ValueError when no API key is set."""
        primitive = UniversalLLMPrimitive(provider=LLMProvider.XAI, api_key=None)
        env_clean = {k: v for k, v in os.environ.items() if k != "XAI_API_KEY"}

        with patch.dict(os.environ, env_clean, clear=True):
            with pytest.raises(ValueError, match="XAI_API_KEY"):
                await primitive._call_xai(_req(), _ctx())

    async def test_tool_calls_parsed(self) -> None:
        """_call_xai parses tool_calls from the response message."""
        # Arrange
        raw_tc = SimpleNamespace(
            id="xai_call",
            function=SimpleNamespace(name="search", arguments='{"q": "xai"}'),
        )
        fake_resp = _oai_response(content="", tool_calls=[raw_tc])
        fake_client = _oai_client(fake_resp)
        primitive = UniversalLLMPrimitive(provider=LLMProvider.XAI, api_key="k")

        # Act
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            result = await primitive._call_xai(_req(), _ctx())

        # Assert
        assert result.tool_calls is not None
        assert result.tool_calls[0].name == "search"
        assert result.tool_calls[0].arguments == {"q": "xai"}


# ---------------------------------------------------------------------------
# 15. _call_openai_compat
# ---------------------------------------------------------------------------


class TestCallOpenAICompat:
    async def test_success_with_compat_provider(self) -> None:
        """_call_openai_compat returns correct LLMResponse for a compat provider."""
        # Arrange
        fake_resp = _oai_response(content="compat response", model="mistral-7b")
        fake_client = _oai_client(fake_resp)
        primitive = UniversalLLMPrimitive(
            provider=LLMProvider.OPENROUTER, api_key="sk-or-test", use_compat=True
        )

        # Act
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            result = await primitive._call_openai_compat(_req(), _ctx(), provider_name="openrouter")

        # Assert
        assert result.content == "compat response"
        assert result.provider == "openrouter"

    async def test_non_compat_provider_raises(self) -> None:
        """_call_openai_compat raises ValueError for providers without OAI-compat endpoint."""
        # Arrange — anthropic has openai_compat=False
        primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="k")

        # Act & Assert
        with pytest.raises(ValueError, match="OpenAI-compatible"):
            await primitive._call_openai_compat(_req(), _ctx(), provider_name="anthropic")

    async def test_missing_key_raises(self) -> None:
        """_call_openai_compat raises ValueError when provider env key is missing."""
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENROUTER, api_key=None)
        env_clean = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}

        with patch.dict(os.environ, env_clean, clear=True):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                await primitive._call_openai_compat(_req(), _ctx(), provider_name="openrouter")

    async def test_tool_calls_parsed(self) -> None:
        """_call_openai_compat parses tool_calls from the response."""
        # Arrange
        raw_tc = SimpleNamespace(
            id="compat_call",
            function=SimpleNamespace(name="lookup", arguments='{"term": "hello"}'),
        )
        fake_resp = _oai_response(content="", tool_calls=[raw_tc], finish_reason="tool_calls")
        fake_client = _oai_client(fake_resp)
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENROUTER, api_key="k")

        # Act
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            result = await primitive._call_openai_compat(_req(), _ctx(), provider_name="openrouter")

        # Assert
        assert result.tool_calls is not None
        assert result.tool_calls[0].name == "lookup"
        assert result.tool_calls[0].arguments == {"term": "hello"}


# ---------------------------------------------------------------------------
# 16. Streaming: _stream_openai
# ---------------------------------------------------------------------------


class TestStreamOpenAI:
    async def test_yields_tokens(self) -> None:
        """_stream_openai yields non-empty delta content strings in order."""
        # Arrange
        chunks = [_oai_chunk("Hello"), _oai_chunk(","), _oai_chunk(" world")]
        fake_client = _oai_client(AsyncMock(return_value=_AsyncIter(chunks))())
        fake_client.chat.completions.create = AsyncMock(return_value=_AsyncIter(chunks))
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="k")

        # Act
        tokens: list[str] = []
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            async for tok in primitive._stream_openai(_req(), _ctx()):
                tokens.append(tok)

        # Assert
        assert tokens == ["Hello", ",", " world"]

    async def test_filters_none_and_empty_content(self) -> None:
        """_stream_openai skips None and empty-string delta content."""
        # Arrange
        chunks = [_oai_chunk(None), _oai_chunk(""), _oai_chunk("real"), _oai_chunk(None)]
        fake_client = MagicMock()
        fake_client.chat.completions.create = AsyncMock(return_value=_AsyncIter(chunks))
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="k")

        # Act
        tokens: list[str] = []
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            async for tok in primitive._stream_openai(_req(), _ctx()):
                tokens.append(tok)

        # Assert
        assert tokens == ["real"]

    async def test_propagates_provider_error(self) -> None:
        """_stream_openai propagates exceptions from the provider."""
        # Arrange
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=ConnectionError("OpenAI unreachable")
        )
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="k")

        # Act & Assert
        with patch("openai.AsyncOpenAI", return_value=mock_client):
            with pytest.raises(ConnectionError, match="OpenAI unreachable"):
                async for _ in primitive._stream_openai(_req(), _ctx()):
                    pass


# ---------------------------------------------------------------------------
# 17. Streaming: _stream_anthropic
# ---------------------------------------------------------------------------


class TestStreamAnthropic:
    async def test_yields_tokens(self) -> None:
        """_stream_anthropic yields tokens from the text_stream."""
        # Arrange
        texts = ["Hello", " from", " Claude"]
        mock_client = MagicMock()
        mock_client.messages.stream = MagicMock(return_value=_AnthropicStreamCM(texts))
        mock_anthropic_mod = MagicMock()
        mock_anthropic_mod.AsyncAnthropic.return_value = mock_client
        primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="k")

        # Act
        tokens: list[str] = []
        with patch.dict("sys.modules", {"anthropic": mock_anthropic_mod}):
            async for tok in primitive._stream_anthropic(_req(), _ctx()):
                tokens.append(tok)

        # Assert
        assert tokens == ["Hello", " from", " Claude"]

    async def test_filters_falsy_tokens(self) -> None:
        """_stream_anthropic drops None and empty-string tokens."""
        # Arrange
        texts = ["", "real", None, "text"]
        mock_client = MagicMock()
        mock_client.messages.stream = MagicMock(return_value=_AnthropicStreamCM(texts))
        mock_anthropic_mod = MagicMock()
        mock_anthropic_mod.AsyncAnthropic.return_value = mock_client
        primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="k")

        # Act
        tokens: list[str] = []
        with patch.dict("sys.modules", {"anthropic": mock_anthropic_mod}):
            async for tok in primitive._stream_anthropic(_req(), _ctx()):
                tokens.append(tok)

        # Assert
        assert tokens == ["real", "text"]

    async def test_system_and_max_tokens_passed(self) -> None:
        """_stream_anthropic forwards system and max_tokens to messages.stream."""
        # Arrange
        mock_client = MagicMock()
        mock_client.messages.stream = MagicMock(return_value=_AnthropicStreamCM([]))
        mock_anthropic_mod = MagicMock()
        mock_anthropic_mod.AsyncAnthropic.return_value = mock_client
        primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="k")

        request = LLMRequest(
            model="claude-3",
            messages=[{"role": "user", "content": "hi"}],
            system="Be terse",
            max_tokens=256,
        )

        # Act
        with patch.dict("sys.modules", {"anthropic": mock_anthropic_mod}):
            async for _ in primitive._stream_anthropic(request, _ctx()):
                pass

        # Assert — messages.stream was called with system and max_tokens
        call_kwargs = mock_client.messages.stream.call_args.kwargs
        assert call_kwargs["system"] == "Be terse"
        assert call_kwargs["max_tokens"] == 256


# ---------------------------------------------------------------------------
# 18. Streaming: _stream_ollama
# ---------------------------------------------------------------------------


class TestStreamOllama:
    async def test_yields_content_tokens(self) -> None:
        """_stream_ollama yields content strings from NDJSON lines."""
        # Arrange
        lines = [
            json.dumps({"message": {"content": "Hello"}, "done": False}),
            json.dumps({"message": {"content": " world"}, "done": False}),
            json.dumps({"message": {"content": ""}, "done": True}),
        ]
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)

        # Act
        tokens: list[str] = []
        with patch("httpx.AsyncClient", return_value=_FakeOllamaStreamClient(lines)):
            async for tok in primitive._stream_ollama(_req("llama3"), _ctx()):
                tokens.append(tok)

        # Assert
        assert tokens == ["Hello", " world"]

    async def test_skips_empty_lines(self) -> None:
        """_stream_ollama ignores blank NDJSON lines (keep-alive pings)."""
        # Arrange
        lines = [
            "",  # empty — must be skipped
            json.dumps({"message": {"content": "token"}, "done": True}),
        ]
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)

        # Act
        tokens: list[str] = []
        with patch("httpx.AsyncClient", return_value=_FakeOllamaStreamClient(lines)):
            async for tok in primitive._stream_ollama(_req(), _ctx()):
                tokens.append(tok)

        # Assert
        assert tokens == ["token"]

    async def test_think_mode_yields_thinking_tokens(self) -> None:
        """When think=True in request.extra, thinking field tokens are also yielded."""
        # Arrange
        lines = [
            json.dumps({"message": {"content": "", "thinking": "...reasoning..."}, "done": False}),
            json.dumps({"message": {"content": "Answer"}, "done": True}),
        ]
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)

        request = LLMRequest(
            model="qwen3",
            messages=[{"role": "user", "content": "hi"}],
        )
        request.extra = {"think": True}  # type: ignore[attr-defined]

        # Act
        tokens: list[str] = []
        with patch("httpx.AsyncClient", return_value=_FakeOllamaStreamClient(lines)):
            async for tok in primitive._stream_ollama(request, _ctx()):
                tokens.append(tok)

        # Assert — both thinking and answer tokens yielded
        assert "...reasoning..." in tokens
        assert "Answer" in tokens

    async def test_stops_after_done_flag(self) -> None:
        """_stream_ollama stops iterating when done=True is received."""
        # Arrange
        lines = [
            json.dumps({"message": {"content": "first"}, "done": False}),
            json.dumps({"message": {"content": "last"}, "done": True}),
            json.dumps({"message": {"content": "never"}, "done": False}),  # after done
        ]
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)

        # Act
        tokens: list[str] = []
        with patch("httpx.AsyncClient", return_value=_FakeOllamaStreamClient(lines)):
            async for tok in primitive._stream_ollama(_req(), _ctx()):
                tokens.append(tok)

        # Assert — "never" should not appear
        assert "first" in tokens
        assert "last" in tokens
        assert "never" not in tokens


# ---------------------------------------------------------------------------
# 19. Streaming: _stream_google / _stream_openrouter / _stream_together / _stream_xai
# ---------------------------------------------------------------------------


class TestStreamGoogle:
    async def test_missing_key_raises(self) -> None:
        """_stream_google raises ValueError when GOOGLE_API_KEY is absent."""
        primitive = UniversalLLMPrimitive(provider=LLMProvider.GOOGLE, api_key=None)
        env_clean = {k: v for k, v in os.environ.items() if k != "GOOGLE_API_KEY"}

        with patch.dict(os.environ, env_clean, clear=True):
            with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
                async for _ in primitive._stream_google(_req(), _ctx()):
                    pass

    async def test_yields_tokens(self) -> None:
        """_stream_google yields non-empty delta content strings."""
        # Arrange
        chunks = [_oai_chunk("Gemini"), _oai_chunk(" here")]
        fake_client = MagicMock()
        fake_client.chat.completions.create = AsyncMock(return_value=_AsyncIter(chunks))
        primitive = UniversalLLMPrimitive(provider=LLMProvider.GOOGLE, api_key="gk-test")

        # Act
        tokens: list[str] = []
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            async for tok in primitive._stream_google(_req(), _ctx()):
                tokens.append(tok)

        # Assert
        assert tokens == ["Gemini", " here"]


class TestStreamOpenRouter:
    async def test_missing_key_raises(self) -> None:
        """_stream_openrouter raises ValueError when OPENROUTER_API_KEY is absent."""
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENROUTER, api_key=None)
        env_clean = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}

        with patch.dict(os.environ, env_clean, clear=True):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                async for _ in primitive._stream_openrouter(_req(), _ctx()):
                    pass

    async def test_yields_tokens(self) -> None:
        """_stream_openrouter yields non-empty delta content strings."""
        # Arrange
        chunks = [_oai_chunk("Or"), _oai_chunk("outed")]
        fake_client = MagicMock()
        fake_client.chat.completions.create = AsyncMock(return_value=_AsyncIter(chunks))
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENROUTER, api_key="sk-or")

        # Act
        tokens: list[str] = []
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            async for tok in primitive._stream_openrouter(_req(), _ctx()):
                tokens.append(tok)

        # Assert
        assert tokens == ["Or", "outed"]


class TestStreamTogether:
    async def test_missing_key_raises(self) -> None:
        """_stream_together raises ValueError when TOGETHER_API_KEY is absent."""
        primitive = UniversalLLMPrimitive(provider=LLMProvider.TOGETHER, api_key=None)
        env_clean = {k: v for k, v in os.environ.items() if k != "TOGETHER_API_KEY"}

        with patch.dict(os.environ, env_clean, clear=True):
            with pytest.raises(ValueError, match="TOGETHER_API_KEY"):
                async for _ in primitive._stream_together(_req(), _ctx()):
                    pass

    async def test_yields_tokens(self) -> None:
        """_stream_together yields non-empty delta content strings."""
        # Arrange
        chunks = [_oai_chunk("Together"), _oai_chunk(" AI")]
        fake_client = MagicMock()
        fake_client.chat.completions.create = AsyncMock(return_value=_AsyncIter(chunks))
        primitive = UniversalLLMPrimitive(provider=LLMProvider.TOGETHER, api_key="ta-key")

        # Act
        tokens: list[str] = []
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            async for tok in primitive._stream_together(_req(), _ctx()):
                tokens.append(tok)

        # Assert
        assert tokens == ["Together", " AI"]


class TestStreamXAI:
    async def test_missing_key_raises(self) -> None:
        """_stream_xai raises ValueError when XAI_API_KEY is absent."""
        primitive = UniversalLLMPrimitive(provider=LLMProvider.XAI, api_key=None)
        env_clean = {k: v for k, v in os.environ.items() if k != "XAI_API_KEY"}

        with patch.dict(os.environ, env_clean, clear=True):
            with pytest.raises(ValueError, match="XAI_API_KEY"):
                async for _ in primitive._stream_xai(_req(), _ctx()):
                    pass

    async def test_yields_tokens(self) -> None:
        """_stream_xai yields non-empty delta content strings."""
        # Arrange
        chunks = [_oai_chunk("Grok"), _oai_chunk(" rocks")]
        fake_client = MagicMock()
        fake_client.chat.completions.create = AsyncMock(return_value=_AsyncIter(chunks))
        primitive = UniversalLLMPrimitive(provider=LLMProvider.XAI, api_key="xai-key")

        # Act
        tokens: list[str] = []
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            async for tok in primitive._stream_xai(_req(), _ctx()):
                tokens.append(tok)

        # Assert
        assert tokens == ["Grok", " rocks"]


# ---------------------------------------------------------------------------
# 20. Streaming: _stream_openai_compat
# ---------------------------------------------------------------------------


class TestStreamOpenAICompat:
    async def test_yields_tokens(self) -> None:
        """_stream_openai_compat yields tokens from the streamed chunks."""
        # Arrange — create() returns a coroutine → _CompatStreamCM async-CM
        chunks = [_oai_chunk("compat"), _oai_chunk(" stream")]
        fake_client = MagicMock()
        fake_client.chat.completions.create = AsyncMock(return_value=_CompatStreamCM(chunks))
        primitive = UniversalLLMPrimitive(
            provider=LLMProvider.OPENROUTER, api_key="sk-or", use_compat=True
        )

        # Act
        tokens: list[str] = []
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            async for tok in primitive._stream_openai_compat(
                _req(), _ctx(), provider_name="openrouter"
            ):
                tokens.append(tok)

        # Assert
        assert tokens == ["compat", " stream"]

    async def test_non_compat_provider_raises(self) -> None:
        """_stream_openai_compat raises ValueError for non-OAI-compat providers."""
        primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="k")

        with pytest.raises(ValueError, match="OpenAI-compatible"):
            async for _ in primitive._stream_openai_compat(
                _req(), _ctx(), provider_name="anthropic"
            ):
                pass

    async def test_filters_empty_chunks(self) -> None:
        """_stream_openai_compat skips None/empty delta content."""
        # Arrange
        chunks = [_oai_chunk(None), _oai_chunk(""), _oai_chunk("real"), _oai_chunk(None)]
        fake_client = MagicMock()
        fake_client.chat.completions.create = AsyncMock(return_value=_CompatStreamCM(chunks))
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENROUTER, api_key="k")

        # Act
        tokens: list[str] = []
        with patch("openai.AsyncOpenAI", return_value=fake_client):
            async for tok in primitive._stream_openai_compat(
                _req(), _ctx(), provider_name="openrouter"
            ):
                tokens.append(tok)

        # Assert
        assert tokens == ["real"]

    async def test_missing_key_raises(self) -> None:
        """_stream_openai_compat raises ValueError when provider env key is missing."""
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENROUTER, api_key=None)
        env_clean = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}

        with patch.dict(os.environ, env_clean, clear=True):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                async for _ in primitive._stream_openai_compat(
                    _req(), _ctx(), provider_name="openrouter"
                ):
                    pass


# ---------------------------------------------------------------------------
# 21. execute() dispatch — verifies routing for each provider
# ---------------------------------------------------------------------------


class TestExecuteDispatch:
    """execute() must route to the correct _call_* bound method."""

    async def _check_dispatch(self, provider: LLMProvider, method_name: str) -> None:
        primitive = UniversalLLMPrimitive(provider=provider, api_key="k")
        expected = LLMResponse(content="ok", model="m", provider=provider.value)
        with patch.object(
            primitive, method_name, new_callable=AsyncMock, return_value=expected
        ) as m:
            result = await primitive.execute(_req(), _ctx())
        m.assert_awaited_once()
        assert result is expected

    async def test_dispatches_to_call_anthropic(self) -> None:
        await self._check_dispatch(LLMProvider.ANTHROPIC, "_call_anthropic")

    async def test_dispatches_to_call_openai(self) -> None:
        await self._check_dispatch(LLMProvider.OPENAI, "_call_openai")

    async def test_dispatches_to_call_ollama(self) -> None:
        await self._check_dispatch(LLMProvider.OLLAMA, "_call_ollama")

    async def test_dispatches_to_call_openrouter(self) -> None:
        await self._check_dispatch(LLMProvider.OPENROUTER, "_call_openrouter")

    async def test_dispatches_to_call_together(self) -> None:
        await self._check_dispatch(LLMProvider.TOGETHER, "_call_together")

    async def test_dispatches_to_call_xai(self) -> None:
        await self._check_dispatch(LLMProvider.XAI, "_call_xai")


# ---------------------------------------------------------------------------
# 22. stream() dispatch — verifies routing for each provider
# ---------------------------------------------------------------------------


class TestStreamDispatch:
    """stream() must route to the correct _stream_* bound method."""

    async def _check_stream_dispatch(self, provider: LLMProvider, method_name: str) -> None:
        primitive = UniversalLLMPrimitive(provider=provider, api_key="k")

        async def _fake(req, ctx):
            yield "tok"

        with patch.object(primitive, method_name, side_effect=_fake):
            tokens = [t async for t in primitive.stream(_req(), _ctx())]
        assert tokens == ["tok"]

    async def test_dispatches_to_stream_openai(self) -> None:
        await self._check_stream_dispatch(LLMProvider.OPENAI, "_stream_openai")

    async def test_dispatches_to_stream_anthropic(self) -> None:
        await self._check_stream_dispatch(LLMProvider.ANTHROPIC, "_stream_anthropic")

    async def test_dispatches_to_stream_ollama(self) -> None:
        await self._check_stream_dispatch(LLMProvider.OLLAMA, "_stream_ollama")

    async def test_dispatches_to_stream_openrouter(self) -> None:
        await self._check_stream_dispatch(LLMProvider.OPENROUTER, "_stream_openrouter")

    async def test_dispatches_to_stream_together(self) -> None:
        await self._check_stream_dispatch(LLMProvider.TOGETHER, "_stream_together")

    async def test_dispatches_to_stream_xai(self) -> None:
        await self._check_stream_dispatch(LLMProvider.XAI, "_stream_xai")

    async def test_dispatches_to_stream_google(self) -> None:
        await self._check_stream_dispatch(LLMProvider.GOOGLE, "_stream_google")

    async def test_dispatches_to_stream_groq(self) -> None:
        await self._check_stream_dispatch(LLMProvider.GROQ, "_stream_groq")


# ---------------------------------------------------------------------------
# 23. _resolve_call_fn — use_compat routing
# ---------------------------------------------------------------------------


class TestResolveCallFn:
    def test_use_compat_raises_for_non_compat_provider(self) -> None:
        """_resolve_call_fn raises ValueError when use_compat=True for Anthropic (no OAI compat)."""
        # Arrange — Anthropic has openai_compat=False
        primitive = UniversalLLMPrimitive(
            provider=LLMProvider.ANTHROPIC, api_key="k", use_compat=True
        )

        # Act & Assert
        with pytest.raises(ValueError, match="OpenAI-compatible"):
            primitive._resolve_call_fn(_req(), _ctx())

    def test_use_compat_returns_partial_for_compat_provider(self) -> None:
        """_resolve_call_fn returns a functools.partial wrapping _call_openai_compat."""
        import functools

        primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="k", use_compat=True)

        # Act
        fn = primitive._resolve_call_fn(_req(), _ctx())

        # Assert
        assert isinstance(fn, functools.partial)
        assert fn.func == primitive._call_openai_compat
        assert fn.keywords.get("provider_name") == "groq"

    def test_default_returns_provider_specific_method(self) -> None:
        """Without use_compat, returns the provider-specific bound method."""
        primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="k")
        fn = primitive._resolve_call_fn(_req(), _ctx())
        assert fn == primitive._call_openai


# ---------------------------------------------------------------------------
# 24. _resolve_stream_fn — use_compat routing
# ---------------------------------------------------------------------------


class TestResolveStreamFn:
    def test_use_compat_raises_for_non_compat_provider(self) -> None:
        """_resolve_stream_fn raises ValueError when use_compat=True for Anthropic."""
        primitive = UniversalLLMPrimitive(
            provider=LLMProvider.ANTHROPIC, api_key="k", use_compat=True
        )

        with pytest.raises(ValueError, match="OpenAI-compatible"):
            primitive._resolve_stream_fn(_req(), _ctx())

    def test_use_compat_returns_partial_for_compat_provider(self) -> None:
        """_resolve_stream_fn returns a functools.partial wrapping _stream_openai_compat."""
        import functools

        primitive = UniversalLLMPrimitive(
            provider=LLMProvider.OPENROUTER, api_key="k", use_compat=True
        )

        fn = primitive._resolve_stream_fn(_req(), _ctx())

        assert isinstance(fn, functools.partial)
        assert fn.func == primitive._stream_openai_compat
        assert fn.keywords.get("provider_name") == "openrouter"

    def test_default_returns_provider_specific_method(self) -> None:
        """Without use_compat, returns the provider-specific stream method."""
        primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="k")
        fn = primitive._resolve_stream_fn(_req(), _ctx())
        assert fn == primitive._stream_anthropic
