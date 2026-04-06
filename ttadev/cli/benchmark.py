"""Benchmark runner for TTA.dev LLM providers.

Sends a standardised prompt set to each configured provider, measures latency
and quality, then stores results in ``.tta/benchmarks.json``.

Usage::

    tta models benchmark
    tta models benchmark --runs 3
    tta models benchmark --json
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

__all__ = [
    "BENCHMARK_PROMPTS",
    "BenchmarkResult",
    "load_benchmarks",
    "save_benchmarks",
    "run_benchmark",
    "cmd_benchmark",
]

# ---------------------------------------------------------------------------
# Prompt set
# ---------------------------------------------------------------------------

BENCHMARK_PROMPTS: list[dict[str, str | None]] = [
    {
        "id": "echo",
        "prompt": "Reply with exactly: BENCHMARK_OK",
        "expected": "BENCHMARK_OK",
    },
    {
        "id": "math",
        "prompt": "What is 17 * 23? Reply with only the number.",
        "expected": "391",
    },
    {
        "id": "code",
        "prompt": "Write a Python one-liner to reverse a string s. Reply with only the code.",
        "expected": None,  # quality: validate it's syntactically valid Python
    },
]

# Default timeout per prompt in seconds.
_PROMPT_TIMEOUT_S = 30.0

# How many samples to collect per provider (for percentile calculation).
_DEFAULT_RUNS = 3

# Providers that require an env var to be active.
_PROVIDER_KEYS: dict[str, str] = {
    "groq/llama-3.3-70b-versatile": "GROQ_API_KEY",
    "gemini/gemini-2.0-flash-lite": "GOOGLE_API_KEY",
    "openrouter/google/gemma-3-27b-it:free": "OPENROUTER_API_KEY",
}


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class BenchmarkResult:
    """Aggregated benchmark result for one provider model.

    Attributes:
        model: litellm model string (e.g. ``"groq/llama-3.3-70b-versatile"``).
        p50_ms: Median round-trip latency across all successful runs (ms).
        p95_ms: 95th-percentile latency (ms); equals p50 when runs < 20.
        success_rate: Fraction of prompts that returned a valid response (0–1).
        quality_score: Fraction of prompts whose content passed validation (0–1).
        last_run: ISO-8601 UTC timestamp of when this benchmark was collected.
    """

    __slots__ = ("last_run", "model", "p50_ms", "p95_ms", "quality_score", "success_rate")

    def __init__(
        self,
        model: str,
        p50_ms: float,
        p95_ms: float,
        success_rate: float,
        quality_score: float,
        last_run: str,
    ) -> None:
        self.model = model
        self.p50_ms = p50_ms
        self.p95_ms = p95_ms
        self.success_rate = success_rate
        self.quality_score = quality_score
        self.last_run = last_run

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-compatible dict."""
        return {
            "p50_ms": round(self.p50_ms, 1),
            "p95_ms": round(self.p95_ms, 1),
            "success_rate": round(self.success_rate, 4),
            "quality_score": round(self.quality_score, 4),
            "last_run": self.last_run,
        }

    @classmethod
    def from_dict(cls, model: str, data: dict[str, Any]) -> BenchmarkResult:
        """Deserialise from a JSON dict entry."""
        return cls(
            model=model,
            p50_ms=float(data.get("p50_ms", 0.0)),
            p95_ms=float(data.get("p95_ms", 0.0)),
            success_rate=float(data.get("success_rate", 0.0)),
            quality_score=float(data.get("quality_score", 0.0)),
            last_run=str(data.get("last_run", "")),
        )


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------


def load_benchmarks(data_dir: Path) -> dict[str, BenchmarkResult]:
    """Load benchmark results from ``.tta/benchmarks.json``.

    Returns an empty dict (gracefully) when the file does not exist or is
    corrupt — SmartRouter must always function without benchmark data.

    Args:
        data_dir: The ``.tta`` state directory (may or may not exist yet).

    Returns:
        Mapping from litellm model string → :class:`BenchmarkResult`.
    """
    bench_file = data_dir / "benchmarks.json"
    if not bench_file.exists():
        return {}
    try:
        raw: dict[str, Any] = json.loads(bench_file.read_text())
        results_raw: dict[str, Any] = raw.get("results", {})
        return {
            model: BenchmarkResult.from_dict(model, data) for model, data in results_raw.items()
        }
    except Exception:  # noqa: BLE001 — intentional graceful degradation
        return {}


def save_benchmarks(data_dir: Path, results: dict[str, BenchmarkResult]) -> None:
    """Persist benchmark results to ``.tta/benchmarks.json``.

    Args:
        data_dir: The ``.tta`` state directory (created if absent).
        results: Mapping from litellm model string → :class:`BenchmarkResult`.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    bench_file = data_dir / "benchmarks.json"
    payload: dict[str, Any] = {
        "updated_at": datetime.now(UTC).isoformat(),
        "results": {model: r.to_dict() for model, r in results.items()},
    }
    bench_file.write_text(json.dumps(payload, indent=2))


# ---------------------------------------------------------------------------
# Quality validation helpers
# ---------------------------------------------------------------------------


def _validate_response(prompt_id: str, expected: str | None, content: str) -> bool:
    """Return ``True`` when the response passes quality checks.

    Args:
        prompt_id: One of ``"echo"``, ``"math"``, or ``"code"``.
        expected: Expected exact content (or ``None`` for syntax-only check).
        content: The model's raw response text.

    Returns:
        ``True`` when the response is considered correct.
    """
    text = content.strip()

    if expected is not None:
        return expected in text

    # code prompt: try to compile it as valid Python
    if prompt_id == "code":
        try:
            compile(text, "<benchmark>", "eval")
            return True
        except SyntaxError:
            try:
                compile(text, "<benchmark>", "exec")
                return True
            except SyntaxError:
                return False

    return bool(text)


# ---------------------------------------------------------------------------
# Core benchmark runner
# ---------------------------------------------------------------------------


async def _run_single(model: str, prompt_text: str) -> tuple[float, str]:
    """Call one model with one prompt, returning ``(latency_ms, content)``.

    Raises an exception on failure (timeout, API error, etc.).

    Args:
        model: litellm model string.
        prompt_text: The user message text.

    Returns:
        Tuple of ``(latency_ms, response_content)``.
    """
    import litellm

    messages = [{"role": "user", "content": prompt_text}]
    t0 = time.monotonic()
    response = await asyncio.wait_for(
        litellm.acompletion(model=model, messages=messages, max_tokens=128),
        timeout=_PROMPT_TIMEOUT_S,
    )
    elapsed_ms = (time.monotonic() - t0) * 1000.0
    content: str = response.choices[0].message.content or ""
    return elapsed_ms, content


async def _benchmark_model(model: str, runs: int) -> BenchmarkResult:
    """Run the full prompt set ``runs`` times against ``model``.

    Never raises — failures are captured in the result metrics.

    Args:
        model: litellm model string to benchmark.
        runs: Number of repetitions of the prompt set.

    Returns:
        Aggregated :class:`BenchmarkResult`.
    """
    latencies: list[float] = []
    total_prompts = 0
    successful_prompts = 0
    quality_passes = 0

    for _ in range(runs):
        for prompt_def in BENCHMARK_PROMPTS:
            total_prompts += 1
            prompt_text: str = str(prompt_def["prompt"])
            prompt_id: str = str(prompt_def["id"])
            expected: str | None = prompt_def.get("expected")  # type: ignore[assignment]

            try:
                latency_ms, content = await _run_single(model, prompt_text)
                latencies.append(latency_ms)
                successful_prompts += 1
                if _validate_response(prompt_id, expected, content):
                    quality_passes += 1
            except Exception:  # noqa: BLE001 — record failure, continue
                pass

    success_rate = successful_prompts / total_prompts if total_prompts else 0.0
    quality_score = quality_passes / successful_prompts if successful_prompts else 0.0

    if latencies:
        sorted_lats = sorted(latencies)
        n = len(sorted_lats)
        p50_ms = sorted_lats[n // 2]
        p95_idx = min(int(n * 0.95), n - 1)
        p95_ms = sorted_lats[p95_idx]
    else:
        p50_ms = 0.0
        p95_ms = 0.0

    return BenchmarkResult(
        model=model,
        p50_ms=p50_ms,
        p95_ms=p95_ms,
        success_rate=success_rate,
        quality_score=quality_score,
        last_run=datetime.now(UTC).isoformat(),
    )


def _discover_models() -> list[str]:
    """Return the list of models to benchmark based on environment.

    Includes a provider only when its API key env var is set.  Ollama is
    always included by querying ``localhost:11434``; any available Ollama
    model is added.

    Returns:
        List of litellm model strings to benchmark.
    """
    models: list[str] = []

    for model_str, env_var in _PROVIDER_KEYS.items():
        if os.environ.get(env_var):
            models.append(model_str)

    # Always include Ollama if running.
    try:
        import httpx

        resp = httpx.get("http://localhost:11434/api/tags", timeout=2)
        ollama_models = [m["name"] for m in resp.json().get("models", [])]
        for om in ollama_models:
            models.append(f"ollama/{om}")
    except Exception:  # noqa: BLE001 — Ollama not running, skip silently
        pass

    return models


async def run_benchmark(
    data_dir: Path,
    runs: int = _DEFAULT_RUNS,
    quiet: bool = False,
) -> dict[str, BenchmarkResult]:
    """Run benchmarks for all discovered providers and save to disk.

    Args:
        data_dir: ``.tta`` state directory where ``benchmarks.json`` is stored.
        runs: Number of prompt-set repetitions per model.
        quiet: Suppress progress output when ``True``.

    Returns:
        Final mapping from model string → :class:`BenchmarkResult`.
    """
    models = _discover_models()
    if not models:
        if not quiet:
            print("No providers configured — set an API key or start Ollama.")
        return {}

    if not quiet:
        print(f"Benchmarking {len(models)} model(s), {runs} run(s) each…")
        print()

    existing = load_benchmarks(data_dir)
    results: dict[str, BenchmarkResult] = dict(existing)

    for model in models:
        if not quiet:
            print(f"  [{model}] … ", end="", flush=True)
        result = await _benchmark_model(model, runs)
        results[model] = result
        if not quiet:
            status = "✓" if result.success_rate > 0 else "✗"
            print(
                f"{status}  p50={result.p50_ms:.0f}ms  "
                f"quality={result.quality_score:.0%}  "
                f"success={result.success_rate:.0%}"
            )

    save_benchmarks(data_dir, results)
    if not quiet:
        print()
        print(f"Results saved to {data_dir / 'benchmarks.json'}")
    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def cmd_benchmark(args: Any, data_dir: Path) -> int:
    """Handle ``tta models benchmark``.

    Args:
        args: Parsed argparse namespace.
        data_dir: ``.tta`` state directory.

    Returns:
        Exit code.
    """
    runs: int = getattr(args, "runs", _DEFAULT_RUNS)
    json_output: bool = getattr(args, "json_output", False)

    async def _run() -> dict[str, BenchmarkResult]:
        return await run_benchmark(data_dir, runs=runs, quiet=json_output)

    results = asyncio.run(_run())

    if json_output:
        payload = {
            "updated_at": datetime.now(UTC).isoformat(),
            "results": {model: r.to_dict() for model, r in results.items()},
        }
        print(json.dumps(payload, indent=2))

    return 0 if results else 1
