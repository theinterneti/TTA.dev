"""
TTA.dev Integration Primitives
================================

Production-ready integration primitives for AI applications across coders, models, and budgets.

**Universal LLM Architecture:**
- Works with ANY agentic coder (Cline, Copilot, Augment Code)
- Works with ANY model provider (OpenAI, Anthropic, Google, OpenRouter, HuggingFace)
- Works across ANY modality (VS Code, CLI, GitHub, browser)
- Budget-aware (FREE, CAREFUL, UNLIMITED profiles)
- Cost tracking with justification

Provides seamless integration with:
- LLM providers (universal interface for all coders/models)
- Databases (Supabase, PostgreSQL, SQLite)
- Auth providers (Clerk, Auth0, custom JWT)

All primitives inherit from tta-dev-primitives base classes and include:
- Automatic retry with exponential backoff
- Observability via OpenTelemetry
- Type-safe interfaces with Pydantic
- Comprehensive error handling

**Budget Tiers:**
- FREE ($0/month): Gemini, Kimi, DeepSeek only
- CAREFUL ($10-50/month): Mix free+paid with justification tracking
- UNLIMITED: Always best model, cost tracked but not limiting
"""

# LLM integrations
# Database and Auth base classes
from tta_dev_integrations.auth.base import AuthPrimitive, AuthRequest, AuthResult
from tta_dev_integrations.database.base import (
    DatabasePrimitive,
    DatabaseQuery,
    DatabaseResult,
)
from tta_dev_integrations.llm import (
    CoderType,
    CostJustification,
    LLMRequest,
    LLMResponse,
    ModalityType,
    ModelTier,
    UniversalLLMPrimitive,
    UserBudgetProfile,
)

# Database integrations
try:
    from tta_dev_integrations.database.supabase_primitive import SupabasePrimitive
except ImportError:
    SupabasePrimitive = None  # type: ignore

try:
    from tta_dev_integrations.database.postgresql_primitive import PostgreSQLPrimitive
except ImportError:
    PostgreSQLPrimitive = None  # type: ignore

try:
    from tta_dev_integrations.database.sqlite_primitive import SQLitePrimitive
except ImportError:
    SQLitePrimitive = None  # type: ignore

# Auth integrations
try:
    from tta_dev_integrations.auth.clerk_primitive import ClerkAuthPrimitive
except ImportError:
    ClerkAuthPrimitive = None  # type: ignore

try:
    from tta_dev_integrations.auth.auth0_primitive import Auth0Primitive
except ImportError:
    Auth0Primitive = None  # type: ignore

try:
    from tta_dev_integrations.auth.jwt_primitive import JWTPrimitive
except ImportError:
    JWTPrimitive = None  # type: ignore

__all__ = [
    # LLM primitives
    "UniversalLLMPrimitive",
    "UserBudgetProfile",
    "CoderType",
    "ModalityType",
    "ModelTier",
    "LLMRequest",
    "LLMResponse",
    "CostJustification",
    # Base classes
    "DatabasePrimitive",
    "AuthPrimitive",
    # Request/Response models
    "DatabaseQuery",
    "DatabaseResult",
    "AuthRequest",
    "AuthResult",
    # Database providers
    "SupabasePrimitive",
    "PostgreSQLPrimitive",
    "SQLitePrimitive",
    # Auth providers
    "ClerkAuthPrimitive",
    "Auth0Primitive",
    "JWTPrimitive",
]

__version__ = "0.3.0"  # Universal LLM architecture with budget awareness
