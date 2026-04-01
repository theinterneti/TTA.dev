"""Resilient LLM pipeline example.

Demonstrates composing TTA.dev primitives into a production-ready LLM call stack:

    MockLLM / UniversalLLMPrimitive(GROQ)
        → RetryPrimitive        (3 retries, exponential back-off)
        → CircuitBreakerPrimitive (opens after 5 consecutive failures)

OTel tracing is enabled via ``ttadev.initialize_observability()``.

Usage::

    # Default — mock mode, no API key required
    uv run python examples/resilient_llm_pipeline.py

    # Live mode — set GROQ_API_KEY first
    MOCK_MODE=false GROQ_API_KEY=gsk_… uv run python examples/resilient_llm_pipeline.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make the repo root importable when running the script directly
# ---------------------------------------------------------------------------
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ---------------------------------------------------------------------------
# TTA.dev imports
# ---------------------------------------------------------------------------
import ttadev
from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.recovery.circuit_breaker_primitive import (
    CircuitBreakerConfig,
    CircuitBreakerPrimitive,
)
from ttadev.primitives.recovery.retry import RetryPrimitive, RetryStrategy

# ---------------------------------------------------------------------------
# Env-var flag: MOCK_MODE defaults to "true" so the example runs everywhere
# Set MOCK_MODE=false (plus GROQ_API_KEY) to hit the real Groq API.
# ---------------------------------------------------------------------------
MOCK_MODE: bool = os.environ.get("MOCK_MODE", "true").lower() not in {"false", "0", "no"}

# Span file written by the OTel file exporter (if tracing is active)
SPAN_FILE = Path(".observability") / "traces.jsonl"


# ---------------------------------------------------------------------------
# Helper: build the pipeline
# ---------------------------------------------------------------------------


def build_mock_pipeline() -> CircuitBreakerPrimitive:
    """Return a fully composed mock pipeline (no API key needed)."""
    from ttadev.primitives.testing.mocks import MockPrimitive

    # Simulate what the real LLM would return — a dict that mirrors LLMResponse
    fake_response = {
        "content": "The answer is 42. (mock response — set MOCK_MODE=false for real output)",
        "model": "mock-llm-v1",
        "provider": "mock",
        "usage": {"prompt_tokens": 12, "completion_tokens": 8},
    }
    llm = MockPrimitive(name="mock_llm", return_value=fake_response)

    # Layer 1 — retry up to 3 times with exponential back-off (2^attempt seconds)
    retry_wrapped = RetryPrimitive(
        primitive=llm,
        strategy=RetryStrategy(max_retries=3, backoff_base=2.0),
    )

    # Layer 2 — circuit breaker: opens after 5 consecutive failures,
    # attempts recovery after 60 s.
    circuit_wrapped = CircuitBreakerPrimitive(
        primitive=retry_wrapped,
        config=CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0),
    )
    return circuit_wrapped


def build_live_pipeline() -> CircuitBreakerPrimitive:
    """Return a fully composed live pipeline targeting Groq.

    Requires the ``groq`` package and a valid ``GROQ_API_KEY`` env var.
    """
    from ttadev.primitives.llm import LLMProvider, UniversalLLMPrimitive

    llm = UniversalLLMPrimitive(
        provider=LLMProvider.GROQ,
        api_key=os.environ.get("GROQ_API_KEY"),  # None → reads env var inside groq SDK
    )

    retry_wrapped = RetryPrimitive(
        primitive=llm,
        strategy=RetryStrategy(max_retries=3, backoff_base=2.0),
    )

    circuit_wrapped = CircuitBreakerPrimitive(
        primitive=retry_wrapped,
        config=CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60.0),
    )
    return circuit_wrapped


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def main() -> None:
    """Run the resilient LLM pipeline demo."""
    # ------------------------------------------------------------------
    # Banner
    # ------------------------------------------------------------------
    print()
    if MOCK_MODE:
        print("╔══════════════════════════════════════════════════════╗")
        print("║  🧪  MOCK MODE  (set MOCK_MODE=false for live Groq)  ║")
        print("╚══════════════════════════════════════════════════════╝")
    else:
        print("╔══════════════════════════════════════════════════════╗")
        print("║  🚀  LIVE MODE  (Groq API)                           ║")
        print("╚══════════════════════════════════════════════════════╝")
    print()

    # ------------------------------------------------------------------
    # Observability — wraps OTel setup; safe to call multiple times.
    # Guard with try/except so the example works even if optional deps
    # (opentelemetry-sdk) are missing.
    # ------------------------------------------------------------------
    try:
        ttadev.initialize_observability()
        print("✅ Observability initialised (OTel tracing active)")
    except Exception as exc:
        print(f"⚠️  Observability skipped: {exc}")
    print()

    # ------------------------------------------------------------------
    # Build the pipeline
    # ------------------------------------------------------------------
    if MOCK_MODE:
        pipeline = build_mock_pipeline()
        print("📐 Pipeline:  MockPrimitive → RetryPrimitive → CircuitBreakerPrimitive")
    else:
        pipeline = build_live_pipeline()
        print(
            "📐 Pipeline:  UniversalLLMPrimitive(GROQ) → RetryPrimitive → CircuitBreakerPrimitive"
        )
    print()

    # ------------------------------------------------------------------
    # Build the request (mirrors LLMRequest for the live path;
    # the mock just receives it as opaque input_data).
    # ------------------------------------------------------------------
    if MOCK_MODE:
        # In mock mode we pass any dict — MockPrimitive ignores input_data
        request: object = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": "What is the meaning of life?"}],
        }
    else:
        from ttadev.primitives.llm import LLMRequest

        request = LLMRequest(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": "What is the meaning of life?"}],
            temperature=0.7,
            max_tokens=256,
        )

    ctx = WorkflowContext(workflow_id="resilient-llm-demo")

    # ------------------------------------------------------------------
    # Execute through the full composed stack
    # ------------------------------------------------------------------
    print("⏳ Executing pipeline …")
    result = await pipeline.execute(request, ctx)
    print()

    # ------------------------------------------------------------------
    # Pretty-print the result
    # ------------------------------------------------------------------
    print("─" * 56)
    print("📨 Response")
    print("─" * 56)

    if isinstance(result, dict):
        # Mock path returns a plain dict
        print(f"  content  : {result.get('content', '')}")
        print(f"  model    : {result.get('model', 'n/a')}")
        print(f"  provider : {result.get('provider', 'n/a')}")
        if usage := result.get("usage"):
            print(f"  usage    : {usage}")
    else:
        # Live path returns an LLMResponse dataclass
        print(f"  content  : {result.content}")
        print(f"  model    : {result.model}")
        print(f"  provider : {result.provider}")
        if result.usage:
            print(f"  usage    : {result.usage}")

    print("─" * 56)
    print()

    # ------------------------------------------------------------------
    # Circuit-breaker state summary
    # ------------------------------------------------------------------
    print(f"🔌 Circuit breaker state : {pipeline.state}")
    print(f"   failure count         : {pipeline.failure_count}")
    print()

    # ------------------------------------------------------------------
    # OTel span file location
    # ------------------------------------------------------------------
    if SPAN_FILE.exists():
        print(f"📄 OTel spans written to : {SPAN_FILE.resolve()}")
        lines = SPAN_FILE.read_text().strip().splitlines()
        print(f"   total spans so far    : {len(lines)}")
    else:
        print("📄 No span file yet — start the observability server to collect traces:")
        print("   uv run python -m ttadev.observability")
    print()
    print("✨ Done!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
