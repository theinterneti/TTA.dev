"""SQLite storage for traces and metrics."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiosqlite

from .models import MetricRecord, Span, Trace, TraceStatus

logger = logging.getLogger(__name__)


class TraceStorage:
    """SQLite-based storage for traces and metrics."""

    def __init__(
        self,
        db_path: str | Path = "tta_traces.db",
        retention_hours: int = 24,
        max_traces: int = 1000,
    ):
        """
        Initialize trace storage.

        Args:
            db_path: Path to SQLite database file
            retention_hours: How long to keep traces (default: 24 hours)
            max_traces: Maximum number of traces to keep (default: 1000)
        """
        self.db_path = Path(db_path)
        self.retention_hours = retention_hours
        self.max_traces = max_traces
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database schema."""
        if self._initialized:
            return

        logger.info(f"Initializing trace storage at {self.db_path}")

        async with aiosqlite.connect(self.db_path) as db:
            # Traces table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    workflow_name TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_ms INTEGER,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    context_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            # Spans table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS spans (
                    span_id TEXT PRIMARY KEY,
                    trace_id TEXT NOT NULL,
                    parent_span_id TEXT,
                    primitive_type TEXT NOT NULL,
                    primitive_name TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_ms INTEGER,
                    status TEXT NOT NULL,
                    attributes TEXT,
                    events TEXT,
                    error_message TEXT,
                    stack_trace TEXT,
                    FOREIGN KEY (trace_id) REFERENCES traces(trace_id)
                )
                """
            )

            # Metrics table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    primitive_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    labels TEXT
                )
                """
            )

            # Indexes for performance
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_traces_created_at ON traces(created_at DESC)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_spans_trace_id ON spans(trace_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp DESC)"
            )

            await db.commit()

        self._initialized = True
        logger.info("Trace storage initialized successfully")

    async def save_trace(self, trace: Trace) -> None:
        """Save a trace and its spans to storage."""
        async with aiosqlite.connect(self.db_path) as db:
            # Save trace
            await db.execute(
                """
                INSERT OR REPLACE INTO traces
                (trace_id, workflow_name, start_time, end_time, duration_ms, status, error_message, context_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace.trace_id,
                    trace.workflow_name,
                    trace.start_time.isoformat(),
                    trace.end_time.isoformat() if trace.end_time else None,
                    trace.duration_ms,
                    trace.status.value,
                    trace.error_message,
                    json.dumps(trace.context_data),
                ),
            )

            # Save spans
            for span in trace.spans:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO spans
                    (span_id, trace_id, parent_span_id, primitive_type, primitive_name,
                     start_time, end_time, duration_ms, status, attributes, events,
                     error_message, stack_trace)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        span.span_id,
                        span.trace_id,
                        span.parent_span_id,
                        span.primitive_type,
                        span.primitive_name,
                        span.start_time.isoformat(),
                        span.end_time.isoformat() if span.end_time else None,
                        span.duration_ms,
                        span.status.value,
                        json.dumps(span.attributes),
                        json.dumps(span.events),
                        span.error_message,
                        span.stack_trace,
                    ),
                )

            await db.commit()
            logger.debug(f"Saved trace {trace.trace_id} with {len(trace.spans)} spans")

    async def get_trace(self, trace_id: str) -> Trace | None:
        """Retrieve a trace by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Get trace
            async with db.execute(
                "SELECT * FROM traces WHERE trace_id = ?", (trace_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None

                trace_data = dict(row)

            # Get spans
            spans = []
            async with db.execute(
                "SELECT * FROM spans WHERE trace_id = ? ORDER BY start_time",
                (trace_id,),
            ) as cursor:
                async for row in cursor:
                    span_data = dict(row)
                    span_data["attributes"] = json.loads(
                        span_data["attributes"] or "{}"
                    )
                    span_data["events"] = json.loads(span_data["events"] or "[]")
                    spans.append(Span(**span_data))

            # Convert to Trace model
            trace_data["context_data"] = json.loads(trace_data["context_data"] or "{}")
            trace_data["status"] = TraceStatus(trace_data["status"])
            trace_data["start_time"] = datetime.fromisoformat(trace_data["start_time"])
            if trace_data["end_time"]:
                trace_data["end_time"] = datetime.fromisoformat(trace_data["end_time"])
            trace_data["spans"] = spans

            trace = Trace(**trace_data)
            trace.compute_stats()
            return trace

    async def list_traces(
        self, limit: int = 100, offset: int = 0, status: str | None = None
    ) -> list[Trace]:
        """List recent traces."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            query = "SELECT * FROM traces"
            params: list[Any] = []

            if status:
                query += " WHERE status = ?"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            traces = []
            async with db.execute(query, params) as cursor:
                async for row in cursor:
                    trace_data = dict(row)
                    trace_data["context_data"] = json.loads(
                        trace_data["context_data"] or "{}"
                    )
                    trace_data["status"] = TraceStatus(trace_data["status"])
                    trace_data["start_time"] = datetime.fromisoformat(
                        trace_data["start_time"]
                    )
                    if trace_data["end_time"]:
                        trace_data["end_time"] = datetime.fromisoformat(
                            trace_data["end_time"]
                        )

                    # Get span count
                    async with db.execute(
                        "SELECT COUNT(*) as count FROM spans WHERE trace_id = ?",
                        (trace_data["trace_id"],),
                    ) as span_cursor:
                        span_row = await span_cursor.fetchone()
                        trace_data["span_count"] = span_row[0] if span_row else 0

                    trace = Trace(**trace_data, spans=[])
                    traces.append(trace)

            return traces

    async def save_metric(self, metric: MetricRecord) -> None:
        """Save a metric record."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO metrics (primitive_type, metric_name, value, labels)
                VALUES (?, ?, ?, ?)
                """,
                (
                    metric.primitive_type,
                    metric.metric_name,
                    metric.value,
                    json.dumps(metric.labels),
                ),
            )
            await db.commit()

    async def cleanup_old_traces(self) -> int:
        """Remove traces older than retention period."""
        cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)

        async with aiosqlite.connect(self.db_path) as db:
            # Delete old spans first (foreign key constraint)
            await db.execute(
                """
                DELETE FROM spans WHERE trace_id IN (
                    SELECT trace_id FROM traces WHERE created_at < ?
                )
                """,
                (cutoff.isoformat(),),
            )

            # Delete old traces
            cursor = await db.execute(
                "DELETE FROM traces WHERE created_at < ?", (cutoff.isoformat(),)
            )
            deleted = cursor.rowcount

            await db.commit()

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old traces")

        return deleted

    async def get_stats(self) -> dict[str, Any]:
        """Get storage statistics."""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}

            # Total traces
            async with db.execute("SELECT COUNT(*) FROM traces") as cursor:
                row = await cursor.fetchone()
                stats["total_traces"] = row[0] if row else 0

            # Success rate
            async with db.execute(
                "SELECT COUNT(*) FROM traces WHERE status = 'success'"
            ) as cursor:
                row = await cursor.fetchone()
                success_count = row[0] if row else 0
                stats["success_rate"] = (
                    success_count / stats["total_traces"]
                    if stats["total_traces"] > 0
                    else 0.0
                )

            # Average duration
            async with db.execute(
                "SELECT AVG(duration_ms) FROM traces WHERE duration_ms IS NOT NULL"
            ) as cursor:
                row = await cursor.fetchone()
                stats["avg_duration_ms"] = row[0] if row and row[0] else 0.0

            # Primitive usage
            async with db.execute(
                "SELECT primitive_type, COUNT(*) as count FROM spans GROUP BY primitive_type"
            ) as cursor:
                primitive_usage = {}
                async for row in cursor:
                    primitive_usage[row[0]] = row[1]
                stats["primitive_usage"] = primitive_usage

            return stats
