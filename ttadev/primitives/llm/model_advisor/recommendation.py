"""Data model types for ModelAdvisor recommendations.

This module defines the core dataclasses used throughout the ModelAdvisor
feature to represent tier recommendations, ROI estimates, and task-level
fine-tuning suggestions.  All types are plain dataclasses with no runtime
dependencies beyond the standard library.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TierRecommendation:
    """Structured recommendation for which model tier to use for a task.

    The ModelAdvisor analyses available benchmarks and cost data to produce
    a single primary recommendation plus ordered fallback alternatives.

    Attributes:
        recommended_tier: The tier label for the primary recommendation.
            One of ``"local-trained"``, ``"ollama"``, ``"or-free"``,
            ``"or-specific"``, or ``"paid"``.
        primary_model: The ``model_id`` of the primary recommended model.
        fallback_models: Ordered list of ``model_id`` strings to try when
            the primary model is unavailable, from most- to least-preferred.
        rationale: Human-readable explanation of why this tier and model
            were chosen.
        quality_score: Predicted quality score for the primary model on
            this task, in the range ``0.0``–``10.0``.
        cost_usd_per_month: Estimated monthly cost in USD assuming
            100 calls per month.
        task_type: The task type this recommendation targets (e.g.
            ``"coding"``, ``"reasoning"``).
        quality_threshold: The minimum acceptable quality score that was
            requested by the caller, in the range ``0.0``–``10.0``.
    """

    recommended_tier: str
    primary_model: str
    fallback_models: list[str]
    rationale: str
    quality_score: float
    cost_usd_per_month: float
    task_type: str
    quality_threshold: float


@dataclass
class ROIEstimate:
    """Training ROI analysis for a task type.

    Captures the cost/benefit breakdown of fine-tuning a local model for a
    specific task type, compared with continuing to use the current best
    free or low-cost model.

    Attributes:
        task_type: The task type being analysed (e.g. ``"coding"``).
        current_best_model: ``model_id`` of the current best free or
            low-cost model for this task type.
        current_score: Benchmark score of ``current_best_model`` on this
            task, in the range ``0.0``–``100.0``.
        finetuned_score_estimate: Estimated benchmark score after
            fine-tuning, in the range ``0.0``–``100.0``.
        training_cost_usd: Estimated one-time cost in USD to perform the
            fine-tuning run.
        monthly_calls: Expected number of calls per month for this task
            type.
        monthly_savings_usd: Estimated monthly cost savings in USD versus
            using a paid API at the same call volume.
        roi_breakeven_days: Number of days required for accumulated monthly
            savings to recover the training cost.
        is_recommended: ``True`` when ``roi_breakeven_days`` is less than
            90 days, indicating a positive ROI within a single quarter.
    """

    task_type: str
    current_best_model: str
    current_score: float
    finetuned_score_estimate: float
    training_cost_usd: float
    monthly_calls: int
    monthly_savings_usd: float
    roi_breakeven_days: float
    is_recommended: bool


@dataclass
class TaskSuggestion:
    """A suggested task type to fine-tune next.

    Produced by the ModelAdvisor when scanning all task types to identify
    the highest-value fine-tuning opportunities given current benchmark
    coverage and cost data.

    Attributes:
        task_type: The task type recommended for fine-tuning (e.g.
            ``"summarisation"``).
        current_score: Current benchmark score on this task type in the
            range ``0.0``–``100.0``.  Lower values indicate a stronger
            candidate for improvement.
        expected_improvement: Absolute percentage-point improvement
            expected after fine-tuning (e.g. ``15.0`` means +15 pp).
        estimated_cost_usd: Estimated one-time cost in USD to perform the
            fine-tuning run for this task type.
        roi_breakeven_days: Number of days required to break even on
            ``estimated_cost_usd`` through accumulated savings.
        rationale: Human-readable explanation of why this task type is
            recommended for fine-tuning at this time.
        confidence: Confidence level in this recommendation, in the range
            ``0.0``–``1.0``.  Values above ``0.7`` are considered reliable.
    """

    task_type: str
    current_score: float
    expected_improvement: float
    estimated_cost_usd: float
    roi_breakeven_days: float
    rationale: str
    confidence: float
