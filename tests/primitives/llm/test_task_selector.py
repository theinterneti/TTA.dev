"""Tests for ttadev/primitives/llm/task_selector.py."""

from __future__ import annotations

import pytest

from ttadev.primitives.llm.task_selector import (
    COMPLEXITY_COMPLEX,
    COMPLEXITY_MODERATE,
    COMPLEXITY_SIMPLE,
    TASK_CHAT,
    TASK_CODING,
    TASK_GENERAL,
    TASK_MATH,
    TASK_REASONING,
    TaskProfile,
    _extract_param_size_b,
    meets_complexity_threshold,
    min_ollama_params_for_complexity,
    rank_models_for_task,
    score_model_for_task,
)

# ── TaskProfile ───────────────────────────────────────────────────────────────


class TestTaskProfile:
    def test_direct_construction(self) -> None:
        p = TaskProfile(task_type=TASK_CODING, complexity=COMPLEXITY_MODERATE)
        assert p.task_type == TASK_CODING
        assert p.complexity == COMPLEXITY_MODERATE

    def test_factory_coding(self) -> None:
        p = TaskProfile.coding()
        assert p.task_type == TASK_CODING
        assert p.complexity == COMPLEXITY_MODERATE  # default

    def test_factory_coding_complex(self) -> None:
        p = TaskProfile.coding(COMPLEXITY_COMPLEX)
        assert p.complexity == COMPLEXITY_COMPLEX

    def test_factory_chat_default_simple(self) -> None:
        p = TaskProfile.chat()
        assert p.task_type == TASK_CHAT
        assert p.complexity == COMPLEXITY_SIMPLE

    def test_factory_reasoning(self) -> None:
        p = TaskProfile.reasoning(COMPLEXITY_COMPLEX)
        assert p.task_type == TASK_REASONING
        assert p.complexity == COMPLEXITY_COMPLEX

    def test_factory_math(self) -> None:
        p = TaskProfile.math()
        assert p.task_type == TASK_MATH

    def test_factory_general_default_simple(self) -> None:
        p = TaskProfile.general()
        assert p.task_type == TASK_GENERAL
        assert p.complexity == COMPLEXITY_SIMPLE

    def test_frozen(self) -> None:
        p = TaskProfile.coding()
        with pytest.raises((AttributeError, TypeError)):
            p.task_type = "other"  # type: ignore[misc]

    def test_invalid_task_type(self) -> None:
        with pytest.raises(ValueError, match="Unknown task_type"):
            TaskProfile(task_type="invalid_task", complexity=COMPLEXITY_SIMPLE)

    def test_invalid_complexity(self) -> None:
        with pytest.raises(ValueError, match="Unknown complexity"):
            TaskProfile(task_type=TASK_CODING, complexity="ultra")


# ── _extract_param_size_b ─────────────────────────────────────────────────────


class TestExtractParamSizeB:
    @pytest.mark.parametrize(
        "model_id,expected",
        [
            ("llama3.3:70b", 70.0),
            ("llama3.2:3b", 3.0),
            ("qwen2.5-coder:7b", 7.0),
            ("gemma2:9b-it", 9.0),
            ("llama-3.1-8b-instant", 8.0),
            ("mixtral:8x7b", 56.0),  # MoE: 8 * 7
            ("phi3:14b", 14.0),
            ("llama3.1:70b-instruct-q4_K_M", 70.0),
            ("qwen2.5:7b", 7.0),
            # Cloud models — no size in name
            ("models/gemini-2.5-flash", None),
            ("gpt-4o", None),
            ("llama-3.3-70b-versatile", 70.0),
        ],
    )
    def test_extract(self, model_id: str, expected: float | None) -> None:
        assert _extract_param_size_b(model_id) == expected


# ── score_model_for_task ──────────────────────────────────────────────────────


class TestScoreModelForTask:
    """Tests that rely on real BENCHMARK_DATA entries."""

    def test_known_coding_model_scores_above_zero(self) -> None:
        score = score_model_for_task("llama-3.3-70b-versatile", TaskProfile.coding())
        assert score > 0.0

    def test_returns_float_between_0_and_1(self) -> None:
        profile = TaskProfile.coding(COMPLEXITY_COMPLEX)
        for mid in [
            "llama-3.3-70b-versatile",
            "models/gemini-2.5-flash",
            "llama3.3:70b",
            "totally-unknown-model:99b",
        ]:
            score = score_model_for_task(mid, profile)
            assert 0.0 <= score <= 1.0, f"{mid} score {score} out of range"

    def test_gemini_flash_scores_for_coding(self) -> None:
        score = score_model_for_task("models/gemini-2.5-flash", TaskProfile.coding())
        assert score > 0.0

    def test_unknown_model_with_large_params_scores_above_tiny(self) -> None:
        # No benchmark data for this fake model, but size heuristic kicks in.
        large = score_model_for_task("unknown-frontier:70b", TaskProfile.coding())
        small = score_model_for_task("unknown-micro:3b", TaskProfile.coding())
        assert large > small

    def test_completely_unknown_model_gets_minimal_score(self) -> None:
        score = score_model_for_task("made-up-model-no-size", TaskProfile.general())
        assert score == pytest.approx(0.1)

    def test_strong_model_outscores_weak_on_coding(self) -> None:
        strong = score_model_for_task("llama-3.3-70b-versatile", TaskProfile.coding())
        weak = score_model_for_task("mixtral-8x7b-32768", TaskProfile.coding())
        assert strong >= weak


# ── meets_complexity_threshold ────────────────────────────────────────────────


class TestMeetsComplexityThreshold:
    def test_simple_always_passes(self) -> None:
        # No minimums for simple — anything passes.
        assert meets_complexity_threshold("made-up-model", TaskProfile.coding(COMPLEXITY_SIMPLE))

    def test_strong_model_passes_complex(self) -> None:
        assert meets_complexity_threshold(
            "llama-3.3-70b-versatile", TaskProfile.coding(COMPLEXITY_COMPLEX)
        )

    def test_gemini_flash_passes_complex_coding(self) -> None:
        assert meets_complexity_threshold(
            "models/gemini-2.5-flash", TaskProfile.coding(COMPLEXITY_COMPLEX)
        )

    def test_weak_model_may_fail_complex(self) -> None:
        # mixtral-8x7b-32768 has humaneval=40.2 vs threshold 80 for complex coding.
        result = meets_complexity_threshold(
            "mixtral-8x7b-32768", TaskProfile.coding(COMPLEXITY_COMPLEX)
        )
        assert result is False

    def test_unknown_model_passes_by_default(self) -> None:
        # Safe-to-route: no data → assume OK.
        assert meets_complexity_threshold("totally-unknown", TaskProfile.coding(COMPLEXITY_COMPLEX))


# ── rank_models_for_task ──────────────────────────────────────────────────────


class TestRankModelsForTask:
    def test_empty_list_returns_empty(self) -> None:
        assert rank_models_for_task([], TaskProfile.coding()) == []

    def test_single_model_returns_singleton(self) -> None:
        result = rank_models_for_task(["llama-3.3-70b-versatile"], TaskProfile.coding())
        assert result == ["llama-3.3-70b-versatile"]

    def test_preserves_all_models(self) -> None:
        models = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"]
        result = rank_models_for_task(models, TaskProfile.coding())
        assert sorted(result) == sorted(models)

    def test_stronger_model_ranked_higher_for_complex_coding(self) -> None:
        models = ["mixtral-8x7b-32768", "llama-3.3-70b-versatile"]
        result = rank_models_for_task(models, TaskProfile.coding(COMPLEXITY_COMPLEX))
        # llama-3.3-70b meets threshold; mixtral does not — it should come first.
        assert result[0] == "llama-3.3-70b-versatile"

    def test_threshold_passers_always_ranked_above_failures(self) -> None:
        models = [
            "mixtral-8x7b-32768",  # fails complex coding threshold (humaneval=40.2)
            "llama-3.3-70b-versatile",  # passes
            "models/gemini-2.5-flash",  # passes
        ]
        result = rank_models_for_task(models, TaskProfile.coding(COMPLEXITY_COMPLEX))
        fail_idx = result.index("mixtral-8x7b-32768")
        for winner in ["llama-3.3-70b-versatile", "models/gemini-2.5-flash"]:
            assert result.index(winner) < fail_idx


# ── min_ollama_params_for_complexity ─────────────────────────────────────────


class TestMinOllamaParamsForComplexity:
    def test_simple_returns_none(self) -> None:
        assert min_ollama_params_for_complexity(COMPLEXITY_SIMPLE) is None

    def test_moderate_returns_7(self) -> None:
        assert min_ollama_params_for_complexity(COMPLEXITY_MODERATE) == 7.0

    def test_complex_returns_30(self) -> None:
        assert min_ollama_params_for_complexity(COMPLEXITY_COMPLEX) == 30.0

    def test_unknown_complexity_returns_none(self) -> None:
        assert min_ollama_params_for_complexity("ultra") is None
