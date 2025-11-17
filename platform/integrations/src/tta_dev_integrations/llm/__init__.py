"""
LLM integration primitives for TTA.dev.

Provides universal, budget-aware LLM integration supporting:
- Multiple agentic coders (Cline, Copilot, Augment Code)
- Multiple model providers (OpenAI, Anthropic, Google, OpenRouter, HuggingFace)
- Multiple modalities (VS Code, CLI, GitHub, browser)
- Budget profiles (FREE, CAREFUL, UNLIMITED)
- Cost tracking with justification
"""

from tta_dev_integrations.llm.universal_llm_primitive import (
    CoderType,
    CostJustification,
    LLMRequest,
    LLMResponse,
    ModalityType,
    ModelTier,
    UniversalLLMPrimitive,
    UserBudgetProfile,
)

__all__ = [
    # Base primitive
    "UniversalLLMPrimitive",
    # Enums
    "UserBudgetProfile",
    "CoderType",
    "ModalityType",
    "ModelTier",
    # Models
    "LLMRequest",
    "LLMResponse",
    "CostJustification",
]
