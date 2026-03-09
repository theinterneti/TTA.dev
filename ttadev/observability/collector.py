"""Persistent trace collector for TTA.dev observability.

This module provides file-based trace collection that:
1. Records trace events to JSONL files (.tta/traces/active/*.jsonl)
2. Moves completed traces to .tta/traces/completed/
3. Provides concurrent-safe event recording
4. Zero external dependencies (no databases)
"""

import asyncio
import json
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any
import aiofiles
import aiofiles.os


@dataclass
class TraceEvent:
    """A single event in a trace."""
    trace_id: str
    span_id: str
    event_type: str
    timestamp: str
    data: dict[str, Any]
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> "TraceEvent":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls(**data)


class ObservabilityCollector:
    """File-based trace event collector with concurrent-safe writes."""

    def __init__(self, trace_dir: Path | str = ".tta/traces"):
        """Initialize collector with trace directory.
        
        Args:
            trace_dir: Directory to store trace files
        """
        self.trace_dir = Path(trace_dir)
        self.active_dir = self.trace_dir / "active"
        self.completed_dir = self.trace_dir / "completed"
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        
        # Create directory structure
        self.active_dir.mkdir(parents=True, exist_ok=True)
        self.completed_dir.mkdir(parents=True, exist_ok=True)

    async def record_event(self, event: TraceEvent) -> None:
        """Record a trace event to the active trace file.
        
        Args:
            event: The trace event to record
        """
        async with self._locks[event.trace_id]:
            trace_file = self.active_dir / f"{event.trace_id}.jsonl"
            async with aiofiles.open(trace_file, "a") as f:
                await f.write(event.to_json() + "\n")

    async def complete_trace(self, trace_id: str) -> None:
        """Move a trace from active to completed.
        
        Args:
            trace_id: The trace ID to complete
        """
        async with self._locks[trace_id]:
            active_file = self.active_dir / f"{trace_id}.jsonl"
            completed_file = self.completed_dir / f"{trace_id}.jsonl"
            
            if await aiofiles.os.path.exists(active_file):
                # Read and write (aiofiles doesn't have rename)
                async with aiofiles.open(active_file, "r") as src:
                    content = await src.read()
                async with aiofiles.open(completed_file, "w") as dst:
                    await dst.write(content)
                await aiofiles.os.remove(active_file)

    async def list_active_traces(self) -> list[str]:
        """List all active trace IDs.
        
        Returns:
            List of active trace IDs
        """
        files = list(self.active_dir.glob("*.jsonl"))
        return [f.stem for f in files]

    async def get_trace_events(self, trace_id: str) -> list[TraceEvent]:
        """Get all events for a trace.
        
        Args:
            trace_id: The trace ID to retrieve
            
        Returns:
            List of trace events
        """
        # Check active first, then completed
        trace_file = self.active_dir / f"{trace_id}.jsonl"
        if not await aiofiles.os.path.exists(trace_file):
            trace_file = self.completed_dir / f"{trace_id}.jsonl"
        
        if not await aiofiles.os.path.exists(trace_file):
            return []
        
        events = []
        async with aiofiles.open(trace_file, "r") as f:
            async for line in f:
                if line.strip():
                    events.append(TraceEvent.from_json(line))
        
        return events


# Legacy compatibility - keep TraceCollector for backward compat
class TraceCollector:
    """Legacy SQLite-based collector (deprecated)."""

    def __init__(self, db_path: str = ".tta/traces.db"):
        self.spans_by_trace = defaultdict(list)
        self.dashboard_url = "http://localhost:8000"
        self._session = None
        self.db_path = Path(db_path)
        self._initialized = False

    def initialize(self):
        """Initialize the trace collector (no-op for compatibility)."""
        self._initialized = True

    async def collect_span(self, span_data: dict[str, Any]) -> None:
        """Collect span (compatibility method)."""
        trace_id = span_data.get("trace_id", "default")
        self.spans_by_trace[trace_id].append(span_data)

    def get_recent_spans(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent spans (compatibility method)."""
        all_spans = []
        for spans in self.spans_by_trace.values():
            all_spans.extend(spans)
        return all_spans[-limit:]

    async def close(self):
        """Close resources."""
        pass


# Global singleton instances
observability_collector = ObservabilityCollector()
trace_collector = TraceCollector()  # Legacy

