"""Tests for model_benchmarks module and benchmark-aware ModelRegistryPrimitive.

All tests are self-contained with no external dependencies or HTTP calls.
Follows AAA (Arrange / Act / Assert) pattern throughout.
"""

from __future__ import annotations

import re

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.llm.model_benchmarks import (
    BENCHMARK_DATA,
    KNOWN_BENCHMARKS,
    ModelBenchmarkMetadata,
    get_benchmarks,
    get_best_score,
    models_above_threshold,
)
from ttadev.primitives.llm.model_registry import (
    ModelEntry,
    ModelRegistryPrimitive,
    RegistryRequest,
    SelectionPolicy,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test-model-benchmarks")


def _registry(*entries: ModelEntry) -> ModelRegistryPrimitive:
    """Create a fresh, unpopulated registry seeded with the given entries."""
    reg = ModelRegistryPrimitive(prepopulate=False)
    for e in entries:
        reg._registry[ModelRegistryPrimitive._key(e.provider, e.model_id)] = e
    return reg


def _entry(
    model_id: str,
    provider: str = "ollama",
    cost_tier: str = "free",
    is_local: bool = True,
) -> ModelEntry:
    return ModelEntry(
        model_id=model_id,
        provider=provider,
        cost_tier=cost_tier,
        is_local=is_local,
    )


# ── get_benchmarks ────────────────────────────────────────────────────────────


class TestGetBenchmarks:
    def test_known_model_returns_entries(self) -> None:
        """get_benchmarks returns at least one entry for a model in BENCHMARK_DATA."""
        # Arrange
        model_id = "qwen2.5:7b"

        # Act
        results = get_benchmarks(model_id)

        # Assert
        assert len(results) > 0
        assert all(r.model_id == model_id for r in results)

    def test_known_model_contains_expected_benchmarks(self) -> None:
        """get_benchmarks for qwen2.5:7b includes mmlu, humaneval, and math."""
        # Arrange / Act
        results = get_benchmarks("qwen2.5:7b")
        benchmarks = {r.benchmark for r in results}

        # Assert
        assert "mmlu" in benchmarks
        assert "humaneval" in benchmarks
        assert "math" in benchmarks

    def test_unknown_model_returns_empty_list(self) -> None:
        """get_benchmarks returns [] for a model not in BENCHMARK_DATA."""
        # Arrange / Act / Assert
        assert get_benchmarks("nonexistent-model:latest") == []

    def test_all_returned_entries_are_model_benchmark_metadata(self) -> None:
        """Every item returned by get_benchmarks is a ModelBenchmarkMetadata instance."""
        # Arrange / Act
        results = get_benchmarks("llama3.1:8b")

        # Assert
        assert len(results) > 0
        for item in results:
            assert isinstance(item, ModelBenchmarkMetadata)

    def test_cloud_model_returns_entries(self) -> None:
        """get_benchmarks works for cloud model IDs like gpt-4o-mini."""
        # Arrange / Act
        results = get_benchmarks("gpt-4o-mini")

        # Assert
        assert len(results) >= 2  # at least mmlu + humaneval

    def test_coder_model_returns_entries(self) -> None:
        """get_benchmarks returns entries for Qwen coder variants."""
        # Arrange / Act
        results = get_benchmarks("qwen2.5-coder:32b")

        # Assert
        benchmarks = {r.benchmark for r in results}
        assert "humaneval" in benchmarks
        assert "mbpp" in benchmarks


# ── get_best_score ────────────────────────────────────────────────────────────


class TestGetBestScore:
    def test_returns_score_for_known_model_and_benchmark(self) -> None:
        """get_best_score returns a float for a known model/benchmark pair."""
        # Arrange / Act
        score = get_best_score("qwen2.5:72b", "mmlu")

        # Assert
        assert score is not None
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    def test_returns_none_for_unknown_model(self) -> None:
        """get_best_score returns None when the model has no benchmark data."""
        # Arrange / Act / Assert
        assert get_best_score("phantom-model:99b", "mmlu") is None

    def test_returns_none_for_unknown_benchmark_on_known_model(self) -> None:
        """get_best_score returns None when the benchmark has no entries for the model."""
        # Arrange / Act / Assert
        # Use a synthetic benchmark name that will never appear in curated or live data.
        assert get_best_score("qwen2.5:7b", "phantom-benchmark-xyz") is None

    def test_returns_maximum_when_duplicate_entries_injected(self) -> None:
        """get_best_score returns the highest score when duplicates exist."""
        # Arrange — temporarily inject a second entry with a higher score
        original_data = BENCHMARK_DATA[:]
        BENCHMARK_DATA.append(
            ModelBenchmarkMetadata(
                model_id="qwen2.5:7b",
                benchmark="mmlu",
                score=99.9,  # artificially high
                source_url="https://example.com/test",
                measured_date="2099-01-01",
                notes="synthetic duplicate for test",
            )
        )
        try:
            # Act
            score = get_best_score("qwen2.5:7b", "mmlu")
            # Assert
            assert score == pytest.approx(99.9)
        finally:
            BENCHMARK_DATA[:] = original_data

    def test_specific_known_score_llama31_humaneval(self) -> None:
        """get_best_score returns the expected published value for llama3.1:8b humaneval."""
        # Arrange / Act
        score = get_best_score("llama3.1:8b", "humaneval")

        # Assert
        assert score == pytest.approx(72.6, abs=0.1)

    def test_cloud_model_humaneval_score_meets_expectation(self) -> None:
        """get_best_score returns a value >= 87 for gpt-4o-mini humaneval."""
        # Arrange / Act
        score = get_best_score("gpt-4o-mini", "humaneval")

        # Assert
        assert score is not None
        assert score >= 87.0

    def test_gpqa_only_for_large_models(self) -> None:
        """Larger models (72b, gpt-4o) have gpqa data; small models do not."""
        # Arrange / Act / Assert
        assert get_best_score("qwen2.5:72b", "gpqa") is not None
        assert get_best_score("gpt-4o", "gpqa") is not None
        assert get_best_score("llama3.2:1b", "gpqa") is None

    def test_mt_bench_score_for_mixtral(self) -> None:
        """Mixtral 8x7B has an mt_bench score >= 80 (scaled from 8.0/10)."""
        # Arrange / Act
        score = get_best_score("mixtral:8x7b", "mt_bench")

        # Assert
        assert score is not None
        assert score >= 80.0


# ── models_above_threshold ────────────────────────────────────────────────────


class TestModelsAboveThreshold:
    def test_high_threshold_returns_fewer_models_than_low(self) -> None:
        """models_above_threshold with high threshold returns fewer models."""
        # Arrange / Act
        above_90 = models_above_threshold("humaneval", 90.0)
        above_50 = models_above_threshold("humaneval", 50.0)

        # Assert
        assert len(above_90) < len(above_50)

    def test_zero_threshold_returns_all_models_with_data(self) -> None:
        """models_above_threshold(0.0) returns every model that has any data."""
        # Arrange
        all_humaneval_models = {e.model_id for e in BENCHMARK_DATA if e.benchmark == "humaneval"}

        # Act
        result = set(models_above_threshold("humaneval", 0.0))

        # Assert
        assert all_humaneval_models == result

    def test_impossible_threshold_returns_empty(self) -> None:
        """models_above_threshold with score > 100 returns empty list."""
        # Arrange / Act / Assert
        assert models_above_threshold("mmlu", 101.0) == []

    def test_specific_models_appear_above_humaneval_80(self) -> None:
        """Models with known HumanEval >= 80 appear in threshold results."""
        # Arrange / Act
        results = models_above_threshold("humaneval", 80.0)

        # Assert — qwen2.5:7b (84.1) and llama3.3:70b (88.4) should qualify
        assert "qwen2.5:7b" in results
        assert "llama3.3:70b" in results

    def test_result_contains_no_duplicates(self) -> None:
        """models_above_threshold never returns duplicate model IDs."""
        # Arrange / Act
        results = models_above_threshold("mmlu", 0.0)

        # Assert
        assert len(results) == len(set(results))

    def test_unknown_benchmark_returns_empty(self) -> None:
        """models_above_threshold returns empty list for a benchmark with no data."""
        # Arrange / Act / Assert
        assert models_above_threshold("nonexistent_bench", 0.0) == []

    def test_models_below_threshold_excluded(self) -> None:
        """Small models with low scores are excluded from high-threshold results."""
        # Arrange / Act
        results = models_above_threshold("humaneval", 75.0)

        # Assert — llama3.2:1b (28.7) and gemma2:2b (35.4) should be absent
        assert "llama3.2:1b" not in results
        assert "gemma2:2b" not in results


# ── Data integrity ────────────────────────────────────────────────────────────


class TestDataIntegrity:
    def test_all_model_ids_are_non_empty_strings(self) -> None:
        """Every ModelBenchmarkMetadata has a non-empty model_id string."""
        # Arrange / Act / Assert
        for entry in BENCHMARK_DATA:
            assert isinstance(entry.model_id, str)
            assert len(entry.model_id) > 0, f"Empty model_id in entry: {entry}"

    def test_all_scores_in_valid_range(self) -> None:
        """Every benchmark score is within its expected range.

        Most benchmarks use a 0.0–100.0 percentage scale.
        The ``arena_elo`` benchmark is an exception: it stores raw LMSYS
        Chatbot Arena ELO values on a 0–2000 scale.
        """
        # Arrange / Act / Assert
        # These benchmarks store raw metrics (not 0–100 scores) and need their own range.
        raw_metric_benchmarks = {
            "arena_elo": (0.0, 2000.0),
            "aa_speed_tok_per_sec": (0.0, 10_000.0),  # tokens/sec — can exceed 100
            "aa_ttft_seconds": (0.0, 60.0),  # latency in seconds
            "aa_price_per_1m_input": (0.0, 1_000.0),  # USD per 1M tokens
        }
        for entry in BENCHMARK_DATA:
            if entry.benchmark in raw_metric_benchmarks:
                lo, hi = raw_metric_benchmarks[entry.benchmark]
                assert lo <= entry.score <= hi, (
                    f"{entry.benchmark} value {entry.score} out of {lo}–{hi} range "
                    f"for {entry.model_id}"
                )
            else:
                assert 0.0 <= entry.score <= 100.0, (
                    f"Score {entry.score} out of range for {entry.model_id}/{entry.benchmark}"
                )

    def test_all_benchmark_names_are_in_known_set(self) -> None:
        """Every benchmark field value is a member of KNOWN_BENCHMARKS."""
        # Arrange / Act / Assert
        for entry in BENCHMARK_DATA:
            assert entry.benchmark in KNOWN_BENCHMARKS, (
                f"Unknown benchmark {entry.benchmark!r} for {entry.model_id}"
            )

    def test_at_least_five_models_have_mmlu_data(self) -> None:
        """BENCHMARK_DATA contains MMLU entries for at least 5 distinct models."""
        # Arrange / Act
        mmlu_models = {e.model_id for e in BENCHMARK_DATA if e.benchmark == "mmlu"}

        # Assert
        assert len(mmlu_models) >= 5, f"Only {len(mmlu_models)} models have MMLU data"

    def test_at_least_five_models_have_humaneval_data(self) -> None:
        """BENCHMARK_DATA contains HumanEval entries for at least 5 distinct models."""
        # Arrange / Act
        he_models = {e.model_id for e in BENCHMARK_DATA if e.benchmark == "humaneval"}

        # Assert
        assert len(he_models) >= 5, f"Only {len(he_models)} models have HumanEval data"

    def test_all_source_urls_are_non_empty_strings(self) -> None:
        """Every entry has a non-empty source_url string."""
        # Arrange / Act / Assert
        for entry in BENCHMARK_DATA:
            assert isinstance(entry.source_url, str)
            assert len(entry.source_url) > 0, f"Empty source_url for {entry.model_id}"

    def test_all_measured_dates_are_iso_format(self) -> None:
        """Every measured_date is a 10-character ISO 8601 date string (YYYY-MM-DD)."""
        # Arrange
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

        # Act / Assert
        for entry in BENCHMARK_DATA:
            assert pattern.match(entry.measured_date), (
                f"measured_date {entry.measured_date!r} not ISO 8601 for {entry.model_id}"
            )

    def test_dataset_size_meets_minimum(self) -> None:
        """BENCHMARK_DATA contains at least 60 entries."""
        # Arrange / Act / Assert
        assert len(BENCHMARK_DATA) >= 60, f"Only {len(BENCHMARK_DATA)} entries in BENCHMARK_DATA"

    def test_entries_are_frozen_immutable(self) -> None:
        """ModelBenchmarkMetadata instances are immutable (frozen dataclass)."""
        # Arrange
        entry = BENCHMARK_DATA[0]

        # Act / Assert
        with pytest.raises((AttributeError, TypeError)):
            entry.score = 0.0  # type: ignore[misc]

    def test_all_models_have_at_least_mmlu_or_humaneval(self) -> None:
        """Every distinct model in BENCHMARK_DATA has at least one capability baseline benchmark.

        Accepts: mmlu, humaneval (curated static), mmlu_pro, aa_intelligence (live sources).
        Live data from Artificial Analysis and HF Leaderboard 2 provides mmlu_pro rather
        than plain mmlu, so both are valid capability baselines.
        """
        # Arrange
        capability_baselines = frozenset({"mmlu", "humaneval", "mmlu_pro", "aa_intelligence"})
        all_model_ids = {e.model_id for e in BENCHMARK_DATA}
        models_with_baseline = {
            e.model_id for e in BENCHMARK_DATA if e.benchmark in capability_baselines
        }

        # Assert — every model should have at least one capability baseline
        missing = all_model_ids - models_with_baseline
        assert missing == set(), f"Models with no capability baseline benchmark: {missing}"


# ── SelectionPolicy benchmark filters ─────────────────────────────────────────


class TestSelectionPolicyBenchmarkFilters:
    @pytest.mark.asyncio
    async def test_min_humaneval_score_excludes_low_scoring_models(self) -> None:
        """SelectionPolicy.min_humaneval_score removes models below the threshold."""
        # Arrange — qwen2.5:7b HumanEval=84.1, llama3.2:1b HumanEval=28.7
        high = _entry("qwen2.5:7b")
        low = _entry("llama3.2:1b")
        reg = _registry(high, low)
        ctx = _ctx()

        # Act — require HumanEval >= 80; llama3.2:1b (28.7) should be excluded
        resp = await reg.execute(
            RegistryRequest(
                action="select",
                policy=SelectionPolicy(
                    min_humaneval_score=80.0,
                    max_cost_tier="free",
                ),
            ),
            ctx,
        )

        # Assert
        assert resp.entry is not None
        assert resp.entry.model_id == "qwen2.5:7b"

    @pytest.mark.asyncio
    async def test_min_humaneval_score_excludes_models_with_no_data(self) -> None:
        """min_humaneval_score excludes models with no HumanEval data at all."""
        # Arrange
        no_data = _entry("mystery-model:7b")
        has_data = _entry("qwen2.5:7b")
        reg = _registry(no_data, has_data)
        ctx = _ctx()

        # Act
        resp = await reg.execute(
            RegistryRequest(
                action="select",
                policy=SelectionPolicy(min_humaneval_score=50.0, max_cost_tier="free"),
            ),
            ctx,
        )

        # Assert
        assert resp.entry is not None
        assert resp.entry.model_id == "qwen2.5:7b"

    @pytest.mark.asyncio
    async def test_min_mmlu_score_filters_registry(self) -> None:
        """SelectionPolicy.min_mmlu_score removes models below the MMLU threshold."""
        # Arrange — gemma2:2b MMLU=52.2, llama3.1:70b MMLU=86.0
        weak = _entry("gemma2:2b")
        strong = _entry("llama3.1:70b")
        reg = _registry(weak, strong)
        ctx = _ctx()

        # Act — require MMLU >= 80; gemma2:2b (52.2) should be excluded
        resp = await reg.execute(
            RegistryRequest(
                action="select",
                policy=SelectionPolicy(min_mmlu_score=80.0, max_cost_tier="free"),
            ),
            ctx,
        )

        # Assert
        assert resp.entry is not None
        assert resp.entry.model_id == "llama3.1:70b"

    @pytest.mark.asyncio
    async def test_no_models_pass_filter_returns_none(self) -> None:
        """select returns entry=None when all models are filtered by benchmark threshold."""
        # Arrange — both models have low HumanEval scores
        e1 = _entry("llama3.2:1b")  # HumanEval 28.7
        e2 = _entry("gemma2:2b")  # HumanEval 35.4
        reg = _registry(e1, e2)
        ctx = _ctx()

        # Act — require HumanEval >= 90, no model qualifies
        resp = await reg.execute(
            RegistryRequest(
                action="select",
                policy=SelectionPolicy(min_humaneval_score=90.0, max_cost_tier="free"),
            ),
            ctx,
        )

        # Assert
        assert resp.entry is None

    @pytest.mark.asyncio
    async def test_preferred_benchmark_sorts_by_score_descending(self) -> None:
        """preferred_benchmark causes higher-scoring models to rank first."""
        # Arrange — qwen2.5-coder:32b HumanEval=92.7, qwen2.5:7b HumanEval=84.1
        # Neither is local so locality doesn't affect the sort.
        coder = _entry(
            "qwen2.5-coder:32b",
            provider="cloud",
            cost_tier="medium",
            is_local=False,
        )
        base = _entry(
            "qwen2.5:7b",
            provider="cloud",
            cost_tier="medium",
            is_local=False,
        )
        reg = _registry(coder, base)
        ctx = _ctx()

        # Act
        resp = await reg.execute(
            RegistryRequest(
                action="select",
                policy=SelectionPolicy(
                    prefer_local=False,
                    preferred_benchmark="humaneval",
                    max_cost_tier="high",
                ),
            ),
            ctx,
        )

        # Assert — coder (92.7) beats base (84.1) on HumanEval
        assert resp.entry is not None
        assert resp.entry.model_id == "qwen2.5-coder:32b"

    @pytest.mark.asyncio
    async def test_combined_mmlu_and_humaneval_filters_applied_as_and(self) -> None:
        """Both min_mmlu_score and min_humaneval_score are applied as AND conditions."""
        # Arrange
        # qwen2.5:7b: MMLU=74.2 ✓, HumanEval=84.1 ✓
        # gemma2:9b:  MMLU=71.3 ✓, HumanEval=54.3 ✗ (fails HE threshold)
        ok = _entry("qwen2.5:7b")
        fail_he = _entry("gemma2:9b")
        reg = _registry(ok, fail_he)
        ctx = _ctx()

        # Act
        resp = await reg.execute(
            RegistryRequest(
                action="select",
                policy=SelectionPolicy(
                    min_mmlu_score=70.0,
                    min_humaneval_score=80.0,
                    max_cost_tier="free",
                ),
            ),
            ctx,
        )

        # Assert
        assert resp.entry is not None
        assert resp.entry.model_id == "qwen2.5:7b"


# ── RegistryRequest benchmark_filter on list action ───────────────────────────


class TestListBenchmarkFilter:
    @pytest.mark.asyncio
    async def test_benchmark_filter_excludes_models_without_data(self) -> None:
        """list with benchmark_filter omits models with no data for that benchmark."""
        # Arrange
        has_gpqa = _entry("qwen2.5:72b")  # has gpqa data (score=49.0)
        no_gpqa = _entry("gemma2:2b")  # no gpqa data
        reg = _registry(has_gpqa, no_gpqa)
        ctx = _ctx()

        # Act
        resp = await reg.execute(
            RegistryRequest(action="list", benchmark_filter="gpqa"),
            ctx,
        )

        # Assert
        ids = [e.model_id for e in resp.entries]
        assert "qwen2.5:72b" in ids
        assert "gemma2:2b" not in ids

    @pytest.mark.asyncio
    async def test_benchmark_filter_with_min_score_threshold(self) -> None:
        """list with benchmark_filter + min_benchmark_score applies score threshold."""
        # Arrange
        # llama3.1:70b MMLU=86.0 ✓, gemma2:9b MMLU=71.3 ✗, gemma2:2b MMLU=52.2 ✗
        high = _entry("llama3.1:70b")
        mid = _entry("gemma2:9b")
        low = _entry("gemma2:2b")
        reg = _registry(high, mid, low)
        ctx = _ctx()

        # Act — only models with MMLU >= 75
        resp = await reg.execute(
            RegistryRequest(
                action="list",
                benchmark_filter="mmlu",
                min_benchmark_score=75.0,
            ),
            ctx,
        )

        # Assert
        ids = [e.model_id for e in resp.entries]
        assert "llama3.1:70b" in ids
        assert "gemma2:9b" not in ids
        assert "gemma2:2b" not in ids

    @pytest.mark.asyncio
    async def test_no_benchmark_filter_returns_all_entries(self) -> None:
        """list without benchmark_filter is unaffected and returns all entries."""
        # Arrange
        e1 = _entry("qwen2.5:7b")
        e2 = _entry("mystery-model:7b")  # no benchmark data at all
        reg = _registry(e1, e2)
        ctx = _ctx()

        # Act
        resp = await reg.execute(RegistryRequest(action="list"), ctx)

        # Assert
        assert len(resp.entries) == 2

    @pytest.mark.asyncio
    async def test_min_benchmark_score_without_filter_is_ignored(self) -> None:
        """min_benchmark_score alone (no benchmark_filter) has no effect on list."""
        # Arrange
        e1 = _entry("qwen2.5:7b")
        e2 = _entry("gemma2:2b")
        reg = _registry(e1, e2)
        ctx = _ctx()

        # Act — only min_benchmark_score set, no benchmark_filter
        resp = await reg.execute(
            RegistryRequest(action="list", min_benchmark_score=99.0),
            ctx,
        )

        # Assert — filter not applied, both entries returned
        assert len(resp.entries) == 2
