"""SmartRouterPrimitive — zero-config best-available-model router.

Builds a :class:`LiteLLMSmartAdapter` that cascades through available free
providers in quality order, using :class:`~ttadev.primitives.llm.litellm_primitive.LiteLLMPrimitive`
as the execution backend:

1. **Groq** — fastest inference, generous free tier (GROQ_API_KEY)
2. **Google Gemini** — reliable free tier (GOOGLE_API_KEY)
3. **OpenRouter** — aggregator with many free model options (OPENROUTER_API_KEY)
4. **Ollama** — local fallback, no API key required

Each tier is included only when the corresponding API key env var is set (or
for Ollama, always included as last resort).  The returned adapter plugs into
any component that accepts a ``ModelRouterPrimitive``-compatible object (i.e.
exposes ``execute(ModelRouterRequest, ctx) -> LLMResponse`` and a ``modes``
attribute).

Usage::

    from ttadev.primitives.llm.smart_router import SmartRouterPrimitive

    router = SmartRouterPrimitive.build()
    # Wrap in adapter for ChatPrimitive protocol:
    from ttadev.agents.adapter import ModelRouterChatAdapter
    model = ModelRouterChatAdapter(SmartRouterPrimitive.build())

    # Or use directly in AgentRouterPrimitive (auto-wired when model=None):
    from ttadev.agents.router import AgentRouterPrimitive
    router_prim = AgentRouterPrimitive()  # SmartRouter is the default

Attribution:
    Model benchmark data sourced from Artificial Analysis (https://artificialanalysis.ai).
"""

from __future__ import annotations

import os
import re
from typing import Any

from ttadev.primitives.core import WorkflowContext, WorkflowPrimitive
from ttadev.primitives.llm.litellm_primitive import LiteLLMPrimitive
from ttadev.primitives.llm.model_router import (
    ModelRouterRequest,
    RouterModeConfig,
    RouterTierConfig,
)
from ttadev.primitives.llm.universal_llm_primitive import LLMRequest, LLMResponse

__all__ = ["LiteLLMSmartAdapter", "SmartRouterPrimitive"]

# OpenRouter free model — high capability, cost $0.
_OR_FREE_MODEL = "google/gemma-3-27b-it:free"

# Best free Groq model for general-purpose tasks (quality/speed balance).
_GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"

# Default models per provider in litellm model-string format.
_PROVIDER_DEFAULT_MODELS: dict[str, str] = {
    "groq": f"groq/{_GROQ_DEFAULT_MODEL}",
    "google": "gemini/gemini-2.0-flash-lite",
    "openrouter": f"openrouter/{_OR_FREE_MODEL}",
    "ollama": "ollama/qwen2.5:7b",
}

# Regex to strip <think>...</think> reasoning tokens.
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _tier_to_litellm_model(tier: RouterTierConfig) -> str | None:
    """Translate a :class:`RouterTierConfig` to a litellm model string.

    Maps the tier's ``provider`` and optional ``model`` to the
    ``"<provider>/<model>"`` format that litellm expects.

    Args:
        tier: A single routing tier configuration.

    Returns:
        A litellm model string (e.g. ``"groq/llama-3.3-70b-versatile"``), or
        ``None`` when the provider is unrecognised and no model is specified.
    """
    provider = tier.provider.lower()

    if tier.model:
        model = tier.model
        # model may already be a full litellm string for openrouter slugs like
        # "google/gemma-3-27b-it:free" — prepend provider prefix only when
        # the provider prefix is not already present.
        if provider == "openrouter" and not model.startswith("openrouter/"):
            return f"openrouter/{model}"
        if provider == "groq" and not model.startswith("groq/"):
            return f"groq/{model}"
        if provider in {"google", "gemini"} and not model.startswith(("gemini/", "google/")):
            return f"gemini/{model}"
        if provider == "ollama" and not model.startswith("ollama/"):
            return f"ollama/{model}"
        # Return as-is when already a full model string.
        return model

    # No explicit model — use provider defaults.
    return _PROVIDER_DEFAULT_MODELS.get(provider)


class LiteLLMSmartAdapter(WorkflowPrimitive[ModelRouterRequest, LLMResponse]):
    """A litellm-backed adapter that accepts :class:`ModelRouterRequest`.

    Bridges the :class:`~ttadev.primitives.llm.model_router.ModelRouterPrimitive`
    interface to :class:`~ttadev.primitives.llm.litellm_primitive.LiteLLMPrimitive`,
    routing requests through litellm's native fallback cascade instead of
    individual provider SDK adapters.

    This class is returned by :meth:`SmartRouterPrimitive.build` and is a
    drop-in replacement for :class:`~ttadev.primitives.llm.model_router.ModelRouterPrimitive`
    in any component that calls ``execute(ModelRouterRequest, ctx)``.

    Attributes:
        modes: Mapping from mode name to ``RouterModeConfig`` — identical
            structure to ``ModelRouterPrimitive.modes`` for backward
            compatibility.

    Args:
        modes: Named routing modes, each with an ordered list of provider tiers.
    """

    def __init__(self, modes: dict[str, RouterModeConfig]) -> None:
        super().__init__()
        self.modes: dict[str, RouterModeConfig] = modes

        # Pre-build a (primary_model, LiteLLMPrimitive) pair per mode so we
        # don't recreate the primitive on every execute() call.
        self._mode_primitives: dict[str, tuple[str, LiteLLMPrimitive]] = {}
        for mode_name, mode_cfg in modes.items():
            model_strings: list[str] = [
                s for t in mode_cfg.tiers if (s := _tier_to_litellm_model(t)) is not None
            ]
            if model_strings:
                primary = model_strings[0]
                fallbacks: list[str] | None = model_strings[1:] or None
                self._mode_primitives[mode_name] = (
                    primary,
                    LiteLLMPrimitive(fallbacks=fallbacks),
                )

    async def execute(self, request: ModelRouterRequest, ctx: WorkflowContext) -> LLMResponse:
        """Execute the request via :class:`LiteLLMPrimitive` with litellm fallbacks.

        Translates the ``ModelRouterRequest`` to an ``LLMRequest`` and delegates
        to the pre-built :class:`LiteLLMPrimitive` for the requested mode.  The
        provider cascade (Groq → Google → OpenRouter → Ollama) is implemented
        via litellm's native ``fallbacks`` parameter.

        Args:
            request: The routing request, including mode, prompt, and optional
                system message.
            ctx: Workflow execution context.

        Returns:
            The :class:`LLMResponse` from whichever provider succeeded.

        Raises:
            KeyError: When ``request.mode`` is not found in ``self.modes``.
            RuntimeError: When no tiers are configured for the requested mode.
            Exception: Re-raises any litellm exception when all fallbacks fail.
        """
        if request.mode not in self._mode_primitives:
            if request.mode not in self.modes:
                raise KeyError(f"Unknown routing mode: {request.mode!r}")
            raise RuntimeError(f"No tiers configured for mode {request.mode!r}")

        primary_model, litellm_prim = self._mode_primitives[request.mode]

        messages: list[dict[str, Any]] = [{"role": "user", "content": request.prompt}]
        llm_request = LLMRequest(
            model=primary_model,
            messages=messages,
            system=request.system,
        )

        response = await litellm_prim.execute(llm_request, ctx)

        # Strip <think>...</think> reasoning tokens (mirrors ModelRouterPrimitive
        # behaviour when strip_thinking=True on individual tiers).
        mode_cfg = self.modes[request.mode]
        if any(t.strip_thinking for t in mode_cfg.tiers):
            response = LLMResponse(
                content=_THINK_RE.sub("", response.content).strip(),
                model=response.model,
                provider=response.provider,
                usage=response.usage,
                tool_calls=response.tool_calls,
                finish_reason=response.finish_reason,
            )

        return response


class SmartRouterPrimitive:
    """Factory for a zero-config, best-available-provider router.

    This is not itself a primitive (it wraps one).  Use
    :meth:`build` to obtain a configured :class:`LiteLLMSmartAdapter` that
    delegates execution to
    :class:`~ttadev.primitives.llm.litellm_primitive.LiteLLMPrimitive`.

    Example::

        router = SmartRouterPrimitive.build()
        adapter = ModelRouterChatAdapter(router)
        agent = DeveloperAgent.with_router(router)

    Args:
        mode: Routing mode label (default: ``"default"``).
        or_free_model: OpenRouter free-model slug to prefer.  Defaults to
            ``google/gemma-3-27b-it:free``.
    """

    def __init__(
        self,
        mode: str = "default",
        or_free_model: str = _OR_FREE_MODEL,
    ) -> None:
        self._mode = mode
        self._or_free_model = or_free_model

    def build(self) -> LiteLLMSmartAdapter:
        """Build and return the configured :class:`LiteLLMSmartAdapter`.

        Provider tiers are included based on available env vars:

        - **Groq** when ``GROQ_API_KEY`` is set
        - **Google** when ``GOOGLE_API_KEY`` is set
        - **OpenRouter** when ``OPENROUTER_API_KEY`` is set
        - **Ollama** always (local, no key required)

        The returned adapter uses :class:`LiteLLMPrimitive` internally, with
        litellm's native fallback cascade replacing the individual provider SDK
        tier cascade from the previous ``ModelRouterPrimitive`` implementation.

        Returns:
            A ready-to-use :class:`LiteLLMSmartAdapter` that cascades through
            available providers in quality/speed order via litellm.
        """
        tiers = self._build_tiers()
        modes = {
            self._mode: RouterModeConfig(
                description="Auto-cascade through best available free providers",
                tiers=tiers,
            )
        }
        return LiteLLMSmartAdapter(modes=modes)

    def _build_tiers(self) -> list[RouterTierConfig]:
        """Return ordered tier list based on available API keys."""
        tiers: list[RouterTierConfig] = []

        if os.environ.get("GROQ_API_KEY"):
            tiers.append(RouterTierConfig(provider="groq", model=_GROQ_DEFAULT_MODEL))

        if os.environ.get("GOOGLE_API_KEY"):
            tiers.append(RouterTierConfig(provider="google"))

        if os.environ.get("OPENROUTER_API_KEY"):
            tiers.append(RouterTierConfig(provider="openrouter", model=self._or_free_model))

        # Ollama is always the final fallback (no key required).
        tiers.append(RouterTierConfig(provider="ollama"))

        return tiers

    @classmethod
    def make(cls, **kwargs: object) -> LiteLLMSmartAdapter:
        """Class-level shortcut: ``SmartRouterPrimitive.make()`` → adapter.

        Equivalent to ``SmartRouterPrimitive().build()``.

        Args:
            **kwargs: Forwarded to :class:`SmartRouterPrimitive.__init__`.

        Returns:
            Configured :class:`LiteLLMSmartAdapter`.
        """
        return cls(**kwargs).build()  # type: ignore[arg-type]
