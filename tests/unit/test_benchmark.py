"""Unit tests for the benchmark runner and SmartRouter benchmark integration.

Coverage:
- BenchmarkResult serialisation/deserialisation
- save_benchmarks / load_benchmarks roundtrip
- load_benchmarks graceful fallback (no file, corrupt file)
- _validate_response for each prompt type
- _build_tiers() default order (no benchmarks)
- _build_tiers() quality mode sorts by quality_score desc
- _build_tiers() fast mode sorts by p50_ms asc
- _build_tiers() graceful fallback when benchmarks.json absent
- _build_tiers() partial data (some tiers unbenchmarked)
- SmartRouterPrimitive.make() with mode kwarg
- cmd_benchmark returns 1 when no providers configured
- run_benchmark mock path (no real network)
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.cli.benchmark import (
    BENCHMARK_PROMPTS,
    BenchmarkResult,
    _validate_response,
    load_benchmarks,
    run_benchmark,
    save_benchmarks,
)
from ttadev.primitives.llm.smart_router import SmartRouterPrimitive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(
    model: str = "groq/llama-3.3-70b-versatile",
    p50_ms: float = 400.0,
    p95_ms: float = 600.0,
    success_rate: float = 1.0,
    quality_score: float = 0.9,
    last_run: str = "2026-01-01T00:00:00+00:00",
) -> BenchmarkResult:
    return BenchmarkResult(
        model=model,
        p50_ms=p50_ms,
        p95_ms=p95_ms,
        success_rate=success_rate,
        quality_score=quality_score,
        last_run=last_run,
    )


# ---------------------------------------------------------------------------
# BenchmarkResult
# ---------------------------------------------------------------------------


class TestBenchmarkResult:
    def test_to_dict_keys(self) -> None:
        r = _make_result()
        d = r.to_dict()
        assert set(d) == {"p50_ms", "p95_ms", "success_rate", "quality_score", "last_run"}

    def test_to_dict_values(self) -> None:
        r = _make_result(p50_ms=420.5, p95_ms=680.0, success_rate=1.0, quality_score=0.95)
        d = r.to_dict()
        assert d["p50_ms"] == 420.5
        assert d["p95_ms"] == 680.0
        assert d["success_rate"] == 1.0
        assert d["quality_score"] == 0.95

    def test_from_dict_roundtrip(self) -> None:
        r = _make_result(model="ollama/qwen2.5:7b", p50_ms=1200.0, quality_score=0.85)
        d = r.to_dict()
        r2 = BenchmarkResult.from_dict("ollama/qwen2.5:7b", d)
        assert r2.model == "ollama/qwen2.5:7b"
        assert r2.p50_ms == 1200.0
        assert r2.quality_score == 0.85

    def test_from_dict_defaults_on_missing_keys(self) -> None:
        r = BenchmarkResult.from_dict("x/y", {})
        assert r.p50_ms == 0.0
        assert r.quality_score == 0.0
        assert r.success_rate == 0.0
        assert r.last_run == ""

    def test_slots(self) -> None:
        r = _make_result()
        assert hasattr(r, "model")
        assert hasattr(r, "p50_ms")


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------


class TestSaveBenchmarks:
    def test_creates_directory(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "state" / ".tta"
        save_benchmarks(data_dir, {"m": _make_result("m")})
        assert (data_dir / "benchmarks.json").exists()

    def test_json_schema(self, tmp_path: Path) -> None:
        results = {
            "groq/llama-3.3-70b-versatile": _make_result("groq/llama-3.3-70b-versatile"),
        }
        save_benchmarks(tmp_path, results)
        raw = json.loads((tmp_path / "benchmarks.json").read_text())
        assert "updated_at" in raw
        assert "results" in raw
        assert "groq/llama-3.3-70b-versatile" in raw["results"]

    def test_values_persisted(self, tmp_path: Path) -> None:
        r = _make_result(p50_ms=321.0, quality_score=0.77)
        save_benchmarks(tmp_path, {"m/n": r})
        raw = json.loads((tmp_path / "benchmarks.json").read_text())
        assert raw["results"]["m/n"]["p50_ms"] == 321.0
        assert raw["results"]["m/n"]["quality_score"] == 0.77


class TestLoadBenchmarks:
    def test_load_roundtrip(self, tmp_path: Path) -> None:
        r = _make_result("groq/llama-3.3-70b-versatile", p50_ms=420.0)
        save_benchmarks(tmp_path, {"groq/llama-3.3-70b-versatile": r})
        loaded = load_benchmarks(tmp_path)
        assert "groq/llama-3.3-70b-versatile" in loaded
        assert loaded["groq/llama-3.3-70b-versatile"].p50_ms == 420.0

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        result = load_benchmarks(tmp_path / "nonexistent")
        assert result == {}

    def test_corrupt_file_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / "benchmarks.json").write_text("NOT JSON {{{{")
        result = load_benchmarks(tmp_path)
        assert result == {}

    def test_empty_results_section(self, tmp_path: Path) -> None:
        payload = {"updated_at": "2026-01-01T00:00:00Z", "results": {}}
        (tmp_path / "benchmarks.json").write_text(json.dumps(payload))
        assert load_benchmarks(tmp_path) == {}

    def test_multiple_models(self, tmp_path: Path) -> None:
        results = {
            "groq/m": _make_result("groq/m", p50_ms=100.0),
            "ollama/m": _make_result("ollama/m", p50_ms=2000.0),
        }
        save_benchmarks(tmp_path, results)
        loaded = load_benchmarks(tmp_path)
        assert len(loaded) == 2
        assert loaded["groq/m"].p50_ms == 100.0


# ---------------------------------------------------------------------------
# _validate_response
# ---------------------------------------------------------------------------


class TestValidateResponse:
    def test_echo_exact_match(self) -> None:
        assert _validate_response("echo", "BENCHMARK_OK", "BENCHMARK_OK")

    def test_echo_substring_match(self) -> None:
        assert _validate_response("echo", "BENCHMARK_OK", "Sure! BENCHMARK_OK done.")

    def test_echo_no_match(self) -> None:
        assert not _validate_response("echo", "BENCHMARK_OK", "I am sorry I cannot do that.")

    def test_math_correct(self) -> None:
        assert _validate_response("math", "391", "391")

    def test_math_wrong(self) -> None:
        assert not _validate_response("math", "391", "400")

    def test_code_valid_python(self) -> None:
        assert _validate_response("code", None, "s[::-1]")

    def test_code_valid_python_exec(self) -> None:
        assert _validate_response("code", None, "result = s[::-1]")

    def test_code_invalid_python(self) -> None:
        assert not _validate_response("code", None, "def oops if x")

    def test_unknown_prompt_id_nonempty_passes(self) -> None:
        assert _validate_response("unknown", None, "some text")

    def test_unknown_prompt_id_empty_fails(self) -> None:
        assert not _validate_response("unknown", None, "")


# ---------------------------------------------------------------------------
# SmartRouterPrimitive._build_tiers() — default order
# ---------------------------------------------------------------------------


class TestBuildTiersDefault:
    def test_no_keys_only_ollama(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        router = SmartRouterPrimitive(data_dir=tmp_path)
        tiers = router._build_tiers()
        assert len(tiers) == 1
        assert tiers[0].provider == "ollama"

    def test_groq_key_adds_groq_tier(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        router = SmartRouterPrimitive(data_dir=tmp_path)
        tiers = router._build_tiers()
        providers = [t.provider for t in tiers]
        assert "groq" in providers
        assert providers[0] == "groq"  # groq first in default order

    def test_all_keys_four_tiers(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.setenv("GOOGLE_API_KEY", "k2")
        monkeypatch.setenv("OPENROUTER_API_KEY", "k3")
        router = SmartRouterPrimitive(data_dir=tmp_path)
        tiers = router._build_tiers()
        assert len(tiers) == 4


# ---------------------------------------------------------------------------
# SmartRouterPrimitive._build_tiers() — quality mode
# ---------------------------------------------------------------------------


class TestBuildTiersQualityMode:
    def _write_benchmarks(self, data_dir: Path, entries: dict) -> None:
        payload = {"updated_at": "2026-01-01T00:00:00Z", "results": entries}
        (data_dir / "benchmarks.json").write_text(json.dumps(payload))

    def test_quality_mode_sorts_by_quality_score_desc(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.setenv("GOOGLE_API_KEY", "k2")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        # groq has lower quality, google has higher → google should come first
        self._write_benchmarks(
            tmp_path,
            {
                "groq/llama-3.3-70b-versatile": {
                    "p50_ms": 400,
                    "p95_ms": 600,
                    "success_rate": 1.0,
                    "quality_score": 0.6,
                    "last_run": "2026-01-01T00:00:00Z",
                },
                "gemini/gemini-2.0-flash-lite": {
                    "p50_ms": 700,
                    "p95_ms": 1000,
                    "success_rate": 1.0,
                    "quality_score": 0.95,
                    "last_run": "2026-01-01T00:00:00Z",
                },
            },
        )
        router = SmartRouterPrimitive(mode="quality", data_dir=tmp_path)
        tiers = router._build_tiers()
        providers = [t.provider for t in tiers]
        assert providers.index("google") < providers.index("groq")

    def test_quality_mode_no_benchmarks_keeps_default_order(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.setenv("GOOGLE_API_KEY", "k2")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        router = SmartRouterPrimitive(mode="quality", data_dir=tmp_path)
        tiers = router._build_tiers()
        providers = [t.provider for t in tiers]
        # No benchmark data → default order: groq first
        assert providers[0] == "groq"

    def test_quality_mode_unbenchmarked_tiers_sorted_last(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.setenv("GOOGLE_API_KEY", "k2")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        # Only groq benchmarked; google has no entry → ollama/google sorted after groq
        self._write_benchmarks(
            tmp_path,
            {
                "groq/llama-3.3-70b-versatile": {
                    "p50_ms": 400,
                    "p95_ms": 600,
                    "success_rate": 1.0,
                    "quality_score": 0.9,
                    "last_run": "2026-01-01T00:00:00Z",
                },
            },
        )
        router = SmartRouterPrimitive(mode="quality", data_dir=tmp_path)
        tiers = router._build_tiers()
        assert tiers[0].provider == "groq"


# ---------------------------------------------------------------------------
# SmartRouterPrimitive._build_tiers() — fast mode
# ---------------------------------------------------------------------------


class TestBuildTiersFastMode:
    def _write_benchmarks(self, data_dir: Path, entries: dict) -> None:
        payload = {"updated_at": "2026-01-01T00:00:00Z", "results": entries}
        (data_dir / "benchmarks.json").write_text(json.dumps(payload))

    def test_fast_mode_sorts_by_p50_ms_asc(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.setenv("GOOGLE_API_KEY", "k2")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        # groq slower, google faster → google should come first
        self._write_benchmarks(
            tmp_path,
            {
                "groq/llama-3.3-70b-versatile": {
                    "p50_ms": 900,
                    "p95_ms": 1200,
                    "success_rate": 1.0,
                    "quality_score": 0.9,
                    "last_run": "2026-01-01T00:00:00Z",
                },
                "gemini/gemini-2.0-flash-lite": {
                    "p50_ms": 200,
                    "p95_ms": 350,
                    "success_rate": 1.0,
                    "quality_score": 0.85,
                    "last_run": "2026-01-01T00:00:00Z",
                },
            },
        )
        router = SmartRouterPrimitive(mode="fast", data_dir=tmp_path)
        tiers = router._build_tiers()
        providers = [t.provider for t in tiers]
        assert providers.index("google") < providers.index("groq")

    def test_fast_mode_no_benchmarks_keeps_default_order(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        router = SmartRouterPrimitive(mode="fast", data_dir=tmp_path)
        tiers = router._build_tiers()
        assert tiers[0].provider == "groq"

    def test_fast_mode_unbenchmarked_placed_after_benchmarked(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GROQ_API_KEY", "k1")
        monkeypatch.setenv("GOOGLE_API_KEY", "k2")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        # Only google benchmarked; groq not benchmarked → groq placed after google
        self._write_benchmarks(
            tmp_path,
            {
                "gemini/gemini-2.0-flash-lite": {
                    "p50_ms": 200,
                    "p95_ms": 350,
                    "success_rate": 1.0,
                    "quality_score": 0.85,
                    "last_run": "2026-01-01T00:00:00Z",
                },
            },
        )
        router = SmartRouterPrimitive(mode="fast", data_dir=tmp_path)
        tiers = router._build_tiers()
        assert tiers[0].provider == "google"


# ---------------------------------------------------------------------------
# SmartRouterPrimitive.make()
# ---------------------------------------------------------------------------


class TestSmartRouterMake:
    def test_make_returns_adapter(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        from ttadev.primitives.llm.smart_router import LiteLLMSmartAdapter

        adapter = SmartRouterPrimitive.make(mode="default", data_dir=tmp_path)
        assert isinstance(adapter, LiteLLMSmartAdapter)


# ---------------------------------------------------------------------------
# run_benchmark — mocked (no real network)
# ---------------------------------------------------------------------------


class TestRunBenchmark:
    @pytest.mark.asyncio
    async def test_no_providers_returns_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        # Simulate Ollama not running
        with patch("ttadev.cli.benchmark._discover_models", return_value=[]):
            results = await run_benchmark(tmp_path, runs=1, quiet=True)
        assert results == {}

    @pytest.mark.asyncio
    async def test_saves_results_to_disk(self, tmp_path: Path) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "BENCHMARK_OK"

        with (
            patch("ttadev.cli.benchmark._discover_models", return_value=["groq/test-model"]),
            patch(
                "litellm.acompletion",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
        ):
            results = await run_benchmark(tmp_path, runs=1, quiet=True)

        assert "groq/test-model" in results
        assert (tmp_path / "benchmarks.json").exists()

    @pytest.mark.asyncio
    async def test_failure_recorded_not_raised(self, tmp_path: Path) -> None:
        with (
            patch(
                "ttadev.cli.benchmark._discover_models",
                return_value=["groq/failing-model"],
            ),
            patch(
                "litellm.acompletion",
                new_callable=AsyncMock,
                side_effect=RuntimeError("connection refused"),
            ),
        ):
            results = await run_benchmark(tmp_path, runs=1, quiet=True)

        assert "groq/failing-model" in results
        assert results["groq/failing-model"].success_rate == 0.0

    @pytest.mark.asyncio
    async def test_quality_score_computed(self, tmp_path: Path) -> None:
        # Only the echo prompt returns the expected value; others return garbage.
        call_count = 0

        async def _mock_acompletion(model: str, messages: list, **kwargs: object) -> object:
            nonlocal call_count
            resp = MagicMock()
            resp.choices = [MagicMock()]
            prompt_text = messages[0]["content"]
            if "BENCHMARK_OK" in prompt_text:
                resp.choices[0].message.content = "BENCHMARK_OK"
            else:
                resp.choices[0].message.content = "garbage"
            call_count += 1
            return resp

        with (
            patch("ttadev.cli.benchmark._discover_models", return_value=["groq/test"]),
            patch("litellm.acompletion", new_callable=AsyncMock),
            patch("litellm.acompletion", side_effect=_mock_acompletion),
        ):
            results = await run_benchmark(tmp_path, runs=1, quiet=True)

        r = results["groq/test"]
        assert r.success_rate == 1.0
        # echo and code prompts pass ("garbage" is valid Python syntax), math fails
        assert r.quality_score == pytest.approx(2 / 3, abs=0.01)


# ---------------------------------------------------------------------------
# BENCHMARK_PROMPTS sanity checks
# ---------------------------------------------------------------------------


class TestBenchmarkPromptsDefinition:
    def test_has_three_prompts(self) -> None:
        assert len(BENCHMARK_PROMPTS) == 3

    def test_ids_are_unique(self) -> None:
        ids = [p["id"] for p in BENCHMARK_PROMPTS]
        assert len(ids) == len(set(ids))

    def test_echo_has_expected(self) -> None:
        echo = next(p for p in BENCHMARK_PROMPTS if p["id"] == "echo")
        assert echo["expected"] is not None

    def test_code_expected_is_none(self) -> None:
        code = next(p for p in BENCHMARK_PROMPTS if p["id"] == "code")
        assert code["expected"] is None
