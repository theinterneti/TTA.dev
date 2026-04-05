"""Tests for ttadev.primitives.persistence.unit_of_work."""

from __future__ import annotations

from ttadev.primitives.persistence.unit_of_work import AbstractUnitOfWork, FakeUnitOfWork


class TestFakeUnitOfWork:
    def test_initial_not_committed(self):
        uow = FakeUnitOfWork()
        assert uow.committed is False

    def test_commit_sets_flag(self):
        uow = FakeUnitOfWork()
        uow.commit()
        assert uow.committed is True

    def test_rollback_clears_flag(self):
        uow = FakeUnitOfWork()
        uow.commit()
        uow.rollback()
        assert uow.committed is False

    def test_context_manager_enter_returns_self(self):
        uow = FakeUnitOfWork()
        result = uow.__enter__()
        assert result is uow

    def test_context_manager_no_exception(self):
        uow = FakeUnitOfWork()
        with uow:
            uow.commit()
        assert uow.committed is True

    def test_context_manager_exception_calls_rollback(self):
        uow = FakeUnitOfWork()
        try:
            with uow:
                uow.commit()
                raise ValueError("boom")
        except ValueError:
            pass
        # rollback was called — committed is False again
        assert uow.committed is False

    def test_context_manager_exit_no_exception_no_rollback(self):
        uow = FakeUnitOfWork()
        uow.commit()
        uow.__exit__(None, None, None)
        assert uow.committed is True  # not rolled back

    def test_isinstance_abstract(self):
        assert isinstance(FakeUnitOfWork(), AbstractUnitOfWork)
