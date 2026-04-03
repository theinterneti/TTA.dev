"""Unit tests for the Gemini provider in UniversalLLMPrimitive.

Gemini is routed through the OpenAI-compatible endpoint
(https://generativelanguage.googleapis.com/v1beta/openai) using
``openai.AsyncOpenAI`` — *not* ``google.generativeai``.  All tests mock
the ``openai`` SDK response objects; no real API calls are made.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.core import WorkflowContext
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    UniversalLLMPrimitive,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="gemini-unit-test")


def _request(model: str = "models/gemini-2.5-flash-lite") -> LLMRequest:
    return LLMRequest(
        model=model,
        messages=[{"role": "user", "content": "Hello, Gemini!"}],
    )


def _make_fake_oai_response(
    *,
    content: str = "Gemini says hello",
    model: str = "models/gemini-2.5-flash-lite",
    prompt_tokens: int = 10,
    completion_tokens: int = 20,
) -> MagicMock:
    """Build a fake openai ChatCompletion response object."""
    message = SimpleNamespace(content=content, tool_calls=None)
    choice = SimpleNamespace(message=message, finish_reason="stop")
    usage = SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
    return SimpleNamespace(choices=[choice], model=model, usage=usage)


def _make_fake_oai_client(response: object) -> MagicMock:
    """Return a fake AsyncOpenAI client whose completions.create returns *response*."""
    create = AsyncMock(return_value=response)
    completions = MagicMock()
    completions.create = create
    chat = MagicMock()
    chat.completions = completions
    client = MagicMock()
    client.chat = chat
    return client


# ---------------------------------------------------------------------------
# 1. Enum value
# ---------------------------------------------------------------------------


def test_gemini_provider_enum_value() -> None:
    """LLMProvider.GOOGLE must have string value 'gemini'."""
    assert LLMProvider.GOOGLE.value == "google"


# ---------------------------------------------------------------------------
# 2. Successful _call_google via OpenAI-compat endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_call_google_success() -> None:
    """_call_google returns LLMResponse with correct content and provider.

    Arrange: fake openai.AsyncOpenAI returning a fixed text response.
    Act:     call _call_google directly.
    Assert:  LLMResponse.content matches; provider == 'gemini'; model correct.
    """
    fake_resp = _make_fake_oai_response(content="Hello from Gemini")
    fake_client = _make_fake_oai_client(fake_resp)

    primitive = UniversalLLMPrimitive(provider=LLMProvider.GOOGLE, api_key="fake-key")
    request = _request()
    ctx = _ctx()

    with patch(
        "openai.AsyncOpenAI",
        return_value=fake_client,
    ):
        result = await primitive._call_google(request, ctx)

    assert isinstance(result, LLMResponse)
    assert result.content == "Hello from Gemini"
    assert result.provider == "google"
    assert result.model == "models/gemini-2.5-flash-lite"


# ---------------------------------------------------------------------------
# 3. Usage metadata mapping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_call_google_maps_usage_metadata() -> None:
    """_call_google populates prompt_tokens and completion_tokens from usage.

    Arrange: fake response with known prompt_tokens / completion_tokens.
    Act:     call _call_google.
    Assert:  LLMResponse.usage dict contains expected values.
    """
    fake_resp = _make_fake_oai_response(
        content="token count test",
        prompt_tokens=42,
        completion_tokens=17,
    )
    fake_client = _make_fake_oai_client(fake_resp)

    primitive = UniversalLLMPrimitive(provider=LLMProvider.GOOGLE, api_key="fake-key")
    request = _request()
    ctx = _ctx()

    with patch(
        "openai.AsyncOpenAI",
        return_value=fake_client,
    ):
        result = await primitive._call_google(request, ctx)

    assert result.usage is not None
    assert result.usage["prompt_tokens"] == 42
    assert result.usage["completion_tokens"] == 17


# ---------------------------------------------------------------------------
# 4. Missing API key raises ValueError
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_call_google_missing_key_raises() -> None:
    """_call_google raises ValueError when no API key is available.

    Arrange: no api_key arg; GOOGLE_API_KEY not in environment.
    Act:     call _call_google.
    Assert:  ValueError raised; message mentions GOOGLE_API_KEY.
    """
    import os

    primitive = UniversalLLMPrimitive(provider=LLMProvider.GOOGLE, api_key=None)
    ctx = _ctx()

    # Ensure GOOGLE_API_KEY is absent from env for this test.
    env_without_key = {k: v for k, v in os.environ.items() if k != "GOOGLE_API_KEY"}
    with patch.dict(os.environ, env_without_key, clear=True):
        with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
            await primitive._call_google(_request(), ctx)


# ---------------------------------------------------------------------------
# 5. execute() dispatch to _call_google
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_dispatches_gemini() -> None:
    """execute() with provider=GEMINI delegates to _call_google.

    Arrange: UniversalLLMPrimitive(GEMINI), patch _call_google.
    Act:     await primitive.execute(request, ctx).
    Assert:  _call_google was called once with the correct arguments.
    """
    primitive = UniversalLLMPrimitive(provider=LLMProvider.GOOGLE, api_key="test-key")
    request = _request()
    ctx = _ctx()

    expected_response = LLMResponse(
        content="dispatched!", model="models/gemini-2.5-flash-lite", provider="google"
    )
    with patch.object(
        primitive,
        "_call_google",
        new_callable=AsyncMock,
        return_value=expected_response,
    ) as mock_call:
        result = await primitive.execute(request, ctx)

    mock_call.assert_awaited_once_with(request, ctx)
    assert result is expected_response


# ---------------------------------------------------------------------------
# 6. use_compat=True routes through _call_openai_compat
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_use_compat_routes_to_generic_helper() -> None:
    """use_compat=True bypasses _call_google and uses _call_openai_compat.

    Arrange: UniversalLLMPrimitive(GEMINI, use_compat=True).
    Act:     patch _call_openai_compat; await execute().
    Assert:  _call_openai_compat called with provider_name='gemini';
             _call_google never called.
    """
    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.GOOGLE, api_key="test-key", use_compat=True
    )
    request = _request()
    ctx = _ctx()

    expected_response = LLMResponse(
        content="compat!", model="models/gemini-2.5-flash-lite", provider="google"
    )

    async def fake_compat(
        req: LLMRequest, c: WorkflowContext, *, provider_name: str
    ) -> LLMResponse:
        return expected_response

    with (
        patch.object(primitive, "_call_openai_compat", side_effect=fake_compat) as mock_compat,
        patch.object(primitive, "_call_google", new_callable=AsyncMock) as mock_native,
    ):
        result = await primitive.execute(request, ctx)

    mock_compat.assert_called_once()
    mock_native.assert_not_called()
    assert result is expected_response
