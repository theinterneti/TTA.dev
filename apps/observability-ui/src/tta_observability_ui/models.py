"""Data models for TTA Observability UI."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, ClassVar

from pydantic import BaseModel, Field


class TraceStatus(str, Enum):
    """Trace execution status."""

    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class SpanStatus(str, Enum):
    """Span execution status."""

    SUCCESS = "success"
    ERROR = "error"
    IN_PROGRESS = "in_progress"


class Span(BaseModel):
    """Represents a single primitive execution within a trace."""

    span_id: str
    trace_id: str
    parent_span_id: str | None = None
    primitive_type: str  # 'CachePrimitive', 'RetryPrimitive', etc.
    primitive_name: str
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: int | None = None
    status: SpanStatus
    attributes: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)
    error_message: str | None = None
    stack_trace: str | None = None

    class Config:
        """Pydantic config."""

        json_encoders: ClassVar[dict[Any, Any]] = {datetime: lambda v: v.isoformat()}


class Trace(BaseModel):
    """Represents a complete workflow execution."""

    trace_id: str
    workflow_name: str
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: int | None = None
    status: TraceStatus
    error_message: str | None = None
    context_data: dict[str, Any] = Field(default_factory=dict)
    spans: list[Span] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Computed properties
    span_count: int = 0
    primitive_types: list[str] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        json_encoders: ClassVar[dict[Any, Any]] = {datetime: lambda v: v.isoformat()}

    def compute_stats(self) -> None:
        """Compute derived statistics from spans."""
        self.span_count = len(self.spans)
        self.primitive_types = list({span.primitive_type for span in self.spans})


class MetricRecord(BaseModel):
    """Represents a recorded metric value."""

    metric_id: int | None = None
    primitive_type: str
    metric_name: str
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        json_encoders: ClassVar[dict[Any, Any]] = {datetime: lambda v: v.isoformat()}


class MetricsSummary(BaseModel):
    """Aggregated metrics summary."""

    total_traces: int
    success_rate: float
    avg_duration_ms: float
    cache_hit_rate: float | None = None
    error_rate: float
    primitive_usage: dict[str, int]
    recent_errors: list[dict[str, Any]] = Field(default_factory=list)


class TraceListResponse(BaseModel):
    """Response model for trace list endpoint."""

    traces: list[Trace]
    total: int
    limit: int
    offset: int


class PrimitiveStats(BaseModel):
    """Statistics for a specific primitive type."""

    primitive_type: str
    total_calls: int
    success_count: int
    error_count: int
    avg_duration_ms: float
    p50_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
