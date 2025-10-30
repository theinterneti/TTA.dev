"""
Complete Multi-Agent Workflow Example

Demonstrates a real-world scenario combining all agent coordination primitives:
- AgentHandoffPrimitive for task delegation
- AgentMemoryPrimitive for decision persistence
- AgentCoordinationPrimitive for parallel execution

Scenario: Software Development Workflow
- Architect makes decisions
- Multiple specialists work in parallel
- Implementation agent uses stored decisions
- QA agent validates against original decisions
"""

import asyncio

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive

from universal_agent_context.primitives import (
    AgentCoordinationPrimitive,
    AgentHandoffPrimitive,
    AgentMemoryPrimitive,
)

# ============================================================================
# Agent Implementations
# ============================================================================


class ArchitectAgent(WorkflowPrimitive[dict, dict]):
    """Makes architectural decisions."""

    def __init__(self):
        self.name = "architect"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        print("🏗️  ARCHITECT: Making design decisions...")
        await asyncio.sleep(0.2)
        return {
            "architecture": "microservices",
            "patterns": ["CQRS", "Event Sourcing", "API Gateway"],
            "technologies": {
                "backend": "Python/FastAPI",
                "database": "PostgreSQL",
                "cache": "Redis",
                "message_queue": "RabbitMQ",
            },
            "rationale": "Scalability, maintainability, and performance",
        }


class SecuritySpecialist(WorkflowPrimitive[dict, dict]):
    """Analyzes security requirements."""

    def __init__(self):
        self.name = "security_specialist"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        print("🔒 SECURITY SPECIALIST: Analyzing security...")
        await asyncio.sleep(0.3)
        return {
            "security_requirements": [
                "OAuth2 authentication",
                "Rate limiting",
                "Input validation",
                "HTTPS only",
            ],
            "compliance": ["GDPR", "SOC2"],
            "risk_level": "medium",
        }


class PerformanceSpecialist(WorkflowPrimitive[dict, dict]):
    """Defines performance requirements."""

    def __init__(self):
        self.name = "performance_specialist"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        print("⚡ PERFORMANCE SPECIALIST: Defining requirements...")
        await asyncio.sleep(0.2)
        return {
            "performance_targets": {
                "latency_p99": "100ms",
                "throughput": "10k req/s",
                "availability": "99.9%",
            },
            "optimization_strategy": "caching + load balancing",
        }


class InfrastructureSpecialist(WorkflowPrimitive[dict, dict]):
    """Plans infrastructure."""

    def __init__(self):
        self.name = "infrastructure_specialist"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        print("☁️  INFRASTRUCTURE SPECIALIST: Planning infrastructure...")
        await asyncio.sleep(0.25)
        return {
            "infrastructure": {
                "platform": "Kubernetes",
                "cloud": "AWS",
                "regions": ["us-east-1", "eu-west-1"],
                "scaling": "horizontal pod autoscaling",
            },
            "estimated_cost": "$5000/month",
        }


class ImplementationAgent(WorkflowPrimitive[dict, dict]):
    """Implements based on all decisions."""

    def __init__(self):
        self.name = "implementation"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        print("💻 IMPLEMENTATION: Building solution...")

        # Retrieve all stored decisions
        architecture = input_data.get("architecture_decision", {})
        security = input_data.get("security_requirements", {})
        performance = input_data.get("performance_requirements", {})
        infrastructure = input_data.get("infrastructure_plan", {})

        print(f"   Using architecture: {architecture.get('value', {}).get('architecture')}")
        print(f"   Security compliance: {security.get('value', {}).get('compliance', [])}")
        print(
            f"   Performance target: {performance.get('value', {}).get('performance_targets', {}).get('latency_p99')}"
        )

        await asyncio.sleep(0.5)

        return {
            "implementation_status": "complete",
            "components": [
                "api-gateway",
                "user-service",
                "auth-service",
                "notification-service",
            ],
            "tests_passed": True,
            "code_coverage": "95%",
        }


class QAAgent(WorkflowPrimitive[dict, dict]):
    """Validates implementation against decisions."""

    def __init__(self):
        self.name = "qa"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        print("🔍 QA: Validating implementation...")

        impl_status = input_data.get("implementation_status")
        tests_passed = input_data.get("tests_passed")

        await asyncio.sleep(0.3)

        return {
            "qa_status": "approved",
            "validation_results": {
                "architecture_compliance": "100%",
                "security_compliance": "100%",
                "performance_compliance": "98%",
                "documentation": "complete",
            },
            "ready_for_deployment": True,
        }


# ============================================================================
# Helper Primitives
# ============================================================================


class SpecialistAggregator(WorkflowPrimitive[dict, dict]):
    """Aggregates specialist results for implementation."""

    def __init__(self):
        self.name = "aggregator"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        print("📋 AGGREGATOR: Combining specialist requirements...")

        # Extract specialist results from coordination output
        agent_results = input_data.get("agent_results", {})

        return {
            "security_requirements": agent_results.get("security", {}),
            "performance_requirements": agent_results.get("performance", {}),
            "infrastructure_plan": agent_results.get("infrastructure", {}),
            "aggregation_complete": True,
        }


class MemoryRetriever(WorkflowPrimitive[dict, dict]):
    """Retrieves all memories for implementation."""

    def __init__(self):
        self.name = "memory_retriever"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        print("🧠 MEMORY RETRIEVER: Loading all decisions...")

        # Get all memories from context
        memories = context.metadata.get("agent_memory", {}).get("session", {})

        return {
            "architecture_decision": memories.get("architecture_decision", {}),
            "security_requirements": memories.get("security_requirements", {}),
            "performance_requirements": memories.get("performance_requirements", {}),
            "infrastructure_plan": memories.get("infrastructure_plan", {}),
        }


# ============================================================================
# Main Workflow
# ============================================================================


async def main():
    """Run complete multi-agent workflow."""
    print("=" * 70)
    print("COMPLETE MULTI-AGENT WORKFLOW")
    print("Scenario: Software Development Lifecycle")
    print("=" * 70)

    # ========================================================================
    # Step 1: Architect makes decisions
    # ========================================================================
    print("\n" + "=" * 70)
    print("PHASE 1: Architectural Design")
    print("=" * 70 + "\n")

    architect = ArchitectAgent()
    store_architecture = AgentMemoryPrimitive(
        operation="store",
        memory_key="architecture_decision",
        memory_scope="session",
    )
    handoff_to_specialists = AgentHandoffPrimitive(
        target_agent="specialists", handoff_strategy="immediate"
    )

    phase1_workflow = architect >> store_architecture >> handoff_to_specialists

    context = WorkflowContext(workflow_id="software-dev-workflow", session_id="dev-session-001")
    context.metadata["current_agent"] = "architect"

    phase1_result = await phase1_workflow.execute({"project": "e-commerce-platform"}, context)

    # ========================================================================
    # Step 2: Specialists work in parallel
    # ========================================================================
    print("\n" + "=" * 70)
    print("PHASE 2: Specialist Analysis (Parallel)")
    print("=" * 70 + "\n")

    specialists = {
        "security": SecuritySpecialist(),
        "performance": PerformanceSpecialist(),
        "infrastructure": InfrastructureSpecialist(),
    }

    specialist_coordinator = AgentCoordinationPrimitive(
        agent_primitives=specialists,
        coordination_strategy="aggregate",
        timeout_seconds=5.0,
    )

    specialist_result = await specialist_coordinator.execute(phase1_result, context)

    # ========================================================================
    # Step 3: Store specialist results
    # ========================================================================
    print("\n" + "=" * 70)
    print("PHASE 3: Storing Specialist Requirements")
    print("=" * 70 + "\n")

    aggregator = SpecialistAggregator()
    store_security = AgentMemoryPrimitive(
        operation="store",
        memory_key="security_requirements",
        memory_scope="session",
    )
    store_performance = AgentMemoryPrimitive(
        operation="store",
        memory_key="performance_requirements",
        memory_scope="session",
    )
    store_infrastructure = AgentMemoryPrimitive(
        operation="store",
        memory_key="infrastructure_plan",
        memory_scope="session",
    )

    phase3_workflow = aggregator >> store_security >> store_performance >> store_infrastructure

    phase3_result = await phase3_workflow.execute(specialist_result, context)

    # ========================================================================
    # Step 4: Implementation using stored decisions
    # ========================================================================
    print("\n" + "=" * 70)
    print("PHASE 4: Implementation")
    print("=" * 70 + "\n")

    memory_retriever = MemoryRetriever()
    implementer = ImplementationAgent()
    handoff_to_qa = AgentHandoffPrimitive(target_agent="qa", handoff_strategy="immediate")

    phase4_workflow = memory_retriever >> implementer >> handoff_to_qa

    implementation_result = await phase4_workflow.execute(phase3_result, context)

    # ========================================================================
    # Step 5: QA Validation
    # ========================================================================
    print("\n" + "=" * 70)
    print("PHASE 5: Quality Assurance")
    print("=" * 70 + "\n")

    qa = QAAgent()
    final_result = await qa.execute(implementation_result, context)

    # ========================================================================
    # Display Final Results
    # ========================================================================
    print("\n" + "=" * 70)
    print("WORKFLOW COMPLETE - FINAL RESULTS")
    print("=" * 70)

    print(f"\n✅ QA Status: {final_result['qa_status']}")
    print(f"✅ Ready for Deployment: {final_result['ready_for_deployment']}")

    print("\n📊 Validation Results:")
    for metric, value in final_result["validation_results"].items():
        print(f"   • {metric}: {value}")

    print("\n🏛️  Agent History:")
    for i, handoff in enumerate(context.metadata.get("agent_history", []), 1):
        print(f"   {i}. {handoff['from_agent']} → {handoff['to_agent']} ({handoff['strategy']})")

    print(f"\n🎯 Final Agent: {context.metadata.get('current_agent')}")

    print("\n💾 Session Memory Summary:")
    memories = context.metadata.get("agent_memory", {}).get("session", {})
    print(f"   Total Decisions Stored: {len(memories)}")
    for key in memories.keys():
        print(f"   • {key}")

    print("\n" + "=" * 70)
    print("SUCCESS: Multi-agent workflow completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
