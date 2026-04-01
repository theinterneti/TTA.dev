"""Safety gate primitive for severity-based routing and human escalation.

Generalizes the TTA 5-level crisis detection pattern into a reusable composable
primitive that any AI application with safety requirements can use.

Example:
    ```python
    from ttadev.primitives.safety import SafetyGatePrimitive, SeverityLevel, ThreatLevel

    safety = SafetyGatePrimitive(
        scorer=my_crisis_detector,
        handlers={
            SeverityLevel.LOW: warning_handler,
            SeverityLevel.CRITICAL: escalation_handler,
        },
        block_on_critical=True,
        threshold=ThreatLevel.MODERATE,
    )
    workflow = safety >> narrative_generator
    ```
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from enum import Enum, IntEnum
from typing import Any

try:
    from opentelemetry import trace
except ImportError:
    trace = None  # type: ignore[assignment]

from ..core.base import WorkflowContext, WorkflowPrimitive
from ..observability.instrumented_primitive import TRACING_AVAILABLE
from ..observability.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Keyword set used by the default _check() implementation.
# Override detect_level() for domain-specific detection logic.
# ---------------------------------------------------------------------------
_UNSAFE_KEYWORDS: frozenset[str] = frozenset(
    {
        "harm",
        "kill",
        "suicide",
        "hurt",
        "die",
        "crisis",
        "self-harm",
        "end it",
        "no reason to live",
    }
)


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


class ThreatLevel(int, Enum):
    """Multi-level threat scale for narrative safety detection (MINIMAL → IMMINENT).

    Maps to the TTA therapeutic safety ladder:

    * ``MINIMAL``  — Normal narrative flow; no intervention needed.
    * ``MILD``     — Therapeutic pacing / grounding language warranted.
    * ``MODERATE`` — In-world mentor guidance recommended.
    * ``SEVERE``   — Gentle fourth-wall break; redirect player.
    * ``IMMINENT`` — Exit game immediately; escalate to human support.
    """

    MINIMAL = 1
    MILD = 2
    MODERATE = 3
    SEVERE = 4
    IMMINENT = 5


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


class SafetyViolationError(Exception):
    """Raised when ``detect_level`` returns a threat at or above ``threshold``.

    This is the multi-level threat detection counterpart to
    ``SafetyGateEscalatedError``.  It signals that text content has crossed
    the configured ``ThreatLevel`` threshold.

    Attributes:
        threat_level: The detected ``ThreatLevel``.
        threshold: The configured threshold that was breached.
        task_id: The L0 workflow task ID (if present in context).
    """

    def __init__(
        self,
        *,
        threat_level: ThreatLevel,
        threshold: ThreatLevel,
        task_id: str | None = None,
    ) -> None:
        self.threat_level = threat_level
        self.threshold = threshold
        self.task_id = task_id
        super().__init__(
            f"Safety violation: threat_level={threat_level.name} >= threshold={threshold.name}"
            + (f", task_id={task_id}" if task_id else "")
        )


class SafetyGatePrimitive(WorkflowPrimitive[Any, Any]):
    """Score input severity, route to handlers, and optionally block on CRITICAL.

    This primitive wraps any workflow input with a two-track safety assessment:

    **Track 1 — SeverityLevel (async scorer)**
    The scorer assigns a ``SeverityLevel``; the primitive then calls the
    registered handler for that level (if any) and blocks with
    ``SafetyGateEscalatedError`` when severity is ``CRITICAL`` and
    ``block_on_critical=True``.

    **Track 2 — ThreatLevel (sync detect_level)**
    ``detect_level(text)`` returns a ``ThreatLevel``.  When the result is
    ``>= threshold`` a ``SafetyViolationError`` is raised.  Override
    ``detect_level`` for domain-specific multi-level detection.  When the
    level is ``IMMINENT``, a best-effort L0 control-plane escalation is
    also recorded.

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
        threshold: Minimum ``ThreatLevel`` that triggers ``SafetyViolationError``.
            Defaults to ``ThreatLevel.MODERATE`` so MINIMAL/MILD inputs pass
            through undisturbed.
    """

    def __init__(
        self,
        scorer: Callable[[Any, WorkflowContext], Awaitable[SeverityLevel]],
        handlers: dict[SeverityLevel, WorkflowPrimitive] | None = None,
        block_on_critical: bool = True,
        service: Any | None = None,
        threshold: ThreatLevel = ThreatLevel.MODERATE,
    ) -> None:
        self.scorer = scorer
        self.handlers: dict[SeverityLevel, WorkflowPrimitive] = handlers or {}
        self.block_on_critical = block_on_critical
        self.service = service
        self.threshold = threshold

    # ------------------------------------------------------------------
    # Public threat-detection API (Track 2)
    # ------------------------------------------------------------------

    def _check(self, text: str) -> bool:
        """Return ``True`` if *text* contains an unsafe keyword.

        This is the default heuristic used by :meth:`detect_level`.  Override
        :meth:`detect_level` directly for richer, model-based detection.

        Args:
            text: The raw input string to inspect.

        Returns:
            ``True`` when any keyword in ``_UNSAFE_KEYWORDS`` appears in the
            lower-cased text.
        """
        text_lower = text.lower()
        return any(kw in text_lower for kw in _UNSAFE_KEYWORDS)

    def detect_level(self, text: str) -> ThreatLevel:
        """Detect threat level from *text*.  Override for custom detection.

        The default implementation is intentionally coarse — it maps any
        keyword match to ``IMMINENT`` and everything else to ``MINIMAL``.
        Subclass and override this method to implement gradient scoring
        (e.g. running an ML model and mapping probabilities to
        ``MILD``/``MODERATE``/``SEVERE``/``IMMINENT``).

        Args:
            text: The raw input string to evaluate.

        Returns:
            A :class:`ThreatLevel` value.
        """
        is_unsafe = self._check(text)
        return ThreatLevel.IMMINENT if is_unsafe else ThreatLevel.MINIMAL

    # ------------------------------------------------------------------
    # WorkflowPrimitive interface
    # ------------------------------------------------------------------

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """Score, route, and optionally block on CRITICAL severity or threat level.

        Runs both safety tracks:

        1. **SeverityLevel track** — awaits ``scorer``, calls handlers, blocks
           on CRITICAL (existing behaviour, fully preserved).
        2. **ThreatLevel track** — calls ``detect_level`` on the string
           representation of *input_data*; raises ``SafetyViolationError``
           when ``>= threshold``; fires control-plane escalation on IMMINENT.

        The ThreatLevel check runs *after* the SeverityLevel track so that
        CRITICAL blocking still takes precedence.

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
            SafetyViolationError: When ``detect_level`` returns a
                ``ThreatLevel >= threshold``.
        """
        severity: SeverityLevel = await self.scorer(input_data, context)

        tracer = None
        if TRACING_AVAILABLE and trace is not None:
            tracer = trace.get_tracer(__name__)

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

    # ------------------------------------------------------------------
    # Internal routing helpers
    # ------------------------------------------------------------------

    async def _route(
        self,
        severity: SeverityLevel,
        input_data: Any,
        context: WorkflowContext,
    ) -> Any:
        """Apply handler routing and blocking logic for *severity*.

        After SeverityLevel processing, runs the ThreatLevel track.

        Args:
            severity: Assessed severity level.
            input_data: Original workflow payload.
            context: Workflow context.

        Returns:
            Handler output or original input_data.

        Raises:
            SafetyGateEscalatedError: On CRITICAL + block_on_critical.
            SafetyViolationError: On ThreatLevel >= threshold.
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

        # ------------------------------------------------------------------
        # Track 2: multi-level threat detection
        # ------------------------------------------------------------------
        text = input_data if isinstance(input_data, str) else str(input_data)
        threat = self.detect_level(text)

        logger.info(
            "safety_gate_threat_detected",
            threat_level=threat.name,
            threat_value=int(threat),
            threshold=self.threshold.name,
            threshold_value=int(self.threshold),
            workflow_id=context.workflow_id,
        )

        if threat >= self.threshold:
            if threat == ThreatLevel.IMMINENT:
                self._record_threat_escalation(context, threat)
            raise SafetyViolationError(
                threat_level=threat,
                threshold=self.threshold,
                task_id=context.workflow_id or None,
            )

        return result

    def _record_escalation(self, context: WorkflowContext) -> None:
        """Best-effort L0 gate recording for CRITICAL SeverityLevel; never raises.

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

    def _record_threat_escalation(
        self,
        context: WorkflowContext,
        threat: ThreatLevel,
    ) -> None:
        """Best-effort L0 gate recording for IMMINENT ThreatLevel; never raises.

        Attempts to import ``ttadev.control_plane`` and record an
        ``ESCALATE_TO_HUMAN`` outcome.  Logs a warning when the control plane
        is unavailable rather than propagating the error.

        Args:
            context: Workflow context supplying the task ID.
            threat: The ``ThreatLevel`` that triggered escalation.
        """
        if self.service is None:
            logger.warning(
                "safety_gate_imminent_no_control_plane",
                task_id=context.workflow_id,
                threat_level=threat.name,
                message="IMMINENT threat detected but no control_plane service configured",
            )
            return

        try:
            from ttadev.control_plane.models import WorkflowGateDecisionOutcome

            self.service.record_workflow_gate_outcome(
                context.workflow_id,
                step_index=0,
                decision=WorkflowGateDecisionOutcome.ESCALATE_TO_HUMAN,
                summary=f"SafetyGatePrimitive triggered at ThreatLevel.IMMINENT ({threat.name})",
            )
            logger.info(
                "safety_gate_threat_escalation_recorded",
                task_id=context.workflow_id,
                threat_level=threat.name,
            )
        except ImportError:
            logger.warning(
                "safety_gate_control_plane_unavailable",
                task_id=context.workflow_id,
                threat_level=threat.name,
                message="ttadev.control_plane not available; IMMINENT escalation not recorded",
            )
        except Exception as exc:
            logger.warning(
                "safety_gate_threat_escalation_record_failed",
                task_id=context.workflow_id,
                threat_level=threat.name,
                error=str(exc),
            )
