"""Tests for ttadev.primitives.research (FreeTierResearchPrimitive).

Covers:
- ModelQualityMetrics: Pydantic field validation, defaults, bounds (11 tests)
- ProviderInfo: Pydantic field validation, model list embedding (7 tests)
- FreeTierResearchRequest: defaults, custom providers, field types (7 tests)
- FreeTierResearchResponse: required providers, optional fields (5 tests)
- FreeTierResearchPrimitive:
    - Instantiation / _provider_data initialisation (7 tests)
    - execute() — filtering, unknowns, changelog, guide generation (20 tests)
    - generate_best_free_models_ranking() — sorting, tuple structure (10 tests)
    - generate_fallback_strategy() — code output, use-case routing (8 tests)
    - _get_primitive_class_name() — provider-name mapping (6 tests)
"""

from __future__ import annotations

import re

import pytest
from pydantic import ValidationError

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.research import (
    FreeTierResearchPrimitive,
    FreeTierResearchRequest,
    FreeTierResearchResponse,
    ModelQualityMetrics,
    ProviderInfo,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(wid: str = "test-research") -> WorkflowContext:
    return WorkflowContext(workflow_id=wid)


def _simple_metric(
    name: str = "test-model",
    score: float = 80.0,
) -> ModelQualityMetrics:
    return ModelQualityMetrics(model_name=name, overall_score=score)


def _simple_provider(
    name: str = "TestProvider",
    free: bool = True,
    models: list[ModelQualityMetrics] | None = None,
    expires: str | None = None,
    free_tier_details: str | None = None,
) -> ProviderInfo:
    return ProviderInfo(
        name=name,
        has_free_tier=free,
        models=models or [],
        expires=expires,
        free_tier_details=free_tier_details,
    )


# ===========================================================================
# TestModelQualityMetrics
# ===========================================================================


class TestModelQualityMetrics:
    """Unit tests for ModelQualityMetrics Pydantic model."""

    def test_required_fields_only(self):
        """Arrange/Act/Assert: minimal required fields succeed."""
        # Arrange & Act
        m = ModelQualityMetrics(model_name="gpt-4o-mini", overall_score=82.0)

        # Assert
        assert m.model_name == "gpt-4o-mini"
        assert m.overall_score == 82.0

    def test_optional_scores_default_none(self):
        """All optional sub-scores default to None when not provided."""
        # Arrange & Act
        m = _simple_metric()

        # Assert
        assert m.reasoning_score is None
        assert m.code_generation_score is None
        assert m.instruction_following_score is None
        assert m.creative_writing_score is None
        assert m.safety_score is None
        assert m.benchmark_source is None

    def test_best_for_defaults_to_empty_list(self):
        """best_for field defaults to an empty list."""
        m = _simple_metric()
        assert m.best_for == []

    def test_all_fields_populated(self):
        """All fields can be set without error."""
        # Arrange & Act
        m = ModelQualityMetrics(
            model_name="claude-3-5-sonnet",
            overall_score=90.0,
            reasoning_score=93.0,
            code_generation_score=92.0,
            instruction_following_score=94.0,
            creative_writing_score=91.0,
            safety_score=95.0,
            benchmark_source="LMSYS Chatbot Arena",
            last_benchmark_date="2025-10-15",
            best_for=["reasoning", "creative writing"],
        )

        # Assert
        assert m.reasoning_score == 93.0
        assert m.benchmark_source == "LMSYS Chatbot Arena"
        assert "reasoning" in m.best_for

    def test_overall_score_upper_bound_valid(self):
        """overall_score == 100 is valid."""
        m = ModelQualityMetrics(model_name="perfect", overall_score=100.0)
        assert m.overall_score == 100.0

    def test_overall_score_lower_bound_valid(self):
        """overall_score == 0 is valid."""
        m = ModelQualityMetrics(model_name="zero", overall_score=0.0)
        assert m.overall_score == 0.0

    def test_overall_score_above_100_raises(self):
        """overall_score > 100 raises ValidationError."""
        with pytest.raises(ValidationError):
            ModelQualityMetrics(model_name="bad", overall_score=101.0)

    def test_overall_score_below_0_raises(self):
        """overall_score < 0 raises ValidationError."""
        with pytest.raises(ValidationError):
            ModelQualityMetrics(model_name="bad", overall_score=-1.0)

    def test_optional_score_out_of_range_raises(self):
        """Optional sub-scores also enforce [0, 100] bounds."""
        with pytest.raises(ValidationError):
            ModelQualityMetrics(model_name="bad", overall_score=80.0, reasoning_score=105.0)

    def test_last_benchmark_date_has_default(self):
        """last_benchmark_date is auto-populated when not supplied."""
        m = _simple_metric()
        assert re.match(r"\d{4}-\d{2}-\d{2}", m.last_benchmark_date)

    def test_model_name_required(self):
        """Omitting model_name raises ValidationError."""
        with pytest.raises(ValidationError):
            ModelQualityMetrics(overall_score=80.0)  # type: ignore[call-arg]


# ===========================================================================
# TestProviderInfo
# ===========================================================================


class TestProviderInfo:
    """Unit tests for ProviderInfo Pydantic model."""

    def test_required_fields_only(self):
        """Minimal required fields succeed."""
        p = ProviderInfo(name="TestProvider", has_free_tier=True)
        assert p.name == "TestProvider"
        assert p.has_free_tier is True

    def test_optional_string_fields_default_none(self):
        """Optional string/bool fields default to None."""
        p = _simple_provider()
        assert p.free_tier_details is None
        assert p.rate_limits is None
        assert p.credit_card_required is None
        assert p.expires is None
        assert p.cost_after_free is None
        assert p.setup_url is None
        assert p.pricing_url is None
        assert p.notes is None

    def test_models_defaults_to_empty_list(self):
        """models list defaults to empty list."""
        p = _simple_provider()
        assert p.models == []

    def test_has_free_tier_false(self):
        """has_free_tier=False is a valid value."""
        p = ProviderInfo(name="Anthropic", has_free_tier=False)
        assert p.has_free_tier is False

    def test_with_embedded_models(self):
        """ProviderInfo can hold ModelQualityMetrics instances in models list."""
        # Arrange
        metric = _simple_metric("gpt-4o", 92.0)

        # Act
        p = ProviderInfo(name="OpenAI", has_free_tier=True, models=[metric])

        # Assert
        assert len(p.models) == 1
        assert p.models[0].model_name == "gpt-4o"

    def test_last_verified_has_default(self):
        """last_verified is auto-populated with a date string."""
        p = _simple_provider()
        assert re.match(r"\d{4}-\d{2}-\d{2}", p.last_verified)

    def test_name_required(self):
        """Omitting name raises ValidationError."""
        with pytest.raises(ValidationError):
            ProviderInfo(has_free_tier=True)  # type: ignore[call-arg]


# ===========================================================================
# TestFreeTierResearchRequest
# ===========================================================================


class TestFreeTierResearchRequest:
    """Unit tests for FreeTierResearchRequest Pydantic model."""

    def test_default_providers_list(self):
        """Default providers list contains exactly the 5 known providers."""
        req = FreeTierResearchRequest()
        assert req.providers == [
            "openai",
            "anthropic",
            "google-gemini",
            "openrouter",
            "ollama",
        ]

    def test_custom_providers_list(self):
        """Can override providers with a custom list."""
        req = FreeTierResearchRequest(providers=["openai", "ollama"])
        assert req.providers == ["openai", "ollama"]

    def test_generate_changelog_default_true(self):
        """generate_changelog defaults to True."""
        req = FreeTierResearchRequest()
        assert req.generate_changelog is True

    def test_generate_changelog_can_be_false(self):
        """generate_changelog can be explicitly set to False."""
        req = FreeTierResearchRequest(generate_changelog=False)
        assert req.generate_changelog is False

    def test_existing_guide_path_defaults_none(self):
        """existing_guide_path defaults to None."""
        req = FreeTierResearchRequest()
        assert req.existing_guide_path is None

    def test_output_path_defaults_none(self):
        """output_path defaults to None."""
        req = FreeTierResearchRequest()
        assert req.output_path is None

    def test_all_fields_supplied(self):
        """All fields can be supplied together without error."""
        req = FreeTierResearchRequest(
            providers=["openai"],
            existing_guide_path="/docs/guide.md",
            output_path="/docs/out.md",
            generate_changelog=False,
        )
        assert req.existing_guide_path == "/docs/guide.md"
        assert req.output_path == "/docs/out.md"
        assert req.generate_changelog is False


# ===========================================================================
# TestFreeTierResearchResponse
# ===========================================================================


class TestFreeTierResearchResponse:
    """Unit tests for FreeTierResearchResponse Pydantic model."""

    def test_providers_required(self):
        """Omitting providers raises ValidationError."""
        with pytest.raises(ValidationError):
            FreeTierResearchResponse()  # type: ignore[call-arg]

    def test_valid_minimal_response(self):
        """A response with just an empty providers dict is valid."""
        resp = FreeTierResearchResponse(providers={})
        assert resp.providers == {}

    def test_changelog_defaults_none(self):
        """changelog defaults to None."""
        resp = FreeTierResearchResponse(providers={})
        assert resp.changelog is None

    def test_updated_guide_defaults_none(self):
        """updated_guide defaults to None."""
        resp = FreeTierResearchResponse(providers={})
        assert resp.updated_guide is None

    def test_research_date_auto_populated(self):
        """research_date is auto-set to today's date (YYYY-MM-DD)."""
        resp = FreeTierResearchResponse(providers={})
        assert re.match(r"\d{4}-\d{2}-\d{2}", resp.research_date)


# ===========================================================================
# TestFreeTierResearchPrimitive
# ===========================================================================


class TestFreeTierResearchPrimitive:
    """Unit tests for FreeTierResearchPrimitive."""

    # ------------------------------------------------------------------
    # Instantiation
    # ------------------------------------------------------------------

    def test_instantiation_no_args(self):
        """FreeTierResearchPrimitive requires no constructor arguments."""
        primitive = FreeTierResearchPrimitive()
        assert primitive is not None

    def test_provider_data_has_five_providers(self):
        """_provider_data is pre-loaded with exactly 5 providers."""
        primitive = FreeTierResearchPrimitive()
        assert len(primitive._provider_data) == 5

    def test_provider_data_keys(self):
        """_provider_data contains all five expected provider keys."""
        primitive = FreeTierResearchPrimitive()
        expected = {"openai", "anthropic", "google-gemini", "openrouter", "ollama"}
        assert set(primitive._provider_data.keys()) == expected

    def test_provider_data_values_are_provider_info(self):
        """All _provider_data values are ProviderInfo instances."""
        primitive = FreeTierResearchPrimitive()
        for value in primitive._provider_data.values():
            assert isinstance(value, ProviderInfo)

    def test_openai_has_free_tier(self):
        """OpenAI provider data has has_free_tier=True."""
        primitive = FreeTierResearchPrimitive()
        assert primitive._provider_data["openai"].has_free_tier is True

    def test_anthropic_has_no_free_tier(self):
        """Anthropic provider data has has_free_tier=False."""
        primitive = FreeTierResearchPrimitive()
        assert primitive._provider_data["anthropic"].has_free_tier is False

    def test_all_providers_have_model_metrics(self):
        """Every hardcoded provider has at least one ModelQualityMetrics entry."""
        primitive = FreeTierResearchPrimitive()
        for key, info in primitive._provider_data.items():
            assert len(info.models) >= 1, f"Provider '{key}' has no model metrics"

    # ------------------------------------------------------------------
    # execute() — basic behaviour
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_execute_returns_response_type(self):
        """execute() returns a FreeTierResearchResponse instance."""
        # Arrange
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(providers=["openai"])
        context = _ctx()

        # Act
        response = await primitive.execute(request, context)

        # Assert
        assert isinstance(response, FreeTierResearchResponse)

    @pytest.mark.asyncio
    async def test_execute_filters_to_requested_providers(self):
        """execute() only populates providers that were requested."""
        # Arrange
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(providers=["openai", "ollama"])
        context = _ctx()

        # Act
        response = await primitive.execute(request, context)

        # Assert
        assert set(response.providers.keys()) == {"openai", "ollama"}

    @pytest.mark.asyncio
    async def test_execute_single_provider(self):
        """execute() works correctly for a single-provider request."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(providers=["google-gemini"])
        context = _ctx()

        response = await primitive.execute(request, context)

        assert len(response.providers) == 1
        assert "google-gemini" in response.providers

    @pytest.mark.asyncio
    async def test_execute_all_default_providers(self):
        """execute() returns all 5 providers when using default request."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest()
        context = _ctx()

        response = await primitive.execute(request, context)

        assert len(response.providers) == 5

    @pytest.mark.asyncio
    async def test_execute_unknown_provider_creates_placeholder(self):
        """Unknown providers get a placeholder ProviderInfo entry."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(providers=["nonexistent-provider"])
        context = _ctx()

        response = await primitive.execute(request, context)

        assert "nonexistent-provider" in response.providers
        assert isinstance(response.providers["nonexistent-provider"], ProviderInfo)

    @pytest.mark.asyncio
    async def test_execute_unknown_provider_has_no_free_tier(self):
        """Placeholder for unknown providers has has_free_tier=False."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(providers=["mystery-llm"])
        context = _ctx()

        response = await primitive.execute(request, context)

        assert response.providers["mystery-llm"].has_free_tier is False

    @pytest.mark.asyncio
    async def test_execute_unknown_provider_note_mentions_name(self):
        """Placeholder notes contain the unknown provider name."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(providers=["mystery-llm"])
        context = _ctx()

        response = await primitive.execute(request, context)

        notes = response.providers["mystery-llm"].notes or ""
        assert "mystery-llm" in notes

    @pytest.mark.asyncio
    async def test_execute_case_insensitive_provider_lookup(self):
        """Provider names are lowercased before lookup, preserving result key."""
        # Arrange — "OpenAI" (mixed case) should resolve to real OpenAI data
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(providers=["OpenAI"])
        context = _ctx()

        # Act
        response = await primitive.execute(request, context)

        # Assert — key is original case, value is real provider data
        assert "OpenAI" in response.providers
        assert response.providers["OpenAI"].has_free_tier is True

    # ------------------------------------------------------------------
    # execute() — changelog behaviour
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_execute_no_changelog_without_guide_path(self):
        """changelog is None when existing_guide_path is not provided."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(
            providers=["openai"],
            generate_changelog=True,
            existing_guide_path=None,
        )
        context = _ctx()

        response = await primitive.execute(request, context)

        assert response.changelog is None

    @pytest.mark.asyncio
    async def test_execute_no_changelog_when_disabled(self):
        """changelog is None when generate_changelog=False, even with a guide path."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(
            providers=["openai"],
            generate_changelog=False,
            existing_guide_path="/some/path.md",
        )
        context = _ctx()

        response = await primitive.execute(request, context)

        assert response.changelog is None

    @pytest.mark.asyncio
    async def test_execute_generates_changelog_with_guide_path(self):
        """changelog is a non-empty list when generate_changelog=True and path set."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(
            providers=["openai"],
            generate_changelog=True,
            existing_guide_path="/docs/guide.md",
        )
        context = _ctx()

        response = await primitive.execute(request, context)

        assert isinstance(response.changelog, list)
        assert len(response.changelog) > 0

    @pytest.mark.asyncio
    async def test_execute_changelog_entries_are_strings(self):
        """All changelog entries are strings."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(
            providers=["openai", "anthropic"],
            generate_changelog=True,
            existing_guide_path="/docs/guide.md",
        )
        context = _ctx()

        response = await primitive.execute(request, context)

        assert response.changelog is not None
        for entry in response.changelog:
            assert isinstance(entry, str)

    @pytest.mark.asyncio
    async def test_execute_changelog_mentions_provider_count(self):
        """Changelog content references the number of providers that were verified."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(
            providers=["openai", "anthropic"],
            generate_changelog=True,
            existing_guide_path="/docs/guide.md",
        )
        context = _ctx()

        response = await primitive.execute(request, context)

        assert response.changelog is not None
        combined = " ".join(response.changelog)
        assert "2" in combined

    # ------------------------------------------------------------------
    # execute() — guide generation behaviour
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_execute_no_guide_without_output_path(self):
        """updated_guide is None when output_path is not provided."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(providers=["openai"], output_path=None)
        context = _ctx()

        response = await primitive.execute(request, context)

        assert response.updated_guide is None

    @pytest.mark.asyncio
    async def test_execute_generates_guide_with_output_path(self):
        """updated_guide is a non-empty string when output_path is set."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(providers=["openai"], output_path="/tmp/guide.md")
        context = _ctx()

        response = await primitive.execute(request, context)

        assert isinstance(response.updated_guide, str)
        assert len(response.updated_guide) > 0

    @pytest.mark.asyncio
    async def test_execute_guide_contains_h1_header(self):
        """Generated guide has the expected top-level markdown heading."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(providers=["openai"], output_path="/tmp/guide.md")
        context = _ctx()

        response = await primitive.execute(request, context)

        assert response.updated_guide is not None
        assert "# Free LLM Access Guide" in response.updated_guide

    @pytest.mark.asyncio
    async def test_execute_guide_contains_provider_name(self):
        """Generated guide includes the provider's display name in the table."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(providers=["openai"], output_path="/tmp/guide.md")
        context = _ctx()

        response = await primitive.execute(request, context)

        assert response.updated_guide is not None
        assert "OpenAI API" in response.updated_guide

    @pytest.mark.asyncio
    async def test_execute_guide_checkmark_for_free_provider(self):
        """Guide shows ✅ Yes for providers with free tiers."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(
            providers=["openai"],  # has_free_tier=True
            output_path="/tmp/guide.md",
        )
        context = _ctx()

        response = await primitive.execute(request, context)

        assert response.updated_guide is not None
        assert "✅ Yes" in response.updated_guide

    @pytest.mark.asyncio
    async def test_execute_guide_cross_for_no_free_tier_provider(self):
        """Guide shows ❌ No for providers without free tiers."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(
            providers=["anthropic"],  # has_free_tier=False
            output_path="/tmp/guide.md",
        )
        context = _ctx()

        response = await primitive.execute(request, context)

        assert response.updated_guide is not None
        assert "❌ No" in response.updated_guide

    @pytest.mark.asyncio
    async def test_execute_guide_contains_table_header(self):
        """Generated guide markdown contains the comparison table header row."""
        primitive = FreeTierResearchPrimitive()
        request = FreeTierResearchRequest(
            providers=["openai", "ollama"], output_path="/tmp/guide.md"
        )
        context = _ctx()

        response = await primitive.execute(request, context)

        assert response.updated_guide is not None
        assert "| Provider |" in response.updated_guide

    # ------------------------------------------------------------------
    # generate_best_free_models_ranking()
    # ------------------------------------------------------------------

    def test_ranking_returns_list(self):
        """generate_best_free_models_ranking() returns a list."""
        primitive = FreeTierResearchPrimitive()
        result = primitive.generate_best_free_models_ranking(primitive._provider_data)
        assert isinstance(result, list)

    def test_ranking_tuples_have_three_elements(self):
        """Each ranked entry is a 3-element tuple."""
        primitive = FreeTierResearchPrimitive()
        result = primitive.generate_best_free_models_ranking(primitive._provider_data)
        for entry in result:
            assert len(entry) == 3

    def test_ranking_tuple_types(self):
        """Tuple elements are typed (int, ModelQualityMetrics, ProviderInfo)."""
        primitive = FreeTierResearchPrimitive()
        result = primitive.generate_best_free_models_ranking(primitive._provider_data)
        assert len(result) > 0
        rank, model, provider = result[0]
        assert isinstance(rank, int)
        assert isinstance(model, ModelQualityMetrics)
        assert isinstance(provider, ProviderInfo)

    def test_ranking_starts_at_rank_one(self):
        """The first entry has rank == 1."""
        primitive = FreeTierResearchPrimitive()
        result = primitive.generate_best_free_models_ranking(primitive._provider_data)
        assert result[0][0] == 1

    def test_ranking_ranks_are_sequential(self):
        """Ranks are consecutive integers starting at 1."""
        primitive = FreeTierResearchPrimitive()
        result = primitive.generate_best_free_models_ranking(primitive._provider_data)
        for i, (rank, _, _) in enumerate(result):
            assert rank == i + 1

    def test_ranking_empty_providers_returns_empty_list(self):
        """Empty providers dict produces an empty ranked list."""
        primitive = FreeTierResearchPrimitive()
        result = primitive.generate_best_free_models_ranking({})
        assert result == []

    def test_ranking_total_entries_equals_all_models(self):
        """Total ranked entries equals the sum of all models across providers."""
        primitive = FreeTierResearchPrimitive()
        total_models = sum(len(p.models) for p in primitive._provider_data.values())
        result = primitive.generate_best_free_models_ranking(primitive._provider_data)
        assert len(result) == total_models

    def test_ranking_free_tier_never_expires_boosts_rank(self):
        """Free provider (expires=Never) ranks above equal-quality paid provider."""
        # Arrange — same quality score (80), one free, one paid
        primitive = FreeTierResearchPrimitive()
        free_metric = _simple_metric("free-model", 80.0)
        paid_metric = _simple_metric("paid-model", 80.0)
        free_p = _simple_provider("FreeP", free=True, models=[free_metric], expires="Never")
        paid_p = _simple_provider("PaidP", free=False, models=[paid_metric])

        # Act
        result = primitive.generate_best_free_models_ranking({"fp": free_p, "pp": paid_p})

        # Assert — free: composite=(80*0.6)+(100*0.4)=88, paid: (80*0.6)+(0*0.4)=48
        assert result[0][1].model_name == "free-model"

    def test_ranking_higher_quality_wins_among_free_peers(self):
        """Among free-tier providers, higher overall_score produces a higher rank."""
        primitive = FreeTierResearchPrimitive()
        strong = _simple_metric("strong-model", 95.0)
        weak = _simple_metric("weak-model", 60.0)
        p_strong = _simple_provider("PS", free=True, models=[strong], expires="Never")
        p_weak = _simple_provider("PW", free=True, models=[weak], expires="Never")

        result = primitive.generate_best_free_models_ranking({"ps": p_strong, "pw": p_weak})

        assert result[0][1].model_name == "strong-model"

    def test_ranking_non_free_provider_still_included(self):
        """Providers without free tiers still appear in the ranking."""
        primitive = FreeTierResearchPrimitive()
        metric = _simple_metric("paid-model", 90.0)
        p = _simple_provider("PaidP", free=False, models=[metric])

        result = primitive.generate_best_free_models_ranking({"pp": p})

        assert len(result) == 1
        assert result[0][1].model_name == "paid-model"

    # ------------------------------------------------------------------
    # generate_fallback_strategy()
    # ------------------------------------------------------------------

    def test_fallback_strategy_returns_string(self):
        """generate_fallback_strategy() returns a string."""
        primitive = FreeTierResearchPrimitive()
        result = primitive.generate_fallback_strategy("code generation", primitive._provider_data)
        assert isinstance(result, str)

    def test_fallback_strategy_contains_fallback_primitive_import(self):
        """Generated code imports FallbackPrimitive."""
        primitive = FreeTierResearchPrimitive()
        result = primitive.generate_fallback_strategy("reasoning", primitive._provider_data)
        assert "FallbackPrimitive" in result

    def test_fallback_strategy_contains_workflow_context(self):
        """Generated code references WorkflowContext."""
        primitive = FreeTierResearchPrimitive()
        result = primitive.generate_fallback_strategy("reasoning", primitive._provider_data)
        assert "WorkflowContext" in result

    def test_fallback_strategy_contains_use_case_comment(self):
        """Generated code includes a comment naming the use case."""
        primitive = FreeTierResearchPrimitive()
        result = primitive.generate_fallback_strategy("code generation", primitive._provider_data)
        assert "code generation" in result

    def test_fallback_strategy_unknown_use_case_does_not_raise(self):
        """Unknown use-case strings fall back to overall_score without raising."""
        primitive = FreeTierResearchPrimitive()
        result = primitive.generate_fallback_strategy(
            "completely-unknown-use-case", primitive._provider_data
        )
        assert isinstance(result, str)
        assert "FallbackPrimitive" in result

    def test_fallback_strategy_hyphenated_use_case(self):
        """Hyphenated use-case form (e.g. 'code-generation') is handled."""
        primitive = FreeTierResearchPrimitive()
        result = primitive.generate_fallback_strategy("code-generation", primitive._provider_data)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_fallback_strategy_includes_primary_assignment(self):
        """Generated code defines a `primary` variable."""
        primitive = FreeTierResearchPrimitive()
        result = primitive.generate_fallback_strategy("reasoning", primitive._provider_data)
        assert "primary =" in result

    def test_fallback_strategy_empty_providers(self):
        """Empty providers dict still returns a valid code string."""
        primitive = FreeTierResearchPrimitive()
        result = primitive.generate_fallback_strategy("reasoning", {})
        assert isinstance(result, str)
        assert "FallbackPrimitive" in result

    # ------------------------------------------------------------------
    # _get_primitive_class_name()
    # ------------------------------------------------------------------

    def test_class_name_openai(self):
        """'OpenAI API' maps to OpenAIPrimitive."""
        primitive = FreeTierResearchPrimitive()
        assert primitive._get_primitive_class_name("OpenAI API") == "OpenAIPrimitive"

    def test_class_name_anthropic(self):
        """'Anthropic Claude API' maps to AnthropicPrimitive."""
        primitive = FreeTierResearchPrimitive()
        assert primitive._get_primitive_class_name("Anthropic Claude API") == "AnthropicPrimitive"

    def test_class_name_ollama(self):
        """'Ollama' maps to OllamaPrimitive."""
        primitive = FreeTierResearchPrimitive()
        assert primitive._get_primitive_class_name("Ollama") == "OllamaPrimitive"

    def test_class_name_google_gemini(self):
        """'Google Gemini' maps to GoogleGeminiPrimitive."""
        primitive = FreeTierResearchPrimitive()
        assert primitive._get_primitive_class_name("Google Gemini") == "GoogleGeminiPrimitive"

    def test_class_name_openrouter(self):
        """'OpenRouter BYOK' maps to OpenRouterPrimitive."""
        primitive = FreeTierResearchPrimitive()
        assert primitive._get_primitive_class_name("OpenRouter BYOK") == "OpenRouterPrimitive"

    def test_class_name_unknown_provider(self):
        """Unknown provider name maps to 'UnknownPrimitive'."""
        primitive = FreeTierResearchPrimitive()
        assert primitive._get_primitive_class_name("SomeFutureLLM") == "UnknownPrimitive"
