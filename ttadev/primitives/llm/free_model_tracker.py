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

logger = logging.getLogger(__name__)

_OR_MODELS_URL = "https://openrouter.ai/api/v1/models"
_DEFAULT_CACHE_PATH = Path("~/.cache/ttadev/or_free_models.json")
_DEFAULT_CACHE_TTL: float = 7 * 24 * 3600  # 1 week

# Sensible cross-app defaults; callers can override per-role.
_BUILTIN_PREFERRED: list[str] = [
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-235b-a22b:free",
    "deepseek/deepseek-r1:free",
    "mistralai/mistral-7b-instruct:free",
]


@dataclass
class ORModel:
    """Metadata for a single OpenRouter model."""

    id: str
    name: str
    context_length: int
    prompt_price: float
    completion_price: float
    tags: list[str] = field(default_factory=list)

    @property
    def is_free(self) -> bool:
        """Return True when both prompt and completion pricing are zero."""
        return self.prompt_price == 0.0 and self.completion_price == 0.0


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
        models.append(
            ORModel(
                id=m["id"],
                name=m.get("name", m["id"]),
                context_length=int(m.get("context_length") or 4096),
                prompt_price=prompt_price,
                completion_price=completion_price,
            )
        )

    return [m for m in models if m.is_free]


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
        models = [ORModel(**m) for m in raw.get("models", [])]
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


def rank_models_for_role(
    models: list[ORModel],
    preferred: list[str] | None = None,
) -> list[ORModel]:
    """Rank free models with preferred IDs first, then by context length.

    Args:
        models: Candidate ORModel instances.
        preferred: Ordered list of preferred model IDs.  When ``None`` the
            built-in defaults (``_BUILTIN_PREFERRED``) are used.

    Returns:
        Ranked list — preferred models in the order given, then the remainder
        sorted by context length descending.
    """
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
    ) -> str | None:
        """Return the best available free model ID.

        Args:
            preferred: Explicit ordered list of preferred model IDs (highest
                priority first).  Falls back to built-in defaults when ``None``.

        Returns:
            Model ID string (e.g. ``"qwen/qwen3-235b-a22b:free"``), or ``None``
            when no free models are available.
        """
        models = self._models if self._models is not None else await self.refresh()
        ranked = rank_models_for_role(models, preferred=preferred)
        return ranked[0].id if ranked else None
