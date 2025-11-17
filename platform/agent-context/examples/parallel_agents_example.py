"""
Parallel Agent Coordination Example

Demonstrates how to use AgentCoordinationPrimitive to execute multiple
agents in parallel with different coordination strategies.
"""

import asyncio

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive

from universal_agent_context.primitives import AgentCoordinationPrimitive


class SecurityAnalyzer(WorkflowPrimitive[dict, dict]):
    """Agent that analyzes security aspects."""

    def __init__(self):
        self.name = "security_analyzer"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Analyze security."""
        print("🔒 Security Analyzer: Checking for vulnerabilities...")
        await asyncio.sleep(0.5)  # Simulate work
        return {
            "agent": "security",
            "score": 8.5,
            "findings": ["HTTPS enforced", "Input validation present"],
            "recommendation": "approved",
        }


class PerformanceAnalyzer(WorkflowPrimitive[dict, dict]):
    """Agent that analyzes performance."""

    def __init__(self):
        self.name = "performance_analyzer"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Analyze performance."""
        print("⚡ Performance Analyzer: Measuring metrics...")
        await asyncio.sleep(0.3)  # Simulate work
        return {
            "agent": "performance",
            "score": 9.0,
            "metrics": {"latency": "45ms", "throughput": "5k req/s"},
            "recommendation": "approved",
        }


class CodeQualityAnalyzer(WorkflowPrimitive[dict, dict]):
    """Agent that analyzes code quality."""

    def __init__(self):
        self.name = "code_quality_analyzer"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Analyze code quality."""
        print("📊 Code Quality Analyzer: Reviewing code...")
        await asyncio.sleep(0.4)  # Simulate work
        return {
            "agent": "code_quality",
            "score": 8.0,
            "metrics": {"coverage": "92%", "complexity": "low"},
            "recommendation": "approved",
        }


class DocumentationAnalyzer(WorkflowPrimitive[dict, dict]):
    """Agent that analyzes documentation."""

    def __init__(self):
        self.name = "documentation_analyzer"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Analyze documentation."""
        print("📝 Documentation Analyzer: Checking docs...")
        await asyncio.sleep(0.2)  # Simulate work
        return {
            "agent": "documentation",
            "score": 7.5,
            "completeness": "85%",
            "recommendation": "approved",
        }


async def aggregate_strategy_example():
    """Demonstrate aggregate coordination strategy."""
    print("=" * 60)
    print("Aggregate Strategy Example")
    print("=" * 60)
    print("Collects results from all agents\n")

    # Create agents
    agents = {
        "security": SecurityAnalyzer(),
        "performance": PerformanceAnalyzer(),
        "code_quality": CodeQualityAnalyzer(),
        "documentation": DocumentationAnalyzer(),
    }

    # Create coordinator with aggregate strategy
    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents,
        coordination_strategy="aggregate",
        timeout_seconds=5.0,
        require_all_success=False,
    )

    # Execute
    context = WorkflowContext(workflow_id="aggregate-example")
    result = await coordinator.execute({"code_review": "feature-123"}, context)

    # Display results
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    print(f"Total Agents: {result['coordination_metadata']['total_agents']}")
    print(f"Successful: {result['coordination_metadata']['successful_agents']}")
    print(f"Failed: {result['coordination_metadata']['failed_agents']}")
    print(f"Elapsed: {result['coordination_metadata']['elapsed_ms']:.2f}ms")

    print("\n📊 Individual Agent Results:")
    for agent_name, agent_result in result["agent_results"].items():
        print(f"\n   {agent_name}:")
        print(f"      Score: {agent_result.get('score', 'N/A')}")
        print(f"      Recommendation: {agent_result.get('recommendation', 'N/A')}")


async def first_success_strategy_example():
    """Demonstrate first-success coordination strategy."""
    print("\n\n" + "=" * 60)
    print("First Success Strategy Example")
    print("=" * 60)
    print("Returns result from first successful agent\n")

    # Create multiple similar agents (e.g., different LLMs)
    class FastLLM(WorkflowPrimitive[dict, dict]):
        def __init__(self):
            self.name = "fast_llm"

        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            print("🚀 Fast LLM: Processing (low quality)...")
            await asyncio.sleep(0.1)
            return {"agent": "fast_llm", "response": "Quick answer", "quality": "low"}

    class BalancedLLM(WorkflowPrimitive[dict, dict]):
        def __init__(self):
            self.name = "balanced_llm"

        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            print("⚖️  Balanced LLM: Processing (medium quality)...")
            await asyncio.sleep(0.3)
            return {
                "agent": "balanced_llm",
                "response": "Balanced answer",
                "quality": "medium",
            }

    class QualityLLM(WorkflowPrimitive[dict, dict]):
        def __init__(self):
            self.name = "quality_llm"

        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            print("💎 Quality LLM: Processing (high quality)...")
            await asyncio.sleep(0.5)
            return {
                "agent": "quality_llm",
                "response": "High quality answer",
                "quality": "high",
            }

    agents = {
        "fast": FastLLM(),
        "balanced": BalancedLLM(),
        "quality": QualityLLM(),
    }

    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents, coordination_strategy="first", timeout_seconds=2.0
    )

    context = WorkflowContext(workflow_id="first-success-example")
    result = await coordinator.execute({"query": "What is AI?"}, context)

    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    print(f"First Response From: {result.get('agent', 'unknown')}")
    print(f"Response: {result.get('response', 'N/A')}")
    print(f"Quality: {result.get('quality', 'N/A')}")


async def consensus_strategy_example():
    """Demonstrate consensus coordination strategy."""
    print("\n\n" + "=" * 60)
    print("Consensus Strategy Example")
    print("=" * 60)
    print("Finds majority agreement among agents\n")

    # Create voting agents
    class Voter(WorkflowPrimitive[dict, dict]):
        def __init__(self, name: str, vote: str):
            self.name = name
            self._vote = vote

        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            print(f"🗳️  {self.name}: Voting '{self._vote}'")
            await asyncio.sleep(0.1)
            return {"agent": self.name, "vote": self._vote, "confidence": 0.9}

    agents = {
        "voter1": Voter("voter1", "approve"),
        "voter2": Voter("voter2", "approve"),
        "voter3": Voter("voter3", "approve"),
        "voter4": Voter("voter4", "reject"),
        "voter5": Voter("voter5", "approve"),
    }

    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents,
        coordination_strategy="consensus",
        timeout_seconds=2.0,
    )

    context = WorkflowContext(workflow_id="consensus-example")
    result = await coordinator.execute({"proposal": "feature-xyz"}, context)

    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    print(f"Consensus Result: {result.get('vote', 'N/A')}")
    print(f"Total Votes: {result['coordination_metadata']['total_agents']}")
    print(f"Agreement: {result['coordination_metadata']['successful_agents']} agents")


async def main():
    """Run all coordination examples."""
    await aggregate_strategy_example()
    await first_success_strategy_example()
    await consensus_strategy_example()

    print("\n\n" + "=" * 60)
    print("All Examples Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
