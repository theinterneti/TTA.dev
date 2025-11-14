"""
Message passing data structures for agent coordination.

Reliability primitives for message coordinators:
- FailureType to distinguish transient vs permanent failures
- ReceivedMessage reservation wrapper for ack/nack with visibility timeout
- QueueMessage extended with delivery_attempts and timestamps
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .models import AgentId, AgentMessage, MessagePriority, MessageType


class MessageResult(BaseModel):
    """Result of message delivery attempt."""

    message_id: str
    delivered: bool
    error: str | None = None


class MessageSubscription(BaseModel):
    """Subscription to specific message types."""

    subscription_id: str
    agent_id: AgentId
    message_types: list[MessageType] = Field(default_factory=list)


class FailureType(str, Enum):
    """Message processing failure types."""

    TRANSIENT = "transient"  # Retry with backoff
    PERMANENT = "permanent"  # Send to DLQ
    TIMEOUT = "timeout"  # Retry with backoff


class QueueMessage(BaseModel):
    """Message in queue with delivery metadata."""

    message: AgentMessage
    priority: MessagePriority = MessagePriority.NORMAL
    enqueued_at: str | None = None
    delivery_attempts: int = 0
    last_error: str | None = None


class ReceivedMessage(BaseModel):
    """Message received with reservation token."""

    token: str
    queue_message: QueueMessage
    visibility_deadline: str | None = None
