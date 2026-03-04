"""Abstract Unit of Work pattern primitive."""

import abc
from types import TracebackType


class AbstractUnitOfWork(abc.ABC):
    """Abstract base class for the Unit of Work pattern."""

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()

    @abc.abstractmethod
    def commit(self) -> None: ...

    @abc.abstractmethod
    def rollback(self) -> None: ...


class FakeUnitOfWork(AbstractUnitOfWork):
    """Minimal in-memory UoW for toolkit-level tests.

    Domain-specific fakes extend this by adding repository attributes.
    """

    def __init__(self) -> None:
        self.committed = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.committed = False
