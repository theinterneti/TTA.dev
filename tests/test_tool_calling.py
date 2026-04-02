"""Tests for native provider tool-calling support — GitHub issue #275.

Covers:
- ToolSchema.to_openai() wire format (basic and strict mode)
- ToolSchema.to_anthropic() wire format
- ToolCall dataclass fields
- LLMRequest backward-compat defaults (tools=None, tool_choice="auto")
- LLMResponse backward-compat defaults (tool_calls=None, finish_reason=None)
- OpenAI provider: request with tools → LLMResponse.tool_calls populated
- OpenAI provider: request without tools → LLMResponse.tool_calls is None
- OpenAI provider: finish_reason propagated ("stop" and "tool_calls")
- OpenAI provider: multiple tool calls in one response
- Groq provider: request with tools → LLMResponse.tool_calls populated
- Anthropic provider: request with tools → LLMResponse.tool_calls populated
- Anthropic provider: request without tools → LLMResponse.tool_calls is None
- Anthropic provider: multiple tool_use blocks parsed correctly
- Ollama provider: request with tools → LLMResponse.tool_calls populated
- Ollama provider: request without tools → LLMResponse.tool_calls is None
- Ollama provider: finish_reason set to "tool_calls" when tools returned
- _parse_openai_tool_calls with empty/None input returns None
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from ttadev.primitives import WorkflowContext
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    ToolCall,
    ToolSchema,
    UniversalLLMPrimitive,
)

# ── Shared fixtures ───────────────────────────────────────────────────────────

WEATHER_TOOL = ToolSchema(
    name="get_weather",
    description="Return current weather for a location.",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
        },
        "required": ["location"],
    },
)

SEARCH_TOOL = ToolSchema(
    name="web_search",
    description="Search the web for information.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
        },
        "required": ["query"],
    },
)


def _make_ctx() -> WorkflowContext:
    return WorkflowContext()


def _make_request(tools: list[ToolSchema] | None = None, **kwargs: Any) -> LLMRequest:
    return LLMRequest(
        model="test-model",
        messages=[{"role": "user", "content": "What is the weather in NYC?"}],
        tools=tools,
        **kwargs,
    )


# ── ToolSchema.to_openai() ────────────────────────────────────────────────────


def test_tool_schema_to_openai_basic_structure():
    """to_openai() must produce OpenAI function-calling wire format."""
    result = WEATHER_TOOL.to_openai()

    assert result["type"] == "function"
    func = result["function"]
    assert func["name"] == "get_weather"
    assert func["description"] == "Return current weather for a location."
    assert func["parameters"] == WEATHER_TOOL.parameters
    assert "strict" not in func, "strict key must be absent when strict=False"


def test_tool_schema_to_openai_strict_mode_includes_strict_key():
    """to_openai() must include strict=True in the function dict when strict=True."""
    strict_tool = ToolSchema(
        name="strict_tool",
        description="A strict tool.",
        parameters={"type": "object", "properties": {}, "required": []},
        strict=True,
    )
    result = strict_tool.to_openai()

    assert result["function"]["strict"] is True


def test_tool_schema_to_openai_strict_false_omits_strict_key():
    """to_openai() must NOT include strict when strict=False (the default)."""
    tool = ToolSchema(
        name="normal",
        description="Normal tool.",
        parameters={"type": "object", "properties": {}},
    )
    result = tool.to_openai()
    assert "strict" not in result["function"]


# ── ToolSchema.to_anthropic() ─────────────────────────────────────────────────


def test_tool_schema_to_anthropic_basic_structure():
    """to_anthropic() must produce Anthropic tool_use wire format."""
    result = WEATHER_TOOL.to_anthropic()

    assert result["name"] == "get_weather"
    assert result["description"] == "Return current weather for a location."
    assert result["input_schema"] == WEATHER_TOOL.parameters


def test_tool_schema_to_anthropic_input_schema_is_full_parameters():
    """input_schema in the Anthropic format must be the full parameters dict."""
    result = SEARCH_TOOL.to_anthropic()

    assert result["input_schema"]["type"] == "object"
    assert "query" in result["input_schema"]["properties"]
    assert result["input_schema"]["required"] == ["query"]


# ── ToolCall dataclass ────────────────────────────────────────────────────────


def test_tool_call_dataclass_stores_fields_correctly():
    """ToolCall must store id, name, and arguments as provided."""
    tc = ToolCall(id="call_xyz", name="get_weather", arguments={"location": "NYC"})

    assert tc.id == "call_xyz"
    assert tc.name == "get_weather"
    assert tc.arguments == {"location": "NYC"}


# ── LLMRequest backward-compat defaults ──────────────────────────────────────


def test_llm_request_tools_defaults_to_none():
    """LLMRequest.tools must be None by default (backward compatible)."""
    req = LLMRequest(model="gpt-4o", messages=[])
    assert req.tools is None


def test_llm_request_tool_choice_defaults_to_auto():
    """LLMRequest.tool_choice must default to 'auto'."""
    req = LLMRequest(model="gpt-4o", messages=[])
    assert req.tool_choice == "auto"


# ── LLMResponse backward-compat defaults ─────────────────────────────────────


def test_llm_response_tool_calls_defaults_to_none():
    """LLMResponse.tool_calls must be None by default (backward compatible)."""
    resp = LLMResponse(content="hello", model="gpt-4o", provider="openai")
    assert resp.tool_calls is None


def test_llm_response_finish_reason_defaults_to_none():
    """LLMResponse.finish_reason must be None by default (backward compatible)."""
    resp = LLMResponse(content="hello", model="gpt-4o", provider="openai")
    assert resp.finish_reason is None


# ── _parse_openai_tool_calls helper ──────────────────────────────────────────


def test_parse_openai_tool_calls_none_input_returns_none():
    """_parse_openai_tool_calls(None) must return None."""
    assert UniversalLLMPrimitive._parse_openai_tool_calls(None) is None


def test_parse_openai_tool_calls_empty_list_returns_none():
    """_parse_openai_tool_calls([]) must return None."""
    assert UniversalLLMPrimitive._parse_openai_tool_calls([]) is None


# ── OpenAI provider tool-calling ─────────────────────────────────────────────


def _make_openai_mock_response(
    content: str = "",
    tool_calls: list[dict] | None = None,
    finish_reason: str = "stop",
    model: str = "gpt-4o",
) -> SimpleNamespace:
    """Build a mock openai ChatCompletion response."""
    raw_tc = None
    if tool_calls:
        raw_tc = [
            SimpleNamespace(
                id=tc["id"],
                function=SimpleNamespace(
                    name=tc["name"],
                    arguments=json.dumps(tc["arguments"]),
                ),
            )
            for tc in tool_calls
        ]
    message = SimpleNamespace(content=content or None, tool_calls=raw_tc)
    choice = SimpleNamespace(message=message, finish_reason=finish_reason)
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5)
    return SimpleNamespace(choices=[choice], model=model, usage=usage)


async def test_openai_provider_with_tools_populates_tool_calls():
    """OpenAI provider: tool call in response → LLMResponse.tool_calls populated."""
    mock_resp = _make_openai_mock_response(
        tool_calls=[{"id": "call_001", "name": "get_weather", "arguments": {"location": "NYC"}}],
        finish_reason="tool_calls",
    )
    primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="test-key")
    ctx = _make_ctx()
    request = _make_request(tools=[WEATHER_TOOL])

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
    mock_openai = MagicMock()
    mock_openai.AsyncOpenAI.return_value = mock_client

    with patch.dict("sys.modules", {"openai": mock_openai}):
        result = await primitive._call_openai(request, ctx)

    assert result.tool_calls is not None
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].id == "call_001"
    assert result.tool_calls[0].name == "get_weather"
    assert result.tool_calls[0].arguments == {"location": "NYC"}
    assert result.finish_reason == "tool_calls"


async def test_openai_provider_without_tools_has_none_tool_calls():
    """OpenAI provider: request without tools → LLMResponse.tool_calls is None."""
    mock_resp = _make_openai_mock_response(content="The weather is sunny.", finish_reason="stop")
    primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="test-key")
    ctx = _make_ctx()
    request = _make_request(tools=None)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
    mock_openai = MagicMock()
    mock_openai.AsyncOpenAI.return_value = mock_client

    with patch.dict("sys.modules", {"openai": mock_openai}):
        result = await primitive._call_openai(request, ctx)

    assert result.tool_calls is None
    assert result.content == "The weather is sunny."
    assert result.finish_reason == "stop"


async def test_openai_provider_finish_reason_stop():
    """OpenAI provider: finish_reason='stop' propagated to LLMResponse."""
    mock_resp = _make_openai_mock_response(content="Done.", finish_reason="stop")
    primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="test-key")
    ctx = _make_ctx()

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
    mock_openai = MagicMock()
    mock_openai.AsyncOpenAI.return_value = mock_client

    with patch.dict("sys.modules", {"openai": mock_openai}):
        result = await primitive._call_openai(_make_request(), ctx)

    assert result.finish_reason == "stop"


async def test_openai_provider_multiple_tool_calls_in_single_response():
    """OpenAI provider: multiple tool_calls parsed into list of ToolCall objects."""
    mock_resp = _make_openai_mock_response(
        tool_calls=[
            {"id": "call_001", "name": "get_weather", "arguments": {"location": "NYC"}},
            {"id": "call_002", "name": "web_search", "arguments": {"query": "NYC restaurants"}},
        ],
        finish_reason="tool_calls",
    )
    primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="test-key")
    ctx = _make_ctx()
    request = _make_request(tools=[WEATHER_TOOL, SEARCH_TOOL])

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
    mock_openai = MagicMock()
    mock_openai.AsyncOpenAI.return_value = mock_client

    with patch.dict("sys.modules", {"openai": mock_openai}):
        result = await primitive._call_openai(request, ctx)

    assert result.tool_calls is not None
    assert len(result.tool_calls) == 2
    assert result.tool_calls[0].name == "get_weather"
    assert result.tool_calls[1].name == "web_search"
    assert result.tool_calls[1].arguments == {"query": "NYC restaurants"}


# ── Groq provider tool-calling ────────────────────────────────────────────────


async def test_groq_provider_with_tools_populates_tool_calls():
    """Groq provider: tool call in response → LLMResponse.tool_calls populated."""
    raw_tc = [
        SimpleNamespace(
            id="groq_call_1",
            function=SimpleNamespace(
                name="get_weather",
                arguments=json.dumps({"location": "Paris", "unit": "celsius"}),
            ),
        )
    ]
    message = SimpleNamespace(content=None, tool_calls=raw_tc)
    choice = SimpleNamespace(message=message, finish_reason="tool_calls")
    usage = SimpleNamespace(prompt_tokens=12, completion_tokens=8)
    mock_resp = SimpleNamespace(
        choices=[choice], model="llama3-groq-70b-8192-tool-use-preview", usage=usage
    )

    primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="test-key")
    ctx = _make_ctx()
    request = _make_request(tools=[WEATHER_TOOL])

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
    mock_groq = MagicMock()
    mock_groq.AsyncGroq.return_value = mock_client

    with patch.dict("sys.modules", {"groq": mock_groq}):
        result = await primitive._call_groq(request, ctx)

    assert result.tool_calls is not None
    assert result.tool_calls[0].id == "groq_call_1"
    assert result.tool_calls[0].name == "get_weather"
    assert result.tool_calls[0].arguments == {"location": "Paris", "unit": "celsius"}
    assert result.finish_reason == "tool_calls"


# ── Anthropic provider tool-calling ───────────────────────────────────────────


def _make_anthropic_mock_response(
    text_content: str = "",
    tool_use_blocks: list[dict] | None = None,
    stop_reason: str = "end_turn",
    model: str = "claude-3-5-sonnet-20241022",
) -> SimpleNamespace:
    """Build a mock Anthropic messages.create response."""
    content_blocks = []
    if tool_use_blocks:
        for tb in tool_use_blocks:
            content_blocks.append(
                SimpleNamespace(type="tool_use", id=tb["id"], name=tb["name"], input=tb["input"])
            )
    if text_content:
        content_blocks.append(SimpleNamespace(type="text", text=text_content))

    usage = SimpleNamespace(input_tokens=15, output_tokens=20)
    return SimpleNamespace(
        content=content_blocks,
        model=model,
        usage=usage,
        stop_reason=stop_reason,
    )


async def test_anthropic_provider_with_tools_populates_tool_calls():
    """Anthropic provider: tool_use block → LLMResponse.tool_calls populated."""
    mock_resp = _make_anthropic_mock_response(
        tool_use_blocks=[
            {"id": "toolu_abc", "name": "get_weather", "input": {"location": "London"}},
        ],
        stop_reason="tool_use",
    )
    primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="test-key")
    ctx = _make_ctx()
    request = _make_request(tools=[WEATHER_TOOL])

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_resp)
    mock_anthropic = MagicMock()
    mock_anthropic.AsyncAnthropic.return_value = mock_client

    with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
        result = await primitive._call_anthropic(request, ctx)

    assert result.tool_calls is not None
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].id == "toolu_abc"
    assert result.tool_calls[0].name == "get_weather"
    assert result.tool_calls[0].arguments == {"location": "London"}
    assert result.finish_reason == "tool_use"


async def test_anthropic_provider_without_tools_has_none_tool_calls():
    """Anthropic provider: no tools in request → LLMResponse.tool_calls is None."""
    # Simulate legacy mock without type attribute (as in existing tests)
    mock_content = SimpleNamespace(text="Sunny in London.")
    usage = SimpleNamespace(input_tokens=5, output_tokens=10)
    mock_resp = SimpleNamespace(
        content=[mock_content],
        model="claude-3-5-sonnet-20241022",
        usage=usage,
        stop_reason="end_turn",
    )
    primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="test-key")
    ctx = _make_ctx()
    request = _make_request(tools=None)

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_resp)
    mock_anthropic = MagicMock()
    mock_anthropic.AsyncAnthropic.return_value = mock_client

    with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
        result = await primitive._call_anthropic(request, ctx)

    assert result.tool_calls is None
    assert result.content == "Sunny in London."


async def test_anthropic_provider_multiple_tool_calls():
    """Anthropic provider: multiple tool_use blocks → all parsed into tool_calls list."""
    mock_resp = _make_anthropic_mock_response(
        tool_use_blocks=[
            {"id": "toolu_001", "name": "get_weather", "input": {"location": "Tokyo"}},
            {"id": "toolu_002", "name": "web_search", "input": {"query": "Tokyo sights"}},
        ],
        stop_reason="tool_use",
    )
    primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="test-key")
    ctx = _make_ctx()
    request = _make_request(tools=[WEATHER_TOOL, SEARCH_TOOL])

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_resp)
    mock_anthropic = MagicMock()
    mock_anthropic.AsyncAnthropic.return_value = mock_client

    with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
        result = await primitive._call_anthropic(request, ctx)

    assert result.tool_calls is not None
    assert len(result.tool_calls) == 2
    names = [tc.name for tc in result.tool_calls]
    assert "get_weather" in names
    assert "web_search" in names


async def test_anthropic_provider_mixed_text_and_tool_calls():
    """Anthropic provider: response with both text and tool_use → both populated."""
    mock_resp = _make_anthropic_mock_response(
        text_content="Let me look that up.",
        tool_use_blocks=[
            {"id": "toolu_003", "name": "get_weather", "input": {"location": "Berlin"}},
        ],
        stop_reason="tool_use",
    )
    primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="test-key")
    ctx = _make_ctx()

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_resp)
    mock_anthropic = MagicMock()
    mock_anthropic.AsyncAnthropic.return_value = mock_client

    with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
        result = await primitive._call_anthropic(_make_request(tools=[WEATHER_TOOL]), ctx)

    assert result.content == "Let me look that up."
    assert result.tool_calls is not None
    assert result.tool_calls[0].name == "get_weather"


# ── Ollama provider tool-calling ──────────────────────────────────────────────


async def test_ollama_provider_with_tools_populates_tool_calls():
    """Ollama provider: tool_calls in response JSON → LLMResponse.tool_calls populated."""
    ollama_response = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "get_weather",
                        "arguments": {"location": "Sydney"},
                    }
                }
            ],
        },
        "done": True,
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = ollama_response
    mock_resp.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)
    ctx = _make_ctx()
    request = _make_request(tools=[WEATHER_TOOL])

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await primitive._call_ollama(request, ctx)

    assert result.tool_calls is not None
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].name == "get_weather"
    assert result.tool_calls[0].arguments == {"location": "Sydney"}
    assert result.tool_calls[0].id == "ollama_call_0"
    assert result.finish_reason == "tool_calls"


async def test_ollama_provider_without_tools_has_none_tool_calls():
    """Ollama provider: no tool_calls in response → LLMResponse.tool_calls is None."""
    ollama_response = {
        "message": {"role": "assistant", "content": "It is sunny in Sydney."},
        "done": True,
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = ollama_response
    mock_resp.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)
    ctx = _make_ctx()
    request = _make_request(tools=None)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await primitive._call_ollama(request, ctx)

    assert result.tool_calls is None
    assert result.content == "It is sunny in Sydney."
    assert result.finish_reason == "stop"


async def test_ollama_provider_finish_reason_is_stop_for_text_response():
    """Ollama provider: plain text response → finish_reason is 'stop'."""
    ollama_response = {
        "message": {"role": "assistant", "content": "42."},
        "done": True,
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = ollama_response
    mock_resp.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)
    ctx = _make_ctx()

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await primitive._call_ollama(_make_request(), ctx)

    assert result.finish_reason == "stop"


async def test_ollama_payload_includes_tools_when_set():
    """Ollama provider: tools in request → payload sent to /api/chat includes 'tools'."""
    ollama_response = {
        "message": {"role": "assistant", "content": ""},
        "done": True,
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = ollama_response
    mock_resp.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)
    ctx = _make_ctx()
    request = _make_request(tools=[WEATHER_TOOL])

    with patch("httpx.AsyncClient", return_value=mock_client):
        await primitive._call_ollama(request, ctx)

    call_kwargs = mock_client.post.call_args
    payload = call_kwargs[1]["json"] if "json" in call_kwargs[1] else call_kwargs[0][1]
    assert "tools" in payload
    assert payload["tools"][0]["type"] == "function"
    assert payload["tools"][0]["function"]["name"] == "get_weather"
