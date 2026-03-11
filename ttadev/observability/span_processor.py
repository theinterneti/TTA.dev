"""SpanProcessor — normalizes spans from three sources into ProcessedSpan.

Sources:
  1. OTEL JSONL  (.observability/traces.jsonl)
  2. ActivityLogger JSON  (~/.tta/traces/{uuid}.json)
  3. AgentTracker JSONL  (.observability/agents/current_session.jsonl)
"""

import uuid as _uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class ProcessedSpan:
    """Unified span representation used by SessionManager and the dashboard."""

    span_id: str
    trace_id: str
    parent_span_id: str | None
    name: str
    provider: str
    model: str
    agent_role: str | None
    workflow_id: str | None
    primitive_type: str | None
    started_at: str  # ISO 8601
    duration_ms: float
    status: str  # "success" | "error" | "running"
    attributes: dict[str, Any] = field(default_factory=dict)
    # Agent identity — set by FileSpanExporter; used to route span to correct session.
    # None on older spans (pre-identity); server falls back to current session.
    agent_id: str | None = None
    agent_tool: str | None = None
    # Project grouping — set when agent joined a ProjectSession before running.
    project_id: str | None = None


# Name-fragment → primitive class name (checked in order, case-insensitive)
_PRIMITIVE_PATTERNS: list[tuple[str, str]] = [
    ("circuitbreaker", "CircuitBreakerPrimitive"),
    ("circuit_breaker", "CircuitBreakerPrimitive"),
    ("circuit", "CircuitBreakerPrimitive"),
    ("retry", "RetryPrimitive"),
    ("cache", "CachePrimitive"),
    ("timeout", "TimeoutPrimitive"),
    ("fallback", "FallbackPrimitive"),
    ("parallel", "ParallelPrimitive"),
    ("sequential", "SequentialPrimitive"),
    ("lambda", "LambdaPrimitive"),
]

# Raw provider values → canonical display names
_PROVIDER_DISPLAY: dict[str, str] = {
    "github-copilot": "GitHub Copilot",
    "github_copilot": "GitHub Copilot",
    "copilot": "GitHub Copilot",
    "anthropic": "Anthropic",
    "anthropic-direct": "Anthropic",
    "openrouter": "OpenRouter",
    "ollama": "Ollama",
    "openai": "OpenAI",
    # Old placeholder values → reclassify as TTA.dev primitive spans
    "ttadev": "TTA.dev",
    "primitives": "TTA.dev",
}

# Nanosecond epoch threshold: anything > 1e15 is nanoseconds not milliseconds
_NS_THRESHOLD = 1_000_000_000_000_000


class SpanProcessor:
    """Normalizes raw span dicts from multiple sources into ProcessedSpan."""

    # ------------------------------------------------------------------
    # Public format-specific converters
    # ------------------------------------------------------------------

    def from_otel_jsonl(self, raw: dict[str, Any]) -> ProcessedSpan:
        """Convert an OpenTelemetry JSONL span dict to ProcessedSpan.

        OTEL spans from TTA.dev primitives carry step/primitive attributes but
        no AI provider info — they represent framework execution, not LLM calls.
        Provider is set to "TTA.dev" for these spans.
        """
        attrs = raw.get("attributes") or {}
        status_code = (raw.get("status") or {}).get("status_code", "OK")
        status = "error" if status_code == "ERROR" else "success"
        duration_ns = raw.get("duration_ns") or 0

        # Provider: explicit ai.provider wins; primitive spans default to "TTA.dev"
        raw_provider = attrs.get("ai.provider")
        if raw_provider:
            provider = self._normalize_provider(raw_provider)
        else:
            provider = "TTA.dev"  # primitive execution span — not an LLM provider call

        model = self.extract_model(attrs)
        if model == "unknown" and provider == "TTA.dev":
            model = "primitives"

        # Extract primitive type from span name or step.primitive_type attribute
        span_name = raw.get("name") or ""
        prim_type = self.extract_primitive_type(
            span_name,
            {
                **attrs,
                # Also check step.primitive_type attribute used by SequentialPrimitive
                "tta.primitive.type": attrs.get("tta.primitive.type")
                or attrs.get("step.primitive_type"),
            },
        )

        return ProcessedSpan(
            span_id=raw.get("span_id") or str(_uuid.uuid4()),
            trace_id=raw.get("trace_id") or "",
            parent_span_id=raw.get("parent_span_id"),
            name=span_name,
            provider=provider,
            model=model,
            agent_role=self.extract_agent_role(attrs),
            workflow_id=attrs.get("tta.workflow.id") or attrs.get("workflow.id"),
            primitive_type=prim_type,
            started_at=self._parse_timestamp(raw.get("start_time")),
            duration_ms=duration_ns / 1_000_000,
            status=status,
            attributes=attrs,
            agent_id=raw.get("tta_agent_id"),
            agent_tool=raw.get("tta_agent_tool"),
            project_id=attrs.get("tta.project_id") or raw.get("tta_project_id"),
        )

    def from_activity_log(self, raw: dict[str, Any]) -> ProcessedSpan:
        """Convert an ActivityLogger JSON record (or old generate-script format) to ProcessedSpan.

        Handles two formats:
          New: {"trace_id","timestamp","activity_type","provider","model","agent","details",...}
          Old: {"primitive","workflow_id","start_time","duration_ms","status","spans":[...]}
        """
        # Detect old generate-script format (has "primitive" key, no "activity_type")
        if "primitive" in raw and "activity_type" not in raw:
            return self._from_old_trace_format(raw)

        details = raw.get("details") or {}
        duration_ns = details.get("duration_ns") or 0
        agent = raw.get("agent")

        raw_provider = raw.get("provider") or ""
        provider = self._normalize_provider(raw_provider) if raw_provider else "TTA.dev"

        return ProcessedSpan(
            span_id=raw.get("trace_id") or str(_uuid.uuid4()),
            trace_id=raw.get("trace_id") or "",
            parent_span_id=None,
            name=raw.get("activity_type") or "activity",
            provider=provider,
            model=raw.get("model") or "unknown",
            agent_role=agent if agent else None,
            workflow_id=details.get("workflow_id"),
            primitive_type=self.extract_primitive_type(raw.get("activity_type") or "", details),
            started_at=self._parse_timestamp(raw.get("timestamp")),
            duration_ms=duration_ns / 1_000_000,
            status="success",
            attributes=details,
        )

    def from_agent_tracker(self, raw: dict[str, Any]) -> ProcessedSpan:
        """Convert an AgentTracker JSONL record to ProcessedSpan."""
        tta_agent = raw.get("tta_agent")
        action_data = raw.get("action_data") or {}

        raw_provider = raw.get("provider") or ""
        provider = self._normalize_provider(raw_provider) if raw_provider else "unknown"

        return ProcessedSpan(
            span_id=str(_uuid.uuid4()),
            trace_id=str(_uuid.uuid4()),
            parent_span_id=None,
            name=raw.get("action_type") or "action",
            provider=provider,
            model=raw.get("model") or "unknown",
            agent_role=tta_agent if tta_agent else None,
            workflow_id=action_data.get("workflow_id"),
            primitive_type=self.extract_primitive_type(raw.get("action_type") or "", action_data),
            started_at=self._parse_timestamp(raw.get("timestamp")),
            duration_ms=0.0,
            status="success",
            attributes=action_data,
        )

    # ------------------------------------------------------------------
    # Attribute extractors (shared)
    # ------------------------------------------------------------------

    def extract_provider(self, attrs: dict[str, Any]) -> str:
        raw = attrs.get("ai.provider")
        return self._normalize_provider(raw) if raw else "TTA.dev"

    def extract_model(self, attrs: dict[str, Any]) -> str:
        return attrs.get("ai.model") or "unknown"

    def extract_agent_role(self, attrs: dict[str, Any]) -> str | None:
        return attrs.get("tta.agent.role") or None

    def extract_primitive_type(self, name: str, attrs: dict[str, Any]) -> str | None:
        """Return primitive class name from explicit attribute or name inference.

        Explicit ``tta.primitive.type`` attribute takes priority over inference.
        Returns None if no primitive pattern matches.
        """
        explicit = attrs.get("tta.primitive.type")
        if explicit:
            return str(explicit)

        lower = name.lower()
        for fragment, primitive_class in _PRIMITIVE_PATTERNS:
            if fragment in lower:
                return primitive_class

        return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _normalize_provider(self, raw: str) -> str:
        """Map raw provider strings to canonical display names."""
        if not raw:
            return "unknown"
        return _PROVIDER_DISPLAY.get(raw.lower().strip(), raw)

    def _parse_timestamp(self, value: Any) -> str:
        """Convert any timestamp format to an ISO 8601 string.

        Handles:
          - ISO string  ("2026-03-10T10:00:00Z")
          - Nanosecond integer  (1773080613514735796)
          - Millisecond integer (1741603200000)
          - None → current time
        """
        if value is None:
            return datetime.now(UTC).isoformat()
        if isinstance(value, str):
            return value  # already ISO
        if isinstance(value, (int, float)):
            if value > _NS_THRESHOLD:
                # Nanoseconds → seconds
                ts = value / 1_000_000_000
            else:
                # Milliseconds → seconds
                ts = value / 1_000
            return datetime.fromtimestamp(ts, tz=UTC).isoformat()
        return str(value)

    def _from_old_trace_format(self, raw: dict[str, Any]) -> ProcessedSpan:
        """Handle old generate-script trace format: {primitive, workflow_id, spans, ...}"""
        prim = raw.get("primitive") or ""
        spans = raw.get("spans") or []
        first_span = spans[0] if spans else {}
        prim_type = first_span.get("attributes", {}).get("primitive.type") or prim or None

        return ProcessedSpan(
            span_id=raw.get("trace_id") or str(_uuid.uuid4()),
            trace_id=raw.get("trace_id") or "",
            parent_span_id=None,
            name=prim or "primitive_execution",
            provider="TTA.dev",
            model="primitives",
            agent_role=None,
            workflow_id=raw.get("workflow_id"),
            primitive_type=prim_type,
            started_at=self._parse_timestamp(raw.get("start_time")),
            duration_ms=raw.get("duration_ms") or 0.0,
            status=raw.get("status") or "success",
            attributes={"primitive.type": prim_type, "workflow.id": raw.get("workflow_id")},
        )
