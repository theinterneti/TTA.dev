"""LLM primitives — runtime LLM provider abstraction and routing."""

from ttadev.primitives.llm.free_model_tracker import (
    FreeModelTracker,
    ORModel,
    fetch_free_models,
    get_free_models,
    rank_models_for_role,
)
from ttadev.primitives.llm.model_router import (
    ModelRouterPrimitive,
    ModelRouterRequest,
    RouterModeConfig,
    RouterTierConfig,
)
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    UniversalLLMPrimitive,
)

__all__ = [
    # universal primitive
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "UniversalLLMPrimitive",
    # free model tracker
    "FreeModelTracker",
    "ORModel",
    "fetch_free_models",
    "get_free_models",
    "rank_models_for_role",
    # model router
    "ModelRouterPrimitive",
    "ModelRouterRequest",
    "RouterModeConfig",
    "RouterTierConfig",
]
