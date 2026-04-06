"""Provider prefix constants for litellm model string resolution.

Maps TTA.dev :class:`~ttadev.primitives.llm.universal_llm_primitive.LLMProvider`
enum values to the litellm provider prefix strings used in model strings of the
form ``"<provider>/<model-name>"``.
"""

from __future__ import annotations

from ttadev.primitives.llm.universal_llm_primitive import LLMProvider

# Map TTA.dev LLMProvider values → litellm provider prefix strings.
_PROVIDER_PREFIX: dict[str, str] = {
    LLMProvider.GROQ: "groq",
    LLMProvider.ANTHROPIC: "anthropic",
    LLMProvider.OPENAI: "openai",
    LLMProvider.OLLAMA: "ollama",
    LLMProvider.GOOGLE: "gemini",  # litellm uses "gemini/" for Google AI Studio
    LLMProvider.OPENROUTER: "openrouter",
    LLMProvider.TOGETHER: "together_ai",
    LLMProvider.XAI: "xai",
}
