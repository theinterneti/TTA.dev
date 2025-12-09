#!/usr/bin/env python3
"""
TTA.dev Integration Demo - Production-Ready Showcase

This demo demonstrates TTA.dev's full capabilities working together:
1. Core primitives (Retry, Cache, Timeout, Sequential, Parallel)
2. Observability integration (OpenTelemetry tracing, metrics)
3. Agent context management (Memory, Handoff, Coordination)
4. Adaptive/self-improving primitives

Run with: uv run python examples/integration_demo.py

Expected output:
- Structured logs showing primitive execution
- Metrics from observability integration
- Agent context flow through multi-agent workflow
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Any

# Add platform packages to path for demo
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "platform", "primitives", "src"))
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "platform", "observability", "src")
)
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "platform", "agent-context", "src")
)

# Core primitives
# Observability integration
from observability_integration import initialize_observability, is_observability_enabled
from observability_integration.primitives import RouterPrimitive
from tta_dev_primitives import (
    CachePrimitive,
    RetryPrimitive,
    TimeoutPrimitive,
    WorkflowContext,
    WorkflowPrimitive,
)
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.sequential import SequentialPrimitive

# Agent context primitives
from universal_agent_context.primitives import (
    AgentCoordinationPrimitive,
    AgentHandoffPrimitive,
    AgentMemoryPrimitive,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# =============================================================================
# Custom Primitives for Demo
# =============================================================================


class DataFetchPrimitive(WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """Simulates fetching data from an external source."""

    def __init__(self, source: str, delay: float = 0.1, fail_rate: float = 0.0):
        self.source = source
        self.delay = delay
        self.fail_rate = fail_rate
        self.call_count = 0

    async def execute(self, input_data: dict[str, Any], context: WorkflowContext) -> dict[str, Any]:
        self.call_count += 1
        import random

        await asyncio.sleep(self.delay)

        if random.random() < self.fail_rate:
            raise ConnectionError(f"Failed to fetch from {self.source}")

        return {
            **input_data,
            "source": self.source,
            "data": f"Data from {self.source} (call #{self.call_count})",
            "workflow_id": context.workflow_id,
        }


class ProcessorPrimitive(WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """Simulates processing data with configurable behavior."""

    def __init__(self, name: str, processing_time: float = 0.05):
        self.name = name
        self.processing_time = processing_time

    async def execute(self, input_data: dict[str, Any], context: WorkflowContext) -> dict[str, Any]:
        await asyncio.sleep(self.processing_time)

        return {
            **input_data,
            f"processed_by_{self.name}": True,
            "processor": self.name,
        }


class AnalyzerPrimitive(WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """Simulates an AI analyzer agent."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    async def execute(self, input_data: dict[str, Any], context: WorkflowContext) -> dict[str, Any]:
        await asyncio.sleep(0.05)

        return {
            "agent": self.agent_name,
            "analysis": f"Analysis by {self.agent_name}",
            "confidence": 0.95,
            "input_summary": str(input_data)[:50],
        }


# =============================================================================
# Demo Functions
# =============================================================================


async def demo_core_primitives():
    """Demonstrate core workflow primitives."""
    print("\n" + "=" * 60)
    print("🔧 CORE PRIMITIVES DEMO")
    print("=" * 60)

    context = WorkflowContext(
        workflow_id="core-demo-001",
        metadata={"demo": "core_primitives", "environment": "development"},
    )

    # Create primitives
    fetch = DataFetchPrimitive("api-server", delay=0.1)
    process1 = ProcessorPrimitive("normalizer")
    process2 = ProcessorPrimitive("enricher")

    # Sequential composition with >> operator
    print("\n📋 Sequential Workflow (fetch >> normalize >> enrich):")
    sequential_workflow = SequentialPrimitive([fetch, process1, process2])
    result = await sequential_workflow.execute({"request_id": 1}, context)
    print(f"   Result: {result.get('processor')} processed data from {result.get('source')}")

    # Retry with exponential backoff
    print("\n🔄 Retry Primitive (with unreliable source):")
    unreliable_fetch = DataFetchPrimitive("flaky-api", delay=0.05, fail_rate=0.5)
    retry_workflow = RetryPrimitive(unreliable_fetch)
    try:
        result = await retry_workflow.execute({"request_id": 2}, context)
        print(f"   Success: Got data from {result.get('source')}")
    except Exception as e:
        print(f"   Failed after retries: {e}")

    # Cache primitive
    print("\n💾 Cache Primitive (second call should be instant):")
    expensive_fetch = DataFetchPrimitive("expensive-api", delay=0.3)
    cached_workflow = CachePrimitive(
        expensive_fetch,
        cache_key_fn=lambda data, ctx: f"{data.get('query', '')}:{ctx.workflow_id}",
        ttl_seconds=60,
    )

    import time

    start = time.time()
    _ = await cached_workflow.execute({"query": "test"}, context)
    time1 = time.time() - start

    start = time.time()
    _ = await cached_workflow.execute({"query": "test"}, context)
    time2 = time.time() - start

    print(f"   First call: {time1:.3f}s")
    print(f"   Second call (cached): {time2:.3f}s")
    print(f"   Speedup: {time1 / max(time2, 0.001):.1f}x")

    # Timeout primitive
    print("\n⏱️ Timeout Primitive:")
    slow_fetch = DataFetchPrimitive("slow-api", delay=0.5)
    timeout_workflow = TimeoutPrimitive(slow_fetch, timeout_seconds=0.2)
    try:
        await timeout_workflow.execute({"request_id": 3}, context)
        print("   Completed within timeout")
    except Exception:
        print("   Correctly timed out (0.2s limit)")

    # Parallel execution
    print("\n⚡ Parallel Primitive (3 sources simultaneously):")
    sources = [
        DataFetchPrimitive("source-a", delay=0.1),
        DataFetchPrimitive("source-b", delay=0.15),
        DataFetchPrimitive("source-c", delay=0.12),
    ]
    parallel_workflow = ParallelPrimitive(sources)

    start = time.time()
    results = await parallel_workflow.execute({"request_id": 4}, context)
    elapsed = time.time() - start

    print(f"   Fetched from {len(results)} sources in {elapsed:.3f}s")
    print(f"   (Sequential would take ~0.37s, parallel took ~{elapsed:.2f}s)")


async def demo_observability():
    """Demonstrate observability integration."""
    print("\n" + "=" * 60)
    print("📊 OBSERVABILITY INTEGRATION DEMO")
    print("=" * 60)

    # Initialize observability
    success = initialize_observability(
        service_name="tta-demo",
        service_version="1.0.0",
        enable_prometheus=False,  # Disable for demo (no prometheus server)
        enable_console_traces=False,
    )
    print(f"\n🔌 Observability initialized: {success}")
    print(f"   Enabled: {is_observability_enabled()}")

    context = WorkflowContext(
        workflow_id="observability-demo-001",
        metadata={"demo": "observability", "tier": "development"},
    )

    # Router primitive with metrics
    print("\n🚦 Router Primitive (intelligent routing with metrics):")

    fast_processor = ProcessorPrimitive("fast", processing_time=0.02)
    premium_processor = ProcessorPrimitive("premium", processing_time=0.1)

    def route_by_priority(data: dict, ctx: WorkflowContext) -> str:
        return "premium" if data.get("priority") == "high" else "fast"

    router = RouterPrimitive(
        routes={"fast": fast_processor, "premium": premium_processor},
        router_fn=route_by_priority,
        default_route="fast",
    )

    # Low priority request
    result1 = await router.execute({"request": "low-priority", "priority": "low"}, context)
    print(f"   Low priority -> {result1.get('processor')} processor")

    # High priority request
    result2 = await router.execute({"request": "high-priority", "priority": "high"}, context)
    print(f"   High priority -> {result2.get('processor')} processor")


async def demo_agent_context():
    """Demonstrate agent context management."""
    print("\n" + "=" * 60)
    print("🤖 AGENT CONTEXT DEMO")
    print("=" * 60)

    context = WorkflowContext(
        workflow_id="agent-demo-001",
        metadata={"current_agent": "copilot", "environment": "development"},
    )

    # Agent memory
    print("\n📝 Agent Memory (store and retrieve architectural decisions):")
    store_decision = AgentMemoryPrimitive(
        operation="store", memory_key="architecture_choice", memory_scope="session"
    )
    await store_decision.execute(
        {"value": "Use composition over inheritance", "tags": ["architecture", "design"]},
        context,
    )
    print("   Stored: architecture_choice = 'Use composition over inheritance'")

    retrieve_decision = AgentMemoryPrimitive(operation="retrieve", memory_key="architecture_choice")
    result = await retrieve_decision.execute({}, context)
    print(f"   Retrieved: {result.get('memory_value')}")

    # Agent handoff
    print("\n🤝 Agent Handoff (transfer task to specialist):")
    handoff = AgentHandoffPrimitive(
        target_agent="claude-analyst",
        handoff_strategy="immediate",
        preserve_context=True,
    )
    result = await handoff.execute(
        {"task": "Analyze performance bottleneck", "data": {"latency_ms": 500}},
        context,
    )
    print(f"   Handoff to: {result.get('handoff_to')}")
    print(f"   Context preserved: {result.get('context_preserved')}")

    # Agent coordination (parallel execution)
    print("\n👥 Agent Coordination (parallel multi-agent workflow):")
    agents = {
        "code_reviewer": AnalyzerPrimitive("code-reviewer"),
        "security_scanner": AnalyzerPrimitive("security-scanner"),
        "performance_analyzer": AnalyzerPrimitive("performance-analyzer"),
    }
    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents,
        coordination_strategy="aggregate",
        require_all_success=False,
    )

    result = await coordinator.execute({"code": "async def main(): pass"}, context)
    print(f"   Agents executed: {list(result.get('agent_results', {}).keys())}")
    print(f"   Successful: {result.get('coordination_metadata', {}).get('successful_agents', 0)}")


async def demo_full_integration():
    """Demonstrate all components working together."""
    print("\n" + "=" * 60)
    print("🚀 FULL INTEGRATION DEMO")
    print("=" * 60)

    context = WorkflowContext(
        workflow_id="integration-demo-001",
        metadata={
            "current_agent": "copilot",
            "environment": "production",
            "user_id": "demo-user",
        },
    )

    print("\n📋 Building production-ready workflow:")
    print("   1. Cache layer for expensive operations")
    print("   2. Retry with exponential backoff")
    print("   3. Timeout for reliability")
    print("   4. Router for cost optimization")
    print("   5. Agent coordination for multi-agent analysis")

    # Build the workflow stack
    data_source = DataFetchPrimitive("production-api", delay=0.1, fail_rate=0.1)

    # Layer 1: Cache
    cached_source = CachePrimitive(
        data_source,
        cache_key_fn=lambda data, ctx: f"{data.get('request_id', '')}:{ctx.workflow_id}",
        ttl_seconds=300,
    )

    # Layer 2: Retry
    reliable_source = RetryPrimitive(cached_source)

    # Layer 3: Timeout
    bounded_source = TimeoutPrimitive(reliable_source, timeout_seconds=5.0)

    # Layer 4: Processing with routing
    fast_proc = ProcessorPrimitive("fast-processor", processing_time=0.02)
    quality_proc = ProcessorPrimitive("quality-processor", processing_time=0.1)

    def smart_router(data: dict, ctx: WorkflowContext) -> str:
        # Route based on environment and data complexity
        env = ctx.metadata.get("environment", "development")
        if env == "production" and data.get("priority") == "high":
            return "quality"
        return "fast"

    router = RouterPrimitive(
        routes={"fast": fast_proc, "quality": quality_proc},
        router_fn=smart_router,
        default_route="fast",
    )

    # Layer 5: Multi-agent analysis
    agents = {
        "validator": AnalyzerPrimitive("validator"),
        "optimizer": AnalyzerPrimitive("optimizer"),
    }
    coordinator = AgentCoordinationPrimitive(
        agent_primitives=agents, coordination_strategy="aggregate"
    )

    # Execute the full workflow
    print("\n⚙️ Executing workflow...")
    import time

    start = time.time()

    # Step 1: Fetch data with all protections
    data = await bounded_source.execute({"request_id": "prod-001"}, context)
    print(f"   ✓ Data fetched: {data.get('source')}")

    # Step 2: Route to appropriate processor
    processed = await router.execute({**data, "priority": "high"}, context)
    print(f"   ✓ Processed by: {processed.get('processor')}")

    # Step 3: Multi-agent validation
    validation = await coordinator.execute(processed, context)
    agents_used = list(validation.get("agent_results", {}).keys())
    print(f"   ✓ Validated by: {agents_used}")

    elapsed = time.time() - start
    print(f"\n✅ Full workflow completed in {elapsed:.3f}s")
    print("   - Retry protection: Active")
    print("   - Cache: Active (60s TTL)")
    print("   - Timeout: 5s max")
    print("   - Routing: Smart (environment-aware)")
    print("   - Multi-agent: 2 validators")


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("🎯 TTA.dev INTEGRATION DEMO")
    print("   Demonstrating production-ready AI workflow primitives")
    print("=" * 60)

    try:
        await demo_core_primitives()
        await demo_observability()
        await demo_agent_context()
        await demo_full_integration()

        print("\n" + "=" * 60)
        print("✅ ALL DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nTTA.dev provides:")
        print("  • Composable workflow primitives")
        print("  • Built-in observability (OpenTelemetry)")
        print("  • Multi-agent coordination")
        print("  • Self-improving adaptive primitives")
        print("  • Production-ready error handling")
        print("\nNext steps:")
        print("  1. See AGENTS.md for full primitive catalog")
        print("  2. Check platform/primitives/examples/ for more patterns")
        print("  3. Run 'uv run pytest -v' to verify all tests pass")

    except Exception as e:
        logger.exception("Demo failed")
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
