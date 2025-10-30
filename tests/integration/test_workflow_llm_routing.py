"""
Multi-package workflow test: LLM Router with Fallback, Retry, and Caching.

Demonstrates:
- RouterPrimitive for intelligent LLM selection
- FallbackPrimitive for graceful degradation
- RetryPrimitive for transient failures
- CachePrimitive for cost optimization
- ObservablePrimitive for monitoring
- Full observability integration
"""

import asyncio
from typing import Any

import pytest
from tta_dev_primitives import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.core.routing import RouterPrimitive
from tta_dev_primitives.recovery import FallbackPrimitive, RetryPrimitive
from tta_dev_primitives.observability.tracing import ObservablePrimitive

# Optional: observability integration
try:
    from observability_integration import initialize_observability

    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False


# ============================================================================
# Mock LLM Primitives
# ============================================================================


class FastLLM(WorkflowPrimitive[dict, dict]):
    """Fast but less accurate LLM (e.g., GPT-3.5)."""

    def __init__(self, failure_rate: float = 0.0):
        self.name = "fast_llm"
        self.failure_rate = failure_rate
        self.call_count = 0

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute fast LLM call."""
        self.call_count += 1
        await asyncio.sleep(0.01)  # Fast response

        # Simulate occasional failures
        if self.failure_rate > 0 and self.call_count % int(1 / self.failure_rate) == 0:
            raise ConnectionError("Fast LLM temporarily unavailable")

        prompt = input_data.get("prompt", "")
        return {
            "response": f"Fast response to: {prompt[:20]}...",
            "model": "gpt-3.5-turbo",
            "cost": 0.001,
            "latency_ms": 10,
        }


class QualityLLM(WorkflowPrimitive[dict, dict]):
    """High quality but slower LLM (e.g., GPT-4)."""

    def __init__(self):
        self.name = "quality_llm"
        self.call_count = 0

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute quality LLM call."""
        self.call_count += 1
        await asyncio.sleep(0.05)  # Slower response

        prompt = input_data.get("prompt", "")
        return {
            "response": f"High-quality response to: {prompt[:20]}...",
            "model": "gpt-4",
            "cost": 0.03,
            "latency_ms": 50,
        }


class LocalLLM(WorkflowPrimitive[dict, dict]):
    """Local LLM (e.g., Llama 3)."""

    def __init__(self):
        self.name = "local_llm"
        self.call_count = 0

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute local LLM call."""
        self.call_count += 1
        await asyncio.sleep(0.02)  # Medium speed

        prompt = input_data.get("prompt", "")
        return {
            "response": f"Local response to: {prompt[:20]}...",
            "model": "llama-3-8b",
            "cost": 0.0,  # Free (local)
            "latency_ms": 20,
        }


class CachedResponse(WorkflowPrimitive[dict, dict]):
    """Cached response primitive."""

    def __init__(self):
        self.name = "cached_response"
        self.cache: dict[str, Any] = {}

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Return cached response if available."""
        prompt = input_data.get("prompt", "")
        cache_key = prompt[:50]  # Use first 50 chars as key

        if cache_key in self.cache:
            return self.cache[cache_key]

        # Not in cache - return empty (will trigger fallback)
        raise KeyError(f"No cached response for: {cache_key}")


# ============================================================================
# Router Strategy
# ============================================================================


def llm_router_strategy(input_data: dict, context: WorkflowContext) -> str:
    """
    Route to appropriate LLM based on request characteristics.

    Strategy:
    - cached: Try cache first
    - fast: Simple queries
    - quality: Complex queries (long prompts, analysis tasks)
    - local: Budget-conscious requests
    """
    prompt = input_data.get("prompt", "")
    task_type = input_data.get("task_type", "general")

    # Try cache first ONLY if explicitly requested
    if context.metadata.get("use_cache", False):
        return "cached"

    # Complex tasks → quality LLM
    if len(prompt) > 500 or task_type in ["analysis", "reasoning"]:
        return "quality"

    # Budget-conscious → local LLM
    if context.metadata.get("budget_mode", False):
        return "local"

    # Default → fast LLM
    return "fast"


# ============================================================================
# Tests: Basic LLM Router
# ============================================================================


@pytest.mark.asyncio
async def test_llm_router_basic():
    """Test basic LLM routing based on input characteristics."""
    # Create LLM primitives
    fast_llm = FastLLM()
    quality_llm = QualityLLM()
    local_llm = LocalLLM()
    cached = CachedResponse()

    # Create router
    router = RouterPrimitive(
        routes={
            "fast": fast_llm,
            "quality": quality_llm,
            "local": local_llm,
            "cached": cached,
        },
        router_fn=llm_router_strategy,
        default="fast",
    )

    context = WorkflowContext(workflow_id="llm-router-test")

    # Test 1: Simple query → fast LLM
    result = await router.execute({"prompt": "Hello world"}, context)
    assert result["model"] == "gpt-3.5-turbo"
    assert fast_llm.call_count == 1

    # Test 2: Complex query → quality LLM
    long_prompt = "Analyze this complex scenario: " + "x" * 500
    result = await router.execute({"prompt": long_prompt}, context)
    assert result["model"] == "gpt-4"
    assert quality_llm.call_count == 1

    # Test 3: Budget mode → local LLM
    context.metadata["budget_mode"] = True
    result = await router.execute({"prompt": "Budget query"}, context)
    assert result["model"] == "llama-3-8b"
    assert local_llm.call_count == 1


@pytest.mark.asyncio
async def test_llm_router_with_fallback():
    """Test LLM router with fallback to alternative models."""
    # Fast LLM that fails sometimes
    fast_llm = FastLLM(failure_rate=1.0)  # Always fails first call
    quality_llm = QualityLLM()

    # Create router with fast LLM
    router = RouterPrimitive(
        routes={"fast": fast_llm, "quality": quality_llm},
        router_fn=lambda data, ctx: "fast",
        default="fast",
    )

    # Wrap in fallback (API uses singular 'fallback', not 'fallbacks')
    workflow = FallbackPrimitive(primary=router, fallback=quality_llm)

    context = WorkflowContext(workflow_id="llm-fallback-test")

    # Fast LLM fails → fallback to quality
    result = await workflow.execute({"prompt": "Test query"}, context)
    assert result["model"] == "gpt-4"  # Fell back to quality
    assert quality_llm.call_count == 1


@pytest.mark.asyncio
async def test_llm_router_with_retry():
    """Test LLM router with automatic retry on transient failures."""
    # LLM that fails on first attempt
    fast_llm = FastLLM(failure_rate=0.5)  # Fails every other call
    fast_llm.call_count = 1  # Start at 1 so first call (which becomes 2) fails

    # Wrap in retry (API uses RetryStrategy object)
    from tta_dev_primitives.recovery.retry import RetryStrategy

    retrying_llm = RetryPrimitive(
        primitive=fast_llm, strategy=RetryStrategy(max_retries=3, backoff_base=1.0)
    )

    context = WorkflowContext(workflow_id="llm-retry-test")

    # Should succeed after retry
    result = await retrying_llm.execute({"prompt": "Test with retry"}, context)
    assert result["model"] == "gpt-3.5-turbo"
    assert fast_llm.call_count >= 3  # Started at 1, failed at 2, succeeded at 3


# ============================================================================
# Tests: Complete LLM Routing Workflow
# ============================================================================


@pytest.mark.asyncio
async def test_complete_llm_routing_workflow():
    """
    Test complete LLM routing workflow with all recovery patterns.

    Workflow:
    1. Try cached response
    2. Route to appropriate LLM
    3. Retry on transient failures
    4. Fallback to alternative LLM if needed
    5. Monitor with observability
    """
    # Create LLM primitives
    fast_llm = FastLLM(failure_rate=0.3)  # 30% failure rate
    quality_llm = QualityLLM()
    local_llm = LocalLLM()
    cached = CachedResponse()

    # Build routing logic with retry
    from tta_dev_primitives.recovery.retry import RetryStrategy

    fast_with_retry = RetryPrimitive(
        primitive=fast_llm, strategy=RetryStrategy(max_retries=2, backoff_base=2.0)
    )

    # Router with retry
    router = RouterPrimitive(
        routes={
            "fast": fast_with_retry,
            "quality": quality_llm,
            "local": local_llm,
            "cached": cached,
        },
        router_fn=llm_router_strategy,
        default="fast",
    )

    # Fallback chain: router → quality (only one fallback level supported)
    workflow = FallbackPrimitive(primary=router, fallback=quality_llm)

    # Add observability
    observable_workflow = ObservablePrimitive(workflow, name="llm_routing_workflow")

    context = WorkflowContext(workflow_id="complete-llm-workflow")

    # Execute workflow
    result = await observable_workflow.execute({"prompt": "Test complete workflow"}, context)

    # Should get a response (from any model)
    assert "response" in result
    assert "model" in result
    assert result["model"] in ["gpt-3.5-turbo", "gpt-4", "llama-3-8b"]


@pytest.mark.asyncio
async def test_llm_routing_cost_optimization():
    """Test that routing optimizes for cost when appropriate."""
    fast_llm = FastLLM()
    quality_llm = QualityLLM()
    local_llm = LocalLLM()

    router = RouterPrimitive(
        routes={"fast": fast_llm, "quality": quality_llm, "local": local_llm},
        router_fn=llm_router_strategy,
        default="fast",
    )

    # Test budget mode uses free local LLM
    context = WorkflowContext(workflow_id="cost-optimization-test")
    context.metadata["budget_mode"] = True

    result = await router.execute({"prompt": "Budget-conscious query"}, context)
    assert result["cost"] == 0.0  # Local LLM is free
    assert result["model"] == "llama-3-8b"


@pytest.mark.asyncio
async def test_llm_routing_latency_optimization():
    """Test that routing optimizes for latency when appropriate."""
    import time

    fast_llm = FastLLM()
    quality_llm = QualityLLM()

    router = RouterPrimitive(
        routes={"fast": fast_llm, "quality": quality_llm},
        router_fn=llm_router_strategy,
        default="fast",
    )

    context = WorkflowContext(workflow_id="latency-optimization-test")

    # Simple query should use fast LLM
    start = time.time()
    result = await router.execute({"prompt": "Quick question"}, context)
    duration = time.time() - start

    assert result["model"] == "gpt-3.5-turbo"
    assert duration < 0.1  # Fast LLM should respond quickly


@pytest.mark.skipif(not OBSERVABILITY_AVAILABLE, reason="observability_integration not available")
@pytest.mark.asyncio
async def test_llm_routing_with_full_observability():
    """Test LLM routing with full observability integration."""
    # Initialize observability
    initialize_observability(service_name="llm-routing-test", enable_prometheus=False)

    fast_llm = FastLLM()
    quality_llm = QualityLLM()

    router = RouterPrimitive(
        routes={"fast": fast_llm, "quality": quality_llm},
        router_fn=llm_router_strategy,
        default="fast",
    )

    workflow = ObservablePrimitive(router, name="observable_llm_router")

    context = WorkflowContext(workflow_id="observability-test", correlation_id="test-123")

    result = await workflow.execute({"prompt": "Test with observability"}, context)

    # Should have successful execution with tracing
    assert "response" in result
    assert context.correlation_id == "test-123"
