"""Hierarchical trace context for observability."""

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TraceContext:
    """Context for creating hierarchical traces."""

    user: str
    provider: str
    model: str
    trace_id: str = field(default_factory=lambda: f"trace-{datetime.now().timestamp()}")
    _current_span: dict[str, Any] | None = field(default=None, repr=False)

    async def create_trace_hierarchy(
        self, agent: str, workflow: str, primitives: list[str]
    ) -> dict[str, Any]:
        """Create a hierarchical trace structure.

        Args:
            agent: Agent name (e.g., "backend-engineer")
            workflow: Workflow name (e.g., "build_api")
            primitives: List of primitive names used

        Returns:
            Complete trace hierarchy
        """
        return {
            "trace_id": self.trace_id,
            "user": self.user,
            "provider": self.provider,
            "model": self.model,
            "agent": agent,
            "workflow": workflow,
            "primitives": primitives,
            "timestamp": datetime.now().isoformat(),
        }

    @contextmanager
    def span(self, name: str, **attributes):
        """Create a nested span with automatic parent tracking.

        Args:
            name: Span name
            **attributes: Additional span attributes

        Yields:
            Span context
        """
        span_id = f"span-{datetime.now().timestamp()}"
        parent_id = self._current_span["span_id"] if self._current_span else None

        span = {
            "span_id": span_id,
            "parent_id": parent_id,
            "name": name,
            "attributes": {
                "user": self.user,
                "provider": self.provider,
                "model": self.model,
                **attributes,
            },
            "start_time": datetime.now().isoformat(),
        }

        # Save previous span
        previous_span = self._current_span
        self._current_span = span

        try:
            yield span
        finally:
            span["end_time"] = datetime.now().isoformat()
            # Restore previous span
            self._current_span = previous_span
