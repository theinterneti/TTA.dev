"""Agent coordination primitives for multi-agent workflows.

This module provides composable primitives for coordinating multiple AI agents,
managing agent context handoffs, and tracking architectural decisions across
agent interactions.
"""

from .coordination import AgentCoordinationPrimitive
from .handoff import AgentHandoffPrimitive
from .memory import AgentMemoryPrimitive

__all__ = [
    "AgentHandoffPrimitive",
    "AgentMemoryPrimitive",
    "AgentCoordinationPrimitive",
]

__version__ = "1.0.0"
