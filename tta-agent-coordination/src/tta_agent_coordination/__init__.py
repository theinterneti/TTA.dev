"""
TTA Agent Coordination - Redis-based multi-agent coordination primitives.

Provides production-ready coordination components for distributed agent systems:
- Message coordination with priority queues and retries
- Agent registry with heartbeat/TTL management
- Circuit breaker for fault tolerance
"""

from .messaging import (
    FailureType,
    MessageResult,
    MessageSubscription,
    QueueMessage,
    ReceivedMessage,
)
from .models import AgentId, AgentMessage, MessagePriority, MessageType, RoutingKey

__version__ = "0.1.0"

__all__ = [
    # Models
    "AgentId",
    "AgentMessage",
    "MessagePriority",
    "MessageType",
    "RoutingKey",
    # Messaging
    "FailureType",
    "MessageResult",
    "MessageSubscription",
    "QueueMessage",
    "ReceivedMessage",
]
