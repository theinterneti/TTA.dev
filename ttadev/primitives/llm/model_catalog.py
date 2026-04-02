"""Human-readable catalog of all supported LLM providers and models.

This module serves as the "swiss army knife" reference document baked into
code.  It summarises every provider's capabilities, cost structure, and free
tier availability, then lists the well-known models registered in
:mod:`~ttadev.primitives.llm.model_registry`.

Usage::

    from ttadev.primitives.llm.model_catalog import print_catalog, PROVIDER_SUMMARY
    print_catalog()

CLI::

    python -m ttadev.primitives.llm.model_catalog
"""

from __future__ import annotations

import textwrap

from ttadev.primitives.llm.model_registry import (
    _DEFAULT_CLOUD_MODELS,
    GEMINI_MODELS,
    GROQ_ROTATION_MODELS,
)

__all__ = [
    "PROVIDER_SUMMARY",
    "print_catalog",
]

# ── Provider summary ──────────────────────────────────────────────────────────

#: Human-readable metadata for each registered provider.
#:
#: Keys are canonical provider names matching :data:`~ttadev.primitives.llm.providers.PROVIDERS`.
#: Values are plain dicts with the following keys:
#:
#: * ``name`` — display name
#: * ``type`` — ``"cloud"`` | ``"local"``
#: * ``free_tier`` — ``True`` if the provider has a genuinely free usage tier
#: * ``auth_env_var`` — environment variable that holds the API key (or empty string)
#: * ``strengths`` — list of short capability descriptors
#: * ``notes`` — additional context for operators
PROVIDER_SUMMARY: dict[str, dict] = {
    "groq": {
        "name": "Groq",
        "type": "cloud",
        "free_tier": True,
        "auth_env_var": "GROQ_API_KEY",
        "strengths": [
            "Extremely low latency (LPU inference)",
            "Free tier with generous rate limits",
            "Strong Llama/Mixtral/Gemma model selection",
            "Supports tool calling on most models",
        ],
        "notes": (
            "Best choice for high-throughput, cost-free inference.  "
            "Use GROQ_ROTATION_MODELS for multi-bucket rotation to spread "
            "load across rate-limit buckets."
        ),
    },
    "gemini": {
        "name": "Google Gemini",
        "type": "cloud",
        "free_tier": True,
        "auth_env_var": "GOOGLE_API_KEY",
        "strengths": [
            "Massive context windows (up to 2M tokens)",
            "Vision support across all tiers",
            "Strong reasoning and coding (2.5 Pro)",
            "Free-tier 1.5 Flash with 1M context",
        ],
        "notes": (
            "Use the ``models/`` prefix for all model IDs when calling the "
            "OpenAI-compatible endpoint.  Default model is ``models/gemini-2.5-flash`` "
            "(best free/low-cost model as of 2026-06)."
        ),
    },
    "openrouter": {
        "name": "OpenRouter",
        "type": "cloud",
        "free_tier": True,
        "auth_env_var": "OPENROUTER_API_KEY",
        "strengths": [
            "Aggregates 200+ models from multiple providers",
            "Free models available via ``:free`` suffix",
            "Single API key for many providers",
            "Useful for model fallback chains",
        ],
        "notes": (
            "Free models have lower rate limits and may have usage caps.  "
            "DeepSeek R1 free requires ``strip_thinking=True`` to remove "
            "``<think>`` blocks from responses."
        ),
    },
    "together": {
        "name": "Together AI",
        "type": "cloud",
        "free_tier": False,
        "auth_env_var": "TOGETHER_API_KEY",
        "strengths": [
            "Wide open-source model selection",
            "Competitive low-cost pricing",
            "Good throughput for 70B+ models",
        ],
        "notes": "Cost tier is 'low' — not free but affordable for most use-cases.",
    },
    "anthropic": {
        "name": "Anthropic",
        "type": "cloud",
        "free_tier": False,
        "auth_env_var": "ANTHROPIC_API_KEY",
        "strengths": [
            "Best-in-class instruction following",
            "Long context with excellent recall (200K tokens)",
            "Strong safety and refusal tuning",
            "Excellent tool calling",
        ],
        "notes": (
            "SDK-only provider — not OpenAI-compatible.  "
            "claude-3-5-haiku is the lowest cost entry point."
        ),
    },
    "openai": {
        "name": "OpenAI",
        "type": "cloud",
        "free_tier": False,
        "auth_env_var": "OPENAI_API_KEY",
        "strengths": [
            "Industry-standard API",
            "GPT-4o vision and tool calling",
            "o3-mini for reasoning tasks",
        ],
        "notes": "Cost tier ranges from 'low' (gpt-4o-mini) to 'medium' (gpt-4o, o3-mini).",
    },
    "xai": {
        "name": "xAI (Grok)",
        "type": "cloud",
        "free_tier": False,
        "auth_env_var": "XAI_API_KEY",
        "strengths": [
            "Grok-3 family with strong reasoning",
            "Full OpenAI-compatible API",
        ],
        "notes": "Default model is grok-3-mini.",
    },
    "ollama": {
        "name": "Ollama (local)",
        "type": "local",
        "free_tier": True,
        "auth_env_var": "",
        "strengths": [
            "Completely free — no API key required",
            "Data stays on-device (privacy)",
            "Works offline",
            "Many quantised models available",
        ],
        "notes": (
            "Requires a running Ollama daemon on localhost:11434.  "
            "Use ``ModelRegistryPrimitive(action='discover_ollama')`` to "
            "auto-register all loaded models."
        ),
    },
    "huggingface": {
        "name": "HuggingFace Inference API",
        "type": "cloud",
        "free_tier": True,
        "auth_env_var": "HF_TOKEN",
        "strengths": [
            "Access to thousands of community models",
            "Serverless inference for many popular models",
            "OpenAI-compatible endpoint",
        ],
        "notes": (
            "Free tier available with rate limits.  HF_TOKEN is your "
            "HuggingFace access token from huggingface.co/settings/tokens.  "
            "Model ID is appended to the base URL path."
        ),
    },
}

# ── Catalog helpers ───────────────────────────────────────────────────────────


def _models_for_provider(provider: str) -> list:
    """Return all default cloud model entries for a given provider.

    Args:
        provider: Canonical provider name, e.g. ``"groq"``.

    Returns:
        Subset of :data:`~ttadev.primitives.llm.model_registry._DEFAULT_CLOUD_MODELS`
        whose ``provider`` field matches *provider*.
    """
    return [m for m in _DEFAULT_CLOUD_MODELS if m.provider == provider]


def print_catalog() -> None:
    """Pretty-print the full provider and model catalog to stdout.

    Iterates over :data:`PROVIDER_SUMMARY` and prints each provider's metadata
    followed by a table of its registered models with context window, cost
    tier, and capability flags.

    Example::

        from ttadev.primitives.llm.model_catalog import print_catalog
        print_catalog()
    """
    width = 80
    print("=" * width)
    print("TTA.dev  LLM Provider & Model Catalog".center(width))
    print("=" * width)

    for provider_key, info in PROVIDER_SUMMARY.items():
        # ── Provider header ────────────────────────────────────────────────────
        free_label = "✅ FREE TIER" if info["free_tier"] else "💳 paid"
        ptype = info["type"].upper()
        print(f"\n{'─' * width}")
        print(f"  {info['name']}  [{ptype}]  {free_label}")
        if info["auth_env_var"]:
            print(f"  Auth: ${info['auth_env_var']}")
        else:
            print("  Auth: (none — local daemon)")
        print()

        # Strengths
        print("  Strengths:")
        for s in info["strengths"]:
            print(f"    • {s}")

        # Notes
        if info["notes"]:
            wrapped = textwrap.fill(
                info["notes"], width=width - 4, initial_indent="  ℹ  ", subsequent_indent="     "
            )
            print(wrapped)

        # ── Model table ────────────────────────────────────────────────────────
        models = _models_for_provider(provider_key)
        if not models:
            print("\n  (no pre-registered models)")
            continue

        print()
        header = f"  {'Model ID':<52} {'Ctx':>6}  {'Tier':<8}  {'Tools':<5}  {'Vision':<6}"
        print(header)
        print("  " + "-" * (len(header) - 2))

        for m in models:
            ctx_k = f"{m.context_length // 1_000}K"
            tools = "✓" if m.supports_tool_calling else "–"
            vision = "✓" if m.supports_vision else "–"
            extras = []
            if m.metadata.get("thinking_model"):
                extras.append("🧠think")
            if m.metadata.get("strip_thinking"):
                extras.append("strip")
            if m.metadata.get("compound_model"):
                extras.append("compound")
            extra_str = f"  [{', '.join(extras)}]" if extras else ""
            print(
                f"  {m.model_id:<52} {ctx_k:>6}  {m.cost_tier:<8}  {tools:<5}  {vision:<6}{extra_str}"
            )

    # ── Rotation constants ─────────────────────────────────────────────────────
    print(f"\n{'─' * width}")
    print("  GROQ_ROTATION_MODELS  (fastest → most capable)")
    for i, mid in enumerate(GROQ_ROTATION_MODELS, 1):
        print(f"    {i}. {mid}")

    print()
    print("  GEMINI_MODELS  (all models/ prefix entries)")
    for mid in GEMINI_MODELS:
        print(f"    • {mid}")

    print(f"\n{'=' * width}")
    total = len(_DEFAULT_CLOUD_MODELS)
    providers = len(PROVIDER_SUMMARY)
    print(f"  {total} models across {providers} providers".center(width))
    print("=" * width)


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print_catalog()
