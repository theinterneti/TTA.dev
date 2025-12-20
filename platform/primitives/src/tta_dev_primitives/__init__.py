"""TTA Dev Primitives - Production-quality workflow primitives for AI applications.

KB Safety: All primitives follow the one-way sync architecture (Code → KB only).
See docs/architecture/KB_SAFETY_ARCHITECTURE.md for details.
"""

# Core primitives
# Collaboration primitives
from .collaboration import (
    AgentIdentity,
    CommitFrequencyPolicy,
    GitCollaborationPrimitive,
    IntegrationFrequency,
    MergeStrategy,
)
from .core.base import LambdaPrimitive, WorkflowContext, WorkflowPrimitive
from .core.conditional import ConditionalPrimitive
from .core.parallel import ParallelPrimitive
from .core.routing import RouterPrimitive
from .core.sequential import SequentialPrimitive

# Performance primitives
from .performance.cache import CachePrimitive

# Recovery primitives
from .recovery.compensation import CompensationPrimitive, CompensationStrategy
from .recovery.fallback import FallbackPrimitive
from .recovery.retry import RetryPrimitive, RetryStrategy
from .recovery.timeout import TimeoutPrimitive

# Testing primitives
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
    # Recovery primitives
    "CompensationPrimitive",
    "CompensationStrategy",
    "FallbackPrimitive",
    "RetryPrimitive",
    "RetryStrategy",
    "TimeoutPrimitive",
    # Testing primitives
    "MockPrimitive",
]

__version__ = "0.1.0"
