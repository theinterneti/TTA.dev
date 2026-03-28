"""Integration test: L0 multi-agent workflow end-to-end proof.

Simulates two coding agents (backend-engineer + reviewer) driving a tracked
workflow through the full MCP tool lifecycle.

Agent 1 (backend-engineer) starts the workflow (which auto-claims the task)
and owns step 0.  After completing its run, Agent 2 (reviewer) claims the
task for step 1.  OTel trace attribution is stamped via
``control_mark_workflow_step_running``.

Two scenarios:
  - Happy path: confidence ≥ 0.8 → policy gate APPROVED → both steps COMPLETED
  - Low confidence: gate stays PENDING → human calls QUIT → workflow aborted
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from ttadev.control_plane import ControlPlaneService
from ttadev.control_plane.models import (
    GateStatus,
    WorkflowGateDecisionOutcome,
    WorkflowStepStatus,
    WorkflowTrackingStatus,
)
from ttadev.observability import agent_identity
from ttadev.primitives.mcp_server.server import create_server

# OTel trace constants for attribution assertions (not real secrets)
_TRACE_AGENT1 = "aabbccddeeff00112233445566778899"  # pragma: allowlist secret
_SPAN_AGENT1 = "1122334455667788"  # pragma: allowlist secret
_TRACE_AGENT2 = "99887766554433221100ffeeddccbbaa"  # pragma: allowlist secret
_SPAN_AGENT2 = "8877665544332211"  # pragma: allowlist secret

_POLICY_GATE = {
    "id": "quality",
    "label": "Quality gate",
    "policy": "auto:confidence>=0.8",
}


async def _call_tool(mcp: Any, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    result = mcp.call_tool(name, arguments)
    if asyncio.iscoroutine(result):
        result = await result
    assert isinstance(result, tuple)
    _, payload = result
    assert isinstance(payload, dict)
    return payload


def _pin_agent(monkeypatch: pytest.MonkeyPatch, agent_id: str) -> None:
    monkeypatch.setattr(agent_identity, "_AGENT_ID", agent_id)
    monkeypatch.setenv("TTA_AGENT_TOOL", "claude-code")


# ── Happy path ──────────────────────────────────────────────────────────────


@pytest.mark.workflow_proof
async def test_happy_path_two_step_workflow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Full two-step workflow: both steps complete with OTel trace attribution.

    Agent 1 starts the workflow (which auto-claims the task for step 0).
    After completing step 0, Agent 2 claims the task for step 1.
    Trace context is stamped via ``control_mark_workflow_step_running``.
    """
    mcp = create_server()
    data_dir = str(tmp_path)

    # ── Step A: agent 1 starts the workflow (auto-claims for itself) ────────
    _pin_agent(monkeypatch, "backend-engineer")
    start = await _call_tool(
        mcp,
        "control_start_workflow",
        {
            "workflow_name": "feature-x",
            "workflow_goal": "implement and review feature X",
            "step_agents": ["backend-engineer", "reviewer"],
            "policy_gates": [_POLICY_GATE],
            "data_dir": data_dir,
        },
    )
    task_id = start["task"]["id"]
    run_id1 = start["run"]["id"]
    assert start["task"]["workflow"]["status"] == WorkflowTrackingStatus.RUNNING
    assert start["task"]["workflow"]["total_steps"] == 2

    # ── Step B: agent 1 marks step 0 running with OTel trace context ────────
    await _call_tool(
        mcp,
        "control_mark_workflow_step_running",
        {
            "task_id": task_id,
            "step_index": 0,
            "trace_id": _TRACE_AGENT1,
            "span_id": _SPAN_AGENT1,
            "data_dir": data_dir,
        },
    )

    # Verify step 0 is RUNNING with trace attribution
    service = ControlPlaneService(tmp_path)
    task = service.get_task(task_id)
    assert task.workflow is not None
    step0 = task.workflow.steps[0]
    assert step0.status == WorkflowStepStatus.RUNNING
    assert step0.trace_id == _TRACE_AGENT1

    # ── Step C: agent 1 records result (confidence 0.9 → gate APPROVED) ────
    await _call_tool(
        mcp,
        "control_record_workflow_step_result",
        {
            "task_id": task_id,
            "step_index": 0,
            "result_summary": "Implemented feature X with full test coverage.",
            "confidence": 0.9,
            "data_dir": data_dir,
        },
    )

    task = service.get_task(task_id)
    step0 = task.workflow.steps[0]
    assert step0.status == WorkflowStepStatus.COMPLETED

    # Policy gate auto-approved (confidence 0.9 ≥ 0.8)
    policy_gate = next(g for g in task.gates if g.id == "quality")
    assert policy_gate.status == GateStatus.APPROVED

    # ── Step D: agent 1 records gate outcome and completes its run ──────────
    await _call_tool(
        mcp,
        "control_record_workflow_gate_outcome",
        {
            "task_id": task_id,
            "step_index": 0,
            "decision": "continue",
            "summary": "Policy gate approved; handing off to reviewer.",
            "data_dir": data_dir,
        },
    )
    # Release (not complete) after step 0 — task stays claimable for agent 2.
    # The required POLICY gate is now APPROVED, so release_run's gate check passes.
    await _call_tool(
        mcp,
        "control_release_run",
        {"run_id": run_id1, "reason": "step 0 done, handing off", "data_dir": data_dir},
    )

    task = service.get_task(task_id)
    assert task.workflow.steps[0].gate_decision == WorkflowGateDecisionOutcome.CONTINUE

    # ── Step E: agent 2 claims the task for step 1 ──────────────────────────
    _pin_agent(monkeypatch, "reviewer")
    claim2 = await _call_tool(
        mcp,
        "control_claim_task",
        {
            "task_id": task_id,
            "trace_id": _TRACE_AGENT2,
            "span_id": _SPAN_AGENT2,
            "data_dir": data_dir,
        },
    )
    run_id2 = claim2["run"]["id"]
    assert claim2["run"]["trace_id"] == _TRACE_AGENT2

    # ── Step F: agent 2 marks step 1 running and records result ─────────────
    await _call_tool(
        mcp,
        "control_mark_workflow_step_running",
        {
            "task_id": task_id,
            "step_index": 1,
            "trace_id": _TRACE_AGENT2,
            "span_id": _SPAN_AGENT2,
            "data_dir": data_dir,
        },
    )
    await _call_tool(
        mcp,
        "control_record_workflow_step_result",
        {
            "task_id": task_id,
            "step_index": 1,
            "result_summary": "Review passed. No issues found.",
            "confidence": 0.95,
            "data_dir": data_dir,
        },
    )
    await _call_tool(
        mcp,
        "control_complete_run",
        {"run_id": run_id2, "summary": "step 1 done", "data_dir": data_dir},
    )

    # ── Final assertions ─────────────────────────────────────────────────────
    task = service.get_task(task_id)
    assert task.workflow is not None
    step1 = task.workflow.steps[1]
    assert step1.status == WorkflowStepStatus.COMPLETED
    assert step1.trace_id == _TRACE_AGENT2

    completed = sum(1 for s in task.workflow.steps if s.status == WorkflowStepStatus.COMPLETED)
    assert completed == 2

    # complete_run auto-finalizes the workflow when all steps are COMPLETED
    assert task.workflow.status == WorkflowTrackingStatus.COMPLETED


# ── Low-confidence gate → human QUIT ────────────────────────────────────────


@pytest.mark.workflow_proof
async def test_low_confidence_gate_requires_human_decision_to_quit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Confidence below threshold → policy gate stays PENDING → human decides QUIT.

    The policy ``auto:confidence>=0.8`` auto-approves when confidence is high.
    When confidence is low the gate remains PENDING — requiring human review.
    The human (or orchestrator) calls ``control_record_workflow_gate_outcome``
    with ``decision=quit`` to abort the workflow.
    """
    mcp = create_server()
    data_dir = str(tmp_path)

    _pin_agent(monkeypatch, "backend-engineer")
    start = await _call_tool(
        mcp,
        "control_start_workflow",
        {
            "workflow_name": "feature-y",
            "workflow_goal": "implement feature Y",
            "step_agents": ["backend-engineer", "reviewer"],
            "policy_gates": [_POLICY_GATE],
            "data_dir": data_dir,
        },
    )
    task_id = start["task"]["id"]
    run_id = start["run"]["id"]

    await _call_tool(
        mcp,
        "control_mark_workflow_step_running",
        {"task_id": task_id, "step_index": 0, "data_dir": data_dir},
    )

    # Low confidence — below the 0.8 threshold
    await _call_tool(
        mcp,
        "control_record_workflow_step_result",
        {
            "task_id": task_id,
            "step_index": 0,
            "result_summary": "Partial implementation, uncertain about edge cases.",
            "confidence": 0.5,
            "data_dir": data_dir,
        },
    )

    service = ControlPlaneService(tmp_path)
    task = service.get_task(task_id)
    assert task.workflow is not None

    # Policy gate stays PENDING — auto:confidence>=0.8 does not auto-reject
    policy_gate = next(g for g in task.gates if g.id == "quality")
    assert policy_gate.status == GateStatus.PENDING

    # Human/orchestrator reviews and decides to QUIT
    await _call_tool(
        mcp,
        "control_record_workflow_gate_outcome",
        {
            "task_id": task_id,
            "step_index": 0,
            "decision": "quit",
            "summary": "Confidence too low; stopping workflow for rework.",
            "data_dir": data_dir,
        },
    )

    task = service.get_task(task_id)
    assert task.workflow is not None
    step0 = task.workflow.steps[0]
    assert step0.gate_decision == WorkflowGateDecisionOutcome.QUIT
    assert step0.status == WorkflowStepStatus.QUIT

    # Workflow itself is QUIT
    assert task.workflow.status == WorkflowTrackingStatus.QUIT

    # Step 1 remains PENDING (never started)
    assert task.workflow.steps[1].status == WorkflowStepStatus.PENDING

    # Clean up the run (it's still active after QUIT)
    _ = run_id  # run is still held by agent 1; just leave it for this test
