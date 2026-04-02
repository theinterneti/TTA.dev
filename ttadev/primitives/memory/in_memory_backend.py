"""InMemoryBackend — pure in-memory backend for AgentMemory.

Drop-in replacement for HindsightClient for tests and ephemeral sessions.
No external dependencies; everything is stored in plain Python dicts.
"""

from __future__ import annotations

import uuid
from typing import Literal

from .types import MemoryResult, RetainResult


class InMemoryBackend:
    """Pure in-memory implementation of the HindsightClient interface.

    Stores memories, directives, and mental models in plain Python dicts.
    Implements the same async interface as ``HindsightClient`` — use it as a
    drop-in replacement for tests or short-lived sessions that do not need
    Hindsight persistence.

    Args:
        directives: Initial directive strings to seed the backend.
        mental_models: Initial mapping of ``name → content`` for mental models.

    Example::

        from ttadev.primitives.memory import AgentMemory, InMemoryBackend

        backend = InMemoryBackend()
        memory = AgentMemory(bank_id="test", _client=backend)
        await memory.retain("prefers concise answers")
        results = await memory.recall("concise")
        # → [MemoryResult(id=..., text="prefers concise answers", type=None)]
    """

    def __init__(
        self,
        directives: list[str] | None = None,
        mental_models: dict[str, str] | None = None,
    ) -> None:
        self._memories: list[MemoryResult] = []
        self._directives: list[str] = list(directives or [])
        self._mental_models: dict[str, str] = dict(mental_models or {})

    # ── HindsightClient interface ──────────────────────────────────────────────

    def is_available(self) -> bool:
        """Always returns ``True`` — no external service required."""
        return True

    async def recall(
        self,
        query: str,
        budget: Literal["low", "mid", "high"] = "mid",
        types: list[str] | None = None,
    ) -> list[MemoryResult]:
        """Return memories whose text contains any word from *query*.

        Search is case-insensitive and word-based. The *budget* parameter is
        accepted for interface compatibility but ignored.

        Args:
            query: Space-separated search terms.
            budget: Ignored — present for interface compatibility only.
            types: Optional type filter (``"world"``, ``"experience"``, etc.).
                ``None`` returns all types.

        Returns:
            List of matching :class:`MemoryResult` entries.
        """
        words = [w for w in query.lower().split() if w]
        results: list[MemoryResult] = []
        for mem in self._memories:
            text_lower = mem["text"].lower()
            if any(word in text_lower for word in words):
                if types is None or mem.get("type") in types:
                    results.append(mem)
        return results

    async def retain(
        self,
        content: str,
        async_: bool = True,
    ) -> RetainResult:
        """Store *content* as a new memory entry.

        Args:
            content: Memory text to store.
            async_: Accepted for interface compatibility; always behaves
                synchronously (the store is in-process).

        Returns:
            :class:`RetainResult` with ``success=True`` and a generated
            ``operation_id``.
        """
        op_id = str(uuid.uuid4())
        self._memories.append(MemoryResult(id=op_id, text=content, type=None))
        return RetainResult(success=True, operation_id=op_id)

    async def get_directives(self) -> list[str]:
        """Return all stored directive strings.

        Returns:
            Snapshot list of directive strings.
        """
        return list(self._directives)

    async def get_mental_model(self, name: str) -> str | None:
        """Look up a named mental model.

        Args:
            name: Mental model name.

        Returns:
            Content string, or ``None`` if not found.
        """
        return self._mental_models.get(name)

    # ── Convenience helpers for test setup ────────────────────────────────────

    def add_directive(self, directive: str) -> None:
        """Append a directive string (convenience for test setup).

        Args:
            directive: Directive text to add.
        """
        self._directives.append(directive)

    def add_mental_model(self, name: str, content: str) -> None:
        """Add or replace a named mental model (convenience for test setup).

        Args:
            name: Model name.
            content: Model content.
        """
        self._mental_models[name] = content

    def seed_memory(self, text: str, type_: str | None = None) -> str:
        """Directly inject a memory entry (convenience for test setup).

        Args:
            text: Memory text.
            type_: Optional memory type (``"world"``, ``"experience"``, etc.).

        Returns:
            The generated memory id.
        """
        mem_id = str(uuid.uuid4())
        self._memories.append(MemoryResult(id=mem_id, text=text, type=type_))
        return mem_id
