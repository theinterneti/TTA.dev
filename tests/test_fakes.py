"""Tests for FakeRepository and FakeUnitOfWork test doubles."""

import pytest

from tests.fakes import FakeRepository, FakeUnitOfWork


@pytest.mark.asyncio
async def test_fake_repository_add_and_get():
    """Test basic add/get operations."""
    repo = FakeRepository[dict]()
    await repo.add("k1", {"name": "alpha"})

    result = await repo.get("k1")
    assert result == {"name": "alpha"}


@pytest.mark.asyncio
async def test_fake_repository_get_missing_key():
    """Test that get returns None for unknown keys."""
    repo = FakeRepository[str]()
    assert await repo.get("missing") is None


@pytest.mark.asyncio
async def test_fake_repository_list_all():
    """Test listing all entities."""
    repo = FakeRepository[int]()
    await repo.add("a", 1)
    await repo.add("b", 2)

    items = await repo.list_all()
    assert sorted(items) == [1, 2]


@pytest.mark.asyncio
async def test_fake_repository_delete():
    """Test delete returns True for existing and False for missing."""
    repo = FakeRepository[str]()
    await repo.add("k", "value")

    assert await repo.delete("k") is True
    assert await repo.delete("k") is False
    assert await repo.get("k") is None


@pytest.mark.asyncio
async def test_fake_repository_exists():
    """Test exists check."""
    repo = FakeRepository[str]()
    await repo.add("k", "v")

    assert await repo.exists("k") is True
    assert await repo.exists("nope") is False


@pytest.mark.asyncio
async def test_fake_repository_clear():
    """Test clearing the repository."""
    repo = FakeRepository[str]()
    await repo.add("a", "1")
    await repo.add("b", "2")
    assert len(repo) == 2

    repo.clear()
    assert len(repo) == 0


@pytest.mark.asyncio
async def test_fake_repository_isolation():
    """Two FakeRepository instances must not share state."""
    repo_a = FakeRepository[str]()
    repo_b = FakeRepository[str]()
    await repo_a.add("k", "from-a")

    assert await repo_b.get("k") is None


@pytest.mark.asyncio
async def test_fake_uow_commit():
    """Committed data persists after exiting the context."""
    repo = FakeRepository[str]()
    uow = FakeUnitOfWork(entities=repo)

    async with uow:
        await uow.entities.add("k", "value")
        await uow.commit()

    assert uow.committed is True
    assert await repo.get("k") == "value"


@pytest.mark.asyncio
async def test_fake_uow_rollback_on_exception():
    """Data is rolled back when an exception occurs inside the context."""
    repo = FakeRepository[str]()
    await repo.add("existing", "keep-me")

    uow = FakeUnitOfWork(entities=repo)

    async def _mutate_then_fail():
        async with uow:
            await uow.entities.add("new", "discard-me")
            raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await _mutate_then_fail()

    # The new entry should be rolled back
    assert await repo.get("new") is None
    # The pre-existing entry should still be there
    assert await repo.get("existing") == "keep-me"


@pytest.mark.asyncio
async def test_fake_uow_multiple_repos():
    """UoW can manage several named repositories."""
    users = FakeRepository[dict]()
    orders = FakeRepository[dict]()
    uow = FakeUnitOfWork(users=users, orders=orders)

    async with uow:
        await uow.users.add("u1", {"name": "Alice"})
        await uow.orders.add("o1", {"item": "widget"})
        await uow.commit()

    assert await users.get("u1") == {"name": "Alice"}
    assert await orders.get("o1") == {"item": "widget"}
