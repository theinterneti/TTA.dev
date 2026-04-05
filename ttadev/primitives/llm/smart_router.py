"""SmartRouterPrimitive — zero-config best-available-model router.

Builds a :class:`~ttadev.primitives.llm.model_router.ModelRouterPrimitive`
that cascades through available free providers in quality order:

1. **Groq** — fastest inference, generous free tier (GROQ_API_KEY)
2. **Google Gemini** — reliable free tier (GOOGLE_API_KEY)
3. **OpenRouter** — aggregator with many free model options (OPENROUTER_API_KEY)
4. **Ollama** — local fallback, no API key required

Each tier is included only when the corresponding API key env var is set (or
for Ollama, always included as last resort).  The returned router plugs into
any component that accepts a :class:`~ttadev.primitives.llm.model_router.ModelRouterPrimitive`.

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

from ttadev.primitives.llm.model_router import (
    ModelRouterPrimitive,
    RouterModeConfig,
    RouterTierConfig,
)

__all__ = ["SmartRouterPrimitive"]

# OpenRouter free model — high capability, cost $0.
_OR_FREE_MODEL = "google/gemma-3-27b-it:free"

# Best free Groq model for general-purpose tasks.
_GROQ_DEFAULT_MODEL: str | None = None  # let providers.py pick the default


class SmartRouterPrimitive:
    """Factory for a zero-config, best-available-provider router.

    This is not itself a primitive (it wraps one).  Use
    :meth:`build` to obtain a configured
    :class:`~ttadev.primitives.llm.model_router.ModelRouterPrimitive`.

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

    def build(self) -> ModelRouterPrimitive:
        """Build and return the configured ``ModelRouterPrimitive``.

        Provider tiers are included based on available env vars:

        - **Groq** when ``GROQ_API_KEY`` is set
        - **Google** when ``GOOGLE_API_KEY`` is set
        - **OpenRouter** when ``OPENROUTER_API_KEY`` is set
        - **Ollama** always (local, no key required)

        Returns:
            A ready-to-use ``ModelRouterPrimitive`` that cascades through
            available providers in quality/speed order.
        """
        tiers = self._build_tiers()
        modes = {
            self._mode: RouterModeConfig(
                description="Auto-cascade through best available free providers",
                tiers=tiers,
            )
        }
        kwargs: dict = {}
        if os.environ.get("GROQ_API_KEY"):
            kwargs["groq_api_key"] = os.environ["GROQ_API_KEY"]
        if os.environ.get("GOOGLE_API_KEY"):
            kwargs["google_api_key"] = os.environ["GOOGLE_API_KEY"]
        if os.environ.get("OPENROUTER_API_KEY"):
            kwargs["openrouter_api_key"] = os.environ["OPENROUTER_API_KEY"]

        return ModelRouterPrimitive(modes=modes, **kwargs)

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
    def make(cls, **kwargs: object) -> ModelRouterPrimitive:
        """Class-level shortcut: ``SmartRouterPrimitive.make()`` → router.

        Equivalent to ``SmartRouterPrimitive().build()``.

        Args:
            **kwargs: Forwarded to :class:`SmartRouterPrimitive.__init__`.

        Returns:
            Configured ``ModelRouterPrimitive``.
        """
        return cls(**kwargs).build()  # type: ignore[arg-type]
