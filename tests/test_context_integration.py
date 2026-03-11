"""Tests for context_integration — G4 gap resolution.

Validates that universal-agent-context primitives are properly integrated
into the tta-agent-coordination package.
"""

import asyncio
from typing import Any

import pytest
from tta_agent_coordination.context_integration import (
    AgentCoordinationPrimitive,
    AgentHandoffPrimitive,
    AgentMemoryPrimitive,
    CoordinatedManagerWorkflow,
)

from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _StubManager(WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """Minimal manager stub for testing."""

    def __init__(self, name: str, result_value: str = "ok") -> None:
        self._name = name
        self._result_value = result_value

    async def execute(self, input_data: dict[str, Any], context: WorkflowContext) -> dict[str, Any]:
        await asyncio.sleep(0.01)
        return {"manager": self._name, "status": self._result_value}


class _FailingManager(WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """Manager that always raises."""

    async def execute(self, input_data: dict[str, Any], context: WorkflowContext) -> dict[str, Any]:
        raise RuntimeError("boom")


# ---------------------------------------------------------------------------
# Re-export smoke tests
# ---------------------------------------------------------------------------


def test_agent_context_primitives_importable():
    """L1 primitives are importable via context_integration."""
    assert AgentCoordinationPrimitive is not None
    assert AgentHandoffPrimitive is not None
    assert AgentMemoryPrimitive is not None


# ---------------------------------------------------------------------------
# CoordinatedManagerWorkflow
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_coordinated_workflow_aggregate():
    """Aggregate strategy returns results from all managers."""
    workflow = CoordinatedManagerWorkflow(
        managers={
            "alpha": _StubManager("alpha"),
            "beta": _StubManager("beta", result_value="done"),
        },
        coordination_strategy="aggregate",
    )
    ctx = WorkflowContext(workflow_id="test-g4")
    result = await workflow.execute({"task": "build"}, ctx)

    assert "agent_results" in result
    assert "coordination_metadata" in result
    assert result["coordination_metadata"]["total_agents"] == 2
    assert result["coordination_metadata"]["successful_agents"] == 2
    assert result["coordination_metadata"]["failed_agents"] == 0


@pytest.mark.asyncio
async def test_coordinated_workflow_stores_memory():
    """When store_results_in_memory=True, result is persisted via AgentMemoryPrimitive."""
    workflow = CoordinatedManagerWorkflow(
        managers={"m1": _StubManager("m1")},
        store_results_in_memory=True,
    )
    ctx = WorkflowContext(workflow_id="test-memory")
    result = await workflow.execute({"task": "check"}, ctx)

    # Memory should have been stored in context metadata
    agent_memory = ctx.metadata.get("agent_memory", {})
    stored = agent_memory.get("workflow_memories", {}).get("coordination_result")
    assert stored is not None
    assert stored["value"] == result


@pytest.mark.asyncio
async def test_coordinated_workflow_partial_failure():
    """Failing managers are tracked when require_all_success is False."""
    workflow = CoordinatedManagerWorkflow(
        managers={
            "good": _StubManager("good"),
            "bad": _FailingManager(),
        },
        require_all_success=False,
    )
    ctx = WorkflowContext(workflow_id="test-partial")
    result = await workflow.execute({}, ctx)

    assert "bad" in result["failed_agents"]
    assert result["coordination_metadata"]["failed_agents"] == 1
    assert result["coordination_metadata"]["successful_agents"] == 1


@pytest.mark.asyncio
async def test_coordinated_workflow_require_all_raises():
    """require_all_success=True raises when any manager fails."""
    workflow = CoordinatedManagerWorkflow(
        managers={
            "good": _StubManager("good"),
            "bad": _FailingManager(),
        },
        require_all_success=True,
    )
    ctx = WorkflowContext(workflow_id="test-strict")
    with pytest.raises(RuntimeError, match="Agent coordination failed"):
        await workflow.execute({}, ctx)


@pytest.mark.asyncio
async def test_coordinated_workflow_first_strategy():
    """First strategy returns the first successful result."""
    workflow = CoordinatedManagerWorkflow(
        managers={
            "fast": _StubManager("fast"),
            "slow": _StubManager("slow"),
        },
        coordination_strategy="first",
    )
    ctx = WorkflowContext(workflow_id="test-first")
    result = await workflow.execute({}, ctx)

    agg = result["aggregated_result"]
    assert agg["strategy"] == "first"
    assert agg["result"] is not None
