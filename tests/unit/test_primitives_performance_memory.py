"""Unit tests for ttadev/primitives/performance/memory.py.

Covers InMemoryStore (LRU cache + keyword search), create_memory_key,
and MemoryPrimitive (hybrid in-memory/Redis with automatic fallback).
All tests use the in-memory backend only — no Redis required.
"""

from __future__ import annotations

import pytest

from ttadev.primitives.performance.memory import (
    InMemoryStore,
    MemoryPrimitive,
    create_memory_key,
)

# ---------------------------------------------------------------------------
# InMemoryStore
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestInMemoryStore:
    """InMemoryStore: LRU cache with keyword search."""

    def test_add_and_get_round_trip(self) -> None:
        store = InMemoryStore()
        store.add("k1", {"data": "hello"})
        assert store.get("k1") == {"data": "hello"}

    def test_get_missing_key_returns_none(self) -> None:
        store = InMemoryStore()
        assert store.get("missing") is None

    def test_size_reflects_item_count(self) -> None:
        store = InMemoryStore()
        assert store.size() == 0
        store.add("a", {"x": 1})
        store.add("b", {"x": 2})
        assert store.size() == 2

    def test_keys_returns_all_keys(self) -> None:
        store = InMemoryStore()
        store.add("a", {})
        store.add("b", {})
        assert set(store.keys()) == {"a", "b"}

    def test_update_existing_key(self) -> None:
        store = InMemoryStore()
        store.add("k", {"v": 1})
        store.add("k", {"v": 2})
        assert store.get("k") == {"v": 2}
        assert store.size() == 1

    def test_lru_eviction_when_full(self) -> None:
        store = InMemoryStore(max_size=2)
        store.add("oldest", {"x": 0})
        store.add("middle", {"x": 1})
        store.add("newest", {"x": 2})  # should evict "oldest"
        assert store.get("oldest") is None
        assert store.get("middle") is not None
        assert store.get("newest") is not None

    def test_get_marks_item_as_recently_used(self) -> None:
        store = InMemoryStore(max_size=2)
        store.add("a", {"x": 1})
        store.add("b", {"x": 2})
        store.get("a")  # mark "a" as recently used
        store.add("c", {"x": 3})  # should evict "b", not "a"
        assert store.get("a") is not None
        assert store.get("b") is None

    def test_clear_removes_all_items(self) -> None:
        store = InMemoryStore()
        store.add("a", {})
        store.add("b", {})
        store.clear()
        assert store.size() == 0
        assert store.get("a") is None

    def test_search_finds_matching_item(self) -> None:
        store = InMemoryStore()
        store.add("k1", {"topic": "python testing"})
        store.add("k2", {"topic": "javascript"})
        results = store.search("python")
        assert len(results) == 1
        assert results[0]["topic"] == "python testing"

    def test_search_empty_query_returns_empty(self) -> None:
        store = InMemoryStore()
        store.add("k", {"data": "stuff"})
        assert store.search("") == []

    def test_search_no_match_returns_empty(self) -> None:
        store = InMemoryStore()
        store.add("k", {"data": "hello"})
        assert store.search("xyz_no_match") == []

    def test_search_limit_is_respected(self) -> None:
        store = InMemoryStore()
        for i in range(10):
            store.add(f"k{i}", {"common": "term", "idx": i})
        results = store.search("common", limit=3)
        assert len(results) == 3

    def test_search_is_case_insensitive(self) -> None:
        store = InMemoryStore()
        store.add("k", {"msg": "Hello World"})
        assert store.search("hello") != []
        assert store.search("WORLD") != []


# ---------------------------------------------------------------------------
# create_memory_key
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCreateMemoryKey:
    """create_memory_key produces stable, unique keys."""

    def test_basic_key_format(self) -> None:
        key = create_memory_key("user1", "sess1")
        assert key == "user1:sess1"

    def test_context_adds_hash_suffix(self) -> None:
        key = create_memory_key("user1", "sess1", context={"page": "home"})
        parts = key.split(":")
        assert parts[0] == "user1"
        assert parts[1] == "sess1"
        assert len(parts) == 3  # base + hash suffix

    def test_same_context_produces_same_key(self) -> None:
        ctx = {"a": 1, "b": 2}
        k1 = create_memory_key("u", "s", context=ctx)
        k2 = create_memory_key("u", "s", context=ctx)
        assert k1 == k2

    def test_different_context_produces_different_key(self) -> None:
        k1 = create_memory_key("u", "s", context={"x": 1})
        k2 = create_memory_key("u", "s", context={"x": 2})
        assert k1 != k2

    def test_none_context_omits_hash(self) -> None:
        key = create_memory_key("u", "s", context=None)
        assert key == "u:s"


# ---------------------------------------------------------------------------
# MemoryPrimitive (in-memory backend only)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMemoryPrimitive:
    """MemoryPrimitive: async API over InMemoryStore with optional Redis."""

    @pytest.fixture
    def memory(self) -> MemoryPrimitive:
        return MemoryPrimitive(redis_url=None)

    async def test_add_and_get(self, memory: MemoryPrimitive) -> None:
        await memory.add("k1", {"val": 42})
        result = await memory.get("k1")
        assert result == {"val": 42}

    async def test_get_missing_returns_none(self, memory: MemoryPrimitive) -> None:
        assert await memory.get("nope") is None

    async def test_search_finds_stored_item(self, memory: MemoryPrimitive) -> None:
        await memory.add("k", {"content": "unique-term-xyz"})
        results = await memory.search("unique-term-xyz")
        assert len(results) == 1

    async def test_search_empty_returns_empty(self, memory: MemoryPrimitive) -> None:
        results = await memory.search("")
        assert results == []

    async def test_clear_empties_store(self, memory: MemoryPrimitive) -> None:
        await memory.add("a", {"x": 1})
        await memory.clear()
        assert memory.size() == 0

    async def test_size_increases_with_adds(self, memory: MemoryPrimitive) -> None:
        assert memory.size() == 0
        await memory.add("a", {})
        await memory.add("b", {})
        assert memory.size() == 2

    def test_not_using_redis_by_default(self, memory: MemoryPrimitive) -> None:
        assert memory.is_using_redis() is False

    def test_redis_disabled_flag(self) -> None:
        m = MemoryPrimitive(redis_url="redis://localhost:9999", enable_redis=False)
        assert m.is_using_redis() is False

    def test_unreachable_redis_falls_back(self) -> None:
        # Port 9 is the discard port — connection will fail immediately
        m = MemoryPrimitive(redis_url="redis://localhost:1")
        assert m.is_using_redis() is False

    def test_get_backend_info_in_memory(self, memory: MemoryPrimitive) -> None:
        info = memory.get_backend_info()
        assert info["backend"] == "in-memory"
        assert info["fallback_available"] is True

    async def test_search_limit_respected(self, memory: MemoryPrimitive) -> None:
        for i in range(10):
            await memory.add(f"k{i}", {"tag": "common", "i": i})
        results = await memory.search("common", limit=3)
        assert len(results) == 3
