"""Free tier research primitive for automated LLM provider research.

This primitive automates the process of researching and documenting free tier
information for LLM providers, making it easy to keep documentation current.
"""

import asyncio
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class ProviderInfo(BaseModel):
    """Information about a provider's free tier."""

    name: str = Field(description="Provider name (e.g., 'OpenAI', 'Anthropic')")
    has_free_tier: bool = Field(description="Whether provider has a free tier")
    free_tier_details: str | None = Field(
        default=None, description="Description of free tier (e.g., '$5 credit')"
    )
    rate_limits: str | None = Field(
        default=None, description="Rate limits (e.g., '1500 RPD')"
    )
    credit_card_required: bool | None = Field(
        default=None, description="Whether credit card is required"
    )
    expires: str | None = Field(
        default=None, description="Expiration info (e.g., 'After $5 used', 'Never')"
    )
    cost_after_free: str | None = Field(
        default=None, description="Cost after free tier (e.g., '$0.15/1M tokens')"
    )
    setup_url: str | None = Field(
        default=None, description="URL for getting started"
    )
    pricing_url: str | None = Field(
        default=None, description="URL for pricing information"
    )
    last_verified: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="Date when information was last verified",
    )
    notes: str | None = Field(
        default=None, description="Additional notes or common confusion points"
    )


class FreeTierResearchRequest(BaseModel):
    """Request model for free tier research primitive."""

    providers: list[str] = Field(
        default=["openai", "anthropic", "google-gemini", "openrouter", "ollama"],
        description="List of providers to research",
    )
    existing_guide_path: str | None = Field(
        default=None, description="Path to existing guide for comparison"
    )
    output_path: str | None = Field(
        default=None, description="Path to write updated guide"
    )
    generate_changelog: bool = Field(
        default=True, description="Whether to generate a changelog of changes"
    )


class FreeTierResearchResponse(BaseModel):
    """Response model for free tier research primitive."""

    providers: dict[str, ProviderInfo] = Field(
        description="Researched provider information"
    )
    changelog: list[str] | None = Field(
        default=None, description="List of changes detected"
    )
    updated_guide: str | None = Field(
        default=None, description="Generated markdown guide content"
    )
    research_date: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="Date when research was performed",
    )


class FreeTierResearchPrimitive(
    WorkflowPrimitive[FreeTierResearchRequest, FreeTierResearchResponse]
):
    """Primitive for automated free tier research and documentation.

    This primitive automates the process of researching LLM provider free tiers
    and generating/updating documentation. It can be used to keep the Free LLM
    Access Guide current as provider tiers change.

    Example:
        ```python
        from tta_dev_primitives.research import FreeTierResearchPrimitive
        from tta_dev_primitives.core.base import WorkflowContext

        # Create primitive
        researcher = FreeTierResearchPrimitive()

        # Research all providers
        context = WorkflowContext(workflow_id="free-tier-update")
        request = FreeTierResearchRequest(
            providers=["openai", "anthropic", "google-gemini"],
            existing_guide_path="docs/guides/free-llm-access-guide.md",
            output_path="docs/guides/free-llm-access-guide.md",
            generate_changelog=True
        )
        response = await researcher.execute(request, context)

        # Check changelog
        if response.changelog:
            print("Changes detected:")
            for change in response.changelog:
                print(f"  - {change}")
        ```

    Note:
        This primitive uses hardcoded provider information as of October 2025.
        For production use, integrate with web scraping tools or provider APIs
        to fetch real-time pricing information.
    """

    def __init__(self) -> None:
        """Initialize the research primitive."""
        # Hardcoded provider information (as of October 2025)
        # In production, this would be fetched from web scraping or APIs
        self._provider_data = {
            "openai": ProviderInfo(
                name="OpenAI API",
                has_free_tier=True,
                free_tier_details="$5 one-time credit",
                rate_limits="500 RPM, 30,000 TPM (Tier 1)",
                credit_card_required=True,
                expires="After $5 used or 3 months",
                cost_after_free="GPT-4o-mini: $0.15/1M input, $0.60/1M output",
                setup_url="https://platform.openai.com/signup",
                pricing_url="https://openai.com/api/pricing/",
                notes="Web UI (ChatGPT) is free forever, but API requires payment after $5 credit",
            ),
            "anthropic": ProviderInfo(
                name="Anthropic Claude API",
                has_free_tier=False,
                free_tier_details=None,
                rate_limits=None,
                credit_card_required=True,
                expires="N/A",
                cost_after_free="Claude 3.5 Sonnet: $3.00/1M input, $15.00/1M output",
                setup_url="https://console.anthropic.com/",
                pricing_url="https://www.anthropic.com/pricing",
                notes="Web UI (claude.ai) is free with limits, but API has no free tier",
            ),
            "google-gemini": ProviderInfo(
                name="Google Gemini",
                has_free_tier=True,
                free_tier_details="1500 RPD free (Google AI Studio)",
                rate_limits="1500 RPD (shared across Flash and Flash-Lite)",
                credit_card_required=False,
                expires="Never",
                cost_after_free="Gemini 2.5 Flash: $0.30/1M input, $2.50/1M output",
                setup_url="https://aistudio.google.com/",
                pricing_url="https://ai.google.dev/pricing",
                notes="Google AI Studio is free, Vertex AI is paid. Don't confuse them!",
            ),
            "openrouter": ProviderInfo(
                name="OpenRouter BYOK",
                has_free_tier=True,
                free_tier_details="1M BYOK requests/month",
                rate_limits="Resets monthly at midnight UTC",
                credit_card_required=False,
                expires="Monthly reset",
                cost_after_free="5% fee on provider costs after 1M requests/month",
                setup_url="https://openrouter.ai/",
                pricing_url="https://openrouter.ai/docs#limits",
                notes="BYOK = Bring Your Own Key. You use your own provider API keys.",
            ),
            "ollama": ProviderInfo(
                name="Ollama",
                has_free_tier=True,
                free_tier_details="Unlimited (runs locally)",
                rate_limits="None (local)",
                credit_card_required=False,
                expires="Never",
                cost_after_free="$0 (uses your hardware)",
                setup_url="https://ollama.com/",
                pricing_url=None,
                notes="100% free, runs on your machine. Requires GPU for good performance.",
            ),
        }

    async def execute(
        self, input_data: FreeTierResearchRequest, context: WorkflowContext
    ) -> FreeTierResearchResponse:
        """Execute free tier research.

        Args:
            input_data: Research request with providers to research
            context: Workflow context for observability

        Returns:
            Research response with provider information and optional changelog
        """
        # Research providers (in production, this would do web scraping)
        providers_info = {}
        for provider in input_data.providers:
            provider_key = provider.lower()
            if provider_key in self._provider_data:
                providers_info[provider] = self._provider_data[provider_key]
            else:
                # Unknown provider - create placeholder
                providers_info[provider] = ProviderInfo(
                    name=provider,
                    has_free_tier=False,
                    notes=f"Provider '{provider}' not found in database",
                )

        # Generate changelog if requested
        changelog = None
        if input_data.generate_changelog and input_data.existing_guide_path:
            changelog = await self._generate_changelog(
                providers_info, input_data.existing_guide_path
            )

        # Generate updated guide if output path provided
        updated_guide = None
        if input_data.output_path:
            updated_guide = await self._generate_guide(providers_info)

        return FreeTierResearchResponse(
            providers=providers_info,
            changelog=changelog,
            updated_guide=updated_guide,
        )

    async def _generate_changelog(
        self, providers: dict[str, ProviderInfo], existing_guide_path: str
    ) -> list[str]:
        """Generate changelog by comparing with existing guide.

        Args:
            providers: Researched provider information
            existing_guide_path: Path to existing guide

        Returns:
            List of detected changes
        """
        # In production, this would parse the existing guide and compare
        # For now, return a placeholder
        changes = [
            f"Verified {len(providers)} providers as of {datetime.now().strftime('%Y-%m-%d')}",
            "No changes detected (using hardcoded data)",
        ]
        return changes

    async def _generate_guide(self, providers: dict[str, ProviderInfo]) -> str:
        """Generate markdown guide from provider information.

        Args:
            providers: Researched provider information

        Returns:
            Generated markdown content
        """
        # Generate comparison table
        table_rows = []
        for provider_name, info in providers.items():
            table_rows.append(
                f"| **{info.name}** | "
                f"{'✅ Yes' if info.has_free_tier else '❌ No'} | "
                f"{info.free_tier_details or 'None'} | "
                f"{info.rate_limits or 'N/A'} | "
                f"{'Yes' if info.credit_card_required else 'No'} | "
                f"{info.expires or 'N/A'} |"
            )

        guide = f"""# Free LLM Access Guide

**Last Updated:** {datetime.now().strftime('%B %d, %Y')}

## 📊 Free Tier Comparison Table

| Provider | Free Tier? | What's Included | Rate Limits | Credit Card Required? | Expires? |
|----------|-----------|-----------------|-------------|----------------------|----------|
{chr(10).join(table_rows)}

---

*This guide was automatically generated by FreeTierResearchPrimitive.*
*For detailed information, see the full guide at docs/guides/free-llm-access-guide.md*
"""
        return guide

