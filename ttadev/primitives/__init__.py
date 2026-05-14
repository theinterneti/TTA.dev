"""TTA Dev Primitives - Production-quality workflow primitives for AI applications.

Core primitives are exported directly from this package:
    WorkflowPrimitive, WorkflowContext, LambdaPrimitive,
    SequentialPrimitive, ParallelPrimitive, ConditionalPrimitive, RouterPrimitive,
    RetryPrimitive, FallbackPrimitive, TimeoutPrimitive, CompensationPrimitive,
    CachePrimitive, MockPrimitive, GitCollaborationPrimitive.

LLM primitives (LiteLLMPrimitive, UniversalLLMPrimitive, etc.) are lazy-loaded
via __getattr__ to avoid triggering ``import litellm`` (which can hang at import
time in some environments due to network cost-map checks).

KB Safety: All primitives follow the one-way sync architecture (Code → KB only).
See docs/architecture/KB_SAFETY_ARCHITECTURE.md for details.
"""

# ── Code graph (CGC / FalkorDB) ─────────────────────────────────────────
from .code_graph import CGCOp, CodeGraphPrimitive, CodeGraphQuery, ImpactReport

# ── Core: collaboration ─────────────────────────────────────────────────
from .collaboration import (
    AgentIdentity,
    CommitFrequencyPolicy,
    GitCollaborationPrimitive,
    IntegrationFrequency,
    MergeStrategy,
)

# ── Core: control flow ──────────────────────────────────────────────────
from .core.base import LambdaPrimitive, WorkflowContext, WorkflowPrimitive
from .core.conditional import ConditionalPrimitive
from .core.parallel import ParallelPrimitive
from .core.routing import RouterPrimitive
from .core.sequential import SequentialPrimitive

# ── Core: performance ───────────────────────────────────────────────────
from .performance.cache import CacheBackend, CachePrimitive, InMemoryBackend, RedisBackend

# ── Core: persistence ───────────────────────────────────────────────────
from .persistence import AbstractRepository, AbstractUnitOfWork, FakeUnitOfWork

# ── Core: recovery ──────────────────────────────────────────────────────
from .recovery.compensation import CompensationPrimitive, CompensationStrategy
from .recovery.fallback import FallbackPrimitive
from .recovery.retry import RetryPrimitive, RetryStrategy
from .recovery.timeout import TimeoutPrimitive

# ── Core: safety ────────────────────────────────────────────────────
from .safety import SafetyGateEscalatedError, SafetyGatePrimitive, SeverityLevel

# ── Core: streaming ─────────────────────────────────────────────────
from .streaming import StreamingPrimitive

# ── Core: testing ───────────────────────────────────────────────────────
from .testing.mocks import MockPrimitive

# ── Memory (Hindsight / AgentMemory) ─────────────────────────────────────
from .memory import AgentMemory, HindsightClient, MemoryResult, RetainResult


# ── Lazy-loaded modules — deferred via __getattr__ to avoid pulling heavy
#    deps (litellm, langgraph) until the caller actually needs them.
_lazy_imports = {
    # LLM primitives (trigger import litellm)
    "LiteLLMPrimitive": ".llm",
    "LLMProvider": ".llm",
    "LLMRequest": ".llm",
    "LLMResponse": ".llm",
    "ToolCall": ".llm",
    "ToolSchema": ".llm",
    "UniversalLLMPrimitive": ".llm",
    "make_resilient_llm": ".llm",
    # LangGraph (trigger import langgraph)
    "LangGraphPrimitive": ".integrations.langgraph_primitive",
}


def __getattr__(name: str):
    if name in _lazy_imports:
        import importlib

        mod = importlib.import_module(_lazy_imports[name], package=__name__)
        attr = getattr(mod, name)
        # Cache in module globals so next access is direct
        globals()[name] = attr
        return attr
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Core primitives
    "WorkflowPrimitive",
    "WorkflowContext",
    "LambdaPrimitive",
    "SequentialPrimitive",
    "ParallelPrimitive",
    "ConditionalPrimitive",
    "RouterPrimitive",
    # Collaboration primitives
    "AgentIdentity",
    "CommitFrequencyPolicy",
    "GitCollaborationPrimitive",
    "IntegrationFrequency",
    "MergeStrategy",
    # Performance primitives
    "CacheBackend",
    "CachePrimitive",
    "InMemoryBackend",
    "RedisBackend",
    # Safety primitives
    "SafetyGatePrimitive",
    "SafetyGateEscalatedError",
    "SeverityLevel",
    # Recovery primitives
    "CompensationPrimitive",
    "CompensationStrategy",
    "FallbackPrimitive",
    "RetryPrimitive",
    "RetryStrategy",
    "TimeoutPrimitive",
    # Persistence primitives
    "AbstractRepository",
    "AbstractUnitOfWork",
    "FakeUnitOfWork",
    # LLM primitives (lazy)
    "LiteLLMPrimitive",
    "make_resilient_llm",
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "ToolCall",
    "ToolSchema",
    "UniversalLLMPrimitive",
    # Testing primitives
    "MockPrimitive",
    # Streaming primitives
    "StreamingPrimitive",
    # LangGraph integration (lazy)
    "LangGraphPrimitive",
    # Code graph primitives
    "CodeGraphPrimitive",
    "CodeGraphQuery",
    "ImpactReport",
    "CGCOp",
    # Memory primitives
    "AgentMemory",
    "HindsightClient",
    "MemoryResult",
    "RetainResult",
]

__version__ = "1.3.1"

# Auto-setup observability is opt-in — call initialize_observability() explicitly.
# Previously setup_tracing() was called at import time, but that triggers the
# observability chain (aiohttp, etc.) on every ``import ttadev.primitives``.
# See ttadev.initialize_observability() for the explicit opt-in path.
