"""Tests for EmpiricalEvalHarness — EvalHarnessPrimitive (issue #278).

All LLM calls are fully mocked — no HTTP traffic.

Pattern: Arrange / Act / Assert throughout.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.llm.eval_harness import (
    COST_PER_1K_OUTPUT_TOKENS,
    TASK_TYPE_PROFILES,
    EvalHarnessPrimitive,
    EvalRun,
    EvalTask,
    ModelEvalResult,
    _score_keywords,
)
from ttadev.primitives.llm.universal_llm_primitive import LLMResponse

# ── Test helpers ──────────────────────────────────────────────────────────────


def _task(
    *,
    task_id: str = "t1",
    prompt: str = "Say hello in three languages.",
    task_type: str = "general",
    keywords: list[str] | None = None,
    max_tokens: int = 512,
    temperature: float = 0.0,
    system_prompt: str | None = None,
) -> EvalTask:
    return EvalTask(
        task_id=task_id,
        prompt=prompt,
        system_prompt=system_prompt,
        task_type=task_type,
        expected_keywords=keywords or [],
        max_tokens=max_tokens,
        temperature=temperature,
    )


def _result(
    *,
    model_id: str = "model-a",
    provider: str = "groq",
    output: str = "Hello Hola Bonjour",
    latency_ms: float = 100.0,
    prompt_tokens: int = 10,
    completion_tokens: int = 20,
    cost_estimate_usd: float = 0.0,
    keyword_score: float = 1.0,
    error: str | None = None,
) -> ModelEvalResult:
    return ModelEvalResult(
        model_id=model_id,
        provider=provider,
        output=output,
        latency_ms=latency_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_estimate_usd=cost_estimate_usd,
        keyword_score=keyword_score,
        error=error,
    )


def _llm_resp(
    content: str = "Hello Hola Bonjour",
    model: str = "model-a",
    provider: str = "groq",
    prompt_tokens: int = 10,
    completion_tokens: int = 20,
) -> LLMResponse:
    return LLMResponse(
        content=content,
        model=model,
        provider=provider,
        usage={"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    )


def _ctx() -> WorkflowContext:
    return WorkflowContext.root("test-eval")


# ── 1. _score_keywords ────────────────────────────────────────────────────────


class TestScoreKeywords:
    def test_full_match_returns_one(self) -> None:
        # Arrange
        output = "Hello Hola Bonjour"
        keywords = ["hello", "hola", "bonjour"]
        # Act
        score = _score_keywords(output, keywords)
        # Assert
        assert score == pytest.approx(1.0)

    def test_half_match_returns_point_five(self) -> None:
        # Arrange
        output = "Hello world"
        keywords = ["hello", "bonjour"]
        # Act
        score = _score_keywords(output, keywords)
        # Assert
        assert score == pytest.approx(0.5)

    def test_no_match_returns_zero(self) -> None:
        # Arrange
        output = "Nothing relevant here"
        keywords = ["hello", "hola", "bonjour"]
        # Act
        score = _score_keywords(output, keywords)
        # Assert
        assert score == pytest.approx(0.0)

    def test_empty_keywords_returns_one(self) -> None:
        # Arrange / Act
        score = _score_keywords("any output", [])
        # Assert
        assert score == pytest.approx(1.0)

    def test_case_insensitive_matching(self) -> None:
        # Arrange
        output = "HELLO HOLA BONJOUR"
        keywords = ["hello", "hola", "bonjour"]
        # Act
        score = _score_keywords(output, keywords)
        # Assert
        assert score == pytest.approx(1.0)

    def test_one_of_three_keywords_found(self) -> None:
        # Arrange
        output = "I only say hello"
        keywords = ["hello", "hola", "bonjour"]
        # Act
        score = _score_keywords(output, keywords)
        # Assert
        assert score == pytest.approx(1 / 3)


# ── 2. EvalRun.ranked_results ─────────────────────────────────────────────────


class TestEvalRunRankedResults:
    def test_sorted_score_desc_then_latency_asc(self) -> None:
        # Arrange
        task = _task()
        results = [
            _result(model_id="slow-good", keyword_score=1.0, latency_ms=500.0),
            _result(model_id="fast-good", keyword_score=1.0, latency_ms=100.0),
            _result(model_id="bad", keyword_score=0.0, latency_ms=50.0),
        ]
        run = EvalRun(run_id="r1", task=task, results=results)
        # Act
        ranked = run.ranked_results()
        # Assert
        assert [r.model_id for r in ranked] == ["fast-good", "slow-good", "bad"]

    def test_error_results_sort_to_bottom(self) -> None:
        # Arrange
        task = _task()
        results = [
            _result(model_id="errored", keyword_score=0.0, latency_ms=1.0, error="oops"),
            _result(model_id="winner", keyword_score=0.8, latency_ms=200.0),
        ]
        run = EvalRun(run_id="r2", task=task, results=results)
        # Act
        ranked = run.ranked_results()
        # Assert
        assert ranked[0].model_id == "winner"
        assert ranked[-1].model_id == "errored"

    def test_does_not_mutate_original_results_list(self) -> None:
        # Arrange
        task = _task()
        results = [
            _result(model_id="b", keyword_score=0.5),
            _result(model_id="a", keyword_score=1.0),
        ]
        run = EvalRun(run_id="r3", task=task, results=results)
        # Act
        ranked = run.ranked_results()
        # Assert — original order preserved
        assert run.results[0].model_id == "b"
        assert ranked[0].model_id == "a"

    def test_single_result_returns_that_result(self) -> None:
        # Arrange
        task = _task()
        run = EvalRun(run_id="r4", task=task, results=[_result(model_id="only")])
        # Act
        ranked = run.ranked_results()
        # Assert
        assert len(ranked) == 1
        assert ranked[0].model_id == "only"

    def test_empty_results_returns_empty_list(self) -> None:
        # Arrange
        run = EvalRun(run_id="r5", task=_task(), results=[])
        # Act / Assert
        assert run.ranked_results() == []


# ── 3. EvalRun.to_report ─────────────────────────────────────────────────────


class TestEvalRunToReport:
    def _make_run(self) -> EvalRun:
        tsk = _task(task_id="greet", prompt="Say hello", keywords=["hello"])
        results = [
            _result(
                model_id="gpt-4o-mini",
                provider="openai",
                keyword_score=1.0,
                latency_ms=300.0,
                completion_tokens=50,
                cost_estimate_usd=0.00003,
            ),
            _result(
                model_id="llama-8b",
                provider="groq",
                keyword_score=0.5,
                latency_ms=150.0,
                completion_tokens=40,
                cost_estimate_usd=0.0,
            ),
        ]
        run = EvalRun(run_id="run-xyz", task=tsk, results=results, started_at=0.0)
        run.completed_at = 1.5
        return run

    def test_report_contains_markdown_table_header(self) -> None:
        report = self._make_run().to_report()
        assert "| Rank | Model | Provider | Score | Latency (ms) | Tokens | Est. Cost |" in report

    def test_report_lists_all_models(self) -> None:
        report = self._make_run().to_report()
        assert "gpt-4o-mini" in report
        assert "llama-8b" in report

    def test_report_shows_ranked_order_best_first(self) -> None:
        # Arrange
        report = self._make_run().to_report()
        # Assert — gpt-4o-mini (score=1.0) appears before llama-8b (score=0.5)
        idx_gpt = report.index("gpt-4o-mini")
        idx_llama = report.index("llama-8b")
        assert idx_gpt < idx_llama

    def test_report_includes_run_id(self) -> None:
        assert "run-xyz" in self._make_run().to_report()

    def test_report_includes_task_id(self) -> None:
        assert "greet" in self._make_run().to_report()

    def test_error_model_shows_warning_marker(self) -> None:
        # Arrange
        tsk = _task()
        results = [_result(model_id="flaky", error="connection refused", keyword_score=0.0)]
        run = EvalRun(run_id="r-err", task=tsk, results=results)
        # Act
        report = run.to_report()
        # Assert
        assert "flaky ⚠" in report

    def test_completion_duration_line_present(self) -> None:
        assert "Run completed in 1.50s" in self._make_run().to_report()

    def test_long_prompt_truncated_to_120_chars_with_ellipsis(self) -> None:
        # Arrange
        long_prompt = "x" * 200
        run = EvalRun(run_id="r-long", task=_task(prompt=long_prompt))
        # Act
        report = run.to_report()
        # Assert
        assert "x" * 120 + "..." in report

    def test_short_prompt_not_truncated(self) -> None:
        # Arrange
        short_prompt = "hello"
        run = EvalRun(run_id="r-short", task=_task(prompt=short_prompt))
        # Act
        report = run.to_report()
        # Assert — no trailing ellipsis
        assert "hello..." not in report
        assert "hello" in report


# ── 4. EvalHarnessPrimitive.execute — happy path ─────────────────────────────


class TestEvalHarnessPrimitiveExecute:
    @pytest.mark.asyncio
    async def test_execute_calls_all_models_and_populates_results(self) -> None:
        # Arrange
        models = [("groq", "llama-3.1-8b-instant"), ("openai", "gpt-4o-mini")]
        harness = EvalHarnessPrimitive(models=models, max_concurrent=2, timeout_seconds=10.0)
        task = _task(keywords=["hello"])

        with patch("ttadev.primitives.llm.eval_harness.UniversalLLMPrimitive") as mock_llm:
            mock_llm.return_value.execute = AsyncMock(return_value=_llm_resp(content="hello world"))
            # Act
            run = await harness.execute(task, _ctx())

        # Assert
        assert len(run.results) == 2
        model_ids = {r.model_id for r in run.results}
        assert "llama-3.1-8b-instant" in model_ids
        assert "gpt-4o-mini" in model_ids

    @pytest.mark.asyncio
    async def test_failed_model_sets_error_field_not_raises(self) -> None:
        # Arrange
        models = [("groq", "good-model"), ("openai", "bad-model")]
        harness = EvalHarnessPrimitive(models=models, max_concurrent=2, timeout_seconds=10.0)

        def _side_effect(request: Any, ctx: Any) -> Any:
            if request.model == "bad-model":
                raise RuntimeError("API error 500")

            async def _ok() -> LLMResponse:
                return _llm_resp()

            return _ok()

        with patch("ttadev.primitives.llm.eval_harness.UniversalLLMPrimitive") as mock_llm:
            mock_llm.return_value.execute = _side_effect
            # Act
            run = await harness.execute(_task(), _ctx())

        # Assert — both results present, bad model has error
        assert len(run.results) == 2
        bad = next(r for r in run.results if r.model_id == "bad-model")
        assert bad.error is not None
        assert "API error 500" in bad.error
        assert bad.keyword_score == pytest.approx(0.0)

    @pytest.mark.asyncio
    async def test_keyword_score_two_of_three(self) -> None:
        # Arrange
        harness = EvalHarnessPrimitive(models=[("groq", "llama-8b")])
        task = _task(keywords=["hello", "hola", "bonjour"])

        with patch("ttadev.primitives.llm.eval_harness.UniversalLLMPrimitive") as mock_llm:
            mock_llm.return_value.execute = AsyncMock(
                return_value=_llm_resp(content="Hello and Hola are greetings")
            )
            # Act
            run = await harness.execute(task, _ctx())

        # Assert — 2/3 keywords found
        assert run.results[0].keyword_score == pytest.approx(2 / 3)

    @pytest.mark.asyncio
    async def test_run_id_is_unique_per_execute_call(self) -> None:
        # Arrange
        harness = EvalHarnessPrimitive(models=[("groq", "llama-8b")])

        with patch("ttadev.primitives.llm.eval_harness.UniversalLLMPrimitive") as mock_llm:
            mock_llm.return_value.execute = AsyncMock(return_value=_llm_resp())
            run1 = await harness.execute(_task(), _ctx())
            run2 = await harness.execute(_task(), _ctx())

        # Assert
        assert run1.run_id != run2.run_id

    @pytest.mark.asyncio
    async def test_completed_at_is_set_after_execute(self) -> None:
        # Arrange
        harness = EvalHarnessPrimitive(models=[("groq", "llama-8b")])

        with patch("ttadev.primitives.llm.eval_harness.UniversalLLMPrimitive") as mock_llm:
            mock_llm.return_value.execute = AsyncMock(return_value=_llm_resp())
            # Act
            run = await harness.execute(_task(), _ctx())

        # Assert
        assert run.completed_at is not None
        assert run.completed_at >= run.started_at

    @pytest.mark.asyncio
    async def test_timeout_model_gets_error_result_not_exception(self) -> None:
        # Arrange
        harness = EvalHarnessPrimitive(models=[("groq", "slow-model")], timeout_seconds=0.01)

        async def _slow(*args: Any, **kwargs: Any) -> LLMResponse:
            await asyncio.sleep(5.0)
            return _llm_resp()

        with patch("ttadev.primitives.llm.eval_harness.UniversalLLMPrimitive") as mock_llm:
            mock_llm.return_value.execute = _slow
            # Act
            run = await harness.execute(_task(), _ctx())

        # Assert
        result = run.results[0]
        assert result.error is not None
        assert "Timeout" in result.error
        assert result.keyword_score == pytest.approx(0.0)
        assert result.output == ""

    @pytest.mark.asyncio
    async def test_unknown_provider_gives_error_result(self) -> None:
        # Arrange — no mock needed; LLMProvider() raises ValueError synchronously
        harness = EvalHarnessPrimitive(models=[("not_a_real_provider", "some-model")])
        # Act
        run = await harness.execute(_task(), _ctx())
        # Assert
        assert len(run.results) == 1
        assert run.results[0].error is not None
        assert "Unknown provider" in run.results[0].error

    @pytest.mark.asyncio
    async def test_no_models_produces_empty_results(self) -> None:
        # Arrange
        harness = EvalHarnessPrimitive(models=[])
        # Act
        run = await harness.execute(_task(), _ctx())
        # Assert
        assert run.results == []
        assert run.completed_at is not None


# ── 5. Cost estimation ────────────────────────────────────────────────────────


class TestCostEstimation:
    @pytest.mark.asyncio
    async def test_ollama_local_model_cost_is_zero(self) -> None:
        # Arrange
        harness = EvalHarnessPrimitive(models=[("ollama", "llama3.2:latest")])

        with patch("ttadev.primitives.llm.eval_harness.UniversalLLMPrimitive") as mock_llm:
            mock_llm.return_value.execute = AsyncMock(
                return_value=_llm_resp(completion_tokens=500, provider="ollama")
            )
            run = await harness.execute(_task(), _ctx())

        # Assert
        assert run.results[0].cost_estimate_usd == pytest.approx(0.0)

    @pytest.mark.asyncio
    async def test_openai_model_has_nonzero_cost_estimate(self) -> None:
        # Arrange
        harness = EvalHarnessPrimitive(models=[("openai", "gpt-4o-mini")])

        with patch("ttadev.primitives.llm.eval_harness.UniversalLLMPrimitive") as mock_llm:
            mock_llm.return_value.execute = AsyncMock(
                return_value=_llm_resp(
                    completion_tokens=1000, provider="openai", model="gpt-4o-mini"
                )
            )
            run = await harness.execute(_task(), _ctx())

        # Assert
        result = run.results[0]
        assert result.cost_estimate_usd > 0.0
        expected = (1000 / 1000.0) * COST_PER_1K_OUTPUT_TOKENS["openai"]
        assert result.cost_estimate_usd == pytest.approx(expected)

    @pytest.mark.asyncio
    async def test_groq_cost_is_zero(self) -> None:
        # Arrange
        harness = EvalHarnessPrimitive(models=[("groq", "llama-3.1-8b-instant")])

        with patch("ttadev.primitives.llm.eval_harness.UniversalLLMPrimitive") as mock_llm:
            mock_llm.return_value.execute = AsyncMock(
                return_value=_llm_resp(completion_tokens=999, provider="groq")
            )
            run = await harness.execute(_task(), _ctx())

        # Assert
        assert run.results[0].cost_estimate_usd == pytest.approx(0.0)


# ── 6. Concurrency control ────────────────────────────────────────────────────


class TestConcurrencyControl:
    @pytest.mark.asyncio
    async def test_semaphore_limits_peak_concurrent_calls(self) -> None:
        """At most max_concurrent=2 calls should be in-flight simultaneously."""
        # Arrange
        max_concurrent = 2
        models = [("groq", f"model-{i}") for i in range(5)]
        harness = EvalHarnessPrimitive(models=models, max_concurrent=max_concurrent)

        active: list[int] = []
        peak: list[int] = []

        async def _tracked(*args: Any, **kwargs: Any) -> LLMResponse:
            active.append(1)
            peak.append(len(active))
            await asyncio.sleep(0.02)
            active.pop()
            return _llm_resp()

        with patch("ttadev.primitives.llm.eval_harness.UniversalLLMPrimitive") as mock_llm:
            mock_llm.return_value.execute = _tracked
            run = await harness.execute(_task(), _ctx())

        # Assert
        assert max(peak) <= max_concurrent
        assert len(run.results) == 5

    @pytest.mark.asyncio
    async def test_all_results_collected_with_tight_concurrency_limit(self) -> None:
        # Arrange
        models = [("groq", f"model-{i}") for i in range(6)]
        harness = EvalHarnessPrimitive(models=models, max_concurrent=2)

        with patch("ttadev.primitives.llm.eval_harness.UniversalLLMPrimitive") as mock_llm:
            mock_llm.return_value.execute = AsyncMock(return_value=_llm_resp())
            run = await harness.execute(_task(), _ctx())

        # Assert — all 6 models produce a result
        assert len(run.results) == 6


# ── 7. Task-type profiles ─────────────────────────────────────────────────────


class TestTaskTypeProfiles:
    def test_all_expected_task_types_present(self) -> None:
        for task_type in ("code", "narrative", "classification", "extraction", "general"):
            assert task_type in TASK_TYPE_PROFILES
            profile = TASK_TYPE_PROFILES[task_type]
            assert "temperature" in profile
            assert "max_tokens" in profile

    def test_code_profile_max_tokens_is_1024(self) -> None:
        assert TASK_TYPE_PROFILES["code"]["max_tokens"] == 1024

    def test_classification_profile_max_tokens_is_64(self) -> None:
        assert TASK_TYPE_PROFILES["classification"]["max_tokens"] == 64

    def test_narrative_profile_temperature_is_nonzero(self) -> None:
        assert TASK_TYPE_PROFILES["narrative"]["temperature"] > 0.0

    def test_code_profile_temperature_is_zero(self) -> None:
        assert TASK_TYPE_PROFILES["code"]["temperature"] == pytest.approx(0.0)

    @pytest.mark.asyncio
    async def test_code_task_passes_zero_temperature_to_llm(self) -> None:
        # Arrange
        harness = EvalHarnessPrimitive(models=[("groq", "llama-8b")])
        task = _task(task_type="code", temperature=0.0)
        captured: list[Any] = []

        async def _capture(request: Any, ctx: Any) -> LLMResponse:
            captured.append(request)
            return _llm_resp()

        with patch("ttadev.primitives.llm.eval_harness.UniversalLLMPrimitive") as mock_llm:
            mock_llm.return_value.execute = _capture
            await harness.execute(task, _ctx())

        # Assert
        assert captured[0].temperature == pytest.approx(0.0)
