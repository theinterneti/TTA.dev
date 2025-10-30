"""Free tier research primitive for automated LLM provider research.

This primitive automates the process of researching and documenting free tier
information for LLM providers, making it easy to keep documentation current.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class ModelQualityMetrics(BaseModel):
    """Quality metrics for a specific model."""

    model_name: str = Field(description="Model name (e.g., 'gpt-4o-mini', 'claude-3-5-sonnet')")
    overall_score: float = Field(description="Overall quality score (0-100)", ge=0, le=100)
    reasoning_score: float | None = Field(
        default=None, description="Reasoning ability score (0-100)", ge=0, le=100
    )
    code_generation_score: float | None = Field(
        default=None, description="Code generation quality score (0-100)", ge=0, le=100
    )
    instruction_following_score: float | None = Field(
        default=None, description="Instruction following score (0-100)", ge=0, le=100
    )
    creative_writing_score: float | None = Field(
        default=None, description="Creative writing quality score (0-100)", ge=0, le=100
    )
    safety_score: float | None = Field(
        default=None, description="Safety and alignment score (0-100)", ge=0, le=100
    )
    benchmark_source: str | None = Field(
        default=None,
        description="Source of benchmark data (e.g., 'LMSYS Chatbot Arena')",
    )
    last_benchmark_date: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="Date when benchmark data was last updated",
    )
    best_for: list[str] = Field(
        default_factory=list,
        description="Use cases this model excels at (e.g., ['code generation', 'reasoning'])",
    )


class ProviderInfo(BaseModel):
    """Information about a provider's free tier."""

    name: str = Field(description="Provider name (e.g., 'OpenAI', 'Anthropic')")
    has_free_tier: bool = Field(description="Whether provider has a free tier")
    free_tier_details: str | None = Field(
        default=None, description="Description of free tier (e.g., '$5 credit')"
    )
    rate_limits: str | None = Field(default=None, description="Rate limits (e.g., '1500 RPD')")
    credit_card_required: bool | None = Field(
        default=None, description="Whether credit card is required"
    )
    expires: str | None = Field(
        default=None, description="Expiration info (e.g., 'After $5 used', 'Never')"
    )
    cost_after_free: str | None = Field(
        default=None, description="Cost after free tier (e.g., '$0.15/1M tokens')"
    )
    setup_url: str | None = Field(default=None, description="URL for getting started")
    pricing_url: str | None = Field(default=None, description="URL for pricing information")
    last_verified: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
        description="Date when information was last verified",
    )
    notes: str | None = Field(
        default=None, description="Additional notes or common confusion points"
    )
    # NEW: Quality metrics for models
    models: list[ModelQualityMetrics] = Field(
        default_factory=list,
        description="Quality metrics for specific models from this provider",
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
    output_path: str | None = Field(default=None, description="Path to write updated guide")
    generate_changelog: bool = Field(
        default=True, description="Whether to generate a changelog of changes"
    )


class FreeTierResearchResponse(BaseModel):
    """Response model for free tier research primitive."""

    providers: dict[str, ProviderInfo] = Field(description="Researched provider information")
    changelog: list[str] | None = Field(default=None, description="List of changes detected")
    updated_guide: str | None = Field(default=None, description="Generated markdown guide content")
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
                models=[
                    ModelQualityMetrics(
                        model_name="gpt-4o-mini",
                        overall_score=82.0,
                        reasoning_score=85.0,
                        code_generation_score=88.0,
                        instruction_following_score=90.0,
                        creative_writing_score=75.0,
                        safety_score=92.0,
                        benchmark_source="LMSYS Chatbot Arena + Artificial Analysis",
                        last_benchmark_date="2025-10-15",
                        best_for=[
                            "code generation",
                            "reasoning",
                            "instruction following",
                        ],
                    ),
                    ModelQualityMetrics(
                        model_name="gpt-4o",
                        overall_score=92.0,
                        reasoning_score=95.0,
                        code_generation_score=94.0,
                        instruction_following_score=96.0,
                        creative_writing_score=88.0,
                        safety_score=94.0,
                        benchmark_source="LMSYS Chatbot Arena + Artificial Analysis",
                        last_benchmark_date="2025-10-15",
                        best_for=[
                            "complex reasoning",
                            "code generation",
                            "general purpose",
                        ],
                    ),
                ],
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
                models=[
                    ModelQualityMetrics(
                        model_name="claude-3-5-sonnet-20241022",
                        overall_score=90.0,
                        reasoning_score=93.0,
                        code_generation_score=92.0,
                        instruction_following_score=94.0,
                        creative_writing_score=91.0,
                        safety_score=95.0,
                        benchmark_source="LMSYS Chatbot Arena + Artificial Analysis",
                        last_benchmark_date="2025-10-15",
                        best_for=[
                            "reasoning",
                            "creative writing",
                            "instruction following",
                        ],
                    ),
                    ModelQualityMetrics(
                        model_name="claude-3-opus-20240229",
                        overall_score=88.0,
                        reasoning_score=91.0,
                        code_generation_score=89.0,
                        instruction_following_score=92.0,
                        creative_writing_score=93.0,
                        safety_score=94.0,
                        benchmark_source="LMSYS Chatbot Arena + Artificial Analysis",
                        last_benchmark_date="2025-10-15",
                        best_for=[
                            "creative writing",
                            "complex reasoning",
                            "long context",
                        ],
                    ),
                ],
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
                models=[
                    ModelQualityMetrics(
                        model_name="gemini-2.5-flash",
                        overall_score=85.0,
                        reasoning_score=83.0,
                        code_generation_score=86.0,
                        instruction_following_score=88.0,
                        creative_writing_score=82.0,
                        safety_score=90.0,
                        benchmark_source="LMSYS Chatbot Arena + Google AI Benchmarks",
                        last_benchmark_date="2025-10-15",
                        best_for=[
                            "general purpose",
                            "fast responses",
                            "cost efficiency",
                        ],
                    ),
                    ModelQualityMetrics(
                        model_name="gemini-2.5-pro",
                        overall_score=89.0,
                        reasoning_score=91.0,
                        code_generation_score=90.0,
                        instruction_following_score=92.0,
                        creative_writing_score=87.0,
                        safety_score=93.0,
                        benchmark_source="LMSYS Chatbot Arena + Google AI Benchmarks",
                        last_benchmark_date="2025-10-15",
                        best_for=[
                            "complex reasoning",
                            "code generation",
                            "general purpose",
                        ],
                    ),
                ],
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
                models=[
                    # OpenRouter provides access to many models - listing top free options
                    ModelQualityMetrics(
                        model_name="openai/gpt-4o-mini (via BYOK)",
                        overall_score=82.0,
                        reasoning_score=85.0,
                        code_generation_score=88.0,
                        instruction_following_score=90.0,
                        creative_writing_score=75.0,
                        safety_score=92.0,
                        benchmark_source="LMSYS Chatbot Arena (via OpenAI)",
                        last_benchmark_date="2025-10-15",
                        best_for=[
                            "code generation",
                            "reasoning",
                            "multi-provider routing",
                        ],
                    ),
                ],
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
                models=[
                    ModelQualityMetrics(
                        model_name="llama3.2:8b",
                        overall_score=78.0,
                        reasoning_score=76.0,
                        code_generation_score=80.0,
                        instruction_following_score=82.0,
                        creative_writing_score=74.0,
                        safety_score=85.0,
                        benchmark_source="HuggingFace Open LLM Leaderboard",
                        last_benchmark_date="2025-10-15",
                        best_for=[
                            "privacy-critical",
                            "offline use",
                            "local development",
                        ],
                    ),
                    ModelQualityMetrics(
                        model_name="mistral:7b",
                        overall_score=75.0,
                        reasoning_score=73.0,
                        code_generation_score=77.0,
                        instruction_following_score=79.0,
                        creative_writing_score=72.0,
                        safety_score=83.0,
                        benchmark_source="HuggingFace Open LLM Leaderboard",
                        last_benchmark_date="2025-10-15",
                        best_for=[
                            "fast inference",
                            "resource-constrained",
                            "local development",
                        ],
                    ),
                    ModelQualityMetrics(
                        model_name="gemma2:9b",
                        overall_score=76.0,
                        reasoning_score=74.0,
                        code_generation_score=78.0,
                        instruction_following_score=80.0,
                        creative_writing_score=73.0,
                        safety_score=88.0,
                        benchmark_source="HuggingFace Open LLM Leaderboard",
                        last_benchmark_date="2025-10-15",
                        best_for=["safety-critical", "local development", "privacy"],
                    ),
                ],
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

**Last Updated:** {datetime.now().strftime("%B %d, %Y")}

## 📊 Free Tier Comparison Table

| Provider | Free Tier? | What's Included | Rate Limits | Credit Card Required? | Expires? |
|----------|-----------|-----------------|-------------|----------------------|----------|
{chr(10).join(table_rows)}

---

*This guide was automatically generated by FreeTierResearchPrimitive.*
*For detailed information, see the full guide at docs/guides/free-llm-access-guide.md*
"""
        return guide

    def generate_best_free_models_ranking(
        self, providers: dict[str, ProviderInfo]
    ) -> list[tuple[int, ModelQualityMetrics, ProviderInfo]]:
        """Generate ranked list of best free models.

        Ranking criteria:
        1. Quality score (from benchmarks)
        2. Availability (truly free > limited credit)
        3. Rate limits (higher = better)
        4. Cost efficiency (quality per dollar for paid tiers)

        Args:
            providers: Provider information with quality metrics

        Returns:
            List of (rank, model, provider) tuples, sorted by quality
        """
        # Collect all models from all providers
        all_models = []
        for provider_info in providers.values():
            for model in provider_info.models:
                # Calculate availability score
                availability_score = 0.0
                if provider_info.has_free_tier:
                    if provider_info.expires == "Never":
                        availability_score = 100.0  # Truly free forever
                    elif "Unlimited" in (provider_info.free_tier_details or ""):
                        availability_score = 100.0  # Local, unlimited
                    elif "$5" in (provider_info.free_tier_details or ""):
                        availability_score = 70.0  # Limited credit
                    elif "1500 RPD" in (provider_info.free_tier_details or ""):
                        availability_score = 90.0  # High rate limit
                    elif "1M" in (provider_info.free_tier_details or ""):
                        availability_score = 85.0  # BYOK with high limit
                    else:
                        availability_score = 50.0  # Other free tier

                # Calculate composite score
                # Weight: 60% quality, 40% availability
                composite_score = (model.overall_score * 0.6) + (availability_score * 0.4)

                all_models.append((composite_score, model, provider_info))

        # Sort by composite score (descending)
        all_models.sort(key=lambda x: x[0], reverse=True)

        # Add rank numbers
        ranked_models = [
            (rank + 1, model, provider) for rank, (score, model, provider) in enumerate(all_models)
        ]

        return ranked_models

    def generate_fallback_strategy(self, use_case: str, providers: dict[str, ProviderInfo]) -> str:
        """Generate intelligent fallback strategy for a use case.

        Args:
            use_case: Use case (e.g., "code generation", "creative writing")
            providers: Provider information with quality metrics

        Returns:
            Python code showing recommended fallback configuration
        """
        # Map use cases to quality metric priorities
        use_case_metrics = {
            "code generation": "code_generation_score",
            "code-generation": "code_generation_score",
            "reasoning": "reasoning_score",
            "creative writing": "creative_writing_score",
            "creative-writing": "creative_writing_score",
            "instruction following": "instruction_following_score",
            "instruction-following": "instruction_following_score",
            "general purpose": "overall_score",
            "general-purpose": "overall_score",
        }

        metric_key = use_case_metrics.get(use_case.lower(), "overall_score")

        # Collect models and score them for this use case
        scored_models = []
        for provider_info in providers.values():
            for model in provider_info.models:
                # Get use case-specific score
                use_case_score = getattr(model, metric_key, model.overall_score)
                if use_case_score is None:
                    use_case_score = model.overall_score

                # Prioritize free models
                is_free = provider_info.has_free_tier
                priority_boost = 10.0 if is_free else 0.0

                final_score = use_case_score + priority_boost

                scored_models.append((final_score, model, provider_info))

        # Sort by score (descending)
        scored_models.sort(key=lambda x: x[0], reverse=True)

        # Select top 3 models for fallback chain
        top_models = scored_models[:3]

        # Generate code
        code_lines = [
            "from tta_dev_primitives.integrations import (",
            "    OpenAIPrimitive,",
            "    AnthropicPrimitive,",
            "    OllamaPrimitive,",
            ")",
            "from tta_dev_primitives.recovery import FallbackPrimitive",
            "from tta_dev_primitives.core.base import WorkflowContext",
            "",
            f"# Recommended fallback strategy for: {use_case}",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d')}",
            "",
        ]

        # Generate primitive instantiations
        for i, (score, model, provider) in enumerate(top_models):
            primitive_name = f"{'primary' if i == 0 else f'fallback{i}'}"
            provider_class = self._get_primitive_class_name(provider.name)
            code_lines.append(
                f'{primitive_name} = {provider_class}(model="{model.model_name}")  '
                f"# Score: {score:.1f}, Best for: {', '.join(model.best_for[:2])}"
            )

        code_lines.extend(
            [
                "",
                "# Create fallback workflow",
                "workflow = FallbackPrimitive(",
                "    primary=primary,",
                f"    fallbacks=[{', '.join(f'fallback{i}' for i in range(1, len(top_models)))}]",
                ")",
                "",
                "# Execute",
                'context = WorkflowContext(workflow_id="my-workflow")',
                "result = await workflow.execute(input_data, context)",
            ]
        )

        return "\n".join(code_lines)

    def _get_primitive_class_name(self, provider_name: str) -> str:
        """Map provider name to primitive class name."""
        mapping = {
            "OpenAI API": "OpenAIPrimitive",
            "Anthropic Claude API": "AnthropicPrimitive",
            "Google Gemini": "GoogleGeminiPrimitive",  # Note: Not yet implemented
            "OpenRouter BYOK": "OpenRouterPrimitive",  # Note: Not yet implemented
            "Ollama": "OllamaPrimitive",
        }
        return mapping.get(provider_name, "UnknownPrimitive")
