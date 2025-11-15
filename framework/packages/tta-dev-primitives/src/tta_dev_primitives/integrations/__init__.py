"""Integration primitives for external services.

This module provides TTA.dev primitives that wrap popular external services:
- LLM providers (OpenAI, Anthropic, Ollama, Google AI Studio, Groq, OpenRouter, Hugging Face, Together.ai)
- Databases (Supabase, SQLite)
- Code Execution (E2B Sandboxes)

All integration primitives follow the WorkflowPrimitive interface for consistent
composition and observability.
"""

from tta_dev_primitives.integrations.anthropic_primitive import AnthropicPrimitive
from tta_dev_primitives.integrations.e2b_primitive import (
    CodeExecutionPrimitive,
    E2BPrimitive,
)
from tta_dev_primitives.integrations.google_ai_studio_primitive import (
    GoogleAIStudioPrimitive,
)
from tta_dev_primitives.integrations.huggingface_primitive import HuggingFacePrimitive
from tta_dev_primitives.integrations.ollama_primitive import OllamaPrimitive
from tta_dev_primitives.integrations.openai_primitive import OpenAIPrimitive
from tta_dev_primitives.integrations.openrouter_primitive import OpenRouterPrimitive
from tta_dev_primitives.integrations.sqlite_primitive import SQLitePrimitive

# Optional integrations (require additional dependencies)
try:
    from tta_dev_primitives.integrations.groq_primitive import GroqPrimitive
except ImportError:
    GroqPrimitive = None  # type: ignore
from tta_dev_primitives.integrations.supabase_primitive import SupabasePrimitive
from tta_dev_primitives.integrations.together_ai_primitive import TogetherAIPrimitive

__all__ = [
    "OpenAIPrimitive",
    "AnthropicPrimitive",
    "OllamaPrimitive",
    "GoogleAIStudioPrimitive",
    "GroqPrimitive",
    "OpenRouterPrimitive",
    "HuggingFacePrimitive",
    "TogetherAIPrimitive",
    "SupabasePrimitive",
    "SQLitePrimitive",
    "CodeExecutionPrimitive",
    "E2BPrimitive",
]
