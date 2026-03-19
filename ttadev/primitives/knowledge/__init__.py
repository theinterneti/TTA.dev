"""Knowledge base integration for workflow primitives.

This module provides primitives for querying contextual guidance backends
to retrieve best practices, examples, and related recommendations.
"""

from .knowledge_base import (
    KBPage,
    KBQuery,
    KBResult,
    KnowledgeBasePrimitive,
)

__all__ = [
    "KBPage",
    "KBQuery",
    "KBResult",
    "KnowledgeBasePrimitive",
]
