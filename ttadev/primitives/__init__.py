"""TTA Dev Primitives - Production-quality workflow primitives for AI applications.

Core primitives are exported directly from this package:
    WorkflowPrimitive, WorkflowContext, LambdaPrimitive,
    SequentialPrimitive, ParallelPrimitive, ConditionalPrimitive, RouterPrimitive,
    RetryPrimitive, FallbackPrimitive, TimeoutPrimitive, CompensationPrimitive,
    CachePrimitive, MockPrimitive, GitCollaborationPrimitive.

Extension modules (ace, adaptive, analysis, apm, benchmarking, knowledge,
lifecycle, orchestration, research, speckit) are accessible via their original
import paths or through the ``extensions`` namespace::

    from ttadev.primitives.extensions import EXTENSION_MODULES
    from ttadev.primitives.extensions import adaptive

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

# ── LLM primitives (runtime provider abstraction) ───────────────────────
from .llm import LLMProvider, LLMRequest, LLMResponse, UniversalLLMPrimitive

# ── Memory (Hindsight / AgentMemory) ─────────────────────────────────────
from .memory import AgentMemory, HindsightClient, MemoryResult, RetainResult

# ── Core: performance ───────────────────────────────────────────────────
from .performance.cache import CachePrimitive

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
    "CachePrimitive",
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
    # LLM primitives
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "UniversalLLMPrimitive",
    # Testing primitives
    "MockPrimitive",
    # Streaming primitives
    "StreamingPrimitive",
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

# Auto-setup observability on import
from .observability.tracing import setup_tracing

setup_tracing()
