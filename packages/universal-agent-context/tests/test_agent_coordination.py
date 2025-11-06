"""Tests for agent coordination primitives."""

import pytest
from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive

from universal_agent_context.primitives import (
    AgentCoordinationPrimitive,
    AgentHandoffPrimitive,
    AgentMemoryPrimitive,
)


class SimplePrimitive(WorkflowPrimitive[dict, dict]):
    """Simple test primitive that adds a field."""

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add 'processed' field to input."""
        return {**input_data, "processed": True}


class NamedPrimitive(WorkflowPrimitive[dict, dict]):
    """Test primitive that adds its name."""

    def __init__(self, name: str):
        self.name = name

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Add name field to input."""
        return {**input_data, "agent": self.name}


class FailingPrimitive(WorkflowPrimitive[dict, dict]):
    """Test primitive that always fails."""

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Raise an error."""
        raise ValueError("Test error")


# AgentHandoffPrimitive Tests


@pytest.mark.asyncio
async def test_agent_handoff_basic():
    """Test basic agent handoff."""
    handoff = AgentHandoffPrimitive(target_agent="agent2", handoff_strategy="immediate")
    context = WorkflowContext(workflow_id="test")
    context.metadata["current_agent"] = "agent1"

    input_data = {"task": "analyze", "data": "test"}
    result = await handoff.execute(input_data, context)

    assert result["handoff_metadata"]["from_agent"] == "agent1"
    assert result["handoff_metadata"]["to_agent"] == "agent2"
    assert result["handoff_metadata"]["strategy"] == "immediate"
    assert context.metadata["current_agent"] == "agent2"


@pytest.mark.asyncio
async def test_agent_handoff_preserves_context():
    """Test that handoff preserves context when enabled."""
    handoff = AgentHandoffPrimitive(target_agent="agent2", preserve_context=True)
    context = WorkflowContext(workflow_id="test")

    input_data = {"task": "analyze", "data": "test", "extra": "context"}
    result = await handoff.execute(input_data, context)

    assert result["task"] == "analyze"
    assert result["data"] == "test"
    assert result["extra"] == "context"
    assert result["handoff_metadata"]["context_preserved"] is True


@pytest.mark.asyncio
async def test_agent_handoff_trims_context():
    """Test that handoff trims context when preserve_context=False."""
    handoff = AgentHandoffPrimitive(target_agent="agent2", preserve_context=False)
    context = WorkflowContext(workflow_id="test")

    input_data = {
        "task": "analyze",
        "data": "test",
        "extra": "context",
        "essential_context": {"key": "value"},
    }
    result = await handoff.execute(input_data, context)

    assert result["task"] == "analyze"
    assert result["essential_context"] == {"key": "value"}
    assert "extra" not in result
    assert "data" not in result
    assert result["handoff_metadata"]["context_preserved"] is False


@pytest.mark.asyncio
async def test_agent_handoff_tracks_history():
    """Test that handoff tracks agent history."""
    handoff1 = AgentHandoffPrimitive(target_agent="agent2")
    handoff2 = AgentHandoffPrimitive(target_agent="agent3")
    context = WorkflowContext(workflow_id="test")
    context.metadata["current_agent"] = "agent1"

    input_data = {"task": "analyze"}

    # First handoff
    result1 = await handoff1.execute(input_data, context)
    # Second handoff
    await handoff2.execute(result1, context)

    agent_history = context.metadata["agent_history"]
    assert len(agent_history) == 2
    assert agent_history[0]["from_agent"] == "agent1"
    assert agent_history[0]["to_agent"] == "agent2"
    assert agent_history[1]["from_agent"] == "agent2"
    assert agent_history[1]["to_agent"] == "agent3"


@pytest.mark.asyncio
async def test_agent_handoff_invalid_strategy():
    """Test that handoff rejects invalid strategy."""
    handoff = AgentHandoffPrimitive(target_agent="agent2", handoff_strategy="invalid")
    context = WorkflowContext(workflow_id="test")

    with pytest.raises(ValueError, match="Invalid handoff_strategy"):
        await handoff.execute({"task": "test"}, context)


# AgentMemoryPrimitive Tests


@pytest.mark.asyncio
async def test_agent_memory_store():
    """Test storing a memory entry."""
    memory = AgentMemoryPrimitive(operation="store", memory_key="test_key", memory_scope="workflow")
    context = WorkflowContext(workflow_id="test")
    context.metadata["current_agent"] = "agent1"

    input_data = {"memory_value": {"data": "test"}}
    result = await memory.execute(input_data, context)

    assert result["memory_stored"] is True
    assert result["memory_key"] == "test_key"
    assert result["memory_scope"] == "workflow"


@pytest.mark.asyncio
async def test_agent_memory_retrieve():
    """Test retrieving a stored memory entry."""
    # Store first
    store = AgentMemoryPrimitive(operation="store", memory_key="test_key")
    context = WorkflowContext(workflow_id="test")
    context.metadata["current_agent"] = "agent1"

    await store.execute({"memory_value": {"data": "test"}}, context)

    # Retrieve
    retrieve = AgentMemoryPrimitive(operation="retrieve", memory_key="test_key")
    result = await retrieve.execute({}, context)

    assert result["memory_found"] is True
    assert result["memory_value"] == {"data": "test"}
    assert result["memory_entry"]["agent"] == "agent1"


@pytest.mark.asyncio
async def test_agent_memory_retrieve_not_found():
    """Test retrieving non-existent memory."""
    retrieve = AgentMemoryPrimitive(operation="retrieve", memory_key="nonexistent")
    context = WorkflowContext(workflow_id="test")

    result = await retrieve.execute({}, context)

    assert result["memory_found"] is False
    assert result["memory_value"] is None


@pytest.mark.asyncio
async def test_agent_memory_query():
    """Test querying memories by tags."""
    context = WorkflowContext(workflow_id="test")
    context.metadata["current_agent"] = "agent1"

    # Store multiple memories with tags
    store1 = AgentMemoryPrimitive(operation="store", memory_key="memory1")
    await store1.execute(
        {"memory_value": "data1", "tags": {"type": "test", "priority": "high"}},
        context,
    )

    store2 = AgentMemoryPrimitive(operation="store", memory_key="memory2")
    await store2.execute(
        {"memory_value": "data2", "tags": {"type": "test", "priority": "low"}},
        context,
    )

    # Query by tags
    query = AgentMemoryPrimitive(operation="query")
    result = await query.execute({"query_tags": {"type": "test", "priority": "high"}}, context)

    assert result["result_count"] == 1
    assert result["query_results"][0]["value"] == "data1"


@pytest.mark.asyncio
async def test_agent_memory_list():
    """Test listing all memories."""
    context = WorkflowContext(workflow_id="test")
    context.metadata["current_agent"] = "agent1"

    # Store multiple memories
    store1 = AgentMemoryPrimitive(operation="store", memory_key="memory1")
    await store1.execute({"memory_value": "data1"}, context)

    store2 = AgentMemoryPrimitive(operation="store", memory_key="memory2")
    await store2.execute({"memory_value": "data2"}, context)

    # List all
    list_mem = AgentMemoryPrimitive(operation="list")
    result = await list_mem.execute({}, context)

    assert result["memory_count"] == 2
    assert len(result["memories"]) == 2


@pytest.mark.asyncio
async def test_agent_memory_invalid_operation():
    """Test that invalid operation raises error."""
    memory = AgentMemoryPrimitive(operation="invalid")
    context = WorkflowContext(workflow_id="test")

    with pytest.raises(ValueError, match="Invalid operation"):
        await memory.execute({}, context)


# AgentCoordinationPrimitive Tests


@pytest.mark.asyncio
async def test_agent_coordination_aggregate():
    """Test coordinating multiple agents with aggregate strategy."""
    agents = {
        "agent1": NamedPrimitive("agent1"),
        "agent2": NamedPrimitive("agent2"),
        "agent3": NamedPrimitive("agent3"),
    }

    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents,  # type: ignore[arg-type]  # Test primitive variance
        coordination_strategy="aggregate",
    )
    context = WorkflowContext(workflow_id="test")

    input_data = {"task": "analyze"}
    result = await coordinator.execute(input_data, context)

    assert result["coordination_metadata"]["total_agents"] == 3
    assert result["coordination_metadata"]["successful_agents"] == 3
    assert result["coordination_metadata"]["failed_agents"] == 0
    assert len(result["agent_results"]) == 3
    assert result["aggregated_result"]["strategy"] == "aggregate"


@pytest.mark.asyncio
async def test_agent_coordination_first():
    """Test coordinating with first-success strategy."""
    agents = {
        "agent1": NamedPrimitive("agent1"),
        "agent2": NamedPrimitive("agent2"),
    }

    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents,  # type: ignore[arg-type]  # Test primitive variance
        coordination_strategy="first",
    )
    context = WorkflowContext(workflow_id="test")

    input_data = {"task": "analyze"}
    result = await coordinator.execute(input_data, context)

    assert result["aggregated_result"]["strategy"] == "first"
    assert result["aggregated_result"]["agent"] in ["agent1", "agent2"]


@pytest.mark.asyncio
async def test_agent_coordination_with_failures():
    """Test coordination with some failing agents."""
    agents = {
        "agent1": NamedPrimitive("agent1"),
        "agent2": FailingPrimitive(),
        "agent3": NamedPrimitive("agent3"),
    }

    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents,
        coordination_strategy="aggregate",
        require_all_success=False,
    )
    context = WorkflowContext(workflow_id="test")

    input_data = {"task": "analyze"}
    result = await coordinator.execute(input_data, context)

    assert result["coordination_metadata"]["successful_agents"] == 2
    assert result["coordination_metadata"]["failed_agents"] == 1
    assert "agent2" in result["failed_agents"]


@pytest.mark.asyncio
async def test_agent_coordination_require_all_success():
    """Test that coordination fails when require_all_success=True."""
    agents = {
        "agent1": NamedPrimitive("agent1"),
        "agent2": FailingPrimitive(),
    }

    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents,
        coordination_strategy="aggregate",
        require_all_success=True,
    )
    context = WorkflowContext(workflow_id="test")

    with pytest.raises(RuntimeError, match="Agent coordination failed"):
        await coordinator.execute({"task": "test"}, context)


@pytest.mark.asyncio
async def test_agent_coordination_timeout():
    """Test coordination with timeout."""
    import asyncio

    class SlowPrimitive(WorkflowPrimitive[dict, dict]):
        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            await asyncio.sleep(2.0)
            return {"slow": True}

    agents = {
        "slow_agent": SlowPrimitive(),
    }

    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents,  # type: ignore[arg-type]  # Test primitive variance
        coordination_strategy="aggregate",
        timeout_seconds=0.1,
        require_all_success=False,
    )
    context = WorkflowContext(workflow_id="test")

    result = await coordinator.execute({"task": "test"}, context)

    assert "slow_agent" in result["failed_agents"]
    assert "timeout" in str(result["agent_results"]["slow_agent"]["error"])


@pytest.mark.asyncio
async def test_agent_coordination_invalid_strategy():
    """Test that invalid strategy raises error."""
    agents = {"agent1": NamedPrimitive("agent1")}

    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents,  # type: ignore[arg-type]  # Test primitive variance
        coordination_strategy="invalid",
    )
    context = WorkflowContext(workflow_id="test")

    with pytest.raises(ValueError, match="Invalid coordination_strategy"):
        await coordinator.execute({"task": "test"}, context)


# Integration Tests


@pytest.mark.asyncio
async def test_agent_handoff_with_memory():
    """Test combining handoff and memory primitives."""
    context = WorkflowContext(workflow_id="test")
    context.metadata["current_agent"] = "agent1"

    # Agent 1 stores decision
    store = AgentMemoryPrimitive(operation="store", memory_key="decision")
    await store.execute({"memory_value": {"choice": "option_a"}, "task": "analyze"}, context)

    # Handoff to agent 2
    handoff = AgentHandoffPrimitive(target_agent="agent2")
    await handoff.execute({"task": "implement"}, context)

    # Agent 2 retrieves decision
    retrieve = AgentMemoryPrimitive(operation="retrieve", memory_key="decision")
    result = await retrieve.execute({}, context)

    assert result["memory_found"] is True
    assert result["memory_value"]["choice"] == "option_a"
    assert context.metadata["current_agent"] == "agent2"


@pytest.mark.asyncio
async def test_multi_agent_workflow():
    """Test complete multi-agent workflow."""
    context = WorkflowContext(workflow_id="test")

    # Initial agent
    context.metadata["current_agent"] = "coordinator"

    # Coordinator stores plan
    store_plan = AgentMemoryPrimitive(operation="store", memory_key="plan")
    await store_plan.execute({"memory_value": {"tasks": ["analyze", "implement", "test"]}}, context)

    # Coordinate parallel agents
    agents = {
        "analyzer": NamedPrimitive("analyzer"),
        "implementer": NamedPrimitive("implementer"),
        "tester": NamedPrimitive("tester"),
    }

    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents,  # type: ignore[arg-type]  # Test primitive variance
        coordination_strategy="aggregate",
    )
    coord_result = await coordinator.execute({"task": "build_feature"}, context)

    assert coord_result["coordination_metadata"]["successful_agents"] == 3

    # Final agent retrieves plan
    handoff = AgentHandoffPrimitive(target_agent="finalizer")
    await handoff.execute({"results": coord_result}, context)

    retrieve_plan = AgentMemoryPrimitive(operation="retrieve", memory_key="plan")
    plan_result = await retrieve_plan.execute({}, context)

    assert plan_result["memory_found"] is True
    assert context.metadata["current_agent"] == "finalizer"
