import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Event:
    """
    A standardized event schema for all internal agent communication.
    """

    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex}")
    event_name: str
    source_agent_id: str
    target_agent_id: str | None = None  # None for broadcast
    timestamp: float = field(default_factory=time.time)
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_name": self.event_name,
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        return cls(
            event_id=data.get("event_id"),
            event_name=data.get("event_name"),
            source_agent_id=data.get("source_agent_id"),
            target_agent_id=data.get("target_agent_id"),
            timestamp=data.get("timestamp"),
            payload=data.get("payload"),
            correlation_id=data.get("correlation_id"),
        )
