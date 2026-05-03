#!/usr/bin/env python3
"""Test all LLM providers configured in litellm_config.yaml.

Run from project root:
    uv run python scripts/test_providers.py

Each provider is tested with a simple prompt. Results show:
- Connection status
- Latency
- Response preview
"""

import asyncio
import os
import sys
import time
from dataclasses import dataclass
from typing import Any

import litellm


@dataclass
class ProviderResult:
    name: str
    model: str
    success: bool
    latency_ms: float | None = None
    response: str | None = None
    error: str | None = None


async def test_provider(name: str, model: str, api_key: str | None = None) -> ProviderResult:
    """Test a single provider with a simple prompt."""
    if api_key:
        os.environ[f"{name.upper()}_API_KEY"] = api_key

    start = time.perf_counter()
    try:
        response: Any = await litellm.acompletion(
            model=model,
            messages=[{"role": "user", "content": "Say 'OK' in exactly one word."}],
            max_tokens=10,
            stream=False,
        )
        latency_ms = (time.perf_counter() - start) * 1000

        # Extract content from response - LiteLLM returns ModelResponse or CustomStreamWrapper
        if hasattr(response, "choices") and response.choices:
            content = response.choices[0].message.content or "No content"
        else:
            content = "Stream response (not collected)"

        return ProviderResult(
            name=name,
            model=model,
            success=True,
            latency_ms=latency_ms,
            response=content[:50],
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start) * 1000
        return ProviderResult(
            name=name,
            model=model,
            success=False,
            latency_ms=latency_ms,
            error=str(e)[:100],
        )


async def main() -> None:
    print("=" * 70)
    print("TTA.dev LLM Provider Test Suite")
    print("=" * 70)
    print()

    # Load keys from environment
    providers = [
        ("Groq", "groq/llama-3.3-70b-versatile", os.environ.get("GROQ_API_KEY")),
        ("Groq", "groq/llama-3.1-8b-instant", os.environ.get("GROQ_API_KEY")),
        ("Gemini", "gemini/gemini-2.0-flash", os.environ.get("GOOGLE_API_KEY")),
        ("Gemini", "gemini/gemini-2.5-flash", os.environ.get("GOOGLE_API_KEY")),
        ("OpenRouter", "openrouter/deepseek/deepseek-r1", os.environ.get("OPENROUTER_API_KEY")),
        ("OpenRouter", "openrouter/qwen/qwen3-32b", os.environ.get("OPENROUTER_API_KEY")),
        ("OpenRouter", "openrouter/qwen/qwen3.6-plus", os.environ.get("OPENROUTER_API_KEY")),
        ("HuggingFace", "huggingface/Qwen/Qwen2.5-7B-Instruct", os.environ.get("HF_TOKEN")),
        (
            "Anthropic",
            "anthropic/claude-3-5-sonnet-v2-20241022",
            os.environ.get("ANTHROPIC_API_KEY"),
        ),
        ("OpenAI", "openai/gpt-4o-mini", os.environ.get("OPENAI_API_KEY")),
    ]

    # Filter out providers without keys
    providers = [(n, m, k) for n, m, k in providers if k and k != "your-key-here"]

    if not providers:
        print("ERROR: No API keys found in environment!")
        print("Please set at least one of:")
        print("  - GROQ_API_KEY")
        print("  - GOOGLE_API_KEY")
        print("  - OPENROUTER_API_KEY")
        print("  - ANTHROPIC_API_KEY")
        print("  - HF_TOKEN")
        sys.exit(1)

    print(f"Testing {len(providers)} provider(s)...\n")

    results: list[ProviderResult] = []
    for name, model, _ in providers:
        print(f"Testing {name} ({model})...", end=" ", flush=True)
        result = await test_provider(name, model)
        results.append(result)
        if result.success:
            print(f"OK ({result.latency_ms:.0f}ms)")
        else:
            print(f"FAILED: {result.error}")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()

    # Group by provider
    by_provider: dict[str, list[ProviderResult]] = {}
    for r in results:
        by_provider.setdefault(r.name, []).append(r)

    for provider, prs in sorted(by_provider.items()):
        working = sum(1 for r in prs if r.success)
        total = len(prs)
        status = "✓" if working == total else "⚠" if working > 0 else "✗"
        print(f"{status} {provider}: {working}/{total} models working")

        for r in prs:
            if r.success:
                print(f"   └─ {r.model}: {r.latency_ms:.0f}ms - {r.response}")
            else:
                print(f"   └─ {r.model}: FAILED - {r.error}")

    print()
    working_total = sum(1 for r in results if r.success)
    print(f"Total: {working_total}/{len(results)} providers responding")

    if working_total == 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
