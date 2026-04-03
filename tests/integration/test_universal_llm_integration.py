"""Integration tests for UniversalLLMPrimitive across all providers.

Every test in this module requires ``RUN_INTEGRATION=true`` in the environment
and is marked ``@pytest.mark.integration`` so it is excluded from the default
test run.  Each provider test additionally skips when its API key env var is
absent, so *no test ever fails* due to a missing credential.

Run the full suite::

    RUN_INTEGRATION=true uv run pytest tests/integration/test_universal_llm_integration.py -v

Run a single provider::

    RUN_INTEGRATION=true uv run pytest tests/integration/test_universal_llm_integration.py \\
        -v -k openai

Provider → model mapping used in tests
---------------------------------------
+------------+---------------------------------+--------------------------------+
| Provider   | Env var                         | Model                          |
+============+=================================+================================+
| openai     | OPENAI_API_KEY                  | gpt-4o-mini                    |
| groq       | GROQ_API_KEY                    | llama-3.1-8b-instant           |
| together   | TOGETHER_API_KEY                | meta-llama/Llama-3.2-3B-       |
|            |                                 | Instruct-Turbo                 |
| openrouter | OPENROUTER_API_KEY              | openai/gpt-4o-mini             |
| gemini     | GEMINI_API_KEY / GOOGLE_API_KEY | gemini-2.0-flash-lite          |
| ollama     | (none — local daemon)           | discovered at runtime          |
+------------+---------------------------------+--------------------------------+
"""

from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.llm import LLMRequest, LLMResponse, UniversalLLMPrimitive
from ttadev.primitives.llm.universal_llm_primitive import LLMProvider

# All tests in this module carry the integration marker.
pytestmark = pytest.mark.integration

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_MESSAGES: list[dict[str, str]] = [{"role": "user", "content": "Say hello in exactly one word."}]


def _ctx(step: str) -> WorkflowContext:
    """Return a fresh WorkflowContext for the given integration test step."""
    return WorkflowContext(workflow_id=f"integration-test-universal-llm-{step}")


# ---------------------------------------------------------------------------
# RUN_INTEGRATION guard — autouse so every test is skipped in normal runs
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _require_integration_flag() -> Generator[None, None, None]:
    """Skip all tests in this module unless ``RUN_INTEGRATION=true``.

    This guard keeps the suite out of the default ``uv run pytest`` run
    while still making every test fully discoverable via ``--collect-only``.
    """
    if os.getenv("RUN_INTEGRATION", "").lower() not in {"1", "true", "yes"}:
        pytest.skip("Set RUN_INTEGRATION=true to run integration tests")
    return


# ---------------------------------------------------------------------------
# 1. OpenAI — gpt-4o-mini
# ---------------------------------------------------------------------------


async def test_openai_execute() -> None:
    """Execute a non-streaming round-trip via OpenAI gpt-4o-mini.

    Arrange: OPENAI_API_KEY set, openai SDK installed, gpt-4o-mini model.
    Act:     UniversalLLMPrimitive.execute() against the live Chat Completions API.
    Assert:  LLMResponse.content is non-empty, provider == 'openai', model is set.
    """
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    pytest.importorskip("openai", reason="openai SDK not installed")

    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    request = LLMRequest(
        model="gpt-4o-mini",
        messages=_MESSAGES,
        max_tokens=50,
    )

    response = await primitive.execute(request, _ctx("openai-execute"))

    assert isinstance(response, LLMResponse)
    assert response.content.strip(), "Expected non-empty content from OpenAI"
    assert response.provider == "openai"
    assert response.model


async def test_openai_stream() -> None:
    """Stream tokens from OpenAI gpt-4o-mini.

    Arrange: OPENAI_API_KEY set, openai SDK installed, gpt-4o-mini model.
    Act:     UniversalLLMPrimitive.stream() against the live Chat Completions API.
    Assert:  At least one non-empty chunk returned.
    """
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    pytest.importorskip("openai", reason="openai SDK not installed")

    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    request = LLMRequest(
        model="gpt-4o-mini",
        messages=_MESSAGES,
        max_tokens=50,
    )

    chunks: list[str] = []
    async for chunk in primitive.stream(request, _ctx("openai-stream")):
        chunks.append(chunk)

    assert chunks, "Expected at least one streamed chunk from OpenAI"
    assert any(c.strip() for c in chunks), "Expected at least one non-empty chunk from OpenAI"


# ---------------------------------------------------------------------------
# 2. Groq — llama-3.1-8b-instant
# ---------------------------------------------------------------------------


async def test_groq_execute() -> None:
    """Execute a non-streaming round-trip via Groq llama-3.1-8b-instant.

    Arrange: GROQ_API_KEY set, groq SDK installed, llama-3.1-8b-instant model.
    Act:     UniversalLLMPrimitive.execute() against the live Groq API.
    Assert:  LLMResponse.content is non-empty, provider == 'groq', model is set.
    """
    if not os.getenv("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not set")

    pytest.importorskip("groq", reason="groq SDK not installed")

    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.GROQ,
        api_key=os.getenv("GROQ_API_KEY"),
    )
    request = LLMRequest(
        model="llama-3.1-8b-instant",
        messages=_MESSAGES,
        max_tokens=50,
    )

    response = await primitive.execute(request, _ctx("groq-execute"))

    assert isinstance(response, LLMResponse)
    assert response.content.strip(), "Expected non-empty content from Groq"
    assert response.provider == "groq"
    assert response.model


async def test_groq_stream() -> None:
    """Stream tokens from Groq llama-3.1-8b-instant.

    Arrange: GROQ_API_KEY set, groq SDK installed, llama-3.1-8b-instant model.
    Act:     UniversalLLMPrimitive.stream() against the live Groq API.
    Assert:  At least one non-empty chunk returned.
    """
    if not os.getenv("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not set")

    pytest.importorskip("groq", reason="groq SDK not installed")

    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.GROQ,
        api_key=os.getenv("GROQ_API_KEY"),
    )
    request = LLMRequest(
        model="llama-3.1-8b-instant",
        messages=_MESSAGES,
        max_tokens=50,
    )

    chunks: list[str] = []
    async for chunk in primitive.stream(request, _ctx("groq-stream")):
        chunks.append(chunk)

    assert chunks, "Expected at least one streamed chunk from Groq"
    assert any(c.strip() for c in chunks), "Expected at least one non-empty chunk from Groq"


# ---------------------------------------------------------------------------
# 3. Together AI — meta-llama/Llama-3.2-3B-Instruct-Turbo
# ---------------------------------------------------------------------------


async def test_together_execute() -> None:
    """Execute a non-streaming round-trip via Together AI.

    Together AI exposes an OpenAI-compatible endpoint; the openai SDK is used
    internally with a custom base_url.

    Arrange: TOGETHER_API_KEY set, openai SDK installed.
    Act:     UniversalLLMPrimitive.execute() against the live Together API.
    Assert:  LLMResponse.content is non-empty, provider == 'together', model is set.
    """
    if not os.getenv("TOGETHER_API_KEY"):
        pytest.skip("TOGETHER_API_KEY not set")

    pytest.importorskip("openai", reason="openai SDK not installed")

    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.TOGETHER,
        api_key=os.getenv("TOGETHER_API_KEY"),
    )
    request = LLMRequest(
        model="meta-llama/Llama-3.2-3B-Instruct-Turbo",
        messages=_MESSAGES,
        max_tokens=50,
    )

    response = await primitive.execute(request, _ctx("together-execute"))

    assert isinstance(response, LLMResponse)
    assert response.content.strip(), "Expected non-empty content from Together AI"
    assert response.provider == "together"
    assert response.model


async def test_together_stream() -> None:
    """Stream tokens from Together AI.

    Arrange: TOGETHER_API_KEY set, openai SDK installed.
    Act:     UniversalLLMPrimitive.stream() against the live Together API.
    Assert:  At least one non-empty chunk returned.
    """
    if not os.getenv("TOGETHER_API_KEY"):
        pytest.skip("TOGETHER_API_KEY not set")

    pytest.importorskip("openai", reason="openai SDK not installed")

    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.TOGETHER,
        api_key=os.getenv("TOGETHER_API_KEY"),
    )
    request = LLMRequest(
        model="meta-llama/Llama-3.2-3B-Instruct-Turbo",
        messages=_MESSAGES,
        max_tokens=50,
    )

    chunks: list[str] = []
    async for chunk in primitive.stream(request, _ctx("together-stream")):
        chunks.append(chunk)

    assert chunks, "Expected at least one streamed chunk from Together AI"
    assert any(c.strip() for c in chunks), "Expected at least one non-empty chunk from Together AI"


# ---------------------------------------------------------------------------
# 4. OpenRouter — openai/gpt-4o-mini
# ---------------------------------------------------------------------------


async def test_openrouter_execute() -> None:
    """Execute a non-streaming round-trip via OpenRouter.

    OpenRouter exposes an OpenAI-compatible endpoint with mandatory extra
    headers (HTTP-Referer, X-Title).  These are injected from the provider
    registry automatically.

    Arrange: OPENROUTER_API_KEY set, openai SDK installed.
    Act:     UniversalLLMPrimitive.execute() against the live OpenRouter API.
    Assert:  LLMResponse.content is non-empty, provider == 'openrouter', model is set.
    """
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set")

    pytest.importorskip("openai", reason="openai SDK not installed")

    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.OPENROUTER,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    request = LLMRequest(
        model="openai/gpt-4o-mini",
        messages=_MESSAGES,
        max_tokens=50,
    )

    response = await primitive.execute(request, _ctx("openrouter-execute"))

    assert isinstance(response, LLMResponse)
    assert response.content.strip(), "Expected non-empty content from OpenRouter"
    assert response.provider == "openrouter"
    assert response.model


async def test_openrouter_stream() -> None:
    """Stream tokens from OpenRouter.

    Arrange: OPENROUTER_API_KEY set, openai SDK installed.
    Act:     UniversalLLMPrimitive.stream() against the live OpenRouter API.
    Assert:  At least one non-empty chunk returned.
    """
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY not set")

    pytest.importorskip("openai", reason="openai SDK not installed")

    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.OPENROUTER,
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )
    request = LLMRequest(
        model="openai/gpt-4o-mini",
        messages=_MESSAGES,
        max_tokens=50,
    )

    chunks: list[str] = []
    async for chunk in primitive.stream(request, _ctx("openrouter-stream")):
        chunks.append(chunk)

    assert chunks, "Expected at least one streamed chunk from OpenRouter"
    assert any(c.strip() for c in chunks), "Expected at least one non-empty chunk from OpenRouter"


# ---------------------------------------------------------------------------
# 5. Gemini — gemini-2.0-flash-lite
# ---------------------------------------------------------------------------


async def test_gemini_execute() -> None:
    """Execute a non-streaming round-trip via Google Gemini.

    Accepts either GEMINI_API_KEY or GOOGLE_API_KEY (both are checked).

    Arrange: GEMINI_API_KEY or GOOGLE_API_KEY set, google-generativeai SDK installed.
    Act:     UniversalLLMPrimitive.execute() against the live Gemini API.
    Assert:  LLMResponse.content is non-empty, provider == 'google', model is set.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set")

    pytest.importorskip(
        "google.generativeai",
        reason="google-generativeai SDK not installed — pip install 'ttadev[gemini]'",
    )

    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.GOOGLE,
        api_key=api_key,
    )
    request = LLMRequest(
        model="gemini-2.0-flash-lite",
        messages=_MESSAGES,
        max_tokens=50,
    )

    response = await primitive.execute(request, _ctx("gemini-execute"))

    assert isinstance(response, LLMResponse)
    assert response.content.strip(), "Expected non-empty content from Gemini"
    assert response.provider == "google"
    assert response.model


async def test_gemini_stream() -> None:
    """Stream tokens from Google Gemini.

    Gemini's ``_stream_gemini`` yields the complete response as a single chunk
    (the underlying SDK call is synchronous).  We verify at least one non-empty
    chunk is returned.

    Arrange: GEMINI_API_KEY or GOOGLE_API_KEY set, google-generativeai SDK installed.
    Act:     UniversalLLMPrimitive.stream() against the live Gemini API.
    Assert:  At least one non-empty chunk returned.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set")

    pytest.importorskip(
        "google.generativeai",
        reason="google-generativeai SDK not installed — pip install 'ttadev[gemini]'",
    )

    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.GOOGLE,
        api_key=api_key,
    )
    request = LLMRequest(
        model="gemini-2.0-flash-lite",
        messages=_MESSAGES,
        max_tokens=50,
    )

    chunks: list[str] = []
    async for chunk in primitive.stream(request, _ctx("gemini-stream")):
        chunks.append(chunk)

    assert chunks, "Expected at least one streamed chunk from Gemini"
    assert any(c.strip() for c in chunks), "Expected at least one non-empty chunk from Gemini"


# ---------------------------------------------------------------------------
# 6. Ollama — model discovered at runtime from local daemon
# ---------------------------------------------------------------------------


async def test_ollama_execute() -> None:
    """Execute a non-streaming round-trip via local Ollama daemon.

    Probes ``http://localhost:11434/api/tags`` to confirm the daemon is running.
    Discovers pulled models at runtime; prefers small models for speed.
    Skips gracefully if the daemon is unreachable or no models are pulled.

    Arrange: Ollama daemon running at localhost:11434 with at least one model pulled.
    Act:     UniversalLLMPrimitive.execute() against the local /api/chat endpoint.
    Assert:  LLMResponse.content is non-empty, provider == 'ollama', model is set.
    """
    httpx = pytest.importorskip("httpx", reason="httpx not installed")

    try:
        probe = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        probe.raise_for_status()
    except Exception as exc:
        pytest.skip(f"Ollama daemon not reachable at localhost:11434: {exc}")

    pulled_models: list[str] = []
    try:
        async with httpx.AsyncClient() as client:
            tags_resp = await client.get("http://localhost:11434/api/tags", timeout=2.0)
            pulled_models = [m["name"] for m in tags_resp.json().get("models", [])]
    except Exception:
        pass

    if not pulled_models:
        pytest.skip("No models pulled in local Ollama — run `ollama pull llama3.2:latest` first")

    # Prefer small/fast models; fall back to the first available model
    preferred_prefixes = ["llama3.2", "qwen3", "gemma3", "mistral", "phi"]
    model = next(
        (m for prefix in preferred_prefixes for m in pulled_models if m.startswith(prefix)),
        pulled_models[0],
    )

    primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)
    request = LLMRequest(
        model=model,
        messages=_MESSAGES,
        max_tokens=50,
    )

    response = await primitive.execute(request, _ctx("ollama-execute"))

    assert isinstance(response, LLMResponse)
    assert response.content.strip(), f"Expected non-empty content from Ollama ({model})"
    assert response.provider == "ollama"
    assert response.model


async def test_ollama_stream() -> None:
    """Stream tokens from local Ollama daemon.

    Probes the daemon and discovers available models at runtime.
    Skips gracefully if the daemon is unreachable or no models are pulled.

    Arrange: Ollama daemon running at localhost:11434 with at least one model pulled.
    Act:     UniversalLLMPrimitive.stream() against the local /api/chat endpoint.
    Assert:  At least one non-empty chunk returned.
    """
    httpx = pytest.importorskip("httpx", reason="httpx not installed")

    try:
        probe = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        probe.raise_for_status()
    except Exception as exc:
        pytest.skip(f"Ollama daemon not reachable at localhost:11434: {exc}")

    pulled_models: list[str] = []
    try:
        async with httpx.AsyncClient() as client:
            tags_resp = await client.get("http://localhost:11434/api/tags", timeout=2.0)
            pulled_models = [m["name"] for m in tags_resp.json().get("models", [])]
    except Exception:
        pass

    if not pulled_models:
        pytest.skip("No models pulled in local Ollama — run `ollama pull llama3.2:latest` first")

    preferred_prefixes = ["llama3.2", "qwen3", "gemma3", "mistral", "phi"]
    model = next(
        (m for prefix in preferred_prefixes for m in pulled_models if m.startswith(prefix)),
        pulled_models[0],
    )

    primitive = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)
    request = LLMRequest(
        model=model,
        messages=_MESSAGES,
        max_tokens=50,
    )

    chunks: list[str] = []
    async for chunk in primitive.stream(request, _ctx("ollama-stream")):
        chunks.append(chunk)

    assert chunks, f"Expected at least one streamed chunk from Ollama ({model})"
    assert any(c.strip() for c in chunks), (
        f"Expected at least one non-empty chunk from Ollama ({model})"
    )


# ---------------------------------------------------------------------------
# 7. Missing API key raises ValueError before any network call
# ---------------------------------------------------------------------------


async def test_missing_key_raises_immediately() -> None:
    """ValueError is raised before any network call when the API key is absent.

    Together AI (and OpenRouter) validate the API key eagerly inside their
    ``_call_*`` and ``_stream_*`` methods, raising ``ValueError`` synchronously
    before any HTTP connection is attempted.  This test verifies that guard
    using Together AI as the representative provider.

    Note: Groq's SDK handles missing keys differently (reads from env at SDK
    instantiation time); Together AI was chosen because its guard is explicit
    and pre-network in the UniversalLLMPrimitive implementation.

    Arrange: UniversalLLMPrimitive(TOGETHER) with no api_key argument;
             TOGETHER_API_KEY patched to empty string in the environment.
    Act:     execute() is awaited inside pytest.raises(ValueError).
    Assert:  ValueError is raised with a message referencing TOGETHER_API_KEY;
             no network call is ever made.
    """
    pytest.importorskip("openai", reason="openai SDK not installed")

    primitive = UniversalLLMPrimitive(provider=LLMProvider.TOGETHER)
    request = LLMRequest(
        model="meta-llama/Llama-3.2-3B-Instruct-Turbo",
        messages=_MESSAGES,
        max_tokens=50,
    )

    with patch.dict(os.environ, {"TOGETHER_API_KEY": ""}, clear=False):
        with pytest.raises(ValueError, match="TOGETHER_API_KEY"):
            await primitive.execute(request, _ctx("missing-key-together"))
