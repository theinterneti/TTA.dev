"""Conditional workflow primitive composition."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from opentelemetry import trace

from ..observability.enhanced_collector import get_enhanced_metrics_collector
from ..observability.instrumented_primitive import TRACING_AVAILABLE
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
        Execute conditional branching with comprehensive instrumentation.

        This method provides observability for conditional execution:
        - Creates spans for condition evaluation and branch execution
        - Logs condition evaluation and branch selection
        - Records per-branch metrics (duration, success/failure)
        - Tracks checkpoints for timing analysis
        - Monitors branch selection patterns

        Args:
            input_data: Input data for the primitive
            context: Workflow context

        Returns:
            Output from the selected branch, or input if no else branch

        Raises:
            Exception: If the selected primitive fails
        """
        metrics_collector = get_enhanced_metrics_collector()

        # Log workflow start
        logger.info(
            "conditional_workflow_start",
            has_else_branch=self.else_primitive is not None,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Record start checkpoint
        context.checkpoint("conditional.start")
        workflow_start_time = time.time()

        # Evaluate condition with instrumentation
        context.checkpoint("conditional.condition_eval.start")
        condition_start_time = time.time()

        try:
            condition_result = self.condition(input_data, context)
        except Exception as e:
            logger.error(
                "conditional_condition_error",
                error=str(e),
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            raise

        condition_duration_ms = (time.time() - condition_start_time) * 1000
        context.checkpoint("conditional.condition_eval.end")

        # Log condition evaluation result
        logger.info(
            "conditional_condition_evaluated",
            condition_result=condition_result,
            duration_ms=condition_duration_ms,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Record condition evaluation metrics
        metrics_collector.record_execution(
            "ConditionalPrimitive.condition_eval",
            duration_ms=condition_duration_ms,
            success=True,
        )

        # Determine which branch to execute
        if condition_result:
            branch_name = "then"
            selected_primitive = self.then_primitive
        elif self.else_primitive:
            branch_name = "else"
            selected_primitive = self.else_primitive
        else:
            # No else branch - pass through
            logger.info(
                "conditional_passthrough",
                reason="no_else_branch",
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            context.checkpoint("conditional.end")
            workflow_duration_ms = (time.time() - workflow_start_time) * 1000

            logger.info(
                "conditional_workflow_complete",
                branch_taken="passthrough",
                total_duration_ms=workflow_duration_ms,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            return input_data

        # Log branch selection
        logger.info(
            "conditional_branch_selected",
            branch=branch_name,
            primitive_type=selected_primitive.__class__.__name__,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Execute selected branch with instrumentation
        context.checkpoint(f"conditional.branch_{branch_name}.start")
        branch_start_time = time.time()

        # Create branch span (if tracing available)
        tracer = trace.get_tracer(__name__) if TRACING_AVAILABLE else None

        if tracer and TRACING_AVAILABLE:
            with tracer.start_as_current_span(f"conditional.branch_{branch_name}") as span:
                span.set_attribute("branch.name", branch_name)
                span.set_attribute("branch.condition_result", condition_result)
                span.set_attribute("branch.primitive_type", selected_primitive.__class__.__name__)

                try:
                    result = await selected_primitive.execute(input_data, context)
                    span.set_attribute("branch.status", "success")
                except Exception as e:
                    span.set_attribute("branch.status", "error")
                    span.set_attribute("branch.error", str(e))
                    span.record_exception(e)
                    raise
        else:
            # Graceful degradation - execute without span
            result = await selected_primitive.execute(input_data, context)

        # Record checkpoint and metrics
        context.checkpoint(f"conditional.branch_{branch_name}.end")
        branch_duration_ms = (time.time() - branch_start_time) * 1000
        metrics_collector.record_execution(
            f"ConditionalPrimitive.branch_{branch_name}",
            duration_ms=branch_duration_ms,
            success=True,
        )

        # Log branch completion
        logger.info(
            "conditional_branch_complete",
            branch=branch_name,
            primitive_type=selected_primitive.__class__.__name__,
            duration_ms=branch_duration_ms,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Record end checkpoint
        context.checkpoint("conditional.end")
        workflow_duration_ms = (time.time() - workflow_start_time) * 1000

        # Log workflow completion
        logger.info(
            "conditional_workflow_complete",
            branch_taken=branch_name,
            total_duration_ms=workflow_duration_ms,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        return result


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
        Execute switch branching with comprehensive instrumentation.

        This method provides observability for switch execution:
        - Creates spans for selector evaluation and case execution
        - Logs selector evaluation and case selection
        - Records per-case metrics (duration, success/failure)
        - Tracks checkpoints for timing analysis
        - Monitors case selection patterns

        Args:
            input_data: Input data for the primitive
            context: Workflow context

        Returns:
            Output from the selected case, default, or input

        Raises:
            Exception: If the selected primitive fails
        """
        metrics_collector = get_enhanced_metrics_collector()

        # Log workflow start
        logger.info(
            "switch_workflow_start",
            case_count=len(self.cases),
            has_default=self.default is not None,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Record start checkpoint
        context.checkpoint("switch.start")
        workflow_start_time = time.time()

        # Evaluate selector with instrumentation
        context.checkpoint("switch.selector_eval.start")
        selector_start_time = time.time()

        try:
            case_key = self.selector(input_data, context)
        except Exception as e:
            logger.error(
                "switch_selector_error",
                error=str(e),
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            raise

        selector_duration_ms = (time.time() - selector_start_time) * 1000
        context.checkpoint("switch.selector_eval.end")

        # Log selector evaluation result
        logger.info(
            "switch_selector_evaluated",
            case_key=case_key,
            duration_ms=selector_duration_ms,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Record selector evaluation metrics
        metrics_collector.record_execution(
            "SwitchPrimitive.selector_eval",
            duration_ms=selector_duration_ms,
            success=True,
        )

        # Determine which case to execute
        if case_key in self.cases:
            case_name = f"case_{case_key}"
            selected_primitive = self.cases[case_key]
        elif self.default:
            case_name = "default"
            selected_primitive = self.default
        else:
            # No matching case or default - pass through
            logger.info(
                "switch_passthrough",
                reason="no_matching_case_or_default",
                case_key=case_key,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            context.checkpoint("switch.end")
            workflow_duration_ms = (time.time() - workflow_start_time) * 1000

            logger.info(
                "switch_workflow_complete",
                case_taken="passthrough",
                case_key=case_key,
                total_duration_ms=workflow_duration_ms,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            return input_data

        # Log case selection
        logger.info(
            "switch_case_selected",
            case_name=case_name,
            case_key=case_key,
            primitive_type=selected_primitive.__class__.__name__,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Execute selected case with instrumentation
        context.checkpoint(f"switch.{case_name}.start")
        case_start_time = time.time()

        # Create case span (if tracing available)
        tracer = trace.get_tracer(__name__) if TRACING_AVAILABLE else None

        if tracer and TRACING_AVAILABLE:
            with tracer.start_as_current_span(f"switch.{case_name}") as span:
                span.set_attribute("case.name", case_name)
                span.set_attribute("case.key", case_key)
                span.set_attribute("case.primitive_type", selected_primitive.__class__.__name__)

                try:
                    result = await selected_primitive.execute(input_data, context)
                    span.set_attribute("case.status", "success")
                except Exception as e:
                    span.set_attribute("case.status", "error")
                    span.set_attribute("case.error", str(e))
                    span.record_exception(e)
                    raise
        else:
            # Graceful degradation - execute without span
            result = await selected_primitive.execute(input_data, context)

        # Record checkpoint and metrics
        context.checkpoint(f"switch.{case_name}.end")
        case_duration_ms = (time.time() - case_start_time) * 1000
        metrics_collector.record_execution(
            f"SwitchPrimitive.{case_name}",
            duration_ms=case_duration_ms,
            success=True,
        )

        # Log case completion
        logger.info(
            "switch_case_complete",
            case_name=case_name,
            case_key=case_key,
            primitive_type=selected_primitive.__class__.__name__,
            duration_ms=case_duration_ms,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Record end checkpoint
        context.checkpoint("switch.end")
        workflow_duration_ms = (time.time() - workflow_start_time) * 1000

        # Log workflow completion
        logger.info(
            "switch_workflow_complete",
            case_taken=case_name,
            case_key=case_key,
            total_duration_ms=workflow_duration_ms,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        return result
