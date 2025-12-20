"""
Agent Memory Example

Demonstrates how to use AgentMemoryPrimitive for persistent memory
across agents and workflow steps.
"""

import asyncio

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive

from universal_agent_context.primitives import AgentMemoryPrimitive


class ArchitectAgent(WorkflowPrimitive[dict, dict]):
    """Agent that makes architectural decisions."""

    def __init__(self):
        self.name = "architect"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Make architectural decision."""
        print("🏗️  Architect: Making design decisions...")
        decision = {
            "architecture": "microservices",
            "database": "PostgreSQL",
            "cache": "Redis",
            "message_queue": "RabbitMQ",
            "rationale": "Scalability and maintainability",
        }
        print(f"   Decision: {decision['architecture']}")
        return decision


class ImplementerAgent(WorkflowPrimitive[dict, dict]):
    """Agent that implements based on architectural decisions."""

    def __init__(self):
        self.name = "implementer"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Implement based on retrieved decision."""
        print("💻 Implementer: Implementing solution...")
        architecture = input_data.get("value", {}).get("architecture")
        print(f"   Using architecture: {architecture}")
        return {
            "implementation_status": "in_progress",
            "components_created": ["api-gateway", "user-service", "auth-service"],
        }


class ReviewerAgent(WorkflowPrimitive[dict, dict]):
    """Agent that reviews implementation against decisions."""

    def __init__(self):
        self.name = "reviewer"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Review implementation against original decision."""
        print("🔍 Reviewer: Validating implementation...")
        decision = input_data.get("value", {})
        print(f"   Checking against: {decision.get('architecture')}")
        print(f"   Rationale: {decision.get('rationale')}")
        return {
            "review_status": "approved",
            "compliance": "100%",
            "comments": "Implementation matches architectural decision",
        }


async def main():
    """Run agent memory example."""
    print("=" * 60)
    print("Agent Memory Example")
    print("=" * 60)

    # Create agents
    architect = ArchitectAgent()
    implementer = ImplementerAgent()
    reviewer = ReviewerAgent()

    # Create memory primitives
    store_decision = AgentMemoryPrimitive(
        operation="store", memory_key="architecture_decision", memory_scope="session"
    )

    retrieve_for_implementation = AgentMemoryPrimitive(
        operation="retrieve", memory_key="architecture_decision"
    )

    retrieve_for_review = AgentMemoryPrimitive(
        operation="retrieve", memory_key="architecture_decision"
    )

    list_all_memories = AgentMemoryPrimitive(operation="list", memory_scope="session")

    # Build workflow with memory
    workflow = (
        architect
        >> store_decision
        >> retrieve_for_implementation
        >> implementer
        >> retrieve_for_review
        >> reviewer
        >> list_all_memories
    )

    # Create context
    context = WorkflowContext(workflow_id="memory-example", session_id="session-123")
    context.metadata["current_agent"] = "architect"

    # Execute workflow
    print("\n🚀 Starting workflow...\n")
    result = await workflow.execute({"project": "e-commerce-platform"}, context)

    # Display results
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    print(f"Review Status: {result['review_status']}")
    print(f"Compliance: {result['compliance']}")
    print(f"Comments: {result['comments']}")

    # Show stored memories
    print("\n" + "=" * 60)
    print("Session Memory:")
    print("=" * 60)
    memories = context.metadata.get("agent_memory", {}).get("session", {})
    for key, memory in memories.items():
        print(f"\n📝 {key}:")
        print(f"   Value: {memory['value']}")
        print(f"   Agent: {memory['agent']}")
        print(f"   Timestamp: {memory['timestamp']}")


async def query_example():
    """Demonstrate memory querying."""
    print("\n" + "=" * 60)
    print("Memory Query Example")
    print("=" * 60)

    # Store multiple memories
    architect = ArchitectAgent()

    store_decision = AgentMemoryPrimitive(
        operation="store", memory_key="architecture_decision", memory_scope="session"
    )

    store_constraint = AgentMemoryPrimitive(
        operation="store",
        memory_key="performance_constraint",
        memory_scope="session",
        memory_value={"max_latency": "100ms", "throughput": "10k req/s"},
    )

    query_memories = AgentMemoryPrimitive(
        operation="query",
        memory_scope="session",
        query_filter={"tags": {"type": "architectural"}},
    )

    # Build workflow
    workflow = architect >> store_decision >> store_constraint >> query_memories

    # Execute
    context = WorkflowContext(workflow_id="query-example", session_id="query-session")
    context.metadata["current_agent"] = "architect"

    result = await workflow.execute({"project": "high-performance-api"}, context)

    print("\n🔍 Query Results:")
    for memory in result.get("memories", []):
        print(f"\n   Key: {memory['key']}")
        print(f"   Value: {memory['value']}")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(query_example())
