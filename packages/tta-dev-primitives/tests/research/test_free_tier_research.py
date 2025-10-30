"""Tests for FreeTierResearchPrimitive."""

import pytest

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.research import (
    FreeTierResearchPrimitive,
    FreeTierResearchRequest,
    ProviderInfo,
)


@pytest.mark.asyncio
class TestFreeTierResearchPrimitive:
    """Test suite for FreeTierResearchPrimitive."""

    async def test_research_all_providers(self):
        """Test researching all default providers."""
        primitive = FreeTierResearchPrimitive()
        context = WorkflowContext(workflow_id="test-research")

        request = FreeTierResearchRequest()
        response = await primitive.execute(request, context)

        # Verify all providers were researched
        assert len(response.providers) == 5
        assert "openai" in response.providers
        assert "anthropic" in response.providers
        assert "google-gemini" in response.providers
        assert "openrouter" in response.providers
        assert "ollama" in response.providers

        # Verify provider info structure
        for provider_name, info in response.providers.items():
            assert isinstance(info, ProviderInfo)
            assert info.name is not None
            assert isinstance(info.has_free_tier, bool)
            assert info.last_verified is not None

    async def test_research_specific_providers(self):
        """Test researching specific providers only."""
        primitive = FreeTierResearchPrimitive()
        context = WorkflowContext(workflow_id="test-specific")

        request = FreeTierResearchRequest(
            providers=["openai", "ollama"],
            generate_changelog=False,
        )
        response = await primitive.execute(request, context)

        # Verify only requested providers
        assert len(response.providers) == 2
        assert "openai" in response.providers
        assert "ollama" in response.providers
        assert "anthropic" not in response.providers

    async def test_openai_provider_info(self):
        """Test OpenAI provider information accuracy."""
        primitive = FreeTierResearchPrimitive()
        context = WorkflowContext(workflow_id="test-openai")

        request = FreeTierResearchRequest(providers=["openai"])
        response = await primitive.execute(request, context)

        openai_info = response.providers["openai"]
        assert openai_info.name == "OpenAI API"
        assert openai_info.has_free_tier is True
        assert "$5" in openai_info.free_tier_details
        assert openai_info.credit_card_required is True
        assert openai_info.setup_url is not None
        assert "ChatGPT" in openai_info.notes  # Web UI vs API confusion

    async def test_anthropic_provider_info(self):
        """Test Anthropic provider information accuracy."""
        primitive = FreeTierResearchPrimitive()
        context = WorkflowContext(workflow_id="test-anthropic")

        request = FreeTierResearchRequest(providers=["anthropic"])
        response = await primitive.execute(request, context)

        anthropic_info = response.providers["anthropic"]
        assert anthropic_info.name == "Anthropic Claude API"
        assert anthropic_info.has_free_tier is False  # No free API tier
        assert anthropic_info.credit_card_required is True
        assert "claude.ai" in anthropic_info.notes  # Web UI is free

    async def test_google_gemini_provider_info(self):
        """Test Google Gemini provider information accuracy."""
        primitive = FreeTierResearchPrimitive()
        context = WorkflowContext(workflow_id="test-gemini")

        request = FreeTierResearchRequest(providers=["google-gemini"])
        response = await primitive.execute(request, context)

        gemini_info = response.providers["google-gemini"]
        assert gemini_info.name == "Google Gemini"
        assert gemini_info.has_free_tier is True
        assert "1500 RPD" in gemini_info.free_tier_details
        assert gemini_info.credit_card_required is False
        assert gemini_info.expires == "Never"
        assert "AI Studio" in gemini_info.notes  # AI Studio vs Vertex AI

    async def test_openrouter_provider_info(self):
        """Test OpenRouter provider information accuracy."""
        primitive = FreeTierResearchPrimitive()
        context = WorkflowContext(workflow_id="test-openrouter")

        request = FreeTierResearchRequest(providers=["openrouter"])
        response = await primitive.execute(request, context)

        openrouter_info = response.providers["openrouter"]
        assert openrouter_info.name == "OpenRouter BYOK"
        assert openrouter_info.has_free_tier is True
        assert "1M" in openrouter_info.free_tier_details
        assert openrouter_info.credit_card_required is False
        assert "BYOK" in openrouter_info.notes  # BYOK explanation

    async def test_ollama_provider_info(self):
        """Test Ollama provider information accuracy."""
        primitive = FreeTierResearchPrimitive()
        context = WorkflowContext(workflow_id="test-ollama")

        request = FreeTierResearchRequest(providers=["ollama"])
        response = await primitive.execute(request, context)

        ollama_info = response.providers["ollama"]
        assert ollama_info.name == "Ollama"
        assert ollama_info.has_free_tier is True
        assert "Unlimited" in ollama_info.free_tier_details
        assert ollama_info.credit_card_required is False
        assert ollama_info.expires == "Never"
        assert ollama_info.cost_after_free == "$0 (uses your hardware)"

    async def test_unknown_provider(self):
        """Test handling of unknown provider."""
        primitive = FreeTierResearchPrimitive()
        context = WorkflowContext(workflow_id="test-unknown")

        request = FreeTierResearchRequest(providers=["unknown-provider"])
        response = await primitive.execute(request, context)

        # Should create placeholder for unknown provider
        assert "unknown-provider" in response.providers
        unknown_info = response.providers["unknown-provider"]
        assert unknown_info.has_free_tier is False
        assert "not found" in unknown_info.notes

    async def test_changelog_generation(self):
        """Test changelog generation."""
        primitive = FreeTierResearchPrimitive()
        context = WorkflowContext(workflow_id="test-changelog")

        request = FreeTierResearchRequest(
            providers=["openai"],
            existing_guide_path="docs/guides/free-llm-access-guide.md",
            generate_changelog=True,
        )
        response = await primitive.execute(request, context)

        # Verify changelog was generated
        assert response.changelog is not None
        assert len(response.changelog) > 0
        assert isinstance(response.changelog[0], str)

    async def test_guide_generation(self):
        """Test markdown guide generation."""
        primitive = FreeTierResearchPrimitive()
        context = WorkflowContext(workflow_id="test-guide")

        request = FreeTierResearchRequest(
            providers=["openai", "ollama"],
            output_path="test-output.md",
        )
        response = await primitive.execute(request, context)

        # Verify guide was generated
        assert response.updated_guide is not None
        assert "# Free LLM Access Guide" in response.updated_guide
        assert "OpenAI API" in response.updated_guide
        assert "Ollama" in response.updated_guide
        assert "| Provider |" in response.updated_guide  # Table header

    async def test_no_changelog_when_disabled(self):
        """Test that changelog is not generated when disabled."""
        primitive = FreeTierResearchPrimitive()
        context = WorkflowContext(workflow_id="test-no-changelog")

        request = FreeTierResearchRequest(
            providers=["openai"],
            generate_changelog=False,
        )
        response = await primitive.execute(request, context)

        # Verify no changelog
        assert response.changelog is None

    async def test_no_guide_when_no_output_path(self):
        """Test that guide is not generated when no output path."""
        primitive = FreeTierResearchPrimitive()
        context = WorkflowContext(workflow_id="test-no-guide")

        request = FreeTierResearchRequest(
            providers=["openai"],
            output_path=None,
        )
        response = await primitive.execute(request, context)

        # Verify no guide
        assert response.updated_guide is None

    async def test_research_date_included(self):
        """Test that research date is included in response."""
        primitive = FreeTierResearchPrimitive()
        context = WorkflowContext(workflow_id="test-date")

        request = FreeTierResearchRequest(providers=["openai"])
        response = await primitive.execute(request, context)

        # Verify research date
        assert response.research_date is not None
        assert len(response.research_date) == 10  # YYYY-MM-DD format
        assert "-" in response.research_date

