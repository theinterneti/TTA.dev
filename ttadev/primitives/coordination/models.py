"""Data models for the coordination primitive.

These types are intentionally domain-agnostic — no TTA-specific agent types,
narrative semantics, or project-specific enums.  Callers define their own
queue_type taxonomy and wrap these models at the domain boundary.
"""

from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Any

from pydantic import BaseModel, Field


class MessagePriority(IntEnum):
    """Priority levels used as Redis sorted-set scores."""

    LOW = 1
    NORMAL = 5
    HIGH = 9


class FailureType(StrEnum):
    """Distinguishes transient failures (retry) from permanent ones (DLQ)."""

    TRANSIENT = "transient"
    PERMANENT = "permanent"
    TIMEOUT = "timeout"


class QueueEndpoint(BaseModel):
    """Generic identity for a queue consumer/producer.

    Replaces TTA-specific ``AgentId(type: AgentType, instance: str)``.
    ``queue_type`` is caller-defined (e.g. ``"worker"``, ``"ingester"``).
    """

    queue_type: str
    instance: str = "default"

    def key_segment(self) -> str:
        """Return the ``type:instance`` segment used in Redis key names."""
        return f"{self.queue_type}:{self.instance}"


class CoordinationMessage(BaseModel):
    """A generic message passed between queue endpoints."""

    message_id: str = Field(..., min_length=1)
    sender: str  # opaque string — e.g. "worker:default"
    message_type: str  # caller-defined label
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: str | None = None


class QueuedMessage(BaseModel):
    """``CoordinationMessage`` decorated with queue metadata."""

    message: CoordinationMessage
    priority: MessagePriority = MessagePriority.NORMAL
    enqueued_at: str | None = None
    delivery_attempts: int = 0
    last_error: str | None = None


class ReceivedMessage(BaseModel):
    """A reserved message awaiting ack or nack."""

    token: str
    queued_message: QueuedMessage
    visibility_deadline: str | None = None


class MessageResult(BaseModel):
    """Outcome of a send attempt."""

    message_id: str
    delivered: bool
    error: str | None = None


class MessageSubscription(BaseModel):
    """Handle returned by ``subscribe_to_messages``."""

    subscription_id: str
    endpoint_id: str
    message_types: list[str] = Field(default_factory=list)
