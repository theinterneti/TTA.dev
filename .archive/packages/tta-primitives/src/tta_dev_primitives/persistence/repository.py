"""Minimal repository interface for use within a Unit of Work."""

import abc
from typing import Generic, TypeVar

T = TypeVar("T")


class AbstractRepository(abc.ABC, Generic[T]):
    """Minimal repository interface for use within a Unit of Work."""

    @abc.abstractmethod
    def add(self, entity: T) -> None: ...

    @abc.abstractmethod
    def get(self, reference: str) -> T | None: ...

    @abc.abstractmethod
    def list(self) -> list[T]: ...
