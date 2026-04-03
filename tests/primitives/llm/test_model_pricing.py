"""Tests for ttadev.primitives.llm.model_pricing.

Covers:
- get_pricing() — known providers, unknown providers/models, prefix matching
- get_effective_cost_tier() — known models, unknown models with fallback
- Provider-specific tier assertions (Groq free, Gemini mixed, GitHub free,
  OpenAI/Anthropic paid)
- PROVIDER_PRICING catalog integrity (no duplicate keys, rate limit fields)
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from ttadev.primitives.llm.model_pricing import (
    PROVIDER_PRICING,
    ModelPricing,
    get_effective_cost_tier,
    get_pricing,
)

# ── Smoke tests ───────────────────────────────────────────────────────────────


class TestModelPricingDataclass:
    def test_model_pricing_is_frozen(self) -> None:
        """ModelPricing is a frozen dataclass — mutation raises."""
        p = ModelPricing(provider="groq", model_id="test", cost_tier="free")
        with pytest.raises((AttributeError, TypeError)):
            p.cost_tier = "high"  # type: ignore[misc]

    def test_model_pricing_defaults(self) -> None:
        """Optional fields default to None / empty string."""
        p = ModelPricing(provider="x", model_id="y", cost_tier="unknown")
        assert p.cost_per_1k_input_tokens is None
        assert p.cost_per_1k_output_tokens is None
        assert p.rate_limit_rpm is None
        assert p.rate_limit_rpd is None
        assert p.as_of == ""
        assert p.notes == ""


# ── get_pricing() ─────────────────────────────────────────────────────────────


class TestGetPricing:
    def test_returns_none_for_unknown_provider(self) -> None:
        """Unknown provider → None."""
        assert get_pricing("acme-cloud", "turbo-9000") is None

    def test_returns_none_for_unknown_model_on_known_provider(self) -> None:
        """Known provider but unknown model_id → None."""
        assert get_pricing("groq", "this-model-does-not-exist-xyz") is None

    def test_returns_correct_entry_for_groq_model(self) -> None:
        """Exact match returns the right ModelPricing for a Groq model."""
        p = get_pricing("groq", "llama-3.3-70b-versatile")
        assert p is not None
        assert p.provider == "groq"
        assert p.model_id == "llama-3.3-70b-versatile"
        assert p.cost_tier == "free"

    def test_returns_correct_entry_for_gemini_flash_lite(self) -> None:
        """Gemini 2.0 Flash Lite is correctly identified as free."""
        p = get_pricing("gemini", "models/gemini-2.0-flash-lite")
        assert p is not None
        assert p.cost_tier == "free"

    def test_returns_correct_entry_for_gemini_25_pro(self) -> None:
        """Gemini 2.5 Pro is correctly identified as medium."""
        p = get_pricing("gemini", "models/gemini-2.5-pro")
        assert p is not None
        assert p.cost_tier == "medium"

    def test_returns_correct_entry_for_github_models_gpt4o(self) -> None:
        """GitHub Models GPT-4o entry is present and free."""
        p = get_pricing("github", "gpt-4o")
        assert p is not None
        assert p.cost_tier == "free"

    def test_returns_correct_entry_for_openai_gpt4o(self) -> None:
        """OpenAI GPT-4o is high tier."""
        p = get_pricing("openai", "gpt-4o")
        assert p is not None
        assert p.cost_tier == "high"

    def test_returns_correct_entry_for_anthropic_sonnet(self) -> None:
        """Anthropic Claude 3.5 Sonnet is high tier."""
        p = get_pricing("anthropic", "claude-3-5-sonnet-20241022")
        assert p is not None
        assert p.cost_tier == "high"

    def test_provider_isolation(self) -> None:
        """Same model_id on different providers returns different entries."""
        # gpt-4o appears as both openai/gpt-4o and github/gpt-4o
        openai_p = get_pricing("openai", "gpt-4o")
        github_p = get_pricing("github", "gpt-4o")
        assert openai_p is not None
        assert github_p is not None
        assert openai_p.cost_tier == "high"
        assert github_p.cost_tier == "free"


# ── get_effective_cost_tier() ─────────────────────────────────────────────────


class TestGetEffectiveCostTier:
    def test_returns_catalog_tier_for_known_model(self) -> None:
        """Known model → catalog tier is returned."""
        assert get_effective_cost_tier("groq", "llama-3.1-8b-instant") == "free"

    def test_returns_fallback_for_unknown_model(self) -> None:
        """Unknown model → fallback is returned unchanged."""
        assert get_effective_cost_tier("groq", "nonexistent-model-xyz", "medium") == "medium"

    def test_default_fallback_is_unknown(self) -> None:
        """Default fallback is 'unknown' when not specified."""
        assert get_effective_cost_tier("acme", "mystery-model") == "unknown"

    def test_custom_fallback_preserved(self) -> None:
        """Caller-supplied fallback is returned for missing entries."""
        assert get_effective_cost_tier("openrouter", "some-paid-model", "low") == "low"


# ── Groq — all free ───────────────────────────────────────────────────────────


class TestGroqPricing:
    _GROQ_MODELS: ClassVar[list[str]] = [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-8b-8192",
        "llama3-70b-8192",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "gemma-7b-it",
        "moonshotai/kimi-k2-instruct",
        "qwen/qwen3-32b",
        "compound-beta",
    ]

    @pytest.mark.parametrize("model_id", _GROQ_MODELS)
    def test_all_groq_models_are_free(self, model_id: str) -> None:
        """Every Groq model in the catalog has cost_tier='free'."""
        p = get_pricing("groq", model_id)
        assert p is not None, f"No pricing entry for groq/{model_id}"
        assert p.cost_tier == "free", f"groq/{model_id} expected 'free', got {p.cost_tier!r}"

    @pytest.mark.parametrize("model_id", _GROQ_MODELS)
    def test_all_groq_models_have_zero_cost(self, model_id: str) -> None:
        """Every Groq model has cost_per_1k=0.0 (free tier)."""
        p = get_pricing("groq", model_id)
        assert p is not None
        assert p.cost_per_1k_input_tokens == 0.0
        assert p.cost_per_1k_output_tokens == 0.0

    @pytest.mark.parametrize("model_id", _GROQ_MODELS)
    def test_all_groq_models_have_rpm(self, model_id: str) -> None:
        """Every Groq model has a known rate_limit_rpm."""
        p = get_pricing("groq", model_id)
        assert p is not None
        assert p.rate_limit_rpm is not None, f"groq/{model_id} missing rate_limit_rpm"


# ── Gemini — mixed free / paid ────────────────────────────────────────────────


class TestGeminiPricing:
    def test_gemini_flash_lite_is_free(self) -> None:
        p = get_pricing("gemini", "models/gemini-2.0-flash-lite")
        assert p is not None
        assert p.cost_tier == "free"
        assert p.rate_limit_rpd == 1_500

    def test_gemini_15_flash_is_free(self) -> None:
        p = get_pricing("gemini", "models/gemini-1.5-flash")
        assert p is not None
        assert p.cost_tier == "free"

    def test_gemini_20_flash_is_low(self) -> None:
        p = get_pricing("gemini", "models/gemini-2.0-flash")
        assert p is not None
        assert p.cost_tier == "low"
        assert p.cost_per_1k_input_tokens is not None
        assert p.cost_per_1k_input_tokens > 0

    def test_gemini_25_flash_is_low(self) -> None:
        p = get_pricing("gemini", "models/gemini-2.5-flash")
        assert p is not None
        assert p.cost_tier == "low"

    def test_gemini_15_pro_is_medium(self) -> None:
        p = get_pricing("gemini", "models/gemini-1.5-pro")
        assert p is not None
        assert p.cost_tier == "medium"


# ── GitHub Models — all free with rate limits ─────────────────────────────────


class TestGitHubModelsPricing:
    def test_github_models_are_free(self) -> None:
        """All GitHub Models entries have cost_tier='free'."""
        github_entries = [p for p in PROVIDER_PRICING if p.provider == "github"]
        assert len(github_entries) > 0, "No GitHub Models entries found"
        for entry in github_entries:
            assert entry.cost_tier == "free", (
                f"github/{entry.model_id} expected 'free', got {entry.cost_tier!r}"
            )

    def test_large_github_model_has_50_rpd(self) -> None:
        """Large GitHub Models (gpt-4o) have rpd=50."""
        p = get_pricing("github", "gpt-4o")
        assert p is not None
        assert p.rate_limit_rpd == 50

    def test_small_github_model_has_150_rpd(self) -> None:
        """Small GitHub Models (gpt-4o-mini) have rpd=150."""
        p = get_pricing("github", "gpt-4o-mini")
        assert p is not None
        assert p.rate_limit_rpd == 150

    def test_github_llama33_70b_has_50_rpd(self) -> None:
        """Llama 3.3 70B (large) has rpd=50."""
        p = get_pricing("github", "Meta-Llama-3.3-70B-Instruct")
        assert p is not None
        assert p.rate_limit_rpd == 50

    def test_github_phi4_has_150_rpd(self) -> None:
        """Phi-4 (small) has rpd=150."""
        p = get_pricing("github", "Phi-4")
        assert p is not None
        assert p.rate_limit_rpd == 150

    def test_all_github_entries_have_rpd(self) -> None:
        """All GitHub Models entries have a rate_limit_rpd set."""
        github_entries = [p for p in PROVIDER_PRICING if p.provider == "github"]
        for entry in github_entries:
            assert entry.rate_limit_rpd is not None, (
                f"github/{entry.model_id} missing rate_limit_rpd"
            )


# ── OpenAI / Anthropic ────────────────────────────────────────────────────────


class TestOpenAIAnthropic:
    def test_openai_gpt4o_is_high(self) -> None:
        assert get_effective_cost_tier("openai", "gpt-4o") == "high"

    def test_openai_gpt4o_mini_is_medium(self) -> None:
        assert get_effective_cost_tier("openai", "gpt-4o-mini") == "medium"

    def test_anthropic_sonnet_is_high(self) -> None:
        assert get_effective_cost_tier("anthropic", "claude-3-5-sonnet-20241022") == "high"

    def test_anthropic_haiku_is_medium(self) -> None:
        assert get_effective_cost_tier("anthropic", "claude-3-5-haiku-20241022") == "medium"

    def test_anthropic_opus_is_high(self) -> None:
        assert get_effective_cost_tier("anthropic", "claude-opus-4-5") == "high"


# ── OpenRouter ────────────────────────────────────────────────────────────────


class TestOpenRouterPricing:
    def test_free_suffix_models_are_free(self) -> None:
        """OpenRouter :free models are cost_tier='free'."""
        free_models = [
            "mistralai/mistral-7b-instruct:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "deepseek/deepseek-r1:free",
        ]
        for model_id in free_models:
            assert get_effective_cost_tier("openrouter", model_id) == "free", (
                f"openrouter/{model_id} should be 'free'"
            )

    def test_unknown_openrouter_model_returns_fallback(self) -> None:
        """OpenRouter model without catalog entry → caller's fallback."""
        assert get_effective_cost_tier("openrouter", "some-unknown-paid-model", "medium") == (
            "medium"
        )


# ── Catalog integrity ─────────────────────────────────────────────────────────


class TestCatalogIntegrity:
    def test_no_duplicate_provider_model_pairs(self) -> None:
        """PROVIDER_PRICING must not have duplicate (provider, model_id) pairs."""
        seen: set[tuple[str, str]] = set()
        duplicates: list[tuple[str, str]] = []
        for entry in PROVIDER_PRICING:
            key = (entry.provider, entry.model_id)
            if key in seen:
                duplicates.append(key)
            seen.add(key)
        assert duplicates == [], f"Duplicate (provider, model_id) pairs: {duplicates}"

    def test_all_cost_tiers_are_valid(self) -> None:
        """All cost_tier values are one of the recognised tiers."""
        valid = {"free", "low", "medium", "high", "unknown"}
        for entry in PROVIDER_PRICING:
            assert entry.cost_tier in valid, (
                f"{entry.provider}/{entry.model_id} has invalid cost_tier={entry.cost_tier!r}"
            )

    def test_no_empty_model_ids(self) -> None:
        """No entry should have an empty model_id (would act as a catch-all)."""
        for entry in PROVIDER_PRICING:
            assert entry.model_id, (
                f"Empty model_id for provider={entry.provider!r} — "
                "this would match every model for that provider"
            )

    def test_catalog_has_entries_for_all_major_providers(self) -> None:
        """At least one entry exists for each major provider."""
        providers_in_catalog = {p.provider for p in PROVIDER_PRICING}
        required = {"groq", "gemini", "github", "openrouter", "openai", "anthropic", "together"}
        missing = required - providers_in_catalog
        assert not missing, f"Missing providers in catalog: {missing}"
