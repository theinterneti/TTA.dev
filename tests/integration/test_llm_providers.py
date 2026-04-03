"""Integration tests for all seven LLM provider backends in UniversalLLMPrimitive.

Each test makes a real round-trip to its provider and is automatically skipped
when the required SDK is not installed **or** the required env var / service is
absent.  No test ever *fails* due to a missing credential — it skips.

Markers
-------
- ``@pytest.mark.integration``  — opt-in only; excluded from the default run.
- ``@pytest.mark.asyncio``      — provided by ``asyncio_mode = auto`` in pytest.ini.

Provider mapping
----------------
| Provider   | Env var                               | Model                        |
|------------|---------------------------------------|------------------------------|
| Groq       | ``GROQ_API_KEY``                      | llama-3.1-8b-instant         |
| Anthropic  | ``ANTHROPIC_API_KEY``                 | claude-haiku-4-5             |
| OpenAI     | ``OPENAI_API_KEY``                    | gpt-4.1-mini                 |
| Ollama     | (none — service at :11434)            | llama3.2:1b                  |
| Gemini     | ``GEMINI_API_KEY``/``GOOGLE_API_KEY`` | gemini-2.0-flash-lite        |
| OpenRouter | ``OPENROUTER_API_KEY``                | meta-llama/llama-3.2-3b-inst |
| Together   | ``TOGETHER_API_KEY``                  | meta-llama/Llama-3.2-3B-Inst |
"""

from __future__ import annotations

import os

import pytest

from ttadev.primitives.core import WorkflowContext
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    UniversalLLMPrimitive,
)

pytestmark = pytest.mark.integration

_MESSAGES = [{"role": "user", "content": "Say hello in one word."}]


def _ctx(provider: str) -> WorkflowContext:
    return WorkflowContext(workflow_id=f"integration-test-{provider}")


# ---------------------------------------------------------------------------
# 1. Groq
# ---------------------------------------------------------------------------


async def test_groq_llm_round_trip() -> None:
    """LLMRequest → LLMResponse round-trip via Groq.

    Arrange: GROQ_API_KEY env var, groq SDK, cheap model.
    Act:     execute() against the live Groq API.
    Assert:  non-empty content, provider == 'groq', usage is None or dict.
    """
    pytest.importorskip("groq", reason="groq SDK not installed — skipping Groq integration test")

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        pytest.skip("GROQ_API_KEY not set — skipping Groq integration test")

    primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key=api_key)
    request = LLMRequest(model="llama-3.1-8b-instant", messages=_MESSAGES)

    response = await primitive.execute(request, _ctx("groq"))

    assert isinstance(response, LLMResponse)
    assert response.content.strip(), "Expected non-empty content from Groq"
    assert response.provider == LLMProvider.GROQ
    assert response.usage is None or isinstance(response.usage, dict)


# ---------------------------------------------------------------------------
# 2. Anthropic
# ---------------------------------------------------------------------------


async def test_anthropic_llm_round_trip() -> None:
    """LLMRequest → LLMResponse round-trip via Anthropic.

    Arrange: ANTHROPIC_API_KEY env var, anthropic SDK, claude-haiku-4-5.
    Act:     execute() against the live Anthropic Messages API.
    Assert:  non-empty content, provider == 'anthropic', usage is dict.
    """
    pytest.importorskip(
        "anthropic", reason="anthropic SDK not installed — skipping Anthropic integration test"
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set — skipping Anthropic integration test")

    primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key=api_key)
    request = LLMRequest(model="claude-haiku-4-5", messages=_MESSAGES)

    response = await primitive.execute(request, _ctx("anthropic"))

    assert isinstance(response, LLMResponse)
    assert response.content.strip(), "Expected non-empty content from Anthropic"
    assert response.provider == LLMProvider.ANTHROPIC
    assert response.usage is None or isinstance(response.usage, dict)


# ---------------------------------------------------------------------------
# 3. OpenAI
# ---------------------------------------------------------------------------


async def test_openai_llm_round_trip() -> None:
    """LLMRequest → LLMResponse round-trip via OpenAI.

    Arrange: OPENAI_API_KEY env var, openai SDK, gpt-4.1-mini.
    Act:     execute() against the live OpenAI Chat Completions API.
    Assert:  non-empty content, provider == 'openai', usage is None or dict.
    """
    pytest.importorskip(
        "openai", reason="openai SDK not installed — skipping OpenAI integration test"
    )

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set — skipping OpenAI integration test")

    primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key=api_key)
    request = LLMRequest(model="gpt-4.1-mini", messages=_MESSAGES)

    response = await primitive.execute(request, _ctx("openai"))

    assert isinstance(response, LLMResponse)
    assert response.content.strip(), "Expected non-empty content from OpenAI"
    assert response.provider == LLMProvider.OPENAI
    assert response.usage is None or isinstance(response.usage, dict)


# ---------------------------------------------------------------------------
# 4. Ollama (no API key — skip if daemon not reachable)
# ---------------------------------------------------------------------------


async def test_ollama_llm_round_trip() -> None:
    """LLMRequest → LLMResponse round-trip via local Ollama daemon.

    Arrange: Ollama running at localhost:11434, llama3.2:1b pulled.
    Act:     execute() against the local /api/chat endpoint.
    Assert:  non-empty content, provider == 'ollama', usage is None or dict.
    """
    httpx = pytest.importorskip(
        "httpx", reason="httpx not installed — skipping Ollama integration test"
    )

    try:
        probe = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        probe.raise_for_status()
    except Exception as exc:
        pytest.skip(f"Ollama daemon not reachable at localhost:11434: {exc}")

    primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)
    # Discover which models are actually pulled; skip if none available
    pulled_models: list[str] = []
    try:
        import httpx as _httpx

        tags = (
            await _httpx.AsyncClient().get("http://localhost:11434/api/tags", timeout=2.0)
        ).json()
        pulled_models = [m["name"] for m in tags.get("models", [])]
    except Exception:
        pass

    if not pulled_models:
        pytest.skip("No models pulled in local Ollama — skipping Ollama integration test")

    # Prefer small models for speed; take whatever is first if none match
    preferred_prefixes = ["qwen3.5", "qwen3", "llama3.2", "gemma3", "mistral"]
    model = next(
        (m for p in preferred_prefixes for m in pulled_models if m.startswith(p)),
        pulled_models[0],
    )
    request = LLMRequest(model=model, messages=_MESSAGES)

    response = await primitive.execute(request, _ctx("ollama"))

    assert isinstance(response, LLMResponse)
    assert response.content.strip(), "Expected non-empty content from Ollama"
    assert response.provider == LLMProvider.OLLAMA
    assert response.usage is None or isinstance(response.usage, dict)


# ---------------------------------------------------------------------------
# 5. Gemini
# ---------------------------------------------------------------------------


async def test_gemini_llm_round_trip() -> None:
    """LLMRequest → LLMResponse round-trip via Google Gemini.

    Arrange: GEMINI_API_KEY (or GOOGLE_API_KEY) env var, google-generativeai SDK.
    Act:     execute() against the live Gemini API using gemini-2.0-flash-lite.
    Assert:  non-empty content, provider == 'google', usage is None or dict.
    """
    pytest.importorskip(
        "google.generativeai",
        reason="google-generativeai SDK not installed — skipping Gemini integration test",
    )

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip(
            "Neither GEMINI_API_KEY nor GOOGLE_API_KEY set — skipping Gemini integration test"
        )

    primitive = UniversalLLMPrimitive(provider=LLMProvider.GOOGLE, api_key=api_key)
    request = LLMRequest(model="gemini-2.0-flash-lite", messages=_MESSAGES)

    response = await primitive.execute(request, _ctx("google"))

    assert isinstance(response, LLMResponse)
    assert response.content.strip(), "Expected non-empty content from Gemini"
    assert response.provider == LLMProvider.GOOGLE
    assert response.usage is None or isinstance(response.usage, dict)


# ---------------------------------------------------------------------------
# 6. OpenRouter
# ---------------------------------------------------------------------------


async def test_openrouter_llm_round_trip() -> None:
    """LLMRequest → LLMResponse round-trip via OpenRouter.

    Arrange: OPENROUTER_API_KEY env var, httpx installed.
    Act:     execute() against the OpenRouter /chat/completions endpoint.
    Assert:  non-empty content, provider == 'openrouter', usage is None or dict.
    """
    pytest.importorskip(
        "httpx", reason="httpx not installed — skipping OpenRouter integration test"
    )

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set — skipping OpenRouter integration test")

    primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENROUTER, api_key=api_key)
    request = LLMRequest(
        model="meta-llama/llama-3.2-3b-instruct:free",
        messages=_MESSAGES,
    )

    response = await primitive.execute(request, _ctx("openrouter"))

    assert isinstance(response, LLMResponse)
    assert response.content.strip(), "Expected non-empty content from OpenRouter"
    assert response.provider == LLMProvider.OPENROUTER
    assert response.usage is None or isinstance(response.usage, dict)


# ---------------------------------------------------------------------------
# 7. Together AI
# ---------------------------------------------------------------------------


async def test_together_llm_round_trip() -> None:
    """LLMRequest → LLMResponse round-trip via Together AI.

    Arrange: TOGETHER_API_KEY env var, httpx installed.
    Act:     execute() against the Together /chat/completions endpoint.
    Assert:  non-empty content, provider == 'together', usage is None or dict.
    """
    pytest.importorskip("httpx", reason="httpx not installed — skipping Together integration test")

    api_key = os.environ.get("TOGETHER_API_KEY")
    if not api_key:
        pytest.skip("TOGETHER_API_KEY not set — skipping Together AI integration test")

    primitive = UniversalLLMPrimitive(provider=LLMProvider.TOGETHER, api_key=api_key)
    request = LLMRequest(
        model="meta-llama/Llama-3.2-3B-Instruct-Turbo",
        messages=_MESSAGES,
    )

    response = await primitive.execute(request, _ctx("together"))

    assert isinstance(response, LLMResponse)
    assert response.content.strip(), "Expected non-empty content from Together AI"
    assert response.provider == LLMProvider.TOGETHER
    assert response.usage is None or isinstance(response.usage, dict)
