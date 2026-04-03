"""Qwen fine-tuning strategy recommender for the ModelAdvisor feature.

Given a dict of evaluation results (task_type → score 0-100), this module
ranks task types as candidates for Qwen fine-tuning.  The ranking considers:

- Current eval score — lower score means more headroom to improve.
- Fine-tuning effectiveness — empirical improvement multipliers per task type.
- Training cost vs. expected monthly savings — ROI breakeven in days.

The primary entry point is :func:`suggest_qwen_finetunes`.

Example::

    from ttadev.primitives.llm.model_advisor.strategy import suggest_qwen_finetunes

    suggestions = suggest_qwen_finetunes(
        eval_results={"coding": 62.0, "math": 48.0, "chat": 81.0},
        monthly_calls_per_task={"coding": 5000, "math": 2000, "chat": 1000},
    )
    for s in suggestions:
        print(s.task_type, s.roi_breakeven_days, s.confidence)
"""

from __future__ import annotations

from dataclasses import dataclass

from ttadev.primitives.llm.task_selector import (
    TASK_CHAT,
    TASK_CODING,
    TASK_FUNCTION_CALLING,
    TASK_GENERAL,
    TASK_MATH,
    TASK_REASONING,
    TASK_VISION,
)

# ---------------------------------------------------------------------------
# Try to import the shared TaskSuggestion type produced by the recommendation
# module (parallel agent).  Fall back to an inline stub so this module stays
# independently importable during the integration phase.
# ---------------------------------------------------------------------------
try:
    from ttadev.primitives.llm.model_advisor.recommendation import (
        TaskSuggestion,  # type: ignore[assignment]  # noqa: F401
    )
except ImportError:  # pragma: no cover — stub path, replaced once wired together

    @dataclass
    class TaskSuggestion:
        """Stub — replaced by ``recommendation.TaskSuggestion`` once wired.

        Field names intentionally mirror ``recommendation.TaskSuggestion`` so
        the stub is a drop-in replacement during the integration phase.

        Attributes:
            task_type: The task identifier (e.g. ``"coding"``).
            current_score: Current eval score in [0, 100].
            expected_improvement: Absolute percentage-point improvement
                expected after fine-tuning (e.g. ``15.0`` means +15 pp).
            estimated_cost_usd: Estimated one-time training cost in USD.
            roi_breakeven_days: Days until training cost is recouped.
                ``float("inf")`` when monthly savings are zero.
            rationale: Human-readable explanation of the recommendation.
            confidence: Confidence score in [0, 1] that fine-tuning will
                deliver the projected improvement.
        """

        task_type: str
        current_score: float
        expected_improvement: float
        estimated_cost_usd: float
        roi_breakeven_days: float
        rationale: str
        confidence: float


__all__ = [
    "TaskSuggestion",
    "suggest_qwen_finetunes",
    "_FINETUNE_IMPROVEMENT",
    "_FINETUNE_BASE_COST",
]

# ---------------------------------------------------------------------------
# Empirical fine-tuning effectiveness multipliers
# ---------------------------------------------------------------------------
# Each value represents the typical *fraction* of remaining headroom
# (100 - current_score) that a Qwen fine-tune recovers.  Values are based on
# published results from the Qwen2.5 / Qwen2.5-Coder fine-tuning literature.
_FINETUNE_IMPROVEMENT: dict[str, float] = {
    TASK_CODING: 0.28,  # +28 % of headroom; strong domain signal
    TASK_MATH: 0.32,  # math benefits most — symbolic supervision
    TASK_REASONING: 0.22,
    TASK_FUNCTION_CALLING: 0.20,
    TASK_CHAT: 0.15,
    TASK_VISION: 0.12,  # multimodal fine-tuning is harder / costlier
    TASK_GENERAL: 0.18,
}

# ---------------------------------------------------------------------------
# Rough one-time training cost estimates in USD
# ---------------------------------------------------------------------------
# Based on a ~500 K-token dataset fine-tuned on a single A100-80 GB for 3-4 h
# via a cloud GPU provider at ~$3/hr.  Adjust ``_FINETUNE_BASE_COST`` values
# for your actual compute environment.
_FINETUNE_BASE_COST: dict[str, float] = {
    TASK_CODING: 45.0,
    TASK_MATH: 35.0,
    TASK_REASONING: 50.0,
    TASK_FUNCTION_CALLING: 30.0,
    TASK_CHAT: 25.0,
    TASK_VISION: 60.0,  # higher due to multimodal data prep
    TASK_GENERAL: 40.0,
}

# Default monthly call volume assumed when the caller omits a task from
# ``monthly_calls_per_task``.
_DEFAULT_MONTHLY_CALLS: int = 100


def _build_rationale(
    task_type: str,
    current_score: float,
    expected_improvement: float,
    roi_breakeven_days: float,
    confidence: float,
) -> str:
    """Compose a human-readable rationale string for a suggestion.

    Args:
        task_type: Task identifier.
        current_score: Current eval score in [0, 100].
        expected_improvement: Projected point gain after fine-tuning.
        roi_breakeven_days: Days to recoup training cost.
        confidence: Confidence in [0, 1].

    Returns:
        A single-sentence rationale string.
    """
    if roi_breakeven_days == float("inf"):
        roi_str = "no monthly savings projected"
    else:
        roi_str = f"ROI breakeven ≈ {roi_breakeven_days:.0f} days"

    return (
        f"Fine-tuning on '{task_type}' (current score {current_score:.1f}/100) "
        f"could yield +{expected_improvement:.1f} pts "
        f"(confidence {confidence:.0%}); {roi_str}."
    )


def suggest_qwen_finetunes(
    eval_results: dict[str, float],
    monthly_calls_per_task: dict[str, int] | None = None,
    cost_per_api_call_usd: float = 0.001,
    max_suggestions: int = 5,
) -> list[TaskSuggestion]:
    """Rank task types as fine-tuning candidates for a Qwen model.

    Uses current eval scores, known fine-tuning improvement rates, and
    estimated training costs to compute ROI breakeven for each task.
    Only tasks present in *eval_results* are considered.

    Args:
        eval_results: Mapping of ``task_type`` → current score (0–100).
            Tasks absent from this mapping are skipped entirely.
        monthly_calls_per_task: Expected monthly call volume per task type.
            Defaults to :data:`_DEFAULT_MONTHLY_CALLS` for any task not
            explicitly listed.
        cost_per_api_call_usd: Cost saved per call when using a fine-tuned
            local model instead of a paid API.  Default: ``$0.001``.
        max_suggestions: Maximum number of :class:`TaskSuggestion` objects
            to return.  Must be ≥ 1.

    Returns:
        A list of :class:`TaskSuggestion` sorted by ``roi_breakeven_days``
        ascending (best ROI first), truncated to *max_suggestions* entries.
        Returns an empty list when *eval_results* is empty.

    Raises:
        ValueError: If *max_suggestions* is less than 1.

    Example::

        suggestions = suggest_qwen_finetunes(
            eval_results={"coding": 55.0, "math": 40.0},
            monthly_calls_per_task={"coding": 3000, "math": 1500},
            max_suggestions=3,
        )
    """
    if max_suggestions < 1:
        raise ValueError(f"max_suggestions must be ≥ 1, got {max_suggestions}")

    if not eval_results:
        return []

    calls = monthly_calls_per_task or {}
    suggestions: list[TaskSuggestion] = []

    for task_type, current_score in eval_results.items():
        # Clamp score to [0, 100] defensively.
        current_score = max(0.0, min(100.0, float(current_score)))

        improvement_rate = _FINETUNE_IMPROVEMENT.get(task_type, 0.18)
        headroom = 100.0 - current_score
        expected_improvement = headroom * improvement_rate

        estimated_cost_usd = _FINETUNE_BASE_COST.get(task_type, 40.0)
        monthly_calls = calls.get(task_type, _DEFAULT_MONTHLY_CALLS)
        monthly_savings = monthly_calls * cost_per_api_call_usd

        # Express breakeven in days (30-day month assumed).
        roi_breakeven_days = (
            (estimated_cost_usd / monthly_savings) * 30.0 if monthly_savings > 0 else float("inf")
        )

        # Confidence: higher when score is low (more room to improve) *and*
        # when the task type has a higher known improvement rate.
        confidence = min(
            1.0,
            (1.0 - current_score / 100.0) * 0.7 + improvement_rate * 0.3,
        )

        rationale = _build_rationale(
            task_type=task_type,
            current_score=current_score,
            expected_improvement=expected_improvement,
            roi_breakeven_days=roi_breakeven_days,
            confidence=confidence,
        )

        suggestions.append(
            TaskSuggestion(
                task_type=task_type,
                current_score=current_score,
                expected_improvement=expected_improvement,
                estimated_cost_usd=estimated_cost_usd,
                roi_breakeven_days=roi_breakeven_days,
                confidence=confidence,
                rationale=rationale,
            )
        )

    # Sort by ROI breakeven ascending (best ROI = fewest days to break even).
    # Tasks with infinite breakeven sort last; ties broken by confidence desc.
    suggestions.sort(
        key=lambda s: (
            s.roi_breakeven_days if s.roi_breakeven_days != float("inf") else 1e18,
            -s.confidence,
        )
    )

    return suggestions[:max_suggestions]
