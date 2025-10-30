#!/usr/bin/env python3
"""
Multi-Agent Orchestration with GitHub Agent HQ

Demonstrates orchestrating multiple AI agents (Claude, Codex, Copilot) using TTA.dev
primitives for a production-ready code review pipeline.

This example shows:
1. Conditional routing for agent selection based on task type
2. Parallel execution of multiple review stages
3. Sequential pipeline composition
4. Built-in observability with WorkflowContext
5. Type-safe composition with >> and | operators

NOTE: This is a demonstration example. In production, replace mock agents with
actual GitHub Agent HQ integrations for Claude, Codex, Copilot, etc.
"""

import asyncio
from dataclasses import dataclass
from typing import Any

from tta_dev_primitives import (
    ParallelPrimitive,
    SequentialPrimitive,
    WorkflowContext,
    WorkflowPrimitive,
)

# =============================================================================
# Mock Agent Implementations
# (In production, replace with actual GitHub Agent HQ integrations)
# =============================================================================


@dataclass
class AgentResponse:
    """Standard response format for all agents."""

    agent_name: str
    task_type: str
    result: dict[str, Any]
    confidence: float
    duration_ms: float


class ClaudeAgent(WorkflowPrimitive[dict[str, Any], AgentResponse]):
    """
    Anthropic Claude agent - Best for complex reasoning and architecture decisions.

    In production, this would integrate with GitHub Agent HQ's Claude instance.
    """

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: dict[str, Any],
    ) -> AgentResponse:
        """Execute Claude agent."""
        # Simulate Claude's deep analysis
        await asyncio.sleep(0.2)  # Simulate API latency

        return AgentResponse(
            agent_name="Claude",
            task_type=input_data.get("task_type", "unknown"),
            result={
                "analysis": "Deep architectural review completed",
                "issues_found": ["Potential race condition in async handler"],
                "suggestions": ["Consider using lock for shared state"],
                "security_concerns": [],
            },
            confidence=0.95,
            duration_ms=200,
        )


class CodexAgent(WorkflowPrimitive[dict[str, Any], AgentResponse]):
    """
    OpenAI Codex agent - Best for test generation and boilerplate code.

    In production, this would integrate with GitHub Agent HQ's Codex instance.
    """

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: dict[str, Any],
    ) -> AgentResponse:
        """Execute Codex agent."""
        # Simulate Codex's code generation
        await asyncio.sleep(0.15)  # Simulate API latency

        return AgentResponse(
            agent_name="Codex",
            task_type=input_data.get("task_type", "unknown"),
            result={
                "tests_generated": 3,
                "coverage_estimate": 85,
                "test_code": "async def test_handler(): ...",
            },
            confidence=0.90,
            duration_ms=150,
        )


class CopilotAgent(WorkflowPrimitive[dict[str, Any], AgentResponse]):
    """
    GitHub Copilot agent - Fast, good for reviews and documentation.

    In production, this would integrate with GitHub Agent HQ's Copilot instance.
    """

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: dict[str, Any],
    ) -> AgentResponse:
        """Execute Copilot agent."""
        # Simulate Copilot's quick analysis
        await asyncio.sleep(0.1)  # Simulate API latency

        return AgentResponse(
            agent_name="Copilot",
            task_type=input_data.get("task_type", "unknown"),
            result={
                "style_issues": ["Missing docstring on function", "Line too long"],
                "quick_fixes": ["Add type hints", "Format with ruff"],
            },
            confidence=0.85,
            duration_ms=100,
        )


# =============================================================================
# Pattern 1: Router - Select Best Agent for Task Type
# =============================================================================


async def pattern1_router():
    """Demonstrate routing different tasks to appropriate agents."""
    print("\n" + "=" * 80)
    print("PATTERN 1: Router - Dynamic Agent Selection")
    print("=" * 80)

    # Create agents
    claude = ClaudeAgent(name="claude-agent")
    codex = CodexAgent(name="codex-agent")
    copilot = CopilotAgent(name="copilot-agent")

    # Create router
    router = RouterPrimitive(
        routes={
            "architecture": claude,
            "test_generation": codex,
            "code_review": copilot,
        },
        default_route="copilot",
        name="agent-router",
    )

    # Test different task types
    tasks = [
        {"task_type": "architecture", "code": "class ApiHandler: ..."},
        {"task_type": "test_generation", "code": "def process_data(): ..."},
        {"task_type": "code_review", "code": "async def handle_request(): ..."},
    ]

    context = WorkflowContext(correlation_id="demo-router")

    for task in tasks:
        print(f"\n📋 Task: {task['task_type']}")
        result = await router.execute(context, task)
        print(f"✅ Handled by: {result.agent_name}")
        print(f"   Confidence: {result.confidence:.0%}")
        print(f"   Duration: {result.duration_ms}ms")


# =============================================================================
# Pattern 2: Parallel Execution - Multiple Agents Review Same Code
# =============================================================================


async def pattern2_parallel_consensus():
    """Run multiple agents in parallel and aggregate results."""
    print("\n" + "=" * 80)
    print("PATTERN 2: Parallel Consensus - Multiple Agent Reviews")
    print("=" * 80)

    # Create agents
    claude = ClaudeAgent(name="claude-agent")
    codex = CodexAgent(name="codex-agent")
    copilot = CopilotAgent(name="copilot-agent")

    # Create parallel workflow
    parallel_review = ParallelPrimitive(
        primitives=[claude, codex, copilot],
        name="parallel-review",
    )

    # Execute all agents in parallel
    context = WorkflowContext(correlation_id="demo-parallel")
    task = {
        "task_type": "code_review",
        "code": """
        async def handle_api_request(data: dict) -> dict:
            result = await process_data(data)
            return result
        """,
    }

    print("\n🚀 Running 3 agents in parallel...")
    results = await parallel_review.execute(context, task)

    print("\n📊 Results from all agents:")
    for result in results:
        print(f"\n  {result.agent_name}:")
        print(f"    Confidence: {result.confidence:.0%}")
        print(f"    Duration: {result.duration_ms}ms")
        print(f"    Result: {list(result.result.keys())}")

    # Calculate consensus
    avg_confidence = sum(r.confidence for r in results) / len(results)
    print(f"\n✅ Average confidence: {avg_confidence:.0%}")


# =============================================================================
# Pattern 3: Fallback Chain - Reliability Through Redundancy
# =============================================================================


async def pattern3_fallback_chain():
    """Demonstrate fallback pattern for high availability."""
    print("\n" + "=" * 80)
    print("PATTERN 3: Fallback Chain - Graceful Degradation")
    print("=" * 80)

    # Create agents (in order of preference)
    claude = ClaudeAgent(name="claude-primary")
    codex = CodexAgent(name="codex-backup")
    copilot = CopilotAgent(name="copilot-fallback")

    # Create fallback chain
    fallback_workflow = FallbackPrimitive(
        primary=claude,
        fallbacks=[codex, copilot],
        name="fallback-chain",
    )

    context = WorkflowContext(correlation_id="demo-fallback")
    task = {
        "task_type": "architecture",
        "code": "class DataProcessor: ...",
    }

    print("\n🔄 Attempting workflow with fallback chain...")
    print("   Primary: Claude")
    print("   Fallback 1: Codex")
    print("   Fallback 2: Copilot")

    result = await fallback_workflow.execute(context, task)
    print(f"\n✅ Successfully handled by: {result.agent_name}")


# =============================================================================
# Pattern 4: Cache - Cost Optimization
# =============================================================================


async def pattern4_caching():
    """Demonstrate caching for cost optimization."""
    print("\n" + "=" * 80)
    print("PATTERN 4: Caching - Cost Optimization")
    print("=" * 80)

    # Create expensive agent (Claude)
    claude = ClaudeAgent(name="claude-expensive")

    # Wrap with cache
    cached_agent = CachePrimitive(
        primitive=claude,
        ttl_seconds=3600,  # Cache for 1 hour
        max_size=1000,
        name="cached-claude",
    )

    context = WorkflowContext(correlation_id="demo-cache")
    task = {
        "task_type": "architecture",
        "code": "class ApiEndpoint: ...",
    }

    print("\n📞 Call 1: First call (cache miss)")
    result1 = await cached_agent.execute(context, task)
    print(f"   Agent: {result1.agent_name}")
    print(f"   Duration: {result1.duration_ms}ms")

    print("\n📞 Call 2: Repeated call (cache hit)")
    result2 = await cached_agent.execute(context, task)
    print(f"   Agent: {result2.agent_name}")
    print(f"   Duration: {result2.duration_ms}ms (from cache)")

    print("\n💰 Cost savings: Eliminated redundant API call!")


# =============================================================================
# Pattern 5: Production Pipeline - All Patterns Combined
# =============================================================================


class AggregatorPrimitive(WorkflowPrimitive[list[AgentResponse], dict[str, Any]]):
    """Aggregate results from multiple agents."""

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: list[AgentResponse],
    ) -> dict[str, Any]:
        """Aggregate agent responses."""
        return {
            "agents_consulted": [r.agent_name for r in input_data],
            "avg_confidence": sum(r.confidence for r in input_data) / len(input_data),
            "total_issues": sum(len(r.result.get("issues_found", [])) for r in input_data),
            "recommendations": [rec for r in input_data for rec in r.result.get("suggestions", [])],
        }


async def pattern5_production_pipeline():
    """Complete production-ready pipeline with all patterns."""
    print("\n" + "=" * 80)
    print("PATTERN 5: Production Pipeline - Real-World Workflow")
    print("=" * 80)

    # Create agents
    claude = RetryPrimitive(
        ClaudeAgent(name="claude"), max_retries=3, backoff_strategy="exponential"
    )
    codex = RetryPrimitive(CodexAgent(name="codex"), max_retries=3, backoff_strategy="exponential")
    copilot = RetryPrimitive(
        CopilotAgent(name="copilot"), max_retries=3, backoff_strategy="exponential"
    )

    # Stage 1: Route to best agent for initial analysis
    router = RouterPrimitive(
        routes={
            "architecture": claude,
            "test_generation": codex,
            "code_review": copilot,
        },
        default_route="copilot",
    )

    # Stage 2: Parallel review by all agents
    parallel_review = ParallelPrimitive(primitives=[claude, codex, copilot])

    # Stage 3: Aggregate results
    aggregator = AggregatorPrimitive(name="aggregator")

    # Build pipeline
    pipeline = SequentialPrimitive(
        primitives=[router, parallel_review, aggregator],
        name="production-pipeline",
    )

    # Execute
    context = WorkflowContext(
        correlation_id="pr-12345",
        data={
            "pr_number": 12345,
            "branch": "feature/new-api",
            "author": "octocat",
        },
    )

    task = {
        "task_type": "architecture",
        "code": """
        class ApiHandler:
            async def handle_request(self, request: Request) -> Response:
                data = await self.validate(request)
                result = await self.process(data)
                return self.format_response(result)
        """,
    }

    print("\n🚀 Running production pipeline:")
    print("   Stage 1: Initial routing")
    print("   Stage 2: Parallel review (3 agents)")
    print("   Stage 3: Result aggregation")

    result = await pipeline.execute(context, task)

    print("\n📊 Pipeline Results:")
    print(f"   Agents consulted: {', '.join(result['agents_consulted'])}")
    print(f"   Average confidence: {result['avg_confidence']:.0%}")
    print(f"   Issues found: {result['total_issues']}")
    print(f"   Recommendations: {len(result['recommendations'])}")


# =============================================================================
# Main Demo
# =============================================================================


async def main():
    """Run all pattern demonstrations."""
    print("\n" + "=" * 80)
    print("TTA.dev + GitHub Agent HQ - Multi-Agent Orchestration Demo")
    print("=" * 80)
    print("\nDemonstrating 5 production patterns for orchestrating AI agents:")
    print("1. Router - Dynamic agent selection")
    print("2. Parallel - Consensus from multiple agents")
    print("3. Fallback - High availability")
    print("4. Cache - Cost optimization")
    print("5. Production Pipeline - All patterns combined")

    # Run all patterns
    await pattern1_router()
    await pattern2_parallel_consensus()
    await pattern3_fallback_chain()
    await pattern4_caching()
    await pattern5_production_pipeline()

    print("\n" + "=" * 80)
    print("✅ Demo Complete!")
    print("=" * 80)
    print("\n📚 Learn more:")
    print("   - Full guide: docs/integration/github-agent-hq.md")
    print("   - Primitives catalog: PRIMITIVES_CATALOG.md")
    print("   - Getting started: GETTING_STARTED.md")


if __name__ == "__main__":
    asyncio.run(main())
