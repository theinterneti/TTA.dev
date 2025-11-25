"""Integration primitives for external services.

This module provides TTA.dev primitives that wrap popular external services:
- LLM providers (OpenAI, Anthropic, Ollama, Google AI Studio, Groq, OpenRouter, Hugging Face, Together.ai)
- Databases (Supabase, SQLite)
- Code Execution (E2B Sandboxes)

All integration primitives follow the WorkflowPrimitive interface for consistent
composition and observability.

Some providers require optional dependencies (e.g. ``anthropic``, ``groq``).
Those integrations degrade gracefully when the optional SDK is not installed so
that other providers can still be imported and used.
"""

try:  # Optional dependency: anthropic SDK
    from tta_dev_primitives.integrations.anthropic_primitive import AnthropicPrimitive
except ModuleNotFoundError as exc:  # pragma: no cover - executed only when SDK missing
    if exc.name == "anthropic":
        AnthropicPrimitive = None  # type: ignore[assignment]
    else:  # Unexpected import error
        raise
from tta_dev_primitives.integrations.e2b_primitive import (
    CodeExecutionPrimitive,
    E2BPrimitive,
)
from tta_dev_primitives.integrations.google_ai_studio_primitive import (
    GoogleAIStudioPrimitive,
)
from tta_dev_primitives.integrations.huggingface_primitive import HuggingFacePrimitive
from tta_dev_primitives.integrations.openai_primitive import OpenAIPrimitive
from tta_dev_primitives.integrations.openrouter_primitive import OpenRouterPrimitive

# Optional integrations (require additional dependencies)
try:  # Optional dependency: ollama SDK
    from tta_dev_primitives.integrations.ollama_primitive import OllamaPrimitive
except ModuleNotFoundError as exc:  # pragma: no cover - executed only when SDK missing
    if exc.name == "ollama":
        OllamaPrimitive = None  # type: ignore[assignment]
    else:
        raise

try:  # Optional dependency: Groq SDK
    from tta_dev_primitives.integrations.groq_primitive import GroqPrimitive
except ImportError:  # pragma: no cover - executed only when SDK missing
    GroqPrimitive = None  # type: ignore[assignment]

try:  # Optional dependency: aiosqlite
    from tta_dev_primitives.integrations.sqlite_primitive import SQLitePrimitive
except ModuleNotFoundError as exc:  # pragma: no cover - executed only when SDK missing
    if exc.name == "aiosqlite":
        SQLitePrimitive = None  # type: ignore[assignment]
    else:
        raise

try:  # Optional dependency: Supabase SDK
    from tta_dev_primitives.integrations.supabase_primitive import SupabasePrimitive
except ModuleNotFoundError as exc:  # pragma: no cover - executed only when SDK missing
    if exc.name == "supabase":
        SupabasePrimitive = None  # type: ignore[assignment]
    else:
        raise

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
