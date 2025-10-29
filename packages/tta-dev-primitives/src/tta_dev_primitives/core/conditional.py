"""Conditional workflow primitive composition."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..observability.logging import get_logger
from .base import WorkflowContext, WorkflowPrimitive

logger = get_logger(__name__)


class ConditionalPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Conditional branching primitive.

    Executes different primitives based on a condition function.

    Example:
        ```python
        workflow = ConditionalPrimitive(
            condition=lambda result, ctx: result.safety_level != "blocked",
            then_primitive=standard_narrative,
            else_primitive=safe_narrative
        )
        ```
    """

    def __init__(
        self,
        condition: Callable[[Any, WorkflowContext], bool],
        then_primitive: WorkflowPrimitive,
        else_primitive: WorkflowPrimitive | None = None,
    ) -> None:
        """
        Initialize conditional primitive.

        Args:
            condition: Function (input, context) -> bool to determine branch
            then_primitive: Primitive to execute if condition is True
            else_primitive: Optional primitive to execute if condition is False
        """
        self.condition = condition
        self.then_primitive = then_primitive
        self.else_primitive = else_primitive

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute conditional branching with instrumentation.

        Args:
            input_data: Input data for the primitive
            context: Workflow context

        Returns:
            Output from the selected branch, or input if no else branch

        Raises:
            Exception: If the selected primitive fails
        """
        # Evaluate condition
        condition_result = self.condition(input_data, context)

        # Log branch decision
        logger.info(
            "conditional_branch_decision",
            condition_result=condition_result,
            has_else_branch=self.else_primitive is not None,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Store decision in context for tracing
        if "conditional_decisions" not in context.state:
            context.state["conditional_decisions"] = []
        context.state["conditional_decisions"].append(
            {"branch": "then" if condition_result else "else", "result": condition_result}
        )

        # Execute selected branch
        if condition_result:
            return await self.then_primitive.execute(input_data, context)
        elif self.else_primitive:
            return await self.else_primitive.execute(input_data, context)
        else:
            # No else branch, pass through input
            logger.info(
                "conditional_passthrough",
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            return input_data


class SwitchPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Multi-way conditional branching primitive.

    Like a switch/case statement for workflows.

    Example:
        ```python
        workflow = SwitchPrimitive(
            selector=lambda input, ctx: input.get("intent"),
            cases={
                "explore": explore_primitive,
                "combat": combat_primitive,
                "dialogue": dialogue_primitive,
            },
            default=generic_primitive
        )
        ```
    """

    def __init__(
        self,
        selector: Callable[[Any, WorkflowContext], str],
        cases: dict[str, WorkflowPrimitive],
        default: WorkflowPrimitive | None = None,
    ) -> None:
        """
        Initialize switch primitive.

        Args:
            selector: Function (input, context) -> str to select case
            cases: Map of case values to primitives
            default: Optional default primitive if no case matches
        """
        self.selector = selector
        self.cases = cases
        self.default = default

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute switch branching with instrumentation.

        Args:
            input_data: Input data for the primitive
            context: Workflow context

        Returns:
            Output from the selected case, default, or input

        Raises:
            Exception: If the selected primitive fails
        """
        # Select case
        case_key = self.selector(input_data, context)

        # Determine which branch will execute
        has_match = case_key in self.cases
        will_use_default = not has_match and self.default is not None

        # Log case selection
        logger.info(
            "switch_case_selection",
            case_key=case_key,
            has_match=has_match,
            will_use_default=will_use_default,
            available_cases=list(self.cases.keys()),
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Store selection in context for tracing
        if "switch_selections" not in context.state:
            context.state["switch_selections"] = []
        context.state["switch_selections"].append(
            {
                "case_key": case_key,
                "matched": has_match,
                "used_default": will_use_default,
            }
        )

        # Execute selected case
        if case_key in self.cases:
            return await self.cases[case_key].execute(input_data, context)
        elif self.default:
            logger.info(
                "switch_using_default",
                case_key=case_key,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            return await self.default.execute(input_data, context)
        else:
            # No matching case or default, pass through input
            logger.info(
                "switch_passthrough",
                case_key=case_key,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            return input_data
