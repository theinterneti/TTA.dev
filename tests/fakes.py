"""In-memory fakes for domain-layer testing without real databases.

These fakes implement the Repository and Unit-of-Work patterns using plain
Python collections so that service-layer tests can run fast and in complete
isolation from Redis, Neo4j, or any other external store.

Usage::

    from tests.fakes import FakeRepository, FakeUnitOfWork

    repo = FakeRepository[str]()
    uow = FakeUnitOfWork(entities=repo)

    async with uow:
        await uow.entities.add("item-1", {"name": "first"})
        await uow.commit()

    assert await repo.get("item-1") == {"name": "first"}
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

T = TypeVar("T")


class FakeRepository(Generic[T]):
    """In-memory repository backed by a Python dict.

    Provides async CRUD methods that mirror a typical repository interface
    so service-layer tests can swap it in without touching the database.
    """

    def __init__(self) -> None:
        self._store: dict[str, T] = {}

    async def add(self, key: str, entity: T) -> None:
        """Add an entity to the repository."""
        self._store[key] = entity

    async def get(self, key: str) -> T | None:
        """Retrieve an entity by key, or ``None`` if absent."""
        return self._store.get(key)

    async def list_all(self) -> list[T]:
        """Return all entities."""
        return list(self._store.values())

    async def delete(self, key: str) -> bool:
        """Remove an entity by key. Returns ``True`` if it existed."""
        return self._store.pop(key, None) is not None

    async def exists(self, key: str) -> bool:
        """Check whether an entity with the given key exists."""
        return key in self._store

    def clear(self) -> None:
        """Remove all entities (useful in teardown)."""
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


class FakeUnitOfWork:
    """In-memory unit-of-work that groups repository mutations into a transaction.

    On ``commit()`` changes are "persisted" (kept in the fake repo).
    On ``rollback()`` the repository is restored to its pre-transaction snapshot.

    Can be used as an async context manager::

        async with FakeUnitOfWork(entities=repo) as uow:
            await uow.entities.add("k", value)
            await uow.commit()
    """

    def __init__(self, **repositories: FakeRepository[Any]) -> None:
        self._repos = repositories
        self._snapshots: dict[str, dict[str, Any]] = {}
        self.committed = False

        # Expose each repository as a named attribute
        for name, repo in repositories.items():
            setattr(self, name, repo)

    async def __aenter__(self) -> FakeUnitOfWork:
        # Snapshot each repo so we can rollback
        for name, repo in self._repos.items():
            self._snapshots[name] = dict(repo._store)
        self.committed = False
        return self

    async def __aexit__(self, exc_type: type | None, *_: Any) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        """Mark the transaction as committed (data already in-memory)."""
        self.committed = True
        # Update snapshots to the new state
        for name, repo in self._repos.items():
            self._snapshots[name] = dict(repo._store)

    async def rollback(self) -> None:
        """Restore each repository to its pre-transaction state."""
        for name, repo in self._repos.items():
            repo._store = dict(self._snapshots.get(name, {}))
        self.committed = False
