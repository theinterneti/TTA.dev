"""
Universal LLM Primitive - Base class for multi-provider, multi-coder, budget-aware LLM operations.

Supports:
- Any agentic coder (Cline, Copilot, Augment Code)
- Any model provider (OpenAI, Anthropic, Google, OpenRouter, HuggingFace)
- Any modality (VS Code, CLI, GitHub, browser)
- Budget profiles (FREE, CAREFUL, UNLIMITED)
- Cost tracking with justification

Based on user requirements:
- 50% free (Gemini, Kimi, DeepSeek)
- 50% paid (Claude Sonnet for complex work)
- User control over budget decisions
- Empirical model selection
"""

from __future__ import annotations

import os
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field
from tta_dev_primitives import WorkflowContext, WorkflowPrimitive


class UserBudgetProfile(str, Enum):
    """Budget profile determining model selection and cost management."""

    FREE = "free"  # Broke students, hobbyists - FREE models only
    CAREFUL = "careful"  # Solo devs, small teams - Mix free+paid with tracking
    UNLIMITED = "unlimited"  # Companies - Best model always, cost tracked but not limiting


class CoderType(str, Enum):
    """Agentic coder type."""

    AUTO = "auto"  # Auto-detect which coder is available
    COPILOT = "copilot"  # GitHub Copilot (VS Code, CLI, GitHub.com)
    CLINE = "cline"  # Cline VS Code extension
    AUGMENT = "augment"  # Augment Code VS Code extension


class ModalityType(str, Enum):
    """Environment where the coder operates."""

    VSCODE = "vscode"  # VS Code extension
    CLI = "cli"  # Terminal/command line
    GITHUB = "github"  # GitHub.com (PR reviews, issues)
    BROWSER = "browser"  # Web interfaces (ChatGPT, Claude, Gemini)


class ModelTier(str, Enum):
    """Model cost tier."""

    FREE = "free"  # Free tier models
    PAID = "paid"  # Paid models


@dataclass
class CostJustification:
    """Justification for using a paid model over free alternative."""

    reason: str
    """Why paid model was chosen over free."""

    free_alternatives_tried: list[str] = field(default_factory=list)
    """Free models that were considered."""

    expected_quality_delta: str | None = None
    """Expected quality improvement (e.g., '+25%')."""

    cost_estimate: str | None = None
    """Estimated cost for this request (e.g., '$0.15')."""

    context_factors: list[str] = field(default_factory=list)
    """Context that influenced decision (project usage, complexity, etc.)."""


class LLMRequest(BaseModel):
    """Request to an LLM."""

    prompt: str = Field(..., description="User prompt")
    complexity: Literal["simple", "medium", "high"] = Field(
        default="medium",
        description="Task complexity level",
    )
    modality: ModalityType = Field(
        default=ModalityType.VSCODE,
        description="Environment modality",
    )
    max_tokens: int | None = Field(default=None, description="Max response tokens")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    justification: CostJustification | None = Field(
        default=None,
        description="Justification for paid model usage",
    )


class LLMResponse(BaseModel):
    """Response from an LLM."""

    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model that generated response")
    coder: CoderType = Field(..., description="Coder that executed request")
    tier: ModelTier = Field(..., description="Model cost tier")
    cost_estimate: float | None = Field(
        default=None,
        description="Estimated cost in USD",
    )
    tokens_used: int | None = Field(default=None, description="Tokens consumed")
    quality_score: float | None = Field(
        default=None,
        description="Quality score if available",
    )


class UniversalLLMPrimitive(WorkflowPrimitive[LLMRequest, LLMResponse]):
    """
    Universal LLM primitive supporting any coder, model, modality, and budget profile.

    Features:
    - Auto-detect coder (Copilot, Cline, Augment)
    - Route to appropriate model based on complexity + budget
    - Track cost AND justification for paid usage
    - Fallback chain with free-first preference
    - Empirical model selection

    Example:
        >>> from tta_dev_primitives.integrations import UniversalLLMPrimitive
        >>> from tta_dev_primitives.integrations.budget import UserBudgetProfile
        >>>
        >>> llm = UniversalLLMPrimitive(
        ...     coder="auto",
        ...     budget_profile=UserBudgetProfile.CAREFUL,
        ...     monthly_limit=50.00,
        ...     free_models=["gemini-1.5-pro", "gemini-1.5-flash"],
        ...     paid_models=["claude-3.5-sonnet"],
        ... )
        >>>
        >>> result = await llm.execute(
        ...     LLMRequest(
        ...         prompt="Build a dashboard",
        ...         complexity="high",
        ...         justification=CostJustification(
        ...             reason="Dashboard requires complex visualization logic",
        ...             free_alternatives_tried=["gemini-1.5-pro"],
        ...             expected_quality_delta="+25%",
        ...         )
        ...     ),
        ...     context
        ... )
    """

    def __init__(
        self,
        coder: CoderType | str = CoderType.AUTO,
        budget_profile: UserBudgetProfile = UserBudgetProfile.CAREFUL,
        monthly_limit: float | None = None,
        free_models: list[str] | None = None,
        paid_models: list[str] | None = None,
        prefer_free_when_close: bool = True,
        quality_threshold: float = 0.85,
        require_justification_for_paid: bool = True,
    ) -> None:
        """
        Initialize UniversalLLMPrimitive.

        Args:
            coder: Which coder to use (auto-detect by default)
            budget_profile: Budget profile (FREE, CAREFUL, UNLIMITED)
            monthly_limit: Monthly spending limit in USD (for CAREFUL mode)
            free_models: List of free models to use
            paid_models: List of paid models to use
            prefer_free_when_close: Use free if quality within threshold
            quality_threshold: Quality threshold for free models (0-1)
            require_justification_for_paid: Require justification for paid usage
        """
        super().__init__()
        self.coder = CoderType(coder) if isinstance(coder, str) else coder
        self.budget_profile = budget_profile
        self.monthly_limit = monthly_limit
        self.prefer_free_when_close = prefer_free_when_close
        self.quality_threshold = quality_threshold
        self.require_justification_for_paid = require_justification_for_paid

        # Default free models (based on user's stack)
        self.free_models = free_models or [
            "gemini-1.5-pro",  # Primary free (Google AI Studio)
            "gemini-1.5-flash",  # Fast free
            "kimi",  # Cline fallback
            "deepseek",  # Cline fallback
        ]

        # Default paid models (based on user's preferences)
        self.paid_models = paid_models or [
            "claude-3.5-sonnet",  # Worth the cost for complex work
        ]

        # Cost tracking
        self.total_spend = 0.0
        self.request_count = 0
        self.free_tier_requests = 0
        self.paid_requests = 0
        self.justifications: list[CostJustification] = []

    async def execute(
        self,
        input_data: LLMRequest,
        context: WorkflowContext,
    ) -> LLMResponse:
        """
        Execute LLM request with budget-aware model selection.

        Args:
            input_data: LLM request with prompt and parameters
            context: Workflow context

        Returns:
            LLM response with content and metadata
        """
        # Auto-detect coder if needed
        if self.coder == CoderType.AUTO:
            detected_coder = self._detect_coder()
        else:
            detected_coder = self.coder

        # Select model based on complexity and budget
        selected_model, tier = self._select_model(
            complexity=input_data.complexity,
            justification=input_data.justification,
        )

        # Validate justification if using paid model
        if tier == ModelTier.PAID and self.require_justification_for_paid:
            if not input_data.justification:
                raise ValueError(
                    f"Justification required for paid model '{selected_model}'. "
                    f"Provide CostJustification with reason and alternatives tried.",
                )

        # Execute with selected coder and model
        response = await self._execute_with_coder(
            coder=detected_coder,
            model=selected_model,
            request=input_data,
            context=context,
        )

        # Track usage
        self._track_usage(response, input_data.justification)

        return response

    def _detect_coder(self) -> CoderType:
        """
        Auto-detect which agentic coder is available.

        Priority: Copilot > Augment > Cline

        Returns:
            Detected coder type
        """
        # Check for Copilot (env var or VS Code extension)
        if os.getenv("GITHUB_TOKEN") or os.getenv("COPILOT_API_KEY"):
            return CoderType.COPILOT

        # Check for Augment Code (env var)
        if os.getenv("AUGMENT_API_KEY"):
            return CoderType.AUGMENT

        # Check for Cline (Google AI Studio key for Gemini)
        if os.getenv("GOOGLE_AI_STUDIO_API_KEY"):
            return CoderType.CLINE

        # Default to Cline (most flexible with free models)
        return CoderType.CLINE

    def _select_model(
        self,
        complexity: Literal["simple", "medium", "high"],
        justification: CostJustification | None,
    ) -> tuple[str, ModelTier]:
        """
        Select appropriate model based on complexity and budget profile.

        Args:
            complexity: Task complexity
            justification: Cost justification if using paid

        Returns:
            (model_name, tier)
        """
        # FREE mode: Only use free models
        if self.budget_profile == UserBudgetProfile.FREE:
            if complexity == "simple":
                return "gemini-1.5-flash", ModelTier.FREE
            else:
                return "gemini-1.5-pro", ModelTier.FREE

        # UNLIMITED mode: Always use best model
        if self.budget_profile == UserBudgetProfile.UNLIMITED:
            if complexity == "high":
                return "claude-3.5-sonnet", ModelTier.PAID
            elif complexity == "medium":
                return "gemini-1.5-pro", ModelTier.FREE  # Good enough for medium
            else:
                return "gemini-1.5-flash", ModelTier.FREE

        # CAREFUL mode: Balance free and paid based on complexity
        if complexity == "simple":
            return "gemini-1.5-flash", ModelTier.FREE

        if complexity == "medium":
            # Use free unless justification shows significant quality delta
            if justification and self._quality_delta_justifies_paid(justification):
                return "claude-3.5-sonnet", ModelTier.PAID
            return "gemini-1.5-pro", ModelTier.FREE

        if complexity == "high":
            # High complexity: Use paid if budget allows and justified
            if self._budget_allows_paid() and justification:
                return "claude-3.5-sonnet", ModelTier.PAID
            # Fallback to best free model
            return "gemini-1.5-pro", ModelTier.FREE

        return "gemini-1.5-pro", ModelTier.FREE

    def _quality_delta_justifies_paid(self, justification: CostJustification) -> bool:
        """Check if quality delta justifies paid usage."""
        if not justification.expected_quality_delta:
            return False

        # Extract percentage (e.g., "+25%" -> 0.25)
        try:
            delta_str = justification.expected_quality_delta.strip("+%")
            delta = float(delta_str) / 100
            return delta >= (1 - self.quality_threshold)
        except ValueError:
            return False

    def _budget_allows_paid(self) -> bool:
        """Check if budget allows paid model usage."""
        if not self.monthly_limit:
            return True  # No limit set

        # Check if we're under 80% of budget
        return self.total_spend < (self.monthly_limit * 0.8)

    @abstractmethod
    async def _execute_with_coder(
        self,
        coder: CoderType,
        model: str,
        request: LLMRequest,
        context: WorkflowContext,
    ) -> LLMResponse:
        """
        Execute request with specific coder and model.

        Must be implemented by subclasses for each coder type.

        Args:
            coder: Which coder to use
            model: Which model to use
            request: LLM request
            context: Workflow context

        Returns:
            LLM response
        """
        pass

    def _track_usage(
        self,
        response: LLMResponse,
        justification: CostJustification | None,
    ) -> None:
        """Track usage statistics and costs."""
        self.request_count += 1

        if response.tier == ModelTier.FREE:
            self.free_tier_requests += 1
        else:
            self.paid_requests += 1
            if response.cost_estimate:
                self.total_spend += response.cost_estimate
            if justification:
                self.justifications.append(justification)

    def get_budget_report(self) -> dict[str, Any]:
        """
        Get current budget usage report.

        Returns:
            Budget statistics
        """
        return {
            "total_requests": self.request_count,
            "free_tier_requests": self.free_tier_requests,
            "paid_requests": self.paid_requests,
            "free_tier_percentage": (
                self.free_tier_requests / self.request_count * 100 if self.request_count > 0 else 0
            ),
            "total_spend": self.total_spend,
            "budget_limit": self.monthly_limit,
            "budget_used_percentage": (
                self.total_spend / self.monthly_limit * 100 if self.monthly_limit else 0
            ),
            "justifications_count": len(self.justifications),
        }
