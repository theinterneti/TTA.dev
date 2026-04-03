"""Training cost and ROI estimation for the ModelAdvisor feature.

Provides cost estimation and ROI math functions used by the ModelAdvisor core.
All cost constants are approximate 2025/2026 rates in USD.

This module is the **canonical source** for :data:`FINETUNE_IMPROVEMENT` rates.
``strategy.py`` (and any other consumer) should import from here rather than
redefining the table.

Example::

    from ttadev.primitives.llm.model_advisor.training_estimator import build_roi_estimate

    roi = build_roi_estimate(
        task_type="coding",
        current_score=55.0,
        current_best_model="llama3-70b",
        monthly_calls=5000,
    )
    print(roi.roi_breakeven_days, roi.is_recommended)
"""

from __future__ import annotations

from ttadev.primitives.llm.model_advisor.recommendation import ROIEstimate

__all__ = [
    "COST_PER_1M_TOKENS_TRAINING",
    "TYPICAL_DATASET_TOKENS",
    "FINETUNE_IMPROVEMENT",
    "estimate_finetune_cost",
    "estimate_quality_improvement",
    "calculate_roi_breakeven",
    "build_roi_estimate",
]

# ---------------------------------------------------------------------------
# Cost constants
# ---------------------------------------------------------------------------

COST_PER_1M_TOKENS_TRAINING: dict[str, float] = {
    "qwen2.5-7b": 0.40,  # fine-tuning cost per 1M training tokens
    "qwen2.5-14b": 0.80,
    "qwen2.5-32b": 2.00,
    "qwen2.5-72b": 4.00,
    "default": 1.00,
}

TYPICAL_DATASET_TOKENS: dict[str, int] = {
    # task_type -> typical fine-tuning dataset size in tokens
    "coding": 500_000,
    "math": 350_000,
    "reasoning": 500_000,
    "function_calling": 300_000,
    "chat": 250_000,
    "vision": 600_000,
    "general": 400_000,
}

# ---------------------------------------------------------------------------
# Empirical fine-tuning effectiveness multipliers (canonical source)
# ---------------------------------------------------------------------------
# Each value is the fraction of remaining headroom (100 - current_score) that
# a Qwen fine-tune is expected to recover, based on published Qwen2.5 /
# Qwen2.5-Coder fine-tuning literature.

FINETUNE_IMPROVEMENT: dict[str, float] = {
    "coding": 0.28,  # strong domain signal from code corpora
    "math": 0.32,  # symbolic supervision benefits most
    "reasoning": 0.22,
    "function_calling": 0.20,
    "chat": 0.15,
    "vision": 0.12,  # multimodal fine-tuning is harder / costlier
    "general": 0.18,
}

# Default improvement rate when a task type is not found in the table.
_DEFAULT_IMPROVEMENT_RATE: float = FINETUNE_IMPROVEMENT["general"]

# Default dataset token count when a task type is not found in the table.
_DEFAULT_DATASET_TOKENS: int = TYPICAL_DATASET_TOKENS["general"]


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def estimate_finetune_cost(
    task_type: str,
    base_model: str = "default",
    dataset_tokens: int | None = None,
) -> float:
    """Estimate the USD cost to fine-tune a Qwen model on a task dataset.

    Looks up the per-1M-token training cost for *base_model* (falling back to
    ``"default"`` if the key is unknown) and multiplies by the effective
    dataset size in millions of tokens.

    Args:
        task_type: The task type (e.g. ``"coding"``, ``"math"``).
        base_model: Qwen model size key (e.g. ``"qwen2.5-7b"``).  Falls back
            to ``"default"`` when the key is not found in
            :data:`COST_PER_1M_TOKENS_TRAINING`.
        dataset_tokens: Number of training tokens.  Defaults to
            :data:`TYPICAL_DATASET_TOKENS` for *task_type* when ``None``.
            Falls back to the ``"general"`` entry for unknown task types.

    Returns:
        Estimated training cost in USD (non-negative float).
    """
    cost_per_1m = COST_PER_1M_TOKENS_TRAINING.get(
        base_model, COST_PER_1M_TOKENS_TRAINING["default"]
    )

    if dataset_tokens is None:
        dataset_tokens = TYPICAL_DATASET_TOKENS.get(task_type, _DEFAULT_DATASET_TOKENS)

    # Convert tokens to millions and compute total cost.
    tokens_millions = max(0, dataset_tokens) / 1_000_000
    return cost_per_1m * tokens_millions


def estimate_quality_improvement(
    task_type: str,
    current_score: float,
) -> float:
    """Estimate quality improvement in score points after fine-tuning.

    Computes the expected absolute gain as::

        improvement = headroom * improvement_rate

    where ``headroom = 100 - current_score`` and *improvement_rate* comes from
    :data:`FINETUNE_IMPROVEMENT` (falling back to the ``"general"`` rate for
    unknown task types).

    Args:
        task_type: The task type (e.g. ``"coding"``, ``"math"``).
        current_score: Current benchmark score in the range ``0``–``100``.
            Values outside this range are clamped defensively.

    Returns:
        Expected score improvement in percentage points (non-negative float).
    """
    current_score = max(0.0, min(100.0, float(current_score)))
    improvement_rate = FINETUNE_IMPROVEMENT.get(task_type, _DEFAULT_IMPROVEMENT_RATE)
    headroom = 100.0 - current_score
    return headroom * improvement_rate


def calculate_roi_breakeven(
    training_cost_usd: float,
    monthly_calls: int,
    cost_per_api_call_usd: float = 0.001,
) -> float:
    """Calculate days to ROI breakeven for a fine-tuning investment.

    Assumes a 30-day month and that the fine-tuned local model replaces paid
    API calls, saving *cost_per_api_call_usd* per call.

    Args:
        training_cost_usd: One-time fine-tuning cost in USD.
        monthly_calls: Expected number of calls per month.  When ``0`` or
            negative the payback period is infinite.
        cost_per_api_call_usd: Cost saved per call by using the local model
            instead of a paid API.  Default: ``$0.001``.

    Returns:
        Days to break even.  Returns ``float("inf")`` when *monthly_calls* is
        ``0`` or *cost_per_api_call_usd* is ``0``, making monthly savings zero.
    """
    monthly_savings = max(0, monthly_calls) * max(0.0, cost_per_api_call_usd)
    if monthly_savings <= 0:
        return float("inf")
    return (training_cost_usd / monthly_savings) * 30.0


def build_roi_estimate(
    task_type: str,
    current_score: float,
    current_best_model: str,
    monthly_calls: int = 100,
    base_model: str = "qwen2.5-7b",
    cost_per_api_call_usd: float = 0.001,
    roi_recommend_threshold_days: float = 90.0,
) -> ROIEstimate:
    """Build a complete ROIEstimate for a task type.

    Combines :func:`estimate_finetune_cost`, :func:`estimate_quality_improvement`,
    and :func:`calculate_roi_breakeven` into a single fully-populated
    :class:`~ttadev.primitives.llm.model_advisor.recommendation.ROIEstimate`.

    Args:
        task_type: Task type to estimate for (e.g. ``"coding"``).
        current_score: Current benchmark score in the range ``0``–``100``.
        current_best_model: ``model_id`` of the model currently achieving
            *current_score*.
        monthly_calls: Expected number of calls per month. Default: ``100``.
        base_model: Qwen model to fine-tune — used as the key for
            :data:`COST_PER_1M_TOKENS_TRAINING`. Default: ``"qwen2.5-7b"``.
        cost_per_api_call_usd: API cost saved per call when using the local
            fine-tuned model. Default: ``$0.001``.
        roi_recommend_threshold_days: Mark ``is_recommended=True`` when
            ``roi_breakeven_days < roi_recommend_threshold_days``.
            Default: ``90.0`` days (one quarter).

    Returns:
        Fully populated :class:`ROIEstimate` dataclass.
    """
    current_score = max(0.0, min(100.0, float(current_score)))

    training_cost_usd = estimate_finetune_cost(
        task_type=task_type,
        base_model=base_model,
    )

    improvement = estimate_quality_improvement(
        task_type=task_type,
        current_score=current_score,
    )
    finetuned_score_estimate = min(100.0, current_score + improvement)

    monthly_savings_usd = max(0, monthly_calls) * max(0.0, cost_per_api_call_usd)

    roi_breakeven_days = calculate_roi_breakeven(
        training_cost_usd=training_cost_usd,
        monthly_calls=monthly_calls,
        cost_per_api_call_usd=cost_per_api_call_usd,
    )

    is_recommended = roi_breakeven_days < roi_recommend_threshold_days

    return ROIEstimate(
        task_type=task_type,
        current_best_model=current_best_model,
        current_score=current_score,
        finetuned_score_estimate=finetuned_score_estimate,
        training_cost_usd=training_cost_usd,
        monthly_calls=monthly_calls,
        monthly_savings_usd=monthly_savings_usd,
        roi_breakeven_days=roi_breakeven_days,
        is_recommended=is_recommended,
    )
