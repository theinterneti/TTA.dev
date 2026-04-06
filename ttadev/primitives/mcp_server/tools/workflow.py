"""TTA.dev MCP server: workflow progression tools."""

from typing import Any

from ttadev.control_plane import ControlPlaneError
from ttadev.control_plane.models import WorkflowGateDecisionOutcome

from ._helpers import (
    _control_plane_error_payload,
    _create_control_plane_service,
    _emit_mcp_span,
    _serialize_lease,
    _serialize_run,
    _serialize_task,
    logger,
)


def register_workflow_tools(mcp: Any, _mut: Any, _idem: Any) -> None:
    """Register workflow progression tools with the MCP server."""

    @mcp.tool(annotations=_mut)
    async def control_start_workflow(
        workflow_name: str,
        workflow_goal: str,
        step_agents: list[str],
        project_name: str | None = None,
        policy_gates: list[dict[str, str]] | None = None,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Create and claim a tracked multi-agent workflow task.

        ``step_agents`` is an ordered list of agent names — one entry per
        workflow step.  ``policy_gates`` is an optional list of extra POLICY
        gate dicts, each with keys ``id``, ``label``, and ``policy``
        (e.g. ``"auto:confidence>=0.85"``).

        Returns the same ``{task, run, lease}`` envelope as
        ``control_claim_task``.
        """
        logger.info(
            "mcp_tool_called",
            tool="control_start_workflow",
            data_dir=data_dir,
            workflow_name=workflow_name,
            step_agents=step_agents,
        )
        try:
            extra_gates: list[dict[str, Any]] | None = None
            if policy_gates:
                extra_gates = [
                    {
                        "id": g["id"],
                        "gate_type": "policy",
                        "label": g["label"],
                        "required": True,
                        "policy_name": g["policy"],
                    }
                    for g in policy_gates
                ]
            with _emit_mcp_span(
                "tta.l0.mcp.workflow.start",
                {"workflow.name": workflow_name, "data_dir": data_dir},
            ):
                service = _create_control_plane_service(data_dir)
                claim = service.start_tracked_workflow(
                    workflow_name=workflow_name,
                    workflow_goal=workflow_goal,
                    step_agents=step_agents,
                    project_name=project_name,
                    extra_gates=extra_gates,
                )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {
            "task": _serialize_task(claim.task),
            "run": _serialize_run(claim.run),
            "lease": _serialize_lease(claim.lease),
        }

    @mcp.tool(annotations=_idem)
    async def control_mark_workflow_step_running(
        task_id: str,
        step_index: int,
        trace_id: str | None = None,
        span_id: str | None = None,
        hindsight_bank_id: str | None = None,
        hindsight_document_id: str | None = None,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Transition a tracked workflow step to RUNNING.

        Pass ``trace_id`` and ``span_id`` to stamp the current OTel span
        context onto the step record.  Safe to call again on retry — the
        trace context is replaced each time.

        Pass ``hindsight_bank_id`` and ``hindsight_document_id`` to correlate
        this step with a Hindsight memory retain operation, so the step record
        carries a direct link to the retained memory artifact.
        """
        logger.info(
            "mcp_tool_called",
            tool="control_mark_workflow_step_running",
            data_dir=data_dir,
            task_id=task_id,
            step_index=step_index,
        )
        try:
            with _emit_mcp_span(
                "tta.l0.mcp.step.running",
                {"task.id": task_id, "step.index": str(step_index), "data_dir": data_dir},
            ):
                service = _create_control_plane_service(data_dir)
                task = service.mark_workflow_step_running(
                    task_id,
                    step_index=step_index,
                    trace_id=trace_id,
                    span_id=span_id,
                    hindsight_bank_id=hindsight_bank_id,
                    hindsight_document_id=hindsight_document_id,
                )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    @mcp.tool(annotations=_mut)
    async def control_record_workflow_step_result(
        task_id: str,
        step_index: int,
        result_summary: str,
        confidence: float,
        hindsight_bank_id: str | None = None,
        hindsight_document_id: str | None = None,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Record the result and confidence score for a completed workflow step.

        ``confidence`` must be in the range 0.0–1.0.  Recording the result
        automatically evaluates any pending POLICY gates attached to the task.

        Pass ``hindsight_bank_id`` and ``hindsight_document_id`` to attach a
        link to the Hindsight memory retain artifact produced by this step.
        """
        logger.info(
            "mcp_tool_called",
            tool="control_record_workflow_step_result",
            data_dir=data_dir,
            task_id=task_id,
            step_index=step_index,
            confidence=confidence,
        )
        try:
            with _emit_mcp_span(
                "tta.l0.mcp.step.completed",
                {
                    "task.id": task_id,
                    "step.index": str(step_index),
                    "step.confidence": str(confidence),
                    "data_dir": data_dir,
                },
            ):
                service = _create_control_plane_service(data_dir)
                task = service.record_workflow_step_result(
                    task_id,
                    step_index=step_index,
                    result_summary=result_summary,
                    confidence=confidence,
                    hindsight_bank_id=hindsight_bank_id,
                    hindsight_document_id=hindsight_document_id,
                )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    @mcp.tool(annotations=_mut)
    async def control_record_workflow_gate_outcome(
        task_id: str,
        step_index: int,
        decision: str,
        summary: str = "",
        policy_name: str | None = None,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Record the approval-gate decision for a tracked workflow step.

        ``decision`` must be one of: ``continue``, ``skip``, ``edit``, ``quit``.
        Set ``policy_name`` when the decision was made automatically by a policy
        rule rather than by a human reviewer.
        """
        logger.info(
            "mcp_tool_called",
            tool="control_record_workflow_gate_outcome",
            data_dir=data_dir,
            task_id=task_id,
            step_index=step_index,
            decision=decision,
        )
        try:
            outcome = WorkflowGateDecisionOutcome(decision)
            with _emit_mcp_span(
                "tta.l0.mcp.gate.outcome",
                {
                    "task.id": task_id,
                    "step.index": str(step_index),
                    "gate.decision": decision,
                    "data_dir": data_dir,
                },
            ):
                service = _create_control_plane_service(data_dir)
                task = service.record_workflow_gate_outcome(
                    task_id,
                    step_index=step_index,
                    decision=outcome,
                    summary=summary,
                    policy_name=policy_name,
                )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    @mcp.tool(annotations=_mut)
    async def control_mark_workflow_step_failed(
        task_id: str,
        step_index: int,
        error_summary: str,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Mark a tracked workflow step as FAILED with an error summary."""
        logger.info(
            "mcp_tool_called",
            tool="control_mark_workflow_step_failed",
            data_dir=data_dir,
            task_id=task_id,
            step_index=step_index,
        )
        try:
            with _emit_mcp_span(
                "tta.l0.mcp.step.failed",
                {
                    "task.id": task_id,
                    "step.index": str(step_index),
                    "error.summary": error_summary,
                    "data_dir": data_dir,
                },
            ) as _span:
                if _span is not None:
                    try:
                        from opentelemetry.trace import Status, StatusCode

                        _span.set_status(Status(StatusCode.ERROR, error_summary))
                    except Exception:
                        pass
                service = _create_control_plane_service(data_dir)
                task = service.mark_workflow_step_failed(
                    task_id,
                    step_index=step_index,
                    error_summary=error_summary,
                )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}
