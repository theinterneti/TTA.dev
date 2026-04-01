"""Unit tests for the LLM provider fallback chain (Groq → Anthropic → Ollama).

Issue: #258 — Recipe: LLM provider fallback chain

All tests run without real API keys by using MockPrimitive stubs.
asyncio_mode = auto (pytest.ini) so @pytest.mark.asyncio is redundant
but is kept for explicitness per the task spec.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from ttadev.primitives import (
    FallbackPrimitive,
    LLMResponse,
    RetryPrimitive,
    RetryStrategy,
    WorkflowContext,
    WorkflowPrimitive,
)
from ttadev.primitives.testing.mocks import MockPrimitive

# ---------------------------------------------------------------------------
# Shared canned responses
# ---------------------------------------------------------------------------

GROQ_RESPONSE = LLMResponse(
    content="Hello from Groq!",
    model="llama3-8b-8192",
    provider="groq",
    usage={"prompt_tokens": 5, "completion_tokens": 10},
)

CLAUDE_RESPONSE = LLMResponse(
    content="Hello from Claude!",
    model="claude-3-haiku-20240307",
    provider="anthropic",
    usage={"input_tokens": 5, "output_tokens": 10},
)

OLLAMA_RESPONSE = LLMResponse(
    content="Hello from Ollama!",
    model="llama3",
    provider="ollama",
)

# A minimal request payload — contents are irrelevant for MockPrimitive tests.
SAMPLE_REQUEST: dict[str, str] = {"role": "user", "content": "Say hello."}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ctx(name: str = "test-llm-fallback") -> WorkflowContext:
    """Return a fresh WorkflowContext for each test."""
    return WorkflowContext(workflow_id=name)


def _make_flat_chain(
    groq_mock: MockPrimitive,
    claude_mock: MockPrimitive,
    ollama_mock: MockPrimitive,
) -> WorkflowPrimitive:
    """Build FallbackPrimitive(groq, FallbackPrimitive(claude, ollama)) without retry.

    Architecture::

        FallbackPrimitive(
            primary  = groq_mock,
            fallback = FallbackPrimitive(
                primary  = claude_mock,
                fallback = ollama_mock,
            ),
        )
    """
    claude_then_ollama = FallbackPrimitive(
        primary=claude_mock,
        fallback=ollama_mock,
    )
    return FallbackPrimitive(
        primary=groq_mock,
        fallback=claude_then_ollama,
    )


def _make_retry_chain(
    groq_mock: MockPrimitive,
    claude_mock: MockPrimitive,
    ollama_mock: MockPrimitive,
    max_retries: int = 2,
) -> WorkflowPrimitive:
    """Build the full chain with RetryPrimitive wrapping groq_mock.

    Architecture::

        FallbackPrimitive(
            primary  = RetryPrimitive(groq_mock, max_retries=N),
            fallback = FallbackPrimitive(
                primary  = claude_mock,
                fallback = ollama_mock,
            ),
        )

    Args:
        groq_mock: Mock for the primary provider.
        claude_mock: Mock for the first fallback provider.
        ollama_mock: Mock for the final fallback provider.
        max_retries: Number of retries passed to RetryStrategy.

    Returns:
        A fully composed WorkflowPrimitive.
    """
    groq_with_retry = RetryPrimitive(
        groq_mock,
        strategy=RetryStrategy(
            max_retries=max_retries,
            backoff_base=2.0,
            jitter=False,  # deterministic delay, patched away in the test
        ),
    )
    claude_then_ollama = FallbackPrimitive(
        primary=claude_mock,
        fallback=ollama_mock,
    )
    return FallbackPrimitive(
        primary=groq_with_retry,
        fallback=claude_then_ollama,
    )


# ---------------------------------------------------------------------------
# Test 1: primary succeeds — fallbacks are never invoked
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_primary_succeeds_no_fallback_used() -> None:
    """When Groq responds successfully, Claude and Ollama must not be called."""
    # Arrange
    groq_mock = MockPrimitive("groq", return_value=GROQ_RESPONSE)
    claude_mock = MockPrimitive("claude", return_value=CLAUDE_RESPONSE)
    ollama_mock = MockPrimitive("ollama", return_value=OLLAMA_RESPONSE)

    chain = _make_flat_chain(groq_mock, claude_mock, ollama_mock)
    ctx = _make_ctx("test-primary-succeeds")

    # Act
    result = await chain.execute(SAMPLE_REQUEST, ctx)

    # Assert
    assert result is GROQ_RESPONSE
    assert result.provider == "groq"
    assert groq_mock.call_count == 1
    assert claude_mock.call_count == 0, "Claude must not be called when Groq succeeds"
    assert ollama_mock.call_count == 0, "Ollama must not be called when Groq succeeds"


# ---------------------------------------------------------------------------
# Test 2: primary raises → first fallback (Claude) is called
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fallback_fires_when_primary_raises() -> None:
    """When Groq raises, FallbackPrimitive must invoke Claude as the first fallback."""
    # Arrange
    groq_mock = MockPrimitive("groq", raise_error=ConnectionError("Groq API unavailable"))
    claude_mock = MockPrimitive("claude", return_value=CLAUDE_RESPONSE)
    ollama_mock = MockPrimitive("ollama", return_value=OLLAMA_RESPONSE)

    chain = _make_flat_chain(groq_mock, claude_mock, ollama_mock)
    ctx = _make_ctx("test-groq-fails")

    # Act
    result = await chain.execute(SAMPLE_REQUEST, ctx)

    # Assert
    assert result is CLAUDE_RESPONSE
    assert result.provider == "anthropic"
    assert groq_mock.call_count == 1
    assert claude_mock.call_count == 1
    assert ollama_mock.call_count == 0, "Ollama must not be called when Claude succeeds"


# ---------------------------------------------------------------------------
# Test 3: primary + first fallback fail → second fallback (Ollama) is called
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_second_fallback_fires_when_both_fail() -> None:
    """When Groq and Claude both fail, Ollama must be invoked as the final backstop."""
    # Arrange
    groq_mock = MockPrimitive("groq", raise_error=ConnectionError("Groq down"))
    claude_mock = MockPrimitive("claude", raise_error=TimeoutError("Claude timed out"))
    ollama_mock = MockPrimitive("ollama", return_value=OLLAMA_RESPONSE)

    chain = _make_flat_chain(groq_mock, claude_mock, ollama_mock)
    ctx = _make_ctx("test-groq-claude-fail")

    # Act
    result = await chain.execute(SAMPLE_REQUEST, ctx)

    # Assert
    assert result is OLLAMA_RESPONSE
    assert result.provider == "ollama"
    assert groq_mock.call_count == 1
    assert claude_mock.call_count == 1
    assert ollama_mock.call_count == 1


# ---------------------------------------------------------------------------
# Test 4: all three providers fail → original primary exception propagates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_fail_raises_original_exception() -> None:
    """When all providers fail the outer primary's exception must propagate.

    FallbackPrimitive re-raises ``primary_error`` (not ``fallback_error``)
    when both sides are exhausted (see fallback.py line 324).

    Trace through the nested chain:
        outer.primary  = groq_mock  → raises ConnectionError   (outer primary_error)
        outer.fallback = inner FallbackPrimitive
            inner.primary  = claude_mock  → raises TimeoutError  (inner primary_error)
            inner.fallback = ollama_mock  → raises RuntimeError  (inner fallback_error)
            inner re-raises TimeoutError  → becomes outer fallback_error
        outer re-raises ConnectionError  ← what we assert here
    """
    # Arrange
    groq_error = ConnectionError("Groq is down")
    groq_mock = MockPrimitive("groq", raise_error=groq_error)
    claude_mock = MockPrimitive("claude", raise_error=TimeoutError("Claude timed out"))
    ollama_mock = MockPrimitive("ollama", raise_error=RuntimeError("Ollama unreachable"))

    chain = _make_flat_chain(groq_mock, claude_mock, ollama_mock)
    ctx = _make_ctx("test-all-fail")

    # Act & Assert
    with pytest.raises(ConnectionError, match="Groq is down"):
        await chain.execute(SAMPLE_REQUEST, ctx)

    # Every provider must have been attempted exactly once
    assert groq_mock.call_count == 1
    assert claude_mock.call_count == 1
    assert ollama_mock.call_count == 1


# ---------------------------------------------------------------------------
# Test 5: RetryPrimitive calls primary max_retries+1 times before fallback fires
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_before_fallback() -> None:
    """Groq mock must be called max_retries+1 times before FallbackPrimitive switches to Claude.

    RetryStrategy(max_retries=2) produces 3 total attempts on the underlying
    primitive (attempt 0, 1, 2).  Only after all attempts are exhausted does
    RetryPrimitive re-raise, triggering FallbackPrimitive to try Claude.

    asyncio.sleep is patched to an AsyncMock so the exponential backoff does
    not slow down CI.  The patch also lets us assert the exact sleep count.
    """
    # Arrange
    max_retries = 2
    expected_groq_calls = max_retries + 1  # 3 total attempts

    groq_mock = MockPrimitive("groq", raise_error=ConnectionError("Groq flaky"))
    claude_mock = MockPrimitive("claude", return_value=CLAUDE_RESPONSE)
    ollama_mock = MockPrimitive("ollama", return_value=OLLAMA_RESPONSE)

    chain = _make_retry_chain(groq_mock, claude_mock, ollama_mock, max_retries=max_retries)
    ctx = _make_ctx("test-retry-before-fallback")

    # Act — patch asyncio.sleep so backoff delays are instant
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await chain.execute(SAMPLE_REQUEST, ctx)

    # Assert — Groq was tried 3 times (original + 2 retries) before giving up
    assert groq_mock.call_count == expected_groq_calls, (
        f"Expected {expected_groq_calls} Groq calls "
        f"(1 original + {max_retries} retries), got {groq_mock.call_count}"
    )

    # Claude (the fallback) was called exactly once after Groq exhaustion
    assert claude_mock.call_count == 1
    # Ollama must not be reached because Claude succeeded
    assert ollama_mock.call_count == 0, "Ollama should not be needed when Claude succeeds"

    # The winning response comes from Claude
    assert result is CLAUDE_RESPONSE
    assert result.provider == "anthropic"

    # RetryPrimitive sleeps between attempts: once after attempt-0, once after attempt-1
    # (no sleep after the final attempt — the error is raised immediately)
    assert mock_sleep.call_count == max_retries, (
        f"Expected {max_retries} asyncio.sleep calls (one per retry gap), "
        f"got {mock_sleep.call_count}"
    )
