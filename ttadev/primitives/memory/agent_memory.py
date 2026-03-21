"""AgentMemory — Hindsight-backed memory service for agents and workflows.

The Recall step of the DevelopmentCycle loop. Provides programmatic access
to Hindsight recall, retain, directives, and mental models.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Literal

from .client import HindsightClient
from .types import MemoryResult, RetainResult

logger = logging.getLogger(__name__)


class AgentMemory:
    """Structured Hindsight layer for agents and workflows.

    Wraps the Hindsight HTTP API. Degrades gracefully when Hindsight is
    unavailable — all methods return safe defaults, never raise on
    connectivity failures.

    Example::

        memory = AgentMemory(bank_id="tta-dev")
        prefix = await memory.build_context_prefix("adding a new primitive")
        # → directives + relevant memories as a system-prompt-friendly string

        await memory.retain("[type: decision] Used FalkorDB direct socket...")
    """

    def __init__(
        self,
        bank_id: str,
        base_url: str | None = None,
        timeout: float = 10.0,
        _client: HindsightClient | None = None,  # injected in tests
    ) -> None:
        self._client = _client or HindsightClient(
            bank_id=bank_id,
            base_url=base_url,
            timeout=timeout,
        )

    # ── Public ────────────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Synchronous liveness check. Returns True if Hindsight is up."""
        return self._client.is_available()

    async def recall(
        self,
        query: str,
        budget: Literal["low", "mid", "high"] = "mid",
        types: list[str] | None = None,
    ) -> list[MemoryResult]:
        """Retrieve semantically relevant memories.

        Args:
            query: Semantic search string. Must not be empty.
            budget: Recall depth — ``"low"`` (fast), ``"mid"`` (default), ``"high"`` (thorough).
            types: Filter by memory type. ``None`` returns all types.

        Returns:
            List of matching memories, or empty list if Hindsight unavailable.

        Raises:
            ValueError: If ``query`` is empty.
        """
        if not query:
            raise ValueError("query must not be empty")
        return await self._client.recall(query, budget=budget, types=types)

    async def retain(
        self,
        content: str,
        async_: bool = True,
    ) -> RetainResult:
        """Store a new memory in the bank.

        Args:
            content: Memory content. Must not be empty.
            async_: If True (default), process in background to avoid rate-limiting.

        Returns:
            RetainResult with success status and optional operation_id.

        Raises:
            ValueError: If ``content`` is empty.
        """
        if not content:
            raise ValueError("content must not be empty")
        return await self._client.retain(content, async_=async_)

    async def get_directives(self) -> list[str]:
        """Fetch directive texts from the bank.

        Returns:
            List of directive content strings. Empty list if Hindsight unavailable.
        """
        return await self._client.get_directives()

    async def get_mental_model(self, name: str) -> str | None:
        """Fetch a named mental model's content.

        Returns:
            Content string, or None if not found or Hindsight unavailable.
        """
        return await self._client.get_mental_model(name)

    async def build_context_prefix(self, query: str) -> str:
        """Fetch directives and recall relevant memories concurrently.

        Formats the combined result as a system-prompt-friendly string prefix.
        Returns empty string if both sources return empty.

        Args:
            query: Semantic search string for recall. Must not be empty.

        Raises:
            ValueError: If ``query`` is empty.
        """
        if not query:
            raise ValueError("query must not be empty")

        directives, memories = await asyncio.gather(
            self._client.get_directives(),
            self._client.recall(query),
        )

        if not directives and not memories:
            return ""

        parts: list[str] = []
        if directives:
            parts.append("## Directives")
            parts.extend(f"- {d}" for d in directives)
        if memories:
            parts.append("## Relevant context")
            parts.extend(f"- {m['text']}" for m in memories)

        return "\n".join(parts)
