"""Simple Agent Patterns Using TTA.dev Primitives.

This example demonstrates how to build agent-like behavior using current TTA.dev
primitives without needing specialized agent classes.

While VISION.md references DeveloperAgent, QAAgent, etc., those classes don't exist yet.
This shows how to achieve similar functionality with custom InstrumentedPrimitives.

Key Patterns:
- Simulating specialized agents with InstrumentedPrimitive
- Sequential agent workflows with >> operator
- Multi-agent parallel execution with | operator
- Agent memory via WorkflowContext.state

Usage:
    uv run python packages/tta-dev-primitives/examples/agent_patterns_simple.py
"""

from __future__ import annotations

import asyncio
from typing import Any

from tta_dev_primitives import ParallelPrimitive, WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive

# ==============================================================================
# Pattern 1: Simple Agent Simulation
# ==============================================================================


class DeveloperAgentPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Developer agent that analyzes code and suggests improvements."""

    def __init__(self) -> None:
        super().__init__(name="developer_agent")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Developer agent: analyze code and provide suggestions."""
        await asyncio.sleep(0.2)  # Simulate analysis time

        return {
            "agent": "developer",
            "analysis": {
                "complexity": "medium",
                "maintainability": "good",
                "test_coverage": "needs_improvement",
            },
            "suggestions": [
                "Add type hints to improve code clarity",
                "Extract repeated logic into helper functions",
                "Add docstrings to public methods",
            ],
            **input_data,  # Pass through input data
        }


class QAAgentPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """QA agent that reviews code for testing gaps."""

    def __init__(self) -> None:
        super().__init__(name="qa_agent")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """QA agent: identify testing gaps and coverage issues."""
        analysis = input_data.get("analysis", {})
        await asyncio.sleep(0.15)  # Simulate review time

        return {
            "agent": "qa",
            "test_recommendations": [
                "Add unit tests for edge cases",
                "Implement integration tests for API endpoints",
                "Add property-based tests for data validation",
            ],
            "coverage_target": "95%",
            "priority": "high"
            if analysis.get("test_coverage") == "needs_improvement"
            else "medium",
            "previous_analysis": analysis,
        }


class SecurityAgentPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Security agent that checks for vulnerabilities."""

    def __init__(self) -> None:
        super().__init__(name="security_agent")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Security agent: scan for security issues."""
        await asyncio.sleep(0.1)  # Simulate scanning

        return {
            "agent": "security",
            "vulnerabilities_found": 0,
            "security_score": "A",
            "recommendations": [
                "Enable dependency scanning in CI/CD",
                "Add input validation for user data",
                "Use environment variables for secrets",
            ],
        }


# ==============================================================================
# Pattern 2: Agent Memory via WorkflowContext
# ==============================================================================


class MemoryAwareAgentPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Agent that accesses and updates shared memory in WorkflowContext."""

    def __init__(self, agent_name: str) -> None:
        super().__init__(name=f"{agent_name}_agent")
        self.agent_name = agent_name

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Make decision and update shared memory."""
        # Access shared memory from context
        previous_decisions = context.state.get("decisions", [])

        # Make decision
        decision = f"{self.agent_name} recommends: Use best practices"
        previous_decisions.append(decision)

        # Update shared memory
        context.state["decisions"] = previous_decisions

        return {
            "agent": self.agent_name,
            "decision": decision,
            "aware_of_previous": len(previous_decisions) - 1,
        }


# ==============================================================================
# Pattern 3: Aggregator Agent
# ==============================================================================


class AggregatorAgentPrimitive(InstrumentedPrimitive[list[dict[str, Any]], dict[str, Any]]):
    """Aggregator agent that combines results from multiple agents."""

    def __init__(self) -> None:
        super().__init__(name="aggregator_agent")

    async def _execute_impl(
        self, input_data: list[dict[str, Any]], context: WorkflowContext
    ) -> dict[str, Any]:
        """Aggregate all agent feedback."""
        all_recommendations: list[str] = []
        for result in input_data:
            if "test_recommendations" in result:
                all_recommendations.extend(result["test_recommendations"])
            if "recommendations" in result:
                all_recommendations.extend(result["recommendations"])

        return {
            "agent": "aggregator",
            "total_recommendations": len(all_recommendations),
            "recommendations": all_recommendations,
            "review_complete": True,
        }


# ==============================================================================
# Demonstrations
# ==============================================================================


async def demo_simple_agents() -> None:
    """Demonstrate simple agent simulation with InstrumentedPrimitive."""
    print("\n" + "=" * 80)
    print("PATTERN 1: Simple Agent Simulation")
    print("=" * 80)

    # Create agent primitives
    developer = DeveloperAgentPrimitive()
    qa = QAAgentPrimitive()
    security = SecurityAgentPrimitive()

    # Sequential workflow: Developer → QA → Security
    review_workflow = developer >> qa >> security

    context = WorkflowContext(correlation_id="demo-simple")
    input_data = {
        "code": "def process_data(data): return data.upper()",
        "file_path": "src/processor.py",
    }

    print("\n🔄 Running sequential agent review...")
    result = await review_workflow.execute(input_data, context)

    print(f"\n✅ Final result from {result['agent']} agent:")
    print(f"   Security Score: {result['security_score']}")
    print(f"   Recommendations: {len(result['recommendations'])} items")


async def demo_parallel_agents() -> None:
    """Demonstrate parallel agent execution."""
    print("\n" + "=" * 80)
    print("PATTERN 2: Parallel Multi-Agent Analysis")
    print("=" * 80)

    # Create multiple specialist agents
    developer = DeveloperAgentPrimitive()
    security = SecurityAgentPrimitive()

    # Parallel execution: Both agents analyze simultaneously
    parallel_review = ParallelPrimitive([developer, security])

    context = WorkflowContext(correlation_id="demo-parallel")
    input_data = {
        "code": "def authenticate(username, password): ...",
        "file_path": "src/auth.py",
    }

    print("\n🚀 Running parallel agent analysis...")
    results = await parallel_review.execute(input_data, context)

    print(f"\n✅ Received {len(results)} analyses:")
    for result in results:
        agent = result.get("agent", "unknown")
        print(f"   - {agent.title()} Agent: ✓")


async def demo_agent_memory() -> None:
    """Demonstrate agent memory using WorkflowContext."""
    print("\n" + "=" * 80)
    print("PATTERN 3: Agent Memory via WorkflowContext")
    print("=" * 80)

    # Create agents that share memory
    agent1 = MemoryAwareAgentPrimitive("architect")
    agent2 = MemoryAwareAgentPrimitive("developer")
    agent3 = MemoryAwareAgentPrimitive("qa")

    workflow = agent1 >> agent2 >> agent3

    # Context serves as shared memory
    context = WorkflowContext(correlation_id="demo-memory", state={"decisions": []})

    print("\n🧠 Agents sharing memory via WorkflowContext...")
    result = await workflow.execute({}, context)

    print(
        f"\n✅ Final agent ({result['agent']}) was aware of {result['aware_of_previous']} previous decisions"
    )
    print(f"   Total decisions made: {len(context.state['decisions'])}")
    print("\nDecision history:")
    for i, decision in enumerate(context.state["decisions"], 1):
        print(f"   {i}. {decision}")


async def demo_code_review_workflow() -> None:
    """Demonstrate a real-world code review workflow with multiple agents."""
    print("\n" + "=" * 80)
    print("REAL-WORLD EXAMPLE: Complete Code Review Workflow")
    print("=" * 80)

    # Stage 1: Initial developer review
    developer = DeveloperAgentPrimitive()

    # Stage 2: Parallel specialist reviews
    qa = QAAgentPrimitive()
    security = SecurityAgentPrimitive()
    specialist_review = ParallelPrimitive([qa, security])

    # Stage 3: Aggregation
    aggregator = AggregatorAgentPrimitive()

    # Complete workflow
    code_review = developer >> specialist_review >> aggregator

    context = WorkflowContext(correlation_id="code-review-001")
    input_data = {
        "code": "def process_payment(card_number, amount): ...",
        "file_path": "src/payments.py",
        "author": "developer@example.com",
    }

    print("\n📋 Starting code review workflow...")
    print("   1. Developer analysis")
    print("   2. QA + Security review (parallel)")
    print("   3. Aggregate feedback")

    result = await code_review.execute(input_data, context)

    print("\n✅ Code review complete!")
    print(f"   Total recommendations: {result['total_recommendations']}")
    print(f"   Review status: {result['review_complete']}")


# ==============================================================================
# Main Demo
# ==============================================================================


async def main() -> None:
    """Run all agent pattern demonstrations."""
    print("\n" + "=" * 80)
    print("AGENT PATTERNS WITH TTA.DEV PRIMITIVES")
    print("=" * 80)
    print("\nThis demonstrates how to build agent-like behavior without")
    print("specialized agent classes (which don't exist yet).")
    print("\nUsing:")
    print("  - InstrumentedPrimitive for custom agents")
    print("  - >> operator for sequential workflows")
    print("  - | operator for parallel execution")
    print("  - ParallelPrimitive for concurrent agents")
    print("  - WorkflowContext.state for shared memory")

    await demo_simple_agents()
    await demo_parallel_agents()
    await demo_agent_memory()
    await demo_code_review_workflow()

    print("\n" + "=" * 80)
    print("KEY TAKEAWAYS")
    print("=" * 80)
    print("\n1. Agent behavior ≠ Agent classes")
    print("   - Use InstrumentedPrimitive for custom agent logic")
    print("   - Automatic observability built-in")
    print("\n2. Agent coordination is built-in")
    print("   - >> operator for sequential pipelines")
    print("   - ParallelPrimitive for concurrent execution")
    print("   - Mix and match primitives freely")
    print("\n3. Shared memory via WorkflowContext.state")
    print("   - context.state for cross-agent communication")
    print("   - Automatic correlation ID propagation")
    print("\n4. Full observability")
    print("   - InstrumentedPrimitive = automatic tracing")
    print("   - Metrics collection built-in")
    print("\n5. Type-safe composition")
    print("   - Generic types ensure correct data flow")
    print("   - Mypy/Pyright catch errors at development time")
    print("\n" + "=" * 80)
    print("\nFor more patterns, see:")
    print("  - examples/multi_agent_workflow.py")
    print("  - packages/universal-agent-context/examples/")
    print("  - ROADMAP.md (Phase 2: Role-Based Agent System)")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
