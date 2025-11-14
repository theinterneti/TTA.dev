"""
Core data models for agent coordination.

Generic models with no application-specific dependencies. AgentId uses string
type instead of enum to support any agent system.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Generic message types for agent communication."""

    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"


class MessagePriority(int, Enum):
    """Message priority levels for queue ordering."""

    LOW = 1
    NORMAL = 5
    HIGH = 9


class RoutingKey(BaseModel):
    """Optional routing metadata for message delivery."""

    topic: str | None = None
    tags: list[str] = Field(default_factory=list)


class AgentId(BaseModel):
    """
    Generic agent identifier.

    Uses string type instead of enum to support any agent system.
    Examples: "input_processor", "world_builder", "data_processor", etc.
    """

    type: str = Field(..., description="Agent type identifier (any string)")
    instance: str | None = Field(
        default=None,
        description="Optional instance identifier (for sharded/pooled agents)",
    )


class AgentMessage(BaseModel):
    """Message sent between agents."""

    message_id: str = Field(..., min_length=6)
    sender: AgentId
    recipient: AgentId
    message_type: MessageType
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    routing: RoutingKey = Field(default_factory=RoutingKey)
    timestamp: str | None = Field(
        default=None, description="ISO-8601 timestamp; may be set by coordinator"
    )
