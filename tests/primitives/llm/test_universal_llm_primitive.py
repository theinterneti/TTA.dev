"""Unit tests for UniversalLLMPrimitive (runtime LLM invocation layer)."""

from unittest.mock import AsyncMock, patch

import pytest

from ttadev.primitives import WorkflowContext
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    UniversalLLMPrimitive,
)


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


# ── Provider body coverage tests ────────────────────────────────────────────


async def test_call_groq_body_builds_response():
    """Cover _call_groq internals by mocking the groq module via sys.modules."""
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch

    primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="k")
    ctx = WorkflowContext()
    request = LLMRequest(model="llama3-8b-8192", messages=[{"role": "user", "content": "hi"}])

    mock_usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5)
    mock_message = SimpleNamespace(content="groq reply")
    mock_choice = SimpleNamespace(message=mock_message)
    mock_resp = SimpleNamespace(choices=[mock_choice], model="llama3-8b-8192", usage=mock_usage)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
    mock_groq = MagicMock()
    mock_groq.AsyncGroq.return_value = mock_client

    with patch.dict("sys.modules", {"groq": mock_groq}):
        result = await primitive._call_groq(request, ctx)

    assert result.content == "groq reply"
    assert result.provider == "groq"
    assert result.usage == {"prompt_tokens": 10, "completion_tokens": 5}


async def test_call_groq_body_no_usage():
    """Cover _call_groq when resp.usage is None."""
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch

    primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="k")
    ctx = WorkflowContext()
    request = LLMRequest(model="llama3-8b-8192", messages=[])

    mock_message = SimpleNamespace(content="reply")
    mock_choice = SimpleNamespace(message=mock_message)
    mock_resp = SimpleNamespace(choices=[mock_choice], model="llama3-8b-8192", usage=None)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
    mock_groq = MagicMock()
    mock_groq.AsyncGroq.return_value = mock_client

    with patch.dict("sys.modules", {"groq": mock_groq}):
        result = await primitive._call_groq(request, ctx)

    assert result.usage is None


async def test_call_anthropic_body_builds_response():
    """Cover _call_anthropic internals."""
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch

    primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="k")
    ctx = WorkflowContext()
    request = LLMRequest(
        model="claude-haiku-4-5-20251001",
        messages=[{"role": "user", "content": "hi"}],
    )

    mock_usage = SimpleNamespace(input_tokens=8, output_tokens=4)
    mock_content = SimpleNamespace(text="anthropic reply")
    mock_resp = SimpleNamespace(
        content=[mock_content], model="claude-haiku-4-5-20251001", usage=mock_usage
    )

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_resp)
    mock_anthropic = MagicMock()
    mock_anthropic.AsyncAnthropic.return_value = mock_client

    with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
        result = await primitive._call_anthropic(request, ctx)

    assert result.content == "anthropic reply"
    assert result.provider == "anthropic"
    assert result.usage == {"input_tokens": 8, "output_tokens": 4}


async def test_call_openai_body_builds_response():
    """Cover _call_openai internals."""
    from types import SimpleNamespace
    from unittest.mock import MagicMock, patch

    primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="k")
    ctx = WorkflowContext()
    request = LLMRequest(model="gpt-4o", messages=[{"role": "user", "content": "hi"}])

    mock_usage = SimpleNamespace(prompt_tokens=6, completion_tokens=3)
    mock_message = SimpleNamespace(content="openai reply")
    mock_choice = SimpleNamespace(message=mock_message)
    mock_resp = SimpleNamespace(choices=[mock_choice], model="gpt-4o", usage=mock_usage)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)
    mock_openai = MagicMock()
    mock_openai.AsyncOpenAI.return_value = mock_client

    with patch.dict("sys.modules", {"openai": mock_openai}):
        result = await primitive._call_openai(request, ctx)

    assert result.content == "openai reply"
    assert result.provider == "openai"
    assert result.usage == {"prompt_tokens": 6, "completion_tokens": 3}


async def test_call_ollama_body_builds_response():
    """Cover _call_ollama internals via httpx mock."""
    from unittest.mock import MagicMock, patch

    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.OLLAMA, base_url="http://localhost:11434"
    )
    ctx = WorkflowContext()
    request = LLMRequest(model="llama3", messages=[{"role": "user", "content": "hi"}])

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"message": {"content": "ollama reply"}}
    mock_resp.raise_for_status = MagicMock()

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await primitive._call_ollama(request, ctx)

    assert result.content == "ollama reply"
    assert result.provider == "ollama"
    assert result.model == "llama3"
