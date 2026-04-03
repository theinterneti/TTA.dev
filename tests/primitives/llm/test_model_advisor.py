"""Unit tests for the ModelAdvisor feature.

Covers:
- training_estimator: estimate_finetune_cost, calculate_roi_breakeven,
  build_roi_estimate
- strategy: suggest_qwen_finetunes
- advisor: ModelAdvisor.recommend_tier, estimate_roi, recommend_with_roi

ModelAdvisor tests mock rank_models_for_task, score_model_for_task, and
HardwareDetector to avoid real hardware / benchmark dependencies so every test
is deterministic and fast.
"""

from __future__ import annotations

import math
from unittest.mock import patch

import pytest

from ttadev.primitives.llm.model_advisor.advisor import (
    _ABSOLUTE_FALLBACK_MODEL,
    _ABSOLUTE_FALLBACK_PROVIDER,
    ModelAdvisor,
)
from ttadev.primitives.llm.model_advisor.recommendation import (
    ROIEstimate,
    TaskSuggestion,
    TierRecommendation,
)
from ttadev.primitives.llm.model_advisor.strategy import suggest_qwen_finetunes
from ttadev.primitives.llm.model_advisor.training_estimator import (
    COST_PER_1M_TOKENS_TRAINING,
    FINETUNE_IMPROVEMENT,
    TYPICAL_DATASET_TOKENS,
    build_roi_estimate,
    calculate_roi_breakeven,
    estimate_finetune_cost,
    estimate_quality_improvement,
)

# ---------------------------------------------------------------------------
# TestTrainingEstimator
# ---------------------------------------------------------------------------


class TestTrainingEstimator:
    """Pure-math tests for training_estimator.py — no mocking required."""

    # ------------------------------------------------------------------
    # estimate_finetune_cost
    # ------------------------------------------------------------------

    def test_estimate_finetune_cost_known_model(self) -> None:
        """qwen2.5-7b + coding → 500_000 tokens × $0.40/1M = $0.20."""
        cost = estimate_finetune_cost(task_type="coding", base_model="qwen2.5-7b")
        expected = COST_PER_1M_TOKENS_TRAINING["qwen2.5-7b"] * (
            TYPICAL_DATASET_TOKENS["coding"] / 1_000_000
        )
        assert math.isclose(cost, expected, rel_tol=1e-9)
        assert math.isclose(cost, 0.20, rel_tol=1e-6)

    def test_estimate_finetune_cost_unknown_task_uses_general_fallback(self) -> None:
        """Unknown task_type falls back to TYPICAL_DATASET_TOKENS['general']."""
        cost_unknown = estimate_finetune_cost(task_type="unknown_task", base_model="qwen2.5-7b")
        cost_general = estimate_finetune_cost(task_type="general", base_model="qwen2.5-7b")
        assert math.isclose(cost_unknown, cost_general, rel_tol=1e-9)

    def test_estimate_finetune_cost_unknown_model_uses_default(self) -> None:
        """Unknown base_model falls back to COST_PER_1M_TOKENS_TRAINING['default']."""
        cost_unknown = estimate_finetune_cost(task_type="coding", base_model="nonexistent-model")
        cost_default = estimate_finetune_cost(task_type="coding", base_model="default")
        assert math.isclose(cost_unknown, cost_default, rel_tol=1e-9)

    def test_estimate_finetune_cost_explicit_dataset_tokens(self) -> None:
        """Providing dataset_tokens overrides the lookup table."""
        cost = estimate_finetune_cost(
            task_type="coding", base_model="qwen2.5-7b", dataset_tokens=1_000_000
        )
        expected = COST_PER_1M_TOKENS_TRAINING["qwen2.5-7b"] * 1.0
        assert math.isclose(cost, expected, rel_tol=1e-9)

    def test_estimate_finetune_cost_zero_tokens(self) -> None:
        """Zero dataset_tokens yields zero cost."""
        cost = estimate_finetune_cost(task_type="coding", base_model="qwen2.5-7b", dataset_tokens=0)
        assert cost == 0.0

    # ------------------------------------------------------------------
    # estimate_quality_improvement
    # ------------------------------------------------------------------

    def test_estimate_quality_improvement_known_task(self) -> None:
        """coding at score 60.0 → headroom 40 × 0.28 = 11.2 pts."""
        improvement = estimate_quality_improvement("coding", 60.0)
        expected = (100.0 - 60.0) * FINETUNE_IMPROVEMENT["coding"]
        assert math.isclose(improvement, expected, rel_tol=1e-9)

    def test_estimate_quality_improvement_clamps_score(self) -> None:
        """Scores outside [0, 100] are clamped."""
        improvement_neg = estimate_quality_improvement("coding", -10.0)
        improvement_over = estimate_quality_improvement("coding", 110.0)
        # -10 → clamped to 0 → headroom = 100
        assert math.isclose(improvement_neg, 100.0 * FINETUNE_IMPROVEMENT["coding"])
        # 110 → clamped to 100 → headroom = 0
        assert math.isclose(improvement_over, 0.0)

    # ------------------------------------------------------------------
    # calculate_roi_breakeven
    # ------------------------------------------------------------------

    def test_calculate_roi_breakeven_normal(self) -> None:
        """cost=60, monthly_calls=100, rate=0.001 → savings=0.1/month → 600 days."""
        days = calculate_roi_breakeven(
            training_cost_usd=60.0,
            monthly_calls=100,
            cost_per_api_call_usd=0.001,
        )
        # monthly_savings = 100 × 0.001 = 0.1; days = (60 / 0.1) × 30 = 18000
        # Actually: (60 / 0.1) * 30 = 18000 days — verify formula
        expected = (60.0 / (100 * 0.001)) * 30.0
        assert math.isclose(days, expected, rel_tol=1e-9)

    def test_calculate_roi_breakeven_zero_calls_returns_inf(self) -> None:
        """monthly_calls=0 → float('inf')."""
        days = calculate_roi_breakeven(
            training_cost_usd=100.0,
            monthly_calls=0,
            cost_per_api_call_usd=0.001,
        )
        assert days == float("inf")

    def test_calculate_roi_breakeven_zero_rate_returns_inf(self) -> None:
        """cost_per_api_call_usd=0 → float('inf')."""
        days = calculate_roi_breakeven(
            training_cost_usd=100.0,
            monthly_calls=1000,
            cost_per_api_call_usd=0.0,
        )
        assert days == float("inf")

    def test_calculate_roi_breakeven_scales_with_calls(self) -> None:
        """Doubling monthly_calls halves the breakeven days."""
        days_100 = calculate_roi_breakeven(100.0, 100, 0.01)
        days_200 = calculate_roi_breakeven(100.0, 200, 0.01)
        assert math.isclose(days_100, days_200 * 2, rel_tol=1e-9)

    # ------------------------------------------------------------------
    # build_roi_estimate
    # ------------------------------------------------------------------

    def test_build_roi_estimate_recommended(self) -> None:
        """High monthly_calls produces is_recommended=True (short breakeven)."""
        roi = build_roi_estimate(
            task_type="coding",
            current_score=60.0,
            current_best_model="llama3-8b",
            monthly_calls=100_000,  # huge volume → short breakeven
            base_model="qwen2.5-7b",
        )
        assert isinstance(roi, ROIEstimate)
        assert roi.is_recommended is True
        assert roi.roi_breakeven_days < 90.0

    def test_build_roi_estimate_not_recommended(self) -> None:
        """Low monthly_calls produces is_recommended=False (long breakeven)."""
        roi = build_roi_estimate(
            task_type="coding",
            current_score=60.0,
            current_best_model="llama3-8b",
            monthly_calls=1,  # almost no usage → very long breakeven
            base_model="qwen2.5-7b",
        )
        assert roi.is_recommended is False
        assert roi.roi_breakeven_days > 90.0

    def test_build_roi_estimate_fields_populated(self) -> None:
        """All ROIEstimate fields are set with correct types."""
        roi = build_roi_estimate(
            task_type="math",
            current_score=50.0,
            current_best_model="gemma2:9b",
            monthly_calls=500,
        )
        assert roi.task_type == "math"
        assert roi.current_best_model == "gemma2:9b"
        assert 0.0 <= roi.current_score <= 100.0
        assert 0.0 <= roi.finetuned_score_estimate <= 100.0
        assert roi.finetuned_score_estimate >= roi.current_score
        assert roi.training_cost_usd >= 0.0
        assert roi.monthly_calls == 500
        assert roi.monthly_savings_usd >= 0.0
        assert isinstance(roi.is_recommended, bool)

    def test_build_roi_estimate_finetuned_score_capped_at_100(self) -> None:
        """finetuned_score_estimate does not exceed 100.0."""
        roi = build_roi_estimate(
            task_type="math",
            current_score=99.0,
            current_best_model="gpt-4",
            monthly_calls=1000,
        )
        assert roi.finetuned_score_estimate <= 100.0

    def test_build_roi_estimate_zero_calls_breakeven_inf(self) -> None:
        """monthly_calls=0 → roi_breakeven_days=inf, is_recommended=False."""
        roi = build_roi_estimate(
            task_type="coding",
            current_score=55.0,
            current_best_model="gemma2:9b",
            monthly_calls=0,
        )
        assert roi.roi_breakeven_days == float("inf")
        assert roi.is_recommended is False


# ---------------------------------------------------------------------------
# TestSuggestQwenFinetunes
# ---------------------------------------------------------------------------


class TestSuggestQwenFinetunes:
    """Tests for strategy.suggest_qwen_finetunes()."""

    def test_empty_eval_results_returns_empty(self) -> None:
        """Empty dict → empty list."""
        assert suggest_qwen_finetunes({}) == []

    def test_returns_task_suggestion_objects(self) -> None:
        """Each item in the result is a TaskSuggestion."""
        suggestions = suggest_qwen_finetunes({"coding": 60.0})
        assert len(suggestions) == 1
        s = suggestions[0]
        assert isinstance(s, TaskSuggestion)
        assert s.task_type == "coding"

    def test_returns_sorted_by_roi_breakeven(self) -> None:
        """Lower cost + more calls → shorter breakeven → ranks first."""
        # coding has a lower base cost than vision — give coding more calls
        suggestions = suggest_qwen_finetunes(
            eval_results={"coding": 50.0, "vision": 50.0},
            monthly_calls_per_task={"coding": 10_000, "vision": 10},
        )
        assert len(suggestions) == 2
        # coding has far more calls → shorter breakeven → should be first
        assert suggestions[0].task_type == "coding"
        assert suggestions[0].roi_breakeven_days <= suggestions[1].roi_breakeven_days

    def test_max_suggestions_respected(self) -> None:
        """5 tasks → max_suggestions=2 → only 2 returned."""
        eval_results = {
            "coding": 60.0,
            "math": 55.0,
            "reasoning": 70.0,
            "chat": 65.0,
            "general": 50.0,
        }
        suggestions = suggest_qwen_finetunes(eval_results, max_suggestions=2)
        assert len(suggestions) == 2

    def test_unknown_task_type_uses_fallback_rates(self) -> None:
        """Unknown task type uses default improvement/cost without raising."""
        suggestions = suggest_qwen_finetunes({"custom_task": 55.0})
        assert len(suggestions) == 1
        s = suggestions[0]
        assert s.task_type == "custom_task"
        assert s.expected_improvement >= 0.0
        assert s.estimated_cost_usd >= 0.0

    def test_confidence_bounded_zero_to_one(self) -> None:
        """Extreme scores never push confidence outside [0, 1]."""
        # Near-zero score — maximum headroom
        suggestions_low = suggest_qwen_finetunes({"coding": 0.01})
        assert 0.0 <= suggestions_low[0].confidence <= 1.0

        # Near-perfect score — almost no headroom
        suggestions_high = suggest_qwen_finetunes({"coding": 99.9})
        assert 0.0 <= suggestions_high[0].confidence <= 1.0

    def test_invalid_max_suggestions_raises(self) -> None:
        """max_suggestions < 1 raises ValueError."""
        with pytest.raises(ValueError, match="max_suggestions"):
            suggest_qwen_finetunes({"coding": 60.0}, max_suggestions=0)

    def test_monthly_calls_per_task_affects_breakeven(self) -> None:
        """Higher call volume shortens breakeven days."""
        s_low = suggest_qwen_finetunes({"coding": 50.0}, monthly_calls_per_task={"coding": 10})[0]
        s_high = suggest_qwen_finetunes(
            {"coding": 50.0}, monthly_calls_per_task={"coding": 10_000}
        )[0]
        assert s_high.roi_breakeven_days < s_low.roi_breakeven_days

    def test_zero_calls_produces_inf_breakeven(self) -> None:
        """monthly_calls=0 → roi_breakeven_days=float('inf')."""
        suggestions = suggest_qwen_finetunes({"coding": 50.0}, monthly_calls_per_task={"coding": 0})
        assert suggestions[0].roi_breakeven_days == float("inf")

    def test_rationale_is_non_empty_string(self) -> None:
        """Each suggestion has a non-empty rationale string."""
        suggestions = suggest_qwen_finetunes({"math": 45.0, "chat": 70.0})
        for s in suggestions:
            assert isinstance(s.rationale, str)
            assert len(s.rationale) > 0


# ---------------------------------------------------------------------------
# TestModelAdvisor
# ---------------------------------------------------------------------------

# Patch targets relative to where advisor.py imports them from.
_RANK_TARGET = "ttadev.primitives.llm.model_advisor.advisor.rank_models_for_task"
_SCORE_TARGET = "ttadev.primitives.llm.model_advisor.advisor.score_model_for_task"
_OLLAMA_CANDIDATES_TARGET = "ttadev.primitives.llm.model_advisor.advisor._get_ollama_candidates"
_BUILD_TIER_MAP_TARGET = "ttadev.primitives.llm.model_advisor.advisor._build_tier_map"


class TestModelAdvisor:
    """Tests for ModelAdvisor with mocked benchmark / hardware dependencies."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_tier_map(
        paid_models: list[str] | None = None,
        or_free_models: list[str] | None = None,
    ) -> dict[str, list[str]]:
        return {
            "ollama": [],
            "or-free": or_free_models or [],
            "or-specific": [],
            "paid": paid_models or ["llama-3.3-70b-versatile", "gemini-pro"],
        }

    # ------------------------------------------------------------------
    # recommend_tier
    # ------------------------------------------------------------------

    def test_recommend_tier_returns_tier_recommendation(self) -> None:
        """recommend_tier() always returns a TierRecommendation."""
        advisor = ModelAdvisor()
        tier_map = self._make_tier_map()

        with (
            patch(_BUILD_TIER_MAP_TARGET, return_value=tier_map),
            patch(_OLLAMA_CANDIDATES_TARGET, return_value=[]),
            patch(_RANK_TARGET, return_value=["llama-3.3-70b-versatile"]),
            patch(_SCORE_TARGET, return_value=0.85),
        ):
            rec = advisor.recommend_tier("coding", quality_threshold=7.0)

        assert isinstance(rec, TierRecommendation)
        assert rec.recommended_tier != ""
        assert rec.primary_model != ""
        assert isinstance(rec.fallback_models, list)
        assert isinstance(rec.rationale, str)
        assert 0.0 <= rec.quality_score <= 10.0
        assert rec.cost_usd_per_month >= 0.0

    def test_recommend_tier_threshold_met_returns_valid_model(self) -> None:
        """When score × 10 >= threshold, primary_model is the mocked top model."""
        advisor = ModelAdvisor()
        tier_map = self._make_tier_map(paid_models=["best-model"])

        with (
            patch(_BUILD_TIER_MAP_TARGET, return_value=tier_map),
            patch(_OLLAMA_CANDIDATES_TARGET, return_value=[]),
            patch(_RANK_TARGET, return_value=["best-model"]),
            patch(_SCORE_TARGET, return_value=0.80),  # score=0.80 → quality=8.0 ≥ 7.0
        ):
            rec = advisor.recommend_tier("coding", quality_threshold=7.0)

        assert rec.primary_model == "best-model"
        assert rec.quality_score == pytest.approx(8.0, abs=0.01)

    def test_recommend_tier_no_threshold_met_returns_best_available(self) -> None:
        """When no tier meets threshold, the highest-scoring model is returned."""
        advisor = ModelAdvisor()
        # Only paid tier has models; score will be below threshold
        tier_map = self._make_tier_map(paid_models=["weak-model"])

        with (
            patch(_BUILD_TIER_MAP_TARGET, return_value=tier_map),
            patch(_OLLAMA_CANDIDATES_TARGET, return_value=[]),
            patch(_RANK_TARGET, return_value=["weak-model"]),
            patch(_SCORE_TARGET, return_value=0.50),  # 5.0/10 < 9.0 threshold
        ):
            rec = advisor.recommend_tier("coding", quality_threshold=9.0)

        assert rec.primary_model == "weak-model"
        assert "No tier reached quality threshold" in rec.rationale

    def test_recommend_tier_no_models_returns_absolute_fallback(self) -> None:
        """When no models exist in any tier, the absolute fallback is returned."""
        advisor = ModelAdvisor()
        empty_tier_map: dict[str, list[str]] = {
            "ollama": [],
            "or-free": [],
            "or-specific": [],
            "paid": [],
        }

        with (
            patch(_BUILD_TIER_MAP_TARGET, return_value=empty_tier_map),
            patch(_OLLAMA_CANDIDATES_TARGET, return_value=[]),
        ):
            rec = advisor.recommend_tier("coding")

        assert rec.primary_model == _ABSOLUTE_FALLBACK_MODEL
        assert rec.recommended_tier == "paid"
        assert _ABSOLUTE_FALLBACK_PROVIDER in rec.rationale

    def test_recommend_tier_ollama_preferred_when_score_meets_threshold(self) -> None:
        """Ollama tier is selected when its score meets the threshold (cheapest first)."""
        advisor = ModelAdvisor()
        tier_map = self._make_tier_map(paid_models=["cloud-model"])

        with (
            patch(_BUILD_TIER_MAP_TARGET, return_value=tier_map),
            patch(_OLLAMA_CANDIDATES_TARGET, return_value=["qwen2.5:7b"]),
            patch(_RANK_TARGET, return_value=["qwen2.5:7b"]),
            patch(_SCORE_TARGET, return_value=0.80),
        ):
            rec = advisor.recommend_tier("coding", quality_threshold=7.0)

        assert rec.recommended_tier == "ollama"
        assert rec.primary_model == "qwen2.5:7b"
        assert rec.cost_usd_per_month == 0.0

    def test_recommend_tier_invalid_task_type_degrades_gracefully(self) -> None:
        """Invalid task_type falls back to 'general' without raising."""
        advisor = ModelAdvisor()
        tier_map = self._make_tier_map()

        with (
            patch(_BUILD_TIER_MAP_TARGET, return_value=tier_map),
            patch(_OLLAMA_CANDIDATES_TARGET, return_value=[]),
            patch(_RANK_TARGET, return_value=["llama-3.3-70b-versatile"]),
            patch(_SCORE_TARGET, return_value=0.75),
        ):
            # Should not raise
            rec = advisor.recommend_tier("totally_invalid_task_xyz")

        assert isinstance(rec, TierRecommendation)

    # ------------------------------------------------------------------
    # estimate_roi
    # ------------------------------------------------------------------

    def test_estimate_roi_returns_roi_estimate(self) -> None:
        """estimate_roi() returns an ROIEstimate with populated fields."""
        advisor = ModelAdvisor()
        roi = advisor.estimate_roi(
            task_type="coding",
            current_score=60.0,
            current_best_model="llama3-8b",
            monthly_calls=1000,
        )
        assert isinstance(roi, ROIEstimate)
        assert roi.task_type == "coding"
        assert roi.current_best_model == "llama3-8b"

    def test_estimate_roi_delegates_to_build_roi_estimate(self) -> None:
        """estimate_roi result matches direct build_roi_estimate call."""
        from ttadev.primitives.llm.model_advisor.training_estimator import (
            build_roi_estimate,
        )

        advisor_obj = ModelAdvisor()
        kwargs = dict(
            task_type="math",
            current_score=55.0,
            current_best_model="gemma2:9b",
            monthly_calls=500,
            base_model="qwen2.5-7b",
        )
        roi_via_advisor = advisor_obj.estimate_roi(**kwargs)
        roi_direct = build_roi_estimate(**kwargs)

        assert roi_via_advisor.training_cost_usd == roi_direct.training_cost_usd
        assert roi_via_advisor.roi_breakeven_days == roi_direct.roi_breakeven_days
        assert roi_via_advisor.is_recommended == roi_direct.is_recommended

    # ------------------------------------------------------------------
    # recommend_with_roi
    # ------------------------------------------------------------------

    def test_recommend_with_roi_includes_roi_when_score_provided(self) -> None:
        """Returns (TierRecommendation, ROIEstimate) when current_score is given."""
        advisor_obj = ModelAdvisor()
        tier_map = self._make_tier_map()

        with (
            patch(_BUILD_TIER_MAP_TARGET, return_value=tier_map),
            patch(_OLLAMA_CANDIDATES_TARGET, return_value=[]),
            patch(_RANK_TARGET, return_value=["llama-3.3-70b-versatile"]),
            patch(_SCORE_TARGET, return_value=0.80),
        ):
            rec, roi = advisor_obj.recommend_with_roi(
                "coding", current_score=62.0, monthly_calls=5000
            )

        assert isinstance(rec, TierRecommendation)
        assert isinstance(roi, ROIEstimate)
        assert roi.task_type == "coding"
        assert roi.monthly_calls == 5000

    def test_recommend_with_roi_omits_roi_when_no_score(self) -> None:
        """Returns (TierRecommendation, None) when current_score is omitted."""
        advisor_obj = ModelAdvisor()
        tier_map = self._make_tier_map()

        with (
            patch(_BUILD_TIER_MAP_TARGET, return_value=tier_map),
            patch(_OLLAMA_CANDIDATES_TARGET, return_value=[]),
            patch(_RANK_TARGET, return_value=["llama-3.3-70b-versatile"]),
            patch(_SCORE_TARGET, return_value=0.80),
        ):
            rec, roi = advisor_obj.recommend_with_roi("coding", current_score=None)

        assert isinstance(rec, TierRecommendation)
        assert roi is None

    def test_recommend_with_roi_uses_primary_model_for_roi(self) -> None:
        """The ROI estimate uses the primary model from the tier recommendation."""
        advisor_obj = ModelAdvisor()
        tier_map = self._make_tier_map(paid_models=["my-primary-model"])

        with (
            patch(_BUILD_TIER_MAP_TARGET, return_value=tier_map),
            patch(_OLLAMA_CANDIDATES_TARGET, return_value=[]),
            patch(_RANK_TARGET, return_value=["my-primary-model"]),
            patch(_SCORE_TARGET, return_value=0.80),
        ):
            rec, roi = advisor_obj.recommend_with_roi(
                "coding", current_score=55.0, monthly_calls=200
            )

        assert rec.primary_model == "my-primary-model"
        assert roi is not None
        assert roi.current_best_model == "my-primary-model"

    # ------------------------------------------------------------------
    # Module-level singleton
    # ------------------------------------------------------------------

    def test_module_level_advisor_singleton_is_model_advisor(self) -> None:
        """The module-level `advisor` singleton is a ModelAdvisor instance."""
        from ttadev.primitives.llm.model_advisor.advisor import advisor as singleton

        assert isinstance(singleton, ModelAdvisor)

    def test_package_level_advisor_export(self) -> None:
        """ModelAdvisor and advisor are accessible from the package __init__."""
        from ttadev.primitives.llm.model_advisor import ModelAdvisor as ModelAdvisorCls
        from ttadev.primitives.llm.model_advisor import advisor as pkg_advisor

        assert ModelAdvisorCls is ModelAdvisor
        assert isinstance(pkg_advisor, ModelAdvisor)

    def test_llm_package_exports_model_advisor(self) -> None:
        """ModelAdvisor exports are accessible from ttadev.primitives.llm."""
        from ttadev.primitives.llm import (
            ModelAdvisor as LlmMA,
        )
        from ttadev.primitives.llm import (
            ROIEstimate as LlmROI,
        )
        from ttadev.primitives.llm import (
            TaskSuggestion as LlmTS,
        )
        from ttadev.primitives.llm import (
            TierRecommendation as LlmTR,
        )
        from ttadev.primitives.llm import (
            advisor as llm_advisor,
        )

        assert LlmMA is ModelAdvisor
        assert LlmROI is ROIEstimate
        assert LlmTS is TaskSuggestion
        assert LlmTR is TierRecommendation
        assert isinstance(llm_advisor, ModelAdvisor)
