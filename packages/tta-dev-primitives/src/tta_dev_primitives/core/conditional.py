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
        
        # Log condition evaluation
        logger.info(
            "conditional_evaluated",
            condition_result=condition_result,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )
        
        # Store branch decision in context state
        context.state["last_conditional_branch"] = "then" if condition_result else "else"
        
        if condition_result:
            logger.info(
                "conditional_then_branch",
                primitive=self.then_primitive.__class__.__name__,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            return await self.then_primitive.execute(input_data, context)
        elif self.else_primitive:
            logger.info(
                "conditional_else_branch",
                primitive=self.else_primitive.__class__.__name__,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            return await self.else_primitive.execute(input_data, context)
        else:
            logger.info(
                "conditional_no_else_passthrough",
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            # No else branch, pass through input
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
        
        # Log case selection
        logger.info(
            "switch_case_selected",
            case_key=case_key,
            has_matching_case=case_key in self.cases,
            has_default=self.default is not None,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )
        
        # Store case selection in context state
        context.state["last_switch_case"] = case_key

        if case_key in self.cases:
            logger.info(
                "switch_executing_case",
                case_key=case_key,
                primitive=self.cases[case_key].__class__.__name__,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            return await self.cases[case_key].execute(input_data, context)
        elif self.default:
            logger.info(
                "switch_executing_default",
                case_key=case_key,
                primitive=self.default.__class__.__name__,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            return await self.default.execute(input_data, context)
        else:
            logger.info(
                "switch_no_match_passthrough",
                case_key=case_key,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            # No matching case or default, pass through input
            return input_data
