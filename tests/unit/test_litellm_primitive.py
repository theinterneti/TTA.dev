"""Unit tests for LiteLLMPrimitive.

All litellm network calls are mocked — no real API keys required.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.core import WorkflowContext
from ttadev.primitives.llm.litellm_primitive import (
    LiteLLMPrimitive,
    _maybe_configure_langfuse,
    make_resilient_llm,
)
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    ToolSchema,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_ctx(workflow_id: str = "test-run") -> WorkflowContext:
    return WorkflowContext(workflow_id=workflow_id)


def _make_litellm_response(
    content: str = "Hello!",
    model: str = "groq/llama-3.1-8b-instant",
    prompt_tokens: int = 10,
    completion_tokens: int = 5,
    finish_reason: str = "stop",
    tool_calls: list | None = None,
) -> MagicMock:
    """Build a realistic litellm ModelResponse mock."""
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls

    choice = MagicMock()
    choice.message = msg
    choice.finish_reason = finish_reason

    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    usage.total_tokens = prompt_tokens + completion_tokens

    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    resp.model = model
    return resp


def _make_request(
    model: str = "groq/llama-3.1-8b-instant",
    system: str | None = None,
    tools: list[ToolSchema] | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.7,
) -> LLMRequest:
    return LLMRequest(
        model=model,
        messages=[{"role": "user", "content": "Hi"}],
        system=system,
        tools=tools,
        max_tokens=max_tokens,
        temperature=temperature,
    )


# ---------------------------------------------------------------------------
# _resolve_model
# ---------------------------------------------------------------------------


class TestResolveModel:
    def test_full_litellm_string_passthrough(self) -> None:
        llm = LiteLLMPrimitive()
        req = _make_request(model="groq/llama-3.1-8b-instant")
        assert llm._resolve_model(req) == "groq/llama-3.1-8b-instant"

    def test_provider_prefix_prepended_for_short_model(self) -> None:
        llm = LiteLLMPrimitive(provider=LLMProvider.GROQ)
        req = _make_request(model="llama-3.1-8b-instant")
        assert llm._resolve_model(req) == "groq/llama-3.1-8b-instant"

    def test_short_model_without_provider_unchanged(self) -> None:
        llm = LiteLLMPrimitive()
        req = _make_request(model="llama-3.1-8b-instant")
        assert llm._resolve_model(req) == "llama-3.1-8b-instant"

    def test_full_string_with_provider_bound_unchanged(self) -> None:
        """Explicit provider in model string takes precedence."""
        llm = LiteLLMPrimitive(provider=LLMProvider.ANTHROPIC)
        req = _make_request(model="groq/llama-3.1-8b-instant")
        assert llm._resolve_model(req) == "groq/llama-3.1-8b-instant"

    def test_raw_string_provider(self) -> None:
        llm = LiteLLMPrimitive(provider="together_ai")
        req = _make_request(model="mixtral-8x7b")
        assert llm._resolve_model(req) == "together_ai/mixtral-8x7b"

    @pytest.mark.parametrize(
        "provider_enum,expected_prefix",
        [
            (LLMProvider.GROQ, "groq"),
            (LLMProvider.ANTHROPIC, "anthropic"),
            (LLMProvider.OPENAI, "openai"),
            (LLMProvider.OLLAMA, "ollama"),
            (LLMProvider.GOOGLE, "gemini"),
            (LLMProvider.OPENROUTER, "openrouter"),
        ],
    )
    def test_provider_enum_mapping(self, provider_enum: LLMProvider, expected_prefix: str) -> None:
        llm = LiteLLMPrimitive(provider=provider_enum)
        assert llm._provider_prefix == expected_prefix


# ---------------------------------------------------------------------------
# _parse_tool_calls
# ---------------------------------------------------------------------------


class TestParseToolCalls:
    def test_none_input(self) -> None:
        assert LiteLLMPrimitive._parse_tool_calls(None) is None

    def test_empty_list(self) -> None:
        assert LiteLLMPrimitive._parse_tool_calls([]) is None

    def test_single_tool_call_json_string(self) -> None:
        fn = SimpleNamespace(name="get_weather", arguments='{"city": "London"}')
        tc = SimpleNamespace(id="call_abc123", function=fn)
        result = LiteLLMPrimitive._parse_tool_calls([tc])
        assert result is not None
        assert len(result) == 1
        assert result[0].name == "get_weather"
        assert result[0].arguments == {"city": "London"}
        assert result[0].id == "call_abc123"

    def test_tool_call_dict_arguments(self) -> None:
        fn = SimpleNamespace(name="search", arguments={"query": "AI"})
        tc = SimpleNamespace(id="call_xyz", function=fn)
        result = LiteLLMPrimitive._parse_tool_calls([tc])
        assert result is not None
        assert result[0].arguments == {"query": "AI"}

    def test_multiple_tool_calls(self) -> None:
        calls = [
            SimpleNamespace(
                id=f"call_{i}",
                function=SimpleNamespace(name=f"fn_{i}", arguments=f'{{"x": {i}}}'),
            )
            for i in range(3)
        ]
        result = LiteLLMPrimitive._parse_tool_calls(calls)
        assert result is not None
        assert len(result) == 3
        assert result[2].arguments == {"x": 2}

    def test_malformed_entry_skipped(self) -> None:
        fn_good = SimpleNamespace(name="valid", arguments='{"k": "v"}')
        tc_good = SimpleNamespace(id="c1", function=fn_good)
        tc_bad = "not-an-object"  # will raise AttributeError

        result = LiteLLMPrimitive._parse_tool_calls([tc_good, tc_bad])  # type: ignore[list-item]
        assert result is not None
        assert len(result) == 1
        assert result[0].name == "valid"

    def test_invalid_json_skipped(self) -> None:
        fn = SimpleNamespace(name="broken", arguments="not-json{{{")
        tc = SimpleNamespace(id="c1", function=fn)
        result = LiteLLMPrimitive._parse_tool_calls([tc])
        assert result is None  # all entries failed → None


# ---------------------------------------------------------------------------
# execute() — happy path
# ---------------------------------------------------------------------------


class TestExecute:
    @pytest.mark.asyncio
    async def test_basic_text_response(self) -> None:
        llm = LiteLLMPrimitive()
        ctx = _make_ctx()
        mock_resp = _make_litellm_response(content="Hello!", model="groq/llama-3.1-8b-instant")

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp):
            result = await llm.execute(_make_request(), ctx)

        assert isinstance(result, LLMResponse)
        assert result.content == "Hello!"
        assert result.model == "groq/llama-3.1-8b-instant"
        assert result.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_usage_mapped(self) -> None:
        llm = LiteLLMPrimitive()
        ctx = _make_ctx()
        mock_resp = _make_litellm_response(prompt_tokens=42, completion_tokens=17, content="ok")

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp):
            result = await llm.execute(_make_request(), ctx)

        assert result.usage is not None
        assert result.usage["prompt_tokens"] == 42
        assert result.usage["completion_tokens"] == 17
        assert result.usage["total_tokens"] == 59

    @pytest.mark.asyncio
    async def test_system_prompt_prepended_to_messages(self) -> None:
        llm = LiteLLMPrimitive()
        ctx = _make_ctx()
        mock_resp = _make_litellm_response()
        captured: dict = {}

        async def fake_acompletion(**kwargs: object) -> MagicMock:
            captured.update(kwargs)
            return mock_resp

        with patch("litellm.acompletion", side_effect=fake_acompletion):
            await llm.execute(_make_request(system="You are helpful."), ctx)

        messages = captured["messages"]
        assert messages[0] == {"role": "system", "content": "You are helpful."}
        assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_provider_prefix_applied(self) -> None:
        llm = LiteLLMPrimitive(provider=LLMProvider.GROQ)
        ctx = _make_ctx()
        mock_resp = _make_litellm_response()
        captured: dict = {}

        async def fake_acompletion(**kwargs: object) -> MagicMock:
            captured.update(kwargs)
            return mock_resp

        with patch("litellm.acompletion", side_effect=fake_acompletion):
            await llm.execute(_make_request(model="llama-3.1-8b-instant"), ctx)

        assert captured["model"] == "groq/llama-3.1-8b-instant"

    @pytest.mark.asyncio
    async def test_max_tokens_forwarded(self) -> None:
        llm = LiteLLMPrimitive()
        ctx = _make_ctx()
        mock_resp = _make_litellm_response()
        captured: dict = {}

        async def fake_acompletion(**kwargs: object) -> MagicMock:
            captured.update(kwargs)
            return mock_resp

        with patch("litellm.acompletion", side_effect=fake_acompletion):
            await llm.execute(_make_request(max_tokens=512), ctx)

        assert captured.get("max_tokens") == 512

    @pytest.mark.asyncio
    async def test_max_tokens_absent_when_not_set(self) -> None:
        llm = LiteLLMPrimitive()
        ctx = _make_ctx()
        mock_resp = _make_litellm_response()
        captured: dict = {}

        async def fake_acompletion(**kwargs: object) -> MagicMock:
            captured.update(kwargs)
            return mock_resp

        with patch("litellm.acompletion", side_effect=fake_acompletion):
            await llm.execute(_make_request(max_tokens=None), ctx)

        assert "max_tokens" not in captured

    @pytest.mark.asyncio
    async def test_tool_calls_mapped(self) -> None:
        llm = LiteLLMPrimitive()
        ctx = _make_ctx()
        fn = SimpleNamespace(name="get_weather", arguments='{"city": "Paris"}')
        tc_mock = SimpleNamespace(id="call_1", function=fn)
        mock_resp = _make_litellm_response(content="", tool_calls=[tc_mock])

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp):
            result = await llm.execute(_make_request(), ctx)

        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "get_weather"
        assert result.tool_calls[0].arguments == {"city": "Paris"}

    @pytest.mark.asyncio
    async def test_tools_forwarded_as_openai_format(self) -> None:
        llm = LiteLLMPrimitive()
        ctx = _make_ctx()
        schema = ToolSchema(
            name="search",
            description="Web search",
            parameters={"type": "object", "properties": {"q": {"type": "string"}}},
        )
        mock_resp = _make_litellm_response()
        captured: dict = {}

        async def fake_acompletion(**kwargs: object) -> MagicMock:
            captured.update(kwargs)
            return mock_resp

        with patch("litellm.acompletion", side_effect=fake_acompletion):
            await llm.execute(_make_request(tools=[schema]), ctx)

        assert "tools" in captured
        assert captured["tools"][0]["type"] == "function"
        assert captured["tools"][0]["function"]["name"] == "search"

    @pytest.mark.asyncio
    async def test_exception_propagates(self) -> None:
        llm = LiteLLMPrimitive()
        ctx = _make_ctx()

        with patch(
            "litellm.acompletion",
            new_callable=AsyncMock,
            side_effect=RuntimeError("rate limit"),
        ):
            with pytest.raises(RuntimeError, match="rate limit"):
                await llm.execute(_make_request(), ctx)

    @pytest.mark.asyncio
    async def test_fallbacks_forwarded(self) -> None:
        fallbacks = ["anthropic/claude-3-haiku-20240307", "ollama/llama3.2"]
        llm = LiteLLMPrimitive(fallbacks=fallbacks)
        ctx = _make_ctx()
        mock_resp = _make_litellm_response()
        captured: dict = {}

        async def fake_acompletion(**kwargs: object) -> MagicMock:
            captured.update(kwargs)
            return mock_resp

        with patch("litellm.acompletion", side_effect=fake_acompletion):
            await llm.execute(_make_request(), ctx)

        assert captured.get("fallbacks") == fallbacks

    @pytest.mark.asyncio
    async def test_metadata_forwarded(self) -> None:
        llm = LiteLLMPrimitive(metadata={"session_id": "abc"})
        ctx = _make_ctx()
        mock_resp = _make_litellm_response()
        captured: dict = {}

        async def fake_acompletion(**kwargs: object) -> MagicMock:
            captured.update(kwargs)
            return mock_resp

        with patch("litellm.acompletion", side_effect=fake_acompletion):
            await llm.execute(_make_request(), ctx)

        assert captured.get("metadata") == {"session_id": "abc"}

    @pytest.mark.asyncio
    async def test_provider_set_in_response(self) -> None:
        llm = LiteLLMPrimitive()
        ctx = _make_ctx()
        mock_resp = _make_litellm_response(model="groq/llama-3.1-8b-instant")

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp):
            result = await llm.execute(_make_request(model="groq/llama-3.1-8b-instant"), ctx)

        assert result.provider == "groq"


# ---------------------------------------------------------------------------
# stream()
# ---------------------------------------------------------------------------


class TestStream:
    @pytest.mark.asyncio
    async def test_streaming_yields_content(self) -> None:
        llm = LiteLLMPrimitive()
        ctx = _make_ctx()

        def _make_chunk(text: str) -> MagicMock:
            delta = MagicMock()
            delta.content = text
            choice = MagicMock()
            choice.delta = delta
            chunk = MagicMock()
            chunk.choices = [choice]
            return chunk

        async def fake_stream() -> AsyncMock:
            for tok in ["Hello", ", ", "world", "!"]:
                yield _make_chunk(tok)

        # acompletion with stream=True returns the async generator itself
        mock_stream = fake_stream()

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_stream):
            tokens = []
            async for token in llm.stream(_make_request(), ctx):
                tokens.append(token)

        assert tokens == ["Hello", ", ", "world", "!"]
        assert "".join(tokens) == "Hello, world!"

    @pytest.mark.asyncio
    async def test_streaming_skips_empty_content(self) -> None:
        llm = LiteLLMPrimitive()
        ctx = _make_ctx()

        def _make_chunk(text: str | None) -> MagicMock:
            delta = MagicMock()
            delta.content = text
            choice = MagicMock()
            choice.delta = delta
            chunk = MagicMock()
            chunk.choices = [choice]
            return chunk

        async def fake_stream() -> AsyncMock:
            for tok in ["Hello", None, "", "!"]:
                yield _make_chunk(tok)

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=fake_stream()):
            tokens = []
            async for token in llm.stream(_make_request(), ctx):
                tokens.append(token)

        assert tokens == ["Hello", "!"]  # None and "" are skipped

    @pytest.mark.asyncio
    async def test_streaming_stream_true_forwarded(self) -> None:
        llm = LiteLLMPrimitive()
        ctx = _make_ctx()
        captured: dict = {}

        async def fake_acompletion(**kwargs: object) -> AsyncMock:
            captured.update(kwargs)

            async def _empty() -> AsyncMock:  # type: ignore[return]
                return
                yield

            return _empty()

        with patch("litellm.acompletion", side_effect=fake_acompletion):
            async for _ in llm.stream(_make_request(), ctx):
                pass

        assert captured.get("stream") is True


# ---------------------------------------------------------------------------
# Langfuse configuration
# ---------------------------------------------------------------------------


class TestLangfuseConfig:
    def test_no_key_no_configure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When LANGFUSE_SECRET_KEY is absent, callback is not added."""
        monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)

        # Reset module-level flag
        import ttadev.primitives.llm.litellm_primitive as mod

        original = mod._LANGFUSE_CONFIGURED
        mod._LANGFUSE_CONFIGURED = False
        try:
            mock_litellm = MagicMock()
            mock_litellm.success_callback = []
            with patch.dict("sys.modules", {"litellm": mock_litellm}):
                _maybe_configure_langfuse()
            assert "langfuse" not in (mock_litellm.success_callback or [])
        finally:
            mod._LANGFUSE_CONFIGURED = original

    def test_key_present_adds_callback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When LANGFUSE_SECRET_KEY is set, 'langfuse' is appended to callbacks."""
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "test-secret")
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "test-public")

        import ttadev.primitives.llm.litellm_primitive as mod

        original = mod._LANGFUSE_CONFIGURED
        mod._LANGFUSE_CONFIGURED = False
        try:
            mock_litellm = MagicMock()
            mock_litellm.success_callback = []
            with patch.dict("sys.modules", {"litellm": mock_litellm}):
                _maybe_configure_langfuse()
            assert "langfuse" in mock_litellm.success_callback
        finally:
            mod._LANGFUSE_CONFIGURED = original

    def test_idempotent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Calling twice when already configured does nothing."""
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "s")

        import ttadev.primitives.llm.litellm_primitive as mod

        original = mod._LANGFUSE_CONFIGURED
        mod._LANGFUSE_CONFIGURED = True
        try:
            mock_litellm = MagicMock()
            mock_litellm.success_callback = []
            with patch.dict("sys.modules", {"litellm": mock_litellm}):
                _maybe_configure_langfuse()
            # Should NOT have been called because flag was already True — callback list unchanged
            assert "langfuse" not in (mock_litellm.success_callback or [])
        finally:
            mod._LANGFUSE_CONFIGURED = original


# ---------------------------------------------------------------------------
# make_resilient_llm
# ---------------------------------------------------------------------------


class TestMakeResilientLLM:
    def test_returns_workflow_primitive(self) -> None:
        from ttadev.primitives.core import WorkflowPrimitive

        llm = make_resilient_llm(provider=LLMProvider.GROQ)
        assert isinstance(llm, WorkflowPrimitive)

    def test_no_cache_returns_retry_primitive(self) -> None:
        from ttadev.primitives import RetryPrimitive

        llm = make_resilient_llm(cache=False)
        assert isinstance(llm, RetryPrimitive)

    def test_with_cache_wraps_in_cache(self) -> None:
        from ttadev.primitives import CachePrimitive

        llm = make_resilient_llm(cache=True)
        assert isinstance(llm, CachePrimitive)

    @pytest.mark.asyncio
    async def test_execute_via_factory(self) -> None:
        llm = make_resilient_llm(provider=LLMProvider.GROQ, cache=False, retry_attempts=1)
        ctx = _make_ctx()
        mock_resp = _make_litellm_response(content="Factory works!")

        with patch("litellm.acompletion", new_callable=AsyncMock, return_value=mock_resp):
            result = await llm.execute(
                LLMRequest(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": "test"}],
                ),
                ctx,
            )

        assert result.content == "Factory works!"

    def test_litellm_fallbacks_forwarded(self) -> None:
        """make_resilient_llm passes litellm_fallbacks to the inner LiteLLMPrimitive."""
        from ttadev.primitives import CachePrimitive, RetryPrimitive

        fallbacks = ["anthropic/claude-3-haiku-20240307"]
        llm = make_resilient_llm(litellm_fallbacks=fallbacks)
        # Unwrap: CachePrimitive → RetryPrimitive → LiteLLMPrimitive
        retry = llm.primitive if isinstance(llm, CachePrimitive) else llm
        inner = retry.primitive if isinstance(retry, RetryPrimitive) else retry
        assert isinstance(inner, LiteLLMPrimitive)
        assert inner._fallbacks == fallbacks
