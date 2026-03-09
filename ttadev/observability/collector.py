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
from datetime import datetime, timezone
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


# Modern TraceCollector for Phase 1 tests
class TraceCollector:
    """Collects traces and persists them to filesystem."""
    
    def __init__(self, traces_dir: Path | str | None = None):
        """Initialize collector.
        
        Args:
            traces_dir: Directory to store traces (default: .observability/traces)
        """
        self.traces_dir = Path(traces_dir) if traces_dir else Path(".observability/traces")
        self.traces_dir.mkdir(parents=True, exist_ok=True)
        self._subscribers: list[asyncio.Queue] = []
    
    async def collect_trace(self, trace_data: dict[str, Any]) -> None:
        """Collect and persist a trace.
        
        Args:
            trace_data: Trace data dictionary with trace_id and spans
        """
        trace_id = trace_data["trace_id"]
        
        # Add timestamp if not present
        if "timestamp" not in trace_data:
            trace_data["timestamp"] = datetime.now(timezone.utc).isoformat() + "Z"
        
        # Write to file
        trace_file = self.traces_dir / f"{trace_id}.json"
        async with aiofiles.open(trace_file, "w") as f:
            await f.write(json.dumps(trace_data, indent=2))
        
        # Broadcast to subscribers
        await self._broadcast(trace_data)
    
    async def _broadcast(self, trace_data: dict[str, Any]) -> None:
        """Broadcast trace to all subscribers."""
        for queue in self._subscribers:
            try:
                await queue.put({"type": "new_trace", "trace": trace_data})
            except Exception:
                pass  # Subscriber queue full or closed
    
    def subscribe(self) -> asyncio.Queue:
        """Subscribe to trace updates.
        
        Returns:
            Queue that will receive trace updates
        """
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.append(queue)
        return queue
    
    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Unsubscribe from trace updates."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)
    
    def get_all_traces(self) -> list[dict[str, Any]]:
        """Get all collected traces.
        
        Returns:
            List of trace dictionaries
        """
        traces = []
        for trace_file in sorted(self.traces_dir.glob("*.json"), reverse=True):
            try:
                with open(trace_file) as f:
                    traces.append(json.load(f))
            except Exception:
                continue  # Skip corrupted files
        return traces
    
    async def close(self):
        """Close resources."""
        pass


# Global singleton instances
observability_collector = ObservabilityCollector()
trace_collector = TraceCollector()  # Legacy

