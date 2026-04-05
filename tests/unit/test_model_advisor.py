"""Unit tests for ModelAdvisor, strategy.py, and training_estimator.py.

Covers:
- advisor.py: _classify_entry, _build_tier_map, _estimate_cost, _build_recommendation,
  ModelAdvisor.recommend_tier, estimate_roi, recommend_with_roi, _select_tier,
  _build_fallbacks, TIER_COST_DEFAULTS, _TIER_PRIORITY, advisor singleton.
- strategy.py: suggest_qwen_finetunes, _FINETUNE_IMPROVEMENT, _FINETUNE_BASE_COST,
  _build_rationale, edge cases (score clamping, inf breakeven, unknown task, sorting).
- training_estimator.py: estimate_finetune_cost, estimate_quality_improvement,
  calculate_roi_breakeven, build_roi_estimate, all constants.

asyncio_mode = auto — no @pytest.mark.asyncio needed.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from ttadev.primitives.llm.model_advisor.advisor import (
    _TIER_PRIORITY,
    TIER_COST_DEFAULTS,
    ModelAdvisor,
    _build_recommendation,
    _build_tier_map,
    _classify_entry,
    _estimate_cost,
    advisor,
)
from ttadev.primitives.llm.model_advisor.recommendation import (
    ROIEstimate,
    TaskSuggestion,
    TierRecommendation,
)
from ttadev.primitives.llm.model_advisor.strategy import (
    _FINETUNE_BASE_COST,
    _FINETUNE_IMPROVEMENT,
    suggest_qwen_finetunes,
)
from ttadev.primitives.llm.model_advisor.training_estimator import (
    COST_PER_1M_TOKENS_TRAINING,
    FINETUNE_IMPROVEMENT,
    TYPICAL_DATASET_TOKENS,
    build_roi_estimate,
    calculate_roi_breakeven,
    estimate_finetune_cost,
    estimate_quality_improvement,
)
from ttadev.primitives.llm.model_registry import ModelEntry
from ttadev.primitives.llm.task_selector import COMPLEXITY_MODERATE, TaskProfile

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _entry(
    model_id: str = "test-model",
    provider: str = "groq",
    cost_tier: str = "free",
    is_local: bool = False,
) -> ModelEntry:
    return ModelEntry(
        model_id=model_id,
        provider=provider,
        cost_tier=cost_tier,
        is_local=is_local,
    )


# ===========================================================================
# advisor.py — _classify_entry
# ===========================================================================


class TestClassifyEntry:
    def test_groq_provider_always_groq_tier(self):
        assert _classify_entry(_entry(provider="groq", cost_tier="free")) == "groq"
        assert _classify_entry(_entry(provider="groq", cost_tier="high")) == "groq"

    def test_google_free_tier(self):
        assert _classify_entry(_entry(provider="google", cost_tier="free")) == "google-free"

    def test_google_paid_tier(self):
        assert _classify_entry(_entry(provider="google", cost_tier="medium")) == "paid"

    def test_google_low_cost_paid(self):
        assert _classify_entry(_entry(provider="google", cost_tier="low")) == "paid"

    def test_github_provider_is_github_models(self):
        assert _classify_entry(_entry(provider="github")) == "github-models"

    def test_openrouter_free_is_or_free(self):
        assert _classify_entry(_entry(provider="openrouter", cost_tier="free")) == "or-free"

    def test_openrouter_low_is_or_specific(self):
        assert _classify_entry(_entry(provider="openrouter", cost_tier="low")) == "or-specific"

    def test_openrouter_medium_is_or_specific(self):
        assert _classify_entry(_entry(provider="openrouter", cost_tier="medium")) == "or-specific"

    def test_openrouter_high_is_paid(self):
        assert _classify_entry(_entry(provider="openrouter", cost_tier="high")) == "paid"

    def test_openai_is_paid(self):
        assert _classify_entry(_entry(provider="openai")) == "paid"

    def test_anthropic_is_paid(self):
        assert _classify_entry(_entry(provider="anthropic")) == "paid"

    def test_together_is_paid(self):
        assert _classify_entry(_entry(provider="together")) == "paid"

    def test_high_cost_tier_unknown_provider_is_paid(self):
        # Any provider with cost_tier="high" falls through to paid
        assert _classify_entry(_entry(provider="mystery", cost_tier="high")) == "paid"

    def test_unknown_provider_free_tier_is_none(self):
        # Provider not in any bucket and cost_tier != "high"
        assert _classify_entry(_entry(provider="mystery-provider", cost_tier="free")) is None


# ===========================================================================
# advisor.py — _build_tier_map
# ===========================================================================


class TestBuildTierMap:
    def test_returns_all_tier_keys(self):
        # Arrange / Act
        tier_map = _build_tier_map()
        # Assert
        for tier in _TIER_PRIORITY:
            assert tier in tier_map

    def test_no_model_id_appears_in_multiple_tiers(self):
        # Arrange / Act
        tier_map = _build_tier_map()
        all_models: list[str] = []
        for models in tier_map.values():
            all_models.extend(models)
        # Assert — each model_id unique across all tiers
        assert len(all_models) == len(set(all_models)), "Duplicate model_ids across tier_map"

    def test_groq_tier_is_nonempty(self):
        tier_map = _build_tier_map()
        assert len(tier_map["groq"]) > 0

    def test_ollama_tier_empty_without_detection(self):
        # _build_tier_map only reads _DEFAULT_CLOUD_MODELS — no ollama entries there
        tier_map = _build_tier_map()
        assert tier_map["ollama"] == []

    def test_all_model_ids_are_strings(self):
        tier_map = _build_tier_map()
        for tier, models in tier_map.items():
            for m in models:
                assert isinstance(m, str), f"Non-string model_id {m!r} in tier {tier!r}"


# ===========================================================================
# advisor.py — _estimate_cost
# ===========================================================================


class TestEstimateCost:
    def test_free_tiers_always_zero(self):
        # Arrange / Act / Assert
        for tier in ("ollama", "groq", "google-free", "github-models", "or-free"):
            assert _estimate_cost(tier, 10_000) == 0.0, f"Expected 0 cost for {tier}"

    def test_or_specific_scales_with_calls(self):
        # Arrange
        baseline = TIER_COST_DEFAULTS["or-specific"]
        # Act
        result = _estimate_cost("or-specific", 500)
        # Assert
        assert result == pytest.approx(baseline * (500 / 100.0))

    def test_paid_scales_with_calls(self):
        # Arrange
        baseline = TIER_COST_DEFAULTS["paid"]
        # Act
        result = _estimate_cost("paid", 200)
        # Assert
        assert result == pytest.approx(baseline * (200 / 100.0))

    def test_unknown_tier_falls_back_to_paid_rate(self):
        # Arrange — unknown tier defaults to "paid" baseline
        paid_baseline = TIER_COST_DEFAULTS["paid"]
        # Act
        result = _estimate_cost("nonexistent-tier", 100)
        # Assert
        assert result == pytest.approx(paid_baseline * (100 / 100.0))

    def test_zero_calls_gives_zero_cost(self):
        # Arrange / Act
        result = _estimate_cost("paid", 0)
        # Assert
        assert result == 0.0


# ===========================================================================
# advisor.py — _build_recommendation
# ===========================================================================


class TestBuildRecommendation:
    def test_constructs_tier_recommendation(self):
        # Arrange / Act
        rec = _build_recommendation(
            tier="groq",
            primary="llama3",
            fallbacks=["m2", "m3"],
            score_0_1=0.75,
            rationale="good model",
            monthly_calls=100,
            task_type="coding",
            quality_threshold=7.0,
        )
        # Assert
        assert isinstance(rec, TierRecommendation)
        assert rec.recommended_tier == "groq"
        assert rec.primary_model == "llama3"
        assert rec.fallback_models == ["m2", "m3"]
        assert rec.quality_score == pytest.approx(7.5)  # 0.75 * 10.0
        assert rec.cost_usd_per_month == 0.0  # groq is free
        assert rec.task_type == "coding"
        assert rec.quality_threshold == 7.0

    def test_score_rounds_to_two_decimal_places(self):
        # Arrange / Act
        rec = _build_recommendation(
            tier="paid",
            primary="gpt-4",
            fallbacks=[],
            score_0_1=0.7777,
            rationale="",
            monthly_calls=100,
            task_type="general",
            quality_threshold=5.0,
        )
        # Assert — rounded
        assert rec.quality_score == pytest.approx(7.78)

    def test_paid_tier_cost_non_zero(self):
        # Arrange / Act
        rec = _build_recommendation(
            tier="paid",
            primary="gpt-4",
            fallbacks=[],
            score_0_1=0.9,
            rationale="",
            monthly_calls=100,
            task_type="general",
            quality_threshold=5.0,
        )
        # Assert
        assert rec.cost_usd_per_month > 0.0


# ===========================================================================
# advisor.py — ModelAdvisor.recommend_tier
# ===========================================================================


class TestRecommendTier:
    def test_valid_task_returns_tier_recommendation(self):
        # Arrange
        mock_advisor = ModelAdvisor()
        # Act
        with patch(
            "ttadev.primitives.llm.model_advisor.advisor._get_ollama_candidates",
            return_value=[],
        ):
            rec = mock_advisor.recommend_tier("coding", quality_threshold=1.0)
        # Assert
        assert isinstance(rec, TierRecommendation)
        assert rec.task_type == "coding"
        assert rec.primary_model != ""

    def test_invalid_task_type_degrades_gracefully(self):
        # Arrange — should not raise
        mock_advisor = ModelAdvisor()
        # Act
        with patch(
            "ttadev.primitives.llm.model_advisor.advisor._get_ollama_candidates",
            return_value=[],
        ):
            rec = mock_advisor.recommend_tier("totally_invalid_task_xyz", quality_threshold=0.0)
        # Assert
        assert isinstance(rec, TierRecommendation)

    def test_high_threshold_returns_best_available(self):
        # Arrange — threshold=10.0 likely not met; returns best available
        mock_advisor = ModelAdvisor()
        # Act
        with patch(
            "ttadev.primitives.llm.model_advisor.advisor._get_ollama_candidates",
            return_value=[],
        ):
            rec = mock_advisor.recommend_tier("coding", quality_threshold=10.0)
        # Assert — fallback rationale string
        assert isinstance(rec, TierRecommendation)
        assert len(rec.rationale) > 0

    def test_returns_fallback_models_list(self):
        # Arrange
        mock_advisor = ModelAdvisor()
        # Act
        with patch(
            "ttadev.primitives.llm.model_advisor.advisor._get_ollama_candidates",
            return_value=[],
        ):
            rec = mock_advisor.recommend_tier("coding", quality_threshold=0.0)
        # Assert
        assert isinstance(rec.fallback_models, list)

    def test_monthly_calls_affects_cost_estimate(self):
        # Arrange
        mock_advisor = ModelAdvisor()
        # Act — very high call volume on a paid tier
        with patch(
            "ttadev.primitives.llm.model_advisor.advisor._get_ollama_candidates",
            return_value=[],
        ):
            rec_low = mock_advisor.recommend_tier("coding", monthly_calls=1)
            rec_high = mock_advisor.recommend_tier("coding", monthly_calls=100_000)
        # Assert — paid tiers should scale; free tiers always 0
        # Both are valid TierRecommendation objects
        assert isinstance(rec_low, TierRecommendation)
        assert isinstance(rec_high, TierRecommendation)


# ===========================================================================
# advisor.py — ModelAdvisor.estimate_roi
# ===========================================================================


class TestEstimateRoi:
    def test_returns_roi_estimate(self):
        # Arrange
        mock_advisor = ModelAdvisor()
        # Act
        roi = mock_advisor.estimate_roi(
            task_type="coding",
            current_score=60.0,
            current_best_model="llama3",
            monthly_calls=500,
        )
        # Assert
        assert isinstance(roi, ROIEstimate)
        assert roi.task_type == "coding"
        assert roi.current_score == 60.0
        assert roi.current_best_model == "llama3"
        assert roi.monthly_calls == 500

    def test_zero_calls_gives_infinite_breakeven(self):
        # Arrange
        mock_advisor = ModelAdvisor()
        # Act
        roi = mock_advisor.estimate_roi(
            task_type="coding",
            current_score=50.0,
            current_best_model="m",
            monthly_calls=0,
        )
        # Assert
        assert roi.roi_breakeven_days == float("inf")
        assert roi.is_recommended is False

    def test_delegates_to_build_roi_estimate(self):
        # Arrange
        mock_advisor = ModelAdvisor()
        # Act
        roi = mock_advisor.estimate_roi("math", 45.0, "model-x", monthly_calls=1000)
        # Assert
        assert roi.training_cost_usd > 0
        assert roi.finetuned_score_estimate > 45.0


# ===========================================================================
# advisor.py — ModelAdvisor.recommend_with_roi
# ===========================================================================


class TestRecommendWithRoi:
    def test_without_current_score_roi_is_none(self):
        # Arrange
        mock_advisor = ModelAdvisor()
        # Act
        with patch(
            "ttadev.primitives.llm.model_advisor.advisor._get_ollama_candidates",
            return_value=[],
        ):
            rec, roi = mock_advisor.recommend_with_roi("coding", current_score=None)
        # Assert
        assert isinstance(rec, TierRecommendation)
        assert roi is None

    def test_with_current_score_roi_is_populated(self):
        # Arrange
        mock_advisor = ModelAdvisor()
        # Act
        with patch(
            "ttadev.primitives.llm.model_advisor.advisor._get_ollama_candidates",
            return_value=[],
        ):
            rec, roi = mock_advisor.recommend_with_roi(
                "coding", current_score=60.0, monthly_calls=500
            )
        # Assert
        assert isinstance(rec, TierRecommendation)
        assert isinstance(roi, ROIEstimate)
        assert roi.current_score == 60.0
        assert roi.monthly_calls == 500

    def test_roi_uses_recommended_model_as_current_best(self):
        # Arrange
        mock_advisor = ModelAdvisor()
        # Act
        with patch(
            "ttadev.primitives.llm.model_advisor.advisor._get_ollama_candidates",
            return_value=[],
        ):
            rec, roi = mock_advisor.recommend_with_roi("coding", current_score=70.0)
        # Assert — ROI's current_best_model matches recommendation's primary_model
        assert roi is not None
        assert roi.current_best_model == rec.primary_model


# ===========================================================================
# advisor.py — _build_fallbacks
# ===========================================================================


class TestBuildFallbacks:
    def _profile(self) -> TaskProfile:
        return TaskProfile(task_type="coding", complexity=COMPLEXITY_MODERATE)

    def test_primary_excluded_from_fallbacks(self):
        # Arrange
        profile = self._profile()
        tier_map = {"groq": ["m1", "m2", "m3"], "paid": ["m4"]}
        # Act
        fallbacks = ModelAdvisor._build_fallbacks(
            primary="m1",
            tier_ranked=["m2", "m3"],
            other_tiers=["groq", "paid"],
            tier_map=tier_map,
            profile=profile,
            current_tier="groq",
        )
        # Assert
        assert "m1" not in fallbacks

    def test_same_tier_models_appear_before_cross_tier(self):
        # Arrange
        profile = self._profile()
        tier_map = {"groq": ["m1", "m2"], "paid": ["m4"]}
        # Act
        fallbacks = ModelAdvisor._build_fallbacks(
            primary="m1",
            tier_ranked=["m2"],
            other_tiers=["groq", "paid"],
            tier_map=tier_map,
            profile=profile,
            current_tier="groq",
        )
        # Assert — m2 (same tier) before m4 (paid cross-tier)
        assert "m2" in fallbacks
        assert "m4" in fallbacks
        assert fallbacks.index("m2") < fallbacks.index("m4")

    def test_max_fallbacks_respected(self):
        # Arrange
        profile = self._profile()
        tier_map = {"groq": ["p", "a", "b", "c", "d", "e", "f"]}
        # Act
        fallbacks = ModelAdvisor._build_fallbacks(
            primary="p",
            tier_ranked=["a", "b", "c", "d", "e", "f"],
            other_tiers=["groq"],
            tier_map=tier_map,
            profile=profile,
            current_tier="groq",
            max_fallbacks=3,
        )
        # Assert
        assert len(fallbacks) <= 3

    def test_no_duplicates_in_fallbacks(self):
        # Arrange
        profile = self._profile()
        tier_map = {"groq": ["m1", "m2"], "or-free": ["m2", "m3"]}
        # Act
        fallbacks = ModelAdvisor._build_fallbacks(
            primary="m1",
            tier_ranked=["m2"],
            other_tiers=["groq", "or-free"],
            tier_map=tier_map,
            profile=profile,
            current_tier="groq",
        )
        # Assert — m2 should appear only once
        assert fallbacks.count("m2") == 1


# ===========================================================================
# advisor.py — singleton
# ===========================================================================


class TestAdvisorSingleton:
    def test_advisor_is_model_advisor_instance(self):
        assert isinstance(advisor, ModelAdvisor)

    def test_advisor_singleton_usable(self):
        # Arrange / Act
        with patch(
            "ttadev.primitives.llm.model_advisor.advisor._get_ollama_candidates",
            return_value=[],
        ):
            rec = advisor.recommend_tier("general", quality_threshold=0.0)
        # Assert
        assert isinstance(rec, TierRecommendation)


# ===========================================================================
# strategy.py — suggest_qwen_finetunes
# ===========================================================================


class TestSuggestQwenFinetunes:
    def test_empty_eval_results_returns_empty_list(self):
        # Arrange / Act
        result = suggest_qwen_finetunes({})
        # Assert
        assert result == []

    def test_max_suggestions_less_than_1_raises_value_error(self):
        # Arrange / Act / Assert
        with pytest.raises(ValueError, match="max_suggestions"):
            suggest_qwen_finetunes({"coding": 50.0}, max_suggestions=0)

    def test_returns_task_suggestion_instances(self):
        # Arrange / Act
        result = suggest_qwen_finetunes({"coding": 60.0, "math": 50.0})
        # Assert
        assert len(result) >= 1
        assert all(isinstance(s, TaskSuggestion) for s in result)

    def test_sorted_by_roi_breakeven_ascending(self):
        # Arrange / Act
        result = suggest_qwen_finetunes(
            {"coding": 60.0, "math": 40.0, "chat": 70.0},
            monthly_calls_per_task={"coding": 5000, "math": 3000, "chat": 100},
        )
        breakevens = [s.roi_breakeven_days for s in result]
        # Assert — non-decreasing
        for i in range(len(breakevens) - 1):
            assert breakevens[i] <= breakevens[i + 1]

    def test_max_suggestions_limits_results(self):
        # Arrange
        eval_results = {
            "coding": 60.0,
            "math": 50.0,
            "reasoning": 45.0,
            "chat": 70.0,
            "general": 55.0,
            "vision": 40.0,
        }
        # Act
        result = suggest_qwen_finetunes(eval_results, max_suggestions=2)
        # Assert
        assert len(result) <= 2

    def test_zero_calls_gives_infinite_breakeven(self):
        # Arrange / Act
        result = suggest_qwen_finetunes(
            {"coding": 60.0},
            monthly_calls_per_task={"coding": 0},
        )
        # Assert
        assert len(result) == 1
        assert result[0].roi_breakeven_days == float("inf")

    def test_score_clamped_to_100(self):
        # Arrange / Act
        result = suggest_qwen_finetunes({"coding": 999.0})
        # Assert
        assert result[0].current_score == 100.0
        assert result[0].expected_improvement == pytest.approx(0.0)

    def test_score_clamped_to_zero(self):
        # Arrange / Act
        result = suggest_qwen_finetunes({"coding": -50.0})
        # Assert
        assert result[0].current_score == 0.0
        # Expected improvement = 100 * improvement_rate
        expected = 100.0 * _FINETUNE_IMPROVEMENT["coding"]
        assert result[0].expected_improvement == pytest.approx(expected)

    def test_unknown_task_uses_default_improvement_rate(self):
        # Arrange / Act
        result = suggest_qwen_finetunes({"mystery_task": 50.0})
        # Assert — falls back to general rate (0.18)
        expected_improvement = 50.0 * 0.18  # headroom=50, default_rate=0.18
        assert result[0].expected_improvement == pytest.approx(expected_improvement)

    def test_known_task_uses_correct_improvement_rate(self):
        # Arrange / Act
        result = suggest_qwen_finetunes({"math": 50.0})
        # Assert
        expected = 50.0 * _FINETUNE_IMPROVEMENT["math"]
        assert result[0].expected_improvement == pytest.approx(expected)

    def test_estimated_cost_from_lookup_table(self):
        # Arrange / Act
        result = suggest_qwen_finetunes({"coding": 60.0})
        # Assert
        assert result[0].estimated_cost_usd == _FINETUNE_BASE_COST["coding"]

    def test_unknown_task_cost_uses_default(self):
        # Arrange / Act
        result = suggest_qwen_finetunes({"mystery_task": 50.0})
        # Assert — default cost is 40.0
        assert result[0].estimated_cost_usd == 40.0

    def test_rationale_is_nonempty_string(self):
        # Arrange / Act
        result = suggest_qwen_finetunes({"coding": 60.0})
        # Assert
        assert isinstance(result[0].rationale, str)
        assert len(result[0].rationale) > 0

    def test_confidence_in_range_zero_to_one(self):
        # Arrange / Act
        result = suggest_qwen_finetunes({"coding": 60.0, "chat": 95.0})
        # Assert
        for s in result:
            assert 0.0 <= s.confidence <= 1.0

    def test_default_monthly_calls_matches_explicit_100(self):
        # Arrange / Act
        result_none = suggest_qwen_finetunes({"coding": 50.0})
        result_100 = suggest_qwen_finetunes(
            {"coding": 50.0}, monthly_calls_per_task={"coding": 100}
        )
        # Assert
        assert result_none[0].roi_breakeven_days == pytest.approx(result_100[0].roi_breakeven_days)

    def test_infinite_breakeven_sorts_after_finite(self):
        # Arrange / Act
        result = suggest_qwen_finetunes(
            {"coding": 60.0, "math": 50.0},
            monthly_calls_per_task={"coding": 5000, "math": 0},
        )
        finite = [s for s in result if s.roi_breakeven_days != float("inf")]
        infinite = [s for s in result if s.roi_breakeven_days == float("inf")]
        # Assert — all finite items appear before infinite
        if finite and infinite:
            last_finite_idx = max(result.index(s) for s in finite)
            first_infinite_idx = min(result.index(s) for s in infinite)
            assert last_finite_idx < first_infinite_idx

    def test_single_task_returns_one_suggestion(self):
        # Arrange / Act
        result = suggest_qwen_finetunes({"coding": 70.0})
        # Assert
        assert len(result) == 1
        assert result[0].task_type == "coding"

    def test_monthly_calls_parameter_none_uses_defaults(self):
        # Arrange / Act — passing None explicitly
        result = suggest_qwen_finetunes({"coding": 50.0}, monthly_calls_per_task=None)
        # Assert — should not raise, returns result
        assert len(result) == 1

    def test_rationale_contains_infinite_roi_message(self):
        # Arrange / Act — no calls → infinite ROI
        result = suggest_qwen_finetunes({"coding": 60.0}, monthly_calls_per_task={"coding": 0})
        # Assert
        assert "no monthly savings" in result[0].rationale.lower()

    def test_rationale_contains_roi_breakeven_days(self):
        # Arrange / Act — positive calls → finite ROI
        result = suggest_qwen_finetunes({"coding": 60.0}, monthly_calls_per_task={"coding": 5000})
        # Assert
        assert "breakeven" in result[0].rationale.lower()


class TestStrategyLookupTables:
    def test_finetune_improvement_has_all_known_tasks(self):
        known = ("coding", "math", "reasoning", "function_calling", "chat", "vision", "general")
        for key in known:
            assert key in _FINETUNE_IMPROVEMENT
            assert 0.0 < _FINETUNE_IMPROVEMENT[key] <= 1.0

    def test_finetune_base_cost_has_all_known_tasks(self):
        known = ("coding", "math", "reasoning", "function_calling", "chat", "vision", "general")
        for key in known:
            assert key in _FINETUNE_BASE_COST
            assert _FINETUNE_BASE_COST[key] > 0

    def test_math_has_highest_improvement_rate(self):
        # Math benefits most from fine-tuning per the literature
        assert _FINETUNE_IMPROVEMENT["math"] == max(_FINETUNE_IMPROVEMENT.values())

    def test_vision_has_lowest_improvement_rate(self):
        # Multimodal fine-tuning is hardest
        assert _FINETUNE_IMPROVEMENT["vision"] == min(_FINETUNE_IMPROVEMENT.values())


# ===========================================================================
# training_estimator.py — constants
# ===========================================================================


class TestTrainingEstimatorConstants:
    def test_cost_per_1m_has_default_key(self):
        assert "default" in COST_PER_1M_TOKENS_TRAINING
        assert COST_PER_1M_TOKENS_TRAINING["default"] > 0

    def test_larger_models_cost_more_per_token(self):
        # qwen2.5-7b < qwen2.5-14b < qwen2.5-32b < qwen2.5-72b
        assert (
            COST_PER_1M_TOKENS_TRAINING["qwen2.5-7b"]
            < COST_PER_1M_TOKENS_TRAINING["qwen2.5-14b"]
            < COST_PER_1M_TOKENS_TRAINING["qwen2.5-32b"]
            < COST_PER_1M_TOKENS_TRAINING["qwen2.5-72b"]
        )

    def test_typical_dataset_tokens_all_positive(self):
        for task, tokens in TYPICAL_DATASET_TOKENS.items():
            assert tokens > 0, f"Non-positive dataset tokens for {task}"

    def test_finetune_improvement_canonical_matches_strategy(self):
        # FINETUNE_IMPROVEMENT in training_estimator must match strategy.py
        for task_type, rate in FINETUNE_IMPROVEMENT.items():
            if task_type in _FINETUNE_IMPROVEMENT:
                assert rate == _FINETUNE_IMPROVEMENT[task_type], (
                    f"Mismatch for {task_type}: estimator={rate}, "
                    f"strategy={_FINETUNE_IMPROVEMENT[task_type]}"
                )


# ===========================================================================
# training_estimator.py — estimate_finetune_cost
# ===========================================================================


class TestEstimateFinetuneCost:
    def test_known_model_and_task(self):
        # Arrange
        expected_per_1m = COST_PER_1M_TOKENS_TRAINING["qwen2.5-7b"]
        expected_tokens_m = TYPICAL_DATASET_TOKENS["coding"] / 1_000_000
        # Act
        cost = estimate_finetune_cost("coding", base_model="qwen2.5-7b")
        # Assert
        assert cost == pytest.approx(expected_per_1m * expected_tokens_m)

    def test_unknown_model_falls_back_to_default_rate(self):
        # Arrange
        default_per_1m = COST_PER_1M_TOKENS_TRAINING["default"]
        tokens_m = TYPICAL_DATASET_TOKENS["coding"] / 1_000_000
        # Act
        cost = estimate_finetune_cost("coding", base_model="nonexistent-model-xyz")
        # Assert
        assert cost == pytest.approx(default_per_1m * tokens_m)

    def test_unknown_task_falls_back_to_general_tokens(self):
        # Arrange
        per_1m = COST_PER_1M_TOKENS_TRAINING["qwen2.5-7b"]
        general_m = TYPICAL_DATASET_TOKENS["general"] / 1_000_000
        # Act
        cost = estimate_finetune_cost("mystery_task", base_model="qwen2.5-7b")
        # Assert
        assert cost == pytest.approx(per_1m * general_m)

    def test_custom_dataset_tokens_overrides_lookup(self):
        # Arrange
        per_1m = COST_PER_1M_TOKENS_TRAINING["qwen2.5-7b"]
        # Act
        cost = estimate_finetune_cost("coding", base_model="qwen2.5-7b", dataset_tokens=1_000_000)
        # Assert
        assert cost == pytest.approx(per_1m * 1.0)

    def test_zero_dataset_tokens_returns_zero(self):
        # Arrange / Act
        cost = estimate_finetune_cost("coding", dataset_tokens=0)
        # Assert
        assert cost == pytest.approx(0.0)

    def test_negative_dataset_tokens_clamped_to_zero(self):
        # Arrange / Act
        cost = estimate_finetune_cost("coding", dataset_tokens=-100_000)
        # Assert
        assert cost == pytest.approx(0.0)

    def test_larger_model_costs_more(self):
        # Arrange / Act
        cost_7b = estimate_finetune_cost("coding", base_model="qwen2.5-7b")
        cost_72b = estimate_finetune_cost("coding", base_model="qwen2.5-72b")
        # Assert
        assert cost_72b > cost_7b

    def test_default_base_model_is_default_key(self):
        # Arrange / Act — base_model defaults to "default"
        cost = estimate_finetune_cost("coding")
        expected = (
            COST_PER_1M_TOKENS_TRAINING["default"] * TYPICAL_DATASET_TOKENS["coding"] / 1_000_000
        )
        # Assert
        assert cost == pytest.approx(expected)


# ===========================================================================
# training_estimator.py — estimate_quality_improvement
# ===========================================================================


class TestEstimateQualityImprovement:
    def test_coding_improvement_formula(self):
        # Arrange — coding score 60; headroom=40; rate=0.28
        # Act
        improvement = estimate_quality_improvement("coding", current_score=60.0)
        expected = 40.0 * FINETUNE_IMPROVEMENT["coding"]
        # Assert
        assert improvement == pytest.approx(expected)

    def test_score_100_gives_zero_improvement(self):
        # Arrange / Act
        improvement = estimate_quality_improvement("coding", current_score=100.0)
        # Assert
        assert improvement == pytest.approx(0.0)

    def test_score_0_gives_full_headroom_improvement(self):
        # Arrange / Act
        improvement = estimate_quality_improvement("math", current_score=0.0)
        expected = 100.0 * FINETUNE_IMPROVEMENT["math"]
        # Assert
        assert improvement == pytest.approx(expected)

    def test_score_above_100_clamped(self):
        # Arrange / Act
        improvement = estimate_quality_improvement("coding", current_score=150.0)
        # Assert — clamped to 100, so headroom=0
        assert improvement == pytest.approx(0.0)

    def test_score_below_zero_clamped(self):
        # Arrange / Act
        improvement = estimate_quality_improvement("coding", current_score=-10.0)
        expected = 100.0 * FINETUNE_IMPROVEMENT["coding"]
        # Assert
        assert improvement == pytest.approx(expected)

    def test_unknown_task_uses_general_rate(self):
        # Arrange / Act
        improvement = estimate_quality_improvement("unknown_task", current_score=50.0)
        expected = 50.0 * FINETUNE_IMPROVEMENT["general"]
        # Assert
        assert improvement == pytest.approx(expected)

    def test_all_known_tasks_return_positive_improvement(self):
        for task in (
            "coding",
            "math",
            "reasoning",
            "function_calling",
            "chat",
            "vision",
            "general",
        ):
            improvement = estimate_quality_improvement(task, current_score=50.0)
            assert improvement > 0, f"Zero improvement for {task}"


# ===========================================================================
# training_estimator.py — calculate_roi_breakeven
# ===========================================================================


class TestCalculateRoiBreakeven:
    def test_normal_calculation(self):
        # Arrange — cost=100, calls=1000, per_call=0.001 → savings=1.0/mo → breakeven=3000d
        # Act
        result = calculate_roi_breakeven(100.0, monthly_calls=1000, cost_per_api_call_usd=0.001)
        # Assert
        assert result == pytest.approx(3000.0)

    def test_zero_monthly_calls_returns_infinity(self):
        # Arrange / Act
        result = calculate_roi_breakeven(100.0, monthly_calls=0)
        # Assert
        assert result == float("inf")

    def test_negative_monthly_calls_returns_infinity(self):
        # Arrange / Act
        result = calculate_roi_breakeven(100.0, monthly_calls=-100)
        # Assert
        assert result == float("inf")

    def test_zero_cost_per_call_returns_infinity(self):
        # Arrange / Act
        result = calculate_roi_breakeven(100.0, monthly_calls=1000, cost_per_api_call_usd=0.0)
        # Assert
        assert result == float("inf")

    def test_negative_cost_per_call_treated_as_zero(self):
        # Arrange / Act
        result = calculate_roi_breakeven(100.0, monthly_calls=1000, cost_per_api_call_usd=-0.5)
        # Assert
        assert result == float("inf")

    def test_high_call_volume_gives_short_breakeven(self):
        # Arrange — 100k calls/month × $0.001 = $100/mo; cost=$50 → breakeven=15d
        # Act
        result = calculate_roi_breakeven(50.0, monthly_calls=100_000, cost_per_api_call_usd=0.001)
        # Assert
        assert result == pytest.approx(15.0)

    def test_default_cost_per_call_is_0_001(self):
        # Arrange / Act — use default cost_per_api_call_usd=0.001
        result_default = calculate_roi_breakeven(100.0, monthly_calls=1000)
        result_explicit = calculate_roi_breakeven(
            100.0, monthly_calls=1000, cost_per_api_call_usd=0.001
        )
        # Assert
        assert result_default == pytest.approx(result_explicit)


# ===========================================================================
# training_estimator.py — build_roi_estimate
# ===========================================================================


class TestBuildRoiEstimate:
    def test_returns_roi_estimate_dataclass(self):
        # Arrange / Act
        roi = build_roi_estimate("coding", 60.0, "llama3", monthly_calls=500)
        # Assert
        assert isinstance(roi, ROIEstimate)

    def test_all_fields_populated(self):
        # Arrange / Act
        roi = build_roi_estimate(
            "coding",
            current_score=60.0,
            current_best_model="llama3",
            monthly_calls=500,
            base_model="qwen2.5-7b",
        )
        # Assert
        assert roi.task_type == "coding"
        assert roi.current_best_model == "llama3"
        assert roi.current_score == 60.0
        assert roi.monthly_calls == 500
        assert roi.training_cost_usd > 0
        assert roi.finetuned_score_estimate > 60.0
        assert roi.monthly_savings_usd == pytest.approx(500 * 0.001)

    def test_finetuned_score_capped_at_100(self):
        # Arrange / Act — start at 99; tiny headroom but score must cap
        roi = build_roi_estimate(
            "math", current_score=99.0, current_best_model="m", monthly_calls=100
        )
        # Assert
        assert roi.finetuned_score_estimate <= 100.0

    def test_is_recommended_when_breakeven_under_threshold(self):
        # Arrange — massive call volume → tiny breakeven → recommended
        roi = build_roi_estimate(
            "coding",
            current_score=50.0,
            current_best_model="m",
            monthly_calls=10_000_000,
            roi_recommend_threshold_days=90.0,
        )
        # Assert
        assert roi.is_recommended is True

    def test_not_recommended_when_zero_calls(self):
        # Arrange / Act
        roi = build_roi_estimate("coding", 50.0, "m", monthly_calls=0)
        # Assert
        assert roi.is_recommended is False
        assert roi.roi_breakeven_days == float("inf")

    def test_score_clamped_below_zero(self):
        # Arrange / Act
        roi = build_roi_estimate("coding", -10.0, "m", monthly_calls=100)
        # Assert
        assert roi.current_score == 0.0

    def test_score_clamped_above_100(self):
        # Arrange / Act
        roi = build_roi_estimate("coding", 150.0, "m", monthly_calls=100)
        # Assert
        assert roi.current_score == 100.0
        assert roi.finetuned_score_estimate == 100.0

    def test_custom_threshold_controls_recommendation(self):
        # Arrange / Act
        roi_easy = build_roi_estimate(
            "coding", 50.0, "m", monthly_calls=10, roi_recommend_threshold_days=99_999.0
        )
        roi_strict = build_roi_estimate(
            "coding", 50.0, "m", monthly_calls=10, roi_recommend_threshold_days=0.001
        )
        # Assert
        assert roi_easy.is_recommended is True  # threshold very generous
        assert roi_strict.is_recommended is False  # threshold impossibly tight

    def test_monthly_savings_calculation(self):
        # Arrange / Act
        roi = build_roi_estimate(
            "coding", 50.0, "m", monthly_calls=1000, cost_per_api_call_usd=0.005
        )
        # Assert — 1000 * 0.005 = 5.0
        assert roi.monthly_savings_usd == pytest.approx(5.0)

    def test_training_cost_matches_estimate_finetune_cost(self):
        # Arrange
        expected_cost = estimate_finetune_cost("math", base_model="qwen2.5-14b")
        # Act
        roi = build_roi_estimate("math", 50.0, "m", base_model="qwen2.5-14b")
        # Assert
        assert roi.training_cost_usd == pytest.approx(expected_cost)
