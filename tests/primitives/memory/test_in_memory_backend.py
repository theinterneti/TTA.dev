"""Unit tests for InMemoryBackend — no external dependencies required."""

from __future__ import annotations

import pytest

from ttadev.primitives.memory import AgentMemory, InMemoryBackend

# ── InMemoryBackend: availability ─────────────────────────────────────────────


class TestInMemoryBackendIsAvailable:
    def test_always_available(self) -> None:
        backend = InMemoryBackend()
        assert backend.is_available() is True


# ── InMemoryBackend: retain + recall ─────────────────────────────────────────


class TestInMemoryBackendRetainAndRecall:
    async def test_retain_returns_success(self) -> None:
        backend = InMemoryBackend()
        result = await backend.retain("some important fact")
        assert result["success"] is True
        assert result["operation_id"] is not None

    async def test_retain_generates_unique_ids(self) -> None:
        backend = InMemoryBackend()
        r1 = await backend.retain("fact one")
        r2 = await backend.retain("fact two")
        assert r1["operation_id"] != r2["operation_id"]

    async def test_recall_empty_store_returns_empty(self) -> None:
        backend = InMemoryBackend()
        results = await backend.recall("anything")
        assert results == []

    async def test_recall_no_match_returns_empty(self) -> None:
        backend = InMemoryBackend()
        await backend.retain("completely unrelated content")
        results = await backend.recall("circuit breaker")
        assert results == []

    async def test_retain_then_recall_exact_word(self) -> None:
        backend = InMemoryBackend()
        await backend.retain("the circuit breaker is closed")
        results = await backend.recall("circuit")
        assert len(results) == 1
        assert "circuit breaker" in results[0]["text"]

    async def test_recall_case_insensitive(self) -> None:
        backend = InMemoryBackend()
        await backend.retain("Used FalkorDB for graph storage")
        results = await backend.recall("FALKORDB")
        assert len(results) == 1

    async def test_recall_multi_word_query_any_word_matches(self) -> None:
        backend = InMemoryBackend()
        await backend.retain("retry timeout handling decision")
        await backend.retain("circuit breaker pattern")
        await backend.retain("completely unrelated")
        # 'retry' matches only first
        results = await backend.recall("retry")
        assert len(results) == 1
        assert "retry" in results[0]["text"]

    async def test_recall_returns_all_matching(self) -> None:
        backend = InMemoryBackend()
        await backend.retain("retry with backoff")
        await backend.retain("retry on 503")
        await backend.retain("timeout only")
        results = await backend.recall("retry")
        assert len(results) == 2

    async def test_recall_type_filter_excludes_non_matching(self) -> None:
        backend = InMemoryBackend()
        backend.seed_memory("experience fact", type_="experience")
        backend.seed_memory("world fact", type_="world")
        results = await backend.recall("fact", types=["experience"])
        assert len(results) == 1
        assert results[0]["type"] == "experience"

    async def test_recall_type_filter_none_returns_all(self) -> None:
        backend = InMemoryBackend()
        backend.seed_memory("experience fact", type_="experience")
        backend.seed_memory("world fact", type_="world")
        results = await backend.recall("fact", types=None)
        assert len(results) == 2

    async def test_recall_budget_param_accepted(self) -> None:
        """budget param is accepted for interface compatibility; ignored."""
        backend = InMemoryBackend()
        await backend.retain("some fact")
        results_low = await backend.recall("fact", budget="low")
        results_high = await backend.recall("fact", budget="high")
        assert results_low == results_high


# ── InMemoryBackend: directives ───────────────────────────────────────────────


class TestInMemoryBackendDirectives:
    async def test_get_directives_empty_by_default(self) -> None:
        backend = InMemoryBackend()
        result = await backend.get_directives()
        assert result == []

    async def test_get_directives_returns_seeded_values(self) -> None:
        backend = InMemoryBackend(directives=["Always orient first", "Use uv"])
        result = await backend.get_directives()
        assert result == ["Always orient first", "Use uv"]

    async def test_get_directives_returns_snapshot_not_reference(self) -> None:
        """Mutating the returned list must not affect the backend."""
        backend = InMemoryBackend(directives=["dir-1"])
        result = await backend.get_directives()
        result.append("injected")
        result2 = await backend.get_directives()
        assert result2 == ["dir-1"]

    async def test_add_directive_helper(self) -> None:
        backend = InMemoryBackend()
        backend.add_directive("new directive")
        result = await backend.get_directives()
        assert "new directive" in result


# ── InMemoryBackend: mental models ────────────────────────────────────────────


class TestInMemoryBackendMentalModels:
    async def test_get_mental_model_returns_none_when_not_found(self) -> None:
        backend = InMemoryBackend()
        result = await backend.get_mental_model("unknown")
        assert result is None

    async def test_get_mental_model_returns_seeded_content(self) -> None:
        backend = InMemoryBackend(mental_models={"primitives": "The primitives system..."})
        result = await backend.get_mental_model("primitives")
        assert result == "The primitives system..."

    async def test_add_mental_model_helper(self) -> None:
        backend = InMemoryBackend()
        backend.add_mental_model("mymodel", "content here")
        result = await backend.get_mental_model("mymodel")
        assert result == "content here"

    async def test_add_mental_model_overwrites_existing(self) -> None:
        backend = InMemoryBackend(mental_models={"m": "old"})
        backend.add_mental_model("m", "new")
        result = await backend.get_mental_model("m")
        assert result == "new"


# ── InMemoryBackend: isolation ────────────────────────────────────────────────


class TestInMemoryBackendIsolation:
    async def test_two_backends_do_not_share_memories(self) -> None:
        backend_a = InMemoryBackend()
        backend_b = InMemoryBackend()
        await backend_a.retain("fact for A")
        results_b = await backend_b.recall("fact")
        assert results_b == []

    async def test_two_backends_do_not_share_directives(self) -> None:
        backend_a = InMemoryBackend(directives=["directive-A"])
        backend_b = InMemoryBackend(directives=["directive-B"])
        assert await backend_a.get_directives() == ["directive-A"]
        assert await backend_b.get_directives() == ["directive-B"]

    async def test_two_backends_do_not_share_mental_models(self) -> None:
        backend_a = InMemoryBackend(mental_models={"m": "content-A"})
        backend_b = InMemoryBackend()
        assert await backend_a.get_mental_model("m") == "content-A"
        assert await backend_b.get_mental_model("m") is None


# ── AgentMemory + InMemoryBackend integration ─────────────────────────────────


class TestAgentMemoryWithInMemoryBackend:
    """End-to-end tests: AgentMemory wired to InMemoryBackend (no Hindsight)."""

    async def test_store_and_retrieve_fact(self) -> None:
        backend = InMemoryBackend()
        memory = AgentMemory(bank_id="test-bank", _client=backend)
        result = await memory.retain("prefers concise answers")
        assert result["success"] is True
        facts = await memory.recall("concise")
        assert len(facts) == 1
        assert "concise" in facts[0]["text"]

    async def test_recall_raises_on_empty_query(self) -> None:
        backend = InMemoryBackend()
        memory = AgentMemory(bank_id="test-bank", _client=backend)
        with pytest.raises(ValueError, match="query must not be empty"):
            await memory.recall("")

    async def test_retain_raises_on_empty_content(self) -> None:
        backend = InMemoryBackend()
        memory = AgentMemory(bank_id="test-bank", _client=backend)
        with pytest.raises(ValueError, match="content must not be empty"):
            await memory.retain("")

    async def test_missing_key_returns_empty(self) -> None:
        backend = InMemoryBackend()
        memory = AgentMemory(bank_id="test-bank", _client=backend)
        results = await memory.recall("nonexistent topic")
        assert results == []

    async def test_is_available_true(self) -> None:
        backend = InMemoryBackend()
        memory = AgentMemory(bank_id="test-bank", _client=backend)
        assert memory.is_available() is True

    async def test_get_directives_returns_seeded(self) -> None:
        backend = InMemoryBackend(directives=["Always orient first", "Use uv"])
        memory = AgentMemory(bank_id="test-bank", _client=backend)
        directives = await memory.get_directives()
        assert directives == ["Always orient first", "Use uv"]

    async def test_get_mental_model_found(self) -> None:
        backend = InMemoryBackend(mental_models={"primitives": "The primitives system..."})
        memory = AgentMemory(bank_id="test-bank", _client=backend)
        result = await memory.get_mental_model("primitives")
        assert result == "The primitives system..."

    async def test_get_mental_model_none_when_missing(self) -> None:
        backend = InMemoryBackend()
        memory = AgentMemory(bank_id="test-bank", _client=backend)
        result = await memory.get_mental_model("nonexistent")
        assert result is None

    async def test_build_context_prefix_combines_directives_and_recall(self) -> None:
        backend = InMemoryBackend(directives=["Always orient first"])
        memory = AgentMemory(bank_id="test-bank", _client=backend)
        await memory.retain("used retry with exponential backoff")
        prefix = await memory.build_context_prefix("retry")
        assert "Always orient first" in prefix
        assert "retry" in prefix

    async def test_build_context_prefix_empty_when_nothing_stored(self) -> None:
        backend = InMemoryBackend()
        memory = AgentMemory(bank_id="test-bank", _client=backend)
        prefix = await memory.build_context_prefix("retry")
        assert prefix == ""

    async def test_build_context_prefix_raises_on_empty_query(self) -> None:
        backend = InMemoryBackend()
        memory = AgentMemory(bank_id="test-bank", _client=backend)
        with pytest.raises(ValueError, match="query must not be empty"):
            await memory.build_context_prefix("")

    async def test_namespace_isolation_via_separate_backends(self) -> None:
        """Two 'namespaces' modelled as two separate InMemoryBackend instances."""
        user_123 = InMemoryBackend()
        user_456 = InMemoryBackend()
        mem_a = AgentMemory(bank_id="user-123", _client=user_123)
        mem_b = AgentMemory(bank_id="user-456", _client=user_456)
        await mem_a.retain("prefers concise answers")
        await mem_b.retain("prefers verbose explanations")
        results_a = await mem_a.recall("prefers")
        results_b = await mem_b.recall("prefers")
        assert len(results_a) == 1
        assert "concise" in results_a[0]["text"]
        assert len(results_b) == 1
        assert "verbose" in results_b[0]["text"]


# ── importability ─────────────────────────────────────────────────────────────


def test_in_memory_backend_importable_from_memory_package() -> None:
    from ttadev.primitives.memory import InMemoryBackend

    assert InMemoryBackend is not None


def test_in_memory_backend_has_no_external_deps() -> None:
    """InMemoryBackend only uses stdlib — uuid, typing."""
    import inspect

    import ttadev.primitives.memory.in_memory_backend as mod

    src = inspect.getsource(mod)
    # No httpx, redis, mongo, etc.
    assert "httpx" not in src
    assert "redis" not in src
    assert "motor" not in src
