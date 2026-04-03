#!/usr/bin/env python3
"""Standalone smoke test for all configured LLM provider APIs.

Usage:
    uv run python scripts/smoke_test_providers.py
    python scripts/smoke_test_providers.py

Reads API keys from the environment (`.env` must be loaded by the shell).
Tests all providers concurrently via asyncio.gather().

Output example:
    Provider         Model                                Status     Latency
    ---------------- ------------------------------------ ---------- --------
    groq             llama-3.1-8b-instant                 ✅ OK       142ms
    groq             llama-3.3-70b-versatile              ✅ OK       891ms
    groq             gemma2-9b-it                         ✅ OK       310ms
    groq             mixtral-8x7b-32768                   ✅ OK       554ms
    gemini           models/gemini-2.5-flash              ✅ OK       423ms
    gemini           models/gemini-2.0-flash              ✅ OK       388ms
    gemini           gemini-2.5-flash (no prefix)         ❌ FAIL       0ms  (400 Bad Request)
    openrouter       mistralai/mistral-7b-instruct:free   ✅ OK      1204ms
    openrouter       google/gemma-3-27b-it:free           ✅ OK      1887ms
    together         meta-llama/Llama-3.2-3B-Instruct-…  ✅ OK       634ms
    openai           gpt-4o-mini                          ✅ OK       712ms
    anthropic        claude-3-5-haiku-20241022            ✅ OK       923ms
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

# ── Data classes ───────────────────────────────────────────────────────────────


@dataclass
class TestCase:
    """A single provider/model combination to test."""

    provider: str
    model: str
    url: str
    env_var: str
    extra_headers: dict[str, str] = field(default_factory=dict)
    use_anthropic_sdk: bool = False


@dataclass
class Result:
    """Outcome of a single smoke test."""

    provider: str
    model: str
    status: str  # "OK" | "SKIP" | "FAIL"
    latency_ms: float
    error: str = ""


# ── Constants ──────────────────────────────────────────────────────────────────

_PROMPT = "Say 'hello' in one word."
_MESSAGES: list[dict[str, str]] = [{"role": "user", "content": _PROMPT}]
_TIMEOUT_S = 30.0

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_TOGETHER_URL = "https://api.together.xyz/v1/chat/completions"
_OPENAI_URL = "https://api.openai.com/v1/chat/completions"

_OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://github.com/theinterneti/TTA.dev",
    "X-Title": "TTA.dev",
}

# Full test matrix
_TEST_CASES: list[TestCase] = [
    # ── Groq ──────────────────────────────────────────────────────────────────
    TestCase("groq", "llama-3.1-8b-instant", _GROQ_URL, "GROQ_API_KEY"),
    TestCase("groq", "llama-3.3-70b-versatile", _GROQ_URL, "GROQ_API_KEY"),
    TestCase("groq", "meta-llama/llama-4-scout-17b-16e-instruct", _GROQ_URL, "GROQ_API_KEY"),
    TestCase("groq", "qwen/qwen3-32b", _GROQ_URL, "GROQ_API_KEY"),
    # ── Gemini (OAI-compat, models/ prefix required) ──────────────────────────
    # Free tier: 20 RPD per model. Use lite models to conserve quota.
    # Confirmed working: gemini-2.5-flash-lite, gemini-3.1-flash-lite-preview
    TestCase("gemini", "models/gemini-2.5-flash-lite", _GEMINI_URL, "GOOGLE_API_KEY"),
    # ── OpenRouter (free tier) ────────────────────────────────────────────────
    TestCase(
        "openrouter",
        "meta-llama/llama-3.3-70b-instruct:free",
        _OPENROUTER_URL,
        "OPENROUTER_API_KEY",
        extra_headers=_OPENROUTER_HEADERS,
    ),
    TestCase(
        "openrouter",
        "google/gemma-3-27b-it:free",
        _OPENROUTER_URL,
        "OPENROUTER_API_KEY",
        extra_headers=_OPENROUTER_HEADERS,
    ),
    # ── Together AI ───────────────────────────────────────────────────────────
    TestCase(
        "together",
        "meta-llama/Llama-3.2-3B-Instruct-Turbo",
        _TOGETHER_URL,
        "TOGETHER_API_KEY",
    ),
    # ── OpenAI ────────────────────────────────────────────────────────────────
    TestCase("openai", "gpt-4o-mini", _OPENAI_URL, "OPENAI_API_KEY"),
    # ── Anthropic (SDK-only — handled separately) ─────────────────────────────
    TestCase(
        "anthropic",
        "claude-3-5-haiku-latest",
        "",  # no URL — SDK path
        "ANTHROPIC_API_KEY",
        use_anthropic_sdk=True,
    ),
]


# ── Provider callers ───────────────────────────────────────────────────────────


async def _call_openai_compat(
    url: str,
    api_key: str,
    model: str,
    extra_headers: dict[str, str] | None = None,
) -> tuple[str, float]:
    """POST to an OpenAI-compatible chat completions endpoint.

    Returns:
        ``(content, elapsed_ms)``

    Raises:
        httpx.HTTPStatusError: On non-2xx response.
        httpx.TimeoutException: On timeout.
        KeyError: If the response JSON is malformed.
    """
    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    # Strip display suffixes like " (no prefix)" from model name
    clean_model = model.split(" ", maxsplit=1)[0]

    payload: dict[str, Any] = {
        "model": clean_model,
        "messages": _MESSAGES,
        "max_tokens": 32,
    }

    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=_TIMEOUT_S) as client:
        resp = await client.post(url, json=payload, headers=headers)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    resp.raise_for_status()
    content: str = resp.json()["choices"][0]["message"]["content"]
    return content, elapsed_ms


async def _call_anthropic_sdk(api_key: str, model: str) -> tuple[str, float]:
    """Call Anthropic via the anthropic SDK.

    Returns:
        ``(content, elapsed_ms)``

    Raises:
        ImportError: If the anthropic package is not installed.
        anthropic.APIError: On API errors.
    """
    import anthropic  # type: ignore[import]

    client = anthropic.AsyncAnthropic(api_key=api_key)
    t0 = time.perf_counter()
    resp = await client.messages.create(
        model=model,
        max_tokens=32,
        messages=[{"role": "user", "content": _PROMPT}],
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000
    import anthropic as _anthropic

    text_blocks = [b for b in resp.content if isinstance(b, _anthropic.types.TextBlock)]
    content = text_blocks[0].text if text_blocks else ""
    return content, elapsed_ms


# ── Test runner ────────────────────────────────────────────────────────────────


async def run_test(tc: TestCase) -> Result:
    """Execute a single smoke test and return its Result.

    Never raises — all exceptions are caught and surfaced in Result.status.
    """
    api_key = os.getenv(tc.env_var)
    if not api_key:
        return Result(tc.provider, tc.model, "SKIP", 0.0, f"{tc.env_var} not set")

    try:
        if tc.use_anthropic_sdk:
            try:
                content, ms = await _call_anthropic_sdk(api_key, tc.model)
            except ImportError:
                return Result(tc.provider, tc.model, "SKIP", 0.0, "anthropic SDK not installed")
        else:
            content, ms = await _call_openai_compat(
                tc.url, api_key, tc.model, tc.extra_headers or None
            )

        if not content.strip():
            return Result(tc.provider, tc.model, "FAIL", ms, "empty response")

        return Result(tc.provider, tc.model, "OK", ms)

    except httpx.HTTPStatusError as exc:
        return Result(
            tc.provider,
            tc.model,
            "FAIL",
            0.0,
            f"HTTP {exc.response.status_code}: {exc.response.text[:80]}",
        )
    except httpx.TimeoutException:
        return Result(tc.provider, tc.model, "FAIL", 0.0, f"Timeout ({_TIMEOUT_S:.0f}s)")
    except Exception as exc:
        return Result(tc.provider, tc.model, "FAIL", 0.0, str(exc)[:80])


# ── Table renderer ─────────────────────────────────────────────────────────────

_COL_PROVIDER = 16
_COL_MODEL = 38
_COL_STATUS = 11
_COL_LATENCY = 8


def _status_glyph(status: str) -> str:
    return {"OK": "✅ OK", "SKIP": "⏭  SKIP", "FAIL": "❌ FAIL"}.get(status, status)


def _print_results(results: list[Result]) -> None:
    """Render all results as a fixed-width table."""
    header = (
        f"{'Provider':<{_COL_PROVIDER}} "
        f"{'Model':<{_COL_MODEL}} "
        f"{'Status':<{_COL_STATUS}} "
        f"{'Latency':>{_COL_LATENCY}}"
    )
    sep = f"{'-' * _COL_PROVIDER} {'-' * _COL_MODEL} {'-' * _COL_STATUS} {'-' * _COL_LATENCY}"

    print()
    print(header)
    print(sep)
    for r in results:
        lat = f"{r.latency_ms:.0f}ms" if r.latency_ms > 0 else "—"
        err = f"  ← {r.error}" if r.error and r.status != "OK" else ""
        print(
            f"{r.provider:<{_COL_PROVIDER}} "
            f"{r.model:<{_COL_MODEL}} "
            f"{_status_glyph(r.status):<{_COL_STATUS}} "
            f"{lat:>{_COL_LATENCY}}"
            f"{err}"
        )

    total = len(results)
    ok = sum(1 for r in results if r.status == "OK")
    skip = sum(1 for r in results if r.status == "SKIP")
    fail = sum(1 for r in results if r.status == "FAIL")

    print()
    print(f"  {total} tests  |  ✅ {ok} OK  |  ⏭  {skip} skipped  |  ❌ {fail} failed")
    print()


# ── Entrypoint ────────────────────────────────────────────────────────────────


async def main() -> None:
    """Run all smoke tests in parallel and display the formatted table."""
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║   TTA.dev  —  Provider API Smoke Tests       ║")
    print("╚══════════════════════════════════════════════╝")
    print(f'  Prompt   : "{_PROMPT}"')
    print(f"  Timeout  : {_TIMEOUT_S:.0f}s per call")
    print(f"  Tests    : {len(_TEST_CASES)} provider/model combinations")
    print("  Strategy : asyncio.gather() — all in parallel")

    # Run every test case concurrently
    results: list[Result] = list(await asyncio.gather(*[run_test(tc) for tc in _TEST_CASES]))

    _print_results(results)

    # Exit non-zero if any FAIL (but not SKIP)
    failures = [r for r in results if r.status == "FAIL"]
    if failures:
        import sys

        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
