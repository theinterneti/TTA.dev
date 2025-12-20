"""Mock primitives for testing.

# See: [[TTA.dev/Primitives/MockPrimitive]]
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..core.base import WorkflowContext, WorkflowPrimitive


class MockPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Mock primitive for testing.

    Example:
        ```python
        mock = MockPrimitive(
            name="test_primitive",
            return_value={"result": "success"}
        )

        workflow = mock >> another_primitive
        result = await workflow.execute(input_data, context)

        assert mock.call_count == 1
        assert mock.calls[0][0] == input_data
        ```
    """

    def __init__(
        self,
        name: str,
        return_value: Any | None = None,
        side_effect: Callable | None = None,
        raise_error: Exception | None = None,
    ) -> None:
        """
        Initialize mock primitive.

        Args:
            name: Name of the mock
            return_value: Value to return (if no side_effect or error)
            side_effect: Function to call instead of returning value
            raise_error: Exception to raise when executed
        """
        self.name = name
        self.return_value = return_value
        self.side_effect = side_effect
        self.raise_error = raise_error

        self.call_count = 0
        self.calls: list[tuple[Any, WorkflowContext]] = []

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute mock primitive.

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Configured return value or side effect result

        Raises:
            Exception: If configured to raise
        """
        self.call_count += 1
        self.calls.append((input_data, context))

        if self.raise_error:
            raise self.raise_error

        if self.side_effect:
            result = self.side_effect(input_data, context)
            # Handle async side effects
            if hasattr(result, "__await__"):
                return await result
            return result

        return self.return_value

    def assert_called(self) -> None:
        """Assert the mock was called at least once."""
        assert self.call_count > 0, f"Mock {self.name} was not called"

    def assert_called_once(self) -> None:
        """Assert the mock was called exactly once."""
        assert self.call_count == 1, f"Mock {self.name} called {self.call_count} times, expected 1"

    def assert_called_with(self, input_data: Any, context: WorkflowContext | None = None) -> None:
        """
        Assert the mock was called with specific arguments.

        Args:
            input_data: Expected input data
            context: Optional expected context
        """
        self.assert_called()
        last_input, last_context = self.calls[-1]

        assert last_input == input_data, f"Expected input {input_data}, got {last_input}"

        if context is not None:
            assert last_context == context, f"Expected context {context}, got {last_context}"

    def reset(self) -> None:
        """Reset call tracking."""
        self.call_count = 0
        self.calls.clear()


class WorkflowTestCase:
    """
    Test case helper for workflow testing.

    Example:
        ```python
        async def test_workflow():
            mock1 = MockPrimitive("step1", return_value={"data": "processed"})
            mock2 = MockPrimitive("step2", return_value={"data": "final"})

            workflow = mock1 >> mock2

            test_case = WorkflowTestCase(workflow)
            result = await test_case.execute({"input": "test"})

            test_case.assert_primitive_called(mock1, times=1)
            test_case.assert_primitive_called(mock2, times=1)
            assert result == {"data": "final"}
        ```
    """

    def __init__(self, workflow: WorkflowPrimitive) -> None:
        """
        Initialize test case.

        Args:
            workflow: Workflow to test
        """
        self.workflow = workflow
        self.mocks: list[MockPrimitive] = []

    async def execute(self, input_data: Any, context: WorkflowContext | None = None) -> Any:
        """
        Execute workflow with test context.

        Args:
            input_data: Input data
            context: Optional workflow context

        Returns:
            Workflow result
        """
        if context is None:
            context = WorkflowContext()

        return await self.workflow.execute(input_data, context)

    def assert_primitive_called(self, mock: MockPrimitive, times: int | None = None) -> None:
        """
        Assert a mock primitive was called.

        Args:
            mock: Mock primitive to check
            times: Optional expected call count
        """
        if times is not None:
            assert mock.call_count == times, (
                f"Expected {times} calls to {mock.name}, got {mock.call_count}"
            )
        else:
            assert mock.call_count > 0, f"Expected {mock.name} to be called"

    def reset_mocks(self) -> None:
        """Reset all tracked mocks."""
        for mock in self.mocks:
            mock.reset()
