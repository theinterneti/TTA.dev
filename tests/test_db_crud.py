"""Unit tests for ttadev.integrations.db.crud — AAA pattern throughout."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import pytest

from ttadev.integrations.db.crud import AsyncCRUDStore

# ---------------------------------------------------------------------------
# Test fixture model
# ---------------------------------------------------------------------------


@dataclass
class Widget:
    """Simple test model with required id field."""

    id: str
    name: str
    colour: str = "blue"
    count: int = 0


def _widget(wid: str = "w1", name: str = "Sprocket", colour: str = "blue") -> Widget:
    return Widget(id=wid, name=name, colour=colour)


# ---------------------------------------------------------------------------
# create / get
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_stores_item_and_get_retrieves_it():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    w = _widget()

    # Act
    created = await store.create(w)
    retrieved = await store.get("w1")

    # Assert
    assert created.id == "w1"
    assert retrieved is not None
    assert retrieved.name == "Sprocket"


@pytest.mark.asyncio
async def test_create_raises_value_error_on_duplicate_id():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    await store.create(_widget("w1"))

    # Act / Assert
    with pytest.raises(ValueError, match="w1"):
        await store.create(_widget("w1"))


@pytest.mark.asyncio
async def test_get_returns_none_for_missing_id():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()

    # Act
    result = await store.get("nonexistent")

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_create_returns_deep_copy_not_same_object():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    original = _widget()

    # Act
    created = await store.create(original)
    original.name = "MUTATED"
    retrieved = await store.get("w1")

    # Assert — store is isolated from external mutations
    assert retrieved is not None
    assert retrieved.name == "Sprocket"
    assert created.name == "Sprocket"


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_all_returns_all_items():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    for i in range(5):
        await store.create(_widget(f"w{i}", f"Widget-{i}"))

    # Act
    items = await store.list_all()

    # Assert
    assert len(items) == 5


@pytest.mark.asyncio
async def test_list_all_respects_limit():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    for i in range(10):
        await store.create(_widget(f"w{i}"))

    # Act
    items = await store.list_all(limit=3)

    # Assert
    assert len(items) == 3


@pytest.mark.asyncio
async def test_list_all_respects_offset():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    for i in range(5):
        await store.create(_widget(f"w{i}"))

    # Act
    items = await store.list_all(limit=100, offset=3)

    # Assert
    assert len(items) == 2


@pytest.mark.asyncio
async def test_list_all_empty_store_returns_empty_list():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()

    # Act
    items = await store.list_all()

    # Assert
    assert items == []


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_modifies_fields_and_returns_updated_item():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    await store.create(_widget("w1", colour="blue"))

    # Act
    updated = await store.update("w1", {"colour": "red", "count": 7})

    # Assert
    assert updated is not None
    assert updated.colour == "red"
    assert updated.count == 7


@pytest.mark.asyncio
async def test_update_persists_changes_visible_via_get():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    await store.create(_widget("w1"))

    # Act
    await store.update("w1", {"name": "Updated"})
    retrieved = await store.get("w1")

    # Assert
    assert retrieved is not None
    assert retrieved.name == "Updated"


@pytest.mark.asyncio
async def test_update_returns_none_for_missing_id():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()

    # Act
    result = await store.update("ghost", {"name": "X"})

    # Assert
    assert result is None


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_returns_true_and_item_is_gone():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    await store.create(_widget("w1"))

    # Act
    deleted = await store.delete("w1")
    gone = await store.get("w1")

    # Assert
    assert deleted is True
    assert gone is None


@pytest.mark.asyncio
async def test_delete_returns_false_for_missing_id():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()

    # Act
    result = await store.delete("nobody")

    # Assert
    assert result is False


# ---------------------------------------------------------------------------
# count
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_count_returns_zero_for_empty_store():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()

    # Act
    n = await store.count()

    # Assert
    assert n == 0


@pytest.mark.asyncio
async def test_count_reflects_creates_and_deletes():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    await store.create(_widget("w1"))
    await store.create(_widget("w2"))
    await store.create(_widget("w3"))
    await store.delete("w2")

    # Act
    n = await store.count()

    # Assert
    assert n == 2


# ---------------------------------------------------------------------------
# find
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_find_filters_by_single_field():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    await store.create(Widget(id="w1", name="A", colour="blue"))
    await store.create(Widget(id="w2", name="B", colour="red"))
    await store.create(Widget(id="w3", name="C", colour="blue"))

    # Act
    results = await store.find(colour="blue")

    # Assert
    assert len(results) == 2
    assert all(r.colour == "blue" for r in results)


@pytest.mark.asyncio
async def test_find_filters_by_multiple_fields():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    await store.create(Widget(id="w1", name="Alpha", colour="blue", count=5))
    await store.create(Widget(id="w2", name="Beta", colour="blue", count=10))
    await store.create(Widget(id="w3", name="Alpha", colour="red", count=5))

    # Act
    results = await store.find(name="Alpha", colour="blue")

    # Assert
    assert len(results) == 1
    assert results[0].id == "w1"


@pytest.mark.asyncio
async def test_find_returns_empty_list_when_no_match():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    await store.create(_widget("w1", colour="blue"))

    # Act
    results = await store.find(colour="green")

    # Assert
    assert results == []


@pytest.mark.asyncio
async def test_find_no_filters_returns_all_items():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    await store.create(_widget("w1"))
    await store.create(_widget("w2"))

    # Act
    results = await store.find()

    # Assert
    assert len(results) == 2


# ---------------------------------------------------------------------------
# Concurrency safety
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_concurrent_creates_are_safe():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()
    widgets = [_widget(f"w{i}", f"Widget-{i}") for i in range(20)]

    # Act — fire all creates concurrently
    results = await asyncio.gather(*[store.create(w) for w in widgets])

    # Assert
    assert len(results) == 20
    assert await store.count() == 20


@pytest.mark.asyncio
async def test_concurrent_creates_raise_on_duplicate_ids():
    # Arrange
    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()

    # Act / Assert — at least one of the duplicate creates must raise
    tasks = [store.create(_widget("same-id")) for _ in range(3)]
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)

    errors = [o for o in outcomes if isinstance(o, ValueError)]
    successes = [o for o in outcomes if isinstance(o, Widget)]
    assert len(successes) == 1
    assert len(errors) == 2
