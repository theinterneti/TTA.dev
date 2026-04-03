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
    from ttadev.primitives.integrations.anthropic_primitive import AnthropicPrimitive
except ModuleNotFoundError as exc:  # pragma: no cover - executed only when SDK missing
    if exc.name == "anthropic":
        AnthropicPrimitive = None  # type: ignore[assignment]
    else:  # Unexpected import error
        raise
try:  # Optional dependency: e2b_code_interpreter SDK
    from ttadev.primitives.integrations.e2b_primitive import (
        CodeExecutionPrimitive,
        E2BPrimitive,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - executed only when SDK missing
    if exc.name == "e2b_code_interpreter":
        CodeExecutionPrimitive = None  # type: ignore[assignment]
        E2BPrimitive = None  # type: ignore[assignment]
    else:
        raise
# GoogleAIStudioPrimitive is intentionally NOT imported eagerly here.
# Its module emits a DeprecationWarning at import time (module-level warnings.warn),
# which would fire on every test run and every ``import ttadev`` statement even when
# the caller has no interest in the deprecated primitive.
#
# Instead, it is exposed via ``__getattr__`` below so the warning only fires when
# a caller explicitly accesses ``GoogleAIStudioPrimitive`` — the correct behaviour
# for a deprecation notice.  The symbol remains listed in ``__all__`` so that
# tools like ``dir()`` and auto-completers still discover it.
from ttadev.primitives.integrations.huggingface_primitive import HuggingFacePrimitive
from ttadev.primitives.integrations.openrouter_primitive import OpenRouterPrimitive

try:  # Optional dependency: OpenAI SDK
    from ttadev.primitives.integrations.openai_primitive import OpenAIPrimitive
except ModuleNotFoundError as exc:  # pragma: no cover - executed only when SDK missing
    if exc.name == "openai":
        OpenAIPrimitive = None  # type: ignore[assignment]
    else:  # Unexpected import error
        raise

# Optional integrations (require additional dependencies)
try:  # Optional dependency: ollama SDK
    from ttadev.primitives.integrations.ollama_primitive import OllamaPrimitive
except ModuleNotFoundError as exc:  # pragma: no cover - executed only when SDK missing
    if exc.name == "ollama":
        OllamaPrimitive = None  # type: ignore[assignment]
    else:
        raise

try:  # Optional dependency: Groq SDK
    from ttadev.primitives.integrations.groq_primitive import GroqPrimitive
except ImportError:  # pragma: no cover - executed only when SDK missing
    GroqPrimitive = None  # type: ignore[assignment]

try:  # Optional dependency: aiosqlite
    from ttadev.primitives.integrations.sqlite_primitive import SQLitePrimitive
except ModuleNotFoundError as exc:  # pragma: no cover - executed only when SDK missing
    if exc.name == "aiosqlite":
        SQLitePrimitive = None  # type: ignore[assignment]
    else:
        raise

try:  # Optional dependency: Supabase SDK
    from ttadev.primitives.integrations.supabase_primitive import SupabasePrimitive
except ModuleNotFoundError as exc:  # pragma: no cover - executed only when SDK missing
    if exc.name == "supabase":
        SupabasePrimitive = None  # type: ignore[assignment]
    else:
        raise

from ttadev.primitives.integrations.together_ai_primitive import TogetherAIPrimitive

try:  # Optional dependency: langgraph
    from ttadev.primitives.integrations.langgraph_primitive import LangGraphPrimitive
except (
    ImportError,
    ModuleNotFoundError,
) as exc:  # pragma: no cover - executed only when SDK missing
    if "langgraph" in str(exc):
        LangGraphPrimitive = None  # type: ignore[assignment]
    else:
        raise


def __getattr__(name: str) -> object:
    """Lazily expose symbols that must not be imported at module load time.

    ``GoogleAIStudioPrimitive`` emits a ``DeprecationWarning`` at the *module*
    level (not inside the class), so importing it eagerly would fire the warning
    on every ``import ttadev`` — including every test collection pass.  By
    deferring the import here, the warning fires only when a caller explicitly
    accesses the symbol, which is the expected UX for a deprecation notice.
    """
    if name == "GoogleAIStudioPrimitive":
        try:
            from ttadev.primitives.integrations.google_ai_studio_primitive import (
                GoogleAIStudioPrimitive,
            )
        except ModuleNotFoundError as exc:  # pragma: no cover - SDK not installed
            if exc.name and exc.name.startswith("google"):
                return None  # type: ignore[return-value]
            raise
        return GoogleAIStudioPrimitive
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


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
    "LangGraphPrimitive",
]
