"""Core ModelAdvisor class for tier-aware model recommendation.

Combines live benchmark data, hardware detection, and cost analysis to
produce actionable :class:`TierRecommendation` objects with rationale and
fallback chains.  The advisor evaluates seven tiers in priority order
(cheapest / most-accessible first) —

1. ``"ollama"`` — local models that fit the current hardware (free, private).
2. ``"groq"`` — Groq cloud free tier (rate-limited, not pay-per-token).
3. ``"gemini-free"`` — Gemini free-tier models (e.g. gemini-2.0-flash-lite).
4. ``"github-models"`` — GPT-4o / Llama / Phi / DeepSeek free with GITHUB_TOKEN.
5. ``"or-free"`` — OpenRouter free-tier models (less reliable than native APIs).
6. ``"or-specific"`` — OpenRouter paid-but-cheap models (low/medium cost).
7. ``"paid"`` — cloud APIs with no persistent free tier (OpenAI, Anthropic).

The cheapest tier whose best model meets the caller's ``quality_threshold``
is returned.

Example::

    from ttadev.primitives.llm.model_advisor.advisor import advisor

    rec = advisor.recommend_tier("coding", quality_threshold=7.0)
    print(rec.recommended_tier, rec.primary_model, rec.quality_score)

    tier_rec, roi = advisor.recommend_with_roi(
        "coding", current_score=62.0, monthly_calls=5000
    )
"""

from __future__ import annotations

import logging

from ttadev.primitives.llm.model_advisor.recommendation import (
    ROIEstimate,
    TierRecommendation,
)
from ttadev.primitives.llm.model_advisor.training_estimator import build_roi_estimate
from ttadev.primitives.llm.model_benchmarks import BENCHMARK_DATA
from ttadev.primitives.llm.model_registry import _DEFAULT_CLOUD_MODELS, ModelEntry
from ttadev.primitives.llm.task_selector import (
    COMPLEXITY_MODERATE,
    TaskProfile,
    rank_models_for_task,
    score_model_for_task,
)

__all__ = ["ModelAdvisor", "advisor"]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Monthly cost defaults by tier, used when a ``ModelEntry`` has no explicit
#: per-call price.  Values assume ~100 calls/month as the baseline.
TIER_COST_DEFAULTS: dict[str, float] = {
    "ollama": 0.0,
    "groq": 0.0,  # free tier (rate-limited, not pay-per-token)
    "gemini-free": 0.0,  # free tier models
    "github-models": 0.0,  # free with GitHub token
    "or-free": 0.0,
    "or-specific": 0.05,
    "paid": 2.50,
    "local-trained": 0.0,
}

#: Evaluation order — cheaper / more private tiers first.
_TIER_PRIORITY: list[str] = [
    "ollama",
    "groq",
    "gemini-free",
    "github-models",
    "or-free",
    "or-specific",
    "paid",
]

#: Fallback model returned when no models at all are available.
_ABSOLUTE_FALLBACK_MODEL: str = "llama-3.3-70b-versatile"
_ABSOLUTE_FALLBACK_PROVIDER: str = "groq"

#: Ollama-style model IDs extracted from ``BENCHMARK_DATA``.
#: These are used as *candidates* for the hardware-availability filter.
#: A model is considered ollama-style when its ID contains ``":"`` and
#: does not begin with ``"models/"`` (which is the Gemini prefix).
_OLLAMA_BENCHMARK_IDS: list[str] = sorted(
    {
        e.model_id
        for e in BENCHMARK_DATA
        if ":" in e.model_id and not e.model_id.startswith("models/")
    }
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _classify_entry(entry: ModelEntry) -> str | None:
    """Map a ``ModelEntry`` to its advisor tier label.

    Args:
        entry: A model registry entry to classify.

    Returns:
        One of ``"groq"``, ``"gemini-free"``, ``"github-models"``,
        ``"or-free"``, ``"or-specific"``, or ``"paid"``, or ``None``
        if the entry does not map to any known advisor tier.
    """
    if entry.provider == "groq":
        return "groq"  # Groq has a generous free tier (rate-limited, not pay-per-token)

    if entry.provider == "gemini":
        if entry.cost_tier == "free":
            return "gemini-free"
        return "paid"  # gemini-2.5-pro etc. are paid

    if entry.provider == "github":
        return "github-models"  # GitHub Models is free with GITHUB_TOKEN

    if entry.provider == "openrouter":
        if entry.cost_tier == "free":
            return "or-free"
        if entry.cost_tier in ("low", "medium"):
            return "or-specific"
        return "paid"

    if entry.provider in ("openai", "anthropic", "together"):
        return "paid"  # No persistent free API tier

    if entry.cost_tier == "high":
        return "paid"

    return None  # unclassified; skip


def _build_tier_map() -> dict[str, list[str]]:
    """Build a dict mapping tier labels → list[model_id] from ``_DEFAULT_CLOUD_MODELS``.

    Returns:
        Mapping of tier name to list of model IDs belonging to that tier.
    """
    tier_map: dict[str, list[str]] = {t: [] for t in _TIER_PRIORITY}
    seen: set[str] = set()

    for entry in _DEFAULT_CLOUD_MODELS:
        tier = _classify_entry(entry)
        if tier is None:
            continue
        if entry.model_id not in seen:
            tier_map[tier].append(entry.model_id)
            seen.add(entry.model_id)

    return tier_map


def _get_ollama_candidates() -> list[str]:
    """Return ollama model IDs from benchmark data that fit current hardware.

    Imports :class:`~ttadev.primitives.llm.hardware_detector.HardwareDetector`
    lazily to avoid slow startup when the advisor is imported.

    Returns:
        Filtered list of ollama model IDs that the local hardware can run.
        Returns the full benchmark candidate list on any import or runtime
        error so the advisor stays functional.
    """
    try:
        from ttadev.primitives.llm.hardware_detector import detector  # lazy import

        return detector.filter_ollama_models(_OLLAMA_BENCHMARK_IDS)
    except Exception as exc:  # pragma: no cover
        logger.debug("Hardware detection failed (%s); skipping ollama tier.", exc)
        return []


def _estimate_cost(tier: str, monthly_calls: int) -> float:
    """Estimate monthly cost in USD for a given tier and call volume.

    Scales the :data:`TIER_COST_DEFAULTS` baseline (100 calls) linearly with
    *monthly_calls*.

    Args:
        tier: Advisor tier label.
        monthly_calls: Expected monthly call volume.

    Returns:
        Estimated monthly cost in USD.
    """
    baseline = TIER_COST_DEFAULTS.get(tier, TIER_COST_DEFAULTS["paid"])
    if baseline == 0.0:
        return 0.0
    # Baseline is calibrated for 100 calls; scale proportionally.
    return baseline * (monthly_calls / 100.0)


def _build_recommendation(
    *,
    tier: str,
    primary: str,
    fallbacks: list[str],
    score_0_1: float,
    rationale: str,
    monthly_calls: int,
    task_type: str,
    quality_threshold: float,
) -> TierRecommendation:
    """Construct a :class:`TierRecommendation` from pre-computed fields.

    Args:
        tier: Advisor tier label.
        primary: Primary model ID.
        fallbacks: Ordered fallback model IDs.
        score_0_1: Raw score from ``score_model_for_task()`` in [0, 1].
        rationale: Human-readable explanation.
        monthly_calls: Expected monthly call volume.
        task_type: Task type string.
        quality_threshold: Caller-requested quality threshold (0–10).

    Returns:
        A fully populated :class:`TierRecommendation`.
    """
    return TierRecommendation(
        recommended_tier=tier,
        primary_model=primary,
        fallback_models=fallbacks,
        rationale=rationale,
        quality_score=round(score_0_1 * 10.0, 2),
        cost_usd_per_month=_estimate_cost(tier, monthly_calls),
        task_type=task_type,
        quality_threshold=quality_threshold,
    )


# ---------------------------------------------------------------------------
# ModelAdvisor
# ---------------------------------------------------------------------------


class ModelAdvisor:
    """Recommends the optimal model tier for a given task and quality threshold.

    Combines live benchmark data, hardware detection, and cost analysis to
    produce actionable recommendations with fallbacks.

    The advisor evaluates seven tiers in priority order (cheapest first):

    1. ``"ollama"`` — local models that fit the current hardware (free).
    2. ``"groq"`` — Groq cloud free tier (rate-limited, not pay-per-token).
    3. ``"gemini-free"`` — Gemini free-tier models (e.g. gemini-2.0-flash-lite).
    4. ``"github-models"`` — GPT-4o / Llama / Phi / DeepSeek free with GITHUB_TOKEN.
    5. ``"or-free"`` — OpenRouter free-tier models (zero cost, less reliable).
    6. ``"or-specific"`` — OpenRouter paid-but-cheap models (low/medium cost).
    7. ``"paid"`` — cloud APIs with no persistent free tier (OpenAI, Anthropic).

    The cheapest tier whose best model meets ``quality_threshold`` is returned.
    If no tier meets the threshold the tier with the highest-scoring model is
    returned with a rationale explaining the gap.

    Example::

        from ttadev.primitives.llm.model_advisor.advisor import advisor

        rec = advisor.recommend_tier("coding", quality_threshold=7.0)
        print(rec.recommended_tier, rec.primary_model, rec.quality_score)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend_tier(
        self,
        task_type: str,
        quality_threshold: float = 7.0,
        complexity: str = COMPLEXITY_MODERATE,
        monthly_calls: int = 100,
    ) -> TierRecommendation:
        """Recommend the best model tier for a task.

        Evaluates tiers in priority order (cheapest-first):
        ollama → groq → gemini-free → github-models → or-free → or-specific → paid.
        Returns the first tier
        whose best model's quality score (0–10) meets *quality_threshold*.
        When no tier satisfies the threshold, returns the tier/model with
        the highest absolute quality score and explains the gap in the
        rationale.

        Args:
            task_type: One of the ``TASK_*`` constants (e.g. ``"coding"``).
            quality_threshold: Minimum acceptable quality score on a 0–10
                scale.  Defaults to ``7.0``.
            complexity: Task complexity — one of the ``COMPLEXITY_*``
                constants.  Defaults to ``COMPLEXITY_MODERATE``.
            monthly_calls: Expected monthly usage (affects cost estimate).
                Defaults to ``100``.

        Returns:
            :class:`TierRecommendation` with the primary model, ordered
            fallbacks, rationale, and estimated monthly cost.
        """
        try:
            profile = TaskProfile(task_type=task_type, complexity=complexity)
        except ValueError:
            # Unknown task_type or complexity — degrade gracefully.
            logger.warning(
                "Invalid task_type=%r or complexity=%r; using defaults.",
                task_type,
                complexity,
            )
            profile = TaskProfile(task_type="general", complexity=COMPLEXITY_MODERATE)

        return self._select_tier(
            profile=profile,
            quality_threshold=quality_threshold,
            monthly_calls=monthly_calls,
            original_task_type=task_type,
        )

    def estimate_roi(
        self,
        task_type: str,
        current_score: float,
        current_best_model: str,
        monthly_calls: int = 100,
        base_model: str = "qwen2.5-7b",
    ) -> ROIEstimate:
        """Estimate the ROI of fine-tuning a Qwen model for this task.

        Delegates to :func:`~ttadev.primitives.llm.model_advisor.training_estimator.build_roi_estimate`.

        Args:
            task_type: Task type to estimate ROI for (e.g. ``"coding"``).
            current_score: Current eval score in the range ``0``–``100``.
            current_best_model: Model ID currently achieving *current_score*.
            monthly_calls: Expected monthly call volume.  Defaults to ``100``.
            base_model: Qwen model size to fine-tune (e.g. ``"qwen2.5-7b"``).

        Returns:
            :class:`ROIEstimate` with breakeven analysis.
        """
        return build_roi_estimate(
            task_type=task_type,
            current_score=current_score,
            current_best_model=current_best_model,
            monthly_calls=monthly_calls,
            base_model=base_model,
        )

    def recommend_with_roi(
        self,
        task_type: str,
        current_score: float | None = None,
        quality_threshold: float = 7.0,
        monthly_calls: int = 100,
    ) -> tuple[TierRecommendation, ROIEstimate | None]:
        """Combined tier recommendation plus optional ROI estimate.

        Calls :meth:`recommend_tier` and, when *current_score* is provided,
        also calls :meth:`estimate_roi` using the recommended primary model
        as the ``current_best_model``.

        Args:
            task_type: Task type string (e.g. ``"coding"``).
            current_score: Current eval score in the range ``0``–``100``.
                Pass ``None`` (default) to skip the ROI estimate.
            quality_threshold: Minimum quality score 0–10.  Defaults to
                ``7.0``.
            monthly_calls: Expected monthly call volume.  Defaults to ``100``.

        Returns:
            A 2-tuple of ``(TierRecommendation, ROIEstimate | None)``.
            The second element is ``None`` when *current_score* is omitted.
        """
        rec = self.recommend_tier(
            task_type=task_type,
            quality_threshold=quality_threshold,
            monthly_calls=monthly_calls,
        )

        roi: ROIEstimate | None = None
        if current_score is not None:
            roi = self.estimate_roi(
                task_type=task_type,
                current_score=current_score,
                current_best_model=rec.primary_model,
                monthly_calls=monthly_calls,
            )

        return rec, roi

    # ------------------------------------------------------------------
    # Internal implementation
    # ------------------------------------------------------------------

    def _select_tier(
        self,
        profile: TaskProfile,
        quality_threshold: float,
        monthly_calls: int,
        original_task_type: str,
    ) -> TierRecommendation:
        """Core tier-selection logic.

        Builds tier candidate lists, scores each tier's best model, and
        returns the cheapest tier that meets *quality_threshold*.

        Args:
            profile: Validated :class:`TaskProfile` for scoring.
            quality_threshold: Caller-requested quality threshold (0–10).
            monthly_calls: Monthly call volume for cost estimation.
            original_task_type: Raw task_type string passed by the caller
                (used for display in rationale / output fields).

        Returns:
            :class:`TierRecommendation` for the best matching tier.
        """
        tier_map = _build_tier_map()
        tier_map["ollama"] = _get_ollama_candidates()

        # Collect all model IDs across all tiers for cross-tier fallbacks.
        all_models: list[str] = []
        for tier in _TIER_PRIORITY:
            all_models.extend(tier_map.get(tier, []))

        # --- Evaluate each tier in priority order ---
        best_overall: tuple[str, str, float] | None = None  # (tier, model_id, score)

        for tier in _TIER_PRIORITY:
            candidates = tier_map.get(tier, [])
            if not candidates:
                continue

            ranked = rank_models_for_task(candidates, profile)
            if not ranked:
                continue

            top_model = ranked[0]
            score = score_model_for_task(top_model, profile)
            quality = score * 10.0

            # Track the global best regardless of threshold.
            if best_overall is None or score > best_overall[2]:
                best_overall = (tier, top_model, score)

            if quality >= quality_threshold:
                # This tier meets the threshold — build and return.
                fallbacks = self._build_fallbacks(
                    primary=top_model,
                    tier_ranked=ranked[1:],
                    other_tiers=_TIER_PRIORITY,
                    tier_map=tier_map,
                    profile=profile,
                    current_tier=tier,
                )
                rationale = (
                    f"Tier '{tier}' model '{top_model}' scores {quality:.1f}/10 "
                    f"for '{original_task_type}' tasks (threshold {quality_threshold}/10). "
                    f"Selected as the cheapest tier meeting quality requirements."
                )
                return _build_recommendation(
                    tier=tier,
                    primary=top_model,
                    fallbacks=fallbacks,
                    score_0_1=score,
                    rationale=rationale,
                    monthly_calls=monthly_calls,
                    task_type=original_task_type,
                    quality_threshold=quality_threshold,
                )

        # --- No tier met the threshold — return best available ---
        if best_overall is not None:
            b_tier, b_model, b_score = best_overall
            b_quality = b_score * 10.0
            ranked_overall = rank_models_for_task(all_models, profile)
            fallbacks = [m for m in ranked_overall if m != b_model][:5]
            rationale = (
                f"No tier reached quality threshold {quality_threshold}/10. "
                f"Best available: '{b_model}' (tier '{b_tier}') scores "
                f"{b_quality:.1f}/10 for '{original_task_type}'. "
                f"Consider lowering the threshold or fine-tuning a local model."
            )
            return _build_recommendation(
                tier=b_tier,
                primary=b_model,
                fallbacks=fallbacks,
                score_0_1=b_score,
                rationale=rationale,
                monthly_calls=monthly_calls,
                task_type=original_task_type,
                quality_threshold=quality_threshold,
            )

        # --- Absolute fallback: no models available at all ---
        return TierRecommendation(
            recommended_tier="paid",
            primary_model=_ABSOLUTE_FALLBACK_MODEL,
            fallback_models=[],
            rationale=(
                "No model benchmark data or registry entries are available. "
                f"Defaulting to '{_ABSOLUTE_FALLBACK_MODEL}' via "
                f"'{_ABSOLUTE_FALLBACK_PROVIDER}'. "
                "Ensure model_benchmarks.py and model_registry.py are populated."
            ),
            quality_score=0.0,
            cost_usd_per_month=_estimate_cost("paid", monthly_calls),
            task_type=original_task_type,
            quality_threshold=quality_threshold,
        )

    @staticmethod
    def _build_fallbacks(
        *,
        primary: str,
        tier_ranked: list[str],
        other_tiers: list[str],
        tier_map: dict[str, list[str]],
        profile: TaskProfile,
        current_tier: str,
        max_fallbacks: int = 5,
    ) -> list[str]:
        """Build a ranked fallback list for a recommendation.

        Collects remaining models from the same tier first, then appends
        top models from subsequent (more expensive) tiers, avoiding
        duplicates and the primary model itself.

        Args:
            primary: The primary recommended model ID (excluded).
            tier_ranked: Already-ranked remaining models in the same tier.
            other_tiers: Full ordered tier list.
            tier_map: Mapping of tier → model IDs.
            profile: :class:`TaskProfile` for ranking cross-tier models.
            current_tier: The tier that was selected.
            max_fallbacks: Maximum number of fallback models to return.

        Returns:
            Ordered list of fallback model IDs (best-first).
        """
        seen: set[str] = {primary}
        fallbacks: list[str] = []

        # Same-tier fallbacks (already ranked).
        for model in tier_ranked:
            if model not in seen and len(fallbacks) < max_fallbacks:
                fallbacks.append(model)
                seen.add(model)

        # Cross-tier fallbacks from more expensive tiers.
        for tier in other_tiers:
            if tier == current_tier:
                continue
            candidates = tier_map.get(tier, [])
            if not candidates:
                continue
            ranked = rank_models_for_task(candidates, profile)
            for model in ranked:
                if model not in seen and len(fallbacks) < max_fallbacks:
                    fallbacks.append(model)
                    seen.add(model)
            if len(fallbacks) >= max_fallbacks:
                break

        return fallbacks


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

#: Convenience singleton — import and use directly without instantiation.
advisor: ModelAdvisor = ModelAdvisor()
