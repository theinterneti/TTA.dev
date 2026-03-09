"""Multi-agent collaboration primitives for version control and coordination."""

from .git_integration import (
    AgentIdentity,
    CommitFrequencyPolicy,
    GitCollaborationPrimitive,
    IntegrationFrequency,
    MergeStrategy,
)

__all__ = [
    "AgentIdentity",
    "CommitFrequencyPolicy",
    "GitCollaborationPrimitive",
    "IntegrationFrequency",
    "MergeStrategy",
]
