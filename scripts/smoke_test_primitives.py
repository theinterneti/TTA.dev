#!/usr/bin/env python3
"""Smoke test for ModelRouterPrimitive and task-aware model selection.

Tests the full primitive stack (not raw HTTP) including:
- Basic routing through ModelRouterPrimitive
- Task-aware selection with TaskProfile
- Ollama complexity skipping
- Groq/Gemini multi-tier fallthrough

Usage::

    uv run python scripts/smoke_test_primitives.py

Reads API keys from the environment (`.env` must be loaded by the shell).
Ollama tests are skipped when the local server is unavailable.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from dataclasses import dataclass

# Load .env if available.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from ttadev.primitives.core import WorkflowContext
from ttadev.primitives.llm import (
    COMPLEXITY_COMPLEX,
    COMPLEXITY_MODERATE,
    COMPLEXITY_SIMPLE,
    ModelRouterPrimitive,
    ModelRouterRequest,
    RouterModeConfig,
    RouterTierConfig,
    TaskProfile,
    rank_models_for_task,
    score_model_for_task,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


@dataclass
class Result:
    label: str
    status: str  # OK | SKIP | FAIL
    latency_ms: float
    detail: str = ""


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="smoke-primitives")


async def _check_ollama() -> bool:
    """Return True if local Ollama is reachable."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=2) as client:
            r = await client.get("http://localhost:11434/api/tags")
            return r.status_code == 200
    except Exception:
        return False


# ── Benchmark scoring smoke ───────────────────────────────────────────────────


def test_benchmark_scoring() -> list[Result]:
    """Quick sanity check — scoring never errors, stays in 0-1."""
    results: list[Result] = []
    models = [
        "llama-3.3-70b-versatile",
        "models/gemini-2.5-flash",
        "mixtral-8x7b-32768",
        "llama3.3:70b",
        "totally-unknown:99b",
    ]
    profiles = [
        TaskProfile.coding(COMPLEXITY_COMPLEX),
        TaskProfile.chat(COMPLEXITY_SIMPLE),
        TaskProfile.general(COMPLEXITY_MODERATE),
    ]
    errors: list[str] = []
    for mid in models:
        for p in profiles:
            try:
                score = score_model_for_task(mid, p)
                if not (0.0 <= score <= 1.0):
                    errors.append(f"{mid}/{p.task_type}/{p.complexity}: score={score} out of range")
            except Exception as exc:
                errors.append(f"{mid}/{p.task_type}/{p.complexity}: {exc}")

    if errors:
        results.append(Result("benchmark-scoring", "FAIL", 0.0, "; ".join(errors)))
    else:
        results.append(
            Result("benchmark-scoring", "OK", 0.0, f"Scored {len(models)}×{len(profiles)} combos")
        )
    return results


def test_ranking() -> list[Result]:
    """Verify rank_models_for_task returns all inputs, best-first."""
    candidates = [
        "mixtral-8x7b-32768",
        "llama-3.3-70b-versatile",
        "models/gemini-2.5-flash",
        "totally-unknown:3b",
    ]
    profile = TaskProfile.coding(COMPLEXITY_COMPLEX)
    ranked = rank_models_for_task(candidates, profile)
    if sorted(ranked) != sorted(candidates):
        return [Result("ranking", "FAIL", 0.0, "Output set differs from input set")]
    # Strong models should beat the unknown tiny one.
    if ranked[-1] not in ("mixtral-8x7b-32768", "totally-unknown:3b"):
        return [Result("ranking", "FAIL", 0.0, f"Expected weak model last, got {ranked[-1]!r}")]
    return [Result("ranking", "OK", 0.0, f"Order: {' → '.join(m.split('/')[-1] for m in ranked)}")]


# ── Router smoke (live providers) ────────────────────────────────────────────


async def test_router_groq(prompt: str) -> Result:
    """Test that the router successfully calls Groq with task_profile."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return Result("router-groq+task_profile", "SKIP", 0.0, "GROQ_API_KEY not set")

    modes = {"coding": RouterModeConfig(tiers=[RouterTierConfig(provider="groq")])}
    router = ModelRouterPrimitive(modes, groq_api_key=api_key)
    profile = TaskProfile.coding(COMPLEXITY_MODERATE)
    req = ModelRouterRequest(mode="coding", prompt=prompt, task_profile=profile)
    t0 = time.monotonic()
    try:
        resp = await router.execute(req, _ctx())
        ms = (time.monotonic() - t0) * 1000
        snippet = resp.content[:60].replace("\n", " ")
        return Result("router-groq+task_profile", "OK", ms, f"model={resp.model!r} → {snippet!r}…")
    except Exception as exc:
        ms = (time.monotonic() - t0) * 1000
        return Result("router-groq+task_profile", "FAIL", ms, str(exc)[:120])


async def test_router_gemini(prompt: str) -> Result:
    """Test that the router successfully calls Gemini with task_profile."""
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        return Result("router-gemini+task_profile", "SKIP", 0.0, "GOOGLE_API_KEY not set")

    modes = {"coding": RouterModeConfig(tiers=[RouterTierConfig(provider="google")])}
    router = ModelRouterPrimitive(modes, gemini_api_key=api_key)
    profile = TaskProfile.coding(COMPLEXITY_MODERATE)
    req = ModelRouterRequest(mode="coding", prompt=prompt, task_profile=profile)
    t0 = time.monotonic()
    try:
        resp = await router.execute(req, _ctx())
        ms = (time.monotonic() - t0) * 1000
        snippet = resp.content[:60].replace("\n", " ")
        return Result(
            "router-gemini+task_profile", "OK", ms, f"model={resp.model!r} → {snippet!r}…"
        )
    except Exception as exc:
        ms = (time.monotonic() - t0) * 1000
        return Result("router-gemini+task_profile", "FAIL", ms, str(exc)[:120])


async def test_router_ollama_skip_small(prompt: str) -> Result:
    """Verify Ollama skip + Groq fallthrough for COMPLEX coding."""
    if not await _check_ollama():
        return Result("router-ollama-skip→groq", "SKIP", 0.0, "Ollama not running")
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return Result("router-ollama-skip→groq", "SKIP", 0.0, "GROQ_API_KEY not set")

    modes = {
        "coding": RouterModeConfig(
            tiers=[
                RouterTierConfig(provider="ollama", model="llama3.2:3b"),  # 3B < 30B → skip
                RouterTierConfig(provider="groq"),
            ]
        )
    }
    router = ModelRouterPrimitive(modes, groq_api_key=api_key)
    profile = TaskProfile.coding(COMPLEXITY_COMPLEX)
    req = ModelRouterRequest(mode="coding", prompt=prompt, task_profile=profile)
    t0 = time.monotonic()
    try:
        resp = await router.execute(req, _ctx())
        ms = (time.monotonic() - t0) * 1000
        if resp.provider != "groq":
            return Result(
                "router-ollama-skip→groq",
                "FAIL",
                ms,
                f"Expected groq but got provider={resp.provider!r}",
            )
        return Result(
            "router-ollama-skip→groq",
            "OK",
            ms,
            f"Correctly skipped 3B Ollama → used {resp.model!r} on groq",
        )
    except Exception as exc:
        ms = (time.monotonic() - t0) * 1000
        return Result("router-ollama-skip→groq", "FAIL", ms, str(exc)[:120])


async def test_router_ollama_allow_large(prompt: str) -> Result:
    """Verify a large Ollama model (70B) is NOT skipped for COMPLEX tasks."""
    if not await _check_ollama():
        return Result("router-ollama-allow-70b", "SKIP", 0.0, "Ollama not running")

    # Check whether the 70b model is actually pulled.
    import httpx

    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get("http://localhost:11434/api/tags")
            tags = r.json()
        names = [m["name"] for m in tags.get("models", [])]
        has_70b = any("70b" in n for n in names)
        if not has_70b:
            return Result(
                "router-ollama-allow-70b",
                "SKIP",
                0.0,
                f"No 70B model pulled locally. Found: {names[:5]}",
            )
        model_70b = next(n for n in names if "70b" in n)
    except Exception as exc:
        return Result("router-ollama-allow-70b", "SKIP", 0.0, f"Tags check failed: {exc}")

    modes = {
        "coding": RouterModeConfig(tiers=[RouterTierConfig(provider="ollama", model=model_70b)])
    }
    router = ModelRouterPrimitive(modes)
    profile = TaskProfile.coding(COMPLEXITY_COMPLEX)
    req = ModelRouterRequest(mode="coding", prompt=prompt, task_profile=profile)
    t0 = time.monotonic()
    try:
        resp = await router.execute(req, _ctx())
        ms = (time.monotonic() - t0) * 1000
        return Result(
            "router-ollama-allow-70b",
            "OK",
            ms,
            f"model={resp.model!r} — 70B correctly not skipped",
        )
    except Exception as exc:
        ms = (time.monotonic() - t0) * 1000
        return Result("router-ollama-allow-70b", "FAIL", ms, str(exc)[:120])


async def test_router_no_profile(prompt: str) -> Result:
    """Verify routing still works without a task_profile (backward compat)."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return Result("router-no-profile", "SKIP", 0.0, "GROQ_API_KEY not set")

    modes = {
        "chat": RouterModeConfig(
            tiers=[RouterTierConfig(provider="groq", model="llama-3.1-8b-instant")]
        )
    }
    router = ModelRouterPrimitive(modes, groq_api_key=api_key)
    req = ModelRouterRequest(mode="chat", prompt=prompt)  # no task_profile
    t0 = time.monotonic()
    try:
        resp = await router.execute(req, _ctx())
        ms = (time.monotonic() - t0) * 1000
        return Result(
            "router-no-profile",
            "OK",
            ms,
            f"model={resp.model!r} (backward compat confirmed)",
        )
    except Exception as exc:
        ms = (time.monotonic() - t0) * 1000
        return Result("router-no-profile", "FAIL", ms, str(exc)[:120])


# ── Entrypoint ────────────────────────────────────────────────────────────────

PROMPT = "Write a Python one-liner that reverses a string. Reply with just the code."


async def main() -> None:
    # Sync tests first.
    all_results: list[Result] = []
    all_results.extend(test_benchmark_scoring())
    all_results.extend(test_ranking())

    # Async live tests.
    live = await asyncio.gather(
        test_router_groq(PROMPT),
        test_router_gemini(PROMPT),
        test_router_ollama_skip_small(PROMPT),
        test_router_ollama_allow_large(PROMPT),
        test_router_no_profile(PROMPT),
    )
    all_results.extend(live)

    # Print table.
    label_w = max(len(r.label) for r in all_results) + 2
    print(f"\n{'Label':<{label_w}} {'Status':<8} {'ms':>6}  Detail")
    print("-" * 80)
    for r in all_results:
        icon = {"OK": "✅", "SKIP": "⏭️ ", "FAIL": "❌"}.get(r.status, "?")
        lat = f"{r.latency_ms:>6.0f}" if r.latency_ms else "     —"
        print(f"{r.label:<{label_w}} {icon} {r.status:<5} {lat}  {r.detail}")

    print()
    failures = [r for r in all_results if r.status == "FAIL"]
    if failures:
        print(f"❌  {len(failures)} test(s) FAILED.")
        sys.exit(1)
    else:
        print(f"✅  All {len(all_results)} tests passed (or skipped).")


if __name__ == "__main__":
    asyncio.run(main())
