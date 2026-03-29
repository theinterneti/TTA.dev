"""Safety gate primitive for severity-based routing and human escalation.

Generalizes the TTA 5-level crisis detection pattern into a reusable composable
primitive that any AI application with safety requirements can use.

Example:
    ```python
    from ttadev.primitives.safety import SafetyGatePrimitive, SeverityLevel

    safety = SafetyGatePrimitive(
        scorer=my_crisis_detector,
        handlers={
            SeverityLevel.LOW: warning_handler,
            SeverityLevel.CRITICAL: escalation_handler,
        },
        block_on_critical=True,
    )
    workflow = safety >> narrative_generator
    ```
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from enum import IntEnum
from typing import Any

from opentelemetry import trace

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.instrumented_primitive import TRACING_AVAILABLE
from ..observability.logging import get_logger

logger = get_logger(__name__)


class SeverityLevel(IntEnum):
    """Five-level severity scale for safety assessment.

    Mirrors TTA's crisis detection levels (NONE → CRITICAL), generalised for
    any domain: content moderation, compliance checks, therapeutic safety, etc.
    """

    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class SafetyGateEscalatedError(Exception):
    """Raised when ``SafetyGatePrimitive`` blocks on a CRITICAL severity.

    Catching this exception is the caller's mechanism for knowing that the
    pipeline was intentionally halted and a human review gate was created.

    Attributes:
        severity: The severity level that triggered the escalation.
        task_id: The L0 workflow task ID (if one was found in context).
    """

    def __init__(self, *, severity: SeverityLevel, task_id: str | None = None) -> None:
        self.severity = severity
        self.task_id = task_id
        super().__init__(
            f"Safety gate escalated: severity={severity.name}"
            + (f", task_id={task_id}" if task_id else "")
        )


class SafetyGatePrimitive(WorkflowPrimitive[Any, Any]):
    """Score input severity, route to handlers, and optionally block on CRITICAL.

    This primitive wraps any workflow input with a safety assessment layer.
    The scorer assigns a ``SeverityLevel``; the primitive then:

    1. Calls the registered handler for that level (if one exists), using its
       result as the output.
    2. If no handler is registered, passes the original input through unchanged.
    3. When severity is ``CRITICAL`` and ``block_on_critical=True``, records an
       ``ESCALATE_TO_HUMAN`` gate in the L0 control plane (if a service is
       provided) and raises ``SafetyGateEscalatedError`` to halt the pipeline.

    Args:
        scorer: Async function ``(input, context) -> SeverityLevel``.
        handlers: Map of ``SeverityLevel`` to a primitive that transforms the
            input for that level.  At CRITICAL with ``block_on_critical``, the
            handler (if present) is called *before* the error is raised so
            callers can capture a formatted escalation response.
        block_on_critical: If ``True`` (default), CRITICAL severity raises
            ``SafetyGateEscalatedError`` after calling any registered handler.
        service: Optional ``ControlPlaneService`` instance. When provided,
            an ``ESCALATE_TO_HUMAN`` gate outcome is recorded before raising.
    """

    def __init__(
        self,
        scorer: Callable[[Any, WorkflowContext], Awaitable[SeverityLevel]],
        handlers: dict[SeverityLevel, WorkflowPrimitive] | None = None,
        block_on_critical: bool = True,
        service: Any | None = None,
    ) -> None:
        self.scorer = scorer
        self.handlers: dict[SeverityLevel, WorkflowPrimitive] = handlers or {}
        self.block_on_critical = block_on_critical
        self.service = service

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """Score, route, and optionally block on CRITICAL severity.

        Args:
            input_data: The workflow payload to assess.
            context: Workflow context; ``workflow_id`` is used as the L0 task
                identifier when recording an escalation gate.

        Returns:
            Either the handler's output (if a handler is registered for the
            detected severity) or the original ``input_data`` unchanged.

        Raises:
            SafetyGateEscalatedError: When severity is ``CRITICAL`` and
                ``block_on_critical`` is ``True``.
        """
        severity: SeverityLevel = await self.scorer(input_data, context)

        tracer = trace.get_tracer(__name__) if TRACING_AVAILABLE else None

        if tracer:
            with tracer.start_as_current_span("safety_gate.execute") as span:
                span.set_attribute("safety.severity", severity.name)
                span.set_attribute("safety.severity_level", int(severity))
                span.set_attribute("safety.block_on_critical", self.block_on_critical)
                span.set_attribute("safety.has_handler", severity in self.handlers)
                try:
                    result = await self._route(severity, input_data, context)
                    span.set_attribute("safety.escalated", False)
                    return result
                except SafetyGateEscalatedError as exc:
                    span.set_attribute("safety.escalated", True)
                    span.record_exception(exc)
                    raise
                except Exception as exc:
                    span.record_exception(exc)
                    raise
        else:
            return await self._route(severity, input_data, context)

    async def _route(
        self,
        severity: SeverityLevel,
        input_data: Any,
        context: WorkflowContext,
    ) -> Any:
        """Apply handler routing and blocking logic for *severity*.

        Args:
            severity: Assessed severity level.
            input_data: Original workflow payload.
            context: Workflow context.

        Returns:
            Handler output or original input_data.

        Raises:
            SafetyGateEscalatedError: On CRITICAL + block_on_critical.
        """
        logger.info(
            "safety_gate_scored",
            severity=severity.name,
            severity_level=int(severity),
            workflow_id=context.workflow_id,
            block_on_critical=self.block_on_critical,
            has_handler=severity in self.handlers,
        )

        handler = self.handlers.get(severity)
        result: Any = input_data

        if handler is not None:
            result = await handler.execute(input_data, context)

        if severity == SeverityLevel.CRITICAL and self.block_on_critical:
            self._record_escalation(context)
            raise SafetyGateEscalatedError(
                severity=severity,
                task_id=context.workflow_id or None,
            )

        return result

    def _record_escalation(self, context: WorkflowContext) -> None:
        """Best-effort L0 gate recording; never raises.

        Args:
            context: Workflow context supplying the task ID.
        """
        if self.service is None:
            return

        try:
            from ttadev.control_plane.models import WorkflowGateDecisionOutcome

            self.service.record_workflow_gate_outcome(
                context.workflow_id,
                step_index=0,
                decision=WorkflowGateDecisionOutcome.ESCALATE_TO_HUMAN,
                summary="SafetyGatePrimitive triggered at CRITICAL severity",
            )
            logger.info(
                "safety_gate_escalation_recorded",
                task_id=context.workflow_id,
            )
        except Exception as exc:
            logger.warning(
                "safety_gate_escalation_record_failed",
                task_id=context.workflow_id,
                error=str(exc),
            )
