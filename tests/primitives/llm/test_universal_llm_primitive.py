"""Unit tests for UniversalLLMPrimitive (runtime LLM invocation layer)."""

from unittest.mock import AsyncMock, patch

import pytest
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    UniversalLLMPrimitive,
)

from ttadev.primitives import WorkflowContext


async def test_llm_request_has_expected_defaults():
    req = LLMRequest(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": "hello"}],
    )
    assert req.model == "llama3-8b-8192"
    assert req.temperature == 0.7  # default


async def test_universal_llm_primitive_calls_groq_provider():
    mock_response = LLMResponse(content="Hello back", model="llama3-8b-8192", provider="groq")
    primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="test-key")
    ctx = WorkflowContext()
    request = LLMRequest(model="llama3-8b-8192", messages=[{"role": "user", "content": "hi"}])
    with patch.object(primitive, "_call_groq", new=AsyncMock(return_value=mock_response)):
        result = await primitive.execute(request, ctx)
    assert result.content == "Hello back"
    assert result.provider == "groq"


async def test_universal_llm_primitive_calls_anthropic_provider():
    mock_response = LLMResponse(
        content="Hi from Claude", model="claude-haiku-4-5-20251001", provider="anthropic"
    )
    primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="test-key")
    ctx = WorkflowContext()
    request = LLMRequest(
        model="claude-haiku-4-5-20251001", messages=[{"role": "user", "content": "hi"}]
    )
    with patch.object(primitive, "_call_anthropic", new=AsyncMock(return_value=mock_response)):
        result = await primitive.execute(request, ctx)
    assert result.provider == "anthropic"


async def test_universal_llm_primitive_calls_openai_provider():
    mock_response = LLMResponse(content="OpenAI response", model="gpt-4o", provider="openai")
    primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="test-key")
    ctx = WorkflowContext()
    request = LLMRequest(model="gpt-4o", messages=[{"role": "user", "content": "hi"}])
    with patch.object(primitive, "_call_openai", new=AsyncMock(return_value=mock_response)):
        result = await primitive.execute(request, ctx)
    assert result.provider == "openai"


async def test_universal_llm_primitive_calls_ollama_provider():
    mock_response = LLMResponse(content="Local response", model="llama3", provider="ollama")
    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.OLLAMA, base_url="http://localhost:11434"
    )
    ctx = WorkflowContext()
    request = LLMRequest(model="llama3", messages=[{"role": "user", "content": "hi"}])
    with patch.object(primitive, "_call_ollama", new=AsyncMock(return_value=mock_response)):
        result = await primitive.execute(request, ctx)
    assert result.provider == "ollama"


def test_universal_llm_primitive_raises_value_error_for_unknown_provider():
    with pytest.raises(ValueError):
        UniversalLLMPrimitive(provider=42)  # type: ignore[arg-type]


def test_llm_request_default_temperature():
    req = LLMRequest(model="any", messages=[])
    assert req.temperature == 0.7


def test_llm_request_custom_max_tokens():
    req = LLMRequest(model="any", messages=[], max_tokens=512)
    assert req.max_tokens == 512


def test_llm_response_has_required_fields():
    resp = LLMResponse(content="text", model="any-model", provider="groq")
    assert resp.content == "text"
    assert resp.provider == "groq"
