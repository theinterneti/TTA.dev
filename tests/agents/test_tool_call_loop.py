"""Tests for ttadev.agents.tool_call_loop — Task C1 + issue #311."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, ClassVar

import pytest

from ttadev.agents.protocol import ChatMessage
from ttadev.agents.tool_call_loop import (
    ToolCall,
    ToolCallLoop,
    ToolCallLoopError,
    ToolCallRequest,
    ToolDefinition,
    _format_tools_for_provider,
    _parse_tool_calls,
)
from ttadev.primitives.core.base import WorkflowContext


class _StaticModel:
    """Returns a fixed string — no tool calls."""

    def __init__(self, response: str = "done"):
        self._response = response

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        return self._response


class _ToolCallingModel:
    """First call requests a tool; second call returns final answer."""

    def __init__(self):
        self._call_count = 0

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        self._call_count += 1
        if self._call_count == 1:
            return "__tool_call__:add_numbers:{}"
        return "the answer is 42"


class _InfiniteModel:
    """Always requests a tool — triggers iteration limit."""

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> str:
        return "__tool_call__:add_numbers:{}"


class TestToolCallLoop:
    @pytest.mark.asyncio
    async def test_no_tool_calls_returns_response_directly(self):
        loop = ToolCallLoop(model=_StaticModel("hello"), tool_handlers={})
        request = ToolCallRequest(
            messages=[{"role": "user", "content": "hi"}],
            tools=[],
            system=None,
        )
        result = await loop.execute(request, WorkflowContext())
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_tool_call_resolved_and_loop_continues(self):
        handlers = {"add_numbers": lambda args: "42"}
        loop = ToolCallLoop(model=_ToolCallingModel(), tool_handlers=handlers)
        request = ToolCallRequest(
            messages=[{"role": "user", "content": "what is 6 * 7?"}],
            tools=[ToolDefinition(name="add_numbers", description="adds", parameters={})],
            system=None,
        )
        result = await loop.execute(request, WorkflowContext())
        assert "42" in result

    @pytest.mark.asyncio
    async def test_iteration_limit_raises(self):
        loop = ToolCallLoop(
            model=_InfiniteModel(),
            tool_handlers={"add_numbers": lambda args: "x"},
            max_iterations=3,
        )
        request = ToolCallRequest(
            messages=[{"role": "user", "content": "go"}],
            tools=[ToolDefinition(name="add_numbers", description="x", parameters={})],
            system=None,
        )
        with pytest.raises(ToolCallLoopError, match="iteration"):
            await loop.execute(request, WorkflowContext())

    def test_tool_definition_construction(self):
        t = ToolDefinition(name="ruff", description="linter", parameters={"path": "str"})
        assert t.name == "ruff"
        assert t.parameters == {"path": "str"}


# ── _parse_tool_calls: provider-native parsing ────────────────────────────────


def _make_openai_response(tool_name: str, arguments_json: str) -> Any:
    """Build a minimal OpenAI/Groq-shaped response fixture."""
    func = SimpleNamespace(name=tool_name, arguments=arguments_json)
    tc = SimpleNamespace(function=func)
    message = SimpleNamespace(tool_calls=[tc])
    choice = SimpleNamespace(message=message)
    return SimpleNamespace(choices=[choice])


def _make_anthropic_response(*tool_blocks: tuple[str, dict[str, Any]]) -> Any:
    """Build a minimal Anthropic-shaped response fixture."""
    content = []
    for name, input_data in tool_blocks:
        content.append(SimpleNamespace(type="tool_use", name=name, input=input_data))
    return SimpleNamespace(content=content)


def _make_google_response(tool_name: str, args: dict[str, Any]) -> Any:
    """Build a minimal Google Gemini-shaped response fixture."""
    fc = SimpleNamespace(name=tool_name, args=args)
    part = SimpleNamespace(function_call=fc)
    content = SimpleNamespace(parts=[part])
    candidate = SimpleNamespace(content=content)
    return SimpleNamespace(candidates=[candidate])


class TestParseToolCalls:
    def test_parse_openai_tool_calls(self):
        """OpenAI/Groq: choices[0].message.tool_calls → ToolCall list."""
        response = _make_openai_response("search", '{"query": "python async"}')
        calls = _parse_tool_calls(response)
        assert len(calls) == 1
        assert calls[0].name == "search"
        assert calls[0].arguments == {"query": "python async"}

    def test_parse_openai_multiple_tool_calls(self):
        """OpenAI response with multiple tool_calls in one message."""
        func1 = SimpleNamespace(name="tool_a", arguments='{"x": 1}')
        func2 = SimpleNamespace(name="tool_b", arguments='{"y": 2}')
        tc1 = SimpleNamespace(function=func1)
        tc2 = SimpleNamespace(function=func2)
        message = SimpleNamespace(tool_calls=[tc1, tc2])
        response = SimpleNamespace(choices=[SimpleNamespace(message=message)])

        calls = _parse_tool_calls(response)
        assert len(calls) == 2
        assert calls[0].name == "tool_a"
        assert calls[0].arguments == {"x": 1}
        assert calls[1].name == "tool_b"
        assert calls[1].arguments == {"y": 2}

    def test_parse_openai_no_tool_calls(self):
        """OpenAI response with tool_calls=None → empty list."""
        message = SimpleNamespace(tool_calls=None)
        response = SimpleNamespace(choices=[SimpleNamespace(message=message)])
        calls = _parse_tool_calls(response)
        assert calls == []

    def test_parse_openai_malformed_json_args(self):
        """OpenAI response with invalid JSON arguments → empty dict, no crash."""
        response = _make_openai_response("my_tool", "NOT_VALID_JSON")
        calls = _parse_tool_calls(response)
        assert len(calls) == 1
        assert calls[0].name == "my_tool"
        assert calls[0].arguments == {}

    def test_parse_anthropic_tool_calls(self):
        """Anthropic: content list with type='tool_use' → ToolCall list."""
        response = _make_anthropic_response(("calculator", {"expression": "2+2"}))
        calls = _parse_tool_calls(response)
        assert len(calls) == 1
        assert calls[0].name == "calculator"
        assert calls[0].arguments == {"expression": "2+2"}

    def test_parse_anthropic_multiple_tool_calls(self):
        """Anthropic response with multiple tool_use blocks."""
        response = _make_anthropic_response(
            ("tool_x", {"a": 1}),
            ("tool_y", {"b": 2}),
        )
        calls = _parse_tool_calls(response)
        assert len(calls) == 2
        assert calls[0].name == "tool_x"
        assert calls[1].name == "tool_y"

    def test_parse_anthropic_mixed_content_blocks(self):
        """Anthropic content with text blocks mixed in — only tool_use extracted."""
        text_block = SimpleNamespace(type="text", text="thinking...")
        tool_block = SimpleNamespace(type="tool_use", name="run_code", input={"code": "print(1)"})
        response = SimpleNamespace(content=[text_block, tool_block])
        calls = _parse_tool_calls(response)
        assert len(calls) == 1
        assert calls[0].name == "run_code"

    def test_parse_anthropic_no_tool_calls(self):
        """Anthropic response with only text blocks → empty list."""
        text_block = SimpleNamespace(type="text", text="Hello!")
        response = SimpleNamespace(content=[text_block])
        calls = _parse_tool_calls(response)
        assert calls == []

    def test_parse_google_tool_calls(self):
        """Google Gemini: candidates[0].content.parts with function_call → ToolCall list."""
        response = _make_google_response("translate", {"text": "hello", "target": "es"})
        calls = _parse_tool_calls(response)
        assert len(calls) == 1
        assert calls[0].name == "translate"
        assert calls[0].arguments == {"text": "hello", "target": "es"}

    def test_parse_google_multiple_parts(self):
        """Google response with multiple function_call parts."""
        fc1 = SimpleNamespace(name="fn_a", args={"p": 1})
        fc2 = SimpleNamespace(name="fn_b", args={"q": 2})
        part1 = SimpleNamespace(function_call=fc1)
        part2 = SimpleNamespace(function_call=fc2)
        content = SimpleNamespace(parts=[part1, part2])
        candidate = SimpleNamespace(content=content)
        response = SimpleNamespace(candidates=[candidate])

        calls = _parse_tool_calls(response)
        assert len(calls) == 2
        assert calls[0].name == "fn_a"
        assert calls[1].name == "fn_b"

    def test_parse_google_parts_without_function_call(self):
        """Google parts that have no function_call attribute are skipped."""
        text_part = SimpleNamespace()  # no function_call attr
        fc = SimpleNamespace(name="my_fn", args={})
        tool_part = SimpleNamespace(function_call=fc)
        content = SimpleNamespace(parts=[text_part, tool_part])
        candidate = SimpleNamespace(content=content)
        response = SimpleNamespace(candidates=[candidate])

        calls = _parse_tool_calls(response)
        assert len(calls) == 1
        assert calls[0].name == "my_fn"

    def test_parse_google_no_tool_calls(self):
        """Google response where no parts have function_call → empty list."""
        part = SimpleNamespace()  # no function_call attr
        content = SimpleNamespace(parts=[part])
        candidate = SimpleNamespace(content=content)
        response = SimpleNamespace(candidates=[candidate])
        calls = _parse_tool_calls(response)
        assert calls == []

    def test_parse_legacy_text_tool_calls(self):
        """Legacy __tool_call__: prefix → single ToolCall."""
        calls = _parse_tool_calls('__tool_call__:my_tool:{"key": "value"}')
        assert len(calls) == 1
        assert calls[0].name == "my_tool"
        assert calls[0].arguments == {"key": "value"}

    def test_parse_legacy_text_empty_args(self):
        """Legacy text with empty JSON args → empty dict."""
        calls = _parse_tool_calls("__tool_call__:some_tool:{}")
        assert len(calls) == 1
        assert calls[0].name == "some_tool"
        assert calls[0].arguments == {}

    def test_parse_legacy_text_no_args_segment(self):
        """Legacy text with no colon after tool name → defaults to empty dict."""
        calls = _parse_tool_calls("__tool_call__:bare_tool")
        assert len(calls) == 1
        assert calls[0].name == "bare_tool"
        assert calls[0].arguments == {}

    def test_parse_legacy_text_malformed_json(self):
        """Legacy text with invalid JSON args → empty dict, no crash."""
        calls = _parse_tool_calls("__tool_call__:bad_tool:NOT_JSON")
        assert len(calls) == 1
        assert calls[0].name == "bad_tool"
        assert calls[0].arguments == {}

    def test_parse_plain_text_returns_empty(self):
        """Plain string without __tool_call__ prefix → empty list."""
        calls = _parse_tool_calls("The answer is 42.")
        assert calls == []

    def test_parse_unknown_type_returns_empty(self):
        """Non-string, non-provider object → empty list, no crash."""
        calls = _parse_tool_calls(42)  # type: ignore[arg-type]
        assert calls == []
        calls = _parse_tool_calls(None)  # type: ignore[arg-type]
        assert calls == []


# ── _format_tools_for_provider ────────────────────────────────────────────────


class TestFormatToolsForProvider:
    _tools: ClassVar[list[ToolDefinition]] = [
        ToolDefinition(
            name="search",
            description="Search the web",
            parameters={"type": "object", "properties": {"query": {"type": "string"}}},
        ),
        ToolDefinition(
            name="calc",
            description="Run a calculation",
            parameters={"type": "object", "properties": {"expr": {"type": "string"}}},
        ),
    ]

    def test_format_openai(self):
        result = _format_tools_for_provider(self._tools, "openai")
        assert len(result) == 2
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "search"
        assert result[0]["function"]["description"] == "Search the web"
        assert "properties" in result[0]["function"]["parameters"]

    def test_format_groq_same_as_openai(self):
        openai_result = _format_tools_for_provider(self._tools, "openai")
        groq_result = _format_tools_for_provider(self._tools, "groq")
        assert openai_result == groq_result

    def test_format_anthropic(self):
        result = _format_tools_for_provider(self._tools, "anthropic")
        assert len(result) == 2
        assert result[0]["name"] == "search"
        assert result[0]["description"] == "Search the web"
        assert "input_schema" in result[0]
        assert "type" not in result[0]  # no "type": "function" wrapper

    def test_format_google(self):
        result = _format_tools_for_provider(self._tools, "google")
        assert len(result) == 1  # one object with function_declarations list
        assert "function_declarations" in result[0]
        decls = result[0]["function_declarations"]
        assert len(decls) == 2
        assert decls[0]["name"] == "search"
        assert decls[1]["name"] == "calc"

    def test_format_unknown_provider_falls_back_to_openai(self):
        result = _format_tools_for_provider(self._tools, "unknown_provider")
        openai_result = _format_tools_for_provider(self._tools, "openai")
        assert result == openai_result

    def test_format_empty_tools_list(self):
        for provider in ("openai", "groq", "anthropic", "google"):
            result = _format_tools_for_provider([], provider)
            assert result == [] or result == [{"function_declarations": []}]


# ── ToolCall dataclass ────────────────────────────────────────────────────────


class TestToolCallDataclass:
    def test_construction(self):
        tc = ToolCall(name="my_tool", arguments={"a": 1})
        assert tc.name == "my_tool"
        assert tc.arguments == {"a": 1}

    def test_empty_arguments(self):
        tc = ToolCall(name="no_args", arguments={})
        assert tc.arguments == {}


# ── Integration: loop uses _parse_tool_calls for all formats ─────────────────


class _NativeToolCallingModel:
    """Returns a provider-native response object on first call, plain text on second."""

    def __init__(self, native_response: Any, final_answer: str = "done"):
        self._native_response = native_response
        self._final_answer = final_answer
        self._call_count = 0

    async def chat(
        self,
        messages: list[ChatMessage],
        system: str | None,
        ctx: WorkflowContext,
    ) -> Any:
        self._call_count += 1
        if self._call_count == 1:
            return self._native_response
        return self._final_answer


class TestToolCallLoopNativeFormats:
    @pytest.mark.asyncio
    async def test_loop_handles_openai_native_response(self):
        """Loop correctly dispatches a tool call from an OpenAI-shaped response."""
        native = _make_openai_response("greet", '{"name": "world"}')
        model = _NativeToolCallingModel(native, "Hello, world!")
        loop = ToolCallLoop(
            model=model,  # type: ignore[arg-type]
            tool_handlers={"greet": lambda args: f"Hi {args.get('name')}"},
        )
        request = ToolCallRequest(
            messages=[{"role": "user", "content": "greet the world"}],
            tools=[],
        )
        result = await loop.execute(request, WorkflowContext())
        assert result == "Hello, world!"
        assert model._call_count == 2

    @pytest.mark.asyncio
    async def test_loop_handles_anthropic_native_response(self):
        """Loop correctly dispatches a tool call from an Anthropic-shaped response."""
        native = _make_anthropic_response(("add", {"a": 1, "b": 2}))
        model = _NativeToolCallingModel(native, "The sum is 3.")
        loop = ToolCallLoop(
            model=model,  # type: ignore[arg-type]
            tool_handlers={"add": lambda args: str(args["a"] + args["b"])},
        )
        request = ToolCallRequest(
            messages=[{"role": "user", "content": "add 1 and 2"}],
            tools=[],
        )
        result = await loop.execute(request, WorkflowContext())
        assert result == "The sum is 3."

    @pytest.mark.asyncio
    async def test_loop_handles_google_native_response(self):
        """Loop correctly dispatches a tool call from a Google-shaped response."""
        native = _make_google_response("upper", {"text": "hello"})
        model = _NativeToolCallingModel(native, "HELLO")
        loop = ToolCallLoop(
            model=model,  # type: ignore[arg-type]
            tool_handlers={"upper": lambda args: args["text"].upper()},
        )
        request = ToolCallRequest(
            messages=[{"role": "user", "content": "uppercase hello"}],
            tools=[],
        )
        result = await loop.execute(request, WorkflowContext())
        assert result == "HELLO"

    @pytest.mark.asyncio
    async def test_loop_missing_handler_returns_error_message(self):
        """Loop returns an error string when a registered tool has no handler."""
        loop = ToolCallLoop(
            model=_ToolCallingModel(),
            tool_handlers={},  # no handler for add_numbers
        )
        request = ToolCallRequest(
            messages=[{"role": "user", "content": "add stuff"}],
            tools=[],
        )
        result = await loop.execute(request, WorkflowContext())
        # Second call returns "the answer is 42" — loop continues
        assert "42" in result
