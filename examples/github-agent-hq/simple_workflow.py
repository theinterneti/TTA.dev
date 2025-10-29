#!/usr/bin/env python3
"""
Simple Multi-Agent Orchestration with GitHub Agent HQ

This is a simplified demonstration showing how TTA.dev primitives enable
production-ready multi-agent workflows for GitHub Agent HQ.

Run this example:
    uv run python examples/github-agent-hq/simple_workflow.py
"""

import asyncio
from dataclasses import dataclass
from typing import Any

from tta_dev_primitives import (
    ParallelPrimitive,
    WorkflowContext,
    WorkflowPrimitive,
)


@dataclass
class AgentResponse:
    """Standard response format for all agents."""

    agent_name: str
    confidence: float
    result: dict[str, Any]


# Mock agents (replace with real GitHub Agent HQ integrations)


class ClaudeAgent(WorkflowPrimitive[dict[str, Any], AgentResponse]):
    """Mock Claude agent for demonstration."""

    async def execute(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> AgentResponse:
        await asyncio.sleep(0.1)  # Simulate API call
        return AgentResponse(
            agent_name="Claude",
            confidence=0.95,
            result={
                "analysis": "Deep code analysis completed",
                "issues": ["Potential race condition"],
            },
        )


class CodexAgent(WorkflowPrimitive[dict[str, Any], AgentResponse]):
    """Mock Codex agent for demonstration."""

    async def execute(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> AgentResponse:
        await asyncio.sleep(0.08)  # Simulate API call
        return AgentResponse(
            agent_name="Codex",
            confidence=0.90,
            result={"tests_generated": 5, "coverage": 85},
        )


class CopilotAgent(WorkflowPrimitive[dict[str, Any], AgentResponse]):
    """Mock Copilot agent for demonstration."""

    async def execute(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> AgentResponse:
        await asyncio.sleep(0.05)  # Simulate API call
        return AgentResponse(
            agent_name="Copilot",
            confidence=0.85,
            result={"style_issues": ["Missing docstring"], "quick_fixes": 2},
        )


# Pattern 1: Sequential Pipeline


async def demo_sequential():
    """Demonstrate sequential agent pipeline."""
    print("\n" + "=" * 60)
    print("PATTERN 1: Sequential Pipeline")
    print("=" * 60)
    print("\nStages: Planning → Implementation → Review")

    # Create agents
    planner = ClaudeAgent()
    implementer = CodexAgent()
    reviewer = CopilotAgent()

    # Compose with >> operator
    pipeline = planner >> implementer >> reviewer

    # Execute
    context = WorkflowContext(correlation_id="demo-seq")
    task = {"feature": "Add rate limiting"}

    print("\n🚀 Executing pipeline...")
    result = await pipeline.execute(task, context)

    print(f"\n✅ Final result from {result.agent_name}:")
    print(f"   Confidence: {result.confidence:.0%}")
    print(f"   Result: {result.result}")


# Pattern 2: Parallel Execution


async def demo_parallel():
    """Demonstrate parallel agent execution."""
    print("\n" + "=" * 60)
    print("PATTERN 2: Parallel Execution (Consensus)")
    print("=" * 60)
    print("\nRunning 3 agents in parallel for consensus...")

    # Create agents
    claude = ClaudeAgent()
    codex = CodexAgent()
    copilot = CopilotAgent()

    # Compose with | operator (under the hood, uses ParallelPrimitive)
    # Note: Direct | operator needs to be implemented in primitives
    # For now, use ParallelPrimitive explicitly
    parallel = ParallelPrimitive([claude, codex, copilot])

    # Execute
    context = WorkflowContext(correlation_id="demo-parallel")
    task = {"code": "async def handler(): ..."}

    print("\n🚀 Executing parallel workflow...")
    results = await parallel.execute(task, context)

    print(f"\n📊 Got {len(results)} responses:")
    for result in results:
        print(f"   {result.agent_name}: {result.confidence:.0%} confidence")

    avg_confidence = sum(r.confidence for r in results) / len(results)
    print(f"\n✅ Average confidence: {avg_confidence:.0%}")


# Pattern 3: Combined Workflow


async def demo_combined():
    """Demonstrate combined sequential + parallel workflow."""
    print("\n" + "=" * 60)
    print("PATTERN 3: Combined Sequential + Parallel")
    print("=" * 60)
    print("\nStage 1: Planning (Claude)")
    print("Stage 2: Parallel review (All agents)")

    # Create agents
    planner = ClaudeAgent()
    reviewers = ParallelPrimitive([ClaudeAgent(), CodexAgent(), CopilotAgent()])

    # Compose: planning → parallel review
    workflow = planner >> reviewers

    # Execute
    context = WorkflowContext(
        correlation_id="pr-12345",
        metadata={"pr_number": 12345, "branch": "feature/api"},
    )
    task = {"code": "class ApiHandler: ..."}

    print("\n🚀 Executing combined workflow...")
    results = await workflow.execute(task, context)

    print("\n✅ Parallel review completed:")
    print(f"   Reviews: {len(results)}")
    print(f"   Agents: {', '.join(r.agent_name for r in results)}")


# Main


async def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("TTA.dev + GitHub Agent HQ")
    print("Multi-Agent Orchestration Demo")
    print("=" * 60)
    print("\nThis demo shows 3 core patterns:")
    print("1. Sequential: Chain agents with >> operator")
    print("2. Parallel: Run agents concurrently for consensus")
    print("3. Combined: Mix sequential and parallel patterns")

    await demo_sequential()
    await demo_parallel()
    await demo_combined()

    print("\n" + "=" * 60)
    print("✅ Demo Complete!")
    print("=" * 60)
    print("\n📚 Next steps:")
    print("   1. Read docs/integration/github-agent-hq.md")
    print("   2. Replace mock agents with real GitHub Agent HQ integrations")
    print("   3. Add error handling with Retry and Fallback primitives")
    print("   4. Enable observability with tta-observability-integration")
    print("\n🚀 Ready to build production multi-agent workflows!")


if __name__ == "__main__":
    asyncio.run(main())
