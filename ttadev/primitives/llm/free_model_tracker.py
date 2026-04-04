"""OpenRouter free model discovery and caching.

Tracks available free models on OpenRouter and provides role-based ranking.
Works standalone (module-level helpers) or as a class instance.

All network I/O is async; on-disk caching uses plain JSON so the cache survives
process restarts with zero dependencies beyond the standard library.

Example::

    tracker = FreeModelTracker(api_key=os.environ.get("OPENROUTER_API_KEY"))
    models = await tracker.refresh()
    best_id = await tracker.recommend(preferred=["qwen/qwen3-235b-a22b:free"])
    print(best_id)  # e.g. "qwen/qwen3-235b-a22b:free"
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import httpx

from ttadev.primitives.llm.model_benchmarks import get_best_score

logger = logging.getLogger(__name__)

_OR_MODELS_URL = "https://openrouter.ai/api/v1/models"
_DEFAULT_CACHE_PATH = Path("~/.cache/ttadev/or_free_models.json")
_DEFAULT_CACHE_TTL: float = 7 * 24 * 3600  # 1 week

# Last-resort fallback ordering used when no Artificial Analysis benchmark data
# is available for any of the candidate models.  When benchmark data *is*
# available, ``rank_free_models_by_quality()`` is used instead and this list is
# ignored.  Update this list only when you want to change the cold-start
# ordering for deployments that have never populated the benchmark cache.
#
# Verified against https://openrouter.ai/models?free=true (April 2026):
#   - qwen/qwen3.6-plus:free   — confirmed tool-use + array-content support ✅
#   - openai/gpt-oss-20b:free  — confirmed tool-use + array-content support ✅
#   - meta-llama/llama-3.3-70b-instruct:free — high quality, occasionally 429s
#   - qwen/qwen3-235b-a22b:free — large MoE, strong general quality
#   - deepseek/deepseek-r1:free — strong reasoning; verbose output
# Removed (stale/incompatible):
#   - nousresearch/hermes-3-llama-3.1-405b:free (consistently unavailable)
#   - mistralai/mistral-7b-instruct:free (low quality, superseded)
_BUILTIN_PREFERRED: list[str] = [
    "qwen/qwen3.6-plus:free",
    "openai/gpt-oss-20b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-235b-a22b:free",
    "deepseek/deepseek-r1:free",
]

# Benchmark weights by task type.  Each entry is an ordered list of
# (benchmark_name, weight) pairs used to compute a composite quality score.
# Benchmarks earlier in the list have higher priority; weights are used in a
# weighted-average so a missing score for one benchmark gracefully degrades
# rather than zeroing out the whole composite.
_ARENA_ELO_SCALE: float = 20.0  # arena_elo is 0-2000; divide to get 0-100

_TASK_WEIGHTS: dict[str, list[tuple[str, float]]] = {
    "coding": [
        ("aa_coding", 3.0),
        ("aa_intelligence", 2.0),
        ("humaneval", 1.0),
    ],
    "math": [
        ("aa_math", 3.0),
        ("aa_intelligence", 2.0),
        ("math", 1.0),
    ],
    "reasoning": [
        ("aa_intelligence", 3.0),
        ("mmlu_pro", 2.0),
        ("gpqa", 1.0),
    ],
}


@dataclass
class ORModel:
    """Metadata for a single OpenRouter model."""

    id: str
    name: str
    context_length: int
    prompt_price: float
    completion_price: float
    tags: list[str] = field(default_factory=list)
    modality: str = "text->text"

    @property
    def is_free(self) -> bool:
        """Return True when both prompt and completion pricing are zero."""
        return self.prompt_price == 0.0 and self.completion_price == 0.0

    @property
    def is_text_model(self) -> bool:
        """Return True when this model accepts text input and produces text output."""
        if not self.modality.startswith("text->text"):
            return False
        # Reject known non-LLM model families by ID pattern (catches stale cache
        # entries that predate modality tracking).
        _non_text = ("lyria", "dall-e", "stable-diffusion", "whisper", "tts", "imagen")
        return not any(p in self.id.lower() for p in _non_text)


# ── Module-level helpers ──────────────────────────────────────────────────────


async def fetch_free_models(api_key: str | None = None) -> list[ORModel]:
    """Fetch current free models from the OpenRouter API.

    Args:
        api_key: Optional OpenRouter API key for authenticated access.

    Returns:
        List of ORModel instances whose prompt *and* completion price are zero.

    Raises:
        httpx.HTTPStatusError: If the API returns a non-2xx response.
        httpx.TimeoutException: If the request times out.
    """
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(_OR_MODELS_URL, headers=headers)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()

    models: list[ORModel] = []
    for m in data.get("data", []):
        pricing = m.get("pricing", {})
        try:
            prompt_price = float(pricing.get("prompt") or "1")
            completion_price = float(pricing.get("completion") or "1")
        except (ValueError, TypeError):
            prompt_price = 1.0
            completion_price = 1.0
        arch = m.get("architecture", {})
        modality = arch.get("modality") or arch.get("input_modalities", ["text"])[0] + "->text"
        models.append(
            ORModel(
                id=m["id"],
                name=m.get("name", m["id"]),
                context_length=int(m.get("context_length") or 4096),
                prompt_price=prompt_price,
                completion_price=completion_price,
                modality=str(modality),
            )
        )

    return [m for m in models if m.is_free and m.is_text_model]


def _load_cache(cache_path: Path) -> tuple[list[ORModel], float]:
    """Load cached model list from disk.

    Args:
        cache_path: Path to the JSON cache file (tilde expansion applied).

    Returns:
        Tuple of ``(models, age_seconds)``.  Age is ``float("inf")`` when the
        file does not exist.
    """
    path = cache_path.expanduser()
    if not path.exists():
        return [], float("inf")

    try:
        raw: dict[str, Any] = json.loads(path.read_text())
        age = time.time() - float(raw.get("fetched_at", 0))
        models = [
            ORModel(**{k: v for k, v in m.items() if k in ORModel.__dataclass_fields__})
            for m in raw.get("models", [])
        ]
        return models, age
    except Exception:
        logger.warning("Could not read free model cache at %s", path)
        return [], float("inf")


def _save_cache(models: list[ORModel], cache_path: Path) -> None:
    """Persist model list to disk as JSON.

    Args:
        models: Models to cache.
        cache_path: Destination path (parent dirs created as needed).
    """
    path = cache_path.expanduser()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {"fetched_at": time.time(), "models": [asdict(m) for m in models]},
                indent=2,
            )
        )
    except Exception:
        logger.warning("Could not write free model cache to %s", path)


async def get_free_models(
    api_key: str | None = None,
    *,
    force_refresh: bool = False,
    cache_path: Path = _DEFAULT_CACHE_PATH,
    cache_ttl: float = _DEFAULT_CACHE_TTL,
) -> list[ORModel]:
    """Return free OR models, using on-disk cache when fresh.

    Args:
        api_key: Optional API key for authenticated access.
        force_refresh: Bypass cache and always fetch from the API.
        cache_path: Path for the JSON cache file.
        cache_ttl: Cache validity in seconds (default one week).

    Returns:
        List of free ORModel instances. Returns stale cache on network failure.
    """
    cached, age = _load_cache(cache_path)
    if cached and age < cache_ttl and not force_refresh:
        cached = [m for m in cached if m.is_text_model]
        logger.debug("Using %d cached free models (age %.0fs)", len(cached), age)
        return cached

    try:
        models = await fetch_free_models(api_key)
        _save_cache(models, cache_path)
        logger.info("Refreshed %d free OR models", len(models))
        return models
    except Exception as exc:
        logger.warning(
            "Failed to fetch OR free models (%r); returning stale cache (%d models)",
            exc,
            len(cached),
        )
        return cached


def _composite_score(model_id: str, task_type: str | None) -> tuple[float, float]:
    """Compute a weighted composite quality score for *model_id*.

    Args:
        model_id: Base model ID (`:free` suffix already stripped).
        task_type: One of ``"coding"``, ``"math"``, ``"reasoning"``, or
            ``None`` for the general-purpose default weights.

    Returns:
        A ``(composite_score, total_weight)`` tuple.  When ``total_weight``
        is zero no benchmark data was found and the caller should fall back
        to a heuristic (e.g. context length).
    """
    weights = _TASK_WEIGHTS.get(task_type or "", None) if task_type else None
    if weights is None:
        # Default: general intelligence > broad knowledge > community preference
        weights = [
            ("aa_intelligence", 3.0),
            ("mmlu", 2.0),
            ("arena_elo", 1.0),
        ]

    total_weight = 0.0
    weighted_sum = 0.0
    for benchmark, weight in weights:
        raw = get_best_score(model_id, benchmark)
        if raw is None:
            continue
        # Normalise arena_elo from 0-2000 scale to 0-100
        score = raw / _ARENA_ELO_SCALE if benchmark == "arena_elo" else raw
        weighted_sum += score * weight
        total_weight += weight

    composite = weighted_sum / total_weight if total_weight > 0 else 0.0
    return composite, total_weight


def rank_free_models_by_quality(
    models: list[ORModel],
    task_type: str | None = None,
) -> list[ORModel]:
    """Rank free OpenRouter models using Artificial Analysis benchmark data.

    For each model the `:free` suffix is stripped from its ID before looking
    up quality scores so that OpenRouter model IDs map correctly to the base
    IDs stored in :data:`~ttadev.primitives.llm.model_benchmarks.BENCHMARK_DATA`.

    Benchmark weights by task type:

    * ``"coding"``:  ``aa_coding`` (×3) › ``aa_intelligence`` (×2) › ``humaneval`` (×1)
    * ``"math"``:    ``aa_math`` (×3) › ``aa_intelligence`` (×2) › ``math`` (×1)
    * ``"reasoning"``: ``aa_intelligence`` (×3) › ``mmlu_pro`` (×2) › ``gpqa`` (×1)
    * ``None`` (default): ``aa_intelligence`` (×3) › ``mmlu`` (×2) › ``arena_elo`` (×1)

    Models with no benchmark data at all are sorted after scored models by
    context length descending (largest context first).

    Args:
        models: Candidate free ORModel instances.
        task_type: Optional task hint — ``"coding"``, ``"math"``,
            ``"reasoning"``, or ``None`` for the general-purpose ranking.

    Returns:
        Ranked list of ORModel instances, highest quality first.
    """
    scored: list[tuple[float, int, ORModel]] = []
    unscored: list[ORModel] = []

    for model in models:
        base_id = model.id.removesuffix(":free")
        composite, total_weight = _composite_score(base_id, task_type)
        if total_weight > 0:
            # Negate composite so larger scores sort first
            scored.append((composite, model.context_length, model))
        else:
            unscored.append(model)

    # Sort scored models: highest composite first; break ties by context length
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    # Sort unscored models by context length descending
    unscored.sort(key=lambda m: m.context_length, reverse=True)

    return [t[2] for t in scored] + unscored


def rank_models_for_role(
    models: list[ORModel],
    preferred: list[str] | None = None,
    task_type: str | None = None,
) -> list[ORModel]:
    """Rank free models, using AA benchmark quality data when available.

    When benchmark data exists for at least one candidate model,
    :func:`rank_free_models_by_quality` is used and *preferred* / the built-in
    default list act only as a tiebreaker for models with identical composite
    scores.  When **no** benchmark data is found for any model the function
    falls back to the classic preferred-list-first then context-length approach.

    Args:
        models: Candidate ORModel instances.
        preferred: Ordered list of preferred model IDs.  When ``None`` the
            built-in defaults (``_BUILTIN_PREFERRED``) are used as the
            last-resort fallback (only applied when no benchmark data is
            available).
        task_type: Optional task hint passed to
            :func:`rank_free_models_by_quality` — ``"coding"``, ``"math"``,
            ``"reasoning"``, or ``None`` for general-purpose ranking.

    Returns:
        Ranked list — benchmark-quality ordered when data is available,
        otherwise preferred models first then the remainder by context length
        descending.
    """
    if not models:
        return []

    # Attempt quality-based ranking
    quality_ranked = rank_free_models_by_quality(models, task_type=task_type)

    # Check how many models actually received a benchmark score
    scored_count = sum(
        1 for m in models if _composite_score(m.id.removesuffix(":free"), task_type)[1] > 0
    )

    if scored_count > 0:
        logger.debug(
            "rank_models_for_role: %d/%d models scored via AA benchmarks (task_type=%r)",
            scored_count,
            len(models),
            task_type,
        )
        return quality_ranked

    # ── Fallback: no benchmark data available ────────────────────────────────
    logger.debug(
        "rank_models_for_role: no AA benchmark data found; "
        "using preferred-list + context-length fallback"
    )
    preferred_ids = preferred if preferred is not None else _BUILTIN_PREFERRED
    model_map = {m.id: m for m in models}

    ordered: list[ORModel] = [model_map[pid] for pid in preferred_ids if pid in model_map]
    seen = {m.id for m in ordered}
    rest = sorted(
        (m for m in models if m.id not in seen),
        key=lambda m: m.context_length,
        reverse=True,
    )
    return ordered + rest


# ── Class wrapper ─────────────────────────────────────────────────────────────


class FreeModelTracker:
    """Convenience wrapper for OpenRouter free model discovery.

    Holds credentials and caches the fetched model list in memory for the
    lifetime of the instance so repeated calls within the same session are fast.

    Example::

        tracker = FreeModelTracker(api_key=os.environ.get("OPENROUTER_API_KEY"))
        models = await tracker.refresh()
        best = await tracker.recommend(preferred=["qwen/qwen3-235b-a22b:free"])
    """

    def __init__(
        self,
        api_key: str | None = None,
        cache_path: Path = _DEFAULT_CACHE_PATH,
        cache_ttl: float = _DEFAULT_CACHE_TTL,
    ) -> None:
        """Initialise the tracker.

        Args:
            api_key: OpenRouter API key (improves rate limits).
            cache_path: Where to persist the fetched model list.
            cache_ttl: How long to trust the on-disk cache (seconds).
        """
        self._api_key = api_key
        self._cache_path = cache_path
        self._cache_ttl = cache_ttl
        self._models: list[ORModel] | None = None

    async def refresh(self, *, force: bool = False) -> list[ORModel]:
        """Fetch (or return cached) free model list.

        Args:
            force: When ``True``, bypass cache and make a network request.

        Returns:
            Current list of free ORModel instances.
        """
        self._models = await get_free_models(
            api_key=self._api_key,
            force_refresh=force,
            cache_path=self._cache_path,
            cache_ttl=self._cache_ttl,
        )
        return self._models

    async def recommend(
        self,
        preferred: list[str] | None = None,
        task_type: str | None = None,
    ) -> str | None:
        """Return the best available free model ID.

        When Artificial Analysis benchmark data is available the ranking is
        driven by quality scores for the given *task_type*.  Falls back to the
        built-in preferred list (``_BUILTIN_PREFERRED``) + context-length
        ordering when no benchmark data exists.

        Args:
            preferred: Explicit ordered list of preferred model IDs (highest
                priority first).  Only applied as a last-resort fallback when
                no benchmark data is available.  Falls back to built-in
                defaults when ``None``.
            task_type: Optional task hint — ``"coding"``, ``"math"``,
                ``"reasoning"``, or ``None`` for general-purpose ranking.

        Returns:
            Model ID string (e.g. ``"qwen/qwen3-235b-a22b:free"``), or ``None``
            when no free models are available.
        """
        models = self._models if self._models is not None else await self.refresh()
        ranked = rank_models_for_role(models, preferred=preferred, task_type=task_type)
        return ranked[0].id if ranked else None
