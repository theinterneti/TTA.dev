"""Integration primitives for external services.

This module provides TTA.dev primitives that wrap popular external services:
- LLM providers (OpenAI, Anthropic, Ollama)
- Databases (Supabase, SQLite)

All integration primitives follow the WorkflowPrimitive interface for consistent
composition and observability.
"""

from tta_dev_primitives.integrations.anthropic_primitive import AnthropicPrimitive
from tta_dev_primitives.integrations.ollama_primitive import OllamaPrimitive
from tta_dev_primitives.integrations.openai_primitive import OpenAIPrimitive
from tta_dev_primitives.integrations.sqlite_primitive import SQLitePrimitive
from tta_dev_primitives.integrations.supabase_primitive import SupabasePrimitive

__all__ = [
    "OpenAIPrimitive",
    "AnthropicPrimitive",
    "OllamaPrimitive",
    "SupabasePrimitive",
    "SQLitePrimitive",
]
