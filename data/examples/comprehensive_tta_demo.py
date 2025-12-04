#!/usr/bin/env python3
"""
===============================================================================
TTA.dev Comprehensive Technical Demonstration
===============================================================================

This demo showcases all major TTA.dev capabilities and integrations:

1. CORE PRIMITIVES: Sequential, Parallel, Conditional, Router
2. RECOVERY PRIMITIVES: Retry, Fallback, Timeout, Circuit Breaker, Compensation
3. PERFORMANCE PRIMITIVES: Cache with LRU+TTL
4. ADAPTIVE PRIMITIVES: Self-improving AdaptiveRetryPrimitive
5. COMPOSITION PATTERNS: >> and | operators for workflow building
6. OBSERVABILITY STACK: OpenTelemetry tracing, metrics, WorkflowContext
7. TESTING UTILITIES: MockPrimitive for unit testing
8. PACKAGE INTEGRATIONS: Cross-package workflow examples

Prerequisites:
    - uv sync --all-extras (install all dependencies)
    - Run from project root: uv run python examples/comprehensive_tta_demo.py

Author: TTA.dev Team
Date: 2025-11-29
===============================================================================
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime
from typing import Any

# ============================================================================
# Section 1: Core Imports
# ============================================================================
# Core primitives
from tta_dev_primitives import (
    CachePrimitive,
    CircuitBreaker,
    ConditionalPrimitive,
    FallbackPrimitive,
    MockPrimitive,
    RetryPrimitive,
    RetryStrategy,
    RouterPrimitive,
    TimeoutPrimitive,
    WorkflowContext,
    WorkflowPrimitive,
)

# Adaptive primitives
from tta_dev_primitives.adaptive import (
    AdaptiveRetryPrimitive,
    LearningMode,
)
from tta_dev_primitives.core.base import LambdaPrimitive

# Observability
from tta_dev_primitives.observability import (
    InstrumentedPrimitive,
    get_enhanced_metrics_collector,
)

# Try to import observability integration
try:
    from observability_integration import (
        initialize_observability,
        is_observability_enabled,
    )

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

    def initialize_observability(*args, **kwargs):
        return False

    def is_observability_enabled():
        return False


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("tta_demo")

# ============================================================================
# Section 2: Demo Utilities
# ============================================================================


def print_banner(title: str, char: str = "=", width: int = 80) -> None:
    """Print a formatted banner."""
    print(f"\n{char * width}")
    print(f"  {title}")
    print(f"{char * width}\n")


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'─' * 60}")
    print(f"  📦 {title}")
    print(f"{'─' * 60}\n")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"  ✅ {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"  ℹ️  {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"  ⚠️  {message}")


def print_result(label: str, value: Any) -> None:
    """Print a labeled result."""
    if isinstance(value, dict):
        print(f"  📊 {label}:")
        for k, v in value.items():
            print(f"      {k}: {v}")
    else:
        print(f"  📊 {label}: {value}")


# ============================================================================
# Section 3: Demo Primitives
# ============================================================================


class SimulatedLLMPrimitive(InstrumentedPrimitive[dict, dict]):
    """Simulates an LLM API call with realistic latency and occasional failures."""

    def __init__(
        self,
        name: str = "llm",
        latency_range: tuple = (0.1, 0.5),
        fail_rate: float = 0.1,
    ):
        super().__init__(name=name)
        self.latency_range = latency_range
        self.fail_rate = fail_rate
        self._call_count = 0

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        self._call_count += 1
        # Simulate realistic latency
        latency = random.uniform(*self.latency_range)
        await asyncio.sleep(latency)

        # Simulate occasional failures
        if random.random() < self.fail_rate:
            raise Exception(f"LLM API Error (simulated): Call #{self._call_count}")

        prompt = input_data.get("prompt", "")
        return {
            "response": f"LLM Response to: {prompt[:50]}...",
            "model": self.name,
            "latency_ms": latency * 1000,
            "tokens": len(prompt.split()) * 2,
        }


class DataProcessingPrimitive(InstrumentedPrimitive[dict, dict]):
    """Simulates data processing/transformation."""

    def __init__(self, name: str = "data_processor"):
        super().__init__(name=name)

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        await asyncio.sleep(random.uniform(0.01, 0.05))  # Fast processing
        return {
            **input_data,
            "processed": True,
            "processor": self.name,
            "timestamp": datetime.now().isoformat(),
        }


class ValidationPrimitive(InstrumentedPrimitive[dict, dict]):
    """Validates input data."""

    def __init__(self, required_fields: list[str] | None = None):
        super().__init__(name="validator")
        self.required_fields = required_fields or ["prompt"]

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        await asyncio.sleep(0.005)  # Very fast validation

        missing = [f for f in self.required_fields if f not in input_data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        return {**input_data, "validated": True}


class UnreliableServicePrimitive(WorkflowPrimitive[dict, dict]):
    """A service that fails frequently - used to demonstrate retry/fallback."""

    def __init__(self, name: str, fail_rate: float = 0.7):
        self.name = name
        self.fail_rate = fail_rate
        self.call_count = 0

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        self.call_count += 1
        await asyncio.sleep(0.05)

        if random.random() < self.fail_rate:
            raise Exception(f"{self.name} failed (call #{self.call_count})")

        return {**input_data, "service": self.name, "call": self.call_count}


# ============================================================================
# Section 4: Core Primitives Demonstration
# ============================================================================


async def demo_core_primitives() -> None:
    """Demonstrate core workflow primitives."""
    print_section("1. CORE PRIMITIVES DEMONSTRATION")

    # --- Sequential Primitive ---
    print("  📝 Sequential Primitive (>>)")
    print("     Chains primitives: output of one → input of next")

    step1 = LambdaPrimitive(lambda x, ctx: {**x, "step1": "complete"})
    step2 = LambdaPrimitive(lambda x, ctx: {**x, "step2": "complete"})
    step3 = LambdaPrimitive(lambda x, ctx: {**x, "step3": "complete"})

    # Using >> operator
    sequential_workflow = step1 >> step2 >> step3

    context = WorkflowContext(workflow_id="demo-sequential", correlation_id="seq-001")
    result = await sequential_workflow.execute({"input": "test"}, context)

    print_success("Sequential execution completed")
    print_result("Result", result)

    # --- Parallel Primitive ---
    print("\n  📝 Parallel Primitive (|)")
    print("     Executes primitives concurrently, collects all results")

    fast_llm = SimulatedLLMPrimitive("gpt-4-mini", (0.05, 0.1), fail_rate=0)
    quality_llm = SimulatedLLMPrimitive("gpt-4", (0.2, 0.4), fail_rate=0)
    local_llm = SimulatedLLMPrimitive("ollama-llama", (0.02, 0.05), fail_rate=0)

    # Using | operator
    parallel_workflow = fast_llm | quality_llm | local_llm

    context = WorkflowContext(workflow_id="demo-parallel", correlation_id="par-001")
    results = await parallel_workflow.execute({"prompt": "Hello, AI!"}, context)

    print_success(f"Parallel execution completed - {len(results)} results")
    for i, r in enumerate(results):
        print(f"      Branch {i + 1}: {r.get('model')} ({r.get('latency_ms', 0):.0f}ms)")

    # --- Conditional Primitive ---
    print("\n  📝 Conditional Primitive")
    print("     Routes based on runtime conditions")

    fast_path = SimulatedLLMPrimitive("fast-model", (0.02, 0.05), fail_rate=0)
    slow_path = SimulatedLLMPrimitive("quality-model", (0.2, 0.4), fail_rate=0)

    conditional = ConditionalPrimitive(
        condition=lambda data, ctx: len(data.get("prompt", "")) < 50,
        then_primitive=fast_path,
        else_primitive=slow_path,
    )

    # Short prompt → fast path
    ctx = WorkflowContext(workflow_id="demo-conditional")
    _ = await conditional.execute({"prompt": "Hi!"}, ctx)
    print_success(f"Short prompt → {result1.get('model')} path")

    # Long prompt → slow path
    _ = await conditional.execute(
        {"prompt": "This is a much longer prompt that requires more sophisticated processing"},
        ctx,
    )
    print_success(f"Long prompt → {result2.get('model')} path")

    # --- Router Primitive ---
    print("\n  📝 Router Primitive")
    print("     Dynamic routing based on custom logic")

    router = RouterPrimitive(
        routes={
            "fast": SimulatedLLMPrimitive("gpt-4-mini", (0.03, 0.08), fail_rate=0),
            "quality": SimulatedLLMPrimitive("gpt-4", (0.15, 0.3), fail_rate=0),
            "code": SimulatedLLMPrimitive("claude-sonnet", (0.1, 0.2), fail_rate=0),
        },
        router_fn=lambda data, ctx: ctx.metadata.get("mode", "fast"),
        default="fast",
    )

    for mode in ["fast", "quality", "code"]:
        ctx = WorkflowContext(metadata={"mode": mode})
        result = await router.execute({"prompt": "Test query"}, ctx)
        print_success(f"Mode '{mode}' → routed to {result.get('model')}")


# ============================================================================
# Section 5: Recovery Primitives Demonstration
# ============================================================================


async def demo_recovery_primitives() -> None:
    """Demonstrate recovery and resilience primitives."""
    print_section("2. RECOVERY PRIMITIVES DEMONSTRATION")

    # --- Retry Primitive ---
    print("  📝 Retry Primitive")
    print("     Automatic retry with exponential backoff")

    unreliable = UnreliableServicePrimitive("flaky-api", fail_rate=0.6)

    retry_workflow = RetryPrimitive(
        primitive=unreliable,
        strategy=RetryStrategy(max_retries=5, backoff_base=1.2, jitter=True),
    )

    ctx = WorkflowContext(workflow_id="demo-retry", correlation_id="retry-001")
    try:
        result = await retry_workflow.execute({"data": "test"}, ctx)
        print_success(f"Succeeded after {unreliable.call_count} attempts")
    except Exception as e:
        print_warning(f"Failed after {unreliable.call_count} attempts: {e}")

    # --- Fallback Primitive ---
    print("\n  📝 Fallback Primitive")
    print("     Graceful degradation with fallback cascade")

    primary = UnreliableServicePrimitive("primary-api", fail_rate=0.9)
    backup = SimulatedLLMPrimitive("reliable-fallback", (0.05, 0.1), fail_rate=0)

    # FallbackPrimitive takes primary and a single fallback
    fallback_workflow = FallbackPrimitive(
        primary=primary,
        fallback=backup,
    )

    ctx = WorkflowContext(workflow_id="demo-fallback")
    result = await fallback_workflow.execute({"prompt": "test"}, ctx)
    service = result.get("service") or result.get("model")
    print_success(f"Request handled by: {service}")

    # --- Timeout Primitive ---
    print("\n  📝 Timeout Primitive")
    print("     Prevents hanging requests with circuit breaker pattern")

    slow_service = SimulatedLLMPrimitive("slow-llm", (0.5, 1.0), fail_rate=0)

    timeout_workflow = TimeoutPrimitive(
        primitive=slow_service,
        timeout_seconds=0.3,  # 300ms timeout
    )

    ctx = WorkflowContext(workflow_id="demo-timeout")
    try:
        result = await timeout_workflow.execute({"prompt": "test"}, ctx)
        print_success("Completed within timeout")
    except Exception as e:
        if "timeout" in str(e).lower():
            print_warning("Request timed out (as expected with slow service)")
        else:
            raise

    # --- Circuit Breaker ---
    print("\n  📝 Circuit Breaker")
    print("     Prevents cascade failures by opening circuit on repeated failures")

    # CircuitBreaker wraps sync functions, not primitives
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=1.0,
    )

    call_count = 0

    def fragile_function() -> dict:
        """A function that fails frequently."""
        nonlocal call_count
        call_count += 1
        if random.random() < 0.8:
            raise Exception(f"Fragile function failed (call #{call_count})")
        return {"success": True, "call": call_count}

    success_count = 0
    fail_count = 0
    circuit_open_count = 0

    for i in range(10):
        try:
            breaker.call(fragile_function)
            success_count += 1
        except Exception as e:
            if "circuit breaker is open" in str(e).lower():
                circuit_open_count += 1
            else:
                fail_count += 1

    print_success(
        f"Circuit breaker results: {success_count} success, {fail_count} failures, {circuit_open_count} circuit-open rejections"
    )


# ============================================================================
# Section 6: Performance Primitives Demonstration
# ============================================================================


async def demo_performance_primitives() -> None:
    """Demonstrate performance optimization primitives."""
    print_section("3. PERFORMANCE PRIMITIVES DEMONSTRATION")

    # --- Cache Primitive ---
    print("  📝 Cache Primitive")
    print("     LRU cache with TTL for expensive operations")

    expensive_llm = SimulatedLLMPrimitive("expensive-gpt4", (0.3, 0.5), fail_rate=0)

    cached_llm = CachePrimitive(
        primitive=expensive_llm,
        cache_key_fn=lambda data, ctx: data.get("prompt", ""),
        ttl_seconds=60.0,  # 1 minute TTL
    )

    ctx = WorkflowContext(workflow_id="demo-cache")

    # First call - cache miss (slow)
    start = time.time()
    _ = await cached_llm.execute({"prompt": "What is AI?"}, ctx)
    first_time = time.time() - start
    print_success(f"First call (cache miss): {first_time * 1000:.0f}ms")

    # Second call - cache hit (fast)
    start = time.time()
    _ = await cached_llm.execute({"prompt": "What is AI?"}, ctx)
    second_time = time.time() - start
    print_success(f"Second call (cache hit): {second_time * 1000:.0f}ms")

    # Different prompt - cache miss
    start = time.time()
    _ = await cached_llm.execute({"prompt": "What is ML?"}, ctx)
    third_time = time.time() - start
    print_success(f"Different prompt (cache miss): {third_time * 1000:.0f}ms")

    # Show cache stats
    stats = cached_llm.get_stats()
    print_result(
        "Cache Stats",
        {
            "hits": stats["hits"],
            "misses": stats["misses"],
            "hit_rate": f"{stats['hit_rate'] * 100:.1f}%",
            "estimated_savings": f"{first_time - second_time:.3f}s per hit",
        },
    )


# ============================================================================
# Section 7: Adaptive/Self-Improving Primitives Demonstration
# ============================================================================


async def demo_adaptive_primitives() -> None:
    """Demonstrate adaptive/self-improving primitives."""
    print_section("4. ADAPTIVE PRIMITIVES DEMONSTRATION")

    print("  📝 Adaptive Retry Primitive")
    print("     Self-improving retry that learns optimal strategies")
    print("     - Learns which retry params work best for different contexts")
    print("     - Adapts backoff strategies based on success patterns")
    print("     - Can persist learned strategies to Logseq KB")

    # Create a simple unreliable primitive for the adaptive retry to wrap
    unreliable = UnreliableServicePrimitive("adaptive-target", fail_rate=0.4)

    # Create adaptive retry (without Logseq integration for demo)
    adaptive_retry = AdaptiveRetryPrimitive(
        target_primitive=unreliable,
        learning_mode=LearningMode.VALIDATE,  # Learn but validate before using
        max_strategies=5,
        enable_auto_persistence=False,  # Don't persist for demo
    )

    print("\n  Running multiple executions to demonstrate learning...")

    success_count = 0
    fail_count = 0

    for i in range(10):
        ctx = WorkflowContext(
            workflow_id=f"adaptive-demo-{i}",
            metadata={
                "environment": "production" if i % 2 == 0 else "staging",
                "priority": "high" if i % 3 == 0 else "normal",
            },
        )

        try:
            result = await adaptive_retry.execute({"request": i}, ctx)
            if result.get("success"):
                success_count += 1
            else:
                fail_count += 1
        except Exception:
            fail_count += 1

    print_success(f"Adaptive retry results: {success_count} success, {fail_count} failures")

    # Show learned strategies
    print("\n  📊 Learned Strategies:")
    for name, strategy in adaptive_retry.strategies.items():
        print(f"      {name}:")
        print(f"        - Description: {strategy.description[:60]}...")
        print(f"        - Parameters: {json.dumps(strategy.parameters, indent=8)[:100]}")

    print_info(f"Total adaptations made: {adaptive_retry.total_adaptations}")


# ============================================================================
# Section 8: Composition Patterns Demonstration
# ============================================================================


async def demo_composition_patterns() -> None:
    """Demonstrate workflow composition patterns."""
    print_section("5. COMPOSITION PATTERNS DEMONSTRATION")

    print("  📝 Complex Workflow with Mixed Composition")
    print("     Building production-ready AI workflow with all safeguards")

    # Create base primitives
    validator = ValidationPrimitive(required_fields=["prompt"])
    fast_llm = SimulatedLLMPrimitive("gpt-4-mini", (0.05, 0.1), fail_rate=0.1)
    quality_llm = SimulatedLLMPrimitive("gpt-4", (0.2, 0.4), fail_rate=0.05)
    local_llm = SimulatedLLMPrimitive("ollama-llama", (0.02, 0.05), fail_rate=0)
    processor = DataProcessingPrimitive("post-processor")

    # Layer 1: Cache for cost reduction
    cached_fast = CachePrimitive(
        primitive=fast_llm,
        cache_key_fn=lambda d, c: d.get("prompt", ""),
        ttl_seconds=300.0,
    )

    # Layer 2: Retry for resilience
    retried_fast = RetryPrimitive(
        primitive=cached_fast,
        strategy=RetryStrategy(max_retries=2, backoff_base=1.5),
    )

    # Layer 3: Fallback for high availability (nested fallbacks)
    # FallbackPrimitive takes a single fallback, so we nest them
    quality_fallback = FallbackPrimitive(
        primary=quality_llm,
        fallback=local_llm,
    )
    resilient_llm = FallbackPrimitive(
        primary=retried_fast,
        fallback=quality_fallback,
    )

    # Layer 4: Timeout for bounded latency
    bounded_llm = TimeoutPrimitive(
        primitive=resilient_llm,
        timeout_seconds=2.0,
    )

    # Layer 5: Full workflow with validation and post-processing
    # Using >> operator for sequential composition
    production_workflow = validator >> bounded_llm >> processor

    print("\n  Workflow Structure:")
    print("    validator >> (cached >> retried >> fallback >> timeout) >> processor")
    print("\n  Running production workflow...")

    ctx = WorkflowContext(
        workflow_id="production-demo",
        correlation_id="prod-001",
        metadata={"tier": "enterprise", "user_id": "user-123"},
    )

    prompts = [
        "Explain quantum computing",
        "What is machine learning?",
        "Explain quantum computing",  # Same prompt - should hit cache
    ]

    for prompt in prompts:
        try:
            result = await production_workflow.execute({"prompt": prompt}, ctx)
            model = result.get("model", "unknown")
            print_success(f"'{prompt[:30]}...' → {model} → processed={result.get('processed')}")
        except Exception as e:
            print_warning(f"'{prompt[:30]}...' → Failed: {e}")


# ============================================================================
# Section 9: Observability Stack Demonstration
# ============================================================================


async def demo_observability() -> None:
    """Demonstrate observability and tracing capabilities."""
    print_section("6. OBSERVABILITY STACK DEMONSTRATION")

    print("  📝 WorkflowContext with Distributed Tracing")
    print("     - Correlation IDs for request tracking")
    print("     - W3C Trace Context support")
    print("     - Checkpoints for workflow state")
    print("     - Baggage for cross-service context")

    # Create context with full observability
    ctx = WorkflowContext(
        workflow_id="observability-demo",
        correlation_id="obs-001",
        trace_id="abc123def456",
        span_id="span-789",
        metadata={
            "user_id": "user-123",
            "request_type": "analysis",
            "tier": "enterprise",
        },
        baggage={"tenant_id": "tenant-456", "region": "us-west-2"},
    )

    print_result(
        "Context Details",
        {
            "workflow_id": ctx.workflow_id,
            "correlation_id": ctx.correlation_id,
            "trace_id": ctx.trace_id,
            "span_id": ctx.span_id,
            "metadata": ctx.metadata,
            "baggage": ctx.baggage,
        },
    )

    # Demonstrate checkpoints
    print("\n  📝 Workflow Checkpoints")
    print("     Track progress through complex workflows")

    # Checkpoints record timing milestones
    ctx.checkpoint("validation_complete")
    ctx.checkpoint("llm_call_complete")
    ctx.checkpoint("processing_complete")

    print_result(
        "Checkpoints",
        {name: f"{(ts - ctx.start_time) * 1000:.2f}ms" for name, ts in ctx.checkpoints},
    )
    print_result("Elapsed Time", f"{ctx.elapsed_ms():.2f}ms")

    # OpenTelemetry integration status
    print("\n  📝 OpenTelemetry Integration")

    if OTEL_AVAILABLE:
        success = initialize_observability(
            service_name="tta-demo",
            enable_prometheus=False,  # Don't start Prometheus server for demo
        )
        if success:
            print_success("OpenTelemetry initialized successfully")
            print_info("Traces would be exported to configured backend")
            print_info("Metrics available on Prometheus endpoint (if enabled)")
        else:
            print_warning("OpenTelemetry initialization returned False")
    else:
        print_warning("OpenTelemetry integration not available")
        print_info("Install with: uv add tta-observability-integration")

    # Metrics collector
    print("\n  📝 Enhanced Metrics Collector")

    metrics = get_enhanced_metrics_collector()

    # Configure SLO for demo primitive
    metrics.configure_slo("demo_primitive", target=0.99, threshold_ms=500.0)

    # Record some sample metrics
    metrics.record_execution("demo_primitive", 150.0, success=True)
    metrics.record_execution("demo_primitive", 200.0, success=True)
    metrics.record_execution("demo_primitive", 180.0, success=False)

    all_metrics = metrics.get_all_metrics("demo_primitive")
    print_result(
        "Metrics Summary",
        {
            "percentiles": all_metrics.get("percentiles", {}),
            "slo_status": all_metrics.get("slo", {}).get("is_compliant", "N/A"),
            "throughput": all_metrics.get("throughput", {}),
        },
    )


# ============================================================================
# Section 10: Testing Utilities Demonstration
# ============================================================================


async def demo_testing_utilities() -> None:
    """Demonstrate testing utilities."""
    print_section("7. TESTING UTILITIES DEMONSTRATION")

    print("  📝 MockPrimitive for Unit Testing")
    print("     - Configurable return values")
    print("     - Call tracking and assertions")
    print("     - Side effects and error simulation")

    # Create mock primitive
    mock_llm = MockPrimitive(
        name="mock-gpt4",
        return_value={"response": "Mocked response", "model": "mock-gpt4"},
    )

    # Use mock in workflow
    processor = DataProcessingPrimitive("processor")
    workflow = mock_llm >> processor

    ctx = WorkflowContext(workflow_id="test-workflow")
    result = await workflow.execute({"prompt": "Test input"}, ctx)

    print_success(f"Mock called {mock_llm.call_count} time(s)")
    print_result("Mock Result", result)

    # Demonstrate call tracking
    print("\n  📝 Call Tracking")

    mock_llm.reset()

    for i in range(3):
        await mock_llm.execute({"prompt": f"Query {i}"}, ctx)

    print_success(f"Total calls: {mock_llm.call_count}")
    if mock_llm.calls:
        last_input, _ = mock_llm.calls[-1]
        print_info(f"Last call input: {last_input}")

    # Demonstrate error simulation
    print("\n  📝 Error Simulation")

    error_mock = MockPrimitive(
        name="error-mock",
        raise_error=ValueError("Simulated error for testing"),
    )

    try:
        await error_mock.execute({}, ctx)
    except ValueError as e:
        print_success(f"Error correctly raised: {e}")


# ============================================================================
# Section 11: MCP Server Integrations Reference
# ============================================================================


def show_mcp_integrations() -> None:
    """Display MCP server integrations reference."""
    print_section("8. MCP SERVER INTEGRATIONS REFERENCE")

    print("  TTA.dev integrates with 8 MCP servers for enhanced capabilities:")
    print()

    mcp_servers = [
        {
            "name": "Context7",
            "purpose": "Library documentation retrieval",
            "tools": ["resolve-library-id", "get-library-docs"],
            "toolset": "#tta-agent-dev",
        },
        {
            "name": "AI Toolkit",
            "purpose": "AI model management and inference",
            "tools": ["get_models", "run_inference", "get_tools"],
            "toolset": "#tta-agent-dev",
        },
        {
            "name": "Grafana",
            "purpose": "Metrics visualization and dashboards",
            "tools": ["search_dashboards", "get_datasources", "query_prometheus"],
            "toolset": "#tta-observability",
        },
        {
            "name": "Pylance",
            "purpose": "Python code intelligence",
            "tools": ["get_hover_info", "get_completions", "get_diagnostics"],
            "toolset": "#tta-package-dev",
        },
        {
            "name": "Database Client",
            "purpose": "Database operations",
            "tools": ["execute_query", "list_tables", "describe_table"],
            "toolset": "#tta-agent-dev",
        },
        {
            "name": "GitHub PR",
            "purpose": "Pull request management",
            "tools": ["create_pr", "list_prs", "review_pr"],
            "toolset": "#tta-package-dev",
        },
        {
            "name": "Sift",
            "purpose": "Code search and analysis",
            "tools": ["search_code", "find_references", "analyze_dependencies"],
            "toolset": "#tta-package-dev",
        },
        {
            "name": "LogSeq",
            "purpose": "Knowledge base and TODO management",
            "tools": ["create_page", "search_pages", "add_block"],
            "toolset": "#tta-agent-dev",
        },
    ]

    for server in mcp_servers:
        print(f"  📦 {server['name']}")
        print(f"     Purpose: {server['purpose']}")
        print(f"     Tools: {', '.join(server['tools'])}")
        print(f"     Toolset: {server['toolset']}")
        print()

    print("  💡 See MCP_SERVERS.md for full configuration details")


# ============================================================================
# Section 12: Logseq TODO Management Reference
# ============================================================================


def show_logseq_integration() -> None:
    """Display Logseq TODO management reference."""
    print_section("9. LOGSEQ TODO MANAGEMENT REFERENCE")

    print("  TTA.dev uses Logseq for comprehensive TODO and knowledge management:")
    print()

    print("  📋 TODO Tag Conventions:")
    print("     #dev-todo      - Development work (building TTA.dev)")
    print("     #learning-todo - User education (tutorials, flashcards)")
    print("     #template-todo - Reusable patterns")
    print("     #ops-todo      - Infrastructure (deployment, monitoring)")
    print()

    print("  📊 TODO Properties:")
    print("     type::     - implementation, bug, feature, learning")
    print("     priority:: - high, medium, low")
    print("     package::  - tta-dev-primitives, tta-observability-integration, etc.")
    print("     status::   - in-progress, blocked, review")
    print("     due::      - YYYY-MM-DD")
    print()

    print("  📁 Key Logseq Pages:")
    print("     logseq/pages/TODO Management System.md - Main dashboard")
    print("     logseq/pages/TTA.dev/TODO Architecture.md - System design")
    print("     logseq/pages/TODO Templates.md - Copy-paste patterns")
    print()

    print("  💡 Example TODO:")
    print("     - TODO Implement CachePrimitive metrics #dev-todo")
    print("       type:: implementation")
    print("       priority:: high")
    print("       package:: tta-observability-integration")
    print()


# ============================================================================
# Section 13: VS Code Toolsets Reference
# ============================================================================


def show_vscode_toolsets() -> None:
    """Display VS Code toolsets reference."""
    print_section("10. VS CODE TOOLSETS REFERENCE")

    print("  TTA.dev provides specialized Copilot toolsets for different workflows:")
    print()

    toolsets = [
        {
            "name": "#tta-agent-dev",
            "purpose": "Agent development and orchestration",
            "includes": ["Context7", "AI Toolkit", "Database Client", "LogSeq"],
        },
        {
            "name": "#tta-observability",
            "purpose": "Monitoring, tracing, and metrics",
            "includes": ["Grafana", "Prometheus queries", "Trace analysis"],
        },
        {
            "name": "#tta-package-dev",
            "purpose": "Package development and testing",
            "includes": ["Pylance", "GitHub PR", "Sift", "Test runners"],
        },
        {
            "name": "#tta-testing",
            "purpose": "Test development and validation",
            "includes": ["MockPrimitive patterns", "pytest integration", "Coverage"],
        },
    ]

    for toolset in toolsets:
        print(f"  🔧 {toolset['name']}")
        print(f"     Purpose: {toolset['purpose']}")
        print(f"     Includes: {', '.join(toolset['includes'])}")
        print()

    print("  💡 Usage: Type toolset name in Copilot Chat to activate")
    print("  💡 Config: .vscode/copilot-toolsets.jsonc")


# ============================================================================
# Section 14: Main Entry Point
# ============================================================================


async def run_all_demos() -> None:
    """Run all demonstrations."""
    print_banner("TTA.dev COMPREHENSIVE TECHNICAL DEMONSTRATION", "═")

    print("  This demo showcases all major TTA.dev capabilities:")
    print("  • Core workflow primitives (Sequential, Parallel, Conditional, Router)")
    print("  • Recovery primitives (Retry, Fallback, Timeout, Circuit Breaker)")
    print("  • Performance primitives (Cache with LRU+TTL)")
    print("  • Adaptive/self-improving primitives (AdaptiveRetryPrimitive)")
    print("  • Composition patterns (>> and | operators)")
    print("  • Observability stack (OpenTelemetry, WorkflowContext)")
    print("  • Testing utilities (MockPrimitive)")
    print("  • MCP server integrations")
    print("  • Logseq TODO management")
    print("  • VS Code toolsets")
    print()
    print("  Running demonstrations...")

    start_time = time.time()

    # Run async demos
    await demo_core_primitives()
    await demo_recovery_primitives()
    await demo_performance_primitives()
    await demo_adaptive_primitives()
    await demo_composition_patterns()
    await demo_observability()
    await demo_testing_utilities()

    # Show reference sections (sync)
    show_mcp_integrations()
    show_logseq_integration()
    show_vscode_toolsets()

    # Summary
    elapsed = time.time() - start_time

    print_banner("DEMONSTRATION COMPLETE", "═")
    print(f"  ⏱️  Total execution time: {elapsed:.2f} seconds")
    print()
    print("  📚 Next Steps:")
    print("     1. Explore packages/tta-dev-primitives/examples/ for more examples")
    print("     2. Read PRIMITIVES_CATALOG.md for complete primitive reference")
    print("     3. Check MCP_SERVERS.md for MCP integration details")
    print("     4. Review .github/copilot-instructions.md for development guidelines")
    print("     5. Use Logseq TODO system for task management")
    print()
    print("  🚀 TTA.dev - Production-ready AI development toolkit")
    print()


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(run_all_demos())
    except KeyboardInterrupt:
        print("\n\n  ⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n  ❌ Demo failed with error: {e}")
        raise


if __name__ == "__main__":
    main()
