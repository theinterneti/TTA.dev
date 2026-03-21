"""AgentMemory types — MemoryResult and RetainResult TypedDicts."""

from __future__ import annotations

from typing import TypedDict


class MemoryResult(TypedDict):
    """A single recalled memory item from Hindsight."""

    id: str
    text: str
    type: str | None  # "world", "experience", "observation", or None


class RetainResult(TypedDict):
    """Result of a retain operation."""

    success: bool
    operation_id: str | None  # None for sync retains or when unavailable
