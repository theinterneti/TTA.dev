"""ModelRouterPrimitive — YAML-configurable multi-tier LLM routing.

Routes LLM requests to the best available provider using an ordered tier list.
Typical tier order: **local Ollama → Groq (fast) → pinned free cloud model → any free model**.
On failure the primitive falls through to the next tier; all tiers failing
raises ``RuntimeError``.

The routing table is driven by a YAML file or plain Python dicts, making it
trivial to adapt for any application without changing code.

Supported providers
-------------------

+---------------+-------------------------------+------------------------------+
| Value         | API                           | Auth env var                 |
+===============+===============================+==============================+
| ``ollama``    | Local Ollama (localhost)      | *(none)*                     |
+---------------+-------------------------------+------------------------------+
| ``groq``      | Groq cloud (OpenAI-compat)    | ``GROQ_API_KEY``             |
+---------------+-------------------------------+------------------------------+
| ``together``  | Together AI (OpenAI-compat)   | ``TOGETHER_API_KEY``         |
+---------------+-------------------------------+------------------------------+
| ``openrouter``| OpenRouter (OpenAI-compat)    | ``OPENROUTER_API_KEY``       |
| / ``or``      |                               |                              |
+---------------+-------------------------------+------------------------------+
| ``auto``      | FreeModelTracker → OpenRouter | ``OPENROUTER_API_KEY``       |
+---------------+-------------------------------+------------------------------+

Example (Python)::

    modes = {
        "chat": RouterModeConfig(
            tiers=[
                RouterTierConfig(provider="ollama", model="llama3.2"),
                RouterTierConfig(provider="groq", model="llama-3.1-8b-instant"),
                RouterTierConfig(provider="openrouter", model="meta-llama/llama-3.3-70b-instruct:free"),
                RouterTierConfig(provider="auto"),
            ]
        )
    }
    router = ModelRouterPrimitive(modes)
    response = await router.execute(
        ModelRouterRequest(mode="chat", prompt="Hello!"),
        WorkflowContext(workflow_id="demo"),
    )

Example YAML (``model_modes.yaml``)::

    modes:
      narration:
        description: "Generate narrative prose"
        tier1:
          provider: ollama
          model: llama3.2
          params:
            temperature: 0.8
        tier2:
          provider: groq
          model: llama-3.3-70b-versatile
          params:
            temperature: 0.8
            max_tokens: 512
        tier3:
          provider: openrouter
          model: "nousresearch/hermes-3-llama-3.1-405b:free"
          params:
            temperature: 0.8
            max_tokens: 512
        tier4:
          provider: auto
          params:
            temperature: 0.8
            max_tokens: 512
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from ttadev.primitives.core import WorkflowContext, WorkflowPrimitive
from ttadev.primitives.llm.free_model_tracker import FreeModelTracker
from ttadev.primitives.llm.model_discovery import ProviderModelDiscovery
from ttadev.primitives.llm.providers import PROVIDERS
from ttadev.primitives.llm.task_selector import (
    TaskProfile,
    _extract_param_size_b,
    min_ollama_params_for_complexity,
    rank_models_for_task,
)
from ttadev.primitives.llm.universal_llm_primitive import LLMResponse

logger = logging.getLogger(__name__)

# URL and credential constants sourced from the central provider registry.
_OLLAMA_DEFAULT_URL = PROVIDERS["ollama"].base_url.removesuffix("/v1")
_GROQ_API_URL = f"{PROVIDERS['groq'].base_url}/chat/completions"
_TOGETHER_API_URL = f"{PROVIDERS['together'].base_url}/chat/completions"
_OPENROUTER_API_URL = f"{PROVIDERS['openrouter'].base_url}/chat/completions"
_GOOGLE_API_URL = f"{PROVIDERS['google'].base_url}/chat/completions"

# Regex to strip <think>...</think> reasoning tokens emitted by some models
# (e.g. qwen-qwen3-32b, deepseek-r1).  Applied per-tier when strip_thinking=True.
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)

# Well-known free Groq models (fast inference, generous free tier)
_GROQ_FREE_MODELS: list[str] = [
    "llama-3.1-8b-instant",  # fast, low-latency
    "llama-3.3-70b-versatile",  # high-quality, reliable
    "meta-llama/llama-4-scout-17b-16e-instruct",  # Llama 4 Scout MoE (fast + capable)
    "qwen/qwen3-32b",  # strong coding + reasoning
    "openai/gpt-oss-20b",  # OpenAI OSS
    "moonshotai/kimi-k2-instruct",  # Moonshot K2 (long-context)
]

# Substrings that identify non-chat Groq models to exclude during live discovery.
_GROQ_NON_CHAT_PATTERNS: tuple[str, ...] = (
    "whisper",
    "orpheus",
    "allam",
    "guard",
    "safeguard",
)


# ── Configuration dataclasses ─────────────────────────────────────────────────


@dataclass
class RouterTierConfig:
    """Configuration for a single routing tier.

    Attributes:
        provider: Which provider to use.  One of ``"ollama"``, ``"groq"``,
            ``"together"``, ``"openrouter"``/``"or"``, ``"google"``, or
            ``"auto"`` (auto-selected free model via FreeModelTracker →
            OpenRouter).
        model: Primary model identifier.  When *models* is also set, this is
            tried first.  ``None``/``"auto"`` lets dynamic discovery or
            FreeModelTracker choose.  Required when ``provider == "ollama"``.
        models: Ordered fallback list of model IDs to try within this tier.
            If set, the tier will cycle through all entries before giving up,
            so a single 429 on the first model doesn't fail the tier entirely.
            When empty, only *model* (or the provider default) is used.
            Example for Gemini::

                RouterTierConfig(
                    provider="google",
                    models=[
                        "models/gemini-flash-lite-latest",
                        "models/gemini-3.1-flash-lite-preview",
                        "models/gemini-2.0-flash-lite",
                    ],
                )
        params: Extra generation parameters forwarded to the provider
            (e.g. ``temperature``, ``max_tokens``).
        strip_thinking: When ``True`` (default), strip ``<think>…</think>``
            blocks from the model response before returning.  Safe no-op on
            models that don't emit reasoning tokens.
    """

    provider: str
    model: str | None = None
    models: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    strip_thinking: bool = True


@dataclass
class RouterModeConfig:
    """Configuration for a named routing mode.

    Attributes:
        description: Human-readable description of the mode.
        tiers: Ordered list of tiers to try.
    """

    description: str = ""
    tiers: list[RouterTierConfig] = field(default_factory=list)


@dataclass
class ModelRouterRequest:
    """Request for the ModelRouterPrimitive.

    Attributes:
        mode: Name of the routing mode to use (must be in the configured modes).
        prompt: User or assistant prompt text.
        system: Optional system message prepended to the conversation.
        tier_override: If set (1-based index), skip directly to that tier and
            don't fall through.  Useful for testing or forcing a specific provider.
        task_profile: Optional :class:`~ttadev.primitives.llm.task_selector.TaskProfile`
            describing the task type and complexity.  When provided, candidate
            models within each tier are ranked by benchmark suitability, and
            Ollama models that are too small for the requested complexity are
            skipped automatically.
    """

    mode: str
    prompt: str
    system: str | None = None
    tier_override: int | None = None
    task_profile: TaskProfile | None = None


# ── Primitive ─────────────────────────────────────────────────────────────────


class ModelRouterPrimitive(WorkflowPrimitive[ModelRouterRequest, LLMResponse]):
    """Routes LLM requests through a configurable tier of providers.

    Each named *mode* has an ordered list of tiers.  On failure the primitive
    logs a warning and falls through to the next tier; it raises ``RuntimeError``
    only when every tier has been exhausted.

    **Provider values:**

    - ``"ollama"``      — local Ollama (requires ``model`` to be set)
    - ``"groq"``        — Groq cloud, OpenAI-compat (``GROQ_API_KEY``)
    - ``"together"``    — Together AI, OpenAI-compat (``TOGETHER_API_KEY``)
    - ``"openrouter"``  — OpenRouter (pinned model or auto-selected free)
    - ``"google"``      — Google (Gemini/Gemma), OpenAI-compat, OpenAI-compat (``GOOGLE_API_KEY``)
    - ``"auto"``        — ``FreeModelTracker`` picks the best free OpenRouter model
    """

    def __init__(
        self,
        modes: dict[str, RouterModeConfig],
        *,
        free_tracker: FreeModelTracker | None = None,
        ollama_url: str | None = None,
        openrouter_api_key: str | None = None,
        groq_api_key: str | None = None,
        together_api_key: str | None = None,
        google_api_key: str | None = None,
        tier_cooldown_seconds: int = 30,
    ) -> None:
        """Initialise the router.

        Args:
            modes: Mapping from mode name to ``RouterModeConfig``.
            free_tracker: Optional pre-configured tracker.  A default instance
                (keyed from the env) is created when ``None``.
            ollama_url: Ollama base URL.  Defaults to ``OLLAMA_URL`` env var or
                ``http://localhost:11434``.
            openrouter_api_key: OpenRouter key.  Defaults to
                ``OPENROUTER_API_KEY`` env var.
            groq_api_key: Groq API key.  Defaults to ``GROQ_API_KEY`` env var.
            together_api_key: Together AI key.  Defaults to
                ``TOGETHER_API_KEY`` env var.
            google_api_key: Google API key for Gemini.  Defaults to
                ``GOOGLE_API_KEY`` env var.
            tier_cooldown_seconds: Seconds to skip a tier after it returns a
                429 rate-limit response.  Set to ``0`` to disable cooldown
                (backward compatible).
        """
        super().__init__()
        self._modes = modes
        self._or_api_key = openrouter_api_key or os.getenv(PROVIDERS["openrouter"].env_var, "")
        self._groq_api_key = groq_api_key or os.getenv(PROVIDERS["groq"].env_var, "")
        self._together_api_key = together_api_key or os.getenv(PROVIDERS["together"].env_var, "")
        self._google_api_key = google_api_key or os.getenv(PROVIDERS["google"].env_var, "")
        self._ollama_url = (ollama_url or os.getenv("OLLAMA_URL", _OLLAMA_DEFAULT_URL)).rstrip("/")
        self._tracker = free_tracker or FreeModelTracker(api_key=self._or_api_key or None)
        self._discovery = ProviderModelDiscovery()
        self._tier_cooldown_seconds = tier_cooldown_seconds
        # Instance-level cooldown state: tier_key → monotonic deadline
        self._tier_cooldowns: dict[str, float] = {}
        self._cooldown_lock: asyncio.Lock = asyncio.Lock()

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_yaml(
        cls,
        path: Path | str,
        **kwargs: Any,
    ) -> ModelRouterPrimitive:
        """Create a ``ModelRouterPrimitive`` from a YAML configuration file.

        The YAML ``modes`` block maps mode names to tier configs.  Each tier
        key is ``tier1``, ``tier2``, … (numeric suffix determines order).

        Example YAML::

            modes:
              extraction:
                description: "Extract structured data"
                tier1:
                  provider: ollama
                  model: qwen2.5:7b
                  params:
                    temperature: 0.1
                tier2:
                  provider: openrouter
                  model: "mistralai/mistral-7b-instruct:free"
                  params:
                    temperature: 0.1
                    max_tokens: 256
                tier3:
                  provider: auto
                  params:
                    temperature: 0.1
                    max_tokens: 256

        Args:
            path: Path to YAML configuration file.
            **kwargs: Additional keyword arguments forwarded to ``__init__``.

        Returns:
            Configured ``ModelRouterPrimitive`` instance.
        """
        import yaml  # PyYAML — already a core dependency

        loaded = yaml.safe_load(Path(path).read_text())
        raw: dict[str, Any] = loaded if isinstance(loaded, dict) else {}
        modes: dict[str, RouterModeConfig] = {}

        for mode_name, mode_data in raw.get("modes", {}).items():
            tiers: list[RouterTierConfig] = []
            for i in range(1, 20):
                tier_key = f"tier{i}"
                if tier_key not in mode_data:
                    break
                td: dict[str, Any] = mode_data[tier_key]
                model_raw = td.get("model")
                model = None if (model_raw in (None, "null", "auto", "")) else str(model_raw)
                tiers.append(
                    RouterTierConfig(
                        provider=str(td.get("provider", "openrouter")),
                        model=model,
                        params=dict(td.get("params", {})),
                    )
                )
            modes[mode_name] = RouterModeConfig(
                description=str(mode_data.get("description", "")),
                tiers=tiers,
            )

        return cls(modes=modes, **kwargs)

    # ── WorkflowPrimitive interface ───────────────────────────────────────────

    async def execute(
        self,
        request: ModelRouterRequest,
        ctx: WorkflowContext,
    ) -> LLMResponse:
        """Route the request to the best available tier.

        Iterates through tiers for the requested mode, trying each in order.
        Logs a warning on per-tier failure and continues to the next tier.

        Args:
            request: Mode name, prompt text, and optional system message.
            ctx: Workflow context for observability.

        Returns:
            ``LLMResponse`` from the first tier that succeeds.

        Raises:
            ValueError: If the requested mode is not configured.
            RuntimeError: If every configured tier fails.
        """
        mode_cfg = self._modes.get(request.mode)
        if mode_cfg is None:
            available = sorted(self._modes)
            raise ValueError(f"Unknown routing mode {request.mode!r}. Available: {available}")

        if request.tier_override is not None:
            idx = request.tier_override - 1
            if idx < 0 or idx >= len(mode_cfg.tiers):
                raise ValueError(
                    f"tier_override={request.tier_override} out of range for mode "
                    f"{request.mode!r} (has {len(mode_cfg.tiers)} tier(s))"
                )
            tiers_to_try = [mode_cfg.tiers[idx]]
        else:
            tiers_to_try = mode_cfg.tiers

        last_exc: Exception = RuntimeError("No tiers configured")
        for i, tier in enumerate(tiers_to_try, start=1):
            tier_key = f"{tier.provider}/{tier.model or 'auto'}"
            if self._is_cooling(tier_key):
                logger.debug(
                    "tier%d (%s) is in cooldown, skipping",
                    i,
                    tier_key,
                )
                last_exc = RuntimeError(f"tier{i} ({tier_key}) is cooling down after 429")
                continue
            try:
                content, used_model = await self._call_tier(
                    tier, request.prompt, request.system, request.task_profile
                )
                if tier.strip_thinking:
                    content = _THINK_RE.sub("", content).strip()
                # Langfuse router-tier annotation (optional — fails silently)
                try:
                    from tta_apm_langfuse import get_integration  # noqa: PLC0415

                    _lf = get_integration()
                    if _lf is not None and _lf.client is not None:
                        _lf.client.update_current_observation(
                            metadata={
                                "router.selected_tier": tier_key,
                                "router.model_id": used_model,
                                "router.fallback": i > 1,
                            }
                        )
                except Exception:
                    pass
                return LLMResponse(
                    content=content,
                    model=used_model,
                    provider=tier.provider,
                )
            except Exception as exc:
                cause = exc.__cause__
                is_429 = (
                    isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 429
                ) or (
                    isinstance(cause, httpx.HTTPStatusError) and cause.response.status_code == 429
                )
                if is_429:
                    self._mark_cooling(tier_key)
                last_exc = exc
                logger.warning(
                    "tier%d (%s / %s) failed: %r — trying next tier",
                    i,
                    tier.provider,
                    tier.model or "auto",
                    exc,
                )

        raise RuntimeError(
            f"All {len(tiers_to_try)} tiers failed for mode {request.mode!r}"
        ) from last_exc

    # ── Cooldown helpers ──────────────────────────────────────────────────────

    def _is_cooling(self, tier_key: str) -> bool:
        """Return ``True`` if *tier_key* is within its rate-limit cooldown window.

        Args:
            tier_key: Canonical key ``"provider/model"`` for the tier.

        Returns:
            ``True`` when the tier should be skipped; ``False`` otherwise.
        """
        if self._tier_cooldown_seconds == 0:
            return False
        deadline = self._tier_cooldowns.get(tier_key, 0.0)
        return time.monotonic() < deadline

    def _mark_cooling(self, tier_key: str) -> None:
        """Record that *tier_key* received a 429 and should be skipped temporarily.

        Args:
            tier_key: Canonical key ``"provider/model"`` for the tier.
        """
        if self._tier_cooldown_seconds == 0:
            return
        self._tier_cooldowns[tier_key] = time.monotonic() + self._tier_cooldown_seconds

    # ── Tier dispatch ─────────────────────────────────────────────────────────

    async def _call_tier(
        self,
        tier: RouterTierConfig,
        prompt: str,
        system: str | None,
        task_profile: TaskProfile | None = None,
    ) -> tuple[str, str]:
        """Dispatch to the appropriate provider for a single tier.

        When the tier has multiple models (via the ``models`` list), they are
        tried in order.  A 429 on one model marks it exhausted in
        :class:`~ttadev.primitives.llm.model_discovery.ProviderModelDiscovery`
        and causes the next model to be tried before the tier fails.  This means
        a caller never needs to know about specific model names — the tier
        self-heals around quota limits.

        When *task_profile* is provided, multi-candidate tiers (Groq, Gemini) are
        ranked by benchmark suitability before being passed to
        :meth:`_try_model_candidates`.  Ollama models that are too small for the
        requested complexity are skipped (raises ``RuntimeError`` so the caller
        can fall through to the next tier).

        Args:
            tier: Tier configuration.
            prompt: User prompt text.
            system: Optional system message.
            task_profile: Optional task profile for task-aware ranking.

        Returns:
            Tuple of ``(content, model_id)``.

        Raises:
            ValueError: For unknown provider or missing Ollama model.
            RuntimeError: When all models in the tier are exhausted/failed,
                or when an Ollama model is too small for the requested complexity.
        """
        provider = tier.provider.lower().strip()

        if provider == "ollama":
            if not tier.model:
                raise ValueError("Ollama tier requires an explicit 'model' name")
            # Skip if too small for requested complexity.
            if task_profile is not None:
                min_params = min_ollama_params_for_complexity(task_profile.complexity)
                if min_params is not None:
                    actual = _extract_param_size_b(tier.model)
                    if actual is not None and actual < min_params:
                        raise RuntimeError(
                            f"Ollama model {tier.model!r} has {actual}B params, "
                            f"but complexity={task_profile.complexity!r} requires "
                            f">={min_params}B — skipping to next tier"
                        )
            content = await self._call_ollama(tier.model, prompt, system, tier.params)
            return content, tier.model

        if provider == "groq":
            if tier.models:
                candidates = tier.models
            elif tier.model:
                candidates = [tier.model]
            else:
                # No model specified — discover live from the provider endpoint,
                # falling back to the curated free-model list if discovery fails.
                discovered = await self._discovery.for_provider(
                    "groq",
                    base_url=PROVIDERS["groq"].base_url,
                    api_key=self._groq_api_key or None,
                )
                # Filter out non-chat models (Whisper, Orpheus TTS, guard models, etc.)
                discovered = [
                    m
                    for m in discovered
                    if not any(pat in m.lower() for pat in _GROQ_NON_CHAT_PATTERNS)
                ]
                candidates = discovered or _GROQ_FREE_MODELS
            if task_profile is not None:
                candidates = rank_models_for_task(candidates, task_profile)
            return await self._try_model_candidates(
                candidates, _GROQ_API_URL, self._groq_api_key, prompt, system, tier.params
            )

        if provider == "together":
            if not tier.model and not tier.models:
                raise ValueError("Together AI tier requires an explicit 'model' name")
            candidates = tier.models or ([tier.model] if tier.model else [])
            return await self._try_model_candidates(
                candidates, _TOGETHER_API_URL, self._together_api_key, prompt, system, tier.params
            )

        if provider in ("openrouter", "or"):
            if tier.models:
                return await self._try_model_candidates(
                    tier.models,
                    _OPENROUTER_API_URL,
                    self._or_api_key,
                    prompt,
                    system,
                    tier.params,
                    extra_headers=PROVIDERS["openrouter"].extra_headers,
                )
            model = tier.model or await self._tracker.recommend()
            if not model:
                raise RuntimeError("FreeModelTracker returned no candidate models")
            content = await self._call_openai_compat(
                _OPENROUTER_API_URL,
                self._or_api_key,
                model,
                prompt,
                system,
                tier.params,
                extra_headers=PROVIDERS["openrouter"].extra_headers,
            )
            return content, model

        if provider == "auto":
            model = await self._tracker.recommend()
            if not model:
                raise RuntimeError("FreeModelTracker returned no candidate models")
            content = await self._call_openai_compat(
                _OPENROUTER_API_URL,
                self._or_api_key,
                model,
                prompt,
                system,
                tier.params,
                extra_headers=PROVIDERS["openrouter"].extra_headers,
            )
            return content, model

        if provider == "google":
            # Build candidate list: explicit > discovered > provider default.
            if tier.models:
                candidates = tier.models
            elif tier.model:
                candidates = [tier.model]
            else:
                # No model specified — discover live from the provider endpoint.
                discovered = await self._discovery.for_provider(
                    "google",
                    base_url=PROVIDERS["google"].base_url,
                    api_key=self._google_api_key or None,
                )
                candidates = discovered or [PROVIDERS["google"].default_model]

            # Ensure every candidate has the required `models/` prefix.
            candidates = [m if m.startswith("models/") else f"models/{m}" for m in candidates]
            if task_profile is not None:
                candidates = rank_models_for_task(candidates, task_profile)
            return await self._try_model_candidates(
                candidates,
                _GOOGLE_API_URL,
                self._google_api_key,
                prompt,
                system,
                tier.params,
                discovery_provider="google",
            )

        raise ValueError(
            f"Unknown provider {provider!r}. "
            "Use 'ollama', 'groq', 'together', 'openrouter', 'google', or 'auto'"
        )

    async def _try_model_candidates(
        self,
        candidates: list[str],
        api_url: str,
        api_key: str,
        prompt: str,
        system: str | None,
        params: dict[str, Any],
        *,
        extra_headers: dict[str, str] | None = None,
        discovery_provider: str | None = None,
    ) -> tuple[str, str]:
        """Try each model in *candidates* until one succeeds.

        On HTTP 429, the model is marked exhausted in
        :class:`~ttadev.primitives.llm.model_discovery.ProviderModelDiscovery`
        so subsequent calls in the same session skip it automatically.

        Args:
            candidates: Ordered list of model IDs to attempt.
            api_url: OpenAI-compat chat completions endpoint.
            api_key: Bearer token.
            prompt: User message.
            system: Optional system message.
            params: Extra generation parameters.
            extra_headers: Additional HTTP headers.
            discovery_provider: When set, 429 failures are recorded in
                :attr:`_discovery` for this provider name.

        Returns:
            Tuple of ``(content, model_id)`` for the first successful model.

        Raises:
            RuntimeError: When every candidate fails.
        """
        last_exc: Exception = RuntimeError("No model candidates provided")
        all_were_429 = True
        last_429_exc: httpx.HTTPStatusError | None = None
        for model_id in candidates:
            if discovery_provider and self._discovery.is_exhausted(model_id):
                logger.debug("model_discovery: skipping exhausted %s", model_id)
                continue
            try:
                content = await self._call_openai_compat(
                    api_url,
                    api_key,
                    model_id,
                    prompt,
                    system,
                    params,
                    extra_headers=extra_headers,
                )
                return content, model_id
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 429:
                    if discovery_provider:
                        self._discovery.mark_exhausted(model_id)
                    last_429_exc = exc
                else:
                    all_were_429 = False
                logger.warning(
                    "model candidate %s returned HTTP %d — trying next",
                    model_id,
                    status,
                )
                last_exc = exc
            except Exception as exc:
                all_were_429 = False
                logger.warning("model candidate %s failed: %r — trying next", model_id, exc)
                last_exc = exc

        # When every failure was a 429, chain the original HTTPStatusError so the
        # tier-level cooldown logic in `execute` can detect it via __cause__.
        if all_were_429 and last_429_exc is not None:
            raise RuntimeError(f"All {len(candidates)} model candidate(s) failed") from last_429_exc

        raise RuntimeError(f"All {len(candidates)} model candidate(s) failed") from last_exc

    # ── Provider calls ────────────────────────────────────────────────────────

    async def _call_ollama(
        self,
        model: str,
        prompt: str,
        system: str | None,
        params: dict[str, Any],
    ) -> str:
        """Call a local Ollama endpoint.

        Args:
            model: Ollama model identifier.
            prompt: User message.
            system: Optional system message.
            params: Extra generation options (temperature, etc.).

        Returns:
            Generated text content.
        """
        messages = _build_messages(prompt, system)
        payload: dict[str, Any] = {"model": model, "messages": messages, "stream": False}
        if params:
            payload["options"] = params
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{self._ollama_url}/api/chat", json=payload)
            resp.raise_for_status()
            return str(resp.json()["message"]["content"])

    async def _call_openai_compat(
        self,
        api_url: str,
        api_key: str,
        model: str,
        prompt: str,
        system: str | None,
        params: dict[str, Any],
        *,
        extra_headers: dict[str, str] | None = None,
    ) -> str:
        """Call any OpenAI-compatible chat completions endpoint.

        Used by Groq, Together AI, and OpenRouter — all share the same
        ``/chat/completions`` request/response format.

        Args:
            api_url: Full URL of the chat completions endpoint.
            api_key: Bearer token for Authorization header.
            model: Model identifier for the provider.
            prompt: User message.
            system: Optional system message.
            params: Extra generation parameters (temperature, max_tokens, etc.).
            extra_headers: Additional HTTP headers (e.g. HTTP-Referer for OR).

        Returns:
            Generated text content.
        """
        messages = _build_messages(prompt, system)
        headers = {"Authorization": f"Bearer {api_key}"}
        if extra_headers:
            headers.update(extra_headers)
        payload: dict[str, Any] = {"model": model, "messages": messages, **params}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(api_url, headers=headers, json=payload)
            resp.raise_for_status()
            return str(resp.json()["choices"][0]["message"]["content"])

    # ── Utility ───────────────────────────────────────────────────────────────

    @property
    def modes(self) -> dict[str, RouterModeConfig]:
        """Return the configured routing modes (read-only view)."""
        return dict(self._modes)


# ── Private helpers ───────────────────────────────────────────────────────────


def _build_messages(prompt: str, system: str | None) -> list[dict[str, str]]:
    """Build an OpenAI-compatible messages list.

    Args:
        prompt: User turn content.
        system: Optional system instruction prepended before the user turn.

    Returns:
        List of ``{role, content}`` dicts.
    """
    msgs: list[dict[str, str]] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return msgs
