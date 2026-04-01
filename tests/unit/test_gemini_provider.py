"""Unit tests for the Gemini provider in UniversalLLMPrimitive.

All tests mock google.generativeai — no real API calls are made.
"""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
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


def _request(model: str = "gemini-2.0-flash") -> LLMRequest:
    return LLMRequest(
        model=model,
        messages=[{"role": "user", "content": "Hello, Gemini!"}],
    )


def _make_fake_genai(
    *,
    text: str = "Gemini says hello",
    prompt_token_count: int = 10,
    candidates_token_count: int = 20,
) -> ModuleType:
    """Return a fake google.generativeai module with a realistic response stub."""
    usage_meta = SimpleNamespace(
        prompt_token_count=prompt_token_count,
        candidates_token_count=candidates_token_count,
    )
    fake_response = SimpleNamespace(text=text, usage_metadata=usage_meta)

    fake_model = MagicMock()
    fake_model.generate_content.return_value = fake_response

    fake_genai = MagicMock()
    fake_genai.GenerativeModel.return_value = fake_model
    fake_genai.configure = MagicMock()
    return fake_genai


# ---------------------------------------------------------------------------
# 1. Enum value
# ---------------------------------------------------------------------------


def test_gemini_provider_enum_value() -> None:
    """LLMProvider.GEMINI must have string value 'gemini'."""
    assert LLMProvider.GEMINI.value == "gemini"


# ---------------------------------------------------------------------------
# 2. Successful _call_gemini
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_call_gemini_success() -> None:
    """_call_gemini returns LLMResponse with correct content and provider.

    Arrange: fake google.generativeai returning a fixed text response.
    Act:     call _call_gemini directly.
    Assert:  LLMResponse.content matches; provider == 'gemini'; model correct.
    """
    fake_genai = _make_fake_genai(text="Hello from Gemini")
    primitive = UniversalLLMPrimitive(provider=LLMProvider.GEMINI, api_key="fake-key")
    request = _request()
    ctx = _ctx()

    with (
        patch.dict(sys.modules, {"google": MagicMock(), "google.generativeai": fake_genai}),
        patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
    ):
        mock_to_thread.return_value = (
            fake_genai.GenerativeModel.return_value.generate_content.return_value
        )
        result = await primitive._call_gemini(request, ctx)

    assert isinstance(result, LLMResponse)
    assert result.content == "Hello from Gemini"
    assert result.provider == "gemini"
    assert result.model == "gemini-2.0-flash"


# ---------------------------------------------------------------------------
# 3. Usage metadata mapping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_call_gemini_maps_usage_metadata() -> None:
    """_call_gemini populates prompt_tokens and completion_tokens from usage_metadata.

    Arrange: fake genai response with known prompt_token_count / candidates_token_count.
    Act:     call _call_gemini.
    Assert:  LLMResponse.usage dict contains expected values.
    """
    fake_genai = _make_fake_genai(
        text="token count test",
        prompt_token_count=42,
        candidates_token_count=17,
    )
    primitive = UniversalLLMPrimitive(provider=LLMProvider.GEMINI, api_key="fake-key")
    request = _request()
    ctx = _ctx()

    with (
        patch.dict(sys.modules, {"google": MagicMock(), "google.generativeai": fake_genai}),
        patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread,
    ):
        mock_to_thread.return_value = (
            fake_genai.GenerativeModel.return_value.generate_content.return_value
        )
        result = await primitive._call_gemini(request, ctx)

    assert result.usage is not None
    assert result.usage["prompt_tokens"] == 42
    assert result.usage["completion_tokens"] == 17


# ---------------------------------------------------------------------------
# 4. ImportError when google-generativeai not installed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_call_gemini_import_error() -> None:
    """_call_gemini raises an informative ImportError when the SDK is missing.

    Arrange: remove google.generativeai from sys.modules, make import raise.
    Act:     call _call_gemini.
    Assert:  ImportError raised; message mentions install instructions.
    """
    primitive = UniversalLLMPrimitive(provider=LLMProvider.GEMINI, api_key="fake-key")
    ctx = _ctx()

    modules_patch = {
        "google": None,
        "google.generativeai": None,
    }
    with patch.dict(sys.modules, modules_patch):
        with pytest.raises(ImportError) as exc_info:
            await primitive._call_gemini(_request(), ctx)

    assert "google-generativeai" in str(exc_info.value)
    assert "pip install" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 5. execute() dispatch to _call_gemini
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_dispatches_gemini() -> None:
    """execute() with provider=GEMINI delegates to _call_gemini.

    Arrange: UniversalLLMPrimitive(GEMINI), patch _call_gemini.
    Act:     await primitive.execute(request, ctx).
    Assert:  _call_gemini was called once with the correct arguments.
    """
    primitive = UniversalLLMPrimitive(provider=LLMProvider.GEMINI, api_key="test-key")
    request = _request()
    ctx = _ctx()

    expected_response = LLMResponse(
        content="dispatched!", model="gemini-2.0-flash", provider="gemini"
    )
    with patch.object(
        primitive,
        "_call_gemini",
        new_callable=AsyncMock,
        return_value=expected_response,
    ) as mock_call:
        result = await primitive.execute(request, ctx)

    mock_call.assert_awaited_once_with(request, ctx)
    assert result is expected_response
