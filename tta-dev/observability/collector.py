"""Simple trace collector for TTA.dev observability.

This module provides a global singleton collector that buffers spans
and sends them to the observability dashboard via WebSocket.
"""

import asyncio
import json
from collections import defaultdict
from typing import Any

import aiohttp


class TraceCollector:
    """Singleton trace collector that sends spans to the dashboard."""

    def __init__(self):
        self.spans_by_trace = defaultdict(list)
        self.dashboard_url = "http://localhost:8000"
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def collect_span(self, span_data: dict[str, Any]) -> None:
        """
        Collect a span and send it to the dashboard.

        Args:
            span_data: Span information including:
                - name: Span name (primitive name)
                - start_time: Start timestamp
                - end_time: End timestamp
                - duration_ms: Duration in milliseconds
                - status: "ok" or "error"
                - attributes: Dict of span attributes
        """
        # Add to local buffer
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
            # We don't want observability to break the application
            pass

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()


# Global singleton instance
trace_collector = TraceCollector()
