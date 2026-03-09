"""Persistent trace collector for TTA.dev observability.

This module provides a global singleton collector that:
1. Persists all spans to SQLite database (.tta/traces.db)
2. Sends spans to the dashboard in real-time (if available)
3. Ensures data is never lost even if dashboard is offline
"""

import asyncio
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import aiohttp
import aiosqlite


class TraceCollector:
    """Singleton trace collector with persistent storage."""

    def __init__(self, db_path: str = ".tta/traces.db"):
        self.spans_by_trace = defaultdict(list)
        self.dashboard_url = "http://localhost:8000"
        self._session: aiohttp.ClientSession | None = None
        self.db_path = Path(db_path)
        self._initialized = False

    def initialize(self):
        """Initialize the trace collector (idempotent)."""
        if not self._initialized:
            self._init_db()
            self._initialized = True

    def _init_db(self):
        """Initialize SQLite database for persistent storage (sync init only)."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Use synchronous sqlite3 for initialization only
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT,
                span_name TEXT,
                primitive_type TEXT,
                start_time REAL,
                end_time REAL,
                duration_ms REAL,
                status TEXT,
                attributes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_spans_trace_id 
            ON spans(trace_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_spans_created_at 
            ON spans(created_at DESC)
        """)

        conn.commit()
        conn.close()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _persist_span(self, span_data: dict[str, Any]) -> None:
        """Persist span to SQLite database asynchronously."""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute(
                    """
                    INSERT INTO spans 
                    (trace_id, span_name, primitive_type, start_time, end_time, 
                     duration_ms, status, attributes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        span_data.get("trace_id", "default"),
                        span_data.get("name", "unknown"),
                        span_data.get("attributes", {}).get("primitive.type", "unknown"),
                        span_data.get("start_time", 0),
                        span_data.get("end_time", 0),
                        span_data.get("duration_ms", 0),
                        span_data.get("status", "unknown"),
                        json.dumps(span_data.get("attributes", {})),
                    ),
                )
                await conn.commit()
        except Exception as e:
            print(f"Warning: Failed to persist span to database: {e}")

    async def collect_span(self, span_data: dict[str, Any]) -> None:
        """
        Collect a span and persist it.

        Args:
            span_data: Span information including:
                - name: Span name (primitive name)
                - start_time: Start timestamp
                - end_time: End timestamp
                - duration_ms: Duration in milliseconds
                - status: "ok" or "error"
                - attributes: Dict of span attributes
        """
        # Always persist to database first (critical path) - now async
        await self._persist_span(span_data)

        # Add to in-memory buffer
        trace_id = span_data.get("trace_id", "default")
        self.spans_by_trace[trace_id].append(span_data)

        # Try to send to dashboard (non-blocking, best effort)
        try:
            session = await self._get_session()
            await session.post(
                f"{self.dashboard_url}/api/spans",
                json=span_data,
                timeout=aiohttp.ClientTimeout(total=0.5),
            )
        except Exception:
            # Silently fail if dashboard is not available
            # Data is already persisted to database
            pass

    def get_recent_spans(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent spans from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT trace_id, span_name, primitive_type, start_time, end_time,
                   duration_ms, status, attributes
            FROM spans
            ORDER BY created_at DESC
            LIMIT ?
        """,
            (limit,),
        )

        spans = []
        for row in cursor.fetchall():
            spans.append(
                {
                    "trace_id": row[0],
                    "name": row[1],
                    "primitive_type": row[2],
                    "start_time": row[3],
                    "end_time": row[4],
                    "duration_ms": row[5],
                    "status": row[6],
                    "attributes": json.loads(row[7]),
                }
            )

        conn.close()
        return spans

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()


# Global singleton instance
trace_collector = TraceCollector()
