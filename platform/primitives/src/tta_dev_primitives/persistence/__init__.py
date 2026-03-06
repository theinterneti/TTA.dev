"""Persistence primitives: AbstractRepository and AbstractUnitOfWork."""

from .repository import AbstractRepository
from .unit_of_work import AbstractUnitOfWork, FakeUnitOfWork

__all__ = ["AbstractRepository", "AbstractUnitOfWork", "FakeUnitOfWork"]
