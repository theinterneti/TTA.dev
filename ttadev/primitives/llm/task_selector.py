"""Task-aware model selection for LLM routing.

Given a task type (coding, reasoning, math, …) and a complexity level
(simple / moderate / complex), this module ranks candidate model IDs from
best to worst so that :class:`~ttadev.primitives.llm.model_router.ModelRouterPrimitive`
can try the most appropriate model first.

Scoring is based on published benchmark data from
:mod:`~ttadev.primitives.llm.model_benchmarks`.  When no benchmark data exists
for a model, a param-size heuristic is used as a graceful fallback.

Benchmark normalization
-----------------------
All benchmarks are treated as 0–100 percentages **except** ``arena_elo``,
which stores raw LMSYS ELO on a 0–2000 scale.  The scoring code divides
``arena_elo`` by 20 before combining it with other benchmarks so all terms
live on a comparable scale.

Example::

    from ttadev.primitives.llm.task_selector import TaskProfile, rank_models_for_task

    profile = TaskProfile.coding(complexity=COMPLEXITY_COMPLEX)
    ordered = rank_models_for_task(
        ["llama3.3:70b", "llama3.2:3b", "qwen2.5-coder:7b"],
        profile,
    )
    # ordered[0] is the best fit
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ttadev.primitives.llm.model_benchmarks import get_best_score

__all__ = [
    # Task-type constants
    "TASK_CODING",
    "TASK_REASONING",
    "TASK_MATH",
    "TASK_CHAT",
    "TASK_FUNCTION_CALLING",
    "TASK_VISION",
    "TASK_GENERAL",
    # Complexity constants
    "COMPLEXITY_SIMPLE",
    "COMPLEXITY_MODERATE",
    "COMPLEXITY_COMPLEX",
    # Core type
    "TaskProfile",
    # Public helpers
    "score_model_for_task",
    "meets_complexity_threshold",
    "rank_models_for_task",
    "min_ollama_params_for_complexity",
]

# ── Task-type constants ────────────────────────────────────────────────────────

TASK_CODING: str = "coding"
TASK_REASONING: str = "reasoning"
TASK_MATH: str = "math"
TASK_CHAT: str = "chat"
TASK_FUNCTION_CALLING: str = "function_calling"
TASK_VISION: str = "vision"
TASK_GENERAL: str = "general"

# ── Complexity constants ───────────────────────────────────────────────────────

COMPLEXITY_SIMPLE: str = "simple"
COMPLEXITY_MODERATE: str = "moderate"
COMPLEXITY_COMPLEX: str = "complex"

# ── Benchmark weights per task type ───────────────────────────────────────────
# Each inner dict maps benchmark_name → weight.  Weights within a task sum ≤ 1.
# arena_elo values are divided by 20 before weighting (normalization).

_TASK_WEIGHTS: dict[str, dict[str, float]] = {
    TASK_CODING: {
        "humaneval": 0.45,
        "mbpp": 0.20,
        "mmlu": 0.20,
        "arena_elo": 0.15,
    },
    TASK_REASONING: {
        "gpqa": 0.35,
        "mmlu": 0.35,
        "arena_elo": 0.20,
        "humaneval": 0.10,
    },
    TASK_MATH: {
        "math": 0.55,
        "gpqa": 0.25,
        "mmlu": 0.20,
    },
    TASK_CHAT: {
        "arena_elo": 0.50,
        "mt_bench": 0.30,
        "mmlu": 0.20,
    },
    TASK_FUNCTION_CALLING: {
        "humaneval": 0.35,
        "mmlu": 0.35,
        "arena_elo": 0.30,
    },
    TASK_VISION: {
        "mmlu": 0.50,
        "arena_elo": 0.30,
        "humaneval": 0.20,
    },
    TASK_GENERAL: {
        "mmlu": 0.35,
        "arena_elo": 0.35,
        "humaneval": 0.20,
        "mt_bench": 0.10,
    },
}

# ── Complexity minimum benchmark scores ───────────────────────────────────────
# Maps task_type → complexity → {benchmark: min_score}.
# A model must meet ALL specified minimums to *meet* the threshold.
# Models below threshold are not excluded from routing (the router still tries
# them), but they are ranked lower by `rank_models_for_task`.

_COMPLEXITY_THRESHOLDS: dict[str, dict[str, dict[str, float]]] = {
    TASK_CODING: {
        COMPLEXITY_SIMPLE: {},
        COMPLEXITY_MODERATE: {"humaneval": 60.0, "mmlu": 65.0},
        COMPLEXITY_COMPLEX: {"humaneval": 80.0, "mmlu": 75.0},
    },
    TASK_REASONING: {
        COMPLEXITY_SIMPLE: {},
        COMPLEXITY_MODERATE: {"mmlu": 70.0},
        COMPLEXITY_COMPLEX: {"mmlu": 80.0, "gpqa": 35.0},
    },
    TASK_MATH: {
        COMPLEXITY_SIMPLE: {},
        COMPLEXITY_MODERATE: {"math": 40.0},
        COMPLEXITY_COMPLEX: {"math": 60.0},
    },
    TASK_CHAT: {
        COMPLEXITY_SIMPLE: {},
        COMPLEXITY_MODERATE: {"arena_elo": 1200.0},
        COMPLEXITY_COMPLEX: {"arena_elo": 1350.0},
    },
    TASK_FUNCTION_CALLING: {
        COMPLEXITY_SIMPLE: {},
        COMPLEXITY_MODERATE: {"humaneval": 55.0},
        COMPLEXITY_COMPLEX: {"humaneval": 75.0},
    },
    TASK_VISION: {
        COMPLEXITY_SIMPLE: {},
        COMPLEXITY_MODERATE: {"mmlu": 65.0},
        COMPLEXITY_COMPLEX: {"mmlu": 80.0},
    },
    TASK_GENERAL: {
        COMPLEXITY_SIMPLE: {},
        COMPLEXITY_MODERATE: {"mmlu": 65.0},
        COMPLEXITY_COMPLEX: {"mmlu": 75.0},
    },
}

# ── Minimum param sizes for Ollama model skipping ────────────────────────────
# SIMPLE: no constraint.  MODERATE: prefer ≥7B.  COMPLEX: require ≥30B.
# ``None`` means no minimum; ``float`` is the threshold in billions.

_COMPLEXITY_MIN_PARAMS_B: dict[str, float | None] = {
    COMPLEXITY_SIMPLE: None,
    COMPLEXITY_MODERATE: 7.0,
    COMPLEXITY_COMPLEX: 30.0,
}

# ── Regex for parsing param size from model IDs ───────────────────────────────
# Matches patterns like "70b", "8x7b", "3b", "13b", "7.1b"
_PARAM_PATTERN = re.compile(
    r"(?:^|[:\-_])(\d+(?:\.\d+)?)x?(\d+(?:\.\d+)?)b\b",
    re.IGNORECASE,
)
_SIMPLE_PARAM_PATTERN = re.compile(
    r"(?:^|[:\-_/])(\d+(?:\.\d+)?)b\b",
    re.IGNORECASE,
)


# ── TaskProfile ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TaskProfile:
    """Describes a task so the router can select the most appropriate model.

    Attributes:
        task_type: One of the ``TASK_*`` string constants.
        complexity: One of the ``COMPLEXITY_*`` string constants.

    Example::

        profile = TaskProfile(task_type=TASK_CODING, complexity=COMPLEXITY_COMPLEX)
        # or via factory:
        profile = TaskProfile.coding(complexity=COMPLEXITY_COMPLEX)
    """

    task_type: str
    complexity: str

    def __post_init__(self) -> None:
        valid_tasks = {
            TASK_CODING,
            TASK_REASONING,
            TASK_MATH,
            TASK_CHAT,
            TASK_FUNCTION_CALLING,
            TASK_VISION,
            TASK_GENERAL,
        }
        valid_complexities = {COMPLEXITY_SIMPLE, COMPLEXITY_MODERATE, COMPLEXITY_COMPLEX}
        if self.task_type not in valid_tasks:
            raise ValueError(f"Unknown task_type {self.task_type!r}. Valid: {valid_tasks}")
        if self.complexity not in valid_complexities:
            raise ValueError(f"Unknown complexity {self.complexity!r}. Valid: {valid_complexities}")

    # ── Factory methods ────────────────────────────────────────────────────

    @classmethod
    def coding(cls, complexity: str = COMPLEXITY_MODERATE) -> TaskProfile:
        """Create a coding task profile."""
        return cls(task_type=TASK_CODING, complexity=complexity)

    @classmethod
    def reasoning(cls, complexity: str = COMPLEXITY_MODERATE) -> TaskProfile:
        """Create a reasoning task profile."""
        return cls(task_type=TASK_REASONING, complexity=complexity)

    @classmethod
    def math(cls, complexity: str = COMPLEXITY_MODERATE) -> TaskProfile:
        """Create a math task profile."""
        return cls(task_type=TASK_MATH, complexity=complexity)

    @classmethod
    def chat(cls, complexity: str = COMPLEXITY_SIMPLE) -> TaskProfile:
        """Create a chat task profile."""
        return cls(task_type=TASK_CHAT, complexity=complexity)

    @classmethod
    def function_calling(cls, complexity: str = COMPLEXITY_MODERATE) -> TaskProfile:
        """Create a function-calling task profile."""
        return cls(task_type=TASK_FUNCTION_CALLING, complexity=complexity)

    @classmethod
    def vision(cls, complexity: str = COMPLEXITY_MODERATE) -> TaskProfile:
        """Create a vision task profile."""
        return cls(task_type=TASK_VISION, complexity=complexity)

    @classmethod
    def general(cls, complexity: str = COMPLEXITY_SIMPLE) -> TaskProfile:
        """Create a general task profile."""
        return cls(task_type=TASK_GENERAL, complexity=complexity)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _extract_param_size_b(model_id: str) -> float | None:
    """Parse the parameter count (in billions) from a model ID string.

    Handles common formats::

        "llama3.3:70b"          → 70.0
        "mixtral:8x7b"          → 56.0   (product of 8 * 7)
        "qwen2.5-coder:7b"      → 7.0
        "gemma2:9b-it"          → 9.0
        "llama-3.1-8b-instant"  → 8.0

    Returns ``None`` if no size can be determined (e.g. cloud models like
    ``"gpt-4o"`` or ``"models/gemini-2.5-flash"``).

    Args:
        model_id: Any model identifier string.

    Returns:
        Parameter size in billions, or ``None`` if unparseable.
    """
    model_lower = model_id.lower()

    # Try MoE pattern first: "NxMb" (e.g. "8x7b" → 56)
    moe = _PARAM_PATTERN.search(model_lower)
    if moe and moe.lastindex == 2:
        n, m = float(moe.group(1)), float(moe.group(2))
        # Confirm the full match includes "x" between them
        if "x" in moe.group(0).lower():
            return n * m

    # Try simple "Nb" pattern
    simple = _SIMPLE_PARAM_PATTERN.search(model_lower)
    if simple:
        return float(simple.group(1))

    return None


def score_model_for_task(model_id: str, profile: TaskProfile) -> float:
    """Compute a 0.0–1.0 suitability score for a model on a given task profile.

    Benchmark scores are weighted by :data:`_TASK_WEIGHTS` for the task type.
    ``arena_elo`` values are divided by 20 before combining.

    When no benchmark data is available for a model, falls back to a
    param-size heuristic: larger → higher score, capped at 0.5 to ensure
    benchmark-backed models always outrank unknowns.

    Args:
        model_id: Any model identifier (aliases are resolved internally).
        profile: The :class:`TaskProfile` describing the task.

    Returns:
        A score between 0.0 and 1.0 (higher is better).
    """
    weights = _TASK_WEIGHTS.get(profile.task_type, _TASK_WEIGHTS[TASK_GENERAL])

    weighted_sum = 0.0
    total_weight = 0.0

    for benchmark, weight in weights.items():
        raw = get_best_score(model_id, benchmark)
        if raw is None:
            continue
        # Normalize arena_elo from 0-2000 to 0-100
        normalized = raw / 20.0 if benchmark == "arena_elo" else raw
        weighted_sum += normalized * weight
        total_weight += weight

    if total_weight > 0:
        # Return weighted average normalized to 0-1
        return (weighted_sum / total_weight) / 100.0

    # Fallback: param-size heuristic
    params_b = _extract_param_size_b(model_id)
    if params_b is not None:
        # 70B → ~0.45, 7B → ~0.25, 3B → ~0.20
        return min(0.5, 0.15 + (params_b / 200.0))

    return 0.1  # unknown model, lowest rank but still routable


def meets_complexity_threshold(model_id: str, profile: TaskProfile) -> bool:
    """Return True if *model_id* satisfies the minimum benchmark scores for *profile*.

    Checks every minimum defined in :data:`_COMPLEXITY_THRESHOLDS` for the
    (task_type, complexity) pair.  A model with no benchmark data passes by
    default (safe-to-route assumption).

    ``arena_elo`` thresholds are compared against the raw ELO score (0–2000
    scale) because the threshold values in :data:`_COMPLEXITY_THRESHOLDS` are
    stored as raw ELO.

    Args:
        model_id: Any model identifier.
        profile: The task profile to check against.

    Returns:
        ``True`` when all minimums are met (or no benchmark data exists).
    """
    task_thresholds = _COMPLEXITY_THRESHOLDS.get(profile.task_type, {})
    minimums = task_thresholds.get(profile.complexity, {})

    for benchmark, min_score in minimums.items():
        score = get_best_score(model_id, benchmark)
        if score is not None and score < min_score:
            return False

    return True


def rank_models_for_task(model_ids: list[str], profile: TaskProfile) -> list[str]:
    """Return *model_ids* sorted from best to worst for *profile*.

    Models that meet the complexity threshold are ranked above those that
    do not.  Within each group, models are ordered by
    :func:`score_model_for_task` descending.

    Args:
        model_ids: Candidate model IDs to rank.
        profile: The task profile to rank against.

    Returns:
        A new list with the same model IDs, best-first.
    """
    if not model_ids:
        return []

    def sort_key(mid: str) -> tuple[int, float]:
        meets = 0 if meets_complexity_threshold(mid, profile) else 1
        score = score_model_for_task(mid, profile)
        return (meets, -score)

    return sorted(model_ids, key=sort_key)


def min_ollama_params_for_complexity(complexity: str) -> float | None:
    """Return the minimum parameter size (in billions) for Ollama models at *complexity*.

    Used by :class:`~ttadev.primitives.llm.model_router.ModelRouterPrimitive`
    to skip small local models when the task demands more capable ones.

    Args:
        complexity: One of the ``COMPLEXITY_*`` constants.

    Returns:
        Minimum size in billions, or ``None`` for no minimum.
    """
    return _COMPLEXITY_MIN_PARAMS_B.get(complexity)
