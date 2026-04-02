"""Async CRUD primitives — thin async wrappers around an in-memory dict store.

Designed as a drop-in that can be backed by SQLAlchemy / Motor / asyncpg in
production.  Currently implemented as in-memory for zero-dependency
development.

Migration path: subclass ``AsyncCRUDStore`` and override each method to issue
real DB queries — all call-sites remain identical because the public interface
is defined here and never changes.

Example::

    from dataclasses import dataclass
    from ttadev.integrations.db.crud import AsyncCRUDStore

    @dataclass
    class Widget:
        id: str
        name: str
        colour: str

    store: AsyncCRUDStore[Widget] = AsyncCRUDStore()

    widget = await store.create(Widget(id="w1", name="Sprocket", colour="blue"))
    found = await store.get("w1")
    updated = await store.update("w1", {"colour": "red"})
    deleted = await store.delete("w1")
"""

from __future__ import annotations

import copy
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class AsyncCRUDStore(Generic[T]):
    """Generic async CRUD store for dataclass models with an ``id: str`` field.

    Items are stored by their ``.id`` attribute.  Deep copies are returned on
    every read so callers cannot mutate the internal state by accident.

    Args:
        Generic[T]: The model type.  Must have an ``id: str`` field.
    """

    def __init__(self) -> None:
        self._store: dict[str, T] = {}

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def create(self, item: T) -> T:
        """Store *item*.

        Args:
            item: The model instance to store.  Must have an ``id`` attribute.

        Returns:
            A deep copy of the stored item.

        Raises:
            ValueError: If an item with the same ``id`` already exists.
        """
        item_id: str = item.id  # type: ignore[attr-defined]
        if item_id in self._store:
            raise ValueError(f"Item with id={item_id!r} already exists")
        self._store[item_id] = copy.deepcopy(item)
        return copy.deepcopy(self._store[item_id])

    async def update(self, item_id: str, updates: dict[str, Any]) -> T | None:
        """Apply field *updates* to the stored item.

        Args:
            item_id: The ``id`` of the item to update.
            updates: Mapping of field names to new values.

        Returns:
            A deep copy of the updated item, or ``None`` if not found.
        """
        stored = self._store.get(item_id)
        if stored is None:
            return None
        for key, value in updates.items():
            object.__setattr__(stored, key, value)
        return copy.deepcopy(stored)

    async def delete(self, item_id: str) -> bool:
        """Delete the item with *item_id*.

        Args:
            item_id: The ``id`` of the item to delete.

        Returns:
            ``True`` if the item was found and deleted, ``False`` otherwise.
        """
        if item_id not in self._store:
            return False
        del self._store[item_id]
        return True

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get(self, item_id: str) -> T | None:
        """Return the item with *item_id*, or ``None`` if not found.

        Args:
            item_id: The ``id`` to look up.

        Returns:
            A deep copy of the item, or ``None``.
        """
        item = self._store.get(item_id)
        return copy.deepcopy(item) if item is not None else None

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """Return all items, paginated by *offset* and *limit*.

        Args:
            limit: Maximum number of items to return (default 100).
            offset: Number of items to skip from the beginning (default 0).

        Returns:
            A list of deep-copied items.
        """
        items = list(self._store.values())
        return [copy.deepcopy(i) for i in items[offset : offset + limit]]

    async def count(self) -> int:
        """Return the total number of stored items.

        Returns:
            Integer count.
        """
        return len(self._store)

    async def find(self, **filters: object) -> list[T]:
        """Filter items by field equality.

        All supplied keyword arguments must match (logical AND).

        Args:
            **filters: Field name / value pairs to match against.

        Returns:
            A list of deep-copied items where every filter matches.

        Example::

            results = await store.find(colour="blue")
        """
        results: list[T] = []
        for item in self._store.values():
            if all(getattr(item, k, object()) == v for k, v in filters.items()):
                results.append(copy.deepcopy(item))
        return results
