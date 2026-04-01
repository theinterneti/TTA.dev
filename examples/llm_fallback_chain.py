"""LLM provider fallback chain: Groq → Anthropic → Ollama.

Demonstrates how to build a resilient LLM pipeline using TTA.dev primitives:
- RetryPrimitive wraps Groq (2 retries on transient failures)
- FallbackPrimitive(groq_with_retry, FallbackPrimitive(claude, ollama))
  cascades through providers until one succeeds

Run in mock mode (default, no API keys needed):
    uv run python examples/llm_fallback_chain.py

Run with real providers (set at least GROQ_API_KEY):
    MOCK_MODE=false GROQ_API_KEY=gsk_... uv run python examples/llm_fallback_chain.py
    MOCK_MODE=false ANTHROPIC_API_KEY=sk-ant-... uv run python examples/llm_fallback_chain.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Make the package importable when run directly from the repo root
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ---------------------------------------------------------------------------
# MOCK_MODE flag
# Set to True by default so the script runs in CI without any API keys.
# Override at the shell:  MOCK_MODE=false uv run python examples/llm_fallback_chain.py
# ---------------------------------------------------------------------------
MOCK_MODE: bool = os.environ.get("MOCK_MODE", "true").lower() != "false"

from ttadev.primitives import (  # noqa: E402  (import after sys.path patch)
    FallbackPrimitive,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    RetryPrimitive,
    RetryStrategy,
    UniversalLLMPrimitive,
    WorkflowContext,
    WorkflowPrimitive,
)
from ttadev.primitives.testing.mocks import MockPrimitive  # noqa: E402


# ---------------------------------------------------------------------------
# Internal helper: build a MockPrimitive that returns a canned LLMResponse
# ---------------------------------------------------------------------------
def _make_mock_provider(name: str, provider_label: str) -> MockPrimitive:
    """Return a MockPrimitive that simulates a successful LLM provider call.

    Args:
        name: Unique name for the mock (used in assertion messages).
        provider_label: Human-readable provider name stored in the response.

    Returns:
        MockPrimitive configured to return a fake LLMResponse.
    """
    response = LLMResponse(
        content=f"Hello from mock {provider_label}! This is a simulated response.",
        model=f"mock-{provider_label}-model",
        provider=provider_label,
        usage={"prompt_tokens": 10, "completion_tokens": 20},
    )
    return MockPrimitive(name=name, return_value=response)


# ---------------------------------------------------------------------------
# Factory: build the full fallback chain
# ---------------------------------------------------------------------------
def build_chain(mock_mode: bool = MOCK_MODE) -> WorkflowPrimitive:
    """Construct the Groq → Anthropic → Ollama fallback chain.

    Architecture::

        FallbackPrimitive(
            primary  = RetryPrimitive(groq,  max_retries=2),
            fallback = FallbackPrimitive(
                primary  = claude,
                fallback = ollama,
            ),
        )

    In mock mode every provider is replaced by a MockPrimitive so the
    script runs without network access or API keys.

    Args:
        mock_mode: When True use MockPrimitive stubs; when False construct
            real UniversalLLMPrimitive instances backed by env-var API keys.

    Returns:
        A fully composed WorkflowPrimitive ready to call with .execute().
    """
    if mock_mode:
        # ── Mock providers (no API keys required) ──────────────────────────
        print("🧪  Running in MOCK_MODE — no real API calls will be made.")
        groq_primitive: WorkflowPrimitive = _make_mock_provider("groq_mock", "groq")
        claude_primitive: WorkflowPrimitive = _make_mock_provider("claude_mock", "anthropic")
        ollama_primitive: WorkflowPrimitive = _make_mock_provider("ollama_mock", "ollama")
    else:
        # ── Live providers — credentials come from environment variables ────
        print("🌐  Running in LIVE_MODE — real API calls will be made.")
        groq_api_key = os.environ.get("GROQ_API_KEY")
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        ollama_base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

        if not groq_api_key:
            print("⚠️   GROQ_API_KEY not set — Groq calls will fail and fallback will fire.")
        if not anthropic_api_key:
            print("⚠️   ANTHROPIC_API_KEY not set — Claude calls will fail and Ollama will be used.")

        groq_primitive = UniversalLLMPrimitive(
            provider=LLMProvider.GROQ,
            api_key=groq_api_key,
        )
        claude_primitive = UniversalLLMPrimitive(
            provider=LLMProvider.ANTHROPIC,
            api_key=anthropic_api_key,
        )
        ollama_primitive = UniversalLLMPrimitive(
            provider=LLMProvider.OLLAMA,
            base_url=ollama_base_url,
        )

    # ── Step 1: Wrap Groq with RetryPrimitive ─────────────────────────────
    # Groq is retried up to 2 times (3 total attempts) before giving up.
    # Exponential backoff with jitter helps with transient rate-limit errors.
    groq_with_retry = RetryPrimitive(
        groq_primitive,
        strategy=RetryStrategy(
            max_retries=2,
            backoff_base=2.0,
            jitter=True,
        ),
    )

    # ── Step 2: Inner fallback — Anthropic → Ollama ───────────────────────
    # If Groq is exhausted, Claude is tried next.
    # If Claude also fails, Ollama (local) is the final backstop.
    claude_then_ollama = FallbackPrimitive(
        primary=claude_primitive,
        fallback=ollama_primitive,
    )

    # ── Step 3: Outer chain — Groq(with retry) → (Claude → Ollama) ───────
    chain = FallbackPrimitive(
        primary=groq_with_retry,
        fallback=claude_then_ollama,
    )

    return chain


# ---------------------------------------------------------------------------
# Demo entry-point
# ---------------------------------------------------------------------------
async def main() -> None:
    """Run the LLM fallback chain and print the result."""
    print()
    print("🔗  LLM Provider Fallback Chain: Groq → Anthropic → Ollama")
    print("=" * 60)

    chain = build_chain(mock_mode=MOCK_MODE)

    # A simple chat request.  In mock mode the model name is ignored.
    request = LLMRequest(
        model="llama3-8b-8192",  # Groq's llama3 model (ignored in mock mode)
        messages=[{"role": "user", "content": "Tell me a one-sentence fun fact."}],
        temperature=0.7,
        max_tokens=128,
    )

    ctx = WorkflowContext(workflow_id="llm-fallback-demo")

    print(f"\n📤  Sending request: {request.messages[0]['content']!r}")
    print()

    # Execute the chain — whichever provider responds first wins.
    response: LLMResponse = await chain.execute(request, ctx)

    print(f"✅  Provider used : {response.provider}")
    print(f"📦  Model         : {response.model}")
    print(f"💬  Response      : {response.content}")
    if response.usage:
        print(f"📊  Token usage   : {response.usage}")

    print()
    print("=" * 60)
    print("💡  Pattern used:")
    print()
    print("    FallbackPrimitive(")
    print("        primary  = RetryPrimitive(groq, max_retries=2),")
    print("        fallback = FallbackPrimitive(")
    print("            primary  = claude,")
    print("            fallback = ollama,")
    print("        ),")
    print("    )")
    print()
    print("    • Groq is retried up to 3× on transient failures.")
    print("    • On exhaustion → Claude is tried next.")
    print("    • On Claude failure → Ollama (local) is the final backstop.")
    print()


if __name__ == "__main__":
    asyncio.run(main())
