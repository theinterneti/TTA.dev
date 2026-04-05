"""Tests for ttadev.primitives.memory.agent_memory.AgentMemory."""

from __future__ import annotations

import pytest

from ttadev.primitives.memory.agent_memory import AgentMemory
from ttadev.primitives.memory.in_memory_backend import InMemoryBackend


def make_memory(**kwargs) -> AgentMemory:
    """AgentMemory with injected InMemoryBackend — no network."""
    backend = InMemoryBackend(**kwargs)
    return AgentMemory(bank_id="test", _client=backend)


class TestAgentMemoryIsAvailable:
    def test_is_available_with_in_memory_backend(self):
        mem = make_memory()
        assert mem.is_available() is True


class TestAgentMemoryRecall:
    @pytest.mark.asyncio
    async def test_recall_empty_store(self):
        mem = make_memory()
        results = await mem.recall("anything")
        assert results == []

    @pytest.mark.asyncio
    async def test_recall_matches_retained(self):
        mem = make_memory()
        await mem.retain("use pytest for tests")
        results = await mem.recall("pytest")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_recall_empty_query_raises(self):
        mem = make_memory()
        with pytest.raises(ValueError, match="query must not be empty"):
            await mem.recall("")

    @pytest.mark.asyncio
    async def test_recall_with_types(self):
        backend = InMemoryBackend()
        backend.seed_memory("world note", type_="world")
        mem = AgentMemory(bank_id="test", _client=backend)
        results = await mem.recall("note", types=["world"])
        assert len(results) == 1


class TestAgentMemoryRetain:
    @pytest.mark.asyncio
    async def test_retain_success(self):
        mem = make_memory()
        result = await mem.retain("a new memory")
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_retain_empty_raises(self):
        mem = make_memory()
        with pytest.raises(ValueError, match="content must not be empty"):
            await mem.retain("")

    @pytest.mark.asyncio
    async def test_retain_async_flag(self):
        mem = make_memory()
        result = await mem.retain("content", async_=False)
        assert result["success"] is True


class TestAgentMemoryDirectives:
    @pytest.mark.asyncio
    async def test_get_directives_empty(self):
        mem = make_memory()
        assert await mem.get_directives() == []

    @pytest.mark.asyncio
    async def test_get_directives_seeded(self):
        mem = make_memory(directives=["always add types"])
        dirs = await mem.get_directives()
        assert "always add types" in dirs


class TestAgentMemoryMentalModel:
    @pytest.mark.asyncio
    async def test_get_mental_model_missing(self):
        mem = make_memory()
        assert await mem.get_mental_model("arch") is None

    @pytest.mark.asyncio
    async def test_get_mental_model_found(self):
        mem = make_memory(mental_models={"arch": "primitives-first"})
        result = await mem.get_mental_model("arch")
        assert result == "primitives-first"


class TestAgentMemoryBuildContextPrefix:
    @pytest.mark.asyncio
    async def test_empty_query_raises(self):
        mem = make_memory()
        with pytest.raises(ValueError, match="query must not be empty"):
            await mem.build_context_prefix("")

    @pytest.mark.asyncio
    async def test_returns_empty_when_nothing(self):
        mem = make_memory()
        prefix = await mem.build_context_prefix("something")
        assert prefix == ""

    @pytest.mark.asyncio
    async def test_returns_directives_section(self):
        mem = make_memory(directives=["use uv always"])
        prefix = await mem.build_context_prefix("query")
        assert "## Directives" in prefix
        assert "use uv always" in prefix

    @pytest.mark.asyncio
    async def test_returns_memories_section(self):
        mem = make_memory()
        await mem.retain("always write tests")
        prefix = await mem.build_context_prefix("tests")
        assert "## Relevant context" in prefix
        assert "always write tests" in prefix

    @pytest.mark.asyncio
    async def test_returns_both_sections(self):
        mem = make_memory(directives=["be concise"])
        await mem.retain("use async def for I/O")
        prefix = await mem.build_context_prefix("async")
        assert "## Directives" in prefix
        assert "## Relevant context" in prefix
