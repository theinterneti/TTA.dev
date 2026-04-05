"""Tests for ttadev.primitives.memory.in_memory_backend."""

from __future__ import annotations

import pytest

from ttadev.primitives.memory.in_memory_backend import InMemoryBackend


class TestInMemoryBackendInit:
    def test_defaults_empty(self):
        b = InMemoryBackend()
        assert b._memories == []
        assert b._directives == []
        assert b._mental_models == {}

    def test_seed_directives(self):
        b = InMemoryBackend(directives=["be concise", "use types"])
        assert b._directives == ["be concise", "use types"]

    def test_seed_mental_models(self):
        b = InMemoryBackend(mental_models={"arch": "primitives-first"})
        assert b._mental_models == {"arch": "primitives-first"}

    def test_is_available_always_true(self):
        assert InMemoryBackend().is_available() is True


class TestInMemoryBackendRecall:
    @pytest.mark.asyncio
    async def test_recall_empty(self):
        b = InMemoryBackend()
        results = await b.recall("anything")
        assert results == []

    @pytest.mark.asyncio
    async def test_recall_matches_word(self):
        b = InMemoryBackend()
        await b.retain("use async def for I/O")
        results = await b.recall("async")
        assert len(results) == 1
        assert "async" in results[0]["text"]

    @pytest.mark.asyncio
    async def test_recall_case_insensitive(self):
        b = InMemoryBackend()
        await b.retain("Use Pytest for testing")
        results = await b.recall("pytest")
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_recall_no_match(self):
        b = InMemoryBackend()
        await b.retain("use ruff for linting")
        results = await b.recall("mypy")
        assert results == []

    @pytest.mark.asyncio
    async def test_recall_type_filter(self):
        b = InMemoryBackend()
        b.seed_memory("world fact", type_="world")
        b.seed_memory("experience fact", type_="experience")
        world_results = await b.recall("fact", types=["world"])
        assert len(world_results) == 1
        assert world_results[0]["type"] == "world"

    @pytest.mark.asyncio
    async def test_recall_budget_ignored(self):
        b = InMemoryBackend()
        await b.retain("hello world")
        results = await b.recall("hello", budget="high")
        assert len(results) == 1


class TestInMemoryBackendRetain:
    @pytest.mark.asyncio
    async def test_retain_returns_success(self):
        b = InMemoryBackend()
        result = await b.retain("some content")
        assert result["success"] is True
        assert result["operation_id"] is not None

    @pytest.mark.asyncio
    async def test_retain_stores_memory(self):
        b = InMemoryBackend()
        await b.retain("stored text")
        results = await b.recall("stored")
        assert len(results) == 1
        assert results[0]["text"] == "stored text"


class TestInMemoryBackendDirectives:
    @pytest.mark.asyncio
    async def test_get_directives_empty(self):
        b = InMemoryBackend()
        assert await b.get_directives() == []

    @pytest.mark.asyncio
    async def test_get_directives_seeded(self):
        b = InMemoryBackend(directives=["always add types"])
        dirs = await b.get_directives()
        assert "always add types" in dirs

    def test_add_directive(self):
        b = InMemoryBackend()
        b.add_directive("be concise")
        assert "be concise" in b._directives


class TestInMemoryBackendMentalModels:
    @pytest.mark.asyncio
    async def test_get_mental_model_missing(self):
        b = InMemoryBackend()
        assert await b.get_mental_model("arch") is None

    @pytest.mark.asyncio
    async def test_get_mental_model_found(self):
        b = InMemoryBackend(mental_models={"arch": "primitives"})
        result = await b.get_mental_model("arch")
        assert result == "primitives"

    def test_add_mental_model(self):
        b = InMemoryBackend()
        b.add_mental_model("style", "ruff + pyright")
        assert b._mental_models["style"] == "ruff + pyright"


class TestInMemoryBackendSeedMemory:
    def test_seed_memory_returns_id(self):
        b = InMemoryBackend()
        mem_id = b.seed_memory("direct inject", type_="world")
        assert mem_id is not None
        assert len(b._memories) == 1
        assert b._memories[0]["type"] == "world"
