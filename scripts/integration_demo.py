"""
TTA.dev Integration Demo - Full Stack Observability

This demo demonstrates the integration of all three TTA.dev packages:
1. tta-dev-primitives - Core workflow primitives
2. tta-observability-integration - OpenTelemetry APM
3. universal-agent-context - Configuration patterns

Run with: uv run python scripts/integration_demo.py
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

# Add packages to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "packages/tta-dev-primitives/src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "packages/tta-observability-integration/src"))

# Setup structured logging
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(colors=True)
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = structlog.get_logger(__name__)

# Import primitives
from tta_dev_primitives.core.base import WorkflowContext, LambdaPrimitive
from tta_dev_primitives.core.routing import RouterPrimitive
from tta_dev_primitives.recovery.retry import RetryPrimitive, RetryStrategy
from tta_dev_primitives.recovery.timeout import TimeoutPrimitive
from tta_dev_primitives.recovery.fallback import FallbackPrimitive
from tta_dev_primitives.performance.cache import CachePrimitive


# ============================================================================
# Demo 1: Basic Primitives with Logging
# ============================================================================

async def demo_basic_primitives():
    """Demonstrate basic primitive composition with logging."""
    logger.info("=" * 70)
    logger.info("Demo 1: Basic Primitive Composition")
    logger.info("=" * 70)

    # Define simple processing steps
    async def validate_input(data: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        logger.info("validating_input", data=data, workflow_id=ctx.workflow_id)
        if not data.get("query"):
            raise ValueError("Missing query field")
        return {**data, "validated": True}

    async def process_query(data: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        logger.info("processing_query", query=data.get("query"), workflow_id=ctx.workflow_id)
        await asyncio.sleep(0.1)  # Simulate processing
        return {**data, "processed": True, "result": f"Processed: {data.get('query')}"}

    async def format_response(data: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        logger.info("formatting_response", workflow_id=ctx.workflow_id)
        return {"status": "success", "data": data}

    # Compose workflow
    workflow = (
        LambdaPrimitive(validate_input) >>
        LambdaPrimitive(process_query) >>
        LambdaPrimitive(format_response)
    )

    # Execute
    context = WorkflowContext(
        workflow_id="demo-basic-001",
        session_id="session-123",
        metadata={"environment": "demo"}
    )

    result = await workflow.execute({"query": "Hello TTA.dev!"}, context)
    logger.info("workflow_complete", result=result)

    return result


# ============================================================================
# Demo 2: Routing with Cost Optimization
# ============================================================================

async def demo_routing():
    """Demonstrate intelligent routing based on context."""
    logger.info("=" * 70)
    logger.info("Demo 2: Intelligent Routing")
    logger.info("=" * 70)

    # Simulate different LLM providers
    async def openai_call(data: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        logger.info("calling_openai", query=data.get("query"))
        await asyncio.sleep(0.3)  # Simulate API latency
        return {"provider": "openai", "response": "High quality response", "cost": 0.10}

    async def local_llm_call(data: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        logger.info("calling_local_llm", query=data.get("query"))
        await asyncio.sleep(0.05)  # Faster local inference
        return {"provider": "local", "response": "Quick response", "cost": 0.01}

    async def anthropic_call(data: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        logger.info("calling_anthropic", query=data.get("query"))
        await asyncio.sleep(0.25)
        return {"provider": "anthropic", "response": "Claude response", "cost": 0.08}

    # Router function based on tier
    def route_by_tier(data: dict[str, Any], ctx: WorkflowContext) -> str:
        tier = ctx.metadata.get("tier", "free")
        logger.info("routing_decision", tier=tier, query_length=len(data.get("query", "")))

        if tier == "premium":
            return "openai"
        elif tier == "standard":
            return "anthropic"
        else:
            return "local"

    # Create router
    router = RouterPrimitive(
        routes={
            "openai": LambdaPrimitive(openai_call),
            "anthropic": LambdaPrimitive(anthropic_call),
            "local": LambdaPrimitive(local_llm_call),
        },
        router_fn=route_by_tier,
        default="local"
    )

    # Test different tiers
    for tier in ["free", "standard", "premium"]:
        context = WorkflowContext(
            workflow_id=f"demo-route-{tier}",
            metadata={"tier": tier}
        )
        result = await router.execute({"query": "Test query"}, context)
        logger.info("route_result", tier=tier, provider=result["provider"], cost=result["cost"])

    return {"demo": "routing", "status": "success"}


# ============================================================================
# Demo 3: Recovery Patterns
# ============================================================================

async def demo_recovery():
    """Demonstrate retry, timeout, and fallback patterns."""
    logger.info("=" * 70)
    logger.info("Demo 3: Recovery Patterns")
    logger.info("=" * 70)

    # Flaky operation that fails first 2 times
    attempt_counter = {"count": 0}

    async def flaky_api(data: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        attempt_counter["count"] += 1
        logger.info("flaky_api_attempt", attempt=attempt_counter["count"])

        if attempt_counter["count"] < 3:
            raise ConnectionError(f"Attempt {attempt_counter['count']} failed")

        return {"success": True, "attempts": attempt_counter["count"]}

    # Wrap with retry
    retry_primitive = RetryPrimitive(
        primitive=LambdaPrimitive(flaky_api),
        strategy=RetryStrategy(max_retries=5, backoff_base=2.0)
    )

    context = WorkflowContext(workflow_id="demo-retry")
    result = await retry_primitive.execute({"request": "data"}, context)
    logger.info("retry_success", result=result)

    # Timeout demo
    async def slow_operation(data: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        logger.info("slow_operation_started")
        await asyncio.sleep(0.5)
        return {"slow": True}

    timeout_primitive = TimeoutPrimitive(
        primitive=LambdaPrimitive(slow_operation),
        timeout_seconds=1.0  # Will succeed (0.5s < 1.0s)
    )

    context = WorkflowContext(workflow_id="demo-timeout")
    result = await timeout_primitive.execute({"data": "test"}, context)
    logger.info("timeout_success", result=result)

    # Fallback demo
    async def primary_fails(data: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        logger.info("primary_service_called")
        raise RuntimeError("Primary service down")

    async def fallback_succeeds(data: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        logger.info("fallback_service_called")
        return {"source": "fallback", "success": True}

    fallback_primitive = FallbackPrimitive(
        primary=LambdaPrimitive(primary_fails),
        fallback=LambdaPrimitive(fallback_succeeds)
    )

    context = WorkflowContext(workflow_id="demo-fallback")
    result = await fallback_primitive.execute({"data": "test"}, context)
    logger.info("fallback_result", result=result)

    return {"demo": "recovery", "status": "success"}


# ============================================================================
# Demo 4: Caching with Cost Savings
# ============================================================================

async def demo_caching():
    """Demonstrate caching for cost savings."""
    logger.info("=" * 70)
    logger.info("Demo 4: Caching for Cost Savings")
    logger.info("=" * 70)

    call_counter = {"count": 0}

    async def expensive_llm_call(data: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        call_counter["count"] += 1
        logger.info("expensive_call", call_number=call_counter["count"], query=data.get("query"))
        await asyncio.sleep(0.2)  # Simulate API latency
        return {
            "query": data.get("query"),
            "response": f"Response for: {data.get('query')}",
            "cost": 0.05
        }

    # Wrap with cache
    cached_llm = CachePrimitive(
        primitive=LambdaPrimitive(expensive_llm_call),
        cache_key_fn=lambda d, c: f"query:{d.get('query', '')}",
        ttl_seconds=3600.0
    )

    context = WorkflowContext(workflow_id="demo-cache")

    # First call - cache miss
    logger.info("first_call")
    result1 = await cached_llm.execute({"query": "What is TTA.dev?"}, context)
    logger.info("first_result", result=result1)

    # Second call - cache hit
    logger.info("second_call_same_query")
    result2 = await cached_llm.execute({"query": "What is TTA.dev?"}, context)
    logger.info("second_result", result=result2)

    # Third call - different query, cache miss
    logger.info("third_call_different_query")
    result3 = await cached_llm.execute({"query": "How do primitives work?"}, context)
    logger.info("third_result", result=result3)

    # Show cache stats
    stats = cached_llm.get_stats()
    logger.info("cache_stats",
                hits=stats["hits"],
                misses=stats["misses"],
                hit_rate=f"{stats['hit_rate']:.1%}",
                total_calls=call_counter["count"])

    # Cost savings calculation
    saved_calls = stats["hits"]
    cost_per_call = 0.05
    savings = saved_calls * cost_per_call
    logger.info("cost_savings", saved_calls=saved_calls, savings_usd=f"${savings:.2f}")

    return {"demo": "caching", "status": "success", "cache_stats": stats}


# ============================================================================
# Demo 5: Full Workflow Pipeline
# ============================================================================

async def demo_full_pipeline():
    """Demonstrate a complete workflow with all patterns combined."""
    logger.info("=" * 70)
    logger.info("Demo 5: Full Workflow Pipeline")
    logger.info("=" * 70)

    # Simulate different LLM backends
    async def fast_llm(data: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        await asyncio.sleep(0.05)
        return {"provider": "fast", "response": "Quick answer", "cost": 0.01}

    async def quality_llm(data: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        await asyncio.sleep(0.2)
        return {"provider": "quality", "response": "Detailed answer", "cost": 0.10}

    # Build complete workflow:
    # 1. Cache layer
    # 2. Timeout protection
    # 3. Routing based on query complexity
    # 4. Retry on failure

    def complexity_router(data: dict[str, Any], ctx: WorkflowContext) -> str:
        query = data.get("query", "")
        if len(query) > 50 or ctx.metadata.get("need_quality"):
            return "quality"
        return "fast"

    inner_router = RouterPrimitive(
        routes={
            "fast": RetryPrimitive(
                LambdaPrimitive(fast_llm),
                strategy=RetryStrategy(max_retries=3)
            ),
            "quality": RetryPrimitive(
                LambdaPrimitive(quality_llm),
                strategy=RetryStrategy(max_retries=3)
            ),
        },
        router_fn=complexity_router,
        default="fast"
    )

    pipeline = CachePrimitive(
        primitive=TimeoutPrimitive(
            primitive=inner_router,
            timeout_seconds=5.0
        ),
        cache_key_fn=lambda d, c: f"pipeline:{d.get('query', '')}:{c.metadata.get('need_quality', False)}",
        ttl_seconds=1800.0
    )

    # Run multiple queries
    queries = [
        {"query": "Simple question", "need_quality": False},
        {"query": "A much longer and more complex question that requires detailed analysis", "need_quality": True},
        {"query": "Simple question", "need_quality": False},  # Cache hit
        {"query": "Another simple one", "need_quality": False},
    ]

    total_cost = 0.0
    for i, q in enumerate(queries, 1):
        context = WorkflowContext(
            workflow_id=f"pipeline-{i}",
            metadata={"need_quality": q["need_quality"]}
        )
        logger.info("pipeline_request", request_num=i, query=q["query"][:30] + "...")

        result = await pipeline.execute({"query": q["query"]}, context)
        total_cost += result.get("cost", 0)
        logger.info("pipeline_response",
                   request_num=i,
                   provider=result["provider"],
                   cost=result["cost"])

    stats = pipeline.get_stats()
    logger.info("pipeline_summary",
               total_cost=f"${total_cost:.2f}",
               cache_hits=stats["hits"],
               cache_misses=stats["misses"],
               hit_rate=f"{stats['hit_rate']:.1%}")

    return {"demo": "full_pipeline", "status": "success", "total_cost": total_cost}


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run all demos."""
    logger.info("=" * 70)
    logger.info("TTA.dev Integration Demo")
    logger.info("Demonstrating Primitives + Observability + Agent Context")
    logger.info("=" * 70)

    demos = [
        ("Basic Primitives", demo_basic_primitives),
        ("Intelligent Routing", demo_routing),
        ("Recovery Patterns", demo_recovery),
        ("Caching & Cost Savings", demo_caching),
        ("Full Pipeline", demo_full_pipeline),
    ]

    results = []
    for name, demo_fn in demos:
        try:
            result = await demo_fn()
            results.append((name, "✅ PASSED", result))
            logger.info("demo_passed", demo=name)
        except Exception as e:
            results.append((name, "❌ FAILED", str(e)))
            logger.error("demo_failed", demo=name, error=str(e))

    # Summary
    logger.info("=" * 70)
    logger.info("Demo Summary")
    logger.info("=" * 70)

    for name, status, _ in results:
        print(f"  {status} {name}")

    passed = sum(1 for _, status, _ in results if "PASSED" in status)
    print(f"\n  Total: {passed}/{len(results)} demos passed")

    return all("PASSED" in status for _, status, _ in results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
