"""LLM primitives — runtime LLM provider abstraction."""

from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    UniversalLLMPrimitive,
)

__all__ = ["LLMProvider", "LLMRequest", "LLMResponse", "UniversalLLMPrimitive"]
