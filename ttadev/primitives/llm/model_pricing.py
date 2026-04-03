"""Model pricing catalog — source of truth for cost tiers and rate limits.

Pricing is a time-varying property of a provider-model relationship, not a fixed
model attribute. Update entries here when providers change pricing without
touching ModelEntry definitions in model_registry.py.

Usage::

    from ttadev.primitives.llm.model_pricing import get_pricing, get_effective_cost_tier

    # Look up full pricing metadata
    p = get_pricing("groq", "llama-3.3-70b-versatile")
    print(p.cost_tier, p.rate_limit_rpm)   # "free", 30

    # Just the cost tier (with fallback)
    tier = get_effective_cost_tier("openai", "gpt-4o", fallback="unknown")
    print(tier)   # "high"
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPricing:
    """Pricing and rate-limit metadata for a provider-model pair.

    Attributes:
        provider: Provider key matching ``ModelEntry.provider``.
        model_id: Exact model ID or prefix pattern (matched by ``startswith``).
        cost_tier: Cost band — ``"free"`` | ``"low"`` | ``"medium"`` | ``"high"``
            | ``"unknown"``.
        cost_per_1k_input_tokens: USD cost per 1 000 input tokens.
            ``None`` = unknown.
        cost_per_1k_output_tokens: USD cost per 1 000 output tokens.
            ``None`` = unknown.
        rate_limit_rpm: Requests per minute limit.  ``None`` = unknown/unlimited.
        rate_limit_rpd: Requests per day limit.  ``None`` = unknown/unlimited.
        as_of: ISO date string when this pricing was last verified.
        notes: Human-readable notes (e.g. ``"free tier requires account verification"``).
    """

    provider: str
    model_id: str
    cost_tier: str
    cost_per_1k_input_tokens: float | None = None
    cost_per_1k_output_tokens: float | None = None
    rate_limit_rpm: int | None = None
    rate_limit_rpd: int | None = None
    as_of: str = ""
    notes: str = ""


# ---------------------------------------------------------------------------
# Catalog — April 2026 pricing snapshot
# ---------------------------------------------------------------------------

#: Single source of truth for provider-model pricing.
#: Entries are searched in order; the first match wins.
#: Lookup uses exact ``model_id`` equality **or** ``model_id.startswith(entry.model_id)``.
#: Avoid empty ``model_id`` strings — they would match every model for that provider.
PROVIDER_PRICING: list[ModelPricing] = [
    # ── Groq ─────────────────────────────────────────────────────────────────
    # All Groq inference is free (rate-limited, not pay-per-token).
    # Rate limits sourced from https://console.groq.com/docs/rate-limits (April 2026).
    ModelPricing(
        provider="groq",
        model_id="llama-3.3-70b-versatile",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=30,
        rate_limit_rpd=14_400,
        as_of="2026-04-01",
        notes="Groq free tier — rate-limited, no per-token charge.",
    ),
    ModelPricing(
        provider="groq",
        model_id="llama-3.1-70b-versatile",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=100,
        rate_limit_rpd=14_400,
        as_of="2026-04-01",
        notes="Groq free tier.",
    ),
    ModelPricing(
        provider="groq",
        model_id="llama-3.1-8b-instant",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=100,
        rate_limit_rpd=14_400,
        as_of="2026-04-01",
        notes="Groq free tier — fastest small model.",
    ),
    ModelPricing(
        provider="groq",
        model_id="llama3-8b-8192",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=100,
        rate_limit_rpd=14_400,
        as_of="2026-04-01",
        notes="Groq free tier.",
    ),
    ModelPricing(
        provider="groq",
        model_id="llama3-70b-8192",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=30,
        rate_limit_rpd=14_400,
        as_of="2026-04-01",
        notes="Groq free tier.",
    ),
    ModelPricing(
        provider="groq",
        model_id="meta-llama/llama-4-scout-17b-16e-instruct",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=30,
        rate_limit_rpd=14_400,
        as_of="2026-04-01",
        notes="Groq free tier — multimodal Llama 4 Scout.",
    ),
    ModelPricing(
        provider="groq",
        model_id="gemma-7b-it",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=100,
        rate_limit_rpd=14_400,
        as_of="2026-04-01",
        notes="Groq free tier.",
    ),
    ModelPricing(
        provider="groq",
        model_id="moonshotai/kimi-k2-instruct",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=30,
        rate_limit_rpd=14_400,
        as_of="2026-04-01",
        notes="Groq free tier.",
    ),
    ModelPricing(
        provider="groq",
        model_id="qwen/qwen3-32b",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=30,
        rate_limit_rpd=14_400,
        as_of="2026-04-01",
        notes="Groq free tier — thinking model.",
    ),
    ModelPricing(
        provider="groq",
        model_id="compound-beta",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=30,
        rate_limit_rpd=14_400,
        as_of="2026-04-01",
        notes="Groq compound model — free tier.",
    ),
    # ── Gemini ────────────────────────────────────────────────────────────────
    # Registry uses the 'models/' prefix required by the Google OpenAI-compat endpoint.
    # Pricing from https://ai.google.dev/pricing (April 2026).
    #
    # IMPORTANT — ordering: more-specific model IDs must precede their prefix
    # siblings because the lookup uses startswith() matching.
    # e.g. "models/gemini-2.0-flash-lite".startswith("models/gemini-2.0-flash") is True,
    # so the -lite entry must come first.
    ModelPricing(
        provider="gemini",
        model_id="models/gemini-2.5-pro",
        cost_tier="medium",
        cost_per_1k_input_tokens=0.00125,  # $1.25 / 1M tokens
        cost_per_1k_output_tokens=0.01,  # $10 / 1M tokens
        rate_limit_rpm=1_000,
        as_of="2026-04-01",
        notes="Gemini 2.5 Pro — most capable Gemini model.",
    ),
    ModelPricing(
        provider="gemini",
        model_id="models/gemini-2.5-flash",
        cost_tier="low",
        cost_per_1k_input_tokens=0.000075,  # $0.075 / 1M tokens
        cost_per_1k_output_tokens=0.0003,  # $0.30 / 1M tokens
        rate_limit_rpm=2_000,
        as_of="2026-04-01",
        notes="Gemini 2.5 Flash — pay-per-token, no free tier.",
    ),
    ModelPricing(
        provider="gemini",
        model_id="models/gemini-2.0-flash-lite",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=30,
        rate_limit_rpd=1_500,
        as_of="2026-04-01",
        notes="Gemini 2.0 Flash Lite — free tier with daily limit.",
    ),
    ModelPricing(
        provider="gemini",
        model_id="models/gemini-2.0-flash",
        cost_tier="low",
        cost_per_1k_input_tokens=0.000075,  # $0.075 / 1M tokens
        cost_per_1k_output_tokens=0.0003,  # $0.30 / 1M tokens
        rate_limit_rpm=2_000,
        as_of="2026-04-01",
        notes="Gemini 2.0 Flash — pay-per-token.",
    ),
    ModelPricing(
        provider="gemini",
        model_id="models/gemini-1.5-flash-8b",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=15,
        rate_limit_rpd=1_500,
        as_of="2026-04-01",
        notes="Gemini 1.5 Flash 8B — free tier.",
    ),
    ModelPricing(
        provider="gemini",
        model_id="models/gemini-1.5-flash",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=15,
        rate_limit_rpd=1_500,
        as_of="2026-04-01",
        notes="Gemini 1.5 Flash — free tier.",
    ),
    ModelPricing(
        provider="gemini",
        model_id="models/gemini-1.5-pro",
        cost_tier="medium",
        cost_per_1k_input_tokens=0.00125,  # $1.25 / 1M tokens
        cost_per_1k_output_tokens=0.005,  # $5 / 1M tokens
        rate_limit_rpm=360,
        as_of="2026-04-01",
        notes="Gemini 1.5 Pro — medium tier.",
    ),
    # ── GitHub Models ─────────────────────────────────────────────────────────
    # Free with GITHUB_TOKEN.  Large models: 10 RPM / 50 RPD.
    # Small models: 15 RPM / 150 RPD.
    # Reference: https://docs.github.com/en/github-models/prototyping-with-ai-models
    #
    # IMPORTANT — ordering: gpt-4o-mini must precede gpt-4o because the lookup
    # uses startswith() matching and "gpt-4o-mini".startswith("gpt-4o") is True.
    ModelPricing(
        provider="github",
        model_id="gpt-4o-mini",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=15,
        rate_limit_rpd=150,
        as_of="2026-04-01",
        notes="GitHub Models free tier — small model quota.",
    ),
    ModelPricing(
        provider="github",
        model_id="gpt-4o",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=10,
        rate_limit_rpd=50,
        as_of="2026-04-01",
        notes="GitHub Models free tier — large model quota.",
    ),
    ModelPricing(
        provider="github",
        model_id="Meta-Llama-3.3-70B-Instruct",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=10,
        rate_limit_rpd=50,
        as_of="2026-04-01",
        notes="GitHub Models free tier — large model quota.",
    ),
    ModelPricing(
        provider="github",
        model_id="Meta-Llama-3.1-8B-Instruct",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=15,
        rate_limit_rpd=150,
        as_of="2026-04-01",
        notes="GitHub Models free tier — small model quota.",
    ),
    ModelPricing(
        provider="github",
        model_id="Phi-4",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=15,
        rate_limit_rpd=150,
        as_of="2026-04-01",
        notes="GitHub Models free tier — small model quota.",
    ),
    ModelPricing(
        provider="github",
        model_id="DeepSeek-R1",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        rate_limit_rpm=10,
        rate_limit_rpd=50,
        as_of="2026-04-01",
        notes="GitHub Models free tier — large model quota.",
    ),
    # ── OpenRouter free models (:free suffix) ─────────────────────────────────
    # Free models are community-hosted; availability varies.  All have cost 0.
    ModelPricing(
        provider="openrouter",
        model_id="mistralai/mistral-7b-instruct:free",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        as_of="2026-04-01",
        notes="OpenRouter free community model.",
    ),
    ModelPricing(
        provider="openrouter",
        model_id="microsoft/phi-3-mini-128k-instruct:free",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        as_of="2026-04-01",
        notes="OpenRouter free community model.",
    ),
    ModelPricing(
        provider="openrouter",
        model_id="meta-llama/llama-3.2-3b-instruct:free",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        as_of="2026-04-01",
        notes="OpenRouter free community model.",
    ),
    ModelPricing(
        provider="openrouter",
        model_id="meta-llama/llama-3.1-8b-instruct:free",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        as_of="2026-04-01",
        notes="OpenRouter free community model.",
    ),
    ModelPricing(
        provider="openrouter",
        model_id="google/gemma-3-27b-it:free",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        as_of="2026-04-01",
        notes="OpenRouter free community model.",
    ),
    ModelPricing(
        provider="openrouter",
        model_id="qwen/qwen3-30b-a3b:free",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        as_of="2026-04-01",
        notes="OpenRouter free community model — Qwen3.",
    ),
    ModelPricing(
        provider="openrouter",
        model_id="deepseek/deepseek-r1:free",
        cost_tier="free",
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        as_of="2026-04-01",
        notes="OpenRouter free community model — DeepSeek R1 thinking model.",
    ),
    # ── OpenRouter paid models ────────────────────────────────────────────────
    ModelPricing(
        provider="openrouter",
        model_id="mistralai/mistral-7b-instruct",
        cost_tier="low",
        cost_per_1k_input_tokens=0.000055,
        cost_per_1k_output_tokens=0.000055,
        as_of="2026-04-01",
        notes="OpenRouter paid — cheap small model.",
    ),
    ModelPricing(
        provider="openrouter",
        model_id="openai/gpt-4o",
        cost_tier="high",
        cost_per_1k_input_tokens=0.005,
        cost_per_1k_output_tokens=0.015,
        as_of="2026-04-01",
        notes="OpenRouter routing to GPT-4o.",
    ),
    ModelPricing(
        provider="openrouter",
        model_id="anthropic/claude-3-5-sonnet",
        cost_tier="high",
        cost_per_1k_input_tokens=0.003,
        cost_per_1k_output_tokens=0.015,
        as_of="2026-04-01",
        notes="OpenRouter routing to Claude 3.5 Sonnet.",
    ),
    # ── Together AI ───────────────────────────────────────────────────────────
    # Pay-per-token but cheap; typically 10–80% of OpenAI pricing.
    ModelPricing(
        provider="together",
        model_id="meta-llama/Llama-3.2-3B-Instruct-Turbo",
        cost_tier="low",
        cost_per_1k_input_tokens=0.00006,  # $0.06 / 1M
        cost_per_1k_output_tokens=0.00006,
        as_of="2026-04-01",
        notes="Together AI — small cheap model.",
    ),
    ModelPricing(
        provider="together",
        model_id="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        cost_tier="low",
        cost_per_1k_input_tokens=0.00088,  # $0.88 / 1M
        cost_per_1k_output_tokens=0.00088,
        as_of="2026-04-01",
        notes="Together AI — 70B model at low cost.",
    ),
    ModelPricing(
        provider="together",
        model_id="Qwen/Qwen2.5-72B-Instruct-Turbo",
        cost_tier="low",
        cost_per_1k_input_tokens=0.0012,  # $1.20 / 1M
        cost_per_1k_output_tokens=0.0012,
        as_of="2026-04-01",
        notes="Together AI — Qwen 72B.",
    ),
    # ── Anthropic ─────────────────────────────────────────────────────────────
    # No persistent free API tier.
    ModelPricing(
        provider="anthropic",
        model_id="claude-3-5-haiku-20241022",
        cost_tier="medium",
        cost_per_1k_input_tokens=0.0008,  # $0.80 / 1M
        cost_per_1k_output_tokens=0.004,  # $4 / 1M
        as_of="2026-04-01",
        notes="Anthropic Claude 3.5 Haiku — fastest, cheapest Claude.",
    ),
    ModelPricing(
        provider="anthropic",
        model_id="claude-3-5-sonnet-20241022",
        cost_tier="high",
        cost_per_1k_input_tokens=0.003,  # $3 / 1M
        cost_per_1k_output_tokens=0.015,  # $15 / 1M
        as_of="2026-04-01",
        notes="Anthropic Claude 3.5 Sonnet — frontier coding model.",
    ),
    ModelPricing(
        provider="anthropic",
        model_id="claude-opus-4-5",
        cost_tier="high",
        cost_per_1k_input_tokens=0.015,  # $15 / 1M
        cost_per_1k_output_tokens=0.075,  # $75 / 1M
        as_of="2026-04-01",
        notes="Anthropic Claude Opus 4.5 — most capable, most expensive.",
    ),
    # ── OpenAI ────────────────────────────────────────────────────────────────
    # No persistent free API tier.
    ModelPricing(
        provider="openai",
        model_id="gpt-4o-mini",
        cost_tier="medium",
        cost_per_1k_input_tokens=0.00015,  # $0.15 / 1M
        cost_per_1k_output_tokens=0.0006,  # $0.60 / 1M
        as_of="2026-04-01",
        notes="GPT-4o Mini — fast, low-cost OpenAI model.",
    ),
    ModelPricing(
        provider="openai",
        model_id="gpt-4o",
        cost_tier="high",
        cost_per_1k_input_tokens=0.005,  # $5 / 1M
        cost_per_1k_output_tokens=0.015,  # $15 / 1M
        as_of="2026-04-01",
        notes="GPT-4o — flagship OpenAI model.",
    ),
    ModelPricing(
        provider="openai",
        model_id="o3-mini",
        cost_tier="medium",
        cost_per_1k_input_tokens=0.0011,  # $1.10 / 1M
        cost_per_1k_output_tokens=0.0044,  # $4.40 / 1M
        as_of="2026-04-01",
        notes="OpenAI o3-mini — reasoning model at medium price.",
    ),
]

# Keep a fast lookup set for duplicate detection at import time (debug builds).
_PRICING_KEYS: list[tuple[str, str]] = [(p.provider, p.model_id) for p in PROVIDER_PRICING]


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def get_pricing(provider: str, model_id: str) -> ModelPricing | None:
    """Look up pricing for a provider-model pair.

    Searches :data:`PROVIDER_PRICING` in order.  A match occurs when
    ``entry.provider == provider`` **and** either
    ``entry.model_id == model_id`` or ``model_id.startswith(entry.model_id)``.
    The first matching entry wins.

    Args:
        provider: Provider key, e.g. ``"groq"``, ``"gemini"``, ``"openai"``.
        model_id: Exact model identifier, e.g. ``"llama-3.3-70b-versatile"``.

    Returns:
        :class:`ModelPricing` if found, ``None`` otherwise.

    Example::

        p = get_pricing("groq", "llama-3.3-70b-versatile")
        assert p is not None
        assert p.cost_tier == "free"
        assert p.rate_limit_rpm == 30
    """
    for entry in PROVIDER_PRICING:
        if entry.provider == provider and (
            entry.model_id == model_id or model_id.startswith(entry.model_id)
        ):
            return entry
    return None


def get_effective_cost_tier(
    provider: str,
    model_id: str,
    fallback: str = "unknown",
) -> str:
    """Return the current cost tier for a provider-model pair.

    Delegates to :func:`get_pricing`.  When no catalog entry is found the
    *fallback* is returned unchanged — this preserves the static ``cost_tier``
    set on :class:`~ttadev.primitives.llm.model_registry.ModelEntry` for any
    model not yet listed in the catalog.

    Args:
        provider: Provider key, e.g. ``"groq"``, ``"gemini"``, ``"openai"``.
        model_id: Exact model identifier.
        fallback: Value to return when no pricing entry exists.  Defaults to
            ``"unknown"``.

    Returns:
        Cost tier string from the catalog, or *fallback*.

    Example::

        tier = get_effective_cost_tier("groq", "llama-3.3-70b-versatile")
        assert tier == "free"

        tier = get_effective_cost_tier("acme", "mystery-model", fallback="medium")
        assert tier == "medium"
    """
    pricing = get_pricing(provider, model_id)
    return pricing.cost_tier if pricing else fallback
