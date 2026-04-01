"""Tests for AbstractUnitOfWork and FakeUnitOfWork."""

import pytest

from ttadev.primitives.persistence.unit_of_work import AbstractUnitOfWork, FakeUnitOfWork


class ConcreteUnitOfWork(AbstractUnitOfWork):
    """Minimal concrete implementation for testing abstract base."""

    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class TestAbstractUnitOfWork:
    def test_context_manager_enter_returns_self(self) -> None:
        uow = ConcreteUnitOfWork()
        with uow as result:
            assert result is uow

    def test_context_manager_no_exception_does_not_rollback(self) -> None:
        uow = ConcreteUnitOfWork()
        with uow:
            pass
        assert not uow.rolled_back

    def test_context_manager_exception_triggers_rollback(self) -> None:
        uow = ConcreteUnitOfWork()
        with pytest.raises(ValueError):
            with uow:
                raise ValueError("boom")
        assert uow.rolled_back

    def test_exit_called_directly_without_exception(self) -> None:
        uow = ConcreteUnitOfWork()
        uow.__exit__(None, None, None)
        assert not uow.rolled_back

    def test_exit_called_directly_with_exception(self) -> None:
        uow = ConcreteUnitOfWork()
        uow.__exit__(ValueError, ValueError("err"), None)
        assert uow.rolled_back

    def test_cannot_instantiate_abstract_class(self) -> None:
        with pytest.raises(TypeError):
            AbstractUnitOfWork()  # type: ignore[abstract]


class TestFakeUnitOfWork:
    def test_initial_state(self) -> None:
        uow = FakeUnitOfWork()
        assert not uow.committed

    def test_commit_sets_committed(self) -> None:
        uow = FakeUnitOfWork()
        uow.commit()
        assert uow.committed

    def test_rollback_clears_committed(self) -> None:
        uow = FakeUnitOfWork()
        uow.commit()
        uow.rollback()
        assert not uow.committed

    def test_context_manager_success(self) -> None:
        uow = FakeUnitOfWork()
        with uow:
            uow.commit()
        assert uow.committed

    def test_context_manager_exception_rolls_back_via_base(self) -> None:
        uow = FakeUnitOfWork()
        uow.commit()
        with pytest.raises(RuntimeError):
            with uow:
                raise RuntimeError("test error")
        assert not uow.committed
