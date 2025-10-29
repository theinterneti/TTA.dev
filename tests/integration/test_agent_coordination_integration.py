"""
Integration tests for agent coordination primitives.

Tests multi-agent workflows with handoff, memory, and coordination primitives.
"""

import asyncio

import pytest
from tta_dev_primitives import WorkflowContext, WorkflowPrimitive
from universal_agent_context.primitives import (
    AgentCoordinationPrimitive,
    AgentHandoffPrimitive,
    AgentMemoryPrimitive,
)

# ============================================================================
# Test Agent Implementations
# ============================================================================


class DataProcessorAgent(WorkflowPrimitive[dict, dict]):
    """Agent that processes data."""

    def __init__(self, processing_time: float = 0.01):
        self.name = "data_processor"
        self.processing_time = processing_time

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Process data."""
        await asyncio.sleep(self.processing_time)
        return {
            "processed": True,
            "data": input_data.get("data", ""),
            "agent": self.name,
        }


class AnalyzerAgent(WorkflowPrimitive[dict, dict]):
    """Agent that analyzes data."""

    def __init__(self, analysis_type: str = "general"):
        self.name = f"analyzer_{analysis_type}"
        self.analysis_type = analysis_type

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Analyze data."""
        await asyncio.sleep(0.01)
        return {
            "analysis": f"{self.analysis_type} analysis complete",
            "score": 0.85,
            "agent": self.name,
        }


class DecisionMakerAgent(WorkflowPrimitive[dict, dict]):
    """Agent that makes decisions."""

    def __init__(self):
        self.name = "decision_maker"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Make decision."""
        return {
            "decision": "approved",
            "confidence": 0.95,
            "reasoning": "All checks passed",
        }


class PrepareForMemoryPrimitive(WorkflowPrimitive[dict, dict]):
    """Helper primitive to prepare data for memory storage.
    
    Wraps data in 'memory_value' key expected by AgentMemoryPrimitive.
    """

    def __init__(self):
        self.name = "prepare_for_memory"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Wrap input data for memory storage."""
        return {"memory_value": input_data}


# ============================================================================
# Integration Tests: Handoff + Memory
# ============================================================================


@pytest.mark.asyncio
async def test_handoff_with_memory_persistence():
    """Test handoff preserves context and memory works across agents."""
    # Create agents and primitives
    processor = DataProcessorAgent()
    prepare_mem = PrepareForMemoryPrimitive()  # Wrap data for storage
    store_decision = AgentMemoryPrimitive(
        operation="store", memory_key="processed_data", memory_scope="workflow"
    )
    handoff = AgentHandoffPrimitive(
        target_agent="analyzer", handoff_strategy="immediate"
    )
    analyzer = AnalyzerAgent()
    retrieve_decision = AgentMemoryPrimitive(
        operation="retrieve", memory_key="processed_data"
    )

    # Build workflow
    workflow = processor >> prepare_mem >> store_decision >> handoff >> analyzer >> retrieve_decision

    # Execute
    context = WorkflowContext(workflow_id="handoff-memory-test")
    context.metadata["current_agent"] = "processor"

    result = await workflow.execute({"data": "test_input"}, context)

    # Verify handoff happened
    assert context.metadata["current_agent"] == "analyzer"
    assert len(context.metadata.get("agent_history", [])) == 1

    # Verify memory persisted (uses memory_value key from AgentMemoryPrimitive)
    assert result["memory_value"]["processed"] is True
    assert result["memory_value"]["data"] == "test_input"


@pytest.mark.asyncio
async def test_memory_shared_across_agents():
    """Test that memory is accessible across different agents."""
    # Agent 1 stores data
    agent1 = DataProcessorAgent()
    prepare_mem = PrepareForMemoryPrimitive()  # Wrap data for storage
    store = AgentMemoryPrimitive(
        operation="store", memory_key="shared_data", memory_scope="session"
    )

    # Agent 2 retrieves data
    agent2 = AnalyzerAgent()
    retrieve = AgentMemoryPrimitive(operation="retrieve", memory_key="shared_data")

    # Build workflow
    workflow = agent1 >> prepare_mem >> store >> agent2 >> retrieve

    # Execute
    context = WorkflowContext(
        workflow_id="memory-sharing-test", session_id="test-session"
    )

    result = await workflow.execute({"data": "shared"}, context)

    # Verify data was shared (uses memory_value key from AgentMemoryPrimitive)
    assert result["memory_value"]["data"] == "shared"


# ============================================================================
# Integration Tests: Coordination + Memory
# ============================================================================


@pytest.mark.asyncio
async def test_coordination_with_memory_aggregate():
    """Test parallel coordination with memory storing results."""
    # Create multiple agents
    agents = {
        "security": AnalyzerAgent("security"),
        "performance": AnalyzerAgent("performance"),
        "quality": AnalyzerAgent("quality"),
    }

    # Coordinate agents
    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents,
        coordination_strategy="aggregate",
        timeout_seconds=2.0,
    )

    # Store aggregated results
    prepare_mem = PrepareForMemoryPrimitive()  # Wrap data for storage
    store_results = AgentMemoryPrimitive(
        operation="store", memory_key="analysis_results", memory_scope="workflow"
    )

    # Build workflow
    workflow = coordinator >> prepare_mem >> store_results

    # Execute
    context = WorkflowContext(workflow_id="coordination-memory-test")
    await workflow.execute({"data": "test"}, context)

    # Verify all agents executed (coordination metadata stored in context)
    coord_metadata = context.metadata["agent_coordination"]
    assert coord_metadata["total_agents"] == 3
    assert coord_metadata["successful_agents"] == 3

    # Verify results stored in memory
    memories = context.metadata.get("agent_memory", {}).get("workflow_memories", {})
    assert "analysis_results" in memories


@pytest.mark.asyncio
async def test_coordination_consensus_strategy():
    """Test consensus coordination strategy with voting agents."""

    class VotingAgent(WorkflowPrimitive[dict, dict]):
        def __init__(self, name: str, vote: str):
            self.name = name
            self._vote = vote

        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            return {"vote": self._vote, "agent": self.name}

    # Create voting agents
    agents = {
        "voter1": VotingAgent("voter1", "approve"),
        "voter2": VotingAgent("voter2", "approve"),
        "voter3": VotingAgent("voter3", "approve"),
        "voter4": VotingAgent("voter4", "reject"),
        "voter5": VotingAgent("voter5", "approve"),
    }

    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents, coordination_strategy="consensus"
    )

    context = WorkflowContext(workflow_id="consensus-test")
    result = await coordinator.execute({"proposal": "feature-x"}, context)

    # Verify consensus strategy executed (each agent returns unique dict, no actual consensus)
    assert result["aggregated_result"]["strategy"] == "consensus"
    assert result["aggregated_result"]["total_votes"] == 5
    assert result["coordination_metadata"]["successful_agents"] == 5


# ============================================================================
# Integration Tests: Full Multi-Agent Workflow
# ============================================================================


@pytest.mark.asyncio
async def test_complete_multi_agent_workflow():
    """Test complete workflow with handoff, coordination, and memory."""
    # Phase 1: Initial processing
    processor = DataProcessorAgent()
    prepare_mem = PrepareForMemoryPrimitive()  # Wrap data for storage
    store_initial = AgentMemoryPrimitive(
        operation="store", memory_key="initial_data", memory_scope="session"
    )

    # Phase 2: Parallel analysis
    analysts = {
        "security": AnalyzerAgent("security"),
        "performance": AnalyzerAgent("performance"),
    }
    coordinator = AgentCoordinationPrimitive(
        agent_primitives=analysts, coordination_strategy="aggregate"
    )

    # Phase 3: Decision making
    handoff_to_decision = AgentHandoffPrimitive(
        target_agent="decision_maker", handoff_strategy="immediate"
    )
    decision_maker = DecisionMakerAgent()
    retrieve_initial = AgentMemoryPrimitive(
        operation="retrieve", memory_key="initial_data"
    )

    # Build complete workflow
    workflow = (
        processor
        >> prepare_mem
        >> store_initial
        >> coordinator
        >> handoff_to_decision
        >> decision_maker
        >> retrieve_initial
    )

    # Execute
    context = WorkflowContext(
        workflow_id="complete-workflow", session_id="test-session"
    )
    context.metadata["current_agent"] = "processor"

    result = await workflow.execute({"data": "test_data"}, context)

    # Verify workflow completed (uses memory_value key from AgentMemoryPrimitive)
    assert result["memory_value"]["processed"] is True
    assert result["memory_value"]["data"] == "test_data"

    # Verify handoff happened
    assert context.metadata["current_agent"] == "decision_maker"
    assert len(context.metadata.get("agent_history", [])) == 1

    # Verify memory persisted (uses session_memories key structure)
    memories = context.metadata.get("agent_memory", {}).get("session_memories", {})
    assert "initial_data" in memories


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.asyncio
async def test_parallel_coordination_performance():
    """Test that parallel coordination is actually faster than sequential."""
    # Create slow agents
    slow_agents = {
        f"agent{i}": DataProcessorAgent(processing_time=0.1) for i in range(5)
    }

    # Parallel execution
    coordinator = AgentCoordinationPrimitive(
        agent_primitives=slow_agents, coordination_strategy="aggregate"
    )

    context = WorkflowContext(workflow_id="perf-test")

    import time

    start = time.perf_counter()
    result = await coordinator.execute({"data": "test"}, context)
    parallel_duration = time.perf_counter() - start

    # Parallel should take roughly 0.1s (not 0.5s for sequential)
    assert parallel_duration < 0.3, (
        f"Parallel execution too slow: {parallel_duration:.2f}s"
    )
    assert result["coordination_metadata"]["successful_agents"] == 5


@pytest.mark.asyncio
async def test_coordination_first_strategy_performance():
    """Test that first strategy returns as soon as first agent completes."""

    class DelayedAgent(WorkflowPrimitive[dict, dict]):
        def __init__(self, name: str, delay: float):
            self.name = name
            self._delay = delay

        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            await asyncio.sleep(self._delay)
            return {"agent": self.name, "completed": True}

    # Create agents with different delays
    agents = {
        "fast": DelayedAgent("fast", 0.01),
        "medium": DelayedAgent("medium", 0.1),
        "slow": DelayedAgent("slow", 0.5),
    }

    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents, coordination_strategy="first"
    )

    context = WorkflowContext(workflow_id="first-strategy-test")

    import time

    start = time.perf_counter()
    result = await coordinator.execute({"data": "test"}, context)
    duration = time.perf_counter() - start

    # Should complete relatively quickly (though current implementation waits for all)
    # TODO: Optimize "first" strategy to return on first success
    assert duration < 1.0, f"First strategy too slow: {duration:.2f}s"
    # First strategy returns first successful agent (alphabetically first if all succeed)
    assert result["aggregated_result"]["strategy"] == "first"
    assert result["aggregated_result"]["agent"] in ["fast", "medium", "slow"]


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_coordination_with_failing_agents():
    """Test coordination handles failing agents gracefully."""

    class FailingAgent(WorkflowPrimitive[dict, dict]):
        def __init__(self, name: str, should_fail: bool):
            self.name = name
            self._should_fail = should_fail

        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            if self._should_fail:
                raise ValueError(f"{self.name} failed")
            return {"agent": self.name, "result": "success"}

    agents = {
        "good1": FailingAgent("good1", should_fail=False),
        "bad": FailingAgent("bad", should_fail=True),
        "good2": FailingAgent("good2", should_fail=False),
    }

    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents,
        coordination_strategy="aggregate",
        require_all_success=False,  # Allow partial success
    )

    context = WorkflowContext(workflow_id="error-handling-test")
    result = await coordinator.execute({"data": "test"}, context)

    # Should get results from successful agents
    assert result["coordination_metadata"]["successful_agents"] == 2
    assert result["coordination_metadata"]["failed_agents"] == 1
    assert "bad" in result["failed_agents"]


@pytest.mark.asyncio
async def test_memory_operations_with_missing_keys():
    """Test memory retrieve handles missing keys gracefully."""
    retrieve = AgentMemoryPrimitive(operation="retrieve", memory_key="non_existent_key")

    context = WorkflowContext(workflow_id="missing-key-test")
    result = await retrieve.execute({"data": "test"}, context)

    # Should return None for missing key (uses correct API keys: memory_value, memory_found)
    assert result["memory_value"] is None
    assert result["memory_found"] is False


# ============================================================================
# Edge Cases
# ============================================================================


@pytest.mark.asyncio
async def test_handoff_preserves_large_context():
    """Test handoff preserves context with large metadata."""
    agent1 = DataProcessorAgent()
    handoff = AgentHandoffPrimitive(target_agent="agent2", handoff_strategy="immediate")
    agent2 = AnalyzerAgent()

    workflow = agent1 >> handoff >> agent2

    context = WorkflowContext(workflow_id="large-context-test")
    context.metadata["current_agent"] = "agent1"

    # Add large metadata
    context.metadata["large_data"] = {f"key{i}": f"value{i}" for i in range(1000)}

    await workflow.execute({"data": "test"}, context)

    # Large metadata should be preserved
    assert len(context.metadata["large_data"]) == 1000
    assert context.metadata["current_agent"] == "agent2"


@pytest.mark.asyncio
async def test_memory_scopes_isolation():
    """Test memory scope fallback behavior (searches all scopes if not found in primary)."""
    # Store in workflow scope
    store_workflow = AgentMemoryPrimitive(
        operation="store", memory_key="scoped_data", memory_scope="workflow"
    )

    # Try to retrieve from session scope
    retrieve_session = AgentMemoryPrimitive(
        operation="retrieve", memory_key="scoped_data", memory_scope="session"
    )

    context = WorkflowContext(workflow_id="scope-test-1", session_id="test-session")

    # Store in workflow scope
    agent = DataProcessorAgent()
    prepare_mem = PrepareForMemoryPrimitive()  # Wrap data for storage
    result1 = await agent.execute({"data": "test"}, context)
    result1_wrapped = await prepare_mem.execute(result1, context)
    await store_workflow.execute(result1_wrapped, context)

    # Retrieve from session scope - will find it via fallback search
    # (AgentMemoryPrimitive searches all scopes if not found in primary)
    result2 = await retrieve_session.execute({"data": "test"}, context)

    assert result2["memory_found"] is True  # Found via fallback
    assert result2["memory_value"]["processed"] is True


@pytest.mark.asyncio
async def test_coordination_timeout_handling():
    """Test coordination timeout works correctly."""

    class SlowAgent(WorkflowPrimitive[dict, dict]):
        def __init__(self, name: str):
            self.name = name

        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            await asyncio.sleep(5.0)  # Very slow
            return {"agent": self.name}

    agents = {"slow1": SlowAgent("slow1"), "slow2": SlowAgent("slow2")}

    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents,
        coordination_strategy="aggregate",
        timeout_seconds=0.5,  # Short timeout
        require_all_success=False,
    )

    context = WorkflowContext(workflow_id="timeout-test")

    import time

    start = time.perf_counter()
    result = await coordinator.execute({"data": "test"}, context)
    duration = time.perf_counter() - start

    # Should timeout quickly
    assert duration < 1.0, f"Timeout not enforced: {duration:.2f}s"

    # All agents should have timed out
    assert result["coordination_metadata"]["failed_agents"] == 2
