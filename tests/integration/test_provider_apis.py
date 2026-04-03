"""Integration tests for cloud LLM provider APIs — scientific round-trip validation.

Run with:
    RUN_INTEGRATION=true uv run pytest tests/integration/test_provider_apis.py -v -s

Each test makes a REAL API call against a live provider endpoint.
Tests skip automatically when the required environment variable is absent.
No test fails merely because a credential is missing — it skips cleanly.

Markers
-------
- ``@pytest.mark.integration`` — excluded from the default ``uv run pytest`` run.
- ``asyncio_mode = auto`` (pytest.ini) — all async functions are auto-detected.

Provider map
------------
+---------------+---------------------------+------------------------------------------+
| Provider      | Env var                   | Notes                                    |
+===============+===========================+==========================================+
| groq          | GROQ_API_KEY              | 4 models tested + rotation latency table |
| gemini        | GOOGLE_API_KEY            | OAI-compat; models/ prefix documented    |
| openrouter    | OPENROUTER_API_KEY        | Free-tier models                         |
| together      | TOGETHER_API_KEY          | OpenAI-compat endpoint                   |
| anthropic     | ANTHROPIC_API_KEY         | SDK-only (not OAI-compat)                |
| openai        | OPENAI_API_KEY            | SDK, gpt-4o-mini                         |
+---------------+---------------------------+------------------------------------------+
"""

from __future__ import annotations

import os
import time

import httpx
import pytest

from ttadev.primitives.core import WorkflowContext
from ttadev.primitives.llm.model_router import (
    ModelRouterPrimitive,
    ModelRouterRequest,
    RouterModeConfig,
    RouterTierConfig,
)
from ttadev.primitives.llm.providers import PROVIDERS
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    UniversalLLMPrimitive,
)

pytestmark = pytest.mark.integration

# ── Constants ──────────────────────────────────────────────────────────────────

_PROMPT = "Say 'hello' in one word."
_MESSAGES: list[dict[str, str]] = [{"role": "user", "content": _PROMPT}]
_TIMEOUT_S = 30.0  # generous for cold-start models

# ── Skip markers ───────────────────────────────────────────────────────────────

SKIP_NO_GROQ = pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY not set")
SKIP_NO_GOOGLE = pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY"), reason="GOOGLE_API_KEY not set"
)
SKIP_NO_OPENROUTER = pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY not set"
)
SKIP_NO_TOGETHER = pytest.mark.skipif(
    not os.getenv("TOGETHER_API_KEY"), reason="TOGETHER_API_KEY not set"
)
SKIP_NO_ANTHROPIC = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set"
)
SKIP_NO_OPENAI = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set"
)


# ── Helpers ────────────────────────────────────────────────────────────────────


def _ctx(test_id: str) -> WorkflowContext:
    """Create a WorkflowContext scoped to a single test."""
    return WorkflowContext(workflow_id=f"api-integration-{test_id}")


async def _timed_execute(
    primitive: UniversalLLMPrimitive,
    request: LLMRequest,
    ctx: WorkflowContext,
) -> tuple[LLMResponse, float]:
    """Execute an LLM call and return ``(response, elapsed_ms)``."""
    t0 = time.perf_counter()
    response = await primitive.execute(request, ctx)
    return response, (time.perf_counter() - t0) * 1000


def _log(provider: str, model: str, response: LLMResponse, elapsed_ms: float) -> None:
    """Emit a one-line diagnostic row to stdout (visible with ``-s``)."""
    preview = response.content.strip()[:60].replace("\n", " ")
    print(f'\n  [{provider}/{model}]  latency={elapsed_ms:.0f}ms  content="{preview}"')


# ══════════════════════════════════════════════════════════════════════════════
# ① Groq
# ══════════════════════════════════════════════════════════════════════════════


@SKIP_NO_GROQ
async def test_groq_llama_8b() -> None:
    """Round-trip: Groq llama-3.1-8b-instant returns non-empty text.

    Arrange: GROQ_API_KEY from environment, groq SDK installed.
    Act:     UniversalLLMPrimitive(GROQ).execute() with llama-3.1-8b-instant.
    Assert:  Non-empty content, provider == 'groq', usage metadata returned.
    """
    pytest.importorskip("groq", reason="groq SDK not installed")
    model = "llama-3.1-8b-instant"

    # Arrange
    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.GROQ,
        api_key=os.environ["GROQ_API_KEY"],
    )
    request = LLMRequest(model=model, messages=_MESSAGES, max_tokens=32)

    # Act
    response, elapsed_ms = await _timed_execute(primitive, request, _ctx("groq-8b"))

    # Assert
    _log("groq", model, response, elapsed_ms)
    assert isinstance(response, LLMResponse)
    assert response.content.strip(), "Expected non-empty content from llama-3.1-8b-instant"
    assert response.provider == "groq"
    assert response.usage is None or isinstance(response.usage, dict)
    assert elapsed_ms < _TIMEOUT_S * 1000


@SKIP_NO_GROQ
async def test_groq_llama_70b() -> None:
    """Round-trip: Groq llama-3.3-70b-versatile returns non-empty text.

    Arrange: GROQ_API_KEY from environment, groq SDK installed.
    Act:     UniversalLLMPrimitive(GROQ).execute() with llama-3.3-70b-versatile.
    Assert:  Non-empty content, provider == 'groq'.
    """
    pytest.importorskip("groq", reason="groq SDK not installed")
    model = "llama-3.3-70b-versatile"

    # Arrange
    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.GROQ,
        api_key=os.environ["GROQ_API_KEY"],
    )
    request = LLMRequest(model=model, messages=_MESSAGES, max_tokens=32)

    # Act
    response, elapsed_ms = await _timed_execute(primitive, request, _ctx("groq-70b"))

    # Assert
    _log("groq", model, response, elapsed_ms)
    assert response.content.strip(), "Expected non-empty content from llama-3.3-70b-versatile"
    assert response.provider == "groq"


@SKIP_NO_GROQ
async def test_groq_gemma2() -> None:
    """Round-trip: Groq gemma2-9b-it returns non-empty text.

    Arrange: GROQ_API_KEY, groq SDK.
    Act:     execute() with gemma2-9b-it.
    Assert:  Non-empty content, provider == 'groq'.
    """
    pytest.importorskip("groq", reason="groq SDK not installed")
    model = "gemma2-9b-it"

    # Arrange
    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.GROQ,
        api_key=os.environ["GROQ_API_KEY"],
    )
    request = LLMRequest(model=model, messages=_MESSAGES, max_tokens=32)

    # Act
    response, elapsed_ms = await _timed_execute(primitive, request, _ctx("groq-gemma2"))

    # Assert
    _log("groq", model, response, elapsed_ms)
    assert response.content.strip(), "Expected non-empty content from gemma2-9b-it"
    assert response.provider == "groq"


@SKIP_NO_GROQ
async def test_groq_mixtral() -> None:
    """Round-trip: Groq mixtral-8x7b-32768 returns non-empty text.

    Arrange: GROQ_API_KEY, groq SDK.
    Act:     execute() with mixtral-8x7b-32768.
    Assert:  Non-empty content, provider == 'groq'.
    """
    pytest.importorskip("groq", reason="groq SDK not installed")
    model = "mixtral-8x7b-32768"

    # Arrange
    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.GROQ,
        api_key=os.environ["GROQ_API_KEY"],
    )
    request = LLMRequest(model=model, messages=_MESSAGES, max_tokens=32)

    # Act
    response, elapsed_ms = await _timed_execute(primitive, request, _ctx("groq-mixtral"))

    # Assert
    _log("groq", model, response, elapsed_ms)
    assert response.content.strip(), "Expected non-empty content from mixtral-8x7b-32768"
    assert response.provider == "groq"


@SKIP_NO_GROQ
async def test_groq_rotation() -> None:
    """Rotation: all 4 Groq models called in sequence; prints a latency table.

    Arrange: GROQ_API_KEY, groq SDK.
    Act:     Sequential calls to llama-8b, llama-70b, gemma2, mixtral.
    Assert:  All 4 return non-empty content; table printed to stdout.

    Use the latency numbers to calibrate tier ordering in model_modes.yaml.
    """
    pytest.importorskip("groq", reason="groq SDK not installed")

    groq_models = [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "gemma2-9b-it",
        "mixtral-8x7b-32768",
    ]
    api_key = os.environ["GROQ_API_KEY"]

    rows: list[tuple[str, float, str]] = []

    # Act — sequential so per-model latency is clean
    for model in groq_models:
        primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key=api_key)
        req = LLMRequest(model=model, messages=_MESSAGES, max_tokens=16)
        response, elapsed_ms = await _timed_execute(primitive, req, _ctx(f"rotation-{model}"))

        # Per-model assertion
        assert response.content.strip(), f"Empty response from Groq model {model!r}"
        assert response.provider == "groq"

        rows.append((model, elapsed_ms, response.content.strip()[:40]))

    # Print latency table
    print("\n")
    print(f"  {'Model':<32} {'Latency':>9}  Preview")
    print(f"  {'-' * 32} {'-' * 9}  {'-' * 32}")
    for model, ms, preview in rows:
        print(f"  {model:<32} {ms:>7.0f}ms  {preview!r}")

    assert len(rows) == 4, "Expected latency rows for all 4 Groq models"


# ══════════════════════════════════════════════════════════════════════════════
# ② Gemini
# ══════════════════════════════════════════════════════════════════════════════


@SKIP_NO_GOOGLE
async def test_gemini_2_5_flash() -> None:
    """Round-trip: Gemini 2.5 Flash via OAI-compat endpoint with models/ prefix.

    Arrange: GOOGLE_API_KEY, httpx.
    Act:     Direct POST to generativelanguage.googleapis.com/v1beta/openai
             with model='models/gemini-2.5-flash'.
    Assert:  HTTP 200, non-empty response content.

    The 'models/' prefix is required by Google's OAI-compat endpoint for
    the Gemini 2.5 series.  Bare model names like 'gemini-2.5-flash' may
    return a 4xx error — see test_gemini_without_prefix_fails.
    """
    api_key = os.environ["GOOGLE_API_KEY"]
    model = "models/gemini-2.5-flash"
    url = f"{PROVIDERS['gemini'].base_url}/chat/completions"

    payload = {"model": model, "messages": _MESSAGES, "max_tokens": 32}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Act
    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
        resp = await client.post(url, json=payload, headers=headers)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Assert
    assert resp.status_code == 200, (
        f"Expected HTTP 200 for {model} on Gemini OAI-compat; "
        f"got {resp.status_code}: {resp.text[:200]}"
    )
    data = resp.json()
    content: str = data["choices"][0]["message"]["content"]
    print(f"\n  [gemini/{model}] latency={elapsed_ms:.0f}ms  content={content.strip()[:60]!r}")
    assert content.strip(), "Expected non-empty content from models/gemini-2.5-flash"


@SKIP_NO_GOOGLE
async def test_gemini_2_0_flash() -> None:
    """Round-trip: Gemini 2.0 Flash via OAI-compat endpoint with models/ prefix.

    Arrange: GOOGLE_API_KEY, httpx.
    Act:     POST with model='models/gemini-2.0-flash'.
    Assert:  HTTP 200, non-empty response content.
    """
    api_key = os.environ["GOOGLE_API_KEY"]
    model = "models/gemini-2.0-flash"
    url = f"{PROVIDERS['gemini'].base_url}/chat/completions"

    payload = {"model": model, "messages": _MESSAGES, "max_tokens": 32}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Act
    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
        resp = await client.post(url, json=payload, headers=headers)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Assert
    assert resp.status_code == 200, (
        f"Expected HTTP 200 for {model} on Gemini OAI-compat; "
        f"got {resp.status_code}: {resp.text[:200]}"
    )
    data = resp.json()
    content: str = data["choices"][0]["message"]["content"]
    print(f"\n  [gemini/{model}] latency={elapsed_ms:.0f}ms  content={content.strip()[:60]!r}")
    assert content.strip(), "Expected non-empty content from models/gemini-2.0-flash"


@SKIP_NO_GOOGLE
async def test_gemini_without_prefix_fails() -> None:
    """Documents bug: bare 'gemini-2.5-flash' (no prefix) fails on OAI-compat.

    Arrange: GOOGLE_API_KEY, httpx.
    Act:     POST to OAI-compat endpoint with model='gemini-2.5-flash' (no prefix).
    Assert:  Non-200 HTTP status — the API rejects bare Gemini 2.5 model names.

    This test DOCUMENTS the bug.  If it starts failing (i.e. the provider
    returns HTTP 200 with content), Google has added prefix normalisation.
    Update the suite accordingly by removing or inverting this assertion.
    """
    api_key = os.environ["GOOGLE_API_KEY"]
    model = "gemini-2.5-flash"  # intentionally bare — no 'models/' prefix
    url = f"{PROVIDERS['gemini'].base_url}/chat/completions"

    payload = {"model": model, "messages": _MESSAGES, "max_tokens": 32}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Act
    async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
        resp = await client.post(url, json=payload, headers=headers)

    # Assert — expect failure
    print(f"\n  [gemini/{model} (no prefix)] status={resp.status_code}  body={resp.text[:100]}")
    assert resp.status_code != 200, (
        f"Expected non-200 for bare model name '{model}' on Gemini OAI-compat, "
        f"but received HTTP 200.  "
        f"The API now accepts bare names — remove or invert this test."
    )


@SKIP_NO_GOOGLE
async def test_gemini_auto_prefix() -> None:
    """Router: ModelRouterPrimitive calls Gemini successfully with explicit models/ prefix.

    Arrange: GOOGLE_API_KEY; ModelRouterPrimitive single-tier mode using
             'models/gemini-2.0-flash' (correctly prefixed by the caller).
    Act:     router.execute() dispatches to the Gemini OAI-compat endpoint.
    Assert:  Non-empty content, provider == 'google'.

    This is the acceptance baseline for Gemini routing.  When the future
    'auto-prefix' feature lands in ModelRouterPrimitive._call_tier(), the
    'models/' in the tier config can be omitted and this test should still
    pass with a bare model name.
    """
    api_key = os.environ["GOOGLE_API_KEY"]

    # Arrange — single tier, correct prefix
    modes = {
        "google": RouterModeConfig(
            description="Gemini auto-prefix acceptance test",
            tiers=[
                RouterTierConfig(
                    provider="google",
                    model="models/gemini-2.0-flash",
                    params={"max_tokens": 32},
                )
            ],
        )
    }
    router = ModelRouterPrimitive(modes=modes, gemini_api_key=api_key)
    req = ModelRouterRequest(mode="google", prompt=_PROMPT)

    # Act
    t0 = time.perf_counter()
    response = await router.execute(req, _ctx("gemini-auto-prefix"))
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Assert
    print(
        f"\n  [router/gemini] model={response.model}  "
        f"latency={elapsed_ms:.0f}ms  "
        f"content={response.content.strip()[:60]!r}"
    )
    assert response.content.strip(), "Expected non-empty content from Gemini router tier"
    assert response.provider == "google"


# ══════════════════════════════════════════════════════════════════════════════
# ③ OpenRouter
# ══════════════════════════════════════════════════════════════════════════════


@SKIP_NO_OPENROUTER
async def test_openrouter_free_model() -> None:
    """Round-trip: OpenRouter free tier with mistralai/mistral-7b-instruct:free.

    Arrange: OPENROUTER_API_KEY, openai SDK installed.
    Act:     UniversalLLMPrimitive(OPENROUTER).execute() with free Mistral model.
    Assert:  Non-empty content, provider == 'openrouter'.
    """
    pytest.importorskip("openai", reason="openai SDK not installed")
    model = "mistralai/mistral-7b-instruct:free"

    # Arrange
    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.OPENROUTER,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    request = LLMRequest(model=model, messages=_MESSAGES, max_tokens=32)

    # Act
    response, elapsed_ms = await _timed_execute(primitive, request, _ctx("openrouter-mistral"))

    # Assert
    _log("openrouter", model, response, elapsed_ms)
    assert response.content.strip(), f"Expected non-empty content from OpenRouter/{model}"
    assert response.provider == "openrouter"


@SKIP_NO_OPENROUTER
async def test_openrouter_gemma_free() -> None:
    """Round-trip: OpenRouter free tier with google/gemma-3-27b-it:free.

    Arrange: OPENROUTER_API_KEY, openai SDK installed.
    Act:     execute() with gemma-3-27b-it:free.
    Assert:  Non-empty content, provider == 'openrouter'.
    """
    pytest.importorskip("openai", reason="openai SDK not installed")
    model = "google/gemma-3-27b-it:free"

    # Arrange
    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.OPENROUTER,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    request = LLMRequest(model=model, messages=_MESSAGES, max_tokens=32)

    # Act
    response, elapsed_ms = await _timed_execute(primitive, request, _ctx("openrouter-gemma"))

    # Assert
    _log("openrouter", model, response, elapsed_ms)
    assert response.content.strip(), f"Expected non-empty content from OpenRouter/{model}"
    assert response.provider == "openrouter"


# ══════════════════════════════════════════════════════════════════════════════
# ④ Together AI
# ══════════════════════════════════════════════════════════════════════════════


@SKIP_NO_TOGETHER
async def test_together_llama() -> None:
    """Round-trip: Together AI with meta-llama/Llama-3.2-3B-Instruct-Turbo.

    Arrange: TOGETHER_API_KEY, openai SDK installed.
    Act:     UniversalLLMPrimitive(TOGETHER).execute().
    Assert:  Non-empty content, provider == 'together'.
    """
    pytest.importorskip("openai", reason="openai SDK not installed")
    model = "meta-llama/Llama-3.2-3B-Instruct-Turbo"

    # Arrange
    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.TOGETHER,
        api_key=os.environ["TOGETHER_API_KEY"],
    )
    request = LLMRequest(model=model, messages=_MESSAGES, max_tokens=32)

    # Act
    response, elapsed_ms = await _timed_execute(primitive, request, _ctx("together-llama"))

    # Assert
    _log("together", model, response, elapsed_ms)
    assert response.content.strip(), "Expected non-empty content from Together AI"
    assert response.provider == "together"


# ══════════════════════════════════════════════════════════════════════════════
# ⑤ Anthropic
# ══════════════════════════════════════════════════════════════════════════════


@SKIP_NO_ANTHROPIC
async def test_anthropic_haiku() -> None:
    """Round-trip: Anthropic claude-3-5-haiku-20241022 via SDK.

    Arrange: ANTHROPIC_API_KEY, anthropic SDK.
    Act:     UniversalLLMPrimitive(ANTHROPIC).execute().
    Assert:  Non-empty content, provider == 'anthropic', usage dict with
             input_tokens > 0 (Anthropic always returns usage).
    """
    pytest.importorskip("anthropic", reason="anthropic SDK not installed")
    model = "claude-3-5-haiku-20241022"

    # Arrange
    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.ANTHROPIC,
        api_key=os.environ["ANTHROPIC_API_KEY"],
    )
    request = LLMRequest(model=model, messages=_MESSAGES, max_tokens=32)

    # Act
    response, elapsed_ms = await _timed_execute(primitive, request, _ctx("anthropic-haiku"))

    # Assert
    _log("anthropic", model, response, elapsed_ms)
    assert response.content.strip(), "Expected non-empty content from Anthropic Haiku"
    assert response.provider == "anthropic"
    assert isinstance(response.usage, dict), "Anthropic always returns token usage"
    assert (response.usage.get("input_tokens") or 0) > 0, "Expected non-zero input_tokens"


# ══════════════════════════════════════════════════════════════════════════════
# ⑥ OpenAI
# ══════════════════════════════════════════════════════════════════════════════


@SKIP_NO_OPENAI
async def test_openai_gpt4o_mini() -> None:
    """Round-trip: OpenAI gpt-4o-mini via SDK.

    Arrange: OPENAI_API_KEY, openai SDK.
    Act:     UniversalLLMPrimitive(OPENAI).execute().
    Assert:  Non-empty content, provider == 'openai'.
    """
    pytest.importorskip("openai", reason="openai SDK not installed")
    model = "gpt-4o-mini"

    # Arrange
    primitive = UniversalLLMPrimitive(
        provider=LLMProvider.OPENAI,
        api_key=os.environ["OPENAI_API_KEY"],
    )
    request = LLMRequest(model=model, messages=_MESSAGES, max_tokens=32)

    # Act
    response, elapsed_ms = await _timed_execute(primitive, request, _ctx("openai-gpt4o-mini"))

    # Assert
    _log("openai", model, response, elapsed_ms)
    assert response.content.strip(), "Expected non-empty content from OpenAI gpt-4o-mini"
    assert response.provider == "openai"
    assert response.usage is None or isinstance(response.usage, dict)


# ══════════════════════════════════════════════════════════════════════════════
# ⑦ ModelRouterPrimitive integration
# ══════════════════════════════════════════════════════════════════════════════


@SKIP_NO_GROQ
async def test_router_groq_cascade() -> None:
    """Integration: 3-tier Groq cascade routes through ModelRouterPrimitive.

    Arrange: GROQ_API_KEY; cascade configured as 8b → 70b → gemma2.
    Act:     router.execute() with mode='chat'.
    Assert:  Non-empty content from the winning tier; provider == 'groq';
             model is one of the three configured Groq models.

    Tier-1 (llama-3.1-8b-instant) should win under normal conditions.
    Tiers 2-3 act as fallback standby and validate the tier config is valid.
    """
    api_key = os.environ["GROQ_API_KEY"]

    # Arrange
    modes = {
        "chat": RouterModeConfig(
            description="3-tier Groq cascade (8b → 70b → gemma2)",
            tiers=[
                RouterTierConfig(
                    provider="groq",
                    model="llama-3.1-8b-instant",
                    params={"max_tokens": 32},
                ),
                RouterTierConfig(
                    provider="groq",
                    model="llama-3.3-70b-versatile",
                    params={"max_tokens": 32},
                ),
                RouterTierConfig(
                    provider="groq",
                    model="gemma2-9b-it",
                    params={"max_tokens": 32},
                ),
            ],
        )
    }
    router = ModelRouterPrimitive(modes=modes, groq_api_key=api_key)
    req = ModelRouterRequest(mode="chat", prompt=_PROMPT)

    # Act
    t0 = time.perf_counter()
    response = await router.execute(req, _ctx("router-groq-cascade"))
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Assert
    print(
        f"\n  [router/groq-cascade] model={response.model}  "
        f"latency={elapsed_ms:.0f}ms  "
        f"content={response.content.strip()[:60]!r}"
    )
    assert response.content.strip(), "Expected non-empty content from Groq cascade"
    assert response.provider == "groq", f"Expected provider='groq', got {response.provider!r}"
    assert response.model in {
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "gemma2-9b-it",
    }, f"Unexpected model returned by Groq cascade: {response.model!r}"


@SKIP_NO_GOOGLE
async def test_router_gemini_tier() -> None:
    """Integration: ModelRouterPrimitive single Gemini tier returns a response.

    Arrange: GOOGLE_API_KEY; single-tier mode for Gemini with models/ prefix.
    Act:     router.execute() dispatches to the Gemini OAI-compat endpoint.
    Assert:  Non-empty content, provider == 'google'.

    Baseline acceptance test for the Gemini routing tier.  A future
    'auto-prefix' implementation would allow the tier config to omit 'models/'.
    """
    api_key = os.environ["GOOGLE_API_KEY"]

    # Arrange
    modes = {
        "google": RouterModeConfig(
            description="Single Gemini tier",
            tiers=[
                RouterTierConfig(
                    provider="google",
                    model="models/gemini-2.0-flash",
                    params={"max_tokens": 32},
                )
            ],
        )
    }
    router = ModelRouterPrimitive(modes=modes, gemini_api_key=api_key)
    req = ModelRouterRequest(mode="google", prompt=_PROMPT)

    # Act
    t0 = time.perf_counter()
    response = await router.execute(req, _ctx("router-gemini-tier"))
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Assert
    print(
        f"\n  [router/gemini] model={response.model}  "
        f"latency={elapsed_ms:.0f}ms  "
        f"content={response.content.strip()[:60]!r}"
    )
    assert response.content.strip(), "Expected non-empty content from Gemini router tier"
    assert response.provider == "google"
