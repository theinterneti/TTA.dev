"""Tests for memory primitives (InMemoryStore and MemoryPrimitive)."""

import pytest

from tta_dev_primitives.performance.memory import (
    InMemoryStore,
    MemoryPrimitive,
    create_memory_key,
)


class TestInMemoryStore:
    """Tests for InMemoryStore."""

    def test_init(self) -> None:
        """Test store initialization."""
        store = InMemoryStore(max_size=100)
        assert store.max_size == 100
        assert store.size() == 0

    def test_add_and_get(self) -> None:
        """Test adding and retrieving items."""
        store = InMemoryStore()
        store.add("key1", {"data": "value1"})

        result = store.get("key1")
        assert result == {"data": "value1"}

    def test_get_nonexistent(self) -> None:
        """Test retrieving nonexistent key."""
        store = InMemoryStore()
        result = store.get("missing")
        assert result is None

    def test_lru_eviction(self) -> None:
        """Test LRU eviction when max_size exceeded."""
        store = InMemoryStore(max_size=3)

        # Add 4 items (should evict first)
        store.add("key1", {"order": 1})
        store.add("key2", {"order": 2})
        store.add("key3", {"order": 3})
        store.add("key4", {"order": 4})

        # key1 should be evicted
        assert store.get("key1") is None
        assert store.get("key2") == {"order": 2}
        assert store.get("key3") == {"order": 3}
        assert store.get("key4") == {"order": 4}
        assert store.size() == 3

    def test_lru_access_order(self) -> None:
        """Test that accessing an item updates LRU order."""
        store = InMemoryStore(max_size=3)

        store.add("key1", {"order": 1})
        store.add("key2", {"order": 2})
        store.add("key3", {"order": 3})

        # Access key1 (moves to end)
        store.get("key1")

        # Add key4 (should evict key2, not key1)
        store.add("key4", {"order": 4})

        assert store.get("key1") == {"order": 1}
        assert store.get("key2") is None
        assert store.get("key3") == {"order": 3}
        assert store.get("key4") == {"order": 4}

    def test_search_keyword(self) -> None:
        """Test keyword search."""
        store = InMemoryStore()
        store.add("key1", {"content": "hello world"})
        store.add("key2", {"content": "goodbye world"})
        store.add("key3", {"content": "hello universe"})

        results = store.search("hello")
        assert len(results) == 2
        assert any("hello world" in str(r) for r in results)
        assert any("hello universe" in str(r) for r in results)

    def test_search_limit(self) -> None:
        """Test search result limiting."""
        store = InMemoryStore()
        for i in range(10):
            store.add(f"key{i}", {"content": f"item {i}"})

        results = store.search("item", limit=3)
        assert len(results) == 3

    def test_clear(self) -> None:
        """Test clearing store."""
        store = InMemoryStore()
        store.add("key1", {"data": "value1"})
        store.add("key2", {"data": "value2"})

        assert store.size() == 2
        store.clear()
        assert store.size() == 0
        assert store.get("key1") is None

    def test_keys(self) -> None:
        """Test getting all keys."""
        store = InMemoryStore()
        store.add("key1", {"data": "value1"})
        store.add("key2", {"data": "value2"})

        keys = store.keys()
        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys


class TestCreateMemoryKey:
    """Tests for create_memory_key helper."""

    def test_basic_key(self) -> None:
        """Test basic key generation."""
        key = create_memory_key("user123", "session456")
        assert key == "user123:session456"

    def test_key_with_context(self) -> None:
        """Test key generation with context."""
        context = {"task": "summarize"}
        key1 = create_memory_key("user123", "session456", context)
        key2 = create_memory_key("user123", "session456", context)

        # Same context should produce same key
        assert key1 == key2
        assert key1.startswith("user123:session456:")

        # Different context should produce different key
        key3 = create_memory_key("user123", "session456", {"task": "translate"})
        assert key3 != key1


class TestMemoryPrimitive:
    """Tests for MemoryPrimitive."""

    @pytest.mark.asyncio
    async def test_init_fallback_only(self) -> None:
        """Test initialization with fallback only."""
        memory = MemoryPrimitive()
        assert not memory.is_using_redis()
        assert memory.fallback is not None

    @pytest.mark.asyncio
    async def test_init_with_invalid_redis(self) -> None:
        """Test initialization with invalid Redis URL falls back gracefully."""
        memory = MemoryPrimitive(redis_url="redis://invalid:9999")
        assert not memory.is_using_redis()
        assert memory.fallback is not None

    @pytest.mark.asyncio
    async def test_add_and_get(self) -> None:
        """Test adding and retrieving memories."""
        memory = MemoryPrimitive()

        await memory.add("test_key", {"content": "test value"})
        result = await memory.get("test_key")

        assert result == {"content": "test value"}

    @pytest.mark.asyncio
    async def test_get_nonexistent(self) -> None:
        """Test retrieving nonexistent memory."""
        memory = MemoryPrimitive()
        result = await memory.get("missing_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_search(self) -> None:
        """Test searching memories."""
        memory = MemoryPrimitive()

        await memory.add("key1", {"content": "python programming"})
        await memory.add("key2", {"content": "java programming"})
        await memory.add("key3", {"content": "python data science"})

        results = await memory.search("python")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_size(self) -> None:
        """Test getting memory size."""
        memory = MemoryPrimitive()

        assert memory.size() == 0

        await memory.add("key1", {"data": "value1"})
        await memory.add("key2", {"data": "value2"})

        assert memory.size() == 2

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        """Test clearing memories."""
        memory = MemoryPrimitive()

        await memory.add("key1", {"data": "value1"})
        await memory.add("key2", {"data": "value2"})

        await memory.clear()
        assert memory.size() == 0

    @pytest.mark.asyncio
    async def test_backend_info(self) -> None:
        """Test getting backend information."""
        memory = MemoryPrimitive()

        info = memory.get_backend_info()
        assert info["backend"] == "in-memory"
        assert info["fallback_available"] is True
        assert "size" in info
