"""Base workflow primitive abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


class WorkflowContext(BaseModel):
    """Context passed through workflow execution."""

    workflow_id: str | None = None
    session_id: str | None = None
    player_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    state: dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class WorkflowPrimitive(Generic[T, U], ABC):
    """
    Base class for composable workflow primitives.

    Primitives are the building blocks of workflows. They can be composed
    using operators:
    - `>>` for sequential execution (self then other)
    - `|` for parallel execution (self and other concurrently)

    Example:
        ```python
        workflow = primitive1 >> primitive2 >> primitive3
        result = await workflow.execute(input_data, context)
        ```
    """

    @abstractmethod
    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """
        Execute the primitive with input data and context.

        Args:
            input_data: Input data for the primitive
            context: Workflow context with session/state information

        Returns:
            Output data from the primitive

        Raises:
            Exception: If execution fails
        """
        pass

    def __rshift__(self, other: WorkflowPrimitive[U, V]) -> WorkflowPrimitive[T, V]:
        """
        Chain primitives sequentially: self >> other.

        The output of self becomes the input to other.

        Args:
            other: The primitive to execute after this one

        Returns:
            A new sequential primitive
        """
        from .sequential import SequentialPrimitive

        return SequentialPrimitive([self, other])

    def __or__(self, other: WorkflowPrimitive[T, U]) -> WorkflowPrimitive[T, list[U]]:
        """
        Execute primitives in parallel: self | other.

        Both primitives receive the same input and execute concurrently.

        Args:
            other: The primitive to execute in parallel

        Returns:
            A new parallel primitive
        """
        from .parallel import ParallelPrimitive

        return ParallelPrimitive([self, other])


class LambdaPrimitive(WorkflowPrimitive[T, U]):
    """
    Primitive that wraps a simple function or lambda.

    Useful for simple transformations or adapters.

    Example:
        ```python
        transform = LambdaPrimitive(lambda x, ctx: x.upper())
        workflow = input_primitive >> transform >> output_primitive
        ```
    """

    def __init__(self, func: Any) -> None:
        """
        Initialize with a function.

        Args:
            func: Async or sync function (input, context) -> output
        """
        self.func = func
        import inspect

        self.is_async = inspect.iscoroutinefunction(func)

    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """Execute the wrapped function."""
        if self.is_async:
            return await self.func(input_data, context)
        else:
            return self.func(input_data, context)
