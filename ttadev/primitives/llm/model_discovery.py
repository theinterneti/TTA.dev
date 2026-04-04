"""Live model discovery for OpenAI-compatible providers.

Queries provider ``/models`` endpoints and caches results so that agents
never need to hard-code model IDs.  When a model 429s, the caller can ask
for the *next* available model without knowing its name in advance.

Supported providers (any that expose an OpenAI-compatible ``/models`` endpoint):

- **Gemini (native)** — ``for_google()`` uses ``/v1beta/models?key=...``
  (non-OpenAI-compat, full authoritative model list)
- **Groq**   — ``https://api.groq.com/openai/v1/models``
- **OpenRouter** — ``https://openrouter.ai/api/v1/models``

Ollama uses a different format (``GET /api/tags``) and is handled separately.

.. note::
    For Gemini, prefer :meth:`ProviderModelDiscovery.for_google` and the
    :func:`best_google_free_model` helper over ``for_provider()``.  The native
    endpoint returns the **full** model list (not the OpenAI-compat subset) and
    uses a ``?key=...`` query-param instead of a Bearer token — matching how
    LiteLLM calls Gemini when the ``gemini/`` prefix is used.

Example::

    discovery = ProviderModelDiscovery()

    # Get an ordered list of Gemini models via the native API (recommended)
    models = await discovery.for_google(api_key=os.environ["GOOGLE_API_KEY"])
    print(models)
    # ['gemini/gemini-flash-lite-latest', 'gemini/gemini-3.1-flash-lite-preview', ...]

    # Get the single best available model (skips exhausted ones)
    best = await best_google_free_model(api_key=os.environ["GOOGLE_API_KEY"])

    # Mark a model as exhausted (429); next call skips it for ttl_seconds
    discovery.mark_exhausted("gemini/gemini-2.5-flash", ttl_seconds=86400)

    # Get next working model (automatically skips exhausted ones)
    model = await discovery.next_working(
        "google",
        base_url="...",
        api_key="...",
    )
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_CACHE_TTL: float = 6 * 3600  # 6 hours — model lists don't change often
_DEFAULT_CACHE_DIR = Path("~/.cache/ttadev/model_discovery")

# Priority ordering hints: prefer aliases (always-latest) then recency.
# Models matching these substrings are sorted to the front.
_GEMINI_PREFER_PATTERNS: list[str] = [
    "flash-lite-latest",  # alias, always tracks best lite
    "flash-latest",  # alias, always tracks best flash
    "3.1-flash-lite",  # gen 3.1 lite (newest, great free quota)
    "3-flash",  # gen 3 flash
    "2.5-flash-lite",  # gen 2.5 lite (newer than 2.0)
    "2.0-flash-lite",  # gen 2.0 lite (known good free tier)
    "2.5-flash",  # gen 2.5 flash
    "2.0-flash",  # gen 2.0 flash
    "3.1-pro",  # gen 3.1 pro
    "3-pro",  # gen 3 pro
    "2.5-pro",  # gen 2.5 pro
]

# Native Google Generative Language API — returns the full authoritative model list.
# Auth uses a ?key=... query param, NOT a Bearer token.
_GOOGLE_NATIVE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


# ── Data structures ───────────────────────────────────────────────────────────


@dataclass
class DiscoveredModel:
    """A model returned by a provider's /models endpoint.

    Attributes:
        id: The model identifier as returned by the provider (e.g.
            ``"models/gemini-2.5-flash"``).
        owned_by: The organization or entity that owns the model.
        created: Unix timestamp when the model was published (0 if unknown).
    """

    id: str
    owned_by: str = ""
    created: int = 0


@dataclass
class _ProviderCache:
    """On-disk cache entry for a single provider's model list."""

    models: list[str] = field(default_factory=list)
    fetched_at: float = 0.0

    def is_fresh(self, ttl: float) -> bool:
        """Return True when the cache was populated within *ttl* seconds."""
        return (time.time() - self.fetched_at) < ttl


# ── Core class ────────────────────────────────────────────────────────────────


class ProviderModelDiscovery:
    """Discover and cache model lists from OpenAI-compatible provider endpoints.

    Maintains two complementary caches:

    1. **Disk cache** — persists across process restarts (JSON files).
    2. **Exhaustion map** — in-memory TTL list of model IDs that returned 429,
       automatically expiring so models become eligible again after their quota
       window resets.

    Args:
        cache_dir: Directory for on-disk JSON caches.  Defaults to
            ``~/.cache/ttadev/model_discovery``.
        cache_ttl: Seconds before a cached model list is considered stale and
            re-fetched from the provider.  Defaults to 6 hours.
    """

    def __init__(
        self,
        cache_dir: Path | str = _DEFAULT_CACHE_DIR,
        cache_ttl: float = _DEFAULT_CACHE_TTL,
    ) -> None:
        self._cache_dir = Path(cache_dir).expanduser()
        self._cache_ttl = cache_ttl
        # provider_name → _ProviderCache (in-memory mirror of disk cache)
        self._mem_cache: dict[str, _ProviderCache] = {}
        # model_id → monotonic expiry time (0 = not exhausted)
        self._exhausted: dict[str, float] = {}

    # ── Public API ────────────────────────────────────────────────────────────

    async def for_provider(
        self,
        provider: str,
        base_url: str,
        api_key: str | None = None,
        *,
        force_refresh: bool = False,
        prefer_patterns: list[str] | None = None,
    ) -> list[str]:
        """Return an ordered list of model IDs available from *provider*.

        Models are ordered so that the most desirable (lowest-cost, highest
        availability) come first.  Callers should iterate the list and stop at
        the first model that succeeds.

        Args:
            provider: Canonical provider name (used as cache key).
            base_url: Root URL of the OpenAI-compatible API (without trailing
                ``/``).  The ``/models`` path is appended automatically.
            api_key: Optional bearer token.  Many providers require this.
            force_refresh: When ``True``, bypass all caches and fetch live.
            prefer_patterns: Optional list of substrings.  Models whose ID
                contains an earlier pattern are sorted to the front of the
                result.  Defaults to built-in patterns for the provider.

        Returns:
            List of model ID strings, best-first.
        """
        cache = self._mem_cache.get(provider)
        if cache and cache.is_fresh(self._cache_ttl) and not force_refresh:
            logger.debug(
                "model_discovery: using memory cache for %s (%d models)",
                provider,
                len(cache.models),
            )
            return cache.models

        disk_cache = self._load_disk_cache(provider)
        if disk_cache and disk_cache.is_fresh(self._cache_ttl) and not force_refresh:
            logger.debug(
                "model_discovery: using disk cache for %s (%d models)",
                provider,
                len(disk_cache.models),
            )
            self._mem_cache[provider] = disk_cache
            return disk_cache.models

        logger.info("model_discovery: fetching live model list for %s", provider)
        try:
            raw = await self._fetch_models(base_url, api_key)
        except Exception as exc:
            logger.warning(
                "model_discovery: failed to fetch models for %s: %s — using cached/fallback",
                provider,
                exc,
            )
            if disk_cache:
                return disk_cache.models
            if cache:
                return cache.models
            return []

        patterns = (
            prefer_patterns
            if prefer_patterns is not None
            else (_GEMINI_PREFER_PATTERNS if provider == "google" else [])
        )
        ordered = _sort_models(raw, patterns)

        entry = _ProviderCache(models=[m.id for m in ordered], fetched_at=time.time())
        self._mem_cache[provider] = entry
        self._save_disk_cache(provider, entry)
        logger.info(
            "model_discovery: discovered %d models for %s",
            len(entry.models),
            provider,
        )
        return entry.models

    def mark_exhausted(self, model_id: str, ttl_seconds: float = 86400.0) -> None:
        """Mark *model_id* as quota-exhausted for *ttl_seconds*.

        Exhausted models are skipped by :meth:`next_working` until the TTL
        expires.

        Args:
            model_id: The model ID that returned 429.
            ttl_seconds: How long to skip this model.  Defaults to 24h —
                the typical daily quota reset window for Gemini free tier.
        """
        deadline = time.monotonic() + ttl_seconds
        self._exhausted[model_id] = deadline
        logger.info(
            "model_discovery: %s marked exhausted for %.0fs",
            model_id,
            ttl_seconds,
        )

    def is_exhausted(self, model_id: str) -> bool:
        """Return ``True`` if *model_id* is currently in the exhaustion window.

        Args:
            model_id: Model ID to check.
        """
        deadline = self._exhausted.get(model_id, 0.0)
        if deadline and time.monotonic() >= deadline:
            # TTL has expired — clear it
            del self._exhausted[model_id]
            return False
        return deadline > 0.0

    async def next_working(
        self,
        provider: str,
        base_url: str,
        api_key: str | None = None,
        *,
        exclude: list[str] | None = None,
    ) -> str | None:
        """Return the next non-exhausted model ID for *provider*.

        Automatically discovers the model list if not already cached, then
        returns the first model that is not exhausted and not in *exclude*.

        Args:
            provider: Canonical provider name.
            base_url: OpenAI-compat root URL.
            api_key: Bearer token for the models endpoint.
            exclude: Additional model IDs to skip (e.g. models that have
                already been attempted in this request).

        Returns:
            The best available model ID, or ``None`` if all models are
            exhausted or excluded.
        """
        models = await self.for_provider(provider, base_url, api_key)
        skip = set(exclude or [])
        for model_id in models:
            if model_id in skip:
                continue
            if self.is_exhausted(model_id):
                continue
            return model_id
        logger.warning("model_discovery: all %s models are exhausted or excluded", provider)
        return None

    def clear_exhausted(self, model_id: str | None = None) -> None:
        """Remove exhaustion status for *model_id* (or all models if ``None``).

        Useful for testing or after a known quota window reset.

        Args:
            model_id: Specific model to un-exhaust, or ``None`` to clear all.
        """
        if model_id is None:
            self._exhausted.clear()
        else:
            self._exhausted.pop(model_id, None)

    async def for_google(
        self,
        api_key: str,
        *,
        force_refresh: bool = False,
    ) -> list[str]:
        """Return an ordered list of Gemini model IDs using the native Google API.

        Unlike ``for_provider()``, this uses Google's non-OpenAI-compat endpoint
        which returns the full authoritative model list and requires a ``?key=...``
        query param instead of a Bearer token.

        Model IDs are returned in LiteLLM ``gemini/`` prefix format (e.g.
        ``"gemini/gemini-3.1-flash-lite-preview"``) ready to pass to LiteLLM or
        OpenHands.

        Args:
            api_key: Google AI Studio API key.
            force_refresh: Bypass cache and fetch live.

        Returns:
            Priority-ordered list of model IDs (best free/lite models first).
        """
        cache_key = "google-native"
        cache = self._mem_cache.get(cache_key)
        if cache and cache.is_fresh(self._cache_ttl) and not force_refresh:
            return cache.models

        disk_cache = self._load_disk_cache(cache_key)
        if disk_cache and disk_cache.is_fresh(self._cache_ttl) and not force_refresh:
            self._mem_cache[cache_key] = disk_cache
            return disk_cache.models

        logger.info("model_discovery: fetching live Google native model list")
        try:
            raw = await self._fetch_google_native_models(api_key)
        except Exception as exc:
            logger.warning(
                "model_discovery: failed to fetch Google native models: %s — using cached/fallback",
                exc,
            )
            if disk_cache:
                return disk_cache.models
            if cache:
                return cache.models
            return []

        ordered = _sort_models(raw, _GEMINI_PREFER_PATTERNS)
        entry = _ProviderCache(models=[m.id for m in ordered], fetched_at=time.time())
        self._mem_cache[cache_key] = entry
        self._save_disk_cache(cache_key, entry)
        logger.info("model_discovery: discovered %d Google models", len(entry.models))
        return entry.models

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _fetch_models(
        self,
        base_url: str,
        api_key: str | None,
    ) -> list[DiscoveredModel]:
        """Hit *base_url*/models and return the parsed model list.

        Args:
            base_url: Provider API root (e.g. ``https://…/v1beta/openai``).
            api_key: Optional bearer token.

        Returns:
            List of :class:`DiscoveredModel` instances.

        Raises:
            httpx.HTTPStatusError: On non-2xx response.
            httpx.TimeoutException: On timeout.
        """
        url = base_url.rstrip("/") + "/models"
        headers: dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()

        results: list[DiscoveredModel] = []
        for entry in data.get("data", []):
            model_id = entry.get("id", "")
            if not model_id:
                continue
            results.append(
                DiscoveredModel(
                    id=model_id,
                    owned_by=entry.get("owned_by", ""),
                    created=int(entry.get("created") or 0),
                )
            )
        return results

    async def _fetch_google_native_models(self, api_key: str) -> list[DiscoveredModel]:
        """Fetch models from Google's native (non-OpenAI-compat) endpoint.

        Uses ``GET https://generativelanguage.googleapis.com/v1beta/models?key=...``
        which is the authoritative full model list, not the OpenAI-compat shim.
        Filters to models supporting ``generateContent`` (text generation).
        Returns IDs in ``gemini/`` LiteLLM prefix format.

        Args:
            api_key: Google AI Studio API key.

        Returns:
            List of :class:`DiscoveredModel` with IDs as ``gemini/<model-name>``.
        """
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(_GOOGLE_NATIVE_URL, params={"key": api_key})
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()

        results: list[DiscoveredModel] = []
        for m in data.get("models", []):
            name = m.get("name", "")  # e.g. "models/gemini-3.1-flash-lite-preview"
            if not name.startswith("models/gemini"):
                continue
            # Must support generateContent for text generation
            if "generateContent" not in m.get("supportedGenerationMethods", []):
                continue
            # Convert to LiteLLM format: "models/gemini-X" → "gemini/gemini-X"
            model_id = "gemini/" + name.removeprefix("models/")
            results.append(DiscoveredModel(id=model_id, owned_by="google", created=0))
        return results

    def _cache_path(self, provider: str) -> Path:
        return self._cache_dir / f"{provider}.json"

    def _load_disk_cache(self, provider: str) -> _ProviderCache | None:
        path = self._cache_path(provider)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return _ProviderCache(
                models=data.get("models", []),
                fetched_at=float(data.get("fetched_at", 0)),
            )
        except Exception as exc:
            logger.debug("model_discovery: could not read disk cache %s: %s", path, exc)
            return None

    def _save_disk_cache(self, provider: str, entry: _ProviderCache) -> None:
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            path = self._cache_path(provider)
            path.write_text(
                json.dumps({"models": entry.models, "fetched_at": entry.fetched_at}, indent=2)
            )
        except Exception as exc:
            logger.debug("model_discovery: could not write disk cache: %s", exc)


# ── Sorting helpers ───────────────────────────────────────────────────────────


def _sort_models(
    models: list[DiscoveredModel],
    prefer_patterns: list[str],
) -> list[DiscoveredModel]:
    """Sort *models* so that the most desirable come first.

    Priority rules (applied in order):

    1. Models whose ID contains an earlier pattern in *prefer_patterns* rank
       higher.
    2. Within the same pattern tier, lexicographically newer (higher version)
       model IDs rank higher.

    Args:
        models: Unsorted list from the provider.
        prefer_patterns: Ordered preference hints (substrings of model IDs).

    Returns:
        Sorted copy of *models*, best first.
    """

    def _rank(model: DiscoveredModel) -> tuple[int, str]:
        model_id = model.id.lower()
        for idx, pattern in enumerate(prefer_patterns):
            if pattern.lower() in model_id:
                return (idx, model_id)
        # No preference match → push to the end, sorted lexicographically
        return (len(prefer_patterns), model_id)

    return sorted(models, key=_rank)


# ── Module-level singleton ────────────────────────────────────────────────────

#: Shared instance — importers can use this directly without constructing their own.
default_discovery = ProviderModelDiscovery()


async def best_google_free_model(
    api_key: str,
    *,
    exclude: list[str] | None = None,
    discovery: ProviderModelDiscovery | None = None,
) -> str | None:
    """Return the best available non-exhausted Gemini model ID for LiteLLM.

    Uses the native Google API (not the OpenAI-compat shim) for an accurate,
    up-to-date model list.  Returns model IDs in ``gemini/`` prefix format.

    Args:
        api_key: Google AI Studio API key.
        exclude: Model IDs to skip (e.g. ones that just returned 429).
        discovery: Optional :class:`ProviderModelDiscovery` instance; uses the
            module-level :data:`default_discovery` singleton when not provided.

    Returns:
        Best available model ID (e.g. ``"gemini/gemini-flash-lite-latest"``),
        or ``None`` if all models are exhausted or the API is unreachable.
    """
    disc = discovery or default_discovery
    models = await disc.for_google(api_key)
    skip = set(exclude or [])
    for model_id in models:
        if model_id in skip:
            continue
        if disc.is_exhausted(model_id):
            continue
        return model_id
    logger.warning("best_google_free_model: all Google models are exhausted or excluded")
    return None
