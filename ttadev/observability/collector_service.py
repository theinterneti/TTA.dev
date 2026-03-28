#!/usr/bin/env python3
"""
Persistent Observability Collector Service

This service runs continuously in the background collecting telemetry data
from all TTA.dev primitives, workflows, and agents. Data is persisted to disk
so the dashboard can display historical data even after restarts.
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult


class SQLiteSpanExporter(SpanExporter):
    """Export spans to SQLite database for persistent storage."""

    def __init__(self, db_path: str = ".tta/traces.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                start_time REAL,
                end_time REAL,
                duration_ms REAL,
                status TEXT,
                workflow_type TEXT,
                metadata TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spans (
                span_id TEXT PRIMARY KEY,
                trace_id TEXT,
                parent_span_id TEXT,
                name TEXT,
                primitive_type TEXT,
                start_time REAL,
                end_time REAL,
                duration_ms REAL,
                status TEXT,
                attributes TEXT,
                events TEXT,
                FOREIGN KEY (trace_id) REFERENCES traces(trace_id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_traces_start_time
            ON traces(start_time DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_spans_trace_id
            ON spans(trace_id)
        """)

        conn.commit()
        conn.close()

    def export(self, spans: list[ReadableSpan]) -> SpanExportResult:
        """Export spans to SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for span in spans:
                if span.context is None:
                    continue
                trace_id = format(span.context.trace_id, "032x")
                span_id = format(span.context.span_id, "016x")
                parent_span_id = format(span.parent.span_id, "016x") if span.parent else None

                start_time = span.start_time / 1e9 if span.start_time else 0
                end_time = span.end_time / 1e9 if span.end_time else 0
                duration_ms = (end_time - start_time) * 1000

                attributes = dict(span.attributes) if span.attributes else {}
                primitive_type = attributes.get("primitive.type", "unknown")
                workflow_type = attributes.get("workflow.type", "unknown")
                status = span.status.status_code.name.lower()

                # Store trace (upsert)
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO traces
                    (trace_id, start_time, end_time, duration_ms, status, workflow_type, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        trace_id,
                        start_time,
                        end_time,
                        duration_ms,
                        status,
                        workflow_type,
                        json.dumps(attributes),
                    ),
                )

                # Store span
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO spans
                    (span_id, trace_id, parent_span_id, name, primitive_type,
                     start_time, end_time, duration_ms, status, attributes, events)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        span_id,
                        trace_id,
                        parent_span_id,
                        span.name,
                        primitive_type,
                        start_time,
                        end_time,
                        duration_ms,
                        status,
                        json.dumps(attributes),
                        json.dumps(
                            [
                                {
                                    "name": e.name,
                                    "timestamp": e.timestamp / 1e9,
                                    "attributes": dict(e.attributes) if e.attributes else {},
                                }
                                for e in span.events
                            ]
                        ),
                    ),
                )

            conn.commit()
            conn.close()
            return SpanExportResult.SUCCESS

        except Exception as e:
            print(f"Failed to export spans: {e}")
            return SpanExportResult.FAILURE

    def shutdown(self):
        """Cleanup on shutdown."""
        pass


def get_recent_traces(db_path: str = ".tta/traces.db", limit: int = 100) -> list[dict[str, Any]]:
    """Get recent traces from database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT trace_id, start_time, end_time, duration_ms, status, workflow_type, metadata
        FROM traces
        ORDER BY start_time DESC
        LIMIT ?
    """,
        (limit,),
    )

    traces = []
    for row in cursor.fetchall():
        trace_id, start_time, end_time, duration_ms, status, workflow_type, metadata = row

        # Get spans for this trace
        cursor.execute(
            """
            SELECT span_id, parent_span_id, name, primitive_type,
                   start_time, end_time, duration_ms, status, attributes, events
            FROM spans
            WHERE trace_id = ?
            ORDER BY start_time
        """,
            (trace_id,),
        )

        spans = []
        for span_row in cursor.fetchall():
            spans.append(
                {
                    "span_id": span_row[0],
                    "parent_span_id": span_row[1],
                    "name": span_row[2],
                    "primitive_type": span_row[3],
                    "start_time": span_row[4],
                    "end_time": span_row[5],
                    "duration_ms": span_row[6],
                    "status": span_row[7],
                    "attributes": json.loads(span_row[8]),
                    "events": json.loads(span_row[9]),
                }
            )

        traces.append(
            {
                "trace_id": trace_id,
                "start_time": start_time,
                "end_time": end_time,
                "duration_ms": duration_ms,
                "status": status,
                "workflow_type": workflow_type,
                "metadata": json.loads(metadata),
                "spans": spans,
            }
        )

    conn.close()
    return traces


async def run_collector_service():
    """Run the persistent collector service."""
    print("🔍 TTA.dev Observability Collector Service")
    print("=" * 50)
    print("📊 Collecting telemetry data to: .tta/traces.db")
    print(f"🚀 Service started at: {datetime.now().isoformat()}")
    print("=" * 50)

    # Keep service running
    while True:
        await asyncio.sleep(60)
        print(f"[{datetime.now().isoformat()}] Collector service running...")


if __name__ == "__main__":
    asyncio.run(run_collector_service())
